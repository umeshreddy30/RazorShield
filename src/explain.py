"""
RazorShield — Explainability
==============================
Generates SHAP-based explanations for individual predictions.

Strategy by model type:
  - Random Forest  → shap.TreeExplainer (exact, fast)
  - LightGBM       → shap.TreeExplainer (exact, fast)
  - Logistic Reg   → coefficient × feature_value (linear attribution)

SHAP values from base (uncalibrated) models are used for directional
attribution. This is appropriate because calibration is monotone — it
doesn't change feature direction, only the probability scale.

Exported by: streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from preprocessing import CATEGORICAL_FEATURES, FEATURE_COLUMNS, FEATURE_DISPLAY_NAMES


# ---------------------------------------------------------------------------
# Core explainer
# ---------------------------------------------------------------------------

def explain_prediction(
    order_dict:  dict,
    artifacts:   dict,
    n_top:       int = 8,
) -> dict:
    """
    Compute feature attributions for a single order.

    Returns
    -------
    {
        top_factors      : list[str]  — formatted top contributing factors
        feature_impacts  : list[dict] — {feature, display_name, shap_value, raw_value}
        explainer_type   : str        — which method was used
    }
    """
    model_dict = artifacts["model_dict"]
    encoders   = artifacts["encoders"]
    model_type = model_dict.get("model_type", "unknown")
    base_model = model_dict.get("base_model")

    # Build feature row
    df = pd.DataFrame([order_dict])
    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            le      = encoders[col]
            known   = set(le.classes_)
            val_str = str(df[col].iloc[0])
            df[f"{col}_encoded"] = le.transform([val_str])[0] if val_str in known else 0

    X = df[FEATURE_COLUMNS].values.astype(float)

    # Optionally scale (for LR)
    X_for_shap = X.copy()
    if model_dict.get("needs_scaling") and model_dict.get("scaler") is not None:
        X_for_shap = model_dict["scaler"].transform(X_for_shap)

    # --------------- SHAP / attribution ---------------
    shap_values = np.zeros(len(FEATURE_COLUMNS))
    explainer_type = "none"

    if base_model is not None and model_type in ("random_forest", "lightgbm"):
        try:
            import shap
            explainer  = shap.TreeExplainer(base_model)
            sv         = explainer.shap_values(X)
            if isinstance(sv, list):          # RF returns list[class_0, class_1]
                shap_values = sv[1][0]
            elif sv.ndim == 3:               # some lgb versions
                shap_values = sv[0, :, 1]
            else:
                shap_values = sv[0]
            explainer_type = "shap_tree"
        except Exception:
            shap_values    = _fallback_lr_attribution(X_for_shap, model_dict)
            explainer_type = "fallback_linear"

    elif model_type == "logistic_regression" and base_model is not None:
        try:
            import shap
            bg_path = ROOT_DIR / "models" / "shap_background.npy"
            if bg_path.exists():
                bg = np.load(bg_path)
                if model_dict.get("needs_scaling") and model_dict.get("scaler") is not None:
                    bg = model_dict["scaler"].transform(bg)
                explainer  = shap.LinearExplainer(base_model, bg)
                shap_values = explainer.shap_values(X_for_shap)[0]
                explainer_type = "shap_linear"
            else:
                shap_values    = _fallback_lr_attribution(X_for_shap, model_dict)
                explainer_type = "fallback_linear"
        except Exception:
            shap_values    = _fallback_lr_attribution(X_for_shap, model_dict)
            explainer_type = "fallback_linear"
    else:
        shap_values    = _fallback_lr_attribution(X_for_shap, model_dict)
        explainer_type = "fallback_linear"

    # --------------- Format output ---------------
    raw_values = X[0]
    feature_impacts = []
    for i, feat in enumerate(FEATURE_COLUMNS):
        display_name = FEATURE_DISPLAY_NAMES.get(feat, feat)
        impact       = float(shap_values[i]) if i < len(shap_values) else 0.0
        raw_val      = float(raw_values[i])   if i < len(raw_values)  else 0.0
        feature_impacts.append({
            "feature":      feat,
            "display_name": display_name,
            "shap_value":   round(impact, 4),
            "raw_value":    round(raw_val, 4),
        })

    feature_impacts.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

    top_factors = []
    for fi in feature_impacts[:n_top]:
        direction = "↑ Increases risk" if fi["shap_value"] > 0 else "↓ Reduces risk"
        top_factors.append(f"{direction}: {fi['display_name']}")

    return {
        "top_factors":     top_factors,
        "feature_impacts": feature_impacts[:n_top],
        "explainer_type":  explainer_type,
    }


def _fallback_lr_attribution(X_scaled: np.ndarray, model_dict: dict) -> np.ndarray:
    """Linear attribution: coefficient × feature_value (for LR / fallback)."""
    base = model_dict.get("base_model")
    if base is None:
        return np.zeros(X_scaled.shape[1])
    coef = getattr(base, "coef_", None)
    if coef is None:
        return np.zeros(X_scaled.shape[1])
    coef_1d = coef[0] if coef.ndim == 2 else coef
    return (coef_1d * X_scaled[0])
