from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class Candle(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: str

    @field_validator("open", "high", "low", "close")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("price must be positive")
        return v
