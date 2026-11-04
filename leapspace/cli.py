"""
Command-line orchestrator.

    python -m leapspace.cli regime   --symbol SPY
    python -m leapspace.cli gamma    --symbol QQQ
    python -m leapspace.cli memes    --query BONK
    python -m leapspace.cli wallet   --address <SOLANA_ADDRESS>
    python -m leapspace.cli disclosure --oge-names Powell,Mullin
    python -m leapspace.cli alerts   --symbol QQQ --oge-names Powell
    python -m leapspace.cli backtest --quick
    python -m leapspace.cli report   --quick

Every command prints its provenance and its source gaps. `--json` emits the
machine-readable payload for each command.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

from .alerts import (AlertEngine, action_alerts, disclosure_alerts, gamma_alerts,
                      memecoin_alerts, onchain_alerts, price_alerts_from_bars,
                      regime_transition_alerts)
from .gamma import compute_gamma_exposure, compute_option_flow, merge_flow_and_gamma
from .http import CachedFetcher
from .market import (closes_and_volumes, fetch_coingecko_prices, fetch_dex_pairs,
                      fetch_many_ohlcv, fetch_option_chain, normalise_dex_pair)
from .memecoin import screen_meme_coin, screen_search
from .onchain import analyse_wallet, cluster_wallets, concentration_report
from .provenance import SourceUnavailable, unavailable, write_json
from .regime import build_regime_features, identify_regimes

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
DATA_DIR = os.path.join(PROJECT, "data")
REPORT_DIR = os.path.join(PROJECT, "reports")
STATE_DIR = os.path.join(PROJECT, "state")

DEFAULT_SYMBOL = "QQQ"
DEFAULT_GAMMA_SYMBOL = "QQQ"


def _out(obj: Any, as_json: bool, text: str = "") -> None:
    if as_json:
        print(json.dumps(obj, indent=2, default=str))
    else:
        if text:
            print(text)
        else:
            print(json.dumps(obj, indent=2, default=str))


def _fetcher() -> CachedFetcher:
    os.makedirs(DATA_DIR, exist_ok=True)
    return CachedFetcher(os.path.join(DATA_DIR, "cache"), max_age_seconds=3600)


# --------------------------------------------------------------------------
# regime
# --------------------------------------------------------------------------


def cmd_architecture(args) -> int:
    """Generate the architecture diagram from the code."""
    from .archviz import build_architecture
    out = getattr(args, "out", None)
    r = build_architecture(out)
    print(f"wrote {r['html']}")
    print(f"  {r['n_modules']} modules, {r['n_public']} public functions")
    return 0


def cmd_regime(args) -> int:
    f = _fetcher()
    bars, failures, provs = fetch_many_ohlcv([args.symbol], rng=args.range,
                                             fetcher=f)
    if args.symbol not in bars:
        payload = {"symbol": args.symbol, "error":
                   "no bars returned",
                   "failures": failures,
                   "provenance": provs[0].disclosure() if provs else ""}
        _out(payload, args.json)
        return 2
    b = bars[args.symbol]
    closes, vols = closes_and_volumes(b)
    feats = build_regime_features(closes, vols,
                                  vol_short=args.vol_short,
                                  vol_long=args.vol_long,
                                  trend_lookback=args.trend_lookback,
                                  drawdown_lookback=args.drawdown_lookback,
                                  liquidity_lookback=args.liquidity_lookback)
    res = identify_regimes(feats, n_states=args.states,
                           min_bars=args.min_bars)
    if res is None:
        payload = {"symbol": args.symbol, "error":
                   "insufficient usable history for a regime fit "
                   f"(need >= {args.min_bars} bars)",
                   "provenance": prov[0].disclosure() if prov else ""}
        _out(payload, args.json)
        return 2
    s = res.summary()
    s["symbol"] = args.symbol
    s["provenance"] = [p.disclosure() for p in provs]
    s["latest_label"] = (res.label_series_filtered[-1]
                         if res.label_series_filtered else None)
    s["latest_posterior"] = {
        lab: (res.probability_of(lab)[-1]
              if res.probability_of(lab) else None)
        for lab in sorted(set(res.labels.values()))
    }
    lines = [f"REGIME — {args.symbol}",
             f"  provenance: {s['provenance'][0] if s['provenance'] else 'n/a'}",
             f"  state labels: {json.dumps(s['labels'])}",
             f"  state share:  {json.dumps({k: round(v, 3) for k, v in s['state_share'].items()})}",
             f"  current:      {s['latest_label']}"]
    for lab, p in s["latest_posterior"].items():
        if p is not None:
            lines.append(f"     P({lab}) = {p:.0%}")
    lines.append(f"  convergence:  {s['converged']} in {s['n_iter']} iterations")
    _out(s, args.json, "\n".join(lines))
    return 0


# --------------------------------------------------------------------------
# gamma
# --------------------------------------------------------------------------


def cmd_gamma(args) -> int:
    f = _fetcher()
    try:
        chain, prov = fetch_option_chain(args.symbol, fetcher=f)
    except SourceUnavailable as exc:
        payload = unavailable("nasdaq.option-chain", None, str(exc))
        _out(payload, args.json)
        return 2
    g = compute_gamma_exposure(chain)
    flow = compute_option_flow(chain)
    merged = merge_flow_and_gamma(flow, g)
    merged["provenance"] = [prov.disclosure()]
    lines = [f"GAMMA & OPTION FLOW — {args.symbol}",
             f"  provenance: {prov.disclosure()}",
             f"  net gamma:  {g.net_gamma:,.0f}  ({g.state})",
             f"  call gamma: {g.call_gamma:,.0f}   put gamma: {g.put_gamma:,.0f}",
             f"  max pain:   {g.max_pain_strike}   zero gamma: {g.zero_gamma_strike}",
             f"  put/call volume ratio: {flow.put_call_volume_ratio}",
             f"  net delta flow: {flow.net_delta_flow:,.0f}",
             f"  interpretation: {g.interpretation()}"]
    if g.warnings:
        lines.append(f"  warnings: {g.warnings}")
    lines.append("  caveats (always apply):")
    for a in g.assumptions:
        lines.append(f"    - {a}")
    _out(merged, args.json, "\n".join(lines))
    return 0


# --------------------------------------------------------------------------
# memes
# --------------------------------------------------------------------------


def cmd_memes(args) -> int:
    if args.mint:
        try:
            r = screen_meme_coin(args.mint)
        except SourceUnavailable as exc:
            _out(unavailable("memecoin.screen", args.mint, str(exc)), args.json)
            return 2
        payload = r.to_dict()
        lines = [f"MEME COIN SCREEN — {payload.get('symbol')} ({args.mint})",
                 f"  passed: {payload['passed']}   score: {payload['score']:.2f}"]
        for lay, v in payload["layers"].items():
            lines.append(f"  {lay}: {json.dumps(v)[:220]}")
        if payload["disqualifiers"]:
            lines.append("  disqualifiers:")
            for d in payload["disqualifiers"]:
                lines.append(f"    - {d}")
    else:
        payload = screen_search(args.query, limit=args.limit)
        lines = [f"MEME COIN SEARCH — {args.query}",
                 f"  screened: {payload['screened']}   passed: {payload['passed']}"]
        for r in payload["results"][:args.limit]:
            lines.append(f"  {r.get('symbol'):<12} passed={r['passed']} "
                         f"score={r['score']:.2f} "
                         f"{'; '.join(r['disqualifiers'][:2])}")
        if payload["errors"]:
            lines.append(f"  errors: {len(payload['errors'])}")
    _out(payload, args.json, "\n".join(lines))
    return 0


# --------------------------------------------------------------------------
# wallet
# --------------------------------------------------------------------------


def cmd_wallet(args) -> int:
    addrs = [a.strip() for a in args.address.split(",") if a.strip()]
    profiles = []
    gaps = []
    for a in addrs:
        try:
            profiles.append(analyse_wallet(a, tx_limit=args.tx_limit))
        except SourceUnavailable as exc:
            gaps.append(unavailable("solana.rpc", a, str(exc)))
    payload: Dict[str, Any] = {
        "wallets": [p.to_dict() for p in profiles],
        "gaps": gaps,
    }
    if len(profiles) > 1:
        payload["clusters"] = cluster_wallets(profiles)
    lines = [f"WALLET ANALYSIS — {len(profiles)} wallet(s)"]
    for p in profiles:
        d = p.to_dict()
        lines.append(f"  {d['address']}")
        lines.append(f"    signatures={d['n_signatures']} txs={d['n_transactions_fetched']} "
                     f"failed={d['n_failed_transactions']}")
        lines.append(f"    counterparties={d['unique_counterparties']} "
                     f"mints={d['unique_token_mints']} "
                     f"loops={len(d['loop_transactions'])} "
                     f"self_trades={len(d['self_trades'])}")
        lines.append(f"    SOL balance={d['sol_balance']}")
    if "clusters" in payload:
        lines.append(f"  clusters: {payload['clusters']['n_clusters']} "
                     f"from {payload['clusters']['n_wallets']} wallets")
        lines.append(f"    {payload['clusters']['interpretation']}")
    for g in gaps:
        lines.append(f"  GAP: {g['reason']}")
    _out(payload, args.json, "\n".join(lines))
    return 0


# --------------------------------------------------------------------------
# disclosure
# --------------------------------------------------------------------------


def cmd_disclosure(args) -> int:
    from .disclosure import build_disclosure_report
    names = [n.strip() for n in (args.oge_names or "").split(",") if n.strip()] or None
    rep = build_disclosure_report(house_year=args.house_year,
                                  oge_names=names,
                                  include_judicial=not args.no_judicial)
    lines = ["US OFFICIALS' FINANCIAL DISCLOSURES — THREE BRANCHES"]
    for key, b in (rep.get("branches") or {}).items():
        lines.append(f"  {key}: {b.get('filings_indexed')} filings indexed")
        if "by_type" in b:
            lines.append(f"      by type: {json.dumps(b['by_type'])[:200]}")
        if "by_agency" in b:
            lines.append(f"      by agency: {b['by_agency']}")
    lines.append(f"  coverage: {json.dumps(rep.get('coverage'))}")
    lines.append(f"  {rep.get('disclosure')}")
    if rep.get("sources_unavailable"):
        lines.append("  SOURCE GAPS (not 'no filings exist'):")
        for g in rep["sources_unavailable"]:
            lines.append(f"    - {g.get('source')}: {str(g.get('reason'))[:180]}")
    _out(rep, args.json, "\n".join(lines))
    return 0


# --------------------------------------------------------------------------
# alerts
# --------------------------------------------------------------------------


def cmd_alerts(args) -> int:
    os.makedirs(STATE_DIR, exist_ok=True)
    state = os.path.join(STATE_DIR, "alert_state.json")
    eng = AlertEngine(state_path=state)
    f = _fetcher()

    # --- price alerts from real OHLCV
    try:
        bars, provs, failures = fetch_many_ohlcv([args.symbol], rng=args.range,
                                                  fetcher=f)
        if args.symbol in bars:
            p = provs[0].disclosure() if provs else ""
            eng.add(price_alerts_from_bars(args.symbol, bars[args.symbol], p))
            # --- regime transition + action alerts
            closes, vols = closes_and_volumes(bars[args.symbol])
            feats = build_regime_features(closes, vols)
            res = identify_regimes(feats, n_states=args.states, min_bars=200)
            if res is not None:
                eng.add(regime_transition_alerts(res, args.symbol, p))
                eng.add(action_alerts(regime_result=res, symbol=args.symbol,
                                       provenance=p))
        else:
            eng.add_gap(unavailable("yahoo.chart", args.symbol,
                                    "no bars returned"))
    except SourceUnavailable as exc:
        eng.add_gap(unavailable("yahoo.chart", args.symbol, str(exc)))

    # --- gamma + flow alerts
    try:
        chain, prov = fetch_option_chain(args.gamma_symbol, fetcher=f)
        g = compute_gamma_exposure(chain)
        flow = compute_option_flow(chain)
        eng.add(gamma_alerts(g, flow, prov.disclosure()))
        eng.add(action_alerts(gamma=g, flow=flow, symbol=args.gamma_symbol,
                               provenance=prov.disclosure()))
    except SourceUnavailable as exc:
        eng.add_gap(unavailable("nasdaq.option-chain", args.gamma_symbol, str(exc)))

    # --- disclosure information alerts
    if args.oge_names:
        from .disclosure import build_disclosure_report
        names = [n.strip() for n in args.oge_names.split(",") if n.strip()]
        rep = build_disclosure_report(house_year=args.house_year,
                                      oge_names=names,
                                      include_judicial=False)
        eng.add(disclosure_alerts(rep, provenance="House Clerk + OGE"))
        for g in rep.get("sources_unavailable", []):
            eng.add_gap(g)

    print(eng.render(only_new=not args.all, show_thresholds=True))
    if args.save:
        eng.save_state()
        print(f"state saved: {state}")
    if args.json:
        write_json(os.path.join(REPORT_DIR, "alerts.json"), eng.to_dict())
    return 0


# --------------------------------------------------------------------------
# backtest
# --------------------------------------------------------------------------


def merge_backtest_results(path: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge freshly-run rows INTO the stored results file and write it back.

    Running a SUBSET of the specs (--spec) must not shrink the results
    file: a later one-spec run would otherwise wipe the other twelve rows
    and leave the consolidated report describing a run that no longer
    exists on disk. Rows for the specs just run replace their previous
    entry; every other row is preserved untouched.

    Returns the merged, name-sorted list that was written.
    """
    from .provenance import read_json
    stored = read_json(path)
    merged: Dict[str, Any] = {}
    order: List[str] = []
    if isinstance(stored, list):
        for row in stored:
            if isinstance(row, dict) and row.get("name"):
                name = row["name"]
                if name not in merged:
                    order.append(name)
                merged[name] = row
    for row in rows or []:
        if isinstance(row, dict) and row.get("name"):
            name = row["name"]
            if name not in merged:
                order.append(name)
            merged[name] = row
    # Preserve the file's existing order (the spec order the report uses);
    # append any genuinely new spec at the end.
    ordered = [merged[n] for n in order]
    write_json(path, ordered)
    return ordered


