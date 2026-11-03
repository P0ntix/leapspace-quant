# Worker 3 -- BUG REPORT: C7 and C8 paper-concept validation

Four defects were found while running the C7/C8 matrix through the full
gauntlet. None of them were fixed, because the task forbids editing
`leapspace/*.py`. Each one is stated with the file, the line, what is
wrong, and what it does to the result.

Every number quoted here was produced by a run in `reports/`; the probe
scripts are named at the end of each item.

---

## BUG 1 -- C7 NEVER RUNS THE INTRADAY PATH IT CLAIMS TO TEST
**Severity: fatal for C7. C7 has produced no result at all.**

* **File:** `leapspace/paperspecs.py`, function `_c7_session_drift`
  (lines 601-633), together with `_make` (lines 279-309) and
  `EXECUTION_BLOCK` (lines 162-166).
* **What is wrong:** the spec declares the feature `session_drift` and its
  own `intake.notes` says "The session path returns DAILY returns (one bar
  per session)". But the spec it actually builds carries:

  ```
  "period":    {"start": "2005-01-01", "end": None, "interval": "1d"},
  "execution": {"fill_at": "open", "cost_multiplier": 2.0, "max_participation": 0.1}
  ```

  `execution.mode` is never set to `"session"`, and `period.interval` stays
  `"1d"`. `_make` hard-codes both (`_make` line 286 sets `interval: "1d"`;
  line 290 copies `EXECUTION_BLOCK`, which has no `mode` key), and
  `_c7_session_drift` does not override either.

  In the engine, `session_drift` lives in `intraday.INTRADAY_FEATURES` and
  is registered only on the session path --
  `btengine.py` lines 1609-1616:

  ```python
  if session_mode:
      from intraday import INTRADAY_FEATURES, build_session_panel
      register_features(INTRADAY_FEATURES)
  ```

  `session_mode` is `exec_spec.get("mode") == "session"` (btengine.py line
  1580). Without it, the daily path runs and `compute_features` raises
  (btengine.py line 782):

  ```
  KeyError: "Unknown feature 'session_drift'. Available: ['atr_pct', ...]"
  ```

* **Effect on the result:** all six C7 asset classes (and their six
  negative controls) return `INCONCLUSIVE` with that KeyError as the
  error. `c7_session_drift_us_equity_style` finishes in 1.8 s, which is
  the time to fail, not the time to test. **The matrix contains no C7
  result at all.**
* **Secondary effect:** even if the feature were registered, the daily
  path would still be wrong for this concept. `btengine.run_spec` raises
  loudly if `period.interval != "1d"` without `execution.mode ==
  "session"` (lines 1584-1592), because the daily path collapses intraday
  bars onto the LAST bar of the day -- the 15:30 ET close -- which is a
  plausible-looking backtest of the wrong window. The C7 concept is about
  the OPENING window, so the spec needs BOTH `period.interval: "60m"`
  AND `execution.mode: "session"`.
* **Evidence:** `reports/worker3_c7_c8_detail.json`
  (`c7_session_drift_*` -> `INCONCLUSIVE`, errors contain the KeyError);
  `reports/worker3_c7_session_mode_diagnostic.json` (the same specs with
  `execution.mode='session'` added in memory, which do run).

---

## BUG 2 -- THE C7 NEGATIVE CONTROL IS A BYTE-IDENTICAL DUPLICATE
**Severity: fatal for the validity of ANY C7 verdict.**

* **File:** `leapspace/paperspecs.py`, `build_negative_controls`
  (lines 724-756), and `btengine.py`, `sig_cross_sectional`
  (lines 831-852).
