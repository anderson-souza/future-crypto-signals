import httpx

from src.signals.models import Signal, SignalDirection
from src.notifier.config import NotifierConfig
from src.notifier.formatter import format_signal


class TelegramNotifier:
    def __init__(self, config: NotifierConfig) -> None:
        self._config = config
        self._base = f"https://api.telegram.org/bot{config.bot_token}"

    def send(self, signal: Signal) -> None:
        if signal.direction == SignalDirection.NO_SIGNAL:
            return
        response = httpx.post(f"{self._base}/sendMessage", json={
            "chat_id": self._config.chat_id,
            "text": format_signal(signal),
        })
        response.raise_for_status()

    def send_chart(self, signal: Signal, png_bytes: bytes) -> None:
        if signal.direction == SignalDirection.NO_SIGNAL:
            return
        response = httpx.post(
            f"{self._base}/sendPhoto",
            data={"chat_id": self._config.chat_id},
            files={"photo": ("chart.png", png_bytes, "image/png")},
        )
        response.raise_for_status()
