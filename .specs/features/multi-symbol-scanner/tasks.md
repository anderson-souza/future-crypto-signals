# Multi-Symbol Scanner Tasks

## Phase 1: Scanner Module

- [x] Create `src/scanner/__init__.py`
- [x] Create `src/scanner/config.py` — `ScannerConfig`
- [x] Create `src/scanner/deduplicator.py` — `SignalDeduplicator`
- [x] Create `src/scanner/loop.py` — `run_scanner()`

## Phase 2: Notifier Update

- [x] Add `send_chart(signal, png_bytes)` to `TelegramNotifier`

## Phase 3: Entry Point

- [x] Rewrite `main.py` to call `run_scanner()`

## Phase 4: Tests

- [ ] `tests/scanner/test_deduplicator.py`
- [ ] `tests/scanner/test_loop.py` (mocked fetcher/notifier)
