import ccxt

from src.fetcher.config import FetcherConfig
from src.fetcher.exceptions import ConnectionError, FetchError
from src.fetcher.models import Candle
from src.fetcher.parser import CandleParser


class BinanceFetcher:
    def __init__(self, config: FetcherConfig) -> None:
        self._config = config
        self._exchange = ccxt.binanceusdm(
            {
                "apiKey": config.api_key,
                "secret": config.api_secret,
                "enableRateLimit": True,
            }
        )
        # fetch_currencies requires auth; OHLCV is public — skip it
        self._exchange.fetch_currencies = lambda *args, **kwargs: {}

    def fetch_candles(self, symbol: str, timeframe: str, limit: int | None = None) -> list[Candle]:
        if limit is not None and limit <= 0:
            raise ValueError("limit must be a positive integer")
        effective_limit = limit if limit is not None else self._config.default_limit
        try:
            raw = self._exchange.fetch_ohlcv(symbol, timeframe, limit=effective_limit)
        except ccxt.BaseError as e:
            raise FetchError(symbol, timeframe, str(e)) from e
        return CandleParser.parse(raw, symbol, timeframe)

    def check_connectivity(self) -> None:
        try:
            self._exchange.load_markets()
        except ccxt.BaseError as e:
            raise ConnectionError(f"Cannot connect to Binance Futures: {e}") from e
