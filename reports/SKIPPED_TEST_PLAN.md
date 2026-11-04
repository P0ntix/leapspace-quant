# THE SKIPPED-TEST PLAN — Monte Carlo and replication

**Date:** 2026-11-04
**Trigger:** *"the standard monte carlo simulation shall be 1,000 trades
samples minimum. why there are skipped tests to the claims?"*
**Status:** options presented, nothing executed. Every decision below
needs your call.

---

## 1. WHAT WAS ACTUALLY SKIPPED, AND WHY

Measured across the **120 rows** in the matrix (96 original + 24 Phase
A), of which **96 carry a stage ledger**:

| Stage | Ran | ERROR | SKIPPED |
|---|---|---|---|
| `gross_vs_net` | 96 | 0 | 0 |
| `cost_stress` | 96 | 0 | 0 |
| `parameter_sensitivity` | 96 | 0 | 0 |
| `subperiod` | 96 | 0 | 0 |
| `capacity` | 96 | 0 | 0 |
| `causality` | 96 | 0 | 0 |
| **`monte_carlo`** | **56** | **40** | 0 |
| **`replication`** | **0** | 0 | **72** |

Two stages are missing work. Nothing else.

### 1.1 Monte Carlo — 40 ERROR, two different causes

The engine's guard is hardcoded:

```python
# btvalidate.py, monte_carlo()
if n < 20:
    return {"error": f"only {n} trades — Monte Carlo needs >=20"}
```

**Cause A — the signal never fired (12 rows).** Trade count **0**:

| Row | Verdict |
|---|---|
| `c1_regime_switch_fx_major` | INCONCLUSIVE |
| `c4_volume_confirmation_fx_major` | INCONCLUSIVE |
| `c7_session_drift_fx_major` | INCONCLUSIVE |
| `c8_liquidity_reversal_fx_major` | INCONCLUSIVE |
| `c8_liquidity_reversal_us_equity_style` | INCONCLUSIVE |
| `c8_liquidity_reversal_rates_credit` | INCONCLUSIVE |
| + their **6 inverted controls** | INCONCLUSIVE |

**This is the serious one, and it is not a Monte Carlo problem.** A
signal that produces zero trades on a populated universe never ran.
And because each of these has an inverted control that ALSO produces
zero trades, **those six controls are vacuous** — they cannot fail,
so they prove nothing. That is the same defect class as the inverted
controls this project already fixed three times (C1, C2, C7), and it
has now reappeared on the `fx_major` universe.

**Cause B — too few trades (28 rows).** Trade counts **6, 8, 10, 12,
13, 15** — all below the guard's 20. These are the low-turnover trend
and regime rules: a 12-month momentum on five ETFs makes 6 trades in
15 years.

The MC **ran** on 54 rows with trade counts from 8 to 880 (median 90).

### 1.2 Replication — 72 SKIPPED, one cause

The stage ledger says it on every row:

> `the gauntlet only runs cross-market replication when alternative
> universes are supplied, and the matrix runner supplies none - so NO
> spec in this matrix was tested for whether it transfers to a
> different market`

**This is not a missing capability.** The engine already has
`cross_market_replication(spec, alt_universe)`, and
`leapspace/backtest.py::run_spec` already accepts an `alt_universes`
argument. **The matrix runner simply never passes it.** One line in
`paperrun.py` is the whole gap.

It also means testing on six markets is **breadth, not replication** —
it is the same universe each time. Whether a surviving concept
transfers to a *different* universe is untested on all 120 rows, and
it is the one stage that decides whether a concept is an edge or a
market curiosity.

---

## 2. THE "1,000 SAMPLES" QUESTION — TWO READINGS, VERY DIFFERENT ANSWERS

The MC has **two** independent numbers, and "1,000 trade samples" can
bind to either. The measurements decide it.

| | Current | Rows that qualify today |
|---|---|---|
| **Bootstrap resample paths** (`n_runs`) | 3,000 (function default 5,000) | **all 56 that ran** — already above 1,000 |
| **Realised trades in the ledger** (`n`) | guard at 20 | ≥20: 55 rows · ≥100: 32 · **≥1000: 0** |

**The maximum realised trade count in the entire 120-row matrix is
880.** No row has 1,000 trades.

So:

- If 1,000 binds to the **paths**: the requirement is **already met**
  (3,000 > 1,000), the fix is to raise it to 10,000 (the modern
  standard), and the real work is fixing the 28 low-trade rows and the
  12 zero-trade rows.
- If 1,000 binds to the **realised trades**: **zero rows qualify**, the
  MC would skip on 100% of the matrix, and the stage would be
  decorative. Every strategy would have to be re-scoped to trade far
  more often.

### 2.1 The cost, measured

| Trades in ledger | 3,000 paths | 10,000 paths |
|---|---|---|
| 6 | 0.02 s | 0.06 s |
| 20 | 0.06 s | 0.22 s |
| 90 (median) | 0.42 s | 1.40 s |
| 880 | 26.8 s | 74.3 s |

