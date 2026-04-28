# Market Data Fetcher Tasks

**Design**: `.specs/features/market-data-fetcher/design.md`
**Status**: Approved

---

## Execution Plan

### Phase 1: Foundation (Sequential)

```
T1 → T2 → T3
```

Models and exceptions first — everything depends on them.

### Phase 2: Core Implementation (Parallel OK)

```
T3 complete, then:
  ├── T4 [P]  BinanceFetcher client
  └── T5 [P]  CandleParser

T4 + T5 complete, then:
  T6  __init__.py exports
```

### Phase 3: Tests (Parallel OK)

```
T6 complete, then:
  ├── T7 [P]  Unit tests (parser)
  └── T8 [P]  Integration tests (client)
```

---

## Task Breakdown

### T1: Create custom exceptions module

**What**: Define `DataValidationError`, `FetchError`, `ConfigError`, `ConnectionError` in one file
**Where**: `src/fetcher/exceptions.py`
**Depends on**: None

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] All 4 exception classes defined, inherit from `Exception`
- [ ] `FetchError` accepts `symbol` and `timeframe` params
- [ ] `DataValidationError` accepts `symbol` and `field` params
- [ ] File has no imports beyond stdlib

**Verify**:
```bash
python -c "from src.fetcher.exceptions import DataValidationError, FetchError, ConfigError; print('OK')"
```

---

### T2: Create Candle pydantic model

**What**: Define immutable `Candle` dataclass with field validation
**Where**: `src/fetcher/models.py`
**Depends on**: T1

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] `Candle` has: `timestamp: datetime`, `open`, `high`, `low`, `close`, `volume: float`, `symbol: str`, `timeframe: str`
- [ ] `field_validator` rejects `open/high/low/close <= 0`
- [ ] `volume == 0` is accepted
- [ ] Model is effectively immutable (`model_config = ConfigDict(frozen=True)`)

**Verify**:
```bash
python -c "
from src.fetcher.models import Candle
from datetime import datetime, timezone
c = Candle(timestamp=datetime.now(timezone.utc), open=1.0, high=2.0, low=0.5, close=1.5, volume=0.0, symbol='BTCUSDT', timeframe='1h')
print(c)
"
```

---

### T3: Create FetcherConfig

**What**: Pydantic-settings config that reads symbols, timeframes, limits, and Binance API keys from env
**Where**: `src/fetcher/config.py`
**Depends on**: T1

**Tools**:
- MCP: `context7` (pydantic-settings docs if needed)
- Skill: NONE

