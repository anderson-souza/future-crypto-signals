from datetime import datetime, timezone

from pydantic import ValidationError

from src.fetcher.exceptions import DataValidationError
from src.fetcher.models import Candle


class CandleParser:
    @staticmethod
    def parse(raw: list[list], symbol: str, timeframe: str) -> list[Candle]:
        candles = []
        for row in raw:
            ts_ms, open_, high, low, close, volume = row
            try:
                candle = Candle(
                    timestamp=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    symbol=symbol,
                    timeframe=timeframe,
                )
            except ValidationError as e:
                field = e.errors()[0]["loc"][0]
                raise DataValidationError(symbol, str(field)) from e
            candles.append(candle)
        return candles
