# Signal Generator Tasks

**Design**: `.specs/features/signal-generator/design.md`
**Status**: Approved

---

## Execution Plan

### Phase 1: Foundation + Implementation (Parallel OK)

```
T1 [P]  Signal models
T2 [P]  evaluate_signal function

T1 + T2 complete, then:
  T3  __init__.py exports
```

---

## Task Breakdown

### T1: Create signal models [P]

**What**: Define `SignalDirection` enum and `Signal` frozen dataclass
**Where**: `src/signals/models.py`
**Depends on**: None

**Done when**:
- [ ] `SignalDirection(Enum)` with `BUY`, `SELL`, `NO_SIGNAL`
- [ ] `Signal(frozen dataclass)` with fields: `symbol`, `timeframe`, `direction`, `close`, `rsi`, `sma`, `supertrend_value`, `supertrend_direction`, `timestamp`

**Verify**:
```bash
uv run python -c "from src.signals.models import Signal, SignalDirection; print(SignalDirection.BUY)"
```

---

### T2: Implement evaluate_signal [P]

**What**: Pure function applying BUY/SELL/NO_SIGNAL conditions
**Where**: `src/signals/evaluator.py`
**Depends on**: None (can be written in parallel with T1)

**Done when**:
- [ ] `evaluate_signal(indicators: IndicatorResult, candle: Candle) -> Signal`
- [ ] BUY when: `rsi < 50` AND `close > sma` AND `supertrend == BULLISH`
- [ ] SELL when: `rsi > 50` AND `close < sma` AND `supertrend == BEARISH`
- [ ] NO_SIGNAL for all other combinations including exact boundary (rsi==50, close==sma)

**Verify**:
```bash
uv run python -c "from src.signals.evaluator import evaluate_signal; print('OK')"
```

---

### T3: Create __init__.py exports

**What**: Export public API from `src/signals/__init__.py`
**Where**: `src/signals/__init__.py`
**Depends on**: T1, T2

**Done when**:
- [ ] Exports: `evaluate_signal`, `Signal`, `SignalDirection`

**Verify**:
```bash
uv run python -c "from src.signals import evaluate_signal, Signal, SignalDirection; print('OK')"
```

---

## Parallel Execution Map

```
Phase 1 (Parallel):
  T1 [P]
  T2 [P]  (independent — no shared deps)

Phase 2 (Sequential):
  T1 + T2 complete, then:
    T3
```
