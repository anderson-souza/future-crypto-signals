# Roadmap

**Current Milestone:** M1 — Core Signal Engine
**Status:** Planning

---

## M1 — Core Signal Engine

**Goal:** System fetches Binance Futures data, calculates indicators, and sends signal to Telegram
**Target:** Working end-to-end pipeline for at least one symbol

### Features

**Market Data Fetcher** - PLANNED

- Connect to Binance Futures via ccxt
- Fetch OHLCV candle data for configured symbols and timeframes
- Validate and normalize data with pydantic models

**Indicator Engine** - PLANNED

- Calculate RSI (relative strength index)
- Calculate SMA (simple moving average, configurable period)
- Calculate Supertrend (ATR-based trend indicator)

**Signal Generator** - PLANNED

- Evaluate indicator values against entry conditions
- Produce buy/sell signal with symbol, direction, and indicator snapshot
- Filter weak/conflicting signals (all 3 indicators must agree)

**Telegram Notifier** - PLANNED

- Send formatted signal message to configured Telegram chat
- Include symbol, direction (BUY/SELL), timeframe, and indicator values

**Candle Chart Renderer** - PLANNED

- Render dark-theme candlestick chart with SMA short/long and Supertrend overlays
- Mark signal candle with directional triangle (▲ BUY / ▼ SELL)
- RSI sub-panel with 50 reference line
- Output: PNG bytes → Telegram attachment + standalone file save
- Configurable candle window via `CHART_WINDOW` env var (default 100)

---

## M2 — Multi-Symbol Scanner

**Goal:** Scan a configurable list of symbols on a schedule, not just one

### Features

**Symbol List Config** - PLANNED
**Scheduled Scan Loop** - PLANNED
**Deduplication** - PLANNED (avoid re-alerting same signal within cooldown window)

---

## M3 — Signal Quality & Filtering

**Goal:** Reduce noise, improve signal-to-noise ratio

### Features

**Timeframe Confluence** - PLANNED (signal must align on 2+ timeframes)
**Volume Filter** - SPECIFIED → see [spec](./../features/volume-filter/spec.md) (suppress signals on low-volume candles via RVOL)
**Signal History Log** - PLANNED (persist signals to file for review)

---

## Future Considerations

- Backtesting engine to validate signal quality historically
- Web dashboard for signal history visualization
- Additional indicators (MACD, Bollinger Bands, funding rate)
- Multiple exchange support
