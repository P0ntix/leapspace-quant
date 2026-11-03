# Meme-Coin Paper Coverage Audit

**Paper:** *Meme coin trading strategies* (LeapSpace), 12 pages, 35 references.
**Implementation:** `leapspace/memecoin.py` (+ `leapspace/onchain.py` for the
per-wallet mechanisms it delegates to).

**Run the audit:** `python leapspace/tests/check_meme_paper_coverage.py`

The audit reads the actual source and verifies that the code claimed to
implement each clause exists. It does not assert coverage — it checks for
it, and it exits non-zero if a claim has no code behind it.

---

## Verdict

| Status | Count |
|---|---|
| **REAL** — a real data source measures the clause | 13 |
| **REAL (delegated)** — implemented in `onchain.py`, not auto-called | 3 |
| **REAL (estimated)** — computed, but from a stated approximation | 1 |
| **REAL (beyond the paper)** — implemented although the paper's evidence does not cover it | 1 |
| **PROXY** — only a proxy is available | 3 |
| **PARTIAL** — partly implemented | 3 |
| **MISSING** — not implemented | 2 |

**19 of 26 clauses are implemented.** The paper's five-layer framework was
present from the start, but the audit found **four clauses with no
implementation at all** and one that was proxy-only. All of those gaps have
since been closed — this document records what was missing and what now
covers it.

**The one clause that is still MISSING** is *"abrupt ownership changes
around price spikes"* [6][13]: it needs a holder-composition time series,
and the screener is stateless per call.

---

## What was MISSING, and what fixed it

### 1. The launchpad funnel — the paper's CENTRAL claim (Layer 4)

> "fewer than 2% of these tokens reached major DEXs… focus on predicting
> migration/survival rather than scanning every launch" [5]

**The gap:** the screener only ever saw tokens *already* on a DEX. It was
scanning the surviving 2% and calling it a funnel filter — the exact
opposite of the paper's instruction. The funnel itself was invisible.

**The fix** — `memecoin.fetch_migration_evidence()` plus
`memecoin.survival.launchpad_funnel`:

| Evidence | Source | What it measures |
|---|---|---|
| distinct DEX list, `n_dexes` | DexScreener `token-pairs/v1` | venue breadth |
| `has_major_dex` / `migrated` | `MAJOR_DEXES` set | has it passed the funnel? |
| `launchpad_origin` | `pumpswap`/`raydium-launchlab` + RugCheck `market_types` | did it START on a launchpad? |
| `first_pool_created` / age | Jupiter `firstPool` | how old is the launchpad pool |

**Verified live.** BONK: `dexes=[meteora, orca, raydium]`, migrated=True,
launchpad_origin=True (via RugCheck's `pump_fun_amm` market type — the
DexScreener DEX list alone missed it because the launchpad pool was
migrated). WIF: `dexes=[fluxbeam, meteora, orca, pumpswap, raydium]`,
launchpad_origin=True.

### 2. One-sided liquidity and wallet clustering (Layer 2)

> "one-sided liquidity, and suspicious wallet clustering" [6][7][13]

**The gap:** neither had a check. The layer only measured concentration.

**The fix:**

| Clause | Implementation |
|---|---|
| one-sided liquidity | `structural_safety.one_sided_liquidity.stable_liquidity_share` — RugCheck's stable liquidity ÷ total market liquidity. A book with almost no quote side cannot absorb a sell |
| suspicious wallet clustering | `structural_safety.graph_insiders_detected` — RugCheck's own wallet-graph cluster count |
| LP control by a small set | `structural_safety.lp_providers` — RugCheck `totalLPProviders` |

**Verified live.** WIF: stable share 28.0%, 65 LP providers, and
**7,195 wallets linked to insider clusters** → disqualifier fires with the
paper's own framing ("the paper's 'linked wallets control float' pattern").
BONK: 48 clusters, 94 LP providers — passes.

### 3. Slippage (Layer 3)

> "slippage and executable depth matter more than headline market cap" [10][12]

**The gap:** slippage was asserted in the layer's prose but never computed.

**The fix:** `exit_quality.estimated_price_impact_bps` — a constant-product
estimate (`notional / (2 × liquidity)`) at a configurable notional, with
the method string stating plainly that it ignores sell-side asymmetry and
is therefore a **lower bound** on realised slippage. It is an estimate,
not a quoted slippage curve, because no free endpoint publishes one.

**Verified live.** BONK 17.4 bps on $1,000; WIF 1.0 bps.

### 4. Narrative heat was proxy-only (Layer 1)

**The gap:** Layer 1 used only DexScreener volume acceleration.

**The fix:** `narrative_heat.REAL_SIGNALS` now carries **real** signals
from Jupiter: the `birdeye-trending` tag (a third-party trending signal —
the closest available analogue to "accelerating attention"), plus
`stats24h` buy/sell volume, `volumeChange` and `holderChange`.

