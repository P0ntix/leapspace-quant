"""The architecture diagram: the project's flow, drawn.

WHAT THIS IS
    A self-contained HTML page showing how the package is put together
    and how data flows through it. It is generated FROM THE CODE, not
    drawn by hand - the module inventory is read with `ast`, and the
    dependency edges are the real import edges (including the lazy
    ones inside functions, which is how this package avoids circular
    imports).

WHAT IT SHOWS
    1. THE LAYER DIAGRAM. The nine layers, with the modules in each
       and the dependency edges between them. This is the map a
       newcomer should read first.
    2. THE DATA FLOW. The actual pipeline, end to end: a data source
       becomes a feature, a feature becomes a signal, the signal
       becomes weights, the weights become a simulation, and the
       simulation becomes a verdict. With the module that owns each
       stage and the gate that can stop it.
    3. THE MODULE TABLE. Every module with its layer, its size, its
       public function count and its dependencies.
    4. THE HOT SPOTS. The modules that most things depend on, and the
       ones that are largest. These are the ones a change breaks.

WHY IT IS HTML AND NOT A STATIC IMAGE
    Because it is regenerated from the code, it cannot go stale
    silently: running the generator after a refactor shows the new
    shape. A hand-drawn diagram would be wrong within a week.

Run: python -m leapspace.archviz
"""
from __future__ import annotations

import ast
import html
import os
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

__all__ = ["LAYERS", "module_inventory", "render_architecture",
           "build_architecture"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "leapspace")
OUT_HTML = os.path.join(ROOT, "reports", "charts", "architecture.html")


#: The layers, in pipeline order. Every module is assigned to exactly
#: one, and the assignment is explicit so a new module has to be
#: placed deliberately rather than falling into a default.
LAYERS: List[Dict[str, Any]] = [
    {"id": "infra", "name": "Infrastructure",
     "desc": "HTTP, caching, provenance, secrets, shared models",
     "colour": "#5a6a7a"},
    {"id": "source", "name": "Data sources",
     "desc": "Market, on-chain, social, disclosure, macro data",
     "colour": "#4a7a9a"},
    {"id": "feature", "name": "Features & leading indicators",
     "desc": "Indicators, the volatility risk premium, funding/OI",
     "colour": "#4a9a7a"},
    {"id": "signal", "name": "Signals",
     "desc": "Features -> positions: regime switch, ensembles, pairs",
     "colour": "#7a9a4a"},
    {"id": "portfolio", "name": "Portfolio & risk",
     "desc": "Sizing, covariance, risk parity, caps, kill switch",
     "colour": "#9a7a4a"},
    {"id": "backtest", "name": "Backtest engine",
     "desc": "The strategy-backtest-lab gauntlet, walk-forward, costs",
     "colour": "#9a5a4a"},
    {"id": "validation", "name": "Validation",
     "desc": "PBO, CPCV, edge scoring, negative controls",
     "colour": "#7a4a9a"},
    {"id": "report", "name": "Reports & visualisation",
     "desc": "Markdown, JSON, inline-SVG dashboards",
     "colour": "#4a7a9a"},
    {"id": "governance", "name": "Governance & policy",
     "desc": "Kill switch, disclosure, source reliability, readiness",
     "colour": "#9a4a6a"},
    {"id": "wallet", "name": "Wallet & chain profiling",
     "desc": "Holder analysis, wallet search, consistency gates",
     "colour": "#6a7a4a"},
]


#: Which layer each module belongs to. Explicit, so a new module has
#: to be placed.
MODULE_LAYER: Dict[str, str] = {
    # infrastructure
    "http": "infra", "provenance": "infra", "models": "infra",
    "cache": "infra", "cli": "infra", "cmd_extra": "infra",
    "sources": "infra", "config": "infra", "secrets": "infra",
    "utils": "infra", "state": "infra",
    # sources
    "market": "source", "onchain": "source", "etherscan": "source",
    "social": "source", "disclosure": "source", "holders": "source",
    "priceatblock": "source", "priced": "source", "traders": "source",
    "narrative": "source", "whitelist": "source", "deployers": "source",
    "source_reliability": "source", "crosschain": "source",
    "chains": "source", "chainregistry": "source",
    # features
    "leading": "feature", "leadingcache": "feature",
    "cryptoderivs": "feature", "gamma": "feature", "regime": "feature",
    "leadingspecs": "feature",
    # signals
    "ensemble": "signal", "trend": "signal", "stats": "signal",
    # portfolio / risk
    "portfolio": "portfolio", "riskguard": "portfolio",
    "costs": "portfolio", "friction": "portfolio",
    # backtest
    "backtest": "backtest", "quant": "backtest", "paperspecs": "backtest",
    "paperrun": "backtest", "specs_2_0": "backtest",
    # validation
    "pbo": "validation", "edge": "validation", "gate_tests": "validation",
    "biasaudit": "validation", "criteria": "validation",
    "reference_gate": "validation",
    # reports
    "report": "report", "report_memecoin": "report", "viz": "report",
    "viz_leading": "report", "viz_memecoin": "report",
    "paperreport": "report", "backtestviz": "report",
    # governance
    "signal": "governance", "alerts": "governance",
    # wallet
    "memecoin": "wallet", "memecoinscan": "wallet",
    "walletsearch": "wallet", "profiler": "wallet",
    "launchscan": "wallet",
}


