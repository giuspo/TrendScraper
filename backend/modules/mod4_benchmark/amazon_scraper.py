import logging
import urllib.parse
import re
import time
from typing import Dict, Any
from curl_cffi import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class AmazonBenchmarkEngine:
    def __init__(self):
        self.base_url = "https://www.amazon.it/s?k="
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def estimate_selling_price(self, keyword: str, max_retries: int = 3) -> Dict[str, Any]:
        logger.info(f"Ricerca prezzo di mercato (Amazon) per: {keyword}")
        url = self.base_url + urllib.parse.quote(keyword)
        
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, impersonate='chrome', headers=self.headers, timeout=15)
                
                if resp.status_code == 503 or "captcha" in resp.text.lower():
                    if attempt < max_retries:
                        wait_time = attempt * 5
                        logger.warning(f"Amazon Bot Protection (Captcha) su '{keyword}'. Ritento tra {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Impossibile superare il Captcha di Amazon per '{keyword}'.")
                        return {"estimated_price_eur": 0.0, "competitors_found": 0}
                
                if resp.status_code != 200:
                    logger.error(f"Amazon ha restituito status code {resp.status_code}")
                    return {"estimated_price_eur": 0.0, "competitors_found": 0}
                    
                soup = BeautifulSoup(resp.text, 'html.parser')
                price_elements = soup.select('.a-price .a-offscreen')
                
                valid_prices = []
                for p in price_elements:
                    text = p.text.strip()
                    match = re.search(r'(\d+[\.,]\d{2})', text)
                    if match:
                        price_float = float(match.group(1).replace(',', '.'))
                        valid_prices.append(price_float)
                
                if not valid_prices:
                    if attempt < max_retries:
                        wait_time = attempt * 5
                        logger.warning(f"Nessun prezzo trovato su Amazon per '{keyword}' (possibile pagina vuota/blocco). Ritento tra {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {"estimated_price_eur": 0.0, "competitors_found": 0}
                    
                valid_prices.sort()
                if len(valid_prices) >= 5:
                    chop = max(1, len(valid_prices) // 5)
                    core_prices = valid_prices[chop:-chop]
                else:
                    core_prices = valid_prices
                    
                avg_price = sum(core_prices) / len(core_prices)
                
                return {
                    "estimated_price_eur": round(avg_price, 2),
                    "competitors_found": len(valid_prices)
                }
                
            except Exception as e:
                if attempt < max_retries:
                    wait_time = attempt * 5
                    logger.warning(f"Errore su Amazon ('{keyword}'): {e}. Ritento tra {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Errore definitivo nello scraping di Amazon: {e}")
                    return {"estimated_price_eur": 0.0, "competitors_found": 0}
                    
        return {"estimated_price_eur": 0.0, "competitors_found": 0}
