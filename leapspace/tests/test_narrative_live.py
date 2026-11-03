"""LIVE TEST of the narrative-specificity classifier.

Screens a real cohort of memecoins, then asks the questions that matter:

  1. Does the classifier DISCRIMINATE? (spread of scores, not all-same)
  2. What is the COHORT BASELINE, and does it separate niche from generic?
  3. Does the paper's PERFORMANCE claim hold on this sample? (backward,
     clearly labelled as backward)
  4. Is the FORWARD test wired? (it needs two snapshots in time)

Everything printed is what was actually observed.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from leapspace.memecoin import screen_search  # noqa: E402
from leapspace.narrative import (cohort_baseline, relative_to_cohort,  # noqa
                                 verify_cohort)

QUERIES = ["pepe", "dog", "cat", "moon", "ai", "elon", "trump", "meme"]

print("=" * 78)
print("LIVE COHORT - screening memecoins across trend keywords")
print("=" * 78)

all_rows = []
seen = set()
for q in QUERIES:
    try:
        res = screen_search(q, limit=6)
    except Exception as exc:  # noqa: BLE001
        print(f"  {q:<8} FAILED {type(exc).__name__}: {str(exc)[:70]}")
        continue
    cohort = res.get("narrative_cohort") or {}
    base = cohort.get("baseline") or {}
    for r in res.get("results", []):
        mint = r.get("mint")
        if mint in seen:
            continue
        seen.add(mint)
        spec = (r.get("layers", {}).get("narrative_heat") or {}).get("SPECIFICITY") or {}
        eq = r.get("layers", {}).get("exit_quality") or {}
        all_rows.append({
            "mint": mint, "symbol": r.get("symbol"),
            "specificity_score": spec.get("specificity_score"),
            "is_niche": spec.get("is_niche"),
            "price_usd": eq.get("price_usd"),
            "price_change_24h": eq.get("price_change_24h"),
            "liquidity_usd": eq.get("liquidity_usd"),
        })
    print(f"  {q:<8} screened={res.get('screened')} passed={res.get('passed')} "
          f"niche_in_cohort={base.get('niche_count')}/{base.get('n')} "
          f"median_score={base.get('median')}")

print()
print(f"UNIQUE COHORT: {len(all_rows)} tokens")

print()
print("=" * 78)
print("1. DOES THE CLASSIFIER DISCRIMINATE?")
print("=" * 78)
base = cohort_baseline(all_rows)
print(f"  baseline: {json.dumps({k: v for k, v in base.items() if k != 'note'})}")
scores = [r["specificity_score"] for r in all_rows if r["specificity_score"] is not None]
if scores:
    print(f"  score spread: min={min(scores)} max={max(scores)} "
          f"distinct={len(set(scores))}")
    print(f"  -> {'DISCRIMINATES' if len(set(scores)) > 3 else 'FLAT - barely varies'}")
for r in sorted(all_rows, key=lambda x: -(x["specificity_score"] or 0)):
    rel = relative_to_cohort(r, base)
    print(f"    {str(r['symbol'])[:14]:<15} score={r['specificity_score']:<6} "
          f"niche={str(r['is_niche']):<6} {rel['relative']:<16} "
          f"h24={r['price_change_24h']}")

print()
print("=" * 78)
print("2. THE COHORT BASELINE (the 'generic' comparison the clause needed)")
print("=" * 78)
print(f"  {base.get('note')}")
below = [r for r in all_rows
         if relative_to_cohort(r, base).get("is_generic_vs_peers")]
print(f"  tokens in the bottom quartile (generic vs peers): "
      f"{[r['symbol'] for r in below]}")

print()
print("=" * 78)
print("3. DOES THE PAPER'S PERFORMANCE CLAIM HOLD ON THIS SAMPLE?")
print("=" * 78)
from leapspace.narrative import backward_association  # noqa: E402
assoc = backward_association(all_rows)
for k, v in assoc.items():
    print(f"  {k}: {v}")

print()
print("=" * 78)
print("4. IS THE FORWARD TEST WIRED?")
print("=" * 78)
v = verify_cohort(current_rows=all_rows, min_gap_seconds=3600)
for k, val in v.items():
    print(f"  {k}: {val}")
print("  (a forward test needs two snapshots separated in time; until then "
      "the verdict is 'not yet measurable', never 'no effect')")
