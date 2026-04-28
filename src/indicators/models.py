from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass(frozen=True)
class SupertrendResult:
    value: float
    direction: TrendDirection


@dataclass(frozen=True)
class IndicatorResult:
    rsi: float
    sma_short: float
    sma_long: float
    supertrend: SupertrendResult


@dataclass(frozen=True)
class IndicatorConfig:
    rsi_period: int = 14
    sma_short_period: int = 8
    sma_long_period: int = 21
    supertrend_period: int = 10
    supertrend_multiplier: float = 3.0
