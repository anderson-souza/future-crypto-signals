import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from src.persistence.exceptions import PersistenceError
from src.signals.models import Signal

if TYPE_CHECKING:
    from src.persistence.repositories.signal import SignalRepository

logger = logging.getLogger(__name__)


class SignalDeduplicator:
    def __init__(
        self,
        cooldown_seconds: int,
        signal_repo: "SignalRepository | None" = None,
    ) -> None:
        self._cooldown = timedelta(seconds=cooldown_seconds)
        self._signal_repo = signal_repo
        self._sent: dict[tuple[str, str, str], datetime] = {}

    def is_duplicate(self, signal: Signal) -> bool:
        if self._signal_repo is not None:
            return self._is_duplicate_db(signal)
        return self._is_duplicate_memory(signal)

    def mark_sent(self, signal: Signal) -> None:
        if self._signal_repo is None:
            key = (signal.symbol, signal.timeframe, signal.direction.value)
            self._sent[key] = datetime.now(UTC)

    def _is_duplicate_memory(self, signal: Signal) -> bool:
        key = (signal.symbol, signal.timeframe, signal.direction.value)
        last = self._sent.get(key)
        return last is not None and datetime.now(UTC) - last < self._cooldown

    def _is_duplicate_db(self, signal: Signal) -> bool:
        since = datetime.now(UTC) - self._cooldown
        try:
            result = self._signal_repo.find_last_sent_at(  # type: ignore[union-attr]
                signal.symbol, signal.timeframe, signal.direction.value, since
            )
            return result is not None
        except PersistenceError:
            logger.error(
                "Dedup DB query failed for %s %s — fail-open",
                signal.symbol,
                signal.timeframe,
            )
            return False
