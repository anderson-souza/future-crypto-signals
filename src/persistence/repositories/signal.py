import sqlite3
from datetime import datetime, timezone

from src.persistence.database import Database
from src.persistence.exceptions import PersistenceError
from src.signals.models import Signal


class SignalRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, signal: Signal, cryptocurrency_id: int) -> None:
        try:
            conn = self._db.get_connection()
            conn.execute(
                """INSERT INTO signals (
                    cryptocurrency_id, timeframe, direction, close, rsi,
                    sma_short, sma_long, supertrend_value, supertrend_direction,
                    rvol, volume_suppressed, candle_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cryptocurrency_id,
                    signal.timeframe,
                    signal.direction.value,
                    signal.close,
                    signal.rsi,
                    signal.sma_short,
                    signal.sma_long,
                    signal.supertrend_value,
                    signal.supertrend_direction,
                    signal.rvol,
                    1 if signal.volume_suppressed else 0,
                    signal.timestamp.isoformat(),
                ),
            )
            conn.commit()
        except sqlite3.Error as exc:
            raise PersistenceError("save", str(exc)) from exc

    def find_last_sent_at(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        since: datetime,
    ) -> datetime | None:
        since_str = since.strftime("%Y-%m-%d %H:%M:%S")
        try:
            row = self._db.get_connection().execute(
                """SELECT s.created_at
                   FROM   signals s
                   JOIN   cryptocurrencies c ON c.id = s.cryptocurrency_id
                   WHERE  c.symbol    = ?
                   AND    s.timeframe = ?
                   AND    s.direction = ?
                   AND    s.created_at >= ?
                   ORDER  BY s.created_at DESC
                   LIMIT  1""",
                (symbol, timeframe, direction, since_str),
            ).fetchone()
            if row is None:
                return None
            return datetime.fromisoformat(row["created_at"]).replace(tzinfo=timezone.utc)
        except sqlite3.Error as exc:
            raise PersistenceError("find_last_sent_at", str(exc)) from exc
