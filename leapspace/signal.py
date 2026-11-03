"""leapspace.signal - the trade-decision engine.

WHAT THIS IS
------------
Every other module in this package produces an ANALYSIS. This one
produces a DECISION: for a given token on a given chain it gathers
the evidence, grades the quality of that evidence, and emits a verdict
with an entry reference, an exit reference, an invalidation list and a
position size - plus, critically, the list of things it COULD NOT
measure.

THE TWO LEGS OF EVIDENCE
------------------------
Leg 1 - RESEARCH EDGE
    The thirteen backtest specifications derived from the source
    papers, run live by `leapspace.backtest`. A specification that
    survives the FULL validation gauntlet is evidence that the RULE has
    a non-random prior. The package's own verdict semantics say a
    SUPPORTED specification warrants PAPER trading and never live
    trading, so this leg can only raise or lower conviction - it can
    never by itself authorise a position.

Leg 2 - QUALIFIED WALLET BEHAVIOUR
    Wallets that have been screened against the consistency gate
    (edge.evaluate_edge) and PASSED. For a token held by such wallets,
    their realised ENTRY levels, HOLD durations and EXIT behaviour are
    the empirical basis for the entry and exit references. This is the
    only leg that can set a price level, because it is the only leg
    derived from accounts that actually made money.

THE HONEST DEFAULT
------------------
Right now NO wallet in the package has passed the consistency gate.
Every one of the fifteen PEPE top-holder wallets screened scored
FLUKE. So for most tokens this module returns AVOID or WATCH with the
reason "no qualified wallet holds this token", and the entry and exit
references are explicitly marked NOT EVIDENCE-BASED.

That is the correct output, not a failure of the module. A system that
manufactures an entry level when no profitable account exists is a
system that will lose money with great confidence.

NO ORDER PLACEMENT
------------------
This module never places an order and never talks to an exchange. It
produces a brief for a human to act on. Order placement is a separate,
deliberately gated step - see LIVE_CAPITAL_READINESS.md.
"""
from __future__ import annotations

import json
import os
import statistics
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from . import provenance as PROV

#: Provenance marker for "this could not be measured". Not a data kind
#: that was fetched - the absence of one.
UNAVAILABLE = "UNAVAILABLE"

ENTER = "ENTER"
WATCH = "WATCH"
AVOID = "AVOID"
NO_DATA = "NO_TRADE_DATA"

SUPPORTS = "SUPPORTS"
CONFLICTS = "CONFLICTS"
NEUTRAL = "NEUTRAL"


@dataclass
class Leg:
    """One independent strand of evidence.

    FIELD ORDER MATTERS: `metrics` comes BEFORE `provenance` because
    the call sites read `Leg(name, verdict, detail, metrics,
    provenance, blocking)` - the natural order for a reader. An earlier
    version had `provenance` in the 4th slot, which silently put the
    metrics dict into the provenance field and broke the provenance
    tally downstream. Keeping metrics in the natural position and
    passing provenance by keyword is what prevents that class of bug.
    """
    name: str
    verdict: str                    # SUPPORTS / CONFLICTS / NEUTRAL / UNAVAILABLE
    detail: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    provenance: str = PROV.LIVE
    #: A blocking CONFLICT vetoes the trade regardless of other legs.
    blocking: bool = False


