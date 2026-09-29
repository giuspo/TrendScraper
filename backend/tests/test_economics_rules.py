import pytest
from core.rules_engine import RulesEngine
from modules.mod5_economics.calculator import FBACalculator
from core.scoring import ScoringEngine

def test_rules_engine_default():
    engine = RulesEngine(config_path="config/rules.yaml", active_profile="default")
    
    # Test valid product
    is_valid, reason = engine.check_compliance(
        weight_g=400,
        dimensions_cm=[20, 15, 5],
        is_220v=False,
        battery_mah=0,
        title_or_desc="Portatile stand per laptop in alluminio"
    )
    assert is_valid is True
    assert reason == ""

    # Test invalid weight
    is_valid, reason = engine.check_compliance(
        weight_g=1000,
        dimensions_cm=[20, 15, 5],
        is_220v=False,
        battery_mah=0,
        title_or_desc="Stand pesante"
    )
    assert is_valid is False
    assert "Peso eccedente" in reason

    # Test banned keyword
    is_valid, reason = engine.check_compliance(
        weight_g=100,
        dimensions_cm=[10, 5, 5],
        is_220v=False,
        battery_mah=0,
        title_or_desc="Crema viso idratante"
    )
    assert is_valid is False
    assert "crema" in reason

def test_fba_calculator():
    # Buybox: 29.90, Costo Fabbrica: 4.50, Peso: 250g
    results = FBACalculator.simulate_margins(
        buybox_price=29.90,
        factory_cost_fob=4.50,
        weight_g=250
    )
    
    assert results["buybox_price_eur"] == 29.90
    assert results["fba_fee_eur"] == 4.50  # 250g -> 4.50
    # Net revenue = 29.90 / 1.22 = 24.508
    assert abs(results["net_revenue_eur"] - 24.51) < 0.1
    # Referral fee = 24.508 * 0.15 = 3.676
    assert abs(results["referral_fee_eur"] - 3.68) < 0.1
    # Dazio = 4.50 * 0.04 = 0.18
    # Landed cost = 4.50 + 1.20 + 0.18 = 5.88
    assert abs(results["landed_cost_eur"] - 5.88) < 0.1

def test_scoring_engine():
    score = ScoringEngine.calculate_opportunity_score(
        trend_score_0_100=90,
        comp_score_0_100=80,
        margin_percent=25,
        weight_g=150,
        compliance_score_0_100=100
    )
    
    badge = ScoringEngine.get_badge_color(score)
    assert score > 0
    assert badge in ["Verde", "Giallo", "Rosso"]
