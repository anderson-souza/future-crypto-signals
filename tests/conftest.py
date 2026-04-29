from datetime import datetime, timezone, timedelta

import pytest

from src.fetcher.models import Candle


def make_candles(n: int = 150, base_price: float = 50000.0, symbol: str = "BTCUSDT", timeframe: str = "1h") -> list[Candle]:
    candles = []
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    price = base_price
    for i in range(n):
        close = price + (i % 10) * 10
        candles.append(
            Candle(
                timestamp=start + timedelta(hours=i),
                open=close - 5,
                high=close + 20,
                low=close - 20,
                close=close,
                volume=1000.0 + i,
                symbol=symbol,
                timeframe=timeframe,
            )
        )
    return candles


@pytest.fixture
def candles_150() -> list[Candle]:
    return make_candles(150)
