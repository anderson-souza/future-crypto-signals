import logging
import time

from src.chart import ChartData, render_chart
from src.exceptions import ConfigError, InsufficientDataError
from src.fetcher import BinanceFetcher, FetcherConfig
from src.indicators import IndicatorConfig, calculate_indicators
from src.notifier import NotifierConfig, TelegramNotifier
from src.persistence import (
    CryptocurrencyRepository,
    Database,
    PersistenceConfig,
    PersistenceError,
    SignalRepository,
)
from src.scanner.config import ScannerConfig
from src.scanner.deduplicator import SignalDeduplicator
from src.signals import SignalDirection, evaluate_signal

logger = logging.getLogger(__name__)


def run_scanner() -> None:
    fetcher_cfg = FetcherConfig()
    indicator_cfg = IndicatorConfig()
    scanner_cfg = ScannerConfig()

    notifier: TelegramNotifier | None
    try:
        # notifier = TelegramNotifier(NotifierConfig())
        notifier = None  # Disable Telegram for now
    except ConfigError:
        logger.warning("Telegram not configured — signals logged to console only")
        notifier = None

    db = Database(PersistenceConfig())
    db.initialize()
    crypto_repo = CryptocurrencyRepository(db)
    signal_repo = SignalRepository(db)

    dedup = SignalDeduplicator(scanner_cfg.signal_cooldown_seconds, signal_repo)
    fetcher = BinanceFetcher(fetcher_cfg)

    min_candles = max(
        indicator_cfg.rsi_period + 1,
        indicator_cfg.sma_long_period,
        indicator_cfg.supertrend_period + 1,
        indicator_cfg.volume_period + 1,
    )

    logger.info(
        "Scanner started | symbols=%s timeframes=%s interval=%ds cooldown=%ds",
        fetcher_cfg.symbols,
        fetcher_cfg.timeframes,
        scanner_cfg.scan_interval_seconds,
        scanner_cfg.signal_cooldown_seconds,
    )

    while True:
        for symbol in fetcher_cfg.symbols:
            for timeframe in fetcher_cfg.timeframes:
                _scan_pair(
                    symbol,
                    timeframe,
                    fetcher,
                    fetcher_cfg,
                    indicator_cfg,
                    min_candles,
                    dedup,
                    notifier,
                    crypto_repo,
                    signal_repo,
                )

        logger.info(
            "Cycle complete. Sleeping %ds...", scanner_cfg.scan_interval_seconds
        )
        time.sleep(scanner_cfg.scan_interval_seconds)


def _scan_pair(
    symbol: str,
    timeframe: str,
    fetcher: BinanceFetcher,
    fetcher_cfg: FetcherConfig,
    indicator_cfg: IndicatorConfig,
    min_candles: int,
    dedup: SignalDeduplicator,
    notifier: TelegramNotifier | None,
    crypto_repo: CryptocurrencyRepository,
    signal_repo: SignalRepository,
) -> None:
    try:
        candles = fetcher.fetch_candles(symbol, timeframe, fetcher_cfg.default_limit)

        if len(candles) < min_candles:
            logger.warning(
                "%s %s: insufficient candles (%d)", symbol, timeframe, len(candles)
            )
            return

        indicators = calculate_indicators(candles, indicator_cfg)
        signal = evaluate_signal(indicators, candles[-1])

        try:
            crypto_id = crypto_repo.upsert(symbol)
            signal_repo.save(signal, crypto_id)
        except PersistenceError as exc:
            logger.error("%s %s: persistence failed: %s", symbol, timeframe, exc)

        if signal.direction == SignalDirection.NO_SIGNAL:
            logger.debug("%s %s: no signal", symbol, timeframe)
            return

        if dedup.is_duplicate(signal):
            logger.info(
                "%s %s: duplicate %s — skipping",
                symbol,
                timeframe,
                signal.direction.value,
            )
            return

        logger.info(
            "SIGNAL %s %s %s close=%.2f",
            signal.direction.value,
            symbol,
            timeframe,
            signal.close,
        )

        if notifier:
            notifier.send(signal)
            png = render_chart(
                ChartData(candles=candles, signals=[signal], config=indicator_cfg)
            )
            notifier.send_chart(signal, png)

        dedup.mark_sent(signal)

    except InsufficientDataError as exc:
        logger.warning("%s %s: %s", symbol, timeframe, exc)
    except Exception as exc:
        logger.error("%s %s: unexpected error: %s", symbol, timeframe, exc)
