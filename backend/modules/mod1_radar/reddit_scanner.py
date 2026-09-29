import logging
from typing import List, Dict, Any
from curl_cffi import requests
from .http_utils import get_base_headers, apply_jitter

logger = logging.getLogger(__name__)

class RedditScanner:
    def __init__(self):
        self.subreddits = ["desksetup", "organization", "gadgets", "toddlers"]
        self.intent_keywords = [
            "looking for", "problem with", "best alternative", 
            "where to buy", "recommendation", "need help finding",
            "must have", "accessory for"
        ]
        self.min_upvotes = 50

    def scan(self) -> List[Dict[str, Any]]:
        """Scansiona i subreddit target tramite l'endpoint pubblico .json"""
        candidates = []
        
        for sub in self.subreddits:
            logger.info(f"Scansionando r/{sub}...")
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=100"
            
            try:
                # Applica polite jitter
                apply_jitter(3.0, 6.0)
                
                # impersonate="chrome" usa la fingerprint TLS di Chrome reale
                response = requests.get(
                    url, 
                    headers=get_base_headers(), 
                    impersonate="chrome",
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get("data", {}).get("children", [])
                    
                    for post in posts:
                        post_data = post.get("data", {})
                        title = post_data.get("title", "")
                        selftext = post_data.get("selftext", "")
                        ups = post_data.get("ups", 0)
                        
                        if ups >= self.min_upvotes:
                            full_text = f"{title} {selftext}".lower()
                            
                            # Verifica intent keywords
                            if any(kw in full_text for kw in self.intent_keywords):
                                candidates.append({
                                    "keyword": title[:100],  # Titolo accorciato usato come keyword candidata
                                    "source": f"reddit/r/{sub}",
                                    "category": sub,
                                    "initial_traction_score": ups,
                                    "raw_title": title
                                })
                else:
                    logger.warning(f"Reddit API error su r/{sub}: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Errore durante lo scan di r/{sub}: {e}")
                
        return candidates
