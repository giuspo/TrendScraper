import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from modules.mod2_trend.trend_engine import TrendEngine

def test_trend_engine_math_logic():
    # Mockiamo la classe TrendReq in modo che l'init non faccia chiamate web
    with patch("modules.mod2_trend.trend_engine.TrendReq"):
        engine = TrendEngine()
        
        # Creiamo un DataFrame mock che simula la risposta di pytrends
        dates = pd.date_range(start="2023-01-01", periods=90)
        
        # Caso 1: Trend Piatto
        flat_data = [50] * 90
        df_flat = pd.DataFrame({"laptop stand": flat_data}, index=dates)
        
        # Caso 2: Breakout
        breakout_data = [20] * 76 + [90] * 14
        df_breakout = pd.DataFrame({"fidget spinner": breakout_data}, index=dates)
        
        mock_pytrends = engine.pytrends
        
        with patch("modules.mod2_trend.trend_engine.apply_jitter"):
            
            # Test piatto
            mock_pytrends.interest_over_time.return_value = df_flat
            res_flat = engine.evaluate_keyword("laptop stand")
            
            assert res_flat["recent_avg"] == 50.0
            assert res_flat["slope"] == 0.0
            assert res_flat["is_breakout"] is False
            assert res_flat["trend_score"] == 50.0
            
            # Test breakout
            mock_pytrends.interest_over_time.return_value = df_breakout
            res_breakout = engine.evaluate_keyword("fidget spinner")
            
            assert res_breakout["recent_avg"] == 90.0
            assert res_breakout["slope"] > 0
            assert res_breakout["is_breakout"] is True
            assert res_breakout["trend_score"] == 100.0

def test_trend_engine_empty():
    with patch("modules.mod2_trend.trend_engine.TrendReq"):
        engine = TrendEngine()
        mock_pytrends = engine.pytrends
        
        with patch("modules.mod2_trend.trend_engine.apply_jitter"):
            mock_pytrends.interest_over_time.return_value = pd.DataFrame()
            res_empty = engine.evaluate_keyword("unknown_item")
            
            assert res_empty["trend_score"] == 0.0

