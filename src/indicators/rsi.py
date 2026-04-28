import pandas_ta_classic as ta

from src.exceptions import InsufficientDataError
from src.fetcher.models import Candle
from src.indicators.utils import candles_to_df


def calculate_rsi(candles: list[Candle], period: int = 14) -> float:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) < period + 1:
        raise InsufficientDataError(required=period + 1, got=len(candles))
    df = candles_to_df(candles)
    rsi = ta.rsi(df["close"], length=period)
    return float(rsi.dropna().iloc[-1])
