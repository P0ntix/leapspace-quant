# C7 and C8 paper-concept backtest — REAL results

**Run:** `python reports/run_matrix_worker3.py`
**Runner:** `leapspace.paperrun.run_matrix(specs + controls, quick=False, only=['c7_','c8_'])`
**Scope:** 24 specs (2 concepts x 6 asset classes x {real, negative control})
**Started:** 2026-11-03 23:06:25 — **finished:** 2026-11-04 01:12 (2 h 06 m)
**Raw log:** `reports/worker3_c7_c8.log`
**Full scorecards:** `reports/worker3_c7_c8_detail.json`
**This worker's rows:** `reports/worker3_c7_c8_results.json`
**Merged into:** `reports/paper_concept_results.json` (all 96 rows present; the 24 C7/C8 rows are in it)

---

## HEADLINE

**No negative control came out SUPPORTED.** The safety check in STEP 4
passes: 9 controls INCONCLUSIVE, 3 controls REFUTED, 0 SUPPORTED. On the
specific question asked, the validation is not currently void.

That said, the pass is partly vacuous, and the reason matters:

* For **C7**, every real spec and every negative control errored out
  identically with the same `KeyError`. The control "failed" only because
  the real spec never ran. **C7 has produced no result at all.**
* For **C8**, the negative control is a real control (`invert_signal` IS
  honoured by `sig_liquidity_gated_reversion`) and it DOES discriminate on
  the three asset classes where C8 traded at all. On the three asset classes
  where C8 produced 0 trades, real and control are identical for the same
  reason.

**C8 verdict: REFUTED / INCONCLUSIVE on five of six asset classes,
FRAGILE on one.** The one FRAGILE (crypto) fails four of its own
robustness checks, rests on 30 trades, and has only 1 of 5 walk-forward
folds profitable.

**C7 verdict: INCONCLUSIVE on all six**, but not because the sample was
short — because the spec never enables the intraday path it is testing.

---

## STEP 3 — EVERY SPEC, EVERY FLAG, EVERY NUMBER

### C7 — `c7_session_drift_*` (order-flow / microstructure base)

All six real specs and all six negative controls:

**VERDICT: INCONCLUSIVE** (identical for real and control)

**ERROR (verbatim, identical on all 12):**
```
KeyError: "Unknown feature 'session_drift'. Available: ['atr_pct', 'bollinger_pct', 'dist_to_high', 'leading_iv_level', 'leading_vrp_score', 'leading_vrp_zscore', 'ma_crossover', 'max_drawdown', 'momentum', 'regime_momentum_score', 'return', 'rsi', 'skew', 'sma_gap', 'vol_ratio', 'volatility', 'volume_ratio', 'zscore']"
```

**FLAGS: (none)** — the spec never reached the engine's checks, so there
are no flags to report.

**Pooled OOS Sharpe:** None (no walk-forward was ever produced)
**In-sample Sharpe:** None
**n_trades / max drawdown / total return:** None / None / None
**Per-fold walk-forward table:** none — the run aborted before the
walk-forward stage.

| spec | verdict | elapsed | stage reached |
|------|---------|---------|---------------|
| `c7_session_drift_us_equity_style` | INCONCLUSIVE | 1.8 s | none (KeyError) |
| `c7_session_drift_crypto` | INCONCLUSIVE | 1.6 s | none (KeyError) |
| `c7_session_drift_fx_major` | INCONCLUSIVE | 23.5 s | none (KeyError) |
| `c7_session_drift_commodities` | INCONCLUSIVE | 14.8 s | none (KeyError) |
| `c7_session_drift_futures_broad` | INCONCLUSIVE | 6.7 s | none (KeyError) |
| `c7_session_drift_rates_credit` | INCONCLUSIVE | 5.9 s | none (KeyError) |
| `NEGATIVE-CONTROL-c7_session_drift_us_equity_style` | INCONCLUSIVE | 0.3 s | none (KeyError) |
| `NEGATIVE-CONTROL-c7_session_drift_crypto` | INCONCLUSIVE | 0.0 s | none (KeyError) |
| `NEGATIVE-CONTROL-c7_session_drift_fx_major` | INCONCLUSIVE | 0.0 s | none (KeyError) |
| `NEGATIVE-CONTROL-c7_session_drift_commodities` | INCONCLUSIVE | 0.0 s | none (KeyError) |
| `NEGATIVE-CONTROL-c7_session_drift_futures_broad` | INCONCLUSIVE | 0.0 s | none (KeyError) |
| `NEGATIVE-CONTROL-c7_session_drift_rates_credit` | INCONCLUSIVE | 0.0 s | none (KeyError) |

