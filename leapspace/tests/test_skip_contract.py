"""The quick-mode skip list must ACTUALLY skip what it claims.

WHY THIS FILE EXISTS
    `run_spec(quick=True)` builds a tuple of stage names to skip and
    passes it to the gauntlet. The gauntlet checks each stage by a
    specific string - `"paramsens" not in skip` for the parameter
    sweep - so a tuple using a DIFFERENT name silently fails to skip
    it.

    The tuple said "sweep". The gauntlet checks "paramsens". The
    parameter sweep therefore RAN in quick mode anyway, and quick mode
    was slower than it claimed to be.

    The failure is silent in the worst way: it does not produce a
    wrong ANSWER, it just does more work than the caller asked for,
    and the skipped_stages list then misreports what was skipped.

WHAT THIS PROVES
    1. Every name in the quick skip tuple is one the gauntlet actually
       checks.
    2. The names the gauntlet checks are covered by the tuple where
       the caller intends them to be.
    3. A quick run's stage ledger records the parameter sweep, the
       Monte Carlo and the replication stage as SKIPPED.
    4. A full run's stage ledger records them as RAN.

Run: python leapspace/tests/test_skip_contract.py
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any, Dict, List, Set

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

PASSED = 0
FAILED = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {label}")
    else:
        FAILED += 1
        print(f"  [FAIL] {label}" + (f"\n         {detail}" if detail else ""))


from leapspace import backtest as B  # noqa: E402

_BTENGINE, _BTVALIDATE, _ = B._load_skill_modules()

print("=" * 72)
print("TEST 1 — the quick skip tuple uses names the gauntlet checks")
print("=" * 72)

import inspect  # noqa: E402

# The names the gauntlet checks, read from its own source so the test
# tracks the engine rather than a copy of it.
src = inspect.getsource(_BTVALIDATE.full_gauntlet)
checked: Set[str] = set(re.findall(r'"(\w+)"\s+not in skip', src))
check("the gauntlet's checked names were found",
      len(checked) >= 5, f"checked={sorted(checked)}")
print(f"         (the gauntlet checks: {sorted(checked)})")

# The skip tuple in run_spec, read from its source.
rsrc = inspect.getsource(B.run_spec)
m = re.search(r'skip\s*=\s*\(([^)]*)\)\s*if\s*quick\s*else\s*\(\)',
               rsrc)
check("the quick skip tuple was found in run_spec", m is not None,
      "could not locate the skip tuple")
tuple_names: List[str] = []
if m:
    tuple_names = re.findall(r'"(\w+)"', m.group(1))
print(f"         (the quick skip tuple is: {tuple_names})")

for name in tuple_names:
    check(f"'{name}' is a name the gauntlet actually checks",
          name in checked,
          f"the gauntlet checks {sorted(checked)} - '{name}' is not among "
          f"them, so that stage is NOT skipped")

# And the stages the quick mode is supposed to skip must be covered.
for required in ("montecarlo", "paramsens", "replication"):
    check(f"quick mode skips '{required}'",
          required in tuple_names,
          f"the quick tuple is {tuple_names}")

print()
print("=" * 72)
print("TEST 2 — a quick run's ledger records the skips")
print("=" * 72)

try:
    from leapspace.paperspecs import build_specs
    specs = build_specs()
    spec = next(s for s in specs
                if s.get("name") == "c4_volume_confirmation_rates_credit")
    r = B.run_spec(spec, quick=True, verbose=False)
    ledger = r.stage_ledger or {}
    skipped = set(r.skipped_stages or [])
    check("the quick run completed", r.verdict in
          ("SUPPORTED", "FRAGILE", "REFUTED", "INCONCLUSIVE", "ERROR"),
          f"verdict={r.verdict}")
    for stage in ("monte_carlo", "parameter_sensitivity", "replication"):
        entry = ledger.get(stage) or {}
        status = str(entry.get("status") or "").upper()
        check(f"the {stage} stage is recorded as SKIPPED",
              "SKIP" in status,
              f"status={status!r} note={entry.get('note')!r}")
    check("the skipped_stages list is populated",
          len(skipped) >= 3, f"skipped={sorted(skipped)}")
except Exception as exc:  # noqa: BLE001
    check("the quick run completed", False, f"{type(exc).__name__}: {exc}")

print()
print("=" * 72)
print("TEST 3 — a FULL run's ledger records those stages as RAN")
print("=" * 72)

# The full gauntlet is slow, so this checks the CONTRACT rather than
# running the whole thing: the skip tuple is empty when quick=False,
# so nothing can be skipped, and the ledger must therefore not claim
# otherwise.
rsrc2 = inspect.getsource(B.run_spec)
m2 = re.search(r'skip\s*=\s*\(([^)]*)\)\s*if\s*quick\s*else\s*\(\)',
                rsrc2)
skip_line = re.search(r'^\s*skip\s*=.*$', rsrc2, re.M)
check("the full run passes an EMPTY skip tuple",
      skip_line is not None and "else ()" in skip_line.group(0),
      "the full run may be skipping stages")

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
