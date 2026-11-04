# TECHNICAL OVERVIEW — leapspace-quant

**Package:** `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant`
**Repository:** https://github.com/P0ntix/leapspace-quant
**Measured:** 2026-11-04 — 63 modules, 42,166 lines, 422 module-level public functions, 125 public methods, 59 classes, 150 internal dependency edges.

**Generated artefacts:**
- `reports/charts/architecture.html` — the diagram and module inventory, **generated from the code** (`python -m leapspace.cli architecture`). It cannot go stale silently, because running the generator after a refactor shows the new shape.
- `reports/TECHNICAL_FUNCTION_REFERENCE.md` — every module, every public function and method, with signatures, dependencies and 26 curated gotchas. Regenerate with `python tools/build_function_reference.py`.

---

## 1. WHAT THIS PACKAGE IS

A research and trading-automation system built from six LeapSpace
research papers (which are really three unique documents — see §9).

It does four things:

1. **Fetches** market, on-chain, social and disclosure data, with every
   fetch recording its provenance.
2. **Computes** features — indicators, and *forward-looking* ones: the
   volatility risk premium, perpetual-swap funding, open interest,
   dealer gamma.
3. **Backtests** trading rules through a purged walk-forward gauntlet,
   with negative controls, cost stress, Monte Carlo and a causality
   audit.
4. **Reports** — markdown, JSON and self-contained HTML dashboards —
   separating what was found from what was not checked.

**The honest state, as measured:** no paper concept has earned a
`SUPPORTED` verdict in the 96-spec matrix; the negative controls all
failed (which is what makes the refutations meaningful); the one
`FRAGILE` row carries a *negative* Sharpe. The package can demonstrate
that it can *test* a claim rigorously. It cannot yet demonstrate that it
has an edge to trade. `LIVE_CAPITAL_READINESS.md` carries the full
assessment.

---

## 2. THE DIAGRAM

Open `reports/charts/architecture.html`. It has four panels:

### 2.1 The ten layers

| Layer | Modules | Lines | What lives there |
|---|---|---|---|
| **Infrastructure** | 9 | 4,778 | `http`, `provenance`, `models`, `cli`, `reportvalidate`, `adapter_checks`, `socialedge`, `cmd_extra`, `archviz` |
| **Data sources** | 16 | 8,662 | `market`, `onchain`, `etherscan`, `social`, `disclosure`, `chains`, `chainregistry`, `crosschain`, `holders`, `traders`, `deployers`, `narrative`, `priced`, `priceatblock`, `whitelist`, `source_reliability` |
| **Features & leading indicators** | 6 | 2,873 | `leading`, `leadingcache`, `cryptoderivs`, `gamma`, `regime`, `leadingspecs` |
| **Signals** | 3 | 953 | `ensemble`, `trend`, `stats` |
| **Portfolio & risk** | 4 | 4,227 | `costs`, `friction`, `riskguard`, `portfolio` |
| **Backtest engine** | 5 | 4,940 | `backtest`, `quant`, `paperspecs`, `paperrun`, `specs_2_0` |
| **Validation** | 6 | 4,028 | `reference_gate`, `edge`, `pbo`, `biasaudit`, `gate_tests`, `criteria` |
| **Reports & visualisation** | 7 | 6,365 | `report`, `report_memecoin`, `paperreport`, `backtestviz`, `viz`, `viz_leading`, `viz_memecoin` |
| **Governance & policy** | 2 | 2,022 | `signal`, `alerts` |
| **Wallet & chain profiling** | 5 | 3,318 | `memecoin`, `memecoinscan`, `profiler`, `launchscan`, `walletsearch` |

The layer assignment is an **explicit table** in `leapspace/archviz.py`,
not a default. A new module has to be placed deliberately.

### 2.2 The pipeline, and the trap at each stage

