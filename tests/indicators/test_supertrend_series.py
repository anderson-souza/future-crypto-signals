import pandas as pd
import pytest

from src.exceptions import InsufficientDataError
from src.indicators.supertrend import calculate_supertrend, calculate_supertrend_series
from tests.conftest import make_candles


def test_returns_two_series(candles_150):
    result = calculate_supertrend_series(candles_150)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert all(isinstance(s, pd.Series) for s in result)


def test_series_length_matches_candles(candles_150):
    value_series, dir_series = calculate_supertrend_series(candles_150)
    assert len(value_series) == len(candles_150)
    assert len(dir_series) == len(candles_150)


def test_last_value_matches_scalar(candles_150):
    value_series, dir_series = calculate_supertrend_series(candles_150)
    scalar = calculate_supertrend(candles_150)
    assert abs(value_series.dropna().iloc[-1] - scalar.value) < 1e-9


def test_direction_series_values_are_1_or_minus1(candles_150):
    _, dir_series = calculate_supertrend_series(candles_150)
    valid = {1, -1}
    assert set(dir_series.dropna().unique()).issubset(valid)


def test_series_has_datetime_index(candles_150):
    value_series, dir_series = calculate_supertrend_series(candles_150)
    assert isinstance(value_series.index, pd.DatetimeIndex)
    assert isinstance(dir_series.index, pd.DatetimeIndex)


def test_insufficient_data_raises():
    with pytest.raises(InsufficientDataError):
        calculate_supertrend_series(make_candles(5), period=10)


def test_invalid_period_raises():
    with pytest.raises(ValueError, match="period must be positive"):
        calculate_supertrend_series(make_candles(50), period=0)
