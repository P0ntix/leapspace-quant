# leapspace-quant

Automation built from the seven LeapSpace research papers supplied by the user.

**Location:** `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\`

Pure Python standard library. No new packages were installed (the host's C:
drive is at 97% full). The backtesting engine is the existing
`strategy-backtest-lab` skill's `btengine`/`btvalidate`, imported rather than
reimplemented, so its invariants and self-tests remain the authority.

---

## Quick start

```bash
cd "C:/Users/HP/AppData/Local/hermes/projects/leapspace-quant"

python -m leapspace.cli regime     --symbol SPY
python -m leapspace.cli gamma      --symbol QQQ
python -m leapspace.cli memes      --query BONK
python -m leapspace.cli wallet     --address <SOLANA_ADDRESS>
python -m leapspace.cli disclosure --oge-names Powell,Mullin
python -m leapspace.cli alerts     --symbol QQQ --gamma-symbol QQQ --all
python -m leapspace.cli backtest   --quick
python -m leapspace.cli report     --quick
```

Add `--json` to any command for machine-readable output.

---

## The seven papers and what each one drives

| Paper | Module | What was implemented |
|---|---|---|
| Financial market regime identification | `regime.py`, `backtest.py` | Gaussian HMM, 3–5 states, vol/trend/drawdown/liquidity features; regime-conditioned momentum↔reversal switching |
| NASDAQ market regime identification | `regime.py`, `gamma.py`, `alerts.py` | The four-axis intraday framework's *testable daily proxy*; gamma sign as the damp/amplify regime; the paper's own execution mapping as ACTION alerts |
| Options market dynamics and volatility | `gamma.py` | Dealer net gamma, max-pain, zero-gamma strike; exposure-adjusted (delta/vega/notional) option flow |
| Free trading indicators for directional edge | `backtest.py` | RSI + volume-confirmation spec (price → volume → one momentum filter, no indicator stacking) |
| Trading strategies for retail traders (v1) | `backtest.py` | Crypto 20-day MA momentum; Nasdaq 12-month TSM; the 1.0–1.5 SD volatility-band mean reversion |
| Trading strategies for retail traders (2.0) | `specs_2_0.py` + `leapspace/data/leapspace_2_0_specs.json` | Six specs distilled from the PDF: crypto MA-20 momentum, Nasdaq 12-month TSM, crypto SD-band reversion, Bollinger-20/2 breakout, volume-confirmed cross-sectional momentum, RSI-14 oversold fade |
| Meme coin trading strategies | `memecoin.py`, `onchain.py` | The five-layer screen (narrative / structural safety / exit quality / survival / manipulation); wallet clustering and concentration |

### Two defects the 2.0 distillation caught

Both produced a plausible-looking but wrong backtest, which is why they are
recorded here rather than quietly fixed:

1. The Bollinger spec originally used `threshold: 0.0`. `bollinger_pct` is
   **already SD-normalised**, so "> 0" only means "above the SMA" and never
   tested the ±2 SD band the paper specifies — it produced results
   *byte-identical* to the moving-average spec. The threshold is now 1.0,
   which is the +2 SD upper band.
2. The RSI spec uses `direction: -1` on the `rsi` feature. The engine's
   threshold signal emits only 0 or +1, so `RSI < 30` is untestable on a
   0–100 scale without inverting the feature first.

---

## Backtest results

Real Yahoo data. `--quick` skips Monte Carlo, the parameter sweep and
replication; the full gauntlet runs were done separately on the SUPPORTED
specs and are marked.

| Strategy | Paper | Verdict | Validation | Trades | Sharpe | OOS Sharpe | OOS folds |
|---|---|---|---|---|---|---|---|
| `regime_switch_cross_sectional_sector_rotation` | regime | **SUPPORTED** | full gauntlet | 2,089 | 0.61 | 0.53 | 5/5 |
| `nasdaq_12m_timeseries_momentum` | 2.0 | **SUPPORTED** | full gauntlet | 71 | 0.63 | 0.90 | 4/5 |
| `v1_crypto_momentum_20d_ma` | v1 | **FRAGILE** | full gauntlet | 1,328 | 0.75 | 0.78 | 3/5 |
| `v1_sd_band_mean_reversion_1_0_1_5` | v1 | REFUTED | --quick | 496 | 0.36 | 0.29 | 4/5 |
| `tradingview_price_volume_rsi_regime_filtered` | directional edge | REFUTED | --quick | 179 | 0.40 | 0.33 | 5/5 |
| `bollinger20_2_breakout_crypto` | 2.0 | REFUTED | --quick | 654 | 0.66 | 0.43 | 3/5 |
| `crypto_rsi_oversold_fade` | 2.0 | REFUTED | --quick | 636 | 0.47 | 0.28 | 4/5 |
| `crypto_ma20_trend_momentum` | 2.0 | REFUTED | --quick | 1,169 | 0.48 | 0.33 | 2/5 |
| `sd_band_mean_reversion_crypto` | 2.0 | REFUTED | --quick | 974 | −0.66 | −0.55 | 2/5 |
| `crypto_xs_momentum_volume_confirmed` | 2.0 | REFUTED | --quick | 2,018 | −0.21 | −0.15 | 2/5 |
| `v1_nasdaq_12m_tsm_vol_scaled` | v1 | REFUTED | --quick | 166 | −0.10 | −0.38 | 0/5 |
| `regime_switch_momentum_reversal_us_equity` | regime | REFUTED | --quick | 80 | 0.03 | −0.08 | 1/5 |
| `regime_switch_momentum_reversal_nasdaq_scalp_proxy` | NASDAQ | REFUTED | --quick | 637 | −0.12 | 0.12 | 4/5 |

`--quick` skips Monte Carlo, the parameter sweep and replication, so those
rows are a preliminary read for those stages. The consolidated report marks
every row with its validation level and never presents a quick verdict as
though it were a full one.

## The intake gate

The backtest lab's `intake.validate_spec()` runs on **every** spec before the
engine sees it, and `run_spec` refuses a spec with an unanswered condition
(verdict `INCONCLUSIVE`, not a backtest). The gate compares each probed field
against the engine's `DEFAULT_SPEC` — a field still holding the engine's value
counts as unanswered unless it is recorded in `intake.accepted_defaults`.

Your research papers are the specification source, so the rule here is:

| Provenance source | Treatment |
|---|---|
| `paper` | supplied — the paper states it |
| `analyst_choice` / `engine_default` and coinciding with an engine default | a deliberate, documented acceptance, recorded with its reason |
| *no provenance entry at all* | **missing — the spec is refused** |

Three probed conditions cannot be expressed by the engine's spec schema and
need an explicit documentation entry (`_PROVENANCE_ADDITIONS` in
`backtest.py`): `direction` (a regime-conditional signal is long/short, but
`long_only=false` equals the default), `exit` (a regime-conditional or
cross-sectional signal has no `signal.params.exit`), and `universe` (a spec
that picks the engine's own default preset is indistinguishable from a
default).

`leapspace/tests/check_intake_gate.py` proves the gate is not decorative: it
strips a provenance entry and asserts the gate **refuses** the spec. Run it
after touching the gate.

## Source reliability of the papers themselves

The seven LeapSpace documents are **literature-synthesis transcripts, not
research papers** — LLM answers to ~26 retail-trader questions against a
retrieved corpus. Reading them surfaced defects in the source material. The
register lives in `leapspace/data/source_reliability.json` and renders as
section 4 of the report.

**15 defects, 6 high severity.** The load-bearing ones:

| ID | Finding | Impact |
|---|---|---|
| **D2** | **Zero numeric performance results in either document** — no Sharpe, win rate, CAGR or drawdown anywhere | The papers cannot calibrate, validate or rank anything. **Every backtest number in this package is independent evidence, not a reproduction of a published result.** |
| **D7** | The word *"rebalance"* appears **zero times** in v1 | Every rebalance cadence here is an analyst choice, tagged as such |
| **D1** | Citation numbers are **section-scoped and collide** — 38 numbers in v1, 34 in 2.0 map to different papers in different sections | A resolver must key on `(section, reference_number)`. This package cites by section and quoted phrase, so it is unaffected |
| **D3** | v1 §9 **mis-cites an on-chain Bitcoin paper** (Grobys, Näsman & Sandretto 2026) as support for US-equity intraday options-flow and gamma claims, at stated Confidence **High** | Those §9 claims are unsupported by their own citation — the clearest sign the section's confidence rating is uncalibrated |
| **D4** | v1 §10 is a **self-citing regeneration** — 14 literal `[turn 9 summary]` citations stand in for real references | §10's uncited items are prior-conversation assertions, not evidence |
| **D5** | Duplicate references within a section (260 entries → 187 unique DOIs) | Naive entry counts overstate evidence breadth by ~39% |

**Verified: no spec depends on a defective or retracted section.**
`leapspace/tests/check_source_reliability.py` cross-checks every paper
section the 13 specs quote against the register's defective sections and
asserts the intersection is empty. The affected material is the
intraday/scalping and on-chain sections, none of which are implemented.

### Sections deliberately not implemented

| Section | Why not | To enable it |
|---|---|---|
| **charm / vanna** | The papers' own subtitle promises them; the body says they are *"not directly tested… would be an inference rather than a directly supported finding."* The subtitle contradicts the body | Live per-strike dealer-side OI plus a stated net-charm/net-vanna sign convention |
| **on-chain feature set** | Ranked #2 by the papers but never operationalized — "active users, hashrate, wallet activity, transaction volume" with no lookbacks or thresholds. A ranking is not a specification | A definition, lookback and threshold per feature, plus a hashrate/active-user source |
| **intraday scalping stack** | Needs opening range, CVD, premium flow, value-area/POC and 0DTE greeks — no Level-2, no trade-by-trade CVD, no intraday greeks here, and CBOE is unreachable (Yahoo options 401) | A paid intraday feed plus a session bar builder. The 5–15 min opening range, value-area %, CVD divergence rule and premium-flow convention would all still need values |
| **pairs / cointegration** | The papers' reversion model is a *pair* model; the engine has no pair construction, no s-score, no hedge-ratio estimator, no pair screen. The SD-band specs compute single-name price z-scores — a weaker question, recorded in each spec's `additional_conditions` | Pair universe + formation window, a cointegration test, a hedge-ratio estimator, a Hurst cutoff |
| **gamma computation spec** | The papers give the gamma **sign** rule but no strikes, expiries, OI source, dealer sign or magnitude threshold | Live per-expiry dealer-side OI, which no free endpoint provides |

## How to read this

Only two strategies survived out-of-sample with the
stages that ran. The strongest finding is not a strategy but a *structural*
one:

- The regime-switch strategy **works only as a cross-sectional selection
  rule** (sector rotation). On a broad-ETF universe it degenerates into
  market timing and dies on costs (Sharpe 0.03, OOS −0.08).
- The paper's own guidance predicts this: the edge is in *choosing between*
  momentum and reversal by regime, which requires dispersion to select from.
- Two momentum variants that look almost identical on paper behave very
  differently out of sample — the Nasdaq 12-month TSM (OOS retention 163%)
  passes while the crypto MA-20 variant (OOS retention 41%) fails. Horizon
  and asset class matter more than the indicator.
- `v1_crypto_momentum_20d_ma` was SUPPORTED under `--quick` but the full
  gauntlet **downgraded it to FRAGILE** (Monte Carlo prob(profitable) 81%).
  That is the gauntlet doing its job.

SUPPORTED means "warrants paper trading" — never "trade it".

---

## Data sources (all verified live from this host)

| Source | Used for | Status |
|---|---|---|
| Yahoo chart API | OHLCV for equities, ETFs, crypto | live (browser UA required — default urllib UA gets HTTP 429) |
| Nasdaq option chain API | Option chains with **open interest and volume** per contract | live; **delayed**, OI is a snapshot |
| Deribit public API | Crypto option instruments, book, trades | live, no key |
| CoinGecko | Crypto spot prices | live, no key |
| DexScreener | DEX pairs, liquidity, volume, buys/sells | live, no key |
| Jupiter token API (`lite-api.jup.ag`) | Holder count, mint/freeze authority, organic score, audit | live, no key |
| RugCheck API | Top holders with **insider flags**, risk score, risks | live, no key |
| Solana public RPC | Wallet signatures, transactions, token accounts | live, no key; rate-limits under bursts |
| Helius (optional) | Same, with DAS + enhanced transactions | needs `HELIUS_API_KEY` |
| House Clerk | Annual FD + PTR index and PDFs | live |
| OGE REST API | Executive 278e / 278-T index and PDFs | live |
| JEFS | **Primary** judicial database | TCP-unreachable + registration-gated from here |
| SCOTUS mirrors | Judicial filings | live, labelled **secondary** |
| `*.senate.gov` | Senate eFD | **HTTP 403 geo-block** from this host |

---

## Provenance rules (the user's hard requirement)

Every datum carries a `Provenance` record:

- **LIVE** — fetched during this run.
- **CACHE** — served from disk; the record keeps the ORIGINAL fetch time and
  source, so a cache hit is never presented as fresh.
- **SYNTHETIC** — generated for self-tests only. It always carries the
  disclosure string *"SYNTHETIC DATA — generated by leapspace.selftest /
  synthetic fixtures. This is NOT market data and must never be used to make
  trading decisions."*

An unreachable source produces an **unavailable-source record**, never a
default, an estimate or a plausible-looking number.

### Threshold disclosure

Every threshold used by the alerts and screens lives in a single table with
its own provenance:

- `alerts.ALERT_THRESHOLDS` — alert thresholds.
- `memecoin.THRESHOLDS` — meme-coin screen thresholds.

Each entry says whether the value is a **paper** statement or an
**analyst_choice**, and quotes the paper text that justifies it. Nothing is
presented as a paper result when it is not.

---

## Strategy specs and their parameter provenance

`backtest.REGIME_SWITCH_SPECS` holds every spec. Each carries a
`parameter_provenance` block where **every** parameter is tagged:

```json
"momentum_lookback": {
  "source": "analyst_choice",
  "note": "The paper names 'medium-horizon return or moving-trend feature' without a window. 60 trading days ≈ one quarter. NOT stated in the paper."
}
```

`source` is one of:

- `paper` — the source states it; `citation` gives the section.
- `analyst_choice` — the source does **not** state it; the note says what was
  chosen and why.
- `engine_default` — the backtest engine's own default.

When a paper's rule could **not** be encoded (a per-position trailing stop, a
volatility cutoff, a two-level entry band), that is recorded as a gap in
`parameter_provenance` rather than approximated away.

---

## Backtesting

`backtest.run_spec()` runs the `strategy-backtest-lab` gauntlet:

- walk-forward out-of-sample with purged, embargoed, **disjoint** folds
- cost stress (1×/1.5×/2×/3×) and gross-of-costs decomposition
- parameter-sensitivity sweep, Monte Carlo, subperiod/regime split, capacity
- cross-market replication (when alternative universes are supplied)
- **causality audit** — every feature must reproduce on truncated data

Verdicts: `SUPPORTED` / `FRAGILE` / `REFUTED` / `INCONCLUSIVE`, with flags
always reported. A partial run names the stages it skipped.

### Engine extensions (registered, not patched)

The paper-specific features and signals are registered onto the engine's
registries at runtime, so the skill's own files and self-test stay intact:

- `regime_momentum_score` (feature) — the raw trailing return.
- `regime_switch` (signal) — soft-posterior regime switching, market-wide
  regime, position size = posterior probability.
- `regime_switch_cross_sectional` (signal) — the cross-sectional selection
  reading: long the strongest names in trend states, the weakest in stress
  states.
- `rsi_volume_confirmation` (signal) — RSI as the momentum filter with volume
  confirmation.

**Known limitation, disclosed in every report:** the HMM's parameters are
fitted on the whole panel, so the regime *classification* is in-sample even
though the *filter* is causal. A walk-forward refit would be cleaner and is
the obvious next step.

---

## Meme-coin paper coverage — audited, not assumed

`leapspace/memecoin.py` implements the meme-coin paper's five layers.
`MEME_PAPER_COVERAGE.md` maps every clause to its implementation, and the
audit is **executable**:

```
python leapspace/tests/check_meme_paper_coverage.py
```

It reads the actual source and verifies the code behind every claim,
exiting non-zero if a claim has no code. Current state: **18 of 26
clauses implemented**, 3 proxy-only, 3 partial, **2 missing**.

**Four clauses had no implementation when the audit was first run.** All
four now have real sources:

| Paper clause | Now implemented via |
|---|---|
| "fewer than 2% reach major DEXs… focus on predicting migration/survival" | `memecoin.fetch_migration_evidence` — distinct-DEX count, `MAJOR_DEXES` presence, `launchpad_origin` (pumpswap / raydium-launchlab, **plus** RugCheck `market_types` because BONK's `pump_fun_amm` is invisible to the DEX list), and Jupiter's `firstPool.createdAt` |
| "one-sided liquidity" (Layer 2) | RugCheck stable liquidity ÷ total market liquidity |
| "suspicious wallet clustering" (Layer 2) | RugCheck `graphInsidersDetected` — its own wallet-graph cluster count. Live: WIF 7,195 / BONK 48 |
| "slippage" (Layer 3) | a constant-product price-impact **estimate**, labelled as such and explicitly a lower bound |
| "accelerating attention" (Layer 1) | Jupiter's `birdeye-trending` tag plus `stats24h` buy/sell volume, volume change and holder change |

The launchpad funnel was the important one. A screener that only sees
tokens already on a DEX is scanning the surviving 2% — the opposite of
what the paper says the edge is.

**Still missing (2):** niche-community vs generic-trend classification (no
free source labels a token "generic"), and abrupt ownership changes
(needs a holder-composition time series).

**Beyond the paper:** mint/freeze authority and LP locks are implemented as
disqualifiers, but the paper says its evidence does not cover them [29] —
so the audit labels that `REAL (beyond the paper)`.

## On-chain memecoin quant layer

Built for the four-quadrant operator brief (`OPERATOR_BRIEF.md`, verbatim,
with a clause→code map and the deviations documented).

```
python -m leapspace.cli chains      # live reachability + token snapshots
python -m leapspace.cli profile     # wallet vs the four thresholds
python -m leapspace.cli consensus   # N profiled wallets on one token
python -m leapspace.cli pool        # trusted wallet pool + derived deployers
python -m leapspace.cli simulate    # friction-aware copy-trading simulation
python -m leapspace.cli risk        # the code-enforced kill switch
python -m leapspace.cli anomaly     # anomaly log + Known Unknowns
python -m leapspace.cli audit       # look-ahead / survivorship / overfitting
python -m leapspace.cli viz         # charts + HTML dashboard
```

### Live-verified sources (free, no API keys)

`*.publicnode.com` JSON-RPC for Ethereum / Base / BSC / Arbitrum, the
Solana public RPC, DexScreener, RugCheck, Jupiter. **certifi is
required** — the Windows CA store mis-validates several chains. A GET to
any RPC URL returns HTML, not JSON; you must POST.

All five chains verified live on 2026-11-02 (solana slot 464,497,105 ·
ethereum block 26,327,060 · base 53,416,166 · bsc 131,239,121 ·
arbitrum 520,564,120). BONK $0.000002856 / $289,596 liquidity · PEPE
$0.000004869 / $31.5M · BRETT $0.004284 · CAKE $1.89.

### The rules, implemented exactly

| Rule | Where |
|---|---|
| ≥30 trades, ≥55% win rate, PF ≥1.5, <40% PnL from one trade | `profiler.profile_wallet` |
| Anti-insider funding-source filter | `profiler.trace_funding_source`, `is_insider` |
| Consensus: ≥N wallets on one token within window T | `profiler.consensus_signal` |
| Trusted-pool re-evaluation | `profiler.TrustedPool.re_evaluate` |
| Slippage / latency / priority fees / failed tx | `friction.FrictionModel` |
| Finite bankroll, skipped trades logged | `friction.CopyTradeSimulator` |
| Rug injection (80–99% drops) | `friction.RugInjector` |
| MEV / sandwich penalty | `friction.MEVSimulator` |
| Look-ahead / survivorship / overfitting audit | `biasaudit.audit_spec` |
| Code-enforced kill switch | `riskguard.KillSwitch` |
| Anomaly log → Known Unknown | `riskguard.AnomalyLog` |

**Profit factor and win rate are computed on REALISED round trips**, with
buys and sells matched FIFO per token. A sell that cannot be matched to a
buy in the observed window is excluded, not counted as a loss.

### Honest limits — read these before trusting a profile

- **No historical memecoin prices from a free endpoint.** On-chain wallets
  therefore have no prunable round trips: win rate and profit factor come
  back `None` and the wallet is disqualified for *lack of evidence*. That
  is the correct answer. Supply a `price_lookup` to a real price history
  to make the thresholds meaningful.
- **EVM deployer derivation is blocked from this host** — publicnode
  refuses `eth_getCode` (403) partway through the binary search. The
  registry records the gap and the search **aborts** on an errored call,
  because a partial search yields a confidently wrong block. Solana
  derivation works and cross-checks against RugCheck.
- **The cabal / exchange / insider registries ship empty.** The CLI says
  so on every run. An empty registry cannot exclude anyone, and "unknown
  funding source" is not a clean bill of health.
- **A wallet with too little history is INSUFFICIENT, not passing.** The
  profile says so; it is never padded to look good.
- **True streaming is unavailable** on free endpoints. The models
  normalise events and support an event-driven consumer, but the polling
  interval is real and visible rather than implied.

### The bias auditor audits this package too

`leapspace/biasaudit.py` reports **29 real findings** against this
package's own 13 specs — including survivorship on every crypto spec,
because a preset universe of today's large liquid coins contains only
survivors by construction. That is a true finding about this package,
not a false positive, and it is reported rather than buried.

## Visual report

`python -m leapspace.cli viz` builds `reports/charts/` — five PNG charts
plus a self-contained `dashboard.html` (images inlined as data URIs, so it
is one portable file):

- `verdicts.png` — in-sample vs out-of-sample Sharpe for all 13 specs,
  coloured by verdict.
- `walkforward.png` — OOS Sharpe and fold profitability per strategy.
- `equity.png` — real engine equity curves with an underwater drawdown
  panel.
- `simulation.png` — the friction-aware copy-trade simulation with rug
  events marked.
- `chains.png` — live chain reachability and token liquidity.

The dashboard applies the full-gauntlet overlay before charting. Without
it the dashboard showed a quick-run SUPPORTED where the markdown report
showed the stricter FRAGILE verdict — two artefacts disagreeing about the
same strategy.

Charts follow the `trading-visualization` skill's dark theme and palette
(green profit, red loss, blue neutral, amber warning). matplotlib,
numpy, pandas, plotly and mplfinance are already installed with Hermes —
nothing needs downloading.

## Alerts

`alerts.AlertEngine` collects three categories and renders them with the
paper, threshold, source and provenance of each:

- **PRICE** — drawdown bands, volatility expansion, regime transitions (with
  posterior probabilities), gamma-state flips, option-flow pressure.
- **INFORMATION** — US officials' disclosures across all three branches, with
  the asset and value band; on-chain wallet clustering, self-trades and
  holder concentration; meme-coin screen outcomes.
- **ACTION** — the papers' own execution mapping: follow vs fade, reduce
  size, stand aside, and the reason (gamma state / regime posterior).

`alerts.py --save` persists fingerprints so a quiet tick is silent.

---

## US officials' financial disclosures — three branches

`disclosure.py` covers the branches and the law that requires each:

| Branch | Regime | Primary source | Coverage here |
|---|---|---|---|
| Legislative | House annual FD + PTR (STOCK Act) | `disclosures-clerk.house.gov` | **full** — 1,805 filings indexed, PDFs parsed |
| Legislative | Senate eFD | `efdsearch.senate.gov` | **blocked** — HTTP 403 geo-rule on all `*.senate.gov`; reported as a source gap, never as "no filings" |
| Executive | OGE Form 278e / 278-T (5 CFR 2634) | `extapps2.oge.gov` | **full** |
| Judicial | AO Form 10 (5 USC 13101-13111) | JEFS `pub.jefs.uscourts.gov` | **primary unreachable** (TCP + registration gate); 45 filings from labelled **secondary** mirrors |

Parsing notes that matter:

- House PDFs use a **custom glyph encoding** — all-caps labels extract as IPA
  code points. `disclosure.HOUSE_GLYPH` reverses it. Asset names, tickers,
  amounts and dates are clean ASCII.
- OGE's `length` is **silently capped at 100** — the index is paged in steps
  of 100 and the row count asserted.
- Some OGE rows are "Request this Document" and have **no public PDF**.
- Some judicial periodic-transaction PDFs are **image-only** (empty text
  layer) and need OCR.

`disclosure.analyse_market_impact()` measures what the market did after a
disclosure date (1/5/20 trading days vs SPY) and returns caveats stating
that a single disclosure is an anecdote, not a demonstrated market effect.

---

## Tests

```bash
cd "C:/Users/HP/AppData/Local/hermes/projects/leapspace-quant"
python leapspace/tests/test_regime.py          # 27 checks, offline
python leapspace/tests/test_gamma_live.py QQQ   # live option chain
python leapspace/tests/test_onchain_live.py     # live Solana RPC
python leapspace/tests/test_disclosure_live.py  # live House + OGE + judicial
python leapspace/tests/test_backtest_run.py --quick
```

---

## Files

```
leapspace/
  provenance.py   every datum carries where it came from
  http.py         stdlib HTTP: browser UA, retries, gzip, disk cache
  regime.py       Gaussian HMM regime identification
  market.py       OHLCV, option chains, crypto prices, DEX pairs
  gamma.py        dealer gamma exposure + exposure-adjusted option flow
  onchain.py      Solana wallet tracking, clustering, concentration
  memecoin.py     the five-layer meme-coin screen
  disclosure.py   three-branch US officials' disclosures + market impact
  backtest.py     paper-derived specs + the validation gauntlet
  alerts.py       price / information / action alerts
  cli.py          the orchestrator
