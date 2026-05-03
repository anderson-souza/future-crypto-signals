# Multi-Symbol Scanner Design

## Module Structure

```
src/scanner/
  __init__.py        # exports run_scanner
  config.py          # ScannerConfig
  deduplicator.py    # SignalDeduplicator
  loop.py            # run_scanner() — main orchestration
```

## Data Flow

```
ScannerConfig / FetcherConfig / IndicatorConfig
        ↓
run_scanner()
  for symbol in symbols:
    for timeframe in timeframes:
      fetch_candles()
        ↓
      calculate_indicators()
        ↓
      evaluate_signal()
        ↓
      SignalDeduplicator.is_duplicate()?
        NO → TelegramNotifier.send() + send_chart()
             SignalDeduplicator.mark_sent()
        YES → log + skip
  sleep(SCAN_INTERVAL_SECONDS)
```

## Key Design Decisions

**Deduplication key**: `(symbol, timeframe, direction)` — same symbol can fire BUY then SELL independently.

**In-memory only**: Dedup state resets on restart. Acceptable for v1 — worst case: one extra alert after restart.

**Telegram optional**: `NotifierConfig` raises `ConfigError` if tokens missing. Scanner catches it, sets `notifier = None`, logs to console only.

**Error isolation**: Each (symbol, timeframe) pair runs in try/except. One bad fetch doesn't stop the loop.

**send_chart**: New method on `TelegramNotifier` using Telegram `sendPhoto` endpoint with `multipart/form-data`.

## ScannerConfig

```python
scan_interval_seconds: int   # SCAN_INTERVAL_SECONDS, default 60
signal_cooldown_seconds: int # SIGNAL_COOLDOWN_SECONDS, default 14400
```

## SignalDeduplicator

```python
_cooldown: timedelta
_sent: dict[tuple[str, str, str], datetime]  # (symbol, timeframe, direction) → sent_at

is_duplicate(signal) -> bool
mark_sent(signal) -> None
```
