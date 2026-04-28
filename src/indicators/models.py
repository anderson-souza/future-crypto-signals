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
    sma: float
    supertrend: SupertrendResult


@dataclass(frozen=True)
class IndicatorConfig:
    rsi_period: int = 14
    sma_period: int = 20
    supertrend_period: int = 10
    supertrend_multiplier: float = 3.0