reports/          backtest reports + JSON artifacts
data/cache/       HTTP cache
state/            alert fingerprints
```

---

## Multi-chain coverage (added 2026-11-03)

The package now screens **10 memecoin networks by measured DEX volume**,
with L1 and L2 **token networks kept separate**. `landscape` prints it.

| # | Chain | Layer | Token network | 24h DEX volume | Source |
|---|-------|-------|---------------|----------------|--------|
| 1 | Ethereum | L1 | ethereum | $1,189,207,436 | DefiLlama `total24h` |
| 2 | Solana | L1 | solana | $905,602,298 | DefiLlama `total24h` |
| 3 | BNB Smart Chain | L1 | bsc | $571,919,026 | DefiLlama `total24h` |
| 4 | Base | **L2** | base | $566,993,410 | DefiLlama `total24h` |
| 5 | **Robinhood Chain** | **L2** | robinhood | $370,172,251 | DefiLlama `total24h` |
| 6 | Polygon PoS | sidechain-L1 | polygon | $172,040,318 | DefiLlama `total24h` |
| — | Celo | **L2** (was L1 until Mar 2025) | celo | — | not in the ranked top 10 |
| 7 | Hyperliquid | L1 | hyperliquid | $161,045,310 | DefiLlama `total24h` |
| 8 | TRON | L1 | tron | $122,247,912 | DefiLlama `total24h` |
| 9 | NEAR | L1 | near | $89,765,583 | DefiLlama `total24h` |
| 10 | Arbitrum One | **L2** | arbitrum | $81,109,247 | DefiLlama `total24h` |

**Why the separation matters.** Base, Robinhood Chain and Arbitrum settle
on Ethereum and share its execution environment, but each is its own
**token network**: its own gas token, DEX liquidity, launchpads and
memecoin market. Merging them into "EVM" would attribute Base liquidity to
Ethereum and miss most EVM-chain memecoins. Every registry record carries
both `layer` and `token_network`, and the layer split is printed.

**Extended coverage.** The registry holds **39 chains**, of which **35 have
a verified working JSON-RPC endpoint** (extended survey in
`data/_raw/step2_results.json`). The registry also records the agent's
declared **coverage gaps** — chains with no public RPC, no GeckoTerminal
listing, or an unusable Ankr pattern — with the per-chain failure detail.

**Hyperliquid runs two chains, and they are not merged.** Hyperliquid L1
is **not EVM**: it has no `eth_blockNumber` endpoint, which is exactly
why the EVM probe returns 404. The working endpoint at
`rpc.hyperliquid.xyz/evm` belongs to **HyperEVM**, a separate chain,
registered separately as an appchain. The L1's DEX volume is measured on
its own venue; its chain state needs its own API, not an EVM RPC.

**Two volume figures, never mixed.** DefiLlama's per-chain `total24h` is a
complete measurement; GeckoTerminal's per-pool `h24` sum is a
page-limited **lower bound**. The `landscape` output marks each row
`[M]` (measured) or `[S]` (sampled).

### New commands

```
python -m leapspace.cli landscape                    # the registry, layered
python -m leapspace.cli landscape --discover base    # memecoins on a chain
python -m leapspace.cli social --chain solana --token <MINT>
python -m leapspace.cli holders --chain solana --token <MINT>   # snapshot
python -m leapspace.cli holders --chain solana --token <MINT> --detect
python -m leapspace.cli traders --criteria           # the authority table
python -m leapspace.cli traders --wallet <ADDR>
python -m leapspace.cli traders --pool
python -m leapspace.cli traders --track
```

## Narrative classifier v2 — multi-platform + traction

The old classifier read only Jupiter's `community` tag and DexScreener's
`info.socials`, and measured **no traction at all**. `leapspace/social.py`
replaces it.

**Membership vs reach.** A project with one X account and no community
channel has reach, not members. The classifier separates
*community platforms* (Telegram, Discord) from *broadcast platforms* (X,
TikTok, Instagram, YouTube, Reddit, Threads, Farcaster, Bluesky). On live
data: BONK scores 7.0 (niche) with Telegram + Discord; Ethereum PEPE scores
1.0 with "broadcast only - reach without membership".

**The project's own description.** DexScreener's per-token profile endpoint
does not exist (verified: HTTP error). The records carrying the extra
platforms (TikTok, Instagram) and the written **description** live in two
*GLOBAL* lists of 30 tokens each — `/token-profiles/latest/v1` and
`/token-boosts/top/v1`. A token in neither gets no description, and that
coverage limit is reported rather than hidden.

**Traction is measured, not asserted.** Holder count and its change, buy/sell
imbalance, **organic** volume (bot-adjusted, Jupiter's), liquidity,
transaction counts, LP lock, and the project's age — from third-party
observations. Every signal carries a confidence tier:
`declared_by_project` (links, description), `third_party_observed`
(on-chain metrics), `vendor_assigned` (Jupiter's organic score, RugCheck's
risk score).

**Scored honestly.** BONK's traction score moved 1.5 → 4.5 once the
observed metrics were actually read. Weights are labelled
`ANALYST_CHOICE` and are re-scorable.

### Community SIZE — the strongest free evidence, and it needs no API key

Having a Telegram link is weak evidence. Having a Telegram with **11,009
members** is strong. Two public endpoints give the counts with no key:

| Platform | Endpoint | Returns |
|---|---|---|
| Discord | `https://discord.com/api/v9/invites/{code}?with_counts=true` | `approximate_member_count`, `approximate_presence_count`, guild name |
| Telegram | `https://t.me/s/{username}` | member count and online count in the page footer |

