from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.persistence.exceptions import PersistenceError
from src.scanner.deduplicator import SignalDeduplicator
from src.signals.models import Signal, SignalDirection


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


# --- in-memory (existing behaviour) ---

def test_new_signal_not_duplicate():
    dedup = SignalDeduplicator(cooldown_seconds=3600)
    assert dedup.is_duplicate(make_signal()) is False


def test_signal_duplicate_after_mark():
    dedup = SignalDeduplicator(cooldown_seconds=3600)
    signal = make_signal()
    dedup.mark_sent(signal)
    assert dedup.is_duplicate(signal) is True


def test_signal_not_duplicate_after_cooldown_expires():
    dedup = SignalDeduplicator(cooldown_seconds=3600)
    signal = make_signal()

    sent_at = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    future = datetime(2024, 1, 1, 2, 0, 1, tzinfo=timezone.utc)  # 2h 1s later

    with patch("src.scanner.deduplicator.datetime") as mock_dt:
        mock_dt.UTC = timezone.utc
        mock_dt.now.return_value = sent_at
        dedup.mark_sent(signal)

        mock_dt.now.return_value = future
        assert dedup.is_duplicate(signal) is False


def test_buy_and_sell_tracked_independently():
    dedup = SignalDeduplicator(cooldown_seconds=3600)
    buy = make_signal(SignalDirection.BUY)
    sell = make_signal(SignalDirection.SELL)

    dedup.mark_sent(buy)
    assert dedup.is_duplicate(buy) is True
    assert dedup.is_duplicate(sell) is False


def test_different_symbols_tracked_independently():
    dedup = SignalDeduplicator(cooldown_seconds=3600)
    btc = make_signal()
    eth = Signal(**{**btc.__dict__, "symbol": "ETHUSDT"})

    dedup.mark_sent(btc)
    assert dedup.is_duplicate(btc) is True
    assert dedup.is_duplicate(eth) is False


# --- DB-backed ---

def test_is_duplicate_db_returns_true_when_recent_signal_exists():
    signal = make_signal()
    repo = MagicMock()
    repo.find_last_sent_at.return_value = datetime.now(timezone.utc)

    dedup = SignalDeduplicator(cooldown_seconds=3600, signal_repo=repo)
    assert dedup.is_duplicate(signal) is True


def test_is_duplicate_db_returns_false_when_no_recent_signal():
    signal = make_signal()
    repo = MagicMock()
    repo.find_last_sent_at.return_value = None

    dedup = SignalDeduplicator(cooldown_seconds=3600, signal_repo=repo)
    assert dedup.is_duplicate(signal) is False


def test_is_duplicate_db_fail_open_on_persistence_error():
    signal = make_signal()
    repo = MagicMock()
    repo.find_last_sent_at.side_effect = PersistenceError("find_last_sent_at")

    dedup = SignalDeduplicator(cooldown_seconds=3600, signal_repo=repo)
    assert dedup.is_duplicate(signal) is False


def test_mark_sent_noop_when_repo_provided():
    signal = make_signal()
    repo = MagicMock()
    repo.find_last_sent_at.return_value = None

    dedup = SignalDeduplicator(cooldown_seconds=3600, signal_repo=repo)
    dedup.mark_sent(signal)

    repo.assert_not_called()
    assert dedup._sent == {}


def test_falls_back_to_memory_when_no_repo():
    dedup = SignalDeduplicator(cooldown_seconds=3600, signal_repo=None)
    signal = make_signal()
    dedup.mark_sent(signal)
    assert dedup.is_duplicate(signal) is True
