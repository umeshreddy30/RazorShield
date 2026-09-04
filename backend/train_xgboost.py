# backend/train_xgboost.py
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
import json
import os
from pathlib import Path

def generate_synthetic_transactions(n_samples: int = 50_000, random_seed: int = 42):
    np.random.seed(random_seed)
    
    amount = np.random.exponential(scale=2500, size=n_samples) + 150
    account_age_days = np.random.exponential(scale=180, size=n_samples)
    device_trust_score = np.random.beta(a=7, b=2, size=n_samples)
    ip_velocity_1h = np.random.poisson(lam=1.5, size=n_samples)
    txn_velocity_1h = np.random.poisson(lam=2.0, size=n_samples)
    is_vpn_proxy = np.random.binomial(n=1, p=0.07, size=n_samples)
    failed_attempts_24h = np.random.poisson(lam=0.4, size=n_samples)
    billing_shipping_match = np.random.binomial(n=1, p=0.88, size=n_samples)
    
    latent_fraud_score = (
        0.0003 * amount
        - 0.015 * account_age_days
        - 3.5 * device_trust_score
        + 0.8 * ip_velocity_1h
        + 0.6 * txn_velocity_1h
        + 2.2 * is_vpn_proxy
        + 1.1 * failed_attempts_24h
        - 1.4 * billing_shipping_match
        - 1.2
    )
    latent_fraud_score += (is_vpn_proxy * (ip_velocity_1h > 4) * 2.0)
    latent_fraud_score += ((amount > 15000) * (account_age_days < 7) * 2.5)
    
    fraud_prob = 1.0 / (1.0 + np.exp(-latent_fraud_score))
    is_fraud = np.random.binomial(n=1, p=fraud_prob)
    
    df = pd.DataFrame({
        "amount": amount,
        "account_age_days": account_age_days,
        "device_trust_score": device_trust_score,
        "ip_velocity_1h": ip_velocity_1h,
        "txn_velocity_1h": txn_velocity_1h,
        "is_vpn_proxy": is_vpn_proxy,
        "failed_attempts_24h": failed_attempts_24h,
        "billing_shipping_match": billing_shipping_match,
        "is_fraud": is_fraud
    })
    return df

def train_and_export():
    root = Path(__file__).resolve().parent.parent
    models_dir = root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print("[INFO] Generating synthetic transaction records for XGBoost...")
    df = generate_synthetic_transactions()
    
    feature_cols = [c for c in df.columns if c != "is_fraud"]
    X = df[feature_cols]
    y = df["is_fraud"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    
    params = {
        "objective": "binary:logistic",
        "eval_metric": ["logloss", "auc"],
        "max_depth": 5,
        "eta": 0.08,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "tree_method": "hist"
    }
    
    print("[TRAIN] Training XGBoost Enterprise Classifier...")
    bst = xgb.train(params, dtrain, num_boost_round=150, evals=[(dtest, "test")], verbose_eval=False)
    
    y_pred_proba = bst.predict(dtest)
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"[SUCCESS] XGBoost Model Validation AUC: {auc:.4f}")
    
    model_path = models_dir / "xgboost_fraud_v1.json"
    bst.save_model(str(model_path))
    
    meta_path = models_dir / "xgboost_feature_metadata.json"
    with open(meta_path, "w") as f:
        json.dump({"features": feature_cols, "auc": float(auc), "version": "1.0.0"}, f, indent=2)
        
    print(f"[EXPORT] Model exported successfully to {model_path}")

if __name__ == "__main__":
    train_and_export()
