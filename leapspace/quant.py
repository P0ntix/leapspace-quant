"""On-chain memecoin quant CLI: chains, profiling, consensus, simulation, risk.

These subcommands implement the operator brief's four quadrants:

  Q1 KNOWN KNOWLEDGE      -> deterministic rules in code: the friction model,
                             the copy-trading simulator, the stop-losses, and
                             the kill switch.
  Q2 KNOWN UNKNOWNS       -> the rug injector and the MEV simulator: we know
                             these happen, we inject them to test survival.
  Q3 UNKNOWN KNOWLEDGE    -> the bias auditor: look-ahead, survivorship,
                             overfitting.
  Q4 UNKNOWN UNKNOWING    -> the anomaly log, and the human-in-the-loop
                             escalation when the kill switch fires.

Every command prints its provenance and its source gaps, like the rest of
this package. Nothing here invents on-chain data: an unreachable source
produces a gap record, never a plausible number.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from .models import CHAINS, SUPPORTED_CHAINS, to_json

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data", "operator_config.json")
STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")


def load_config(path: str = CONFIG_PATH) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _out(obj: Any, as_json: bool) -> None:
    if as_json:
        print(to_json(obj))


def _cfg(args) -> Dict[str, Any]:
    return load_config(getattr(args, "config", None) or CONFIG_PATH)


# --------------------------------------------------------------------------
# chains
# --------------------------------------------------------------------------


def cmd_chains(args) -> int:
    """Which chains are we targeting today, and are they actually reachable?"""
    from .chains import chain_health
    targets = [c.strip() for c in (args.chains or "").split(",") if c.strip()]
    if not targets:
        targets = _cfg(args)["chains"]["targets"]
    health = chain_health(targets)
    if args.json:
        _out(health, True)
        return 0
    print("CHAIN HEALTH — live, checked just now")
    print()
    for cid, h in (health.get("chains") or {}).items():
        spec = CHAINS.get(cid)
        flag = "OK " if h.get("reachable") else "DOWN"
        print(f"  [{flag}] {cid:<10} {spec.name if spec else '':<20} "
              f"rpc={h.get('rpc_status')}  data={h.get('data_status')}")
        if h.get("note"):
            print(f"        {h['note']}")
    gaps = health.get("gaps") or []
    if gaps:
        print("\n  SOURCE GAPS (availability problems, NOT 'no data exists'):")
        for g in gaps:
            print(f"    - {g.get('source')}: {g.get('reason')}")
    else:
        print("\n  no source gaps")
    return 0


# --------------------------------------------------------------------------
# profile
# --------------------------------------------------------------------------


def cmd_profile(args) -> int:
    """Profile one wallet against the operator's consistency thresholds."""
    from .profiler import profile_wallet
    cfg = _cfg(args)
    th = dict(cfg["thresholds"])
    if args.min_trades is not None:
        th["min_trades"] = args.min_trades
    if args.min_win_rate is not None:
        th["min_win_rate"] = args.min_win_rate
    if args.min_profit_factor is not None:
        th["min_profit_factor"] = args.min_profit_factor

    p = profile_wallet(args.chain, args.wallet, thresholds=th)
    d = p.to_flat()
    d.pop("trades", None)
    if args.json:
        _out(d, True)
        return 0
    print(f"WALLET PROFILE — {p.wallet} ({p.chain})")
    print(f"  provenance: {p.provenance}   source: {p.source or 'n/a'}")
    print(f"  trades={p.n_trades}  win_rate="
          f"{_num(p.win_rate)}  profit_factor={_num(p.profit_factor)}  "
          f"pnl=${_num(p.pnl_total_usd)}")
    print(f"  largest single trade share = {_num(p.largest_trade_pnl_share)} "
          f"(cap {th['max_single_trade_pnl_share']})")
    print()
    print(f"  THRESHOLDS (operator policy): trades>={th['min_trades']}, "
          f"win_rate>={th['min_win_rate']}, pf>={th['min_profit_factor']}, "
          f"single_trade_share<{th['max_single_trade_pnl_share']}")
    if p.disqualifiers:
        print("  DISQUALIFIED:")
        for r in p.disqualifiers:
            print(f"    - {r}")
    else:
        print("  QUALIFIES")
    if p.warnings:
        print("  WARNINGS:")
        for w in p.warnings:
            print(f"    - {w}")
    if p.notes:
        print(f"  note: {p.notes}")
    return 0


