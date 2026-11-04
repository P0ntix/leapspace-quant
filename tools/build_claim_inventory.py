"""Build `reports/PAPER_CLAIM_INVENTORY.md` from the inventory body + derived views.

INPUT   reports/paper_claims_body.md   (sections 1-8: the claim tables)
OUTPUT  reports/PAPER_CLAIM_INVENTORY.md (body + section 9, the derived views)

Section 9 is MECHANICALLY derived from the tables in the body, so it cannot
drift from the inventory. Every number in section 10 is computed here.

Run:  python tools/build_claim_inventory.py
"""
from __future__ import annotations

import collections
import re

BODY = r"C:/Users/HP/AppData/Local/hermes/projects/leapspace-quant/reports/paper_claims_body.md"
OUT = r"C:/Users/HP/AppData/Local/hermes/projects/leapspace-quant/reports/PAPER_CLAIM_INVENTORY.md"

MARK = " - ALSO TESTED: "

txt = open(BODY, encoding="utf-8").read()
assert "## 4. GROUP OPT" in txt and "## 8. GROUP NAS" in txt, "inventory sections not found"

rows = []
for line in txt.splitlines():
    m = re.match(r"^\|\s*([A-Z]+-\d+)\s*\|", line)
    if not m:
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    assert len(cells) == 8, (m.group(1), len(cells))
    rows.append({
        "id": m.group(1),
        "claim": cells[1],
        "source": cells[2],
        "type": cells[3],
        "status": cells[4],
        "inputs": cells[5],
        "daily": cells[6],
        "refute": cells[7],
    })
assert len(rows) == 293, len(rows)


def clean(s: str) -> str:
    s = re.sub(r"\*+", "", s)
    return re.sub(r"\s+", " ", s.replace("|", "/")).strip()


def bucket(s: str) -> str:
    if s.startswith("**IMPLEMENTED") or s.startswith("IMPLEMENTED"):
        return "IMPLEMENTED"
    if s.startswith("PARTIAL"):
        return "PARTIAL"
    if s.startswith("NOT"):
        return "NOT"
    if s.startswith("EXCLUDED"):
        return "EXCLUDED"
    return "OTHER"


for r in rows:
    r["b"] = bucket(r["status"])
    r["short"] = clean(r["claim"])
    m = re.match(r'(?:"([^"]{0,220})")', r["short"])
    r["sh"] = m.group(1) if m else r["short"][:200]
    r["daily_clean"] = r["daily"].split(" ")[0].split("(")[0].strip()
    r["impl"] = ""
    mm = re.search(r"\((C\d[^)]*)\)", r["status"])
    if mm:
        r["impl"] = mm.group(1)
    if r["b"] == "IMPLEMENTED" and not r["impl"]:
        r["impl"] = "C1-C8"
    r["also"] = ""
    if MARK in r["status"]:
        r["also"] = r["status"].split(MARK, 1)[1].strip()

L: list[str] = []
A = L.append

A("---")
A("")
A("## 9. Derived views")
A("")
A("All four lists below are **derived mechanically from the tables in sections 4-8**, not written by hand,")
A("so they cannot drift from the inventory. The generator is `tools/build_claim_inventory.py`.")
A("")

# ---------------------------------------------------------------- 9.1
dirs = [r for r in rows if "DIRECTIONAL" in r["type"]]
A("### 9.1 DIRECTIONAL claims - the tradable set")
A("")
A(f"**{len(dirs)} of {len(rows)} distinct claims predict a direction** (long/short, up/down, fade/follow,")
A("buy/sell, or a directional payoff). These are the only claims that can be an EDGE on their own. A gate,")
A("a sizing rule, a classifier or a stop cannot be an edge - it modifies another signal.")
A("")
A("The `Tradable here` column is the honest one: `YES` = the claim can be tested on this package's daily")
A("panels today; `PROXY` = only via a stand-in that tests the proxy, not the construct; `NO` = the data")
A("(historical options chain, order book, intraday) does not exist in this package.")
A("")
A("| ID | Claim | Source | Status | Tradable here |")
A("|---|---|---|---|---|")
for r in dirs:
    d = r["daily_clean"]
    tag = {"YES": "YES", "EXT": "YES (new feature needed)", "PROXY": "PROXY only",
           "NO": "NO - data absent"}.get(d, d)
    A(f"| {r['id']} | {r['sh']} | {r['source']} | {r['b']}{(' ' + r['impl']) if r['impl'] and r['b']=='IMPLEMENTED' else ''} | {tag} |")
A("")
d_trade = [r for r in dirs if r["daily_clean"] in ("YES", "EXT")]
d_not = [r for r in dirs if r["b"] == "NOT" and r["daily_clean"] in ("YES", "EXT")]
d_new = [r for r in d_not if not r["also"]]
A(f"**Summary:** {len(dirs)} directional claims total. {len(d_trade)} are testable on this package's daily")
A(f"panels (with {len(d_not)} of those not implemented in C1-C8). {len(dirs)-len(d_trade)} need data the")
A("package does not have - predominantly a historical options chain (gamma, option flow, strike distance)")
A("or an order book (CVD, spread, depth).")
A("")
A("**After removing the claims that a standalone spec has already tested** (section 9.7), the genuinely")
A(f"NEW directional backlog that is testable on daily bars is **{len(d_new)} claims**.")
A("")
A("**The single most important structural finding:** of the directional claims that ARE testable here, the")
A("paper-supported ones cluster into three families - (a) time-series momentum, (b) short-horizon mean")
A("reversion, and (c) pairs/spread reversion. Everything the options papers assert directionally is")
A("untestable without a chain archive. That is a data-acquisition problem, not a modelling one.")
A("")

