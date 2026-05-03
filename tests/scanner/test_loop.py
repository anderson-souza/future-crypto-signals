from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.scanner.deduplicator import SignalDeduplicator
from src.scanner.loop import _scan_pair
from src.signals.models import Signal, SignalDirection
from tests.conftest import make_candles


def _make_signal(direction: SignalDirection) -> Signal:
    return Signal(
        symbol="BTCUSDT",
        timeframe="1h",
        direction=direction,
        close=50000.0,
        rsi=45.0,
        sma_short=49000.0,
        sma_long=48000.0,
        supertrend_value=48500.0,
        supertrend_direction="bullish",
        rvol=1.2,
        volume_suppressed=False,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def fetcher_cfg():
    cfg = MagicMock()
    cfg.default_limit = 200
    return cfg


@pytest.fixture
def indicator_cfg():
    cfg = MagicMock()
    cfg.rsi_period = 14
    cfg.sma_long_period = 21
    cfg.supertrend_period = 10
    return cfg


def test_no_signal_does_not_notify(fetcher_cfg, indicator_cfg):
    fetcher = MagicMock()
    fetcher.fetch_candles.return_value = make_candles(150)
    notifier = MagicMock()
    dedup = SignalDeduplicator(3600)

    with patch("src.scanner.loop.calculate_indicators"), \
         patch("src.scanner.loop.evaluate_signal", return_value=_make_signal(SignalDirection.NO_SIGNAL)):
        _scan_pair("BTCUSDT", "1h", fetcher, fetcher_cfg, indicator_cfg, 30, dedup, notifier)

    notifier.send.assert_not_called()
    notifier.send_chart.assert_not_called()


def test_buy_signal_notifies_and_marks(fetcher_cfg, indicator_cfg):
    fetcher = MagicMock()
    fetcher.fetch_candles.return_value = make_candles(150)
    notifier = MagicMock()
    dedup = SignalDeduplicator(3600)
    signal = _make_signal(SignalDirection.BUY)

    with patch("src.scanner.loop.calculate_indicators"), \
         patch("src.scanner.loop.evaluate_signal", return_value=signal), \
         patch("src.scanner.loop.render_chart", return_value=b"png"):
        _scan_pair("BTCUSDT", "1h", fetcher, fetcher_cfg, indicator_cfg, 30, dedup, notifier)

    notifier.send.assert_called_once_with(signal)
    notifier.send_chart.assert_called_once_with(signal, b"png")
    assert dedup.is_duplicate(signal) is True


def test_duplicate_signal_skips_notify(fetcher_cfg, indicator_cfg):
    fetcher = MagicMock()
    fetcher.fetch_candles.return_value = make_candles(150)
    notifier = MagicMock()
    dedup = SignalDeduplicator(3600)
    signal = _make_signal(SignalDirection.BUY)
    dedup.mark_sent(signal)

    with patch("src.scanner.loop.calculate_indicators"), \
         patch("src.scanner.loop.evaluate_signal", return_value=signal):
        _scan_pair("BTCUSDT", "1h", fetcher, fetcher_cfg, indicator_cfg, 30, dedup, notifier)

    notifier.send.assert_not_called()


def test_fetch_error_does_not_crash(fetcher_cfg, indicator_cfg):
    fetcher = MagicMock()
    fetcher.fetch_candles.side_effect = RuntimeError("network error")
    notifier = MagicMock()
    dedup = SignalDeduplicator(3600)

    _scan_pair("BTCUSDT", "1h", fetcher, fetcher_cfg, indicator_cfg, 30, dedup, notifier)

    notifier.send.assert_not_called()


def test_no_notifier_still_marks_dedup(fetcher_cfg, indicator_cfg):
    fetcher = MagicMock()
    fetcher.fetch_candles.return_value = make_candles(150)
    dedup = SignalDeduplicator(3600)
    signal = _make_signal(SignalDirection.BUY)

    with patch("src.scanner.loop.calculate_indicators"), \
         patch("src.scanner.loop.evaluate_signal", return_value=signal):
        _scan_pair("BTCUSDT", "1h", fetcher, fetcher_cfg, indicator_cfg, 30, dedup, notifier=None)

    assert dedup.is_duplicate(signal) is True
