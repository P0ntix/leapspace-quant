# LIVE CAPITAL READINESS — leapspace-quant

**Assessment date:** 2026-11-03 (package state verified 12:39–13:15 local, during which
the package was being modified concurrently — see §0.3)
**Package:** `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant`
**Question asked:** what stands between this package and usable with real money, and in
what order.
**Answer in one line:** a stage-gated build-out, but stage A cannot start today because
the two decisions that would be traded (the friction-aware simulator, and the new
`signal` decision engine) both have a **broken input path and a silently wrong risk
number** — see §5, which is the whole answer.

---

## UPDATE — 2026-11-04: the paper-concept matrix changes the answer

This assessment was written before the research papers were tested. They now have
been, and the result moves the biggest blocker. **A missing edge is a harder blocker
than a missing order-routing path**, because the order-routing path can be built,
while an edge that does not exist cannot be shipped.

### What was run

Eight testable claims from the five research papers, each coded as a rule and tested
on six asset classes — US equity style, crypto, FX majors, commodities, futures
broad, and rates/credit. Every spec used the **same** risk block (gross 1.0, vol
target 15%, 10% per name, 5 names, net 0.0, monthly rebalance) with costs stressed
to 2× the engine default, so a difference in the result is attributable to the
market rather than to the bookkeeping. Each concept shipped with an
**inverted-polarity negative control**: 48 real specs + 48 controls = 96.

### What came out

| | Real specs | Negative controls |
|---|---|---|
| SUPPORTED | **0** | 0 |
| FRAGILE | 1 | 0 |
| REFUTED | 29 | 30 |
| INCONCLUSIVE | 18 | 18 |
| **actually executed** | **36** | **36** |

* **No concept earned a SUPPORTED verdict.** The single FRAGILE row
  (`c8_liquidity_reversal_crypto`) carries a **negative** OOS Sharpe of −0.19 and a
  negative total return: it is a losing strategy the gauntlet could not cleanly
  reject, not an edge.
* **No negative control survived**, so the validation is discriminating over the 36
  controls that ran. That matters: a matrix without controls would look identical
  whether the concepts were real or invented.
* **The two most promising concepts were never actually tested.** The leading
  volatility risk premium (C2) and the order-flow microstructure base (C7) — 24 rows
  — crashed on implementation bugs, and the runner was reporting those crashes as
  INCONCLUSIVE, which made an implementation failure look like a research finding.
  Both bugs are fixed (the `z`-rebinding crash, and a **genuine look-ahead** in the
  z-score that normalised over the whole panel instead of an expanding window), the
  verdict logic now distinguishes ERROR from INCONCLUSIVE, and the 24 rows are being
  re-run through the full gauntlet.
* **Leading-data coverage is a hard limit on the equity panel.** ^VXN covers only
  1,250 of 5,492 panel bars (22.8%) — 2005–2021 has no implied-volatility data at
  all. Crypto is far better: Deribit DVOL covers 2,049 of 2,132 bars (96.1%).

### What this means for live capital

1. **The "higher upside than downside" claim is not supported.** Nothing survived.
   The package can demonstrate that it can *test* a claim rigorously; it cannot yet
   demonstrate that it has one to trade.
2. **The existing stage gates in §1 are unchanged, and one of them has moved up the
   list.** Stage A (paper trading) still requires the two decisions to have a sound
   input path; but stage A is now pointless for any spec that has not produced a
   SUPPORTED verdict, so **the gate before stage A is: at least one concept must
   survive the full gauntlet, with its control failing.** That gate did not exist
   before this matrix.
3. **The kill switch still has no order path.** `signal.assess_trade` now consults
   the persisted switch and downgrades an ENTER to an AVOID, but there is still no
   `place_order` / `submit_order` / `execute_trade` anywhere in the package, so the
   brake cannot yet stop a real order. This is unchanged from the original
   assessment.
4. **Two new modules make the edge-finding work real rather than rhetorical.**
   `leapspace/leading.py` measures the volatility risk premium from a timestamped
   external series with a one-bar publication lag; `leapspace/cryptoderivs.py`
   measures perpetual-swap funding and open interest from Bybit and Binance, all
   keyless and all with real history. The equity panel's weak coverage is the
   binding constraint there, not the absence of a source.

### The updated gap table rows

| Gap | Before | Now |
|---|---|---|
| A validated edge to trade | not assessed | **measured: none found.** 0 of 48 real specs supported; 24 rows were untested due to bugs now fixed and re-running |
| Negative controls | not present | **present and working.** 48 inverted twins; 36 executed; 0 survived |
| Multi-asset coverage | one market | **six asset classes**, constant risk block, 2× cost stress |
| Leading (forward-looking) data | none | **implemented and live:** DVOL, ^VIX/^VXN/^VXD, funding, open interest, dealer-gamma proxy |
| Portfolio risk beyond diagonal covariance | not implemented | **implemented:** shrunk covariance, equal-risk-contribution sizing, forward-weighted vol, drawdown slope, caps applied last |
| Kill switch on the decision path | not wired | **wired to the decision path**; still has no order path to gate |
| Order placement / execution | none | **still none** |

---

## 0. How to read this document

### 0.1 Sourcing rule used

Every claim below is tagged with the file and function it was verified in. Where I could
not verify something, the row says **UNVERIFIED** rather than guessing. Claims marked
**VERIFIED BY EXECUTION** were produced by running the package on this host during this
assessment; the command and its output are quoted.

### 0.2 The package as measured today

| Measure | Value | Where |
|---|---|---|
| Python modules in `leapspace/` | 47 files | `ls leapspace/*.py` |
| Lines in `leapspace/*.py` | 30,819 | `cat leapspace/*.py \| wc -l` |
| CLI subcommands | 32 | `python -m leapspace.cli --help` (the list ends `…holders, signal`) |
| Test scripts | 21 in `leapspace/tests/` | `ls leapspace/tests/*.py` |
| Backtest specs | 13, all with an intake gate | `leapspace/backtest.py::all_specs`, `apply_intake_gate` |
| Full-gauntlet verdicts on record | 3 (2 SUPPORTED, 1 FRAGILE) | `reports/full_gauntlet_results.json` |
| Wallets passing the consistency gate | **0** | `reports/pepe_priced_edge.json` — all 15 rows `verdict: FLUKE`; `leapspace/state/whitelist.json` — 2 entries, statuses `{RETIRED: 1, FLUKE: 1}` |
| Broker / exchange / order-routing integration | **none** | sweep of `leapspace/*.py` for `place_order|submit_order|send_raw_transaction|sign_transaction|private_key|ccxt|binance|alpaca|kraken` → zero hits outside `chains.py:10` (a comment about `bsc-dataseed.binance.org`, a public RPC host) |

### 0.3 IMPORTANT: the package changed under me during this assessment

`leapspace/signal.py` (a trade-decision engine) did not exist when I started reading;
it appeared at 12:58 local and was wired into the CLI as `signal` while I was reading
it. `leapspace/stats.py` was extracted from `edge.py` at 12:55, and `leapspace/gate_tests.py`
was extracted from `edge.py::evaluate_edge` at 13:05. This document reflects the
**13:15** state. Two of my findings are in code that did not exist at 12:39, so
they are flagged **[NEW CODE, 2026-11-03 12:58]** and should be re-verified against
whatever the module looks like when you read this.

---

## 1. THE STAGE-GATED PATH — A → B → C → D

Dependency order is not arbitrary. Each stage's exit criteria are expressed **in the
package's own vocabulary**, because that vocabulary is the only thing this package has
that a live system would inherit.

### What the package's vocabulary already gives you

