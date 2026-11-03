"""Test the results-file merge: a subset run must NOT shrink the file.

This is the footgun that a late background process could trigger:
`backtest --spec <one>` used to REPLACE backtest_results.json, so the
other twelve rows vanished and the consolidated report would describe a
run that no longer existed on disk.

Runs in a temp file -- it does not touch the real results.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from leapspace.cli import merge_backtest_results  # noqa: E402

REAL = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))),
    "reports", "backtest_results.json")

with open(REAL, "r", encoding="utf-8") as fh:
    real = json.load(fh)
print(f"real results file: {len(real)} rows")

fails = []

# --- case 1: a one-spec run must keep the other twelve -------------------
with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, "backtest_results.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(real, fh)
    one = [dict(real[0], verdict="REFRESHED")]
    out = merge_backtest_results(path, one)
    if len(out) != len(real):
        fails.append(f"case1: {len(out)} rows, expected {len(real)}")
    refreshed = [r for r in out if r["name"] == real[0]["name"]]
    if not refreshed or refreshed[0]["verdict"] != "REFRESHED":
        fails.append("case1: the refreshed row was not updated")
    if [r["name"] for r in out] != [r["name"] for r in real]:
        fails.append("case1: the file order changed")
    with open(path, "r", encoding="utf-8") as fh:
        after = json.load(fh)
    if len(after) != len(real):
        fails.append(f"case1: file on disk has {len(after)} rows")
    if not all((r.get("intake_gate") or {}).get("available") for r in after):
        fails.append("case1: the gate record was lost on merge")
    print(f"  case1 one-spec run on a {len(real)}-row file -> {len(out)} rows, "
          f"order preserved, refreshed verdict="
          f"{refreshed[0]['verdict'] if refreshed else 'n/a'}")

# --- case 2: a new spec name is ADDED, not ignored -----------------------
with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, "backtest_results.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(real, fh)
    fresh = [{"name": "brand_new_spec", "verdict": "SUPPORTED"}]
    out = merge_backtest_results(path, fresh)
    if len(out) != len(real) + 1:
        fails.append(f"case2: {len(out)} rows, expected {len(real) + 1}")
    print(f"  case2 new spec added -> {len(out)} rows")

# --- case 3: merging into a MISSING file must not crash ------------------
with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, "backtest_results.json")
    out = merge_backtest_results(path, [{"name": "solo", "verdict": "REFUTED"}])
    if len(out) != 1:
        fails.append(f"case3: {len(out)} rows, expected 1")
    print(f"  case3 merge into a missing file -> {len(out)} rows (no crash)")

# --- case 4: malformed stored file must not crash ------------------------
with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, "backtest_results.json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{not json at all")
    out = merge_backtest_results(path, [{"name": "solo", "verdict": "REFUTED"}])
    if len(out) != 1:
        fails.append(f"case4: {len(out)} rows, expected 1")
    print(f"  case4 merge into a corrupt file -> {len(out)} rows (no crash)")

print()
if fails:
    for f in fails:
        print("  FAIL " + f)
    sys.exit(1)
print("  ALL MERGE CASES PASS")