**Done when**:
- [ ] Reads `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `BINANCE_SYMBOLS`, `BINANCE_TIMEFRAMES` from env
- [ ] `BINANCE_SYMBOLS` and `BINANCE_TIMEFRAMES` parse as `list[str]` (comma-separated env var)
- [ ] `default_limit: int = 200`
- [ ] Missing `BINANCE_API_KEY` or `BINANCE_API_SECRET` raises `ConfigError` at init

**Verify**:
```bash
BINANCE_API_KEY=x BINANCE_API_SECRET=y BINANCE_SYMBOLS=BTCUSDT BINANCE_TIMEFRAMES=1h python -c "
from src.fetcher.config import FetcherConfig
cfg = FetcherConfig()
print(cfg.symbols, cfg.timeframes)
"
```

---

### T4: Create BinanceFetcher client [P]

**What**: ccxt wrapper that calls `fetch_ohlcv` and returns `list[Candle]`
**Where**: `src/fetcher/client.py`
**Depends on**: T2, T3

**Tools**:
- MCP: `context7` (ccxt docs)
- Skill: NONE

**Done when**:
- [ ] `BinanceFetcher.__init__` accepts `FetcherConfig`, creates `ccxt.binance` with `{'defaultType': 'future'}` and `enableRateLimit=True`
- [ ] `fetch_candles(symbol, timeframe, limit) -> list[Candle]` calls `exchange.fetch_ohlcv` and passes result to `CandleParser`
- [ ] `check_connectivity()` calls `exchange.load_markets()` and raises `ConnectionError` on failure
- [ ] ccxt exceptions caught and re-raised as `FetchError(symbol, timeframe)`

**Verify**:
```bash
# Requires real API keys — skip in unit tests
python -c "
from src.fetcher.config import FetcherConfig
from src.fetcher.client import BinanceFetcher
cfg = FetcherConfig()
fetcher = BinanceFetcher(cfg)
candles = fetcher.fetch_candles('BTCUSDT', '1h', 5)
print(len(candles), candles[0])
"
```

---

### T5: Create CandleParser [P]

**What**: Stateless parser that converts raw ccxt OHLCV `list[list]` into `list[Candle]`
**Where**: `src/fetcher/parser.py`
**Depends on**: T2

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] `CandleParser.parse(raw, symbol, timeframe) -> list[Candle]` converts each row `[ts_ms, o, h, l, c, v]`
- [ ] Timestamp converted from ms epoch to `datetime` (UTC)
- [ ] Pydantic `ValidationError` caught and re-raised as `DataValidationError(symbol, field)`
- [ ] Empty `raw` input returns `[]` without error

**Verify**:
```bash
python -c "
from src.fetcher.parser import CandleParser
raw = [[1700000000000, 30000.0, 31000.0, 29000.0, 30500.0, 100.0]]
candles = CandleParser.parse(raw, 'BTCUSDT', '1h')
print(candles[0])
"
```

---

### T6: Create package __init__.py exports

**What**: Export public API from `src/fetcher/__init__.py`
**Where**: `src/fetcher/__init__.py`
**Depends on**: T4, T5

**Tools**:
- MCP: NONE
- Skill: NONE

**Done when**:
- [ ] Exports: `BinanceFetcher`, `FetcherConfig`, `Candle`, `CandleParser`
- [ ] Exports exceptions: `DataValidationError`, `FetchError`, `ConfigError`

**Verify**:
```bash
python -c "from src.fetcher import BinanceFetcher, FetcherConfig, Candle; print('OK')"
```

---

### T7: Unit tests for CandleParser [P]

**What**: Pytest unit tests covering parser logic — no exchange required
**Where**: `tests/fetcher/test_parser.py`
**Depends on**: T5, T6

**Tools**:
- MCP: NONE
- Skill: `python-testing`

**Done when**:
- [ ] Test: valid OHLCV list parses to correct `Candle` fields
- [ ] Test: timestamp converts ms to UTC `datetime`
- [ ] Test: volume `0.0` is accepted
- [ ] Test: negative close price raises `DataValidationError`
- [ ] Test: empty input returns `[]`
- [ ] Test: missing field (None) raises `DataValidationError`
- [ ] All tests pass: `pytest tests/fetcher/test_parser.py -v`

**Verify**:
```bash
pytest tests/fetcher/test_parser.py -v
```
Expected: all green, 0 failures.

---

### T8: Integration tests for BinanceFetcher [P]

**What**: Pytest integration tests hitting live Binance Futures (requires API keys in env)
**Where**: `tests/fetcher/test_client.py`
**Depends on**: T4, T6

**Tools**:
- MCP: NONE
- Skill: `python-testing`

**Done when**:
- [ ] Test: `fetch_candles("BTCUSDT", "1h", 10)` returns exactly 10 `Candle` objects
- [ ] Test: all returned candles have `symbol == "BTCUSDT"` and `timeframe == "1h"`
- [ ] Test: `check_connectivity()` succeeds without raising
- [ ] Tests marked `@pytest.mark.integration` to allow skipping in CI
- [ ] All tests pass: `pytest tests/fetcher/test_client.py -v -m integration`

**Verify**:
```bash
pytest tests/fetcher/test_client.py -v -m integration
```
Expected: 3 tests pass, candle count and fields correct.

---

## Parallel Execution Map

```
Phase 1 (Sequential — foundations):
  T1 ──→ T2
  T1 ──→ T3

Phase 2 (Parallel — core):
  T2 + T3 complete, then:
    ├── T4 [P]
    └── T5 [P]

  T4 + T5 complete, then:
    T6

Phase 3 (Parallel — tests):
  T6 complete, then:
    ├── T7 [P]  (unit, no keys needed)
    └── T8 [P]  (integration, needs API keys)
```

---

## Granularity Check

| Task | Scope | Status |
|------|-------|--------|
| T1: exceptions module | 1 file, 4 classes | ✅ |
| T2: Candle model | 1 model | ✅ |
| T3: FetcherConfig | 1 config class | ✅ |
| T4: BinanceFetcher | 1 client class | ✅ |
| T5: CandleParser | 1 parser class | ✅ |
| T6: __init__ exports | 1 file | ✅ |
| T7: parser unit tests | 1 test file | ✅ |
| T8: client integration tests | 1 test file | ✅ |