Live on this host: **BONK** — Telegram 11,009 members / 282 online, Discord
32,583 / 2,127 (guild "Bonk"), combined **43,592** across two platforms.
**WIF** — Telegram 25,795 / 481. That moved BONK's narrative score 7.0 →
**11.0** and traction 4.5 → **7.0**, and WIF's 6.0 → **9.5**.

**The validity trap.** A **nonexistent** Telegram channel still returns
HTTP 200 — its title reads `Telegram: Contact @name`, not
`Telegram: View @name`. Only the latter is a channel with a member count.
Parsing without that title check would report members for a channel that
has none. The parser requires `View` *and* a member count; otherwise the
platform is reported as **unmeasured**, never as zero.

A non-existent Discord invite returns an HTTP error, which is the correct
signal.

**Confidence split.** The project publishes its own links
(`declared_by_project`), but the counts are hosted and computed by a third
party (`observed_public_metric`). Both are stated.

**Two things that are NOT available free, stated so nobody tries:**
- **X/Twitter is not free.** Pay-per-use only ($0.005/post read, $0.010/user
  read), no free tier, and the ToS forbids scraping. A free screener
  **cannot** measure X follower counts or mention velocity. DexScreener
  gives the *link*, which is all this package uses.
- **RugCheck has no `socials` field at all.** Any classifier reading
  RugCheck for social links reads nothing. (Verified against the live
  `/report` payload.)
