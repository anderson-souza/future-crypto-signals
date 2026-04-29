from datetime import datetime, timezone, timedelta

import pytest

from src.chart.exceptions import ChartRenderError
from src.chart.models import ChartConfig, ChartData
from src.chart.renderer import render_chart
from src.exceptions import InsufficientDataError
from src.indicators.models import IndicatorConfig
from src.signals.models import Signal, SignalDirection
from tests.conftest import make_candles


def _make_signal(candles, direction: SignalDirection) -> Signal:
    last = candles[-1]
    return Signal(
        symbol=last.symbol,
        timeframe=last.timeframe,
        direction=direction,
        close=last.close,
        rsi=45.0,
        sma_short=last.close - 100,
        sma_long=last.close - 200,
        supertrend_value=last.close - 500,
        supertrend_direction="bullish",
        timestamp=last.timestamp,
    )


@pytest.fixture
def candles():
    return make_candles(150)


@pytest.fixture
def chart_config():
    return ChartConfig(window=100)


def test_render_buy_signal_returns_bytes(candles, chart_config):
    signal = _make_signal(candles, SignalDirection.BUY)
    result = render_chart(ChartData(candles=candles, signal=signal), chart_config)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_render_sell_signal_returns_bytes(candles, chart_config):
    signal = _make_signal(candles, SignalDirection.SELL)
    result = render_chart(ChartData(candles=candles, signal=signal), chart_config)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_render_no_signal_returns_bytes(candles, chart_config):
    signal = _make_signal(candles, SignalDirection.NO_SIGNAL)
    result = render_chart(ChartData(candles=candles, signal=signal), chart_config)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_signal_timestamp_not_in_window_raises(candles, chart_config):
    last = candles[-1]
    signal = Signal(
        symbol=last.symbol,
        timeframe=last.timeframe,
        direction=SignalDirection.BUY,
        close=last.close,
        rsi=45.0,
        sma_short=last.close - 100,
        sma_long=last.close - 200,
        supertrend_value=last.close - 500,
        supertrend_direction="bullish",
        timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    with pytest.raises(ChartRenderError):
        render_chart(ChartData(candles=candles, signal=signal), chart_config)


def test_empty_candles_raises(chart_config):
    signal = Signal(
        symbol="BTCUSDT",
        timeframe="1h",
        direction=SignalDirection.BUY,
        close=50000.0,
        rsi=45.0,
        sma_short=49900.0,
        sma_long=49800.0,
        supertrend_value=49500.0,
        supertrend_direction="bullish",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    with pytest.raises(InsufficientDataError):
        render_chart(ChartData(candles=[], signal=signal), chart_config)


def test_chart_config_from_env_default(monkeypatch):
    monkeypatch.delenv("CHART_WINDOW", raising=False)
    cfg = ChartConfig.from_env()
    assert cfg.window == 100


def test_chart_config_from_env_custom(monkeypatch):
    monkeypatch.setenv("CHART_WINDOW", "50")
    cfg = ChartConfig.from_env()
    assert cfg.window == 50


def test_fewer_candles_than_window_renders(chart_config):
    candles = make_candles(40)
    signal = _make_signal(candles, SignalDirection.NO_SIGNAL)
    # 40 candles < window=100 → renders all available, no error
    result = render_chart(ChartData(candles=candles, signal=signal), ChartConfig(window=100))
    assert len(result) > 0
