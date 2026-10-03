import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from curl_cffi import requests
from dotenv import load_dotenv

# Carica il .env dalla radice del progetto, indipendentemente da dove parte l'app
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

logger = logging.getLogger(__name__)


class TrendEngine:
    def __init__(self, geo: str = "IT"):
        self.geo = geo
        self.api_key = os.environ.get("SERPAPI_KEY", "")
        if not self.api_key:
            logger.error("API KEY MANCANTE! Inseriscila nel file .env alla voce SERPAPI_KEY")
        self.base_url = "https://serpapi.com/search.json"
        self.account_url = "https://serpapi.com/account.json"
        
        # Setup Cache
        self.cache_file = os.path.join(os.path.dirname(__file__), "trends_cache.json")
        self.cache_ttl_days = 7
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Carica la cache da file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Errore lettura cache: {e}")
        return {}

    def _save_cache(self):
        """Salva la cache su file."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=4)
        except Exception as e:
            logger.error(f"Errore salvataggio cache: {e}")

    def get_remaining_credits(self):
        """Crediti SerpApi rimasti (int), oppure None se non verificabili (mai un numero inventato)."""
        try:
            resp = requests.get(f"{self.account_url}?api_key={self.api_key}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("total_searches_left")
        except Exception as e:
            logger.warning(f"Impossibile verificare crediti API: {e}")
        return None

    def _query_trends(self, keyword: str) -> dict:
        params = {
            "engine": "google_trends",
            "q": keyword,
            "data_type": "TIMESERIES",
            "date": "today 3-m",
            "geo": self.geo,
            "api_key": self.api_key
        }
        
        resp = requests.get(self.base_url, params=params, timeout=15)
        
        if resp.status_code != 200:
            logger.error(f"Errore API SerpApi: {resp.status_code} - {resp.text}")
            return {}
            
        data = resp.json()
        
        if "interest_over_time" not in data or "timeline_data" not in data["interest_over_time"]:
            return {}
            
        timeline = data["interest_over_time"]["timeline_data"]
        
        if not timeline:
            return {}
            
        values = []
        for point in timeline:
            if "values" in point and len(point["values"]) > 0:
                val = point["values"][0].get("extracted_value", 0)
                values.append(val)
                
        if not values:
            return {}
            
        recent_values = values[-14:]
        avg_score = sum(recent_values) / len(recent_values)
        is_breakout = values[-1] > (avg_score * 1.5)
        
        return {"trend_score": round(avg_score, 2), "is_breakout": is_breakout}

    def evaluate_keyword(self, keyword: str, max_retries: int = 3) -> dict:
        """Valuta il trend usando cache locale e controllo limiti API."""
        
        # 1. Controllo CACHE
        now = datetime.now().isoformat()
        if keyword in self.cache:
            entry = self.cache[keyword]
            cached_date = datetime.fromisoformat(entry["timestamp"])
            if datetime.now() - cached_date < timedelta(days=self.cache_ttl_days):
                logger.info(f"Trend per '{keyword}' recuperato dalla CACHE (Risparmiata 1 chiamata API!)")
                return entry["data"]
        
        # 2. API Call (solo se non in cache)
        for attempt in range(1, max_retries + 1):
            try:
                result = self._query_trends(keyword)
                if result:
                    # Salva in cache
                    self.cache[keyword] = {
                        "timestamp": now,
                        "data": result
                    }
                    self.save_required = True
                    return result
                else:
                    logger.warning(f"Nessun dato Trends su SerpApi per '{keyword}'.")
                    # Salviamo in cache anche lo ZERO, cosi non sprechiamo API per ri-controllare i fallimenti
                    self.cache[keyword] = {"timestamp": now, "data": {"trend_score": 0.0, "is_breakout": False}}
                    self.save_required = True
                    return self.cache[keyword]["data"]
            except Exception as e:
                logger.error(f"Errore imprevisto su '{keyword}': {e}")
                if attempt < max_retries:
                    time.sleep(2)

        return {"trend_score": 0.0, "is_breakout": False}
        
    def __del__(self):
        if getattr(self, 'save_required', False):
            self._save_cache()