import logging
import time
from typing import Dict, Any
from curl_cffi import requests

logger = logging.getLogger(__name__)


class TrendEngine:
    def __init__(self, geo: str = "IT"):
        self.geo = geo
        # Sostituire pytrends con la API Key di SerpApi fornita dall'utente
        self.api_key = "7986c654ac1aded6bb379b04a2ff4d21dd55ba45b10689d9a60e5b1cc38d31d8"
        self.base_url = "https://serpapi.com/search.json"

    def _query_trends(self, keyword: str) -> dict:
        """Interroga Google Trends in modo professionale tramite SerpApi."""
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
            
        # Estraiamo i valori (da 0 a 100) per ogni giorno
        values = []
        for point in timeline:
            if "values" in point and len(point["values"]) > 0:
                val = point["values"][0].get("extracted_value", 0)
                values.append(val)
                
        if not values:
            return {}
            
        # Prendiamo gli ultimi 14 giorni
        recent_values = values[-14:]
        avg_score = sum(recent_values) / len(recent_values)
        
        # Breakout: se l'ultimo valore è > 1.5x della media
        is_breakout = values[-1] > (avg_score * 1.5)
        
        return {"trend_score": round(avg_score, 2), "is_breakout": is_breakout}

    def evaluate_keyword(self, keyword: str, max_retries: int = 3) -> dict:
        """
        Valuta il trend di una keyword su Google Trends via SerpApi.
        Essendo un'API pro, non servono trucchetti come accorciare la keyword.
        """
        for attempt in range(1, max_retries + 1):
            try:
                result = self._query_trends(keyword)
                if result:
                    return result
                else:
                    logger.warning(f"Nessun dato Trends su SerpApi per '{keyword}'.")
                    return {"trend_score": 0.0, "is_breakout": False}
            except Exception as e:
                logger.error(f"Errore imprevisto su '{keyword}': {e}")
                if attempt < max_retries:
                    time.sleep(2)

        return {"trend_score": 0.0, "is_breakout": False}