```
1  DATA SOURCE          market · onchain · social · disclosure
      ⚠ a fetch can fail, rate-limit, or return a different subset than
        the last fetch. Every fetch records URL, HTTP status and what
        was measured.

2  FEATURE              leading · cryptoderivs · regime · gamma
      ⚠ a leading feature must be timestamped and aligned with a
        ONE-BAR PUBLICATION LAG, or it is not leading - it is
        look-ahead. A missing value is None, NEVER zero.

3  SIGNAL               backtest · ensemble · trend
      ⚠ the signal says WHICH WAY; the portfolio block does the sizing.
        A signal that ignores `invert_signal` produces a negative
        control that CANNOT FAIL.

4  PORTFOLIO & RISK     portfolio · riskguard · costs · friction
      ⚠ the caps are applied LAST. The kill switch downgrades an ENTER
        to an AVOID - but there is still NO order-placement path for
        it to gate.

5  SIMULATION           btengine / btvalidate  (the shared skill)
      walk-forward with purge + embargo · cost stress · gross-vs-net ·
      parameter sweep · Monte Carlo · subperiod · capacity ·
      replication · causality audit

6  VERDICT              backtest · pbo · edge
      ⚠ a crash is an ERROR, not an INCONCLUSIVE. The pooled OOS
        Sharpe is the result; the in-sample Sharpe is reported BESIDE
        it and never substituted for it.

7  REPORT               paperreport · backtestviz · report
      ⚠ the report separates a finding from a crash, scopes the
        discrimination claim to the controls that executed, and says
        which stages never ran.
```

### 2.3 The hot spots

The modules most things depend on — where a refactor does the most
damage:

| Module | Depended on by | Why it matters |
|---|---|---|
| `provenance` | 30 | Every fetch and every artefact. The single chokepoint for credential redaction. |
| `http` | 19 | The fetch layer: retries, decompression, caching, SSL context. |
| `models` | 8 | The shared dataclasses (`TradeRecord`, `RugEvent`, `CopyTrade`, …). |
| `backtest` | 6 | The engine wrapper, the intake gate, the signal/feature registry, the stage ledger. |
| `chains` | 6 | The chain registry and multi-chain routing. |
| `market` | 5 | OHLCV and option-chain fetching. |
| `leading` | 4 | The volatility risk premium and the alignment rule. |
| `costs` | 4 | The cost model everything else is stressed against. |

---

## 3. THE DATA MODEL

`leapspace/models.py` (421 lines, 12 classes) holds the shared types.
The ones that matter:

| Type | Shape | Used by |
|---|---|---|
| `TradeRecord` | dataclass — entry/exit, size, P&L, fees, skip reason | `friction`, `quant`, `signal` |
| `RugEvent` | dataclass — a detected rug event on a position | `friction`, `quant` |
| `CopyTrade` | dataclass — a copied trade from a tracked wallet | `quant`, `edge` |
| `Signal` / `SignalLeg` | dataclass — a decision with per-leg reasoning | `signal`, `riskguard` |
| `Provenance` | dataclass — source, kind, URL, params, note | every fetch; `provenance.py` |

The convention throughout: **a field that was not measured is `None`,
never `0`**. A zero volatility risk premium reads as "options are
fairly priced", which is a claim the data does not support; a zero
probability reads as "impossible". This is enforced in the features, in
the metrics and in the reports.

---

## 4. THE FIVE MODULES THAT MATTER MOST

If you read five files, read these.

### 4.1 `leapspace/backtest.py` (2,291 lines)

The engine wrapper and the package's centre of gravity.

- **`register_extensions(btengine)`** — injects the package's features
  and signals into the shared engine's registries. Currently:
  `regime_momentum_score`, `leading_iv_level`, `leading_vrp_score`,
  `leading_vrp_zscore`, `session_drift`; and the signals
  `regime_switch`, `regime_switch_cross_sectional`,
  `rsi_volume_confirmation`, `leading_vrp_switch`,
  `vol_regime_momentum`, `volume_confirmed_momentum`,
  `rsi_confirmed_reversion`, `rebound_danger_momentum`,
  `liquidity_gated_reversion`, `paper_cross_sectional`,
  `ensemble_blend`, `trend_long_short`, `pairs_mean_reversion`.
- **`apply_intake_gate(spec)`** — a spec cannot run until every probed
  condition (direction, exit, timeframe, leverage, costs, period, …)
  has a provenance entry saying whether it came from the paper or from
  a documented analyst choice. This is why the package can state
  "analyst_choice" next to a number.
- **`run_spec(spec, quick=…)`** — runs the gauntlet and returns a
  `BacktestResult` carrying the verdict, the flags, the metrics, the
  **pooled OOS Sharpe**, the **per-fold table**, the **stage ledger**
  and the **skipped stages**.
