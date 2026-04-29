# Candle Chart Renderer Tasks

**Design**: `.specs/features/candle-chart-renderer/design.md`
**Status**: Approved

---

## Execution Plan

```
Phase 1 (Parallel — no deps between):
  T1 [P]  Install mplfinance dependency
  T2 [P]  Add indicator series functions (rsi, sma, supertrend)
  T3 [P]  Create src/chart/ scaffold (models, exceptions, __init__)

T1 + T2 + T3 complete, then:

Phase 2 (Sequential):
  T4      Implement render_chart (depends on T1, T2, T3)
  T5      Implement save_chart (depends on T3)

T4 + T5 complete, then:

Phase 3:
  T6      Wire indicator series exports in src/indicators/__init__.py
  T7      Wire chart exports in src/chart/__init__.py
  T8      Write tests (unit + integration)
```

---

## Task Breakdown

### T1: Install mplfinance [P]

**What**: Add `mplfinance` to project dependencies
**Depends on**: None

**Done when**:
- [ ] `uv add mplfinance` run successfully
- [ ] `pyproject.toml` and `uv.lock` updated

**Verify**:
```bash
uv run python -c "import mplfinance as mpf; print(mpf.__version__)"
```

**Note**: Confirm `"nightclouds"` exists — if missing use `"binance"`:
```bash
uv run python -c "import mplfinance as mpf; print(mpf.available_styles())"
```

---

### T2: Add indicator series functions [P]

**What**: Add `calculate_rsi_series`, `calculate_sma_series`, `calculate_supertrend_series` alongside existing scalars
**Where**:
- `src/indicators/rsi.py` — add `calculate_rsi_series`
- `src/indicators/sma.py` — add `calculate_sma_series`
- `src/indicators/supertrend.py` — add `calculate_supertrend_series`

**Depends on**: None (existing scalar functions stay unchanged)

**Signatures**:
```python
def calculate_rsi_series(candles: list[Candle], period: int = 14) -> pd.Series: ...
def calculate_sma_series(candles: list[Candle], period: int = 20) -> pd.Series: ...
def calculate_supertrend_series(
    candles: list[Candle], period: int = 10, multiplier: float = 3.0
) -> tuple[pd.Series, pd.Series]: ...  # (value_series, direction_series)
```

**Done when**:
- [ ] Each function validates `period > 0` and `len(candles) >= minimum`
- [ ] `InsufficientDataError` raised (same thresholds as scalar siblings)
- [ ] Returns `pd.Series` with DatetimeIndex aligned to candle timestamps
- [ ] `calculate_supertrend_series` returns `(value_series, direction_series)` — direction values are `1` (BULLISH) and `-1` (BEARISH)
- [ ] Existing scalar functions untouched — no regressions

**Verify**:
```bash
uv run python -c "
from src.indicators.rsi import calculate_rsi_series
from src.indicators.sma import calculate_sma_series
from src.indicators.supertrend import calculate_supertrend_series
print('series functions OK')
"
```

---

### T3: Create src/chart/ scaffold [P]

**What**: Empty module scaffold — models, exceptions, __init__
**Where**: `src/chart/`
**Depends on**: None

**Files to create**:

`src/chart/exceptions.py`:
```python
class ChartRenderError(Exception):
    pass
```

`src/chart/models.py`:
```python
import os
from dataclasses import dataclass, field
from src.fetcher.models import Candle
from src.signals.models import Signal
from src.indicators.models import IndicatorConfig

@dataclass(frozen=True)
class ChartData:
    candles: list[Candle]
    signal: Signal
    config: IndicatorConfig = field(default_factory=IndicatorConfig)

@dataclass(frozen=True)
class ChartConfig:
    window: int = 100

    @classmethod
    def from_env(cls) -> "ChartConfig":
        return cls(window=int(os.getenv("CHART_WINDOW", "100")))
```

`src/chart/__init__.py`: empty for now (wired in T7)

**Done when**:
- [ ] All three files exist and are importable
- [ ] `ChartData` and `ChartConfig` import cleanly
- [ ] `ChartRenderError` is a proper `Exception` subclass

**Verify**:
```bash
uv run python -c "
from src.chart.models import ChartData, ChartConfig
from src.chart.exceptions import ChartRenderError
print('scaffold OK')
"
```

---

### T4: Implement render_chart

**What**: Core renderer — `ChartData` → PNG `bytes`
**Where**: `src/chart/renderer.py`
**Depends on**: T1, T2, T3

**Signature**:
```python
def render_chart(data: ChartData, config: ChartConfig | None = None) -> bytes: ...
```

**Implementation steps**:

1. `config = config or ChartConfig.from_env()`
2. Slice `window_candles = data.candles[-config.window:]`
3. Guard: if `len(window_candles) == 0` → raise `InsufficientDataError`
4. Build `df = candles_to_df(window_candles)` (DatetimeIndex)
5. Compute series: `rsi`, `sma_short`, `sma_long`, `st_value`, `st_dir`
6. Split supertrend:
   ```python
   st_bullish = st_value.where(st_dir == 1)
   st_bearish = st_value.where(st_dir == -1)
   ```