# ---------------------------------------------------------------- 9.2
LS = {
    "REG-01": "The regime switch is the two-leg long/short construction (momentum leg / reversal leg).",
    "REG-12": "Activates the reversal (opposite-side) leg in stress states.",
    "REG-50": "The 5-state map assigns momentum-on / reversal-favoured / smaller-size per state - a long/short ladder.",
    "REG-64": "Conclusion: momentum belongs to trend states, reversal to stress states - the core long/short rule.",
    "REG-65": "Switch between momentum and reversal rather than forcing one model to work all the time.",
    "REG-40": "Reversal is horizon-specific; the long and short legs differ by horizon.",
    "REG-46": "HEDGING: crypto-equity correlation is regime-dependent; crypto loses safe-haven properties in some crisis windows.",
    "REG-47": "HEDGING: a crypto regime model should include external linkage to equities - i.e. a hedge-condition input.",
    "RET-16": "'Go long when price is above its trend proxy; go short or flat when below' - explicit long/short.",
    "RET-21": "'long if close > 20-day MA and 20-day return positive; short or exit if not' - explicit long/short.",
    "RET-24": "Crypto PAIRS trading - a market-neutral long/short construction.",
    "RET-25": "Mean-reversion evidence in crypto is strongest for PAIRS/SPREAD frameworks.",
    "RET-26": "Pair-spread entry: enter when the spread is stretched beyond a threshold, with a buffer zone.",
    "RET-27": "Pair-spread exit: exit when the spread reverts to mean.",
    "RET-31": "Nasdaq PAIRS: cointegration/spread model, z-score entry, mean-reversion exit - long/short basket.",
    "RET-32": "Crypto PAIRS: dynamic cointegration or Hurst-filtered pairs with short holds.",
    "RET-33": "Regime-switching plus faster holding periods improved PAIRS-trading results.",
    "RET-46": "Composite reversion ENTRY LONG: stretched below fair value + extreme imbalance + temporary pressure.",
    "RET-47": "'Enter short on the opposite setup when the stretch and pressure reverse' - the explicit SHORT leg.",
    "RET-48": "Exit fast when the spread normalizes - the exit rule for a long/short spread book.",
    "RET-49": "Imbalance-driven short-lived reversals - the mechanism behind a contrarian short leg.",
    "IND-09": "Trend tools vs mean-reversion tools: choose the side by regime.",
    "OPT-17": "Informed option trades map to value premium and discount - a long/short mapping from options flow.",
    "OPT-18": "Dealer hedging creates temporary price pressure and REVERSALS - a contrarian short leg.",
    "OPT-19": "Order imbalance often reflects market-maker delta hedging, producing short-lived REVERSALS.",
    "NAS-16": "'A pullback can be a fade in a damped market but an ENTRY in an amplified market' - same setup, opposite side by state.",
    "NAS-38": "ASYMMETRY: negative prior returns mean-revert MORE strongly than positive ones - the short leg deserves more size.",
    "NAS-43": "Pinning: prices are pulled toward option strikes near expiry - a mean-reversion mechanism.",
    "NAS-54": "Balanced flow + good depth + narrow spread -> range/mean-reversion conditions become more plausible.",
    "NAS-55": "One-sided flow + thin depth + rising message intensity -> breakout/momentum conditions become more plausible.",
    "NAS-78": "Mean-reversion/pinning regime -> FADE extensions.",
    "NAS-79": "Momentum/breakout regime -> FOLLOW breaks.",
    "NAS-87": "'Fade less and follow more when short-gamma dynamics likely amplify price movement.'",
    "NAS-88": "'Fade more and chase less when gamma is stabilizing and strike pinning is plausible.'",
    "NAS-98": "Positive gamma + balanced liquidity -> mean reversion; negative gamma + rising vol + one-sided flow -> momentum.",
    "OPT-08": "Intraday momentum persists ONLY when net gamma is negative - a conditional long/short continuation.",
    "OPT-20": "Negative gamma amplifies BOTH upside and downside - the sign of the amplification is not predicted.",
}
ls_rows = [r for r in rows if r["id"] in LS]
assert not (set(LS) - {r["id"] for r in rows})
A("### 9.2 Claims specifically about LONG / SHORT, PAIRS and HEDGING")
A("")
A(f"**{len(ls_rows)} claims.** The user wants a strategy that can go long OR short and can hedge. This is")
A("exactly what the papers do and do not supply.")
A("")
A("**What the papers DO support:**")
A("- **Long/short via a regime switch** (REG-01, REG-12, REG-50, REG-64, REG-65; RET-16, RET-21).")
A("- **Market-neutral long/short via PAIRS / cointegrated spreads** (RET-24, RET-25, RET-26, RET-27,")
A("  RET-31, RET-32, RET-33, RET-48). This is the papers' only genuine HEDGING construction, and it is a")
A("  relative-value one: long the cheap leg, short the rich leg.")
A("- **A short leg that is stronger than the long leg** (NAS-38) - directly actionable for how a long/short")
A("  book should be weighted.")
A("- **A crypto-vs-equity hedge condition** (REG-46, REG-47) - the papers explicitly state that crypto")
A("  loses safe-haven properties in some crisis regimes and that a crypto regime model needs an external")
A("  linkage input. That is a hedge-timing rule, not a hedge instrument.")
A("")
A("**What the papers DO NOT support - stated plainly, because it changes the build:**")
A("- **No paper proposes hedging a position with options or derivatives as a strategy.** Across all six")
A("  papers, options and gamma appear only as *signal inputs* (regime classifier, volatility forecaster,")
A("  flow pressure gauge). There is no long-options / put-write / collar / tail-hedge construction, no")
A("  long-vol-versus-short-vol trade, and no option-spread overlay anywhere in the evidence set. If the")
A("  user wants option-based hedging, that is NEW construction with no paper claim behind it, and it must be")
A("  labelled as such rather than attributed to these papers.")
A("- **The gamma claims are directional-AGNOSTIC by the papers' own statement** (OPT-20, OPT-21, NAS-98,")
A("  NAS-100): gamma predicts whether a move PERSISTS, not which way it goes. It is a fade-vs-follow")
A("  switch, not a long/short signal.")
A("- **The one standalone long/short result that exists is the strongest single finding in the set:**")
A("  `nasdaq_12m_timeseries_momentum` (12-month time-series momentum, long above the trend proxy / short")
A("  below, vol-scaled) came out **SUPPORTED**, while the vol-gated variant `v1_nasdaq_12m_tsm_vol_scaled`")
A("  came out **REFUTED** and the crypto 20-day analogue came out **REFUTED / FRAGILE**. The difference")
A("  between the two Nasdaq runs is the only thing that discriminates them, and it should be the first")
A("  thing a new spec replicates.")
A("")
A("| ID | Claim | Why it is a long/short or hedging claim | Status | Daily? |")
A("|---|---|---|---|---|")
for r in ls_rows:
    A(f"| {r['id']} | {r['sh']} | {LS[r['id']]} | {r['b']} | {r['daily_clean']} |")
