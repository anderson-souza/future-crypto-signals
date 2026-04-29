# Telegram Notifier — Design

## Module Structure

```
src/notifier/
├── __init__.py        # exports TelegramNotifier, NotifierConfig
├── config.py          # NotifierConfig reads env vars
├── formatter.py       # format_signal(signal) -> str
└── client.py          # TelegramNotifier.send(signal)
```

## NotifierConfig (`config.py`)

```python
class NotifierConfig:
    def __init__(self) -> None:
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if not self.bot_token or not self.chat_id:
            raise ConfigError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")
```

## formatter (`formatter.py`)

Pure function, no I/O:

```python
def format_signal(signal: Signal) -> str:
    return (
        f"[{signal.direction.value.upper()}] {signal.symbol} {signal.timeframe}\n"
        f"Close: {signal.close:.2f}\n"
        f"RSI: {signal.rsi:.1f}\n"
        f"SMA8: {signal.sma_short:.2f} | SMA21: {signal.sma_long:.2f}\n"
        f"Supertrend: {signal.supertrend_direction.upper()}\n"
        f"Time: {signal.timestamp}"
    )
```

## TelegramNotifier (`client.py`)

```python
class TelegramNotifier:
    def __init__(self, config: NotifierConfig) -> None:
        self._config = config
        self._url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"

    def send(self, signal: Signal) -> None:
        if signal.direction == SignalDirection.NO_SIGNAL:
            return
        response = httpx.post(self._url, json={
            "chat_id": self._config.chat_id,
            "text": format_signal(signal),
        })
        response.raise_for_status()
```

## Integration in `main.py`

```python
notifier = TelegramNotifier(NotifierConfig())
# inside signal loop:
if signal.direction != SignalDirection.NO_SIGNAL:
    notifier.send(signal)
```

## Dependencies

- `httpx` — sync HTTP client
