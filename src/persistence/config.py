import os


class PersistenceConfig:
    def __init__(self) -> None:
        self.db_path: str = os.getenv("DB_PATH", ".data/signals.db")
