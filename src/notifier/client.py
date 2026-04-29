import httpx

from src.signals.models import Signal, SignalDirection
from src.notifier.config import NotifierConfig
from src.notifier.formatter import format_signal


class TelegramNotifier:
    def __init__(self, config: NotifierConfig) -> None:
        self._config = config
        self._url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"

    def send(self, signal: Signal) -> None:
        if signal.direction == SignalDirection.NO_SIGNAL:
            return
        response = httpx.post(self._url, json={
            "chat_id": self._config.chat_id,
            "text": format_signal(signal),
        })
        response.raise_for_status()
