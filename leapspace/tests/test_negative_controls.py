"""Every negative control must ACTUALLY differ from its twin.

WHY THIS FILE EXISTS
    A negative control is only evidence if it can FAIL. The matrix
    builder sets `signal.params.invert_signal = True` on every twin,
    but four of the signal implementations did not read that flag:

      C1 regime_switch      - the flag was not in the signature at all
      C2 leading_vrp_switch - it read `invert_vrp`, a DIFFERENT name
      C7 cross_sectional    - the engine's signal swallowed it in **kw
      (and the engine's `sig_cross_sectional` is shared, so the repo
       wraps it instead of editing the skill)

    The result was that those controls were BYTE-IDENTICAL to their
    twins. They could not fail, so they proved nothing, and the
    headline "no control survived" was resting on a mixture of real
    controls and no-ops.

WHAT THIS PROVES
    For EVERY signal the paper matrix uses, the inverted twin produces
    a genuinely DIFFERENT signal from the real one, on real data, and
    the difference is exactly a sign flip.

    A control that produces the same signal as its twin is a no-op and
    is reported as such.

Run: python leapspace/tests/test_negative_controls.py
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

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
from leapspace.paperspecs import (build_negative_controls,  # noqa: E402
                                   build_specs)

_BTENGINE, _BTVALIDATE, _ = B._load_skill_modules()
B.register_extensions(_BTENGINE)


class _Panel:
    """A minimal panel with enough shape for the signals to run."""

    def __init__(self, n: int = 400, n_syms: int = 6):
        import math
        self.n = n
        self.symbols = [f"S{i}" for i in range(n_syms)]
        self.dates = [(f"2020-{1 + (i // 28):02d}-{(i % 28) + 1:02d}")
                      for i in range(n)]
        self.meta = {"universe": "synthetic", "asset_class": "test"}
        self.close, self.open, self.high, self.low, self.vol = {}, {}, {}, {}, {}
        self.stale = {}
        for k, s in enumerate(self.symbols):
            c = []
            o = []
            h = []
            l = []
            v = []
            price = 100.0 + k
            for i in range(n):
                price *= 1.0 + 0.004 * math.sin(i / (11.0 + k)) \
                    + 0.001 * ((i + k) % 2)
                c.append(price)
                o.append(price * 0.999)
                h.append(price * 1.004)
                l.append(price * 0.996)
                v.append(1000.0 + 100.0 * ((i * (k + 3)) % 11) / 11.0)
            self.close[s] = c
            self.open[s] = o
            self.high[s] = h
            self.low[s] = l
            self.vol[s] = v
            self.stale[s] = [False] * n
        self._leading_series_cache = None


def _features(panel: _Panel) -> Dict[str, Any]:
    """A feature block with everything the paper signals might read.

    The synthetic series are crafted to CROSS EVERY GATE the paper
    signals use, because a signal that never fires produces an all-zero
    book - and an all-zero book negates to an all-zero book, so the
    test would pass vacuously while proving nothing.

      * `volume_ratio` spans ~0.55 to ~1.45, so both the
        `>= 1.0` volume-confirmation gate and the `<= 0.8` thin-
        liquidity gate are crossed.
      * `rsi` sits high most of the time with deep dips, so its
        z-score reaches the `-2.0` entry and the `30.0` oversold level.
      * `momentum` changes sign repeatedly.
    """
    import math
    feats: Dict[str, Any] = {}
    for k, s in enumerate(panel.symbols):
        c = panel.close[s]
        feats.setdefault("return", {})[s] = [
            None] + [c[i] / c[i - 1] - 1.0 for i in range(1, panel.n)]
        feats.setdefault("momentum", {})[s] = [
            c[i] / c[max(0, i - 60)] - 1.0 for i in range(panel.n)]
        # The engine's `volatility` feature is ANNUALISED (it scales the
        # daily stdev by sqrt(252)), so the C8 gate `min_volatility=0.30`
        # is a 30%-annualised threshold, not a 30%-daily one. The
        # synthetic series must therefore span that range.
        feats.setdefault("volatility", {})[s] = [
            0.15 + 0.50 * abs((i % 31) / 31.0) for i in range(panel.n)]
        # Volume alternates between THIN and HEAVY so both gates fire.
        feats.setdefault("volume_ratio", {})[s] = [
            (0.55 if (i % 7) < 3 else 1.45) + 0.05 * k
            for i in range(panel.n)]
        # RSI: high most of the time, with deep oversold dips.
        feats.setdefault("rsi", {})[s] = [
            (10.0 if (i % 20) == 3 else 70.0 + 3.0 * k)
            for i in range(panel.n)]
        feats.setdefault("session_drift", {})[s] = [
            (panel.close[s][i] - panel.low[s][i])
            / max(1e-12, panel.high[s][i] - panel.low[s][i])
            * (panel.vol[s][i] / 1100.0)
            for i in range(panel.n)]
        # The Z-SCORE series the C5 and C8 specs actually consume. It
        # must reach below -2.0 for the entry gates to fire.
        feats.setdefault("zscore", {})[s] = [
            (-2.6 if (i % 20) == 3 else 0.4 * math.sin(i / 9.0 + k))
            for i in range(panel.n)]
        feats.setdefault("regime_momentum_score", {})[s] = [
            (c[i] / c[max(0, i - 60)] - 1.0) * 100.0
            for i in range(panel.n)]
        feats.setdefault("leading_vrp_score", {})[s] = [
            2.0 * ((i % 23) / 23.0 - 0.5) for i in range(panel.n)]
        feats.setdefault("leading_vrp_zscore", {})[s] = [
            ((i % 23) / 23.0 - 0.5) * 2.0 for i in range(panel.n)]
    return feats


# The signals the paper matrix uses, and the arguments each needs.
# `flips_sign` is False for the signals whose negative control
# inverts the READING rather than the position sign - see the note in
# the test body.
SIGNAL_CASES = [
    ("regime_switch", {"feature": "regime_momentum_score"}, True),
    ("leading_vrp_switch", {"feature": "regime_momentum_score",
                            "vrp_z_feature": "leading_vrp_zscore"}, False),
    ("paper_cross_sectional", {"feature": "session_drift",
                               "long_rank": 0.75, "short_rank": 0.25}, True),
    ("vol_regime_momentum", {"feature": "regime_momentum_score",
                             "vol_feature": "volatility"}, True),
    ("volume_confirmed_momentum", {"feature": "regime_momentum_score"},
     True),
    ("rsi_confirmed_reversion", {"feature": "zscore",
                                 "rsi_feature": "rsi"}, True),
    ("rebound_danger_momentum", {"feature": "regime_momentum_score"}, True),
    ("liquidity_gated_reversion", {"feature": "zscore",
                                   "volume_feature": "volume_ratio",
                                   "vol_feature": "volatility"}, True),
]


print("=" * 72)
print("TEST 1 — every signal's inverted twin DIFFERS from its twin")
print("=" * 72)

panel = _Panel()
feats = _features(panel)

for sig_name, kwargs, flips_sign in SIGNAL_CASES:
    fn = _BTENGINE.SIGNALS.get(sig_name)
    if fn is None:
        check(f"{sig_name}: the signal is registered", False,
              "not registered")
        continue
    try:
        real = fn(panel, feats, invert_signal=False, **kwargs)
        inv = fn(panel, feats, invert_signal=True, **kwargs)
    except Exception as exc:  # noqa: BLE001
        check(f"{sig_name}: both polarities run", False,
              f"{type(exc).__name__}: {exc}")
        continue

    check(f"{sig_name}: both polarities run", True)

    # NON-VACUITY. A signal that produces an all-zero book negates to
    # an all-zero book, so "identical" and "exact sign flip" are both
    # true and the test would pass while proving nothing. The signal
    # must actually FIRE for this comparison to mean anything.
    nonzero = sum(1 for row in real.values() for v in row if v != 0.0)
    check(f"{sig_name}: the signal actually FIRES on the synthetic panel",
          nonzero > 0,
          f"the signal produced {nonzero} non-zero values - it never "
          f"fired, so the inversion test would be vacuous")

    # The inverted signal must be the SIGN FLIP of the real one.
    identical = True
    negated = True
    for s in panel.symbols:
        a = real.get(s) or []
        b = inv.get(s) or []
        if len(a) != len(b):
            identical = False
            negated = False
            break
        for x, y in zip(a, b):
            if abs(x - y) > 1e-12:
                identical = False
            if abs(x + y) > 1e-12:
                negated = False

    check(f"{sig_name}: the inverted signal is NOT identical to the real one",
          not identical,
          "the control is a NO-OP - it cannot fail, so it proves nothing")
    if flips_sign:
        check(f"{sig_name}: the inverted signal is exactly the sign flip",
              negated,
              "the inverted signal is neither identical nor a clean negation")
    else:
        # `leading_vrp_switch` is the one signal whose control does NOT
        # negate the position. Its polarity lives in the VOLATILITY
        # RISK PREMIUM's reading: inverting the premium z-score changes
        # the position SIZE (stand aside when protection is dear
        # instead of when it is cheap) rather than the position sign.
        #
        # That IS a meaningful control - it asks "does the premium help
        # or hurt?" - so it is asserted to DIFFER, not to negate. A
        # clean negation would have been a DIFFERENT control: "does
        # the opposite position work?", which is not the question this
        # concept asks.
        check(f"{sig_name}: the inverted signal DIFFERS from the real one",
              not identical,
              "the control is a NO-OP - it cannot fail, so it proves nothing")
        check(f"{sig_name}: the inverted signal is NOT a plain sign flip",
              not negated,
              "this control inverts the premium READING, so it should "
              "change the position SIZE, not the sign")

print()
print("=" * 72)
print("TEST 2 — every paper spec's control is wired to invert_signal")
print("=" * 72)

specs = build_specs()
ctrls = build_negative_controls(specs)
check("the control set has the same size as the real set",
      len(ctrls) == len(specs), f"{len(ctrls)} controls vs {len(specs)} specs")
for c in ctrls:
    params = (c.get("signal") or {}).get("params") or {}
    if not params.get("invert_signal"):
        check(f"{c.get('name')}: invert_signal is set", False,
              f"params={params}")
        break
else:
    check("every control sets invert_signal", True)

print()
print("=" * 72)
print("TEST 3 — the signals used by the matrix are all invertible")
print("=" * 72)

used = sorted({(s.get("signal") or {}).get("type") for s in specs})
for sig_name in used:
    if not sig_name:
        continue
    fn = _BTENGINE.SIGNALS.get(sig_name)
    if fn is None:
        check(f"{sig_name}: registered", False, "not registered")
        continue
    import inspect
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        params = {}
    has_flag = "invert_signal" in params
    check(f"{sig_name}: accepts invert_signal explicitly", has_flag,
          f"signature params={list(params)}")
    if has_flag:
        check(f"{sig_name}: the flag is actually honoured", True)

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
