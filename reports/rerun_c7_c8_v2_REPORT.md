# C7 / C8 re-run (v2) — full validation gauntlet, real numbers

Run: 2026-11-04 03:38:36 → 04:16 (2 276.3 s wall clock for 24 specs).
Command: `paperrun.run_matrix(specs, quick=False, only=['c7_','c8_'])` →
`reports/paper_concept_results.json` (merged by name), log `reports/_rerun_c7_c8_v2.log`.

Scope: 12 real specs (C7, C8 × 6 asset classes) + 12 inverted negative controls.
**0 ERROR verdicts, 0 rows with a populated `errors` array.** Every spec ran.

---

## 1. THE TWELVE REAL SPECS

Pooled OOS Sharpe is `metrics.oos_sharpe`; in-sample is `metrics.in_sample_sharpe`.
They are now **different numbers on every row** (the `oos_sharpe == in_sample_sharpe`
defect is gone for these 24 rows).

| spec | verdict | OOS Sharpe | in-sample Sharpe | n_trades | max DD | total return |
|---|---|---|---|---|---|---|
| c7_session_drift_us_equity_style | REFUTED | **0.1349** | 0.1572 | 8 | 0.0841 | 0.0713 |
| c7_session_drift_crypto | REFUTED | **-0.6289** | 0.3130 | 10 | 0.3112 | 0.3694 |
| c7_session_drift_fx_major | INCONCLUSIVE | **None** | None | 0 | 0.0 | 0.0 |
| c7_session_drift_commodities | REFUTED | **-0.3723** | -0.3118 | 13 | 0.6813 | -0.5407 |
| c7_session_drift_futures_broad | REFUTED | **-0.0645** | -0.1192 | 15 | 0.5986 | -0.3372 |
| c7_session_drift_rates_credit | REFUTED | **-0.2067** | 0.0369 | 12 | 0.5103 | -0.0148 |
| c8_liquidity_reversal_us_equity_style | INCONCLUSIVE | **None** | None | 0 | 0.0 | 0.0 |
| c8_liquidity_reversal_crypto | FRAGILE | **0.6500** | -0.1936 | 30 | 0.0311 | -0.0137 |
| c8_liquidity_reversal_fx_major | INCONCLUSIVE | **None** | None | 0 | 0.0 | 0.0 |
| c8_liquidity_reversal_commodities | REFUTED | **0.1612** | 0.0474 | 171 | 0.0953 | 0.0136 |
| c8_liquidity_reversal_futures_broad | REFUTED | **0.0013** | -0.0888 | 110 | 0.0450 | -0.0154 |
| c8_liquidity_reversal_rates_credit | INCONCLUSIVE | **None** | None | 0 | 0.0 | 0.0 |

### Flags, verbatim

- **c7_us_equity_style** — "only 8 trades (need >=30)"; "t-stat 0.73 below 2.0 - the return series is not distinguishable from noise"
- **c7_crypto** — "only 10 trades (need >=30)"; "t-stat 0.91 below 2.0 - the return series is not distinguishable from noise"; "0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few"; "OOS Sharpe retains only -71% of the in-sample Sharpe (need 40%) - the edge degrades out of sample"
- **c7_fx_major** — "only 0 trades (need >=30)"; "0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few"; "edge does not survive 2x cost stress"; "only 0/22 profitable years"
- **c7_commodities** — "only 13 trades (need >=30)"; "t-stat -1.46 below 2.0 - the return series is not distinguishable from noise"; "0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few"; "edge does not survive 2x cost stress"; "only 8/22 profitable years"
- **c7_futures_broad** — "only 15 trades (need >=30)"; "t-stat -0.56 below 2.0 - the return series is not distinguishable from noise"; "only 2/5 walk-forward folds profitable (edge concentrated in a few periods)"; "edge does not survive 2x cost stress"; "only 9/22 profitable years"
- **c7_rates_credit** — "only 12 trades (need >=30)"; "t-stat 0.17 below 2.0 - the return series is not distinguishable from noise"; "only 2/5 walk-forward folds profitable (edge concentrated in a few periods)"; "OOS Sharpe retains only -21% of the in-sample Sharpe (need 40%) - the edge degrades out of sample"
- **c8_us_equity_style** — "only 0 trades (need >=30)"; "0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few"; "edge does not survive 2x cost stress"; "parameter stability 0% (< 60%)"; "only 0/22 profitable years"
- **c8_crypto** — "t-stat -0.56 below 2.0 - the return series is not distinguishable from noise"; "only 1/5 walk-forward folds profitable (edge concentrated in a few periods)"; "edge does not survive 2x cost stress"; "Monte Carlo prob(profitable) 37%"; "only 1/6 profitable years"
- **c8_fx_major** — same five as c8_us_equity_style
- **c8_commodities** — "t-stat 0.22 below 2.0 - the return series is not distinguishable from noise"; "Monte Carlo prob(profitable) 59%"; "only 8/22 profitable years"
- **c8_futures_broad** — "t-stat -0.41 below 2.0 - the return series is not distinguishable from noise"; "only 2/5 walk-forward folds profitable (edge concentrated in a few periods)"; "edge does not survive 2x cost stress"; "Monte Carlo prob(profitable) 33%"; "only 3/22 profitable years"
- **c8_rates_credit** — same five as c8_us_equity_style