- **`_normalise_stage` / `_stage_entry`** — canonicalise the gauntlet's
  stage names and derive each stage's real status. The gauntlet marks a
  skipped stage `{"error": "skipped"}`; reading only `status` made every
  skipped stage look like it had run.

### 4.2 `leapspace/leading.py` (711 lines) + `leadingcache.py` (255)

The forward-looking layer.

- `implied_vol_series(symbol)` — ^VIX / ^VXN / ^VXD from Yahoo.
- `dvol_history(currency, days)` — Deribit's DVOL for crypto, paginated.
  **The pagination detail matters:** the endpoint caps each call at 1,000
  points, so at *hourly* resolution it covers ~41 days and at *daily*
  resolution ~1,000 days. Getting this wrong would leave a multi-year
  panel with no leading input in most of it.
- `volatility_risk_premium(iv, rv)` — implied minus realised.
- `align_to_bars(series, bar_timestamps, max_lag_bars=1)` — the
  no-look-ahead rule. A bar at *T* may only use a measurement published
  before *T*.
- `deribit_gamma_exposure`, `deribit_option_flow` — live dealer-gamma
  and flow readings.

### 4.3 `leapspace/portfolio.py` (612 lines)

The risk layer the engine lacked. The engine's portfolio block assumes
**zero correlation** between assets, which overstates a diversified
book's risk and makes risk parity impossible. This module supplies:

- `estimate_covariance(returns, shrinkage)` — a shrunk covariance
  estimate. The shrinkage is what stops a 2-asset sample producing a
  nonsense correlation.
- `risk_parity_weights(cov)` — equal *risk contribution* sizing by
  fixed-point iteration. The update works on risk **shares** (which are
  scale-invariant), not absolute contributions (which are not) — the
  absolute form fights the renormalisation and never converges.
- `build_risk_managed_weights(...)` — volatility targeting, forward-
  weighted volatility, a drawdown-responsive de-risking slope, and the
  caps applied last.
- `portfolio_risk_report(...)` — concentration (HHI), effective number
  of names, per-name risk shares.

Measured effect: on a correlated two-asset book, risk parity gives a
**0.0443** annualised portfolio volatility against **0.1377** for equal
weighting — a 3.1× reduction. The drawdown scaler takes a 76.5% max
drawdown to 20.0%.

### 4.4 `leapspace/paperspecs.py` (808 lines) + `paperrun.py` (409)

The matrix.

- `build_specs(concepts, asset_classes)` — 9 concepts × 6 asset classes
  = 54 real specs.
- `build_negative_controls(specs)` — 54 inverted-polarity twins. The
  control builder sets `signal.params.invert_signal = True`; **every
  signal must read it**, and the test `test_negative_controls.py`
  asserts that each inverted signal differs from its real one.
- `run_matrix(specs, quick, only, out_path, log_path)` — runs and
  merges **by name**, under an exclusive lock, so parallel workers
  cannot lose each other's rows.

### 4.5 `leapspace/backtestviz.py` (899 lines) + `paperreport.py` (953)

The visual presentation. `backtestviz` reads the raw OOS return
series from the scorecards and renders equity curves, the underwater
drawdown plot, per-fold Sharpe bars, the P&L distribution and the
outcome table (win rate, profit factor, payoff ratio, expectancy per
bar). Pure-stdlib inline SVG, because this host has no scientific
stack and a report that cannot be rendered is not a report.

---

## 5. THE FEATURE AND SIGNAL REGISTRY

The registries are **the shared engine's**, extended by
`backtest.py::register_extensions`. To read them live:

```python
from leapspace import backtest as B
_bt, _bv, _ = B._load_skill_modules()
B.register_extensions(_bt)
sorted(_bt.FEATURES.keys()), sorted(_bt.SIGNALS.keys())
```

The engine's own features and signals are `return`, `momentum`,
`sma_gap`, `volatility`, `vol_ratio`, `zscore`, `rsi`, `max_drawdown`,
`skew`, `volume_ratio`, `bollinger_pct`, `atr_pct`, `ma_crossover`,
`dist_to_high`, plus `constant`, `cross_sectional`, `crossover`,
`time_series_threshold` and `time_series_zscore`.

The package adds:

