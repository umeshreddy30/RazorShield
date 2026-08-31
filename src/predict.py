"""
RazorShield — Inference
=========================
Loads the best trained model and scores a single order dictionary.

The risk score (0–100) comes entirely from the trained ML model's
predict_proba() output — no hardcoded rules.

Usage (as module):
    from predict import load_artifacts, score_order
    artifacts = load_artifacts()
    result = score_order(order_dict, artifacts)

Usage (CLI — for quick smoke test):
    python src/predict.py
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from preprocessing import FEATURE_COLUMNS, CATEGORICAL_FEATURES


# ---------------------------------------------------------------------------
# Artifact loader (cached by caller)
# ---------------------------------------------------------------------------

def load_artifacts(model_name: str | None = None) -> dict:
    """
    Load model, encoders, and metadata from disk.

    Returns a dict with:
        model_dict  : the model bundle (includes .model, .scaler, .base_model)
        encoders    : dict of LabelEncoders
        meta        : best_model.json contents
        model_name  : which model is active
    """
    models_dir = ROOT_DIR / "models"

    with open(models_dir / "best_model.json") as f:
        meta = json.load(f)

    if model_name is None:
        model_name = meta["best_model"]

    with open(models_dir / f"{model_name}.pkl", "rb") as f:
        model_dict = pickle.load(f)

    with open(models_dir / "encoders.pkl", "rb") as f:
        encoders = pickle.load(f)

    return {
        "model_dict": model_dict,
        "encoders":   encoders,
        "meta":       meta,
        "model_name": model_name,
    }


# ---------------------------------------------------------------------------
# Risk label helpers
# ---------------------------------------------------------------------------

_RISK_LEVELS = {
    "LOW":    (0,  30),
    "MEDIUM": (31, 70),
    "HIGH":   (71, 100),
}

_ACTIONS = {
    "LOW":    "PROCEED_NORMALLY",
    "MEDIUM": "RECOMMEND_VERIFICATION",
    "HIGH":   "VERIFY_BEFORE_FULFILLMENT",
}

_ACTION_LABELS = {
    "LOW":    "✅ Proceed normally",
    "MEDIUM": "⚠️ Recommend customer / order verification",
    "HIGH":   "🚨 Manual review required before fulfillment",
}


def _risk_level(score: int) -> str:
    if score <= 30:
        return "LOW"
    elif score <= 70:
        return "MEDIUM"
    return "HIGH"


# ---------------------------------------------------------------------------
# Single-order scorer
# ---------------------------------------------------------------------------

def score_order(order_dict: dict, artifacts: dict) -> dict:
    """
    Score one order dict and return a structured prediction response.

    Parameters
    ----------
    order_dict : dict with the same keys as the feature columns
    artifacts  : output of load_artifacts()

    Returns
    -------
    {
        risk_score:         int   (0–100)
        risk_probability:   float (0.0–1.0)
        risk_level:         str   (LOW / MEDIUM / HIGH)
        recommended_action: str
        action_label:       str   (human readable)
    }
    """
    model_dict = artifacts["model_dict"]
    encoders   = artifacts["encoders"]

    df = pd.DataFrame([order_dict])

    # Encode categoricals
    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            le      = encoders[col]
            known   = set(le.classes_)
            val_str = str(df[col].iloc[0])
            df[f"{col}_encoded"] = le.transform([val_str])[0] if val_str in known else 0

    # Build feature matrix
    X = df[FEATURE_COLUMNS].values.astype(float)

    if model_dict.get("needs_scaling") and model_dict.get("scaler") is not None:
        X = model_dict["scaler"].transform(X)

    prob       = float(model_dict["model"].predict_proba(X)[0, 1])
    risk_score = int(round(prob * 100))
    level      = _risk_level(risk_score)

    return {
        "risk_score":         risk_score,
        "risk_probability":   round(prob, 4),
        "risk_level":         level,
        "recommended_action": _ACTIONS[level],
        "action_label":       _ACTION_LABELS[level],
    }


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    demo_order = {
        "order_value":                7999,
        "num_items":                  2,
        "is_cod":                     1,
        "customer_age_days":          12,
        "previous_orders":            3,
        "previous_delivered_orders":  1,
        "previous_rto_orders":        2,
        "previous_return_orders":     0,
        "previous_cancellations":     1,
        "customer_rto_rate":          0.667,
        "orders_last_7_days":         5,
        "orders_last_30_days":        8,
        "avg_previous_order_value":   1200,
        "current_vs_avg_order_value": 6.67,
        "pincode_rto_rate":           0.31,
        "address_completeness_score": 62,
        "customer_location_type":     "TIER2",
        "delivery_attempt_history":   2.1,
        "order_hour":                 23,
        "day_of_week":                6,
        "is_weekend":                 1,
        "is_festival_period":         0,
        "product_category":           "Electronics",
        "payment_method":             "COD",
    }

    arts = load_artifacts()
    result = score_order(demo_order, arts)
    print(json.dumps(result, indent=2))
