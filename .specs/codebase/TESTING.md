# Testing Infrastructure

## Test Frameworks

**Unit/Integration:** pytest >=9.0.3  
**Coverage:** pytest-cov >=7.1.0  
**Current coverage:** ~98%

## Test Organization

**Location:** tests/ (mirrors src/ structure)  
**Naming:** `test_<subject>.py`  
**Structure:** One test file per logical unit; shared fixtures in conftest.py

### Test Inventory

| File | Tests | What's covered |
|------|-------|----------------|
| tests/indicators/test_rsi_series.py | 6 | Series output, length, scalar match, datetime index, errors |
| tests/indicators/test_sma_series.py | 6 | Series output, length, scalar match, datetime index, errors |
| tests/indicators/test_supertrend_series.py | 8 | Tuple return, length, value match, direction values, index, errors |
| tests/indicators/test_volume.py | 17 | RVOL calc, sufficiency threshold, boundary, error cases |
| tests/signals/test_evaluator.py | 21 | Volume suppression, buy/sell conditions, RSI boundary, rvol carry |
| tests/scanner/test_deduplicator.py | 5 | New signal, duplicate tracking, cooldown expiry, independence by direction/symbol |
| tests/scanner/test_loop.py | 8 | No-signal skip, notify on BUY, duplicate skip, error resilience, no-notifier |
| tests/chart/test_renderer.py | 12 | BUY/SELL/no-signal, multiple signals, timestamp outside window, empty, env config |
| tests/chart/test_file_writer.py | 3 | Write file, missing parent dir, empty bytes |
| **Total** | **86** | |

## Testing Patterns

### Core Fixture

```python
# tests/conftest.py
def make_candles(n: int = 150, base_price: float = 50000.0,
                 symbol: str = "BTCUSDT", timeframe: str = "1h") -> list[Candle]:
    candles = []
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    price = base_price
    for i in range(n):
        close = price + (i % 10) * 10
        candles.append(Candle(
            timestamp=start + timedelta(hours=i),
            open=close - 5, high=close + 20, low=close - 20, close=close,
            volume=1000.0 + i, symbol=symbol, timeframe=timeframe,
        ))
    return candles
```

### Unit Tests (indicators, signals)

Pure function testing — build controlled inputs, assert outputs:

```python
def test_buy_signal_when_all_long_conditions_met():
    indicators = _make_indicators(
        rsi=45.0, sma_short=53000.0, sma_long=51000.0,
        supertrend_direction=TrendDirection.BULLISH, is_sufficient=True,
    )
    signal = evaluate_signal(indicators, _last_candle())
    assert signal.direction == SignalDirection.BUY
```

### Boundary Testing

Explicit boundary conditions (inclusive/exclusive thresholds):

```python
def test_boundary_inclusive_at_min_rvol():
    # rvol == min_rvol exactly → is_sufficient=True
    volumes = [100.0] * 20 + [50.0]
    result = calculate_volume_filter(candles, period=20, min_rvol=0.5)
    assert result.is_sufficient is True
```

### Integration Tests (scanner loop)

Mock external dependencies, test orchestration:

```python
def test_notifies_on_buy_signal():
    fetcher = MagicMock()
    fetcher.fetch_candles.return_value = make_candles(150)
    notifier = MagicMock()

    with patch("src.scanner.loop.calculate_indicators"), \
         patch("src.scanner.loop.evaluate_signal", return_value=buy_signal):
        _scan_pair("BTCUSDT", "1h", fetcher, fetcher_cfg, indicator_cfg, 50, dedup, notifier)

    notifier.send.assert_called_once_with(buy_signal)
```

## Test Execution

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=term-missing

# Specific module
uv run pytest tests/indicators/
```

## Coverage Targets

**Current:** ~98% (measured 2026-04-28)  
**Goal:** 80%+ (per project rules)  
**Enforcement:** Manual — no CI gate configured