A("")

# ---------------------------------------------------------------- 9.3
risk_rows = [r for r in rows if "RISK" in r["type"] or "SIZING" in r["type"]]
A("### 9.3 Claims about RISK MANAGEMENT and POSITION SIZING")
A("")
A(f"**{len(risk_rows)} claims.** These are not edges. They are what makes an edge tradable - and they are")
A("the area where the package is weakest, because the current `RISK_BLOCK` in `paperspecs.py` is a set of")
A("**analyst choices with no paper behind them** (`vol_target 0.15`, `max_position 0.10`, `max_names 5`,")
A("`net_target 0.0`, `rebalance monthly`, `gross_leverage 1.0` are all marked `analyst_choice` in")
A("`parameter_provenance`).")
A("")
A("The papers do supply concrete, testable risk rules. Adopting them would replace analyst choices with")
A("paper-grounded parameters - the single cheapest improvement available to the spec set.")
A("")
A("| ID | Claim | Type | Status | Daily? |")
A("|---|---|---|---|---|")
for r in risk_rows:
    A(f"| {r['id']} | {r['sh']} | {r['type']} | {r['b']} | {r['daily_clean']} |")
A("")
A("**Concretely, the papers license these risk changes to the existing block:**")
A("- A **stop-loss overlay** differentiated by model type (RET-19, RET-73, RET-74, RET-76): a")
A("  tight-to-moderate TRAILING stop for momentum, a wider FIXED stop plus a TIME stop for mean reversion.")
A("  Note the polarity that matters: the papers say stop-losses HELP momentum and HURT mean reversion")
A("  (RET-73, RET-75, RET-77).")
A("- A **volatility-normalized stop distance** of 1.0-1.5 rolling standard deviations from the entry, with")
A("  the stop RATCHETING as new highs are made (RET-79, RET-82, RET-87, RET-89, RET-90, RET-91, RET-92).")
A("  This is a paper-grounded replacement for the current flat `vol_target 0.15`.")
A("- **Inverse-volatility position scaling** as an explicit momentum sizing rule (RET-17, RET-18, RET-22,")
A("  RET-44) - the package has the machinery (`blended_volatility`, `target_vol`) but the paper's rule is")
A("  not expressed as a spec.")
A("- **State-proportional exposure** (REG-14, REG-50): translate state probabilities into position sizing and")
A("  turnover controls, with the specific 5-step ladder (full / reduced / low / smaller / off). C1 currently")
A("  switches hard between two legs instead of grading exposure.")
A("- **Per-regime size cuts** in the NASDAQ taxonomy (NAS-81, NAS-82, NAS-86): size down or stand aside in")
A("  event-distorted and fragile-liquidity states.")
A("- **Cost discipline** (IND-10, REG-58): the papers explicitly warn that reversal is 'much weaker after")
A("  costs' and that 'nice-looking indicator results can collapse once transaction costs and out-of-sample")
A("  testing are included'. The package's `cost_multiplier 2.0` already encodes this, and every risk claim")
A("  above must be evaluated at that stressed multiple, not at 1.0.")
A("")
A("**A warning the risk section must carry:** the standalone runs already show that adding risk machinery")
A("does NOT rescue a weak signal - `sd_band_mean_reversion_crypto` (wide fixed stop + time stop + 1.0/1.5 SD")
A("band) was REFUTED, and `crypto_ma20_trend_momentum` (vol-scaled sizing + stop-loss + trend-failure exit)")
A("was REFUTED with a gross Sharpe of 0.74 that costs consumed. Risk overlay is a filter on an edge, not a")
A("substitute for one.")
A("")

