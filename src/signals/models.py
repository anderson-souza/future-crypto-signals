from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SignalDirection(Enum):
    BUY = "buy"
    SELL = "sell"
    NO_SIGNAL = "no_signal"


@dataclass(frozen=True)
class Signal:
    symbol: str
    timeframe: str
    direction: SignalDirection
    close: float
    rsi: float
    sma_short: float
    sma_long: float
    supertrend_value: float
    supertrend_direction: str
    timestamp: datetime
