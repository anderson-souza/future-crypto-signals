# Architecture

**Pattern:** Modular pipeline — 6 independent layers feeding data top-to-bottom

## High-Level Structure

```
main.py
  └─ run_scanner() [scanner/loop.py]
       │
       ├─ BinanceFetcher        [fetcher/]    → list[Candle]
       ├─ calculate_indicators  [indicators/] → IndicatorResult
       ├─ evaluate_signal       [signals/]    → Signal
       ├─ SignalDeduplicator    [scanner/]    → bool (skip?)
       ├─ TelegramNotifier      [notifier/]   → send text + chart
       └─ render_chart          [chart/]      → PNG bytes
```

## Identified Patterns

### Frozen Dataclass / Pydantic Model (Immutability)

**Location:** fetcher/models.py, indicators/models.py, signals/models.py, chart/models.py  
**Purpose:** Prevent accidental mutation across pipeline stages  
**Implementation:** Pydantic `ConfigDict(frozen=True)` or `@dataclass(frozen=True)`  
**Example:** `Candle(BaseModel)` with frozen config + field validators

### Config-from-Env Objects

**Location:** */config.py in each module  
**Purpose:** Centralize env var reading per module boundary  
**Implementation:** Plain `os.getenv()` + manual list parsing (not pydantic-settings for lists)  
**Example:** `FetcherConfig` reads `BINANCE_SYMBOLS` with `.split(",")` + `.strip()`

### Module Public API via `__init__.py`

**Location:** Every src/ subdirectory  
**Purpose:** Clean import surface — consumers import from `src.module`, not `src.module.subfile`  
**Example:** `from src.fetcher import BinanceFetcher, Candle`

### Exception Hierarchy with Context

**Location:** src/exceptions.py + each module's exceptions.py  
**Purpose:** Carry structured context (symbol, timeframe) through error chain  
**Implementation:** Custom exceptions with `__init__` taking context args, chained with `from e`

## Data Flow

### Main Scan Cycle

```
1. FETCH
   BinanceFetcher.fetch_candles(symbol, timeframe, limit=200)
   └─> ccxt.binanceusdm.fetch_ohlcv()
       └─> CandleParser.parse(raw_ohlcv) → list[Candle]

2. ANALYZE
   calculate_indicators(candles, IndicatorConfig)
   ├─ calculate_rsi(candles, period=14) → float
   ├─ calculate_sma(candles, period=8)  → float  [short]
   ├─ calculate_sma(candles, period=21) → float  [long]
   ├─ calculate_supertrend(candles, period=7, mult=2.0) → SupertrendResult
   └─ calculate_volume_filter(candles, period=20, min_rvol=0.5) → VolumeResult
      └─> IndicatorResult (frozen dataclass)

3. SIGNAL GENERATION
   evaluate_signal(indicators, last_candle) → Signal
   ├─ volume.is_sufficient == False → NO_SIGNAL (suppressed)
   ├─ rsi < 50 AND sma_short > sma_long AND supertrend == BULLISH → BUY
   ├─ rsi > 50 AND sma_short < sma_long AND supertrend == BEARISH → SELL
   └─ else → NO_SIGNAL

4. DEDUPLICATION
   dedup.is_duplicate(signal)
   └─ checks (symbol, timeframe, direction) + cooldown window (default 4h)

5. NOTIFY
   TelegramNotifier.send(signal)        → text message
   render_chart(ChartData) → PNG bytes
   TelegramNotifier.send_chart(signal, png) → image message

6. SLEEP
   time.sleep(SCAN_INTERVAL_SECONDS)   [default 3600s]
```

## Code Organization

**Approach:** Feature/domain-based — each subdirectory owns one concern

**Module boundaries:**

| Module | Owns | Imports from |
|--------|------|--------------|
| fetcher | Candle acquisition + parsing | ccxt, pydantic |
| indicators | Technical computation | fetcher.models, pandas |
| signals | Buy/sell decision logic | indicators.models, fetcher.models |
| scanner | Loop orchestration + dedup | all of the above |
| notifier | Telegram delivery | signals.models, httpx |
| chart | Visualization | fetcher.models, signals.models, indicators.models |

Dependencies flow one-way: scanner → signals → indicators → fetcher. No circular imports.
