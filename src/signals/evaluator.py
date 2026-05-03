from src.fetcher.models import Candle
from src.indicators.models import IndicatorResult, TrendDirection
from src.signals.models import Signal, SignalDirection


def evaluate_signal(indicators: IndicatorResult, candle: Candle) -> Signal:
    if not indicators.volume.is_sufficient:
        return Signal(
            symbol=candle.symbol,
            timeframe=candle.timeframe,
            direction=SignalDirection.NO_SIGNAL,
            close=candle.close,
            rsi=indicators.rsi,
            sma_short=indicators.sma_short,
            sma_long=indicators.sma_long,
            supertrend_value=indicators.supertrend.value,
            supertrend_direction=indicators.supertrend.direction.value,
            rvol=indicators.volume.rvol,
            volume_suppressed=True,
            timestamp=candle.timestamp,
        )

    is_buy = (
        indicators.rsi < 50
        and indicators.sma_short > indicators.sma_long
        and indicators.supertrend.direction == TrendDirection.BULLISH
    )
    is_sell = (
        indicators.rsi > 50
        and indicators.sma_short < indicators.sma_long
        and indicators.supertrend.direction == TrendDirection.BEARISH
    )
    if is_buy:
        direction = SignalDirection.BUY
    elif is_sell:
        direction = SignalDirection.SELL
    else:
        direction = SignalDirection.NO_SIGNAL

    return Signal(
        symbol=candle.symbol,
        timeframe=candle.timeframe,
        direction=direction,
        close=candle.close,
        rsi=indicators.rsi,
        sma_short=indicators.sma_short,
        sma_long=indicators.sma_long,
        supertrend_value=indicators.supertrend.value,
        supertrend_direction=indicators.supertrend.direction.value,
        rvol=indicators.volume.rvol,
        volume_suppressed=False,
        timestamp=candle.timestamp,
    )
