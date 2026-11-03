"""
Loads the LeapSpace 2.0 strategy specs.

The six specs in this file were distilled from
`Downloads/Trading_strategies_for_retail_traders_LeapSpace 2.0.pdf` by a
subagent that read the PDF directly and validated every spec against the
engine's feature/signal registries. They are kept in their own module rather
than inlined into `backtest.py` so the provenance is easy to audit.

Two defects the distillation found and fixed are worth keeping in view,
because both produced a plausible-looking but wrong backtest:

1. The Bollinger spec originally used `threshold: 0.0`. `bollinger_pct` is
   ALREADY standard-deviation-normalised, so "> 0" merely means "above the
   SMA" and never tested the +/-2 SD band the paper specifies — it produced
   results byte-identical to the moving-average spec. The threshold is now
   1.0, which IS the +2 SD upper band (the feature divides by nstd=2, so the
   band's normalised value is 2/2 = 1.0).

2. The RSI spec uses `direction: -1` on the `rsi` feature. That is a valid
   engine feature parameter, but it sits outside the plain `rsi(lookback)`
   parameter list, and it is DELIBERATE: without inversion the engine's
   threshold signal (which emits only 0 or +1) cannot express an oversold
   fade at all, because `RSI < 30` is untestable on a 0-100 scale with a `>`
   comparison.

Every parameter in every spec carries a `parameter_provenance` entry tagged
`paper` / `analyst_choice` / `engine_default`.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

SPEC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "data", "leapspace_2_0_specs.json")


def load_specs() -> List[Dict[str, Any]]:
    """Load the LeapSpace 2.0 specs from disk."""
    if not os.path.exists(SPEC_FILE):
        return []
    with open(SPEC_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def spec_summary() -> List[Dict[str, Any]]:
    out = []
    for s in load_specs():
        out.append({
            "name": s.get("name"),
            "paper": s.get("paper"),
            "hypothesis": s.get("hypothesis"),
            "signal": s.get("signal", {}).get("type"),
            "universe": s.get("universe"),
            "parameter_provenance": s.get("parameter_provenance", {}),
        })
    return out
