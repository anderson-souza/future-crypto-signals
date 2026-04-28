from src.fetcher.models import Candle
from src.indicators.models import IndicatorConfig, IndicatorResult
from src.indicators.rsi import calculate_rsi
from src.indicators.sma import calculate_sma
from src.indicators.supertrend import calculate_supertrend


def calculate_indicators(candles: list[Candle], config: IndicatorConfig = IndicatorConfig()) -> IndicatorResult:
    return IndicatorResult(
        rsi=calculate_rsi(candles, config.rsi_period),
        sma=calculate_sma(candles, config.sma_period),
        supertrend=calculate_supertrend(candles, config.supertrend_period, config.supertrend_multiplier),
    )
