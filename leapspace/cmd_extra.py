"""CLI command bodies that live outside quant.py.

They were moved here so that quant.py stays readable and so that the
command wiring can be verified independently of the argument parser.
`quant.py` imports these names.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def _out(obj: Any, as_json: bool = True) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, default=str))


# --------------------------------------------------------------------------
# holders - the holder-composition time series
# --------------------------------------------------------------------------
def cmd_holders(args) -> int:
    """Holder composition over time, and abrupt ownership changes.

    A screener that is stateless per call cannot answer "abrupt
    ownership changes around price spikes", because that question is
    about the CHANGE between two snapshots. This command records a
    snapshot and, with `--detect`, compares the stored series.
    """
    from .holders import (detect_ownership_shifts, load_series,
                           record_snapshot, rugcheck_holder_composition)
    from .market import fetch_dex_pairs

    chain = args.chain or "solana"
    token = args.token

    if args.detect:
        res = detect_ownership_shifts(
            chain, token,
            spike_pct=args.spike_pct if args.spike_pct is not None else 50.0,
            concentration_delta_pp=(args.delta_pp
                                    if args.delta_pp is not None else 10.0))
        print(f"OWNERSHIP SHIFTS — {token} ({chain})")
        if res.get("status") != "ok":
            print(f"  {res.get('status')}: {res.get('reason')}")
            print("  A shift needs at least two time-separated snapshots. "
                  "Record one with:  holders --token <mint>")
            return 2
        print(f"  snapshots compared: {res.get('n_snapshots')}")
        shifts = res.get("shifts") or []
        print(f"  shifts detected  : {len(shifts)}")
        for s in shifts[:12]:
            print(f"    {s}")
        if not shifts:
            print("    none")
        if args.json:
            _out(res)
        return 0

    # ---- record a snapshot ---------------------------------------------
    if chain == "solana":
        comp = rugcheck_holder_composition(token)
        if comp.get("status") != "ok":
            print(f"HOLDERS — {token}: {comp.get('status')} "
                  f"{comp.get('reason')}")
            return 2
    else:
        from .holders import evm_holder_composition
        comp = evm_holder_composition(None, token)

    price = args.price
    if price is None:
        try:
            pairs = fetch_dex_pairs(token)
            if pairs:
                price = pairs[0].get("price_usd")
        except Exception as exc:  # noqa: BLE001
            print(f"  price fetch failed: {type(exc).__name__}: {exc}")

    rec = record_snapshot(chain, token, comp, price_usd=price,
                          price_change_24h=args.change24h)
    print(f"HOLDER SNAPSHOT — {token} ({chain})")
    print(f"  top-10 share     : {comp.get('top_n_pct')}%")
    print(f"  gini             : {comp.get('gini')}")
    print(f"  nakamoto coeff   : {comp.get('nakamoto')}")
    print(f"  concentration    : {comp.get('concentration_class')}")
    print(f"  price at snapshot: {price}")
    print(f"  source           : {comp.get('source')}")
    print(f"  recorded -> {rec.get('path')}")
    if args.json:
        _out({"composition": comp, "snapshot": rec})
    return 0


# --------------------------------------------------------------------------
# memeflow - top holders, classified, with allocation patterns
# --------------------------------------------------------------------------
def cmd_memeflow(args) -> int:
    """Top holders of a memecoin, classified, with their allocation."""
    from .memecoinscan import (memecoin_universe, token_holders,
                               wallet_memecoin_profile)

    chain = args.chain or "ethereum"
    token = args.token
    uni = memecoin_universe()
    holders = token_holders(token, chain=chain, top=args.top)
    print(f"TOP HOLDERS — {token} ({chain})")
    if holders.get("status") != "ok":
        print(f"  {holders.get('status')}: {holders.get('reason')}")
        return 2

    rows = holders.get("holders") or []
    counts: Dict[str, int] = {}
    for h in rows:
        counts[h.get("entity") or "EOA"] = counts.get(h.get("entity") or "EOA", 0) + 1
    print(f"  {len(rows)} holders   "
          + "   ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print()
    for h in rows[:min(args.top, 20)]:
        print(f"    {h['address'][:26]:<28} {h.get('entity','?'):<10} "
              f"{h.get('value', 0):,.0f}  {h.get('name') or ''}")
    if len(rows) > 20:
        print(f"    ... and {len(rows) - 20} more")

    traders = [h for h in rows
               if h.get("entity") == "EOA" and not h.get("is_contract")]
    if traders:
        print()
        print(f"  ALLOCATION PATTERNS of the {len(traders)} personal traders")
        for h in traders[:6]:
            p = wallet_memecoin_profile(h["address"], uni, chain=chain,
                                        max_items=120)
            if p.get("status") != "ok":
                continue
            print(f"    {h['address'][:24]:<26} "
                  f"tokens={p.get('n_meme_tokens_bought')} "
                  f"closed={p.get('n_meme_tokens_closed')} "
                  f"entry={p.get('entry_class_breakdown')} "
                  f"median_hold={p.get('median_hold_days')}d "
                  f"flows_to_exchange={p.get('flows_to_exchange')}")
    if args.json:
        _out({"holders": holders, "universe": uni})
    return 0


# --------------------------------------------------------------------------
# traders - qualification against the cited standards
# --------------------------------------------------------------------------
def cmd_traders(args) -> int:
    """Wallet qualification against the cited standards."""
    from .traders import (criteria_table, load_pool, pool_report,
                          qualify_wallet, record_evaluation,
                          track_wallets)

    if args.criteria:
        rows = criteria_table()
        print("QUALIFICATION CRITERIA")
        print()
        for r in rows:
            thr = r.get("threshold")
            thr = "-" if thr is None else str(thr)
            print(f"  {r.get('key') or r.get('label'):<38} {thr:<12} "
                  f"{str(r.get('tag') or r.get('authority'))[:46]}")
            if r.get("url"):
                print(f"      {r['url'][:110]}")
        if args.json:
            _out(rows)
        return 0

    if args.pool:
        rep = pool_report()
        print("QUALIFIED POOL")
        print(f"  members: {len(rep.get('qualified') or [])}")
        for x in (rep.get("qualified") or [])[:20]:
            print(f"    {x.get('address','')[:24]:<26} {x.get('chain',''):<12} "
                  f"{str(x.get('verdict'))[:14]:<16} "
                  f"trades={x.get('n_closed_trades')}")
        if args.json:
            _out(rep)
        return 0

    if args.track:
        res = track_wallets(chain=args.chain or "solana", limit=25)
        print(f"FORWARD COHORT — {args.chain or 'solana'}")
        print(f"  status: {res.get('status')}")
        print(f"  {str(res)[:600]}")
        if args.json:
            _out(res)
        return 0

    if args.wallet:
        from .memecoinscan import memecoin_universe, wallet_memecoin_profile
        chain = args.chain or "solana"
        uni = memecoin_universe()
        prof = wallet_memecoin_profile(args.wallet, uni, chain=chain,
                                       max_items=250)
        if prof.get("status") != "ok":
            print(f"TRADERS — {args.wallet}: {prof.get('status')} "
                  f"{prof.get('reason')}")
            return 2
        v = qualify_wallet(prof)
        print(f"TRADERS — {args.wallet} ({chain})")
        for k, val in v.items():
            if isinstance(val, (dict, list)):
                val = json.dumps(val, default=str)[:220]
            print(f"  {k}: {val}")
        if args.record:
            record_evaluation(args.wallet, chain, v)
            print("  recorded into the qualified pool")
        if args.json:
            _out(v)
        return 0

    print("traders — pass --wallet ADDR, --criteria, --pool or --track")
    return 2


# --------------------------------------------------------------------------
# edge - the consistency gate
# --------------------------------------------------------------------------
def cmd_edge(args) -> int:
    """Evaluate a wallet's edge against the fluke tests."""
    from .edge import evaluate_edge

    trades: List[Dict[str, Any]] = []
    if args.trades:
        with open(args.trades, "r", encoding="utf-8") as fh:
            trades = json.load(fh)
    elif args.mint:
        from .memecoinscan import memecoin_universe, wallet_memecoin_profile
        uni = memecoin_universe()
        p = wallet_memecoin_profile(args.mint, uni,
                                    chain=args.chain or "ethereum",
                                    max_items=200)
        trades = p.get("positions") or []
    if not trades:
        print("edge: pass --trades FILE (a JSON list of trades) or --mint "
              "ADDRESS")
        return 2

    v = evaluate_edge(trades, trials_scanned=args.trials or 1)
    if args.json:
        _out(v)
        return 0
    print(f"EDGE VERDICT: {v['verdict']}")
    print(f"  {v['reason']}")
    print()
    print(f"  closed trades      : {v['n_closed_trades']}  "
          f"({v['wins']}W/{v['losses']}L, wr={v['win_rate']})")
    print(f"  independent bets   : "
          f"{v['independent_bets']['independent_bets']}"
          f"  across {v['independent_bets']['distinct_tokens']} tokens")
    wi = v.get("wilson_interval") or {}
    if wi.get("status") == "computed":
        print(f"  win rate 95% CI    : [{wi['lower']:.3f}, {wi['upper']:.3f}]")
    print(f"  P(win rate > 50%)  : {v['bayesian_skill_p']}")
    print(f"  total realised PnL : ${v['total_realised_pnl_usd']:,.0f}")
    print(f"  largest win share  : {v['largest_win_share']}")
    print(f"  sharpe / sortino   : {v['sharpe_per_trade']} / "
          f"{v['sortino_per_trade']}")
    print(f"  deflated sharpe    : {v['deflated_sharpe']}  "
          f"(after {v['trials_scanned']} candidate(s) scanned)")
    print(f"  consistency ratio  : {v['consistency_ratio']}")
    print()
    print("  FLUKE TESTS:")
    for t in v["fluke_tests"]:
        mark = "FAIL" if t["failed"] else "pass"
        print(f"    [{mark}] {t['test']:<28} [{t.get('binding')}] {t['detail']}")
    print()
    print(f"  {v['trials_note']}")
    return 0


