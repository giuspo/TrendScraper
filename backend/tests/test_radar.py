import pytest
from unittest.mock import patch, MagicMock
from modules.mod1_radar.reddit_scanner import RedditScanner
from modules.mod1_radar.tiktok_scanner import TikTokScanner
from modules.mod1_radar.radar import RadarEngine

def test_reddit_scanner_logic():
    scanner = RedditScanner()
    scanner.subreddits = ["testsub"] # usiamo solo un sub per il test
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Looking for a great laptop stand",
                        "selftext": "Any recommendations?",
                        "ups": 150
                    }
                },
                {
                    "data": {
                        "title": "Just a normal post",
                        "selftext": "Nothing to see here",
                        "ups": 10
                    }
                }
            ]
        }
    }

    with patch("modules.mod1_radar.reddit_scanner.requests.get", return_value=mock_response):
        with patch("modules.mod1_radar.reddit_scanner.apply_jitter"): # Disabilitiamo il time.sleep nel test
            results = scanner.scan()
            
    assert len(results) == 1
    assert "laptop stand" in results[0]["keyword"]
    assert results[0]["initial_traction_score"] == 150

def test_radar_engine_aggregation():
    engine = RadarEngine()
    
    # Mock dei risultati dei singoli scanner
    with patch.object(engine.reddit_scanner, "scan", return_value=[{"keyword": "Desk mat", "source": "reddit"}]):
        with patch.object(engine.tiktok_scanner, "scan", return_value=[{"keyword": "Led Lights", "source": "tiktok"}]):
            with patch.object(engine.facebook_scanner, "scan", return_value=[{"keyword": "posture corrector", "source": "facebook_ad_library"}]):
                all_candidates = engine.run_scan()
            
    assert len(all_candidates) == 3
    keywords = [c["keyword"] for c in all_candidates]
    assert "Desk mat" in keywords
    assert "Led Lights" in keywords
    assert "posture corrector" in keywords
