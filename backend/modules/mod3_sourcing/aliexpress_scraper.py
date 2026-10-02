import logging
import urllib.parse
import re
from typing import Dict, Any
from curl_cffi import requests

logger = logging.getLogger(__name__)

class AliExpressScraper:
    def __init__(self):
        self.base_url = "https://it.aliexpress.com/w/wholesale-{}.html"
        
    def estimate_sourcing_cost(self, keyword: str) -> Dict[str, Any]:
        """Cerca il prodotto su AliExpress usando curl_cffi (Zero blocchi) e calcola il prezzo medio."""
        logger.info(f"Ricerca fornitori (AliExpress) per: {keyword}")
        
        # AliExpress formatta gli url con il + al posto degli spazi
        search_query = "+".join(keyword.split())
        url = self.base_url.format(urllib.parse.quote(search_query))
        
        try:
            resp = requests.get(url, impersonate='chrome', timeout=15)
            if resp.status_code != 200:
                logger.error(f"AliExpress ha risposto con codice {resp.status_code}")
                return {"estimated_cost_usd": 0.0, "suppliers_found": 0}
                
            html = resp.text
            
            # Regex infallibile per i prezzi: cerca cifre con virgola o punto seguite dal simbolo € o $
            # Esempio: "1,86 €" oppure "4.99$"
            prices_str = re.findall(r'(\d+[\.,]\d{2})\s*[€\$]', html)
            
            valid_prices = []
            for p in prices_str:
                try:
                    p_float = float(p.replace(',', '.'))
                    valid_prices.append(p_float)
                except ValueError:
                    pass
                    
            if not valid_prices:
                logger.warning("Nessun prezzo valido trovato nella pagina (forse non ci sono risultati per questa keyword).")
                return {"estimated_cost_usd": 0.0, "suppliers_found": 0}
                
            # Tagliamo gli outlier (10% superiori e 10% inferiori)
            valid_prices.sort()
            if len(valid_prices) >= 10:
                chop = max(1, len(valid_prices) // 10)
                core_prices = valid_prices[chop:-chop]
            else:
                core_prices = valid_prices
                
            avg_price = sum(core_prices) / len(core_prices)
            
            return {
                "estimated_cost_usd": round(avg_price, 2),
                "suppliers_found": len(valid_prices)
            }
            
        except Exception as e:
            logger.error(f"Errore nello scraping di AliExpress: {e}")
            return {"estimated_cost_usd": 0.0, "suppliers_found": 0}