- CoinGecko removed `community_data` / `developer_data` on 28 Aug 2026, so
  `twitter_followers` is gone; `links` still works.

**Engagement rate is non-monotonic** (arXiv:2209.02911): returns are lower
when engagement is too low **or too high** — high engagement signals bot
activity. Score it as a band, never as a ramp. This package avoids the
problem by using community *size* rather than engagement rate.

## Holder-composition time series — the last missing paper clause

"Abrupt ownership changes around price spikes" needed a time series: a
single call can show concentration, but a change needs two observations.

`leapspace/holders.py` keeps a per-token series under
`state/holder_series/`, each snapshot carrying holder composition **and**
the price at the same moment. `detect_ownership_shifts` flags a window
when the price moved past a spike threshold **and** either concentration
moved past a delta threshold **or** a new address entered the top 10 (a
swap of control, not drift).

- **Solana**: RugCheck's full report — top holders with the owning
  wallet, pct and an `insider` flag. (BONK: 2,101,361 holders, top-20
  covering 38.95%.)
- **EVM**: ERC-20 Transfer logs reconstructed into net balances. Base's
  RPC names the range it will accept ("retry with the range A-B") and the
  code uses it: 19,811 logs over 184 blocks for Base USDC, 2,285 holders.
  The scanned window is reported with every result.