| Package term | Where it is defined | Meaning for a gate |
|---|---|---|
| **validation gauntlet** (10 stages) | `strategy-backtest-lab/scripts/btvalidate.py::full_gauntlet` | the pre-trade evidence bar |
| **pooled OOS Sharpe** | `btvalidate.THRESHOLDS["min_oos_sharpe"] = 0.5` | the edge bar |
| **OOS retention** | `btvalidate.THRESHOLDS["oos_retention_min"] = 0.4` | OOS must retain ≥40% of IS Sharpe |
| **profitable-fold fraction** | `btvalidate.THRESHOLDS["min_profitable_fold_frac"] = 0.6` | ≥60% of walk-forward folds must be profitable |
| **Monte Carlo prob(profitable)** | `btvalidate.THRESHOLDS["mc_prob_min"] = 0.85` | the bootstrap profitability floor |
| **cost-stress survival** | `btvalidate.THRESHOLDS["cost_stress_min_x"] = 2.0` | the edge must survive 2× costs |
| **t-stat** | `btvalidate.THRESHOLDS["t_stat_min"] = 2.0` | statistical power |
| **min trades** | `btvalidate.THRESHOLDS["min_trades"] = 30` | trade-count floor |
| **causality audit** | `btvalidate.causality_audit` → hard-fail REFUTED | no look-ahead, ever |
| **intake gate** | `leapspace/backtest.py::apply_intake_gate` | a spec with an unanswered condition is refused, not run |
| **SUPPORTED / FRAGILE / REFUTED / INCONCLUSIVE** | `btvalidate._verdict` | the verdict vocabulary |
| **consistency gate** | `leapspace/edge.py::evaluate_edge` | per-wallet CONSISTENT / WEAK / FLUKE / INSUFFICIENT |
| **Deflated Sharpe bar** | `leapspace/edge.py::ANALYST_CHOICES["min_deflated_sharpe"] = 0.95` (cited: Bailey & López de Prado) | selection-bias bar |
| **independent bets** | `leapspace/edge.py::independent_bets`, `time_disjoint_bets`, `bet_outcomes` | the sample is non-overlapping bets, not raw trades |
| **unknown-N automatic reject** | `leapspace/edge.py::evaluate_edge` — `trials_scanned` defaults to `None` = UNKNOWN = reject | an unscreened claim is refused |
| **kill switch** | `leapspace/riskguard.py::KillSwitch` | code-enforced halt, persists across restart |
| **max drawdown guard** | `KillSwitch.check` — 20% from the rolling window peak, 900 s window | the equity-level stop |
| **liquidity floor** | `KillSwitch.check` — `min_liquidity_usd` 1,000 | "can you get out" |
| **slippage cap** | `KillSwitch.check` — `max_slippage_bps` 500 | observed-vs-modelled slippage gate |
| **rug signals** | `leapspace/riskguard.py::detect_rug_signals`, `rug_signal_details` | LP removal, concentration, collapse |
| **friction model** | `leapspace/friction.py::FrictionModel` (slippage / MEV / failed-tx / latency / fees) | the cost model |
| **finite bankroll, skipped trades recorded** | `leapspace/friction.py::CopyTradeSimulator` | sizing and cash discipline |
| **1% of pool liquidity** | `leapspace/signal.py::leg_liquidity` | position ceiling (ANALYST_CHOICE) |
| **DATA_QUALITY leg** | `leapspace/signal.py::leg_data_quality` | <40% of legs answered → blocking CONFLICT |
| **ENTER / WATCH / AVOID / NO_TRADE_DATA** | `leapspace/signal.py::assess_trade` | the decision vocabulary |

---

### STAGE A — PAPER TRADING (no money, no orders)

**Purpose:** prove that the *decisions the package emits* are reproducible, correctly
sized, and correctly refused when they should be.

**Exit criteria (all must hold):**

| # | Criterion | Threshold | Measured where |
|---|---|---|---|
| A1 | The `simulate` CLI runs | `python -m leapspace.cli simulate --prices P --signals S` exits 0 and prints a ledger | **FAILS TODAY.** `leapspace/quant.py:290` `friction = Friction(**fr)` raises `TypeError: Friction.__init__() got an unexpected keyword argument 'note'` because `operator_config.json`'s `friction` block has a `note` key that `leapspace/models.py::Friction` does not accept. **VERIFIED BY EXECUTION.** |
| A2 | The `signal` CLI runs and emits a brief | `python -m leapspace.cli signal --token <addr> --chain <chain>` writes `reports/briefs/<SYM>_TRADE_BRIEF.md` with `VERDICT`, `ENTRY`, `EXIT`, `POSITION`, `INVALIDATE`, `WHAT COULD NOT BE MEASURED` | **PASSES.** VERIFIED BY EXECUTION on PEPE/ethereum → verdict `WATCH`, confidence `LOW`, position **ZERO**, basis `NOT EVIDENCE-BASED`. |
| A3 | Holder concentration is measured, not assumed | the `HOLDER_RISK` leg's `top10_supply_share` is a real fraction, not `0.0` | **FAILS TODAY.** `leapspace/signal.py::leg_holder_risk` (lines ~615-632) reads `r.get("pct")`, else `r.get("balance")`/`r.get("total")`. `leapspace/memecoinscan.py::fetch_top_holders` on Blockscout returns rows with keys `{address, value, kind, entity, is_contract, is_verified, name}` — **no `pct`, no `balance`, no `total`**. The `except` branch sets `pct = 0.0` for every holder, so the leg reports *"the top 10 holders control 0.0% of the supply; insider-flagged share 0.0%"* and returns **SUPPORTS**. VERIFIED BY EXECUTION on PEPE: `{"source": "blockscout", "holders_read": 50, "top10_supply_share": 0.0, "top1_supply_share": 0.0, "insider_supply_share": 0.0}`. **A live-capital risk control that always reads zero is worse than no control.** |
| A4 | Synthetic data cannot be declared LIVE by assertion | the `simulate` CLI's `--price-provenance` / `--signal-provenance` flags | **FAILS TODAY.** `leapspace/quant.py:302-305` sets `price_provenance="LIVE" if args.price_provenance else "SYNTHETIC"` — a bare boolean, with no verification that the file was live. Worse: `leapspace/friction.py::run_simulation` **mutates the price series with synthetic rug drops even when the caller declares LIVE**, and the disclosure string then says only *"Live data: price series LIVE, signals LIVE."* VERIFIED BY EXECUTION: with `price_provenance="LIVE"`, **8 synthetic rugs of 84–98% were injected** into the series and the equity curve was computed on the mutated series, while `res.price_provenance == "LIVE"` and `res.disclosure == "Live data: price series LIVE, signals LIVE."` |
| A5 | The kill switch is on the decision path | every decision that could lead to an order consults `KillSwitch.check()` before it is emitted | **FAILS TODAY.** `KillSwitch.check()` is called from **nowhere in the package except its own self-test** (`leapspace/riskguard.py:672-729`) and one integration test (`leapspace/tests/check_quant_integration.py:203-216`). `leapspace/quant.py::cmd_risk` only *reads and resets* state. `leapspace/friction.py` does not import `riskguard` at all. `leapspace/signal.py` does not import `riskguard` at all. The kill switch is a well-built component with **no consumer**. |
| A6 | Every paper-derived spec that could ever be traded has a full-gauntlet verdict | no `--quick`-only verdict may reach a decision | The `signal` leg already refuses to treat a quick-only SUPPORTED as evidence (`leapspace/signal.py::leg_research_edge` → `NEUTRAL`, *"look supported under quick validation only — not enough to rely on"*). **PASSES** for the two SUPPORTED specs; **10 of 13 specs are REFUTED or quick-only** (`reports/backtest_results.json`). |
| A7 | Reproducibility | the same token + the same inputs → the same verdict | `leapspace/signal.py` has no seed and no snapshot; DEX state changes between runs. **UNVERIFIED — no test exists** (`leapspace/tests/` contains no reference to `signal`). |
| A8 | Wallets are qualified before their behaviour is used as evidence | `QUALIFIED_WALLETS` leg is `SUPPORTS` for at least one token | **CANNOT PASS YET.** 0 of 15 PEPE top-holder wallets passed; `leapspace/state/whitelist.json` holds 2 entries, `{RETIRED: 1, FLUKE: 1}`. The leg correctly returns `CONFLICTS` — *"NO qualified wallet holds this token"* — and the brief correctly says entry/exit are `NOT EVIDENCE-BASED`. |

**Stage A verdict: NOT ENTERED.** A1, A3, A4 and A5 are hard failures. A1 and A3 are
one-line fixes; A4 and A5 are design work.

---

### STAGE B — SHADOW / LIVE-READ (real data, no orders)

**Purpose:** prove the package's *reads* of the live world match reality, and that it
refuses to act when the data is bad.

**Exit criteria:**