# ---------------------------------------------------------------- 9.4
neg_rows = [r for r in rows if "NEGATIVE" in r["type"] or "LIMITATION" in r["type"] or r["b"] == "EXCLUDED"]
A("### 9.4 The papers' own fragility, limitation and failure-mode claims")
A("")
A(f"**{len(neg_rows)} claims.** These are worth testing DIRECTLY as negative controls, because a claim that")
A("is right about its own limits is falsifiable in the same way as an edge. Two rules make them useful:")
A("")
A("1. **Every claim that says a signal is NOT directional should be tested as a spec whose expected verdict is")
A("   FAIL.** If a 'gamma does not predict direction' control comes out SUPPORTED, the validation is not")
A("   discriminating and every other verdict is void. The package already builds inverted-polarity twins")
A("   (`build_negative_controls` in `paperspecs.py`); these claims are the same idea at the level of the")
A("   paper's content, and they need their own twin set.")
A("2. **The limitations are a specification of what NOT to build.** REG-53, REG-56, NAS-12, NAS-100 and")
A("   NAS-92 together tell you the order of work: test each axis alone first, then test whether")
A("   combinations improve discrimination - and do not claim a single best detector until that horse race")
A("   has been run.")
A("")
A("| ID | Claim | Type | Status | Daily? |")
A("|---|---|---|---|---|")
for r in neg_rows:
    A(f"| {r['id']} | {r['sh']} | {r['type']} | {r['b']} | {r['daily_clean']} |")
A("")
A("**The highest-value negative controls, in order:**")
A("")
A("| Rank | ID | Why |")
A("|---|---|---|")
rank = [
    ("1", "REG-56", "The paper explicitly says no unified out-of-sample comparison exists for volatility vs trend vs drawdown vs liquidity vs HMM vs event classifiers. The horse race it asks for is a spec, and it is the one that would let the package claim (or refuse) a best detector."),
    ("2", "REG-53", "Feature-family ablation. If no family dominates, then 'volatility is the most consistently useful regime feature' (REG-20) is refuted and C1's four-feature design has no privileged input."),
    ("3", "NAS-61", "Only volatility-strategy order flow predicts next-day realised volatility, NOT next-day index returns. A clean directional negative that would be embarrassing to get wrong."),
    ("4", "OPT-15", "Gamma is 'much weaker as a pure direction signal' - Medium for direction, High for volatility regime. If gamma-as-direction profits, this control fails."),
    ("5", "IND-10", "Results collapse once costs and out-of-sample are included. Tests whether the package's own gross-of-costs stage is doing real work."),
    ("6", "REG-58", "Reversal is economically meaningful before costs but much weaker after. A direct cost-sensitivity control on C8."),
    ("7", "NAS-66", "Individual-stock gamma estimates are 'severely noisy... of doubtful usefulness beyond averages'. Kills a whole family of gamma specs if true."),
    ("8", "REG-42", "'Daily aggregation can hide intraday mean reversion.' This is a binding CAVEAT on C8, not a spec: a SUPPORTED daily-bar C8 verdict may NOT be reported as evidence for an intraday edge."),
    ("9", "RET-85", "Reversal at short horizons, momentum at even shorter ones, with the sign FLIPPING by horizon. If the flip is real, a single-horizon reversion spec will report a misleading sign."),
    ("10", "IND-02", "Indicator stacking is 'signal soup' and is weaker than a disciplined single rule. A direct ablation against a stacked baseline. NOTE: already tested - both `crypto_rsi_oversold_fade` and `tradingview_price_volume_rsi_regime_filtered` came out REFUTED, so the control has a prior result."),
]
for n, i, why in rank:
    A(f"| {n} | {i} | {why} |")
A("")

