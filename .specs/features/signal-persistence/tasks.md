# Signal Persistence — Tasks

**Feature:** Signal Persistence
**Spec:** [spec.md](./spec.md)
**Design:** [design.md](./design.md)
**Status:** TODO

---

## Phase 1 — Infraestrutura base

### T01 — Migration SQL + .gitignore
**Files:** `db/migrations/001_initial.sql`, `.gitignore`
**Actions:**
- Criar `db/migrations/001_initial.sql` com DDL de `cryptocurrencies` e `signals` (ver design)
- Adicionar `.data/` ao `.gitignore`

**Verify:** arquivo SQL existe e contém as 2 tabelas + índice de dedup

---

### T02 — PersistenceConfig
**Files:** `src/persistence/config.py`
**Actions:**
- Criar `PersistenceConfig` com `db_path = os.getenv("DB_PATH", ".data/signals.db")`

**Verify:** `PersistenceConfig().db_path == ".data/signals.db"` sem env var

---

### T03 — PersistenceError
**Files:** `src/persistence/exceptions.py`
**Actions:**
- Criar `PersistenceError(Exception)` com campo `operation: str`

**Verify:** `str(PersistenceError("save"))` contém `"save"`

---

### T04 — Database — testes
**Files:** `tests/persistence/test_database.py`
**Actions (TDD — RED first):**
- `test_initialize_creates_tables` — após `db.initialize()`, tabelas `cryptocurrencies` e `signals` existem
- `test_initialize_creates_parent_dir` — `initialize()` cria diretório pai se não existir
- `test_initialize_idempotent` — chamar `initialize()` duas vezes não lança exceção
- Usar `tmp_path` (pytest fixture) para isolar arquivos de teste

**Verify:** todos falham antes de T05

---

### T05 — Database — implementação
**Files:** `src/persistence/database.py`
**Actions:**
- `Database.__init__(config: PersistenceConfig)` — armazena config
- `initialize()` — cria dir pai com `Path.mkdir(parents=True, exist_ok=True)`, lê e executa `db/migrations/001_initial.sql`
- `get_connection()` — `sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)` com `row_factory=sqlite3.Row`

**Verify:** testes T04 passam

---

## Phase 2 — Repositórios

### T06 — CryptocurrencyRepository — testes
**Files:** `tests/persistence/test_cryptocurrency_repository.py`
**Actions (TDD — RED first):**
- `test_upsert_inserts_new_symbol` — `upsert("BTCUSDT")` insere registro, retorna `id > 0`
- `test_upsert_parses_assets` — `base_asset="BTC"`, `quote_asset="USDT"`
- `test_upsert_idempotent` — segunda chamada retorna mesmo `id`, count=1
- `test_upsert_different_symbols` — retorna ids distintos
- Fixture: `db` com `tmp_path` inicializado

**Verify:** todos falham antes de T07

---

### T07 — CryptocurrencyRepository — implementação
**Files:** `src/persistence/repositories/cryptocurrency.py`
**Actions:**
- `CryptocurrencyRepository.__init__(db: Database)`
- `upsert(symbol: str) -> int` — `INSERT OR IGNORE` + `SELECT id`
- Parsing: `base_asset = symbol[:-4]`, `quote_asset = symbol[-4:]`
- Captura `sqlite3.Error` → relança como `PersistenceError("upsert")`

**Verify:** testes T06 passam

---

### T08 — SignalRepository — testes
**Files:** `tests/persistence/test_signal_repository.py`
**Actions (TDD — RED first):**
- `test_save_inserts_signal` — `save(signal, crypto_id=1)` → count=1 em `signals`
- `test_save_all_fields` — SELECT e assert cada campo (direction, rsi, close, etc.)
- `test_save_no_signal_direction` — persiste `NO_SIGNAL` sem erro
- `test_find_last_sent_at_returns_none_when_empty` — retorna `None`
- `test_find_last_sent_at_within_window` — signal com `created_at = now - 1h`, `since = now - 4h` → retorna datetime
- `test_find_last_sent_at_outside_window` — signal com `created_at = now - 5h`, `since = now - 4h` → retorna `None`
- `test_find_last_sent_at_filters_by_direction` — sinal BUY não conta como dedup de SELL
- Helper: `make_signal(direction=BUY)` — cria `Signal` com valores válidos

**Verify:** todos falham antes de T09

---

### T09 — SignalRepository — implementação
**Files:** `src/persistence/repositories/signal.py`
**Actions:**
- `SignalRepository.__init__(db: Database)`
- `save(signal: Signal, cryptocurrency_id: int) -> None` — INSERT com todos os campos; `candle_timestamp` como ISO-8601 UTC; captura `sqlite3.Error` → `PersistenceError("save")`
- `find_last_sent_at(symbol, timeframe, direction, since) -> datetime | None` — JOIN query do design; retorna `datetime` ou `None`; captura `sqlite3.Error` → `PersistenceError("find_last_sent_at")`