# --------------------------------------------------------------------------
# whitelist - the registry of consistent traders
# --------------------------------------------------------------------------
def cmd_whitelist(args) -> int:
    """The whitelist of consistent traders, with rejected candidates shown."""
    from .whitelist import record_evaluation, whitelist_report

    if args.wallet and args.trades:
        from .edge import evaluate_edge
        with open(args.trades, "r", encoding="utf-8") as fh:
            trades = json.load(fh)
        edge = evaluate_edge(trades, trials_scanned=args.trials or 1)
        e = record_evaluation(args.wallet, args.chain or "ethereum", edge,
                              cluster_id=args.cluster)
        if args.json:
            _out(e)
            return 0
        print(f"WHITELIST ENTRY: {e['key']}  status={e['status']}")
        print(f"  verdict  : {edge['verdict']} - {edge['reason']}")
        print(f"  history  : {len(e.get('history') or [])} evaluation(s)")
        return 0

    rep = whitelist_report()
    if args.json:
        _out(rep)
        return 0
    print("WHITELIST - consistent memecoin traders")
    print()
    print(f"  WHITELISTED ({len(rep['whitelisted'])}):")
    for x in rep["whitelisted"]:
        print(f"    {x['address'][:20]:<22} "
              f"chains={','.join(x.get('chains') or [])}"
              f"  trades={x.get('n_closed_trades')}  "
              f"bets={x.get('independent_bets')}  "
              f"skill_p={x.get('bayesian_skill_p')}")
        if x.get("promoted_reason"):
            print(f"        {x['promoted_reason'][:150]}")
    print(f"  WATCH ({len(rep['watch'])}):")
    for x in rep["watch"]:
        print(f"    {x['address'][:20]:<22} {str(x.get('reason'))[:110]}")
    print(f"  FLUKE REJECTED ({len(rep['fluke_rejected'])}):")
    for x in rep["fluke_rejected"]:
        print(f"    {x['address'][:20]:<22} {str(x.get('reason'))[:110]}")
    print(f"  RETIRED, HISTORY RETAINED "
          f"({len(rep['retired_history_retained'])}):")
    for x in rep["retired_history_retained"]:
        print(f"    {x['address'][:20]:<22} "
              f"history_entries={x.get('history_entries')}  "
              f"{str(x.get('retired_reason'))[:100]}")
    print()
    print(f"  {rep['selection_bias_note']}")
    print(f"  {rep['retention_rule']}")
    return 0