**Verified live.** BONK: trending=True, buy/sell 1.092, holder change
+0.65%. WIF: trending=False, buy/sell 0.963, holder change +4.6%.

---

## Still MISSING (1 clause)

**"abrupt ownership changes around price spikes" [6][13]** — no
time-series of holder composition is maintained, so a change cannot be
detected. This needs periodic snapshots of the holder set per token,
which is a stateful job the screener does not currently do.

---

## The niche-community clause — how the "no baseline" objection was answered

The first audit recorded this as MISSING, with the reasoning: *"no free
source labels a token generic, so there's no baseline to compare
against."* That reasoning was half right and half wrong, and it was
fixable.

**Right:** no free source ASSIGNS a token a "generic" label.

**Wrong:** there are free sources of COMMUNITY FOOTPRINT, and the baseline
can be derived from the screened COHORT ITSELF rather than from an
external label set.

### What was built — `leapspace/narrative.py`

| Piece | What it does |
|---|---|
| `classify_specificity` | a disclosed, weighted classifier over free signals: Jupiter's `community` tag, social-platform diversity, a community channel (telegram/discord), a designed header image, a dedicated website, Jupiter verification — minus launchpad-random names and broad-trend keywords |
| `cohort_baseline` | the baseline the clause needed: the median and quartiles of the cohort's OWN specificity distribution |
| `relative_to_cohort` | places a token **by RANK** in that distribution, so ties cannot silently empty a bucket |
| `backward_association` | a clearly-labelled BACKWARD association between specificity and realised 24h performance |
| `save_cohort` / `verify_cohort` | the FORWARD test: a timestamped snapshot now, and a later run that measures forward returns between two snapshots |

### The taxonomy, and a correction to it

The first draft of `TREND_KEYWORDS` wrongly included *specific meme names*
(pepe, doge, shib, bonk, wif, inu, ape, milady) and subculture markers
(based, cult, rez). By the paper's own distinction those are **NICHE** — a
specific meme with its own community — not the broad-trend category. Only
mass themes (moon, pump, ai, elon, trump, btc, new, baby, safe, king)
belong in the list now.

### Live result — 29-token cohort across eight trend keywords

The classifier **discriminates**: scores span −1 to 9 across 10 distinct
values, 9 niche / 20 generic.

The per-cohort medians are the paper's distinction appearing directly in
the data:

| Cohort | median specificity | reading |
|---|---|---|
| `cat` | **7.0** | niche-heavy — "cat" is a specific animal meme with communities |
| `dog` | 3.0 | mixed |
| `elon` | 2.0 | mixed |
| `trump` | 1.0 | mostly generic |
| `meme` | −1.0 | pure trend clones |
| `moon` | **−1.0** | pure trend clones |

The bottom quartile **by rank** correctly isolates the trend clones:
`moon`, `MOON`, `ELON`, `TRUMP`, `meme`, and one `DOG`.

### Does the paper's PERFORMANCE claim hold on this sample?

The clause asserts niche tokens **outperform**. A filter that asserts a
performance relationship should be held to it.

- **Backward (h24, already realised):** niche median **−0.49%** vs
  generic **−3.74%** — a **+3.25pp** difference. `supports_claim: True`
  *on this sample*.
- **Forward:** wired and honest. `verify_cohort()` returns
  `"not yet measurable"` until two snapshots separated in time exist, and
  then measures forward returns. Until that measurement exists the
  verdict is never "no effect".

**The backward result is a small-sample association on a free dataset,
not evidence of causation.** A token may be niche *because* it already
ran. That is exactly why the forward harness exists.

### What running the forward test actually found

Running it surfaced two real bugs, both of which would have produced a
*wrong number* rather than an error:

**Bug 1 — the wrong endpoint.** `narrative --verify` re-priced tokens with
`market.fetch_dex_pairs(mint)`, which is DexScreener's **search** endpoint
(`/latest/dex/search?q=`). Given a mint address it usually returns
nothing or unrelated pairs: only **1 of 29** tokens got priced. The
correct per-token source is `/token-pairs/v1/{chain}/{token}`. Fixed — all
30 now price.

**Bug 2 — cross-pool comparison, which MANUFACTURES returns.** With the
endpoint fixed, one token showed a **+30,833%** move over a 2.4-hour
window. That is not a memecoin move. The snapshot and the current price
each selected "the pair with the most liquidity", and that ranking
changed in between — so two *different pools* were being compared as one
token.

The fix pins the **pool**: the snapshot records its `pair_address`, and
the forward test fetches that same pool. If the pool is gone, the token
is **skipped** rather than re-matched against another pool, because
falling back would silently reintroduce the bias. Tokens whose snapshot
predates the fix carry no pair address and are skipped with the reason
reported — 38 of them in the current history.

