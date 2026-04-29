# Telegram Notifier — Tasks

## T1: Add httpx dependency
- Run `uv add httpx`
- Verify: `uv run python -c "import httpx"`

## T2: Create `src/notifier/config.py`
- `NotifierConfig` reads `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` from env
- Raises `ConfigError` if either missing
- Verify: instantiate without env vars → raises `ConfigError`

## T3: Create `src/notifier/formatter.py`
- Pure `format_signal(signal: Signal) -> str`
- Verify: call with a mock Signal → returns expected string

## T4: Create `src/notifier/client.py`
- `TelegramNotifier(config)` with `send(signal: Signal) -> None`
- Skips if `signal.direction == SignalDirection.NO_SIGNAL`
- POSTs to Telegram API, calls `response.raise_for_status()`
- Verify: module imports without error

## T5: Create `src/notifier/__init__.py`
- Exports `TelegramNotifier`, `NotifierConfig`

## T6: Wire into `main.py`
- Instantiate `TelegramNotifier(NotifierConfig())`
- Call `notifier.send(signal)` for each signal found
- Verify: run `uv run python main.py` → signals sent to Telegram

## T7: Update `.env.example` (if exists) or document required env vars in README
