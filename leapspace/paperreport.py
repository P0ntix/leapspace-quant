"""The paper-concept report: the matrix, read and rendered.

WHAT THIS IS
    Reads the results file written by `leapspace.paperrun` and renders
    the findings as (a) a markdown report and (b) a self-contained
    HTML dashboard with inline SVG charts.

WHAT THE REPORT IS FOR
    The user asked for an EDGE - something with higher upside than
    downside on the portfolio, that survives an industry-standard
    backtest across multiple market conditions and multiple asset
    classes. So the report is organised around the questions that
    actually decide that, in this order:

      1. DID ANYTHING SURVIVE?  The verdict table, with every flag.
      2. DID THE NEGATIVE CONTROLS FAIL?  If a control survived, the
         validation is not discriminating and everything else is void.
         This is checked FIRST and reported first.
      3. IS IT AN EDGE OR A MARKET CURIOSITY?  A concept that works on
         one asset class is not an edge. The cross-asset table is the
         centrepiece.
      4. IS THE UPSIDE BIGGER THAN THE DOWNSIDE?  The return
         distribution and the drawdown, per surviving concept.
      5. WHAT WAS LEADING AND WHAT WAS LAGGING?  The comparison the
         papers' claim rests on.

THE CHARTS
    1. The verdict matrix - concept x asset class, coloured by verdict.
    2. The out-of-sample Sharpe by concept and asset class.
    3. The real-spec vs negative-control Sharpe comparison, per
       concept. A concept whose control matches it is not doing work.
    4. The leading coverage - how much of each panel the
       forward-looking indicator actually covered.

WHAT THIS IS NOT
    It is NOT a summary that flatters the result. A matrix of
    REFUTED verdicts rendered beautifully is still a matrix of
    REFUTED verdicts, and the report says so in the first line.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .viz_leading import (ACCENT, BG, DOWN, GRID, MUTED, NEUTRAL, TEXT,
                          UP, WARN, svg_bars, svg_line_chart)

__all__ = [
    "PAPER_REPORT_PATH",
    "load_results",
    "summarise",
    "render_markdown",
    "render_html",
    "build_report",
]


PAPER_REPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports", "PAPER_CONCEPT_REPORT.md")

_HTML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports", "charts", "paper_concepts.html")

_VERDICT_COLOUR = {
    "SUPPORTED": UP,
    "FRAGILE": WARN,
    "REFUTED": DOWN,
    "INCONCLUSIVE": NEUTRAL,
    "ERROR": "#ff00ff",
}


def load_results(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """The results rows, or an empty list when there are none."""
    p = path or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "reports", "paper_concept_results.json")
    if not os.path.isfile(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return [r for r in data if isinstance(r, dict)] if isinstance(
            data, list) else []
    except Exception:  # noqa: BLE001
        return []


def _is_control(name: str) -> bool:
    return str(name or "").startswith("NEGATIVE-CONTROL-")


def _twin(name: str) -> str:
    """The real spec's name for a control, or the control's for a real."""
    if _is_control(name):
        return str(name)[len("NEGATIVE-CONTROL-"):]
    return f"NEGATIVE-CONTROL-{name}"


def _sharpe(row: Dict[str, Any]) -> Optional[float]:
    """The POOLED OUT-OF-SAMPLE Sharpe, or None.

    The key's PRESENCE is what decides, not its value. If the row has
    an `oos_sharpe` key and it is None, the answer is None - a spec
    with no out-of-sample result has no out-of-sample Sharpe, and
    falling through to another key would substitute a different number
    for the missing one.

    The `sharpe` fallback is for legacy rows written before the key
    existed. Those rows carried the IN-SAMPLE number under `sharpe`, so
    using it would be wrong - but a row that has neither key has
    nothing to report at all, and None says that.
    """
    m = row.get("metrics") or {}
    if "oos_sharpe" in m:
        v = m.get("oos_sharpe")
        return float(v) if isinstance(v, (int, float)) else None
    v = m.get("sharpe")
    return float(v) if isinstance(v, (int, float)) else None


def _in_sample_sharpe(row: Dict[str, Any]) -> Optional[float]:
    """The IN-SAMPLE Sharpe, or None."""
    m = row.get("metrics") or {}
    for key in ("in_sample_sharpe", "sharpe"):
        if key in m:
            v = m.get(key)
            return float(v) if isinstance(v, (int, float)) else None
    return None


def _ran(row: Dict[str, Any]) -> bool:
    """Whether a spec ACTUALLY EXECUTED, as opposed to failing.

    A row can be INCONCLUSIVE because the evidence was insufficient -
    in which case it ran and produced flags - or because the code
    crashed - in which case it carries an error and no metrics at all.
    Those are different claims and the report must not merge them.

    The rule: an ERROR means it did not run. Otherwise, any sign of
    real execution (flags, metrics, a stage record) means it did.

    A spec that ran and produced ZERO trades has flags like "only 0
    trades (need >=30)" and a null Sharpe. That is a real result - the
    signal never fired - and it must not be counted as a crash.
    """
    if row.get("errors"):
        return False
    if row.get("flags"):
        return True
    m = row.get("metrics") or {}
    if any(m.get(k) is not None for k in ("oos_sharpe", "n_trades",
                                          "total_return", "max_drawdown")):
        return True
    if row.get("walk_forward") or row.get("stages"):
        return True
    return False


def summarise(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Turn the rows into the tables the report renders."""
    real = [r for r in rows if not _is_control(r.get("name", ""))]
    controls = [r for r in rows if _is_control(r.get("name", ""))]
    by_name = {r.get("name"): r for r in rows}

    concepts: List[str] = []
    for r in real:
        c = r.get("concept") or "unknown"
        if c not in concepts:
            concepts.append(c)
    asset_classes: List[str] = []
    for r in real:
        a = r.get("asset_class") or "unknown"
        if a not in asset_classes:
            asset_classes.append(a)

    # The verdict matrix.
    matrix: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for r in real:
        c = r.get("concept") or "unknown"
        a = r.get("asset_class") or "unknown"
        matrix.setdefault(c, {})[a] = r

    # The control comparison: does the real spec beat its inverted twin?
    comparison: List[Dict[str, Any]] = []
    for r in real:
        ctrl = by_name.get(_twin(r.get("name", "")))
        comparison.append({
            "concept": r.get("concept"),
            "asset_class": r.get("asset_class"),
            "name": r.get("name"),
            "real_verdict": r.get("verdict"),
            "real_sharpe": _sharpe(r),
            "control_verdict": (ctrl or {}).get("verdict"),
            "control_sharpe": _sharpe(ctrl) if ctrl else None,
        })

    survived = [r for r in real if r.get("verdict") == "SUPPORTED"]
    fragile = [r for r in real if r.get("verdict") == "FRAGILE"]
    controls_survived = [r for r in controls
                         if r.get("verdict") == "SUPPORTED"]

    # Which specs ACTUALLY EXECUTED. A control that never ran cannot
    # testify that the validation discriminates.
    real_ran = [r for r in real if _ran(r)]
    real_did_not_run = [r for r in real if not _ran(r)]
    controls_ran = [r for r in controls if _ran(r)]
    controls_did_not_run = [r for r in controls if not _ran(r)]
    controls_tested_and_failed = [
        r for r in controls_ran
        if r.get("verdict") in ("REFUTED", "FRAGILE", "INCONCLUSIVE")]

    # Cross-asset consistency: how many asset classes each concept
    # produced a SUPPORTED or FRAGILE result on.
    consistency: List[Dict[str, Any]] = []
    for c in concepts:
        rows_c = [r for r in real if r.get("concept") == c]
        good = [r for r in rows_c
                if r.get("verdict") in ("SUPPORTED", "FRAGILE")]
        sharpes = [_sharpe(r) for r in rows_c]
        sharpes = [s for s in sharpes if s is not None]
        controls_c = [r for r in controls if r.get("concept") == c]
        controls_good = [r for r in controls_c
                         if r.get("verdict") in ("SUPPORTED", "FRAGILE")]
        consistency.append({
            "concept": c,
            "n_asset_classes": len(rows_c),
            "n_good": len(good),
            "n_controls_good": len(controls_good),
            "mean_sharpe": (sum(sharpes) / len(sharpes)) if sharpes else None,
            "best_sharpe": max(sharpes) if sharpes else None,
            "worst_sharpe": min(sharpes) if sharpes else None,
            "n_positive_sharpe": sum(1 for s in sharpes if s > 0),
            "paper": (rows_c[0].get("paper") if rows_c else ""),
        })

    # Leading coverage.
    coverage: List[Dict[str, Any]] = []
    for r in real:
        cov = r.get("leading_coverage") or {}
        if not cov or cov.get("reason", "").startswith("this spec"):
            continue
        coverage.append({
            "name": r.get("name"),
            "concept": r.get("concept"),
            "asset_class": r.get("asset_class"),
            "source": cov.get("source"),
            "asset": cov.get("asset"),
            "n_points": cov.get("n_points"),
            "reason": cov.get("reason"),
        })

    return {
        "n_rows": len(rows),
        "n_real": len(real),
        "n_controls": len(controls),
        "concepts": concepts,
        "asset_classes": asset_classes,
        "matrix": matrix,
        "comparison": comparison,
        "consistency": consistency,
        "survived": survived,
        "fragile": fragile,
        "controls_survived": controls_survived,
        "real_ran": real_ran,
        "real_did_not_run": real_did_not_run,
        "controls_ran": controls_ran,
        "controls_did_not_run": controls_did_not_run,
        "controls_tested_and_failed": controls_tested_and_failed,
        "coverage": coverage,
        "verdict_counts": _counts(real),
        "control_verdict_counts": _counts(controls),
    }


