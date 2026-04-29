import pandas as pd
import pytest

from src.exceptions import InsufficientDataError
from src.indicators.rsi import calculate_rsi, calculate_rsi_series
from tests.conftest import make_candles


def test_returns_series(candles_150):
    result = calculate_rsi_series(candles_150)
    assert isinstance(result, pd.Series)


def test_series_length_matches_candles(candles_150):
    result = calculate_rsi_series(candles_150)
    assert len(result) == len(candles_150)


def test_last_value_matches_scalar(candles_150):
    series = calculate_rsi_series(candles_150)
    scalar = calculate_rsi(candles_150)
    assert abs(series.dropna().iloc[-1] - scalar) < 1e-9


def test_series_has_datetime_index(candles_150):
    result = calculate_rsi_series(candles_150)
    assert isinstance(result.index, pd.DatetimeIndex)


def test_insufficient_data_raises():
    with pytest.raises(InsufficientDataError):
        calculate_rsi_series(make_candles(5), period=14)


def test_invalid_period_raises():
    with pytest.raises(ValueError, match="period must be positive"):
        calculate_rsi_series(make_candles(50), period=0)
