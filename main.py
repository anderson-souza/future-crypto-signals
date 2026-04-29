from dotenv import load_dotenv

load_dotenv()

from src.fetcher import BinanceFetcher, FetcherConfig
from src.indicators import IndicatorConfig, calculate_indicators
from src.signals import SignalDirection, evaluate_signal
from src.exceptions import InsufficientDataError
from src.notifier import TelegramNotifier, NotifierConfig


def main() -> None:
    cfg = FetcherConfig()
    fetcher = BinanceFetcher(cfg)
    indicator_cfg = IndicatorConfig()
    notifier = TelegramNotifier(NotifierConfig())

    min_candles = max(indicator_cfg.rsi_period + 1, indicator_cfg.sma_long_period, indicator_cfg.supertrend_period + 1)

    print("Fetching 500 candles for BTCUSDT 4h...")
    candles = fetcher.fetch_candles("BTCUSDT", "4h", 500)
    print(f"Got {len(candles)} candles\n")

    signals = []
    for i in range(min_candles, len(candles) + 1):
        window = candles[:i]
        try:
            indicators = calculate_indicators(window, indicator_cfg)
        except InsufficientDataError:
            continue
        signal = evaluate_signal(indicators, window[-1])
        if signal.direction != SignalDirection.NO_SIGNAL:
            signals.append(signal)
            notifier.send(signal)

    print(f"Found {len(signals)} signal(s):\n")
    for s in signals:
        print(
            f"  [{s.timestamp}]  {s.direction.value.upper():4}  "
            f"Close: {s.close:.2f}  RSI: {s.rsi:.1f}  "
            f"SMA8: {s.sma_short:.2f}  SMA21: {s.sma_long:.2f}  "
            f"Supertrend: {s.supertrend_direction.upper()}"
        )


if __name__ == "__main__":
    main()
