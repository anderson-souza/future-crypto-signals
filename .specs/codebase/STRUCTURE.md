# Project Structure

**Root:** E:\repos\future-crypto

## Directory Tree

```
future-crypto/
├── main.py                    # Entry point: load_dotenv() + run_scanner()
├── pyproject.toml             # Deps, tool config
├── uv.lock                    # Pinned lockfile
├── CLAUDE.md                  # Dev guidelines + project-specific gotchas
├── .env                       # Secrets (gitignored)
├── chart.png                  # Sample output
│
├── src/
│   ├── exceptions.py          # Root exception classes
│   ├── fetcher/               # Market data acquisition (112 LOC)
│   │   ├── __init__.py        # Exports: BinanceFetcher, FetcherConfig, Candle
│   │   ├── client.py          # BinanceFetcher (ccxt wrapper)
│   │   ├── config.py          # FetcherConfig (env vars)
│   │   ├── models.py          # Candle (frozen Pydantic)
│   │   ├── parser.py          # CandleParser.parse()
│   │   └── exceptions.py      # Re-exports
│   ├── indicators/            # Technical analysis (169 LOC)
│   │   ├── __init__.py
│   │   ├── engine.py          # calculate_indicators() orchestrator
│   │   ├── models.py          # IndicatorResult, IndicatorConfig
│   │   ├── rsi.py             # calculate_rsi + rsi_series
│   │   ├── sma.py             # calculate_sma + sma_series
│   │   ├── supertrend.py      # calculate_supertrend + series
│   │   ├── volume.py          # calculate_volume_filter (RVOL)
│   │   └── utils.py           # candles_to_df()
│   ├── signals/               # Signal evaluation (85 LOC)
│   │   ├── __init__.py
│   │   ├── models.py          # Signal, SignalDirection enum
│   │   └── evaluator.py       # evaluate_signal()
│   ├── scanner/               # Main loop (153 LOC)
│   │   ├── __init__.py        # Exports run_scanner
│   │   ├── loop.py            # run_scanner() + _scan_pair()
│   │   ├── config.py          # ScannerConfig
│   │   └── deduplicator.py    # SignalDeduplicator
│   ├── notifier/              # Telegram (71 LOC)
│   │   ├── __init__.py
│   │   ├── client.py          # TelegramNotifier
│   │   ├── config.py          # NotifierConfig
│   │   └── formatter.py       # format_signal()
│   └── chart/                 # Visualization (182 LOC)
│       ├── __init__.py
│       ├── renderer.py        # render_chart() → PNG bytes
│       ├── file_writer.py     # save_chart()
│       ├── models.py          # ChartData, ChartConfig
│       └── exceptions.py      # ChartRenderError
│
├── tests/                     # 70 tests, ~98% coverage
│   ├── conftest.py            # make_candles() fixture
│   ├── indicators/            # 37 unit tests
│   ├── signals/               # 21 unit tests
│   ├── scanner/               # 13 integration tests
│   └── chart/                 # 15 rendering tests
│
└── .specs/
    ├── project/               # PROJECT.md, ROADMAP.md
    ├── codebase/              # Brownfield docs (this dir)
    └── features/              # Per-feature specs
```

## Module Organization

### fetcher
**Purpose:** Acquire raw OHLCV candles from Binance, parse into typed models  
**Key files:** client.py (BinanceFetcher), models.py (Candle), parser.py (CandleParser)

### indicators
**Purpose:** Compute technical analysis values from candle lists  
**Key files:** engine.py (orchestrator), rsi.py, sma.py, supertrend.py, volume.py

### signals
**Purpose:** Combine indicator values into a BUY/SELL/NO_SIGNAL decision  
**Key files:** evaluator.py (evaluate_signal), models.py (Signal, SignalDirection)

### scanner
**Purpose:** Infinite loop orchestrating all pipeline stages; deduplication  
**Key files:** loop.py (run_scanner, _scan_pair), deduplicator.py (SignalDeduplicator)

### notifier
**Purpose:** Deliver signals + charts to Telegram  
**Key files:** client.py (TelegramNotifier), formatter.py (message text)

### chart
**Purpose:** Render candlestick charts with indicator overlays as PNG  
**Key files:** renderer.py (render_chart), models.py (ChartData)

## Where Things Live

**Configuration:**
- All env vars: */config.py in each module
- Project config: pyproject.toml

**External API clients:**
- Binance: src/fetcher/client.py
- Telegram: src/notifier/client.py

**Data models:**
- Each module's models.py

**Business logic:**
- Signal decisions: src/signals/evaluator.py
- Deduplication: src/scanner/deduplicator.py
- Indicator math: src/indicators/*.py