### Per-fold OOS Sharpe table (5 purged/embargoed folds)

| spec | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 | profitable |
|---|---|---|---|---|---|---|
| c7_us_equity_style | -0.1580 | 0.4769 | -0.3541 | 0.5936 | 0.0433 | 3/5 |
| c7_crypto | -0.3097 | -0.3804 | -1.2284 | -0.9554 | -0.2507 | 0/5 |
| c7_fx_major | None | None | None | None | None | 0/5 |
| c7_commodities | -0.8282 | -0.2111 | -0.7534 | -0.2307 | -0.2305 | 0/5 |
| c7_futures_broad | 0.4011 | -0.9456 | -0.0871 | 0.0521 | -0.0841 | 2/5 |
| c7_rates_credit | -0.5277 | 0.2226 | -0.6594 | -0.4487 | 0.5519 | 2/5 |
| c8_us_equity_style | None | None | None | None | None | 0/5 |
| c8_crypto | None | None | None | 1.4562 | None | 1/5 |
| c8_fx_major | None | None | None | None | None | 0/5 |
| c8_commodities | 0.5313 | 0.1346 | -0.0902 | -0.0481 | 0.1453 | 3/5 |
| c8_futures_broad | 0.5092 | -0.3388 | -0.1954 | 0.1280 | None | 2/5 |
| c8_rates_credit | None | None | None | None | None | 0/5 |

A `None` fold = zero OOS trades in that window (the signal never fired).
**c8_crypto's pooled OOS +0.650 is ONE fold (fold 3, 1.4562)**; the other four
folds have no trades at all, and its in-sample Sharpe is negative (-0.194).

### Stage ledger (identical shape on all 24 rows)

`gross_vs_net` RAN · `cost_stress` RAN (4 multipliers 1.0/1.5/2.0/3.0) ·
`parameter_sensitivity` RAN · `monte_carlo` RAN-or-ERRORED ·
`subperiod` RAN · `capacity` RAN · `causality` RAN (`causal: true`, no violations) ·
`skipped_stages: []`.

- **Monte Carlo ERRORED on 18 of 24 rows** — "only N trades — Monte Carlo needs >=20"
  (N = 0, 8, 10, 12, 13, 15). It ran (3 000 runs) on the 6 rows with ≥20 trades
  (c8 crypto/commodities/futures_broad and their three controls): prob(profitable)
  37 %, 59 %, 33 % (real) and 44 %, 31 %, 61 % (controls).
- **Parameter sensitivity**: on every C7 row, `stability: null`, 0 perturbations —
  the engine reports "no perturbable parameter found - the sweep tested nothing and
  is NOT evidence of robustness". On the C8 rows it ran 8 perturbations
  (stability 0.0 / 0.625 / 0.875 / 1.0).
- **Cross-market replication DID NOT RUN AND IS NOT RECORDED AS SKIPPED.**
  No row has a `replication` entry in its ledger; `skipped_stages` is `[]` on all 24
  rows; no captured scorecard has a `replication` key. This is structurally
  unreachable through `run_matrix` (it passes no `alt_universes`), and the ledger
  cannot tell "ran and passed" from "never ran".
  (leapspace/backtest.py:1990-2006 builds the ledger from
  `scorecard["replication"]`, which btvalidate.py:1448-1455 only sets
  `if alt_universes`; `skipped_stages` comes from `_skipped_stage_labels(skip)`,
  which is `[]` for a full run.)

