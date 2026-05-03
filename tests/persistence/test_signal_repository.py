from datetime import datetime, timedelta, timezone

import pytest

from src.persistence.database import Database
from src.persistence.repositories.cryptocurrency import CryptocurrencyRepository
from src.persistence.repositories.signal import SignalRepository
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


@pytest.fixture
def crypto_id(db: Database) -> int:
    return CryptocurrencyRepository(db).upsert("BTCUSDT")


def test_save_inserts_signal(db: Database, crypto_id: int):
    repo = SignalRepository(db)
    repo.save(make_signal(), crypto_id)

    count = db.get_connection().execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    assert count == 1


def test_save_all_fields(db: Database, crypto_id: int):
    signal = make_signal(SignalDirection.BUY)
    SignalRepository(db).save(signal, crypto_id)

    row = db.get_connection().execute("SELECT * FROM signals").fetchone()
    assert row["cryptocurrency_id"] == crypto_id
    assert row["timeframe"] == "1h"
    assert row["direction"] == "buy"
    assert row["close"] == 50000.0
    assert row["rsi"] == 45.0
    assert row["sma_short"] == 49000.0
    assert row["sma_long"] == 48000.0
    assert row["supertrend_value"] == 48500.0
    assert row["supertrend_direction"] == "bullish"
    assert row["rvol"] == 1.2
    assert row["volume_suppressed"] == 0


def test_save_no_signal_direction(db: Database, crypto_id: int):
    SignalRepository(db).save(make_signal(SignalDirection.NO_SIGNAL), crypto_id)
    count = db.get_connection().execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    assert count == 1


def test_find_last_sent_at_returns_none_when_empty(db: Database):
    repo = SignalRepository(db)
    since = datetime.now(timezone.utc) - timedelta(hours=4)
    result = repo.find_last_sent_at("BTCUSDT", "1h", "buy", since)
    assert result is None


def test_find_last_sent_at_within_window(db: Database, crypto_id: int):
    repo = SignalRepository(db)
    repo.save(make_signal(SignalDirection.BUY), crypto_id)

    since = datetime.now(timezone.utc) - timedelta(hours=4)
    result = repo.find_last_sent_at("BTCUSDT", "1h", "buy", since)
    assert result is not None


def test_find_last_sent_at_outside_window(db: Database, crypto_id: int):
    # Insert signal with a past created_at by manipulating directly
    conn = db.get_connection()
    conn.execute(
        """INSERT INTO signals
           (cryptocurrency_id, timeframe, direction, close, rsi, sma_short, sma_long,
            supertrend_value, supertrend_direction, rvol, volume_suppressed, candle_timestamp, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (crypto_id, "1h", "buy", 50000.0, 45.0, 49000.0, 48000.0,
         48500.0, "bullish", 1.2, 0, "2024-01-01T00:00:00+00:00",
         "2024-01-01 00:00:00"),  # 5h ago effectively
    )
    conn.commit()

    since = datetime.now(timezone.utc) - timedelta(hours=4)
    result = SignalRepository(db).find_last_sent_at("BTCUSDT", "1h", "buy", since)
    assert result is None


def test_find_last_sent_at_filters_by_direction(db: Database, crypto_id: int):
    repo = SignalRepository(db)
    repo.save(make_signal(SignalDirection.BUY), crypto_id)

    since = datetime.now(timezone.utc) - timedelta(hours=4)
    result = repo.find_last_sent_at("BTCUSDT", "1h", "sell", since)
    assert result is None


def test_find_last_sent_at_filters_by_symbol(db: Database, crypto_id: int):
    repo = SignalRepository(db)
    repo.save(make_signal(SignalDirection.BUY), crypto_id)

    since = datetime.now(timezone.utc) - timedelta(hours=4)
    result = repo.find_last_sent_at("ETHUSDT", "1h", "buy", since)
    assert result is None
