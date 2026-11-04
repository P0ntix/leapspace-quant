"""Generate the complete technical function reference from the code.

WHAT THIS DOES
    Walks every module in `leapspace/` with `ast` and writes
    `reports/TECHNICAL_FUNCTION_REFERENCE.md`: every module, its
    purpose, its layer, every public function and class with its
    signature, its dependencies, and the traps a reader would
    otherwise fall into.

WHY IT IS GENERATED
    A hand-written function reference is wrong the moment the code
    changes, and wrong in a way nobody notices. This one is read out
    of the source, so it cannot drift.

THE CURATED PART
    The "notable gotcha" for the modules that have one is written by
    hand in `GOTCHAS` below, because a gotcha is a piece of knowledge
    that is not in the code - it is what the code does NOT say. The
    rest is derived.
"""
from __future__ import annotations

import ast
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "leapspace")
OUT = os.path.join(ROOT, "reports", "TECHNICAL_FUNCTION_REFERENCE.md")

# The package is not installed; it is imported from the repository.
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from leapspace.archviz import LAYERS, MODULE_LAYER  # noqa: E402

LAYER_BY_ID = {lay["id"]: lay for lay in LAYERS}


#: The traps. A gotcha is what the code does NOT say, so it cannot be
#: derived - it has to be written down.
GOTCHAS: Dict[str, str] = {
    "backtest":
        "The engine's `base` block is the IN-SAMPLE run and its "
        "`sharpe` is the in-sample Sharpe; the pooled OUT-OF-SAMPLE "
        "Sharpe lives on the walk-forward block as `oos_sharpe`. Never "
        "let one fall through to the other. A crash is an ERROR, not an "
        "INCONCLUSIVE. Every signal must read `invert_signal` or its "
        "negative control is a no-op that cannot fail. `register_"
        "extensions` injects into the SHARED skill's registries, so a "
        "signal type rename can change the engine's behaviour "
        "silently (the exact-string test in the conviction-ranking "
        "branch).",
    "leading":
        "`align_to_bars` is the no-look-ahead rule: a bar at T may only "
        "use a measurement published before T. `dvol_history` must be "
        "paged at DAILY resolution - the endpoint caps each call at "
        "1,000 points, so hourly resolution covers ~41 days and would "
        "leave most of a multi-year panel with no leading input. A "
        "missing value is None, never zero.",
    "leadingcache":
        "`series_for_panel` resolves the leading source from the "
        "universe PRESET, and the cache key must include the source and "
        "asset - a cached BTC series served to an equity panel would "
        "be a silent corruption.",
    "cryptoderivs":
        "Funding and open interest are VENUE-SPECIFIC: Bybit's open "
        "interest is not Binance's, and neither is the whole market. "
        "Compare within a venue. A funding rate is published at the END "
        "of its interval, so the alignment uses the same one-bar "
        "publication lag as every other leading series.",
    "portfolio":
        "The risk-parity update must work on risk SHARES, which are "
        "scale-invariant, not absolute contributions, which are not - "
        "the absolute form fights the renormalisation and never "
        "converges. The risk contributions are divided by Sigma "
        "SQUARED so they sum to 1 and read as a share of risk. The "
        "caps are applied LAST; anything upstream that scales the book "
        "must not be able to undo them.",
    "ensemble":
        "`rank_floor` is a FLOOR: raising it makes the book MORE "
        "selective. It is applied to the MEAN rank of the members that "
        "AGREE, not to the most extreme rank across all members - a "
        "name that is top-ranked on a member voting the other way is "
        "not evidence for the position.",
    "trend":
        "`sig_trend_long_short` is the paper's rule with BOTH legs live; "
        "the engine's own `time_series_threshold` only goes long OR "
        "short, never both. The pairs signal selects its pairs from "
        "the panel by spread stability, and the z-score is measured "
        "over a TRAILING window - a whole-sample z-score would be "
        "look-ahead.",
    "paperspecs":
        "Every spec carries the CONSTANT risk block so a difference in "
        "the result is attributable to the market and not to the "
        "bookkeeping. `_make` sets that block; a spec must NOT pass "
        "its own `portfolio` argument.",
    "paperrun":
        "`merge_results` merges BY NAME under an exclusive lock. A "
        "read-modify-write without the lock is a lost-update race, and "
        "with parallel workers that silently drops rows. The row's "
        "`oos_sharpe` comes from the walk-forward block - never from "
        "`base['sharpe']`, which is the in-sample number.",
    "backtestviz":
        "The OOS return series come from the RAW SCORECARDS, not the "
        "results file - the results file never carried them. The paths "
        "are downsampled for rendering, keeping the first and last "
        "exactly, because a 4,290-bar polyline per series made a "
        "megabyte of SVG for no visual gain.",
    "paperreport":
        "The report separates a FINDING from a CRASH. A spec whose "
        "signal never fired produced zero trades and a null Sharpe; "
        "that is a real result, not a crash, and the detector "
        "distinguishes them by the presence of an `errors` entry.",
    "quant":
        "The friction-aware simulator. `TradeRecord` and `RugEvent` are "
        "DATACLASSES, so field access is `getattr`, not `.get()`; the "
        "skipped-trade reason lives on the nested `trade` object, not "
        "on the outer record. Statistics are written to `stderr` so "
        "`--json` stdout stays parseable.",
    "signal":
        "`assess_trade` consults the persisted kill switch and "
        "downgrades an ENTER to an AVOID. There is NO order-placement "
        "path anywhere in the package, so the brake cannot yet stop a "
        "real order - it gates a decision, not a trade.",
    "riskguard":
        "`KillSwitch` persists a halt state. A halt is authoritative: "
        "it blocks ENTER and the reason is surfaced, not swallowed.",
    "edge":
        "The consistency gate. A wallet that scored FLUKE has not "
        "passed - the gate distinguishes a repeatable edge from one "
        "lucky trade, and all fifteen PEPE top-holder wallets have "
        "scored FLUKE.",
    "pbo":
        "Probability of Backtest Overfitting. The CSCV combination "
        "count must be computed from the ACTUAL fold geometry; an "
        "empty return series silently yields a PBO of zero, which "
        "reads as a pass.",
    "http":
        "The SYSTEM CA store mis-validates Let's Encrypt chains on this "
        "host, so `ssl.create_default_context()` fails. `requests` and "
        "`certifi` work. The SSL context is built once from certifi.",
    "provenance":
        "The single chokepoint for credential redaction. Every fetch "
        "records its URL, HTTP status and what was measured, and every "
        "credential-shaped string is stripped before it reaches an "
        "artefact.",
    "friction":
        "The cost model. Costs are stressed to 2x the engine default "
        "in the paper matrix, which is what separates 'real but "
        "untradeable at this size' from 'no edge at all'.",
    "costs":
        "The cost model the friction module and the price-at-block "
        "tools share.",
    "regime":
        "The HMM is a FILTER, not a smoother - smoothing uses the "
        "future and would be look-ahead. The parameters are fitted on "
        "the whole panel, so the regime CLASSIFICATION is in-sample; "
        "that is disclosed in every report that uses it.",
    "gamma":
        "The dealer side of the gamma exposure is INFERRED from open "
        "interest, which does not reveal who holds the option. The "
        "magnitude is indicative; the SIGN and the RELATIVE magnitude "
        "across expiries carry the information. Open interest is stale.",
    "memecoin":
        "The memecoin screen. Prices are taken AT THE BLOCK, so a "
        "token that moved after the wallet bought it is not scored on "
        "a price the wallet never saw.",
    "launchscan":
        "The launch window is found with a BOUNDED `eth_getLogs` query "
        "over `[launch_block, launch_block + window]`, not by paging an "
        "established token's whole history. Public RPC providers can "
        "return DIFFERENT SUBSETS of the same range, so provider "
        "provenance is recorded and subsets are never merged.",
    "reportvalidate":
        "The pre-flight report validator. It finds known defect "
        "classes; it does NOT claim a report is correct. A clean "
        "result means only that the implemented checks found nothing.",
    "models":
        "The shared dataclasses. A field that was not measured is "
        "`None`, never `0` - a zero means something different from a "
        "missing value and the difference has caused silent wrong "
        "numbers.",
}


