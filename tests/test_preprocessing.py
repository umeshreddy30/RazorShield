"""Tests for preprocessing.py"""
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

try:
    from data_generator import generate_synthetic_orders
    from preprocessing import (
        CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES,
        encode_splits, fit_encoders, get_X, get_X_y, get_y,
    )
except ImportError:
    from src.data_generator import generate_synthetic_orders
    from src.preprocessing import (
        CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES,
        encode_splits, fit_encoders, get_X, get_X_y, get_y,
    )


@pytest.fixture(scope="module")
def splits():
    df = generate_synthetic_orders(n_samples=3000, seed=99)
    df = df.sort_values("order_timestamp").reset_index(drop=True)
    n = len(df)
    train = df.iloc[:int(n * 0.7)].copy()
    val = df.iloc[int(n * 0.7):int(n * 0.85)].copy()
    test = df.iloc[int(n * 0.85):].copy()
    return train, val, test


def test_encode_splits_no_leakage(splits):
    """Encoders must be fit on train only — val/test must not raise."""
    train, val, test = splits
    train_enc, val_enc, test_enc, _ = encode_splits(train, val, test)
    for col in CATEGORICAL_FEATURES:
        assert f"{col}_encoded" in train_enc.columns
        assert f"{col}_encoded" in val_enc.columns
        assert f"{col}_encoded" in test_enc.columns


def test_feature_matrix_shape(splits):
    train, val, test = splits
    train_enc, val_enc, test_enc, _ = encode_splits(train, val, test)
    X_train = get_X(train_enc)
    assert X_train.shape == (len(train), len(FEATURE_COLUMNS))
    assert X_train.dtype == float


def test_labels_binary(splits):
    train, _, _ = splits
    y = get_y(train)
    assert set(np.unique(y)).issubset({0, 1})


def test_no_nan_in_features(splits):
    train, val, test = splits
    train_enc, val_enc, test_enc, _ = encode_splits(train, val, test)
    for name, df in [("train", train_enc), ("val", val_enc), ("test", test_enc)]:
        X = get_X(df)
        assert not np.isnan(X).any(), f"NaN found in {name} features"
