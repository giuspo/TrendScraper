import logging
from typing import List, Dict, Any
from .reddit_scanner import RedditScanner
from .tiktok_scanner import TikTokScanner
from .facebook_scanner import FacebookScanner

logger = logging.getLogger(__name__)

class RadarEngine:
    def __init__(self):
        self.reddit_scanner = RedditScanner()
        self.tiktok_scanner = TikTokScanner()
        self.facebook_scanner = FacebookScanner()

    def run_scan(self) -> List[Dict[str, Any]]:
        """Esegue tutti gli scanner in sequenza e aggrega le Candidate Keywords"""
        all_candidates = []
        
        # 1. Scan Reddit
        logger.info("Inizio scansione Reddit...")
        reddit_results = self.reddit_scanner.scan()
        logger.info(f"Trovate {len(reddit_results)} idee da Reddit.")
        all_candidates.extend(reddit_results)
        
        # 2. Scan TikTok
        logger.info("Inizio scansione TikTok...")
        tiktok_results = self.tiktok_scanner.scan()
        logger.info(f"Trovate {len(tiktok_results)} idee da TikTok.")
        all_candidates.extend(tiktok_results)
        
        # 3. Scan Facebook Advisor
        logger.info("Inizio scansione Facebook Advisor...")
        fb_results = self.facebook_scanner.scan()
        logger.info(f"Trovate {len(fb_results)} idee da Facebook.")
        all_candidates.extend(fb_results)
        
        # Rimuoviamo eventuali duplicati grezzi basandoci sulla keyword esatta
        unique_candidates = {}
        for cand in all_candidates:
            kw = cand["keyword"].lower().strip()
            if kw and kw not in unique_candidates:
                unique_candidates[kw] = cand
                
        final_list = list(unique_candidates.values())
        logger.info(f"Radar Idee terminato. Totale candidati unici estratti: {len(final_list)}")
        return final_list

