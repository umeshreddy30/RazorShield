"""
RazorShield — Business Cost Model
====================================
Translates model predictions into ₹ impact for a merchant.

Configurable cost parameters:
  C_rto  = ₹350  (default) — cost of each missed RTO
  C_ver  = ₹30   (default) — cost of verifying each flagged order

Exported by: streamlit_app.py, evaluate.py
"""

from __future__ import annotations

import numpy as np


def compute_business_impact(
    y_true:            np.ndarray,
    y_prob:            np.ndarray,
    threshold:         float,
    rto_cost:          float = 350.0,
    verification_cost: float = 30.0,
) -> dict:
    """
    Compute merchant financial impact at a given classification threshold.

    Parameters
    ----------
    y_true            : ground-truth labels (0/1)
    y_prob            : model RTO probabilities (0.0–1.0)
    threshold         : classification cutoff
    rto_cost          : ₹ lost per undetected RTO order
    verification_cost : ₹ cost per flagged order (ops + customer friction)

    Returns
    -------
    dict with keys:
        total_orders, total_rto, rto_rate,
        baseline_loss,    ← total loss if no model is used
        model_loss,       ← expected loss with model at this threshold
        loss_prevented,   ← TP × rto_cost
        fp_cost,          ← FP × verification_cost
        net_benefit,      ← baseline_loss - model_loss
        tp, fp, fn, tn,
        rto_cost, verification_cost, threshold
    """
    y_pred = (y_prob >= threshold).astype(int)

    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())

    total_orders = len(y_true)
    total_rto    = int(y_true.sum())

    baseline_loss  = total_rto * rto_cost
    loss_prevented = tp * rto_cost
    fp_cost        = fp * verification_cost
    model_loss     = fn * rto_cost + (tp + fp) * verification_cost
    net_benefit    = baseline_loss - model_loss

    return {
        "total_orders":     total_orders,
        "total_rto":        total_rto,
        "rto_rate":         float(total_rto / max(total_orders, 1)),
        "baseline_loss":    float(baseline_loss),
        "model_loss":       float(model_loss),
        "loss_prevented":   float(loss_prevented),
        "fp_cost":          float(fp_cost),
        "net_benefit":      float(net_benefit),
        "tp":               tp,
        "fp":               fp,
        "fn":               fn,
        "tn":               tn,
        "rto_cost":         rto_cost,
        "verification_cost": verification_cost,
        "threshold":        float(threshold),
    }


def sweep_thresholds_business(
    y_true:            np.ndarray,
    y_prob:            np.ndarray,
    rto_cost:          float = 350.0,
    verification_cost: float = 30.0,
) -> list[dict]:
    """Return per-threshold business metrics for chart rendering."""
    results = []
    for t in np.arange(0.10, 0.91, 0.05):
        impact = compute_business_impact(
            y_true, y_prob, float(t), rto_cost, verification_cost
        )
        prec = impact["tp"] / max(impact["tp"] + impact["fp"], 1)
        results.append({
            "threshold":      round(float(t), 2),
            "net_benefit":    impact["net_benefit"],
            "loss_prevented": impact["loss_prevented"],
            "fp_cost":        impact["fp_cost"],
            "precision":      prec,
            "recall":         impact["tp"] / max(impact["tp"] + impact["fn"], 1),
            "flagged_orders": impact["tp"] + impact["fp"],
        })
    return results
