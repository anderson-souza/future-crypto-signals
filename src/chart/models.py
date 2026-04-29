import os
from dataclasses import dataclass, field

from src.fetcher.models import Candle
from src.indicators.models import IndicatorConfig
from src.signals.models import Signal


@dataclass(frozen=True)
class ChartData:
    candles: list[Candle]
    signal: Signal
    config: IndicatorConfig = field(default_factory=IndicatorConfig)


@dataclass(frozen=True)
class ChartConfig:
    window: int = 100

    @classmethod
    def from_env(cls) -> "ChartConfig":
        return cls(window=int(os.getenv("CHART_WINDOW", "100")))
