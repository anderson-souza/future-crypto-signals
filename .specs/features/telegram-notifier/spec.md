# Telegram Notifier — Spec

## Goal

Send formatted signal alerts to a configured Telegram chat when a BUY or SELL signal is generated.

## Inputs

- `Signal` object from `src/signals/models.py`
- Telegram bot token (env: `TELEGRAM_BOT_TOKEN`)
- Telegram chat ID (env: `TELEGRAM_CHAT_ID`)

## Outputs

- HTTP POST to Telegram Bot API — message delivered to chat
- No return value needed (fire-and-forget from caller's perspective)

## Behavior

- Format signal as readable message including: symbol, timeframe, direction, close price, RSI, SMA8, SMA21, Supertrend direction, timestamp
- Send only BUY or SELL signals — skip NO_SIGNAL
- Raise on HTTP error (non-2xx) so caller can log/handle

## Out of Scope

- Retry logic
- Rate limiting / deduplication
- Markdown formatting (plain text only)
- Multiple chat targets

## Message Format

```
[BUY] BTCUSDT 4h
Close: 65432.10
RSI: 44.2
SMA8: 65100.00 | SMA21: 64800.00
Supertrend: BULLISH
Time: 2026-04-27 12:00:00
```

## Config

- `TELEGRAM_BOT_TOKEN` — required, no default
- `TELEGRAM_CHAT_ID` — required, no default
- Raise `ConfigError` at init if either is missing

## Dependencies

- `httpx` for HTTP (already likely available, else `uv add httpx`)
- No new internal dependencies