| # | Criterion | Threshold | Notes |
|---|---|---|---|
| B1 | Live-read freshness | every price used in a decision carries an observation age, and a decision is refused when the age exceeds a stated bound | **ABSENT.** `leapspace/signal.py::leg_identity` gets a `Provenance` from `leapspace/market.py::fetch_dex_pairs` but never reads `prov.fetched_at_epoch`; there is no age comparison anywhere in `signal.py` (grep for `age_seconds|age_days|stale|fetched_at` → no hits in that file). |
| B2 | Block-page handling | an HTML block page served with HTTP 200 must never be parsed as data | **MOSTLY OK, WITH ONE HOLE.** `leapspace/http.py::http_json` raises `HttpError` on a non-JSON body — VERIFIED BY EXECUTION with a simulated Sangfor-style `HTTP 200 + <html>` body: it raised `Non-JSON response … Expecting value: line 1 column 1`. **But `http_get` does no shape check at all** — it returned `200 text/html` and the raw bytes. Every PDF path (`leapspace/disclosure.py::fetch_oge_pdf`, `fetch_house_pdf`, `fetch_judicial_text`) goes through `http_get` and then `extract_pdf_text`, which returns `None` for an HTML body and is reported as **"EMPTY TEXT LAYER — image-only PDF, OCR required"** (`disclosure.py:551-556`) — i.e. a network block page is misreported as a document-content fact. The `chains.py` RPC path is safe: `_post_json` → `http_post_json` → `json.loads` → raises on HTML. |
| B3 | Data-quality kill | a decision is refused when the evidence set is too thin | **PRESENT.** `leapspace/signal.py::leg_data_quality`: `<40%` of legs answered → blocking `CONFLICT`; `<70%` → `NEUTRAL` (*"partial coverage, treat the brief as indicative"*). VERIFIED BY EXECUTION (4/7 answered → NEUTRAL). **But it is not a KILL** — a blocking CONFLICT at the DATA_QUALITY level produces `NO_TRADE_DATA`, which is a *verdict*, not a halt. There is no state to latch. |
| B4 | Rate-limit handling | a 429/403 does not silently truncate a scan | **PRESENT AND GOOD.** `leapspace/http.py::http_get` retries 429/500/502/503/504 with backoff and never retries other 4xx; `leapspace/chains.py::EVMClient.rpc` sleeps 6 s × attempt on 403/429; `leapspace/priced.py::_Throttle`, `leapspace/costs.py::_dl_throttle`, `leapspace/etherscan.py::_throttle` all throttle per host. |
| B5 | Per-source failure is visible, not absorbed | a failed source is reported as a gap | **MOSTLY PRESENT.** `leapspace/provenance.py::unavailable` produces a `SOURCE UNAVAILABLE` record; `leapspace/signal.py::_leg_safe` turns any leg exception into an `UNAVAILABLE` leg with the reason. **One absorb:** `leapspace/chains.py::EVMClient.get_logs` returns `[]` on `SourceUnavailable` after 8 recursion levels (line 203-211) — an empty log list is indistinguishable from "no transfers". |
| B6 | Shadow mode runs on a schedule and logs | ≥30 consecutive days of briefs with no data-quality incident | **ABSENT.** No scheduler for `signal`. The only scheduled job is `\HermesCommunitySizeCollector` (Windows Task Scheduler, every 4 h) and the Hermes cron has 4 jobs, none of which touches `signal` (`hermes/cron/jobs.json`). |
| B7 | Venue reconciliation | the package's view of a wallet matches the venue's | **ABSENT, and vacuous** — there is no venue. See §3. |

---

### STAGE C — TINY CAPITAL

**Purpose:** lose a known, small, bounded amount if the machine is wrong.

**Exit criteria:**

| # | Criterion | Threshold | Notes |
|---|---|---|---|
| C1 | A kill switch that actually gates | `KillSwitch.check()` is called on every order path, and its return value can only ever *reduce* trading | Machinery exists (`riskguard.py::KillSwitch.check`, `verify_no_bypass` — VERIFIED BY EXECUTION: `{'ok': True, 'writes': ['reset: self.state.halted = False'], 'violations': []}`). **No consumer.** |
| C2 | The kill switch persists across restart and fails closed | a restarted process must not resume trading; an unreadable state file halts | **PRESENT and strong.** `KillSwitch.load` (line 345): a *missing* file is a clean start; a *corrupt* file calls `self.halt("persisted state … unreadable — failing closed")`. VERIFIED by `riskguard.py::_selftest` steps 5-7. |
| C3 | Drawdown guard is live | 20% from the rolling 900 s window peak halts trading | Machinery present (`KillSwitch.check`, `DEFAULT_MAX_DRAWDOWN_PCT = 0.20`, `DEFAULT_DRAWDOWN_WINDOW_SECONDS = 900`). **Not on any path.** |
| C4 | Fees are accounted, not assumed | realised fees reconcile to modelled fees within a stated tolerance | **MODELS exist, no reconciliation.** `leapspace/friction.py::FrictionModel.total_cost_usd` = slippage + priority fee + gas; the simulator reports `total_fees_usd`, `total_slippage_usd`, `total_mev_usd` in `stats` (line 1067-1069). But `operator_config.json`'s `friction` block ships `priority_fee_usd: 0.0`, `gas_usd: 0.0`, `mev_penalty_bps: 0.0` — VERIFIED BY EXECUTION: `total_cost_usd(1000 notional) = 10.0`, i.e. **only slippage, no gas, no priority fee**. And `cmd_simulate` builds `MEVConfig(max_penalty_bps=0.0, sandwich_probability=0.35)` — VERIFIED BY EXECUTION: the MEV penalty over 200 fills was **0.0** in every case. **The shipped configuration understates execution cost by the entire fee and MEV component.** |
| C5 | Slippage assumption is checked against realised slippage | modelled vs realised slippage compared per fill, with a tolerance | **ABSENT.** `FrictionModel.simulate_fill` applies `apply_slippage` and `apply_mev` (both *modelled*); nothing anywhere records the *realised* fill. `KillSwitch.check` accepts a `slippage_bps` argument that a caller could feed with realised slippage — **no caller does**. |
| C6 | Position sizing uses a stop distance | size = risk budget ÷ stop distance | **PARTIAL.** `leapspace/signal.py::assess_trade` explicitly refuses: *"no evidence-derived stop distance exists, so a risk-based size cannot be computed; this is a CEILING, not a recommendation"*. `leapspace/friction.py` sizes at `equity * size_pct` (line 997) — a fixed fraction, no stop distance. `CopyConfig.stop_loss_pct` exists and is enforced per position in `_trigger_reason` (line 705-716), so a stop *distance* exists in the simulator — it just is not used to size. |
| C7 | Exposure caps are enforced in code | per-asset, per-chain and total-notional caps | **PARTIAL / WRONG LAYER.** The friction simulator has `max_open_positions` (5) and `size_pct` (10%) — but the shipped `operator_config.json` names them `max_concurrent_positions: 10` and `position_pct: 0.1`, and `cmd_simulate`'s filter (`{k: v for k, v in ct.items() if k in CopyConfig.__dataclass_fields__}`) **drops both**. VERIFIED BY EXECUTION: config says `max_concurrent_positions = 10`; the simulator actually runs with `max_open_positions = 5`. The `leapspace/signal.py::leg_liquidity` 1%-of-pool rule is a **brief annotation, not an enforced cap** — nothing prevents an order larger than 1% of the pool. |
| C8 | Live-decision refusal under bad data | a blocking CONFLICT must actually block the trade, not merely relabel it | **PARTIAL.** `assess_trade` precedence (line ~690-730) does put a blocking CONFLICT first → `AVOID`, and `leg_holder_risk` can set `blocking=True` on insider share >10% or top-10 >50%. But A3 shows the concentration inputs are currently zero, so **the block would not fire**. |
| C9 | Exposure is capped by realised liquidity, not quoted | a position must be sized against the pool you can actually exit through | `leg_liquidity` uses `identity.metrics["liquidity_usd"]` — DexScreener's quoted pool liquidity, i.e. the same number `KillSwitch`'s `min_liquidity_usd` floor is compared against. No depth/spread model exists. |

---

### STAGE D — SCALED CAPITAL

**Purpose:** run real money at size without a single unknown.

**Exit criteria:**

| # | Criterion | Threshold |
|---|---|---|
| D1 | Multi-asset | ≥2 chains live, ≥3 assets, ≥90 days of tiny-capital operation, no kill-switch trip that was not the intended one |
| D2 | Drawdown | realised max drawdown ≤ the modelled 20% (`KillSwitch.DEFAULT_MAX_DRAWDOWN_PCT`) and the kill switch's 900 s window trips *before* the strategy's own max DD is exceeded |
| D3 | Statistical | pooled OOS Sharpe ≥ 0.5 (`btvalidate.THRESHOLDS["min_oos_sharpe"]`), OOS retention ≥ 40%, ≥60% of walk-forward folds profitable, Monte Carlo prob(profitable) ≥ 85%, edge survives 2× cost stress — **measured on the LIVE fills**, not on the historical backtest |
| D4 | Cost realism | modelled slippage + fees + MEV within the realised band on every fill; the shipped `operator_config.json` friction block must carry real values, not zeros |
| D5 | Wallet evidence | at least one wallet with a `CONSISTENT` verdict from `edge.evaluate_edge`, a `trials_scanned` count that is real, and an independent-bet count ≥ 5 — because until then the package's own entry/exit references are `NOT EVIDENCE-BASED` by construction |
| D6 | Operational | the whole loop survives a restart with the halt state intact, a source outage, a rate-limit storm, and a block page |

