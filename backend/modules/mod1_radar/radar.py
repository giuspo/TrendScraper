import logging
from typing import List, Dict, Any
from .amazon_radar import SmartGoogleAutocompleteRadar

logger = logging.getLogger(__name__)

class RadarEngine:
    def __init__(self):
        self.scanners = [SmartGoogleAutocompleteRadar()]

    def run_scan(self, category: str = "all") -> List[Dict[str, Any]]:
        results = []
        for scanner in self.scanners:
            try:
                data = scanner.scan(category=category)
                if data:
                    results.extend(data)
            except Exception as e:
                logger.error(f"Errore nello scanner {scanner.__class__.__name__}: {e}")
        return results