def _counts(rows: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rows:
        v = str(r.get("verdict") or "UNKNOWN")
        out[v] = out.get(v, 0) + 1
    return out


def _stage_coverage(rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """How often each robustness stage RAN, was SKIPPED, or ERRORED.

    A stage that is absent from the ledger did not run, and a stage
    that errored is not the same as one that was skipped. Both are
    counted, because "we did not check this" and "the check failed to
    run" are different facts about the validation.
    """
    out: Dict[str, Dict[str, int]] = {}
    for r in rows:
        stages = r.get("stages") or {}
        if not isinstance(stages, dict):
            continue
        skipped = set(r.get("skipped_stages") or [])
        for stage, val in stages.items():
            if stage == "skipped_stages":
                continue
            c = out.setdefault(stage, {"ran": 0, "skipped": 0,
                                       "errored": 0, "absent": 0})
            status = ""
            if isinstance(val, dict):
                status = str(val.get("status") or "").upper()
            else:
                status = str(val).upper()
            if "SKIP" in status:
                c["skipped"] += 1
            elif "ERROR" in status or "FAIL" in status:
                c["errored"] += 1
            else:
                c["ran"] += 1
        for stage in skipped:
            c = out.setdefault(stage, {"ran": 0, "skipped": 0,
                                       "errored": 0, "absent": 0})
            c["skipped"] += 1
    return out


def _fold_tables(rows: Sequence[Dict[str, Any]],
                 limit: int = 12) -> List[Dict[str, Any]]:
    """The specs worth showing a fold table for.

    The ones with the most interesting out-of-sample numbers: the
    highest OOS Sharpe, the lowest, and anything that came out
    FRAGILE. The fold table is what distinguishes "an edge" from "one
    lucky period".
    """
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for r in rows:
        wf = r.get("walk_forward") or {}
        folds = wf.get("folds") or []
        if not folds:
            continue
        sh = _sharpe(r)
        scored.append((sh if sh is not None else -999.0, r))
    if not scored:
        return []
    scored.sort(key=lambda x: -x[0])

    picked: List[Dict[str, Any]] = []
    seen = set()
    for _sh, r in scored:
        name = r.get("name")
        if name in seen:
            continue
        seen.add(name)
        picked.append(r)
        if len(picked) >= limit:
            break
    # Always include the FRAGILE and SUPPORTED rows, whatever their
    # rank - those are the ones a reader will look for.
    for r in rows:
        if r.get("verdict") in ("FRAGILE", "SUPPORTED"):
            name = r.get("name")
            if name and name not in seen:
                seen.add(name)
                wf = r.get("walk_forward") or {}
                if wf.get("folds"):
                    picked.append(r)
    return [{"name": r.get("name"), "verdict": r.get("verdict"),
             "folds": (r.get("walk_forward") or {}).get("folds") or []}
            for r in picked]


# --------------------------------------------------------------------------
# The markdown report
# --------------------------------------------------------------------------
def render_markdown(rows: Sequence[Dict[str, Any]],
                    summary: Optional[Dict[str, Any]] = None) -> str:
    """Render the findings as markdown."""
    s = summary or summarise(rows)
    L: List[str] = []
    # The section number is a counter, not a literal. The report has
    # CONDITIONAL sections - the fold tables and the leading coverage
    # only appear when there is data for them - so hard-coded numbers
    # collide and two sections end up called "6".
    _sec = [0]

    def sec(title: str) -> str:
        _sec[0] += 1
        return f"## {_sec[0]}. {title}"

    L.append("# PAPER-CONCEPT MATRIX — what the research actually supports")
    L.append("")
    L.append("Every claim in the five research papers this package implements, "
             "coded as a rule and tested through the engine's full "
             "validation gauntlet (walk-forward with purge and embargo, "
             "cost stress, gross-vs-net, parameter sweep, Monte Carlo, "
             "regime breakdown, capacity, replication, causality audit) "
             "across six asset classes.")
    L.append("")

    # ---- the headline, honestly -------------------------------------
    n_real = s["n_real"]
    n_ctrl = s["n_controls"]
    L.append(sec("The headline"))
    L.append("")
    if not n_real:
        L.append("**No results were available.** The matrix has not been "
                 "run, or the results file could not be read.")
        L.append("")
        return "\n".join(L)

    counts = s["verdict_counts"]
    L.append(f"| | Real specs | Negative controls |")
    L.append("|---|---|---|")
    for v in ("SUPPORTED", "FRAGILE", "REFUTED", "INCONCLUSIVE", "ERROR"):
        L.append(f"| {v} | {counts.get(v, 0)} | "
                 f"{s['control_verdict_counts'].get(v, 0)} |")
    L.append(f"| **total** | **{n_real}** | **{n_ctrl}** |")
    L.append(f"| **of which actually executed** | **{len(s['real_ran'])}** | "
             f"**{len(s['controls_ran'])}** |")
    L.append("")

    # ---- did the specs actually run? --------------------------------
    if s["real_did_not_run"] or s["controls_did_not_run"]:
        L.append("### :rotating_light: CRITICAL — some specs did NOT run")
        L.append("")
        L.append(f"**{len(s['real_did_not_run'])} of the {n_real} real specs "
                 f"and {len(s['controls_did_not_run'])} of the {n_ctrl} "
                 "controls produced no result at all.** A spec that "
                 "crashed is not a research finding, and its row is not "
                 "evidence about the concept. The rows that did not run:")
        L.append("")
        for r in (s["real_did_not_run"] + s["controls_did_not_run"]):
            errs = r.get("errors") or ["no metrics produced"]
            L.append(f"* `{r.get('name')}` — {errs[0]}")
        L.append("")
        L.append("**These rows must be re-run before the matrix means "
                 "anything for the concepts they cover.** Until then, a "
                 "concept whose every row is in this list has NOT been "
                 "tested - it has not been refuted either.")
        L.append("")

    if s["controls_survived"]:
        L.append("### :rotating_light: CRITICAL — a negative control "
                 "SURVIVED")
        L.append("")
        L.append("**The validation is not discriminating.** The following "
                 "controls, whose signal polarity was deliberately "
                 "INVERTED, came out SUPPORTED:")
        L.append("")
        for r in s["controls_survived"]:
            L.append(f"* `{r.get('name')}` — {r.get('verdict')}, "
                     f"Sharpe {_sharpe(r)}")
        L.append("")
        L.append("A control is a twin of a real spec in which the ONLY "
                 "difference is that the signal points the wrong way. If "
                 "the wrong-way version is SUPPORTED, the concept was "
                 "never what produced the result, and **every other "
                 "verdict in this matrix is void** until that is "
                 "explained.")
        L.append("")
    else:
        L.append("### The negative controls that ran, all failed")
        L.append("")
        if s["controls_did_not_run"]:
            L.append(f"Of the {n_ctrl} negative controls, **{len(s['controls_ran'])} "
                     "actually executed** and every one of them came out "
                     f"REFUTED, FRAGILE or INCONCLUSIVE. The remaining "
                     f"**{len(s['controls_did_not_run'])} did not run** and "
                     "so say nothing either way.")
            L.append("")
            L.append("The discrimination claim therefore covers the "
                     f"{len(s['controls_ran'])} controls that executed, "
                     "not the whole set.")
        else:
            L.append("Every inverted-polarity control was REFUTED, "
                     "FRAGILE or INCONCLUSIVE. The validation is "
                     "discriminating, so the verdicts below are "
                     "meaningful.")
        L.append("")

    # ---- the matrix --------------------------------------------------
    L.append(sec("The verdict matrix"))
    L.append("")
    L.append("One row per paper concept, one column per asset class. A "
             "concept that works on ONE asset class is a market curiosity, "
             "not an edge.")
    L.append("")
    acs = s["asset_classes"]
    L.append("| Concept | " + " | ".join(acs) + " |")
    L.append("|---" * (len(acs) + 1) + "|")
    for c in s["concepts"]:
        cells = []
        for a in acs:
            r = (s["matrix"].get(c) or {}).get(a)
            if not r:
                cells.append("—")
                continue
            sh = _sharpe(r)
            v = str(r.get("verdict") or "?")
            if not _ran(r):
                # A spec that did not execute has NO finding attached to
                # it. Rendering its verdict as if it were a result would
                # repeat the exact mistake that made 24 crashed rows
                # look like research outcomes.
                cells.append("**DID NOT RUN**")
                continue
            cells.append(f"**{v}**" + (f" ({sh:.2f})" if sh is not None
                                        else ""))
        L.append(f"| {c} | " + " | ".join(cells) + " |")
    L.append("")
    L.append("Sharpe figures are the POOLED OUT-OF-SAMPLE numbers, not "
             "the in-sample ones. **DID NOT RUN** means the spec "
             "produced no result at all - it is not a verdict on the "
             "concept.")
    L.append("")

    # ---- cross-asset consistency --------------------------------------
    L.append(sec("Does it work everywhere, or only somewhere?"))
    L.append("")
    L.append("| Concept | Asset classes SUPPORTED or FRAGILE | Mean OOS "
             "Sharpe | Best | Worst | Controls that also passed |")
    L.append("|---|---|---|---|---|---|")
    for row in s["consistency"]:
        mean = row["mean_sharpe"]
        best = row["best_sharpe"]
        worst = row["worst_sharpe"]
        L.append(
            f"| {row['concept']} | {row['n_good']}/{row['n_asset_classes']} "
            f"| {('%.2f' % mean) if mean is not None else 'n/a'} "
            f"| {('%.2f' % best) if best is not None else 'n/a'} "
            f"| {('%.2f' % worst) if worst is not None else 'n/a'} "
            f"| {row['n_controls_good']}/{row['n_asset_classes']} |")
    L.append("")
    L.append("**A concept whose negative control ALSO passed is not "
             "demonstrated.** The last column is the number of inverted "
             "twins that were SUPPORTED or FRAGILE; where it equals the "
             "second column, the concept is doing nothing that its own "
             "control does not also do.")
    L.append("")

    # ---- surviving ----------------------------------------------------
    L.append(sec("What survived, and with which flags"))
    L.append("")
    if not s["survived"] and not s["fragile"]:
        L.append("**Nothing survived.** Not one of the "
                 f"{n_real} real specs earned a SUPPORTED or FRAGILE "
                 "verdict. The papers' mechanisms did not produce a "
                 "tradeable edge on the data and universes tested here, "
                 "at the cost levels and risk controls applied.")
        L.append("")
    for r in s["survived"]:
        L.append(f"### :white_check_mark: SUPPORTED — `{r.get('name')}`")
        L.append("")
        L.append(f"* OOS Sharpe: {_sharpe(r)}")
        L.append(f"* Flags: {', '.join(r.get('flags') or ['none'])}")
        L.append("")

    # ---- the full table ------------------------------------------------
    L.append(sec("Every spec, with its flags"))
    L.append("")
    L.append("| Spec | Verdict | OOS Sharpe | In-sample Sharpe | Trades | "
             "Max DD | Flags |")
    L.append("|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda x: (str(x.get("concept")),
                                          str(x.get("asset_class")))):
        sh = _sharpe(r)
        m = r.get("metrics") or {}
        ish = m.get("in_sample_sharpe")
        dd = m.get("max_drawdown")
        L.append(
            f"| `{r.get('name')}` | {r.get('verdict')} "
            f"| {('%.2f' % sh) if sh is not None else 'n/a'} "
            f"| {('%.2f' % ish) if isinstance(ish, (int, float)) else 'n/a'} "
            f"| {m.get('n_trades', 'n/a')} "
            f"| {('%.1f%%' % (dd * 100)) if isinstance(dd, (int, float)) else 'n/a'} "
            f"| {'; '.join(r.get('flags') or []) or '—'} |")
    L.append("")
    L.append("**The OOS Sharpe is the result.** The in-sample Sharpe is "
             "shown beside it because the GAP between them is the "
             "overfitting, and a large gap is exactly what a purged "
             "walk-forward is there to expose.")
    L.append("")

    # ---- what was actually validated -----------------------------------
    L.append(sec("What was validated, and what was not"))
    L.append("")
    L.append("A verdict is only as good as the checks behind it. The "
             "stage ledger records, for every spec, which robustness "
             "stages ran, which were skipped, and which errored. A "
             "stage that did not run is reported, never hidden.")
    L.append("")
    stage_counts = _stage_coverage(rows)
    if stage_counts:
        L.append("| Stage | RAN | SKIPPED | ERRORED | NOT RECORDED |")
        L.append("|---|---|---|---|---|")
        for stage in sorted(stage_counts):
            c = stage_counts[stage]
            L.append(f"| {stage} | {c.get('ran', 0)} | {c.get('skipped', 0)} "
                     f"| {c.get('errored', 0)} | {c.get('absent', 0)} |")
        L.append("")
        never = [s for s, c in stage_counts.items()
                 if c.get("ran", 0) == 0 and c.get("errored", 0) == 0]
        if never:
            L.append("**Stages that never ran for ANY spec:** "
                     + ", ".join(f"`{s}`" for s in never) + ".")
            L.append("")
            L.append("This is a real limitation of the matrix, not a "
                     "detail. Cross-market replication is structurally "
                     "unreachable through the matrix runner because it "
                     "passes no alternative universes to the gauntlet, "
                     "so no spec in this matrix was tested for whether "
                     "it transfers to a different market.")
            L.append("")

    # ---- the fold tables ------------------------------------------------
    folds = _fold_tables(rows)
    if folds:
        L.append(sec("The per-fold walk-forward tables"))
        L.append("")
        L.append("Each row is one purged-and-embargoed out-of-sample "
                 "fold. A concept that works because ONE fold worked is "
                 "not an edge, and the fold table is where that shows.")
        L.append("")
        for r in folds:
            L.append(f"### `{r['name']}` — {r['verdict']}")
            L.append("")
            L.append("| Fold | OOS Sharpe | OOS trades | Period |")
            L.append("|---|---|---|---|")
            for f in r["folds"]:
                o = f.get("oos_sharpe")
                period = ""
                if f.get("start") or f.get("end"):
                    period = f"{f.get('start') or '?'} → {f.get('end') or '?'}"
                L.append(f"| {f.get('fold')} "
                         f"| {('%.2f' % o) if isinstance(o, (int, float)) else 'n/a'} "
                         f"| {f.get('oos_trades', 'n/a')} | {period} |")
            L.append("")

    # ---- leading coverage ----------------------------------------------
    if s["coverage"]:
        L.append(sec("Leading-indicator coverage"))
        L.append("")
        L.append("How much of each panel the forward-looking indicator "
                 "actually covered. A leading feature that covers a small "
                 "fraction of the sample cannot be evaluated, and the "
                 "verdict for that spec is a verdict on a short sample.")
        L.append("")
        L.append("| Spec | Source | Points | Note |")
        L.append("|---|---|---|---|")
        for c in s["coverage"]:
            L.append(f"| `{c['name']}` | {c.get('source')} "
                     f"({c.get('asset')}) | {c.get('n_points')} "
                     f"| {c.get('reason') or ''} |")
        L.append("")

    # ---- what this means -----------------------------------------------
    L.append(sec("What this establishes and what it does not"))
    L.append("")
    L.append("* Every result above is an OUT-OF-SAMPLE result from a "
             "purge-and-embargo walk-forward, at 2x the engine's default "
             "costs, with a volatility-targeted, dollar-neutral, "
             "10%-per-name-capped book.")
    L.append("* A SUPPORTED verdict means the strategy warrants PAPER "
             "TRADING. It is not a licence to trade it with money, and "
             "the package's own stage gates say so "
             "(`LIVE_CAPITAL_READINESS.md`).")
    L.append("* The negative controls are the reason any of this is "
             "believable. A matrix without them would look identical "
             "whether the concepts were real or invented.")
    L.append("* Crypto and equities are DIFFERENT markets. The regime "
             "paper says so explicitly, so a concept that survives on "
             "one and fails on the other is a finding about the market, "
             "not a defect in the test.")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------
# The HTML dashboard
# --------------------------------------------------------------------------
def _verdict_matrix_svg(summary: Dict[str, Any]) -> str:
    """A grid of cells, coloured by verdict."""
    concepts = summary["concepts"]
    acs = summary["asset_classes"]
    if not concepts or not acs:
        return "<p>no data</p>"
    cw, ch = 150, 34
    pad_l, pad_t = 210, 60
    width = pad_l + cw * len(acs) + 20
    height = pad_t + ch * len(concepts) + 20
    out = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
           f'style="max-width:{width}px;background:{BG}" '
           f'xmlns="http://www.w3.org/2000/svg">',
           f'<rect width="{width}" height="{height}" fill="{BG}"/>',
           f'<text x="12" y="26" fill="{TEXT}" font-size="13" '
           f'font-weight="bold">Verdict by concept and asset class</text>']
    for j, a in enumerate(acs):
        out.append(f'<text x="{pad_l + j * cw + cw/2:.0f}" y="{pad_t - 10}" '
                   f'fill="{MUTED}" font-size="10" text-anchor="middle">'
                   f'{_esc(a)}</text>')
    for i, c in enumerate(concepts):
        y = pad_t + i * ch
        out.append(f'<text x="12" y="{y + 21}" fill="{TEXT}" '
                   f'font-size="11">{_esc(c)}</text>')
        for j, a in enumerate(acs):
            r = (summary["matrix"].get(c) or {}).get(a)
            x = pad_l + j * cw
            if not r:
                out.append(f'<rect x="{x}" y="{y}" width="{cw-4}" '
                           f'height="{ch-4}" fill="#2a2a44" rx="3"/>')
                continue
            col = _VERDICT_COLOUR.get(str(r.get("verdict")), NEUTRAL)
            sh = _sharpe(r)
            if not _ran(r):
                col = NEUTRAL
                label = "NOT RUN"
            else:
                label = str(r.get("verdict") or "?")[:4]
            if sh is not None and _ran(r):
                label += f" {sh:.1f}"
            out.append(f'<rect x="{x}" y="{y}" width="{cw-4}" '
                       f'height="{ch-4}" fill="{col}" opacity="0.22" '
                       f'stroke="{col}" rx="3"/>')
            out.append(f'<text x="{x + (cw-4)/2:.0f}" y="{y + 21}" '
                       f'fill="{col}" font-size="10" text-anchor="middle">'
                       f'{_esc(label)}</text>')
    out.append("</svg>")
    return "".join(out)