* **What is wrong:** `build_negative_controls` flips the polarity by
  writing `params["invert_signal"] = True` into the signal's params
  (lines 746-748). That flag only does anything if the signal
  implementation reads it. C7's signal type is `cross_sectional`, which
  is the ENGINE's `sig_cross_sectional`:

  ```python
  def sig_cross_sectional(panel, features, long_rank=0.8, short_rank=0.2, **kw):
      fname = kw["feature"]
      ...
  ```

  `**kw` swallows `invert_signal` and the body never reads it. The flag is
  **silently discarded**. The "negative control" is therefore the same
  strategy as the real spec, with a different name.

  (For contrast: C8's signal `liquidity_gated_reversion` is registered by
  LeapSpace in `leapspace/backtest.py` line 1347 and DOES take
  `invert_signal=False` and apply `_invert()` -- line 1394. C8's control
  is a real control. C7's is not.)
* **Effect on the result:** the C7 negative control returns the SAME
  verdict, the SAME pooled OOS Sharpe, the SAME fold table and the SAME
  flags as the real C7 spec. A control that is identical to the thing it
  controls cannot fail, so it can never prove that the validation
  discriminates. If a C7 verdict of SUPPORTED or FRAGILE is ever
  published, it is void.
* **Evidence:** `reports/worker3_c7_control_invert_test.json` -- on the
  real session panel, `identical_signal_series: true`,
  `nonzero_real: 2004`, `nonzero_control: 2004`,
  `short_positions_real: 1002`, `short_positions_control: 1002` (the
  short leg is NOT flipped).
  `reports/worker3_c7_session_mode_diagnostic.json` -- real and control
  have identical pooled OOS Sharpe to full float precision
  (1.5128349449978349 for both on us_equity_style; 0.7030924221564215 for
  both on crypto).
* **Fix (not applied):** either give `sig_cross_sectional` an
  `invert_signal` parameter that negates the emitted weights, or have
  `build_negative_controls` negate the signal's own `direction` /
  `long_rank`/`short_rank` params for a cross-sectional signal.

---

## BUG 3 -- C8's SIGNAL EMITS ITS POSITION VALUE ON THE ENTRY BAR ONLY
**Severity: fatal for C8 on any universe where entries miss the rebalance
bar. C8's trade counts are a sampling artefact, not a measure of the
concept.**

* **File:** `leapspace/backtest.py`, `sig_liquidity_gated_reversion`
  (lines 1347-1402). The same pattern is in
  `sig_rsi_confirmed_reversion` (lines 1247-1294) and, by inspection,
  in the other stateful signals in `register_extensions`.
* **What is wrong:**

  ```python
  if not in_pos:
      if zz <= float(entry) and thin and hot:
          in_pos = True
          row.append(_invert(1.0, invert_signal))   # entry bar: 1.0
      else:
          row.append(0.0)
  else:
      if zz >= float(exit):
          in_pos = False
      row.append(0.0)                               # HELD bars: 0.0
  ```

  On every bar where the position is HELD the signal emits `0.0`. The
  position value is emitted for exactly one bar -- the bar the position
  opens -- and then discarded.

  `btengine.construct_target_weights` (btengine.py lines 990-1016) only
  rebuilds the book on bars marked by `rebalance_mask`. The shared risk
  block sets `rebalance: "monthly"`, so only ~1 bar in 21 can generate an
  order. The engine's own `sig_time_series_zscore` (btengine.py lines
  873-896) does the opposite -- it keeps `pos` and appends `pos` on every
  bar, so a position survives across rebalances. The LeapSpace signals
  invert that convention.

  Net effect: a position is opened only when the ENTRY bar happens to
  coincide with a monthly rebalance bar. On any other bar the entry is
  invisible to the portfolio builder, the name is never a candidate, and
  nothing is ever traded.
* **Effect on the result (measured, `c8_liquidity_reversal_us_equity_style`):**
  * sample: 5492 daily bars, 262 monthly rebalance bars;
  * entry events in the whole sample: **5** (DIA 0, IWM 2, MDY 1, QQQ 1,
    RSP 2, SPY 0);
  * entry events that land ON a rebalance bar: **0 of 5**;
  * engine trades recorded: **0**; final equity 100000.00 (unchanged);
  * every fold's OOS Sharpe: `n/a`; base Sharpe `n/a`; maxDD 0.0%;
  * the verdict `INCONCLUSIVE` is reached via the "too few trades"
    branch, so the strategy was never actually evaluated.
  * Had the signal kept the position value while held, the same sample
    would have carried **30 held bars** -- still a tiny book, but a real
    one.
* **Effect on the result (crypto, `c8_liquidity_reversal_crypto`):** the
  same mechanism, and the C8 crypto spec came out `FRAGILE` with a
  pooled OOS Sharpe that rests on a handful of trades whose entries
  happened to coincide with rebalance bars. It is not evidence of an
  edge; it is evidence of a sampling artefact.
* **Evidence:** `reports/worker3_c8_zero_trades_probe.json` (the counts
  above); `reports/_probe_worker3_c8_us_verbose.log` (the engine's own
  transcript: `bars=5492 trades=0 sharpe=n/a`, every fold `OOS sh=n/a`,
  `cost x1.0: sharpe=n/a`).