# --------------------------------------------------------------------------
# launchscan - the NEW-meme path
# --------------------------------------------------------------------------
def cmd_launchscan(args) -> int:
    """Find the early buyers of a freshly launched meme and test them.

    A new token has no holder list worth reading and no history. What it
    does have is a launch window: the buyers who arrived in the first N
    blocks. Those wallets are judged on their PRIOR record on
    established memes, which is the record a new token cannot provide.
    """
    from .launchscan import early_buyers, screen_early_buyers
    from .memecoinscan import memecoin_universe

    chain = args.chain or "ethereum"
    token = args.token
    universe = memecoin_universe()
    eb = early_buyers(token, chain=chain, window_blocks=args.window or 1000,
                      max_pages=args.pages or 30)
    if eb.get("status") != "ok":
        print(f"LAUNCH SCAN — {token}")
        print(f"  status: {eb.get('status')}")
        print(f"  reason: {eb.get('reason')}")
        print("\n  The launch window could not be identified. This is a "
              "source-coverage gap, NOT evidence that nobody bought early.")
        return 2

    launch = eb.get("launch") or {}
    creator = (launch.get("creator") or "").lower()
    print(f"LAUNCH SCAN — {token} ({chain})")
    print(f"  launch block {launch.get('launch_block')}   "
          f"creator {str(launch.get('creator'))[:24]}")
    print(f"  buyers in the first {eb.get('window_blocks')} blocks: "
          f"{eb.get('n_buyers_in_window')}")
    print()
    for b in eb.get("buyers") or []:
        tag = ("  <-- THE DEPLOYER"
               if (b["address"] or "").lower() == creator else "")
        print(f"    {b['address'][:26]:<28} lag={b['entry_lag_blocks']:>6} "
              f"({b['entry_class']:<22}) bought={b['bought']:>18,.0f}{tag}")

    res = screen_early_buyers(token, chain=chain,
                              window_blocks=args.window or 1000,
                              universe=universe,
                              max_candidates=args.candidates or 25,
                              early=eb)
    print()
    print("  EDGE SCREEN (their PRIOR record on established memes)")
    print(f"  candidates scanned: {res.get('candidates_scanned')}  - this "
          f"number enters the Deflated Sharpe, so a wider screen raises the "
          f"bar for every one of them")
    for c in res.get("candidates", []):
        rej = c.get("rejected_by")
        rej_s = ",".join(t["test"] for t in rej) if isinstance(rej, list) else ""
        print(f"    {str(c['address'])[:26]:<28} "
              f"verdict={c.get('edge_verdict'):<13} "
              f"prior_memes={c.get('prior_meme_tokens')} "
              f"bets={c.get('independent_bets')} "
              f"skill_p={c.get('skill_p')}")
        if rej_s:
            print(f"        rejected_by: {rej_s}")

    if args.json:
        _out({"early_buyers": eb, "screen": res})
    return 0


