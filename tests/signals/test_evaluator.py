from datetime import datetime, timezone

import pytest

from src.indicators.models import IndicatorResult, SupertrendResult, TrendDirection, VolumeResult
from src.signals.evaluator import evaluate_signal
from src.signals.models import SignalDirection
from tests.conftest import make_candles


def _make_indicators(
    rsi: float = 45.0,
    sma_short: float = 51000.0,
    sma_long: float = 50000.0,
    supertrend_value: float = 49000.0,
    supertrend_direction: TrendDirection = TrendDirection.BULLISH,
    rvol: float = 1.0,
    is_sufficient: bool = True,
) -> IndicatorResult:
    return IndicatorResult(
        rsi=rsi,
        sma_short=sma_short,
        sma_long=sma_long,
        supertrend=SupertrendResult(value=supertrend_value, direction=supertrend_direction),
        volume=VolumeResult(rvol=rvol, is_sufficient=is_sufficient),
    )


def _last_candle():
    return make_candles(1)[0]


# --- Volume suppression ---

def test_buy_suppressed_when_volume_insufficient():
    indicators = _make_indicators(
        rsi=45.0,
        sma_short=51000.0,
        sma_long=50000.0,
        supertrend_direction=TrendDirection.BULLISH,
        rvol=0.3,
        is_sufficient=False,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.NO_SIGNAL
    assert signal.volume_suppressed is True


def test_sell_suppressed_when_volume_insufficient():
    indicators = _make_indicators(
        rsi=55.0,
        sma_short=49000.0,
        sma_long=50000.0,
        supertrend_direction=TrendDirection.BEARISH,
        rvol=0.3,
        is_sufficient=False,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.NO_SIGNAL
    assert signal.volume_suppressed is True


def test_volume_suppressed_flag_false_on_normal_no_signal():
    # indicator disagreement, volume fine → NO_SIGNAL but not volume_suppressed
    indicators = _make_indicators(
        rsi=45.0,
        sma_short=49000.0,  # close < sma_short → no alignment
        sma_long=50000.0,
        supertrend_direction=TrendDirection.BEARISH,
        is_sufficient=True,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.NO_SIGNAL
    assert signal.volume_suppressed is False


# --- BUY signal ---

def test_buy_signal_when_all_long_conditions_met():
    candles = make_candles(1, base_price=52000.0)
    last = candles[0]  # close ≈ 52000
    indicators = _make_indicators(
        rsi=45.0,
        sma_short=53000.0,  # sma_short > sma_long
        sma_long=51000.0,
        supertrend_direction=TrendDirection.BULLISH,
        is_sufficient=True,
    )
    signal = evaluate_signal(indicators, last)
    assert signal.direction == SignalDirection.BUY
    assert signal.volume_suppressed is False


def test_buy_requires_all_three_conditions():
    # rsi < 50 + BULLISH, but sma_short < sma_long → NO_SIGNAL
    indicators = _make_indicators(
        rsi=45.0,
        sma_short=49000.0,
        sma_long=51000.0,
        supertrend_direction=TrendDirection.BULLISH,
        is_sufficient=True,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.NO_SIGNAL


# --- SELL signal ---

def test_sell_signal_when_all_short_conditions_met():
    indicators = _make_indicators(
        rsi=55.0,
        sma_short=49000.0,  # sma_short < sma_long
        sma_long=51000.0,
        supertrend_direction=TrendDirection.BEARISH,
        is_sufficient=True,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.SELL
    assert signal.volume_suppressed is False


def test_sell_requires_all_three_conditions():
    # rsi > 50 + BEARISH, but sma_short > sma_long → NO_SIGNAL
    indicators = _make_indicators(
        rsi=55.0,
        sma_short=51000.0,
        sma_long=49000.0,
        supertrend_direction=TrendDirection.BEARISH,
        is_sufficient=True,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.NO_SIGNAL


# --- RVOL carried in all outcomes ---

def test_rvol_carried_on_buy_signal():
    indicators = _make_indicators(
        rsi=45.0, sma_short=53000.0, sma_long=51000.0,
        supertrend_direction=TrendDirection.BULLISH,
        rvol=1.8, is_sufficient=True,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.BUY
    assert abs(signal.rvol - 1.8) < 1e-9


def test_rvol_carried_on_no_signal():
    indicators = _make_indicators(rvol=0.3, is_sufficient=False)
    signal = evaluate_signal(indicators, _last_candle())
    assert abs(signal.rvol - 0.3) < 1e-9


def test_rvol_carried_on_indicator_disagreement_no_signal():
    indicators = _make_indicators(
        rsi=45.0, sma_short=49000.0, sma_long=51000.0,
        supertrend_direction=TrendDirection.BEARISH,
        rvol=2.1, is_sufficient=True,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.NO_SIGNAL
    assert abs(signal.rvol - 2.1) < 1e-9


# --- RSI boundary ---

def test_rsi_exactly_50_yields_no_signal():
    indicators = _make_indicators(
        rsi=50.0, sma_short=53000.0, sma_long=51000.0,
        supertrend_direction=TrendDirection.BULLISH,
        is_sufficient=True,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.NO_SIGNAL
