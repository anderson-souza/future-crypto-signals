# CLAUDE.md

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Commits — Conventional Commits

**Format:**
```
<type>(<scope>): <short description>

[optional body]
```

**Types:**

| Type | When |
|------|------|
| `feat` | New feature or behaviour |
| `fix` | Bug fix |
| `refactor` | Code change that is not a fix or feature |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `chore` | Build, deps, config — no production code |
| `perf` | Performance improvement |

**Rules:**
- Description: imperative, lowercase, no period (`add signal persistence`, not `Added signal persistence.`)
- Scope: module or layer affected, optional (`feat(persistence): ...`, `fix(scanner): ...`)
- Body: explain *why*, not *what* — what is already in the diff
- Breaking change: append `!` after type (`feat!: ...`) and describe in body

**Examples:**
```
feat(persistence): add SQLite-backed signal and crypto repositories
fix(scanner): fail-open on dedup DB error to prevent signal loss
refactor(deduplicator): extract _is_duplicate_db for clarity
test(persistence): cover find_last_sent_at boundary cases
```

---

## 6. Project-Specific Knowledge

### Binance Futures via ccxt

- Use `ccxt.binanceusdm` — not `ccxt.binance` with `defaultType: 'future'`. The latter loads spot + margin markets and requires auth.
- `load_markets()` internally calls `fetch_currencies()` which hits an authenticated endpoint. For public OHLCV data, patch it out:
  ```python
  exchange.fetch_currencies = lambda *args, **kwargs: {}
  ```
- OHLCV candle fetching is fully public — no API key required.
- API keys are only needed for order placement, account balance, trade history.

### Config

- Do NOT use `pydantic-settings` for `list[str]` fields read from env vars. It tries to JSON-decode them before validators run, causing `JSONDecodeError` on comma-separated values.
- Use plain `os.getenv` + manual split:
  ```python
  self.symbols = [s.strip() for s in os.getenv("BINANCE_SYMBOLS", "BTCUSDT").split(",") if s.strip()]
  ```

### Package Management

- Project uses `uv`. Add deps with `uv add <package>`, run scripts with `uv run python <script>`.

### Indicators (pandas-ta-classic)

- Import as `pandas_ta_classic` (not `pandas_ta`) — the package installs under a different module name.
- `ta.supertrend()` returns 4 columns: `SUPERT`, `SUPERTd`, `SUPERTl`, `SUPERTs`. The `l`/`s` columns have alternating NaN (one is null depending on direction). Always select only `SUPERT` + `SUPERTd` before calling `dropna()`, otherwise all rows are dropped.
- Direction: `SUPERTd == 1` → BULLISH, `SUPERTd == -1` → BEARISH.

### Spec-Driven Workflow

- Specs live in `.specs/project/` (PROJECT.md, ROADMAP.md) and `.specs/features/<name>/` (spec.md, design.md, tasks.md).
- Order: specify → design → tasks → implement. Get approval at each phase before proceeding.