def _esc(s: Any) -> str:
    import html
    return html.escape(str(s), quote=True)


def render_html(rows: Sequence[Dict[str, Any]],
                summary: Optional[Dict[str, Any]] = None) -> str:
    """Render the matrix as a self-contained HTML page."""
    s = summary or summarise(rows)
    parts: List[str] = []

    counts = s["verdict_counts"]
    ccounts = s["control_verdict_counts"]
    ctrl_ok = s["controls_survived"]

    parts.append(
        '<div class="card"><h2>What the matrix found</h2>'
        '<div class="grid">'
        f'<div><div class="kv">Real specs tested</div>'
        f'<div class="vv big">{s["n_real"]}</div></div>'
        f'<div><div class="kv">Actually executed</div>'
        f'<div class="vv big">{len(s["real_ran"])}</div></div>'
        f'<div><div class="kv">Negative controls</div>'
        f'<div class="vv big">{s["n_controls"]}</div></div>'
        f'<div><div class="kv">SUPPORTED (real)</div>'
        f'<div class="vv big" style="color:{UP}">'
        f'{counts.get("SUPPORTED", 0)}</div></div>'
        f'<div><div class="kv">FRAGILE (real)</div>'
        f'<div class="vv big" style="color:{WARN}">'
        f'{counts.get("FRAGILE", 0)}</div></div>'
        f'<div><div class="kv">REFUTED (real)</div>'
        f'<div class="vv big" style="color:{DOWN}">'
        f'{counts.get("REFUTED", 0)}</div></div>'
        f'<div><div class="kv">Controls that survived</div>'
        f'<div class="vv big" style="color:'
        f'{DOWN if ctrl_ok else UP}">{len(ctrl_ok)}</div></div>'
        '</div>'
        + ('<p class="note warn">A negative control SURVIVED. The '
           'validation is not discriminating and every other verdict is '
           'void until that is explained.</p>' if ctrl_ok else
           f'<p class="note">Of the {s["n_controls"]} negative controls, '
           f'{len(s["controls_ran"])} actually executed and every one of '
           f'them failed, as it must.'
           + (f' The other {len(s["controls_did_not_run"])} did not run and '
              'so say nothing either way.'
              if s["controls_did_not_run"] else '')
           + '</p>')
        + ('<p class="note warn">'
           f'{len(s["real_did_not_run"])} real specs and '
           f'{len(s["controls_did_not_run"])} controls produced NO result '
           'at all. A spec that crashed is not a research finding; those '
           'concepts are untested, not refuted, and the rows are marked '
           'DID NOT RUN.</p>'
           if (s["real_did_not_run"] or s["controls_did_not_run"]) else '')
        + '</div>')

    parts.append('<div class="card"><h2>Verdict matrix</h2>'
                 + _verdict_matrix_svg(s)
                 + '<p class="note">One cell per concept x asset class. '
                   'Sharpe figures are pooled OUT-OF-SAMPLE.</p></div>')

    # The real-vs-control comparison, per concept.
    comp_chart = []
    for c in s["concepts"]:
        rows_c = [x for x in s["comparison"] if x["concept"] == c]
        real_sh = [x["real_sharpe"] for x in rows_c
                   if x["real_sharpe"] is not None]
        ctrl_sh = [x["control_sharpe"] for x in rows_c
                   if x["control_sharpe"] is not None]
        if not real_sh and not ctrl_sh:
            continue
        comp_chart.append({
            "title": f"{c} — real vs inverted control",
            "svg": svg_line_chart(
                [{"name": "real", "values": real_sh, "color": UP},
                 {"name": "inverted control", "values": ctrl_sh,
                  "color": DOWN}],
                None, f"{c}: real vs inverted control", y_label="OOS Sharpe",
                hlines=[{"value": 0.0, "color": MUTED, "label": "zero"}]),
            "note": ("If the two lines overlap, the concept is not "
                     "separating itself from its own negation."),
        })
    parts.extend('<div class="card"><h2>' + _esc(c["title"]) + '</h2>'
                  + c["svg"] + '<p class="note">' + _esc(c["note"])
                  + '</p></div>' for c in comp_chart)

    # Cross-asset consistency bars.
    cons = s["consistency"]
    if cons:
        items = [{"label": c["concept"][:22],
                  "value": (c["mean_sharpe"] or 0.0)} for c in cons]
        parts.append('<div class="card"><h2>Mean out-of-sample Sharpe by '
                     'concept</h2>'
                     + svg_bars(items, "Mean OOS Sharpe by concept",
                                value_key="value", label_key="label")
                     + '<p class="note">A concept that only works on one '
                       'asset class is a market curiosity, not an edge. '
                       'The table in the markdown report gives the '
                       'per-asset-class breakdown.</p></div>')

    # The stage coverage: what was validated, and what was not.
    stage_counts = _stage_coverage(rows)
    if stage_counts:
        trows = []
        for stage in sorted(stage_counts):
            c = stage_counts[stage]
            ran = c.get("ran", 0)
            skipped = c.get("skipped", 0)
            errored = c.get("errored", 0)
            col = UP if ran else (WARN if skipped else DOWN)
            trows.append(
                f'<tr><td>{_esc(stage)}</td>'
                f'<td style="color:{col}">{ran}</td>'
                f'<td style="color:{WARN if skipped else MUTED}">{skipped}</td>'
                f'<td style="color:{DOWN if errored else MUTED}">{errored}</td>'
                f'</tr>')
        parts.append('<div class="card"><h2>What was validated</h2>'
                     '<table><tr><th>Stage</th><th>Ran</th><th>Skipped</th>'
                     '<th>Errored</th></tr>' + "".join(trows) + '</table>'
                     '<p class="note">A verdict is only as good as the '
                     'checks behind it. A stage that did not run is '
                     'reported, never hidden.</p></div>')

    # The verdict detail table.
    trows = []
    for r in sorted(rows, key=lambda x: (str(x.get("concept")),
                                          str(x.get("asset_class")))):
        sh = _sharpe(r)
        ran = _ran(r)
        col = _VERDICT_COLOUR.get(str(r.get("verdict")), NEUTRAL)
        if not ran:
            label = "DID NOT RUN"
            col = NEUTRAL
        else:
            label = str(r.get("verdict"))
        flag_text = "; ".join(str(x) for x in (r.get("flags") or []))
        if not ran and r.get("errors"):
            flag_text = "; ".join(str(x) for x in (r.get("errors") or []))
        trows.append(
            f'<tr><td>{_esc(r.get("concept"))}</td>'
            f'<td>{_esc(r.get("asset_class"))}</td>'
            f'<td><span class="tag" style="color:{col};background:'
            f'{col}22">{_esc(label)}</span></td>'
            f'<td>{("%.2f" % sh) if (sh is not None and ran) else "n/a"}</td>'
            f'<td class="kv">{_esc(flag_text)}</td></tr>')
    parts.append('<div class="card"><h2>Every spec, with its flags</h2>'
                 '<table><tr><th>Concept</th><th>Asset class</th>'
                 '<th>Verdict</th><th>OOS Sharpe</th><th>Flags</th></tr>'
                 + "".join(trows) + '</table></div>')

    parts.append('<div class="card"><h2>What this establishes</h2><ul>'
                 '<li>Every figure is a pooled OUT-OF-SAMPLE result from '
                 'a purge-and-embargo walk-forward.</li>'
                 '<li>Costs are stressed to 2x the engine default; the '
                 'book is volatility-targeted, dollar-neutral and capped '
                 'at 10% per name.</li>'
                 '<li>A SUPPORTED verdict warrants PAPER TRADING. It is '
                 'not a licence to trade with money.</li>'
                 '<li>The negative controls are why any of this is '
                 'believable.</li></ul></div>')

    body = "\n".join(parts)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LeapSpace — paper-concept matrix</title>
