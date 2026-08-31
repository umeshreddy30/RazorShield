"""Tests for predict.py — smoke tests for the inference pipeline."""
import sys
import json
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

MODELS_READY = (ROOT_DIR / "models" / "best_model.json").exists()

DEMO_ORDER = {
    "order_value": 7999.0,
    "num_items": 2,
    "is_cod": 1,
    "customer_age_days": 12,
    "previous_orders": 3,
    "previous_delivered_orders": 1,
    "previous_rto_orders": 2,
    "previous_return_orders": 0,
    "previous_cancellations": 1,
    "customer_rto_rate": 0.667,
    "orders_last_7_days": 5,
    "orders_last_30_days": 8,
    "avg_previous_order_value": 1200.0,
    "current_vs_avg_order_value": 6.67,
    "pincode_rto_rate": 0.31,
    "address_completeness_score": 62.0,
    "customer_location_type": "TIER2",
    "delivery_attempt_history": 2.1,
    "order_hour": 23,
    "day_of_week": 6,
    "is_weekend": 1,
    "is_festival_period": 0,
    "product_category": "Electronics",
    "payment_method": "COD",
}


@pytest.mark.skipif(not MODELS_READY, reason="Models not trained yet — run python src/train.py first")
def test_score_output_structure():
    from predict import load_artifacts, score_order
    arts   = load_artifacts()
    result = score_order(DEMO_ORDER, arts)
    assert "risk_score"       in result
    assert "risk_probability" in result
    assert "risk_level"       in result
    assert "recommended_action" in result


@pytest.mark.skipif(not MODELS_READY, reason="Models not trained yet")
def test_score_ranges():
    from predict import load_artifacts, score_order
    arts   = load_artifacts()
    result = score_order(DEMO_ORDER, arts)
    assert 0 <= result["risk_score"] <= 100
    assert 0.0 <= result["risk_probability"] <= 1.0
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")


@pytest.mark.skipif(not MODELS_READY, reason="Models not trained yet")
def test_demo_order_is_high_risk():
    """The canonical demo order (COD, 2 previous RTOs, bad address) should be HIGH."""
    from predict import load_artifacts, score_order
    arts   = load_artifacts()
    result = score_order(DEMO_ORDER, arts)
    assert result["risk_level"] == "HIGH", (
        f"Expected HIGH for demo order, got {result['risk_level']} (score={result['risk_score']})"
    )


@pytest.mark.skipif(not MODELS_READY, reason="Models not trained yet")
def test_low_risk_order():
    """A clean UPI order with good history should score LOW."""
    from predict import load_artifacts, score_order
    arts = load_artifacts()
    safe_order = {
        "order_value": 999.0, "num_items": 1,
        "is_cod": 0, "customer_age_days": 730,
        "previous_orders": 25, "previous_delivered_orders": 24,
        "previous_rto_orders": 0, "previous_return_orders": 0,
        "previous_cancellations": 1, "customer_rto_rate": 0.0,
        "orders_last_7_days": 0, "orders_last_30_days": 2,
        "avg_previous_order_value": 1100.0, "current_vs_avg_order_value": 0.91,
        "pincode_rto_rate": 0.07, "address_completeness_score": 95.0,
        "customer_location_type": "METRO", "delivery_attempt_history": 1.05,
        "order_hour": 11, "day_of_week": 1, "is_weekend": 0, "is_festival_period": 0,
        "product_category": "Books", "payment_method": "UPI",
    }
    result = score_order(safe_order, arts)
    assert result["risk_level"] in ("LOW", "MEDIUM"), (
        f"Expected LOW/MEDIUM for safe order, got {result['risk_level']} (score={result['risk_score']})"
    )
