# Volume Filter Tasks

**Design**: `.specs/features/volume-filter/design.md`
**Status**: Ready

---

## Execution Plan

```
Phase 1 (Sequential):
  T1  models update  (VolumeResult + IndicatorConfig/IndicatorResult fields)

Phase 2 (Parallel — T1 complete):
  ├── T2 [P]  calculate_volume_filter + tests
  └── T3 [P]  Signal model update

Phase 3 (Sequential — T2 + T3 complete):
  T4  engine update
  T5  evaluator update + tests
```

---

## Task Breakdown

### T1: Extend indicator models

**What**: Add `VolumeResult` dataclass; add `volume_period`, `volume_min_rvol` to `IndicatorConfig`; add `volume: VolumeResult` to `IndicatorResult`
**Where**: `src/indicators/models.py`
**Depends on**: None

**Done when**:
- [ ] `VolumeResult(frozen dataclass)` with `rvol: float`, `is_sufficient: bool`
- [ ] `IndicatorConfig` has `volume_period: int = 20` and `volume_min_rvol: float = 0.5`
- [ ] `IndicatorResult` has `volume: VolumeResult`

**Verify**:
```bash
uv run python -c "from src.indicators.models import VolumeResult, IndicatorConfig, IndicatorResult; print(VolumeResult(rvol=1.0, is_sufficient=True), IndicatorConfig().volume_period)"
```

---

### T2: Implement calculate_volume_filter + unit tests [P]

**What**: Pure function — computes RVOL from candle volumes, returns `VolumeResult`
**Where**: `src/indicators/volume.py` (new file), `tests/indicators/test_volume.py` (new file)
**Depends on**: T1

**Implementation**:
```python
def calculate_volume_filter(
    candles: list[Candle],
    period: int = 20,
    min_rvol: float = 0.5,
) -> VolumeResult:
    if period <= 0:
        raise ValueError("period must be positive")
    if min_rvol < 0:
        raise ValueError("min_rvol cannot be negative")
    if len(candles) < period + 1:
        raise InsufficientDataError(required=period + 1, got=len(candles))
    df = candles_to_df(candles)
    avg_vol = df["volume"].iloc[-(period + 1):-1].mean()
    if avg_vol == 0:
        raise ValueError("average volume is zero — cannot compute RVOL")
    current_vol = df["volume"].iloc[-1]
    rvol = current_vol / avg_vol
    return VolumeResult(rvol=rvol, is_sufficient=rvol >= min_rvol)
```

**Tests** (write first — TDD):
```python
# test: 21 candles, last vol = avg of prev 20 → rvol ≈ 1.0, is_sufficient=True
# test: last vol = 40% of avg, min_rvol=0.5 → is_sufficient=False
# test: last vol = exactly 50% of avg, min_rvol=0.5 → is_sufficient=True (inclusive boundary)
# test: fewer than period+1 candles → InsufficientDataError
# test: period=0 → ValueError
# test: min_rvol=0.0 → is_sufficient always True
# test: all prev candles have vol=0 → ValueError("average volume is zero")
```

**Done when**:
- [ ] All tests pass
- [ ] `rvol` computed using previous N candles (excludes current)
- [ ] `is_sufficient` boundary is inclusive (`>=`)
- [ ] All error cases raise correct exceptions

**Verify**:
```bash
uv run pytest tests/indicators/test_volume.py -v
```

---

### T3: Extend Signal model [P]

**What**: Add `rvol: float` and `volume_suppressed: bool` to `Signal`
**Where**: `src/signals/models.py`
**Depends on**: None (independent of T2)

**Done when**:
- [ ] `Signal` has `rvol: float`
- [ ] `Signal` has `volume_suppressed: bool`
- [ ] Existing fields unchanged

**Verify**:
```bash
uv run python -c "
from src.signals.models import Signal, SignalDirection
from datetime import datetime, timezone
s = Signal(symbol='X', timeframe='1h', direction=SignalDirection.NO_SIGNAL,
           close=1.0, rsi=50.0, sma_short=1.0, sma_long=1.0,
           supertrend_value=1.0, supertrend_direction='bullish',
           rvol=0.8, volume_suppressed=False, timestamp=datetime.now(timezone.utc))
print(s.rvol, s.volume_suppressed)
"
```

---

### T4: Wire volume into engine

**What**: Call `calculate_volume_filter` inside `calculate_indicators`, pass result to `IndicatorResult`
**Where**: `src/indicators/engine.py`
**Depends on**: T1, T2

**Done when**:
- [ ] `calculate_indicators` imports and calls `calculate_volume_filter(candles, config.volume_period, config.volume_min_rvol)`
- [ ] Returns `IndicatorResult(..., volume=volume_result)`
- [ ] Does not catch `InsufficientDataError` — lets it propagate

**Verify**:
```bash
uv run python -c "from src.indicators.engine import calculate_indicators; print('OK')"
```

---

### T5: Update evaluator + integration tests

**What**: Add volume guard at top of `evaluate_signal`; update all `Signal` constructions to include `rvol` and `volume_suppressed`; add tests
**Where**: `src/signals/evaluator.py`, `tests/signals/test_evaluator.py`
**Depends on**: T3, T4

**Logic** (add before existing BUY/SELL conditions):
```python
if not indicators.volume.is_sufficient:
    return Signal(
        ...,
        rvol=indicators.volume.rvol,
        volume_suppressed=True,
    )
```

Both the early-return and the normal path must set `rvol=indicators.volume.rvol`.

**Tests** (write first — TDD):
```python
# test: all 3 long conditions met + is_sufficient=False → NO_SIGNAL + volume_suppressed=True
# test: all 3 long conditions met + is_sufficient=True → BUY + volume_suppressed=False
# test: all 3 short conditions met + is_sufficient=False → NO_SIGNAL + volume_suppressed=True
# test: indicator disagreement + is_sufficient=True → NO_SIGNAL + volume_suppressed=False
# test: rvol carried on all signal outcomes (BUY, SELL, NO_SIGNAL)
```

**Done when**:
- [ ] All new tests pass
- [ ] Existing evaluator tests still pass (update Signal constructor calls in old tests to include `rvol` and `volume_suppressed`)
- [ ] `volume_suppressed=True` only when volume guard fires, `False` otherwise

**Verify**:
```bash
uv run pytest tests/signals/ -v
uv run pytest tests/ -v  # full suite green
```

---

## Parallel Execution Map

```
T1  (sequential — models first)
│
├── T2 [P]  volume.py + tests
└── T3 [P]  signal model

T2 + T3 complete →
  T4  engine
  T5  evaluator + tests
```

---

## Definition of Done

- [ ] `uv run pytest tests/indicators/test_volume.py -v` — all pass
- [ ] `uv run pytest tests/signals/ -v` — all pass (including existing tests)
- [ ] `uv run pytest tests/ -v` — full suite green
- [ ] No new `Signal` construction missing `rvol` / `volume_suppressed` fields
