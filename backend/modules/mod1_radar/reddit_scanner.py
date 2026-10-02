import logging
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
import time

logger = logging.getLogger(__name__)

class RedditScanner:
    def __init__(self):
        self.subreddits = ["desksetup", "gadgets", "macsetups", "EDC"]
        self.intent_keywords = [
            "keyboard", "mouse", "chair", "desk", "monitor", "cable", 
            "usb", "charger", "laptop", "light", "lamp", "stand", 
            "bag", "backpack", "wallet", "watch", "case", "setup",
            "hub", "dock", "organizer", "shelf", "speaker", "audio", "screen", "pad", "mat"
        ]
        self.min_upvotes = 0

    def scan(self) -> List[Dict[str, Any]]:
        candidates = []
        logger.info("Avvio browser Headless (Playwright) per Reddit Stealth Scraping...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context(viewport={"width": 1920, "height": 1080})
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                for sub in self.subreddits:
                    url = f"https://old.reddit.com/r/{sub}/hot/"
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        time.sleep(2)
                        posts = page.query_selector_all(".thing")
                        for post in posts:
                            title_elem = post.query_selector("a.title")
                            score_elem = post.query_selector(".score.unvoted")
                            if title_elem and score_elem:
                                title = title_elem.inner_text()
                                score_text = score_elem.inner_text()
                                try:
                                    if "k" in score_text.lower():
                                        ups = int(float(score_text.lower().replace("k", "")) * 1000)
                                    else:
                                        ups = int(score_text) if score_text.isdigit() else 0
                                except ValueError:
                                    ups = 0
                                if ups >= self.min_upvotes:
                                    full_text = title.lower()
                                    matched_kws = [kw for kw in self.intent_keywords if kw in full_text]
                                    if matched_kws:
                                        candidates.append({
                                            "keyword": matched_kws[0],
                                            "source": f"reddit/r/{sub}",
                                            "category": sub,
                                            "initial_traction_score": ups,
                                            "raw_title": title
                                        })
                    except Exception as e:
                        logger.error(f"Errore su r/{sub}: {e}")
                browser.close()
        except Exception as e:
            pass
        return candidates
