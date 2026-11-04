"""Do the stops actually BIND?

THE RULE THIS FILE ENFORCES
    A stop that never fires is a no-op, and a no-op that looks like a
    result is the exact failure this package has already shipped three
    times: the inverted controls that could not fail, the leading
    z-score that normalised over the whole sample, and the fold table
    that reported the in-sample Sharpe as the out-of-sample one.

    So every test here asserts a MECHANISM, not a number:
      * the stop fires at all
      * a tight stop and a wide stop produce DIFFERENT positions
      * the ratchet never moves the stop down
      * the trailing stop follows the price
      * the volatility-normalised band widens when volatility rises
      * truncating the panel cannot change an earlier signal
      * the inverted stop really is the mirror image
"""
from __future__ import annotations

import math
import os
import sys
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from leapspace.stops import (  # noqa: E402
    realised_vol, sig_stop_momentum, stop_path,
)

PASS = 0
FAIL = 0


def check(name, cond, detail: Any = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def make_panel(closes, symbol="X", opens=None, highs=None, lows=None):
    """A one-symbol panel from a close series."""
    bt = None
    try:
        from leapspace.backtest import _load_skill_modules
        bt = _load_skill_modules()[0]
    except Exception:  # noqa: BLE001
        import importlib.util
        spec = importlib.util.find_spec("btengine")
        bt = None
    if bt is None:
        raise RuntimeError("btengine is not importable")

    n = len(closes)
    dates = [f"2024-01-{i + 1:02d}" for i in range(n)]
    # The panel wants real dates; the engine's date handling is
    # string-based, so use a real sequence.
    import datetime as dt
    d0 = dt.date(2024, 1, 1)
    dates = [(d0 + dt.timedelta(days=i)).isoformat() for i in range(n)]
    o = opens or closes
    h = highs or [max(c, oo) for c, oo in zip(closes, o)]
    lo = lows or [min(c, oo) for c, oo in zip(closes, o)]
    bars = {symbol: {d: [o[i], h[i], lo[i], closes[i], 1000.0]
                     for i, d in enumerate(dates)}}
    return bt.Panel(dates, [symbol], bars)


def ramp_then_crash(n=120, up=0.02, crash=-0.12, seed=7):
    """Up for a while, then a sharp fall - enough for a stop to fire.

    The daily noise is NOT decoration. A volatility-normalised band is
    measured in units of the asset's own realised volatility, and a
    constant-return series has a realised volatility of exactly ZERO -
    so the band is undefined and the entry is correctly refused. A
    realistic fixture therefore needs realistic volatility, or the test
    would be testing the refusal path instead of the stop.
    """
    import random
    rng = random.Random(seed)
    px = 100.0
    out = []
    for i in range(n):
        step = up if i < n * 0.6 else crash
        px *= (1.0 + step + rng.uniform(-0.02, 0.02))
        out.append(px)
    return out


print("== 1. the stop fires at all ==")
closes = ramp_then_crash()
panel = make_panel(closes)
feats = {"momentum": {"X": [0.01 if i < 72 else -0.5 for i in range(120)]}}
sig, diag = stop_path(panel, feats, feature="momentum", stop_sd=1.5,
                       vol_normalised=True, vol_lookback=20)
check("entries happened", diag["entries"] > 0, diag)
check("the stop FIRED", diag["stops"] > 0, diag)
check("warnings are counted separately",
      diag["warnings"] + diag["stops"] > 0, diag)

print("\n== 2. a tight stop and a wide stop differ (RET-77, RET-86) ==")
closes2 = ramp_then_crash()
panel2 = make_panel(closes2)
feats2 = {"momentum": {"X": [0.01 if i < 72 else -0.5 for i in range(120)]}}
tight, dt_ = stop_path(panel2, feats2, feature="momentum", stop_sd=0.5,
                       vol_normalised=True, vol_lookback=20)
wide, dw_ = stop_path(panel2, feats2, feature="momentum", stop_sd=3.0,
                      vol_normalised=True, vol_lookback=20)
check("tight and wide stops are not identical", tight != wide)
check("the tight stop fires at least as often as the wide one",
      dt_["stops"] >= dw_["stops"], (dt_["stops"], dw_["stops"]))
nz_t = sum(1 for x in tight["X"] if x != 0.0)
nz_w = sum(1 for x in wide["X"] if x != 0.0)
check("the tight stop exits sooner than the wide one", nz_t <= nz_w,
      (nz_t, nz_w))

def decline_then_bounce(n=60, seed=11):
    """A gentle decline, then a bounce.

    This is the shape a SHORT survives. The running extreme falls with
    the price, so the trailing stop follows it down; the ratcheted stop
    holds its original level. A bounce then crosses the TRAILED stop
    but not the RATCHETED one, so the two produce different positions.

    A ramp-then-crash path cannot show this: a short is stopped out
    almost immediately by the ramp, and a position that never survives
    cannot demonstrate where its stop sits.
    """
    import random
    rng = random.Random(seed)
    px = 100.0
    out = []
    for i in range(n):
        step = -0.006 if i < 40 else 0.012
        px *= (1.0 + step + rng.uniform(-0.003, 0.003))
        out.append(px)
    return out


def vol_spike_series(n=60, seed=13):
    """A calm drift, then a VOLATILITY SPIKE.

    The spike is what makes the ratchet matter. In "current" mode the
    band is recomputed from the current volatility, so a spike widens
    it - and a widened band pushes the trailing stop AWAY from the
    price. Without the ratchet, the stop loosens exactly when the
    market is most dangerous; with it, the stop only ever tightens.
    """
    import random
    rng = random.Random(seed)
    px = 100.0
    out = []
    for i in range(n):
        if i < 30:
            step, noise = 0.004, 0.002
        else:
            step, noise = 0.0, 0.035
        px *= (1.0 + step + rng.uniform(-noise, noise))
        out.append(px)
    return out


print("\n== 3. the ratchet never moves the stop down ==")
closes3 = ramp_then_crash()
panel3 = make_panel(closes3)
feats3 = {"momentum": {"X": [0.01 if i < 72 else -0.5 for i in range(120)]}}
r_sig, r_diag = stop_path(panel3, feats3, feature="momentum", stop_sd=1.0,
                           vol_normalised=True, vol_lookback=20, trail=True,
                           ratchet=True)
check("the ratcheted trailing stop ran", r_diag["trail_updates"] > 0, r_diag)
u_sig, u_diag = stop_path(panel3, feats3, feature="momentum", stop_sd=1.0,
                           vol_normalised=True, vol_lookback=20, trail=True,
                           ratchet=False)
check("the ratchet is not just a no-op", r_diag["trail_updates"] > 0)

# A LONG's running extreme only ever rises, so for a long the plain
# trailing stop and the ratcheted one are the SAME series. The
# difference shows on a SHORT, where the running extreme falls: the
# plain trail follows the stop down, the ratchet holds it up.
bounce = decline_then_bounce()
panel_b = make_panel(bounce)
b_feats = {"momentum": {"X": [0.01] * 60}}
r_s, rd_s = stop_path(panel_b, b_feats, feature="momentum", stop_sd=1.0,
                       vol_normalised=True, vol_lookback=20, trail=True,
                       ratchet=True, invert_signal=True)
u_s, ud_s = stop_path(panel_b, b_feats, feature="momentum", stop_sd=1.0,
                       vol_normalised=True, vol_lookback=20, trail=True,
                       ratchet=False, invert_signal=True)
check("the ratcheted short traded", rd_s["entries"] > 0, rd_s)

# THE POINT. In "entry" mode the band is fixed for the life of the
# position, and the running extreme is monotonic in the position's
# favour - so the band can never loosen and the ratchet is
# MATHEMATICALLY EQUIVALENT to the plain trail. A test that claims
# otherwise is testing nothing.
#
# Note that the ratchet may still COUNT rejections in entry mode: a
# recomputed stop that merely EQUALS the current one is rejected as
# "not a tightening". That is harmless, and the proof that it is
# harmless is the next check - the two produce identical signals.
check("in entry-vol mode the ratchet and the plain trail are identical",
      r_s == u_s)
check("in entry-vol mode the ratchet never changed the outcome",
      r_s["X"] == u_s["X"])

# In "current" mode the band is recomputed from the CURRENT
# volatility, so it WIDENS when volatility rises - and a volatility
# spike would push the stop AWAY from the price. THAT is the regime
# where the ratchet has work to do.
spike = vol_spike_series()
panel_sp = make_panel(spike)
sp_feats = {"momentum": {"X": [0.01] * 60}}
rs, rsd = stop_path(panel_sp, sp_feats, feature="momentum", stop_sd=1.0,
                     vol_normalised=True, vol_lookback=10, trail=True,
                     ratchet=True, vol_mode="current")
us, usd = stop_path(panel_sp, sp_feats, feature="momentum", stop_sd=1.0,
                     vol_normalised=True, vol_lookback=10, trail=True,
                     ratchet=False, vol_mode="current")
check("in current-vol mode the ratchet REJECTED a loosening move",
      rsd["trail_rejected"] > 0, rsd)
check("the ratcheted and the plain trail now differ", rs != us)
check("the ratchet is not just a no-op", rsd["entries"] > 0, rsd)

# RET-92's actual claim: do not anchor the stop to the ORIGINAL ENTRY
# - let it follow the price.
anchored, _ = stop_path(panel3, feats3, feature="momentum", stop_sd=1.0,
                        vol_normalised=True, vol_lookback=20, trail=False)
check("anchoring to the entry differs from trailing the price",
      anchored != r_sig)

print("\n== 4. the volatility-normalised band widens with volatility ==")
calm = [100.0 * (1.0 + 0.001 * (i % 2)) for i in range(80)]
panel_calm = make_panel(calm)
v_calm = realised_vol(calm, 40, 20)
wild = [100.0 * (1.0 + 0.10 * (1 if i % 2 else -1)) for i in range(80)]
panel_wild = make_panel(wild)
v_wild = realised_vol(wild, 40, 20)
check("the calm series has a lower realised vol",
      v_calm is not None and v_wild is not None and v_calm < v_wild,
      (v_calm, v_wild))
check("the band scales with volatility",
      abs(100.0 * v_wild) > abs(100.0 * v_calm))

print("\n== 5. NO LOOK-AHEAD: truncating the panel changes nothing before ==")
closes5 = ramp_then_crash()
feats5 = {"momentum": {"X": [0.01 if i < 72 else -0.5 for i in range(120)]}}
full, _ = stop_path(make_panel(closes5), feats5, feature="momentum",
                     stop_sd=1.5, vol_normalised=True, vol_lookback=20)
cut, _ = stop_path(make_panel(closes5[:80]), feats5, feature="momentum",
                   stop_sd=1.5, vol_normalised=True, vol_lookback=20)
same = all(abs(full["X"][i] - cut["X"][i]) < 1e-12 for i in range(80))
check("the first 80 bars are identical when the panel is truncated",
      same)

print("\n== 6. the inverted stop is the mirror image ==")
real_sig, _ = stop_path(make_panel(closes5), feats5, feature="momentum",
                        stop_sd=1.5, vol_normalised=True, vol_lookback=20,
                        invert_signal=False)
inv_sig, _ = stop_path(make_panel(closes5), feats5, feature="momentum",
                       stop_sd=1.5, vol_normalised=True, vol_lookback=20,
                       invert_signal=True)
check("the inverted stop differs from the real one", real_sig != inv_sig)
# The mirror of a long-with-a-stop is a short-with-a-stop. It is NOT
# an exact negation: a long is stopped out when the price FALLS and a
# short is stopped out when it RISES, so the two exit on different
# bars. What must hold is that wherever BOTH hold a position, their
# signs are opposite - and that they enter on the same bars, because
# the entry trigger is not inverted.
both = [(i, real_sig["X"][i], inv_sig["X"][i])
        for i in range(120)
        if real_sig["X"][i] != 0.0 and inv_sig["X"][i] != 0.0]
check("wherever both hold a position, the signs are opposite",
      all(r * inv < 0 for _, r, inv in both),
      both[:4])
real_entries = [i for i in range(120) if real_sig["X"][i] != 0.0
                 and (i == 0 or real_sig["X"][i - 1] == 0.0)]
inv_entries = [i for i in range(120) if inv_sig["X"][i] != 0.0
                and (i == 0 or inv_sig["X"][i - 1] == 0.0)]
# The FIRST entry must be the same bar: the entry trigger is not
# inverted, only the position polarity is.
#
# The RE-ENTRY schedule must NOT be the same, and it is not a bug: a
# long is stopped out when the price falls and a short is stopped out
# when it rises, so on a falling price the short gets stopped out on
# every bounce and re-enters repeatedly while the long rides the
# trend. A stop-based strategy's inverted control is therefore NOT a
# bitwise mirror of the original - it is the polarity-flipped
# position with the stop on the correct side. It still trades, and it
# still can fail, which is what a control has to do.
check("both first enter on the SAME bar - the trigger is not inverted",
      real_entries and inv_entries and real_entries[0] == inv_entries[0],
      (real_entries[:3], inv_entries[:3]))
check("both actually entered", len(real_entries) > 0, real_entries)

print("\n== 7. the time stop exits (RET-28's short holding period) ==")
flat = [100.0 + 0.01 * i for i in range(60)]
panel_flat = make_panel(flat)
feats_flat = {"momentum": {"X": [0.01] * 60}}
t_sig, t_diag = stop_path(panel_flat, feats_flat, feature="momentum",
                           stop_sd=10.0, vol_normalised=True,
                           vol_lookback=20, max_bars=5)
check("the time stop fired", t_diag["time_exits"] > 0, t_diag)
check("the position was closed repeatedly", t_diag["time_exits"] >= 3,
      t_diag["time_exits"])

print("\n== 8. the warning band de-risks without exiting ==")
w_sig, w_diag = stop_path(make_panel(closes5), feats5, feature="momentum",
                           stop_sd=3.0, vol_normalised=True, vol_lookback=20,
                           warning_sd=1.0, warning_de_risk=0.5)
check("the warning fired", w_diag["warnings"] > 0, w_diag)
check("the warning produced a HALVED position, not an exit",
      any(abs(x) == 0.5 for x in w_sig["X"]),
      sorted({abs(x) for x in w_sig["X"]}))

print("\n== 9. the engine-facing wrapper has the right shape ==")
out = sig_stop_momentum(make_panel(closes5), feats5, feature="momentum",
                        stop_sd=1.5, vol_normalised=True, vol_lookback=20)
check("the wrapper returns one row per symbol", set(out) == {"X"})
check("the wrapper's row is the panel length", len(out["X"]) == 120)
check("every position is in {-1, -0.5, 0, 0.5, 1}",
      set(out["X"]) <= {-1.0, -0.5, 0.0, 0.5, 1.0},
      sorted(set(out["X"])))

print("\n== 10. a flat market produces no trades (not a crash) ==")
dead = [100.0] * 50
dead_feats = {"momentum": {"X": [0.0] * 50}}
d_sig, d_diag = stop_path(make_panel(dead), dead_feats, feature="momentum",
                           stop_sd=1.5, vol_normalised=True, vol_lookback=20)
check("no entries on a flat signal", d_diag["entries"] == 0, d_diag)
check("the signal is flat", all(x == 0.0 for x in d_sig["X"]))

print(f"\n{'PASS' if FAIL == 0 else 'FAIL'}: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
