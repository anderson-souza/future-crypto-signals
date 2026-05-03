# Signal Persistence — Design

## Module Structure

```
src/persistence/
├── __init__.py                     # public API
├── config.py                       # PersistenceConfig (DB path)
├── database.py                     # Database — connection + schema init
├── exceptions.py                   # PersistenceError
└── repositories/
    ├── __init__.py
    ├── cryptocurrency.py           # CryptocurrencyRepository
    └── signal.py                   # SignalRepository

db/
└── migrations/
    └── 001_initial.sql             # schema DDL
```

---

## Schema SQL — `db/migrations/001_initial.sql`

```sql
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
    candle_timestamp     DATETIME NOT NULL,
    created_at           DATETIME NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_signals_dedup
    ON signals(cryptocurrency_id, timeframe, direction, created_at);
```

---

## Classes

### `PersistenceConfig`

```python
class PersistenceConfig:
    def __init__(self) -> None:
        self.db_path: str = os.getenv("DB_PATH", ".data/signals.db")
```

---

### `Database`

Gerencia conexão SQLite e executa migration na inicialização.

```python
class Database:
    def __init__(self, config: PersistenceConfig) -> None: ...

    def initialize(self) -> None:
        """Cria diretório pai e executa 001_initial.sql se tabelas não existem."""

    def get_connection(self) -> sqlite3.Connection:
        """Retorna conexão com row_factory=sqlite3.Row e detect_types=PARSE_DECLTYPES."""
```

**Decisões:**
- `check_same_thread=False` — loop single-threaded, mas permite reuso da conexão
- `detect_types=PARSE_DECLTYPES` — converte `DATETIME` → `datetime` automaticamente
- `initialize()` chamado 1x no startup — sem overhead no ciclo de scan

---

### `CryptocurrencyRepository`

```python
class CryptocurrencyRepository:
    def __init__(self, db: Database) -> None: ...

    def upsert(self, symbol: str) -> int:
        """
        Insere ou ignora. Retorna id do registro (novo ou existente).
        Parsing: base_asset = symbol[:-4], quote_asset = symbol[-4:]
        """
```

**SQL:**
```sql
INSERT INTO cryptocurrencies (symbol, base_asset, quote_asset)
VALUES (?, ?, ?)
ON CONFLICT(symbol) DO NOTHING;

SELECT id FROM cryptocurrencies WHERE symbol = ?;
```

**Notas:**
- `ON CONFLICT DO NOTHING` evita upsert complexo — o SELECT seguinte garante o id
- Parsing de `base_asset`/`quote_asset` assume sufixo `USDT` (4 chars) — funciona para
  `BTCUSDT`, `ETHUSDT`, `SOLUSDT` etc. Fallback aceita qualquer sufixo de 4 chars.

---

### `SignalRepository`

```python
class SignalRepository:
    def __init__(self, db: Database) -> None: ...

    def save(self, signal: Signal, cryptocurrency_id: int) -> None:
        """Insert append-only. Falha loga e propaga PersistenceError."""

    def find_last_sent_at(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        since: datetime,
    ) -> datetime | None:
        """
        Retorna created_at do sinal mais recente que bate (symbol, timeframe, direction)
        com created_at >= since. Usado pelo deduplicador DB-backed.
        """
```

**SQL save:**
```sql
INSERT INTO signals (
    cryptocurrency_id, timeframe, direction, close, rsi,
    sma_short, sma_long, supertrend_value, supertrend_direction,
    rvol, volume_suppressed, candle_timestamp
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
```

**SQL find_last_sent_at:**
```sql
SELECT s.created_at
FROM   signals s
JOIN   cryptocurrencies c ON c.id = s.cryptocurrency_id
WHERE  c.symbol    = ?
AND    s.timeframe = ?
AND    s.direction = ?
AND    s.created_at >= ?
ORDER  BY s.created_at DESC
LIMIT  1;
```

---

### `SignalDeduplicator` — extensão DB-backed (P2)

Modificação cirúrgica: aceita `SignalRepository` opcional.