def _num(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


# --------------------------------------------------------------------------
# consensus
# --------------------------------------------------------------------------


def cmd_consensus(args) -> int:
    """Did >=N profiled wallets act on the same token inside the window?"""
    from .profiler import consensus_signal
    cfg = _cfg(args)
    c = cfg["consensus"]
    min_wallets = args.min_wallets if args.min_wallets is not None else c["min_wallets"]
    window = args.window if args.window is not None else c["window_seconds"]

    trades = []
    gaps = []
    for w in args.wallets:
        try:
            from .chains import fetch_wallet_trades
            trades.extend(fetch_wallet_trades(args.chain, w))
        except Exception as exc:  # noqa: BLE001
            gaps.append({"source": f"wallet_trades:{w}", "reason": str(exc)})

    pool = set(args.pool or [])
    summary = consensus_signal(trades, min_wallets=min_wallets,
                               window_seconds=window,
                               trusted_wallets=pool or None)
    if args.json:
        _out({"summary": summary, "gaps": gaps}, True)
        return 0
    print(f"CONSENSUS — need >={min_wallets} wallets within {window}s")
    rows = summary.get("tokens") if isinstance(summary, dict) else summary
    if not rows:
        print("  no trades found in the window")
    for r in rows or []:
        mark = "REACHED" if r.get("consensus") else "no"
        print(f"  [{mark}] {r.get('token')}  wallets={r.get('distinct_wallets')}  "
              f"{r.get('window_seconds')}s")
    for g in gaps:
        print(f"  GAP {g['source']}: {g['reason']}")
    return 0


# --------------------------------------------------------------------------
# pool — the trusted wallet pool
# --------------------------------------------------------------------------


def cmd_pool(args) -> int:
    """Inspect, add to, or re-evaluate the trusted wallet pool."""
    from .profiler import TrustedPool
    cfg = _cfg(args)
    pool = TrustedPool(cfg=cfg["pool"])
    pool.load()

    if args.add:
        pool.add(args.add, score=args.score, reason=args.reason or "operator add")
    if args.remove:
        pool.remove(args.remove, reason=args.reason or "operator remove")
    if args.reevaluate:
        pool.re_evaluate()
    if args.seed_deployers:
        from .deployers import registry_as_addresses, seed_registry
        reg = seed_registry([{"chain": c, "address": a}
                             for c, a in (t.split(":") for t in args.seed_deployers)])
        print(f"  derived {len(reg.get('deployers') or {})} deployer(s) "
              f"from on-chain data")
    if args.add or args.remove or args.reevaluate or args.seed_deployers:
        pool.save()

    if args.json:
        _out(pool.to_flat(), True)
        return 0
    print(f"TRUSTED WALLET POOL — {len(pool.wallets)} wallet(s)")
    for w, rec in sorted(pool.wallets.items(),
                         key=lambda kv: -(kv[1].get("score") or 0)):
        print(f"  {w:<46} score={rec.get('score')}  "
              f"added={rec.get('added_at')}  {rec.get('reason', '')}")

    # The DEPLOYER registry is derived from on-chain data; show what it holds.
    try:
        from .deployers import load_registry
        reg = load_registry()
        derived = reg.get("deployers") or {}
        print()
        print(f"  DERIVED DEPLOYER REGISTRY — {len(derived)} address(es)")
        for key, ev in list(derived.items())[:10]:
            print(f"    {key:<50} token={str(ev.get('token'))[:18]} "
                  f"method={ev.get('method')}")
        if derived:
            print("    (derived on-chain - see leapspace/state/deployer_registry.json "
                  "for the evidence)")
    except Exception as exc:  # noqa: BLE001
        print(f"  deployer registry unavailable: {exc}")

    reg = cfg["registries"]
    empty = [k for k in ("cabals", "exchanges", "insiders")
             if not reg.get(k)]
    if empty:
        print()
        print(f"  REGISTRIES EMPTY: {', '.join(empty)}")
        print("  The anti-insider filter CANNOT exclude anyone on these grounds")
        print("  until they are populated. 'unknown' funding source is not a")
        print("  clean bill of health.")
    if pool.log:
        print(f"\n  pool log: {len(pool.log)} entr(ies)")
        for e in pool.log[-6:]:
            print(f"    {e}")
    return 0


# --------------------------------------------------------------------------
# simulate — the friction-aware copy-trading backtest
# --------------------------------------------------------------------------


#: Keys whose name in the operator config differs from the dataclass
#: field name. Mapping them explicitly is better than dropping them.
CONFIG_KEY_ALIASES = {
    "copy_trade": {"position_pct": "size_pct",
                   "max_concurrent_positions": "max_open_positions",
                   "note": "notes"},
    "friction": {"note": "notes"},
    "rug": {"note": "notes"},
    "mev": {"note": "notes"},
}


def _build_config(section: str, obj: Dict[str, Any], cls, label: str):
    """Build a dataclass from a config block, keeping only the declared
    fields - and saying LOUDLY what was dropped.

    A config key that does not match a field used to be either a
    TypeError (crash) or silently filtered away, which meant the
    operator's own risk limits could be discarded without a word.
    """
    aliases = CONFIG_KEY_ALIASES.get(section, {})
    mapped: Dict[str, Any] = {}
    renamed: List[str] = []
    for key, value in (obj or {}).items():
        target = aliases.get(key, key)
        if target != key:
            renamed.append(f"{key}->{target}")
        if target in cls.__dataclass_fields__:
            mapped[target] = value
    # A key that was RENAMED is not dropped. A key starting with "_"
    # is metadata, not a setting.
    dropped = sorted(k for k in (obj or {})
                     if not k.startswith("_")
                     and k not in aliases
                     and k not in cls.__dataclass_fields__)
    if renamed:
        print(f"  [{label}] renamed: {', '.join(renamed)}")
    if dropped:
        print(f"  [{label}] WARNING: {len(dropped)} config key(s) match no "
              f"field and were DROPPED: {', '.join(dropped)}")
        print(f"  [{label}] the settings they carried are NOT in effect.")
    return cls(**mapped)

def cmd_simulate(args) -> int:
    """Run a friction-aware copy-trading simulation over a price series."""
    from .friction import (CopyConfig, FrictionModel, MEVConfig, RugConfig,
                           run_simulation)
    from .models import Friction
    cfg = _cfg(args)
    fr = dict(cfg["friction"])
    if args.slippage_bps is not None:
        fr["slippage_bps"] = args.slippage_bps
    if args.failed_tx_rate is not None:
        fr["failed_tx_rate"] = args.failed_tx_rate
    if args.mev_penalty_bps is not None:
        fr["mev_penalty_bps"] = args.mev_penalty_bps
    ct = dict(cfg["copy_trade"])
    if args.bankroll is not None:
        ct["start_usd"] = args.bankroll
    seed = args.seed if args.seed is not None else int(ct.get("seed", 42))

    prices = _load_price_series(args.prices)
    if not prices:
        print("no price series available; pass --prices <json file> with "
              "[[ts, px], ...] rows")
        return 2

    signals = _load_signals(args.signals)
    if signals is None:
        print("no signals available; pass --signals <json file> with "
              "[{wallet, chain, token, side, amount, price_usd, ts}, ...] rows")
        return 2

    # RugConfig expresses drops in PERCENT; the operator config uses a
    # fraction. Convert explicitly rather than silently mis-scaling.
    rug_cfg = dict(cfg["rug"])
    for key in ("min_drop_pct", "max_drop_pct"):
        v = float(rug_cfg.get(key, 0.8))
        rug_cfg[key] = v * 100.0 if v <= 1.0 else v
    rug_cfg["seed"] = seed

    friction = _build_config("friction", fr, Friction, "friction")
    rug = _build_config("rug", rug_cfg, RugConfig, "rug")
    mev = MEVConfig(max_penalty_bps=float(fr.get("mev_penalty_bps", 0.0)),
                    sandwich_probability=0.35, seed=seed)
    copy_cfg = _build_config("copy_trade", ct, CopyConfig, "copy_trade")

    res = run_simulation(signals, prices, friction=friction,
                          bankroll=float(ct.get("start_usd", 1000.0)),
                          rug_config=rug, mev_config=mev, seed=seed,
                          config=copy_cfg,
                          price_provenance="LIVE" if args.price_provenance
                          else "SYNTHETIC",
                          signal_provenance="LIVE" if args.signal_provenance
                          else "SYNTHETIC")
    if args.json:
        _out(res.to_flat(), True)
        return 0
    stats = res.stats or {}
    print("COPY-TRADE SIMULATION (friction-aware)")
    print(f"  provenance: prices={res.price_provenance} "
          f"signals={res.signal_provenance}")
    print(f"  friction: slippage={fr['slippage_bps']}bps  "
          f"failed_tx={fr['failed_tx_rate']}  latency={fr['latency_seconds']}s  "
          f"mev_max={fr['mev_penalty_bps']}bps")
    print(f"  trades={stats.get('n_trades')}  skipped={stats.get('n_skipped')}  "
          f"win_rate={_num(stats.get('win_rate'))}  "
          f"profit_factor={_num(stats.get('profit_factor'))}")
    print(f"  return={_num(stats.get('total_return'))}  "
          f"max_dd={_num(stats.get('max_drawdown'))}")
    rugs = res.rugs or []
    if rugs:
        print(f"\n  INJECTED RUG EVENTS ({len(rugs)}) — SYNTHETIC by construction:")
        for r in rugs[:10]:
            _rf = r.to_flat() if hasattr(r, "to_flat") else dict(r)
            print(f"    ts={_rf.get('ts')} {_rf.get('token', '')} "
                  f"{_num(r.get('drop_pct'))} drop")
    skipped = [c for c in (res.trades or []) if c.get("skipped")]
    if skipped:
        print(f"\n  SKIPPED TRADES ({len(skipped)}) — recorded, never dropped:")
        for c in skipped[:10]:
            print(f"    {c.get('token')} {c.get('action')}: {c.get('skip_reason')}")
    if res.disclosure:
        print(f"\n  {res.disclosure}")
    return 0


def _load_price_series(path: str):
    if not path:
        return []
    with open(path, "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    out = []
    for r in rows:
        if isinstance(r, (list, tuple)) and len(r) >= 2:
            out.append((int(r[0]), float(r[1])))
        elif isinstance(r, dict):
            out.append((int(r.get("ts", 0)), float(r.get("px", r.get("price", 0)))))
    return out


def _load_signals(path: str):
    """Load the signal file and convert each row to a WalletTrade.

    The rows arrive as plain JSON dicts, but the simulator sorts and
    reads them as OBJECTS (`s.ts`, `s.wallet`, `s.token`). Passing the
    dicts straight through crashed the simulator with
    `AttributeError: 'dict' object has no attribute 'ts'`, so the
    conversion belongs here rather than in the simulator.
    """
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    from .friction import WalletTrade
    fields = {f.name for f in __import__("dataclasses").fields(WalletTrade)}
    out = []
    for row in rows or []:
        if isinstance(row, WalletTrade):
            out.append(row)
            continue
        if not isinstance(row, dict):
            continue
        kw = {k: v for k, v in row.items() if k in fields}
        kw.setdefault("symbol", "")
        kw.setdefault("value_usd", (float(row.get("amount") or 0.0)
                                    * float(row.get("price_usd") or 0.0)))
        kw.setdefault("provenance", "SYNTHETIC")
        kw.setdefault("source", "signal_file")
        try:
            out.append(WalletTrade(**kw))
        except TypeError:
            out.append(WalletTrade(wallet=str(row.get("wallet") or ""),
                                   chain=str(row.get("chain") or ""),
                                   token=str(row.get("token") or ""),
                                   symbol=str(row.get("symbol") or ""),
                                   side=str(row.get("side") or "buy"),
                                   amount=float(row.get("amount") or 0.0),
                                   price_usd=float(row.get("price_usd") or 0.0),
                                   value_usd=float(row.get("value_usd") or 0.0),
                                   ts=int(row.get("ts") or 0)))
    return out


# --------------------------------------------------------------------------
# risk — kill switch + anomaly log
# --------------------------------------------------------------------------


def cmd_risk(args) -> int:
    """Inspect or reset the code-enforced kill switch."""
    from .riskguard import KillSwitch
    cfg = _cfg(args)
    ks = KillSwitch(cfg=cfg["kill_switch"])
    ks.load()
    if args.reset:
        ks.reset(by="operator", reason=args.reset)
        ks.save()
    state = ks.to_flat()
    if args.json:
        _out(state, True)
        return 0
    print("KILL SWITCH — code-enforced")
    print(f"  halted: {state.get('halted')}")
    if state.get("halted"):
        print(f"  reason: {state.get('reason')}")
        print(f"  trigger: {state.get('trigger')}")
        print(f"  drawdown: {_num(state.get('drawdown_pct'))}")
        print("  Trading is BLOCKED. Only an explicit reset with an actor and a")
        print("  reason clears this - no prompt, no LLM, no flag.")
    else:
        print("  trading permitted (subject to the per-check rules)")
    try:
        bypass = ks.verify_no_bypass()
        print(f"  bypass audit: {bypass}")
    except Exception as exc:  # noqa: BLE001
        print(f"  bypass audit unavailable: {exc}")
    log = state.get("state_log") or ""
    if log:
        print("\n  state log:")
        for e in str(log).split(" | ")[-8:]:
            print(f"    {e}")
    return 0


def cmd_anomaly(args) -> int:
    """Show the anomaly log and the promoted Known Unknowns."""
    from .riskguard import AnomalyLog
    log = AnomalyLog()
    log.load()
    if args.json:
        _out(log.to_flat(), True)
        return 0
    print(f"ANOMALY LOG — {len(log.anomalies)} entr(ies), "
          f"{len(log.known_unknowns)} promoted to Known Unknown")
    for a in log.anomalies[-10:]:
        print(f"  [{a.severity:<8}] {a.kind:<22} {a.description}")
    if log.known_unknowns:
        print("\n  KNOWN UNKNOWNS (replayable conditions):")
        for k in log.known_unknowns:
            print(f"    {k.get('kind')}: {k.get('lesson')}")
    return 0


# --------------------------------------------------------------------------
# audit — the bias auditor
# --------------------------------------------------------------------------


def cmd_audit(args) -> int:
    """Audit the specs and the stored backtest results for hidden bias."""
    from .biasaudit import audit_backtest_results, audit_spec, audit_report
    findings = []
    if args.spec:
        from .backtest import all_specs
        for s in all_specs():
            if args.spec in s.get("name", ""):
                findings.extend(audit_spec(s))
    else:
        from .backtest import all_specs
        for s in all_specs():
            findings.extend(audit_spec(s))
    if args.results:
        with open(args.results, "r", encoding="utf-8") as fh:
            findings.extend(audit_backtest_results(json.load(fh)))
    if args.json:
        _out({"findings": [f.to_flat() for f in findings]}, True)
        return 0
    print(audit_report(findings))
    return 0


def cmd_viz(args) -> int:
    """Build the visual report: PNG charts + an HTML dashboard."""
    from .viz import build_dashboard
    out = build_dashboard(live=not args.no_live,
                          results_path=args.results)
    if args.json:
        _out(out, True)
        return 0
    print("VISUAL REPORT")
    print(f"  html   : {out['html']}")
    print(f"  charts : {out['n_charts']}")
    for c in out["charts"]:
        print(f"    - {c['title']:<22} {c['file']}")
    print(f"  specs  : {out['n_specs']}")
    print(f"  matplotlib: {out['matplotlib']}")
    return 0


def cmd_narrative(args) -> int:
    """Narrative specificity: classify a token, or run the forward test.

    The paper's clause asserts a PERFORMANCE relationship - niche tokens
    outperform broader-trend tokens. A filter that asserts that should be
    held to it, so this command can measure it FORWARD once two
    snapshots separated in time exist.
    """
    from .narrative import (classify_specificity, cohort_baseline,
                            relative_to_cohort, verify_cohort)

    if args.mint:
        from .memecoin import fetch_token_profile
        from .market import fetch_dex_pairs, normalise_dex_pair
        prof, _ = fetch_token_profile(args.mint)
        pairs, _ = fetch_dex_pairs(args.mint, limit=30)
        norm = [normalise_dex_pair(p) for p in pairs]
        pair = max(norm, key=lambda n: (n.get("liquidity_usd") or 0.0)) if norm else {}
        spec = classify_specificity(prof, pair)
        if args.json:
            _out(spec, True)
            return 0
        print(f"NARRATIVE SPECIFICITY - {prof.get('symbol')} ({args.mint})")
        print(f"  score: {spec['specificity_score']}  niche: {spec['is_niche']}  "
              f"threshold: {spec['niche_threshold']}")
        print(f"  community footprint: {spec['has_community_footprint']}")
        print("  signals:")
        for k, v in spec["signals"].items():
            print(f"    {k:<26} {v}  (weight {spec['weights'][k]:+.1f})")
        print("  reasons:")
        for r in spec["reasons"]:
            print(f"    - {r}")
        print(f"  social platforms: {spec['social_platforms']}")
        print(f"\n  {spec['disclosure']}")
        return 0

    # Forward test: re-price the saved cohort and compare.
    from .narrative import COHORT_PATH, select_base_rows
    from .provenance import read_json
    from .chains import dexscreener_pairs
    from .market import normalise_dex_pair
    blob = read_json(COHORT_PATH) or {"snapshots": []}
    snaps = blob.get("snapshots") or []
    if not snaps:
        print("no cohort snapshot saved yet - run `memes --query <q> --limit N` "
              "first to save one")
        return 2
    # Base selection uses the SAME rule as verify_cohort. Doing it here
    # with a first-row-wins dedup silently dropped every token first seen
    # before the pool-address fix - which in the observed history was every
    # NICHE token, emptying the niche bucket and making the forward test
    # uninterpretable. One shared rule, so the pool priced here is always
    # the pool the forward test compares against.
    base_rows, _no_pair = select_base_rows(snaps, min_gap_seconds=3600)
    current = []
    for mint, base in base_rows.items():
        try:
            pairs = dexscreener_pairs("solana", mint)
        except Exception:  # noqa: BLE001
            continue
        norm = [normalise_dex_pair(p) for p in pairs]
        if not norm:
            continue
        # Price the SAME POOL the snapshot used. Picking "the pair with
        # the most liquidity now" compares two different pools and
        # manufactures returns.
        want = (base.get("pair_address") or "").lower()
        same = [n for n in norm
                if want and (n.get("pair") or "").lower() == want]
        if not (want and same):
            continue  # the snapshot's pool is gone
        best = same[0]
        current.append({
            "mint": mint, "symbol": base.get("symbol"),
            "is_niche": base.get("is_niche"),
            "specificity_score": base.get("specificity_score"),
            "price_usd": best.get("price_usd"),
            "price_change_24h": best.get("price_change_24h"),
            "liquidity_usd": best.get("liquidity_usd"),
            "pair_address": best.get("pair"),
            "dex": best.get("dex"),
        })
    verdict = verify_cohort(current_rows=current)
    if args.json:
        _out({"verdict": verdict, "n_current": len(current)}, True)
        return 0
    print("NARRATIVE FORWARD TEST")
    print(f"  current tokens priced: {len(current)}")
    for k, v in verdict.items():
        if k == "note":
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")
    return 0


# --------------------------------------------------------------------------
# parser
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# landscape - the multi-chain registry, ranked, with L1/L2 kept separate
# --------------------------------------------------------------------------


def cmd_landscape(args) -> int:
    """The memecoin chain registry: ranked, layered, and honest about gaps."""
    from .chainregistry import (chain_health, chains, discover_memecoins,
                                layer_split, top_chains)
    if getattr(args, "discover", None):
        res = discover_memecoins(args.discover, limit=args.limit or 20,
                                 pages=args.pages or 2)
        if args.json:
            _out(res, True)
            return 0
        print(f"MEMECOIN CANDIDATES — {res.get('chain')} "
              f"({res.get('layer')}, token network: {res.get('token_network')})")
        print(f"  status: {res.get('status')}   "
              f"pools examined: {res.get('pools_examined')}")
        if res.get("layer_note"):
            print(f"  {res['layer_note']}")
        for g in res.get("gaps") or []:
            print(f"  GAP [{g.get('source')}]: {g.get('reason')}")
        print()
        for c in res.get("candidates") or []:
            print(f"  {c.get('symbol',''):<12} {c.get('token_address','')[:16]:<18} "
                  f"vol24=${(c.get('volume_24h_usd') or 0):,.0f} "
                  f"liq=${(c.get('liquidity_usd') or 0):,.0f} "
                  f"chg24h={(c.get('price_change_24h') or 0):+.1f}%")
        print(f"\n  prefilter: {res.get('prefilter')}")
        return 0

    top = top_chains(args.limit or 10)
    split = layer_split()
    health = chain_health()
    if args.json:
        _out({"top_chains": top, "layer_split":
              {k: [c["chain_id"] for c in v] for k, v in split.items()},
              "health": health}, True)
        return 0

    print("MEMECOIN CHAIN REGISTRY — ranked by measured 24h DEX volume")
    print("  TWO VOLUME MEASURES, never mixed:")
    print("    [M] DefiLlama per-chain DEX total24h - a COMPLETE measurement.")
    print("    [S] GeckoTerminal per-pool h24 sum over the sampled pools - a")
    print("        LOWER BOUND (the free API rate-limits and pages), never a")
    print("        chain total. A chain with no figure was not measured, not")
    print("        empty.")
    print()
    print(f"  {'#':>3}  {'chain':<24} {'layer':<15} {'token network':<14} "
          f"{'24h DEX volume':>18}  src")
    for c in top:
        vol = c.get("dex_volume_24h_usd")
        vs = (f"${vol:,.0f}" if vol is not None else "not measured")
        src = "M" if "llama" in str(c.get("dex_volume_source")) else "S"
        print(f"  {c.get('rank','') or '-':>3}  {c.get('name',''):<24} "
              f"{c.get('layer',''):<15} {c.get('token_network',''):<14} "
              f"{vs:>18}  {src}")
    print()
    print("  LAYER SPLIT — L1 and L2 token networks are NEVER merged:")
    for layer in ("L1", "L2", "APPCHAIN"):
        ids = [c["chain_id"] for c in split.get(layer, [])]
        if ids:
            print(f"    {layer:<9} {', '.join(ids)}")
    print()
    print("  CAPABILITY MATRIX:")
    print(f"    RPC working        : {', '.join(health.get('rpc_working') or []) or '-'}")
    print(f"    DexScreener working: {', '.join(health.get('dexscreener_working') or []) or '-'}")
    print(f"    RugCheck (Solana)  : {', '.join(health.get('rugcheck_solana_only') or []) or '-'}")
    print(f"    Jupiter  (Solana)  : {', '.join(health.get('jupiter_solana_only') or []) or '-'}")
    if health.get("rpc_failing"):
        print("    RPC failing        :")
        for f in health["rpc_failing"]:
            print(f"        {f['chain_id']:<12} status={f['status']} "
                  f"{f.get('note','')}")
    if health.get("rpc_unprobed"):
        print(f"    RPC unprobed       : {', '.join(health['rpc_unprobed'])}")
        for c in chains():
            if (c.get("chain_id") in health["rpc_unprobed"]
                    and c.get("rpc_note")):
                print(f"        {c['chain_id']}: {c['rpc_note']}")
    print(f"\n    {health.get('note','')}")
    return 0


# --------------------------------------------------------------------------
# social - multi-platform narrative + traction for one token
# --------------------------------------------------------------------------


def cmd_social(args) -> int:
    """Narrative specificity and traction for one token on one chain."""
    from .social import (fetch_social_profile, score_narrative,
                         score_traction)
    from .narrative import _name_specificity
    chain = args.chain or "solana"
    token = args.token
    fam_svm = chain == "solana"
    prof = fetch_social_profile(chain, token, jupiter=fam_svm,
                                 rugcheck=fam_svm)
    nar = score_narrative(prof, _name_specificity(args.symbol or "",
                                                  args.symbol or ""))
    tr = score_traction(prof)
    if args.json:
        _out({"profile": prof, "narrative": nar, "traction": tr}, True)
        return 0
    n = prof.get("narrative") or {}
    pc = prof.get("platform_classes") or {}
    o = tr.get("observed") or {}
    print(f"SOCIAL + TRACTION — {chain} / {args.symbol or token}")
    print()
    print("  PLATFORMS (all free sources):")
    print(f"    all        : {prof.get('platforms')}")
    print(f"    community  : {pc.get('community')}   (membership)")
    print(f"    broadcast  : {pc.get('broadcast')}   (reach)")
    print(f"    site       : {pc.get('site')}")
    print()
    print("  NARRATIVE:")
    print(f"    score {nar.get('narrative_score')}  niche={nar.get('is_niche')}  "
          f"(threshold {nar.get('threshold')}, {nar.get('threshold_label')})")
    for r in nar.get("reasons") or []:
        print(f"      - {r}")
    if n.get("has_description"):
        print(f"    description: {n.get('description_chars')} chars  "
              f"community_framed={n.get('community_framed')}  "
              f"generic={n.get('generic_framed')}")
        print(f"      community markers: {n.get('community_markers')}")
        print(f"      generic markers : {n.get('generic_markers')}")
        print(f"      named entities  : {n.get('named_entities')}")
    else:
        print("    description: not available for this token "
              "(DexScreener's description lists hold 30 tokens each)")
    print()
    print("  COMMUNITY SIZE (free, no API key):")
    cs = prof.get("community_size") or {}
    print(f"    telegram members : {cs.get('telegram_members')}   "
          f"online: {cs.get('telegram_online')}")
    print(f"    discord  members : {cs.get('discord_members')}   "
          f"online: {cs.get('discord_online')}"
          f"   guild: {cs.get('discord_guild_name')}")
    print(f"    combined         : {cs.get('combined_members')}   "
          f"measured on {cs.get('measured_platforms')} platform(s)")
    for e in cs.get("errors") or []:
        print(f"    unmeasured: {e['platform']} -> {e['status']}")
    print()
    print("  TRACTION:")
    print(f"    score {tr.get('traction_score')}")
    for k, v in (o or {}).items():
        print(f"      {k:<28} {v}")
    print(f"    confidence: {tr.get('confidence')}")
    if prof.get("gaps"):
        print("\n  SOURCE GAPS:")
        for g in prof["gaps"]:
            print(f"    - [{g.get('source')}] {g.get('reason')}")
    return 0


# --------------------------------------------------------------------------
# socialedge - did a wallet buy BEFORE the social traction spike?
#
# This is the TIMING edge, and it is complementary to `cmd_edge` (which is
# the STATISTICAL edge: fluke tests, Bayesian skill, deflated Sharpe). A
# wallet can be statistically consistent and still have bought after every
# narrative spike, or vice versa.
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# socialedge / pnl / link - the social, priced and cross-chain edges
# --------------------------------------------------------------------------


def cmd_socialedge(args) -> int:
    """The social-edge test: did a wallet buy BEFORE the traction spike?

    A wallet that bought early is not evidence of an edge on its own.
    It is evidence only if the early buy PRECEDED the social comparators
    (the membership crossing, the holder inflection, the first major
    mention). This command computes that lead time, and the CONVERSE
    test: wallets that bought after the narrative was established are
    crowd-following, not leading, and are reported separately.
    """
    from .socialedge import (assess_wallet_edge, build_activity_series,
                             classify_late_buyers, community_series_diagnostics,
                             load_community_series, record_community_snapshot,
                             sample_community_size, telegram_post_activity)

    chain = args.chain or "solana"
    token = args.token

    # ---- --sample: record one live community-size snapshot --------------
    if args.sample:
        from .social import fetch_social_profile
        prof = fetch_social_profile(chain, token)
        links = prof.get("social_links") or prof.get("socials") or {}
        links = {k: v for k, v in links.items()
                 if isinstance(v, str) and v.startswith("http")}
        size = sample_community_size(links) if links else {
            "status": "no_social_links",
            "note": ("the token record carries no Telegram or Discord link, "
                     "so there is no community to measure")}
        print(f"SAMPLE — {token} ({chain})")
        for k, v in size.items():
            if isinstance(v, (dict, list)):
                v = str(v)[:200]
            print(f"  {k}: {v}")
        if size.get("status") == "ok":
            rec = record_community_snapshot(
                chain, token,
                telegram_members=size.get("telegram_members"),
                discord_members=size.get("discord_members"),
                telegram_online=size.get("telegram_online"),
                discord_online=size.get("discord_online"),
                source="leapspace.cli socialedge --sample")
            print(f"\n  recorded snapshot -> {rec.get('path')}")
        else:
            print("\n  NOT recorded. An unmeasured platform is reported as "
                  "unmeasured, never as zero.")
        return 0

    # ---- --activity: the live Telegram post-activity series -------------
    if args.activity:
        from .social import fetch_social_profile
        prof = fetch_social_profile(chain, token)
        links = prof.get("social_links") or prof.get("socials") or {}
        tg = links.get("telegram") if isinstance(links, dict) else None
        if not tg:
            print(f"ACTIVITY — {token}: no Telegram link in the token record")
            return 2
        act = telegram_post_activity(tg)
        print(f"ACTIVITY — {token} ({chain})")
        print(f"  status: {act.get('status')}")
        if act.get("status") == "ok":
            stamps = act.get("post_timestamps") or []
            print(f"  posts retrieved: {len(stamps)}")
            series = build_activity_series(stamps, args.bucket or 3600)
            print(f"  bucketed series ({args.bucket or 3600}s): "
                  f"{len(series)} buckets")
            for b in series[-12:]:
                print(f"    {b}")
            print("\n  This measures ACTIVITY, not community SIZE. It is "
                  "retrievable today in one call; a member-count history "
                  "is not.")
        else:
            print(f"  note: {str(act.get('note') or act.get('reason'))[:200]}")
        return 0

    # ---- the main assessment -------------------------------------------
    series = load_community_series(chain, token)
    snaps = series.get("snapshots") or []
    if not snaps:
        print(f"SOCIAL EDGE — {token} ({chain})")
        print("  no community-size series stored for this token.")
        print("  Record one with:  socialedge --token <mint> --sample")
        print("  A quiet channel and an unmeasured channel are different "
              "things; neither is a zero.")
        return 2

    print(f"SOCIAL EDGE — {args.symbol or token} ({chain})")
    diag = community_series_diagnostics(snaps)
    print(f"  community snapshots: {len(snaps)}   "
          f"platforms measured: {diag.get('n_platforms_measured')}   "
          f"lower bound: {diag.get('combined_is_lower_bound')}")
    if diag.get("first_ts") and diag.get("last_ts"):
        print(f"  window: {diag.get('first_ts')} -> {diag.get('last_ts')}")

    buys = []
    if args.buys:
        import json as _json
        with open(args.buys, "r", encoding="utf-8") as fh:
            buys = _json.load(fh)
    else:
        print("  no --buys file supplied: reporting the comparators only")
        print("  (a lead time needs the wallet's buy timestamps)")
        return 0

    holder_series = None
    if args.holders:
        from .holders import load_holder_series
        hs = load_holder_series(chain, token)
        holder_series = hs.get("snapshots") or None
        print(f"  holder series: {len(holder_series or [])} snapshot(s)")

    mention_series = None
    if args.mentions:
        import json as _json
        with open(args.mentions, "r", encoding="utf-8") as fh:
            mention_series = _json.load(fh)
        print(f"  mention series: {len(mention_series)} observation(s)")

    res = assess_wallet_edge(
        buys, snaps, token_address=token, symbol=args.symbol,
        holder_series=holder_series, mention_series=mention_series,
        membership_threshold=args.threshold or 500,
        coincident_window_hours=args.window or 6.0)

    print()
    edge = res.get("edge") or res
    for k in ("overall_class", "lead_time_hours", "lead_time_mean_hours",
              "n_comparators_resolved", "n_comparators_possible",
              "comparator_coverage", "entry_ts"):
        if k in edge:
            print(f"  {k}: {edge[k]}")
    for name, cmp_ in (edge.get("per_comparator") or {}).items():
        if isinstance(cmp_, dict):
            print(f"    {name}: class={cmp_.get('class')} "
                  f"lead_h={cmp_.get('lead_time_hours')} "
                  f"event_ts={cmp_.get('event_ts')}")
        else:
            print(f"    {name}: {str(cmp_)[:160]}")

    late = classify_late_buyers(
        buys, snaps, token_address=token, symbol=args.symbol,
        established_threshold=args.established or 1000)
    print()
    print(f"  CONVERSE TEST — wallets that bought AFTER the narrative was "
          f"established")
    for k in ("n_buys_for_token", "n_late_buys", "late_buys",
              "established_ts", "classification"):
        if k in late:
            v = late[k]
            if isinstance(v, (dict, list)):
                v = str(v)[:200]
            print(f"    {k}: {v}")

    if args.json:
        _out({"assessment": res, "late_buyers": late,
              "diagnostics": diag}, True)
    return 0


def cmd_pnl(args) -> int:
    """A wallet's real cost basis, priced at each trade's own block."""
    from .memecoinscan import memecoin_universe, wallet_memecoin_profile
    from .priced import price_wallet_positions, realised_pnl_and_edge

    chain = args.chain or "ethereum"
    uni = memecoin_universe()
    prof = wallet_memecoin_profile(args.wallet, uni, chain=chain,
                                   max_items=args.max_items)
    if prof.get("status") != "ok":
        print(f"PNL — {args.wallet}")
        print(f"  scan: {prof.get('status')}  {prof.get('reason')}")
        return 2
    priced = price_wallet_positions(prof, chain=chain, method=args.method)
    res = realised_pnl_and_edge(priced, trials_scanned=args.trials or 1)
    e = res["edge"]
    pnl = res["pnl"]
    print(f"PNL — {args.wallet} ({chain})")
    print(f"  pricing method : {priced.get('method')}  "
          f"(pool = the DEX's own reserves at the trade's block)")
    print(f"  trades priced  : {res['n_trades_priced']}   "
          f"unpriced: {res['n_unpriced']}")
    if priced.get("unpriced_reasons"):
        for k, v in list(priced["unpriced_reasons"].items())[:5]:
            print(f"      {k}: {v}")
    print(f"  closed trades  : {res['n_closed_trades']}")
    print(f"  realised PnL   : ${(pnl.get('realised_pnl_usd') or 0):,.0f}  "
          f"(GROSS of gas, DEX fees and MEV)")
    print(f"  total cost     : ${(pnl.get('total_cost_usd') or 0):,.0f}   "
          f"proceeds: ${(pnl.get('total_proceeds_usd') or 0):,.0f}")
    print(f"  win rate       : {e.get('win_rate')}   "
          f"skill p={e.get('bayesian_skill_p')}")
    print(f"  independent bets: "
          f"{(e.get('independent_bets') or {}).get('independent_bets')}")
    print(f"  VERDICT        : {e.get('verdict')}")
    print(f"     {e.get('reason')}")
    if args.json:
        _out({"priced": {k: v for k, v in priced.items() if k != "trades"},
              "pnl": pnl, "edge": e}, True)
    return 0


def cmd_link(args) -> int:
    """Cross-chain identity: score every pair of wallets, with evidence."""
    from .crosschain import build_wallet_profile, link_wallets

    wallets = [w.strip() for w in (args.wallets or "").split(",")
               if w.strip()]
    if len(wallets) < 2:
        print("link — pass --wallets ADDR1,ADDR2[,ADDR3]")
        print("        (chain:ADDR form is accepted, e.g. "
              "ethereum:0xabc,base:0xdef)")
        return 2
    profiles = []
    for w in wallets:
        if ":" in w and not w.startswith("0x"):
            chain, addr = w.split(":", 1)
        else:
            chain, addr = (args.chain or "ethereum"), w
        profiles.append(build_wallet_profile(
            addr, chain=chain, with_bridge_scan=not args.no_bridge))
    res = link_wallets(profiles)
    if args.json:
        _out(res, True)
        return 0
    print("CROSS-CHAIN LINK SCORES")
    print()
    cands = (res.get("candidates") or res.get("pairs")
             or res.get("links") or [])
    if not cands:
        print(f"  {str(res)[:600]}")
        return 0
    for c in cands[:12]:
        print(f"  {str(c.get('wallet_a'))[:24]:<26} <-> "
              f"{str(c.get('wallet_b'))[:24]:<26} score={c.get('score')} "
              f"label={c.get('label')}")
        for comp in (c.get("components") or [])[:4]:
            print(f"       {comp.get('signal')}: score={comp.get('score')} "
                  f"weight={comp.get('weight')} "
                  f"{str(comp.get('value') or comp.get('detail'))[:70]}")
    print()
    print(f"  {res.get('note') or res.get('caveat') or ''}")
    return 0


# The command bodies for holders / memeflow / traders / edge / whitelist /
# launchscan live in cmd_extra.py. Importing them here keeps the parser
# table and the implementations in separate, testable places.
from .cmd_extra import (cmd_edge, cmd_etherscan, cmd_holders,  # noqa: E402
                        cmd_launchscan, cmd_memeflow, cmd_traders,
                        cmd_vizmem, cmd_whitelist)


def add_parsers(sub) -> None:
    """Register the quant subcommands on an existing subparser action."""
    def common(p):
        p.add_argument("--json", action="store_true", help="emit flat JSON")
        p.add_argument("--config", default=None, help="operator config path")
        return p

    sp = sub.add_parser("chains", help="chain health and reachability")
    sp.add_argument("--chains", default=None,
                    help="comma-separated chain ids (default: config targets)")
    common(sp)
    sp.set_defaults(func=cmd_chains)

    sp = sub.add_parser("profile", help="profile a wallet against the thresholds")
    sp.add_argument("--chain", required=True)
    sp.add_argument("--wallet", required=True)
    sp.add_argument("--min-trades", type=int, default=None)
    sp.add_argument("--min-win-rate", type=float, default=None)
    sp.add_argument("--min-profit-factor", type=float, default=None)
    common(sp)
    sp.set_defaults(func=cmd_profile)

    sp = sub.add_parser("consensus", help="N profiled wallets on one token")
    sp.add_argument("--chain", required=True)
    sp.add_argument("--wallets", nargs="+", required=True)
    sp.add_argument("--pool", nargs="*", default=None)
    sp.add_argument("--min-wallets", type=int, default=None)
    sp.add_argument("--window", type=int, default=None)
    common(sp)
    sp.set_defaults(func=cmd_consensus)

    sp = sub.add_parser("pool", help="trusted wallet pool")
    sp.add_argument("--add", default=None)
    sp.add_argument("--remove", default=None)
    sp.add_argument("--score", type=float, default=None)
    sp.add_argument("--reason", default=None)
    sp.add_argument("--reevaluate", action="store_true")
    sp.add_argument("--seed-deployers", nargs="*", default=None,
                    metavar="CHAIN:ADDRESS",
                    help="derive deployers from on-chain data for these "
                         "tokens and seed the registry from them")
    common(sp)
    sp.set_defaults(func=cmd_pool)

    sp = sub.add_parser("simulate", help="friction-aware copy-trading sim")
    sp.add_argument("--prices", default=None, help="JSON [[ts, px], ...]")
    sp.add_argument("--signals", default=None, help="JSON list of trade signals")
    sp.add_argument("--bankroll", type=float, default=None)
    sp.add_argument("--slippage-bps", type=float, default=None)
    sp.add_argument("--failed-tx-rate", type=float, default=None)
    sp.add_argument("--mev-penalty-bps", type=float, default=None)
    sp.add_argument("--seed", type=int, default=None)
    sp.add_argument("--price-provenance", action="store_true",
                    help="declare the price series LIVE (it came from a real "
                         "source) rather than the default SYNTHETIC")
    sp.add_argument("--signal-provenance", action="store_true",
                    help="declare the signals LIVE rather than SYNTHETIC")
    common(sp)
    sp.set_defaults(func=cmd_simulate)

    sp = sub.add_parser("risk", help="kill switch state / reset")
    sp.add_argument("--reset", default=None, help="reason for an explicit reset")
    common(sp)
    sp.set_defaults(func=cmd_risk)

    sp = sub.add_parser("anomaly", help="anomaly log and known unknowns")
    common(sp)
    sp.set_defaults(func=cmd_anomaly)

    sp = sub.add_parser("audit", help="bias audit of specs and results")
    sp.add_argument("--spec", default=None, help="filter by spec name")
    sp.add_argument("--results", default=None, help="backtest results JSON")
    common(sp)
    sp.set_defaults(func=cmd_audit)

    sp = sub.add_parser("narrative", help="narrative specificity / forward test")
    sp.add_argument("--mint", default=None,
                    help="classify one token's narrative specificity")
    sp.add_argument("--verify", action="store_true",
                    help="run the forward test against the saved cohort")
    common(sp)
    sp.set_defaults(func=cmd_narrative)


    sp = sub.add_parser("viz", help="visual report: charts + HTML dashboard")
    sp.add_argument("--results", default=None,
                    help="backtest results JSON to chart")
    sp.add_argument("--no-live", action="store_true",
                    help="skip the live chain/token fetch")
    common(sp)
    sp.set_defaults(func=cmd_viz)

    sp = sub.add_parser("landscape",
                        help="memecoin chain registry: ranked, layered")
    sp.add_argument("--discover", default=None, metavar="CHAIN",
                    help="discover memecoin candidates on a chain")
    sp.add_argument("--limit", type=int, default=10)
    sp.add_argument("--pages", type=int, default=2)
    common(sp)
    sp.set_defaults(func=cmd_landscape)

    sp = sub.add_parser("social",
                        help="multi-platform narrative + traction for a token")
    sp.add_argument("--token", required=True, help="token address")
    sp.add_argument("--chain", default="solana")
    sp.add_argument("--symbol", default=None)
    common(sp)
    sp.set_defaults(func=cmd_social)

    sp = sub.add_parser("socialedge",
                        help="social-edge test: did a wallet buy BEFORE "
                             "the traction spike?")
    sp.add_argument("--token", required=True, help="token address")
    sp.add_argument("--chain", default="solana")
    sp.add_argument("--symbol", default=None)
    sp.add_argument("--buys", default=None,
                    help="JSON file: list of buy events "
                         "[{'ts','symbol','token_address'}]")
    sp.add_argument("--mentions", default=None,
                    help="JSON file: mention/attention series "
                         "[{'ts','mentions'}]")
    sp.add_argument("--holders", action="store_true",
                    help="use the stored holder-count series as a comparator")
    sp.add_argument("--sample", action="store_true",
                    help="record a live community-size snapshot and exit")
    sp.add_argument("--activity", action="store_true",
                    help="report the live Telegram post-activity series")
    sp.add_argument("--bucket", type=int, default=3600,
                    help="activity bucket size in seconds")
    sp.add_argument("--threshold", type=int, default=500,
                    help="membership threshold for the lead-time comparator")
    sp.add_argument("--established", type=int, default=1000,
                    help="member count at which the narrative counts as "
                         "established (the converse test)")
    sp.add_argument("--window", type=float, default=6.0,
                    help="coincident window in hours")
    common(sp)
    sp.set_defaults(func=cmd_socialedge)

    sp = sub.add_parser("traders",
                        help="wallet qualification vs cited standards")
    sp.add_argument("--wallet", default=None, help="wallet address")
    sp.add_argument("--chain", default="solana")
    sp.add_argument("--criteria", action="store_true",
                    help="print the criteria table with authorities")
    sp.add_argument("--pool", action="store_true",
                    help="print the qualified pool")
    sp.add_argument("--track", action="store_true",
                    help="poll the forward cohort for activity")
    sp.add_argument("--record", action="store_true",
                    help="record the verdict into the qualified pool")
    common(sp)
    sp.set_defaults(func=cmd_traders)

    sp = sub.add_parser("etherscan",
                        help="Etherscan V2: balances, holders, transfers")
    sp.add_argument("--token", required=True)
    sp.add_argument("--chain", default="ethereum")
    sp.add_argument("--holders", action="store_true",
                    help="net the holders from the transfer tape")
    sp.add_argument("--balances", default=None,
                    help="comma-separated addresses to batch-balance")
    sp.add_argument("--actions", action="store_true",
                    help="show which actions the free tier supports")
    common(sp)
    sp.set_defaults(func=cmd_etherscan)

    sp = sub.add_parser("vizmem",
                        help="build the memecoin charts")
    sp.add_argument("--root", default=None)
    sp.add_argument("--out", default=None)
    common(sp)
    sp.set_defaults(func=cmd_vizmem)

    sp = sub.add_parser("pnl",
                        help="a wallet's real cost basis, priced at each "
                             "trade's own block")
    sp.add_argument("--wallet", required=True)
    sp.add_argument("--chain", default="ethereum")
    sp.add_argument("--method", default="auto", choices=["auto", "pool",
                                                         "defillama"])
    sp.add_argument("--max-items", type=int, default=250)
    sp.add_argument("--trials", type=int, default=1)
    common(sp)
    sp.set_defaults(func=cmd_pnl)

    sp = sub.add_parser("link",
                        help="cross-chain wallet identity, with evidence")
    sp.add_argument("--wallets", required=True,
                    help="comma-separated; chain:ADDR form allowed")
    sp.add_argument("--chain", default="ethereum")
    sp.add_argument("--no-bridge", action="store_true")
    common(sp)
    sp.set_defaults(func=cmd_link)

    sp = sub.add_parser("launchscan",
                        help="early buyers of a NEW meme, edge-screened")
    sp.add_argument("--token", required=True, help="new memecoin contract")
    sp.add_argument("--chain", default="ethereum")
    sp.add_argument("--window", type=int, default=1000,
                    help="blocks after launch to consider 'early'")
    sp.add_argument("--pages", type=int, default=30)
    sp.add_argument("--candidates", type=int, default=25)
    common(sp)
    sp.set_defaults(func=cmd_launchscan)

    sp = sub.add_parser("edge", help="consistent-trader vs fluke gate")
    sp.add_argument("--trades", default=None,
                    help="JSON file: list of closed trades")
    sp.add_argument("--mint", default=None,
                    help="build trades from a live token scan")
    sp.add_argument("--chain", default="ethereum")
    sp.add_argument("--trials", type=int, default=1,
                    help="candidates scanned before this one was chosen")
    common(sp)
    sp.set_defaults(func=cmd_edge)

    sp = sub.add_parser("whitelist", help="consistent-trader whitelist")
    sp.add_argument("--wallet", default=None, help="address to evaluate")
    sp.add_argument("--trades", default=None,
                    help="JSON file: list of closed trades")
    sp.add_argument("--chain", default="ethereum")
    sp.add_argument("--cluster", default=None,
                    help="cluster id for a cross-chain identity")
    sp.add_argument("--trials", type=int, default=1)
    common(sp)
    sp.set_defaults(func=cmd_whitelist)

    sp = sub.add_parser("memeflow",
                        help="top-holder scan + allocation patterns")
    sp.add_argument("--token", required=True, help="memecoin contract")
    sp.add_argument("--chain", default="ethereum")
    sp.add_argument("--top", type=int, default=50)
    common(sp)
    sp.set_defaults(func=cmd_memeflow)

    sp = sub.add_parser("holders",
                        help="holder-composition series / ownership shifts")
    sp.add_argument("--token", required=True, help="token address")
    sp.add_argument("--chain", default="solana")
    sp.add_argument("--price", type=float, default=None,
                    help="price at snapshot time (live fetch if omitted)")
    sp.add_argument("--change24h", type=float, default=None)
    sp.add_argument("--detect", action="store_true",
                    help="detect abrupt ownership changes instead of snapshot")
    sp.add_argument("--spike-pct", type=float, default=None)
    sp.add_argument("--delta-pp", type=float, default=None)
    common(sp)
    sp.set_defaults(func=cmd_holders)

    # ---- signal: the trade-decision brief --------------------------------
    from .cmd_extra import cmd_signal as _cmd_signal
    sp = sub.add_parser("signal",
                        help="decision-ready trade brief for one token")
    sp.add_argument("--token", required=True, help="token address")
    sp.add_argument("--chain", default="solana")
    sp.add_argument("--target-usd", type=float, default=1000.0,
                    help="the size you intend to trade, used for the "
                         "liquidity-depth check")
    sp.add_argument("--out", default=None, help="output directory")
    common(sp)
    sp.set_defaults(func=_cmd_signal)


OPERATOR_OPENING = (
    "Which blockchains are we targeting today, and do you have a specific "
    "wallet address or strategy you want me to profile?"
)
