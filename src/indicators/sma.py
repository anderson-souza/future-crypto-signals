import pandas as pd
import pandas_ta_classic as ta

from src.exceptions import InsufficientDataError
from src.fetcher.models import Candle
from src.indicators.utils import candles_to_df


def calculate_sma(candles: list[Candle], period: int = 20) -> float:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) < period:
        raise InsufficientDataError(required=period, got=len(candles))
    df = candles_to_df(candles)
    sma = ta.sma(df["close"], length=period)
    return float(sma.dropna().iloc[-1])


def calculate_sma_series(candles: list[Candle], period: int = 20) -> pd.Series:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) < period:
        raise InsufficientDataError(required=period, got=len(candles))
    df = candles_to_df(candles)
    return ta.sma(df["close"], length=period)
