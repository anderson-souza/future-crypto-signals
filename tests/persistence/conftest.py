import pytest

from src.persistence.config import PersistenceConfig
from src.persistence.database import Database


@pytest.fixture
def db(tmp_path) -> Database:
    cfg = PersistenceConfig()
    cfg.db_path = str(tmp_path / "test.db")
    database = Database(cfg)
    database.initialize()
    yield database
    database.close()
