from dotenv import load_dotenv

load_dotenv()

from src.fetcher import BinanceFetcher, FetcherConfig
from src.indicators import IndicatorConfig, calculate_indicators


def main() -> None:
    cfg = FetcherConfig()
    fetcher = BinanceFetcher(cfg)

    print("Fetching 100 candles for BTCUSDT 1h...")
    candles = fetcher.fetch_candles("BTCUSDT", "1h", 100)
    print(f"Got {len(candles)} candles\n")

    indicators = calculate_indicators(candles, IndicatorConfig())
    print(f"RSI(14):          {indicators.rsi:.2f}")
    print(f"SMA(20):          {indicators.sma:.2f}")
    print(f"Supertrend:       {indicators.supertrend.value:.2f} [{indicators.supertrend.direction.value.upper()}]")


if __name__ == "__main__":
    main()
