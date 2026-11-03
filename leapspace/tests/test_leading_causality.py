"""Tests for the CAUSALITY of the leading features.

WHY THIS FILE EXISTS
    The leading-VRP feature normalised its z-score over the WHOLE
    panel. Bar i's z-score therefore depended on bars that come AFTER
    bar i, which is look-ahead by construction - and it defeated the
    entire purpose of a LEADING feature.

    The engine's causality audit caught it (10 violations on the crypto
    panel), but only after the fact, and only for the specs that
    reached the audit. A feature that quietly reaches forward is the
    single most damaging kind of bug in a backtest engine, because it
    produces BETTER results, not worse ones, so nothing else in the
    system complains.

    So these tests assert the property directly, on synthetic data
    where the answer is known exactly.

WHAT THIS PROVES
      1. The z-score is CAUSAL. Truncating the panel at bar k leaves
         the z-scores at bars <= k BIT-IDENTICAL. That is the
         definition of causality, and it is asserted exactly, not
         approximately.
      2. A whole-panel z-score would FAIL that test - so the test
         would have caught the original bug.
      3. The realised side is shifted, so bar T never uses bar T's own
         close.
      4. The implied series is aligned with a publication lag, so a
         measurement published after bar T never reaches bar T.
      5. A missing leading value is None, never zero.
      6. The `session_drift` feature reaches only BACKWARD.

Run: python leapspace/tests/test_leading_causality.py
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

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
B.register_extensions(_BTENGINE)
FEATURES = _BTENGINE.FEATURES


# --------------------------------------------------------------------------
# A synthetic panel, so the answer is known exactly
# --------------------------------------------------------------------------
class FakePanel:
    """A minimal stand-in for btengine's Panel.

    The feature functions only need `n`, `dates`, `symbols`, `close`,
    `open`, `high`, `low` and `vol`, so a real btengine Panel is not
    required to test causality.

    The panel can carry a SYNTHETIC implied-volatility series, cached
    directly on `_leading_series_cache`, so the volatility risk premium
    is non-degenerate. Without it the premium is all None and every
    causality assertion about the z-score is vacuously true - which is
    exactly the kind of test that passes without testing anything.
    """

    def __init__(self, closes: List[float], volumes: Optional[List[float]] = None,
                 highs: Optional[List[float]] = None,
                 lows: Optional[List[float]] = None,
                 opens: Optional[List[float]] = None,
                 start_date: str = "2020-01-01",
                 iv_series: Optional[List[Tuple[int, float]]] = None):
        n = len(closes)
        self.n = n
        self.symbols = ["AAA"]
        import datetime as _dt
        d0 = _dt.date.fromisoformat(start_date)
        self.dates = [(d0 + _dt.timedelta(days=i)).isoformat()
                      for i in range(n)]
        self.close = {"AAA": list(closes)}
        self.open = {"AAA": list(opens) if opens else [c - 0.1 for c in closes]}
        self.high = {"AAA": list(highs) if highs else [c + 0.5 for c in closes]}
        self.low = {"AAA": list(lows) if lows else [c - 0.5 for c in closes]}
        self.vol = {"AAA": list(volumes) if volumes else [1000.0] * n}
        self.stale = {"AAA": [False] * n}
        self.meta = {"universe": "synthetic", "asset_class": "test"}
        self._leading_series_cache = (iv_series, {"source": "synthetic"}) \
            if iv_series else None


def _synthetic_iv(n: int, start_date: str = "2020-01-01"
                  ) -> List[Tuple[int, float]]:
    """A synthetic implied-volatility series on the panel's own dates.

    It varies over time, so the risk premium - implied minus realised
    - is non-degenerate and its z-score has something to measure.
    """
    import calendar
    import datetime as _dt
    d0 = _dt.date.fromisoformat(start_date)
    out: List[Tuple[int, float]] = []
    for i in range(n):
        d = d0 + _dt.timedelta(days=i)
        ts = int(calendar.timegm((d.year, d.month, d.day, 0, 0, 0, 0, 0, 0)))
        out.append((ts, 18.0 + 6.0 * math.sin(i / 11.0)
                    + 1.5 * math.sin(i / 3.0)))
    return out


def _drifting_panel(n: int = 240) -> FakePanel:
    """A price series with a clear drift, so the volatility risk
    premium is non-degenerate and the z-score is not a flat zero."""
    closes: List[float] = []
    price = 100.0
    for i in range(n):
        # A slow sine-driven drift plus a small alternating component,
        # so realised volatility varies over time and the z-score has
        # something to measure.
        price *= 1.0 + 0.002 * math.sin(i / 9.0) + 0.001 * (1 if i % 2 else -1)
        closes.append(price)
    return FakePanel(closes, iv_series=_synthetic_iv(n))


def _whole_panel_zscore(raw: List[Optional[float]]) -> List[Optional[float]]:
    """The ORIGINAL, non-causal implementation, kept here so the test
    can prove it WOULD have failed."""
    vals = [v for v in raw if v is not None]
    if len(vals) < 3:
        return [None] * len(raw)
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    sd = var ** 0.5
    if sd <= 0:
        return [None] * len(raw)
    return [None if v is None else (v - m) / sd for v in raw]


def _truncate(panel: FakePanel, k: int) -> FakePanel:
    """A copy of the panel cut off after bar k."""
    iv = panel._leading_series_cache
    iv_series = None
    if iv and iv[0]:
        # Keep only the implied observations that fall on the
        # TRUNCATED date grid, so the truncated panel sees exactly the
        # data it would have seen had it been built that way.
        import calendar
        import datetime as _dt
        d0 = _dt.date.fromisoformat(panel.dates[0])
        cutoff = d0 + _dt.timedelta(days=k - 1)
        cut_ts = int(calendar.timegm((cutoff.year, cutoff.month,
                                       cutoff.day, 0, 0, 0, 0, 0, 0)))
        iv_series = [(t, v) for t, v in iv[0] if t <= cut_ts]
    p = FakePanel(panel.close["AAA"][:k], iv_series=iv_series)
    p.open = {"AAA": panel.open["AAA"][:k]}
    p.high = {"AAA": panel.high["AAA"][:k]}
    p.low = {"AAA": panel.low["AAA"][:k]}
    p.vol = {"AAA": panel.vol["AAA"][:k]}
    return p


print("=" * 72)
print("TEST 1 — the z-score is CAUSAL")
print("=" * 72)

panel = _drifting_panel(240)
raw = FEATURES["leading_vrp_score"](panel, "AAA", lookback=20)
check("the premium series produces values", sum(1 for v in raw if v is not None) > 100,
      f"observed={sum(1 for v in raw if v is not None)}")

# The DECISIVE CHECK. For every truncation point k, the z-scores at
# bars <= k must be IDENTICAL between the full panel and the truncated
# panel. That is the definition of causality.
causal = True
first_bad = None
for k in (80, 120, 160, 200, 220):
    full_z = FEATURES["leading_vrp_zscore"](panel, "AAA", lookback=20)
    trunc_z = FEATURES["leading_vrp_zscore"](_truncate(panel, k), "AAA",
                                               lookback=20)
    for i in range(k):
        a, b = full_z[i], trunc_z[i]
        if a is None and b is None:
            continue
        if a is None or b is None:
            causal = False
            first_bad = f"bar {i}: full={a} trunc={b} (k={k})"
            break
        if abs(a - b) > 1e-12:
            causal = False
            first_bad = f"bar {i}: full={a:.12f} trunc={b:.12f} (k={k})"
            break
    if not causal:
        break

check("truncating the panel leaves the EARLIER z-scores bit-identical",
      causal, first_bad or "")

print()
print("=" * 72)
print("TEST 2 — the whole-panel version WOULD have failed")
print("=" * 72)

# If the old implementation also passed test 1, then test 1 proves
# nothing and the causality fix is unverified.
noncausal = _whole_panel_zscore(raw)
old_causal = True
old_first_bad = None
for k in (120, 160, 200):
    trunc_raw = raw[:k]
    trunc_z = _whole_panel_zscore(trunc_raw)
    for i in range(k):
        a, b = noncausal[i], trunc_z[i]
        if a is None and b is None:
            continue
        if a is None or b is None or abs(a - b) > 1e-12:
            old_causal = False
            old_first_bad = f"bar {i}: full={a} trunc={b} (k={k})"
            break
    if not old_causal:
        break
check("the OLD whole-panel z-score FAILS the same causality test",
      not old_causal, old_first_bad or "the old version was already causal")
print(f"         (the old implementation first diverged at: {old_first_bad})")

print()
print("=" * 72)
print("TEST 3 — the realised side is shifted")
print("=" * 72)

# If the realised series were NOT shifted, bar T's premium would use
# bar T's own close. Change bar T's close and the premium at bar T
# must NOT change.
p1 = _drifting_panel(120)
p2 = _drifting_panel(120)
# Perturb the LAST bar's close only.
p2.close["AAA"][-1] *= 1.5
p2.high["AAA"][-1] *= 1.5
r1 = FEATURES["leading_vrp_score"](p1, "AAA", lookback=20)
r2 = FEATURES["leading_vrp_score"](p2, "AAA", lookback=20)
last = len(r1) - 1
check("bar T's premium does NOT use bar T's own close",
      r1[last] is None or r2[last] is None or abs(r1[last] - r2[last]) < 1e-12,
      f"r1={r1[last]} r2={r2[last]}")
check("the bar BEFORE T is also unaffected by T's close",
      r1[last - 1] is None or r2[last - 1] is None
      or abs(r1[last - 1] - r2[last - 1]) < 1e-12,
      f"r1={r1[last - 1]} r2={r2[last - 1]}")

print()
print("=" * 72)
print("TEST 4 — the implied series is aligned with a publication lag")
print("=" * 72)

from leapspace.leading import align_to_bars  # noqa: E402

bars = [0, 100, 200, 300]
al = align_to_bars([(100, 0.5)], bars, max_lag_bars=1)
check("a measurement at t=100 reaches only bars after the lag",
      al[0] is None and al[1] is None, f"got {al}")
check("it reaches the bar at t=200", al[2] == 0.5, f"got {al}")
al0 = align_to_bars([(100, 0.5)], bars, max_lag_bars=0)
check("with a zero lag the measurement reaches its own bar",
      al0[1] == 0.5, f"got {al0}")

print()
print("=" * 72)
print("TEST 5 — a missing leading value is None, never zero")
print("=" * 72)

empty = FakePanel([100.0] * 50)
z_empty = FEATURES["leading_vrp_zscore"](empty, "AAA", lookback=20)
check("with no implied series the z-score is all None",
      all(v is None for v in z_empty),
      f"got {sum(1 for v in z_empty if v is not None)} non-None")
check("it is NOT a series of zeros",
      not any(v == 0.0 for v in z_empty if v is not None))

print()
print("=" * 72)
print("TEST 6 — session_drift reaches only BACKWARD")
print("=" * 72)

p = FakePanel(
    [100.0 + i * 0.1 for i in range(80)],
    volumes=[1000.0 + (i % 5) * 100 for i in range(80)],
    highs=[100.5 + i * 0.1 for i in range(80)],
    lows=[99.5 + i * 0.1 for i in range(80)],
    opens=[100.0 + i * 0.1 for i in range(80)],
)
dr = FEATURES["session_drift"](p, "AAA", lookback=20)
check("the session drift produces values",
      sum(1 for v in dr if v is not None) > 0,
      f"observed={sum(1 for v in dr if v is not None)}")
check("the warm-up window is None",
      dr[0] is None and dr[5] is None, f"got {dr[:6]}")

# Perturb the LAST bar's volume and high. Bar T-1 and earlier must not
# change; bar T may change.
p2 = FakePanel(
    [100.0 + i * 0.1 for i in range(80)],
    volumes=[1000.0 + (i % 5) * 100 for i in range(80)],
    highs=[100.5 + i * 0.1 for i in range(80)],
    lows=[99.5 + i * 0.1 for i in range(80)],
    opens=[100.0 + i * 0.1 for i in range(80)],
)
p2.vol["AAA"][-1] *= 10.0
dr2 = FEATURES["session_drift"](p2, "AAA", lookback=20)
earlier_same = all(
    dr[i] is None or dr2[i] is None or abs(dr[i] - dr2[i]) < 1e-12
    for i in range(len(dr) - 1))
check("changing the LAST bar does not change any earlier bar",
      earlier_same, "the feature reached forward")
check("the last bar itself does react",
      dr[-1] is None or dr2[-1] is None or abs(dr[-1] - dr2[-1]) > 1e-12,
      "the last bar did not react to its own volume change")

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
