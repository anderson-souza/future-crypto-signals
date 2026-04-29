from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.chart import ChartData, render_chart, save_chart
from src.exceptions import InsufficientDataError
from src.fetcher import BinanceFetcher, FetcherConfig
from src.indicators import IndicatorConfig, calculate_indicators
from src.signals import SignalDirection, evaluate_signal


def main() -> None:
    cfg = FetcherConfig()
    fetcher = BinanceFetcher(cfg)
    indicator_cfg = IndicatorConfig()

    min_candles = max(
        indicator_cfg.rsi_period + 1,
        indicator_cfg.sma_long_period,
        indicator_cfg.supertrend_period + 1,
    )

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

    print(f"Found {len(signals)} signal(s):\n")
    for s in signals:
        print(
            f"  [{s.timestamp}]  {s.direction.value.upper():4}  "
            f"Close: {s.close:.2f}  RSI: {s.rsi:.1f}  "
            f"SMA8: {s.sma_short:.2f}  SMA21: {s.sma_long:.2f}  "
            f"Supertrend: {s.supertrend_direction.upper()}"
        )

    if signals:
        path = Path("chart.png")
        png = render_chart(ChartData(candles=candles, signals=signals, config=indicator_cfg))
        save_chart(png, path)
        print(f"\n→ chart saved to {path}")


if __name__ == "__main__":
    main()
