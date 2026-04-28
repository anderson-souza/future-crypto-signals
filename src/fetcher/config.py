import os


class FetcherConfig:
    def __init__(self) -> None:
        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.symbols = [s.strip() for s in os.getenv("BINANCE_SYMBOLS", "BTCUSDT").split(",") if s.strip()]
        self.timeframes = [t.strip() for t in os.getenv("BINANCE_TIMEFRAMES", "1h").split(",") if t.strip()]
        self.default_limit = int(os.getenv("BINANCE_DEFAULT_LIMIT", "200"))
