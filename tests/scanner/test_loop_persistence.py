from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.fetcher.models import Candle
from src.persistence.exceptions import PersistenceError
from src.scanner.loop import _scan_pair
from src.signals.models import Signal, SignalDirection


def make_candle(close: float = 50000.0) -> Candle:
    return Candle(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        open=close - 5,
        high=close + 20,
        low=close - 20,
        close=close,
        volume=1000.0,
        symbol="BTCUSDT",
        timeframe="1h",
    )


def make_signal(direction: SignalDirection = SignalDirection.BUY) -> Signal:
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
def base_mocks():
    fetcher = MagicMock()
    fetcher.fetch_candles.return_value = [make_candle()] * 50

    fetcher_cfg = MagicMock()
    fetcher_cfg.default_limit = 200

    indicator_cfg = MagicMock()

    dedup = MagicMock()
    dedup.is_duplicate.return_value = False

    crypto_repo = MagicMock()
    crypto_repo.upsert.return_value = 1

    signal_repo = MagicMock()

    notifier = None

    return {
        "fetcher": fetcher,
        "fetcher_cfg": fetcher_cfg,
        "indicator_cfg": indicator_cfg,
        "dedup": dedup,
        "crypto_repo": crypto_repo,
        "signal_repo": signal_repo,
        "notifier": notifier,
    }


def call_scan_pair(mocks, signal: Signal, min_candles: int = 5):
    with (
        patch("src.scanner.loop.calculate_indicators"),
        patch("src.scanner.loop.evaluate_signal", return_value=signal),
    ):
        _scan_pair(
            symbol="BTCUSDT",
            timeframe="1h",
            fetcher=mocks["fetcher"],
            fetcher_cfg=mocks["fetcher_cfg"],
            indicator_cfg=mocks["indicator_cfg"],
            min_candles=min_candles,
            dedup=mocks["dedup"],
            notifier=mocks["notifier"],
            crypto_repo=mocks["crypto_repo"],
            signal_repo=mocks["signal_repo"],
        )


def test_signal_persisted_after_evaluate(base_mocks):
    signal = make_signal(SignalDirection.BUY)
    call_scan_pair(base_mocks, signal)
    base_mocks["signal_repo"].save.assert_called_once_with(signal, 1)


def test_no_signal_still_persisted(base_mocks):
    signal = make_signal(SignalDirection.NO_SIGNAL)
    call_scan_pair(base_mocks, signal)
    base_mocks["signal_repo"].save.assert_called_once()


def test_crypto_upsert_called_with_symbol(base_mocks):
    call_scan_pair(base_mocks, make_signal())
    base_mocks["crypto_repo"].upsert.assert_called_once_with("BTCUSDT")


def test_persistence_failure_does_not_stop_dedup_check(base_mocks):
    base_mocks["signal_repo"].save.side_effect = PersistenceError("save")
    base_mocks["dedup"].is_duplicate.return_value = False

    signal = make_signal(SignalDirection.BUY)
    call_scan_pair(base_mocks, signal)

    base_mocks["dedup"].is_duplicate.assert_called_once()
