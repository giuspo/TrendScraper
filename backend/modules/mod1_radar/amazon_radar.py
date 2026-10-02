import logging
import urllib.parse
import time
import random
from typing import List, Dict, Any
from curl_cffi import requests

logger = logging.getLogger(__name__)

COMMERCIAL_TRIGGERS = [
    "attrezzi", "prodotti", "accessori", "kit", "set", "prezzo",
    "offerta", "migliore", "comprare", "acquistare", "migliori", "guanti",
    "vaso", "annaffiatoio", "cesoie", "concime", "sementi", "piante",
    "portatile", "wireless", "bluetooth", "usb", "smart", "led", "cover",
    "custodia", "supporto", "caricatore", "cavo", "stand", "borsa", "zaino",
    "olio", "crema", "siero", "maschera", "shampoo", "profumo", "regalo",
    "professionale", "automatico", "elettrico", "ricaricabile", "impermeabile",
    "bambini", "donna", "uomo", "telescopico", "manuale", "portatile",
]

STORE_BLACKLIST = [
    "amazon", "ikea", "lidl", "leroy merlin", "action", "temu", "decathlon",
    "obi", "bricofer", "brico", "tecnomat", "leroymerlin", "rituals",
    "shein", "aliexpress", "ebay", "zalando", "zara", "primark", "auchan",
    "carrefour", "esselunga", "conad", "euronics", "mediaworld", "unieuro",
    "service", "pro ", " pro", "srl", "vicino", "vicino a me", "in inglese", 
    "significato",
]

ALPHABET_LETTERS = list("acgkmoprstv")
COMMERCIAL_PREFIXES = ["kit", "set", "accessori", "migliori", "guanti", "attrezzi"]


class SmartGoogleAutocompleteRadar:
    def _query_autocomplete(self, query: str) -> List[str]:
        encoded = urllib.parse.quote(query)
        url = f"http://suggestqueries.google.com/complete/search?client=chrome&q={encoded}&hl=it"
        try:
            resp = requests.get(url, impersonate="chrome", timeout=10)
            data = resp.json()
            return data[1] if len(data) > 1 else []
        except Exception as e:
            logger.error(f"Errore Google Autocomplete per '{query}': {e}")
            return []

    def _is_valid_product_keyword(self, kw: str) -> bool:
        kw_lower = kw.lower()
        if any(store in kw_lower for store in STORE_BLACKLIST):
            return False
        
        # ORA E' RIGOROSO: DEVE contenere almeno un termine commerciale!
        has_commercial = any(t in kw_lower for t in COMMERCIAL_TRIGGERS)
        return has_commercial

    def scan(self, category: str = "all") -> List[Dict[str, Any]]:
        candidates = []
        search_term = "accessori" if category == "all" else category
        logger.info(f"Radar Alphabet Soup per: '{search_term}'...")

        found_keywords = set()

        for s in self._query_autocomplete(search_term):
            if "http" not in s and len(s.split()) <= 5:
                found_keywords.add(s)

        for letter in ALPHABET_LETTERS:
            time.sleep(random.uniform(0.3, 0.6))
            for s in self._query_autocomplete(f"{search_term} {letter}"):
                if "http" not in s and len(s.split()) <= 5:
                    found_keywords.add(s)

        for prefix in COMMERCIAL_PREFIXES:
            time.sleep(random.uniform(0.2, 0.5))
            for s in self._query_autocomplete(f"{prefix} {search_term}"):
                if "http" not in s and len(s.split()) <= 5:
                    found_keywords.add(s)

        for kw in found_keywords:
            if self._is_valid_product_keyword(kw):
                candidates.append({
                    "keyword": kw,
                    "source": "google_autocomplete_it",
                    "category": category,
                    "initial_traction_score": 100,
                    "raw_title": kw
                })

        logger.info(f"Trovate {len(candidates)} keyword prodotto per '{search_term}'")
        return candidates