def cmd_backtest(args) -> int:
    from .backtest import all_specs, run_spec
    os.makedirs(REPORT_DIR, exist_ok=True)
    specs = all_specs()
    if args.spec:
        specs = [s for s in specs if args.spec in s.get("name", "")]
        if not specs:
            print(f"no spec matches '{args.spec}'. Available:")
            for s in all_specs():
                print(f"  - {s.get('name')}  ({s.get('paper')})")
            return 2
    results = []
    for s in specs:
        res = run_spec(s, quick=args.quick, out_dir=REPORT_DIR,
                       verbose=not args.quiet)
        results.append(res.to_dict())
        print("=" * 70)
        print(f"{res.name}: {res.verdict}")
        for fl in res.flags:
            print(f"  FLAG: {fl}")
        if res.errors:
            for e in res.errors:
                print(f"  ERROR: {e}")
        m = res.metrics
        for k in ("n_bars", "n_trades", "sharpe", "cagr", "max_drawdown",
                  "profit_factor", "win_rate", "t_stat"):
            if k in m:
                print(f"  {k}: {m[k]}")
        w = res.walk_forward
        for k in ("oos_sharpe", "oos_retention", "oos_profitable_folds", "n_folds"):
            if k in w:
                print(f"  wf.{k}: {w[k]}")
        if res.skipped_stages:
            print(f"  SKIPPED STAGES: {res.skipped_stages}")
        g = res.intake_gate or {}
        if g.get("available"):
            acc = g.get("auto_accepted") or []
            print(f"  INTAKE GATE: {'PASS' if g.get('passed') else 'REFUSED'}"
                  + (f"  accepted-as-engine-default: {acc}" if acc else ""))
        if res.report_path:
            print(f"  report: {res.report_path}")
    # Merge into the stored results rather than replacing them. Running a
    # SUBSET of the specs (--spec) must not shrink the results file: a
    # later one-spec run would otherwise wipe the other twelve rows and
    # leave the consolidated report describing a run that no longer exists
    # on disk. Rows for the specs just run replace their previous entry.
    path = os.path.join(REPORT_DIR, "backtest_results.json")
    ordered = merge_backtest_results(path, results)
    print(f"\nwrote {path} ({len(ordered)} specs"
          + (f", {len(results)} refreshed this run)" if len(results) != len(ordered)
             else ")"))
    return 0