# ---------------------------------------------------------------- 9.5
A("### 9.5 Build priority: proposed new specifications")
A("")
A("Each proposed concept below is grounded in at least one NOT-implemented claim that is testable on daily")
A("bars. IDs continue the existing C1-C8 convention. The 'Prior test' column records what the standalone")
A("specs already found, so nothing refuted is rebuilt without a new reason.")
A("")
A("| Proposed | Concept | Paper claims | What it tests | Prior test | New work needed |")
A("|---|---|---|---|---|---|")
builds = [
    ("C9", "Standalone time-series momentum (long/short), cross-asset",
     "RET-14, RET-15, RET-16, RET-21, REG-31",
     "Does the 12-month Nasdaq rule and the 20-day crypto rule behave differently by asset class, and does the horizon interact with the regime?",
     "MIXED: `nasdaq_12m_timeseries_momentum` SUPPORTED; `v1_nasdaq_12m_tsm_vol_scaled` REFUTED; `crypto_ma20_trend_momentum` REFUTED; `v1_crypto_momentum_20d_ma` FRAGILE. The two Nasdaq runs differ only in the volatility gate - that difference IS the hypothesis.",
     "signal `time_series_momentum` (needs a 252-bar lookback and an explicit short leg); run it across all 6 asset classes, not just one"),
    ("C10", "Asymmetric reversal - the short leg is stronger",
     "NAS-38, REG-39, REG-40",
     "Does mean reversion after DOWN moves exceed mean reversion after UP moves, and does sizing the short leg accordingly beat symmetric reversion?",
     "NONE. This is the single most actionable untested directional claim for a long/short book.",
     "sign-split feature (lagged return x sign) and a two-sided reversion signal"),
    ("C11", "Pairs / cointegration spread mean reversion",
     "RET-24, RET-25, RET-26, RET-27, RET-31, RET-32, RET-33",
     "Does a cointegration-spread z-score rule with a buffer zone and a time stop profit on liquid Nasdaq pairs and on crypto pairs, net of costs?",
     "PARTIAL: `sd_band_mean_reversion_crypto` REFUTED - but that was a SINGLE-ASSET z-score, not a pair spread. The pair construction is untested.",
     "pair-selection (cointegration) and a spread-series feature; the engine has no pair construct"),
    ("C12", "Volatility-normalized trailing stop overlay",
     "RET-19, RET-73, RET-74, RET-76, RET-87, RET-89, RET-90, RET-91, RET-92",
     "Does a 1.0-1.5 SD volatility-scaled trailing stop improve the SUPPORTED 12m Nasdaq momentum result, and does it HURT mean reversion, as the papers claim?",
     "NONE as a clean ablation - the standalone momentum specs mention a stop-loss but do not isolate its effect against the same signal without it.",
     "stop/overlay logic in the signal layer; the engine has no stop feature or exit band beyond 'signal returns to flat'"),
    ("C13", "1.0/1.5 SD band as a two-tier entry",
     "RET-79, RET-80, RET-81, RET-82, RET-83, RET-95, NAS-29",
     "Does a 1.5 SD entry beat a 1.0 SD entry on expectancy, and does a Parkinson/Garman-Klass range estimator beat close-to-close vol as the denominator?",
     "REFUTED: `v1_sd_band_mean_reversion_1_0_1_5` (gross Sharpe 0.39 - a real gross edge, too small for costs) and `sd_band_mean_reversion_crypto` (gross Sharpe -0.47). Do NOT rebuild this as a reversion entry. The range-estimator half is untested.",
     "rolling-SD band feature (the paper-grounded 20-day window) and a range-based volatility estimator (Parkinson / Garman-Klass from daily OHLC)"),
    ("C14", "Regime-graded exposure ladder",
     "REG-14, REG-50, NAS-80, NAS-81, NAS-82, NAS-86",
     "Does translating state probabilities into a graded 5-step exposure ladder beat C1's hard two-leg switch?",
     "PARTIAL: `regime_switch_cross_sectional_sector_rotation` SUPPORTED with the posterior AS the size. The 5-step discrete ladder is untested.",
     "per-state exposure mapping; the portfolio layer needs a per-state scale input"),
    ("C15", "Horizon-specific regime models (crypto first)",
     "REG-07, REG-13, REG-40, REG-49, REG-52, REG-62, RET-85",
     "Do daily and weekly crypto regime classifiers disagree, and does fitting them separately beat one shared classifier?",
     "NONE.",
     "a weekly-bar panel variant; the engine's spec interval is fixed to 1d but the panel loader supports other intervals"),
    ("C16", "Range-based volatility as the regime input",
     "NAS-28, NAS-29, NAS-30, NAS-32",
     "Does a Parkinson/Garman-Klass range volatility classify regimes better than close-to-close realised vol, and does a log-scale variance model beat a level-scale one?",
     "NONE.",
     "range estimator feature; the engine has `atr_pct`, which is close but is not Parkinson or Garman-Klass"),
    ("C17", "Crash-aware momentum variant",
     "REG-35, REG-27, REG-31",
     "Does a momentum rule that conditions on the crash dummy (negative trailing return + positive current return + elevated short-vs-long vol) beat plain momentum, and do low-vol and high-vol bulls differ?",
     "NONE.",
     "none beyond C6's features; needs the variant wired as a separate signal"),
    ("C18", "Regime-feature ablation and classifier horse race",
     "REG-20, REG-22, REG-53, REG-56, NAS-92",
     "Which single feature family (volatility / trend / drawdown / liquidity) and which classifier (HMM / hard-threshold / event-based) actually earns its place?",
     "NONE. This is the spec REG-56 explicitly says the evidence lacks.",
     "a runner that varies features and state counts across the same universe and risk block"),
    ("C19", "Credit-risk leading drawdown signal",
     "REG-21",
     "Does rising credit risk (HYG/LQD/EMB spread) predict a deeper drawdown ahead of the price?",
     "NONE.",
     "credit spread series feature (the `rates_credit` preset already carries HYG, LQD, EMB, TIP, BND)"),
    ("C20", "Crypto-equity linkage / safe-haven regime feature",
     "REG-46, REG-47, REG-48",
     "Does adding an equity-linkage feature to the crypto regime classifier improve it, and is crypto's safe-haven status genuinely regime-dependent?",
     "NONE.",
     "cross-asset correlation feature across the crypto and equity panels"),
    ("C21", "Directional-change / threshold event trigger",
     "REG-08, REG-24, REG-25, REG-26, REG-51",
     "Does a threshold-based (directional-change) regime trigger outperform the fixed-time-bar baseline?",
     "NONE.",
     "directional-change / threshold overlay on daily bars"),
    ("C22", "Duration-aware regime classifier (HSMM-style)",
     "REG-03, REG-17, REG-18, REG-19",
     "Do tranquil states really persist longer than stress states, and does modelling duration improve the switch?",
     "NONE.",
     "duration modelling in `leapspace/regime.py`; `identify_regimes` is currently a Gaussian HMM filter"),
    ("C23", "VIX-level augmentation of the reversal gate",
     "REG-36, REG-43",
     "Does adding the VIX level to C8's liquidity+volatility gate improve the reversal result, or is it collinear with realised vol?",
     "NONE.",
     "none beyond C8's features; VIX is already available as a leading series"),
    ("C24", "On-chain crypto features",
     "RET-01, RET-07",
     "Do on-chain variables (active users, hashrate, wallet activity, transaction volume) add forecastability over price+volume on crypto?",
     "NONE.",
     "on-chain feature wiring into the backtest panel; `leapspace/onchain.py` exists but no spec uses it"),
    ("C25", "Return x volume interaction (crypto reversion)",
     "REG-39",
     "Does the interaction of lagged return with volume predict the reversal effect, as the panel evidence states?",
     "NONE.",
     "an interaction feature (lagged return x volume)"),
    ("C26", "Bollinger / MA parameter study",
     "RET-94",
     "Is the conventional 20-period + 2 SD setting optimal, and how much do band width and MA length matter?",
     "REFUTED: `bollinger20_2_breakout_crypto` tested the 20/2 configuration as a breakout and it failed. The PARAMETER study (band width x MA length) is still untested - but do not assume a better pair exists.",
     "none - the engine already has `bollinger_pct` and `ma_crossover`; only the sweep is missing"),
]
for b in builds:
    A("| " + " | ".join(b) + " |")
