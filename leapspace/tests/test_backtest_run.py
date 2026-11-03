"""Run the paper-derived backtest specs through the engine."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from leapspace.backtest import (ENGINE_AVAILABLE, ENGINE_IMPORT_ERROR,
                                REGIME_SWITCH_SPECS, run_spec)

print("engine available:", ENGINE_AVAILABLE, ENGINE_IMPORT_ERROR)

only = sys.argv[1] if len(sys.argv) > 1 else None
quick = "--quick" in sys.argv
out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "reports")

for spec in REGIME_SWITCH_SPECS:
    if only and only not in spec["name"]:
        continue
    print("\n" + "=" * 70)
    print("SPEC:", spec["name"])
    print("=" * 70)
    res = run_spec(spec, quick=quick, out_dir=out_dir, verbose=True)
    print("\n--- RESULT ---")
    print("verdict:", res.verdict)
    print("flags:", res.flags)
    print("errors:", res.errors)
    m = res.metrics
    for k in ("n_bars", "n_trades", "sharpe", "cagr", "max_drawdown",
              "profit_factor", "win_rate", "t_stat"):
        if k in m:
            print(f"  {k} = {m[k]}")
    w = res.walk_forward
    for k in ("oos_sharpe", "oos_retention", "oos_profitable_folds",
              "n_folds", "is_sharpe"):
        if k in w:
            print(f"  wf.{k} = {w[k]}")
    if res.report_path:
        print("  report:", res.report_path)