7. Build signal markers:
   ```python
   buy_markers  = pd.Series(float("nan"), index=df.index)
   sell_markers = pd.Series(float("nan"), index=df.index)
   if signal.direction == SignalDirection.BUY:
       if signal.timestamp not in df.index:
           raise ChartRenderError(f"signal timestamp {signal.timestamp} not in chart window")
       buy_markers.loc[signal.timestamp] = df.loc[signal.timestamp, "high"] * 1.002
   elif signal.direction == SignalDirection.SELL:
       if signal.timestamp not in df.index:
           raise ChartRenderError(f"signal timestamp {signal.timestamp} not in chart window")
       sell_markers.loc[signal.timestamp] = df.loc[signal.timestamp, "low"] * 0.998
   ```
8. Assemble `addplots` list (sma_short orange, sma_long blue, st_bullish green, st_bearish red, rsi panel=1, rsi-50 reference, buy_markers scatter ^, sell_markers scatter v)
9. `fig, _ = mpf.plot(df, type="candle", style="nightclouds", addplot=addplots, title=..., panel_ratios=(3,1), returnfig=True, figsize=(14,8), tight_layout=True)`
10. `buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=100, bbox_inches="tight"); plt.close(fig); return buf.getvalue()`

**Done when**:
- [ ] Returns `bytes` with `len > 0` for BUY signal
- [ ] Returns `bytes` with `len > 0` for SELL signal
- [ ] Returns `bytes` with `len > 0` for NO_SIGNAL (no markers, no error)
- [ ] `ChartRenderError` raised when signal timestamp not in window
- [ ] `plt.close(fig)` always called (even on error path — use try/finally)
- [ ] Title format: `"BTCUSDT • 1h • BUY"`

**Verify**:
```bash
uv run python -c "
from src.chart.renderer import render_chart
print('render_chart importable OK')
"
```

---

### T5: Implement save_chart

**What**: Write PNG bytes to disk
**Where**: `src/chart/file_writer.py`
**Depends on**: T3

**Signature**:
```python
def save_chart(png: bytes, path: Path) -> None: ...
```

**Done when**:
- [ ] Writes `png` bytes to `path`
- [ ] Raises `FileNotFoundError` if `path.parent` does not exist (no silent mkdir)
- [ ] Does NOT accept empty bytes silently — raise `ValueError("png bytes are empty")` if `len(png) == 0`

**Verify**:
```bash
uv run python -c "from src.chart.file_writer import save_chart; print('OK')"
```

---

### T6: Update src/indicators/__init__.py exports

**What**: Export new series functions from `src/indicators/__init__.py`
**Where**: `src/indicators/__init__.py`
**Depends on**: T2

**Done when**:
- [ ] `calculate_rsi_series`, `calculate_sma_series`, `calculate_supertrend_series` exported

**Verify**:
```bash
uv run python -c "
from src.indicators import calculate_rsi_series, calculate_sma_series, calculate_supertrend_series
print('exports OK')
"
```

---

### T7: Wire src/chart/__init__.py exports

**What**: Export public API
**Where**: `src/chart/__init__.py`
**Depends on**: T4, T5

**Done when**:
- [ ] Exports: `render_chart`, `save_chart`, `ChartData`, `ChartConfig`

**Verify**:
```bash
uv run python -c "
from src.chart import render_chart, save_chart, ChartData, ChartConfig
print('exports OK')
"
```

---

### T8: Write tests

**What**: Unit + integration tests for all new code
**Where**: `tests/chart/` and `tests/indicators/` (series functions)
**Depends on**: T4, T5, T6, T7

**Test files**:

`tests/indicators/test_rsi_series.py`
`tests/indicators/test_sma_series.py`
`tests/indicators/test_supertrend_series.py`
`tests/chart/test_renderer.py`
`tests/chart/test_file_writer.py`

**Done when**:
- [ ] Series functions: returns `pd.Series`, correct length, `InsufficientDataError` on bad input
- [ ] `render_chart`: returns non-empty bytes for BUY, SELL, NO_SIGNAL
- [ ] `render_chart`: raises `ChartRenderError` when timestamp not in window
- [ ] `save_chart`: file exists after call, `FileNotFoundError` when parent missing
- [ ] `save_chart`: `ValueError` on empty bytes
- [ ] Coverage ≥ 80% on `src/chart/`

**Verify**:
```bash
uv run pytest tests/chart/ tests/indicators/ -v --cov=src/chart --cov=src/indicators --cov-report=term-missing
```

---

## Parallel Execution Map

```
Phase 1 (all parallel):
  T1  mplfinance install
  T2  indicator series functions
  T3  chart/ scaffold

Phase 2:
  T4  render_chart        ← needs T1 + T2 + T3
  T5  save_chart          ← needs T3 (can run in parallel with T4)

Phase 3:
  T6  indicators exports  ← needs T2
  T7  chart exports       ← needs T4 + T5

Phase 4:
  T8  tests               ← needs T6 + T7
```
