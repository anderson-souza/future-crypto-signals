# Signal Persistence Specification

## Problem Statement

Sinais gerados são efêmeros — existem apenas na memória durante a execução. Sem
persistência, não há como revisar histórico de sinais, analisar qualidade ao longo
do tempo, ou identificar padrões de falso-positivo. A deduplicação in-memory também
reinicia a cada restart do processo.

## Goals

- [ ] Persistir cada sinal gerado (BUY/SELL/NO_SIGNAL) com todos os campos de contexto
- [ ] Manter catálogo de criptomoedas monitoradas como referência normalizada
- [ ] Substituir deduplicação in-memory por consulta ao banco (sobrevive a restarts)
- [ ] Não impactar latência do loop de scan — write assíncrono ou tolerante a falha

## Out of Scope

- Dashboard ou UI de visualização
- Backtesting sobre sinais persistidos
- Alertas baseados em histórico
- Limpeza / TTL automático de registros antigos

---

## Data Model

### `cryptocurrencies` — Catálogo de símbolos

| Coluna | Tipo | Restrições |
|--------|------|------------|
| `id` | INTEGER | PK, autoincrement |
| `symbol` | TEXT | NOT NULL, UNIQUE (ex: `BTCUSDT`) |
| `base_asset` | TEXT | NOT NULL (ex: `BTC`) |
| `quote_asset` | TEXT | NOT NULL (ex: `USDT`) |
| `created_at` | DATETIME | NOT NULL, default now |

**Regra:** upsert — se símbolo já existe, reutiliza o registro.

---

### `signals` — Histórico de sinais

| Coluna | Tipo | Restrições |
|--------|------|------------|
| `id` | INTEGER | PK, autoincrement |
| `cryptocurrency_id` | INTEGER | FK → cryptocurrencies.id, NOT NULL |
| `timeframe` | TEXT | NOT NULL (ex: `1h`) |
| `direction` | TEXT | NOT NULL, CHECK IN (`buy`, `sell`, `no_signal`) |
| `close` | REAL | NOT NULL |
| `rsi` | REAL | NOT NULL |
| `sma_short` | REAL | NOT NULL |
| `sma_long` | REAL | NOT NULL |
| `supertrend_value` | REAL | NOT NULL |
| `supertrend_direction` | TEXT | NOT NULL |
| `rvol` | REAL | NOT NULL |
| `volume_suppressed` | INTEGER | NOT NULL, CHECK IN (0, 1) |
| `candle_timestamp` | DATETIME | NOT NULL — timestamp do candle que gerou o sinal |
| `created_at` | DATETIME | NOT NULL, default now |

**Índice:** `(cryptocurrency_id, timeframe, direction, created_at)` — otimiza consulta de deduplicação.

---

## User Stories

### P1: Persistir sinal ao final de cada ciclo ⭐ MVP

**User Story**: Como sistema, quero persistir cada sinal avaliado no banco para que eu
possa revisar o histórico de sinais gerados.

**Acceptance Criteria**:

1. QUANDO `evaluate_signal()` retornar qualquer `Signal` (incluindo NO_SIGNAL) ENTÃO o
   sistema SHALL inserir um registro em `signals`
2. QUANDO a gravação falhar (ex: disco cheio, lock) ENTÃO o sistema SHALL logar o erro
   e continuar o loop — persistência não bloqueia notificação
3. QUANDO o mesmo sinal for gravado duas vezes ENTÃO o sistema SHALL inserir dois registros
   — `signals` é append-only (dedup é consulta separada)

**Independent Test**: Chamar `SignalRepository.save(signal)` com um `Signal` válido
→ assert `SELECT COUNT(*) FROM signals = 1`.

---

### P1: Upsert de criptomoeda ao detectar símbolo ⭐ MVP

**User Story**: Como sistema, quero que cada símbolo monitorado exista como registro em
`cryptocurrencies` para que sinais possam referenciar a cripto de forma normalizada.

**Acceptance Criteria**:

1. QUANDO um sinal é salvo para `BTCUSDT` pela primeira vez ENTÃO o sistema SHALL inserir
   `cryptocurrencies(symbol='BTCUSDT', base_asset='BTC', quote_asset='USDT')`
2. QUANDO o mesmo símbolo aparecer novamente ENTÃO o sistema SHALL reutilizar o registro
   existente (upsert — sem duplicatas)
3. QUANDO o símbolo não seguir o padrão `<BASE>USDT` ENTÃO o sistema SHALL usar
   `base_asset = symbol[:-4]` e `quote_asset = symbol[-4:]` como fallback

**Independent Test**: Chamar `CryptocurrencyRepository.upsert('ETHUSDT')` duas vezes
→ assert `SELECT COUNT(*) FROM cryptocurrencies = 1`.

---

### P2: Deduplicação via banco (sobrevive a restart)

**User Story**: Como sistema, quero que a deduplicação de sinais consulte o banco em vez
de memória para que restarts não causem re-alertas dentro da janela de cooldown.

**Acceptance Criteria**:

1. QUANDO `is_duplicate(signal)` for chamado ENTÃO o sistema SHALL consultar `signals`
   filtrando por `(symbol, timeframe, direction)` com `created_at > now - cooldown`
2. QUANDO existir registro dentro da janela ENTÃO SHALL retornar `True` (duplicata)
3. QUANDO o banco estiver inacessível ENTÃO SHALL logar erro e retornar `False`
   (fail-open — prefere re-alertar a bloquear indefinidamente)
4. `SignalDeduplicator` existente SHALL aceitar um `SignalRepository` como dependência
   injetada — fallback para in-memory se `None`

**Independent Test**: Inserir sinal manualmente no DB com `created_at = now - 1h`.
Chamar `is_duplicate` com cooldown=4h → assert `True`.

---

## Technical Decisions

### Banco: SQLite

- Zero infra — arquivo local `.data/signals.db`
- Suficiente para uso pessoal (< 1M registros em anos de operação)
- Sem dependência de servidor externo

### Acesso: stdlib `sqlite3` + SQL explícito

- Sem ORM — projeto pequeno, queries simples
- SQL legível e sem abstração desnecessária
- Migrations via script `.sql` versionado em `db/migrations/`

### Camada: `src/persistence/`

```
src/persistence/
├── __init__.py
├── database.py          # conexão, init schema
├── repositories/
│   ├── __init__.py
│   ├── cryptocurrency.py   # CryptocurrencyRepository
│   └── signal.py           # SignalRepository
└── migrations/
    └── 001_initial.sql
```

### Integração no loop

`scanner/loop.py` receberá `SignalRepository` + `CryptocurrencyRepository` como
dependências injetadas. Persistência ocorre APÓS `notifier.send()` — não bloqueia
notificação se falhar.

---

## Edge Cases

- QUANDO banco não existe → `database.py` cria o arquivo e executa migration automaticamente
- QUANDO `Signal.direction == NO_SIGNAL` → ainda persiste (P2 pode filtrar por direction)
- QUANDO `symbol` não termina em `USDT` (ex: `BTCBUSD`) → fallback de parsing aceita
- QUANDO `candle_timestamp` é timezone-aware → armazenar como UTC string ISO-8601

---

## Success Criteria

- [ ] `signals` inserido para cada ciclo de scan (BUY/SELL/NO_SIGNAL)
- [ ] `cryptocurrencies` upsert sem duplicatas
- [ ] Falha de gravação não derruba o loop
- [ ] Deduplicação DB-backed sobrevive a restart do processo
- [ ] Schema criado automaticamente na primeira execução
