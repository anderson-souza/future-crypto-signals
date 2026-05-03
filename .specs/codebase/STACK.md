# Tech Stack

**Analyzed:** 2026-05-02

## Core

- Language: Python 3.13+
- Package manager: uv
- Entry point: main.py → src/scanner/run_scanner()

## Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| ccxt | >=4.5.51 | Exchange API abstraction — Binance Futures OHLCV |
| httpx | >=0.28.1 | Synchronous HTTP client — Telegram Bot API |
| pydantic | >=2.13.3 | Data validation, frozen models |
| pydantic-settings | >=2.14.0 | Present but NOT used for list fields (JSONDecodeError risk) |
| pandas-ta-classic | >=0.4.47 | Technical indicators — import as `pandas_ta_classic` |
| mplfinance | >=0.12.10b0 | Candlestick chart rendering |
| python-dotenv | implicit | .env file loading in main.py |

## Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=9.0.3 | Test framework |
| pytest-cov | >=7.1.0 | Coverage reporting |
| ruff | >=0.15.12 | Linting + formatting |
| ty | >=0.0.32 | Type checking |

## External Services

- Exchange: Binance USD-Margined Futures (`ccxt.binanceusdm`)
- Notifications: Telegram Bot API (sendMessage, sendPhoto)

## Testing

- Unit: pytest
- Coverage: pytest-cov (~98% current)
- No CI/CD config (.github/workflows absent)

## Development Tools

- Formatter/Linter: ruff
- Type checker: ty
- Lock file: uv.lock (332KB, all transitive deps pinned)
