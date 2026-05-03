# Multi-Symbol Scanner Specification

## Problem Statement

`main.py` is a one-shot batch script for a single hardcoded symbol. It does not use Telegram, does not iterate configured symbols/timeframes, and does not run continuously. M2 makes the system a real scanner.

## Goals

- Scan all configured symbols × timeframes on a schedule
- Send signal + chart to Telegram on new signals
- Deduplicate signals within a cooldown window

## Out of Scope

- Persistent deduplication across restarts
- Multi-exchange support
- Volume/confluence filters (M3)

## Signal Conditions

Unchanged from M1 — RSI + SMA + Supertrend must all agree.

## User Stories

### P1: Continuous scan loop

**User Story**: As a trader, I want the system to scan all configured symbols on a schedule so that I don't miss signals while away.

**Acceptance Criteria**:
1. WHEN scanner starts THEN it SHALL iterate every (symbol, timeframe) pair from config
2. WHEN cycle completes THEN system SHALL sleep `SCAN_INTERVAL_SECONDS` before next cycle
3. WHEN a symbol fetch fails THEN system SHALL log error and continue to next symbol (no crash)

### P1: Telegram delivery

**User Story**: As a trader, I want signal alerts sent to Telegram with a chart so I can act immediately.

**Acceptance Criteria**:
1. WHEN signal is BUY or SELL THEN system SHALL send text message to Telegram
2. WHEN signal is BUY or SELL THEN system SHALL send chart PNG to Telegram
3. WHEN Telegram is not configured THEN system SHALL log signal to console and continue

### P1: Signal deduplication

**User Story**: As a trader, I don't want repeated alerts for the same signal within a cooldown period.

**Acceptance Criteria**:
1. WHEN same (symbol, timeframe, direction) fires within `SIGNAL_COOLDOWN_SECONDS` THEN system SHALL skip it
2. WHEN cooldown expires THEN same signal SHALL be sent again if conditions still met

## Env Vars

| Var | Default | Description |
|-----|---------|-------------|
| `SCAN_INTERVAL_SECONDS` | `60` | Sleep between full scan cycles |
| `SIGNAL_COOLDOWN_SECONDS` | `14400` | Per-(symbol, tf, direction) cooldown |

## Success Criteria

- [ ] Scanner runs continuously across all configured symbols × timeframes
- [ ] Signals sent to Telegram with chart
- [ ] No duplicate alerts within cooldown window
- [ ] Single symbol/timeframe failure does not crash scanner