The meme-paper audit is now **20/26 clauses implemented, 0 MISSING**
(was 19/26 with 1 missing).

## "Successful trader" — grounded in cited standards

`AUTHORITATIVE_TRADER_STANDARDS.md` is the research. `leapspace/traders.py`
is the code. Three findings changed the implementation:

**1. "30 trades" is not a standard.** No regulator, exchange, professional
body or academic text publishes a minimum trade count. NIST publishes the
*formula* for the sample size given the precision you claim. The
qualification gate is now **computed**: for the package's own 55% win-rate
claim against a 50% coin flip (α=0.05 one-sided, β=0.20, δ=0.05) it needs
**N ≥ 637** — 21× the old hard-coded 30. The old 30 survives as the
profiler's *validity floor* for the normal approximation, which is what NIST
§7.2.4 actually says it is.

**2. The bands are not standardised.** Win-rate thresholds, profit-factor
bands and max-drawdown limits have **no** citable authority — the
frequently repeated "1.5 / 2.0 / 55%" figures circulate on vendor and blog
pages. They are kept because they are operable, and every one is labelled
with its actual authority. What *is* citable is used: the **Wilson score
interval** (NIST §7.2.4.1) for win rate, the **rule of three** for a
zero-numerator sample, and the **Sharpe definition** (CFA Institute: "the
industry standard for measuring risk-adjusted return").

**3. GIPS 3.A.9 points the opposite way to the old pool design.** "Terminated
portfolios must be included in the historical performance of the composite."
So a wallet that degrades leaves the **forward cohort** while its
**history is retained** — never silently dropped, never retroactively
restated. Every promotion and retirement carries a timestamp and a reason.

**An unavailable metric is unknown, not zero.** If the profiler cannot
price a wallet's trades, the win rate is `null` and no confidence interval
is computed — a zero there would fabricate a performance record.

### The limits of the claim

Passing the gates does **not** mean a wallet is a successful trader. The
thresholds are mostly analyst choices; what the research makes citable is
the sample size, the interval, and the fee-basis label. A 30-day on-chain
track record is not comparable to a GIPS-compliant 5-year record
(GIPS 1.A.3) and must not be presented as if it were.

---

## The memecoin trader screen (added 2026-11-03)

### What was built

| Module | What it does |
|---|---|
| `edge.py` | The consistency gate. Five rejection tests; the verdict is CONSISTENT / WEAK / FLUKE / INSUFFICIENT. |
| `whitelist.py` | The persistent, cross-chain registry of consistent traders. History is never deleted (GIPS 3.A.9). |
| `priceatblock.py` | A DIRECT USD price at a past block, read from the DEX pool's own reserves. |
| `priced.py` | The pipeline: transfer history -> historical price -> FIFO cost basis -> closed trades -> the gate. |
| `launchscan.py` | The NEW-meme path: the launch window, the early buyers, their prior records. |
| `memecoinscan.py` | Top-holder fetch, entity classification, per-wallet memecoin behaviour. |
| `costs.py` | Cost-basis engines (FIFO, weighted-average), archive-RPC pool reads, quantity-proxy bias test. |
| `crosschain.py` | Cross-chain identity scoring from funder, counterparties, timing, size — with traceable evidence. |
| `socialedge.py` | Lead time against the social comparators; the converse test for late buyers. |
| `criteria.py` | Loads the 31 authority-tagged criteria from `leapspace/data/consistency_criteria.json`. |

29 CLI commands.

### The cost basis is now REAL — and it was not before

The earlier limitation was: "realised PnL cannot be computed keylessly."
That was wrong, in two ways.

**1. DefiLlama's historical endpoint works. The URL form was wrong.**
The form is a COLON between chain and token, and a COMMA between coins:

```
https://coins.llama.fi/prices/historical/{unix_ts}/ethereum:0xPEPE
https://coins.llama.fi/prices/current/ethereum:0xPEPE,ethereum:0xSHIB
```

The comma form (`ethereum,0xPEPE`) returns `{"coins": {}}` and looks like
a dead endpoint. It is not. Verified live: PEPE at 2023-06-01 =
$1.26e-06, 2024-01-01 = $1.29e-06, 2025-01-01 = $1.984e-05.

Caveat: the historical endpoint is aggressively rate limited (HTTP 429) and
needs slow, deduplicated requests.

**2. The better answer needs no price API at all.**
`priceatblock.py` asks the Uniswap V2 factory, AT THE TRADE'S OWN BLOCK,
which pair existed for (token, USDC), then reads that pair's
`getReserves()` at the same block. That is the actual liquidity-weighted
price at that moment, from a keyless archive RPC (`eth.drpc.org` and
four other providers were verified to serve state from 2022).

Verified against known history:

| token | date | pool price | reference | error |
|---|---|---|---|---|
| PEPE | 2024-01-01 | $1.2370e-06 | $1.29e-06 | 4.1% |
| PEPE | 2025-01-01 | $1.8291e-05 | $1.984e-05 | 7.8% |
| PEPE | 2023-06-01 | $1.6065e-06 | $1.26e-06 | 27.5% (the pool was new and shallow) |
| SHIB | 2024-01-01 | $9.7679e-06 | ~$9.5e-06 | ~3% |

A pair whose quote side holds less than the floor is REJECTED rather than
priced, so a nearly-empty pool cannot manufacture a price.

### The consistency gate

Five ways a wallet can look good without being good, each rejected
explicitly:

| Test | Rejects when | Authority |
|---|---|---|
| `largest_win_share` | one trade carries >50% of the PnL | analyst choice |
| `skill_not_distinguishable` | P(win rate > 50%) < 0.95 | Beta-Binomial, Barber/Bay/Solberg |
| `deflated_sharpe` | DSR <= 0 after correcting for candidates scanned | Bailey & Lopez de Prado |
| `edge_decay` | recent expectancy < 0.5x early expectancy | analyst choice |
| `insufficient_independent_bets` | too few non-overlapping bets | NIST sample size |

The Deflated Sharpe is what makes "not a fluke" quantitative. The same
wallet with the same trades gets HARDER to qualify as the scan widens:

| candidates scanned | expected max Sharpe under the null | verdict |
|---|---|---|
| 1 | 0.000 | CONSISTENT |
| 10 | 1.575 | CONSISTENT |
| 100 | 2.531 | FLUKE |
| 10,000 | 3.861 | FLUKE |

Validated against six synthetic wallets with known ground truth: a
consistent trader, a one-lucky-win wallet, a coin-flip wallet, a decaying
wallet, a single-token wallet and a too-few-trades wallet all classify
correctly.

### Two entry points, one method

| | OLD meme (PEPE) | NEW meme (launched 1h ago) |
|---|---|---|
| find wallets | top-holder list, exchange wallets removed | transfers in the first N blocks |
| get record | their history on the meme universe | their history on OTHER established memes |
| test edge | consistency gate | consistency gate |
| social check | bought before or after the narrative? | bought before or after the narrative? |
| whitelist | promote with evidence | promote with evidence |

`memeflow` runs the old path; `launchscan` runs the new one. Both end at
the same gate.

On a live launch scan of GIGA (Ethereum), the very first wallet inside the
launch window WAS the deployer, in the same block as the launch
(lag = 0, creator address identical). The launch scan finds insiders by
construction; it does not need a hand-maintained insider list.

### What the social edge actually says

`socialedge.py` computes a wallet's lead time in hours against three
comparators — the membership threshold crossing, the holder-count growth
inflection, and the first major mention event — and classifies the wallet
LEADING / COINCIDENT / LAGGING. It also runs the CONVERSE test: a wallet
that bought after the narrative was established is crowd-following and is
reported separately.

Verified at realistic timescale: a day-1 buyer is LEADING (+72h), a
day-5 buyer LAGGING (-24h), a day-9 buyer LAGGING (-120h).

### Free social data, and what is NOT free

| Signal | Source | Free? |
|---|---|---|
| Community membership | `t.me/s/{username}` | yes |
| Community membership | `discord.com/api/v9/invites/{code}?with_counts=true` | yes |
| Platform breadth | DexScreener `info.socials` | yes |
| Organic traction | Jupiter `organicScore` | yes, Solana only |
| Risk | RugCheck full report | yes, Solana only |
| **X/Twitter followers** | — | **no. Pay-per-use only; scraping is forbidden by ToS.** |

**The validity trap:** a nonexistent Telegram channel still returns HTTP
200, with the title `Telegram: Contact @name`. Only `Telegram: View @name`
is a channel with a member count. An unmeasurable platform is reported
UNMEASURED, never zero.

**Engagement rate is non-monotonic** (arXiv:2209.02911): too high signals
bots. It is a band, never a ramp.

### The honest finding about PEPE's top holders

The scan found 27 exchange hot wallets among PEPE's top 50 (54% custody,
not traders). Of the remaining personal traders, the median holder:

