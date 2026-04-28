# future-crypto

**Vision:** Personal crypto futures signal system that scans Binance Futures market data, calculates technical indicators, and delivers buy/sell entry signals via Telegram.
**For:** Solo trader (personal use)
**Solves:** Manual market monitoring — automates scanning and signal generation for futures entries.

## Goals

- Scan Binance Futures market data continuously and detect high-quality entry signals with RSI + SMA + Supertrend
- Deliver actionable buy/sell signals to Telegram with enough context to make a trade decision

## Tech Stack

**Core:**

- Language: Python 3.13+
- Exchange: Binance Futures via `ccxt`
- Validation: `pydantic`

**Key dependencies:**
- `ccxt` — Binance Futures market data
- `pydantic` — data models and config validation
- `python-telegram-bot` or `httpx` — Telegram delivery
- `pandas` / `pandas-ta` — indicator calculation (RSI, SMA, Supertrend)

## Scope

**v1 includes:**

- Fetch OHLCV candle data from Binance Futures
- Calculate RSI, SMA, Supertrend indicators
- Generate buy/sell signals when indicator conditions align
- Send signal alerts to Telegram (symbol, direction, indicator values)

**Explicitly out of scope:**

- Order execution / automated trading
- Portfolio tracking or PnL reporting
- Multiple exchanges
- Web UI or dashboard
- Backtesting engine

## Constraints

- Personal use only — no multi-user auth needed
- Signaling only — no real-money order placement in v1
- Binance Futures exclusively
