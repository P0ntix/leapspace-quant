"""Run the Phase A matrix: the paper's long/short rule and the pairs.

Writes to its OWN results file so the existing matrix is not clobbered
by a partial run. The two are merged only after the Phase A rows have
been verified.
"""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from leapspace.paperrun import run_matrix  # noqa: E402

REPORTS = os.path.join(ROOT, "reports")

SPECS = os.path.join(REPORTS, "phase_a_specs.json")
OUT = os.path.join(REPORTS, "phase_a_results.json")
LOG = os.path.join(REPORTS, "phase_a_run.log")


def main() -> int:
    specs = json.load(open(SPECS, encoding="utf-8"))
    t0 = time.time()
    print(f"running {len(specs)} Phase A specs -> {OUT}", flush=True)
    res = run_matrix(specs, quick=False, out_path=OUT, log_path=LOG)
    print(f"done in {time.time() - t0:.0f}s: {json.dumps(res, default=str)[:600]}",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
