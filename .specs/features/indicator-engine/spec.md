# Indicator Engine Specification

## Problem Statement

Raw candle data has no signal value on its own. This feature transforms `list[Candle]`
into computed indicator values (RSI, SMA, Supertrend) that the Signal Generator will
evaluate to produce buy/sell decisions.

## Goals

- [ ] Calculate RSI for a candle series and return current value
- [ ] Calculate SMA for a configurable period and return current value
- [ ] Calculate Supertrend and return current value + trend direction (bullish/bearish)

## Out of Scope

- Signal generation (next feature)
- Multiple timeframe confluence
- Storing or persisting indicator history
- Any indicator beyond RSI, SMA, Supertrend

---

## User Stories

### P1: Calculate RSI ⭐ MVP

**User Story**: As a trader, I want to compute RSI from a candle series so that I can detect overbought/oversold conditions.

**Why P1**: Core indicator. Required for signal generation.

**Acceptance Criteria**:

1. WHEN `calculate_rsi(candles, period=14)` is called with enough candles THEN system SHALL return a `float` between 0 and 100
2. WHEN fewer candles than `period + 1` are provided THEN system SHALL raise `InsufficientDataError`
3. WHEN RSI > 70 THEN value SHALL be above 70.0 (overbought zone preserved)
4. WHEN RSI < 30 THEN value SHALL be below 30.0 (oversold zone preserved)

**Independent Test**: Feed 50 known OHLCV values into `calculate_rsi`, assert result matches manually verified RSI value within 0.01.

---

### P1: Calculate SMA ⭐ MVP

**User Story**: As a trader, I want to compute SMA from a candle series so that I can identify trend direction.

**Why P1**: Core indicator. Required for signal generation.

**Acceptance Criteria**:

1. WHEN `calculate_sma(candles, period=20)` is called THEN system SHALL return the arithmetic mean of the last `period` close prices as a `float`
2. WHEN fewer candles than `period` are provided THEN system SHALL raise `InsufficientDataError`
3. WHEN all close prices are equal THEN SMA SHALL equal that price exactly

**Independent Test**: Feed 20 candles with known close prices, assert SMA equals expected mean.

---

### P1: Calculate Supertrend ⭐ MVP

**User Story**: As a trader, I want to compute Supertrend from a candle series so that I can determine the prevailing trend direction.

**Why P1**: Core indicator. Required for signal generation.

**Acceptance Criteria**:

1. WHEN `calculate_supertrend(candles, period=10, multiplier=3.0)` is called THEN system SHALL return a `SupertrendResult` with `value: float` and `direction: TrendDirection` (BULLISH or BEARISH)
2. WHEN price is above the Supertrend line THEN `direction` SHALL be `BULLISH`
3. WHEN price is below the Supertrend line THEN `direction` SHALL be `BEARISH`
4. WHEN fewer candles than `period + 1` are provided THEN system SHALL raise `InsufficientDataError`

**Independent Test**: Feed candles with clear uptrend, assert `direction == TrendDirection.BULLISH`.

---

### P2: Bundle all indicators in one call

**User Story**: As a developer, I want to compute all indicators in a single call so that the Signal Generator has one clean entry point.

**Why P2**: Convenience wrapper — reduces boilerplate in Signal Generator.

**Acceptance Criteria**:

1. WHEN `calculate_indicators(candles, config)` is called THEN system SHALL return an `IndicatorResult` with `rsi`, `sma`, and `supertrend` fields
2. WHEN any single indicator fails THEN system SHALL raise the underlying error without swallowing it

**Independent Test**: Call `calculate_indicators` with valid candles and assert all three fields present and non-None.

---

## Edge Cases

- WHEN `candles` list is empty THEN system SHALL raise `InsufficientDataError`
- WHEN candles have identical high/low (zero ATR) THEN Supertrend calculation SHALL not divide by zero
- WHEN `period` is 0 or negative THEN system SHALL raise `ValueError`

---

## Success Criteria

- [ ] `calculate_rsi(candles, 14)` returns float in [0, 100] for valid input
- [ ] `calculate_sma(candles, 20)` returns correct mean for known input
- [ ] `calculate_supertrend(candles, 10, 3.0)` returns correct direction for clear trend
- [ ] All three raise `InsufficientDataError` when not enough candles provided