| Feature | Source | Leading? |
|---|---|---|
| `regime_momentum_score` | `backtest.py` | no, but regime-scaled |
| `leading_iv_level` | `backtest.py` | **yes** — implied volatility level |
| `leading_vrp_score` | `backtest.py` | **yes** — implied minus realised |
| `leading_vrp_zscore` | `backtest.py` | **yes** — the premium's z-score, over an **expanding** window |
| `session_drift` | `backtest.py` | no — a daily-bar proxy for session drift |

| Signal | Concept | Direction | `invert_signal` honoured? |
|---|---|---|---|
| `regime_switch` | C1 regime-conditioned momentum/reversal | long/short | yes |
| `leading_vrp_switch` | C2 volatility risk premium | long/short | yes |
| `vol_regime_momentum` | C3 volatility-regime filter | long/short | yes |
| `volume_confirmed_momentum` | C4 volume confirmation | long/short | yes |
| `rsi_confirmed_reversion` | C5 RSI confirmation | long | yes |
| `rebound_danger_momentum` | C6 rebound danger | long/short | yes |
| `paper_cross_sectional` | C7 session drift | long/short | yes — a wrapper, because the engine's own signal swallows the flag |
| `liquidity_gated_reversion` | C8 liquidity-provision reversal | long | yes |
| `ensemble_blend` | C9 the hedged ensemble | long/short | yes |
| `trend_long_short` | the paper's long/short trend rule | long/short | yes |
| `pairs_mean_reversion` | dollar-neutral pairs | long/short | yes |
| `regime_switch_cross_sectional`, `rsi_volume_confirmation` | the package's original specs | varies | n/a |

**Every one of them honours `invert_signal`**, and
`leapspace/tests/test_negative_controls.py` asserts it — each inverted
signal must differ from its real one, and negate exactly where the
control semantics say it should. That test exists because four
signals once did not.

---

## 6. THE EIGHT FAILURE MODES THE PACKAGE NOW GUARDS AGAINST

These are not hypothetical. Each one was found in this package, and
each has a test.

| Failure | What it did | The guard |
|---|---|---|
| **A crash reported as INCONCLUSIVE** | 24 specs looked like weak research findings when they had never run | a crash is `ERROR`; the report marks non-running rows "DID NOT RUN" |
| **A look-ahead in a leading feature** | the z-score normalised over the whole panel, so bar *i* depended on later bars | expanding-window z-score; `test_leading_causality.py` asserts causality by truncation |
| **A no-op negative control** | four signals ignored the inversion flag, so those controls could not fail | `test_negative_controls.py` asserts each inverted signal differs and negates |
| **In-sample Sharpe reported as OOS** | 62 of 96 rows carried the in-sample number under the `oos_sharpe` key | separate keys; `oos_sharpe` is read from the walk-forward block |
| **A skipped stage counted as validated** | the gauntlet marks skips as `{"error": "skipped"}`; only `status` was read | `_stage_entry` derives the real status; `replication` is explicitly SKIPPED |
| **A coverage number that was never measured** | "the series has 2,051 points" was reported as coverage | coverage is now the ALIGNED count: 2,051/2,134 bars = 96.1% on crypto |
| **Wrapping an engine changes its behaviour** | renaming the signal type silently dropped the conviction ranking, so `max_names` kept names alphabetically | `test_cross_sectional_parity.py` asserts the wrapper's book is identical to the engine's |
| **A parameter that tightens when loosened** | `rank_floor` was applied as `1 - rank_floor`, so raising it made the book looser | `test_ensemble.py` asserts the filters actually filter |

---

## 7. THE RESEARCH STATE, MEASURED

From `reports/PAPER_CONCEPT_REPORT.md` and
`reports/charts/backtest_outcomes.html`:

| | Real specs | Negative controls |
|---|---|---|
| SUPPORTED | **0** | 0 |
| FRAGILE | 1 | 0 |
| REFUTED | 29 | 30 |
| INCONCLUSIVE | 18 | 18 |
| **actually executed** | **36 / 48** | **36 / 48** |

The strongest single cell is **C6 rebound-danger on US equity style,
OOS Sharpe +0.429** — one market, below the 0.5 bar, t-stat 1.17, 3/5
folds. The strongest by profit factor is **C8 liquidity-reversal on
crypto, PF 2.59** — but with a **1.2% win rate**, so the upside is a
handful of large wins rather than consistency. Neither is an edge.

