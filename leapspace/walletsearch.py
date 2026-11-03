"""leapspace.walletsearch - find wallets that are actually skilled.

WHY THIS EXISTS
---------------
The consistency gate (edge.evaluate_edge) rejects 15 of 15 PEPE top
holders. That is the correct verdict for the WRONG POPULATION.

PEPE's top-holder list is:
  - SURVIVORSHIP-SELECTED. It is the list of accounts that HELD the
    winner, which is exactly the list of accounts that made money.
  - LATE. The median first-buy was about 2.4 years after launch.
  - CONCENTRATED. The median largest position was 100% of the wallet's
    memecoin allocation.

So each candidate's history is one or two positions, and the gate
reduces 18 raw closed trades to ONE independent bet. The gate cannot
tell skill from luck on a sample of one - that is a statement about the
sample, not about the wallet.

THE FIX IS THE POPULATION, NOT THE THRESHOLD
--------------------------------------------
This module searches a DIFFERENT population: wallets that appear in
the EARLY-BUYER list of SEVERAL different tokens. Breadth is the
filter. A wallet that bought early in five unrelated memecoins is
structurally different from a whale that accumulated one token late,
and - critically - it has enough independent bets for the gate to
measure.

**The thresholds are NOT loosened here.** The gate's criteria are
frozen. If no wallet in the searched population passes, that is the
finding, and it is reported as such. Loosening a gate until something
passes would destroy the only thing that makes it trustworthy.

THE TWO SCREENS A CANDIDATE MUST PASS
--------------------------------------
1. `edge.evaluate_edge` on the FULL priced history across every token
   the wallet traded in the universe. This is the skill test.
2. The selection-bias correction. `trials_scanned` must be the number
   of candidates this scan EXAMINED before the winner was chosen, not
   the number that passed. That number is what deflates the Sharpe.
   The screen reports it, and the Deflated Sharpe is computed against
   it. This is the number the earlier scans got wrong by scanning 15
   candidates and reporting 15 as if it were small.

WHAT IT DOES NOT DO
-------------------
It places no orders, and it produces no verdict for a token. It finds
CANDIDATES and reports whether they cleared the gate. The trade brief
in `leapspace.signal` is what turns a qualified wallet into a
decision.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Sequence

from . import provenance as PROV

#: The default memecoin symbol set. Broad on purpose: the search needs
#: BREADTH in the candidate's history, and breadth comes from the
#: universe covering many tokens.
DEFAULT_SYMBOLS = [
    "PEPE", "SHIB", "DOGE", "FLOKI", "BONK", "WIF", "MOG", "BRETT",
    "POPCAT", "TURBO", "SPX6900", "BOME", "NEIRO", "TRUMP", "MEME",
    "FARTCOIN", "PNUT", "ACT", "GOAT", "CHILLGUY", "BANANA", "MYRO",
    "POPCAT", "PENGU", "MOODENG", "KIWI", "SIGMA", "MOBY", "KAITO",
]


# --------------------------------------------------------------------------
# 1. the universe
# --------------------------------------------------------------------------
def build_universe(chain: str = "ethereum",
                   symbols: Optional[Sequence[str]] = None,
                   extra_tokens: Optional[Sequence[Dict[str, Any]]] = None
                   ) -> Dict[str, Any]:
    """A wide memecoin universe, resolved from live market data.

    Addresses are never typed from memory - each is read from a live
    DexScreener pair record together with its liquidity and market cap
    at that moment.
    """
    from . import memecoinscan as MS
    syms = list(symbols or DEFAULT_SYMBOLS)
    base = MS.memecoin_universe(symbols=syms, chain=chain)
    tokens = list(base.get("tokens") or [])
    seen = {str(t.get("address")).lower() for t in tokens}

    # Extra tokens the operator supplies - typically NEW launches, so
    # the population is not only old-token whales.
    for t in (extra_tokens or []):
        addr = str(t.get("address") or "").lower()
        if not addr or addr in seen:
            continue
        seen.add(addr)
        tokens.append(dict(t))

    return {"chain": chain, "tokens": tokens,
            "n_tokens": len(tokens),
            "gaps": base.get("gaps") or [],
            "symbols_requested": syms}


# --------------------------------------------------------------------------
# 2. candidate discovery
# --------------------------------------------------------------------------
def discover_new_tokens(chain: str = "ethereum", limit: int = 20,
                        pages: int = 2,
                        progress: Optional[Any] = None) -> Dict[str, Any]:
    """Find FRESH memecoins on a chain, from the chain's live top pools.

    Fresh tokens matter for the EARLY-BUYER filter. On an old token the
    launch window is unreachable: PEPE's transfer history is so long
    that paging back to its launch needs thousands of pages, and the
    scan correctly refuses rather than guessing ("read 200 transfers
    without reaching the start of this token's history"). On a fresh
    token the whole history fits in a handful of pages, so the first
    buyers in its life are actually findable.

    This is a PRE-FILTER on the chain's highest-volume pools, not a
    screening verdict.
    """
    from . import chainregistry as CR
    try:
        res = CR.discover_memecoins(chain_id=chain, limit=limit, pages=pages,
                                    meme_only=True)
    except Exception as exc:  # noqa: BLE001
        return {"chain": chain, "tokens": [], "status": "error",
                "reason": f"{type(exc).__name__}: {str(exc)[:150]}"}
    out: List[Dict[str, Any]] = []
    for c in (res.get("candidates") or []):
        addr = str(c.get("address") or c.get("token_address") or "")
        if not addr:
            continue
        out.append({"symbol": c.get("symbol") or addr[:10],
                    "address": addr,
                    "liquidity_usd": c.get("liquidity_usd")
                    or c.get("liquidity"),
                    "volume_24h_usd": c.get("volume_24h_usd"),
                    "pair_created_at": c.get("pair_created_at"),
                    "source": "chain_top_pools"})
    if progress:
        progress(f"  fresh tokens on {chain}: {len(out)}")
    return {"chain": chain, "tokens": out, "status": res.get("status"),
            "gaps": res.get("gaps") or []}


def discover_candidates(universe: Dict[str, Any], chain: str = "ethereum",
                         max_tokens: Optional[int] = None,
                         holders_per_token: int = 50,
                         early_buyers: bool = True,
                         early_window_blocks: int = 1000,
                         early_max_pages: int = 40,
                         progress: Optional[Any] = None) -> Dict[str, Any]:
    """Find candidate wallets across the universe and score their BREADTH.

    For each token the module collects:
      - the top holders (from the chain's own explorer), and
      - the EARLY BUYERS (the first wallets in the token's life).

    A candidate is then scored by how many DIFFERENT tokens it appears
    in. That breadth is the population filter: one token is a fluke,
    several unrelated tokens is a track record.

    `early_window_blocks` and `early_max_pages` bound the early-buyer
    scan. It is the expensive part - it pages through the token's
    opening transfers - so on a constrained host these need to be
    tight. A narrow window still finds the genuinely early buyers,
    which is the point: the filter is about TIMING, not about covering
    every early trade.
    """
    from . import memecoinscan as MS
    from . import launchscan as LS

    tokens = list(universe.get("tokens") or [])
    if max_tokens:
        tokens = tokens[:max_tokens]

    by_addr: Dict[str, Dict[str, Any]] = {}
    per_token: List[Dict[str, Any]] = []
    gaps: List[Dict[str, Any]] = []

    for i, tok in enumerate(tokens):
        addr = str(tok.get("address") or "")
        sym = tok.get("symbol") or addr[:10]
        if not addr:
            continue
        holders, early = [], []
        t_start = time.time()
        try:
            res = MS.fetch_top_holders(addr, chain, limit=holders_per_token)
            if isinstance(res, dict):
                if res.get("status") == "unavailable":
                    gaps.append({"token": sym, "stage": "holders",
                                 "reason": res.get("reason")})
                holders = res.get("holders") or []
            else:
                holders = res or []
        except Exception as exc:  # noqa: BLE001
            gaps.append({"token": sym, "stage": "holders",
                         "reason": f"{type(exc).__name__}: {str(exc)[:120]}"})

        if early_buyers:
            try:
                eb = LS.early_buyers(addr, chain,
                                     window_blocks=early_window_blocks,
                                     max_pages=early_max_pages)
                early = (eb.get("early_buyers") or eb.get("buyers")
                         or eb.get("addresses") or []) if isinstance(eb, dict) \
                    else (eb or [])
            except Exception as exc:  # noqa: BLE001
                gaps.append({"token": sym, "stage": "early_buyers",
                             "reason": f"{type(exc).__name__}: {str(exc)[:120]}"})

        hset = {str(h.get("address") or "").lower() for h in holders
                if isinstance(h, dict) and h.get("address")}
        eset = {str(e if isinstance(e, str) else e.get("address") or "").lower()
                for e in early}
        eset.discard("")

        for a in (hset | eset):
            if not a:
                continue
            rec = by_addr.setdefault(a, {
                "address": a, "n_tokens": 0, "n_early": 0, "n_holder": 0,
                "tokens": [], "early_tokens": [], "holder_tokens": [],
            })
            rec["n_tokens"] += 1
            rec["tokens"].append(sym)
            if a in eset:
                rec["n_early"] += 1
                rec["early_tokens"].append(sym)
            if a in hset:
                rec["n_holder"] += 1
                rec["holder_tokens"].append(sym)

        per_token.append({"token": sym, "address": addr,
                          "holders": len(hset), "early_buyers": len(eset),
                          "seconds": round(time.time() - t_start, 1)})
        if progress:
            progress(f"  [{i+1}/{len(tokens)}] {sym}: {len(hset)} holders, "
                     f"{len(eset)} early buyers, "
                     f"{time.time() - t_start:.1f}s")

    candidates = list(by_addr.values())
    for c in candidates:
        # The rank key: breadth first, then how early they were.
        c["breadth_score"] = (c["n_early"] * 2) + c["n_holder"]
    candidates.sort(key=lambda c: (-c["breadth_score"], -c["n_tokens"], c["address"]))
    return {"chain": chain, "candidates": candidates,
            "n_candidates": len(candidates),
            "per_token": per_token, "gaps": gaps,
            "tokens_scanned": len(per_token)}


# --------------------------------------------------------------------------
# 3. screening
# --------------------------------------------------------------------------
def screen_candidates(candidates: Sequence[Dict[str, Any]],
                      universe: Dict[str, Any], chain: str = "ethereum",
                      trials_scanned: Optional[int] = None,
                      max_candidates: int = 25,
                      progress: Optional[Any] = None) -> Dict[str, Any]:
    """Price and gate each candidate.

    `trials_scanned` MUST be the number of candidates examined, not the
    number that passed. It is what deflates the Sharpe, and under-
    stating it is how a selection-bias-corrected test becomes a
    selection-biased one. It defaults to the number examined here.
    """
    from . import priced as PR

    examined = len(candidates)
    n_trials = int(trials_scanned) if trials_scanned else examined
    results: List[Dict[str, Any]] = []
    for i, c in enumerate(candidates[:max_candidates]):
        addr = c["address"]
        if progress:
            progress(f"  [{i+1}/{min(max_candidates, examined)}] {addr} "
                     f"(breadth {c.get('n_tokens')}, early "
                     f"{c.get('n_early')})")
        try:
            res = PR.screen_wallet(addr, universe, chain=chain,
                                   trials_scanned=n_trials)
        except Exception as exc:  # noqa: BLE001
            results.append({"address": addr, "status": "error",
                            "reason": f"{type(exc).__name__}: {str(exc)[:160]}",
                            "breadth": c.get("n_tokens")})
            continue
        res["breadth"] = c.get("n_tokens")
        res["n_early"] = c.get("n_early")
        res["n_holder"] = c.get("n_holder")
        res["tokens_seen"] = c.get("tokens")
        results.append(res)
    return {"chain": chain, "results": results,
            "candidates_examined": examined,
            "trials_scanned_for_dsr": n_trials,
            "n_qualified": sum(1 for r in results
                               if str(r.get("verdict", "")).upper()
                               in ("CONSISTENT", "QUALIFIED")),
            "verdict_counts": _counts(results)}


def _counts(results: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in results:
        v = str(r.get("verdict") or r.get("status") or "UNKNOWN").upper()
        out[v] = out.get(v, 0) + 1
    return out


# --------------------------------------------------------------------------
# 4. the orchestrator
# --------------------------------------------------------------------------
def search(chain: str = "ethereum",
           symbols: Optional[Sequence[str]] = None,
           extra_tokens: Optional[Sequence[Dict[str, Any]]] = None,
           max_tokens: Optional[int] = None,
           min_breadth: int = 2,
           max_candidates: int = 25,
           holders_per_token: int = 50,
           early_buyers: bool = True,
           progress: Optional[Any] = None) -> Dict[str, Any]:
    """The whole search: universe -> candidates -> screened -> ranked.

    Returns a dict with the qualified wallets (if any), the full
    candidate table, and an explicit statement of what could not be
    measured.
    """
    universe = build_universe(chain=chain, symbols=symbols,
                              extra_tokens=extra_tokens)
    if progress:
        progress(f"universe: {universe['n_tokens']} tokens on {chain} "
                 f"({len(universe['gaps'])} gap(s))")
    disc = discover_candidates(universe, chain=chain, max_tokens=max_tokens,
                               holders_per_token=holders_per_token,
                               early_buyers=early_buyers, progress=progress)
    if progress:
        progress(f"candidates: {disc['n_candidates']} distinct wallets "
                 f"across {disc['tokens_scanned']} tokens")

    wide = [c for c in disc["candidates"] if c.get("n_tokens", 0) >= min_breadth]
    if progress:
        progress(f"{len(wide)} candidate(s) reached the breadth floor of "
                 f"{min_breadth} token(s)")

    scr = screen_candidates(wide or disc["candidates"][:max_candidates],
                            universe, chain=chain,
                            max_candidates=max_candidates, progress=progress)
    qualified = [r for r in scr["results"]
                 if str(r.get("verdict", "")).upper() in ("CONSISTENT",
                                                         "QUALIFIED")]
    qualified.sort(key=lambda r: -(r.get("edge_score") or 0))

    return {
        "status": "ok",
        "chain": chain,
        "universe": {"n_tokens": universe["n_tokens"],
                     "gaps": universe["gaps"]},
        "discovery": {"n_candidates": disc["n_candidates"],
                      "tokens_scanned": disc["tokens_scanned"],
                      "gaps": disc["gaps"],
                      "min_breadth": min_breadth,
                      "n_passing_breadth": len(wide)},
        "screening": {k: v for k, v in scr.items() if k != "results"},
        "qualified": qualified,
        "n_qualified": len(qualified),
        "results": scr["results"],
        "thresholds_note": (
            "The consistency gate's thresholds were NOT changed. Only the "
            "candidate POPULATION was widened. If nothing qualified, that "
            "is the finding for this population."),
        "generated_at": PROV.utcnow_iso(),
    }


def render_report(result: Dict[str, Any]) -> str:
    """A human-readable summary of a search."""
    L: List[str] = []
    L.append("# WALLET SEARCH RESULT")
    L.append("")
    L.append(f"**chain:** {result.get('chain')}  |  "
             f"**generated:** {result.get('generated_at')}")
    L.append("")
    disc = result.get("discovery") or {}
    scr = result.get("screening") or {}
    L.append(f"- tokens scanned: **{disc.get('tokens_scanned')}** "
             f"(universe {((result.get('universe') or {}).get('n_tokens'))})")
    L.append(f"- distinct candidate wallets: **{disc.get('n_candidates')}**")
    L.append(f"- passed the breadth floor of {disc.get('min_breadth')}: "
             f"**{disc.get('n_passing_breadth')}**")
    L.append(f"- candidates examined: **{scr.get('candidates_examined')}**")
    L.append(f"- trials used to deflate the Sharpe: "
             f"**{scr.get('trials_scanned_for_dsr')}**")
    L.append(f"- **QUALIFIED: {result.get('n_qualified')}**")
    L.append("")
    counts = scr.get("verdict_counts") or {}
    if counts:
        L.append("| Verdict | Wallets |")
        L.append("|---|---|")
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
            L.append(f"| {k} | {v} |")
        L.append("")
    L.append("## The candidates")
    L.append("")
    L.append("| Wallet | Breadth | Early | Verdict | PnL | Reason |")
    L.append("|---|---|---|---|---|---|")
    for r in (result.get("results") or [])[:40]:
        L.append(f"| `{str(r.get('address') or '')[:16]}` "
                 f"| {r.get('breadth')} | {r.get('n_early')} "
                 f"| {r.get('verdict') or r.get('status')} "
                 f"| {r.get('total_realised_pnl_usd')} "
                 f"| {str(r.get('reason') or '')[:60]} |")
    L.append("")
    if result.get("n_qualified"):
        L.append("## QUALIFIED")
        L.append("")
        for r in result["qualified"]:
            L.append(f"### `{r.get('address')}`")
            L.append(f"- verdict: {r.get('verdict')}")
            L.append(f"- reason: {r.get('reason')}")
            L.append(f"- independent bets: "
                     f"{r.get('effective_sample_size')}")
            L.append(f"- realised PnL: ${r.get('total_realised_pnl_usd')}")
            L.append(f"- tokens: {', '.join((r.get('tokens_seen') or [])[:12])}")
            L.append("")
    else:
        L.append("## No wallet qualified")
        L.append("")
        L.append("Every candidate in this population failed the consistency "
                 "gate. The thresholds were not changed - only the "
                 "population was widened. That is the finding for this "
                 "population: it contains no demonstrably skilled wallet "
                 "that the gate can measure.")
        L.append("")
    gaps = (disc.get("gaps") or [])[:10]
    if gaps:
        L.append("## What could not be measured")
        L.append("")
        for g in gaps:
            L.append(f"- {g.get('token')} ({g.get('stage')}): "
                     f"{str(g.get('reason'))[:110]}")
        L.append("")
    L.append("---")
    L.append("")
    L.append(result.get("thresholds_note", ""))
    return "\n".join(L)


def save(result: Dict[str, Any], path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, default=str)
    md = os.path.splitext(path)[0] + ".md"
    with open(md, "w", encoding="utf-8") as fh:
        fh.write(render_report(result))
    return path
