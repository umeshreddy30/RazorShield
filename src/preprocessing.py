"""
RazorShield — Feature Preprocessing
=====================================
Handles feature engineering, categorical encoding, and time-based splits.

All transformations are fit on the training set only and applied to
validation/test to prevent leakage.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

ROOT_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Feature definitions
# ---------------------------------------------------------------------------

CATEGORICAL_FEATURES = [
    "product_category",
    "payment_method",
    "customer_location_type",
]

NUMERIC_FEATURES = [
    "order_value",
    "num_items",
    "is_cod",
    "customer_age_days",
    "previous_orders",
    "previous_delivered_orders",
    "previous_rto_orders",
    "previous_return_orders",
    "previous_cancellations",
    "customer_rto_rate",
    "orders_last_7_days",
    "orders_last_30_days",
    "avg_previous_order_value",
    "current_vs_avg_order_value",
    "pincode_rto_rate",
    "address_completeness_score",
    "delivery_attempt_history",
    "order_hour",
    "day_of_week",
    "is_weekend",
    "is_festival_period",
]

# Final feature matrix columns (numeric + encoded categoricals)
FEATURE_COLUMNS = NUMERIC_FEATURES + [f"{c}_encoded" for c in CATEGORICAL_FEATURES]

# Human-readable names for dashboard display
FEATURE_DISPLAY_NAMES: dict[str, str] = {
    "order_value":                     "Order Value (₹)",
    "num_items":                       "Number of Items",
    "is_cod":                          "Cash-on-Delivery",
    "customer_age_days":               "Customer Account Age (days)",
    "previous_orders":                 "Lifetime Orders",
    "previous_delivered_orders":       "Successful Deliveries",
    "previous_rto_orders":             "Previous RTO Orders",
    "previous_return_orders":          "Previous Returns",
    "previous_cancellations":          "Previous Cancellations",
    "customer_rto_rate":               "Customer RTO Rate",
    "orders_last_7_days":              "Orders in Last 7 Days",
    "orders_last_30_days":             "Orders in Last 30 Days",
    "avg_previous_order_value":        "Avg Previous Order Value (₹)",
    "current_vs_avg_order_value":      "Current vs Avg Order Value",
    "pincode_rto_rate":                "Pincode Historical RTO Rate",
    "address_completeness_score":      "Address Completeness Score",
    "delivery_attempt_history":        "Avg Delivery Attempts (history)",
    "order_hour":                      "Order Hour of Day",
    "day_of_week":                     "Day of Week",
    "is_weekend":                      "Weekend Order",
    "is_festival_period":              "Festival / Sale Period",
    "product_category_encoded":        "Product Category",
    "payment_method_encoded":          "Payment Method",
    "customer_location_type_encoded":  "Customer Location Type",
}


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------

def load_and_split(config: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the raw CSV and perform a time-based train/val/test split.

    Rows are sorted by order_timestamp (ascending), then sliced by ratio.
    No random shuffling is applied — this preserves temporal ordering.
    """
    cfg = config["data"]
    raw_path = ROOT_DIR / cfg["output_path"]
    df = pd.read_csv(raw_path, parse_dates=["order_timestamp"])
    df = df.sort_values("order_timestamp").reset_index(drop=True)

    n          = len(df)
    train_end  = int(n * cfg["train_ratio"])
    val_end    = train_end + int(n * cfg["val_ratio"])

    train = df.iloc[:train_end].copy()
    val   = df.iloc[train_end:val_end].copy()
    test  = df.iloc[val_end:].copy()

    print(
        f"[preprocessing] Split -> "
        f"train={len(train):,}  val={len(val):,}  test={len(test):,}"
    )
    return train, val, test


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def fit_encoders(train: pd.DataFrame) -> dict[str, LabelEncoder]:
    """Fit LabelEncoders on training data only."""
    encoders: dict[str, LabelEncoder] = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        le.fit(train[col].astype(str))
        encoders[col] = le
    return encoders


def apply_encoders(
    df: pd.DataFrame,
    encoders: dict[str, LabelEncoder],
    is_train: bool = False,
) -> pd.DataFrame:
    """Apply pre-fitted encoders; unknown categories map to -1."""
    df = df.copy()
    for col in CATEGORICAL_FEATURES:
        le = encoders[col]
        col_str = df[col].astype(str)
        if is_train:
            df[f"{col}_encoded"] = le.transform(col_str)
        else:
            # Handle unseen categories gracefully
            known = set(le.classes_)
            df[f"{col}_encoded"] = col_str.apply(
                lambda v: le.transform([v])[0] if v in known else -1
            )
    return df


def encode_splits(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, LabelEncoder]]:
    """Fit encoders on train; transform all splits."""
    encoders = fit_encoders(train)
    train = apply_encoders(train, encoders, is_train=True)
    val   = apply_encoders(val,   encoders)
    test  = apply_encoders(test,  encoders)
    return train, val, test, encoders


# ---------------------------------------------------------------------------
# Feature matrix helpers
# ---------------------------------------------------------------------------

def get_X(df: pd.DataFrame) -> np.ndarray:
    return df[FEATURE_COLUMNS].values.astype(float)


def get_y(df: pd.DataFrame) -> np.ndarray:
    return df["is_rto"].values.astype(int)


def get_X_y(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    return get_X(df), get_y(df)
