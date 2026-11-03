# Third-Party Skill Comparison — LeapSpace Quant

**Generated:** 2026-11-03
**Compared against:** `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant` (30+ modules, 31 CLI commands)
**Host constraints:** Windows 10, Python 3.14, ~2.7 GB free on C:, **no new packages installed**
**Machine-readable source:** `data/third_party_skill_candidates.json` (14 candidates, every one fetched and verified)

---

## 1. Top candidates per category

Scoring: **Depth** (implementation_depth) · **Fit** (does it close a gap we actually have) ·
**Zero-cost** (runs with no paid key and no install) · **Maint. risk** (lower is better).

| Category | Candidate | Depth | Fit | Zero-cost | Maint. risk | Note |
|---|---|---|---|---|---|---|
| Strategy research | **purgedcv** (eslazarev/purged-cross-validation) | real impl | **HIGH** — closes our CPCV gap | YES (numpy/pandas/scipy/sklearn already installed) | Low (MIT, 61★, 2026-10-25) | PBO + DSR **verified to match ours** |
| Strategy research | **ml4t/skills** (61 skills) | prompt only | MED — CPCV doctrine, factor rubric | YES for the docs | Low (Apache-2.0, 2026-11-02) | Best-written prose; **zero executable payload** |
| Strategy research | **ml4t/diagnostic** (the library) | real impl | MED — CPCV + degradation stats | NO — needs polars/pyarrow/arch, none present | Med (MIT, 46★, 2026-11-02) | Right code, wrong install weight |
| Market data | **tradermonty `data-quality-checker`** | real impl | **HIGH** — closes the report-arithmetic gap | YES (stdlib only, no key) | Low (MIT, 3563★, 2026-11-02) | Ships its own pytest suite |
| Market data | **gauss314/skills** (backtesting/options/portfolio) | real impl | HIGH for options+portfolio | YES (numpy/pandas/scipy present) | Med (MIT, 253★, **2026-06-14**, 5 months stale) | 30/31 self-checks pass when assembled correctly |
| On-chain | **sheldonivish/degen-desk** | real impl | MED — second, independent on-chain decode path | YES (stdlib only, no key) | **HIGH** (MIT but **0★**, unvetted) | Zero stars; ships live-trading skills alongside research |
| Options | **Iman/agent-driven-options-desk** | real impl | HIGH — real Greeks/smile/GARCH engine | YES | **HIGH** (**PolyForm Noncommercial** — not OSS) | Unusable commercially |
| Options | **rgourley/quant-garage** | paid API wrapper | MED — factor IC/decile rubric | **NO** — `MASSIVE_API_KEY` on every useful skill | **HIGH** (AGPL-3.0, 7★) | Two ideas worth stealing, no code worth taking |
| Signal packaging | **PVinh-Quant/pseud** (`alpha-hypothesis-writer`) | real impl | MED — mechanism-anchor gate | YES | Med (MIT, 13★, 2026-08-11) | Written in Vietnamese |
| Signal packaging | **Jimmy7892/quant-research-skill** | prompt only | LOW — parameter-surface framing | YES | Med (MIT, 7★) | 1 helper script; overlaps ml4t sensitivity-analysis |

### The four categories we searched and what we found

| Our need | Best available | Reality |
|---|---|---|
| 1. Backtesting / walk-forward / overfitting control | purgedcv, ml4t/skills | **Real gap found: we have no CPCV.** purgedcv closes it with an already-installed dependency stack. |
| 2. Market data pipelines / multi-source reconciliation / data quality | tradermonty `data-quality-checker`, gauss314 | **Real gap found: we validate response SHAPE, never report ARITHMETIC.** |
| 3. On-chain / wallet / holders / insider | degen-desk | Mostly covered already. Only a *second independent decode path* is missing. |
| 4. Options / derivatives / gamma / vol surface | gauss314 `option-pricing`, Iman option-desk | **Real gap found: we have NO options pricing engine at all.** gamma.py works from OI + last trades and our own SKILL.md calls the IV "approximate". |
| 5. Financial research synthesis / provenance / citations | (tradermonty, pseud) | **Already well covered.** Our `consistency_criteria.json` (31 authority-tagged criteria) and `parameter_provenance` tagging are stronger than anything third-party. |
| 6. Signal packaging / decision-ready brief | tradermonty `edge-signal-aggregator` | Partial gap: our `report.py` emits markdown+JSON but has no multi-source conviction layer. |