# --------------------------------------------------------------------------
# etherscan - the keyed source, used as a fallback and for balances
# --------------------------------------------------------------------------
def cmd_etherscan(args) -> int:
    """Etherscan V2: the one source that needs a key.

    The key is read from the environment (ETHERSCAN_API_KEY), which
    `leapspace/http.py` populates from the gitignored `.secrets.env`.
    It is never printed, never logged and never written to an artefact.
    """
    from . import etherscan

    if args.actions:
        print("ETHERSCAN V2 FREE TIER - verified live 2026-11-03")
        print()
        for k, v in etherscan.FREE_TIER_ACTIONS.items():
            mark = "PRO " if v.startswith("PRO") else "ok  "
            print(f"  [{mark}] {k:<28} {v}")
        print()
        print("  the key is configured: "
              f"{'yes' if etherscan.has_key() else 'no'}")
        return 0

    if not etherscan.has_key():
        print("ETHERSCAN — no key configured.")
        print("  Set ETHERSCAN_API_KEY in the environment, or put it in")
        print("  the gitignored .secrets.env beside the package.")
        return 2

    chain = args.chain or "ethereum"
    if args.balances:
        addrs = [a.strip() for a in args.balances.split(",") if a.strip()]
        r = etherscan.token_balances(addrs, args.token, chain=chain)
        print(f"ERC-20 BALANCES — {args.token} ({chain})")
        if r.get("status") != "ok":
            print(f"  {r.get('status')}: {r.get('reason')}")
            return 2
        for b in r.get("balances") or []:
            print(f"  {b['address'][:26]:<28} {b['balance_raw']:,}")
        return 0

    if args.holders:
        r = etherscan.token_holders_from_transfers(args.token, chain=chain)
        print(f"HOLDERS — {args.token} ({chain})")
        if r.get("status") != "ok":
            print(f"  {r.get('status')}: {r.get('reason')}")
            return 2
        print(f"  {r.get('n_holders')} holders netted from "
              f"{r.get('n_transfers_read')} transfers")
        for h in (r.get("holders") or [])[:15]:
            print(f"    {h['address'][:28]:<30} {h['pct']:.4f}%")
        return 0

    r = etherscan.token_transfers(args.token, chain=chain, limit=200)
    print(f"TOKEN TRANSFERS — {args.token} ({chain})")
    if r.get("status") != "ok":
        print(f"  {r.get('status')}: {r.get('reason')}")
        return 2
    print(f"  {r.get('n_transfers')} transfers")
    for t in (r.get("transfers") or [])[:10]:
        print(f"    {t['ts']}  {str(t['from'])[:16]} -> "
              f"{str(t['to'])[:16]}  {t['value']:,.0f}")
    return 0