**The controls are what make this meaningful.** The C3–C6 controls were
genuine and all failed. A matrix without controls would look identical
whether the concepts were real or invented.

---

## 8. THE DATA SOURCES

Documented in `LEADING_DATA_SOURCES.md` (leading vs lagging, global
scope) and `FREE_DATA_SOURCES.md` (memecoin and on-chain).

**Leading, all keyless, all verified live on this host:**

| Source | What it measures | Depth verified |
|---|---|---|
| Deribit DVOL | crypto implied volatility | 2,051 daily points, 2021-03-24 → now |
| ^VIX / ^VXN / ^VXD / ^OVX / GVZ / RVX / ^MOVE | implied volatility, US and commodities | 22 daily bars per month |
| Bybit & Binance funding + open interest | crypto positioning | 200 daily OI points, 200 funding points |
| Deribit option book | dealer gamma, option flow | 737 BTC instruments at one call |

**The equity-panel coverage limit:** ^VXN covers only 1,250 of 5,492
panel bars (**22.8%**). Crypto is 96.1%. Any equity result from the
leading layer is a result over the last five years, not the last
twenty.

---

## 9. THE PAPERS: 293 CLAIMS, 80 DIRECTIONAL

`reports/PAPER_CLAIM_INVENTORY.md` enumerates every testable,
falsifiable claim in the six PDFs. Three findings change the build:

1. **The six PDFs are three documents.** GAM ≡ RET pp.6–8, IND ≡ RET
   pp.12–14, RET-1 ≡ RET pp.1–54. Claims are counted once.
2. **Of 293 claims, 80 are directional** — the only kind that can be an
   edge on its own. A gate, a sizing rule, a classifier or a stop
   modifies another signal; it cannot be one.
3. **The package's only SUPPORTED result predates the matrix:**
   `nasdaq_12m_timeseries_momentum` — the canonical 12-month time-series
   momentum. But reading its spec shows it is **`long_only: true`** at
   **`cost_multiplier: 1.0`**, while the paper says *"go long when price
   is above its trend proxy; go short or flat when below"*. **The
   paper's long/short version was never tested.** `leapspace/trend.py`
   now supplies it, and `leapspace/trend.py::sig_pairs_mean_reversion`
   supplies the dollar-neutral pairs construction the paper also
   specifies.

---

## 10. THE KNOWN GAPS

| Gap | State |
|---|---|
| **Order placement / execution** | **none.** No `place_order`, `submit_order` or `execute_trade` anywhere. The kill switch gates a *decision*, not an order. |
| **A validated edge** | 0 of 48 real specs supported. The package can test a claim rigorously; it does not yet have one to trade. |
| **Cross-market replication** | structurally unreachable through the matrix runner (no `alt_universes`). Recorded as SKIPPED on every row rather than hidden. |
| **Equity leading-data coverage** | 22.8% of the panel. The binding constraint is history, not the absence of a source. |
| **Intraday data** | the C7 concept claims the session opening-window drift; the panels are daily, so it runs a stated proxy. |
| **C1's regime classification** | fitted on the whole panel, so the regime boundary is in-sample. Disclosed in every report. |
| **CPU saturation** | four parallel gauntlet runs saturate this host; the shell approval gate times out under load. |

---

## 11. HOW TO RUN IT

```bash
cd C:/Users/HP/AppData/Local/hermes/projects/leapspace-quant

# the architecture diagram, regenerated from the code
python -m leapspace.cli architecture

# the full test suite (26 files, offline)
python -m pytest leapspace/tests -q

# the paper-concept matrix, one concept group at a time
python -c "
from leapspace.paperspecs import build_specs, build_negative_controls
from leapspace import paperrun
s = list(build_specs()) + list(build_negative_controls(build_specs()))
paperrun.run_matrix(s, quick=False, only=['c9_'],
                    out_path='reports/paper_concept_results.json')
"

# the reports, from the stored results
python -c "
from leapspace.paperreport import build_report
from leapspace.backtestviz import build_backtest_dashboard
build_report(); build_backtest_dashboard()
"
```

**CI:** `.github/workflows/ci.yml` has a blocking offline job
(compile, imports, the vendored suite, the validator, the simulator,
and every `test_*.py` with `LEAPSPACE_SKIP_NETWORK_TESTS=1`) and an
informational live job that runs the network-dependent tests for real.