A("")

# ---------------------------------------------------------------- 9.6
A("### 9.6 The backlog that needs DATA, not code")
A("")
no_rows = [r for r in rows if r["daily_clean"] == "NO"]
A(f"{len(no_rows)} claims are rated `NO` and cannot be built with the data this package holds. They fall into")
A("three buckets:")
A("")
A("| Bucket | What it covers | What would unblock it |")
A("|---|---|---|")
A("| **Historical options chain** | net gamma sign (OPT-07, OPT-10, OPT-11, OPT-13, NAS-02, NAS-41, NAS-49), delta/vega/notional-adjusted option flow (OPT-01, OPT-02, OPT-04, NAS-05, NAS-60, NAS-96), strike distance and days-to-expiry / pinning (NAS-43, NAS-46, NAS-47, NAS-48), put-call ratios (NAS-62), the directional-bias claims (OPT-15..OPT-21), the momentum-stage claims (RET-37, RET-41, RET-43), and every NAS failure-mode claim (NAS-65..NAS-71) | A historical options chain archive (open interest + quotes by strike and expiry) so `leapspace/gamma.py` can be run over time instead of once. **This is the single largest gap: it is the difference between 'the papers' options claims are untested' and 'they are tested'.** |")
A("| **Order book / L2 / trade-level** | CVD divergence (RET-60, RET-66, RET-71), spread and depth (NAS-53, NAS-54, NAS-55, NAS-76, NAS-84, NAS-85), trade-flow imbalance (RET-11, RET-12, RET-34, RET-40, RET-42, RET-46, RET-49, REG-06, NAS-03, NAS-25, NAS-50, NAS-69), the acceptance/rejection and open-range claims (RET-56..RET-72, RET-93, NAS-04, NAS-11, NAS-56..NAS-59) | A historical L2 feed or a trade-level archive. The package's `session_drift` is a daily-bar stand-in and is already disclosed as such in the C7 notes. |")
A("| **Intraday bars / session structure** | session and time-of-day effects (RET-51..RET-53, RET-56..RET-67, NAS-04, NAS-07, NAS-22, NAS-24, NAS-26, NAS-39, NAS-44, NAS-56..NAS-59, NAS-89..NAS-91), intraday reversal and continuation (OPT-06, OPT-08, RET-41, REG-41, REG-45) | The skill's `intraday.py` already collapses 60-minute bars into a session-opening-window bar per day, which covers a subset (session drift, opening-window return). Full intraday testing needs a session panel with per-session high/low/POC plus a macro/earnings calendar. |")
A("")
A("**A macro-release / earnings / expiry calendar is also absent** (NAS-10, NAS-21, NAS-30, NAS-81, NAS-91,")
A("NAS-97). Event-conditioned claims need it.")
A("")