def _sig(node: ast.AST) -> str:
    """A readable signature for a function or a method."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ""
    try:
        args = ast.unparse(node.args)
    except Exception:  # noqa: BLE001
        args = "..."
    ret = ""
    if node.returns is not None:
        try:
            ret = " -> " + ast.unparse(node.returns)
        except Exception:  # noqa: BLE001
            ret = ""
    star = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{star}{node.name}({args}){ret}"


def _first_line(doc: Optional[str]) -> str:
    if not doc:
        return ""
    return doc.strip().split("\n")[0].strip()


def _module_doc(tree: ast.Module) -> str:
    doc = ast.get_docstring(tree) or ""
    return doc.strip()


def build_reference() -> Dict[str, Any]:
    """Walk the package and build the reference."""
    mods: Dict[str, Dict[str, Any]] = {}
    for fname in sorted(os.listdir(PKG)):
        if not fname.endswith(".py") or fname.startswith("__"):
            continue
        name = fname[:-3]
        path = os.path.join(PKG, fname)
        try:
            source = open(path, encoding="utf-8").read()
            tree = ast.parse(source)
        except Exception:  # noqa: BLE001
            continue

        funcs: List[Dict[str, Any]] = []
        classes: List[Dict[str, Any]] = []
        deps: set = set()
        consts: List[str] = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    funcs.append({
                        "name": node.name,
                        "sig": _sig(node),
                        "doc": _first_line(ast.get_docstring(node)),
                        "async": isinstance(node, ast.AsyncFunctionDef),
                    })
            elif isinstance(node, ast.ClassDef):
                methods = []
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef,
                                         ast.AsyncFunctionDef)):
                        if not sub.name.startswith("_"):
                            methods.append({
                                "name": sub.name,
                                "sig": _sig(sub),
                                "doc": _first_line(ast.get_docstring(sub)),
                            })
                classes.append({
                    "name": node.name,
                    "doc": _first_line(ast.get_docstring(node)),
                    "bases": [ast.unparse(b) for b in node.bases],
                    "methods": methods,
                })
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id.isupper():
                        try:
                            consts.append(f"{t.id} = "
                                          f"{ast.unparse(node.value)[:70]}")
                        except Exception:  # noqa: BLE001
                            consts.append(t.id)

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
            "lines": source.count("\n") + 1,
            "doc": _module_doc(tree),
            "funcs": funcs,
            "classes": classes,
            "consts": consts,
            "deps": sorted(deps),
            "layer": MODULE_LAYER.get(name, "infra"),
        }
    return mods


def render_reference(mods: Dict[str, Dict[str, Any]]) -> str:
    out: List[str] = []
    out.append("# TECHNICAL FUNCTION REFERENCE — leapspace-quant\n")
    out.append("**Generated from the code** by "
               "`tools/build_function_reference.py`. A hand-written "
               "function reference is wrong the moment the code "
               "changes, and wrong in a way nobody notices. This one is "
               "read out of the source with `ast`, so it cannot "
               "drift.\n")
    out.append("**Measured:** "
               f"{len(mods)} modules, "
               f"{sum(m['lines'] for m in mods.values()):,} lines, "
               f"{sum(len(m['funcs']) for m in mods.values())} module-level "
               f"public functions, "
               f"{sum(len(c['methods']) for m in mods.values() for c in m['classes'])} "
               f"public methods, "
               f"{sum(len(m['classes']) for m in mods.values())} "
               "classes.\n")
    out.append("**The gotchas are curated, not derived.** A gotcha is a "
               "piece of knowledge that is not *in* the code - it is "
               "what the code does NOT say. Those entries are written "
               "by hand; everything else is read out of the "
               "source.\n")
    out.append("---\n")
    out.append("## Contents\n")
    out.append("")

    by_layer: Dict[str, List[str]] = {}
    for name, m in mods.items():
        by_layer.setdefault(m["layer"], []).append(name)

    for lay in LAYERS:
        names = sorted(by_layer.get(lay["id"], []))
        if not names:
            continue
        out.append(f"### {lay['name']}\n")
        out.append("| Module | Lines | Public fns | Classes | "
                   "Depends on |")
        out.append("|---|---|---|---|---|")
        for n in names:
            m = mods[n]
            deps = ", ".join(f"`{d}`" for d in m["deps"][:5]) or "—"
            if len(m["deps"]) > 5:
                deps += f", +{len(m['deps']) - 5}"
            out.append(f"| [`{n}`](#{n}) | {m['lines']} | "
                       f"{len(m['funcs'])} | {len(m['classes'])} | "
                       f"{deps} |")
        out.append("")

    out.append("---\n")
    out.append("## The modules\n")

    for lay in LAYERS:
        names = sorted(by_layer.get(lay["id"], []))
        if not names:
            continue
        out.append(f"# {lay['name']}\n")
        out.append(f"_{lay['desc']}_\n")
        for n in names:
            m = mods[n]
            out.append(f"<a id=\"{n}\"></a>")
            out.append(f"## `{n}.py`\n")
            if m["doc"]:
                first = m["doc"].split("\n\n")[0]
                out.append(first.strip() + "\n")
            out.append(f"*{m['lines']} lines · "
                       f"{len(m['funcs'])} public functions · "
                       f"{len(m['classes'])} classes · layer: "
                       f"{LAYER_BY_ID.get(m['layer'], {}).get('name', m['layer'])}*\n")
            if m["deps"]:
                out.append("**Depends on:** "
                           + ", ".join(f"`{d}`" for d in m["deps"]) + "\n")
            if m["consts"]:
                out.append("**Module constants:**\n")
                out.append("```python")
                for c in m["consts"][:12]:
                    out.append(c)
                if len(m["consts"]) > 12:
                    out.append(f"# ... and {len(m['consts']) - 12} more")
                out.append("```\n")
            if m["funcs"]:
                out.append("**Functions**\n")
                out.append("```python")
                for f in m["funcs"]:
                    out.append(f"def {f['sig']}")
                out.append("```\n")
                for f in m["funcs"]:
                    if f["doc"]:
                        out.append(f"- `{f['name']}` — {f['doc']}")
                if any(f["doc"] for f in m["funcs"]):
                    out.append("")
            if m["classes"]:
                out.append("**Classes**\n")
                for c in m["classes"]:
                    base = (f"({', '.join(c['bases'])})"
                            if c["bases"] else "")
                    out.append(f"### `class {c['name']}{base}`\n")
                    if c["doc"]:
                        out.append(c["doc"] + "\n")
                    if c["methods"]:
                        out.append("```python")
                        for meth in c["methods"]:
                            out.append(f"def {meth['sig']}")
                        out.append("```\n")
                        for meth in c["methods"]:
                            if meth["doc"]:
                                out.append(f"- `{meth['name']}` — "
                                           f"{meth['doc']}")
                        out.append("")
            if n in GOTCHAS:
                out.append("> **Gotcha.** " + GOTCHAS[n] + "\n")
            out.append("---\n")

    return "\n".join(out)


def main() -> int:
    mods = build_reference()
    text = render_reference(mods)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    mod_level = sum(len(m["funcs"]) for m in mods.values())
    methods = sum(len(c["methods"]) for m in mods.values()
                   for c in m["classes"])
    print(f"wrote {OUT}")
    print(f"  {len(mods)} modules, {mod_level} module-level public "
          f"functions, {methods} public methods, "
          f"{sum(len(m['classes']) for m in mods.values())} classes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
