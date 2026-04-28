# Indicator Engine Tasks

**Design**: `.specs/features/indicator-engine/design.md`
**Status**: Approved

---

## Execution Plan

### Phase 1: Foundation (Sequential)

```
T1 → T2
```

Exceptions and models first — all calculators depend on them.

### Phase 2: Core Implementation (Parallel OK)

```
T2 complete, then:
  ├── T3 [P]  candles_to_df utility
  ├── T4 [P]  calculate_rsi
  ├── T5 [P]  calculate_sma
  └── T6 [P]  calculate_supertrend

T3-T6 complete, then:
  T7  engine bundle
  T8  __init__.py exports
```

---

## Task Breakdown

### T1: Add InsufficientDataError to exceptions

**What**: Add `InsufficientDataError(required, got)` to existing exceptions module
**Where**: `src/fetcher/exceptions.py` → move to `src/exceptions.py` (shared)
**Depends on**: None

**Done when**:
- [ ] `InsufficientDataError` defined with `required: int` and `got: int` fields
- [ ] Placed in `src/exceptions.py` (shared across fetcher + indicators)
- [ ] `src/fetcher/exceptions.py` imports from `src/exceptions.py` for backward compat

**Verify**:
```bash
uv run python -c "from src.exceptions import InsufficientDataError; print('OK')"
```

---

### T2: Create indicator models

**What**: Define `TrendDirection`, `SupertrendResult`, `IndicatorResult`, `IndicatorConfig` as frozen dataclasses
**Where**: `src/indicators/models.py`
**Depends on**: None

**Done when**:
- [ ] `TrendDirection(Enum)` with `BULLISH` and `BEARISH`
- [ ] `SupertrendResult(frozen dataclass)` with `value: float`, `direction: TrendDirection`
- [ ] `IndicatorResult(frozen dataclass)` with `rsi: float`, `sma: float`, `supertrend: SupertrendResult`
- [ ] `IndicatorConfig(frozen dataclass)` with `rsi_period=14`, `sma_period=20`, `supertrend_period=10`, `supertrend_multiplier=3.0`

**Verify**:
```bash
uv run python -c "from src.indicators.models import IndicatorConfig, TrendDirection; print(IndicatorConfig(), TrendDirection.BULLISH)"
```

---

### T3: Create candles_to_df utility [P]

**What**: Convert `list[Candle]` to pandas DataFrame with OHLCV columns and datetime index
**Where**: `src/indicators/utils.py`
**Depends on**: T2

**Done when**:
- [ ] `candles_to_df(candles)` returns DataFrame with columns: `open`, `high`, `low`, `close`, `volume`
- [ ] Index is `datetime` (UTC) from `candle.timestamp`
- [ ] Empty list returns empty DataFrame without error

**Verify**:
```bash
uv run python -c "
from datetime import datetime, timezone
from src.fetcher.models import Candle
from src.indicators.utils import candles_to_df
c = Candle(timestamp=datetime.now(timezone.utc), open=1.0, high=2.0, low=0.5, close=1.5, volume=100.0, symbol='BTCUSDT', timeframe='1h')
df = candles_to_df([c])
print(df.columns.tolist())
"
```

---

### T4: Implement calculate_rsi [P]

**What**: Compute RSI via `pandas-ta-classic`, return last value as float
**Where**: `src/indicators/rsi.py`
**Depends on**: T2, T3

**Done when**:
- [ ] `calculate_rsi(candles, period=14) -> float` returns value in [0, 100]
- [ ] Raises `InsufficientDataError(required=period+1, got=len(candles))` when not enough data
- [ ] Raises `ValueError` when `period <= 0`

**Verify**:
```bash
uv run python -c "
from src.indicators.rsi import calculate_rsi
# will need real candles — run against live data
"
```

---

### T5: Implement calculate_sma [P]

**What**: Compute SMA via `pandas-ta-classic`, return last value as float
**Where**: `src/indicators/sma.py`
**Depends on**: T2, T3

**Done when**:
- [ ] `calculate_sma(candles, period=20) -> float` returns arithmetic mean of last `period` closes
- [ ] Raises `InsufficientDataError(required=period, got=len(candles))` when not enough data
- [ ] Raises `ValueError` when `period <= 0`

**Verify**:
```bash
uv run python -c "
from src.indicators.sma import calculate_sma
# will need real candles — run against live data
"
```

---

### T6: Implement calculate_supertrend [P]

**What**: Compute Supertrend via `pandas-ta-classic`, return `SupertrendResult`
**Where**: `src/indicators/supertrend.py`
**Depends on**: T2, T3

**Done when**:
- [ ] `calculate_supertrend(candles, period=10, multiplier=3.0) -> SupertrendResult`
- [ ] `direction` is `BULLISH` when close > supertrend line, `BEARISH` otherwise
- [ ] Raises `InsufficientDataError(required=period+1, got=len(candles))` when not enough data
- [ ] Raises `ValueError` when `period <= 0`

**Verify**:
```bash
uv run python -c "
from src.indicators.supertrend import calculate_supertrend
# will need real candles — run against live data
"
```

---

### T7: Create engine bundle

**What**: `calculate_indicators` calls all three calculators and returns `IndicatorResult`
**Where**: `src/indicators/engine.py`
**Depends on**: T4, T5, T6

**Done when**:
- [ ] `calculate_indicators(candles, config=IndicatorConfig()) -> IndicatorResult`
- [ ] Uses `config.rsi_period`, `config.sma_period`, `config.supertrend_period`, `config.supertrend_multiplier`
- [ ] Does not catch exceptions — lets `InsufficientDataError` propagate

**Verify**:
```bash
uv run python -c "from src.indicators.engine import calculate_indicators; print('OK')"
```

---

### T8: Create __init__.py exports

**What**: Export public API from `src/indicators/__init__.py`
**Where**: `src/indicators/__init__.py`
**Depends on**: T7

**Done when**:
- [ ] Exports: `calculate_indicators`, `IndicatorResult`, `IndicatorConfig`, `SupertrendResult`, `TrendDirection`

**Verify**:
```bash
uv run python -c "from src.indicators import calculate_indicators, IndicatorResult, IndicatorConfig; print('OK')"
```

---

## Parallel Execution Map

```
Phase 1 (Sequential):
  T1  T2  (independent, run in parallel)

Phase 2 (Parallel):
  T1 + T2 complete, then:
    ├── T3 [P]
    ├── T4 [P]
    ├── T5 [P]
    └── T6 [P]

Phase 3 (Sequential):
  T3-T6 complete, then:
    T7 → T8
```
