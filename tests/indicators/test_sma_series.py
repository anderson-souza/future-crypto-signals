import pandas as pd
import pytest

from src.exceptions import InsufficientDataError
from src.indicators.sma import calculate_sma, calculate_sma_series
from tests.conftest import make_candles


def test_returns_series(candles_150):
    result = calculate_sma_series(candles_150, period=20)
    assert isinstance(result, pd.Series)


def test_series_length_matches_candles(candles_150):
    result = calculate_sma_series(candles_150, period=20)
    assert len(result) == len(candles_150)


def test_last_value_matches_scalar(candles_150):
    series = calculate_sma_series(candles_150, period=20)
    scalar = calculate_sma(candles_150, period=20)
    assert abs(series.dropna().iloc[-1] - scalar) < 1e-9


def test_series_has_datetime_index(candles_150):
    result = calculate_sma_series(candles_150, period=20)
    assert isinstance(result.index, pd.DatetimeIndex)


def test_insufficient_data_raises():
    with pytest.raises(InsufficientDataError):
        calculate_sma_series(make_candles(5), period=20)


def test_invalid_period_raises():
    with pytest.raises(ValueError, match="period must be positive"):
        calculate_sma_series(make_candles(50), period=0)
