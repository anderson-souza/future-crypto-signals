# Volume Filter Design

**Spec**: `.specs/features/volume-filter/spec.md`
**Status**: Draft

---

## Architecture Overview

Pure function pattern — same as existing indicators. No new module; volume filter lives in
`src/indicators/` alongside RSI, SMA, Supertrend. Engine bundles it. Signal evaluator gates
on `VolumeResult.is_sufficient`.

```mermaid
graph TD
    A[list[Candle]] --> B[calculate_volume_filter]
    B --> C[VolumeResult\nrvol: float\nis_sufficient: bool]
    C --> D[IndicatorResult.volume]
    D --> E[evaluate_signal]
    E -->|is_sufficient=False| F[Signal NO_SIGNAL\nvolume_suppressed=True]
    E -->|is_sufficient=True| G[existing RSI/SMA/ST logic]
```

---

## Code Reuse Analysis

### Existing Components to Leverage

| Component | Location | How to Use |
|-----------|----------|------------|
| `Candle.volume` | `src/fetcher/models.py` | Already fetched — no new API calls |
| `candles_to_df` | `src/indicators/utils.py` | Convert to DataFrame for vectorized mean |
| `InsufficientDataError` | `src/exceptions.py` | Raise when fewer than `period + 1` candles |
| `IndicatorConfig` | `src/indicators/models.py` | Add two new fields with defaults |
| `IndicatorResult` | `src/indicators/models.py` | Add `volume: VolumeResult` field |
| `Signal` | `src/signals/models.py` | Add `rvol` and `volume_suppressed` fields |
| `evaluate_signal` | `src/signals/evaluator.py` | Add early-return guard on volume |

### Integration Points

| System | Integration Method |
|--------|--------------------|
| Indicator Engine | `calculate_indicators()` calls `calculate_volume_filter()` and stores result in `IndicatorResult.volume` |
| Signal Evaluator | Reads `indicators.volume.is_sufficient` — if False, short-circuit to `NO_SIGNAL` |

---

## Components

### `calculate_volume_filter`

- **Purpose**: Compute RVOL (current candle volume / mean of previous N candles), return `VolumeResult`
- **Location**: `src/indicators/volume.py` (new file)
- **Interface**:
  ```python
  def calculate_volume_filter(
      candles: list[Candle],
      period: int = 20,
      min_rvol: float = 0.5,
  ) -> VolumeResult:
  ```
- **Dependencies**: `candles_to_df`, `VolumeResult`, `InsufficientDataError`
- **Algorithm**:
  ```
  df = candles_to_df(candles)
  current_vol  = df["volume"].iloc[-1]
  avg_vol      = df["volume"].iloc[-(period+1):-1].mean()   # previous N candles only
  rvol         = current_vol / avg_vol
  is_sufficient = rvol >= min_rvol
  ```
- **Notes**: Uses previous N candles for the average (excludes current) — avoids self-referential bias. Requires `period + 1` candles total.

### Model changes — `src/indicators/models.py`

Add `VolumeResult`:

```python
@dataclass(frozen=True)
class VolumeResult:
    rvol: float
    is_sufficient: bool
```

Add fields to `IndicatorConfig`:

```python
volume_period: int = 20
volume_min_rvol: float = 0.5
```

Add field to `IndicatorResult`:

```python
volume: VolumeResult
```

### Engine update — `src/indicators/engine.py`

```python
from src.indicators.volume import calculate_volume_filter

def calculate_indicators(candles: list[Candle], config: IndicatorConfig = IndicatorConfig()) -> IndicatorResult:
    return IndicatorResult(
        rsi=calculate_rsi(candles, config.rsi_period),
        sma_short=calculate_sma(candles, config.sma_short_period),
        sma_long=calculate_sma(candles, config.sma_long_period),
        supertrend=calculate_supertrend(candles, config.supertrend_period, config.supertrend_multiplier),
        volume=calculate_volume_filter(candles, config.volume_period, config.volume_min_rvol),
    )
```

### Signal model changes — `src/signals/models.py`

Add two fields to `Signal`:

```python
rvol: float
volume_suppressed: bool
```

### Evaluator update — `src/signals/evaluator.py`

```python
def evaluate_signal(indicators: IndicatorResult, candle: Candle) -> Signal:
    if not indicators.volume.is_sufficient:
        return Signal(
            symbol=candle.symbol,
            timeframe=candle.timeframe,
            direction=SignalDirection.NO_SIGNAL,
            close=candle.close,
            rsi=indicators.rsi,
            sma_short=indicators.sma_short,
            sma_long=indicators.sma_long,
            supertrend_value=indicators.supertrend.value,
            supertrend_direction=indicators.supertrend.direction.value,
            rvol=indicators.volume.rvol,
            volume_suppressed=True,
            timestamp=candle.timestamp,
        )

    is_buy = (
        indicators.rsi < 50
        and indicators.sma_short > indicators.sma_long
        and indicators.supertrend.direction == TrendDirection.BULLISH
    )
    is_sell = (
        indicators.rsi > 50
        and indicators.sma_short < indicators.sma_long
        and indicators.supertrend.direction == TrendDirection.BEARISH
    )
    direction = SignalDirection.BUY if is_buy else SignalDirection.SELL if is_sell else SignalDirection.NO_SIGNAL

    return Signal(
        symbol=candle.symbol,
        timeframe=candle.timeframe,
        direction=direction,
        close=candle.close,
        rsi=indicators.rsi,
        sma_short=indicators.sma_short,
        sma_long=indicators.sma_long,
        supertrend_value=indicators.supertrend.value,
        supertrend_direction=indicators.supertrend.direction.value,
        rvol=indicators.volume.rvol,
        volume_suppressed=False,
        timestamp=candle.timestamp,
    )
```

---

## File Structure

```
src/
└── indicators/
    ├── models.py       # + VolumeResult; IndicatorConfig += volume_period, volume_min_rvol; IndicatorResult += volume
    ├── volume.py       # NEW — calculate_volume_filter
    └── engine.py       # + calculate_volume_filter call
src/
└── signals/
    ├── models.py       # Signal += rvol, volume_suppressed
    └── evaluator.py    # + volume guard at top of evaluate_signal
tests/
└── indicators/
    └── test_volume.py  # NEW
```

---

## Error Handling Strategy

| Error Scenario | Exception | Where |
|---------------|-----------|-------|
| `len(candles) < period + 1` | `InsufficientDataError(required=period+1, got=len(candles))` | `calculate_volume_filter` |
| `period <= 0` | `ValueError("period must be positive")` | `calculate_volume_filter` |
| All candles have zero volume (avg = 0) | `ValueError("average volume is zero — cannot compute RVOL")` | `calculate_volume_filter` |
| `min_rvol < 0` | `ValueError("min_rvol cannot be negative")` | `calculate_volume_filter` |

---

## Tech Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Average window | previous N candles, exclude current | Avoids self-referential bias; RVOL > 1 means current exceeded historical norm |
| Library | pandas (already a dep via pandas-ta-classic) | No new dependency; vectorized mean on DataFrame column |
| Guard placement | top of `evaluate_signal`, before condition logic | Cheapest check first; short-circuits without evaluating RSI/SMA/ST conditions |
| `volume_suppressed` field on `Signal` | explicit boolean | Lets notifier/logger distinguish low-volume rejection from indicator disagreement without string parsing |
| `min_rvol = 0.0` → filter disabled | natural edge case | Allows disabling filter via config without code changes |
