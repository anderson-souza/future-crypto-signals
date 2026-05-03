# Code Conventions

## Naming Conventions

**Files:** `snake_case.py`  
Examples: `client.py`, `file_writer.py`, `deduplicator.py`

**Functions/Methods:** `snake_case`, verb-noun descriptive  
Examples: `fetch_candles`, `calculate_rsi`, `evaluate_signal`, `format_signal`, `is_duplicate`, `mark_sent`

**Classes:** `PascalCase`  
Examples: `BinanceFetcher`, `IndicatorResult`, `SignalDeduplicator`, `ChartRenderError`

**Enums:** `PascalCase` class, `UPPER_CASE` members  
Examples: `SignalDirection.BUY`, `TrendDirection.BULLISH`

**Private attributes:** `_prefix`  
Examples: `self._config`, `self._exchange`, `self._cooldown`, `self._sent`

**Constants / env var names:** `UPPER_SNAKE_CASE`  
Examples: `SCAN_INTERVAL_SECONDS`, `BINANCE_SYMBOLS`

## Type Hints

All function signatures annotated. Modern Python 3.10+ union syntax:

```python
def fetch_candles(self, symbol: str, timeframe: str, limit: int | None = None) -> list[Candle]:
def calculate_rsi(candles: list[Candle], period: int = 14) -> float:
def evaluate_signal(indicators: IndicatorResult, candle: Candle) -> Signal:
```

Return types always present, including `-> None`.

## Import Ordering

1. Python stdlib (`datetime`, `io`, `os`, `logging`, `pathlib`)
2. Third-party (`pydantic`, `pandas`, `ccxt`, `httpx`, `matplotlib`)
3. Local src (`from src.module import ...`)

## File Structure

Consistent pattern per module:
- `__init__.py` — public API exports only
- `models.py` — dataclasses / Pydantic models
- `config.py` — env var reading via `os.getenv()`
- `client.py` or named file — business logic class
- `exceptions.py` — custom exceptions or re-exports

## Error Handling

Custom exceptions carry context:
```python
raise FetchError(symbol, timeframe, str(e)) from e
```

Exception chaining with `from e` preserved throughout.

Scanner loop uses graceful degradation:
```python
except InsufficientDataError as exc:
    logger.warning("%s %s: %s", symbol, timeframe, exc)
except Exception as exc:
    logger.error("%s %s: unexpected error: %s", symbol, timeframe, exc)
```

## Logging

```python
logger = logging.getLogger(__name__)
logger.info("Scanner started | symbols=%s timeframes=%s interval=%ds", ...)
logger.debug("%s %s: no signal", symbol, timeframe)
logger.warning("%s %s: insufficient candles (%d)", symbol, timeframe, n)
logger.error("%s %s: unexpected error: %s", symbol, timeframe, exc)
```

- `%`-style formatting (not f-strings) in logger calls
- `__name__` as logger name
- Appropriate levels: INFO for events, DEBUG for noise, WARNING/ERROR for problems

## Data Validation

Pydantic models with `field_validator`:
```python
@field_validator("open", "high", "low", "close")
@classmethod
def must_be_positive(cls, v: float) -> float:
    if v <= 0:
        raise ValueError("price must be positive")
    return v
```

## Comments/Documentation

No docstrings. Code is self-documenting via naming + type hints.  
Inline comments only for non-obvious behavior:
- ccxt patch to skip auth: `# avoid fetch_currencies hitting authenticated endpoint`
- Supertrend column selection: `# l/s columns alternate NaN — select only SUPERT + SUPERTd`
