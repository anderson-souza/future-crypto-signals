# future-crypto

Crypto futures scanner for Binance. Polls multiple symbols and timeframes, computes technical indicators, emits BUY/SELL signals, and sends Telegram alerts with candlestick charts.

## How it works

1. Fetches OHLCV candles from Binance Futures (`ccxt.binanceusdm`) — no API key required for market data.
2. Calculates RSI, SMA (short/long), Supertrend, and RVOL.
3. Emits a signal when all three align:
   - **BUY**: RSI < 50 AND SMA short > SMA long AND Supertrend bullish
   - **SELL**: RSI > 50 AND SMA short < SMA long AND Supertrend bearish
4. Suppresses signal when RVOL < threshold (low-volume filter).
5. Deduplicates signals per symbol/timeframe within a configurable cooldown window.
6. Sends signal text + chart PNG to Telegram (optional).

## Setup

```bash
# Install dependencies
uv sync

# Copy and edit env
cp .env .env.local
```

## Configuration

All config via environment variables (copy `.env` as reference):

| Variable | Default | Description |
|---|---|---|
| `BINANCE_SYMBOLS` | `BTCUSDT` | Comma-separated list of futures symbols |
| `BINANCE_TIMEFRAMES` | `1h` | Comma-separated timeframes (`1h`, `4h`, etc.) |
| `BINANCE_DEFAULT_LIMIT` | `200` | Candles to fetch per request |
| `BINANCE_API_KEY` | _(empty)_ | Only needed for order placement |
| `BINANCE_API_SECRET` | _(empty)_ | Only needed for order placement |
| `SCAN_INTERVAL_SECONDS` | `3600` | Sleep between full scan cycles |
| `SIGNAL_COOLDOWN_SECONDS` | `14400` | Dedup window per symbol/timeframe |
| `TELEGRAM_BOT_TOKEN` | _(required)_ | Telegram bot token |
| `TELEGRAM_CHAT_ID` | _(required)_ | Telegram chat/channel ID |

## Running

```bash
uv run python -m src
```

Telegram is optional — if `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` are missing, signals are logged to console only.

## Indicator defaults

| Indicator | Parameter | Default |
|---|---|---|
| RSI | period | 14 |
| SMA short | period | 8 |
| SMA long | period | 21 |
| Supertrend | period | 7 |
| Supertrend | multiplier | 2.0 |
| Volume | period | 20 |
| Volume | min RVOL | 0.5 |

## Project structure

```
src/
├── fetcher/      # Binance OHLCV fetching (ccxt)
├── indicators/   # RSI, SMA, Supertrend, Volume (pandas-ta-classic)
├── signals/      # Signal evaluation logic
├── scanner/      # Main loop + deduplication
├── notifier/     # Telegram client
└── chart/        # Candlestick chart rendering (mplfinance)
```

## Dev

```bash
uv run pytest --cov=src
uv run ruff check src/
uv run ty check src/
```