**ROBUSTNESS STAGES — C7:** NONE RAN. Every stage (walk-forward, cost
stress, gross-vs-net, parameter sweep, Monte Carlo, subperiod, capacity,
replication, causality, deflated Sharpe) was **NOT RUN** — the spec
aborted at feature computation. This is reported rather than hidden: no
C7 stage passed, because no C7 stage executed.

### C8 — `c8_liquidity_reversal_*` (liquidity-provision reversal)

#### 1. `c8_liquidity_reversal_us_equity_style` — **INCONCLUSIVE**

FLAGS (verbatim):
```
only 0 trades (need >=30)
0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few
edge does not survive 2x cost stress
parameter stability 0% (< 60%)
only 0/22 profitable years
```
- pooled OOS Sharpe (walk-forward): **None** (no fold produced a return series)
- in-sample Sharpe (base run): **None**
- n_trades: **0** | max drawdown: **0.0000** | total return: **0.0000** | n_bars: 5492
- OOS retention: None

Per-fold walk-forward (purge=20, embargo=20, mode=purged_embargoed, 5 folds, **0 profitable**):

| fold | OOS Sharpe | IS Sharpe | test range | oos_trades |
|------|-----------|-----------|------------|------------|
| 0 | None | None | 2005-08-23 → 2009-05-14 | 0 |
| 1 | None | None | 2010-01-05 → 2013-09-25 | 0 |
| 2 | None | None | 2014-05-16 → 2018-02-05 | 0 |
| 3 | None | None | 2018-09-25 → 2022-06-15 | 0 |
| 4 | None | None | 2023-02-06 → 2026-10-30 | 0 |