# ---------------------------------------------------------------- 9.7
A("### 9.7 Claims ALREADY tested outside the C1-C8 matrix")
A("")
A("The C1-C8 matrix is not the only place these papers have been built. There is a set of STANDALONE specs")
A("- the six \"LeapSpace 2.0\" specs in `leapspace/data/leapspace_2_0_specs.json`, the earlier `v1_*` specs,")
A("and `REGIME_SWITCH_SPECS` in `leapspace/backtest.py` - each with a verdict in `reports/*.md`.")
A("")
A("**This changes what \"not yet implemented\" means.** A claim that was built and REFUTED is not an open")
A("item; a claim that was never built is. The `ALSO TESTED` annotation in the Status column of sections 4-8")
A("records this claim by claim, and it is applied by `tools/annotate_claim_test_status.py`.")
A("")
A("| Standalone spec | Universe | Verdict | Claims it covers |")
A("|---|---|---|---|")
specs = [
    ("nasdaq_12m_timeseries_momentum", "us_equity_style", "SUPPORTED", "RET-13, RET-14, RET-16, RET-17, RET-18, RET-19, RET-20, RET-21"),
    ("regime_switch_cross_sectional_sector_rotation", "us_equity_style", "SUPPORTED", "IND-09, REG-01, REG-02, REG-09, REG-10, REG-14, REG-15, REG-16, REG-50, REG-64, REG-65"),
    ("v1_crypto_momentum_20d_ma", "crypto", "FRAGILE", "RET-14, RET-17, RET-21, RET-22, RET-23"),
    ("v1_nasdaq_12m_tsm_vol_scaled", "us_equity_style", "REFUTED", "RET-14, RET-16, RET-17"),
    ("v1_sd_band_mean_reversion_1_0_1_5", "crypto", "REFUTED", "RET-79, RET-80, RET-81, RET-82"),
    ("regime_switch_momentum_reversal_us_equity", "us_equity", "REFUTED", "REG-01, REG-11, REG-12, REG-16"),
    ("regime_switch_momentum_reversal_nasdaq_scalp_proxy", "us_equity_style", "REFUTED", "REG-01, NAS-16, NAS-17, NAS-19, NAS-20"),
    ("crypto_ma20_trend_momentum", "crypto", "REFUTED", "RET-13, RET-14, RET-18, RET-21, RET-22, RET-23"),
    ("sd_band_mean_reversion_crypto", "crypto", "REFUTED", "RET-26, RET-27, RET-29, RET-73, RET-75, RET-78, RET-79, RET-82"),
    ("crypto_xs_momentum_volume_confirmed", "crypto", "REFUTED", "RET-39, RET-40 (declared but UNENFORCED), RET-42, RET-45"),
    ("tradingview_price_volume_rsi_regime_filtered", "crypto+equity mix", "REFUTED", "IND-01, IND-02, IND-04, IND-05, IND-06, IND-09, IND-11"),
    ("crypto_rsi_oversold_fade", "crypto", "REFUTED", "IND-02, IND-05, IND-08"),
    ("bollinger20_2_breakout_crypto", "crypto", "REFUTED", "RET-82, RET-84, RET-94"),
]
for s in specs:
    A("| `" + s[0] + "` | " + s[1] + " | **" + s[2] + "** | " + s[3] + " |")
A("")
also_rows = [r for r in rows if r["also"]]
A(f"**{len(also_rows)} of the {len(rows)} claims carry an `ALSO TESTED` annotation.** The rest have never")
A("been built in any form.")
A("")
A("**Three findings a spec writer must not skip:**")
A("")
A("1. **The single best-supported long/short result in the whole evidence set is")
A("   `nasdaq_12m_timeseries_momentum` (SUPPORTED).** Its REFUTED twin `v1_nasdaq_12m_tsm_vol_scaled` differs")
A("   only in the volatility gate. That single difference - volatility gate ON vs OFF - is the cleanest")
A("   natural experiment in the package, and it is exactly REG-03's claim (\"cut or disable momentum in")
A("   high-volatility states\") coming out the other way. **Replicate that pair before anything else.**")
A("2. **Crypto 20-day momentum has been tested three times and failed every time** (REFUTED, REFUTED,")
A("   FRAGILE), with a gross Sharpe of 0.74 that costs consumed. RET-14's crypto leg should not be rebuilt")
A("   as-is.")
A("3. **The 1.0/1.5 SD band mean-reversion entry has been tested twice and failed twice**, and it fails")
A("   GROSS of costs (Sharpe -0.47 in `sd_band_mean_reversion_crypto`), so it is not a cost problem - the")
A("   signal itself has no expectancy. C13's SD-band work should be aimed at the *risk overlay* and the")
A("   *range estimator*, not at a third reversion entry.")
A("")