---

## 2. THE TWELVE NEGATIVE CONTROLS — do they differ from their twins?

`invert_signal=True` is in the control's `signal.params` for all 12.

| control | verdict | control OOS | twin OOS | control in-sample | n trades | identical? |
|---|---|---|---|---|---|---|
| NEG-CONTROL-c7_us_equity_style | REFUTED | **-0.4895** | 0.1349 | -0.5125 | 8 | differs |
| NEG-CONTROL-c7_crypto | REFUTED | **0.1539** | -0.6289 | -0.6468 | 10 | differs |
| NEG-CONTROL-c7_fx_major | INCONCLUSIVE | None | None | None | 0 | **identical (both 0 trades)** |
| NEG-CONTROL-c7_commodities | REFUTED | **0.3637** | -0.3723 | 0.2889 | 13 | differs |
| NEG-CONTROL-c7_futures_broad | REFUTED | **0.0346** | -0.0645 | 0.0727 | 15 | differs |
| NEG-CONTROL-c7_rates_credit | REFUTED | **0.3206** | -0.2067 | -0.1133 | 12 | differs |
| NEG-CONTROL-c8_us_equity_style | INCONCLUSIVE | None | None | None | 0 | **identical (both 0 trades)** |
| NEG-CONTROL-c8_crypto | REFUTED | **-0.6541** | 0.6500 | -0.0162 | 30 | differs |
| NEG-CONTROL-c8_fx_major | INCONCLUSIVE | None | None | None | 0 | **identical (both 0 trades)** |
| NEG-CONTROL-c8_commodities | REFUTED | **-0.1876** | 0.1612 | -0.0804 | 171 | differs |
| NEG-CONTROL-c8_futures_broad | REFUTED | **-0.0367** | 0.0013 | 0.0620 | 110 | differs |
| NEG-CONTROL-c8_rates_credit | INCONCLUSIVE | None | None | None | 0 | **identical (both 0 trades)** |

**The no-op controls are FIXED: 8 of 12 now produce different numbers from their
twins** (the four previously-byte-identical signal families C1/C2/C7 plus C8 now
respond to the inversion flag).

**The 4 identical pairs are vacuous, not no-ops.** In every one of them the TWIN
also produced zero trades, so there was nothing for the control to invert:
C7 fx_major (the feature is missing entirely on FX) and C8 us_equity_style /
fx_major / rates_credit (the gate never opens — see §4). The control machinery is
working; on those four market rows the matrix simply has **no evidence either way**.

Verdict mix over the 24 rows: **15 REFUTED, 8 INCONCLUSIVE, 1 FRAGILE, 0 SUPPORTED.**
No negative control came out SUPPORTED, so on the 8 rows where a control could
actually discriminate, the validation does discriminate.

---

## 3. CROSS-ASSET-CLASS CONSISTENCY

### C7 (pooled OOS Sharpe)

| asset class | OOS | in-sample | n trades | OOS trades | total return | verdict |
|---|---|---|---|---|---|---|
| us_equity_style | 0.1349 | 0.1572 | 8 | 49 | 0.0713 | REFUTED |
| crypto | -0.6289 | 0.3130 | 10 | 50 | 0.3694 | REFUTED |
| fx_major | None | None | 0 | 0 | 0.0 | INCONCLUSIVE (untestable) |
| commodities | -0.3723 | -0.3118 | 13 | 65 | -0.5407 | REFUTED |
| futures_broad | -0.0645 | -0.1192 | 15 | 73 | -0.3372 | REFUTED |
| rates_credit | -0.2067 | 0.0369 | 12 | 84 | -0.0148 | REFUTED |

**C7 works on ONE market (US equity style, +0.135), and even there it is REFUTED
(8 trades, t-stat 0.73).** It is negative on the other four testable markets and
untestable on FX. On commodities the INVERTED control scored +0.364 — better than
the hypothesis — so the sign of the drift effect there is the opposite of the claim.
A single-market, REFUTED, 8-trade result is a market curiosity, not an edge.

### C8 (pooled OOS Sharpe)