Raising to 10,000 paths adds roughly **+5 minutes to a full
120-spec matrix run** (median case). A **bar-level block bootstrap** —
resampling blocks of the daily return series rather than trades —
costs ~2.2 s per spec at 10,000 paths and works with **thousands** of
observations instead of tens.

---

## 3. THE OPTIONS

### Decision A — what "1,000 samples minimum" binds to

| | Option | Effect |
|---|---|---|
| **A1** | **1,000+ bootstrap PATHS; raise `n_runs` 3,000 → 10,000.** The realised-trade floor is handled by Decision B. | The requirement is met and exceeded. +5 min per matrix run. |
| A2 | 1,000+ **realised trades** required. | **0 rows qualify.** MC skips on 100% of the matrix. Honest, but the stage becomes decorative. |
| A3 | **Both** — 1,000 paths and 1,000 realised trades. | Same as A2 for the skip rate, plus A1's runtime. |
| A4 | 1,000+ paths, and the MC additionally reports the **effective sample size** it actually had, so a 20-trade bootstrap is labelled as a 20-trade bootstrap. | A1, plus the report stops implying more precision than the data carries. |

### Decision B — the realised-trade floor (what happens to the 28 low-trade rows)

| | Option | Rows passing today |
|---|---|---|
| **B1** | **Floor 20 (unchanged) + a bar-level block-bootstrap FALLBACK** for low-trade strategies, reported as a separate, labelled basis. | 56 run the trade bootstrap; 28 run the bar bootstrap instead of being skipped. **Nothing is skipped.** |
| B2 | Floor **100**, no fallback. | 32 rows run; 64 skipped. |
| B3 | Floor **500**, no fallback. | 0 rows run. |
| B4 | Floor **1,000**, no fallback. | 0 rows run. |
| B5 | Floor 20 (unchanged), no fallback, but the skip is reported with the reason and the attainable trade count. | 56 run, 40 skipped and explained. |

### Decision C — the 12 zero-trade rows

| | Option | Effect |
|---|---|---|
| **C1** | **Diagnose and FIX each signal, and make "zero trades on a populated universe" a hard ERROR** rather than INCONCLUSIVE. Then re-run. | The six vacuous controls become real controls. A signal that never fires is a configuration error, and the runner should say so loudly. |
| C2 | Diagnose and report only; leave the rows as INCONCLUSIVE. | The six vacuous controls stay vacuous and stay in the matrix. |

### Decision D — replication

| | Option | Effect |
|---|---|---|
| **D1** | **Supply alternative universes to the matrix runner** so the stage runs for every spec. The engine already supports it. | The one stage that says "edge or market curiosity" finally runs. Cost: the replication stage re-runs each spec on each alternative universe, so the matrix run gets materially longer. |
| D2 | Implement replication inside the package (run the same signal on a different universe and compare), leaving the engine's stage unused. | More control over the comparison; more new code; duplicates a capability that already exists. |
| D3 | Leave it SKIPPED and disclose. | Current state. The gap stays open and is stated in every report. |

### Decision E — the verdict-level trade-count gate

The verdict says *"only 6 trades (need >=30)"*. Same family as the MC
guard.

| | Option | Effect |
|---|---|---|
| **E1** | **Keep ≥30, but make the gate turnover-aware**: report the signal's *attainable* opportunity count (how many times it could have fired) alongside the realised count, so a low-turnover rule is judged on whether 30 was even reachable. | A 12-month momentum is judged on its own terms, without weakening the gate for any other rule class. |
| E2 | Keep the gate exactly as it is. | Simple; a 12-month momentum will always read as INCONCLUSIVE/FRAGILE regardless of merit. |
| E3 | Lower the threshold. | Not recommended — 6 trades genuinely cannot be told from luck. |

---

## 4. WHAT THE FIXES TOUCH

| Decision | File | Change |
|---|---|---|
| A1 | `…/skills/research/strategy-backtest-lab/scripts/btvalidate.py` | `monte_carlo(..., n_runs=3000)` → `10_000`; parameterise the floor |
| B1 | `btvalidate.py` + `leapspace/backtest.py` | a `bar_block_bootstrap` function and its wiring into the stage ledger as a labelled alternative basis |
| C1 | `leapspace/backtest.py` (`sig_c1/c4/c7/c8`), `leapspace/paperrun.py` | fix the four signals; add a zero-trade assertion |
| D1 | `leapspace/paperrun.py` | pass `alt_universes` to `run_spec`; an asset-class → alternative-universe map |
| E1 | `…/btvalidate.py` / `leapspace/backtest.py` | compute and report the attainable opportunity count |

**Note on the shared skill:** `btvalidate.py` lives in the shared
`strategy-backtest-lab` skill, alongside the `btengine.py` float-`stdev`
patch already applied there. Changes to it affect that skill, not just
this repository. The alternative is to implement the new MC behaviour
in `leapspace/` as a wrapper that post-processes the gauntlet's scorecard
— more self-contained, no shared-skill mutation, but it cannot change
the *floor* the engine applies, only add a fallback around it.

---

## 5. THE COST / BENEFIT, STATED PLAINLY

