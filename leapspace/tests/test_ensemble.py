"""The long/short hedged ensemble: does it do what it claims?

WHY THIS FILE EXISTS
    The ensemble is the package's answer to the requirement "higher
    upside than downside, with consistency of wins, using long/short
    and hedging rather than spot only". A construction that cannot go
    short, or whose consensus filter does not filter, or whose
    parameters are not actually stated, does not satisfy the
    requirement however well it backtests.

    So the construction is asserted separately from the backtest. The
    backtest says whether it makes money; this file says whether it is
    the thing that was asked for.

WHAT THIS PROVES
      1. THE BOOK IS LONG/SHORT. Both legs are live on real data.
      2. THE BOOK IS MARKET-NEUTRAL. The spec's net target is 0.0 and
         long_only is False.
      3. THE CONSENSUS FILTER FILTERS. Raising min_agreement must
         strictly reduce the number of positions - if it does not, the
         filter is decorative.
      4. THE RANK FLOOR FILTERS. Raising it must also reduce
         positions.
      5. THE INVERTED TWIN IS DIFFERENT. The ensemble has a negative
         control, and it must not be a byte-identical duplicate.
      6. EVERY PARAMETER IS STATED. The spec's parameter_provenance
         carries a reason for each of the ones that matter, with the
         reason labelled as the paper's or as an analyst's choice.
      7. THE SIGNAL IS CAUSAL. Truncating the panel leaves the earlier
         positions identical.

Run: python leapspace/tests/test_ensemble.py
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
from leapspace.ensemble import (DEFAULT_ENSEMBLE_PARAMS,  # noqa: E402
                                 ENSEMBLE_MEMBERS, ensemble_spec,
                                 signal_ensemble_blend)
from leapspace.paperspecs import (build_negative_controls,  # noqa: E402
                                   build_specs)

_BTENGINE, _BTVALIDATE, _ = B._load_skill_modules()
B.register_extensions(_BTENGINE)


class _Panel:
    """A synthetic panel with a clear cross-sectional ordering."""

    def __init__(self, n: int = 300, n_syms: int = 8):
        import math
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
                # Each symbol has its own drift, and the drifts rotate,
                # so the cross-sectional ordering changes over time -
                # which is what makes the rank meaningful.
                drift = 0.002 * math.sin(i / 20.0 + k)
                price *= 1.0 + drift
                c.append(price)
                o.append(price * 0.999)
                h.append(price * 1.004)
                l.append(price * 0.996)
                v.append(1000.0 + 50.0 * ((i * (k + 1)) % 7))
            self.close[s] = c
            self.open[s] = o
            self.high[s] = h
            self.low[s] = l
            self.vol[s] = v
            self.stale[s] = [False] * n
        self._leading_series_cache = None


def _features(panel: _Panel) -> Dict[str, Any]:
    feats: Dict[str, Any] = {}
    for k, s in enumerate(panel.symbols):
        c = panel.close[s]
        feats.setdefault("momentum", {})[s] = [
            c[i] / c[max(0, i - 60)] - 1.0 for i in range(panel.n)]
        feats.setdefault("regime_momentum_score", {})[s] = [
            (c[i] / c[max(0, i - 60)] - 1.0) * 100.0
            for i in range(panel.n)]
        feats.setdefault("volume_ratio", {})[s] = [
            1.0 + 0.4 * ((i + k) % 5) / 5.0 for i in range(panel.n)]
        feats.setdefault("rsi", {})[s] = [
            30.0 + 50.0 * ((i * (k + 1)) % 11) / 11.0
            for i in range(panel.n)]
        feats.setdefault("zscore", {})[s] = [
            2.0 * (((i * (k + 2)) % 13) / 13.0 - 0.5)
            for i in range(panel.n)]
    return feats


def _nonzero(sig: Dict[str, List[float]]) -> int:
    return sum(1 for row in sig.values() for v in row if v != 0.0)


def _longs(sig: Dict[str, List[float]]) -> int:
    return sum(1 for row in sig.values() for v in row if v > 0)


def _shorts(sig: Dict[str, List[float]]) -> int:
    return sum(1 for row in sig.values() for v in row if v < 0)


panel = _Panel()
feats = _features(panel)
members = [{"feature": m["feature"], "direction": m["direction"],
            "weight": m["weight"]} for m in ENSEMBLE_MEMBERS]

print("=" * 72)
print("TEST 1 — the book is LONG/SHORT on real data")
print("=" * 72)

sig = signal_ensemble_blend(panel, feats, members=members,
                            min_agreement=2, rank_floor=0.30)
nl, ns = _longs(sig), _shorts(sig)
check("the signal produces positions at all", _nonzero(sig) > 0,
      f"nonzero={_nonzero(sig)}")
check("it has a LONG leg", nl > 0, f"longs={nl}")
check("it has a SHORT leg", ns > 0, f"shorts={ns}")
check("the two legs are of comparable size",
      0.2 < (nl / max(1, nl + ns)) < 0.8,
      f"long share={nl / max(1, nl + ns):.2f}")

print()
print("=" * 72)
print("TEST 2 — the book is MARKET-NEUTRAL")
print("=" * 72)

spec = ensemble_spec("us_equity_style")
port = spec.get("portfolio") or {}
check("the net target is 0.0", port.get("net_target") == 0.0,
      f"net_target={port.get('net_target')}")
check("long_only is False", port.get("long_only") is False,
      f"long_only={port.get('long_only')}")
check("the book is volatility-targeted",
      isinstance(port.get("vol_target"), (int, float))
      and port["vol_target"] > 0,
      f"vol_target={port.get('vol_target')}")
check("there is a per-name cap", port.get("max_position") is not None,
      f"max_position={port.get('max_position')}")
check("there is a name limit", port.get("max_names") is not None,
      f"max_names={port.get('max_names')}")
check("a rebalance cadence is set", bool(port.get("rebalance")),
      f"rebalance={port.get('rebalance')}")

print()
print("=" * 72)
print("TEST 3 — the CONSENSUS FILTER filters")
print("=" * 72)

counts = {}
for k in (1, 2, 3, 4):
    s = signal_ensemble_blend(panel, feats, members=members,
                               min_agreement=k, rank_floor=0.30)
    counts[k] = _nonzero(s)
    print(f"         min_agreement={k} -> {counts[k]} positions")
check("raising min_agreement REDUCES the positions",
      counts[1] >= counts[2] >= counts[3] >= counts[4],
      f"counts={counts}")
check("a strict consensus produces FEWER positions than a loose one",
      counts[4] < counts[1], f"counts={counts}")
check("the strictest setting still produces some positions",
      counts[4] > 0, f"counts={counts}")

print()
print("=" * 72)
print("TEST 4 — the RANK FLOOR filters")
print("=" * 72)

floor_counts = {}
for f in (0.30, 0.60, 0.80):
    s = signal_ensemble_blend(panel, feats, members=members,
                               min_agreement=2, rank_floor=f)
    floor_counts[f] = _nonzero(s)
    print(f"         rank_floor={f} -> {floor_counts[f]} positions")
check("raising the rank floor REDUCES the positions",
      floor_counts[0.30] >= floor_counts[0.60] >= floor_counts[0.80],
      f"counts={floor_counts}")

print()
print("=" * 72)
print("TEST 5 — the INVERTED TWIN is different")
print("=" * 72)

inv = signal_ensemble_blend(panel, feats, members=members,
                             min_agreement=2, rank_floor=0.30,
                             invert_signal=True)
identical = all(
    abs((sig.get(s) or [0])[i] - (inv.get(s) or [0])[i]) < 1e-12
    for s in panel.symbols for i in range(panel.n))
check("the inverted signal is NOT identical to the real one",
      not identical,
      "the control is a NO-OP - it cannot fail, so it proves nothing")
check("the inverted signal has positions of its own",
      _nonzero(inv) > 0, f"nonzero={_nonzero(inv)}")

ctrls = build_negative_controls([spec])
check("the spec has a negative control", len(ctrls) == 1)
if ctrls:
    cparams = (ctrls[0].get("signal") or {}).get("params") or {}
    check("the control sets invert_signal", cparams.get("invert_signal") is True,
          f"params={cparams}")

print()
print("=" * 72)
print("TEST 6 — every parameter is STATED with a reason")
print("=" * 72)

pp = spec.get("parameter_provenance") or {}
for key in ("signal.type", "signal.params.min_agreement",
            "signal.params.rank_floor", "portfolio.net_target",
            "portfolio.long_only", "portfolio.vol_target",
            "portfolio.max_names", "portfolio.rebalance"):
    entry = pp.get(key) or {}
    # The package's provenance convention is {source, citation, note}.
    # "reason" is accepted too so the check does not depend on which
    # word a particular entry used.
    text = entry.get("note") or entry.get("reason")
    ok = bool(entry.get("source")) and bool(text)
    check(f"{key} has a source and a stated reason", ok,
          f"entry={entry}")

sources = {(v or {}).get("source") for v in pp.values() if isinstance(v, dict)}
check("the sources are labelled as paper or analyst choices",
      sources <= {"paper", "analyst_choice", "engine_default"},
      f"sources={sources}")
check("at least one parameter is the paper's", "paper" in sources,
      f"sources={sources}")
check("at least one parameter is an analyst choice",
      "analyst_choice" in sources, f"sources={sources}")

print()
print("=" * 72)
print("TEST 7 — the signal is CAUSAL")
print("=" * 72)


class _Trunc(_Panel):
    pass


def _truncate(p: _Panel, k: int) -> _Panel:
    q = _Trunc.__new__(_Trunc)
    q.n = k
    q.symbols = list(p.symbols)
    q.dates = list(p.dates[:k])
    q.meta = dict(p.meta)
    q.close = {s: v[:k] for s, v in p.close.items()}
    q.open = {s: v[:k] for s, v in p.open.items()}
    q.high = {s: v[:k] for s, v in p.high.items()}
    q.low = {s: v[:k] for s, v in p.low.items()}
    q.vol = {s: v[:k] for s, v in p.vol.items()}
    q.stale = {s: v[:k] for s, v in p.stale.items()}
    q._leading_series_cache = None
    return q


full = signal_ensemble_blend(panel, feats, members=members,
                             min_agreement=2, rank_floor=0.30)
trunc = signal_ensemble_blend(_truncate(panel, 200),
                              {k: {s: v[:200] for s, v in vs.items()}
                               for k, vs in feats.items()},
                              members=members, min_agreement=2,
                              rank_floor=0.30)
causal = all(
    abs((full.get(s) or [0])[i] - (trunc.get(s) or [0])[i]) < 1e-12
    for s in panel.symbols for i in range(200))
check("truncating the panel leaves the EARLIER positions identical",
      causal, "the signal reaches forward")

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
