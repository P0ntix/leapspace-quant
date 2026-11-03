"""
Meme-coin screening — the paper's five-layer edge framework.

Source: "Meme coin trading strategies" (LeapSpace). The paper's five layers:

  1. Narrative Heat       — accelerating attention / narrative prevalence
  2. Structural Safety    — concentration, one-sided liquidity, fake distribution
  3. Exit Quality         — depth, slippage, order-flow persistence
  4. Survival Probability — prioritise tokens likely to survive the launchpad funnel
  5. Manipulation Check   — wallet clusters, circular flows, self-trading

VERIFIED LIVE DATA SOURCES (no API key required):
  jupiter.lite-api.jup.ag/tokens/v2/search   -> holderCount, mint/freeze authority,
                                                 organicScore, audit.topHoldersPercentage,
                                                 devBalancePercentage, liquidity, tags, createdAt
  api.rugcheck.xyz/v1/tokens/<mint>/report   -> topHolders[] with pct + insider flag,
                                                 totalHolders, totalMarketLiquidity, risks,
                                                 score, creator, creatorBalance, markets[]
  api.dexscreener.com                        -> pair price, volume, liquidity, txns,
                                                 pairCreatedAt, DEX id, socials/websites

WHAT IS NOT AVAILABLE and therefore NOT COMPUTED:
  * Social attention / narrative heat has no free, reliable API. Layer 1 is
    therefore scored on PROXY inputs only (volume acceleration, holder growth
    proxy, social-link presence, token age), and every such proxy is labelled
    as a proxy in the output. It is NOT presented as measured attention.
  * The paper itself says the short-horizon predictive thresholds are not
    quantified in the literature. Every threshold used here is an ANALYST
    CHOICE and is listed in the returned `thresholds` block.
  * The paper's own limitation: creator share / top-10 concentration / first-hour
    imbalance predicting 1-day-to-2-week returns is an OPEN EMPIRICAL QUESTION.
    This screener is a FILTER, not a validated return predictor.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .http import http_json
from .market import fetch_dex_pairs, normalise_dex_pair
from .provenance import Provenance, SourceUnavailable

JUPITER_TOKEN = "https://lite-api.jup.ag/tokens/v2/search?query={mint}"
RUGCHECK_REPORT = "https://api.rugcheck.xyz/v1/tokens/{mint}/report"

# Analyst-chosen thresholds. The paper does not quantify them.
THRESHOLDS = {
    "min_liquidity_usd": 25_000.0,
    "min_volume_24h_usd": 50_000.0,
    "max_top_holder_pct": 15.0,
    "max_top10_holder_pct": 40.0,
    "max_dev_balance_pct": 5.0,
    "max_age_days": 365,
    "min_age_hours": 1.0,
    "min_buy_sell_ratio": 1.15,
    "max_rugcheck_score": 40,
    "min_holders": 50,
    # --- launchpad funnel / migration (Layer 4) ---
    "min_major_dexes": 1,
    "max_launchpad_pool_age_days": 90,
    # --- one-sided liquidity and LP control (Layer 2) ---
    "min_stable_liquidity_share": 0.15,
    "min_lp_providers": 3,
    "max_graph_insiders": 50,
    # --- price impact (Layer 3) ---
    "max_price_impact_bps_1k": 500.0,
    "price_impact_notional_usd": 1000.0,
}

# DEXes the paper treats as "major" venues - a token present on one of
# these has MIGRATED past the launchpad funnel (paper: "fewer than 2% of
# these tokens reached major DEXs", citing Mancino 2025).
MAJOR_DEXES = {"raydium", "raydium-clmm", "orca", "meteora", "meteoraDlmm",
               "meteora_damm", "meteora_damm_v2", "uniswap", "uniswap-v2",
               "uniswap-v3", "aerodrome", "pancakeswap", "pumpswap",
               "raydiumlaunchlab", "heaven", "sugar"}
# pump.fun's own DEX. Its presence means the token started on the
# launchpad - the funnel the paper is about.
LAUNCHPAD_DEXES = {"pumpswap", "raydiumlaunchlab", "raydium-launchlab",
                   "launchlab", "believe"}


def _pct(x: Any) -> Optional[float]:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def fetch_token_profile(mint: str) -> Tuple[Dict[str, Any], Provenance]:
    """Jupiter token profile: holder count, authorities, organic score, audit."""
    url = JUPITER_TOKEN.format(mint=mint)
    payload, status = http_json(url, timeout=30)
    if not isinstance(payload, list) or not payload:
        raise SourceUnavailable(f"jupiter returned no profile for mint {mint}")
    t = payload[0]
    audit = t.get("audit") or {}
    prov = Provenance(source="jupiter.tokens.v2", url=url,
                      note=f"HTTP {status}; symbol={t.get('symbol')}")
    return {
        "mint": t.get("id") or mint,
        "name": t.get("name"),
        "symbol": t.get("symbol"),
        "decimals": t.get("decimals"),
        "holder_count": t.get("holderCount"),
        "total_supply": t.get("totalSupply"),
        "circ_supply": t.get("circSupply"),
        "mint_authority": t.get("mintAuthority"),
        "freeze_authority": t.get("freezeAuthority"),
        "mint_authority_disabled": audit.get("mintAuthorityDisabled"),
        "freeze_authority_disabled": audit.get("freezeAuthorityDisabled"),
        "top_holders_pct": _pct(audit.get("topHoldersPercentage")),
        "dev_balance_pct": _pct(audit.get("devBalancePercentage")),
        "dev_mints": audit.get("devMints"),
        "organic_score": t.get("organicScore"),
        "organic_score_label": t.get("organicScoreLabel"),
        "is_verified": t.get("isVerified"),
        "tags": t.get("tags") or [],
        "liquidity_usd": t.get("liquidity"),
        "usd_price": t.get("usdPrice"),
        "fdv": t.get("fdv"),
        "mcap": t.get("mcap"),
        "created_at": t.get("createdAt"),
        "first_pool": t.get("firstPool"),
        "first_pool_created": ((t.get("firstPool") or {}) or {}).get("createdAt"),
        "first_pool_id": ((t.get("firstPool") or {}) or {}).get("id"),
        "birdeye_trending": "birdeye-trending" in (t.get("tags") or []),
        "tags_community": "community" in (t.get("tags") or []),
        "stats_5m": t.get("stats5m"),
        "stats_1h": t.get("stats1h"),
        "stats_24h": t.get("stats24h"),
    }, prov


def fetch_rugcheck(mint: str) -> Tuple[Dict[str, Any], Provenance]:
    """RugCheck full report: top holders with insider flags, risks, liquidity."""
    url = RUGCHECK_REPORT.format(mint=mint)
    payload, status = http_json(url, timeout=45)
    if not isinstance(payload, dict) or not payload:
        raise SourceUnavailable(f"rugcheck returned no report for mint {mint}")
    holders = []
    for h in (payload.get("topHolders") or [])[:20]:
        holders.append({
            "address": h.get("address"),
            "owner": h.get("owner"),
            "pct": _pct(h.get("pct")),
            "insider": h.get("insider"),
            "ui_amount": h.get("uiAmount"),
        })
    prov = Provenance(source="rugcheck.report", url=url,
                      note=f"HTTP {status}; totalHolders={payload.get('totalHolders')}")
    return {
        "mint": payload.get("mint") or mint,
        "token_meta": payload.get("tokenMeta"),
        "total_holders": payload.get("totalHolders"),
        "total_market_liquidity": payload.get("totalMarketLiquidity"),
        "total_stable_liquidity": payload.get("totalStableLiquidity"),
        "graph_insiders_detected": payload.get("graphInsidersDetected"),
        "market_types": sorted({m.get("marketType") for m
                                 in (payload.get("markets") or [])
                                 if m.get("marketType")}),
        "total_lp_providers": payload.get("totalLPProviders"),
        "score": payload.get("score"),
        "score_normalised": payload.get("score_normalised"),
        "rugged": payload.get("rugged"),
        "creator": payload.get("creator"),
        "creator_balance": payload.get("creatorBalance"),
        "risks": payload.get("risks") or [],
        "top_holders": holders,
        "top_holders_pct_sum": sum(h["pct"] for h in holders if h["pct"] is not None),
        "insider_holder_count": sum(1 for h in holders if h.get("insider")),
        "locker_owners": payload.get("lockerOwners") or {},
        "verification": payload.get("verification") or {},
        "markets": (payload.get("markets") or [])[:5],
        "transfer_fee": payload.get("transferFee"),
    }, prov


def fetch_migration_evidence(mint: str) -> Tuple[Dict[str, Any], Provenance]:
    """Launchpad-origin and migration evidence from the token's DEX pairs.

    The paper's central claim is about the LAUNCHPAD FUNNEL: fewer than
    2% of launchpad tokens reach major DEXs, so the edge is in predicting
    migration/survival rather than scanning every launch. That evidence
    is only visible across a token's SET OF PAIRS, which is what this
    fetches.

    Returns the distinct DEX list, whether a major DEX is present
    (migrated), whether a launchpad DEX is present (origin), and the age
    of the earliest pair.
    """
    from .http import http_json
    url = f"https://api.dexscreener.com/token-pairs/v1/solana/{mint}"
    payload, status = http_json(url, timeout=30)
    pairs = [p for p in (payload or []) if isinstance(p, dict)]
    dexes = sorted({p.get("dexId") for p in pairs if p.get("dexId")})
    created = [p.get("pairCreatedAt") for p in pairs if p.get("pairCreatedAt")]
    earliest = min(created) if created else None
    age_days = None
    if earliest:
        try:
            age_days = (_dt.datetime.now(_dt.timezone.utc).timestamp()
                        - earliest / 1000.0) / 86400.0
        except (TypeError, ValueError):
            age_days = None
    major = [d for d in dexes if d in MAJOR_DEXES]
    launchpad = [d for d in dexes if d in LAUNCHPAD_DEXES]
    prov = Provenance(source="dexscreener.token-pairs.v1", url=url,
                      note=f"HTTP {status}; {len(pairs)} pairs, "
                           f"{len(dexes)} DEXes")
    return {
        "n_pairs": len(pairs),
        "n_dexes": len(dexes),
        "dexes": dexes,
        "major_dexes": major,
        "has_major_dex": bool(major),
        "launchpad_dexes": launchpad,
        "launchpad_origin": bool(launchpad),
        "earliest_pair_created_ms": earliest,
        "earliest_pair_age_days": age_days,
        "migrated": bool(major) and len(major) >= 1,
    }, prov


@dataclass
class ScreenResult:
    mint: str
    symbol: Optional[str]
    passed: bool
    score: float
    layers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    disqualifiers: List[str] = field(default_factory=list)
    provenance: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mint": self.mint,
            "symbol": self.symbol,
            "passed": self.passed,
            "score": self.score,
            "layers": self.layers,
            "reasons": self.reasons,
            "disqualifiers": self.disqualifiers,
            "provenance": self.provenance,
            "warnings": self.warnings,
            "thresholds": THRESHOLDS,
            "thresholds_note": ("Every threshold above is an ANALYST CHOICE. "
                                "The source paper explicitly states the "
                                "short-horizon predictive thresholds are not "
                                "quantified in the retrieved literature."),
        }


def screen_meme_coin(mint: str, pair: Optional[Dict[str, Any]] = None,
                     thresholds: Optional[Dict[str, float]] = None
                     ) -> ScreenResult:
    """Apply the paper's five layers to one token.

    `pair` is a normalised DexScreener pair (see market.normalise_dex_pair).
    If omitted, the deepest-liquidity pair for the mint is fetched.
    """
    th = dict(THRESHOLDS)
    th.update(thresholds or {})
    provs: List[str] = []
    warnings: List[str] = []

    try:
        prof, p1 = fetch_token_profile(mint)
    except SourceUnavailable as exc:
        raise SourceUnavailable(f"token profile unavailable for {mint}: {exc}")
    provs.append(p1.disclosure())
    try:
        rug, p2 = fetch_rugcheck(mint)
    except SourceUnavailable as exc:
        rug = {}
        warnings.append(f"rugcheck unavailable: {exc}")
    else:
        provs.append(p2.disclosure())

    # Launchpad / migration evidence (the paper's central claim).
    try:
        migration, pm = fetch_migration_evidence(mint)
    except Exception as exc:  # noqa: BLE001
        migration = {}
        warnings.append(f"migration evidence unavailable: {exc}")
    else:
        provs.append(pm.disclosure())

    if pair is None:
        pairs, p3 = fetch_dex_pairs(mint, limit=30)
        provs.append(p3.disclosure())
        norm = [normalise_dex_pair(p) for p in pairs]
        norm = [n for n in norm if n.get("base_address") == mint
                or n.get("pair", "").startswith(mint[:6])]
        if not norm:
            norm = [normalise_dex_pair(p) for p in pairs]
        pair = max(norm, key=lambda n: (n.get("liquidity_usd") or 0.0)) if norm else {}
    else:
        pair = normalise_dex_pair(pair) if "liquidity_usd" not in pair else pair

    layers: Dict[str, Dict[str, Any]] = {}
    reasons: List[str] = []
    disq: List[str] = []

    # --- Layer 2: Structural Safety -------------------------------------
    top_pct = rug.get("top_holders_pct_sum") or prof.get("top_holders_pct")
    top1 = None
    if rug.get("top_holders"):
        top1 = rug["top_holders"][0].get("pct")
    dev_pct = prof.get("dev_balance_pct")
    insiders = rug.get("insider_holder_count", 0)
    mint_auth = prof.get("mint_authority_disabled")
    freeze_auth = prof.get("freeze_authority_disabled")
    struct_ok = True
    if top_pct is not None and top_pct > th["max_top10_holder_pct"]:
        struct_ok = False
        disq.append(f"Top-holder concentration {top_pct:.1f}% exceeds the "
                    f"{th['max_top10_holder_pct']:.0f}% threshold.")
    if top1 is not None and top1 > th["max_top_holder_pct"]:
        struct_ok = False
        disq.append(f"Single largest holder {top1:.1f}% exceeds the "
                    f"{th['max_top_holder_pct']:.0f}% threshold "
                    f"(paper's Libra case: 92.8% creator control).")
    if dev_pct is not None and dev_pct > th["max_dev_balance_pct"]:
        struct_ok = False
        disq.append(f"Developer balance {dev_pct:.2f}% exceeds the "
                    f"{th['max_dev_balance_pct']:.0f}% threshold.")
    if mint_auth is False:
        struct_ok = False
        disq.append("Mint authority is still active — supply can be inflated.")
    if freeze_auth is False:
        struct_ok = False
        disq.append("Freeze authority is still active — transfers can be frozen.")
    if insiders:
        struct_ok = False
        disq.append(f"{insiders} of the top-20 holders are flagged as insiders.")

    # ONE-SIDED LIQUIDITY. The paper's Layer 2 names "one-sided liquidity"
    # as a fragility marker, and the Exit filter compares "apparent pool
    # liquidity with likely sell-side execution conditions". RugCheck's
    # stable-liquidity share measures exactly that: if almost none of the
    # pool is quote-side, the book is one-sided and a sell cannot be
    # absorbed.
    total_liq = rug.get("total_market_liquidity")
    stable_liq = rug.get("total_stable_liquidity")
    stable_share = None
    if total_liq and stable_liq is not None and total_liq > 0:
        stable_share = float(stable_liq) / float(total_liq)
        if stable_share < th["min_stable_liquidity_share"]:
            struct_ok = False
            disq.append(
                f"ONE-SIDED LIQUIDITY: only {stable_share:.1%} of pool "
                f"liquidity is quote-side (below the "
                f"{th['min_stable_liquidity_share']:.0%} threshold) - a sell "
                f"cannot be absorbed by the book.")

    # LP CONTROL. Few LP providers means one or a few providers can pull
    # the pool, which is the "liquidity control by a small set of wallets"
    # fragility the paper flags.
    lp_providers = rug.get("total_lp_providers")
    if lp_providers is not None and lp_providers < th["min_lp_providers"]:
        struct_ok = False
        disq.append(f"Only {lp_providers} LP provider(s) - liquidity control "
                    f"is concentrated (below {th['min_lp_providers']}).")

    # WALLET CLUSTERING. RugCheck's graph analysis counts wallets it
    # links as insiders. This is the paper's "suspicious wallet clustering"
    # measured by a third party, not inferred.
    graph_insiders = rug.get("graph_insiders_detected")
    if (isinstance(graph_insiders, int)
            and graph_insiders > th["max_graph_insiders"]):
        struct_ok = False
        disq.append(f"RugCheck's graph links {graph_insiders} wallets to "
                    f"insider clusters (above {th['max_graph_insiders']}) - "
                    f"the paper's 'linked wallets control float' pattern.")

    layers["structural_safety"] = {
        "passed": struct_ok,
        "top_holders_pct": top_pct,
        "top1_holder_pct": top1,
        "dev_balance_pct": dev_pct,
        "mint_authority_disabled": mint_auth,
        "freeze_authority_disabled": freeze_auth,
        "insider_flagged_top20": insiders,
        "total_holders": rug.get("total_holders") or prof.get("holder_count"),
        "one_sided_liquidity": {
            "total_market_liquidity": total_liq,
            "stable_liquidity": stable_liq,
            "stable_liquidity_share": stable_share,
            "threshold": th["min_stable_liquidity_share"],
        },
        "lp_providers": lp_providers,
        "lp_providers_threshold": th["min_lp_providers"],
        "graph_insiders_detected": graph_insiders,
        "graph_insiders_threshold": th["max_graph_insiders"],
        "market_types": rug.get("market_types"),
        "locker_owners": rug.get("locker_owners"),
    }

    # --- Layer 3: Exit Quality ------------------------------------------
    liq = pair.get("liquidity_usd")
    vol24 = pair.get("volume_24h")
    buys = pair.get("buys_24h") or 0
    sells = pair.get("sells_24h") or 0
    buys1 = pair.get("buys_1h") or 0
    sells1 = pair.get("sells_1h") or 0
    exit_ok = True
    if liq is None:
        exit_ok = False
        disq.append("Liquidity unavailable — exit quality cannot be assessed.")
    elif liq < th["min_liquidity_usd"]:
        exit_ok = False
        disq.append(f"Liquidity ${liq:,.0f} below the ${th['min_liquidity_usd']:,.0f} "
                    f"threshold — a small notional would move price materially.")
    if vol24 is not None and vol24 < th["min_volume_24h_usd"]:
        exit_ok = False
        disq.append(f"24h volume ${vol24:,.0f} below the "
                    f"${th['min_volume_24h_usd']:,.0f} threshold.")
    ratio_24 = (buys / sells) if sells else None
    ratio_1 = (buys1 / sells1) if sells1 else None
    if ratio_24 is not None and sells > 0 and buys > 0 and ratio_24 < 0.85:
        exit_ok = False
        disq.append(f"24h buy/sell ratio {ratio_24:.2f} shows persistent sell "
                    f"pressure — the paper warns against chasing fades.")
    # PRICE IMPACT / SLIPPAGE. The paper's Exit Quality layer names
    # slippage and executable depth explicitly. There is no free endpoint
    # that quotes a token's slippage curve, so it is ESTIMATED from pool
    # liquidity and the method is stated. The constant is the standard
    # constant-product impact coefficient; the estimate ignores the
    # sell-side asymmetry, so it is a lower bound on realised cost.
    impact_bps = None
    if liq and liq > 0:
        notional = th["price_impact_notional_usd"]
        frac = notional / (2.0 * liq)
        impact_bps = frac * 10_000.0
        if impact_bps > th["max_price_impact_bps_1k"]:
            exit_ok = False
            disq.append(
                f"Estimated price impact {impact_bps:.0f}bps for a "
                f"${notional:,.0f} trade on ${liq:,.0f} liquidity (above "
                f"{th['max_price_impact_bps_1k']:.0f}bps) - the paper's "
                f"depth filter.")
    layers["exit_quality"] = {
        "passed": exit_ok,
        "estimated_price_impact_bps": impact_bps,
        "price_impact_notional_usd": th["price_impact_notional_usd"],
        "price_impact_method": (
            "constant-product estimate: notional / (2 * liquidity), in bps. "
            "It ignores sell-side asymmetry, so it is a LOWER bound on "
            "realised slippage. It is an ESTIMATE, not a quoted slippage "
            "curve."),
        "liquidity_usd": liq,
        # The PAIR ADDRESS matters: a forward test must compare the same
        # pool at both ends, not "whatever pair has the most liquidity
        # now", or two different pools get compared as one token.
        "pair_address": pair.get("pair"),
        "dex": pair.get("dex"),
        "price_usd": pair.get("price_usd"),
        "price_change_24h": pair.get("price_change_24h"),
        "price_change_1h": pair.get("price_change_1h"),
        "price_change_5m": pair.get("price_change_5m"),
        "volume_24h": vol24,
        "buys_24h": buys,
        "sells_24h": sells,
        "buy_sell_ratio_24h": ratio_24,
        "buy_sell_ratio_1h": ratio_1,
        "flow_persistence": ("improving" if (ratio_1 and ratio_24 and ratio_1 >= ratio_24)
                             else ("fading" if (ratio_1 and ratio_24 and ratio_1 < ratio_24)
                                   else "insufficient")),
    }

    # --- Layer 4: Survival Probability ----------------------------------
    created = prof.get("created_at") or pair.get("created_at_ms")
    age_days = None
    if pair.get("created_at_ms"):
        age_days = (_dt.datetime.now(_dt.timezone.utc).timestamp()
                    - pair["created_at_ms"] / 1000.0) / 86400.0
    elif created:
        try:
            c = _dt.datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            age_days = (_dt.datetime.now(_dt.timezone.utc) - c).total_seconds() / 86400.0
        except ValueError:
            age_days = None
    holders = rug.get("total_holders") or prof.get("holder_count")
    survival_ok = True
    if age_days is not None and age_days > th["max_age_days"]:
        survival_ok = False
        disq.append(f"Token age {age_days:.0f}d exceeds {th['max_age_days']}d — "
                    f"the paper's edge is in early attention formation, not "
                    f"an already-matured asset.")
    if holders is not None and holders < th["min_holders"]:
        survival_ok = False
        disq.append(f"Only {holders} holders — below the {th['min_holders']} "
                    f"threshold for a plausibly distributed token.")
    if prof.get("organic_score_label") in ("high", "medium"):
        reasons.append(f"Jupiter organic score: {prof.get('organic_score_label')} "
                       f"({prof.get('organic_score'):.1f}) — automated-trading "
                       f"activity indicator.")

    # THE LAUNCHPAD FUNNEL. The paper's central claim: "fewer than 2% of
    # launchpad tokens reach major DEXs... edge likely comes from
    # identifying migration survivors, not chasing the full funnel". A
    # token that is ALREADY on a major DEX has survived that filter; one
    # that only sits on a launchpad DEX has not.
    n_dexes = migration.get("n_dexes") or 0
    has_major = bool(migration.get("has_major_dex"))
    launchpad_origin = bool(migration.get("launchpad_origin"))
    # RugCheck's market types see launchpad venues the DexScreener DEX
    # list can miss - BONK's pools include `pump_fun_amm` even though its
    # DexScreener DEX list has no pumpswap entry, because the launchpad
    # pool was migrated. Both sources are consulted.
    rug_launchpad_markets = sorted(
        m for m in (rug.get("market_types") or [])
        if "pump" in str(m).lower() or "launchlab" in str(m).lower())
    if rug_launchpad_markets:
        launchpad_origin = True
    lp_age = prof.get("first_pool_created")
    lp_age_days = None
    if lp_age:
        try:
            c = _dt.datetime.fromisoformat(str(lp_age).replace("Z", "+00:00"))
            lp_age_days = (_dt.datetime.now(_dt.timezone.utc) - c).total_seconds() / 86400.0
        except ValueError:
            lp_age_days = None
    if has_major and n_dexes < th["min_major_dexes"]:
        survival_ok = False
        disq.append(f"Present on {n_dexes} DEX(es) — too thin for the "
                    f"survival the paper's funnel filter expects.")
    if lp_age_days is not None and lp_age_days > th["max_launchpad_pool_age_days"]:
        survival_ok = False
        disq.append(f"Launchpad pool is {lp_age_days:.0f}d old (above "
                    f"{th['max_launchpad_pool_age_days']}d) — the edge is in "
                    f"early attention formation.")

    layers["survival"] = {
        "passed": survival_ok,
        "age_days": age_days,
        "holders": holders,
        "organic_score": prof.get("organic_score"),
        "organic_score_label": prof.get("organic_score_label"),
        "tags": prof.get("tags"),
        "verified": prof.get("is_verified"),
        "launchpad_funnel": {
            "n_pairs": migration.get("n_pairs"),
            "n_dexes": n_dexes,
            "dexes": migration.get("dexes"),
            "major_dexes": migration.get("major_dexes"),
            "has_major_dex": has_major,
            "migrated": bool(has_major),
            "launchpad_dexes": migration.get("launchpad_dexes"),
            "launchpad_origin": launchpad_origin,
            "launchpad_market_types": rug_launchpad_markets,
            "first_pool_created": prof.get("first_pool_created"),
            "first_pool_age_days": lp_age_days,
            "note": ("A token on a MAJOR DEX has survived the launchpad "
                     "funnel the paper says fewer than 2% of launches pass. "
                     "A launchpad DEX (pumpswap/raydium-launchlab) in the "
                     "list means the token STARTED on a launchpad."),
        },
    }

    # --- Layer 5: Manipulation Check ------------------------------------
    manip_ok = True
    risks = rug.get("risks") or []
    # RugCheck risk levels observed live: "danger", "warn", "info".
    # Only a "danger" level is treated as a hard disqualifier; a "warn" is
    # surfaced as a caution. The paper's concern is with PREDATORY structure
    # (concentration, one-sided liquidity, fake distribution), which maps to
    # "danger"-level findings.
    high_risks = [r for r in risks
                  if str(r.get("level", "")).strip().lower() == "danger"]
    warn_risks = [r for r in risks
                  if str(r.get("level", "")).strip().lower() == "warn"]
    if rug.get("rugged"):
        manip_ok = False
        disq.append("RugCheck reports this token as rugged.")
    for r in high_risks:
        manip_ok = False
        disq.append(f"RugCheck DANGER risk '{r.get('name')}' — {r.get('description', '')}")
    score = rug.get("score")
    if isinstance(score, (int, float)) and score > th["max_rugcheck_score"]:
        manip_ok = False
        disq.append(f"RugCheck risk score {score} exceeds the "
                    f"{th['max_rugcheck_score']} threshold "
                    f"(higher RugCheck score = higher detected risk).")
    for r in warn_risks:
        warnings.append(f"RugCheck caution (not disqualifying): '{r.get('name')}' — "
                        f"{r.get('description', '')}")
    layers["manipulation_check"] = {
        "passed": manip_ok,
        "rugcheck_score": score,
        "rugcheck_score_note": ("RugCheck's score is a RISK score: higher "
                                "means more detected risk. Observed live: "
                                "USDC=1, BONK=101."),
        "danger_risks": high_risks,
        "warn_risks": warn_risks,
        "risks": risks,
        "rugged": rug.get("rugged"),
        "locker_owners": rug.get("locker_owners"),
        "note": ("Wallet-clustering and circular-flow detection for a token's "
                 "holders requires per-wallet transaction history; run "
                 "leapspace.onchain.analyse_wallet on the flagged holders. "
                 "That work is not performed here automatically."),
    }

    # --- Layer 1: Narrative Heat (PROXY ONLY) ----------------------------
    # There is no free reliable attention API. These are PROXIES and are
    # labelled as such.
    socials = pair.get("socials") or []
    websites = pair.get("websites") or []
    vol_accel = None
    v6 = pair.get("volume_6h") or 0.0
    v24 = pair.get("volume_24h") or 0.0
    if v24 > 0:
        vol_accel = (v6 * 4.0) / v24 if v6 else None
    # REAL attention/flow signals, where a real source provides them.
    st24 = prof.get("stats_24h") or {}
    buy_vol = st24.get("buyVolume")
    sell_vol = st24.get("sellVolume")
    flow_ratio = None
    if buy_vol is not None and sell_vol not in (None, 0):
        try:
            flow_ratio = float(buy_vol) / float(sell_vol)
        except (TypeError, ValueError, ZeroDivisionError):
            flow_ratio = None
    holder_change = st24.get("holderChange")
    volume_change = st24.get("volumeChange")
    trending = bool(prof.get("birdeye_trending"))
    # NARRATIVE SPECIFICITY. The paper's clause: "tokens tied to niche
    # communities and viral cultural expressions outperformed broader-trend
    # tokens... launch selection should include cultural specificity as a
    # filtering feature, not just momentum". This classifies the token's
    # community footprint from free sources; the cohort-relative baseline
    # is added by screen_search, which sees all the tokens at once.
    from .narrative import classify_specificity
    specificity = classify_specificity(prof, pair)

    layers["narrative_heat"] = {
        "passed": None,
        "PROXY": True,
        "SPECIFICITY": specificity,
        "REAL_SIGNALS": {
            "birdeye_trending_tag": trending,
            "birdeye_trending_note": (
                "Jupiter's 'birdeye-trending' tag is a THIRD-PARTY trending "
                "signal - the closest available proxy for 'accelerating "
                "attention' that the paper's Layer 1 asks for."),
            "buy_volume_24h_usd": buy_vol,
            "sell_volume_24h_usd": sell_vol,
            "buy_sell_volume_ratio_24h": flow_ratio,
            "holder_change_24h": holder_change,
            "volume_change_24h": volume_change,
            "community_tag": bool(prof.get("tags_community")),
            "note": ("Narrative SPECIFICITY (a niche community rather than "
                     "a generic trend clone) is not measurable from these "
                     "sources and is still a proxy."),
        },
        "disclosure": ("No free, reliable social-attention API is available. "
                       "Attention is NOT measured here. The fields below are "
                       "proxies for attention formation and must not be read "
                       "as measured narrative heat."),
        "social_links": len(socials),
        "website_links": len(websites),
        "volume_acceleration_6h_vs_24h": vol_accel,
        "volume_5m": pair.get("volume_5m"),
        "tags_include_meme": "meme" in (prof.get("tags") or []),
        "pair_created_at_ms": pair.get("created_at_ms"),
    }

    # --- Score -----------------------------------------------------------
    # A simple, disclosed composite. NOT a validated return predictor.
    score_parts = []
    if layers["structural_safety"]["passed"]:
        score_parts.append(1.0)
    if layers["exit_quality"]["passed"]:
        score_parts.append(1.0)
    if layers["survival"]["passed"]:
        score_parts.append(1.0)
    if layers["manipulation_check"]["passed"]:
        score_parts.append(1.0)
    score = sum(score_parts) / 4.0

    passed = (struct_ok and exit_ok and survival_ok and manip_ok)
    if passed:
        reasons.append("Passes all four hard layers (structural safety, exit "
                       "quality, survival, manipulation check).")
    return ScreenResult(
        mint=mint, symbol=prof.get("symbol"),
        passed=passed, score=score, layers=layers, reasons=reasons,
        disqualifiers=disq, provenance=provs, warnings=warnings,
    )


def screen_search(query: str, limit: int = 15,
                  thresholds: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Search a meme-coin narrative and screen each result."""
    pairs, prov = fetch_dex_pairs(query, limit=limit * 3)
    norm = [normalise_dex_pair(p) for p in pairs]
    norm = [n for n in norm if n.get("chain") == "solana"]
    seen = set()
    results: List[ScreenResult] = []
    errors: List[Dict[str, Any]] = []
    for n in norm:
        mint = n.get("base_address")
        if not mint or mint in seen:
            continue
        seen.add(mint)
        if len(results) >= limit:
            break
        try:
            r = screen_meme_coin(mint, pair=n, thresholds=thresholds)
            results.append(r)
        except SourceUnavailable as exc:
            errors.append({"mint": mint, "error": str(exc)})
    passed = [r for r in results if r.passed]

    # COHORT ANALYSIS. The paper's specificity clause needs a baseline to
    # compare against, and no free source assigns a "generic" label. The
    # cohort's OWN distribution provides one: a token carrying fewer
    # community-footprint signals than a quarter of its peers is generic
    # RELATIVE TO THIS COHORT.
    from .narrative import (backward_association, cohort_baseline,
                            relative_to_cohort, save_cohort)
    cohort_rows = []
    for r in results:
        spec = (r.layers.get("narrative_heat") or {}).get("SPECIFICITY") or {}
        cohort_rows.append({
            "mint": r.mint, "symbol": r.symbol,
            "specificity_score": spec.get("specificity_score"),
            "is_niche": spec.get("is_niche"),
            "price_usd": r.layers.get("exit_quality", {}).get("price_usd"),
            "pair_address": r.layers.get("exit_quality", {}).get("pair_address"),
            "dex": r.layers.get("exit_quality", {}).get("dex"),
            "price_change_24h": r.layers.get("exit_quality", {}).get(
                "price_change_24h"),
            "liquidity_usd": r.layers.get("exit_quality", {}).get(
                "liquidity_usd"),
        })
    baseline = cohort_baseline(cohort_rows)
    for r, row in zip(results, cohort_rows):
        rel = relative_to_cohort(row, baseline)
        (r.layers.get("narrative_heat") or {})["COHORT_RELATIVE"] = rel
    assoc = backward_association(cohort_rows)
    try:
        snap = save_cohort(cohort_rows)
    except Exception as exc:  # noqa: BLE001
        snap = {"error": str(exc)}

    return {
        "query": query,
        "screened": len(results),
        "passed": len(passed),
        "results": [r.to_dict() for r in sorted(results, key=lambda x: -x.score)],
        "errors": errors,
        "provenance": [prov.disclosure()],
        "narrative_cohort": {
            "baseline": baseline,
            "backward_association": assoc,
            "forward_test": ("run `leapspace.cli narrative --verify` later "
                             "with a saved cohort to measure FORWARD returns"),
            "snapshot": snap,
            "note": ("Specificity measures the PRESENCE of a community "
                     "footprint, not attention or community size. The "
                     "paper's [15] claim is a PERFORMANCE claim; the "
                     "association above is BACKWARD and on a small free "
                     "sample."),
        },
        "disclosure": ("This is a FILTER, not a validated return predictor. The "
                       "source paper states the predictive thresholds for "
                       "creator share, top-10 concentration and first-hour "
                       "imbalance are an open empirical question."),
    }
