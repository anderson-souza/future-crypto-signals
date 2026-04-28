# Indicator Engine Design

**Spec**: `.specs/features/indicator-engine/spec.md`
**Status**: Draft

---

## Architecture Overview

Candles in → pandas DataFrame → `pandas-ta` calculations → typed result models out.
Each indicator is a pure function. The engine bundles them.

```mermaid
graph TD
    A[list[Candle]] --> B[candles_to_df]
    B --> C[DataFrame with OHLCV columns]
    C --> D[calculate_rsi]
    C --> E[calculate_sma]
    C --> F[calculate_supertrend]
    D --> G[float]
    E --> H[float]
    F --> I[SupertrendResult]
    G & H & I --> J[IndicatorResult]
```

---

## Code Reuse Analysis

### Existing Components to Leverage

| Component | Location | How to Use |
|-----------|----------|------------|
| `Candle` model | `src/fetcher/models.py` | Source data — extract close/high/low |
| `pandas-ta` | new dependency | RSI, SMA, Supertrend calculations |
| `pandas` | transitive via pandas-ta | DataFrame for vectorized ops |

### Integration Points

| System | Integration Method |
|--------|--------------------|
| Market Data Fetcher | Consumes `list[Candle]` — same type, no conversion layer needed |
| Signal Generator (next) | Consumes `IndicatorResult` — stable output contract |

---

## Components

### candles_to_df (utility function)

- **Purpose**: Convert `list[Candle]` to a pandas DataFrame with columns expected by `pandas-ta`
- **Location**: `src/indicators/utils.py`
- **Interfaces**:
  - `candles_to_df(candles: list[Candle]) -> pd.DataFrame`
- **Dependencies**: `Candle`, `pandas`
- **Notes**: DataFrame must have columns `open`, `high`, `low`, `close`, `volume` with datetime index

### calculate_rsi

- **Purpose**: Compute RSI using `pandas-ta`, return last value
- **Location**: `src/indicators/rsi.py`
- **Interfaces**:
  - `calculate_rsi(candles: list[Candle], period: int = 14) -> float`
- **Dependencies**: `candles_to_df`, `pandas-ta`, `InsufficientDataError`

### calculate_sma

- **Purpose**: Compute SMA using `pandas-ta`, return last value
- **Location**: `src/indicators/sma.py`
- **Interfaces**:
  - `calculate_sma(candles: list[Candle], period: int = 20) -> float`
- **Dependencies**: `candles_to_df`, `pandas-ta`, `InsufficientDataError`

### calculate_supertrend

- **Purpose**: Compute Supertrend using `pandas-ta`, return value + direction
- **Location**: `src/indicators/supertrend.py`
- **Interfaces**:
  - `calculate_supertrend(candles: list[Candle], period: int = 10, multiplier: float = 3.0) -> SupertrendResult`
- **Dependencies**: `candles_to_df`, `pandas-ta`, `SupertrendResult`, `TrendDirection`, `InsufficientDataError`

### IndicatorEngine (bundle)

- **Purpose**: Run all three indicators in one call, return `IndicatorResult`
- **Location**: `src/indicators/engine.py`
- **Interfaces**:
  - `calculate_indicators(candles: list[Candle], config: IndicatorConfig) -> IndicatorResult`
- **Dependencies**: all three calculators, `IndicatorConfig`, `IndicatorResult`

---

## Data Models

### TrendDirection

```python
from enum import Enum

class TrendDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
```

### SupertrendResult

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SupertrendResult:
    value: float
    direction: TrendDirection
```

### IndicatorResult

```python
@dataclass(frozen=True)
class IndicatorResult:
    rsi: float
    sma: float
    supertrend: SupertrendResult
```

### IndicatorConfig

```python
@dataclass(frozen=True)
class IndicatorConfig:
    rsi_period: int = 14
    sma_period: int = 20
    supertrend_period: int = 10
    supertrend_multiplier: float = 3.0
```

---

## File Structure

```
src/
└── indicators/
    ├── __init__.py        # exports: calculate_indicators, IndicatorResult, IndicatorConfig
    ├── engine.py          # calculate_indicators bundle
    ├── models.py          # IndicatorResult, IndicatorConfig, SupertrendResult, TrendDirection
    ├── exceptions.py      # InsufficientDataError
    ├── rsi.py             # calculate_rsi
    ├── sma.py             # calculate_sma
    ├── supertrend.py      # calculate_supertrend
    └── utils.py           # candles_to_df
```

---

## Error Handling Strategy

| Error Scenario | Exception | Raised In |
|---------------|-----------|-----------|
| Not enough candles for period | `InsufficientDataError(required, got)` | Each calculator |
| `period <= 0` | `ValueError` | Each calculator |
| Empty candles list | `InsufficientDataError` | Each calculator |

---

## Tech Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Indicator library | `pandas-ta-classic` | Community-maintained fork of pandas-ta, same API |
| Data format | pandas DataFrame | Required by pandas-ta-classic; single conversion at boundary |
| Models | frozen dataclasses | Simpler than pydantic for pure data containers |
| Pure functions | yes | Stateless, testable without mocking |
