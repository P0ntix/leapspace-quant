"""The whitelist: memecoin whales and consistently successful traders.

A whitelist entry is a WALLET (or a linked cluster of wallets across
chains) that has been shown to trade with a real, consistent edge - not a
single lucky win.

WHAT MAKES AN ENTRY
-------------------
Every entry carries:
  * the address(es) and the chain(s)
  * the edge verdict and the metrics behind it (from `leapspace.edge`)
  * the EVIDENCE: which trades, which tokens, which period
  * the number of CANDIDATES SCANNED before this one was picked - which
    is what the Deflated Sharpe is corrected for
  * a timestamp and a reason for every promotion and every retirement

RETENTION, NOT DELETION
------------------------
Following CFA Institute GIPS 3.A.9 ("Terminated portfolios must be
included in the historical performance of the composite up to the last
full measurement period"), a wallet that stops trading or decays LEAVES
THE FORWARD COHORT but its HISTORY STAYS in the record. It is never
silently dropped and never retroactively restated. A whitelist that
edits itself is a whitelist you cannot audit.

STATUSES
--------
  WHITELISTED  in the forward cohort; edge is CONSISTENT
  WATCH        edge is WEAK or the evidence is thin; tracked, not trusted
  FLUKE        rejected by a fluke test; retained in the record as a
               rejected candidate, so the selection bias of the scan is
               visible rather than invisible
  RETIRED      was whitelisted, no longer qualifies; history retained

CROSS-CHAIN
------------
The same operator can hold different addresses on different chains. The
registry keys an entry on a CANONICAL IDENTITY, which is either a single
address or a cluster id established by `leapspace.crosschain` with
traceable evidence. A link that is only SUGGESTED is stored as a
suggestion, never merged into a confirmed identity.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from .provenance import read_json

WHITELIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "state", "whitelist.json")

STATUS_WHITELISTED = "WHITELISTED"
STATUS_WATCH = "WATCH"
STATUS_FLUKE = "FLUKE"
STATUS_RETIRED = "RETIRED"


def load_whitelist(path: Optional[str] = None) -> Dict[str, Any]:
    p = path or WHITELIST_PATH
    blob = read_json(p) or {}
    blob.setdefault("entries", {})
    blob.setdefault("events", [])
    blob.setdefault("rejected", [])
    return blob


def save_whitelist(blob: Dict[str, Any], path: Optional[str] = None) -> str:
    p = path or WHITELIST_PATH
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(blob, fh, indent=2)
    os.replace(tmp, p)
    return p


def _entry_key(address: str, chain: str = "ethereum",
               cluster_id: Optional[str] = None) -> str:
    if cluster_id:
        return f"cluster:{cluster_id}"
    return f"{chain}:{address.lower()}"


def record_evaluation(address: str, chain: str, edge: Dict[str, Any],
                      evidence: Optional[Dict[str, Any]] = None,
                      cluster_id: Optional[str] = None,
                      cluster_evidence: Optional[Dict[str, Any]] = None,
                      blob: Optional[Dict[str, Any]] = None,
                      path: Optional[str] = None) -> Dict[str, Any]:
    """Record one edge evaluation and update the whitelist status.

    `edge` is the output of `leapspace.edge.evaluate_edge`. `evidence`
    should carry the underlying trades/tokens/period so the verdict can be
    re-checked later.
    """
    blob = blob if blob is not None else load_whitelist(path)
    key = _entry_key(address, chain, cluster_id)
    now = int(time.time())
    verdict = edge.get("verdict")
    snapshot = {
        "ts": now,
        "verdict": verdict,
        "reason": edge.get("reason"),
        "n_closed_trades": edge.get("n_closed_trades"),
        "win_rate": edge.get("win_rate"),
        "bayesian_skill_p": edge.get("bayesian_skill_p"),
        "wilson": (edge.get("wilson_interval") or {}).get("lower"),
        "independent_bets": (edge.get("independent_bets") or {}
                              ).get("independent_bets"),
        "distinct_tokens": (edge.get("independent_bets") or {}
                            ).get("distinct_tokens"),
        "total_realised_pnl_usd": edge.get("total_realised_pnl_usd"),
        "sharpe_per_trade": edge.get("sharpe_per_trade"),
        "deflated_sharpe": edge.get("deflated_sharpe"),
        "consistency_ratio": edge.get("consistency_ratio"),
        "trials_scanned": edge.get("trials_scanned"),
        "rejected_by": edge.get("rejected_by"),
        "edge_detail": edge,
    }

    entry = blob["entries"].get(key)
    if entry is None:
        entry = {
            "key": key,
            "address": address,
            "chain": chain,
            "cluster_id": cluster_id,
            "chains_seen": [chain],
            "status": None,
            "first_seen": now,
            "history": [],
        }
        blob["entries"][key] = entry
    if chain not in entry.get("chains_seen", []):
        entry.setdefault("chains_seen", []).append(chain)
    entry["last_evaluated_at"] = now
    entry.setdefault("history", []).append(snapshot)

    if cluster_id:
        entry["cluster_evidence"] = cluster_evidence
        entry["cluster_evidence_label"] = (
            (cluster_evidence or {}).get("label", "SUGGESTED"))

    # ---- status transitions -------------------------------------------
    # Explicit and ordered. Every transition is logged with a timestamp
    # and a reason, and no transition ever DELETES the history.
    prev = entry.get("status")
    was_whitelisted = prev == STATUS_WHITELISTED

    if verdict == "CONSISTENT":
        if prev != STATUS_WHITELISTED:
            entry["status"] = STATUS_WHITELISTED
            entry["promoted_at"] = now
            entry["promoted_reason"] = (
                f"edge verdict CONSISTENT: {edge.get('reason')}; "
                f"{edge.get('n_closed_trades')} closed trades, "
                f"{(edge.get('independent_bets') or {}).get('independent_bets')}"
                f" independent bets, skill p={edge.get('bayesian_skill_p')}")
            blob["events"].append({"ts": now, "action": "promote", "key": key,
                                   "reason": entry["promoted_reason"]})
    elif verdict == "FLUKE":
        if was_whitelisted:
            # It WAS in the forward cohort. The meaningful transition is
            # whitelisted -> retired, with the history retained. It is
            # still recorded as a rejected candidate so the scan's
            # selection bias stays visible.
            entry["status"] = STATUS_RETIRED
            entry["retired_at"] = now
            entry["retired_reason"] = (
                f"retired: no longer qualifying - {edge.get('reason')}")
            entry["rejected_at"] = now
            entry["rejected_reason"] = edge.get("reason")
            entry["rejected_by"] = edge.get("rejected_by")
            blob["events"].append({"ts": now, "action": "retire", "key": key,
                                   "reason": entry["retired_reason"]})
        else:
            entry["status"] = STATUS_FLUKE
            entry["rejected_at"] = now
            entry["rejected_reason"] = edge.get("reason")
            entry["rejected_by"] = edge.get("rejected_by")
            blob["events"].append({"ts": now, "action": "reject", "key": key,
                                   "reason": edge.get("reason")})
        # Retained in the REJECTED list so the scan's selection bias is
        # visible: you can see how many candidates were examined and how
        # many were thrown out.
        blob["rejected"].append({
            "ts": now, "key": key, "address": address, "chain": chain,
            "reason": edge.get("reason"),
            "rejected_by": edge.get("rejected_by"),
            "trials_scanned": edge.get("trials_scanned"),
            "n_closed_trades": edge.get("n_closed_trades"),
        })
    elif verdict in ("WEAK", "INSUFFICIENT"):
        if prev in (None, STATUS_FLUKE):
            entry["status"] = STATUS_WATCH
            blob["events"].append({"ts": now, "action": "watch", "key": key,
                                   "reason": edge.get("reason")})
        if was_whitelisted:
            # Leaves the FORWARD cohort; the history stays in the record
            # (GIPS 3.A.9).
            entry["status"] = STATUS_RETIRED
            entry["retired_at"] = now
            entry["retired_reason"] = (
                f"retired: no longer qualifying - {edge.get('reason')}")
            blob["events"].append({"ts": now, "action": "retire", "key": key,
                                   "reason": entry["retired_reason"]})

    if evidence:
        entry["evidence"] = evidence
    save_whitelist(blob, path)
    return entry


def whitelist_report(blob: Optional[Dict[str, Any]] = None,
                      path: Optional[str] = None) -> Dict[str, Any]:
    """The whitelist, reported with every rejected candidate visible."""
    blob = blob if blob is not None else load_whitelist(path)
    entries = blob.get("entries") or {}
    wl = [e for e in entries.values() if e.get("status") == STATUS_WHITELISTED]
    watch = [e for e in entries.values() if e.get("status") == STATUS_WATCH]
    fluke = [e for e in entries.values() if e.get("status") == STATUS_FLUKE]
    retired = [e for e in entries.values() if e.get("status") == STATUS_RETIRED]
    rejected = blob.get("rejected") or []

    def _metrics(e: Dict[str, Any]) -> Dict[str, Any]:
        h = (e.get("history") or [])
        last = h[-1] if h else {}
        return {
            "n_closed_trades": last.get("n_closed_trades"),
            "win_rate": last.get("win_rate"),
            "wilson_lower": last.get("wilson"),
            "bayesian_skill_p": last.get("bayesian_skill_p"),
            "independent_bets": last.get("independent_bets"),
            "distinct_tokens": last.get("distinct_tokens"),
            "total_realised_pnl_usd": last.get("total_realised_pnl_usd"),
            "deflated_sharpe": last.get("deflated_sharpe"),
            "consistency_ratio": last.get("consistency_ratio"),
            "trials_scanned": last.get("trials_scanned"),
        }

    return {
        "whitelisted": sorted(
            ({"key": e["key"], "address": e.get("address"),
              "chains": e.get("chains_seen"),
              "cluster_id": e.get("cluster_id"),
              "cluster_label": e.get("cluster_evidence_label"),
              "promoted_at": e.get("promoted_at"),
              "promoted_reason": e.get("promoted_reason"),
              "evidence": e.get("evidence"),
              **_metrics(e)} for e in wl),
            key=lambda r: -(r.get("total_realised_pnl_usd") or 0)),
        "watch": [{"key": e["key"], "address": e.get("address"),
                   "reason": e.get("promoted_reason") or
                   (e.get("history") or [{}])[-1].get("reason"),
                   **_metrics(e)} for e in watch],
        "fluke_rejected": [{"key": e["key"], "address": e.get("address"),
                            "reason": e.get("rejected_reason"),
                            "rejected_by": e.get("rejected_by")}
                           for e in fluke],
        "retired_history_retained": [
            {"key": e["key"], "address": e.get("address"),
             "retired_at": e.get("retired_at"),
             "retired_reason": e.get("retired_reason"),
             "history_entries": len(e.get("history") or []),
             **_metrics(e)} for e in retired],
        "rejected_candidates_count": len(rejected),
        "events": blob.get("events") or [],
        "retention_rule": ("A retired wallet leaves the forward cohort and "
                           "its history is RETAINED. CFA Institute GIPS "
                           "3.A.9: 'Terminated portfolios must be included "
                           "in the historical performance of the composite "
                           "up to the last full measurement period that each "
                           "portfolio was under management.'"),
        "selection_bias_note": (
            f"{len(rejected)} candidate(s) were examined and rejected. "
            "That number is what the Deflated Sharpe is corrected for, and "
            "it is reported so the scan's selection bias is visible."),
    }