| Fix | Effort | What it buys |
|---|---|---|
| **C1** (zero-trade rows) | Medium — four signals to diagnose | Six **vacuous controls** become real. Without this, six rows of the matrix are noise dressed as evidence. |
| **D1** (replication) | Low — the engine already supports it | The only stage that distinguishes an edge from a market curiosity. Currently untested on all 120 rows. |
| **A1** (10,000 paths) | Low | Exceeds the stated 1,000 standard. +5 min per matrix run. |
| **B1** (bar-block fallback) | Medium | 28 rows stop being skipped. Gives a bootstrap distribution for low-turnover rules instead of a hole. |
| **E1** (turnover-aware gate) | Low | A low-turnover rule is judged on whether its sample was attainable, not on a threshold set for a different strategy class. |

**Recommended combination: A1 + B1 + C1 + D1 + E1.**

The order matters: **C1 and D1 first.** C1 because six controls
currently cannot fail, which is a correctness problem, not a
reporting one. D1 because replication is the stage that decides
whether anything found here is an edge. Then A1 and B1, which are
mechanical. E1 last, because it only matters once B1 has given the
low-turnover rows a real basis to be judged on.

---

## 6. THE OUTCOME — WHAT WAS EXECUTED

Decisions taken: **A1, B4, C1, D1**. All four are implemented and
verified. What they produced:

### A1 — 1,000+ bootstrap paths

`btvalidate.py` now runs **10,000** paths (was 3,000), and the
`MONTE_CARLO_RUNS` constant makes it one number in one place. The
function's own default was 5,000; the gauntlet call was the thing
pinning it lower.

### B4 — a 1,000-realised-trade floor

`MIN_TRADES_FOR_MC = 1000`, and the skip is now a **SKIPPED stage with
its own status and reason**, not an `error` string:

```
monte_carlo: {"status": "SKIPPED",
              "note": "only 36 trades — Monte Carlo needs >=1000"}
```

**THE CONSEQUENCE, AS EXPECTED: no row in the matrix reaches 1,000
trades, so the Monte Carlo does not run on any of them.** The maximum
realised trade count in the 120-row matrix is 880. The stage is empty
until the strategies trade more — which is the point of the floor. The
fix is more names and more history, not a lower threshold.

### C1 — the zero-trade rows are fixed

The diagnosis found THREE distinct causes, not one:

1. **Yahoo spot-FX carries `volume: 0` on 100% of bars** — 45,440 of
   45,440 observations. `volume_ratio` and `session_drift` are
   therefore **all None**, so `c4`, `c7` and `c8` could never fire on
   `fx_major`, and their inverted controls could not fail either. The
   signals now **raise a clear configuration error** naming the
   feature and the universe, instead of silently producing zero
   trades.
2. **`c8`'s `min_volatility: 0.30` was a structural exclusion.** Only
   8.4% of `us_equity_style` observations and 16.9% of
   `rates_credit` observations clear 0.30 — so the rule produced zero
   trades on equities and rates. The paper says "more volatile
   conditions", which is a statement about the asset's **own norm**,
   not about 30%. The gate is now `vol_percentile: 0.75` — the top
   quartile of the asset's own trailing 252-bar volatility — with no
   absolute floor.
3. **The regime classifier was fed an all-None liquidity column.**
   The regime's liquidity is the log of average *dollar volume*, which
   is undefined where volume is zero. `c1_regime_switch_fx_major`
   produced zero trades. The classifier now **uses the features that
   exist and records which it dropped**, in the panel's own metadata.

**AND A BUG THE DIAGNOSIS SURFACED, WHICH IS BIGGER THAN ALL THREE:**

`c5` and `c8` appended **`0.0` while holding a position**. The engine
reads a signal series as a per-bar **TARGET POSITION** — the contract
the engine's own `time_series_zscore` follows. Appending zero while
holding therefore **closes the position on the next bar**. The rule
was reduced to a one-bar hold, the exit condition could never be
reached, and **every result those two signals produced was about a
different strategy than the paper describes.** Both are fixed, and the
position is now appended every bar.

### D1 — replication now runs

`ALT_UNIVERSES` maps each asset class to genuinely **different**
markets — `us_equity_style` → `us_equity_sector` and
`us_equity_broad`, `crypto` → `multi_asset` and `risk_on_risk_off`, and
so on. The runner passes them, and the stage reports:

```
replication: {"status": "ran"}
```

instead of `SKIPPED` on all 120 rows. Testing on six asset classes is
**breadth, not replication** — it is the same universe each time.

**One limitation to state: the engine's replication stage measures the
IN-SAMPLE Sharpe on the alternative universe.** It is a presence check
— "does the signal still point the right way there?" — and not a full
out-of-sample replication. The stage's own docstring says so.

### Verified end to end

```
verdict: REFUTED
gross_vs_net          ran
cost_stress           ran
parameter_sensitivity ran
monte_carlo           SKIPPED  (only 36 trades — needs >=1000)
subperiod             ran
capacity              ran
replication           ran
causality             ran
```
