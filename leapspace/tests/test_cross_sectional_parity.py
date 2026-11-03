"""The repo's cross-sectional wrapper must keep the engine's book.

WHY THIS FILE EXISTS
    The repo wraps the engine's `cross_sectional` signal as
    `paper_cross_sectional` so the NEGATIVE CONTROL can negate the
    positions - the engine's own signal swallows `invert_signal` in
    `**kw`, so the control was a byte-identical duplicate of its
    twin and could not fail.

    The wrapper changed the signal's TYPE STRING. And the engine picks
    the conviction-ranking strength series with an EXACT string test:

        if sig_spec["type"] == "cross_sectional":
            _strength = _cross_sectional_strength(panel, features[_fname])

    So the renamed signal silently stopped receiving the
    cross-sectional RANK as its strength series. Without it, `max_names`
    keeps the ALPHABETICALLY FIRST names rather than the most extreme
    ones, and the selected book differed from the engine's own
    `cross_sectional` on 234/262 rebalance bars.

    The bug was silent in the worst way: it did not crash, it did not
    produce an error, and the spec and its control were affected
    EQUALLY, so the control comparison looked perfectly healthy while
    the book being traded was not the book the concept describes.

WHAT THIS PROVES
    1. The engine's conviction-ranking branch recognises the repo's
       wrapper type.
    2. The engine's source does not use a bare exact-string test that
       the wrapper would miss.

Run: python leapspace/tests/test_cross_sectional_parity.py
"""

from __future__ import annotations

import inspect
import os
import re
import sys
from typing import Any, Dict, List

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


print("=" * 72)
print("TEST 1 — the engine's conviction ranking covers the wrapper type")
print("=" * 72)

src = inspect.getsource(_BTENGINE)
# The engine reads the signal spec and branches on its type to decide
# whether to pass the cross-sectional rank as the strength series.
branches = re.findall(
    r'sig_spec\["type"\]\s*(==|!=|\bin\b)\s*'
    r'(?:["\'](\w+)["\']|\(([^)]*)\))',
    src)

wrapper_mentioned = False
for op, literal, tuple_body in branches:
    if literal == "cross_sectional":
        # A bare equality test would miss the wrapper.
        check("the engine does not use a bare exact-string test for "
              "'cross_sectional'",
              False,
              "the engine tests `sig_spec[\"type\"] == \"cross_sectional\"` "
              "exactly, so the repo's wrapper would silently lose the "
              "conviction ranking")
    if tuple_body and "cross_sectional" in tuple_body:
        wrapper_mentioned = wrapper_mentioned or ("paper_cross_sectional"
                                                  in tuple_body)
    if literal == "cross_sectional" and op == "==":
        wrapper_mentioned = wrapper_mentioned or False

check("the engine's branch mentions the repo's wrapper type",
      wrapper_mentioned,
      "no branch in the engine mentions 'paper_cross_sectional', so the "
      "wrapper gets no conviction ranking and the selected book "
      "differs from the engine's own cross_sectional")

print()
print("=" * 72)
print("TEST 2 — both signal types exist and the wrapper inverts")
print("=" * 72)

check("the engine's cross_sectional is registered",
      "cross_sectional" in _BTENGINE.SIGNALS)
check("the repo's wrapper is registered",
      "paper_cross_sectional" in _BTENGINE.SIGNALS)

wrapper = _BTENGINE.SIGNALS.get("paper_cross_sectional")
engine = _BTENGINE.SIGNALS.get("cross_sectional")
check("both signal callables are available", wrapper and engine)

if wrapper and engine:
    import inspect as _i
    wparams = _i.signature(wrapper).parameters
    check("the wrapper accepts invert_signal explicitly",
          "invert_signal" in wparams, f"params={list(wparams)}")
    check("the engine's own signal does NOT accept invert_signal "
          "(which is why the wrapper exists)",
          "invert_signal" not in _i.signature(engine).parameters,
          "the engine's signal now accepts invert_signal - the wrapper "
          "may no longer be needed, and should be re-checked")

print()
print("=" * 72)
print("TEST 3 — the wrapper produces the engine's book, inverted")
print("=" * 72)


class _Panel:
    def __init__(self, n: int = 200, n_syms: int = 8):
        self.n = n
        self.symbols = [f"S{i}" for i in range(n_syms)]
        self.dates = [f"2020-{1 + (i // 28):02d}-{(i % 28) + 1:02d}"
                      for i in range(n)]
        self.meta = {"universe": "synthetic"}
        self.close, self.open, self.high, self.low, self.vol = {}, {}, {}, {}, {}
        self.stale = {}
        for k, s in enumerate(self.symbols):
            c, o, h, l, v = [], [], [], [], []
            price = 100.0 + k
            for i in range(n):
                price *= 1.0 + 0.003 * ((-1) ** i) * (1 + k * 0.1)
                c.append(price)
                o.append(price * 0.999)
                h.append(price * 1.005)
                l.append(price * 0.995)
                v.append(1000.0 + 37.0 * ((i * (k + 1)) % 13))
            self.close[s] = c
            self.open[s] = o
            self.high[s] = h
            self.low[s] = l
            self.vol[s] = v
            self.stale[s] = [False] * n
        self._leading_series_cache = None


panel = _Panel()
feats: Dict[str, Any] = {"session_drift": {}}
for k, s in enumerate(panel.symbols):
    feats["session_drift"][s] = [
        ((i % 11) / 11.0) * (1.0 + 0.05 * k) for i in range(panel.n)]

kwargs = {"feature": "session_drift", "long_rank": 0.75, "short_rank": 0.25}
try:
    real = wrapper(panel, feats, invert_signal=False, **kwargs)
    inv = wrapper(panel, feats, invert_signal=True, **kwargs)
    engine_sig = engine(panel, feats, **kwargs)

    same = all(
        abs((real.get(s) or [0])[i] - (engine_sig.get(s) or [0])[i]) < 1e-12
        for s in panel.symbols for i in range(panel.n))
    check("the wrapper's REAL book is identical to the engine's",
          same,
          "the wrapper changed the book - the engine's branch must be "
          "reading the wrapper's type")

    negated = all(
        abs((real.get(s) or [0])[i] + (inv.get(s) or [0])[i]) < 1e-12
        for s in panel.symbols for i in range(panel.n))
    check("the wrapper's inverted book is the exact negation",
          negated,
          "the inverted book is not the negation of the real one")

    nonzero = sum(1 for row in real.values() for v in row if v != 0.0)
    check("the signal actually fires (so the comparison is not vacuous)",
          nonzero > 0, f"the signal produced {nonzero} non-zero values")
except Exception as exc:  # noqa: BLE001
    check("both signal types run", False, f"{type(exc).__name__}: {exc}")

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
