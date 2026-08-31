"""
RazorShield — Synthetic Data Generator
======================================
Generates 50,000 realistic Indian e-commerce orders with RTO ground-truth labels.

Usage:
    python src/data_generator.py

Output:
    data/raw/orders_synthetic.csv

IMPORTANT: No real PII is generated. All addresses, pincodes, and customer
identifiers are synthetic. This dataset is for research and demonstration only.
"""

from __future__ import annotations

import os
import sys
import uuid
import yaml
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

# ---------------------------------------------------------------------------
# Resolve project root regardless of where script is called from
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    cfg_path = ROOT_DIR / "config" / "config.yaml"
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PINCODE_BUCKETS: dict[str, float] = {
    "METRO_LOW":       0.07,
    "METRO_MED":       0.11,
    "TIER1_LOW":       0.14,
    "TIER1_MED":       0.19,
    "TIER1_HIGH":      0.26,
    "TIER2_MED":       0.24,
    "TIER2_HIGH":      0.33,
    "RURAL_HIGH":      0.39,
    "RURAL_VERY_HIGH": 0.46,
}

LOCATION_PINCODE_MAP: dict[str, list[str]] = {
    "METRO": ["METRO_LOW", "METRO_MED"],
    "TIER1": ["TIER1_LOW", "TIER1_MED", "TIER1_HIGH"],
    "TIER2": ["TIER2_MED", "TIER2_HIGH"],
    "RURAL": ["RURAL_HIGH", "RURAL_VERY_HIGH"],
}

PRODUCT_CATEGORIES = [
    "Electronics", "Apparel", "Beauty", "Home",
    "Books", "Sports", "Footwear",
]
CATEGORY_PROBS = [0.14, 0.26, 0.14, 0.15, 0.10, 0.11, 0.10]

PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "COD"]
LOCATION_TYPES  = ["METRO", "TIER1", "TIER2", "RURAL"]
LOCATION_PROBS  = [0.35, 0.30, 0.20, 0.15]

# Payment method split per location (UPI, CARD, NETBANKING, COD)
PAYMENT_PROBS: dict[str, list[float]] = {
    "METRO": [0.50, 0.30, 0.10, 0.10],
    "TIER1": [0.40, 0.25, 0.10, 0.25],
    "TIER2": [0.30, 0.20, 0.10, 0.40],
    "RURAL": [0.15, 0.10, 0.05, 0.70],
}

# log-normal parameters (mu, sigma) for order value by category
CATEGORY_VALUE_PARAMS: dict[str, tuple[float, float]] = {
    "Electronics": (8.5, 0.75),
    "Apparel":     (6.5, 0.90),
    "Beauty":      (5.8, 0.70),
    "Home":        (7.2, 0.80),
    "Books":       (5.0, 0.50),
    "Sports":      (6.8, 0.80),
    "Footwear":    (6.3, 0.60),
}

# Festival windows (Indian calendar + major sale events)
FESTIVAL_PERIODS: list[tuple[str, str]] = [
    ("2024-03-20", "2024-03-30"),   # Holi
    ("2024-10-10", "2024-11-05"),   # Dussehra–Diwali
    ("2024-12-20", "2024-12-31"),   # Christmas / New Year
    ("2025-01-10", "2025-01-26"),   # Makar Sankranti / Republic Day sale
    ("2025-03-10", "2025-03-20"),   # Holi 2025
    ("2025-05-01", "2025-05-10"),   # Summer sale
]


