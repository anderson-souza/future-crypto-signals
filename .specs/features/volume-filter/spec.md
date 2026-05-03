# Volume Filter Specification

## Problem Statement

The signal generator can fire BUY/SELL signals on candles with abnormally low trading volume.
Low-volume candles indicate weak market participation — price moves are more likely to be noise
than genuine directional momentum. Entering a trade on such a signal increases the risk of
getting trapped in a false breakout or an illiquid move.

This feature adds a volume filter that computes **Relative Volume (RVOL)** — the ratio of the
current candle's volume to the rolling N-period average — and blocks signals when RVOL falls
below a configurable threshold.

## Goals

- [ ] Calculate RVOL for a candle series and return current value
- [ ] Expose an `is_sufficient` flag indicating whether volume is acceptable for trading
- [ ] Integrate the volume filter into the signal generator so BUY/SELL are suppressed on low-volume candles

## Out of Scope

- Volume-based entry sizing (e.g., position size proportional to RVOL)
- Volume profile or VWAP analysis
- Multi-timeframe volume confluence
- Alerting specifically about low-volume conditions

---

## Concept: Relative Volume (RVOL)

```
RVOL = current_candle.volume / mean(last N candles' volume)
```

- RVOL = 1.0 → volume matches the N-period average (normal)
- RVOL = 0.3 → volume is 30% of average (suspiciously low)
- RVOL = 2.5 → volume is 2.5× the average (high conviction)

Default config: period = 20, min_rvol = 0.5 (reject candles with < 50% of average volume).

---

## User Stories

### P1: Calculate RVOL ⭐ MVP

**User Story**: As a trader, I want to compute RVOL from a candle series so that I can detect
low-volume candles and avoid entering trades with weak participation.

**Why P1**: Core filter. Required for signal suppression.

**Acceptance Criteria**:

1. WHEN `calculate_volume_filter(candles, period=20)` is called with enough candles THEN system
   SHALL return a `VolumeResult` with `rvol: float` and `is_sufficient: bool`
2. WHEN `rvol >= min_rvol` THEN `is_sufficient` SHALL be `True`
3. WHEN `rvol < min_rvol` THEN `is_sufficient` SHALL be `False`
4. WHEN fewer than `period + 1` candles are provided THEN system SHALL raise `InsufficientDataError`
5. WHEN `period` is 0 or negative THEN system SHALL raise `ValueError`

**Independent Test**: Feed 21 candles where the last has volume = 50% of the 20-candle mean
with `min_rvol=0.5` → assert `rvol ≈ 0.5` and `is_sufficient=True` (boundary inclusive).

---

### P1: Signal suppression on low volume ⭐ MVP

**User Story**: As a trader, I want BUY and SELL signals to be suppressed when volume is too
low so that I don't receive false entries during thin markets.

**Why P1**: The filter has no value unless it gates the signal generator.

**Acceptance Criteria**:

1. WHEN `volume_result.is_sufficient == False` THEN `generate_signal()` SHALL return
   `Signal` with `direction=NO_SIGNAL` regardless of RSI, SMA, or Supertrend values
2. WHEN `volume_result.is_sufficient == True` THEN the existing RSI/SMA/Supertrend logic
   SHALL evaluate normally and may return BUY, SELL, or NO_SIGNAL
3. WHEN signal is suppressed by volume THEN the signal SHALL carry `volume_suppressed=True`
   so callers can distinguish volume-blocked signals from indicator-disagreement NO_SIGNALs

**Independent Test**: Pass all 3 long conditions (rsi=45, close > sma, BULLISH supertrend)
with `is_sufficient=False` → assert `direction=NO_SIGNAL` and `volume_suppressed=True`.

---

### P2: Volume result included in signal context

**User Story**: As a trader, I want the signal to include RVOL so that I can judge conviction
without re-fetching data.

**Why P2**: Signal already carries full indicator snapshot — RVOL extends that context.

**Acceptance Criteria**:

1. WHEN any signal is generated (BUY, SELL, or NO_SIGNAL) THEN it SHALL include `rvol: float`
2. WHEN signal is suppressed by volume THEN `rvol` SHALL still reflect the actual computed value

---

## Models

### `VolumeResult`

```python
@dataclass(frozen=True)
class VolumeResult:
    rvol: float          # relative volume (current / N-period mean)
    is_sufficient: bool  # True when rvol >= min_rvol
```

### `VolumeConfig` (added to `IndicatorConfig`)

```python
volume_period: int = 20          # N-period rolling average
volume_min_rvol: float = 0.5     # minimum acceptable RVOL
```

### Signal model changes

Add to existing `Signal`:
```python
rvol: float
volume_suppressed: bool
```

---

## Integration Point

`calculate_indicators()` in `engine.py` SHALL compute `VolumeResult` and include it in `IndicatorResult`.
`generate_signal()` SHALL read `indicator_result.volume` and short-circuit to `NO_SIGNAL` when
`is_sufficient=False`.

---

## Edge Cases

- WHEN all candles have volume = 0 THEN system SHALL raise `ValueError("all candles have zero volume")`
- WHEN `min_rvol = 0.0` THEN `is_sufficient` SHALL always be `True` (filter disabled)
- WHEN `min_rvol > 1.0` THEN filter is valid — it requires above-average volume to signal

---

## Success Criteria

- [ ] `calculate_volume_filter(candles, period=20)` returns `VolumeResult` with correct `rvol` for known input
- [ ] `is_sufficient=False` when current volume < 50% of 20-period mean (default config)
- [ ] Signal generator returns `NO_SIGNAL` + `volume_suppressed=True` when filter rejects
- [ ] Signal carries `rvol` in all outcomes (BUY, SELL, NO_SIGNAL)
- [ ] `InsufficientDataError` raised when fewer than `period + 1` candles provided