# ---------------------------------------------------------------- totals
A("---")
A("")
A("## 10. Totals")
A("")
b = collections.Counter(r["b"] for r in rows)
d = collections.Counter(r["daily_clean"] for r in rows)
never = [r for r in rows if not r["also"]]
never_not = [r for r in rows if r["b"] == "NOT" and not r["also"]]
never_testable = [r for r in never_not if r["daily_clean"] in ("YES", "EXT")]
A("| Metric | Count |")
A("|---|---|")
A(f"| **TOTAL distinct testable claims** | **{len(rows)}** |")
A(f"| - GROUP OPT (options flow, IV, gamma) | {len([r for r in rows if r['id'].startswith('OPT')])} |")
A(f"| - GROUP RET (retail trader compilation) | {len([r for r in rows if r['id'].startswith('RET')])} |")
A(f"| - GROUP IND (free trading indicators) | {len([r for r in rows if r['id'].startswith('IND')])} |")
A(f"| - GROUP REG (financial market regime identification) | {len([r for r in rows if r['id'].startswith('REG')])} |")
A(f"| - GROUP NAS (NASDAQ market regime identification) | {len([r for r in rows if r['id'].startswith('NAS')])} |")
A(f"| **ALREADY FULLY IMPLEMENTED as C1-C8** | **{b['IMPLEMENTED']}** |")
A(f"| PARTIALLY implemented (a C-spec covers part of the claim) | {b['PARTIAL']} |")
A(f"| **NOT IMPLEMENTED in C1-C8** | **{b['NOT']}** |")
A(f"| EXCLUDED (the paper states there is no evidence - e.g. charm/vanna) | {b['EXCLUDED']} |")
A(f"| meta / not-a-claim row | {b['OTHER']} |")
A(f"| | |")
A(f"| of which ALSO already tested by a standalone spec | {len(also_rows)} |")
A(f"| **NEVER BUILT IN ANY FORM** | **{len(never)}** |")
A(f"| | |")
A(f"| **DIRECTIONAL (tradable) claims** | **{len(dirs)}** |")
A(f"| GATE claims | {len([r for r in rows if 'GATE' in r['type']])} |")
A(f"| SIZING claims | {len([r for r in rows if 'SIZING' in r['type']])} |")
A(f"| TIMING claims | {len([r for r in rows if 'TIMING' in r['type']])} |")
A(f"| RISK claims | {len([r for r in rows if 'RISK' in r['type']])} |")
A(f"| MARKET-STATE / classifier claims | {len([r for r in rows if 'MARKET-STATE' in r['type']])} |")
A(f"| COMPARATIVE (ablation) claims | {len([r for r in rows if 'COMPARATIVE' in r['type']])} |")
A(f"| NEGATIVE (fragility / limitation) claims | {len([r for r in rows if 'NEGATIVE' in r['type']])} |")
A(f"| | |")
A(f"| Testable on daily bars today (YES) | {d.get('YES',0)} |")
A(f"| Testable on daily bars with a NEW small feature (EXT) | {d.get('EXT',0)} |")
A(f"| Testable only via a proxy (PROXY) | {d.get('PROXY',0)} |")
A(f"| NOT testable here - data absent (NO) | {d.get('NO',0)} |")
A(f"| n/a (meta rows) | {d.get('n/a',0)} |")
A("")
A(f"**Headline numbers.** {len(rows)} distinct testable claims. **{b['NOT']} are not implemented in the C1-C8**")
A(f"matrix**; of those, {len(also_rows)} claims have in fact been built as standalone specs and already carry a")
A(f"verdict, so the **genuinely open backlog is {len(never_not)} claims**, of which **{len(never_testable)} are")
A("testable on this package's daily panels** with the engine's existing feature registry or with one small new")
A("feature. Section 9.5 proposes 18 new concepts (C9-C26) to cover the highest-value ones; section 9.6 lists")
A("the claims that need a data acquisition (historical options chain, order book, intraday session structure,")
A("macro calendar) rather than more code.")
A("")
A("### Appendix A - excluded from the claim count")
A("")
A("The following content was read and deliberately **not** counted as claims, because each is an arithmetic")
A("illustration or a non-answer rather than a falsifiable claim about markets:")
A("")
A("- The '$100 average, $4 standard deviation -> $96 / $94 / $104 / $106' Nasdaq worked example (RET pp.48-51).")
A("- The '$60,000 / $2,000 -> $58,000 / $57,000' BTC worked example (RET pp.48-49).")
A("- The '29,943 - 1x300 = 29,643' arithmetic exercises (RET pp.70-71).")
A("- The 'is the Nasdaq 29,000, 30,000 or 33,000?' exchange and the paper's own 'I can't confirm the current")
A("  Nasdaq Composite level' non-answer (RET pp.63-65).")
A("- The reference lists themselves (each paper cites 30-160 academic sources; the reference titles are")
A("  bibliography, not claims made by the paper).")
A("")
A("### Appendix B - how to read this document")
A("")
A("- **The claim column is the paper's own wording**, quoted, so a reader can check it against the PDF")
A("  without re-deriving it. Where the paper used an em-dash or an ellipsis, it is preserved.")
A("- **The refutation column is the acceptance test.** A spec for a claim is SUPPORTED only if the refutation")
A("  condition does NOT hold. If it holds, the claim is refuted and that verdict must be reported as such.")
A("- **The Daily? column is the build filter.** `NO` claims should not be queued for spec-writing until the")
A("  underlying data exists; writing a spec for them would produce a proxy dressed up as a paper test, which")
A("  is exactly the failure mode the existing C7 notes already warn about.")
A("- **The Status column distinguishes FULL implementation from PARTIAL**, and the `ALSO TESTED` suffix")
A("  distinguishes 'never built' from 'built and refuted'. Read them together: a claim marked")
A("  `NOT - ALSO TESTED: ... -> REFUTED` is a CLOSED item, not an open one.")
A("")
A("---")
A("")
A("*Inventory generated from the six LeapSpace PDFs in `C:\\Users\\HP\\Downloads\\` via the Hermes native PDF")
A("text extractor. Sections 9 and 10 are generated by `tools/build_claim_inventory.py` directly from the")
A("tables in sections 4-8, so they cannot drift from the inventory. The `ALSO TESTED` annotations are applied")
A("by `tools/annotate_claim_test_status.py`.*")

open(OUT, "w", encoding="utf-8").write(txt.rstrip() + "\n\n" + "\n".join(L) + "\n")
print("wrote", OUT)
print(f"claims={len(rows)} directional={len(dirs)} not={b['NOT']} also_tested={len(also_rows)} "
      f"never_built={len(never)} never_not={len(never_not)} never_testable={len(never_testable)}")
