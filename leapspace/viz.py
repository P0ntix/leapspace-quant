"""Visual presentation of the package's outputs.

Charts follow the trading-visualization skill's conventions: dark theme,
green for profit / red for loss, blue for neutral, amber for warnings, and
multi-panel layouts with a shared x-axis (equity above, drawdown below).

Two output layers:

* PNG charts (matplotlib) for embedding and sharing.
* A single self-contained HTML dashboard that references the PNGs and
  carries the summary tables, so the whole result set can be read in one
  place.

Every chart states its provenance. Synthetic inputs are labelled as such
ON the chart, because a chart of simulated data that looks like live data
is exactly the kind of lie this package exists to prevent.

matplotlib is used when available; when it is not, the HTML dashboard is
still produced (tables only) and the module says so rather than failing.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "reports")
REPORT_DIR = os.path.abspath(REPORT_DIR)
VIZ_DIR = os.path.join(REPORT_DIR, "charts")

# --- the skill's trading palette -------------------------------------------
UP = "#00ff88"
DOWN = "#ff4444"
NEUTRAL = "#4488ff"
WARN = "#ffaa00"
MA_SHORT = "#ff6600"
MA_LONG = "#3399ff"
BG = "#1a1a2e"
GRID = "#333333"
TEXT = "#e0e0e0"
MUTED = "#aaaaaa"

VERDICT_COLOR = {
    "SUPPORTED": UP,
    "FRAGILE": WARN,
    "REFUTED": DOWN,
    "INCONCLUSIVE": NEUTRAL,
}

plt: Any = None
gridspec: Any = None
Line2D: Any = None
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as _plt
    import matplotlib.gridspec as _gs
    from matplotlib.lines import Line2D as _Line2D
    plt, gridspec, Line2D = _plt, _gs, _Line2D
    HAVE_MPL = True
except Exception:  # noqa: BLE001
    HAVE_MPL = False


def _style() -> None:
    if not HAVE_MPL:
        return
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG,
        "axes.edgecolor": GRID, "grid.color": GRID, "grid.alpha": 0.4,
        "text.color": TEXT, "xtick.color": MUTED, "ytick.color": MUTED,
        "font.size": 10,
    })


def _save(fig, path: str) -> Optional[str]:
    if not HAVE_MPL:
        return None
    fig.savefig(path, dpi=140, facecolor=fig.get_facecolor(),
                edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------


def load_backtest_results(path: Optional[str] = None) -> List[Dict[str, Any]]:
    p = path or os.path.join(REPORT_DIR, "backtest_results.json")
    try:
        with open(p, "r", encoding="utf-8") as fh:
            rows = json.load(fh)
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def equity_curve_for_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Run one spec through the engine and capture its real equity curve.

    The engine's bundle nests the simulation under "sim", so the equity
    series lives at bundle["sim"]["equity"].
    """
    try:
        import sys
        from .backtest import SKILL_SCRIPTS, register_extensions
        if SKILL_SCRIPTS not in sys.path:
            sys.path.insert(0, SKILL_SCRIPTS)
        import btengine
        import btvalidate
        register_extensions(btengine)
        bundle = btvalidate.run_spec(spec, verbose=False)
        if "error" in bundle:
            return {"error": bundle["error"]}
        sim = bundle.get("sim") or {}
        return {
            "equity": sim.get("equity") or [],
            "returns": sim.get("returns") or [],
            "trades": sim.get("trades") or [],
            "dates": bundle.get("panel").dates if bundle.get("panel") else [],
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def _apply_gauntlet_overlay(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Overlay the FULL-gauntlet verdicts before charting.

    Without this the dashboard would show a quick-run SUPPORTED where the
    markdown report shows the stricter FRAGILE verdict from the complete
    gauntlet - two artifacts disagreeing about the same strategy.
    """
    try:
        from .report import merge_full_gauntlet
        path = os.path.join(REPORT_DIR, "full_gauntlet_results.json")
        payload = {"sections": {"backtests": rows}}
        merge_full_gauntlet(payload, path)
        out = payload["sections"]["backtests"]
        if payload.get("full_gauntlet_overlay"):
            return out
    except Exception:  # noqa: BLE001
        pass
    return rows


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------


def chart_verdicts(rows: List[Dict[str, Any]], path: str) -> Optional[str]:
    """IS Sharpe vs OOS Sharpe for every spec, coloured by verdict."""
    if not HAVE_MPL or not rows:
        return None
    _style()
    data = []
    for r in rows:
        m = r.get("metrics") or {}
        w = r.get("walk_forward") or {}
        data.append((r.get("name", "?"), m.get("sharpe"), w.get("oos_sharpe"),
                     r.get("verdict", "?")))
    data.sort(key=lambda d: (d[1] is None, -(d[1] or 0)))
    names = [d[0] for d in data]
    y = list(range(len(data)))
    fig, ax = plt.subplots(figsize=(13, max(6, len(data) * 0.42)))
    for i, (_n, is_s, oos_s, verdict) in enumerate(data):
        c = VERDICT_COLOR.get(str(verdict).upper(), NEUTRAL)
        if is_s is not None:
            ax.barh(i, is_s, color=c, alpha=0.85, height=0.62,
                    label="In-sample Sharpe" if i == 0 else None)
        if oos_s is not None:
            ax.barh(i, oos_s, color=c, alpha=0.35, height=0.62,
                    edgecolor=c, linewidth=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.axvline(0, color=MUTED, linewidth=0.8)
    ax.set_xlabel("Sharpe ratio  (solid = in-sample, outline = out-of-sample)")
    ax.set_title("Backtest verdicts — every strategy derived from the seven papers",
                 fontsize=13, fontweight="bold", color="white")
    ax.grid(True, axis="x", alpha=0.3)
    handles = [Line2D([], [], color=UP, lw=8, label="SUPPORTED"),
               Line2D([], [], color=WARN, lw=8, label="FRAGILE"),
               Line2D([], [], color=DOWN, lw=8, label="REFUTED"),
               Line2D([], [], color=NEUTRAL, lw=8, label="INCONCLUSIVE")]
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    return _save(fig, path)


def chart_walk_forward(rows: List[Dict[str, Any]], path: str) -> Optional[str]:
    """Per-fold in-sample vs out-of-sample Sharpe."""
    if not HAVE_MPL or not rows:
        return None
    _style()
    have = [r for r in rows if (r.get("walk_forward") or {}).get("n_folds")]
    if not have:
        return None
    have = sorted(have, key=lambda r: -(r["walk_forward"].get("oos_sharpe") or -9))
    have = have[:8]
    fig, ax = plt.subplots(figsize=(13, max(4, len(have) * 0.9)))
    labels, is_vals, oos_vals = [], [], []
    for r in have:
        w = r["walk_forward"]
        labels.append(f"{r.get('name')}\n{w.get('oos_profitable_folds')}/"
                      f"{w.get('n_folds')} folds profitable")
        is_vals.append(w.get("oos_sharpe"))
        oos_vals.append(w.get("is_sharpe") or w.get("oos_retention"))
    x = list(range(len(labels)))
    width = 0.38
    ax.bar([i - width / 2 for i in x], [v if v is not None else 0 for v in is_vals],
           width, color=NEUTRAL, label="out-of-sample Sharpe")
    ax.bar([i + width / 2 for i in x],
           [v if v is not None else 0 for v in oos_vals],
           width, color=MA_LONG, alpha=0.65, label="OOS retention (x)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_ylabel("Sharpe / retention")
    ax.set_title("Walk-forward: out-of-sample performance by strategy",
                 fontsize=13, fontweight="bold", color="white")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    return _save(fig, path)


def chart_equity(equities: Dict[str, List[float]], path: str,
                 title: str = "Equity curves (real engine output)") -> Optional[str]:
    """Equity curve above, underwater drawdown below, shared x-axis."""
    if not HAVE_MPL or not equities:
        return None
    _style()
    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(2, 1, height_ratios=[2.4, 1], hspace=0.06)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    colors = [UP, NEUTRAL, WARN, MA_SHORT, MA_LONG]
    for i, (name, eq) in enumerate(equities.items()):
        if not eq:
            continue
        c = colors[i % len(colors)]
        x = list(range(len(eq)))
        ax1.plot(x, eq, color=c, linewidth=1.5, label=name)
        peak = eq[0]
        dd = []
        for v in eq:
            peak = max(peak, v)
            dd.append((v - peak) / peak if peak else 0.0)
        ax2.fill_between(x, dd, 0, color=c, alpha=0.35)
    ax1.set_ylabel("Portfolio value")
    ax1.set_title(title, fontsize=13, fontweight="bold", color="white")
    ax1.legend(fontsize=8, loc="upper left")
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(labelbottom=False)
    ax2.set_ylabel("Drawdown")
    ax2.set_xlabel("Bar")
    ax2.grid(True, alpha=0.3)
    return _save(fig, path)


def _equity_points(sim: Any) -> Tuple[List[Any], List[float]]:
    """Extract (x, y) points from a simulation result.

    The FLATTENED form of the simulation joins the equity curve into a
    string, so the raw object is used where available; the extraction is
    defensive about the key names because they are the simulation's
    business, not the chart's.
    """
    curve = getattr(sim, "equity_curve", None)
    if curve is None and isinstance(sim, dict):
        curve = sim.get("equity_curve")
    if isinstance(curve, str) or not curve:
        return [], []
    xs: List[Any] = []
    ys: List[float] = []
    for i, row in enumerate(curve):
        if isinstance(row, dict):
            val = None
            for key in ("equity", "value", "equity_usd", "portfolio_value",
                        "total"):
                if key in row:
                    val = row[key]
                    break
            # The x-axis is the BAR INDEX, not the timestamp: a unix
            # timestamp axis compresses the whole curve into a sliver.
            x = row.get("bar", i)
        else:
            val = row
            x = i
        try:
            y = float(val) if val is not None else None
        except (TypeError, ValueError):
            continue
        if y is None:
            continue
        xs.append(x)
        ys.append(y)
    return xs, ys


def chart_simulation(sim: Dict[str, Any], path: str) -> Optional[str]:
    """The friction-aware copy-trade simulation: equity, drawdown, rugs."""
    if not HAVE_MPL:
        return None
    xs, ys = _equity_points(sim)
    if not ys:
        return None
    _style()
    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(3, 1, height_ratios=[2.4, 1, 0.8], hspace=0.08)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax1.plot(xs, ys, color=UP, linewidth=1.6)
    ax1.set_ylabel("Equity (USD)")
    price_prov = (sim.get("price_provenance") if isinstance(sim, dict)
                  else getattr(sim, "price_provenance", "?")) or "?"
    signal_prov = (sim.get("signal_provenance") if isinstance(sim, dict)
                   else getattr(sim, "signal_provenance", "?")) or "?"
    ax1.set_title(
        f"Copy-trade simulation — friction-aware "
        f"[prices {price_prov}, signals {signal_prov}]",
        fontsize=13, fontweight="bold", color="white")
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(labelbottom=False)
    peak = ys[0]
    dd = []
    for v in ys:
        peak = max(peak, v)
        dd.append((v - peak) / peak if peak else 0.0)
    ax2.fill_between(xs, dd, 0, color=DOWN, alpha=0.55)
    ax2.set_ylabel("Drawdown")
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(labelbottom=False)
    # Rug events.
    rugs = (sim.get("rugs") if isinstance(sim, dict)
            else getattr(sim, "rugs", None)) or []
    rug_x = []
    for r in rugs:
        if isinstance(r, dict):
            rug_x.append(r.get("index", r.get("ts")))
        else:
            rug_x.append(getattr(r, "index", getattr(r, "ts", None)))
    ax3.vlines(rug_x, 0, 1, color=DOWN, linewidth=2, alpha=0.85)
    ax3.set_yticks([])
    ax3.set_ylabel(f"Rugs\n({len(rugs)})", rotation=0, ha="right",
                    fontsize=8, color=DOWN)
    ax3.set_xlabel("Bar")
    stats = (sim.get("stats") if isinstance(sim, dict)
             else getattr(sim, "stats", None)) or {}

    def _f2(v):
        if v is None:
            return "n/a"
        if isinstance(v, float):
            return f"{v:.4g}"
        return str(v)

    txt = (f"trades={stats.get('n_trades')}  skipped={stats.get('n_skipped')}  "
           f"win_rate={_f2(stats.get('win_rate'))}  "
           f"return={_f2(stats.get('total_return_pct'))}  "
           f"max_dd={_f2(stats.get('max_drawdown_pct'))}  "
           f"PF={_f2(stats.get('profit_factor'))}")
    ax1.text(0.01, 0.95, txt, transform=ax1.transAxes, fontsize=9,
             color=TEXT, va="top",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#00000055",
                       edgecolor=GRID))
    return _save(fig, path)


def chart_regime(price: Sequence[float], labels: Sequence[str], path: str,
                 title: str = "Market regime") -> Optional[str]:
    """Price with the HMM regime states shaded behind it."""
    if not HAVE_MPL or not price or not labels:
        return None
    _style()
    states = sorted(set(labels))
    palette = {s: c for s, c in zip(states, [UP, NEUTRAL, WARN, DOWN, MA_LONG])}
    fig, ax = plt.subplots(figsize=(14, 6))
    x = list(range(len(price)))
    ax.plot(x, price, color=TEXT, linewidth=1.0, zorder=3)
    start = 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[start]:
            c = palette.get(labels[start], GRID)
            ax.axvspan(start, i, color=c, alpha=0.16, zorder=1)
            start = i
    handles = [Line2D([], [], color=palette[s], lw=8, alpha=0.6, label=s)
               for s in states]
    ax.legend(handles=handles, fontsize=8, loc="upper left", ncol=3)
    ax.set_ylabel("Price")
    ax.set_xlabel("Bar")
    ax.set_title(title, fontsize=13, fontweight="bold", color="white")
    ax.grid(True, alpha=0.3)
    return _save(fig, path)


def chart_chains(health: Dict[str, Any], path: str) -> Optional[str]:
    """Multi-chain reachability and live liquidity."""
    if not HAVE_MPL:
        return None
    chains = health.get("chains") or {}
    if not chains:
        return None
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5),
                                    gridspec_kw={"width_ratios": [1, 1.3]})
    names = list(chains.keys())
    heights = [1 if chains[n].get("reachable") else 0 for n in names]
    colors = [UP if h else DOWN for h in heights]
    ax1.bar(names, heights, color=colors, alpha=0.85)
    ax1.set_ylim(0, 1.3)
    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(["DOWN", "LIVE"])
    ax1.set_title("Chain reachability (checked live)", fontsize=12,
                  fontweight="bold", color="white")
    ax1.grid(True, axis="y", alpha=0.3)
    for i, n in enumerate(names):
        ax1.text(i, heights[i] + 0.05, str(chains[n].get("rpc_status", ""))[:22],
                 ha="center", fontsize=6.5, color=MUTED)

    snaps = health.get("tokens") or []
    if snaps:
        labels = [s.get("symbol") or s.get("chain", "?") for s in snaps]
        liq = [float(s.get("liquidity_usd") or 0) for s in snaps]
        cols = [UP if l > 1_000_000 else (WARN if l > 100_000 else DOWN)
                for l in liq]
        ax2.barh(range(len(labels)), liq, color=cols, alpha=0.85)
        ax2.set_yticks(range(len(labels)))
        ax2.set_yticklabels(labels, fontsize=8)
        ax2.set_xscale("log")
        ax2.set_xlabel("Liquidity (USD, log scale)")
        ax2.set_title("Live token liquidity", fontsize=12, fontweight="bold",
                      color="white")
        ax2.grid(True, axis="x", alpha=0.3)
    else:
        ax2.text(0.5, 0.5, "no token snapshot", ha="center", color=MUTED,
                 transform=ax2.transAxes)
    return _save(fig, path)


# --------------------------------------------------------------------------
# HTML dashboard
# --------------------------------------------------------------------------


def _table(rows: Sequence[Sequence[Any]], headers: Sequence[str]) -> str:
    out = ["<table><thead><tr>"]
    for h in headers:
        out.append(f"<th>{h}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for c in r:
            out.append(f"<td>{c}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def run_demo_simulation(seed: int = 42) -> Any:
    """Run the friction-aware copy-trade simulation for the dashboard.

    The inputs are SYNTHETIC and the output says so in three places: the
    chart title, the dashboard note and the provenance fields. The
    simulation exercises the real friction model, rug injector, MEV
    simulator and finite-bankroll logic against a synthetic price series,
    because a live memecoin price history at minute resolution is not
    available from a free endpoint.
    """
    try:
        from .friction import (CopyConfig, MEVConfig, RugConfig,
                               run_simulation)
        from .models import Friction, WalletTrade
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    prices = [(1700000000 + i * 3600,
               1.0 + 0.01 * (i % 17) - 0.002 * i) for i in range(160)]
    signals = []
    for i in range(24):
        signals.append(WalletTrade(
            wallet=f"w{i % 5}", chain="solana", token=f"TOK{i % 4}",
            side="buy" if (i % 7) else "sell", amount=100.0,
            price_usd=1.0 + 0.01 * (i % 17), ts=1700000000 + i * 3600,
            provenance="SYNTHETIC"))
    try:
        res = run_simulation(
            signals, prices,
            friction=Friction(slippage_bps=100.0, failed_tx_rate=0.05,
                              latency_seconds=2.0),
            bankroll=1000.0,
            rug_config=RugConfig(rug_probability=0.1, min_drop_pct=80.0,
                                  max_drop_pct=99.0, seed=seed),
            mev_config=MEVConfig(max_penalty_bps=50.0,
                                  sandwich_probability=0.35, seed=seed),
            seed=seed,
            config=CopyConfig(start_usd=1000.0, size_pct=0.1,
                               stop_loss_pct=0.2, take_profit_pct=0.5),
            price_provenance="SYNTHETIC", signal_provenance="SYNTHETIC")
        # The RAW result is returned: its flattened form joins the equity
        # curve into a string, which cannot be plotted.
        return res
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def build_dashboard(out_dir: str = VIZ_DIR,
                    results_path: Optional[str] = None,
                    live: bool = True) -> Dict[str, Any]:
    """Build the PNG charts and the HTML dashboard. Returns the paths."""
    os.makedirs(out_dir, exist_ok=True)
    rows = _apply_gauntlet_overlay(load_backtest_results(results_path))
    charts: List[Dict[str, Any]] = []
    failures: List[str] = []

    def add(title: str, path: Optional[str], note: str = "") -> None:
        if path:
            charts.append({"title": title, "file": os.path.basename(path),
                           "note": note})

    def safe(title: str, fn, *a, **kw) -> Optional[str]:
        """One chart failing must not take the whole dashboard down."""
        try:
            return fn(*a, **kw)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{title}: {type(exc).__name__}: {exc}")
            return None

    p = os.path.join(out_dir, "verdicts.png")
    add("Backtest verdicts", safe("verdicts", chart_verdicts, rows, p),
        "In-sample vs out-of-sample Sharpe for every paper-derived strategy.")
    p = os.path.join(out_dir, "walkforward.png")
    add("Walk-forward", safe("walkforward", chart_walk_forward, rows, p),
        "Out-of-sample Sharpe and fold profitability per strategy.")

    # Equity curves for the leading specs (real engine runs).
    equities: Dict[str, List[float]] = {}
    if rows:
        from .backtest import all_specs
        by_name = {s.get("name"): s for s in all_specs()}
        ranked = sorted(
            [r for r in rows if (r.get("metrics") or {}).get("sharpe") is not None],
            key=lambda r: -((r["metrics"].get("sharpe")) or -9))
        for r in ranked[:3]:
            spec = by_name.get(r.get("name"))
            if not spec:
                continue
            got = equity_curve_for_spec(spec)
            eq = got.get("equity") or []
            if eq:
                equities[r["name"]] = eq
    p = os.path.join(out_dir, "equity.png")
    add("Equity curves", safe("equity", chart_equity, equities, p),
        "Real engine equity curves for the three highest-Sharpe strategies.")

    # The friction-aware copy-trade simulation.
    sim_payload = run_demo_simulation()
    p = os.path.join(out_dir, "simulation.png")
    add("Copy-trade simulation", safe("simulation", chart_simulation, sim_payload, p),
        "Friction-aware copy-trading simulation: equity, underwater "
        "drawdown and injected rug events. Synthetic inputs, labelled as "
        "such on the chart.")

    # Multi-chain health + live token snapshot.
    health: Dict[str, Any] = {"chains": {}, "tokens": []}
    if live:
        try:
            from .chains import chain_health, fetch_token_events
            health = chain_health(["solana", "ethereum", "base", "bsc",
                                   "arbitrum"])
            samples = {
                "solana": ("BONK", "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"),
                "ethereum": ("PEPE", "0x6982508145454Ce325dDbE47a25d4ec3d2311933"),
                "base": ("BRETT", "0x532f27101965dd16442E59d40670FaF5eBB142E4"),
                "bsc": ("CAKE", "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"),
            }
            for cid, (sym, addr) in samples.items():
                try:
                    res = fetch_token_events(cid, addr)
                    for e in res["events"]:
                        if e.kind == "price_update":
                            health["tokens"].append({
                                "chain": cid, "symbol": sym,
                                "price_usd": e.detail.get("price_usd"),
                                "liquidity_usd": e.detail.get("liquidity_usd"),
                                "volume_24h_usd": e.detail.get("volume_24h_usd"),
                                "dex": e.detail.get("dex"),
                            })
                            break
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            pass
    p = os.path.join(out_dir, "chains.png")
    add("Multi-chain", safe("chains", chart_chains, health, p),
        "Live chain reachability and token liquidity.")

    # ---- the memecoin-trader half --------------------------------------
    # These charts exist because the gate's most important finding is a
    # COLLAPSE that a table of numbers hides: a wallet's 18 closed
    # trades may be ONE independent bet.
    try:
        from . import viz_memecoin as VM

        def _load(rel, default=None):
            import json as _json
            try:
                with open(os.path.join(os.path.dirname(out_dir), rel),
                          encoding="utf-8") as fh:
                    return _json.load(fh)
            except Exception:
                return default

        _priced = _load("pepe_priced_edge.json", {}) or {}
        _results = _priced.get("results") or []
        p = os.path.join(out_dir, "edge_gate.png")
        add("Consistency gate", safe("edge_gate",
                                     VM.chart_edge_gate, _results, p),
            "Raw closed trades vs the INDEPENDENT BETS the statistical "
            "tests actually use. The collapse IS the finding.")

        _wl = _load(os.path.join("..", "leapspace", "state",
                                 "whitelist.json"), {}) or {}
        p = os.path.join(out_dir, "whitelist.png")
        add("Whitelist", safe("whitelist", VM.chart_whitelist, _wl, p),
            "Registry status and the promotion/retirement timeline. "
            "History is never deleted (GIPS 3.A.9).")

        p = os.path.join(out_dir, "price_accuracy.png")
        add("Price at a past block", safe("price_accuracy",
                                          VM.chart_price_accuracy, p),
            "Historical price read from the DEX's own reserves at each "
            "trade's block, against the known reference prices.")

        try:
            from .report_memecoin import build_memecoin_sections
            _sec = (build_memecoin_sections(
                os.path.dirname(os.path.dirname(out_dir)))
                .get("sections") or {})
            _cov = _sec.get("criteria_coverage") or {}
            _rows = (_cov.get("rows") or _cov.get("criteria")
                     or _cov.get("table") or [])
            if isinstance(_rows, dict):
                _rows = list(_rows.values())
        except Exception:
            _rows = []
        if _rows:
            p = os.path.join(out_dir, "criteria.png")
            add("Criteria coverage", safe("criteria",
                                         VM.chart_criteria_coverage,
                                         _rows, p),
                "Which of the cited criteria are enforced in code. A "
                "documented-but-unenforced criterion is shown as a gap.")

        _series = {}
        import os as _os
        # NOTE the "..": `out_dir` is <root>/reports/charts, so the
        # package's state directory is two levels up, not one.
        _sd = _os.path.join(_os.path.dirname(_os.path.dirname(out_dir)),
                            "leapspace", "state", "social_series")
        if _os.path.isdir(_sd):
            for _fn in _os.listdir(_sd):
                if _fn.endswith(".json"):
                    _blob = _load(os.path.join("..", "leapspace", "state",
                                               "social_series", _fn),
                                  {}) or {}
                    _snaps = _blob.get("snapshots") or []
                    if _snaps:
                        _series[_fn[:22]] = _snaps
        if _series:
            p = os.path.join(out_dir, "community.png")
            add("Community size", safe("community",
                                       VM.chart_community_series,
                                       _series, p),
                "The community-size series, as it is COLLECTED. There is "
                "no keyless source for a historical member count.")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"memecoin charts: {type(exc).__name__}: {exc}")

    # Backtest summary table.
    bt_rows = []
    for r in sorted(rows, key=lambda x: -((x.get("metrics") or {})
                                          .get("sharpe") or -9)):
        m = r.get("metrics") or {}
        w = r.get("walk_forward") or {}
        v = str(r.get("verdict", "?")).upper()
        bt_rows.append([
            f"<code>{r.get('name')}</code>",
            r.get("paper", "?"),
            f"<span style='color:{VERDICT_COLOR.get(v, NEUTRAL)};"
            f"font-weight:700'>{v}</span>",
            r.get("validation") or ("--quick" if r.get("skipped_stages")
                                    else "full"),
            m.get("n_trades", "n/a"), m.get("sharpe", "n/a"),
            m.get("cagr", "n/a"), m.get("max_drawdown", "n/a"),
            w.get("oos_sharpe", "n/a"),
            f"{w.get('oos_profitable_folds', 'n/a')}/{w.get('n_folds', 'n/a')}",
        ])
    bt_table = _table(bt_rows, ["Strategy", "Paper", "Verdict", "Validation",
                                "Trades", "Sharpe", "CAGR", "MaxDD",
                                "OOS Sharpe", "OOS folds"])

    chain_rows = [[c, r.get("rpc_status", ""), r.get("data_status", ""),
                   "reachable" if r.get("reachable") else "DOWN"]
                  for c, r in (health.get("chains") or {}).items()]
    token_rows = [[t.get("chain"), t.get("symbol"),
                   t.get("price_usd"), t.get("liquidity_usd"),
                   t.get("volume_24h_usd"), t.get("dex")]
                  for t in (health.get("tokens") or [])]

    gap_rows = [[g.get("source"), g.get("reason")]
                for g in (health.get("gaps") or [])]

    cards = []
    for c in charts:
        cards.append(
            f"<section class='card'><h2>{c['title']}</h2>"
            f"<p class='note'>{c['note']}</p>"
            f"<img src='{c['file']}' alt='{c['title']}'></section>")

    html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>LeapSpace Quant — visual report</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ background:#12121f; color:#e0e0e0; font-family: ui-sans-serif,
          system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
          margin:0; padding:28px 32px; }}
  h1 {{ font-size:24px; margin:0 0 4px; letter-spacing:-0.2px; }}
  h2 {{ font-size:16px; margin:0 0 4px; }}
  .sub {{ color:#8a8aa0; font-size:13px; margin:0 0 22px; }}
  .card {{ background:#1a1a2e; border:1px solid #2a2a3e; border-radius:12px;
           padding:18px 20px; margin:0 0 20px; }}
  .note {{ color:#8a8aa0; font-size:12px; margin:0 0 12px; }}
  img {{ width:100%; height:auto; border-radius:6px; display:block; }}
  table {{ width:100%; border-collapse:collapse; font-size:12px;
           font-variant-numeric: tabular-nums; }}
  th {{ text-align:left; color:#8a8aa0; font-weight:600; padding:8px 10px;
        border-bottom:1px solid #2a2a3e; position:sticky; top:0;
        background:#1a1a2e; }}
  td {{ padding:7px 10px; border-bottom:1px solid #222233; }}
  code {{ color:#9fd0ff; font-size:11px; }}
  .scroll {{ max-height:460px; overflow:auto; }}
  .warn {{ background:#2a2010; border:1px solid #6b4d12; color:#ffcf7a;
           padding:10px 14px; border-radius:8px; font-size:12px;
           margin:0 0 20px; }}
</style></head><body>
<h1>LeapSpace Quant — visual report</h1>
<p class="sub">Seven papers · thirteen strategies · three-branch disclosures ·
on-chain memecoin quant layer</p>

<div class="warn">
Every figure states its provenance. Live data is fetched at render time;
simulated data is labelled SYNTHETIC on the chart. A verdict of SUPPORTED
means "warrants paper trading", never "trade it".
</div>

<h2 style="margin-bottom:10px">Backtests</h2>
<div class="card"><div class="scroll">{bt_table}</div></div>

{'<div class="card"><div class="scroll">' + _table(chain_rows, ['Chain', 'RPC', 'Data source', 'Status']) + '</div></div>' if chain_rows else ''}
{'<div class="card"><div class="scroll">' + _table(token_rows, ['Chain', 'Token', 'Price USD', 'Liquidity USD', '24h volume USD', 'DEX']) + '</div></div>' if token_rows else ''}
{'<div class="card"><h2>Source gaps</h2><p class="note">Availability problems — NOT statements that the data does not exist.</p><div class="scroll">' + _table(gap_rows, ['Source', 'Reason']) + '</div></div>' if gap_rows else ''}

{''.join(cards)}
</body></html>
"""
    html_path = os.path.join(out_dir, "dashboard.html")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return {"html": html_path, "charts": charts,
            "n_charts": len(charts), "n_specs": len(rows),
            "matplotlib": HAVE_MPL, "failures": failures}


if __name__ == "__main__":
    import sys
    out = build_dashboard()
    print("VISUAL REPORT")
    print(f"  html    : {out['html']}")
    print(f"  charts  : {out['n_charts']}")
    for c in out["charts"]:
        print(f"    - {c['title']:<22} {c['file']}")
    print(f"  specs   : {out['n_specs']}")
    print(f"  matplotlib available: {out['matplotlib']}")
    sys.exit(0)
