"""Tests for data_generator.py"""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from data_generator import generate_synthetic_orders


@pytest.fixture(scope="module")
def df():
    return generate_synthetic_orders(n_samples=2000, seed=42)


def test_shape(df):
    assert len(df) == 2000
    assert "is_rto" in df.columns


def test_rto_rate_realistic(df):
    rto_rate = df["is_rto"].mean()
    assert 0.10 <= rto_rate <= 0.40, f"Unexpected RTO rate: {rto_rate:.3f}"


def test_no_null_values(df):
    assert df.isnull().sum().sum() == 0, "Unexpected nulls in dataset"


def test_timestamps_sorted(df):
    ts = df["order_timestamp"].values
    assert (ts[1:] >= ts[:-1]).all(), "Timestamps not sorted ascending"


def test_cod_higher_rto(df):
    """COD orders should have higher average RTO rate than prepaid."""
    cod_rto = df[df["is_cod"] == 1]["is_rto"].mean()
    prep_rto = df[df["is_cod"] == 0]["is_rto"].mean()
    assert cod_rto > prep_rto, f"COD RTO ({cod_rto:.3f}) not > prepaid ({prep_rto:.3f})"


def test_feature_ranges(df):
    assert (df["address_completeness_score"].between(20, 100)).all()
    assert (df["pincode_rto_rate"].between(0.02, 0.65)).all()
    assert (df["order_value"].between(99, 49_999)).all()
    assert (df["is_cod"].isin([0, 1])).all()
    assert (df["is_rto"].isin([0, 1])).all()


def test_no_leakage_columns(df):
    forbidden = ["delivery_outcome", "rto_date", "return_reason", "final_delivery_status"]
    for col in forbidden:
        assert col not in df.columns, f"Leakage column found: {col}"


def test_customer_rto_rate_bounds(df):
    assert (df["customer_rto_rate"] >= 0).all()
    assert (df["customer_rto_rate"] <= 1).all()
