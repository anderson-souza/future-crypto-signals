import pytest

from src.persistence.database import Database
from src.persistence.repositories.cryptocurrency import CryptocurrencyRepository


def test_upsert_inserts_new_symbol(db: Database):
    repo = CryptocurrencyRepository(db)
    crypto_id = repo.upsert("BTCUSDT")
    assert crypto_id > 0


def test_upsert_parses_assets(db: Database):
    repo = CryptocurrencyRepository(db)
    repo.upsert("ETHUSDT")

    row = db.get_connection().execute(
        "SELECT base_asset, quote_asset FROM cryptocurrencies WHERE symbol = 'ETHUSDT'"
    ).fetchone()
    assert row["base_asset"] == "ETH"
    assert row["quote_asset"] == "USDT"


def test_upsert_idempotent(db: Database):
    repo = CryptocurrencyRepository(db)
    id1 = repo.upsert("BTCUSDT")
    id2 = repo.upsert("BTCUSDT")

    assert id1 == id2
    count = db.get_connection().execute(
        "SELECT COUNT(*) FROM cryptocurrencies WHERE symbol = 'BTCUSDT'"
    ).fetchone()[0]
    assert count == 1


def test_upsert_different_symbols_get_distinct_ids(db: Database):
    repo = CryptocurrencyRepository(db)
    id_btc = repo.upsert("BTCUSDT")
    id_eth = repo.upsert("ETHUSDT")
    assert id_btc != id_eth


def test_upsert_sol(db: Database):
    repo = CryptocurrencyRepository(db)
    repo.upsert("SOLUSDT")

    row = db.get_connection().execute(
        "SELECT base_asset FROM cryptocurrencies WHERE symbol = 'SOLUSDT'"
    ).fetchone()
    assert row["base_asset"] == "SOL"
