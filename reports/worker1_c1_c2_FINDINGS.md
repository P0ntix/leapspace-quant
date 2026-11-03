# Worker 1 — C1 + C2 paper-concept full-gauntlet run

**Date:** 2026-11-03/04
**Repo:** C:/Users/HP/AppData/Local/hermes/projects/leapspace-quant
**Engine:** strategy-backtest-lab (`btengine.py` / `btvalidate.py`), FULL gauntlet
(`quick=False`) — walk-forward with purge+embargo, gross-vs-net, cost stress,
parameter sweep, Monte Carlo, subperiod/regime, capacity, replication,
causality audit, deflated Sharpe.

**Scope note:** `only=['c1_','c2_']` selects **24** specs, not 16 — 2 concepts
x 6 asset classes x (real + negative control). 24 = the full C1+C2 matrix.

## Artefacts

| File | What |
|---|---|
| `reports/paper_concept_results.json` | merged results file (shared; my 24 rows merged in, another worker's 48 rows untouched) |
| `reports/worker1_c1_c2.log` | raw run log (task-required) |
| `reports/worker1_c1_c2_detail.json` | raw scorecards: per-fold tables, per-stage ran/skipped/errored, real leading coverage |
| `reports/worker1_c1_c2_report.txt` | rendered report (per-spec, all numbers) |
| `reports/worker1_c1_c2_FINDINGS.md` | this file |
| `reports/worker1_diagnostic_patched_*.json/.log` | diagnostic run (C2 crash fixed, control knobs honoured) |
| `reports/run_matrix_worker1.py` | the runner (STEP 2 deliverable) |
| `reports/run_matrix_worker1_diagnostic.py` | diagnostic runner |
| `reports/_render_worker1_report.py` | report generator |
| `reports/_probe_*.py` | bug-verification probes |
| `reports/_prefetch_c1_c2.py` | OHLCV prefetch (30 symbols) |

## HEADLINE

**No spec is SUPPORTED. No negative control is SUPPORTED.**

C1: REFUTED on 4 of 6 asset classes, INCONCLUSIVE on 2.
C2: **could not be evaluated at all as shipped** — all 12 C2 rows (6 real +
6 controls) ERROR with `TypeError: object of type 'float' has no len()`.

## The results, as shipped

| spec | verdict | IS Sharpe | pooled OOS Sharpe | n_trades | maxDD | total ret |
|---|---|---|---|---|---|---|
| c1_regime_switch_us_equity_style | REFUTED | 0.268 | **0.090** | 36 | 0.085 | 0.1611 |
| c1_regime_switch_crypto | INCONCLUSIVE | -0.133 | **None** (all folds flat) | 20 | 0.367 | -0.1462 |
| c1_regime_switch_fx_major | INCONCLUSIVE | None | **None** (all folds flat) | 0 | 0.000 | 0.0000 |
| c1_regime_switch_commodities | REFUTED | -0.093 | **-0.138** | 84 | 0.388 | -0.2244 |
| c1_regime_switch_futures_broad | REFUTED | -0.190 | **0.132** | 92 | 0.473 | -0.3231 |
| c1_regime_switch_rates_credit | REFUTED | -0.469 | **-0.439** | 52 | 0.242 | -0.2001 |
| c2_leading_vrp_* (all 6) | INCONCLUSIVE (ERROR) | None | None | None | None | None |
| NEGATIVE-CONTROL-c1_* (all 6) | identical to twin | - | - | - | - | - |
| NEGATIVE-CONTROL-c2_* (all 6) | INCONCLUSIVE (ERROR) | None | None | None | None | None |

### Per-fold walk-forward tables

**c1_regime_switch_us_equity_style** (858-bar test blocks, purge 60 / embargo 60)

| fold | OOS Sharpe | IS Sharpe | test range | OOS trades |
|---|---|---|---|---|
| 0 | **0.597** | 1.151 | 2005-12-15..2009-05-14 | 12 |
| 1 | **-0.498** | 2.015 | 2010-04-30..2013-09-25 | 6 |
| 2 | **0.092** | 1.508 | 2014-09-10..2018-02-05 | 17 |
| 3 | **-0.077** | 1.081 | 2019-01-22..2022-06-15 | 12 |
| 4 | **0.371** | 0.341 | 2023-06-01..2026-10-30 | 6 |

pooled OOS **0.090**; 2/5 folds profitable; OOS retention 26% (bar: 40%).
Flags: `t-stat 1.25 below 2.0 - the return series is not distinguishable from noise`,
`OOS Sharpe retains only 26% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`.
Gross-vs-net: gross 0.397 vs net 0.268.

**c1_regime_switch_crypto** (186-bar blocks) — every fold OOS Sharpe `None`,
0 OOS trades (see B5). IS per fold: +0.661, +0.314, +0.299, -0.378, -0.229.

**c1_regime_switch_fx_major** (896-bar blocks) — every fold OOS Sharpe `None`,
0 OOS trades, 0 trades total (see B6). IS per fold: `None` on all 5.

**c1_regime_switch_commodities** — OOS Sharpe -0.138 pooled, 52 OOS trades.
**c1_regime_switch_futures_broad** — OOS Sharpe +0.132 pooled, 92 trades.
**c1_regime_switch_rates_credit** — OOS Sharpe -0.439 pooled, 52 trades.

Full tables and every flag: `reports/worker1_c1_c2_report.txt`.

### Which robustness stages RAN / SKIPPED / ERRORED

| stage | C1 (6 specs) | C2 (12 specs) |
|---|---|---|
| walk_forward | ran | **NOT RUN** (crashed first) |
| gross_vs_net | ran | **NOT RUN** |
| cost_stress | ran | **NOT RUN** |
| parameter_sensitivity | ran | **NOT RUN** |
| monte_carlo | ran (fx_major **ERRORED**: "only 0 trades - Monte Carlo needs >=20") | **NOT RUN** |
| subperiod | ran | **NOT RUN** |
| capacity | ran | **NOT RUN** |
| causality | ran (all causal) | **NOT RUN** |
| deflated_sharpe | ran | **NOT RUN** |
| replication | **NOT RUN** - no `alt_universes` is plumbed through `paperrun`/`run_spec`, so `btvalidate.full_gauntlet`'s `if alt_universes:` guard (btvalidate.py:1449) never fires | **NOT RUN** |

`skipped_stages` from the engine was `[]` for every C1 spec - the replication
stage is not "skipped", it is simply never reachable through this runner.
The C2 rows have NO stage at all: the crash happens before the scorecard
exists.

## STEP 4 - the negative controls

**As shipped, the C1 negative controls are IDENTICAL to their twins.** Not
"came out SUPPORTED" - they came out *the same*, because they ARE the same
strategy. Verified: all 6 C1 control rows match their twin on verdict, flags,
errors, in-sample Sharpe, pooled OOS Sharpe, n_trades, max drawdown, total
return AND the per-fold table. The C1 controls "pass" only vacuously.

The C2 controls crash with the same TypeError, so they discriminate nothing.

**Diagnostic run (control knob honoured at runtime):**

| C1 control (inverted) | verdict | IS Sharpe | pooled OOS Sharpe |
|---|---|---|---|
| us_equity_style | REFUTED | -0.521 | -0.313 |
| crypto | INCONCLUSIVE | -0.300 | None |
| fx_major | INCONCLUSIVE | None | None |
| commodities | REFUTED | 0.019 | 0.068 |
| futures_broad | REFUTED | 0.134 | -0.194 |
| **rates_credit** | **FRAGILE** | -0.065 | **+0.560** |

**NO negative control is SUPPORTED** - the validation is not vacuously passing
anything. But note `NEGATIVE-CONTROL-c1_regime_switch_rates_credit` came out
**FRAGILE with pooled OOS Sharpe +0.560**, *better* than its real twin's
-0.439. On rates/credit, inverting the C1 signal IMPROVES out-of-sample
performance by a wide margin. That is not a "control passed" failure - it is
evidence that the C1 concept's polarity may be backwards on that asset class,
and it is reported as such.

All 6 C2 controls (with `invert_vrp` honoured) are REFUTED.

## STEP 5 - C1 vs C2 on the same asset classes

**The claim is NOT supported. The numbers do not even permit the comparison
as shipped.**

As shipped, C2 has no numbers at all: every C2 row is a crash. The only way
to compare is the diagnostic run (C2 crash fixed), where C2's real specs are:

| asset class | C1 OOS (as shipped) | C2 OOS (diagnostic, crash fixed) | C2 verdict |
|---|---|---|---|
| us_equity_style | **0.090** | **-0.156** | REFUTED |
| crypto | **None** (folds flat) | **-0.277** | REFUTED |
| fx_major | **None** (0 trades) | **-0.047** | REFUTED |
| commodities | **-0.138** | **-0.075** | REFUTED |
| futures_broad | **0.132** | **+0.023** | REFUTED |
| rates_credit | **-0.439** | **+0.313** | REFUTED |

C2 trades 6-32 times (below the 30-trade bar in 5 of 6 asset classes) and is
**negative in 4 of 6**. Where both are measurable, C2 beats C1 on 2 of 4
(commodities, rates_credit) and loses on 2 (us_equity_style, futures_broad).
The two are not distinguishable, and **a forward-looking input did NOT beat
a backward-looking one.**

**Two caveats that matter as much as the numbers:**

1. **C2's feature is look-ahead.** `f_leading_vrp_zscore` normalises with the
   whole-panel mean/sd (B4). The engine's own causality audit says
   `causal: False` with 10 violations (all `leading_vrp_zscore`, all at bar
   83) and the crypto C2 row carries the flag
   `LOOK-AHEAD DETECTED - feature uses future data`. **A leading indicator
   normalised on the full sample is not leading.** C2's OOS numbers are not
   a trustworthy out-of-sample result at all.
2. **C2 has ~23% leading coverage on 5 of 6 asset classes** (below).

C2's REFUTED verdict is therefore, if anything, generous: the concept does
not work, and its headline feature is also not causal.

## The leading-coverage limitation (CRITICAL, as requested)

Computed by aligning the real series to the panel's bar grid with the
engine's own `align_to_bars(..., max_lag_bars=1)` - the same call the engine
makes inside `f_leading_vrp_score`:

| C2 spec | panel bars | bars WITH a leading value | fraction | source | series span |
|---|---|---|---|---|---|
| us_equity_style | 5492 | 1250 | **22.8%** | yahoo.chart **^VXN** | 2021-11-03..2026-11-03 |
| crypto | 2132 | 2049 | **96.1%** | deribit.dvol **BTC** | 2021-03-24..2026-11-03 |
| fx_major | 5680 | 1298 | **22.9%** | yahoo.chart **^VIX** | 2021-11-03..2026-11-03 |
| commodities | 5492 | 1255 | **22.9%** | yahoo.chart **^VIX** | 2021-11-03..2026-11-03 |
| futures_broad | 5497 | 1256 | **22.8%** | yahoo.chart **^VIX** | 2021-11-03..2026-11-03 |
| rates_credit | 5491 | 1253 | **22.8%** | yahoo.chart **^VIX** | 2021-11-03..2026-11-03 |

Feature-level coverage (`leading_vrp_score` and `leading_vrp_zscore`)
matches the bar-level numbers exactly (per-symbol non-null counts are
identical across every symbol in a panel).

**Stated plainly:** the equity/FX/commodities/futures/rates panels start in
2005, but Yahoo's implied-volatility series is fetched with `range=5y`, so
it only reaches back to 2021-11-03. **~77% of each of those five panels
has NO leading input at all** - the strategy is flat there for reasons that
have nothing to do with the concept. Only crypto (Deribit DVOL, daily, from
2021-03-24, matching the crypto panel's 2021-01-01 start) has near-full
coverage, and crypto is the one asset class where C2 has a genuinely
measurable OOS Sharpe (-0.277).

## SIX BUGS (reported, not fixed - no leapspace/*.py file was edited)

**B1 - `leapspace/backtest.py:1146` - C2 CRASHES EVERY C2 SPEC.**
`sig_leading_vrp_switch` assigns `z = zvals.get(s) or []` (a LIST) at line
1129; line 1146 then does `z = -float(zz) if invert_vrp else float(zz)`,
rebinding `z` to a FLOAT. The next bar's `z[i] if i < len(z)` (line 1132)
raises `TypeError: object of type 'float' has no len()`. The scalar needs
its own variable name. Reproduced in isolation.

**B2 - `leapspace/backtest.py:676-810` - THE C1 NEGATIVE CONTROL IS A NO-OP.**
`sig_regime_switch` accepts `**kw` but never reads `invert_signal`, which is
exactly what `build_negative_controls` sets (`leapspace/paperspecs.py:747`).
Verified: output identical with and without the flag, and all 6 C1 control
rows match their twin on every metric and on the per-fold table.

**B3 - `leapspace/backtest.py:1089-1153` - THE C2 NEGATIVE CONTROL IS A NO-OP.**
`sig_leading_vrp_switch` reads `invert_vrp`, never `invert_signal`. Its own
docstring (line 1142) says `invert_vrp` "exists ONLY for the NEGATIVE
CONTROL", but `build_negative_controls` never sets it.

**B4 - `leapspace/backtest.py:1069-1087` - C2's FEATURE IS LOOK-AHEAD.**
`f_leading_vrp_zscore` normalises with the whole-panel mean and sd
(`m = sum(vals) / len(vals)` over every non-None value), so every bar's value
depends on the sample's future. The engine's causality audit confirms it:
`causal: False`, 10 violations, all `leading_vrp_zscore`, all at bar 83.

**B5 - `leapspace/backtest.py:676-810` - C1's FOLDS ARE FLAT, SO ITS OOS IS
UNMEASURABLE ON SHORT PANELS.** The regime HMM is refitted on whatever panel
the signal is handed. Base run: 2072 usable rows, fits. A walk-forward fold
gets a SLICED panel (186 bars for crypto -> 126 usable rows) and
`identify_regimes` needs `max(min_bars=120, n_states*40=160)` ->
returns None -> the signal stands aside on EVERY bar -> 0 OOS trades and
OOS Sharpe `None`. Hits c1_crypto and c1_fx_major.

**B6 - `leapspace/regime.py:125-133` - fx_major PRODUCES ZERO TRADES.**
`liquidity` = log(rolling mean of close*volume). FX pairs have no
consolidated volume (`panel.vol` is all 0.0) -> liquidity is None on every
bar -> 0 of 5680 market-level HMM rows usable -> `identify_regimes` returns
None -> the whole C1 strategy is flat on FX.

**B7 - `leapspace/paperrun.py:250-289` - THE MERGED ROW MISREPORTS THE
RESULT.** `_row_from_result` reads the OOS Sharpe, the fold table and the
stage status out of `res.metrics`, but `run_spec` puts the BASE metrics in
`res.metrics` and the walk-forward in `res.walk_forward`. Consequences in
`reports/paper_concept_results.json`:
  * `metrics.oos_sharpe` actually holds the **IN-SAMPLE** Sharpe (0.268 for
    c1_us_equity_style, whose real pooled OOS is 0.090) - a 3x overstatement;
  * `walk_forward` is `null` - the fold table is lost;
  * `stages` is `{}` - the ran/skipped/errored status is lost;
  * `leading_coverage_for` (paperrun.py:136-171) never populates
    `n_bars`/`n_leading`/`fraction`; it reports only the raw series length
    as `n_points`.

**The merged results file cannot be used to report these results.** The
numbers in this document come from the raw scorecard captured at
`btvalidate.full_gauntlet` (`reports/worker1_c1_c2_detail.json`).

## Data notes

- 30 symbols prefetched into the engine cache before the run.
- `LBS=F` 404s at Yahoo (the symbol does not exist there) - the commodities
  universe loses one name.
- Disk before: 2.0 GB free. After: 1.9 GB free. Nothing was deleted.
