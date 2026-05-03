# External Integrations

## Market Data

**Service:** Binance USD-Margined Futures  
**Purpose:** Fetch OHLCV candlestick data  
**Implementation:** src/fetcher/client.py — BinanceFetcher  
**Authentication:** API key + secret (public OHLCV endpoints don't require auth in practice)  
**Library:** ccxt.binanceusdm

```python
self._exchange = ccxt.binanceusdm({
    "apiKey": config.api_key,
    "secret": config.api_secret,
    "enableRateLimit": True,
})
# Patch to skip authenticated fetch_currencies on load_markets()
self._exchange.fetch_currencies = lambda *args, **kwargs: {}
raw = self._exchange.fetch_ohlcv(symbol, timeframe, limit=effective_limit)
```

**Key endpoints used:** fetch_ohlcv (public), load_markets (patched)  
**Error handling:** `ccxt.BaseError` → `FetchError(symbol, timeframe, message)`

**Environment variables:**
```
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_SYMBOLS=BTCUSDT,ETHUSDT,...    # comma-separated
BINANCE_TIMEFRAMES=2h,4h               # comma-separated
BINANCE_DEFAULT_LIMIT=200
```

## Notifications

**Service:** Telegram Bot API  
**Purpose:** Deliver trade signal text + chart images  
**Implementation:** src/notifier/client.py — TelegramNotifier  
**Authentication:** Bot token in URL  
**Library:** httpx (synchronous POST)

```python
base = f"https://api.telegram.org/bot{token}"

# Text message
httpx.post(f"{base}/sendMessage", json={
    "chat_id": chat_id,
    "text": format_signal(signal),
})

# Chart image
httpx.post(f"{base}/sendPhoto",
    data={"chat_id": chat_id},
    files={"photo": ("chart.png", png_bytes, "image/png")},
)
```

**Endpoints:** /sendMessage, /sendPhoto  
**Error handling:** `response.raise_for_status()` — raises httpx.HTTPError on 4xx/5xx

**Environment variables:**
```
TELEGRAM_BOT_TOKEN=           # required — ConfigError if missing
TELEGRAM_CHAT_ID=             # required — ConfigError if missing
```

**Note:** Telegram currently disabled in scanner loop (`notifier = None`). Config validated on construct but commented out in loop.py.

## Chart Rendering

**Service:** Local — mplfinance + matplotlib  
**Purpose:** Generate candlestick PNG with indicator overlays  
**Implementation:** src/chart/renderer.py — render_chart()  
**Output:** PNG bytes → sent to Telegram or saved to disk

```python
import matplotlib
matplotlib.use("Agg")   # Must be set before pyplot import

fig, _ = mpf.plot(df, type="candle", style="nightclouds",
                  addplot=addplots, returnfig=True, figsize=(14, 8))
buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
```

**Overlays rendered:** SMA short, SMA long, RSI + midline at 50, Supertrend (bullish/bearish lines), BUY/SELL markers  
**Environment variables:**
```
CHART_WINDOW=100    # candles visible in chart (default 100)
```

## Configuration Summary

All config via `os.getenv()` — never pydantic-settings for list fields.

| Config Class | Module | Env Vars |
|---|---|---|
| FetcherConfig | src/fetcher/config.py | BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_SYMBOLS, BINANCE_TIMEFRAMES, BINANCE_DEFAULT_LIMIT |
| ScannerConfig | src/scanner/config.py | SCAN_INTERVAL_SECONDS (default 3600), SIGNAL_COOLDOWN_SECONDS (default 14400) |
| NotifierConfig | src/notifier/config.py | TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID |
| ChartConfig | src/chart/models.py | CHART_WINDOW (default 100) |

List fields parsed manually:
```python
self.symbols = [s.strip() for s in os.getenv("BINANCE_SYMBOLS", "BTCUSDT").split(",") if s.strip()]
```
