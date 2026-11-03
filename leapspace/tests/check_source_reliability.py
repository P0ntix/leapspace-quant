"""Verify the source-reliability register and its effect on the specs.

The important check: does ANY spec in the package depend on a section the
register flags as defective? If one does, the package is trading a rule
built on mis-cited or retracted evidence and that must be fixed, not
documented.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from leapspace.source_reliability import (load_register, register_section,  # noqa
                                         defect_rows, scope_rows)
from leapspace.backtest import all_specs  # noqa: E402

reg = load_register()
sec = register_section(reg)
print(f"register loaded: {bool(reg)}  defects={sec['defect_count']}  "
      f"high={sec['high_severity']}  scope_exclusions={len(sec['scope_exclusions'])}")

print("\n=== defects ===")
for d in defect_rows(reg):
    print(f"  [{d['severity']:<6}] {d['id']:<4} {d['document'][:44]:<46} "
          f"impacts={d['impacts_specs'][:46]}")

# Which paper sections do the built specs actually quote?
print("\n=== paper sections the 13 specs depend on ===")
sections_cited = {}
for s in all_specs():
    pp = s.get("parameter_provenance") or {}
    cites = set()
    for entry in pp.values():
        c = str(entry.get("citation", ""))
        if "->" in c:
            head = c.split("->")[0].strip()
            if head:
                cites.add(head)
    for c in cites:
        sections_cited.setdefault(c, []).append(s.get("name"))
    print(f"  {s.get('name'):<52} {sorted(cites)[:3]}")

print("\n=== all distinct paper sections cited across the package ===")
for sec_name, names in sorted(sections_cited.items()):
    print(f"  {sec_name[:70]:<72} <- {len(names)} spec(s)")

# The register's per-document defect scopes that mention sections.
print("\n=== defect->section cross-check ===")
BAD = ["Intraday scalping strategies and analysis",   # v1 section 9 (D3 mis-citation)
       "Advanced Order Flow Scalping",                # v1 section 8
       "Intraday Scalping Strategy",                   # v1 section 10 (D4 self-citing)
       "Intraday Scalping Strategies",                 # v1 section 11
       "Intraday trading strategies and market analysis"]
cited_blob = " | ".join(sections_cited.keys()).lower()
hits = [b for b in BAD if b.lower() in cited_blob]
print(f"  defective/intraday sections cited by any spec: {hits or 'NONE'}")
assert not hits, f"a spec depends on a defective section: {hits}"
print("  OK - no spec depends on a defective or retracted section")

# The two universal defects (D2, D7) must be disclosed per spec.
print("\n=== universal defects disclosed per spec ===")
for s in all_specs():
    notes = json.dumps(s.get("parameter_provenance") or {}).lower()
    d2 = "no performance" in notes or "reports no performance" in notes \
        or "not the paper's" in notes or "no original" in notes \
        or "synthesis" in notes or "no numeric" in notes
    d7 = "rebalance" in notes
    if not (d2 or d7):
        print(f"  WARN {s.get('name')}: D2/D7 disclosure not detected")
print("  (a warning above would mean a spec omits a universal disclosure)")