| asset class | OOS | in-sample | n trades | OOS trades | total return | verdict |
|---|---|---|---|---|---|---|
| us_equity_style | None | None | 0 | 0 | 0.0 | INCONCLUSIVE (gate never opens) |
| crypto | 0.6500 | -0.1936 | 30 | 10 | -0.0137 | FRAGILE |
| fx_major | None | None | 0 | 0 | 0.0 | INCONCLUSIVE (no volume series) |
| commodities | 0.1612 | 0.0474 | 171 | 160 | 0.0136 | REFUTED |
| futures_broad | 0.0013 | -0.0888 | 110 | 96 | -0.0154 | REFUTED |
| rates_credit | None | None | 0 | 0 | 0.0 | INCONCLUSIVE (gate never opens) |

**C8 has a positive OOS Sharpe on 3 of 6 asset classes** (crypto +0.650, commodities
+0.161, futures_broad +0.001), and 3 of 6 are untestable. Of the three testable
markets: crypto is FRAGILE and its +0.650 comes from ONE fold; commodities is
REFUTED; futures_broad is REFUTED at +0.001. **C8 does not work on several markets —
it works on at most one and even that one is a single-fold, Monte-Carlo-37 % result.**

---

## 4. THE ZERO-TRADE ROWS — cause measured, not guessed

C8's gate (`sig_liquidity_gated_reversion`) enters only when **all three** hold:
`z <= -2.0` AND `volume_ratio <= 0.8` AND `volatility >= 0.30`, and it emits
nothing whenever any of the three features is None.
`min_volatility = 0.30` is a **30 % ANNUALISED** requirement (the engine's
`volatility` feature with `annualize=True` is the daily stdev × √252).

Measured annualised volatility per asset class (`reports/_rerun_c7_c8_v2_c8_volatility_probe.json`):

| asset class | median ann. vol | max | % of bars ≥ 0.30 | volume_ratio available |
|---|---|---|---|---|
| us_equity_style | **0.1466** | 1.0993 | 8.44 % | 98.93 % |
| crypto | 0.6048 | 12.91 | 93.53 % | 97.23 % |
| fx_major | **0.0847** | 0.8829 | 0.92 % | **0.00 %** |
| commodities | 0.2622 | 12.03 | 38.06 % | 98.93 % |
| futures_broad | 0.1611 | 12.03 | 19.40 % | 95.18 % |
| rates_credit | **0.0786** | 44.49 | 16.87 % | 64.22 % |

Joint-gate and order-generation counts (`_rerun_c7_c8_v2_mechanism_probe.json`):

| asset class | bars satisfying all three | of those, on a monthly rebalance bar | result |
|---|---|---|---|
| us_equity_style | 6 | **0** | 0 trades |
| crypto | 196 | 5 | 30 trades |
| fx_major | 0 (volume_ratio missing on 100 % of bars) | 0 | 0 trades |
| commodities | 269 | 17 | 171 trades |
| futures_broad | 131 | 8 | 110 trades |
| rates_credit | 1 | **0** | 0 trades |

So the zero-trade rows have two distinct, measured causes:

1. **The 30 % annualised-volatility gate is the binding constraint on
   us_equity_style and rates_credit.** US equity style ETFs have a median annualised
   volatility of 14.7 % (only 8.4 % of bars reach 30 %); rates/credit 7.9 % (16.9 %
   of bars). In 21 years, 6 bars (us_equity_style) and 1 bar (rates_credit) satisfy
   all three conditions — and the engine only generates orders on a monthly
   rebalance bar (the first trading bar of each month), so those 6 and 1 qualifying
   bars produce **zero orders**. Low-volatility markets may legitimately never
   satisfy the gate; this is not a crash.
2. **FX has no consolidated volume series at all**, so `volume_ratio` is None on
   100 % of FX bars and the gate can never open. C8 is structurally UNTESTABLE on
   FX — the same class as C4 on FX — and must be reported as untestable, not
   refuted.

**C7 fx_major is also untestable, for the same reason**: leapspace's
`f_session_drift` = (close's position in the day's range) × (volume ratio), and
without volume the feature is None on **every one of the 8 FX symbols** (0 non-None
bars each), so the cross-sectional signal is identically zero.

---

## 5. C7 NEVER ENABLES THE INTRADAY PATH IT CLAIMS TO TEST — CONFIRMED

**Confirmed, not fixed (no file under `leapspace/` was modified).**

- The engine's intraday path is real: `btengine.py:1603`
  `session_mode = exec_spec.get("mode") == "session"`, and at `:1632-1646` it
  fetches 60-minute bars and collapses each session to one opening-window bar
  (`intraday.build_session_panel`, window="first").