---

## 2. ALREADY ADOPTED — no action needed

These are installed under `C:\Users\HP\AppData\Local\hermes\skills\`. They already cover the
ground the third-party candidates would claim.

### Installed from `P0ntix/NavAeroCapital` (git remote confirmed on each folder)

`strategy-backtest-lab` · `walk-forward-validation` · `vectorbt` · `backtrader` ·
`signal-classification` · `strategy-framework` · `regime-detection` · `risk-management` ·
`position-sizing` · `volatility-modeling`

> **Finding:** `walk-forward-validation`, `vectorbt`, `backtrader`, `signal-classification` and
> `strategy-framework` are **byte-identical in frontmatter to the `agiprolabs/claude-trading-skills`
> versions** (only CRLF line endings differ; upstream 8,733 chars vs local 9,559 for
> walk-forward-validation). **The `agiprolabs/claude-trading-skills` repo (508★, MIT, 68 skills) is
> ALREADY ADOPTED** — do not re-adopt it, and do not adopt the third-party mirrors of it
> (`Serennity007/awesome-stock-quant-skills`, `NeverSight/skills_feed`, `claudemods.dev` bundles,
> `claudeskills.info`, `skillsmp.com`) which are re-publications of the same files.

### Installed from other sources — same territory, do not duplicate

| Local skill | Covers | Kills candidate |
|---|---|---|
| `strategy-backtest-lab` | `btengine`/`btvalidate` — **purged + embargoed** walk-forward (`_plan_purged_folds`), disjointness assertion, the validation gauntlet our `backtest.py` IMPORTS rather than reimplements | any "better backtester" |
| `walk-forward-validation` | rolling/expanding windows, purging, embargo, CPCV **described** (not implemented) | Jimmy7892, ml4t/skills walk-forward-cv |
| `signal-classification` | walk-forward validation + SHAP + threshold optimisation | ml4t `shap-analysis` |
| `regime-detection` | volatility clustering, trend detection, adaptive regime | tradermonty `market-regime`, quant-garage `market-regime` |
| `macro-regime-detector` | 1–2 yr macro regime transitions | tradermonty `macro-regime-detector` (same skill, same repo family) |
| `options-strategy-advisor` | Black-Scholes, Greeks, P/L simulation | Iman `options-strategy`, dongzhuoyao pricing skills |
| `options-pricing` | **marked `[STUB]`** — pricing models, IV surfaces, Greeks | **our own gap**; gauss314/Iman fill it |
| `token-holder-analysis` | holder concentration, insider risk, cohort behaviour | any holder-scanner candidate |
| `wallet-profiling` | wallet behaviour, performance, copy suitability | degen-desk whale-wallet-analysis |
| `sybil-detection` | coordinated wallets, wash trading, insider funding | on-chain cluster detectors |
| `copy-trading` | copy-trade simulation, consensus, trusted pool | tradermonty copy-trade skills |
| `portfolio-analytics` | return/risk metrics, rolling analysis, HTML reports | gauss314 `portfolio` (partly) |
| `position-sizing` · `kelly-criterion` | sizing methods | quant-garage `position-sizer` |
| `risk-management` | portfolio limits, circuit breakers | quant-garage `drawdown-circuit-breaker` |
| `correlation-analysis` · `cointegration-analysis` | cross-asset correlation, pairs | tradermonty `pair-trade-screener` |
| `mean-reversion` | Hurst exponent, half-life, ADF | quant-garage `hurst-exponent` |
| `slippage-modeling` · `lp-math` · `liquidity-analysis` | execution cost, AMM math, depth | quant-garage cost skills |
| `feature-engineering` | price/volume/on-chain/microstructure features | ml4t `compute-features` |
| `ohlcv-processing` | resampling, gap handling, anomaly detection, **multi-source merging** | ml4t `validate-data` / `fetch-data` |
| `grounded-citations` | grounding answers in cited, verifiable sources | ml4t / Harness-Research citation skills |
| `research-paper-writing` | paper workflow | `research-paper-assistant` |
| `arxiv` | arXiv search by keyword/author/category/ID | `bgpt-paper-search` |
| `third-party-skill-sourcing` | **the vetting procedure used for this report** | — |
| `leapspace-quant` · `leapspace-free-data-sources` | our own package + its keyless source catalogue | — |

### Non-skill reference material already exploited

`AUTHORITATIVE_TRADER_STANDARDS.md` (NIST sample size, Wilson interval, GIPS 3.A.9),
`AUTHORITATIVE_CONSISTENCY_STANDARDS.md`, `SOCIAL_NARRATIVE_STANDARDS.md`,
`FREE_DATA_SOURCES.md`, `CROSSCHAIN_WALLET_METHODS.md`, `CHAIN_LANDSCAPE.md`.
These already encode the citation discipline that third-party "research synthesis" skills sell.

---

## 3. RECOMMENDED TO ADOPT — at most 3

### 1. `tradermonty/claude-trading-skills` → **`skills/data-quality-checker` only**

* **Repo:** https://github.com/tradermonty/claude-trading-skills · MIT · 3,563★ · pushed 2026-11-02
* **Paths:** `skills/data-quality-checker/SKILL.md`, `skills/data-quality-checker/scripts/check_data_quality.py`
  (26,136 chars, **stdlib only**), `skills/data-quality-checker/scripts/tests/`
* **Concrete change to our package:** add `leapspace/reportvalidate.py` — a pre-flight validator
  invoked from `report.py` before the markdown is written, wired into
  `leapspace/tests/check_report_integrity.py` as a hard gate. It checks five families over our
  rendered report: **price_scale** (an ETF quoted against its futures), **notation** (instrument
  symbol errors), **dates** (date/day-of-week mismatch, with year inference), **allocations**
  (allocation totals that do not sum) and **units**. Three of those five families we do not check
  anywhere today.
* **Why this one first:** our own SKILL.md documents *two* bugs of exactly this class that were
  found by hand — the cross-pool price comparison that manufactured a **+30,833%** return, and the
  producer/consumer base-selection drift that emptied the NICHE bucket while still printing a
  confident verdict. `check_report_integrity.py` asserts the report matches the data; it does
  **not** assert the report's internal arithmetic is self-consistent. This closes that hole
  mechanically.
* **Effort:** low — ~2 hours. Copy one folder (not the 60 MB repo), add ~30 lines of wiring, extend
  the number formats to our USD/provenance conventions, keep it advisory-with-a-failing-exit-code.
* **Risk:** **low**. Stdlib only, no key, no install, MIT. Two caveats: it validates *markdown
  documents*, not our JSON payloads or on-chain holder tables, so it covers the report renderer but
  not the chain artefacts; and it is advisory by design, so we must make the warnings fail the
  build ourselves or it changes nothing.
* **Explicitly NOT adopting from this repo:** `macro-regime-detector`,
  `institutional-flow-tracker`, `cot-contrarian-detector`, `options-strategy-advisor` (already
  installed), and the `edge-*` family (coupled to siblings we do not have).

### 2. `eslazarev/purged-cross-validation` (**purgedcv**) — vendored source, not a pip install

* **Repo:** https://github.com/eslazarev/purged-cross-validation · MIT · 61★ · pushed 2026-10-25 ·
  v0.1.11 on PyPI (2026-10-16)
* **Paths:** `src/purgedcv/` (`_cpcv.py`, `_purged_kfold.py`, `_purge.py`, `_embargo.py`, `_pbo.py`,
  `_metrics.py`, `_paths.py`, `_path_metrics.py`, `_walk_forward.py`, `diagnostics.py`).
  **No SKILL.md** — this is a library. The nearest agent wrapper is
  `howard-lynn-ye/fin-skills` → `lib-purgedcv`, which is prompt-only and whose documented API has
  already drifted from the code.
* **Concrete change to our package:** add `leapspace/cpcv.py` exposing `CombinatorialPurgedCV` and
  `PurgedKFold` so `backtest.py`'s gauntlet gains a **combinatorial purged** stage alongside its
  existing purged/embargoed walk-forward, and add `min_track_record_length()` +
  `minimum_backtest_length()` to `edge.py` so the **0.95 DSR bar becomes sample-size-conditional**
  rather than a hard-coded constant. Also add `effective_n_trials()` as a second, principled route
  to the independent-bet count that `edge.py::bet_outcomes` currently computes by hand.
* **Verification already done (this is why it is #2):**
  - CSCV PBO: our `leapspace/pbo.py::probability_of_backtest_overfitting` vs purgedcv on an
    identical 6-candidate × 240-row matrix → **0.6 == 0.6, exact** (70 combinations, 8 partitions).
  - DSR: our `leapspace/stats.py::deflated_sharpe_ratio` vs purgedcv → max abs diff **1.8e-3**
    across 20 (drift, n_trials) combinations.
  - **Decision agreement at our 0.95 bar: 72/72 cases, 0 disagreements.**
  - `PurgedKFold(n_splits=5, purge_horizon="5D", embargo="5D")` on 200 datetime-indexed rows →
    5 folds, fold0 150 train / 40 test. `effective_n_trials()` → 140.
  - Imported **from source with no install** — numpy/pandas/scipy/sklearn are already on this host.
* **Effort:** medium — ~1 day to vendor `src/purgedcv/` (17 files, ~10 MB repo but the package
  itself is small), wire a CPCV stage into `backtest.py`, add MinTRL/MinBTL to `edge.py`, and add
  tests asserting the vendored PBO still equals our own.
* **Risk:** **medium**. It adds a runtime dependency to a package that is currently pure-stdlib on
  the hot path (sklearn is the heavy one). The API is young (0.1.x). Vendor the source into
  `leapspace/vendor/purgedcv/` rather than pip-installing on a 2.7 GB-free host, and pin the
  commit. Note the PBO half is a **cross-check, not a replacement** — our CSCV implementation is
  already faithful; the value is CPCV + MinTRL + MinBTL + effective-n, which we simply do not have.

### 3. `gauss314/skills` → **`skills/option-pricing` only** (and `skills/portfolio` as a stretch)

* **Repo:** https://github.com/gauss314/skills · MIT · 253★ · **pushed 2026-06-14** (5 months stale)
* **Paths:** `skills/option-pricing/SKILL.md` + `scripts/option_pricing.py` (49,731 chars);
  `skills/portfolio/SKILL.md`; `skills/backtesting/scripts/` (engine, ratios, copulas, forward,
  simulations, validate)
* **Concrete change to our package:** replace the approximate IV in `leapspace/gamma.py` with a real
  pricing model. Add `leapspace/optionpricing.py` (flat numpy, no classes) exposing
  `bs_price`, `bs_greeks`, BAW/Bjerksund-Stensland, CRR binomial, Boyle trinomial, Monte Carlo with
  antithetic variates, Longstaff-Schwartz, Heston-with-Fourier-smile and Bates-with-jumps. Then
  `gamma.py` can compute dealer gamma against a fitted surface instead of last-trade prices, and
  the "Option IV is derived from last-trade prices and is approximate" caveat in our SKILL.md
  becomes fixable. The `portfolio` skill would give us the **first portfolio-construction layer in
  the package** (Markowitz, Black-Litterman with Idzorek omega, HRP/HERC/NCO with risk parity) —
  grep for `markowitz|black_litterman|risk_parity` in `leapspace/*.py` returns **NONE**.
* **Verification already done:** downloaded the scripts to scratch (no install) and RAN them —
  `python option_pricing.py bs --S 100 --K 100 --T 0.25 --r 0.05 --sigma 0.20` → price **4.614997**,
  delta 0.569460, gamma 0.039288, vega 19.644000, theta −10.474151, rho 13.082755.
  `python validate.py` from a correctly assembled layout → **30/31 checks passed** (the single
  failure is the bundled pytest suite, which needs the `tests/` dir a sparse checkout omits; I had
  to fetch a missing sibling `fundamental_ratios.py` and 8 asset CSVs to get there).
* **Effort:** medium — ~1 day for option-pricing; ~2 days more for portfolio. Flat numpy means it
  fits the package's existing style with no new dependencies.
* **Risk:** **medium**. Two honest caveats. (a) The documentation is in **Spanish** — a real
  translation cost for an English-language package, though the code and CLI are language-neutral.
  (b) It is 5 months stale relative to the other candidates, and the `backtesting` skill's engine
  **overlaps `strategy-backtest-lab`, which our SKILL.md explicitly says must remain the
  authority** — so take `option-pricing` (and optionally `portfolio`), **not** `backtesting`.
  The MIT licence is clean.

> **Not recommended for adoption:** `ml4t/skills` and `ml4t/diagnostic` despite their quality. The
> skills are prompt-only, and the library needs polars + pyarrow + arch + statsmodels (none
> installed; only ~2.7 GB free) — the wrong shape for a deliberately stdlib-only package. `ml4t/skills`
> is genuinely the best-written articulation of the CPCV doctrine we lack, so the correct move is to
> **read it before implementing #2**, not to install it.

---

## 4. DO NOT ADOPT

| Candidate | Why not |
|---|---|
| **rgourley/quant-garage** | **Needs `MASSIVE_API_KEY` on every useful skill** (verified across 9 skills) — our package is built entirely on keyless Yahoo/Nasdaq/Deribit/CoinGecko/DexScreener/Blockscout/RugCheck/Jupiter. Adopting it would replace a working free path with a paid one, which the brief forbids. Also **AGPL-3.0** (copyleft; GitHub reports NOASSERTION), 7★. Its `market-regime` also collides with our `regime.py`. **Two ideas worth stealing without the code:** the dual-layer output contract (canonical JSON + human report + the methodology shipped *with* the output) and the flat-files-by-day-bucket bulk-download pattern. |
| **Iman/agent-driven-options-desk-and-skills** | **PolyForm Noncommercial 1.0.0** — not an OSI licence, forbids noncommercial use, unusable for a package the user owns. 9★, 75 MB, two installable packages, and the agent half drags in a LangGraph/LLM stack. The engine is the best options implementation found, but the licence disqualifies it. |
| **agent-skills-hub/agent-skills-hub** (`quant-analyst`) | **Prompt-only, and the clearest example of the failure mode this comparison exists to expose.** 1,831 chars: "Clarify goals, constraints, and required inputs. Apply relevant best practices and validate outcomes." Its description claims it "Implements risk metrics, portfolio optimization, and statistical arbitrage" — it implements nothing, cites nothing, and contains no code. 813 skills and 127★ are not evidence of substance. |
| **dongzhuoyao/finance-option-skills** | **Prompt-only with ZERO .py files in the whole repo.** No LICENSE file (GitHub: NOASSERTION) → default "all rights reserved", not safely adoptable. 1★, pushed 2026-05-11. Its `gex-max-pain` and `dvol-index` describe what our `gamma.py` already *computes* from real Nasdaq chains — a prose description of something we run is strictly worse. |
| **ml4t/skills** | Prompt-only; 61 skills would flood the context with guidance we mostly already carry as cited, tested code. Its named libraries (`ml4t-diagnostic`, `ml4t-data`, `ml4t-backtest`) require polars/pyarrow/arch — none installed, ~2.7 GB free. **Read it, don't install it.** Also substantially overlaps the `agiprolabs/claude-trading-skills` set we already ship. |
| **ml4t/diagnostic** | Right code, wrong install weight: needs polars≥1.36, pyarrow≥14, arch≥7.2, statsmodels, pydantic (verified: polars and arch **absent** on this host) plus Python ≥3.12,<3.15. It would also drag in `ml4t-backtest`, a backtest engine we deliberately do not want because `strategy-backtest-lab` is the authority. |
| **howard-lynn-ye/fin-skills** | Reference material only; the repo **moved** (GitHub returns "Moved Permanently" → `howard-lynn-ye/Fin-RSI`, 1★), so the documented install path is stale. Its own API description has drifted: it quotes `deflated_sharpe_ratio(observed_sr, n_trials, sr_std, n_obs, ...)` but the current signature is `(returns, n_trials, var_sharpe, *, bars_per_year=None)`. **Useful as a trap list before adopting purgedcv, not as an install.** |
| **Jimmy7892/quant-research-skill** | Prompt-only with one helper script; 7★; the parameter-surface framing is good advice but our problem is not parameter picking inside a spec — it is that 10 of our 13 specs are REFUTED. Overlaps ml4t `backtest/sensitivity-analysis`. |
| **PVinh-Quant/pseud** (`alpha-hypothesis-writer`) | Right idea (mechanism-anchor gate, event clustering, 8-field pre-registration), but 13★, pushed 2026-08-11, **written in Vietnamese**, and tied to a 1-minute OHLCV pipeline we do not have. Our own `apply_intake_gate` + `parameter_provenance` already enforces the pre-registration half more strictly. Take the *concept*; skip the skill. |
| **sheldonivish/degen-desk** | **Not in the DO-NOT list — but not recommended either.** MIT, keyless, stdlib-only, and the on-chain decode path is genuinely a useful independent second opinion. Held back by **0 stars** (wholly unvetted), a 50 KB single-file implementation with no tests, hard-coded `/workspace/trenches/` paths, and — decisively — the repo ships **live-trading skills** (`arcus-autopilot`, `lighter-perps`, `popdex-market-maker`, `vps-bot-deploy`) which must never sit next to research skills. If adopted later, cherry-pick the three memecoin research skills only. |
| **agiprolabs/claude-trading-skills** | **Already adopted** — see §2. |
| **Third-party mirrors** (`Serennity007/awesome-stock-quant-skills`, `NeverSight/skills_feed`, `claudemods.dev`, `claudeskills.info`, `skillsmp.com`, `skillsclaude.org`, `awesomeskills.dev`, `skillmd.com`, `skillsmd.dev`, `linny006/awesome-agent-skills`, `VoltAgent/awesome-agent-skills`) | These are indexes or re-publications of upstream skill files. Adopt the **upstream repo** once, not the mirrors — mirrors carry no licence provenance, no update signal and duplicate upstream content into the context. `VoltAgent` (36,779★) and `linny006` are **awesome-lists, not skills** — useful as a discovery index only. |

---

## 5. What we searched, and how

**Discovery (four independent routes, all GitHub-wide):**

1. **GitHub code search** via the authenticated `gh` CLI (`search/code`), `filename:SKILL.md`:
   `memecoin OR solana wallet onchain` (58 hits) · `dealer gamma OR gamma exposure` (31) ·
   `holder concentration OR wallet profiling OR insider detection OR cluster analysis` (0) ·
   `data quality OR reconciliation "price data" pipeline` (4) ·
   `trading brief OR decision-ready OR signal package` (0) ·
   `provenance citation research paper extract` (3,928).
2. **`gh search repos`** for `agent skills crypto trading`, `skills onchain wallet analyzer`,
   `claude skills data pipeline validation`, `hermes agent skills`.
3. **Web search** for `awesome agent skills` lists, `claude code skills trading`,
   `SKILL.md trading backtesting quant` — which surfaced the Hermes-specific registries
   (`ZeroPointRepo/awesome-hermes-skills` 658★, `itgoyo/hermes-skills` 304 skills,
   `codesstar/hermes-skill-atlas`, `cosmicstack-labs/mercury-agent-skills`).
4. **Direct API enumeration** of every candidate repo's full file tree.

**Verification performed on every candidate:**

- `GET /repos/{owner}/{repo}` → stars, `pushed_at`, SPDX licence, archive status, size.
- `GET /git/trees/{branch}?recursive=1` → the real file listing. **This is what separated real
  implementations from prompt documents**: `ml4t/skills` = 61 dirs × 1 file; `dongzhuoyao` = 20
  SKILL.md and **0 .py**; `gauss314` = 74 .py; `tradermonty` = 880 .py; `purgedcv` = 17 modules.
- Raw fetch of each SKILL.md **in full**, its `scripts/` tree, its LICENSE and its CI config.
- **Execution where possible, with nothing installed** — files were downloaded to scratch and run:
  - `gauss314` `option_pricing.py bs` → 4.614997 with full Greeks; `validate.py` → **30/31 pass**.
  - `tradermonty` `evaluate_backtest.py` → *"Quality score: 55/100 — Decision: REJECT"*, with named
    blocking reasons, 2 red flags, JSON + Markdown written out.
  - `purgedcv` imported from source → `PurgedKFold` 5 folds (150/40), `effective_n_trials` 140.
- **PyPI JSON API** for every named dependency (`ml4t-diagnostic` v0.2.0, `purgedcv` v0.1.11,
  `mlfinlab` — confirmed absent).
- **Cross-check against our own code** — purgedcv's PBO and DSR computed on identical inputs
  against `leapspace/pbo.py` and `leapspace/stats.py` (exact PBO match; 1.8e-3 DSR; 0/72 verdict
  disagreements at the 0.95 bar).
- **Gap analysis of our own package** by grepping `leapspace/*.py` for `cpcv`, `purged`,
  `spearman`, `information_coefficient`, `triple_barrier`, `markowitz`, `black_litterman`,
  `risk_parity`, `hurst`, `min_track_record`, `effective_n_trials` — all **NONE**, which is how
  the three recommendations were selected rather than by star count.
- **Local catalogue**: the `description:` line of all 160 installed SKILL.md files was read
  (not dumped), and each of the ten `P0ntix/NavAeroCapital` folders had its git remote confirmed.

**Coverage honesty:** the two searches that returned **0** results
(`holder concentration / wallet profiling / insider detection`, and `trading brief /
decision-ready / signal package`) are why categories 3 and 6 are thin — there is very little
first-party SKILL.md material for on-chain analytics or brief assembly, and the strong candidates
in those areas are ordinary Python libraries rather than agent skills. The two directories named
`awesome-agent-skills` are **lists of other people's skills**, not skills, and were used only as
discovery indexes.

---

## 6. Compact index

| # | Name | Category | Depth | Needs key | Verdict |
|---|---|---|---|---|---|
| 1 | purgedcv (eslazarev/purged-cross-validation) | strategy research | real_implementation | no | **ADOPT** (vendor, don't pip install) — closes the CPCV gap; PBO/DSR verified against ours |
| 2 | tradermonty → `data-quality-checker` | market data pipelines | real_implementation | no | **ADOPT** (that folder only) — closes the report-arithmetic gap |
| 3 | gauss314/skills → `option-pricing` | market data pipelines / options | real_implementation | no | **ADOPT** (that skill only; `portfolio` optional) — closes the no-options-engine gap |
| 4 | tradermonty/claude-trading-skills (rest) | financial research synthesis | real_implementation | no | SKIP — 4 of its skills already installed; `edge-*` family needs siblings we lack |
| 5 | ml4t/skills | strategy research | prompt_only | no | SKIP — read the CPCV doctrine, don't install 61 prompt docs |
| 6 | ml4t/diagnostic | strategy research | real_implementation | no | SKIP — right code, wrong install weight (polars/arch absent) |
| 7 | sheldonivish/degen-desk | on-chain | real_implementation | no | SKIP (hold) — 0★, ships live-trading skills; cherry-pick 3 research skills if revisited |
| 8 | Iman/agent-driven-options-desk | options | real_implementation | no | SKIP — PolyForm Noncommercial is not OSS |
| 9 | rgourley/quant-garage | options / factor | paid_api_wrapper | **YES** | SKIP — paid key + AGPL-3.0; steal 2 output-design ideas only |
| 10 | agent-skills-hub → `quant-analyst` | strategy research | prompt_only | no | SKIP — 1,831 chars of generic advice; implements nothing |
| 11 | dongzhuoyao/finance-option-skills | options | prompt_only | no | SKIP — 0 .py files, no licence, 1★ |
| 12 | howard-lynn-ye/fin-skills | strategy research | reference_material | no | SKIP — repo moved; API description already stale; read as a trap list |
| 13 | Jimmy7892/quant-research-skill | signal packaging | prompt_only | no | SKIP — good framing, no payload, overlaps ml4t |
| 14 | PVinh-Quant/pseud → `alpha-hypothesis-writer` | signal packaging | real_implementation | no | SKIP — 13★, Vietnamese, pipeline-specific; take the concept |
| 15 | agiprolabs/claude-trading-skills | strategy research | real_implementation | no | **ALREADY-HAVE** — installed as `P0ntix/NavAeroCapital` |
| 16 | local `strategy-backtest-lab` + `walk-forward-validation` + 8 more | strategy research | real_implementation | no | **ALREADY-HAVE** — purged+embargoed walk-forward is the authority |
| 17 | local `leapspace-quant` + `leapspace-free-data-sources` | own package | real_implementation | no | **ALREADY-HAVE** — the package under comparison |

---

*Nothing was installed. Every execution test ran from source downloaded to
`%LOCALAPPDATA%\hermes\cache\scratch`, which is disposable.*
