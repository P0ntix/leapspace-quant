"""Source reliability register: the papers' own defects and this package's scope.

The seven LeapSpace documents are literature-synthesis transcripts, not
research papers. Reading them surfaced defects in the SOURCE material
(a mis-cited section, section-scoped citation numbers that collide, no
numeric results at all, no rebalance cadence anywhere) plus a set of
sections this package deliberately does not implement.

This module loads the register and turns it into report-ready rows. It
never invents a finding: every entry traces to a specific defect in the
register file, and the register file records the evidence.
"""
import json
import os
from typing import Any, Dict, List

_HERE = os.path.dirname(os.path.abspath(__file__))
REGISTER_PATH = os.path.join(_HERE, "data", "source_reliability.json")


def load_register(path: str = None) -> Dict[str, Any]:
    """Load the register. Returns {} when it is absent (degrade, don't crash)."""
    p = path or REGISTER_PATH
    try:
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def defect_rows(reg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten the register into one row per defect, across all documents."""
    rows: List[Dict[str, Any]] = []
    for doc in (reg.get("documents") or []):
        for d in (doc.get("defects") or []):
            rows.append({
                "document": doc.get("title", doc.get("key", "?")),
                "id": d.get("id", "?"),
                "severity": d.get("severity", "?"),
                "finding": d.get("finding", ""),
                "evidence": d.get("evidence", ""),
                "impact": d.get("impact", ""),
                "impacts_specs": d.get("impacts_specs", ""),
            })
    order = {"high": 0, "medium": 1, "low": 2}
    rows.sort(key=lambda r: (order.get(r["severity"], 3), r["document"], r["id"]))
    return rows


def scope_rows(reg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The paper sections this package deliberately does not implement."""
    return [
        {
            "id": s.get("id", "?"),
            "why": s.get("why", ""),
            "decision": s.get("decision", ""),
            "if_wanted": s.get("if_wanted", ""),
        }
        for s in (reg.get("scope_exclusions") or [])
    ]


def register_section(reg: Dict[str, Any]) -> Dict[str, Any]:
    """The report-ready payload for the source-reliability section."""
    defects = defect_rows(reg)
    scopes = scope_rows(reg)
    return {
        "available": bool(reg),
        "generated": reg.get("generated"),
        "defect_count": len(defects),
        "high_severity": sum(1 for d in defects if d["severity"] == "high"),
        "defects": defects,
        "scope_exclusions": scopes,
        "how_to_use": reg.get("how_to_use_this_register", []),
        "no_spec_depends_on_a_defect": all(
            not (d.get("impacts_specs") or "").strip()
            or "None" in (d.get("impacts_specs") or "")
            or "All" in (d.get("impacts_specs") or "")
            for d in defects),
    }