- entered **~2.4 years after launch** (median lag 6,615,284 blocks),
- held a **100% single-token position** (10 of 15),
- held a median **142 days**,
- had a median position of **$10.6M**.

These are late, concentrated accumulators of the one meme that worked —
on an outcome-selected sample. That is exactly why the NEW-meme path
exists: it screens an unbiased universe of early buyers and tests their
prior records instead.

Only ONE wallet in the sample showed an active-trader signature:
`0xAf2358e98683265cBd3a48509123d390dDf54534` — 5 memes, 2.62-day median
hold, TURBO at 745 blocks, PEPE at 1,440 blocks, 34 SHIB buys.

### Reproduce

```bash
python -m leapspace.cli memeflow --token 0x6982508145454ce325ddbe47a25d4ec3d2311933 --top 50
python -m leapspace.cli pnl --wallet 0xAf2358e98683265cBd3a48509123d390dDf54534 --method pool
python -m leapspace.cli launchscan --token <new memecoin> --window 1000
python -m leapspace.cli edge --trades trades.json --trials 500
python -m leapspace.cli whitelist
python -m leapspace.cli link --wallets ethereum:0xAAA,base:0xBBB
python -m leapspace.cli socialedge --token <mint> --buys buys.json
python -m leapspace.cli traders --criteria
```
