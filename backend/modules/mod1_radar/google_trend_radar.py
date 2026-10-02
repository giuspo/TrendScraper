import logging
from typing import List, Dict, Any
from pytrends.request import TrendReq
from .http_utils import apply_jitter

logger = logging.getLogger(__name__)

class TrendRadar:
    """Usa Google Trends 'Trending Searches' come Radar primario per aggirare i blocchi WAF."""
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        
    def scan(self) -> List[Dict[str, Any]]:
        candidates = []
        logger.info("Interrogando Google Trending Searches (Real-Time Network Data)...")
        try:
            apply_jitter(2.0, 4.0)
            # Prende le tendenze di ricerca odierne negli Stati Uniti
            trending_df = self.pytrends.trending_searches(pn='united_states')
            
            if not trending_df.empty:
                for idx, row in trending_df.iterrows():
                    keyword = str(row[0])
                    # Evitiamo nomi troppo lunghi o strani
                    if len(keyword.split()) <= 3:
                        candidates.append({
                            "keyword": keyword,
                            "source": "google_trending_searches",
                            "category": "general",
                            "initial_traction_score": 100 - idx, # Punteggio basato sul rank
                            "raw_title": keyword
                        })
        except Exception as e:
            logger.error(f"Errore nello scan di Google Trends Radar: {e}")
            
        return candidates
