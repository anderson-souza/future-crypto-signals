import os

from src.exceptions import ConfigError


class NotifierConfig:
    def __init__(self) -> None:
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if not self.bot_token or not self.chat_id:
            raise ConfigError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")
