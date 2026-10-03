import json
import logging
import os
import re
import statistics
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, List

from curl_cffi import requests

logger = logging.getLogger(__name__)

CACHE_TTL_DAYS = 30
MIN_SECONDS_BETWEEN_REQUESTS = 45  # approccio gentile anti-ban
BLOCK_COOLDOWN_MINUTES = 60        # dopo un blocco non riproviamo per un'ora


class AlibabaScraper:
    """
    Verifica B2B su Alibaba.com (prezzi wholesale a range + MOQ).
    Approccio gentile: 1 richiesta ogni 45s, cache 30 giorni, stop dopo un blocco.
    Se Alibaba blocca ritorna blocked=True: NESSUN dato inventato.
    """

    def __init__(self):
        base = os.path.dirname(__file__)
        self.cache_file = os.path.join(base, "alibaba_cache.json")
        self.state_file = os.path.join(base, "alibaba_state.json")
        self.cache = self._load(self.cache_file)
        self.state = self._load(self.state_file)

    @staticmethod
    def _load(path: str) -> dict:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @staticmethod
    def _save(path: str, data: dict):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Errore salvataggio {path}: {e}")

    def _in_cooldown(self) -> bool:
        ts = self.state.get("blocked_at")
        if not ts:
            return False
        return datetime.now() - datetime.fromisoformat(ts) < timedelta(minutes=BLOCK_COOLDOWN_MINUTES)

    def _throttle(self):
        last = self.state.get("last_request")
        if last:
            elapsed = (datetime.now() - datetime.fromisoformat(last)).total_seconds()
            if elapsed < MIN_SECONDS_BETWEEN_REQUESTS:
                time.sleep(MIN_SECONDS_BETWEEN_REQUESTS - elapsed)

    @staticmethod
    def _parse(html: str) -> Dict[str, Any]:
        # Normalizza gli escape unicode del JSON incorporato (\u20AC -> euro)
        text = html.replace("\\u20AC", "€").replace("\\u0024", "$")
        ranges: List[tuple] = []
        for m in re.finditer(r"€\s?(\d+(?:[.,]\d+)?)\s*(?:-|~)\s*€?\s?(\d+(?:[.,]\d+)?)", text):
            lo, hi = (float(x.replace(",", ".")) for x in m.groups())
            if 0 < lo <= hi:
                ranges.append((lo, hi))
        singles = [float(x.replace(",", ".")) for x in
                   re.findall(r"€\s?(\d+(?:[.,]\d+)?)(?![\d.,]*\s*(?:-|~))", text)]
        moqs = [int(x) for x in re.findall(r"Min\.?\s*order:?\s*(\d+)\s*(?:piece|pc|unit|set)", text, re.I)]

        if not ranges and not singles:
            return {}
        lows = [r[0] for r in ranges] + singles
        highs = [r[1] for r in ranges] + singles
        return {
            "wholesale_min": round(statistics.median(lows), 2),
            "wholesale_max": round(statistics.median(highs), 2),
            "moq_typical": int(statistics.median(moqs)) if moqs else None,
            "listings_found": len(ranges) + len(singles),
        }

    def estimate_wholesale(self, keyword: str) -> Dict[str, Any]:
        key = keyword.strip().lower()

        entry = self.cache.get(key)
        if entry and datetime.now() - datetime.fromisoformat(entry["timestamp"]) < timedelta(days=CACHE_TTL_DAYS):
            return {**entry["data"], "from_cache": True}

        if self._in_cooldown():
            return {"blocked": True, "reason": "cooldown dopo blocco recente"}

        self._throttle()
        url = ("https://www.alibaba.com/trade/search?SearchText="
               f"{urllib.parse.quote(keyword)}&IndexArea=product_en")
        try:
            resp = requests.get(url, impersonate="chrome", timeout=25)
        except Exception as e:
            logger.error(f"Alibaba errore rete: {e}")
            return {"blocked": False, "error": str(e)[:100]}
        finally:
            self.state["last_request"] = datetime.now().isoformat()
            self._save(self.state_file, self.state)

        html = resp.text
        if resp.status_code != 200 or "Min. order" not in html:
            # pagina 'punish' / anti-bot: ci fermiamo, niente dati inventati
            self.state["blocked_at"] = datetime.now().isoformat()
            self._save(self.state_file, self.state)
            logger.warning("Alibaba ha risposto con pagina anti-bot. Cooldown 60 minuti.")
            return {"blocked": True, "reason": "anti-bot Alibaba"}

        data = self._parse(html)
        if not data:
            return {"blocked": False, "error": "nessun prezzo in EUR trovato"}

        data["blocked"] = False
        self.cache[key] = {"timestamp": datetime.now().isoformat(), "data": data}
        self._save(self.cache_file, self.cache)
        return data