```python
class SignalDeduplicator:
    def __init__(
        self,
        cooldown_seconds: int,
        signal_repo: SignalRepository | None = None,
    ) -> None:
        self._cooldown = timedelta(seconds=cooldown_seconds)
        self._signal_repo = signal_repo
        self._sent: dict[tuple[str, str, str], datetime] = {}  # fallback in-memory

    def is_duplicate(self, signal: Signal) -> bool:
        if self._signal_repo is not None:
            return self._is_duplicate_db(signal)
        return self._is_duplicate_memory(signal)

    def mark_sent(self, signal: Signal) -> None:
        if self._signal_repo is None:
            key = (signal.symbol, signal.timeframe, signal.direction.value)
            self._sent[key] = datetime.now(UTC)
        # DB-backed: sinal já foi persistido em SignalRepository.save() — no-op

    def _is_duplicate_db(self, signal: Signal) -> bool:
        since = datetime.now(UTC) - self._cooldown
        try:
            result = self._signal_repo.find_last_sent_at(  # type: ignore[union-attr]
                signal.symbol, signal.timeframe, signal.direction.value, since
            )
            return result is not None
        except PersistenceError:
            logger.error("Dedup DB query failed — fail-open (allowing signal)")
            return False
```

**Invariante:** `mark_sent` só grava in-memory quando `signal_repo is None`. Em modo
DB-backed, `SignalRepository.save()` no loop já persiste o sinal — chamar `mark_sent`
seria gravação dupla.

---

## Integração no Loop — `scanner/loop.py`

### Mudanças em `run_scanner()`

```python
def run_scanner() -> None:
    # ... configs existentes ...

    persistence_cfg = PersistenceConfig()
    db = Database(persistence_cfg)
    db.initialize()
    crypto_repo = CryptocurrencyRepository(db)
    signal_repo = SignalRepository(db)

    dedup = SignalDeduplicator(scanner_cfg.signal_cooldown_seconds, signal_repo)
    # ...
```

### Mudanças em `_scan_pair()`

Assinatura adiciona `crypto_repo` e `signal_repo`. Fluxo após `evaluate_signal`:

```
signal = evaluate_signal(indicators, candles[-1])

# 1. Upsert cripto + persistir sinal (sempre, inclusive NO_SIGNAL)
try:
    crypto_id = crypto_repo.upsert(symbol)
    signal_repo.save(signal, crypto_id)
except PersistenceError as exc:
    logger.error("%s %s: persistence failed: %s", symbol, timeframe, exc)
    # continua — persistência não bloqueia notificação

# 2. Filtros (igual ao fluxo atual)
if signal.direction == SignalDirection.NO_SIGNAL:
    logger.debug(...)
    return

if dedup.is_duplicate(signal):
    logger.info(...)
    return

# 3. Notificação
if notifier: ...

# 4. mark_sent (no-op em modo DB-backed)
dedup.mark_sent(signal)
```

**Ordem:** persist → filtrar → notificar. Persistência acontece antes da notificação
para garantir que mesmo sinais filtrados (dedup) ficam no histórico.

---

## Exceções

```python
# src/persistence/exceptions.py
class PersistenceError(Exception):
    def __init__(self, operation: str, message: str = "") -> None:
        self.operation = operation
        super().__init__(message or f"Persistence failed during '{operation}'")
```

Todos os métodos de repositório capturam `sqlite3.Error` e relançam como
`PersistenceError` — isolam o caller do detalhe de implementação sqlite3.

---

## `src/persistence/__init__.py` — API pública

```python
from src.persistence.config import PersistenceConfig
from src.persistence.database import Database
from src.persistence.exceptions import PersistenceError
from src.persistence.repositories.cryptocurrency import CryptocurrencyRepository
from src.persistence.repositories.signal import SignalRepository

__all__ = [
    "CryptocurrencyRepository",
    "Database",
    "PersistenceConfig",
    "PersistenceError",
    "SignalRepository",
]
```

---

## Env Vars Adicionadas

| Variável | Default | Descrição |
|---|---|---|
| `DB_PATH` | `.data/signals.db` | Caminho do arquivo SQLite |

---

## Dependências

Nenhuma nova dependência de runtime — `sqlite3` é stdlib Python.

`.data/` deve ser adicionado ao `.gitignore`.

---

## Diagrama de Dependências (atualizado)

```
scanner/loop.py
  ├─ persistence/
  │    ├─ Database
  │    ├─ CryptocurrencyRepository  ←── signals/models.py (symbol parsing)
  │    └─ SignalRepository          ←── signals/models.py (Signal)
  └─ scanner/deduplicator.py       ←── persistence/repositories/signal.py (opcional)
```

Sem ciclos. `persistence/` depende apenas de `signals/models.py` — não depende de
`scanner/`, `notifier/`, `chart/`.
