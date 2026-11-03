"""Load the agent-researched, authority-tagged consistency criteria and
expose them to the gate.

The machine-readable spec lives at
`leapspace/data/consistency_criteria.json` (31 criteria, each with a
formula, a threshold, an authority, a tag and a URL). This module reads
it and hands the gate the thresholds that are actually CITED, keeping
the analyst choices clearly separated from them.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

CRITERIA_PATH = os.path.join(os.path.dirname(__file__), "data",
                             "consistency_criteria.json")

_CACHE: Optional[Dict[str, Any]] = None


def load_criteria(path: Optional[str] = None) -> Dict[str, Any]:
    """The full criteria spec."""
    global _CACHE
    if path is None and _CACHE is not None:
        return _CACHE
    p = path or CRITERIA_PATH
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "reason": f"{type(exc).__name__}: {exc}",
                "criteria": [], "fluke_tests": []}
    if path is None:
        _CACHE = data
    return data


def criteria_index(spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """criteria keyed by key, for O(1) lookup."""
    spec = spec if spec is not None else load_criteria()
    return {c["key"]: c for c in (spec.get("criteria") or [])
            if isinstance(c, dict) and c.get("key")}


def criterion(key: str,
              spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """One criterion, with its authority, tag and URL."""
    c = criteria_index(spec).get(key)
    if c is None:
        return {"key": key, "status": "not_in_spec"}
    return c


def cited_thresholds(spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Thresholds that carry a real citation.

    Only criteria whose authority is not NONE / analyst-only are
    returned, so the gate never presents an invented number as a
    published standard.
    """
    out: Dict[str, Any] = {}
    for c in (spec if spec is not None else load_criteria()).get("criteria") \
            or []:
        if not isinstance(c, dict):
            continue
        auth = str(c.get("authority") or "")
        if auth.startswith("NONE") or "analyst choice" in auth.lower():
            continue
        if c.get("threshold") is None:
            continue
        out[c["key"]] = {
            "threshold": c.get("threshold"),
            "authority": auth,
            "tag": c.get("tag"),
            "url": c.get("url"),
            "note": c.get("note"),
        }
    return out


def analyst_thresholds(spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Thresholds that are the analyst's own, with no published source."""
    out: Dict[str, Any] = {}
    for c in (spec if spec is not None else load_criteria()).get("criteria") \
            or []:
        if not isinstance(c, dict):
            continue
        auth = str(c.get("authority") or "")
        if not (auth.startswith("NONE") or "analyst choice" in auth.lower()):
            continue
        out[c["key"]] = {
            "threshold": c.get("threshold"),
            "authority": auth,
            "tag": c.get("tag"),
            "note": c.get("note"),
        }
    return out


def fluke_test_specs(spec: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """The fluke tests from the spec, with their definitions."""
    return [t for t in ((spec if spec is not None else load_criteria())
                        .get("fluke_tests") or []) if isinstance(t, dict)]


def verdict_semantics(spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """How each verdict is defined in the spec."""
    return ((spec if spec is not None else load_criteria())
            .get("verdict_semantics") or {})


def tag_definitions(spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return ((spec if spec is not None else load_criteria())
            .get("tag_definitions") or {})


def criteria_table(spec: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """A flat, printable index: key, threshold, tag, authority, url."""
    rows = []
    for c in ((spec if spec is not None else load_criteria())
              .get("criteria") or []):
        if not isinstance(c, dict):
            continue
        rows.append({
            "key": c.get("key"),
            "label": c.get("label"),
            "threshold": c.get("threshold"),
            "tag": c.get("tag"),
            "authority": c.get("authority"),
            "url": c.get("url"),
        })
    return rows


def derived_scoring(spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return ((spec if spec is not None else load_criteria())
            .get("derived_scoring") or {})
