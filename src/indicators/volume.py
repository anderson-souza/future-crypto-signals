from src.exceptions import InsufficientDataError
from src.fetcher.models import Candle
from src.indicators.models import VolumeResult
from src.indicators.utils import candles_to_df


def calculate_volume_filter(
    candles: list[Candle],
    period: int = 20,
    min_rvol: float = 0.5,
) -> VolumeResult:
    if period <= 0:
        raise ValueError("period must be positive")
    if min_rvol < 0:
        raise ValueError("min_rvol cannot be negative")
    if len(candles) < period + 1:
        raise InsufficientDataError(required=period + 1, got=len(candles))
    df = candles_to_df(candles)
    avg_vol = df["volume"].iloc[-(period + 1):-1].mean()
    if avg_vol <= 0:
        raise ValueError(f"average volume is non-positive ({avg_vol}) — cannot compute RVOL")
    current_vol = float(df["volume"].iloc[-1])
    rvol = current_vol / float(avg_vol)
    return VolumeResult(rvol=rvol, is_sufficient=rvol >= min_rvol)
