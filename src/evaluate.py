"""
RazorShield — Evaluation
=========================
Computes all metrics on validation or test split.
Saves a comprehensive JSON results file for the dashboard to load.

Usage:
    python src/evaluate.py                 # evaluates on validation
    python src/evaluate.py --split test    # evaluates on held-out test set
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import yaml
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from preprocessing import get_X, get_y
from cost_model import compute_business_impact

import pandas as pd


def load_config() -> dict:
    with open(ROOT_DIR / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Core metric functions (importable by other modules)
# ---------------------------------------------------------------------------

def evaluate_model(
    y_true:    np.ndarray,
    y_prob:    np.ndarray,
    threshold: float = 0.50,
) -> dict:
    """Compute classification metrics at a given threshold."""
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    return {
        "prauc":     float(average_precision_score(y_true, y_prob)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall":    float(recall_score(y_true, y_pred, zero_division=0)),
        "f1":        float(f1_score(y_true, y_pred, zero_division=0)),
        "fpr":       float(fp / max(fp + tn, 1)),
        "tp":        int(tp),
        "fp":        int(fp),
        "fn":        int(fn),
        "tn":        int(tn),
        "threshold": float(threshold),
    }


def find_optimal_threshold(
    y_true:            np.ndarray,
    y_prob:            np.ndarray,
    rto_cost:          float = 350.0,
    verification_cost: float = 30.0,
) -> tuple[float, list[dict]]:
    """
    Sweep thresholds and find the one that minimises total merchant cost:
        cost = FN × rto_cost + FP × verification_cost
    """
    thresholds = np.arange(0.10, 0.91, 0.05)
    best_threshold = 0.50
    best_cost      = float("inf")
    results: list[dict] = []

    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        precision = tp / max(tp + fp, 1)
        # Enforce a minimum precision floor so threshold doesn't collapse to near-zero
        if precision < 0.35:
            results.append({
                "threshold": round(float(t), 2),
                "cost":      float("inf"),
                "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
            })
            continue
        cost = fn * rto_cost + fp * verification_cost
        results.append({
            "threshold": round(float(t), 2),
            "cost":      float(cost),
            "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        })
        if cost < best_cost:
            best_cost      = cost
            best_threshold = float(t)

    return round(best_threshold, 2), results


def get_pr_curve_data(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> dict:
    """Return precision-recall curve arrays serialisable to JSON."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    return {
        "precision":  precision.tolist(),
        "recall":     recall.tolist(),
        "thresholds": thresholds.tolist(),
    }


# ---------------------------------------------------------------------------
# Full evaluation run (saves JSON)
# ---------------------------------------------------------------------------

def evaluate_on_split(split: str = "validation", config: dict | None = None) -> dict:
    """
    Load the best model and evaluate on `split` (validation|test).
    Saves results to models/{split}_metrics.json.
    """
    if config is None:
        config = load_config()

    models_dir = ROOT_DIR / "models"

    with open(models_dir / "best_model.json") as f:
        meta = json.load(f)
    best_name  = meta["best_model"]
    opt_thresh = meta["optimal_threshold"]

    with open(models_dir / f"{best_name}.pkl", "rb") as f:
        model_dict = pickle.load(f)

    proc_dir = ROOT_DIR / config["data"]["processed_dir"]
    df = pd.read_csv(proc_dir / f"{split}.csv")

    X = get_X(df)
    y = get_y(df)

    if model_dict["needs_scaling"]:
        X = model_dict["scaler"].transform(X)

    y_prob = model_dict["model"].predict_proba(X)[:, 1]

    # Metrics at optimal threshold
    metrics = evaluate_model(y, y_prob, threshold=opt_thresh)

    # PR curve
    pr_curve = get_pr_curve_data(y, y_prob)

    # Threshold sweep
    _, threshold_sweep = find_optimal_threshold(
        y, y_prob,
        rto_cost          = config["cost"]["rto_cost"],
        verification_cost = config["cost"]["verification_cost"],
    )

    # Business impact
    business = compute_business_impact(
        y_true            = y,
        y_prob            = y_prob,
        threshold         = opt_thresh,
        rto_cost          = config["cost"]["rto_cost"],
        verification_cost = config["cost"]["verification_cost"],
    )

    # Per-model comparison (all models evaluated on this split)
    all_model_metrics: dict[str, dict] = {}
    for name in ["logistic_regression", "random_forest", "lightgbm"]:
        pkl_path = models_dir / f"{name}.pkl"
        if not pkl_path.exists():
            continue
        with open(pkl_path, "rb") as f:
            md = pickle.load(f)
        Xm = md["scaler"].transform(get_X(df)) if md["needs_scaling"] else get_X(df)
        probs_m = md["model"].predict_proba(Xm)[:, 1]
        all_model_metrics[name] = evaluate_model(y, probs_m, threshold=opt_thresh)

    results = {
        "split":            split,
        "best_model":       best_name,
        "optimal_threshold": opt_thresh,
        "metrics":          metrics,
        "pr_curve":         pr_curve,
        "threshold_sweep":  threshold_sweep,
        "business_impact":  business,
        "all_model_metrics": all_model_metrics,
    }

    out_path = models_dir / f"{split}_metrics.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[evaluate] {split.upper()} results for {best_name}:")
    print(f"  PR-AUC    : {metrics['prauc']:.4f}")
    print(f"  Precision : {metrics['precision']:.4f}")
    print(f"  Recall    : {metrics['recall']:.4f}")
    print(f"  F1        : {metrics['f1']:.4f}")
    print(f"  Threshold : {opt_thresh}")
    print(f"  TP={metrics['tp']}  FP={metrics['fp']}  FN={metrics['fn']}  TN={metrics['tn']}")
    print(f"\n  Business impact saved -> {out_path}")

    return results


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="validation", choices=["validation", "test"])
    args = parser.parse_args()
    evaluate_on_split(split=args.split)