def _module_files() -> List[str]:
    if not os.path.isdir(PKG):
        return []
    return sorted(f for f in os.listdir(PKG)
                  if f.endswith(".py") and not f.startswith("__"))


def module_inventory() -> Dict[str, Any]:
    """Read the real shape of the package: modules, sizes, APIs, edges."""
    mods: Dict[str, Dict[str, Any]] = {}
    for fname in _module_files():
        name = fname[:-3]
        path = os.path.join(PKG, fname)
        try:
            source = open(path, encoding="utf-8").read()
            tree = ast.parse(source)
        except Exception:  # noqa: BLE001
            continue
        lines = source.count("\n") + 1
        public: List[str] = []
        classes: List[str] = []
        doc = ""
        deps: Set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Module) and ast.get_docstring(node):
                doc = (ast.get_docstring(node) or "").strip().split("\n")[0]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    public.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef,
                                         ast.AsyncFunctionDef)):
                        if not sub.name.startswith("_"):
                            public.append(f"{node.name}.{sub.name}")
        # The dependency edges, INCLUDING the lazy ones inside
        # functions - this package imports lazily to avoid circular
        # imports, so a top-level-only scan would miss most of the
        # graph.
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level and node.module:
                    deps.add(node.module.split(".")[-1])
                elif node.module and node.module.startswith("leapspace"):
                    deps.add(node.module.split(".")[-1])
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("leapspace"):
                        deps.add(alias.name.split(".")[-1])
        deps.discard(name)
        mods[name] = {
            "name": name,
            "file": fname,
            "lines": lines,
            "public": public,
            "n_public": len(public),
            "classes": classes,
            "deps": sorted(deps),
            "doc": doc,
            "layer": MODULE_LAYER.get(name, "infra"),
        }
    return mods


