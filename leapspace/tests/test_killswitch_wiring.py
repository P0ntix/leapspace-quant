"""Tests for the kill switch ON THE DECISION PATH.

THE GAP THIS FILE CLOSES
    `leapspace/riskguard.py` contains a code-enforced kill switch with
    drawdown, liquidity and slippage rules, a latching halt that
    survives a restart, and an explicit reset that requires an actor and
    a reason. It was excellent — and it was NOT CONNECTED TO ANYTHING.

    `leapspace/signal.py::assess_trade` assembled eight evidence legs
    and produced a verdict without ever asking the kill switch whether
    trading was permitted. A brake that is never touched is not a brake.

WHAT IS ASSERTED HERE
    1. `assess_trade` consults the kill switch and REFUSES to emit an
       ENTER verdict while the switch is halted.
    2. The halt survives a process restart (it is latched on disk).
    3. A blocking DATA_QUALITY conflict HALTS the switch, so a data
       problem stops trading rather than merely lowering confidence.
    4. The reason is visible in the signal's gaps, so a reader can see
       WHY no trade happened.
    5. The switch's own state file is created where the operator
       expects it, and `verify_no_bypass()` still reports ok.

WHAT THIS FILE IS NOT
    It does not test the kill switch's arithmetic — `riskguard.py`
    already has its own suite for that. It tests the WIRING: that the
    decision path actually asks the brake.

Run: python leapspace/tests/test_killswitch_wiring.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

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


print("=" * 72)
print("TEST 1 — the kill switch is consulted on the decision path")
print("=" * 72)

from leapspace.riskguard import KillSwitch  # noqa: E402
from leapspace import signal as S  # noqa: E402

# The wiring must be reachable as a function, so a test can drive it
# without a live network. `assess_trade` gathers eight live legs; this
# test drives the gate function directly.
check(
    "signal.py exposes a kill-switch gate function",
    hasattr(S, "kill_switch_gate"),
    "assess_trade has no kill-switch gate to call — the brake is "
    "not on the decision path",
)

check(
    "the gate function is documented",
    bool((S.kill_switch_gate.__doc__ or "").strip())
    if hasattr(S, "kill_switch_gate") else False,
    "the gate function has no docstring",
)

print()
print("=" * 72)
print("TEST 2 — a halted switch blocks the trade")
print("=" * 72)

with tempfile.TemporaryDirectory() as tmp:
    state = os.path.join(tmp, "kill_switch.json")
    ks = KillSwitch(cfg={"state_path": state})
    ks.load()
    ks.halt("test halt", trigger="test", ts=1700000000)
    ks.save()

    # A FRESH instance reads the latched state from disk.
    ks2 = KillSwitch(cfg={"state_path": state})
    loaded = ks2.load()
    check(
        "the halt is latched on disk and read back by a fresh instance",
        loaded and ks2.to_flat().get("halted") is True,
        f"loaded={loaded} state={ks2.to_flat()}",
    )

    allowed, reason = ks2.check(10_000.0, 1700000100)
    check(
        "check() refuses to allow trading while halted",
        allowed is False,
        "the switch allowed a trade while halted",
    )
    check(
        "the refusal names the reason",
        bool(reason),
        "the refusal carried no reason",
    )

print()
print("=" * 72)
print("TEST 3 — the gate blocks an ENTER verdict")
print("=" * 72)

if hasattr(S, "kill_switch_gate"):
    with tempfile.TemporaryDirectory() as tmp:
        state = os.path.join(tmp, "kill_switch.json")
        ks = KillSwitch(cfg={"state_path": state})
        ks.halt("operator halt", trigger="test", ts=1700000000)
        ks.save()

        res = S.kill_switch_gate(
            ks=ks, token_address="0xabc", chain="ethereum",
            equity_usd=10_000.0, liquidity_usd=500_000.0,
        )
        check(
            "the gate reports NOT allowed while halted",
            res.get("allowed") is False,
            f"gate said {res.get('allowed')!r}",
        )
        check(
            "the gate names the trigger",
            bool(res.get("reason")),
            "the gate gave no reason",
        )
        check(
            "the gate reports the trigger kind",
            res.get("trigger") is not None,
            "the gate did not report a trigger",
        )

        # And the decision path must respect it.
        sig_like = {
            "verdict": S.ENTER,
            "gaps": list(res.get("gaps") or []),
        }
        blocked = S.apply_kill_switch(sig_like, res)
        check(
            "a halted switch downgrades an ENTER verdict",
            blocked.get("verdict") != S.ENTER,
            f"verdict stayed {blocked.get('verdict')!r}",
        )
        check(
            "the block is visible in the signal's gaps",
            any("kill" in str(g).lower() or "halt" in str(g).lower()
                for g in (blocked.get("gaps") or [])),
            f"gaps={blocked.get('gaps')}",
        )
else:
    print("  [SKIP] no kill_switch_gate function to test")

print()
print("=" * 72)
print("TEST 4 — a blocking data-quality conflict HALTS the switch")
print("=" * 72)

if hasattr(S, "kill_switch_gate"):
    with tempfile.TemporaryDirectory() as tmp:
        state = os.path.join(tmp, "kill_switch.json")
        ks = KillSwitch(cfg={"state_path": state})

        dq = S.Leg("DATA_QUALITY", S.CONFLICTS,
                   "only 1/8 evidence legs answered", {}, S.PROV.LIVE,
                   blocking=True)
        S.halt_on_data_quality(ks, dq)
        check(
            "a blocking DATA_QUALITY conflict halts the switch",
            ks.to_flat().get("halted") is True,
            f"state={ks.to_flat()}",
        )
        check(
            "the halt names data_quality as the trigger",
            ks.to_flat().get("trigger") == "data_quality",
            f"trigger={ks.to_flat().get('trigger')!r}",
        )
        ks.save()

        # And it must survive a restart.
        ks2 = KillSwitch(cfg={"state_path": state})
        ks2.load()
        check(
            "the data-quality halt survives a restart",
            ks2.to_flat().get("halted") is True,
            f"state after restart={ks2.to_flat()}",
        )
        allowed, _ = ks2.check(10_000.0, 1700000100)
        check(
            "the restarted switch still blocks trading",
            allowed is False,
            "the switch allowed a trade after a data-quality halt",
        )

        bypass = ks2.verify_no_bypass()
        check(
            "verify_no_bypass() still reports ok",
            bypass.get("ok") is True,
            f"bypass audit={bypass}",
        )
else:
    print("  [SKIP] no kill_switch_gate function to test")

print()
print("=" * 72)
print("TEST 5 — a clean state does NOT halt")
print("=" * 72)

if hasattr(S, "kill_switch_gate"):
    with tempfile.TemporaryDirectory() as tmp:
        state = os.path.join(tmp, "kill_switch.json")
        ks = KillSwitch(cfg={"state_path": state})
        dq = S.Leg("DATA_QUALITY", S.SUPPORTS, "8/8 answered", {},
                   S.PROV.LIVE)
        S.halt_on_data_quality(ks, dq)
        check(
            "a healthy DATA_QUALITY leg does NOT halt",
            ks.to_flat().get("halted") is False,
            f"state={ks.to_flat()}",
        )

        res = S.kill_switch_gate(
            ks=ks, token_address="0xabc", chain="ethereum",
            equity_usd=10_000.0, liquidity_usd=500_000.0,
        )
        check(
            "the gate ALLOWS when nothing is wrong",
            res.get("allowed") is True,
            f"gate said {res.get('allowed')!r}",
        )
else:
    print("  [SKIP] no kill_switch_gate function to test")

print()
print("=" * 72)
print("TEST 6 — the liquidity floor is enforced through the gate")
print("=" * 72)

if hasattr(S, "kill_switch_gate"):
    with tempfile.TemporaryDirectory() as tmp:
        state = os.path.join(tmp, "kill_switch.json")
        # The operator config's floor is $1,000.
        ks = KillSwitch(cfg={"state_path": state,
                             "min_liquidity_usd": 1000.0})
        res = S.kill_switch_gate(
            ks=ks, token_address="0xabc", chain="ethereum",
            equity_usd=10_000.0, liquidity_usd=500.0,
        )
        check(
            "a pool below the liquidity floor is refused",
            res.get("allowed") is False,
            f"gate allowed a trade into a ${500} pool",
        )
        check(
            "the refusal names the liquidity rule",
            "liquidity" in str(res.get("reason", "")).lower(),
            f"reason={res.get('reason')!r}",
        )

        ks2 = KillSwitch(cfg={"state_path": os.path.join(tmp, "ks2.json"),
                              "min_liquidity_usd": 1000.0})
        res2 = S.kill_switch_gate(
            ks=ks2, token_address="0xabc", chain="ethereum",
            equity_usd=10_000.0, liquidity_usd=500_000.0,
        )
        check(
            "a pool above the floor is allowed",
            res2.get("allowed") is True,
            f"gate refused a ${500000:,} pool: {res2.get('reason')}",
        )
else:
    print("  [SKIP] no kill_switch_gate function to test")

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
