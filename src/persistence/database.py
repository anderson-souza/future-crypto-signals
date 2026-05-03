import sqlite3
from pathlib import Path

from src.persistence.config import PersistenceConfig

_MIGRATION = Path(__file__).parent.parent.parent / "db" / "migrations" / "001_initial.sql"


class Database:
    def __init__(self, config: PersistenceConfig) -> None:
        self._config = config
        self._conn: sqlite3.Connection | None = None

    def initialize(self) -> None:
        Path(self._config.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            self._config.db_path,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_MIGRATION.read_text())

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not initialized — call initialize() first")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