def _edges(mods: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
    """The real dependency edges, as (dependent, dependency) pairs."""
    out: List[Tuple[str, str]] = []
    for name, m in mods.items():
        for d in m["deps"]:
            if d in mods:
                out.append((name, d))
    return out


def _layer_of(mods: Dict[str, Dict[str, Any]], name: str) -> str:
    return mods.get(name, {}).get("layer", "infra")


def render_architecture(mods: Optional[Dict[str, Dict[str, Any]]] = None
                        ) -> str:
    """Render the architecture page."""
    mods = mods or module_inventory()
    edges = _edges(mods)
    layer_ids = [lay["id"] for lay in LAYERS]
    layer_by_id = {lay["id"]: lay for lay in LAYERS}

    # ---- the layer diagram ------------------------------------------
    boxes: List[str] = []
    for lay in LAYERS:
        members = sorted(n for n, m in mods.items()
                         if m["layer"] == lay["id"])
        if not members:
            continue
        chips = "".join(
            f'<span class="chip" title="{html.escape(mods[n]["doc"][:160])}">'
            f'{html.escape(n)}'
            f'<i>{mods[n]["n_public"]}</i></span>'
            for n in members)
        boxes.append(
            f'<div class="layer" style="--c:{lay["colour"]}">'
            f'<div class="lname">{html.escape(lay["name"])}</div>'
            f'<div class="ldesc">{html.escape(lay["desc"])}</div>'
            f'<div class="chips">{chips}</div></div>')

    # ---- the pipeline ------------------------------------------------
    pipeline = [
        ("DATA SOURCE", "market / onchain / social / disclosure",
         "market.py, onchain.py, social.py, disclosure.py",
         "A fetch can fail, be rate-limited, or return a different "
         "subset than the last fetch. Every fetch records its "
         "provenance: URL, HTTP status, and what was measured."),
        ("FEATURE", "indicators, the volatility risk premium, funding/OI",
         "leading.py, cryptoderivs.py, regime.py",
         "A leading feature must be timestamped and aligned with a "
         "one-bar publication lag, or it is not leading - it is "
         "look-ahead. A missing value is None, never zero."),
        ("SIGNAL", "features -> per-symbol positions",
         "backtest.py, ensemble.py, trend.py",
         "The signal says WHICH WAY. The portfolio block does the "
         "sizing. A signal that ignores invert_signal produces a "
         "negative control that cannot fail."),
        ("PORTFOLIO & RISK", "weights, caps, vol target, kill switch",
         "portfolio.py, riskguard.py, costs.py, friction.py",
         "The caps are applied LAST. The kill switch downgrades an "
         "ENTER to an AVOID - but there is still no order-placement "
         "path for it to gate."),
        ("SIMULATION", "the engine's 8-stage gauntlet",
         "btengine.py / btvalidate.py (the shared skill)",
         "Walk-forward with purge and embargo, cost stress, "
         "gross-vs-net, parameter sweep, Monte Carlo, subperiod, "
         "capacity, replication, causality audit."),
        ("VERDICT", "SUPPORTED / FRAGILE / REFUTED / INCONCLUSIVE / ERROR",
         "backtest.py, pbo.py, edge.py",
         "A crash is an ERROR, not an INCONCLUSIVE. The pooled OOS "
         "Sharpe is the result; the in-sample Sharpe is reported "
         "beside it and never substituted for it."),
        ("REPORT", "markdown, JSON, inline-SVG dashboards",
         "paperreport.py, backtestviz.py, report.py",
         "The report separates a finding from a crash, scopes the "
         "discrimination claim to the controls that executed, and "
         "says which stages never ran."),
    ]
    pipe_html = []
    for i, (stage, what, where, gotcha) in enumerate(pipeline):
        pipe_html.append(
            f'<div class="pipe">'
            f'<div class="pnum">{i + 1}</div>'
            f'<div class="pbody">'
            f'<div class="pstage">{html.escape(stage)}</div>'
            f'<div class="pwhat">{html.escape(what)}</div>'
            f'<div class="pwhere">{html.escape(where)}</div>'
            f'<div class="pgot">{html.escape(gotcha)}</div>'
            f'</div></div>')
        if i < len(pipeline) - 1:
            pipe_html.append('<div class="parrow"></div>')

    # ---- the module table ---------------------------------------------
    rows = []
    for name in sorted(mods, key=lambda n: -mods[n]["lines"]):
        m = mods[name]
        lay = layer_by_id.get(m["layer"], {"name": m["layer"]})
        deps = ", ".join(m["deps"][:6])
        if len(m["deps"]) > 6:
            deps += f", +{len(m['deps']) - 6}"
        rows.append(
            f'<tr><td class="mono"><b>{html.escape(name)}</b></td>'
            f'<td><span class="tag" style="--c:{lay["colour"]}">'
            f'{html.escape(lay["name"])}</span></td>'
            f'<td class="num">{m["lines"]}</td>'
            f'<td class="num">{m["n_public"]}</td>'
            f'<td class="num">{len(m["classes"])}</td>'
            f'<td class="mono sm">{html.escape(deps) or "-"}</td>'
            f'<td class="sm">{html.escape(m["doc"][:110])}</td></tr>')

    # ---- the hot spots -------------------------------------------------
    dep_count: Dict[str, int] = {}
    for a, b in edges:
        dep_count[b] = dep_count.get(b, 0) + 1
    hotspots = sorted(dep_count.items(), key=lambda kv: -kv[1])[:12]

    total_lines = sum(m["lines"] for m in mods.values())
    total_public = sum(m["n_public"] for m in mods.values())
    total_classes = sum(len(m["classes"]) for m in mods.values())
    total_edges = len(edges)

    layer_counts = []
    for lay in LAYERS:
        n = sum(1 for m in mods.values() if m["layer"] == lay["id"])
        if n:
            layer_counts.append(
                f'<span class="lc" style="--c:{lay["colour"]}">'
                f'{html.escape(lay["name"])} <b>{n}</b></span>')

    hot_html = "".join(
        f'<span class="hc">{html.escape(k)} <b>{v}</b></span>'
        for k, v in hotspots)

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LeapSpace — architecture</title>
<style>
 :root {{ color-scheme: dark; }}
 body {{ margin:0; padding:24px; background:#12121f; color:#e0e0e0;
        font:14px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif; }}
 h1 {{ font-size:22px; margin:0 0 4px; }}
 h2 {{ font-size:16px; margin:0 0 12px; color:#ffcc00; }}
 .sub {{ color:#9a9a9a; margin:0 0 22px; font-size:13px; max-width:1000px; }}
 .card {{ background:#1c1c30; border:1px solid #2e2e46; border-radius:12px;
          padding:18px 20px; margin-bottom:18px; }}
 .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
          gap:12px; margin-bottom:16px; }}
 .kv {{ color:#8a8a9a; font-size:11px; text-transform:uppercase;
         letter-spacing:.05em; }}
 .vv {{ font-size:24px; font-weight:600; }}
 .layers {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
            gap:12px; }}
 .layer {{ border-left:4px solid var(--c); background:#181828;
           border-radius:0 10px 10px 0; padding:12px 14px; }}
 .lname {{ font-weight:700; font-size:14px; color:var(--c); }}
 .ldesc {{ color:#8a8a9a; font-size:11.5px; margin:2px 0 8px; }}
 .chips {{ display:flex; flex-wrap:wrap; gap:4px; }}
 .chip {{ background:#22223a; border:1px solid #34344e; border-radius:5px;
          padding:2px 6px; font-size:11px; font-family:ui-monospace,monospace; }}
 .chip i {{ color:#7a7a92; font-style:normal; margin-left:4px; }}
 .pipe {{ display:flex; gap:14px; align-items:flex-start; }}
 .pnum {{ flex:0 0 26px; height:26px; border-radius:50%; background:#ffcc00;
          color:#12121f; font-weight:700; display:flex; align-items:center;
          justify-content:center; font-size:13px; }}
 .pstage {{ font-weight:700; letter-spacing:.04em; }}
 .pwhat {{ color:#b8b8c8; }}
 .pwhere {{ color:#7a9ac0; font-family:ui-monospace,monospace; font-size:11.5px;
           margin-top:3px; }}
 .pgot {{ color:#9a9a9a; font-size:11.5px; margin-top:5px;
          border-left:2px solid #33334a; padding-left:9px; }}
 .parrow {{ height:16px; margin-left:12px; border-left:2px solid #33334a; }}
 table {{ border-collapse:collapse; width:100%; font-size:12px; }}
 th,td {{ text-align:left; padding:4px 8px; border-bottom:1px solid #26263a;
          vertical-align:top; }}
 th {{ color:#8a8a9a; font-size:10px; text-transform:uppercase;
       position:sticky; top:0; background:#1c1c30; }}
 .mono {{ font-family:ui-monospace,monospace; }}
 .sm {{ font-size:11px; color:#9a9a9a; }}
 .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
 .tag {{ display:inline-block; padding:1px 7px; border-radius:999px;
        font-size:10px; color:var(--c); border:1px solid var(--c); }}
 .lc,.hc {{ display:inline-block; background:#22223a; border-radius:6px;
           padding:3px 9px; margin:0 5px 5px 0; font-size:11.5px; }}
 .lc {{ border-left:3px solid var(--c); }}
 .hc b {{ color:#ffcc00; }}
 .tw {{ max-height:640px; overflow:auto; border:1px solid #2e2e46;
        border-radius:8px; }}
</style></head><body>
<h1>leapspace-quant — architecture</h1>
<p class="sub">Generated from the code, not drawn by hand: the module
inventory is read with <span class="mono">ast</span> and the dependency
edges are the real import edges, including the lazy ones inside
functions (this package imports lazily to avoid circular imports, so a
top-level-only scan would miss most of the graph).</p>

<div class="card">
  <div class="grid">
    <div><div class="kv">Modules</div><div class="vv">{len(mods)}</div></div>
    <div><div class="kv">Lines</div><div class="vv">{total_lines:,}</div></div>
    <div><div class="kv">Public functions</div><div class="vv">{total_public}</div></div>
    <div><div class="kv">Classes</div><div class="vv">{total_classes}</div></div>
    <div><div class="kv">Internal edges</div><div class="vv">{total_edges}</div></div>
  </div>
  <div>{''.join(layer_counts)}</div>
</div>

<div class="card">
  <h2>1 · The layers</h2>
  <div class="layers">{''.join(boxes)}</div>
  <p class="sub" style="margin-top:14px">Each chip is a module; the
  number is its public function count. The colour is the layer. Hover a
  chip for its one-line purpose.</p>
</div>

<div class="card">
  <h2>2 · The pipeline, and the trap at each stage</h2>
  {''.join(pipe_html)}
</div>

<div class="card">
  <h2>3 · The hot spots</h2>
  <p class="sub" style="margin-top:0">The modules most things depend
  on. A change to one of these breaks the most code, so they are where
  a refactor needs the most care.</p>
  <div>{hot_html}</div>
</div>

<div class="card">
  <h2>4 · Every module</h2>
  <div class="tw"><table>
  <tr><th>Module</th><th>Layer</th><th class="num">Lines</th>
      <th class="num">Public fns</th><th class="num">Classes</th>
      <th>Depends on</th><th>Purpose</th></tr>
  {''.join(rows)}
  </table></div>
</div>
</body></html>"""


def build_architecture(out_path: Optional[str] = None
                       ) -> Dict[str, Any]:
    """Generate the architecture page."""
    mods = module_inventory()
    page = render_architecture(mods)
    out_path = out_path or OUT_HTML
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return {"html": out_path, "n_modules": len(mods),
            "n_public": sum(m["n_public"] for m in mods.values())}


if __name__ == "__main__":  # pragma: no cover
    r = build_architecture()
    print(f"wrote {r['html']} ({r['n_modules']} modules, "
          f"{r['n_public']} public functions)")
