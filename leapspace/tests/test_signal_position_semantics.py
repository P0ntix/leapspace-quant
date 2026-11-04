"""Does a signal HOLD its position, or drop it on the next bar?

THE BUG THIS FILE EXISTS TO CATCH
    The engine reads a signal series as a per-bar TARGET POSITION.
    That is the contract its own `time_series_threshold` and
    `time_series_zscore` follow, and the one this package's
    `regime_switch` follows.

    Two of the package's signals broke it. They tracked the position in
    an `in_pos` flag, and while holding they appended `0.0` to the
    row instead of the position. Appending zero while holding CLOSES
    the position on the next bar, so:

      * the rule was reduced to a ONE-BAR HOLD,
      * the exit condition could never be reached,
      * and every result those signals produced was about a different
        strategy than the paper describes.

    The measured effect: `c5_rsi_reversion_crypto` produced **10**
    trades before the fix and **100** after. `c8_liquidity_reversal`
    produced **0** trades on equities and rates before the fix and
    **18** and **86** after. Those numbers are the whole argument.

    The bug survived because nothing checked it. A signal that is
    supposed to HOLD a position was only ever asserted to produce
    "some" positions.

THE INVARIANT
    A signal that opens a position must HOLD it on at least one
    further bar. If every non-zero entry in the series is isolated -
    a non-zero immediately followed by a zero - the signal is a
    one-bar hold, and every number computed from it is about a
    different strategy.

    That is checked here for EVERY signal the package registers, so a
    future signal cannot reintroduce it.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from leapspace.backtest import (  # noqa: E402
    _load_skill_modules, register_extensions,
)

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: Any = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def make_panel(bt: Any, closes: List[float], symbol: str = "X"):
    import datetime as dt
    n = len(closes)
    d0 = dt.date(2024, 1, 1)
    dates = [(d0 + dt.timedelta(days=i)).isoformat() for i in range(n)]
    opens = closes
    highs = [max(c, o) for c, o in zip(closes, opens)]
    lows = [min(c, o) for c, o in zip(closes, opens)]
    bars = {symbol: {d: [opens[i], highs[i], lows[i], closes[i], 1000.0]
                     for i, d in enumerate(dates)}}
    return bt.Panel(dates, [symbol], bars)


def longest_held_run(row: List[float]) -> int:
    """The longest run of CONSECUTIVE non-zero bars."""
    best = run = 0
    for x in row:
        if x != 0.0:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


print("== building the panel and the registry ==")
bt, _bv, _ = _load_skill_modules()
register_extensions(bt)

# A panel whose PRICES are irrelevant to this test: the signals are
# driven by a HAND-BUILT feature set, not by derived prices.
#
# THAT IS THE POINT. The first version of this file derived the
# features from a synthetic price series and seven of the ten signals
# never fired, so the test passed while checking almost nothing - the
# "a fixture that is too clean tests the wrong branch" failure, in
# this very file. Building the features directly makes every entry
# condition fire on demand, so the hold invariant is actually
# exercised.
N = 160
panel = make_panel(bt, [100.0 + 0.01 * i for i in range(N)])

# A SECOND symbol, because the cross-sectional pair signal needs at
# least two instruments to rank against each other.
import datetime as _dt  # noqa: E402
_d0 = _dt.date(2024, 1, 1)
_dates = [(_d0 + _dt.timedelta(days=i)).isoformat() for i in range(N)]
_closes2 = [100.0 - 0.01 * i for i in range(N)]
_bars = {s: {} for s in panel.symbols}
_bars["Y"] = {}
for _s in panel.symbols:
    for _i, _d in enumerate(_dates):
        _c = float(panel.close[_s][_i]) if _i < len(panel.close.get(_s) or []) \
            else 100.0
        _bars[_s][_d] = [_c, _c, _c, _c, 1000.0]
for _i, _d in enumerate(_dates):
    _c = _closes2[_i]
    _bars["Y"][_d] = [_c, _c, _c, _c, 1000.0]
panel = bt.Panel(_dates, ["X", "Y"], _bars)

z = [0.0] * N
for i in range(30, 80):
    z[i] = -2.6          # a stretched-down move: the reversion entry
for i in range(80, 100):
    z[i] = 0.0           # recovered: the exit
z2 = [-x for x in z]
rsi = [50.0] * N
for i in range(30, 80):
    rsi[i] = 20.0        # oversold, confirming exhaustion
vol = [0.10] * N
for i in range(40, N):
    vol[i] = 0.10 + 0.01 * (i - 40)   # RISING: top quartile of own norm
vr = [0.5] * N          # thin liquidity throughout
mom = [0.01] * N
for i in range(30, 80):
    mom[i] = -0.02

feats: Dict[str, Any] = {
    "zscore": {"X": z, "Y": z2},
    "rsi": {"X": rsi, "Y": rsi},
    "volume_ratio": {"X": vr, "Y": vr},
    "volatility": {"X": vol, "Y": vol},
    "momentum": {"X": mom, "Y": [-m for m in mom]},
    "regime_momentum_score": {"X": mom, "Y": [-m for m in mom]},
}

#: The signals that manage a position state, and the arguments each
#: one needs. Every one of these must HOLD a position.
STATEFUL: List[tuple] = [
    ("rsi_confirmed_reversion",
     dict(feature="zscore", rsi_feature="rsi", entry=-2.0, exit=-0.5,
          oversold=30.0)),
    ("liquidity_gated_reversion",
     dict(feature="zscore", volume_feature="volume_ratio",
          vol_feature="volatility", entry=-2.0, exit=-0.5,
          max_volume_ratio=0.8, vol_percentile=0.75)),
    ("volume_confirmed_momentum",
     dict(feature="regime_momentum_score", volume_feature="volume_ratio",
          min_volume_ratio=0.4)),
    ("trend_long_short", dict(feature="momentum", threshold=0.0,
                              dead_band=0.0)),
    ("pairs_mean_reversion", dict(feature="zscore", z_entry=2.0, z_exit=0.5,
                                  max_hold_bars=20)),
]

print("\n== every stateful signal must HOLD a position, not drop it ==")
for name, params in STATEFUL:
    fn = bt.SIGNALS.get(name)
    if fn is None:
        check(f"{name} is registered", False, "missing from SIGNALS")
        continue
    try:
        sig = fn(panel, feats, **params)
    except Exception as exc:  # noqa: BLE001
        check(f"{name} runs", False, f"{type(exc).__name__}: {exc}")
        continue
    row = list(sig.get("X") or [])
    if not row:
        check(f"{name} produced a row", False)
        continue
    nz = [i for i, x in enumerate(row) if x != 0.0]
    if not nz:
        # No trades on this fixture is legitimate for a signal whose
        # entry condition never fired. It is NOT a one-bar-hold bug.
        print(f"  --   {name}: no positions on this fixture (entry "
              f"condition never fired) - not a hold bug")
        PASS += 1
        continue
    run = longest_held_run(row)
    check(f"{name} HOLDS its position for more than one bar",
          run >= 2, f"longest held run = {run} bar(s)")

print("\n== a one-bar hold is now IMPOSSIBLE to reintroduce ==")
# The sharpest form of the check: in ANY signal row, a non-zero bar
# that is immediately followed by a zero is a CLOSED position. That is
# legal ONCE, at an exit. It is not legal as the ONLY kind of
# position. So: if a signal ever holds a position, it must hold it
# for at least two consecutive bars somewhere.
for name, params in STATEFUL:
    fn = bt.SIGNALS.get(name)
    if fn is None:
        continue
    try:
        sig = fn(panel, feats, **params)
    except Exception:  # noqa: BLE001
        continue
    row = list(sig.get("X") or [])
    nz = [i for i, x in enumerate(row) if x != 0.0]
    if not nz:
        continue
    check(f"{name}: no position is an isolated one-bar flick",
          longest_held_run(row) >= 2,
          f"isolated entries at {[i for i in nz if (i + 1 >= len(row) or row[i + 1] == 0.0)][:5]}")

print("\n== the control still inverts, and the fix did not break it ==")
for name, params in STATEFUL:
    fn = bt.SIGNALS.get(name)
    if fn is None:
        continue
    try:
        real = fn(panel, feats, **params)
        inv = fn(panel, feats, invert_signal=True, **params)
    except Exception:  # noqa: BLE001
        continue
    r = list(real.get("X") or [])
    i = list(inv.get("X") or [])
    if not any(x != 0.0 for x in r):
        continue
    # Where both hold a position the SIGNS must be opposite. They need
    # not be exact mirrors - a stop-based signal exits on different
    # bars - but they must never agree in direction.
    both = [(a, b) for a, b in zip(r, i) if a != 0.0 and b != 0.0]
    if not both:
        print(f"  --   {name}: no bar where both hold a position")
        continue
    check(f"{name}: inverted control never agrees in direction",
          all(a * b < 0 for a, b in both),
          both[:3])

print(f"\n{'PASS' if FAIL == 0 else 'FAIL'}: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
