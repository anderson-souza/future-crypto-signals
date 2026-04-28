# Signal Generator Specification

## Problem Statement

Indicator values alone don't tell a trader what to do. This feature evaluates
RSI, SMA, and Supertrend together and produces a clear BUY, SELL, or NO_SIGNAL
decision that the Telegram notifier can act on.

## Goals

- [ ] Evaluate indicator conditions and produce a typed signal (BUY / SELL / NO_SIGNAL)
- [ ] Only fire a signal when all 3 indicators agree — no partial matches

## Out of Scope

- Telegram delivery (next feature)
- Signal deduplication / cooldown
- Confidence scores or ranking
- Multiple timeframe confluence

---

## Signal Conditions

| Signal | RSI | Price vs SMA | Supertrend |
|--------|-----|--------------|------------|
| BUY    | < 50 | close > SMA | BULLISH |
| SELL   | > 50 | close < SMA | BEARISH |
| NO_SIGNAL | any other combination | — | — |

---

## User Stories

### P1: Generate BUY signal ⭐ MVP

**User Story**: As a trader, I want a BUY signal when RSI < 50, close > SMA, and Supertrend is BULLISH so that I have confirmation to enter a long position.

**Acceptance Criteria**:

1. WHEN `rsi < 50` AND `close > sma` AND `supertrend.direction == BULLISH` THEN system SHALL return `Signal` with `direction=BUY`
2. WHEN only 2 of 3 conditions are met THEN system SHALL return `Signal` with `direction=NO_SIGNAL`
3. WHEN RSI is exactly 50.0 THEN system SHALL return `NO_SIGNAL` (boundary is exclusive)

**Independent Test**: Pass `IndicatorResult(rsi=45, sma=76000, supertrend=SupertrendResult(77000, BULLISH))` and `close=77500` → assert `BUY`.

---

### P1: Generate SELL signal ⭐ MVP

**User Story**: As a trader, I want a SELL signal when RSI > 50, close < SMA, and Supertrend is BEARISH so that I have confirmation to enter a short position.

**Acceptance Criteria**:

1. WHEN `rsi > 50` AND `close < sma` AND `supertrend.direction == BEARISH` THEN system SHALL return `Signal` with `direction=SELL`
2. WHEN only 2 of 3 conditions are met THEN system SHALL return `Signal` with `direction=NO_SIGNAL`
3. WHEN RSI is exactly 50.0 THEN system SHALL return `NO_SIGNAL`

**Independent Test**: Pass `IndicatorResult(rsi=62, sma=78000, supertrend=SupertrendResult(79000, BEARISH))` and `close=77500` → assert `SELL`.

---

### P1: Signal carries full context ⭐ MVP

**User Story**: As a trader, I want the signal to include symbol, timeframe, and indicator values so that I can assess the trade without looking up the data myself.

**Acceptance Criteria**:

1. WHEN a signal is generated THEN it SHALL include: `symbol`, `timeframe`, `direction`, `rsi`, `sma`, `supertrend_value`, `supertrend_direction`, `close`, `timestamp`
2. WHEN direction is `NO_SIGNAL` THEN the signal SHALL still carry all fields (for logging purposes)

---

## Edge Cases

- WHEN `IndicatorResult` has `rsi == 50.0` exactly THEN NO_SIGNAL (not BUY, not SELL)
- WHEN `close == sma` exactly THEN NO_SIGNAL (boundary exclusive on both sides)

---

## Success Criteria

- [ ] BUY signal fires when all 3 long conditions met
- [ ] SELL signal fires when all 3 short conditions met
- [ ] NO_SIGNAL returned for all partial matches
- [ ] Signal carries symbol, timeframe, direction, and all indicator values