---

## BUG 4 -- `session_drift` IS UNUSABLE ON THE FX UNIVERSE
**Severity: fatal for C7 on FX, independently of Bug 1.**

* **File:** `intraday.py`, `f_session_drift` (lines 176-218), specifically
  the guard on line 204: `if rng <= 0 or not vol: raw.append(None)`.
* **What is wrong:** Yahoo returns **volume = 0.0** on every 60-minute bar
  for the G10 FX pairs. `not vol` is true for `0.0`, so `f_session_drift`
  returns `None` for every bar of every FX pair, and the feature has no
  usable value anywhere in the FX panel.

  Measured over the whole 60m sample per symbol (session bars extracted
  from the raw 60m records):

  | symbol | sessions | None OHLC | zero/neg range | **zero volume** | usable |
  |--------|---------:|----------:|---------------:|-----------------:|-------:|
  | EURUSD=X | 581 | 0 | 2 | **579** | **0** |
  | GBPUSD=X | 581 | 0 | 1 | **580** | **0** |
  | AUDUSD=X | 581 | 0 | 2 | **579** | **0** |
  | SPY      | 501 | 0 | 0 | 0 | 501 |
  | BTC-USD  | 731 | 0 | 0 | 404 | 327 |

  With zero usable values the engine's `compute_signal` refuses the
  cross-sectional signal:
  `ValueError: The cross_sectional signal needs at least TWO instruments
  to rank against each other, but only 0 has a usable value for feature
  'session_drift'`.

  A related, separate problem: the session extractor takes the FIRST bar
  of each UTC calendar date. For FX that is the 00:00 UTC bar (the
  middle of the London/NY overlap, not an opening window at all), and
  for BTC-USD it is the 00:00 UTC bar too. The "09:30 ET opening window"
  the module documents only exists for the US-equity universe. So even
  with volume fixed, the C7 concept as specified (an opening-window
  drift) is not measurable on FX or crypto.
* **Evidence:** `reports/worker3_fx_session_drift_probe.json`
  (`session_bar_condition_counts` per symbol, plus the raw first-bar
  rows showing `v: 0.0` for every FX session and
  `first_bar_utc: 00:00:00+00:00` for FX and BTC).

---

## A FIFTH, NON-BUG FINDING: THE INTRADAY SAMPLE IS ~2 YEARS
The provider caps 60-minute history at roughly 2 years
(`btengine.py` lines 228-232: `range=2y` for any non-daily interval, and
the comment "60m is capped by the provider at roughly 2 years of
history"). Measured first/last dates on the 60m series: every asset class
starts between 2024-11-03 and 2024-11-04 and ends 2026-11-03.

Consequences for C7, whatever the bugs above are fixed:
* the sample is **501-731 session bars**, not the 2005-start the spec
  requests;
* the walk-forward therefore runs **2-3 folds, not 5** (the engine needs
  `n >= (n_folds+1)*60` bars and the purged/embargoed planner needs the
  purge and embargo bands on top);
* trade counts are 9-40, so the engine's own Monte Carlo stage refuses to
  run ("only N trades -- Monte Carlo needs >=20") on four of the six
  universes.

So even in the best case C7's intraday evidence is a 2-year, 2-3 fold,
under-30-trade sample. `INCONCLUSIVE` is the honest verdict for C7 on
that evidence -- and on the evidence actually produced (the KeyError) it
is INCONCLUSIVE too, for a different and more damning reason.

---

## FILES
No file under `leapspace/` was modified. Everything below is new, under
`reports/`:

| file | purpose |
|------|---------|
| `run_matrix_worker3.py` | the deliverable runner: `run_matrix(..., quick=False, only=['c7_','c8_'])` |
| `worker3_c7_c8.log` | the raw run log |
| `worker3_c7_c8_detail.json` | full per-spec gauntlet scorecards |
| `worker3_c7_c8_results.json` | this worker's rows, standalone |
| `worker3_c7_session_mode_diagnostic.json` / `.log` | C7 with the session path enabled in memory |
| `worker3_c7_session_path_probe.json` | the intraday sample per asset class |
| `worker3_c7_control_invert_test.json` | proof that the C7 control does not invert |
| `worker3_c8_zero_trades_probe.json` | proof of the C8 zero-trade mechanism |
| `worker3_fx_session_drift_probe.json` | proof of the FX zero-volume problem |
| `_probe_worker3_*.py` | the probe scripts that produced the above |
