CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    symbol      TEXT     NOT NULL UNIQUE,
    base_asset  TEXT     NOT NULL,
    quote_asset TEXT     NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE TABLE IF NOT EXISTS signals (
    id                   INTEGER  PRIMARY KEY AUTOINCREMENT,
    cryptocurrency_id    INTEGER  NOT NULL REFERENCES cryptocurrencies(id),
    timeframe            TEXT     NOT NULL,
    direction            TEXT     NOT NULL CHECK(direction IN ('buy', 'sell', 'no_signal')),
    close                REAL     NOT NULL,
    rsi                  REAL     NOT NULL,
    sma_short            REAL     NOT NULL,
    sma_long             REAL     NOT NULL,
    supertrend_value     REAL     NOT NULL,
    supertrend_direction TEXT     NOT NULL,
    rvol                 REAL     NOT NULL,
    volume_suppressed    INTEGER  NOT NULL CHECK(volume_suppressed IN (0, 1)),
    candle_timestamp     TEXT     NOT NULL,
    created_at           DATETIME NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_signals_dedup
    ON signals(cryptocurrency_id, timeframe, direction, created_at);
