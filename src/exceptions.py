class ConfigError(Exception):
    pass


class ConnectionError(Exception):
    pass


class FetchError(Exception):
    def __init__(self, symbol: str, timeframe: str, message: str = "") -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        super().__init__(message or f"Failed to fetch {symbol} {timeframe}")


class DataValidationError(Exception):
    def __init__(self, symbol: str, field: str, message: str = "") -> None:
        self.symbol = symbol
        self.field = field
        super().__init__(message or f"Invalid field '{field}' for symbol {symbol}")


class InsufficientDataError(Exception):
    def __init__(self, required: int, got: int) -> None:
        self.required = required
        self.got = got
        super().__init__(f"Insufficient data: required {required} candles, got {got}")