Stages: walk-forward **RAN** | gross-vs-net **RAN** | cost stress **RAN** |
parameter sweep **RAN** | Monte Carlo **ERRORED** ("only 0 trades — Monte
Carlo needs >=20") | subperiod/regime **RAN** | capacity **RAN** |
cross-market replication **NOT-RUN (absent from scorecard)** | causality
audit **RAN** | deflated Sharpe **NOT-RUN (None)**

#### 2. `c8_liquidity_reversal_crypto` — **FRAGILE**

FLAGS (verbatim):
```
t-stat -0.56 below 2.0 - the return series is not distinguishable from noise
only 1/5 walk-forward folds profitable (edge concentrated in a few periods)
edge does not survive 2x cost stress
Monte Carlo prob(profitable) 37%
only 1/6 profitable years
```
- pooled OOS Sharpe (walk-forward): **0.650**
- pooled OOS Sharpe (live basis): **0.650**
- in-sample Sharpe (base run, full sample): **-0.194**
- final-fold in-sample Sharpe: **-0.725** | OOS retention: None (final IS ≤ 0)
- n_trades: **30** | max drawdown: **0.0311** | total return: **-0.0137** | n_bars: 2132

Per-fold walk-forward (purge=20, embargo=20, **1 of 5 profitable**):

| fold | OOS Sharpe | IS Sharpe | test range | oos_trades |
|------|-----------|-----------|------------|------------|
| 0 | None | None | 2021-06-11 → 2022-03-03 | 0 |
| 1 | None | None | 2022-08-12 → 2023-05-04 | 0 |
| 2 | None | 0.140 | 2023-10-12 → 2024-07-03 | 0 |
| 3 | **1.456** | 0.122 | 2024-12-11 → 2025-09-02 | 10 |
| 4 | None | -0.725 | 2026-02-10 → 2026-11-02 | 0 |

All 30 trades and the entire pooled OOS Sharpe come from **one fold**
(10 trades). Four of five folds have no trades at all.

Stages: walk-forward **RAN** | gross-vs-net **RAN** | cost stress **RAN** |
parameter sweep **RAN** | Monte Carlo **RAN** | subperiod/regime **RAN** |
capacity **RAN** | cross-market replication **NOT-RUN (absent from
scorecard)** | causality audit **RAN** | deflated Sharpe **RAN**

#### 3. `c8_liquidity_reversal_fx_major` — **INCONCLUSIVE**

FLAGS (verbatim):
```
only 0 trades (need >=30)
0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few
edge does not survive 2x cost stress
parameter stability 0% (< 60%)
only 0/22 profitable years
```
- pooled OOS Sharpe: **None** | in-sample Sharpe: **None**
- n_trades: **0** | max drawdown: **0.0000** | total return: **0.0000** | n_bars: 5680

Per-fold walk-forward (5 folds, **0 profitable**, every fold OOS Sharpe None):

| fold | OOS Sharpe | IS Sharpe | test range | oos_trades |
|------|-----------|-----------|------------|------------|
| 0 | None | None | 2005-08-14 → 2009-05-19 | 0 |
| 1 | None | None | 2009-12-31 → 2013-09-26 | 0 |
| 2 | None | None | 2014-05-12 → 2018-02-08 | 0 |
| 3 | None | None | 2018-09-20 → 2022-06-19 | 0 |
| 4 | None | None | 2023-01-31 → 2026-11-03 | 0 |

Stages: walk-forward **RAN** | gross-vs-net **RAN** | cost stress **RAN** |
parameter sweep **RAN** | Monte Carlo **ERRORED** ("only 0 trades — Monte
Carlo needs >=20") | subperiod **RAN** | capacity **RAN** | replication
**NOT-RUN** | causality **RAN** | deflated Sharpe **NOT-RUN (None)**

#### 4. `c8_liquidity_reversal_commodities` — **REFUTED**

FLAGS (verbatim):
```
t-stat 0.22 below 2.0 - the return series is not distinguishable from noise
Monte Carlo prob(profitable) 59%
only 8/22 profitable years
```
- pooled OOS Sharpe: **0.161**
- in-sample Sharpe (base run): **0.047**
- final-fold in-sample Sharpe: **-0.615** | OOS retention: None
- n_trades: **171** | max drawdown: **0.0953** | total return: **0.0136** | n_bars: 5492

Per-fold walk-forward (purge=20, embargo=20, **3 of 5 profitable**):

| fold | OOS Sharpe | IS Sharpe | test range | oos_trades |
|------|-----------|-----------|------------|------------|
| 0 | 0.531 | None | 2005-08-23 → 2009-05-18 | 25 |
| 1 | 0.135 | -0.969 | 2010-01-07 → 2013-09-27 | 38 |
| 2 | **-0.090** | -0.792 | 2014-05-20 → 2018-02-09 | 45 |
| 3 | **-0.048** | -0.687 | 2018-10-01 → 2022-06-22 | 13 |
| 4 | 0.145 | -0.615 | 2023-02-10 → 2026-11-03 | 39 |

Pooled OOS 0.161 is below the 0.50 bar → REFUTED. The in-sample Sharpe
(0.047) is far below the pooled OOS; the final-fold in-sample Sharpe is
negative, so there is no positive IS edge to retain.

Stages: walk-forward **RAN** | gross-vs-net **RAN** | cost stress **RAN** |
parameter sweep **RAN** | Monte Carlo **RAN** | subperiod **RAN** |
capacity **RAN** | replication **NOT-RUN** | causality **RAN** | deflated
Sharpe **RAN**

#### 5. `c8_liquidity_reversal_futures_broad` — **REFUTED**

FLAGS (verbatim):
```
t-stat -0.41 below 2.0 - the return series is not distinguishable from noise
only 2/5 walk-forward folds profitable (edge concentrated in a few periods)
edge does not survive 2x cost stress
Monte Carlo prob(profitable) 33%
only 3/22 profitable years
```
- pooled OOS Sharpe: **0.001**
- in-sample Sharpe (base run): **-0.089**
- final-fold in-sample Sharpe: **-0.441** | OOS retention: None
- n_trades: **110** | max drawdown: **0.0450** | total return: **-0.0154** | n_bars: 5497

Per-fold walk-forward (purge=20, embargo=20, **2 of 5 profitable**):

| fold | OOS Sharpe | IS Sharpe | test range | oos_trades |
|------|-----------|-----------|------------|------------|
| 0 | 0.509 | None | 2005-08-23 → 2009-05-13 | 14 |
| 1 | **-0.339** | -0.695 | 2010-01-04 → 2013-09-25 | 14 |
| 2 | **-0.195** | -0.568 | 2014-05-16 → 2018-02-08 | 40 |
| 3 | 0.128 | -0.492 | 2018-09-28 → 2022-06-22 | 28 |
| 4 | None | -0.441 | 2023-02-10 → 2026-11-03 | 0 |

Pooled OOS 0.001 — indistinguishable from zero.

Stages: walk-forward **RAN** | gross-vs-net **RAN** | cost stress **RAN** |
parameter sweep **RAN** | Monte Carlo **RAN** | subperiod **RAN** |
capacity **RAN** | replication **NOT-RUN** | causality **RAN** | deflated
Sharpe **RAN**

#### 6. `c8_liquidity_reversal_rates_credit` — **INCONCLUSIVE**

FLAGS (verbatim):
```
only 0 trades (need >=30)
0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few
edge does not survive 2x cost stress
parameter stability 0% (< 60%)
only 0/22 profitable years
```
- pooled OOS Sharpe: **None** | in-sample Sharpe: **None**
- n_trades: **0** | max drawdown: **0.0000** | total return: **0.0000** | n_bars: 5491

Per-fold walk-forward (5 folds, **0 profitable**, every fold OOS Sharpe None):

| fold | OOS Sharpe | IS Sharpe | test range | oos_trades |
|------|-----------|-----------|------------|------------|
| 0 | None | None | 2005-08-23 → 2009-05-19 | 0 |
| 1 | None | None | 2010-01-07 → 2013-09-27 | 0 |
| 2 | None | None | 2014-05-16 → 2018-02-07 | 0 |
| 3 | None | None | 2018-09-27 → 2022-06-17 | 0 |
| 4 | None | None | 2023-02-08 → 2026-11-03 | 0 |

Stages: walk-forward **RAN** | gross-vs-net **RAN** | cost stress **RAN** |
parameter sweep **RAN** | Monte Carlo **ERRORED** ("only 0 trades — Monte
Carlo needs >=20") | subperiod **RAN** | capacity **RAN** | replication
**NOT-RUN** | causality **RAN** | deflated Sharpe **NOT-RUN (None)**

### C8 NEGATIVE CONTROLS

#### `NEGATIVE-CONTROL-c8_liquidity_reversal_crypto` — **REFUTED**
FLAGS (verbatim):
```
t-stat -0.05 below 2.0 - the return series is not distinguishable from noise
0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few
OOS Sharpe retains only -164% of the in-sample Sharpe (need 40%) - the edge degrades out of sample
edge does not survive 2x cost stress
Monte Carlo prob(profitable) 44%
only 2/6 profitable years
```
pooled OOS **-0.654** | in-sample **-0.016** | final-fold IS **0.400** |
retention **-1.635** | n_trades **30** | maxDD **0.0266** | total return **-0.0015**

| fold | OOS Sharpe | IS Sharpe | test range | oos_trades |
|------|-----------|-----------|------------|------------|
| 0 | None | None | 2021-06-11 → 2022-03-03 | 0 |
| 1 | None | None | 2022-08-12 → 2023-05-04 | 0 |
| 2 | None | -0.448 | 2023-10-12 → 2024-07-03 | 0 |
| 3 | **-1.465** | -0.388 | 2024-12-11 → 2025-09-02 | 10 |
| 4 | None | 0.400 | 2026-02-10 → 2026-11-02 | 0 |

**This is the control doing its job:** same universe, same 10 trades in the
same fold, opposite sign — real +1.456, control -1.465.

#### `NEGATIVE-CONTROL-c8_liquidity_reversal_commodities` — **REFUTED**
FLAGS (verbatim):
```
t-stat -0.38 below 2.0 - the return series is not distinguishable from noise
only 2/5 walk-forward folds profitable (edge concentrated in a few periods)
OOS Sharpe retains only -31% of the in-sample Sharpe (need 40%) - the edge degrades out of sample
edge does not survive 2x cost stress
Monte Carlo prob(profitable) 31%
only 7/22 profitable years
```
pooled OOS **-0.188** | in-sample **-0.080** | final-fold IS **0.603** |
retention **-0.311** | n_trades **171** | maxDD **0.0832** | total return **-0.0298**

| fold | OOS Sharpe | IS Sharpe | test range | oos_trades |
|------|-----------|-----------|------------|------------|
| 0 | **-0.534** | None | 2005-08-23 → 2009-05-18 | 25 |
| 1 | **-0.202** | 0.951 | 2010-01-07 → 2013-09-27 | 38 |
| 2 | 0.045 | 0.778 | 2014-05-20 → 2018-02-09 | 45 |
| 3 | 0.034 | 0.674 | 2018-10-01 → 2022-06-22 | 13 |
| 4 | **-0.161** | 0.603 | 2023-02-10 → 2026-11-03 | 39 |

#### `NEGATIVE-CONTROL-c8_liquidity_reversal_futures_broad` — **REFUTED**
FLAGS (verbatim):
```
t-stat 0.29 below 2.0 - the return series is not distinguishable from noise
only 2/5 walk-forward folds profitable (edge concentrated in a few periods)
OOS Sharpe retains only -8% of the in-sample Sharpe (need 40%) - the edge degrades out of sample
Monte Carlo prob(profitable) 61%
only 4/22 profitable years
```
pooled OOS **-0.037** | in-sample **0.062** | final-fold IS **0.438** |
retention **-0.084** | n_trades **110** | maxDD **0.0227** | total return **0.0097**

| fold | OOS Sharpe | IS Sharpe | test range | oos_trades |
|------|-----------|-----------|------------|------------|
| 0 | **-0.537** | None | 2005-08-23 → 2009-05-13 | 14 |
| 1 | 0.308 | 0.690 | 2010-01-04 → 2013-09-25 | 14 |
| 2 | 0.150 | 0.565 | 2014-05-16 → 2018-02-08 | 40 |
| 3 | **-0.174** | 0.489 | 2018-09-28 → 2022-06-22 | 28 |
| 4 | None | 0.438 | 2023-02-10 → 2026-11-03 | 0 |

#### `NEGATIVE-CONTROL-c8_liquidity_reversal_us_equity_style` — **INCONCLUSIVE**
#### `NEGATIVE-CONTROL-c8_liquidity_reversal_fx_major` — **INCONCLUSIVE**
#### `NEGATIVE-CONTROL-c8_liquidity_reversal_rates_credit` — **INCONCLUSIVE**

All three carry the identical flag set to their real twins (0 trades,
0/5 folds profitable, edge does not survive 2x cost stress, parameter
stability 0%, only 0/22 profitable years), the identical zero metrics
(n_trades 0, maxDD 0.0000, total return 0.0000), and 5 walk-forward folds
with OOS Sharpe None and oos_trades 0 on every fold. Stages: walk-forward
**RAN**, gross-vs-net **RAN**, cost stress **RAN**, parameter sweep
**RAN**, Monte Carlo **ERRORED** ("only 0 trades — Monte Carlo needs
>=20"), subperiod **RAN**, capacity **RAN**, replication **NOT-RUN**,
causality **RAN**, deflated Sharpe **NOT-RUN (None)**.

---

## STEP 4 — THE NEGATIVE CONTROLS

**No NEGATIVE-CONTROL spec came out SUPPORTED. Not one.**

| verdict | count | which |
|---------|-------|-------|
| SUPPORTED | **0** | — |
| REFUTED | 3 | c8 crypto, c8 commodities, c8 futures_broad |
| INCONCLUSIVE | 9 | all 6 C7 controls; c8 us_equity_style, c8 fx_major, c8 rates_credit |

The three C8 controls that produced trades all went the right way: the
inverted twin of the real spec has a **negative** pooled OOS Sharpe on
every one of them (crypto -0.654 vs real +0.650; commodities -0.188 vs
real +0.161; futures_broad -0.037 vs real +0.001). **C8's validation
discriminates.**

Two honest caveats:
1. **The C7 controls are not controls.** They are byte-identical to their
   real twins because `invert_signal` is silently discarded by the
   engine's `sig_cross_sectional`. They "failed" only because the real
   spec crashed first. A C7 verdict is currently unfalsifiable.
2. **The three C8 controls on the zero-trade universes are vacuous** for
   the same reason the real spec is: no trades, so nothing to invert.

See `reports/worker3_BUG_REPORT.md` for the full defect write-up.

---

## STEP 5 — CROSS-ASSET-CLASS CONSISTENCY

Pooled OOS Sharpe (walk-forward, out-of-sample) by asset class:

| asset class | C7 real | C7 control | C8 real | C8 control |
|-------------|---------|------------|---------|------------|
| us_equity_style | INCONCLUSIVE (none) | INCONCLUSIVE (none) | INCONCLUSIVE (none) | INCONCLUSIVE (none) |
| crypto | INCONCLUSIVE (none) | INCONCLUSIVE (none) | **FRAGILE (0.650)** | REFUTED (-0.654) |
| fx_major | INCONCLUSIVE (none) | INCONCLUSIVE (none) | INCONCLUSIVE (none) | INCONCLUSIVE (none) |
| commodities | INCONCLUSIVE (none) | INCONCLUSIVE (none) | **REFUTED (0.161)** | REFUTED (-0.188) |
| futures_broad | INCONCLUSIVE (none) | INCONCLUSIVE (none) | **REFUTED (0.001)** | REFUTED (-0.037) |
| rates_credit | INCONCLUSIVE (none) | INCONCLUSIVE (none) | INCONCLUSIVE (none) | INCONCLUSIVE (none) |

### C7 — does it work on one market, several, or all?
**It does not work on ANY market, because it never ran.** All six are
INCONCLUSIVE with the same `KeyError`. There is no cross-asset-class
consistency statement to make for C7 in the matrix. The honest statement
is: **C7 was not tested at all.**

### C8 — does it work on one market, several, or all?
**Not on one market, not on several, not on all.**

* On the three asset classes where it traded at all, the pooled OOS
  Sharpe is **0.650, 0.161, 0.001** — i.e. it clears the 0.50 bar on
  crypto only, is 3x below it on commodities, and is indistinguishable
  from zero on futures_broad.
* Two of those three are REFUTED outright, and the third (crypto,
  FRAGILE) fails four of its own robustness checks: t-stat -0.56,
  1/5 folds profitable, does not survive 2x cost stress, Monte Carlo
  prob(profitable) 37%. All 30 of its trades come from a single
  walk-forward fold.
* On the other three asset classes it produced **zero trades**, so it was
  not evaluated.

**Plain statement: C8 does not work on any asset class in this matrix.**
The one asset class where it looks non-negative (crypto) is FRAGILE on a
single fold and fails its own robustness checks, and the cross-asset-class
pattern — 0.65, 0.16, 0.00, and three markets with no trades at all — is
a market curiosity at best, not an edge.

---

## STEP 3 (CONT.) — C7 THE INTRADAY SESSION PATH: THE ACTUAL SAMPLE

**The sample size the provider actually serves (measured, 60m bars
collapsed to one opening-window bar per session):**

| asset class | spec period.start | 60m span | session bars | first → last session | symbols in panel | fetch failures |
|-------------|-------------------|----------|--------------|----------------------|------------------|----------------|
| us_equity_style | 2005-01-01 | 729 d | **501** | 2024-11-04 → 2026-11-03 | 6/6 | 0 |
| crypto | 2021-01-01 | 730 d | **731** | 2024-11-03 → 2026-11-03 | 10/10 | 0 |
| fx_major | 2005-01-01 | 729 d | **581** | 2024-11-04 → 2026-11-03 | 8/8 | 0 |
| commodities | 2005-01-01 | 729–730 d | **610** | 2024-11-03 → 2026-11-03 | 13/14 | 1 (`LBS=F` HTTP 404) |
| futures_broad | 2005-01-01 | 729–730 d | **612** | 2024-11-03 → 2026-11-03 | 15/15 | 0 |
| rates_credit | 2005-01-01 | 729 d | **501** | 2024-11-04 → 2026-11-03 | 12/12 | 0 |

**Was the sample truncated by the provider's 60m history limit? YES, on
every asset class.** The engine requests `range=2y` for any non-daily
interval (`btengine.py` lines 228-232: "60m is capped by the provider at
roughly 2 years of history"). Every asset class's 60m series starts
2024-11-03 or 2024-11-04 and ends 2026-11-03 — **~2 years**, against a
`period.start` of 2005-01-01 (or 2021-01-01 for crypto). The C7 concept is
therefore tested on **~2 of the ~21 requested years**.

### Would that short sample even support a verdict?

**No — and this is measured, not asserted.** Running the same C7 specs
with `execution.mode='session'` switched on in memory (a DIAGNOSTIC, not
the matrix result; `reports/worker3_c7_session_mode_diagnostic.json`):

| C7 spec (session mode) | verdict | pooled OOS | in-sample | trades | folds | profitable folds | key flags |
|------------------------|---------|------------|-----------|--------|-------|------------------|------------|
| us_equity_style | FRAGILE | 1.513 | 1.586 | **9** | **2** | 2 | only 9 trades (need >=30) |
| crypto | FRAGILE | 0.703 | **-0.139** | 40 | **3** | 2 | t-stat -0.24 below 2.0; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 38% |
| fx_major | INCONCLUSIVE | None | None | None | None | — | ValueError: cross_sectional needs >= 2 instruments with a usable value for 'session_drift', but only **0** has one |
| commodities | FRAGILE | 0.770 | 1.182 | **13** | **3** | 3 | only 13 trades (need >=30); t-stat 1.84 below 2.0 |
| futures_broad | FRAGILE | 0.524 | 0.489 | **15** | **3** | 2 | only 15 trades (need >=30); t-stat 0.76 below 2.0 |
| rates_credit | REFUTED | 0.257 | **-0.162** | 15 | **2** | 1 | only 15 trades; t-stat -0.23; only 1/2 folds profitable; edge does not survive 2x cost stress |

The walk-forward runs **2 or 3 folds, not 5**, because the sample is
501-731 bars and the engine needs `(n_folds+1)*60` bars plus purge and
embargo bands on top. The Monte Carlo stage **ERRORS** on four of the six
universes ("only N trades — Monte Carlo needs >=20").

**So the honest C7 answer is INCONCLUSIVE, twice over:**
1. In the matrix as shipped, C7 is INCONCLUSIVE because the spec never
   enables the session path (`KeyError: Unknown feature 'session_drift'`).
2. Even with the session path enabled, the intraday sample is ~2 years
   (501-731 sessions) against a 21-year request, yields 9-40 trades,
   2-3 folds instead of 5, and an unusable Monte Carlo stage. On that
   sample a verdict would be INCONCLUSIVE for sample-size reasons, not
   because the concept was refuted.

**The one thing that IS refuted here is C8** — and it is refuted on the
daily path where the sample is adequate (5,492 bars, 5 folds, 171 and
110 trades on commodities and futures_broad).

### Two further C7 data problems found while measuring this

* **FX is structurally unmeasurable on this path.** Yahoo returns
  **volume = 0.0** on every 60-minute bar for all eight G10 FX pairs, and
  `f_session_drift` (`intraday.py` line 204, `if rng <= 0 or not vol`)
  returns `None` for every bar of every FX pair. Measured: 579/581, 580/581
  and 579/581 unusable session bars for EURUSD=X, GBPUSD=X and AUDUSD=X
  respectively; **0 usable**. SPY: 501/501 usable; BTC-USD: 327/731.
  This is independent of the sample-length problem.
* **The "09:30 ET opening window" only exists for US equities.** The
  session extractor (`intraday.py` `extract_sessions`) takes the FIRST bar
  of each UTC calendar date. For SPY that is the 14:30 UTC (09:30 ET)
  bar. For EURUSD=X it is the **00:00 UTC** bar — the middle of the
  London/NY overlap, not an opening window — and for BTC-USD likewise
  00:00 UTC. So even with the volume bug fixed, C7's stated concept is
  not measurable on FX or crypto.

---

## BUGS FOUND (not fixed — no `leapspace/*.py` file was modified)

Full detail with line numbers in `reports/worker3_BUG_REPORT.md`.

1. **C7 never runs the intraday path it claims to test.**
   `leapspace/paperspecs.py` `_c7_session_drift` (lines 601-633) +
   `_make` (lines 279-309) + `EXECUTION_BLOCK` (lines 162-166).
   `execution.mode` is never `"session"` and `period.interval` stays
   `"1d"`, so `session_drift` is never registered
   (`btengine.py` lines 1609-1616) and `compute_features` raises
   (line 782). Fix needs BOTH `period.interval: "60m"` AND
   `execution.mode: "session"` — `btengine.py` lines 1584-1592 raise
   loudly on a 60m interval without session mode, because the daily path
   would silently collapse intraday bars onto the 15:30 ET close and
   return a plausible backtest of the wrong window.

2. **The C7 negative control is a byte-identical duplicate.**
   `leapspace/paperspecs.py` `build_negative_controls` (lines 724-756)
   sets `params["invert_signal"]=True`; the engine's
   `sig_cross_sectional` (`btengine.py` lines 831-852) takes `**kw` and
   never reads it, so the flag is silently discarded. Measured on the real
   session panel: `identical_signal_series: true`, 2004 non-zero positions
   on both sides, 1002 short positions on both sides — **the short leg is
   not flipped**. C8's signal (`leapspace/backtest.py` line 1347) *does*
   honour it, which is why C8's control works and C7's does not.

3. **C8's signal emits its position value on the entry bar ONLY.**
   `leapspace/backtest.py` `sig_liquidity_gated_reversion` (lines
   1347-1402): the held-bar branch appends `0.0`. The engine's
   `construct_target_weights` (`btengine.py` lines 990-1016) only rebuilds
   the book on rebalance-marked bars, and the shared risk block sets
   `rebalance: "monthly"`, so a position opens only when the entry bar
   coincides with a monthly rebalance bar. The engine's own
   `sig_time_series_zscore` (lines 873-896) keeps `pos` and appends it on
   every bar — the LeapSpace signals invert that convention. Measured on
   `c8_liquidity_reversal_us_equity_style`: 5492 bars, 262 rebalance bars,
   **5 entry events, 0 of which land on a rebalance bar → 0 trades, final
   equity 100000.00 unchanged.** The same pattern is in
   `sig_rsi_confirmed_reversion` (lines 1247-1294) and the other stateful
   signals in `register_extensions`.

4. **`session_drift` is unusable on FX** — Yahoo serves volume = 0.0 on
   every 60m FX bar; `intraday.py` line 204 rejects the bar. 0 usable
   session bars across all eight G10 pairs.

5. **`paperrun.py`'s result row is lossy** (a reporting defect, not a
   validation defect): `_row_from_result` (lines 204-243) reads
   `oos_sharpe` from the BASE metric block, so it falls back to the
   **in-sample** Sharpe; the per-fold walk-forward table is a list and is
   dropped; and the scorecard has no `"validation"`/`"stages"` key, so the
   row records no stage status at all. This run captured the full
   scorecards separately (`reports/worker3_c7_c8_detail.json`) so the
   numbers reported above are the real ones.

---

## DISK

`df -h /c` before the run: **2.0 GB free** (119 G, 99% used).
After the run: **1.9 GB free**. The engine's OHLCV cache grew from 31 MB to
**98 MB** (70 new `*_60m.json` files for the intraday probes, plus the
daily series for commodities/futures/rates that were not previously
cached). Nothing was deleted; no unrelated file was removed.

---

## FILES CREATED (all under `reports/`; no `leapspace/*.py` was touched)

| file | purpose |
|------|---------|
| `run_matrix_worker3.py` | the deliverable runner |
| `worker3_c7_c8.log` | the raw run log (282 lines) |
| `worker3_c7_c8_detail.json` | full per-spec gauntlet scorecards |
| `worker3_c7_c8_results.json` | this worker's 24 rows, standalone |
| `worker3_BUG_REPORT.md` | the four defects, with line numbers |
| `worker3_c7_session_mode_diagnostic.json` / `.log` | C7 with the session path on, in memory |
| `worker3_c7_session_path_probe.json` | the intraday sample per asset class |
| `worker3_c7_control_invert_test.json` | proof the C7 control does not invert |
| `worker3_c8_zero_trades_probe.json` | proof of the C8 zero-trade mechanism |
| `worker3_fx_session_drift_probe.json` | proof of the FX zero-volume problem |
| `worker3_invert_control_probe.json` | C8's control DOES invert (the contrast case) |
| `_probe_worker3_*.py` | the probe scripts that produced the above |

`reports/paper_concept_results.json` was updated by the run (96 rows: the
24 C7/C8 rows plus the 72 from the other workers).