# --------------------------------------------------------------------------
# report — everything, one artifact
# --------------------------------------------------------------------------


def _backfill_papers(payload: Dict[str, Any]) -> None:
    """Fill a missing 'paper' field on backtest rows from the spec catalogue.

    A stored payload written before the field existed would otherwise render
    a column of "?". This is a display fix only — it never changes a verdict
    or a metric.
    """
    try:
        from .backtest import all_specs
        lookup = {s.get("name"): s.get("paper", "") for s in all_specs()}
    except Exception:  # noqa: BLE001
        return
    for row in (payload.get("sections") or {}).get("backtests") or []:
        if not row.get("paper"):
            row["paper"] = lookup.get(row.get("name"), "")


def cmd_report(args) -> int:
    os.makedirs(REPORT_DIR, exist_ok=True)

    # --from-json regenerates the report from the stored payload WITHOUT
    # re-running the network work or the backtests. Useful after a rendering
    # fix, and it guarantees the numbers in the report are exactly the
    # numbers already on disk.
    if args.from_json:
        from .report import write_report
        from .provenance import read_json
        stored = read_json(args.from_json)
        if not stored:
            print(f"no stored payload at {args.from_json}")
            return 2
        payload = stored
        _backfill_papers(payload)
        from .report import merge_full_gauntlet
        full_path = os.path.join(REPORT_DIR, "full_gauntlet_results.json")
        n = merge_full_gauntlet(payload, full_path)
        paths = write_report(payload)
        print(f"regenerated from {args.from_json}")
        print(f"  full-gauntlet verdicts applied: {n}")
        print(f"wrote {paths['markdown']}")
        print(f"wrote {paths['json']}")
        return 0

    payload: Dict[str, Any] = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "disclosure": ("All figures below are computed from LIVE sources at "
                       "run time unless the entry says otherwise. Sources "
                       "that could not be reached are listed as gaps; no "
                       "data was substituted for them."),
        "sections": {},
        "gaps": [],
    }
    f = _fetcher()

    # regime
    try:
        bars, failures, provs = fetch_many_ohlcv([args.symbol], rng=args.range,
                                                 fetcher=f)
        if args.symbol in bars:
            closes, vols = closes_and_volumes(bars[args.symbol])
            feats = build_regime_features(closes, vols)
            res = identify_regimes(feats, n_states=args.states, min_bars=200)
            if res is not None:
                s = res.summary()
                s["symbol"] = args.symbol
                s["latest_label"] = res.label_series_filtered[-1]
                s["provenance"] = [p.disclosure() for p in provs]
                payload["sections"]["regime"] = s
            else:
                payload["gaps"].append(unavailable(
                    "regime_model", args.symbol,
                    "insufficient usable history for a regime fit"))
        else:
            payload["gaps"].append(unavailable(
                "yahoo.chart", args.symbol, "no bars returned"))
    except SourceUnavailable as exc:
        payload["gaps"].append(unavailable("yahoo.chart", args.symbol, str(exc)))

    # gamma
    try:
        chain, prov = fetch_option_chain(args.gamma_symbol, fetcher=f)
        g = compute_gamma_exposure(chain)
        flow = compute_option_flow(chain)
        merged = merge_flow_and_gamma(flow, g)
        merged["provenance"] = [prov.disclosure()]
        payload["sections"]["gamma"] = merged
    except SourceUnavailable as exc:
        payload["gaps"].append(unavailable("nasdaq.option-chain",
                                           args.gamma_symbol, str(exc)))

    # backtests
    from .backtest import all_specs, run_spec
    bt = []
    if args.reuse_backtests:
        # Reuse the stored results instead of re-running the engine. The
        # results carry the intake-gate record, and re-running would waste
        # the whole gauntlet to reproduce identical numbers.
        from .provenance import read_json
        stored = read_json(args.reuse_backtests)
        if not stored:
            print(f"no stored backtest results at {args.reuse_backtests}")
            return 2
        bt = list(stored)
        print(f"reusing {len(bt)} stored backtest results from {args.reuse_backtests}")
    else:
        for s in all_specs():
            if args.spec and args.spec not in s.get("name", ""):
                continue
            res = run_spec(s, quick=args.quick, out_dir=REPORT_DIR, verbose=False)
            bt.append(res.to_dict())
    from .report import merge_full_gauntlet
    full_path = os.path.join(REPORT_DIR, "full_gauntlet_results.json")
    n_overlay = merge_full_gauntlet({"sections": {"backtests": bt}}, full_path)
    if n_overlay:
        payload["sections"]["backtests"] = bt
        payload["full_gauntlet_overlay"] = {
            "applied": n_overlay,
            "source": full_path,
            "note": ("Rows marked 'FULL gauntlet' carry the stricter verdict "
                     "from a complete validation run. Rows without the marker "
                     "were run with --quick, which skips Monte Carlo, the "
                     "parameter sweep and replication — their verdict is a "
                     "preliminary read for those stages."),
        }
    payload["sections"]["backtests"] = bt

    # disclosure
    if args.with_disclosure:
        from .disclosure import build_disclosure_report
        names = [n.strip() for n in (args.oge_names or "").split(",") if n.strip()]
        payload["sections"]["disclosure"] = build_disclosure_report(
            house_year=args.house_year, oge_names=names or None,
            include_judicial=True)

    from .report import write_report
    paths = write_report(payload)
    print(f"wrote {paths['markdown']}")
    print(f"wrote {paths['json']}")
    for key in ("regime", "gamma", "disclosure"):
        print(f"  {key}: {'ok' if key in payload['sections'] else 'gap'}")
    print(f"  backtests: {len(bt)}")
    for b in bt:
        m = b.get("metrics") or {}
        w = b.get("walk_forward") or {}
        print(f"    {b['name']}: {b['verdict']}  "
              f"sharpe={m.get('sharpe')} oos={w.get('oos_sharpe')}")
    if payload["gaps"]:
        print("  gaps:")
        for g in payload["gaps"]:
            print(f"    - {g.get('source')}: {str(g.get('reason'))[:100]}")
    return 0


# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="leapspace.cli",
                                description="Automation built from the seven "
                                            "LeapSpace research papers.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--json", action="store_true", help="machine-readable output")

    sp = sub.add_parser("regime", help="market regime classification")
    sp.add_argument("--symbol", default=DEFAULT_SYMBOL)
    sp.add_argument("--states", type=int, default=4)
    sp.add_argument("--range", default="5y")
    sp.add_argument("--vol-short", type=int, default=10)
    sp.add_argument("--vol-long", type=int, default=60)
    sp.add_argument("--trend-lookback", type=int, default=60)
    sp.add_argument("--drawdown-lookback", type=int, default=60)
    sp.add_argument("--liquidity-lookback", type=int, default=20)
    sp.add_argument("--min-bars", type=int, default=250)
    common(sp)
    sp.set_defaults(func=cmd_regime)

    sp = sub.add_parser("gamma", help="dealer gamma exposure and option flow")
    sp.add_argument("--symbol", default=DEFAULT_GAMMA_SYMBOL)
    common(sp)
    sp.set_defaults(func=cmd_gamma)

    sp = sub.add_parser("memes", help="meme-coin screening")
    sp.add_argument("--query", default="BONK")
    sp.add_argument("--mint", default=None)
    sp.add_argument("--limit", type=int, default=10)
    common(sp)
    sp.set_defaults(func=cmd_memes)

    sp = sub.add_parser("wallet", help="Solana wallet analysis")
    sp.add_argument("--address", required=True)
    sp.add_argument("--tx-limit", type=int, default=25)
    common(sp)
    sp.set_defaults(func=cmd_wallet)

    sp = sub.add_parser("disclosure", help="US officials' financial disclosures")
    sp.add_argument("--oge-names", default=None)
    sp.add_argument("--house-year", type=int, default=2026)
    sp.add_argument("--no-judicial", action="store_true")
    common(sp)
    sp.set_defaults(func=cmd_disclosure)

    sp = sub.add_parser("alerts", help="price / information / action alerts")
    sp.add_argument("--symbol", default=DEFAULT_SYMBOL)
    sp.add_argument("--gamma-symbol", default=DEFAULT_GAMMA_SYMBOL)
    sp.add_argument("--range", default="1y")
    sp.add_argument("--states", type=int, default=4)
    sp.add_argument("--oge-names", default=None)
    sp.add_argument("--house-year", type=int, default=2026)
    sp.add_argument("--all", action="store_true", help="include already-seen alerts")
    sp.add_argument("--save", action="store_true", help="persist alert fingerprints")
    common(sp)
    sp.set_defaults(func=cmd_alerts)

    sp = sub.add_parser("backtest", help="run the paper-derived backtests")
    sp.add_argument("--spec", default=None)
    sp.add_argument("--quick", action="store_true")
    sp.add_argument("--quiet", action="store_true")
    common(sp)
    sp.set_defaults(func=cmd_backtest)

    sp = sub.add_parser("report", help="one consolidated artifact")
    sp.add_argument("--symbol", default=DEFAULT_SYMBOL)
    sp.add_argument("--gamma-symbol", default=DEFAULT_GAMMA_SYMBOL)
    sp.add_argument("--range", default="5y")
    sp.add_argument("--states", type=int, default=4)
    sp.add_argument("--spec", default=None)
    sp.add_argument("--quick", action="store_true")
    sp.add_argument("--with-disclosure", action="store_true",
                    help="include the three-branch disclosure report")
    sp.add_argument("--oge-names", default=None)
    sp.add_argument("--house-year", type=int, default=2026)
    sp.add_argument("--from-json", default=None,
                    help="regenerate the report from a stored payload "
                         "without re-running anything")
    sp.add_argument("--reuse-backtests", default=None,
                    help="reuse stored backtest results (a JSON list) instead "
                         "of re-running the engine")
    common(sp)
    sp.set_defaults(func=cmd_report)

    # --- on-chain memecoin quant (the four-quadrant operator brief) ---
    from .quant import add_parsers as _add_quant
    _add_quant(sub)

    # --- the architecture diagram ---
    sp = sub.add_parser(
        "architecture",
        help="generate the architecture diagram and module inventory "
             "(read from the code with ast, so it cannot go stale)")
    sp.add_argument("--out", default=None,
                    help="where to write the HTML (default: "
                         "reports/charts/architecture.html)")
    sp.set_defaults(func=cmd_architecture)

    common(p)
    p.set_defaults(func=cmd_report)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    os.makedirs(REPORT_DIR, exist_ok=True)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
