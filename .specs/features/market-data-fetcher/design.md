# Market Data Fetcher Design

**Spec**: `.specs/features/market-data-fetcher/spec.md`
**Status**: Draft

---

## Architecture Overview

Single responsibility chain: config → ccxt client → raw OHLCV → pydantic parse → `list[Candle]`.

```mermaid
graph TD
    A[FetcherConfig] --> B[BinanceFetcher]
    B -->|ccxt| C[Binance Futures API]
    C -->|raw list of lists| B
    B --> D[CandleParser]
    D -->|pydantic validation| E[list[Candle]]
    E --> F[Indicator Engine - next feature]
```

---

## Code Reuse Analysis

### Existing Components to Leverage

| Component | Location | How to Use |
|-----------|----------|------------|
| `ccxt.binance` | installed via ccxt | Use `fetch_ohlcv` with `options={'defaultType': 'future'}` |
| `pydantic.BaseModel` | installed via pydantic | Candle model + FetcherConfig validation |
| `pydantic_settings.BaseSettings` | pydantic-settings | Read config from env vars |

### Integration Points

| System | Integration Method |
|--------|--------------------|
| Indicator Engine (future) | Consumes `list[Candle]` — stable interface contract |

---

## Components

### FetcherConfig

- **Purpose**: Validate and expose all fetcher configuration at startup
- **Location**: `src/fetcher/config.py`
- **Interfaces**:
  - `symbols: list[str]` — e.g. `["BTCUSDT", "ETHUSDT"]`
  - `timeframes: list[str]` — e.g. `["1h", "4h"]`
  - `default_limit: int` — default candle count (default: 200)
  - `api_key: str` — Binance API key (from env)
  - `api_secret: str` — Binance API secret (from env)
- **Dependencies**: `pydantic-settings`, env vars
- **Reuses**: `BaseSettings` for env var parsing

### BinanceFetcher

- **Purpose**: Wraps ccxt to fetch OHLCV candles and return typed `Candle` objects
- **Location**: `src/fetcher/client.py`
- **Interfaces**:
  - `fetch_candles(symbol: str, timeframe: str, limit: int) -> list[Candle]`
  - `check_connectivity() -> None` — raises `ConnectionError` if exchange unreachable
- **Dependencies**: `ccxt`, `FetcherConfig`, `CandleParser`
- **Reuses**: ccxt built-in rate limiter (`enableRateLimit=True`)

### CandleParser

- **Purpose**: Parses raw ccxt OHLCV list-of-lists into validated `list[Candle]`
- **Location**: `src/fetcher/parser.py`
- **Interfaces**:
  - `parse(raw: list[list], symbol: str) -> list[Candle]`
- **Dependencies**: `Candle` model
- **Reuses**: pydantic model validation

---

## Data Models

### Candle

```python
from datetime import datetime
from pydantic import BaseModel, field_validator

class Candle(BaseModel):
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
```

### FetcherConfig

```python
from pydantic_settings import BaseSettings

class FetcherConfig(BaseSettings):
    symbols: list[str]
    timeframes: list[str]
    default_limit: int = 200
    api_key: str
    api_secret: str

    class Config:
        env_prefix = "BINANCE_"
```

---

## File Structure

```
src/
└── fetcher/
    ├── __init__.py        # exports: BinanceFetcher, FetcherConfig, Candle
    ├── client.py          # BinanceFetcher
    ├── config.py          # FetcherConfig
    ├── models.py          # Candle
    ├── parser.py          # CandleParser
    └── exceptions.py      # DataValidationError, FetchError, ConfigError
tests/
└── fetcher/
    ├── test_client.py     # integration tests (live or vcr)
    └── test_parser.py     # unit tests (no exchange needed)
```

---

## Error Handling Strategy

| Error Scenario | Exception | Raised In |
|---------------|-----------|-----------|
| Missing/invalid env config | `ConfigError` | `FetcherConfig` init |
| Exchange unreachable | `ConnectionError` | `check_connectivity()` |
| Network timeout / ccxt error | `FetchError(symbol, timeframe)` | `fetch_candles()` |
| Missing or null candle field | `DataValidationError(symbol, field)` | `CandleParser.parse()` |
| Invalid symbol (no futures contract) | `ConfigError` | `check_connectivity()` |

---

## Tech Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ccxt market type | `defaultType='future'` | Ensures Binance Futures, not spot |
| Rate limiting | ccxt built-in `enableRateLimit=True` | Avoids reimplementing, battle-tested |
| Config source | env vars via pydantic-settings | Keeps secrets out of code |
| Candle immutability | `BaseModel` (default immutable) | Safe to pass downstream |
| Parser as separate class | `CandleParser` | Testable without exchange connection |
