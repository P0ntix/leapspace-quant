"""
Consolidated report writer.

Produces one human-readable markdown report covering every module, with
the provenance of each figure and an explicit gaps section. The report is
written from a JSON payload so it can be regenerated without re-running the
network work, and so the numbers in it always match the artifacts on disk.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any, Dict, List, Optional, Sequence

from .provenance import write_json

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "reports")


def _fmt(v: Any, pct: bool = False, nd: int = 3) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        if pct:
            return f"{v:.1%}"
        return f"{v:.{nd}f}"
    return str(v)


def _verdict_banner(verdict: str) -> str:
    return {
        "SUPPORTED": ("SUPPORTED — the out-of-sample evidence survives the "
                      "stages that ran. Per the backtest lab's rule this "
                      "means 'warrants paper trading', NEVER 'trade it'."),
        "FRAGILE": ("FRAGILE — a positive out-of-sample result that a "
                    "robustness stage failed, or out-of-sample evidence only. "
                    "Treat as unproven."),
        "REFUTED": ("REFUTED — the edge did not survive out-of-sample "
                    "testing and/or cost stress. See the flags for what "
                    "specifically killed it."),
        "INCONCLUSIVE": ("INCONCLUSIVE — too few trades or too short a "
                         "sample to tell signal from noise."),
    }.get(verdict, verdict)


def merge_full_gauntlet(payload: Dict[str, Any], path: str) -> int:
    """Overlay the FULL-gauntlet verdicts onto a quick-run payload.

    A `--quick` run can produce a MORE favourable verdict than the full
    gauntlet (it skips Monte Carlo, the parameter sweep and replication). This
    replaces the quick verdict with the stricter full one where a full run
    exists, and marks the row so the reader can see which evidence stands.
    """
    from .provenance import read_json
    blob = read_json(path)
    if not blob:
        return 0
    full = {r["name"]: r for r in (blob.get("results") or [])}
    merged = 0
    for row in (payload.get("sections") or {}).get("backtests") or []:
        f = full.get(row.get("name"))
        if not f:
            continue
        row["verdict"] = f.get("verdict", row.get("verdict"))
        row["flags"] = f.get("flags", row.get("flags"))
        if f.get("metrics"):
            row["metrics"] = {**row.get("metrics", {}), **f["metrics"]}
        if f.get("walk_forward"):
            row["walk_forward"] = {**row.get("walk_forward", {}), **f["walk_forward"]}
        row["skipped_stages"] = f.get("skipped_stages", [])
        row["validation"] = "FULL gauntlet"
        if f.get("note"):
            row["full_gauntlet_note"] = f["note"]
        merged += 1
    payload["full_gauntlet_overlay"] = {
        "applied": merged,
        "source": path,
        "note": ("Rows marked 'FULL gauntlet' carry the stricter verdict from "
                 "a complete validation run. Rows without the marker were run "
                 "with --quick, which skips Monte Carlo, the parameter sweep "
                 "and replication — their verdict is a preliminary read for "
                 "those stages."),
    }
    return merged


def render_report(payload: Dict[str, Any]) -> str:
    L: List[str] = []
    A = L.append
    A("# LeapSpace Quant — consolidated report")
    A("")
    A(f"Generated: {payload.get('generated_at')}")
    A("")
    A(f"> {payload.get('disclosure', '')}")
    A("")

    sections = payload.get("sections") or {}

    # --- regime ---
    reg = sections.get("regime")
    A("## 1. Market regime")
    A("")
    if reg and "error" not in reg:
        A(f"- **Symbol:** {reg.get('symbol')}")
        A(f"- **State labels:** `{json.dumps(reg.get('labels'))}`")
        A(f"- **State share:** `{json.dumps({k: round(v, 3) for k, v in (reg.get('state_share') or {}).items()})}`")
        A(f"- **Current state:** `{reg.get('latest_label')}`")
        A(f"- **HMM convergence:** {reg.get('converged')} in {reg.get('n_iter')} iterations")
        A(f"- **Bars used:** {reg.get('bars_used')} of {reg.get('bars_total')} "
          f"({reg.get('unusable_bars_warmup')} in warm-up)")
        for p in reg.get("provenance", [])[:2]:
            A(f"- **Provenance:** {p}")
        A("")
        A("> **Limitation:** the HMM's parameters are fitted on the whole "
          "panel, so the regime *classification* is in-sample even though the "
          "filter itself is causal. A walk-forward refit is the next step.")
    else:
        A(f"- **Gap:** {reg}")
    A("")

    # --- gamma ---
    g = sections.get("gamma")
    A("## 2. Dealer gamma exposure and option flow")
    A("")
    if g and "net_gamma" in json.dumps(g):
        gg = g.get("gamma", {})
        ff = g.get("flow", {})
        A(f"- **Underlying:** {gg.get('underlying')}")
        A(f"- **Spot:** {gg.get('spot')} (as of {gg.get('as_of')})")
        A(f"- **Net gamma:** {_fmt(gg.get('net_gamma'))} → **{gg.get('state')}**")
        A(f"- **Call / put gamma:** {_fmt(gg.get('call_gamma'))} / {_fmt(gg.get('put_gamma'))}")
        A(f"- **Max-pain strike:** {gg.get('max_pain_strike')}  ·  "
          f"**Zero-gamma strike:** {gg.get('zero_gamma_strike')}")
        A(f"- **Put/call volume ratio:** {_fmt(ff.get('put_call_volume_ratio'))}")
        A(f"- **Net delta flow:** {_fmt(ff.get('net_delta_flow'))}  ·  "
          f"**net vega flow:** {_fmt(ff.get('net_vega_flow'))}")
        A("")
        A(f"**Paper read:** {gg.get('interpretation')}")
        A("")
        A("**Caveats that apply to every number above:**")
        for a in (gg.get("assumptions") or []):
            A(f"- {a}")
        for w in (gg.get("warnings") or []):
            A(f"- {w}")
        A(f"- {g.get('note', '')}")
    else:
        A(f"- **Gap:** {g}")
    A("")

    # --- backtests ---
    bt = sections.get("backtests") or []
    A("## 3. Backtests — the paper-derived strategies")
    A("")
    if bt:
        overlay = payload.get("full_gauntlet_overlay") or {}
        A("| Strategy | Paper | Verdict | Validation | Trades | Sharpe | OOS Sharpe | OOS folds |")
        A("|---|---|---|---|---|---|---|---|")
        for b in bt:
            m = b.get("metrics") or {}
            w = b.get("walk_forward") or {}
            val = b.get("validation") or ("--quick" if b.get("skipped_stages")
                                          else "full")
            A(f"| `{b.get('name')}` | {b.get('paper', '?')} | "
              f"**{b.get('verdict')}** | {val} | "
              f"{m.get('n_trades', 'n/a')} | "
              f"{_fmt(m.get('sharpe'))} | {_fmt(w.get('oos_sharpe'))} | "
              f"{w.get('oos_profitable_folds', 'n/a')}/{w.get('n_folds', 'n/a')} |")
        A("")
        if overlay:
            A(f"**Validation note:** {overlay.get('note')}")
            A("")
        # Intake-gate accounting: every strategy condition must be SUPPLIED,
        # not merely ticked off. A condition whose value coincides with an
        # engine default is recorded here as an accepted default, with the
        # reason, so the reader can see which conditions came from the paper
        # and which were the analyst's.
        gated = [b for b in bt if (b.get("intake_gate") or {}).get("available")]
        if gated:
            A("### Intake gate")
            A("")
            A("The backtest lab's intake gate ran on every spec. It compares "
              "each probed condition against the engine's defaults and "
              "refuses a spec with an unanswered condition. A condition whose "
              "value coincides with an engine default is recorded below as an "
              "**accepted default** — the decision was made deliberately and "
              "is documented in the spec's `parameter_provenance`, so the gate "
              "records the decision instead of reading it as an open question.")
            A("")
            A("| Strategy | Gate | Conditions accepted as engine defaults |")
            A("|---|---|---|")
            for b in gated:
                g = b.get("intake_gate") or {}
                acc = g.get("auto_accepted") or []
                A(f"| `{b.get('name')}` | "
                  f"{'PASS' if g.get('passed') else 'REFUSED'} | "
                  f"{', '.join(f'`{c}`' for c in acc) or 'none'} |")
            A("")
        for b in bt:
            A(f"### `{b.get('name')}`")
            A("")
            A(f"**Verdict: {b.get('verdict')}** — {_verdict_banner(b.get('verdict', ''))}")
            A("")
            if b.get("validation"):
                A(f"Validation: **{b['validation']}**")
                A("")
            if b.get("full_gauntlet_note"):
                A(f"> {b['full_gauntlet_note']}")
                A("")
            if b.get("flags"):
                A("Flags:")
                for fl in b["flags"]:
                    A(f"- {fl}")
                A("")
            if b.get("skipped_stages"):
                A(f"**Stages NOT run:** {', '.join(b['skipped_stages'])}. "
                  f"This was a partial validation; the verdict is a "
                  f"preliminary read for those stages.")
                A("")
            pp = b.get("parameter_provenance") or {}
            if pp:
                A("Parameter provenance:")
                A("")
                A("| Parameter | Source | Note |")
                A("|---|---|---|")
                for k, v in pp.items():
                    src = v.get("source", "?")
                    note = (v.get("note") or v.get("citation") or "").replace(
                        "|", "\\|")
                    A(f"| `{k}` | {src} | {note} |")
                A("")
            if b.get("report_path"):
                A(f"Full engine report: `{b['report_path']}`")
                A("")
    else:
        A("- No backtests were run in this report.")
        A("")

    # --- source reliability of the papers themselves ---
    from .source_reliability import register_section, load_register
    reg = register_section(load_register())
    if reg.get("available"):
        A("## 4. Source reliability of the papers themselves")
        A("")
        A("The seven LeapSpace documents are literature-synthesis transcripts, "
          "not research papers. Reading them surfaced defects in the SOURCE "
          "material, and a set of sections this package deliberately does not "
          "implement. These findings are about the papers' evidence, not "
          "about the backtests above.")
        A("")
        A(f"**{reg['defect_count']} defects recorded** "
          f"({reg['high_severity']} high severity) across the documents.")
        A("")
        A("| Document | ID | Severity | Finding | Impact on this package |")
        A("|---|---|---|---|---|")
        for d in reg["defects"]:
            A(f"| {d['document']} | {d['id']} | {d['severity']} | "
              f"{d['finding']} | {d['impacts_specs']} |")
        A("")
        A("**The load-bearing ones:**")
        A("")
        for d in reg["defects"]:
            if d["severity"] == "high":
                A(f"- **{d['id']}** — {d['finding']}")
                if d.get("evidence"):
                    A(f"  - Evidence: {d['evidence']}")
                if d.get("impact"):
                    A(f"  - Impact: {d['impact']}")
        A("")
        if reg["scope_exclusions"]:
            A("### Sections deliberately not implemented")
            A("")
            A("These paper sections have no automation behind them. Each entry "
              "states why, and what would be needed to close the gap.")
            A("")
            for s in reg["scope_exclusions"]:
                A(f"**{s['id']}**")
                A("")
                A(f"- Why not: {s['why']}")
                A(f"- Decision: {s['decision']}")
                if s.get("if_wanted"):
                    A(f"- To enable it: {s['if_wanted']}")
                A("")
        if reg.get("how_to_use"):
            A("### How to use this register")
            A("")
            for line in reg["how_to_use"]:
                A(f"- {line}")
            A("")

    # --- disclosure ---
    disc = sections.get("disclosure")
    if disc:
        A("## 5. US officials' financial disclosures — three branches")
        A("")
        for key, b in (disc.get("branches") or {}).items():
            A(f"### {b.get('title', key)}")
            A("")
            A(f"- Law: {b.get('law', 'n/a')}")
            A(f"- Filings indexed: {b.get('filings_indexed')}")
            if "by_type" in b:
                A(f"- By filing type: `{json.dumps(b['by_type'])}`")
            if "by_agency" in b:
                A(f"- By agency (top): `{json.dumps(b['by_agency'])}`")
            if "with_public_pdf" in b:
                A(f"- With a public PDF: {b['with_public_pdf']} · "
                  f"request-form-only: {b['request_form_only']}")
            if "primary_filings" in b:
                A(f"- Primary-source filings: {b['primary_filings']} · "
                  f"secondary (mirrors): {b['secondary_filings']}")
            for note_key, label in (
                    ("provenance_note", "Provenance"),
                    ("scotus_disclosure_page", "SCOTUS disclosure page")):
                if b.get(note_key):
                    A(f"- {label}: {b[note_key]}")
            A("")
        A(f"**Coverage:** `{json.dumps(disc.get('coverage'))}`")
        A("")
        if disc.get("sources_unavailable"):
            A("**Source gaps** — these are availability problems, NOT "
              "statements that filings do not exist:")
            A("")
            for g in disc["sources_unavailable"]:
                A(f"- **{g.get('source')}** — {g.get('reason')}")
            A("")
        A(disc.get("disclosure", ""))
        A("")

    # --- gaps ---
    if payload.get("gaps"):
        A("## 6. Source gaps")
        A("")
        for g in payload["gaps"]:
            A(f"- **{g.get('source')}** — {g.get('reason')}")
        A("")

    A("---")
    A("")
    A("*This report is produced by an automated research system. It is not "
      "investment advice. A SUPPORTED verdict means the hypothesis survived "
      "the validation stages that ran — nothing more.*")
    return "\n".join(L)


def write_report(payload: Dict[str, Any], out_dir: str = REPORT_DIR) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "leapspace_report.json")
    md_path = os.path.join(out_dir, "leapspace_report.md")

    # --- Pre-flight validation ------------------------------------------
    # The report is rendered first, then validated, then written. A
    # report that fails validation is STILL written, but it carries a
    # machine-readable block naming every error so a reader cannot
    # mistake it for a clean report. Warnings alone never block.
    markdown = render_report(payload)
    validation: Dict[str, Any] = {}
    try:
        from leapspace.reportvalidate import (
            format_validation_block,
            validate_report,
        )

        validation = validate_report(markdown, payload, filepath=md_path)
        block = format_validation_block(validation)
        if block:
            markdown = markdown.rstrip() + "\n\n" + block
    except Exception as exc:  # noqa: BLE001
        # The validator must never prevent a report from being written.
        # A failure to validate is itself a finding, recorded below.
        validation = {
            "ok": False,
            "checks": [],
            "errors": [
                {
                    "severity": "ERROR",
                    "category": "validator_crashed",
                    "message": f"The report validator failed to run: {exc}",
                    "line_number": None,
                    "context": None,
                }
            ],
            "warnings": [],
            "n_findings": 1,
            "vendor_status": "unavailable",
        }

    payload = dict(payload)
    payload["data_quality_validation"] = validation

    write_json(json_path, payload)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(markdown)
    return {"json": json_path, "markdown": md_path}
