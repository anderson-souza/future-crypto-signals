# Candle Chart Renderer Specification

## Problem Statement

Signal text alone lacks visual context. A trader receiving a BUY/SELL alert needs to
see the candle pattern, where indicators stood, and exactly which candle triggered
the signal — without opening a separate charting tool.

## Goals

- [ ] Render a dark-theme OHLCV candlestick chart with SMA, Supertrend, and RSI overlays
- [ ] Mark the exact candle where a BUY or SELL signal fired
- [ ] Return PNG bytes consumable by Telegram notifier and standalone file save
- [ ] Expose configurable candle window (default 100, via env var)

## Out of Scope

- Interactive or HTML charts
- Multiple signals on one chart
- Chart persistence / history log
- Backtesting visualization
- Light theme

---

## Visual Layout

```
┌─────────────────────────────────────────────┐
│  Title: BTCUSDT • 1h • BUY  2026-04-28      │
│                                             │
│  [Main panel]                               │
│    Candlesticks (last N candles)            │
│    SMA short — orange line                  │
│    SMA long  — blue line                    │
│    Supertrend — green (bullish) / red (bearish) line │
│    ▲ green triangle above signal candle (BUY)        │
│    ▼ red triangle below signal candle (SELL)         │
│                                             │
├─────────────────────────────────────────────┤
│  [RSI sub-panel]                            │
│    RSI(14) line                             │
│    50 reference line (dashed, grey)         │
└─────────────────────────────────────────────┘
```

---

## Data Contract

### Input: `ChartData`

```python
@dataclass(frozen=True)
class ChartData:
    candles: list[Candle]      # full OHLCV series (>= chart_window candles)
    signal: Signal             # carries timestamp, direction, and indicator snapshot
    config: IndicatorConfig    # same config used to generate the signal
```

### Output: `bytes` (PNG)

Caller decides what to do with bytes (send to Telegram, write to file).

---

## Indicator Series Gap (Design Decision)

Current indicator functions (`calculate_rsi`, `calculate_sma`, `calculate_supertrend`)
return only the **last scalar value**. Charting requires the full series across all candles.

**Resolution:** Add series-returning variants to the indicator module:

| New function | Returns |
|---|---|
| `calculate_rsi_series(candles, period) → pd.Series` | RSI for all candles |
| `calculate_sma_series(candles, period) → pd.Series` | SMA for all candles |
| `calculate_supertrend_series(candles, period, multiplier) → tuple[pd.Series, pd.Series]` | (value series, direction series) |

Existing scalar functions stay unchanged. Series functions reuse `candles_to_df` util.

---

## Configuration

| Env var | Default | Description |
|---|---|---|
| `CHART_WINDOW` | `100` | Number of candles rendered (tail of series) |

Config validated at startup via existing `pydantic`-style config pattern.

---

## User Stories

### P1: Render BUY signal chart ⭐ MVP

**User Story:** As a trader, I want a chart attached to a BUY alert so I can visually
confirm the setup before entering a trade.

**Acceptance Criteria:**

1. WHEN `render_chart(ChartData)` called with `signal.direction == BUY`
   THEN returns `bytes` with length > 0
2. WHEN rendered, chart SHALL contain:
   - Candlesticks for last `CHART_WINDOW` candles
   - SMA short line (orange)
   - SMA long line (blue)
   - Supertrend line (green when BULLISH, red when BEARISH)
   - Green upward triangle (▲) positioned above the signal candle's high
   - RSI sub-panel with 50 reference line
3. WHEN `signal.timestamp` does not match any candle timestamp
   THEN `render_chart` SHALL raise `ChartRenderError`

**Independent Test:** Build `ChartData` with 150 synthetic candles + BUY signal on last candle.
Call `render_chart`. Assert `isinstance(result, bytes)` and `len(result) > 0`.

---

### P1: Render SELL signal chart ⭐ MVP

**User Story:** As a trader, I want a chart attached to a SELL alert showing a red
downward triangle at the signal candle.

**Acceptance Criteria:**

1. WHEN `signal.direction == SELL`
   THEN chart SHALL contain red downward triangle (▼) below signal candle's low
2. Supertrend line SHALL be red (BEARISH direction)

**Independent Test:** Same as BUY test but with SELL signal. Assert bytes non-empty.

---

### P1: Save chart to file ⭐ MVP

**User Story:** As a trader running the system standalone, I want charts saved to disk
so I can review them without Telegram.

**Acceptance Criteria:**

1. WHEN `save_chart(bytes, path: Path)` called
   THEN file at `path` SHALL exist and have size > 0
2. WHEN `path` parent directory does not exist
   THEN `save_chart` SHALL raise `FileNotFoundError` (no silent mkdir)

**Independent Test:** Call `save_chart(png_bytes, tmp_path / "chart.png")`. Assert file exists.

---

### P2: Configurable candle window

**User Story:** As a trader, I want to control how many candles appear on the chart
via `CHART_WINDOW` env var so I can adjust to different timeframes.

**Acceptance Criteria:**

1. WHEN `CHART_WINDOW=50` set THEN chart renders last 50 candles
2. WHEN `CHART_WINDOW` not set THEN defaults to 100
3. WHEN `len(candles) < CHART_WINDOW` THEN renders all available candles (no error)

---

## Edge Cases

- WHEN `candles` list empty THEN `render_chart` SHALL raise `InsufficientDataError`
- WHEN `len(candles) < config.sma_long_period` THEN `render_chart` SHALL raise `InsufficientDataError`
- WHEN `signal.direction == NO_SIGNAL` THEN no marker rendered (chart still valid)

---

## Module Location

```
src/
└── chart/
    ├── __init__.py
    ├── renderer.py       # render_chart(data: ChartData) -> bytes
    ├── file_writer.py    # save_chart(png: bytes, path: Path) -> None
    ├── models.py         # ChartData dataclass, ChartConfig
    └── exceptions.py     # ChartRenderError
```

Indicator series functions added to existing `src/indicators/` module alongside scalars.

---

## Dependencies

- `mplfinance` — candlestick rendering with addplot support
- `matplotlib` — already pulled in by mplfinance

Add via: `uv add mplfinance`

---

## Success Criteria

- [ ] `render_chart` returns valid PNG bytes for BUY signal
- [ ] `render_chart` returns valid PNG bytes for SELL signal
- [ ] Signal candle marked with correct direction marker
- [ ] SMA short, SMA long, Supertrend lines present on main panel
- [ ] RSI sub-panel present with 50 reference line
- [ ] `save_chart` writes file to disk
- [ ] `CHART_WINDOW` env var respected
- [ ] 80%+ test coverage on `src/chart/`
