import logging
from typing import List, Dict, Any
from curl_cffi import requests
from .http_utils import get_base_headers, apply_jitter

logger = logging.getLogger(__name__)

class TikTokScanner:
    def __init__(self):
        # Endpoint fittizio/pubblico di Creative Center (varia nel tempo)
        # In scenari reali si adatta o si usano API non ufficiali stabili.
        self.api_url = "https://ads.tiktok.com/business/creativecenter/api/trend/hashtag/list"
        self.min_growth_percent = 40.0

    def scan(self) -> List[Dict[str, Any]]:
        """
        Interroga il TikTok Creative Center per hashtag in crescita.
        Poiché le API di TikTok sono altamente protette, usiamo curl_cffi con gestione errori gracefully.
        """
        candidates = []
        logger.info("Scansionando TikTok Creative Center...")
        
        try:
            apply_jitter(3.0, 5.0)
            
            # Prepariamo un payload di ricerca tipico del frontend di TikTok CC
            payload = {
                "period": 7, # ultimi 7 giorni
                "industry_id": "", 
                "sort_by": "popular",
                "page": 1,
                "limit": 50
            }
            
            headers = get_base_headers()
            headers["Content-Type"] = "application/json"
            headers["Referer"] = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pad/en"

            response = requests.post(
                self.api_url, 
                json=payload,
                headers=headers, 
                impersonate="chrome",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    hashtags = data.get("data", {}).get("list", [])
                    
                    for tag in hashtags:
                        # Esempio di struttura ipotetica restituita da TikTok
                        hashtag_name = tag.get("hashtag_name", "")
                        growth_rate = float(tag.get("growth_rate", 0.0))
                        views = tag.get("view_count", 0)
                        
                        if growth_rate >= self.min_growth_percent:
                            candidates.append({
                                "keyword": hashtag_name,
                                "source": "tiktok_creative_center",
                                "category": "trending_hashtag",
                                "initial_traction_score": int(views),
                                "growth_percent": growth_rate
                            })
                else:
                    logger.warning(f"TikTok API ha restituito un codice errore interno: {data.get('msg')}")
            else:
                logger.warning(f"TikTok API HTTP error: {response.status_code}")
                
        except Exception as e:
            # Fallback graceful: non facciamo crollare la pipeline se TikTok cambia endpoint
            logger.error(f"Errore durante lo scan di TikTok (le API potrebbero essere cambiate o servire un captcha): {e}")
            
        return candidates
