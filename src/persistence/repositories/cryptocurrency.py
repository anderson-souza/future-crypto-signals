import sqlite3

from src.persistence.database import Database
from src.persistence.exceptions import PersistenceError


class CryptocurrencyRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def upsert(self, symbol: str) -> int:
        base_asset = symbol[:-4]
        quote_asset = symbol[-4:]
        try:
            conn = self._db.get_connection()
            conn.execute(
                "INSERT OR IGNORE INTO cryptocurrencies (symbol, base_asset, quote_asset) VALUES (?, ?, ?)",
                (symbol, base_asset, quote_asset),
            )
            conn.commit()
            row = conn.execute(
                "SELECT id FROM cryptocurrencies WHERE symbol = ?", (symbol,)
            ).fetchone()
            return int(row["id"])
        except sqlite3.Error as exc:
            raise PersistenceError("upsert", str(exc)) from exc
