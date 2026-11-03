"""Regression tests for the narrative forward-test base selection.

The bug these lock down: `cmd_narrative` (which re-prices the cohort) and
`verify_cohort` (which computes the forward return) each chose a BASE
observation independently. The CLI used a first-row-wins dedup over the
whole snapshot history, so any token first seen BEFORE the pool-address
fix was dropped entirely - even when a LATER snapshot of the same token
had recorded its pool. In the observed history that dropped every NICHE
token, emptying the niche bucket and making the forward test
uninterpretable while still printing a confident-looking verdict.

These tests are OFFLINE: no network, no live DexScreener. They use
temporary snapshot files, because verify_cohort reads its snapshots from
DISK (that is the whole point - a later run must see an earlier run's
snapshot).
"""
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from leapspace.narrative import select_base_rows, verify_cohort  # noqa: E402

FAIL = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        FAIL.append(name)


NOW = int(time.time())
OLD = NOW - 7200          # 2 hours ago: old enough to qualify
MID = NOW - 4000          # also qualifies
NEW = NOW - 60            # too recent: must be ignored


def snap(ts, rows):
    return {"ts": ts, "n": len(rows), "rows": rows}


def row(mint, price, pair=None, niche=False):
    return {"mint": mint, "symbol": mint[:4], "price_usd": price,
            "is_niche": niche, "pair_address": pair}


def write_snapshots(snaps):
    """Write snapshots to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json", prefix="narrative_test_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"snapshots": snaps}, fh)
    return path


print("=" * 78)
print("1. A TOKEN FIRST SEEN WITHOUT A POOL IS STILL MEASURABLE FROM A")
print("   LATER SNAPSHOT THAT RECORDED ONE")
print("=" * 78)
snaps = [
    # NICHE token, first seen with NO pool address (pre-fix snapshot)
    snap(OLD, [row("NICHE1", 1.0, pair=None, niche=True)]),
    # same token, later snapshot, WITH pool address
    snap(MID, [row("NICHE1", 2.0, pair="POOL1", niche=True)]),
    # a token that ONLY ever lacked a pool address
    snap(OLD, [row("NOPOOL", 5.0, pair=None, niche=False)]),
]
base, no_pair = select_base_rows(snaps, now=NOW, min_gap_seconds=3600)
check("niche token with a later pool snapshot is in the base set",
      "NICHE1" in base, f"base keys={list(base)}")
check("its base is the EARLIEST row that RECORDED a pool",
      base.get("NICHE1", {}).get("price_usd") == 2.0,
      f"got {base.get('NICHE1', {}).get('price_usd')}")
check("its base carries the pool address",
      base.get("NICHE1", {}).get("pair_address") == "POOL1")
check("a token with no pool anywhere is NOT in the base set",
      "NOPOOL" not in base)
check("the no-pool row is reported as skipped",
      "NOPOOL" in no_pair, f"no_pair={no_pair}")

print()
print("=" * 78)
print("2. RECENT SNAPSHOTS ARE NOT ELIGIBLE BASES")
print("=" * 78)
snaps2 = [
    snap(MID, [row("TOK", 1.0, pair="POOLX")]),
    snap(NEW, [row("TOK", 9.0, pair="POOLX")]),
]
base2, _ = select_base_rows(snaps2, now=NOW, min_gap_seconds=3600)
check("base is the old snapshot, not the recent one",
      base2.get("TOK", {}).get("price_usd") == 1.0,
      f"got {base2.get('TOK', {}).get('price_usd')}")

print()
print("=" * 78)
print("3. verify_cohort AND THE CLI's BASE SELECTION AGREE")
print("=" * 78)
# The CLI prices the pool named in the base row; verify_cohort must then
# compare that same pool. If the two disagreed, every token would be
# dropped as a pair mismatch.
snaps3 = [
    snap(OLD, [row("A", 1.0, pair=None, niche=True),
               row("B", 2.0, pair=None, niche=False)]),
    snap(MID, [row("A", 4.0, pair="PA", niche=True),
               row("B", 8.0, pair="PB", niche=False)]),
]
base3, _ = select_base_rows(snaps3, now=NOW, min_gap_seconds=3600)
current = []
for mint, b in base3.items():
    current.append({"mint": mint, "symbol": b["symbol"],
                    "is_niche": b["is_niche"], "price_usd": b["price_usd"] * 1.1,
                    "pair_address": b["pair_address"]})
path3 = write_snapshots(snaps3)
v = verify_cohort(path=path3, current_rows=current, min_gap_seconds=3600)
os.unlink(path3)
check("both tokens matched (no spurious pair mismatch)",
      v.get("n_matched") == 2, f"n_matched={v.get('n_matched')}")
check("no pair mismatches", v.get("skipped_pair_mismatch") == 0,
      f"mismatch={v.get('skipped_pair_mismatch')}")
check("niche bucket populated", v.get("n_niche") == 1,
      f"n_niche={v.get('n_niche')}")
check("returns computed against the pinned pool",
      v.get("matched") and all(abs(m["forward_return_pct"] - 10.0) < 0.01
                               for m in v["matched"]),
      f"matched={v.get('matched')}")

print()
print("=" * 78)
print("4. A MISMATCHED POOL IS SKIPPED, NOT COMPARED")
print("=" * 78)
current_bad = [{"mint": "A", "symbol": "A", "is_niche": True,
                "price_usd": 4.4, "pair_address": "DIFFERENT"},
               {"mint": "B", "symbol": "B", "is_niche": False,
                "price_usd": 8.8, "pair_address": "PB"}]
path4 = write_snapshots(snaps3)
v2 = verify_cohort(path=path4, current_rows=current_bad,
                   min_gap_seconds=3600)
os.unlink(path4)
check("the mismatched token is skipped", v2.get("n_matched") == 1,
      f"n_matched={v2.get('n_matched')}")
check("the mismatch is counted", v2.get("skipped_pair_mismatch") == 1,
      f"mismatch={v2.get('skipped_pair_mismatch')}")

print()
print("=" * 78)
print("5. NOT YET MEASURABLE IS NOT 'NO EFFECT'")
print("=" * 78)
snaps5 = [snap(NOW - 100, [row("X", 1.0, pair="PX")])]
base5, _ = select_base_rows(snaps5, now=NOW, min_gap_seconds=3600)
check("a snapshot younger than the gap yields no base", len(base5) == 0)
path5 = write_snapshots(snaps5)
v3 = verify_cohort(path=path5, min_gap_seconds=3600,
                   current_rows=[{"mint": "X", "symbol": "X",
                                  "is_niche": True, "price_usd": 2.0,
                                  "pair_address": "PX"}])
os.unlink(path5)
check("status is 'not yet measurable'",
      v3.get("status") == "not yet measurable", f"status={v3.get('status')}")
check("supports_claim is absent, not False",
      "supports_claim" not in v3, f"keys={list(v3)}")

print()
print("=" * 78)
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s): {FAIL}")
    sys.exit(1)
print("ALL CHECKS PASSED")
