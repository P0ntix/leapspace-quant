# leapspace-quant

A trading research and signal-generation instrument. It finds candidate
trades, gathers the evidence for each one, grades the quality of that
evidence, and produces a **decision-ready brief** a human can act on.

It does **not** place orders. It is not a broker. It is not an
autonomous trading system. Read [What this is not](#what-this-is-not)
before trusting any number it produces.

```
pip install nothing. Python 3.11+. Standard library only for the core.
```

---

## The honest state, as verified

Everything below was measured on live data from this host. Nothing here
is a projection.

| | |
|---|---|
| Research papers implemented | 7 of 7 |
| Backtest specifications | 13 (6 new in LeapSpace 2.0) |
| Specifications surviving the **full** validation gauntlet | **2** |
| Specifications refuted under quick validation | 10 |
| **Paper-concept matrix (the 5 attached research papers)** | **96 specs: 48 real + 48 inverted negative controls, 8 concepts × 6 asset classes** |
| **Paper concepts earning a SUPPORTED verdict** | **0** |
| Negative controls that survived (validation failing to discriminate) | **0** |
| Memecoin wallets screened against the consistency gate | 15 |
| Wallets that passed the gate | **0** |
| Chains in the registry | 52 |
| CLI commands | 32 |
| Python lines | ~30,700 across 46 modules |

**The single most important fact about this project right now:** no
wallet has ever passed the consistency gate. All fifteen PEPE top-holder
wallets scored FLUKE. A system that trades memecoins today has no
evidence-backed basis for doing so, and this package says so out loud
rather than manufacturing a signal.

**The second most important fact:** the paper-concept matrix found no
SUPPORTED concept either. Of the 96 specs, 0 earned a SUPPORTED
verdict. The single FRAGILE row carries a *negative* Sharpe. That is
not a disappointing result — it is the result, and it is reported
rather than dressed up.

**A caveat on the negative controls.** The first matrix pass reported
that no control survived, which is what makes the refutations
meaningful. That claim has since been *narrowed*: four of the eight
signals did not read the inversion flag, so those controls were
byte-identical to their twins and could not fail. The controls for C3,
C4, C5 and C6 were genuine and all failed; the controls for C1, C2 and
C7 are being re-run against fixed code. The report states which
controls executed and which were no-ops, so the discrimination claim
is always scoped to the controls that could actually fail.

See `reports/PAPER_CONCEPT_REPORT.md` for the full matrix and
`reports/charts/paper_concepts.html` for the visual presentation.

---

## Quick start

Three commands do most of the work.

```bash
cd C:/Users/HP/AppData/Local/hermes/projects/leapspace-quant

# 1. Is there a trade? -> a decision brief with entry, exit, invalidation
python -m leapspace.cli signal --token DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263 --chain solana --target-usd 1000

# 2. Is this wallet actually skilled, or did it get lucky once?
python -m leapspace.cli edge --wallet 0xAf2358e9868326...

# 3. Run the paper-derived strategies against live data
python -m leapspace.cli backtest --all
```

A real brief from the first command:

```
## VERDICT: WATCH   (confidence: LOW)
> a research prior exists but no qualified wallet holds this token -
  the prior alone is not a signal

| Evidence leg   | Verdict | Detail |
|----------------|---------|--------|
| IDENTITY       | SUPPORT | Bonk on orca, pool $278,277, price $2.762e-06 |
| RESEARCH_EDGE  | SUPPORT | 2 specification(s) survived the FULL gauntlet |
| QUALIFIED_WALLETS | CONFLICT | NO qualified wallet holds this token |
| NARRATIVE      | SUPPORT | specificity 9.0 of 5.0 needed for niche |
| TRACTION       | SUPPORT | community 43,585; 24h buy/sell 1.303 |
| HOLDER_RISK    | neutral | top 10 holders control 39.0% of supply |
| LIQUIDITY      | SUPPORT | $278,277 pool supports a $1,000 position |
| DATA_QUALITY   | SUPPORT | 7/7 evidence legs answered (7 live) |

ENTRY: NOT EVIDENCE-BASED - no qualified wallet holds this token
POSITION: ZERO. The verdict is not ENTER.
```

Note what that brief does **not** do: it does not invent an entry price.

---

## What this is not

- **Not a trading system.** There is no exchange integration, no order
  placement, no position reconciliation, no venue balance check.
- **Not a source of tradeable alpha.** The two surviving specifications
  are equity/sector-rotation rules validated on historical bars. They
  establish a *non-random prior*, nothing more. The package's own
  verdict semantics say a SUPPORTED specification warrants **paper**
  trading and never live trading.
- **Not a memcoin alpha source yet.** Every wallet screened was a
  fluke. The memecoin layer can tell you *why* a token is dangerous; it
  cannot yet tell you a token is good.
- **Not investment advice.** It is decision support.

See [LIVE_CAPITAL_READINESS.md](LIVE_CAPITAL_READINESS.md) for the
stage-gated path from here to real capital, with exit criteria.

---

## The two legs of evidence

A trade is only worth taking if **both** legs are present. Neither
alone is sufficient, and this package refuses to act when one is
missing.

### Leg 1 — Research edge (the rules)

The seven supplied papers, distilled into 13 executable specifications
with a mandatory intake gate: every parameter must cite its source, or
be tagged `ANALYST_CHOICE`, or be declared "unspecified in source".

Validation is not optional. Each specification is put through a gauntlet:
walk-forward out-of-sample folds, cost stress, a causality audit that
looks for look-ahead, Monte Carlo, and a parameter sweep. A quick run
that skips these is labelled **quick-only** everywhere it appears.

```
regime_switch_cross_sectional_sector_rotation   SUPPORTED  (2,089 trades, Sharpe 0.61, OOS 0.53, 5/5 folds)
nasdaq_12m_timeseries_momentum                   SUPPORTED  (71 trades, Sharpe 0.63, OOS 0.90, 4/5 folds)
v1_crypto_momentum_20d_ma                        FRAGILE   (1,328 trades, Sharpe 0.75, OOS 0.78, 3/5 folds)
```

### Leg 2 — Qualified wallet behaviour (the accounts)

This is the leg that can set a **price**. A wallet qualifies only if it
passes a consistency gate built on cited standards:

| Test | Threshold | Source |
|---|---|---|
| Bayesian skill probability | ≥ 0.95 | Barber/Bay/Solberg, *Bayes Rules* |
| Deflated Sharpe Ratio | ≥ 0.95 | Bailey & López de Prado |
| Largest single win as a share of total profit | ≤ 0.5 | fluke control |
| Edge decay, recent vs early expectancy | ratio ≥ 0.5 | decay control |
| Independent bets | ≥ 5 (NIST bar: **637** for a 55%-vs-flip claim) | NIST/SEMATECH |
| Probability of Backtest Overfitting | ≤ 0.05 | Bailey/Borwein/López de Prado/Zhu |
| Wilson interval on win rate | lower bound above chance | NIST |
| Survivorship-selected universe | rejected | Bailey/López de Prado |
| Backfilled / pre-listing performance | rejected | Bailey/López de Prado |

**Independent bets, not raw trades.** A "bet" is flat-to-flat within
one asset, and the effective sample is further reduced to the maximum
set of mutually non-overlapping holding intervals across assets. One
wallet with 18 raw closes and 1 independent bet is not a trader.

Only wallets that pass contribute entry levels, hold durations and exit
behaviour to a brief. That is why the brief above says
"NOT EVIDENCE-BASED" instead of quoting a number.

---

## Provenance rules

Non-negotiable, and enforced in code:

- Every datum carries `LIVE` / `CACHE` / `SYNTHETIC`.
- A source that cannot be reached produces an **unavailable** record,
  never a plausible-looking number.
- An unavailable metric is **unmeasured, not zero** — an empty
  Telegram channel and an unreachable one are different facts.
- Synthetic data carries an explicit disclosure in every artefact that
  contains it.
- A parameter from a paper is quoted. A parameter the paper does not
  specify is declared "unspecified in source". A rule the analyst
  invented is tagged `ANALYST_CHOICE`.
- An unpriceable trade is `null` / `UNPRICED` — never valued at
  today's price.

---

## Architecture

```
leapspace/
  provenance.py      LIVE/CACHE/SYNTHETIC records
  http.py            browser-UA HTTP, retries, gzip, disk cache, secret redaction
  stats.py           shared numerics: norm_cdf, norm_ppf, binomial tail, DSR
  criteria.py        31 authority-tagged criteria loaded from data/
  pbo.py             CSCV / Probability of Backtest Overfitting, BH, Bonferroni
  edge.py            the consistency gate - 11 fluke tests
  whitelist.py       persistent cross-chain registry of qualified traders
  traders.py         NIST sample size, Wilson interval, GIPS retention
  priced.py          transfer history -> prices -> FIFO cost basis -> PnL
  priceatblock.py    historical USD price from DEX pool reserves at a block
  memecoinscan.py    holder cohorts, entity classification, wallet profiles
  launchscan.py      early-buyer discovery for NEW memecoins
  crosschain.py      cross-chain wallet identity scoring
  social.py          narrative vs traction, kept separate
  socialedge.py      community size, lead/lag, three comparators
  narrative.py       cohort-relative narrative classifier
  holders.py         holder composition over time, ownership shifts
  chainregistry.py   52 chains, L1/L2/appchain token-network separation
  deployers.py       creator discovery, registry seeded from on-chain data
  regime.py          Gaussian HMM market regimes (Baum-Welch)
  gamma.py           dealer gamma exposure, max pain, option flow
  disclosure.py      US officials' financial disclosures, all 3 branches
  backtest.py        13 specs + the validation gauntlet
  friction.py        fee/slippage/MEV/rug simulation
  riskguard.py       kill switch, anomaly detection
  biasaudit.py       look-ahead and survivorship auditor
  signal.py          THE TRADE-DECISION ENGINE
  viz.py             charts + self-contained HTML dashboard
  report*.py         markdown/JSON reporting
  quant.py cli.py    CLI surface
```

`stats.py` and `criteria.py` exist because duplicated numerics are a
correctness risk: if one copy of the inverse normal CDF is ever
corrected and the others are not, the package silently produces two
different answers to the same question. The extraction was done with a
numeric fingerprint taken before and after, and the values are
bit-identical.

---

## The seven papers and what each one drives

| Paper | Drives |
|---|---|
| Trading strategies for retail traders (LeapSpace) | v1 specs: 20-day MA, 1.0–1.5 SD bands |
| Trading strategies for retail traders (LeapSpace 2.0) | 6 new specs: momentum/reversal, cross-sectional rotation |
| Gamma exposure and option flow | `gamma.py` — net/gross/call/put gamma, zero gamma, exposure-adjusted flow |
| TradingView directional edge | direction/momentum feature set |
| Financial market regime identification | `regime.py` — 3–5 state Gaussian HMM |
| NASDAQ market regime identification | NASDAQ-specific regime spec |
| Meme coin trading strategies | `memecoin.py`, `launchscan.py`, the consistency gate |

**Important:** these seven documents are synthesis transcripts. They
contain **no original performance data and no numeric backtest
results**. Every backtest number this package produces is therefore
independent evidence, not a reproduction of the papers' claims.

---

## Where the evidence lives

```
reports/
  leapspace_report.md / .json          the main consolidated report
  memecoin_report.md / .json            9-section memecoin report
  backtest_results.json                 quick-validation verdicts
  full_gauntlet_results.json            FULL gauntlet verdicts
  pepe_priced_edge.json                 15 wallets, priced at the block
  gate_crosscheck.md                    independent gate cross-check
  PAPER_CONCEPT_REPORT.md               the 96-spec research matrix
  paper_concept_results.json            the raw matrix rows
  briefs/                               per-token trade briefs
  charts/                               PNG charts
  charts/dashboard.html                 self-contained dashboard
  charts/paper_concepts.html            the matrix dashboard (inline SVG)
```

State that persists between runs lives in `leapspace/state/`.

---

## The edge-finding layer

Four modules exist to answer one question: **is there an edge that
survives an industry-standard backtest?** They are new, and they are
the ones that matter for that question.

| Module | What it does |
|---|---|
| `leapspace/leading.py` | Measures the **volatility risk premium** — implied minus realised volatility — from a real, timestamped external series, aligned with a one-bar publication lag. Sources: Deribit DVOL (crypto), ^VIX / ^VXN / ^VXD (equities). Also a live dealer-gamma proxy and the live option-flow tape. |
| `leapspace/cryptoderivs.py` | The **crypto-native leading indicators**: perpetual-swap funding rate, annualised funding, funding z-score, open interest and open-interest change, from Bybit and Binance. All keyless, all with real history. Funding is the crypto analogue of the implied-volatility risk premium: it says how crowded the market is and what it costs to hold that crowding. |
| `leapspace/portfolio.py` | The **risk layer the engine lacked**. The backtest's portfolio block assumes zero correlation between assets, which overstates a diversified book's risk and makes risk parity impossible. This adds a shrunk covariance estimate, equal-risk-contribution sizing, a forward-weighted volatility estimate, a drawdown-responsive de-risking slope, and caps applied last — plus a risk report showing concentration, effective number of names, and per-name risk shares. |
| `leapspace/paperspecs.py` + `paperrun.py` + `paperreport.py` | The **matrix**: 8 testable claims from the research papers × 6 asset classes, each with an inverted-polarity negative control, run through the full gauntlet and rendered as a markdown report and an HTML dashboard. |

Two properties the leading layer holds to, because getting them wrong
is worse than not having the feature at all:

* **A measurement published after a bar never reaches that bar.** The
  alignment enforces a one-bar publication lag, and the realised side
  is shifted so no bar uses its own close.
* **A missing measurement is `None`, never `0`.** A zero premium reads
  as "options are fairly priced", which is a claim the data does not
  support.

`leapspace/tests/test_leading_causality.py` asserts the first property
directly, by truncation: cut the panel at bar *k* and the values at
bars ≤ *k* must be bit-identical. It also proves the old
whole-panel z-score would have failed the same test.

`LEADING_DATA_SOURCES.md` documents every source with its licensing,
timestamp semantics and — importantly — whether it was verified on this
host or is a known gap. ^V2TX is listed as a gap because the Yahoo
chart API 404s it.

---

## Free data only

Every source is free and keyless except the Etherscan key, which is
read from `.secrets.env` (gitignored, ACL-restricted, redacted from
all URLs and exceptions) and never appears in a source file, a report,
a chart or a log.

Sources that are **not** available and are reported as gaps rather than
filled in: Yahoo options (401), CBOE (timeout), Senate disclosures
(403), JEFS (registration-gated), X/Twitter metrics (no free tier),
CoinGecko community data (removed 2026-08-28).

---

## Tests

```bash
python -m compileall -q leapspace
for t in leapspace/tests/test_*.py leapspace/tests/check_*.py; do
  echo "--- $t"; python "$t" 2>&1 | tail -3
done
```

The suite includes live end-to-end tests against real endpoints, a
synthetic ground-truth suite for the consistency gate (6 cases: a
consistent wallet, a one-lucky-win fluke, a coin-flip, a decayer, and
two edge cases), an independent reference implementation of the gate
cross-checked against the package's own, and an intake-gate refusal
suite that proves the validator rejects specifications with stripped
provenance.

`leapspace/tests/check_quant_integration.py` is excluded from the loop
above because it makes live network calls that can take several
minutes on a slow link. Run it directly when you want the live
integration check.

### The pre-flight report validator

Every report is validated **before** it is written. If validation finds
errors, the report is still written, but it carries a machine-readable
block naming every error so nobody can mistake it for a clean report.

```bash
python -m leapspace.cli report --from-json reports/leapspace_report.json
```

The validator runs five checks from a vendored, unmodified, MIT-licensed
`data_quality_checker` skill (price scale, notation, dates, allocations,
units) plus three package-specific checks that upstream does not
implement:

| Check | What it catches |
|---|---|
| `base_unit_scale` | a token quantity in raw base units (1 token = 1e18 base units) compared against a whole-token price — the error class that once shipped a +30,833% return |
| `missing_not_zero` | `n/a` / `unavailable` rendered as `0`, which silently changes the arithmetic |
| `percent_scale` | one quantity stated twice in the two percentage scales with values that disagree |

The vendored code lives in `leapspace/vendor/data_quality_checker/` with
its own `NOTICE` file recording the upstream commit, licence and every
adapter decision. It is used **unmodified**; package-specific behaviour
lives in `leapspace/reportvalidate.py`.

The validator's own test suite proves it catches each defect class *and*
that it does not fire on legitimate documents:

```bash
python leapspace/tests/test_reportvalidate.py
```

---

## Repository

This is a **standalone repository**. It is not a subdirectory of, and
does not share history with, any other project.

```
https://github.com/P0ntix/leapspace-quant
```

Clone it anywhere and run it — the core is standard library only:

```bash
git clone https://github.com/P0ntix/leapspace-quant.git
cd leapspace-quant
python -m leapspace.cli --help
```

---

## Further reading

| Document | What it covers |
|---|---|
| [docs/DEEP_DIVE.md](docs/DEEP_DIVE.md) | the full operational reference (869 lines) |
| [LIVE_CAPITAL_READINESS.md](LIVE_CAPITAL_READINESS.md) | stage-gated path to real capital |
| [OPERATOR_BRIEF.md](OPERATOR_BRIEF.md) | the short operator summary |
| [MEME_TRADER_SCREENING_METHODOLOGY.md](MEME_TRADER_SCREENING_METHODOLOGY.md) | how a memecoin is screened |
| [AUTHORITATIVE_CONSISTENCY_STANDARDS.md](AUTHORITATIVE_CONSISTENCY_STANDARDS.md) | the cited standards behind every threshold |
| [FREE_DATA_SOURCES.md](FREE_DATA_SOURCES.md) | every free source, verified live |
| [CHAIN_LANDSCAPE.md](CHAIN_LANDSCAPE.md) | chain ranking and the L1/L2/appchain split |
| [NARRATIVE_EDGE_METHODOLOGY.md](NARRATIVE_EDGE_METHODOLOGY.md) | narrative vs social edge methodology |
| [CROSSCHAIN_WALLET_METHODS.md](CROSSCHAIN_WALLET_METHODS.md) | cross-chain identity scoring |
| [THIRD_PARTY_SKILL_COMPARISON.md](THIRD_PARTY_SKILL_COMPARISON.md) | what else exists, and what was chosen against it |

---

*Built by Hermes Agent. Every number in this document was produced by a
run you can reproduce with the commands shown above.*