# --------------------------------------------------------------------------
# vizmem - the memecoin charts
# --------------------------------------------------------------------------
def cmd_vizmem(args) -> int:
    """Build the memecoin-trader charts from the real artefacts.

    Five charts: the gate's raw-vs-independent-bet collapse, the
    whitelist registry, the price-at-block accuracy, the criteria
    coverage, and the community-size series as it accrues.
    """
    import json
    import os

    from . import viz_memecoin as VM

    root = args.root or os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))
    out = args.out or os.path.join(root, "reports", "charts")
    os.makedirs(out, exist_ok=True)

    def load(rel, default=None):
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return default

    made = []
    priced = load("reports/pepe_priced_edge.json", {}) or {}
    results = priced.get("results") or []
    if results:
        p = VM.chart_edge_gate(results, os.path.join(out, "edge_gate.png"))
        if p:
            made.append(p)

    wl = load("leapspace/state/whitelist.json", {}) or {}
    if (wl.get("entries") or wl.get("events")):
        p = VM.chart_whitelist(wl, os.path.join(out, "whitelist.png"))
        if p:
            made.append(p)

    p = VM.chart_price_accuracy(os.path.join(out, "price_accuracy.png"))
    if p:
        made.append(p)

    try:
        from .report_memecoin import build_memecoin_sections
        _sec = (build_memecoin_sections(root).get("sections") or {})
        _cov = _sec.get("criteria_coverage") or {}
        rows = (_cov.get("rows") or _cov.get("criteria")
                or _cov.get("table") or [])
        if isinstance(rows, dict):
            rows = list(rows.values())
        if rows:
            p = VM.chart_criteria_coverage(rows,
                                           os.path.join(out, "criteria.png"))
            if p:
                made.append(p)
    except Exception as exc:
        print(f"  criteria chart skipped: {type(exc).__name__}: "
              f"{str(exc)[:90]}")

    series = {}
    sd = os.path.join(root, "leapspace", "state", "social_series")
    if os.path.isdir(sd):
        for fn in os.listdir(sd):
            if fn.endswith(".json"):
                blob = load(os.path.join("leapspace", "state",
                                         "social_series", fn), {}) or {}
                snaps = blob.get("snapshots") or []
                if snaps:
                    series[fn[:22]] = snaps
    if series:
        p = VM.chart_community_series(series,
                                      os.path.join(out, "community.png"))
        if p:
            made.append(p)

    print(f"charts written: {len(made)} -> {out}")
    for m in made:
        print(f"  {os.path.basename(m)}")
    if args.json:
        _out({"charts": made, "out_dir": out})
    return 0


# --------------------------------------------------------------------------
# signal - the trade-decision engine
# --------------------------------------------------------------------------
def cmd_signal(args) -> int:
    """Produce a decision-ready trade brief for one token.

    This is the command that answers the question the whole package
    exists to answer: "should I trade this pair, and why?" It gathers
    every leg of evidence, grades the quality of that evidence, and
    emits a verdict with an entry reference, an exit reference, an
    invalidation list, a position size and - crucially - the list of
    things it could NOT measure.

    It never places an order.
    """
    import os
    from .signal import assess_trade, render_brief, write_brief

    sig = assess_trade(args.token, args.chain or "solana",
                       target_usd=float(args.target_usd or 1000.0))

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = getattr(args, "out", None) or os.path.join(root, "reports",
                                                         "briefs")
    name = (sig.token.get("symbol") or "token").upper()
    path = os.path.join(out_dir, f"{name}_TRADE_BRIEF.md")
    write_brief(sig, path)

    if getattr(args, "json", False):
        print(json.dumps(sig.to_dict(), indent=2, default=str))
    else:
        print(render_brief(sig))
        print(f"\nbrief written: {path}")
    return 0
