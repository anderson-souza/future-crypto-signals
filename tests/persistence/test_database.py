import sqlite3

import pytest

from src.persistence.config import PersistenceConfig
from src.persistence.database import Database


def make_db(tmp_path) -> Database:
    cfg = PersistenceConfig()
    cfg.db_path = str(tmp_path / "test.db")
    return Database(cfg)


def test_initialize_creates_tables(tmp_path):
    db = make_db(tmp_path)
    db.initialize()

    conn = db.get_connection()
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "cryptocurrencies" in tables
    assert "signals" in tables


def test_initialize_creates_parent_dir(tmp_path):
    cfg = PersistenceConfig()
    cfg.db_path = str(tmp_path / "nested" / "dir" / "test.db")
    db = Database(cfg)
    db.initialize()

    import os
    assert os.path.exists(cfg.db_path)


def test_initialize_idempotent(tmp_path):
    db = make_db(tmp_path)
    db.initialize()
    db.initialize()  # must not raise


def test_get_connection_returns_sqlite_connection(tmp_path):
    db = make_db(tmp_path)
    db.initialize()
    conn = db.get_connection()
    assert isinstance(conn, sqlite3.Connection)


def test_get_connection_row_factory(tmp_path):
    db = make_db(tmp_path)
    db.initialize()
    conn = db.get_connection()
    assert conn.row_factory == sqlite3.Row
