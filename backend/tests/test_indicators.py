import pytest
import pandas as pd
import numpy as np

from backend.indicators.normalizer import Normalizer
from backend.indicators.momentum import MomentumIndicator
from backend.indicators.put_call import PutCallIndicator


def test_normalizer_rolling_percentile():
    n = Normalizer()
    history = pd.Series(np.random.randn(1260) * 10 + 50)
    score = n.rolling_percentile(55.0, history, invert=False)
    assert 0 <= score <= 100


def test_normalizer_invert():
    n = Normalizer()
    history = pd.Series(range(100))
    score_normal = n.rolling_percentile(50, history, invert=False)
    score_inverted = n.rolling_percentile(50, history, invert=True)
    assert score_inverted == 100 - score_normal


def test_normalizer_empty_history():
    n = Normalizer()
    score = n.rolling_percentile(50.0, pd.Series([], dtype=float))
    assert score == 50.0


def test_normalizer_nan_handling():
    n = Normalizer()
    score = n.rolling_percentile(float("nan"), pd.Series([1, 2, 3]))
    assert np.isnan(score)


def test_momentum_indicator_sync():
    ind = MomentumIndicator()
    prices = list(100 + np.cumsum(np.random.randn(1260) * 0.5))
    result = ind.calculate_sync(prices)
    assert result is not None
    assert 0 <= result <= 100


def test_momentum_indicator_insufficient_data():
    ind = MomentumIndicator()
    prices = list(100 + np.cumsum(np.random.randn(50) * 0.5))
    result = ind.calculate_sync(prices)
    assert result is None


def test_put_call_inverted():
    ind = PutCallIndicator()
    history = [0.8, 0.9, 1.0, 1.1, 1.2] * 50 + [1.5]
    result = ind.calculate_sync(history)
    assert result is not None
    # High put/call should give low score (inverted)
    assert result < 50


def test_put_call_low_ratio():
    ind = PutCallIndicator()
    history = [0.8, 0.9, 1.0, 1.1, 1.2] * 50 + [0.5]
    result = ind.calculate_sync(history)
    assert result is not None
    # Low put/call should give high score
    assert result > 50


def test_put_call_insufficient_data():
    ind = PutCallIndicator()
    result = ind.calculate_sync([1.0, 1.1])
    assert result is None


def test_normalizer_min_max():
    n = Normalizer()
    history = pd.Series(range(100))
    score = n.min_max_normalize(50, history)
    assert 0 <= score <= 100


def test_normalizer_z_score():
    n = Normalizer()
    history = pd.Series(np.random.randn(100) * 10 + 50)
    score = n.z_score_normalize(50, history)
    assert 0 <= score <= 100


def test_normalizer_dispatch():
    n = Normalizer()
    history = pd.Series(range(100))
    score_rp = n.normalize(50, history, method="rolling_percentile")
    score_mm = n.normalize(50, history, method="min_max")
    score_zs = n.normalize(50, history, method="z_score")
    assert 0 <= score_rp <= 100
    assert 0 <= score_mm <= 100
    assert 0 <= score_zs <= 100
