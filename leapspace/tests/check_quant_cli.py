"""Verify the CLI wiring for the on-chain quant subcommands.

Checks that every quant command is registered, that each has a handler,
that --json is accepted everywhere, and that the operator brief's opening
question is available for the agent to ask.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from leapspace.cli import build_parser  # noqa: E402
from leapspace.quant import OPERATOR_OPENING  # noqa: E402

EXPECTED = ["chains", "profile", "consensus", "pool", "simulate",
            "risk", "anomaly", "audit"]

p = build_parser()
subs = p._subparsers._group_actions[0].choices  # type: ignore[attr-defined]
print(f"registered subcommands: {len(subs)}")
print(f"  {', '.join(sorted(subs))}")
print()

fails = []
for name in EXPECTED:
    if name not in subs:
        fails.append(f"{name}: NOT REGISTERED")
        continue
    sp = subs[name]
    has_func = sp.get_default("func") is not None
    has_json = any("--json" in a.option_strings
                   for a in sp._actions)  # type: ignore[attr-defined]
    flag = "OK " if (has_func and has_json) else "BAD"
    if not has_func:
        fails.append(f"{name}: no handler bound")
    if not has_json:
        fails.append(f"{name}: no --json flag")
    print(f"  [{flag}] {name:<10} handler={'yes' if has_func else 'NO'}  "
          f"--json={'yes' if has_json else 'NO'}")

# The pre-existing commands must still work.
for name in ("regime", "gamma", "memes", "wallet", "disclosure", "alerts",
             "backtest", "report"):
    if name not in subs:
        fails.append(f"{name}: REGRESSED - previously registered command gone")
    elif subs[name].get_default("func") is None:
        fails.append(f"{name}: REGRESSED - handler unbound")

print()
print(f"operator opening question: {OPERATOR_OPENING}")
print()
if fails:
    for f in fails:
        print("  FAIL " + f)
    sys.exit(1)
print("  ALL CLI WIRING CHECKS PASS")