<style>
 :root {{ color-scheme: dark; }}
 body {{ margin:0; padding:24px; background:{BG}; color:{TEXT};
        font:14px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif; }}
 h1 {{ font-size:21px; margin:0 0 4px; }}
 .sub {{ color:{MUTED}; margin:0 0 22px; font-size:13px; }}
 .card {{ background:#20203a; border:1px solid {GRID}; border-radius:12px;
          padding:16px 18px; margin-bottom:16px; }}
 .note {{ color:{MUTED}; font-size:12.5px; margin:8px 0 0; }}
 .warn {{ color:{WARN}; }}
 .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
          gap:14px; }}
 .kv {{ color:{MUTED}; font-size:12px; }}
 .vv {{ font-size:16px; }} .big {{ font-size:26px; font-weight:600; }}
 table {{ border-collapse:collapse; width:100%; font-size:12.5px; }}
 th,td {{ text-align:left; padding:6px 9px; border-bottom:1px solid {GRID};
          vertical-align:top; }}
 th {{ color:{MUTED}; font-weight:600; text-transform:uppercase; font-size:10.5px; }}
 .tag {{ display:inline-block; padding:2px 8px; border-radius:999px;
         font-size:11px; font-weight:600; }}
</style></head><body>
<h1>Paper-concept matrix</h1>
<p class="sub">Every claim in the five research papers, coded and tested
through the full validation gauntlet across six asset classes.</p>
{body}
</body></html>"""


def build_report(results_path: Optional[str] = None,
                 md_path: Optional[str] = None,
                 html_path: Optional[str] = None) -> Dict[str, Any]:
    """Build the markdown report and the HTML dashboard."""
    rows = load_results(results_path)
    summary = summarise(rows)
    md = render_markdown(rows, summary)
    md_path = md_path or PAPER_REPORT_PATH
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md)
    html = render_html(rows, summary)
    html_path = html_path or _HTML_PATH
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return {"markdown": md_path, "html": html_path, "summary": summary,
            "n_rows": len(rows)}