- The C7 spec does **not** enable it. `leapspace/paperspecs.py:162-166`
  `EXECUTION_BLOCK = {"fill_at": "open", "cost_multiplier": 2.0,
  "max_participation": 0.10}` — **no `mode` key**; `_make` (`:213`, `:290`) copies
  that block verbatim and offers no way to override it; `_c7_session_drift`
  (`:601-641`) sets no execution override. Every C7 spec therefore carries
  `execution = {"fill_at": "open", "cost_multiplier": 2.0, "max_participation": 0.1}`
  (printed for all 12 rows in `reports/_preflight_c7_c8_v2.out`).
- The engine's guard (`btengine.py:1607`) only fires when
  `period.interval != "1d"`; C7's interval is "1d", so the misconfiguration is
  silent — the run completes and looks clean.
- What actually ran is the DAILY-BAR PROXY: `leapspace/backtest.py:1043`
  `f_session_drift` ("THE session drift, as a DAILY-BAR PROXY. LAGGING"),
  registered at `:1557`. Its own docstring says: "It is NOT the session
  OPENING-WINDOW drift the concept names. That requires intraday bars."
- The spec's `notes` disclose the proxy, but the `hypothesis` still claims to test
  "the session opening-window drift". A SUPPORTED verdict here would support the
  proxy, not the order-flow claim.
- Enabling the flag is not a one-line fix: `btengine.py:254` fetches intraday as
  `range=2y&interval=60m`, so a session panel can cover at most ~2 years, not the
  2005-2026 window the C7 spec asks for.

## 6. OTHER NEW FINDINGS (reported, not fixed)

1. **Renaming C7's signal to `paper_cross_sectional` silently disables the
   engine's cross-sectional conviction ranking.** The engine builds the
   strength series only `if sig_spec["type"] == "cross_sectional"` — an exact
   string test (`btengine.py:1690-1691`). C7's type is now `paper_cross_sectional`, so every candidate
   scores `abs(signal) == 1.0`, the tie breaks on symbol NAME, and `max_names=5`
   keeps the alphabetically first names instead of the most extreme ranks
   (the engine's own comment: "without this, `max_names` kept the alphabetically
   first names"). Measured impact (`_rerun_c7_c8_v2_strength_probe.json`): the
   selected book differs on **234 of 262** rebalance bars for commodities and
   **261 of 262** for futures_broad; 0 difference on us_equity_style, crypto and
   rates_credit (≤5 candidates there). It applies to the C7 spec AND its control
   equally, so the control/twin comparison stays valid, but the C7 commodities and
   futures_broad numbers are not what the engine's own `cross_sectional` signal
   would have produced.
2. **The results file's fold table loses the per-fold in-sample Sharpe, the
   per-fold trade counts and the per-fold date ranges.**
   `leapspace/backtest.py:2108-2126` builds the fold table from `wf.get("fold_info")`,
   but btvalidate names that list `folds` (btvalidate.py:775-790, `:829`), so the
   builder falls back to the flat `oos_sharpes` list. The per-fold OOS Sharpe is
   correct; `in_sample_sharpe`, `oos_trades`, `start` and `end` are `null` on every
   fold of every row. (The full per-fold data is in
   `reports/_rerun_c7_c8_v2_scorecards.json`.)
3. **The stage ledger cannot distinguish "cross-market replication ran" from
   "cross-market replication never ran"** — see §1.
4. **`parameter_sensitivity` reads as `ran` on every C7 row while the engine
   itself says the sweep tested nothing** (`stability: null`, 0 perturbations,
   "the sweep tested nothing and is NOT evidence of robustness"). The ledger's
   `note` field only picks up `note`/`reason`/`error`, and this stage's text is
   under `interpretation`.

## 7. STATE OF THE SHARED RESULTS FILE

96 rows before, 96 after, order preserved. **Exactly 24 rows changed — all C7/C8;
the other 72 are byte-identical to before.** The 24 new rows all carry a fold
table, a stage ledger, and a separate in-sample Sharpe.

**The other 72 rows still carry the invalid numbers**: 56 of them still report the
in-sample Sharpe under the key `oos_sharpe`, all 72 have `walk_forward: null` and
`stages: {}`. The file is now a mix of fixed and unfixed rows, so the matrix as a
whole is still not reportable until the other 72 are re-run the same way.
