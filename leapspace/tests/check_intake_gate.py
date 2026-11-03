"""Check the intake gate against every spec — no backtests, just the gate."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from leapspace.backtest import all_specs, apply_intake_gate  # noqa: E402

specs = all_specs()
print(f"{len(specs)} specs\n")
refused = 0
for s in specs:
    g = apply_intake_gate(s)
    name = s.get("name")
    if not g.get("available"):
        print(f"  {name:<52} GATE UNAVAILABLE: {g.get('note')}")
        continue
    before = g.get("missing_before") or []
    after = g.get("missing_after") or []
    auto = g.get("auto_accepted") or []
    if after:
        refused += 1
        print(f"  {name:<52} REFUSED  missing={after}")
        print(f"      provenance keys present: "
              f"{sorted((s.get('parameter_provenance') or {}).keys())[:8]}")
    else:
        print(f"  {name:<52} PASSED   gate flagged {before or '[]'} "
              f"-> auto-accepted {auto or '[]'}")

print(f"\nrefused: {refused} / {len(specs)}")

# ---------------------------------------------------------------------------
# NEGATIVE TEST: the gate must still be able to REFUSE.
#
# Auto-acceptance applies only to a DOCUMENTED condition. If a spec's
# provenance entry for a probed condition is removed, the gate has to refuse
# the spec rather than let it through. Without this, the gate is decorative.
# ---------------------------------------------------------------------------
print("\n=== NEGATIVE TEST: an undocumented condition must be REFUSED ===")
import copy  # noqa: E402

for target, strip in (("regime_switch_momentum_reversal_us_equity", "direction"),
                      ("regime_switch_cross_sectional_sector_rotation", "exit"),
                      ("v1_sd_band_mean_reversion_1_0_1_5", "universe")):
    spec = next(s for s in specs if s.get("name") == target)
    stripped = copy.deepcopy(spec)
    (stripped.get("parameter_provenance") or {}).pop(strip, None)
    # Also drop any pre-existing acceptance so the strip really bites.
    (stripped.get("intake") or {}).pop("accepted_defaults", None)
    g = apply_intake_gate(stripped)
    if g.get("missing_after"):
        print(f"  OK   {target}: stripping '{strip}' -> REFUSED "
              f"({g['missing_after']})")
    else:
        print(f"  FAIL {target}: stripping '{strip}' still PASSED -- "
              f"the gate is decorative")

