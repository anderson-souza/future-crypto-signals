from src.signals.models import Signal


def format_signal(signal: Signal) -> str:
    return (
        f"[{signal.direction.value.upper()}] {signal.symbol} {signal.timeframe}\n"
        f"Close: {signal.close:.2f}\n"
        f"RSI: {signal.rsi:.1f}\n"
        f"SMA8: {signal.sma_short:.2f} | SMA21: {signal.sma_long:.2f}\n"
        f"Supertrend: {signal.supertrend_direction.upper()}\n"
        f"Time: {signal.timestamp}"
    )