**Verify:** testes T08 passam

---

### T10 — Public API `src/persistence/__init__.py`
**Files:** `src/persistence/__init__.py`, `src/persistence/repositories/__init__.py`
**Actions:**
- `src/persistence/__init__.py` exporta: `Database`, `PersistenceConfig`, `PersistenceError`, `CryptocurrencyRepository`, `SignalRepository`
- `src/persistence/repositories/__init__.py` vazio ou re-exporta repositórios

**Verify:** `from src.persistence import Database, SignalRepository` funciona

---

## Phase 3 — Deduplicação DB-backed (P2)

### T11 — SignalDeduplicator DB-backed — testes
**Files:** `tests/scanner/test_deduplicator.py` (atualizar existente)
**Actions (TDD — RED first):**
- `test_is_duplicate_db_returns_true_when_recent_signal_exists`
- `test_is_duplicate_db_returns_false_when_outside_cooldown`
- `test_is_duplicate_db_fail_open_on_persistence_error` — `find_last_sent_at` lança `PersistenceError` → retorna `False`
- `test_mark_sent_noop_when_repo_provided` — chamar `mark_sent` não chama nenhum método no repo
- `test_falls_back_to_memory_when_no_repo` — comportamento in-memory existente preservado

**Verify:** testes novos falham antes de T12

---

### T12 — SignalDeduplicator — extensão DB-backed
**Files:** `src/scanner/deduplicator.py`
**Actions:**
- Adicionar parâmetro `signal_repo: SignalRepository | None = None` ao `__init__`
- `is_duplicate` — delega para `_is_duplicate_db` se `signal_repo` presente, senão `_is_duplicate_memory`
- `_is_duplicate_db` — chama `signal_repo.find_last_sent_at(...)` com `since = now - cooldown`; captura `PersistenceError` → loga + retorna `False`
- `mark_sent` — grava in-memory só se `signal_repo is None`

**Verify:** testes T11 passam; testes in-memory existentes continuam passando

---

## Phase 4 — Integração no Loop

### T13 — Loop — testes de integração
**Files:** `tests/scanner/test_loop_persistence.py`
**Actions (TDD — RED first):**
- `test_signal_persisted_after_evaluate` — mock `SignalRepository.save`; chamar `_scan_pair`; assert `save` chamado 1x
- `test_no_signal_still_persisted` — `evaluate_signal` retorna NO_SIGNAL; assert `save` ainda chamado
- `test_persistence_failure_does_not_stop_notification` — `save` lança `PersistenceError`; assert notifier ainda chamado
- `test_crypto_upsert_called_per_scan` — assert `CryptocurrencyRepository.upsert` chamado com o symbol correto

**Verify:** todos falham antes de T14

---

### T14 — Loop — integração
**Files:** `src/scanner/loop.py`
**Actions:**
- Em `run_scanner()`: criar `PersistenceConfig`, `Database`, `db.initialize()`, `CryptocurrencyRepository`, `SignalRepository`
- Passar `signal_repo` para `SignalDeduplicator`
- Adicionar `crypto_repo` e `signal_repo` à assinatura de `_scan_pair`
- Em `_scan_pair`: após `evaluate_signal`, bloco `try/except PersistenceError` que chama `crypto_repo.upsert(symbol)` + `signal_repo.save(signal, crypto_id)`, loga erro e continua
- Persistência ocorre ANTES do filtro `NO_SIGNAL` e dedup

**Verify:** testes T13 passam; loop executa sem erro com `DB_PATH=/tmp/test.db`

---

## Phase 5 — Qualidade

### T15 — Smoke test end-to-end
**Actions:**
- `uv run python -c "from src.persistence import Database, PersistenceConfig; db = Database(PersistenceConfig()); db.initialize(); print('OK')"`
- Verificar criação de `.data/signals.db` com tabelas

**Verify:** sem exceção; arquivo DB existe; `.tables` no sqlite3 mostra as 2 tabelas

---

### T16 — Coverage check
**Actions:**
- `uv run pytest tests/persistence/ tests/scanner/test_deduplicator.py tests/scanner/test_loop_persistence.py --cov=src/persistence --cov=src/scanner/deduplicator --cov-report=term-missing`

**Verify:** coverage ≥ 90% em `src/persistence/`

---

## Dependências entre tasks

```
T01 → T05 (migration SQL lida em initialize)
T02 → T05
T03 → T07, T09
T04 → T05 (RED/GREEN)
T05 → T07, T09
T06 → T07 (RED/GREEN)
T07 → T10
T08 → T09 (RED/GREEN)
T09 → T10
T10 → T12, T14
T11 → T12 (RED/GREEN)
T12 → T14
T13 → T14 (RED/GREEN)
T14 → T15 → T16
```

## Ordem de execução recomendada

```
T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09 → T10
→ T11 → T12 → T13 → T14 → T15 → T16
```

Total: **16 tasks** | Estimativa: ~3-4h