@dataclass
class TradeSignal:
    token: Dict[str, Any]
    verdict: str
    confidence: str
    legs: List[Leg] = field(default_factory=list)
    entry: Dict[str, Any] = field(default_factory=dict)
    exit: Dict[str, Any] = field(default_factory=dict)
    sizing: Dict[str, Any] = field(default_factory=dict)
    invalidation: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    provenance_summary: Dict[str, int] = field(default_factory=dict)
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "generated_at": self.generated_at or PROV.utcnow_iso(),
            "legs": [
                {"name": l.name, "verdict": l.verdict, "detail": l.detail,
                 "provenance": l.provenance, "blocking": l.blocking,
                 "metrics": l.metrics}
                for l in self.legs
            ],
            "entry": self.entry,
            "exit": self.exit,
            "sizing": self.sizing,
            "invalidation": self.invalidation,
            "gaps": self.gaps,
            "provenance_summary": self.provenance_summary,
        }


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _read_json(path: str) -> Optional[Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _root(project_root: Optional[str] = None) -> str:
    if project_root:
        return project_root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _leg_safe(name: str, fn: Callable[..., Leg], *args, **kwargs) -> Leg:
    """Run an evidence leg. Any failure becomes an UNAVAILABLE leg with
    the reason - never a silent omission. A leg that could not be
    measured is a GAP, and gaps are reported in the brief."""
    try:
        leg = fn(*args, **kwargs)
        if isinstance(leg, Leg):
            return leg
        return Leg(name, NEUTRAL, str(leg))
    except Exception as exc:
        return Leg(name, UNAVAILABLE,
                   f"could not measure: {type(exc).__name__}: {str(exc)[:200]}",
                   provenance=UNAVAILABLE)


# --------------------------------------------------------------------------
# LEG - token identity and market state
# --------------------------------------------------------------------------
def leg_identity(address: str, chain: str = "solana") -> Leg:
    """Resolve the token and its current market state from live DEX data.

    Uses the package's own tested DexScreener adapter rather than a
    raw call, so the retry, gzip and cache behaviour is the same one
    the rest of the package gets.
    """
    from . import market as MK
    pairs: List[Dict[str, Any]] = []
    prov = PROV.LIVE
    try:
        pairs, prov = MK.fetch_dex_pairs(address, limit=50)
    except Exception as exc:
        return Leg("IDENTITY", UNAVAILABLE,
                   f"DEX pair lookup failed: {type(exc).__name__}: "
                   f"{str(exc)[:180]}", provenance=UNAVAILABLE)
    if not pairs:
        return Leg("IDENTITY", UNAVAILABLE,
                   f"no DEX pair found for {address} on {chain}",
                   provenance=UNAVAILABLE)

    # A search can return other tokens. Prefer the pair whose BASE token
    # is the one asked for; fall back to the deepest pair.
    def _base_is_target(p: Dict[str, Any]) -> bool:
        b = (p.get("baseToken") or {}).get("address") or ""
        return str(b).lower() == str(address).lower()

    def _liq(p: Dict[str, Any]) -> float:
        try:
            return float((p.get("liquidity") or {}).get("usd") or 0.0)
        except Exception:
            return 0.0

    exact = [p for p in pairs if _base_is_target(p)]
    pool = exact or pairs
    pair = max(pool, key=_liq)
    liq = _liq(pair)
    base = pair.get("baseToken") or {}
    quote = pair.get("quoteToken") or {}
    price = None
    try:
        price = float(pair.get("priceUsd"))
    except Exception:
        pass
    metrics = {
        "symbol": base.get("symbol"),
        "name": base.get("name"),
        "pair_address": pair.get("pairAddress"),
        "price_usd": price,
        "liquidity_usd": liq,
        "fdv_usd": pair.get("fdv"),
        "volume_24h_usd": (pair.get("volume") or {}).get("h24"),
        "txns_24h": (pair.get("txns") or {}).get("h24"),
        "price_change_h24": (pair.get("priceChange") or {}).get("h24"),
        "dex": pair.get("dexId"),
        "quote_symbol": quote.get("symbol"),
        "url": pair.get("url"),
        "exact_base_match": bool(exact),
    }
    if liq <= 0:
        return Leg("IDENTITY", CONFLICTS,
                   "the pair exists but reports zero liquidity",
                   metrics, PROV.LIVE, blocking=True)
    return Leg("IDENTITY", SUPPORTS,
               f"{base.get('symbol')} on {pair.get('dexId')}, "
               f"pool ${liq:,.0f}, price ${price if price else 'n/a'}",
               metrics, PROV.LIVE)


# --------------------------------------------------------------------------
# LEG - data quality. This gates everything else.
# --------------------------------------------------------------------------
def leg_data_quality(legs: List[Leg]) -> Leg:
    """Grade how much of the evidence set actually answered.

    A signal built on two live sources out of eight is a signal built
    on a thin sample, and the verdict must say so.
    """
    total = len(legs)
    unavail = sum(1 for l in legs if l.verdict == UNAVAILABLE)
    live = sum(1 for l in legs if l.provenance == PROV.LIVE)
    answered = total - unavail
    metrics = {"legs_total": total, "legs_answered": answered,
               "legs_unavailable": unavail, "legs_live": live}
    if total == 0:
        return Leg("DATA_QUALITY", UNAVAILABLE, "no evidence gathered",
                   metrics, UNAVAILABLE, blocking=True)
    frac = answered / total
    metrics["answered_fraction"] = round(frac, 3)
    if frac < 0.4:
        return Leg("DATA_QUALITY", CONFLICTS,
                   f"only {answered}/{total} evidence legs answered - too "
                   f"thin to support a decision",
                   metrics, PROV.LIVE, blocking=True)
    if frac < 0.7:
        return Leg("DATA_QUALITY", NEUTRAL,
                   f"{answered}/{total} evidence legs answered - partial "
                   f"coverage, treat the brief as indicative",
                   metrics, PROV.LIVE)
    return Leg("DATA_QUALITY", SUPPORTS,
               f"{answered}/{total} evidence legs answered ({live} live)",
               metrics, PROV.LIVE)


# --------------------------------------------------------------------------
# LEG - research edge from the backtest gauntlet
# --------------------------------------------------------------------------
def _iter_verdicts(obj: Any):
    """Yield (name, verdict) from any of the shapes these artefacts use.

    The backtest artefacts have used three different shapes over time:
    a flat list of rows, a dict with a "results" list, and a dict keyed
    by specification name. Reading them positionally or with one
    hard-coded key silently produced the WRONG verdict set - which is
    exactly the kind of quiet failure this package is supposed to
    prevent. This reader handles all of them and skips the "_note"
    metadata keys.
    """
    if isinstance(obj, list):
        for r in obj:
            if isinstance(r, dict):
                name = (r.get("name") or r.get("spec") or r.get("spec_id")
                        or r.get("id"))
                yield name, str(r.get("verdict") or "").upper()
    elif isinstance(obj, dict):
        for key in ("results", "rows", "specs"):
            sub = obj.get(key)
            if isinstance(sub, list):
                for row in sub:
                    if isinstance(row, dict):
                        name = (row.get("name") or row.get("spec")
                                or row.get("spec_id") or row.get("id"))
                        yield name, str(row.get("verdict") or "").upper()
                return
        for name, v in obj.items():
            if name.startswith("_"):
                continue
            if isinstance(v, dict):
                yield name, str(v.get("verdict") or "").upper()


def leg_research_edge(project_root: Optional[str] = None) -> Leg:
    """What do the paper-derived specifications currently say?

    A specification counts as SUPPORTED only if the FULL gauntlet
    validated it, never the quick run.
    """
    root = _root(project_root)
    results = _read_json(os.path.join(root, "reports", "backtest_results.json"))
    if not results:
        return Leg("RESEARCH_EDGE", UNAVAILABLE,
                   "no backtest results artefact - run `backtest --all` first",
                   provenance=UNAVAILABLE)
    full = _read_json(os.path.join(root, "reports",
                                   "full_gauntlet_results.json")) or {}
    full_by_name = {n: v for n, v in _iter_verdicts(full) if n}
    quick_by_name = {n: v for n, v in _iter_verdicts(results) if n}
    supported, quick_only, refuted = [], [], []
    for name, quick_verdict in quick_by_name.items():
        full_verdict = full_by_name.get(name, "")
        if full_verdict == "SUPPORTED":
            supported.append(name)
        elif quick_verdict == "SUPPORTED":
            quick_only.append(name)
        else:
            refuted.append(name)
    # A specification the full gauntlet validated but that is missing
    # from the quick file still counts.
    for name, full_verdict in full_by_name.items():
        if full_verdict == "SUPPORTED" and name not in supported:
            supported.append(name)
    metrics = {"specs_total": len(quick_by_name) or len(full_by_name),
               "supported_full_gauntlet": supported,
               "supported_quick_only": quick_only,
               "refuted": len(refuted)}
    if supported:
        return Leg("RESEARCH_EDGE", SUPPORTS,
                   f"{len(supported)} specification(s) survived the FULL "
                   f"validation gauntlet: {', '.join(supported)}. That "
                   f"establishes a non-random PRIOR for the rule - it is "
                   f"not a live signal and not permission to trade it.",
                   metrics, PROV.LIVE)
    if quick_only:
        return Leg("RESEARCH_EDGE", NEUTRAL,
                   f"{len(quick_only)} specification(s) look supported under "
                   f"quick validation only - not enough to rely on.",
                   metrics, PROV.LIVE)
    return Leg("RESEARCH_EDGE", CONFLICTS,
               "no paper-derived specification is currently supported by the "
               "full validation gauntlet", metrics, PROV.LIVE)


# --------------------------------------------------------------------------
# LEG - qualified wallet behaviour. THE leg that can set a price.
# --------------------------------------------------------------------------
def _load_priced_wallets(project_root: Optional[str] = None) -> Dict[str, Any]:
    root = _root(project_root)
    data = _read_json(os.path.join(root, "reports", "pepe_priced_edge.json"))
    if data is None:
        return {}
    if isinstance(data, list):
        return {str(d.get("wallet", "")): d
                for d in data if isinstance(d, dict)}
    if isinstance(data, dict):
        for key in ("wallets", "results", "rows"):
            v = data.get(key)
            if isinstance(v, list):
                return {str(d.get("wallet", "")): d
                        for d in v if isinstance(d, dict)}
            if isinstance(v, dict):
                return v
    return {}


def _qualified_set(root: str) -> set:
    wl = _read_json(os.path.join(root, "leapspace", "state",
                                 "whitelist.json")) or {}
    entries = wl.get("wallets") or wl.get("entries") or []
    ok = {"WHITELISTED", "QUALIFIED", "ACTIVE"}
    if isinstance(entries, dict):
        return {w for w, v in entries.items()
                if isinstance(v, dict)
                and str(v.get("status", "")).upper() in ok}
    if isinstance(entries, list):
        return {str(e.get("wallet") or e.get("address"))
                for e in entries if isinstance(e, dict)
                and str(e.get("status", "")).upper() in ok}
    return set()


def _wallet_holds_token(d: Dict[str, Any], token_address: str) -> bool:
    addr = (token_address or "").lower()
    if not addr:
        return False
    for key in ("tokens", "tokens_held", "token_addresses", "symbols"):
        v = d.get(key)
        if isinstance(v, list):
            for t in v:
                if isinstance(t, dict):
                    cand = (t.get("address") or t.get("token_address")
                            or t.get("contract") or "")
                    if str(cand).lower() == addr:
                        return True
                elif str(t).lower() == addr:
                    return True
    for key in ("token_address", "address", "token"):
        if str(d.get(key) or "").lower() == addr:
            return True
    return False


def leg_qualified_wallets(token_address: str,
                          project_root: Optional[str] = None) -> Leg:
    """How many QUALIFIED wallets hold this token, and what did they do?

    A wallet qualifies only if it passed the consistency gate. Their
    realised entries, holds and exits are the ONLY evidence in this
    package that can justify a price level.
    """
    root = _root(project_root)
    priced = _load_priced_wallets(root)
    qualified = _qualified_set(root)

    holders_here, rejected_here = [], []
    for w, d in priced.items():
        if not isinstance(d, dict) or not _wallet_holds_token(d, token_address):
            continue
        verdict = str(d.get("verdict") or d.get("gate_verdict") or "").upper()
        if w in qualified or verdict in ("CONSISTENT", "QUALIFIED", "WHITELISTED"):
            holders_here.append((w, d))
        else:
            rejected_here.append((w, d, verdict))

    metrics = {
        "qualified_wallets_total": len(qualified),
        "wallets_holding_this_token": len(holders_here) + len(rejected_here),
        "qualified_holding_this_token": len(holders_here),
        "rejected_holding_this_token": len(rejected_here),
        "priced_artefact_wallets": len(priced),
    }
    if holders_here:
        entries_pr, holds, pnls = [], [], []
        for _w, d in holders_here:
            ep = d.get("median_entry_price") or d.get("entry_price")
            hd = d.get("median_hold_days") or d.get("hold_days")
            pl = d.get("total_realised_pnl_usd") or d.get("realised_pnl_usd")
            if ep is not None:
                entries_pr.append(float(ep))
            if hd is not None:
                holds.append(float(hd))
            if pl is not None:
                pnls.append(float(pl))
        metrics["median_entry_price"] = (statistics.median(entries_pr)
                                         if entries_pr else None)
        metrics["median_hold_days"] = (statistics.median(holds)
                                       if holds else None)
        metrics["aggregate_realised_pnl_usd"] = sum(pnls) if pnls else None
        return Leg("QUALIFIED_WALLETS", SUPPORTS,
                   f"{len(holders_here)} qualified wallet(s) hold this token. "
                   f"Median entry ${metrics['median_entry_price']}, median "
                   f"hold {metrics['median_hold_days']} days.",
                   metrics, PROV.LIVE)

    detail = (f"NO qualified wallet holds this token. {len(qualified)} "
              f"wallet(s) have passed the consistency gate in total and "
              f"none of them holds this asset.")
    if rejected_here:
        verdicts: Dict[str, int] = {}
        for _w, _d, v in rejected_here:
            verdicts[v or "UNKNOWN"] = verdicts.get(v or "UNKNOWN", 0) + 1
        detail += (f" {len(rejected_here)} wallet(s) that DO hold it scored: "
                   + ", ".join(f"{v} x{n}" for v, n in sorted(verdicts.items()))
                   + ". Their behaviour is not evidence of skill.")
        metrics["reject_verdicts"] = verdicts
    return Leg("QUALIFIED_WALLETS", CONFLICTS, detail, metrics, PROV.LIVE)


# --------------------------------------------------------------------------
# LEG - narrative specificity and traction, kept strictly separate
# --------------------------------------------------------------------------
def leg_narrative(address: str, chain: str = "solana") -> Leg:
    """Narrative specificity: does the project declare a specific story?

    Narrative is what the project SAYS about itself. It is not evidence
    of traction and it is not evidence of skill.
    """
    from . import memecoin as MC
    from . import narrative as NR
    try:
        profile, _prov = MC.fetch_token_profile(address)
    except Exception as exc:
        return Leg("NARRATIVE", UNAVAILABLE,
                   f"the token profile could not be retrieved: "
                   f"{type(exc).__name__}: {str(exc)[:140]}",
                   provenance=UNAVAILABLE)
    if not profile:
        return Leg("NARRATIVE", UNAVAILABLE,
                   "the token profile could not be retrieved",
                   provenance=UNAVAILABLE)
    pair: Dict[str, Any] = {}
    try:
        from . import market as MK
        pairs, _p = MK.fetch_dex_pairs(address, limit=10)
        if pairs:
            raw = pairs[0]
            try:
                pair = MK.normalise_dex_pair(raw)
            except Exception:
                pair = raw
    except Exception:
        pair = {}
    try:
        res = NR.classify_specificity(profile, pair)
    except Exception as exc:
        return Leg("NARRATIVE", UNAVAILABLE,
                   f"narrative classifier failed: {type(exc).__name__}: "
                   f"{str(exc)[:150]}", provenance=UNAVAILABLE)
    score = res.get("specificity_score")
    is_niche = bool(res.get("is_niche"))
    metrics = {"specificity_score": score, "is_niche": is_niche,
               "niche_threshold": res.get("niche_threshold"),
               "signals": res.get("signals"), "reasons": res.get("reasons"),
               "weights": res.get("weights")}
    verdict = SUPPORTS if is_niche else NEUTRAL
    return Leg("NARRATIVE", verdict,
               f"narrative specificity {score} of "
               f"{res.get('niche_threshold')} needed for niche "
               f"(niche={is_niche})",
               metrics, PROV.LIVE)


def leg_traction(address: str, chain: str = "solana") -> Leg:
    """Traction: observable market and community behaviour.

    Community size is UNMEASURED when it cannot be retrieved, never
    zero - an unavailable platform is not an empty one.
    """
    from . import social as S
    prof = S.fetch_social_profile(chain, address)
    tr = prof.get("traction") or {}
    cs = prof.get("community_size") or {}
    srcs = cs.get("sources") or {}
    metrics = {
        "price_usd": tr.get("price_usd"),
        "liquidity_usd": tr.get("liquidity_usd"),
        "volume_24h_usd": tr.get("volume_24h_usd"),
        "market_cap": tr.get("market_cap"),
        "buys_24h": tr.get("buys_24h"),
        "sells_24h": tr.get("sells_24h"),
        "buy_sell_ratio_24h": tr.get("buy_sell_ratio_24h"),
        "community_members": tr.get("community_members"),
    }
    per_platform: Dict[str, int] = {}
    for plat, info in srcs.items():
        if isinstance(info, dict):
            m = info.get("members")
            if m is not None:
                per_platform[plat] = m
    metrics["community_by_platform"] = per_platform
    total = tr.get("community_members")
    if not total:
        return Leg("TRACTION", UNAVAILABLE,
                   "community size could not be measured on any platform - "
                   "UNMEASURED, not zero", metrics, UNAVAILABLE)
    verdict = SUPPORTS if float(total) >= 1000 else NEUTRAL
    detail = ", ".join(f"{p} {v:,}" for p, v in sorted(per_platform.items()))
    return Leg("TRACTION", verdict,
               f"community size {int(total):,} ({detail or 'total only'}); "
               f"24h buy/sell {tr.get('buy_sell_ratio_24h')}",
               metrics, PROV.LIVE)


# --------------------------------------------------------------------------
# LEG - holder concentration and insider exposure
# --------------------------------------------------------------------------
def leg_holder_risk(address: str, chain: str = "solana") -> Leg:
    """Concentration and insider share of the holder base."""
    rows: List[Dict[str, Any]] = []
    source = ""
    if chain == "solana":
        from . import holders as H
        try:
            comp = H.rugcheck_holder_composition(address)
        except Exception as exc:
            return Leg("HOLDER_RISK", UNAVAILABLE,
                       f"holder composition unavailable: {type(exc).__name__}: "
                       f"{str(exc)[:150]}", provenance=UNAVAILABLE)
        rows = comp.get("holders") or []
        source = "rugcheck"
    else:
        from . import memecoinscan as MS
        try:
            res = MS.fetch_top_holders(address, chain, limit=50)
        except Exception as exc:
            return Leg("HOLDER_RISK", UNAVAILABLE,
                       f"holder list unavailable: {type(exc).__name__}: "
                       f"{str(exc)[:150]}", provenance=UNAVAILABLE)
        if isinstance(res, dict):
            if res.get("status") == "unavailable":
                return Leg("HOLDER_RISK", UNAVAILABLE,
                           f"holder source unavailable: {res.get('reason')}",
                           provenance=UNAVAILABLE)
            rows = res.get("holders") or []
        else:
            rows = res or []
        source = "blockscout"
    if not rows:
        return Leg("HOLDER_RISK", UNAVAILABLE, "no holder list returned",
                   provenance=UNAVAILABLE)

    # Normalise to (address, pct, insider).
    #
    # The EVM and Solana sources use DIFFERENT field names, and getting
    # this wrong is not cosmetic: if every share silently defaults to
    # 0.0, the concentration control reads "0% held by the top 10" and
    # returns SUPPORTS - a risk control that ALWAYS passes. So read
    # every known field name, and FAIL CLOSED when the denominator is
    # unknown.
    norm: List[Dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        pct = None
        for key in ("pct", "share", "percent"):
            if r.get(key) is not None:
                try:
                    pct = float(r[key])
                    break
                except (TypeError, ValueError):
                    pct = None
        absolute = None
        if pct is None:
            for key in ("value", "balance", "amount"):
                if r.get(key) is not None:
                    try:
                        absolute = float(r[key])
                        break
                    except (TypeError, ValueError):
                        absolute = None
        if pct is None and absolute is None:
            # Neither a percentage nor an absolute amount. This row is
            # uninterpretable, so it must NOT count as 0%.
            continue
        if pct is None:
            # An absolute amount (Blockscout reports `value` in the
            # token's smallest unit). It becomes a share only with the
            # total supply; without it we cannot say anything.
            continue
        norm.append({"address": r.get("address"), "pct": pct,
                     "insider": bool(r.get("insider")),
                     "kind": r.get("kind"), "entity": r.get("entity"),
                     "is_contract": bool(r.get("is_contract"))})

    # Absolute amounts: convert to shares using the total supply, which
    # is derived from the live market data.
    if not norm:
        supply = _total_supply(address, chain)
        if not supply:
            return Leg("HOLDER_RISK", UNAVAILABLE,
                       "the holder rows carried neither a percentage nor a "
                       "usable amount, so concentration is UNKNOWN - "
                       "explicitly NOT 0%",
                       {"source": source}, UNAVAILABLE)
        for r in rows:
            if not isinstance(r, dict):
                continue
            try:
                val = float(r.get("value") if r.get("value") is not None
                            else r.get("balance"))
            except (TypeError, ValueError):
                continue
            norm.append({"address": r.get("address"),
                         "pct": val / supply * 100.0,
                         "insider": bool(r.get("insider")),
                         "kind": r.get("kind"), "entity": r.get("entity"),
                         "is_contract": bool(r.get("is_contract"))})
        if not norm:
            return Leg("HOLDER_RISK", UNAVAILABLE,
                       "no holder row carried a usable amount",
                       {"source": source}, UNAVAILABLE)
        total_supply = supply
    else:
        total_supply = None

    top10 = sum(h["pct"] for h in norm[:10]) / 100.0
    insiders = sum(h["pct"] for h in norm if h["insider"]) / 100.0
    metrics = {"source": source, "holders_read": len(norm),
               "top10_supply_share": round(top10, 4),
               "top1_supply_share": round(norm[0]["pct"] / 100.0, 4),
               "insider_supply_share": round(insiders, 4),
               "total_supply": total_supply}
    if insiders > 0.10:
        return Leg("HOLDER_RISK", CONFLICTS,
                   f"insider-flagged addresses hold {insiders:.1%} of the "
                   f"supply", metrics, PROV.LIVE, blocking=True)
    if top10 > 0.50:
        return Leg("HOLDER_RISK", CONFLICTS,
                   f"the top 10 holders control {top10:.1%} of the supply - a "
                   f"single exit moves the price against you",
                   metrics, PROV.LIVE, blocking=True)
    if top10 > 0.30:
        return Leg("HOLDER_RISK", NEUTRAL,
                   f"the top 10 holders control {top10:.1%} of the supply",
                   metrics, PROV.LIVE)
    return Leg("HOLDER_RISK", SUPPORTS,
               f"the top 10 holders control {top10:.1%} of the supply; "
               f"insider-flagged share {insiders:.1%}",
               metrics, PROV.LIVE)


#: EVM block explorers that expose a token's total supply in the same
#: unit the holder balances are reported in (the token's smallest unit).
_SUPPLY_HOSTS = {
    "ethereum": "https://eth.blockscout.com",
    "base": "https://base.blockscout.com",
}


def _total_supply(address: str, chain: str = "solana") -> Optional[float]:
    """The token's total supply in its SMALLEST unit.

    The unit matters: Blockscout reports a holder's `value` in the
    token's smallest unit (PEPE: 18 decimals), so the supply must be in
    the same unit or every share is out by a factor of 10^decimals.

    Derived from DexScreener's fdv/price it would be in TOKENS, not in
    the smallest unit - that mistake produced shares 10^18 times too
    large. So the primary route is the explorer's own token record,
    which reports `total_supply` in the right unit; DexScreener is only
    a fallback and is scaled by the decimals when they are known.

    Returns None when the supply cannot be established, so the caller
    fails closed instead of reporting a share of zero.
    """
    from . import http as H

    host = _SUPPLY_HOSTS.get(chain)
    if host:
        try:
            resp = H.http_json(f"{host}/api/v2/tokens/{address}")
            data = resp[0] if isinstance(resp, tuple) else resp
            if isinstance(data, dict):
                raw = data.get("total_supply")
                if raw is not None:
                    supply = float(raw)
                    if supply > 0:
                        return supply
        except Exception:
            pass

    # Fallback: DexScreener's fdv/price gives the supply in TOKENS.
    # Only usable if the decimals are known, otherwise the unit is
    # ambiguous and the result is not returned.
    decimals = _token_decimals(address, chain)
    if decimals is None:
        return None
    try:
        from . import market as MK
        pairs, _p = MK.fetch_dex_pairs(address, limit=10)
    except Exception:
        return None
    if not pairs:
        return None

    def _liq(p: Dict[str, Any]) -> float:
        try:
            return float((p.get("liquidity") or {}).get("usd") or 0.0)
        except Exception:
            return 0.0

    def _base(p: Dict[str, Any]) -> str:
        return str((p.get("baseToken") or {}).get("address") or "").lower()

    exact = [p for p in pairs if _base(p) == str(address).lower()]
    pair = max(exact or pairs, key=_liq)
    try:
        price = float(pair.get("priceUsd"))
        fdv = float(pair.get("fdv"))
    except (TypeError, ValueError):
        return None
    if price <= 0 or fdv <= 0:
        return None
    return (fdv / price) * (10 ** decimals)


def _token_decimals(address: str, chain: str = "solana") -> Optional[int]:
    """The token's decimal count, or None when it cannot be established."""
    host = _SUPPLY_HOSTS.get(chain)
    if not host:
        return None
    try:
        from . import http as H
        resp = H.http_json(f"{host}/api/v2/tokens/{address}")
        data = resp[0] if isinstance(resp, tuple) else resp
        if isinstance(data, dict) and data.get("decimals") is not None:
            return int(data["decimals"])
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------
# LEG - liquidity. Can you actually get out?
# --------------------------------------------------------------------------
def leg_liquidity(identity: Leg, target_usd: float = 1000.0) -> Leg:
    """Is there enough depth to enter AND exit a target position?

    The rule used here - a position may be at most 1% of pool
    liquidity - is an ANALYST_CHOICE, not a cited standard, and is
    labelled as such wherever it appears.
    """
    liq = float((identity.metrics or {}).get("liquidity_usd") or 0.0)
    if liq <= 0:
        return Leg("LIQUIDITY", UNAVAILABLE,
                   "no liquidity figure to assess", provenance=UNAVAILABLE)
    max_pos = liq * 0.01
    metrics = {"pool_liquidity_usd": liq, "max_position_usd": max_pos,
               "target_usd": target_usd,
               "target_pct_of_pool": round(target_usd / liq, 5),
               "rule": "ANALYST_CHOICE: position <= 1% of pool liquidity"}
    if target_usd > max_pos:
        return Leg("LIQUIDITY", CONFLICTS,
                   f"a ${target_usd:,.0f} position is {target_usd/liq:.2%} of "
                   f"the ${liq:,.0f} pool - exit slippage would dominate",
                   metrics, PROV.LIVE, blocking=True)
    return Leg("LIQUIDITY", SUPPORTS,
               f"${liq:,.0f} of pool depth supports a ${target_usd:,.0f} "
               f"position (1% rule, ANALYST_CHOICE)",
               metrics, PROV.LIVE)


# --------------------------------------------------------------------------
# THE ASSEMBLY
# --------------------------------------------------------------------------
def assess_trade(address: str, chain: str = "solana",
                 target_usd: float = 1000.0,
                 project_root: Optional[str] = None,
                 risk_per_trade_pct: float = 0.005,
                 max_position_pct_of_liquidity: float = 0.01) -> TradeSignal:
    """Gather every leg of evidence and return a decision.

    The verdict follows a fixed precedence, so the outcome is auditable
    and not a judgement call:

      1. a blocking CONFLICT anywhere            -> AVOID
      2. data quality below the floor            -> NO_TRADE_DATA
      3. no qualified-wallet evidence            -> AVOID
      4. research prior but no wallet evidence   -> WATCH
      5. qualified-wallet evidence, no conflict  -> ENTER
    """
    root = _root(project_root)
    legs: List[Leg] = []

    identity = _leg_safe("IDENTITY", leg_identity, address, chain)
    legs.append(identity)
    legs.append(_leg_safe("RESEARCH_EDGE", leg_research_edge, root))
    legs.append(_leg_safe("QUALIFIED_WALLETS", leg_qualified_wallets,
                           address, root))
    legs.append(_leg_safe("NARRATIVE", leg_narrative, address, chain))
    legs.append(_leg_safe("TRACTION", leg_traction, address, chain))
    legs.append(_leg_safe("HOLDER_RISK", leg_holder_risk, address, chain))
    legs.append(_leg_safe("LIQUIDITY", leg_liquidity, identity, target_usd))

    dq = leg_data_quality(legs)
    legs.append(dq)

    blocking = [l for l in legs if l.blocking and l.verdict == CONFLICTS]
    unavail = [l for l in legs if l.verdict == UNAVAILABLE]
    qualified = next((l for l in legs if l.name == "QUALIFIED_WALLETS"), None)
    research = next((l for l in legs if l.name == "RESEARCH_EDGE"), None)

    if blocking:
        verdict, confidence = AVOID, "HIGH"
        reason = "blocked by: " + ", ".join(l.name for l in blocking)
    elif dq.verdict == CONFLICTS:
        verdict, confidence = NO_DATA, "INSUFFICIENT"
        reason = dq.detail
    elif qualified is not None and qualified.verdict == SUPPORTS:
        verdict, confidence = ENTER, "MEDIUM"
        reason = ("qualified-wallet evidence is present and nothing blocks "
                  "it - note the confidence is MEDIUM because no wallet in "
                  "the package has yet passed the gate at scale")
    elif research is not None and research.verdict == SUPPORTS:
        verdict, confidence = WATCH, "LOW"
        reason = ("a research prior exists but no qualified wallet holds "
                  "this token - the prior alone is not a signal")
    else:
        verdict, confidence = AVOID, "MEDIUM"
        reason = ("no qualified-wallet evidence and no supported research "
                  "edge for this asset")
    dq.metrics["verdict_reason"] = reason

    # ---- entry / exit ----------------------------------------------------
    if qualified is not None and qualified.verdict == SUPPORTS:
        m = qualified.metrics
        entry = {"basis": "EVIDENCE-BASED: qualified wallets' realised entries",
                 "price_usd": m.get("median_entry_price"),
                 "source_count": m.get("qualified_holding_this_token")}
        exit_ = {"basis": "EVIDENCE-BASED: qualified wallets' realised exits",
                 "hold_days_median": m.get("median_hold_days"),
                 "aggregate_realised_pnl_usd":
                     m.get("aggregate_realised_pnl_usd")}
    else:
        entry = {"basis": "NOT EVIDENCE-BASED - no qualified wallet holds "
                          "this token, so there is no reference level",
                 "price_usd": None}
        exit_ = {"basis": "NOT EVIDENCE-BASED - no qualified wallet holds "
                          "this token, so there is no reference exit",
                 "hold_days_median": None}

    # ---- sizing ----------------------------------------------------------
    liq = float((identity.metrics or {}).get("liquidity_usd") or 0.0)
    if verdict == ENTER:
        sizing = {"risk_per_trade_pct": risk_per_trade_pct,
                  "max_position_usd_by_liquidity":
                      liq * max_position_pct_of_liquidity,
                  "note": "no evidence-derived stop distance exists, so a "
                          "risk-based size cannot be computed; this is a "
                          "CEILING, not a recommendation"}
    else:
        sizing = {"position_usd": 0.0,
                  "note": f"the verdict is {verdict} - position size is zero"}

    invalidation = [
        "Liquidity falls below the level assumed in the sizing calculation.",
        "A qualified wallet exits - their exit is the reference exit.",
        "A re-run of the consistency gate returns a different verdict for a "
        "qualified wallet.",
        "Holder concentration rises above the level in the HOLDER_RISK leg.",
    ]
    if (identity.metrics or {}).get("pair_address"):
        invalidation.append(f"Pair {identity.metrics['pair_address']} stops "
                            f"printing a price.")

    gaps = [f"{l.name}: {l.detail}" for l in unavail] or \
           ["none - every evidence leg answered"]

    prov_summary: Dict[str, int] = {}
    for l in legs:
        prov_summary[l.provenance] = prov_summary.get(l.provenance, 0) + 1

    im = identity.metrics or {}
    token = {"address": address, "chain": chain, "symbol": im.get("symbol"),
             "pair_address": im.get("pair_address"),
             "price_usd": im.get("price_usd"),
             "liquidity_usd": im.get("liquidity_usd"), "dex": im.get("dex"),
             "url": im.get("url")}

    return TradeSignal(token=token, verdict=verdict, confidence=confidence,
                       legs=legs, entry=entry, exit=exit_, sizing=sizing,
                       invalidation=invalidation, gaps=gaps,
                       provenance_summary=prov_summary,
                       generated_at=PROV.utcnow_iso())


# --------------------------------------------------------------------------
# THE BRIEF
# --------------------------------------------------------------------------
def render_brief(sig: TradeSignal) -> str:
    """Render the decision as a briefing the user can act on."""
    L: List[str] = []
    t = sig.token
    L.append(f"# TRADE BRIEF - {t.get('symbol') or t.get('address')}")
    L.append("")
    L.append(f"**{t.get('chain')}** | `{t.get('address')}` | price "
             f"{t.get('price_usd')} | pool ${_fmt(t.get('liquidity_usd'))} on "
             f"{t.get('dex')}")
    L.append("")
    L.append(f"## VERDICT: {sig.verdict}   (confidence: {sig.confidence})")
    L.append("")
    dq = next((l for l in sig.legs if l.name == "DATA_QUALITY"), None)
    if dq:
        L.append(f"> {dq.metrics.get('verdict_reason', '')}")
        L.append("")
    L.append("| Evidence leg | Verdict | Detail |")
    L.append("|---|---|---|")
    for l in sig.legs:
        mark = {"SUPPORTS": "SUPPORT", "CONFLICTS": "CONFLICT",
                "NEUTRAL": "neutral", UNAVAILABLE: "N/A"}.get(l.verdict, l.verdict)
        L.append(f"| {l.name} | {mark} | {l.detail} |")
    L.append("")
    L.append("## ENTRY")
    L.append("")
    L.append(f"- Basis: {sig.entry.get('basis')}")
    if sig.entry.get("price_usd"):
        L.append(f"- Reference price: ${sig.entry['price_usd']}")
    L.append("")
    L.append("## EXIT")
    L.append("")
    L.append(f"- Basis: {sig.exit.get('basis')}")
    if sig.exit.get("hold_days_median"):
        L.append(f"- Median hold: {sig.exit['hold_days_median']} days")
    L.append("")
    L.append("## POSITION")
    L.append("")
    if sig.sizing.get("position_usd") == 0.0:
        L.append("- **ZERO.** The verdict is not ENTER.")
    else:
        for k, v in sig.sizing.items():
            L.append(f"- {k}: {v}")
    L.append("")
    L.append("## INVALIDATE THE THESIS IF")
    L.append("")
    for i in sig.invalidation:
        L.append(f"- {i}")
    L.append("")
    L.append("## WHAT COULD NOT BE MEASURED")
    L.append("")
    for g in sig.gaps:
        L.append(f"- {g}")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"Provenance: {sig.provenance_summary} | generated "
             f"{sig.generated_at}")
    L.append("")
    L.append("This brief is decision support for a human. It places no "
             "orders and it is not investment advice.")
    return "\n".join(L)


def _fmt(v: Any) -> str:
    try:
        return f"{float(v):,.0f}"
    except Exception:
        return "n/a"


def write_brief(sig: TradeSignal, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_brief(sig))
    payload = os.path.splitext(path)[0] + ".json"
    with open(payload, "w", encoding="utf-8") as fh:
        json.dump(sig.to_dict(), fh, indent=2, default=str)
    return path