---

## 2. THE GAP TABLE — now → A/B/C/D

"**Machinery present, not wired**" means the code exists in this package and only needs
connecting. "**Genuinely absent**" means it must be built.

| # | Gap | Why it matters | What closes it | Machinery |
|---|---|---|---|---|
| G1 | `cmd_simulate` crashes: `Friction(**fr)` gets `note` | the friction simulator — the only path to a simulated P&L — cannot be run from the CLI at all | filter the config dict to `Friction.__dataclass_fields__` the way `CopyConfig`/`RugConfig` already are (`quant.py:295, 291`) | **Present, not wired** (one-line) |
| G2 | `leg_holder_risk` reads `pct`/`balance`/`total`; Blockscout returns `value` → concentration always 0.0% | a blocking risk control reads zero on every token | map `value` ÷ total supply, or use the `alloc_pct` path in `memecoinscan.py`; and **fail closed** when the field is absent rather than defaulting to 0.0 | **Present, not wired** (the data is there) |
| G3 | `run_simulation` injects synthetic rugs even when the caller declares LIVE, and the disclosure still says "Live data" | a live-capital P&L could be computed on a synthetic-mutated series and labelled live | only inject when the caller asks for a stress test; make `price_provenance` and `rug_config` mutually exclusive; make the disclosure mention injected events regardless of provenance | **Present, not wired** |
| G4 | `--price-provenance` / `--signal-provenance` are unverified booleans | any operator can label a hand-made file LIVE | derive provenance from the fetch that produced the data, or require a signed/attested manifest | **Genuinely absent** (needs a provenance-carrying input format) |
| G5 | `KillSwitch.check()` has **no consumer** | the package's strongest asset — a code-enforced, restart-surviving, AST-audited halt — guards nothing | call `check()` inside `signal.assess_trade` and inside the (future) order path; persist after every trip | **Present, not wired** |
| G6 | No order-placement path of any kind | there is literally nothing that could spend money | build a venue adapter, a signer, a fill reconciler — **and decide whether you want that at all** | **Genuinely absent** |
| G7 | No realised-vs-modelled slippage comparison | every cost figure in the package is a *model*; nothing checks the model | capture the realised fill price against the decision price and store the delta; feed it to `KillSwitch.check(slippage_bps=…)` | **Genuinely absent** |
| G8 | Shipped friction has `priority_fee_usd: 0.0`, `gas_usd: 0.0`, `mev_penalty_bps: 0.0` | the package's own cost model says the friction of a memecoin trade is 1% slippage and nothing else. On-chain, gas alone is often >1% | populate real values per chain, from the chain's own fee data; make `MEVConfig.max_penalty_bps` non-zero so the sandwich branch is live | **Present, not wired** |
| G9 | `operator_config.json` names `position_pct` / `max_concurrent_positions`; `CopyConfig` wants `size_pct` / `max_open_positions` | the operator's stated risk limits are silently dropped. Verified: config 10 concurrent, simulator runs 5 | rename the config keys to match, or map explicitly in `cmd_simulate` | **Present, not wired** |
| G10 | No data-freshness/staleness check on any decision input | a 2-hour-old price looks identical to a live one | compare `Provenance.fetched_at_epoch` against a per-source max age; refuse or downgrade | **Genuinely absent** |
| G11 | No kill condition on data quality that *latches* | a thin-data decision is a verdict, not a stop; the next call re-decides | promote a DATA_QUALITY failure into `KillSwitch.halt(trigger="data_quality")` | **Present, not wired** (`KillSwitch.halt` exists) |
| G12 | No reconciliation against venue balances | the package's belief about a wallet's holdings is never checked against the venue | a per-chain balance reconcile against the venue's own API, run on every cycle | **Genuinely absent** |
| G13 | `http_get` does no content-type/shape check | a Sangfor-style HTTP 200 + HTML block page is returned as a successful fetch; the PDF paths then report it as "EMPTY TEXT LAYER — OCR required" | add a `Content-Type`/magic-byte assertion to `http_get`; make `extract_pdf_text` distinguish "not a PDF" from "no text layer" | **Present, not wired** (`http_json` already does the JSON equivalent) |
| G14 | `EVMClient.get_logs` returns `[]` on `SourceUnavailable` | an RPC outage is indistinguishable from "no transfers" — a wallet looks inactive when it was unreachable | raise, or return a tagged empty-with-reason | **Present, not wired** |
| G15 | No exposure cap per asset / per chain in code | `leg_liquidity`'s 1%-of-pool rule is a *label on a brief*, not a limit | enforce the caps in the sizing function and refuse an order that breaches them | **Present, not wired** (the number exists) |
| G16 | No correlation / portfolio-level limit | the friction simulator holds `max_open_positions` positions with no regard for whether they are the same bet | a correlated-exposure check: memecoins share one risk factor (the package's own `time_disjoint_bets` already encodes this idea for the wallet gate) | **Genuinely absent** |
| G17 | No order-size limit beyond `size_pct` | a single order can be sized at 10% of equity with no cap relative to the pool it must exit through | cap notional at min(1% of pool liquidity, X% of equity) in code | **Present, not wired** |
| G18 | No scheduler for the decision loop; `signal` has no test | Stage B requires 30 days of briefs; nothing produces them | a cron/task that runs `signal` on a watchlist and appends to a ledger; a test file | **Genuinely absent** |
| G19 | Zero wallets have passed the consistency gate | the package's own entry/exit references are `NOT EVIDENCE-BASED`; the `QUALIFIED_WALLETS` leg is a permanent `CONFLICT` | screen a large unbiased universe via `launchscan` (the NEW-meme path), report `trials_scanned` honestly, and let `edge.screen_universe` compute PBO over the whole screened set | **Present, not wired** (`screen_universe` has **no caller** — verified: `grep screen_universe leapspace/` finds only its own definition) |
| G20 | The walk-forward / Monte Carlo evidence is 100% historical | the gauntlet says nothing about live fills | re-run the gauntlet against the shadow ledger from Stage B | **Present, not wired** |
| G21 | `operator_config.json` `friction`/`copy_trade` blocks are POLICY but read as SETTINGS | `operator_config.json` line 74 discloses the fee basis requirement; nothing enforces that a risk figure computed on modelled fees is labelled net-of-fees everywhere | tag every risk figure with its fee basis | **Present, not wired** |
| G22 | 10 of 13 specs are REFUTED or quick-only | only 2 specs carry a full-gauntlet SUPPORTED | nothing to close — this is a *finding*, not a gap | n/a |
| G23 | `leapspace/state/kill_switch.json` does not exist | the switch has never been tripped or armed in production | created on first `save()` | **Present, not wired** |

---

## 3. RISK-CONTROL REQUIREMENTS — PRESENT / PARTIAL / ABSENT

Each row is a control a live system needs, with the evidence.

| Control | Status | Evidence |
|---|---|---|
| **Kill switch — does it cover all order paths?** | **PRESENT as a component / ABSENT as a control** | `leapspace/riskguard.py::KillSwitch` is genuinely strong: `check()` (line 227) returns `(allowed, reason)` and every subsequent call is blocked while halted; the halt is persisted (`save`, line 332) and reloaded (`load`, line 345); a corrupt state file **fails closed**; `reset(by, reason)` refuses an empty actor or reason; `_GuardedKillState.__setattr__` raises `PermissionError` on any `halted = False` outside `reset()`; `verify_no_bypass()` re-derives the guarantee from the module's own AST. VERIFIED BY EXECUTION: `python -m leapspace.cli risk` → `bypass audit: {'ok': True, 'writes': ['reset: self.state.halted = False'], 'violations': []}`. **BUT it covers ZERO order paths, because there are zero order paths.** `KillSwitch.check()` is called from **only** `riskguard.py::_selftest` and `tests/check_quant_integration.py`. `leapspace/friction.py` and `leapspace/signal.py` do not import `riskguard` at all. It is a dead code-enforced brake. |
| **Position sizing** | **PARTIAL** | `friction.py::CopyTradeSimulator._decide` sizes at `equity * size_pct` (line 997) — fixed fraction, **no stop distance**, so it is not risk-based. `signal.py::assess_trade` returns `risk_per_trade_pct` and a liquidity ceiling but explicitly says *"no evidence-derived stop distance exists, so a risk-based size cannot be computed; this is a CEILING, not a recommendation"* — and returns `position_usd: 0.0` for any verdict that is not ENTER. `CopyConfig.stop_loss_pct` is enforced per-position (`_trigger_reason`, line 705), so a stop *distance* exists in the simulator but is never used to size. **And the operator's own sizing config is dropped** — see G9. |
| **Max drawdown guard** | **PRESENT as a component / ABSENT as a control** | `KillSwitch.check()` compares equity to the **rolling-window** peak (900 s) and trips at `max_drawdown_pct` 0.20; per-token overrides via `token_rules`. `riskguard.py::_selftest` step 2 proves the trip, step 3 proves every later call is blocked. **No caller.** The friction simulator computes `max_drawdown_pct` *after the fact* (`_result`, line 1063) and does nothing about it — it reports the damage, it does not stop the run. |
| **Max exposure per asset** | **PARTIAL** | `signal.py::leg_liquidity` computes `max_position_usd = liquidity_usd * 0.01` (labelled ANALYST_CHOICE) and CONFLICTS if `target_usd > max_pos`. But this is a **field in a brief**, not a cap in an order path. `friction.py` has no per-token notional cap beyond `size_pct` and `max_open_positions`. |
| **Max exposure per chain** | **ABSENT** | No chain-level exposure concept anywhere. `CopyTrade` carries `chain` (`models.py`) and `friction.py::_skip` records it, but no limit is computed from it. `signal.py` assesses one token on one chain per call. |
| **Correlation / portfolio limits** | **ABSENT** | `grep -rE "correlation|covariance|max_gross|exposure_limit"` over `leapspace/` returns only `crosschain.py::timing_correlation` (identity linking, not risk) and `regime.py`'s "diagonal covariance" comment. `friction.py` opens up to `max_open_positions` positions with **no regard for whether they are the same underlying bet** — and the package already knows this failure mode: `edge.py::time_disjoint_bets` exists precisely because *"two bets held simultaneously in different tokens are correlated — every memecoin shares one risk factor"*. The wallet gate applies that insight; the simulator does not. |
| **Order-size limits** | **PARTIAL** | `MIN_TRADE_USD = 1.0` (`friction.py:85`) is a *floor* (below it the trade is skipped as "funds locked"). `max_open_positions` (5 effective, config says 10 — dropped). `size_pct` 10%. No notional cap relative to pool depth in code. `signal.py`'s 1% rule is advisory. |
| **Slippage assumptions vs realised** | **ABSENT** | The model applies `FrictionModel.apply_slippage` (line 203) and `apply_mev` (line 215) — both *modelled*. There is no realised fill anywhere to compare against, because there is no venue. `KillSwitch.check` accepts a `slippage_bps` parameter that *would* accept a realised value — **no caller passes it**. The `btengine` backtest charges costs analytically too (`btengine.py::DEFAULT_COSTS`, crypto = 10 bps commission + 5 half-spread + 5 slippage + 30 borrow). |
| **Fee accounting** | **PARTIAL (models exist, values are zero)** | `FrictionModel.total_cost_usd` = slippage-on-notional + priority fee + gas; `CopyTradeSimulator._result` reports `total_fees_usd`, `total_slippage_usd`, `total_mev_usd`. `operator_config.json` ships `priority_fee_usd: 0.0`, `gas_usd: 0.0`, `mev_penalty_bps: 0.0`. VERIFIED BY EXECUTION: `total_cost_usd(1000 notional) = 10.0` — i.e. slippage only. `cmd_simulate` builds `MEVConfig(max_penalty_bps=0.0, sandwich_probability=0.35)`; VERIFIED BY EXECUTION: the MEV penalty was **0.0 across 200 fills** — the sandwich branch is inert. `btengine` charges non-zero costs (its `cost_stress` stage proves the edge survives 2× costs), so the two cost models in this package disagree. |
| **Rate-limit handling** | **PRESENT** | `http.py::http_get` retries only 429/500/502/503/504 with `backoff * (attempt+1)`; `chains.py::EVMClient.rpc` sleeps 6 s × attempt on 403/429 (a public host refusing needs a longer pause than a blip); `chains.py::SolanaClient.rpc`, `onchain.py::get_transaction`, `holders.py`, `priced.py::_Throttle`, `costs.py::_dl_throttle`, `etherscan.py::_throttle` all throttle. RugCheck rate-limits are documented and a fallback path exists. |
| **Data-freshness / staleness checks** | **PARTIAL** | `http.py::CachedFetcher` records `fetched_at_epoch` and re-fetches when older than `max_age_seconds`; `cli.py::_fetcher()` sets 3600 s; `Provenance.disclosure()` renders "Cached data — originally fetched {ts}". `btengine` refuses to fill on a stale bar (`panel.stale`, `stale_skips`). **But `signal.py` never checks age** — grep for `fetched_at|stale|age_seconds` in `signal.py` → no hits. A brief can be built from a cached or an old DEX quote with no age in the output. |
| **Kill condition on data quality** | **PARTIAL** | `signal.py::leg_data_quality` grades the evidence set: `<40%` answered → **blocking CONFLICT** → `NO_TRADE_DATA`; `<70%` → `NEUTRAL`; else `SUPPORTS`. VERIFIED BY EXECUTION (4/7 → NEUTRAL). **But it does not latch**: it changes the verdict, not the state. A `KillSwitch.halt(trigger="data_quality")` would latch and survive restart. |
| **Reconciliation against venue balances** | **ABSENT** | `grep -rE "reconcil"` over `leapspace/` → **zero hits**. There is no venue to reconcile against. The closest thing is `chains.py::fetch_wallet_trades` (derives a wallet's transfers from logs) and `etherscan.py` balance reads — but nothing compares the package's internal position ledger to an external source of truth. |
| **Data source down / block page (Sangfor NGAF: HTTP 200 + HTML)** | **PARTIAL — one hole, and it is in the PDF path** | `http.py::http_json` **fails closed**: VERIFIED BY EXECUTION with a simulated `HTTP 200 + <html>` body, it raised `HttpError: Non-JSON response … Expecting value: line 1 column 1`. So every JSON endpoint (DexScreener, RugCheck, Jupiter, Discord, Etherscan, RPC via `http_post_json`) correctly rejects a block page. **`http_get` does not check**: VERIFIED BY EXECUTION it returned `200, text/html, <html>…`. `disclosure.py::fetch_oge_pdf` (line 418) / `fetch_house_pdf` / `fetch_judicial_text` then call `extract_pdf_text` on the HTML, which returns `None`, and the note becomes **`"text_layer=EMPTY"`** / **"EMPTY TEXT LAYER — image-only PDF, OCR required"** (line 551-556). **A blocked fetch is reported as a document-content fact.** `social.py::fetch_telegram_size` is the one place that gets this right for HTML: it requires `_TG_VIEW_RE` (`<title>Telegram: View @`) and otherwise reports `not_a_channel_or_absent` — and the package's own docs call that out as *"the validity trap"*. `chains.py::chain_health` catches the exception and records `UNREACHABLE` with the reason, which is right. `report_memecoin.py` already names the general hazard in its gaps section: *"On this host a blocked host can answer HTTP 200 with an HTML block page."* — **but that is a documented gap, not a fix.** |

**Summary of §3:** of 13 controls, **3 are PRESENT** (kill switch as a component, rate-limit
handling, and the JSON-side block-page defence), **7 are PARTIAL**, **3 are ABSENT**
(per-chain exposure, correlation limits, venue reconciliation). And the single most
damning fact: **the kill switch and the drawdown guard are the two best-engineered
components in the package and neither has a consumer.**

---

## 4. THE SIMULATED-DATA QUESTION — exhaustive

### 4.1 Every synthetic / simulated / demo / placeholder site

| # | Site | What is synthetic | Can it reach a live-capital decision? |
|---|---|---|---|
| S1 | `leapspace/viz.py::run_demo_simulation` (line 463) | A **hard-coded** price series — `prices = [(1700000000 + i*3600, 1.0 + 0.01*(i%17) - 0.002*i) for i in range(160)]` — and 24 `WalletTrade` signals with `provenance="SYNTHETIC"`. Runs the **real** friction model, rug injector, MEV simulator and finite-bankroll logic over it. | **NO — but it is the most dangerous item on this list.** It is labelled: the docstring says *"The inputs are SYNTHETIC"*, `price_provenance="SYNTHETIC"` and `signal_provenance="SYNTHETIC"` are passed (line 501), `run_simulation` then sets `result.disclosure` to the `SYNTHETIC_DATA` string, and the chart title reads *"Copy-trade simulation — friction-aware [prices SYNTHETIC, signals SYNTHETIC]"* (`viz.py:322-325`). **However**, `build_dashboard` (line 559) calls it **unconditionally** and puts it on the dashboard as *"Copy-trade simulation"*, whose card note says *"Synthetic inputs, labelled as such on the chart."* The chart PNG itself is embedded in a self-contained `dashboard.html` that also contains the LIVE chain/token tables. **The label is in the chart title, not in the filename, not in the JSON, and not in the dashboard's own card title.** A reader who screenshots the card loses the label. **Recommend:** rename the card and the file to carry `SYNTHETIC` in the name, and emit the disclosure into the JSON payload. |
| S2 | `leapspace/friction.py::RugInjector` (line 346) / `RugConfig` | Injects 80–99% drops and liquidity-vanish events into a historical series at `rug_probability` (shipped 0.05) / `liquidity_vanish_probability` (0.02), seed 42. `operator_config.json` says so: *"Injected rug events are SYNTHETIC by construction and every injection is logged with its before/after price so the output is auditable."* | **YES, INDIRECTLY — this is the item to fix.** Every injection IS logged (`RugEvent` carries `before_px`, `after_px`, `drop_pct`, `detected_as_rug`), but `run_simulation` **injects them unconditionally when a `rug_config` is supplied**, and `cmd_simulate` always supplies one. VERIFIED BY EXECUTION: with `price_provenance="LIVE"` declared, **8 synthetic rugs of 84–98%** were injected into the series, the equity curve was computed on the mutated series, `res.price_provenance == "LIVE"`, and `res.disclosure == "Live data: price series LIVE, signals LIVE."` — **the disclosure says nothing about injected events.** A live-capital P&L could be computed on a synthetic-mutated series and labelled live. **Fix:** make `rug_config` and `price_provenance="LIVE"` mutually exclusive, and make the disclosure mention injected events regardless of provenance. |
| S3 | `leapspace/friction.py::MEVSimulator` / `MEVConfig` | Randomised sandwich penalty, `sandwich_probability` 0.35 in `cmd_simulate`. | **NO today — inert.** VERIFIED BY EXECUTION: `operator_config.json` ships `mev_penalty_bps: 0.0`, so `cmd_simulate` builds `MEVConfig(max_penalty_bps=0.0, …)`, and the penalty was **0.0 across 200 fills**. But note the *mechanism* is synthetic-by-construction: `apply_mev` samples uniformly in [0, max]. When real values are entered, the penalty becomes a **model**, not a measurement — and nothing will ever compare it to a realised sandwich. **Label it as a model in any P&L it touches.** |
| S4 | `leapspace/friction.py::CopyConfig.provenance` / `SimulationResult.provenance` (defaults `SYNTHETIC`) and `run_simulation`'s `price_provenance`/`signal_provenance` defaults (`SYNTHETIC`) | The *defaults* are honest. | **NO — the defaults are correct.** `run_simulation` sets `result.disclosure` to the `SYNTHETIC_DATA` string when either input is SYNTHETIC, else `"Live data: price series {p}, signals {s}."` |
| S5 | `leapspace/quant.py::cmd_simulate`'s `--price-provenance` / `--signal-provenance` flags (line 302-305, 1041-1046) | **None** — they are bare booleans. | **YES — THIS IS A HOLE.** `--price-provenance` flips `price_provenance` to `"LIVE"` for **any** input file, with no verification that the file came from a live fetch. The flag's own help text says *"declare the price series LIVE (it came from a real source) rather than the default SYNTHETIC"* — i.e. it is an **assertion**, not a check. A hand-made price file plus this flag produces an artefact labelled LIVE. **This is the one place in the package where synthetic data can be laundered into a live-capital artefact by a single flag.** |
| S6 | `leapspace/data/operator_config.json` — the "seed data" | **There is no seed DATA.** I checked: `grep -nE "0x[0-9a-fA-F]{6,}" leapspace/data/operator_config.json` → **zero address literals**. The `seed` values (42 in `rug`, 42 in `copy_trade`) are **RNG seeds**, not market data. What the config *does* contain is (a) **empty registries**: `registries.deployers/cabals/exchanges/insiders` are all `[]`, with the note *"the CABAL, EXCHANGE and INSIDER registries remain hand-maintained and are EMPTY by default — the anti-insider filter can only exclude a wallet it has been told about"*; and (b) the **policy** blocks `friction`, `copy_trade`, `kill_switch`, `rug`, `thresholds`, `consensus`. | **The registries: YES, and this is a live-capital hazard.** `profiler.py::is_insider` reports `unknown` for every funding source when the lists are empty — *"unknown funding source is not a clean bill of health"*. The empty `deployers` list is partially mitigated: `leapspace/deployers.py` DERIVES deployers on-chain (one live entry in `leapspace/state/deployer_registry.json`: BONK's deployer `4A7UsK17…`, cross-checked against RugCheck, no mismatch) — and it **honestly records two gaps**: PEPE and BRETT both aborted after 2 calls because the host refused, and it states *"a creation block is NOT reported, because a partial search yields a WRONG block"*. So the **cabal / exchange / insider registries are empty and nothing else fills them.** Before any capital goes near a token, those must be populated or the anti-insider filter must be treated as *inert*. **The friction/copy_trade policy blocks: YES** — they set the slippage, fee, rug and sizing assumptions that every simulated P&L inherits, and they currently say *zero fees* (see §3). |
| S7 | `leapspace/friction.py::_synthetic_series` (line 1173), `_synthetic_signals` (1188), `_synthetic_market` / `_synthetic_signals_multi` (1213, 1230) | The self-test fixtures. | **NO.** Self-test only (`friction.py::_selftest`, line 1300+). |
| S8 | `leapspace/friction.py::_selftest` "RUN 2" (line ~1377-1395) | A "live-market" simulation built on synthetic signals. | **NO.** Its own output prints: *"SYNTHETIC (generated by this self-test), so its trade list is labelled SYNTHETIC and must not be read as a live strategy result."* |
| S9 | `leapspace/tests/check_quant_integration.py` (lines 134-190) | Synthetic prices + signals, `price_provenance="SYNTHETIC"`, `signal_provenance="SYNTHETIC"`. | **NO.** It even asserts the disclosure: *"synthetic data is disclosed"*. **Caveat:** this test file **timed out at 180 s** when I ran it — I could not verify it passes today. **UNVERIFIED.** |
| S10 | `leapspace/tests/test_regime.py::synthetic_market` (line 23) | A seeded regime-switching price series. | **NO.** Docstring: *"SYNTHETIC — test fixture only."* |
| S11 | `leapspace/tests/test_pbo.py` (line 129 "Synthetic fixtures (deterministic seeds throughout)") | `dominant_matrix(seed=…)`, `noise_universe(seed=…)` — synthetic candidate universes for PBO. | **NO.** The PBO module itself (`leapspace/pbo.py`) operates on whatever matrix it is given; the fixtures are the test's, not the module's. |
| S12 | `leapspace/tests/test_socialedge.py` (line 40) | A synthetic community-size series 40→1200 members over 48 h, plus synthetic holder series. | **NO.** Line 580 prints *"Data source: SYNTHETIC fixtures (offline section) and LIVE…"*. |
| S13 | `leapspace/tests/demo_socialedge.py` (lines 74-76) | A synthetic community-size + holder series. | **NO.** Labelled at line 76: *"SYNTHETIC: a community-size + holder series (labelled)"*. |
| S14 | `leapspace/costs.py` self-test (lines 1213-1237, 1366-1405) | SYNTHETIC data with an explicit disclosure, plus one LIVE leg. | **NO.** `provenance: "SYNTHETIC + LIVE"`, `disclosure: SYNTHETIC_DISCLOSURE`. |
| S15 | `leapspace/crosschain.py` self-test (lines 1103-1225) | SYNTHETIC profiles with a known answer. | **NO.** `provenance: SYNTHETIC`, `disclosure: SYNTHETIC_DISCLOSURE`. |
| S16 | `leapspace/report_memecoin.py` — the `ALLOWED_PROVENANCE` gate | The *report* module permits a section to declare `SYNTHETIC`. | **NO in production, and there is a test asserting it.** `leapspace/tests/test_report_memecoin.py` (lines 112-115) asserts *"no section is marked SYNTHETIC"*. That is exactly the right guard. |
| S17 | `leapspace/data/_raw/cg_coin_*.json` (~40 files under `data/_raw/`) | Archived CoinGecko raw payloads. | **NO.** Not referenced by any `leapspace/*.py` (verified by grep). These are *real* archived data, not synthetic. |
| S18 | `leapspace/data/free_data_sources.json`, `chain_registry.json`, `consistency_criteria.json`, `leapspace_2_0_specs.json`, `source_reliability.json` | Real derived registries and specs. | **NO.** No synthetic data. |
| S19 | `leapspace/state/holder_series/`, `leapspace/state/social_series/` | **Collected** real series (the community-size collector runs every 4 h). | **NO.** This is the opposite problem: the *series* is real but *thin*, and `signal.py` has no lead-time measurement (the skill states *"Not a lead-time measurement"*). |
| S20 | `leapspace/state/whitelist.json` / `qualified_pool.json` | Real gate outcomes. | **NO.** Both are all-FLUKE / RETIRED — the honest state. |
| S21 | `reports/backtest_results.json` (13 rows) and `reports/full_gauntlet_results.json` (3 rows) | **Real** backtest runs against **real** Yahoo data via the imported `btengine`/`btvalidate`. | **NO.** But note `backtest_results.json` still carries the **quick-run** verdicts for 10 of 13 specs — its `skipped_stages` reads `["montecarlo","sweep","replication"]` for **every row**, including the two SUPPORTED ones. `full_gauntlet_results.json` is the stricter artefact, and `signal.py::leg_research_edge` reads **both** and only counts a spec as SUPPORTED when the *full-gauntlet* file says so. That is the correct design. |
| S22 | `.fingerprint.py` (package root) and `reports/_probe_one.py` | Scratch scripts. `.fingerprint.py` prints a numeric fingerprint of `norm_cdf`/`norm_ppf`/`binomial_tail_p` across three modules to prove they agree after the `stats.py` extraction. `reports/_probe_one.py` is a one-wallet probe. | **NO.** Both are developer scratch, not part of the package's output. **Recommend deleting or moving them out of the package root** — `.fingerprint.py` at the root of a package that holds a `.secrets.env` is the kind of file that gets committed by accident. |

### 4.2 Items that could be mistaken for real data in an output artefact

Ranked by how likely a mistake is:

1. **`simulation.png` / the "Copy-trade simulation" dashboard card** (S1). The label is in the *chart title*, not in the filename, not in the JSON, and not in the card's own heading. It sits on a dashboard that also carries LIVE chain/token tables. **The card title and the file name should say SYNTHETIC.**
2. **A `simulate` run with `--price-provenance`** (S5). The provenance field says LIVE; the truth is "the operator said so". Nothing in the artefact distinguishes an attested LIVE series from an asserted one.
3. **A `simulate` run on a LIVE-declared series with rugs injected** (S2). The disclosure says *"Live data: price series LIVE, signals LIVE."* and the injected 84–98% drops are absent from the disclosure (they are in `result.rugs`, which the CLI *does* print as *"INJECTED RUG EVENTS — SYNTHETIC by construction"* — but the JSON artefact carries them under a `rugs` key with no provenance field).
4. **`leg_holder_risk`'s "top 10 holders control 0.0% of the supply"** (§3, G2). This is not synthetic data — it is a **real** number that is **wrong**. It reads as a clean bill of health on a token whose top-10 actually control a large share. **This is the one that could get money lost.**
5. **`reports/full_gauntlet_results.json`'s note on `v1_crypto_momentum_20d_ma`** — *"Monte Carlo probability of profit 81%, below the 90% bar"*. The actual bar in `btvalidate.THRESHOLDS["mc_prob_min"]` is **0.85**, not 0.90. The note is wrong; the verdict (FRAGILE) is right. Minor, but it is a stated threshold that does not match the code.

### 4.3 What is NOT synthetic and is therefore safe

Everything in `leapspace/provenance.py`'s `LIVE`/`CACHE` tier: Yahoo OHLCV, Nasdaq option chains, DexScreener, RugCheck, Jupiter, Blockscout, Etherscan V2, Discord invite counts, Telegram previews, the public RPCs, the archive RPCs. The price-at-a-past-block method (`priceatblock.py`, Uniswap V2 reserves read at the trade's own block) is real and independently checked (PEPE 2024-01-01 $1.2370e-06 vs reference $1.29e-06, 4.1% error).

---

## 5. THE HONEST VERDICT

### What this package IS

A **research and signal-generation instrument**, and a good one.

- It **imports** the `strategy-backtest-lab` engine rather than reimplementing it, and its own `apply_intake_gate` runs the lab's intake gate on every spec — a spec with an unanswered condition is *refused*, not backtested. That is unusual discipline.
- It runs a **13-spec gauntlet** and reports the unflattering verdicts: 10 of 13 specs are REFUTED or quick-only. It records that `v1_crypto_momentum_20d_ma` was SUPPORTED under `--quick` and **downgraded to FRAGILE** by the full gauntlet (Monte Carlo prob(profitable) 81%). A package that publishes its own downgrade is one you can trust about the other numbers.
- It has a **real consistency gate** (`edge.py`) whose DSR bar is the cited 0.95, whose sample size is **independent bets and not raw trades**, whose unknown-N is an **automatic reject**, and whose verdict precedence binds a fluke before an insufficiency. And it applied that gate to its own headline finding: **15 of 15 PEPE top-holder wallets scored FLUKE.** The headline result of this package is *"the wallets that made money on the winner are not demonstrably skilled"* — and the package proves it on its own data rather than claiming otherwise.
- It **labels its own thresholds** by authority (`ANALYST_CHOICE` vs cited), refuses to present an analyst choice as a paper result, and keeps the paper registry honest: the seven source "papers" are LLM synthesis transcripts with **no numeric performance results**, so every backtest number is independent evidence, not a reproduction.
- It has **one genuinely production-grade component**: `riskguard.py::KillSwitch` — code-enforced, restart-surviving, corrupt-state-fails-closed, AST-audited for bypasses, `reset(by, reason)`-only. Most packages would not have this. This one does not use it.

### What this package IS NOT

**It is not a trading system.** Not "not quite ready" — structurally, categorically:

- **There is no order path.** No adapter, no signer, no venue client, no fill, no position ledger. A sweep of `leapspace/*.py` for `place_order|submit_order|send_raw_transaction|sign_transaction|private_key|ccxt|binance|alpaca|kraken` returns zero hits.
- **The kill switch has no consumer.** `KillSwitch.check()` is called from its own self-test and one integration test. The friction simulator does not import `riskguard`. The decision engine does not import `riskguard`. **The brake is not connected to anything.**
- **The friction-aware simulator cannot be run from the CLI.** `leapspace/quant.py:290` raises `TypeError` on the shipped config.
- **The shipped cost model says a memecoin trade costs 1% and nothing else.** `priority_fee_usd: 0.0`, `gas_usd: 0.0`, `mev_penalty_bps: 0.0` → `total_cost_usd(1000) = 10.0`, and the MEV penalty was 0.0 across 200 fills. On a real chain, gas alone routinely exceeds the entire modelled cost.
- **The operator's own risk limits are silently discarded.** `operator_config.json` says `max_concurrent_positions: 10`; the simulator runs with 5, because the config keys do not match the dataclass fields and the CLI filters unknown keys away without a warning.
- **The decision engine's holder-concentration control reads 0.0% on every token** and returns SUPPORTS, because the Blockscout field names do not match what it looks for.
- **Zero wallets have passed the consistency gate**, so by the package's own logic every entry and exit reference is `NOT EVIDENCE-BASED` and every position size is zero. The engine is honest about this — it says *"A system that manufactures an entry level when no profitable account exists is a system that will lose money with great confidence"* — but it means **the package currently has no tradable edge to trade.**
- **All three candidate strategies are cross-sectional/slow**, and the strongest one (`regime_switch_cross_sectional_sector_rotation`) needs dispersion to select from — it works as a *selection rule* on a multi-asset equity universe, not as a memecoin entry.
- **The research edge and the wallet edge are not the same thing.** `signal.py` is explicit: the research leg *"establishes a non-random PRIOR for the rule — it is not a live signal and not permission to trade it"*, and only the qualified-wallet leg *"can set a price level, because it is the only leg derived from accounts that actually made money."* With 0 qualified wallets, **the only leg that can price anything is empty.**

### THE SINGLE BIGGEST THING THAT IS MISSING

**A venue: order placement, fill capture, and reconciliation against venue balances.**

Everything else is a wiring or a bug. Without a venue there is no realised slippage to compare the model against (G7), no real fee to check the fee model against (G8), no realised P&L to re-run the gauntlet against (G20), no venue balance to reconcile the internal ledger against (G12), and no way for the kill switch to have an "order path" to cover (G5, the one that makes the kill switch mean anything). Every other gap in §2 is a prerequisite for or a consequence of this one.

**But note the sequencing consequence, because it is the uncomfortable truth:** the biggest missing thing is also the thing you should build **last**, not first. Building a venue adapter on top of (a) a simulator that crashes, (b) a risk control that reads zero, (c) a cost model that says fees are zero, and (d) zero qualified wallets would produce a *machine that can lose money quickly* rather than one that can make it slowly. **The venue is last; the wiring is first.**

And the honest corollary: **even with a perfect venue, this package has no demonstrated edge to trade.** The wallet layer has zero survivors; the strategy layer's 3 supported specs are slow cross-sectional rules on equities, tested on Yahoo daily bars. If the goal is memecoin trading from wallet behaviour, **the qualified-wallet cohort is the whole game, and it is currently empty.**

---

## 6. WHAT TO BUILD NEXT — prioritized

Sized **small** (<1 day, one file, no new dependencies), **medium** (1–3 days), **large** (>1 week).

### NEXT 1 — SMALL — Fix the four defects that make today's numbers wrong

`leapspace/quant.py:290` (filter the config dict like `CopyConfig`/`RugConfig` already do) ·
`leapspace/signal.py::leg_holder_risk` (map Blockscout's `value` ÷ total supply; **fail closed** when the field is missing, never default to `0.0`) ·
`leapspace/friction.py::run_simulation` (make `rug_config` and `price_provenance="LIVE"` mutually exclusive; put injected events in the disclosure) ·
`leapspace/quant.py::cmd_simulate` (rename or map `position_pct`→`size_pct`, `max_concurrent_positions`→`max_open_positions`; **warn loudly** on any dropped config key rather than filtering silently).

**Why first:** each is small, each currently produces a *confident wrong number*, and each is a prerequisite for trusting anything downstream. The `leg_holder_risk` bug is the urgent one — it is a risk control that always passes.
**Done when:** `python -m leapspace.cli simulate --prices … --signals …` exits 0; `leg_holder_risk` on PEPE reports a non-zero top-10 share; a `--price-provenance` run with rugs configured is refused or labelled.

### NEXT 2 — SMALL — Wire the kill switch onto the decision path

Call `KillSwitch.check(equity_usd, ts, liquidity_usd, slippage_bps)` inside `signal.assess_trade` **before** it emits a verdict, and `KillSwitch.halt(trigger="data_quality")` when `leg_data_quality` returns a blocking CONFLICT. Persist on every trip.

**Why:** the package already contains a genuinely excellent brake and a genuinely excellent data-quality grader. Connecting them is small work with an outsized payoff, and it is the *precondition* for the kill switch meaning anything at all. It also creates the state file (`leapspace/state/kill_switch.json`) that Stage B needs.
**Done when:** a deliberately thin-evidence token produces a latched halt that survives a restart, and `verify_no_bypass()` still reports `ok: True`.

### NEXT 3 — MEDIUM — Make provenance a property of the data, not an assertion

Retire the `--price-provenance` / `--signal-provenance` booleans. Price/signal files become self-describing: every row carries `{ts, px, source, fetched_at, source_url, provenance}` and the loader **derives** the provenance. Synthetic fixtures are marked at creation and cannot be relabelled. Add a `Content-Type`/magic-byte assertion to `http.py::http_get`, and distinguish "not a PDF" from "no text layer" in `disclosure.py::extract_pdf_text`.

**Why (ties to your goal "accurate data fast"):** this is the *accuracy* half of your stated objective, and it is currently one boolean away from being a lie. It also closes the Sangfor block-page hole at the one place it is still open (the PDF path), and it removes the only route by which synthetic data reaches an artefact labelled live.
**Done when:** no input file can be labelled LIVE by a flag; a `HTTP 200 + <html>` body is rejected at the HTTP layer, not parsed.

### NEXT 4 — MEDIUM — Build the shadow ledger (Stage B proper)

A scheduled runner (Windows Task Scheduler, as `\HermesCommunitySizeCollector` already does — zero model tokens) that runs `signal` over a watchlist every N minutes and appends each brief to a JSONL ledger: the verdict, every leg, the evidence fractions, the DEX pair address, the liquidity at decision time, the pool snapshot. Plus the missing tests for `signal.py` (there are none — `leapspace/tests/` contains no reference to it) and for `edge.screen_universe` (also no caller).

**Why:** you cannot stage-gate on evidence you do not collect. Stage B's exit criteria in §1 are all *measurements*, and today nothing produces them. This is also where the first realised-vs-modelled slippage data comes from — compare the ledger's DEX quote at decision time against the quote at a fixed horizon later, per pair.
**Done when:** 30 consecutive days of briefs with no unexplained gaps and no data-quality incident.

### NEXT 5 — MEDIUM — Populate the wallet layer, or accept that it is empty

This is the user's third stated goal: *"quantifying entry/exit of genuinely profitable wallets."* Right now the answer is **zero wallets qualify.** Two routes:
- **Scale the NEW-meme path.** `launchscan.early_buyers` finds insiders *by construction* (the first buyer in the launch window was the deployer, same block). Screen many launches, build the full candidate matrix, and run `edge.screen_universe` over it — which is the **only** place PBO can be computed correctly, and it currently has **no caller**. Report `trials_scanned` honestly; the DSR bar then does its job.
- **Or scale the OLD-meme path** with a bias-free universe (the current PEPE top-holder list is survivorship-selected, and the gate already has the `survivorship_selected_universe` rejection test to say so — it lives in `leapspace/gate_tests.py` as of the 13:05 extraction; before that it was inside `edge.py::evaluate_edge`).

Also: **populate the empty cabal / exchange / insider registries** (`operator_config.json::registries`). They are `[]`. Until they are not, `profiler.is_insider` reports `unknown` for every funding source and the anti-insider filter excludes nobody.

**Why:** the decision engine's own logic says the qualified-wallet leg is the only one that can set a price level. A trading system with no qualified wallets has no entry or exit to learn from, and the honest output — `WATCH`, position `ZERO`, `NOT EVIDENCE-BASED` — is the package working correctly, not a bug to route around.
**Done when:** at least one wallet reaches `CONSISTENT` with a **real** `trials_scanned` and ≥5 independent bets, and the whitelist records the evidence.

### NEXT 6 — LARGE — Only then: the venue

A venue adapter + signer + fill capture + balance reconciliation, behind the kill switch. **Build it last.** When you get there, the design constraints are already written by the package itself: `KillSwitch.check()` on every order path (G5); the 1%-of-pool-liquidity ceiling enforced in code rather than printed on a brief (G15); per-chain and correlated-exposure caps that use the `time_disjoint_bets` insight the wallet gate already encodes (G16); a realised-vs-modelled slippage feed into `check(slippage_bps=…)` (G7); and a reconcile against venue balances on every cycle (G12).

**Why:** a venue adapter built on a crashing simulator, a zero-reading risk control, a zero-fee cost model and zero qualified wallets is a machine that loses money fast. The gate on Stage C exists precisely to make that sequence impossible.

---

## 7. WHAT I COULD NOT VERIFY

| Item | Why |
|---|---|
| `leapspace/tests/check_quant_integration.py` | **timed out at 180 s** on this host during this assessment. Its assertions are unverified. |
| `leapspace/tests/test_pbo.py`, `test_socialedge.py`, `test_report_memecoin.py`, `check_intake_gate.py`, `check_source_reliability.py` | not executed during this assessment — read, not run. |
| Whether `signal.py` and `cmd_extra.py::cmd_signal` were still in the same state at the moment you read this | the package was being modified **during** this assessment (`signal.py` appeared at 12:58, `stats.py` at 12:55). Everything about those two modules is **[NEW CODE, 2026-11-03 12:58]**. |
| Behaviour of `signal.py` against a *live* Solana token with a real holder cohort | only exercised against PEPE/ethereum and a bogus address in this assessment. |
| Whether `edge.screen_universe` produces a sane PBO on real data | it has no caller and no live candidate matrix. |
| Any venue-specific behaviour | there is no venue. |

---

*Assessment only. No code was modified, refactored or rewritten. The only files this
assessment created are this document and three scratch artefacts under
`C:\Users\HP\AppData\Local\hermes\cache\scratch\` (outside the package). Two files were
written into the package by the `signal` CLI during verification:
`reports/briefs/PEPE_TRADE_BRIEF.md|.json`.*
