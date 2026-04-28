# Market Data Fetcher Specification

## Problem Statement

No market data = no signals. This feature establishes the data pipeline foundation:
connect to Binance Futures, fetch OHLCV candles for configured symbols/timeframes,
and return validated, normalized data ready for indicator calculation.

## Goals

- [ ] Fetch OHLCV candle data from Binance Futures for any symbol + timeframe
- [ ] Validate and normalize raw exchange data into typed pydantic models
- [ ] Fail fast and clearly when exchange or config is broken

## Out of Scope

- Indicator calculation (next feature)
- Persistent storage / caching of candles
- Real-time streaming (REST polling only in v1)
- Multiple exchanges

---

## User Stories

### P1: Fetch OHLCV candles for a symbol ⭐ MVP

**User Story**: As a trader, I want to fetch the latest N candles for a given symbol and timeframe so that I have raw price data to feed into indicators.

**Why P1**: Zero data = zero everything. Absolute prerequisite.

**Acceptance Criteria**:

1. WHEN `fetch_candles(symbol="BTCUSDT", timeframe="1h", limit=100)` is called THEN system SHALL return a list of 100 `Candle` objects with open, high, low, close, volume, and timestamp fields
2. WHEN data is returned THEN each `Candle` SHALL have a valid UTC timestamp and all numeric fields SHALL be positive floats
3. WHEN the exchange returns fewer candles than requested (e.g., new listing) THEN system SHALL return whatever is available without error

**Independent Test**: Call `fetch_candles("BTCUSDT", "1h", 10)` and assert 10 candles returned with correct shape.

---

### P1: Validate raw exchange response ⭐ MVP

**User Story**: As a developer, I want raw ccxt data validated through pydantic so that downstream code can trust the types.

**Why P1**: ccxt returns untyped dicts. Pydantic boundary is critical before any math.

**Acceptance Criteria**:

1. WHEN ccxt returns a valid OHLCV list THEN system SHALL parse it into `list[Candle]` without errors
2. WHEN a candle field is missing or None THEN system SHALL raise a `DataValidationError` with the symbol and field name
3. WHEN volume is 0 THEN system SHALL still include the candle (0-volume is valid)

**Independent Test**: Pass a malformed candle dict to the parser and assert `DataValidationError` is raised.

---

### P2: Configurable symbol and timeframe list

**User Story**: As a trader, I want to configure which symbols and timeframes to scan so that I control what the system watches.

**Why P2**: MVP can hardcode one symbol; config list enables multi-symbol scanning in M2.

**Acceptance Criteria**:

1. WHEN `FetcherConfig` is loaded THEN system SHALL read `symbols` and `timeframes` from environment or config file
2. WHEN a symbol is invalid (not on Binance Futures) THEN system SHALL raise a `ConfigError` at startup, not silently skip

**Independent Test**: Load config with one valid and one invalid symbol; assert `ConfigError` raised on invalid.

---

### P3: Exchange connectivity check at startup

**User Story**: As a trader, I want the system to verify Binance Futures connectivity on startup so that I know immediately if credentials or network are broken.

**Why P3**: Nice-to-have guard; not required for signals to work.

**Acceptance Criteria**:

1. WHEN system starts THEN it SHALL ping the exchange and log success or raise `ConnectionError` with a clear message
2. WHEN API key is missing THEN system SHALL raise `ConfigError` before attempting any fetch

---

## Edge Cases

- WHEN Binance Futures rate limit is hit THEN system SHALL wait and retry (respect ccxt built-in rate limiter)
- WHEN network timeout occurs THEN system SHALL raise `FetchError` with symbol and timeframe context
- WHEN symbol has no futures contract (e.g., wrong market type) THEN system SHALL raise `ConfigError` at startup
- WHEN `limit` is 0 or negative THEN system SHALL raise `ValueError`

---

## Success Criteria

- [ ] `fetch_candles("BTCUSDT", "1h", 100)` returns 100 valid `Candle` objects against live Binance Futures
- [ ] Malformed data raises `DataValidationError` (unit test, no exchange needed)
- [ ] Invalid symbol raises `ConfigError` before any fetch attempt
