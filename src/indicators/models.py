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
class VolumeResult:
    rvol: float
    is_sufficient: bool


@dataclass(frozen=True)
class IndicatorResult:
    rsi: float
    sma_short: float
    sma_long: float
    supertrend: SupertrendResult
    volume: VolumeResult


@dataclass(frozen=True)
class IndicatorConfig:
    rsi_period: int = 14
    sma_short_period: int = 8
    sma_long_period: int = 21
    supertrend_period: int = 7
    supertrend_multiplier: float = 2.0
    volume_period: int = 20
    volume_min_rvol: float = 0.5
