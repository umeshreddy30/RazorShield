"""
RazorShield — Model Training
==============================
Trains three models:
  1. Logistic Regression  (baseline)
  2. Random Forest        (primary candidate)
  3. LightGBM             (gradient boosted candidate)

Each model is calibrated with Platt scaling on the validation set so that
predict_proba() outputs are well-calibrated probabilities (not raw scores).

The model with the highest Validation PR-AUC is selected as the "best model"
and used for production inference.

Usage:
    python src/train.py
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import yaml
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Backward-compatible Platt calibration helper
# sklearn >= 1.6 deprecated cv='prefit'; sklearn >= 1.9 removed it entirely.
# FrozenEstimator (introduced in 1.6) is the correct replacement.
# This wrapper works on sklearn 1.3-1.5 (old) AND 1.6+ (new/cloud).
# ---------------------------------------------------------------------------
try:
    from sklearn.frozen import FrozenEstimator as _FrozenEstimator

    def _calibrate(estimator, X_val, y_val, method="sigmoid"):
        """Calibrate a pre-fitted estimator (sklearn >= 1.6 path)."""
        calib = CalibratedClassifierCV(_FrozenEstimator(estimator), method=method)
        calib.fit(X_val, y_val)
        return calib

except ImportError:
    # sklearn < 1.6 — cv='prefit' still works
    def _calibrate(estimator, X_val, y_val, method="sigmoid"):  # type: ignore[misc]
        """Calibrate a pre-fitted estimator (legacy sklearn < 1.6 path)."""
        calib = CalibratedClassifierCV(estimator, method=method, cv="prefit")
        calib.fit(X_val, y_val)
        return calib


ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from preprocessing import encode_splits, get_X, get_X_y, load_and_split
from evaluate import evaluate_model, find_optimal_threshold


def load_config() -> dict:
    with open(ROOT_DIR / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Training helpers
# ---------------------------------------------------------------------------

def _train_logistic_regression(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val:   np.ndarray,
    y_val:   np.ndarray,
    cfg:     dict,
    seed:    int,
) -> dict:
    lr_cfg = cfg["model"]["logistic_regression"]

    scaler = StandardScaler()
    Xtr = scaler.fit_transform(X_train)
    Xvl = scaler.transform(X_val)

    lr = LogisticRegression(
        max_iter     = lr_cfg["max_iter"],
        C            = lr_cfg["C"],
        class_weight = lr_cfg["class_weight"],
        random_state = seed,
        solver       = "lbfgs",
    )
    lr.fit(Xtr, y_train)

    calib = _calibrate(lr, Xvl, y_val)

    return {
        "model":        calib,
        "base_model":   lr,
        "scaler":       scaler,
        "needs_scaling": True,
        "model_type":   "logistic_regression",
    }


def _train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val:   np.ndarray,
    y_val:   np.ndarray,
    cfg:     dict,
    seed:    int,
) -> dict:
    rf_cfg = cfg["model"]["random_forest"]

    rf = RandomForestClassifier(
        n_estimators   = rf_cfg["n_estimators"],
        max_depth      = rf_cfg["max_depth"],
        min_samples_leaf = rf_cfg["min_samples_leaf"],
        class_weight   = rf_cfg["class_weight"],
        random_state   = seed,
        n_jobs         = rf_cfg["n_jobs"],
    )
    rf.fit(X_train, y_train)

    calib = _calibrate(rf, X_val, y_val)

    return {
        "model":        calib,
        "base_model":   rf,
        "scaler":       None,
        "needs_scaling": False,
        "model_type":   "random_forest",
    }


def _train_lightgbm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val:   np.ndarray,
    y_val:   np.ndarray,
    cfg:     dict,
    seed:    int,
) -> dict:
    try:
        import lightgbm as lgb
    except ImportError:
        print("[train] lightgbm not installed — skipping.")
        return None

    lgb_cfg = cfg["model"]["lightgbm"]
    pos_weight = float((y_train == 0).sum()) / max(float((y_train == 1).sum()), 1)

    lgb_model = lgb.LGBMClassifier(
        n_estimators     = lgb_cfg["n_estimators"],
        max_depth        = lgb_cfg["max_depth"],
        learning_rate    = lgb_cfg["learning_rate"],
        num_leaves       = lgb_cfg["num_leaves"],
        min_child_samples= lgb_cfg["min_child_samples"],
        scale_pos_weight = pos_weight,
        random_state     = seed,
        n_jobs           = lgb_cfg["n_jobs"],
        verbosity        = lgb_cfg.get("verbosity", -1),
    )
    lgb_model.fit(X_train, y_train)

    calib = _calibrate(lgb_model, X_val, y_val)

    return {
        "model":        calib,
        "base_model":   lgb_model,
        "scaler":       None,
        "needs_scaling": False,
        "model_type":   "lightgbm",
    }


# ---------------------------------------------------------------------------
# Main training orchestrator
# ---------------------------------------------------------------------------

def train_all_models(config: dict | None = None) -> tuple[dict, str]:
    """
    Train all models, calibrate on validation set, persist to disk.

    Returns
    -------
    models : dict of model name → model_dict
    best_model_name : str
    """
    if config is None:
        config = load_config()

    seed = config["random_seed"]

    # -- Data --
    train_df, val_df, test_df = load_and_split(config)
    train_df, val_df, test_df, encoders = encode_splits(train_df, val_df, test_df)

    X_train, y_train = get_X_y(train_df)
    X_val,   y_val   = get_X_y(val_df)

    # -- Save splits & encoders --
    out_dir = ROOT_DIR / config["data"]["processed_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(out_dir / "train.csv",      index=False)
    val_df.to_csv(  out_dir / "validation.csv", index=False)
    test_df.to_csv( out_dir / "test.csv",       index=False)

    models_dir = ROOT_DIR / "models"
    models_dir.mkdir(exist_ok=True)

    with open(models_dir / "encoders.pkl", "wb") as f:
        pickle.dump(encoders, f)

    # Save background data sample for SHAP LinearExplainer (LR)
    bg_idx = np.random.RandomState(seed).choice(len(X_train), size=500, replace=False)
    np.save(models_dir / "shap_background.npy", X_train[bg_idx])

    # -- Train --
    print("\n[train] Training Logistic Regression …")
    lr_dict  = _train_logistic_regression(X_train, y_train, X_val, y_val, config, seed)

    print("[train] Training Random Forest …")
    rf_dict  = _train_random_forest(X_train, y_train, X_val, y_val, config, seed)

    print("[train] Training LightGBM …")
    lgb_dict = _train_lightgbm(X_train, y_train, X_val, y_val, config, seed)

    models: dict[str, dict] = {}
    if lr_dict:  models["logistic_regression"] = lr_dict
    if rf_dict:  models["random_forest"]       = rf_dict
    if lgb_dict: models["lightgbm"]            = lgb_dict

    # -- Evaluate on validation → pick best by PR-AUC --
    print("\n[train] Validation PR-AUC comparison:")
    best_name  = None
    best_prauc = -1.0

    for name, md in models.items():
        Xv = md["scaler"].transform(X_val) if md["needs_scaling"] else X_val
        probs   = md["model"].predict_proba(Xv)[:, 1]
        metrics = evaluate_model(y_val, probs)
        print(
            f"  {name:<25}  PR-AUC={metrics['prauc']:.4f}  "
            f"F1={metrics['f1']:.4f}  "
            f"Prec={metrics['precision']:.4f}  "
            f"Recall={metrics['recall']:.4f}"
        )
        if metrics["prauc"] > best_prauc:
            best_prauc = metrics["prauc"]
            best_name  = name

    print(f"\n[train] Best model -> {best_name}  (Val PR-AUC={best_prauc:.4f})")

    # -- Find optimal threshold on validation set --
    best_md = models[best_name]
    Xv_best = best_md["scaler"].transform(X_val) if best_md["needs_scaling"] else X_val
    val_probs = best_md["model"].predict_proba(Xv_best)[:, 1]

    opt_threshold, _ = find_optimal_threshold(
        y_val, val_probs,
        rto_cost          = config["cost"]["rto_cost"],
        verification_cost = config["cost"]["verification_cost"],
    )
    print(f"[train] Optimal threshold (cost-minimising on val) = {opt_threshold:.2f}")

    # -- Save all models --
    for name, md in models.items():
        with open(models_dir / f"{name}.pkl", "wb") as f:
            pickle.dump(md, f)

    # -- Persist metadata --
    meta = {
        "best_model":      best_name,
        "val_prauc":       round(best_prauc, 4),
        "optimal_threshold": float(opt_threshold),
        "cost_config":     config["cost"],
    }
    with open(models_dir / "best_model.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"[train] All models saved to {models_dir}/")
    return models, best_name


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cfg = load_config()
    train_all_models(cfg)