**Verified after the fix** (6 tokens, 200-second gap, same pool at both
ends):

| Metric | Cross-pool (broken) | Same-pool (fixed) |
|---|---|---|
| max \|return\| | **30,833%** | **0.0922%** |
| returns over 1000% | 1 | **0** |
| tokens priced from the same pool | — | 6 of 6, 0 skipped |

**Current status: the forward verdict is still PENDING**, because the new
snapshot with pool addresses is only minutes old and the test requires a
≥1-hour gap. The 38 pre-fix tokens are correctly refused rather than
used. Once the gap elapses, `python -m leapspace.cli narrative --verify`
produces the real forward number.

### Two things this test cannot do

- It measures **momentum in the next few hours**, which is not what the
  paper's [15] claim is about (it concerns a launch-to-migration horizon
  over a large Pump.fun sample). A 1–2 hour window is a plumbing test.
- The free sample is a **cross-section of currently-listed tokens** — the
  same survivorship trap the bias auditor flags elsewhere. Dead launches
  are absent by construction, so this sample cannot reproduce the paper's
  launch-level population.

## The last missing clause is now implemented

**"Abrupt ownership changes around price spikes"** was the one clause with
no implementation, because a stateless screener cannot detect a *change*.
The infrastructure now exists:

- `leapspace/holders.py` keeps a **timestamped holder-composition series**
  per token (`state/holder_series/<chain>_<mint>.json`). Each snapshot
  carries holder composition AND the price at the same moment.
- `holders.record_snapshot` appends one snapshot. Sources: RugCheck's full
  report on Solana (top holders with owning wallet, pct and insider flag),
  and ERC-20 Transfer-log reconstruction on EVM (Base's RPC names the range
  it will accept and the code uses it).
- `holders.detect_ownership_shifts` flags a window when the price moved
  past a spike threshold AND either concentration moved past a delta
  threshold OR a new address entered the top 10 (a swap of control).
- Detection thresholds are labelled `ANALYST_CHOICE - not a paper-stated
  value` in every output.

With fewer than two snapshots the detector reports
`insufficient_history` rather than filling anything in. A change needs two
observations; one observation is not a change.

### The narrative clause now measures COMMUNITY SIZE, not just link presence

The classifier originally scored "has a Telegram link". It now reads the
actual counts from two keyless public endpoints (Discord's invite API and
Telegram's public preview), so the clause is graded on membership:

- BONK — Telegram 11,009 members / 282 online, Discord 32,583 / 2,127,
  combined 43,592 across two platforms. Narrative score 7.0 → **11.0**,
  traction 4.5 → **7.0**.
- WIF — Telegram 25,795 / 481. Narrative 6.0 → **9.5**.

A nonexistent Telegram channel still returns HTTP 200 (its title reads
`Contact @name` rather than `View @name`), so the parser requires the
`View` title *and* a member count; an unmeasurable platform is reported
as unmeasured, never as zero.

**Audit status: 20/26 clauses implemented, 3 proxy only, 3 partial,
0 MISSING.**

## Still PARTIAL (3 clauses)

1. **Cross-venue arbitrage gaps** [16][17] — venue count is recorded, but
   no gap is measured between venues.
2. **Community-driven token retention** [32] — holders and organic score
   are recorded, not a retention measure.
3. **Wash trading: trade-size roundness / Benford irregularities** [14] —
   RugCheck's danger risks cover some of this; the specific detectors are
   not implemented.

## Still PROXY (3 clauses)

Generic sentiment, narrative specificity, and the 1–2 week attention decay
all need social data. There is no free reliable attention API, and the
layer is explicitly flagged `"PROXY": True` in its output so it can never
be misread as measured attention.

---

## Beyond the paper

Mint authority, freeze authority, renounced ownership and LP-lock status
are implemented as disqualifiers. **The paper explicitly says these are
NOT well covered in its retrieved evidence** [29] — so this goes beyond
what the paper supports, and the audit labels it
`REAL (beyond the paper)` rather than claiming paper backing.

---

## Standing limitations

- **Every threshold is an ANALYST CHOICE.** The paper states plainly that
  the short-horizon predictive thresholds for creator share, top-10
  concentration and first-hour imbalance are an open empirical question.
  All thresholds live in `memecoin.THRESHOLDS` and are returned with every
  screen.
- **This is a FILTER, not a validated return predictor.** The paper makes
  no claim that these filters predict returns, and neither does the code.
- **Solana only.** Jupiter and RugCheck are Solana sources. The
  multi-chain layer (`leapspace/chains.py`) covers Ethereum, Base, BSC and
  Arbitrum but has no meme-specific holder or risk source for them.