def _is_festival(dt: datetime) -> bool:
    for s, e in FESTIVAL_PERIODS:
        if datetime.strptime(s, "%Y-%m-%d") <= dt <= datetime.strptime(e, "%Y-%m-%d"):
            return True
    return False


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_synthetic_orders(
    n_samples: int = 50_000,
    seed: int = 42,
    start_date: str = "2024-01-01",
    end_date: str = "2025-06-30",
) -> pd.DataFrame:
    """
    Generate a synthetic order dataset with realistic RTO label correlations.

    The data-generating process (DGP) uses a logistic model to compute
    per-order RTO probability, then samples Bernoulli(p_rto) for the label.
    Gaussian noise ensures no single feature perfectly predicts the outcome.

    Returns
    -------
    pd.DataFrame with 27 columns (26 features + 1 label).
    """
    rng = np.random.RandomState(seed)

    # ------------------------------------------------------------------
    # 1. Timestamps — sorted so time-based split works correctly
    # ------------------------------------------------------------------
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt   = datetime.strptime(end_date,   "%Y-%m-%d")
    total_sec = int((end_dt - start_dt).total_seconds())

    ts_seconds = np.sort(rng.choice(total_sec, size=n_samples, replace=False))
    timestamps = [start_dt + timedelta(seconds=int(s)) for s in ts_seconds]

    # ------------------------------------------------------------------
    # 2. Location & pincode
    # ------------------------------------------------------------------
    location_types = rng.choice(LOCATION_TYPES, size=n_samples, p=LOCATION_PROBS)

    pincode_rto_rates = np.array([
        float(np.clip(
            PINCODE_BUCKETS[rng.choice(LOCATION_PINCODE_MAP[loc])]
            + rng.normal(0, 0.02),
            0.02, 0.65,
        ))
        for loc in location_types
    ])

    # ------------------------------------------------------------------
    # 3. Payment method
    # ------------------------------------------------------------------
    payment_methods = np.array([
        rng.choice(PAYMENT_METHODS, p=PAYMENT_PROBS[loc])
        for loc in location_types
    ])
    is_cod = (payment_methods == "COD").astype(int)

    # ------------------------------------------------------------------
    # 4. Product & order value
    # ------------------------------------------------------------------
    product_categories = rng.choice(
        PRODUCT_CATEGORIES, size=n_samples, p=CATEGORY_PROBS
    )
    order_values = np.array([
        float(np.clip(np.exp(rng.normal(*CATEGORY_VALUE_PARAMS[cat])), 99, 49_999))
        for cat in product_categories
    ]).round(0)

    num_items = rng.randint(1, 7, size=n_samples)

    # ------------------------------------------------------------------
    # 5. Customer history (built causally — no look-ahead)
    # ------------------------------------------------------------------
    customer_age_days = np.clip(
        rng.exponential(200, size=n_samples), 1, 1500
    ).astype(int)

    # Max plausible previous orders given account age
    max_prev = np.clip(
        (customer_age_days / 30 * rng.uniform(0.5, 3.0, n_samples)).astype(int),
        0, 200,
    )
    previous_orders = np.array([rng.randint(0, max(1, m + 1)) for m in max_prev])

    # Customer-level RTO tendency (independent of observed label)
    rto_tendency = rng.beta(2, 8, n_samples)

    previous_rto_orders = np.minimum(
        (previous_orders * rto_tendency).astype(int),
        previous_orders,
    )
    previous_delivered_orders = np.maximum(
        previous_orders - previous_rto_orders - rng.randint(0, 2, n_samples), 0
    )
    previous_return_orders = (
        previous_delivered_orders * rng.beta(1, 15, n_samples)
    ).astype(int)
    previous_cancellations = (
        previous_orders * rng.beta(1, 12, n_samples)
    ).astype(int)

    # Derived: customer historical RTO rate (safe -- uses only prior orders)
    _safe_prev = np.where(previous_orders > 0, previous_orders, 1)
    customer_rto_rate = np.where(
        previous_orders > 0,
        previous_rto_orders / _safe_prev,
        0.0,
    ).round(4)

    # ------------------------------------------------------------------
    # 6. Recent order velocity
    # ------------------------------------------------------------------
    orders_last_7_days  = np.clip(rng.poisson(1.2, n_samples), 0, 15).astype(int)
    orders_last_30_days = np.clip(
        orders_last_7_days + rng.poisson(2.5, n_samples), 0, 40
    ).astype(int)

    # ------------------------------------------------------------------
    # 7. Historical order value vs current
    # ------------------------------------------------------------------
    avg_previous_order_value = np.where(
        previous_orders > 0,
        np.clip(order_values * rng.uniform(0.5, 1.8, n_samples), 99, 49_999),
        order_values,
    ).round(0)

    current_vs_avg = (order_values / np.maximum(avg_previous_order_value, 1)).round(3)

    # ------------------------------------------------------------------
    # 8. Address & delivery signals
    # ------------------------------------------------------------------
    addr_base = np.where(
        location_types == "METRO", 85,
        np.where(location_types == "TIER1", 75,
        np.where(location_types == "TIER2", 65, 55))
    )
    address_completeness_score = np.clip(
        addr_base + rng.normal(0, 12, n_samples), 20, 100
    ).round(1)

    delivery_attempt_history = np.where(
        previous_delivered_orders > 0,
        np.clip(1.0 + rng.exponential(0.3, n_samples), 1.0, 4.0),
        1.5,
    ).round(2)

    # ------------------------------------------------------------------
    # 9. Temporal features
    # ------------------------------------------------------------------
    order_hours  = np.array([t.hour      for t in timestamps])
    days_of_week = np.array([t.weekday() for t in timestamps])
    is_weekend   = (days_of_week >= 5).astype(int)
    is_festival  = np.array([int(_is_festival(t)) for t in timestamps])

    # ------------------------------------------------------------------
    # 10. RTO probability (data-generating logit formula)
    # ------------------------------------------------------------------
    logit = (
        -1.80
        + 1.30 * is_cod
        + 2.50 * customer_rto_rate
        + 1.20 * (1.0 - address_completeness_score / 100.0)
        + 1.00 * pincode_rto_rates
        + 0.50 * np.log1p(orders_last_7_days)
        + 0.40 * np.clip(current_vs_avg - 2.0, 0.0, None)
        + 0.35 * is_festival
        - 0.70 * np.log1p(previous_delivered_orders)
        - 0.40 * (customer_age_days / 365.0)
        + 0.30 * (location_types == "RURAL").astype(float)
        + 0.20 * (location_types == "TIER2").astype(float)
        - 0.20 * (location_types == "METRO").astype(float)
        + rng.normal(0, 0.90, n_samples)          # realistic overlap noise
    )

    rto_probability = expit(logit)
    is_rto = rng.binomial(1, rto_probability)

    # ------------------------------------------------------------------
    # 11. Assemble DataFrame
    # ------------------------------------------------------------------
    df = pd.DataFrame({
        "order_id":                    [str(uuid.UUID(int=int(rng.randint(0, 2**31)))) for _ in range(n_samples)],
        "order_timestamp":             timestamps,
        "order_value":                 order_values,
        "num_items":                   num_items,
        "product_category":            product_categories,
        "payment_method":              payment_methods,
        "is_cod":                      is_cod,
        "customer_age_days":           customer_age_days,
        "previous_orders":             previous_orders,
        "previous_delivered_orders":   previous_delivered_orders,
        "previous_rto_orders":         previous_rto_orders,
        "previous_return_orders":      previous_return_orders,
        "previous_cancellations":      previous_cancellations,
        "customer_rto_rate":           customer_rto_rate,
        "orders_last_7_days":          orders_last_7_days,
        "orders_last_30_days":         orders_last_30_days,
        "avg_previous_order_value":    avg_previous_order_value,
        "current_vs_avg_order_value":  current_vs_avg,
        "pincode_rto_rate":            pincode_rto_rates.round(3),
        "address_completeness_score":  address_completeness_score,
        "customer_location_type":      location_types,
        "delivery_attempt_history":    delivery_attempt_history,
        "order_hour":                  order_hours,
        "day_of_week":                 days_of_week,
        "is_weekend":                  is_weekend,
        "is_festival_period":          is_festival,
        "is_rto":                      is_rto,
    })

    return df


def generate_and_save(config: dict | None = None) -> pd.DataFrame:
    """Generate synthetic data and persist to disk."""
    if config is None:
        config = load_config()

    cfg = config["data"]
    df = generate_synthetic_orders(
        n_samples  = cfg["n_samples"],
        seed       = config["random_seed"],
        start_date = cfg["start_date"],
        end_date   = cfg["end_date"],
    )

    out_path = ROOT_DIR / cfg["output_path"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    rto_rate = df["is_rto"].mean() * 100
    print(f"[data_generator] Generated {len(df):,} orders -> {out_path}")
    print(f"[data_generator] RTO rate: {rto_rate:.1f}%")
    return df


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cfg = load_config()
    generate_and_save(cfg)
