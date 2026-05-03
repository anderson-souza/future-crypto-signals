from datetime import UTC, datetime, timedelta

from src.signals.models import Signal


class SignalDeduplicator:
    def __init__(self, cooldown_seconds: int) -> None:
        self._cooldown = timedelta(seconds=cooldown_seconds)
        self._sent: dict[tuple[str, str, str], datetime] = {}

    def is_duplicate(self, signal: Signal) -> bool:
        key = (signal.symbol, signal.timeframe, signal.direction.value)
        last = self._sent.get(key)
        return last is not None and datetime.now(UTC) - last < self._cooldown

    def mark_sent(self, signal: Signal) -> None:
        key = (signal.symbol, signal.timeframe, signal.direction.value)
        self._sent[key] = datetime.now(UTC)
