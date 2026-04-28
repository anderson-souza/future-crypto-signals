import pandas_ta_classic as ta

from src.exceptions import InsufficientDataError
from src.fetcher.models import Candle
from src.indicators.models import SupertrendResult, TrendDirection
from src.indicators.utils import candles_to_df


def calculate_supertrend(candles: list[Candle], period: int = 10, multiplier: float = 3.0) -> SupertrendResult:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) < period + 1:
        raise InsufficientDataError(required=period + 1, got=len(candles))
    df = candles_to_df(candles)
    result = ta.supertrend(df["high"], df["low"], df["close"], length=period, multiplier=multiplier)
    col_trend = f"SUPERTd_{period}_{multiplier}"
    col_value = f"SUPERT_{period}_{multiplier}"
    last = result[[col_value, col_trend]].dropna().iloc[-1]
    direction = TrendDirection.BULLISH if int(last[col_trend]) == 1 else TrendDirection.BEARISH
    return SupertrendResult(value=float(last[col_value]), direction=direction)
