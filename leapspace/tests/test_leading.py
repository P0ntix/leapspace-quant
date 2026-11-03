"""Tests for the LEADING-indicator features.

THE GAP THIS FILE CLOSES
    `leapspace.regime` classifies the market from four LAGGING inputs
    (realised volatility, trend, drawdown, liquidity). The papers this
    package implements are explicit that forward-looking option and
    volatility-index signals detect stress transitions EARLIER, and
    that implied volatility "often ... outperforms historical volatility
    forecasts".

    This file proves the new leading features:
      1. compute what they claim to,
      2. do NOT look ahead, which is the property that makes them
         leading rather than fake,
      3. degrade honestly when the source is unavailable.

WHAT IS ASSERTED
    * The volatility risk premium is implied minus realised.
    * The alignment rule never lets a bar use a measurement published
      after it — checked with a series whose values are deliberately
      set so a look-ahead would be visible.
    * A missing leading series produces None everywhere, NOT zero.
    * The realised side is shifted one bar, so no bar uses its own
      close.
    * The z-score is centred and scaled.
    * The source resolution picks the matching market's leading
      indicator rather than the wrong one.

Run: python leapspace/tests/test_leading.py
"""

from __future__ import annotations

import os
import sys

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


from leapspace import leading as L  # noqa: E402
from leapspace import leadingcache as LC  # noqa: E402

print("=" * 72)
print("TEST 1 — the volatility risk premium is implied minus realised")
print("=" * 72)

check(
    "VRP(40, 25) == 15",
    abs(L.volatility_risk_premium(40.0, 25.0) - 15.0) < 1e-9,
    f"got {L.volatility_risk_premium(40.0, 25.0)}",
)
check(
    "VRP(20, 35) == -15 (negative when options are cheap)",
    abs(L.volatility_risk_premium(20.0, 35.0) + 15.0) < 1e-9,
    f"got {L.volatility_risk_premium(20.0, 35.0)}",
)
check(
    "VRP with a missing implied side is None, not 0",
    L.volatility_risk_premium(None, 25.0) is None,
    "a missing input produced a number",
)
check(
    "VRP with a missing realised side is None, not 0",
    L.volatility_risk_premium(40.0, None) is None,
    "a missing input produced a number",
)

print()
print("=" * 72)
print("TEST 2 — the alignment rule does NOT look ahead")
print("=" * 72)

# A series whose value at each timestamp is a DISTINCT number, so a
# look-ahead would be visible as the wrong value.
DAY = 86400
T0 = 1_700_000_000
series = [(T0 + i * DAY, 100.0 + i) for i in range(10)]
bars = [T0 + i * DAY for i in range(10)]

aligned = L.align_to_bars(series, bars, max_lag_bars=1)

# Bar 0 has NO prior measurement, so it is None. That is correct: a
# one-bar lag means bar 0 can only use a measurement published before
# the series starts.
check(
    "bar 0 is None (no prior measurement exists)",
    aligned[0] is None,
    f"aligned[0]={aligned[0]} — it should be None, not a future value",
)
check(
    "every bar from 1 onward has a value",
    all(v is not None for v in aligned[1:]),
    f"aligned={aligned}",
)
# The decisive check: with a one-bar lag, bar i may use a measurement
# timestamped at or before bar (i-1).
check(
    "bar i uses a measurement no later than bar i-1",
    all(aligned[i] <= 100.0 + (i - 1) for i in range(1, len(aligned))),
    f"aligned={aligned}",
)
check(
    "bar i never uses its OWN bar's measurement",
    all(aligned[i] != 100.0 + i for i in range(len(aligned))),
    f"aligned={aligned} — a bar used its own bar's value",
)

# With NO lag, the value carried to bar i is the one AT bar i.
aligned0 = L.align_to_bars(series, bars, max_lag_bars=0)
check(
    "with zero lag, bar i carries the measurement AT bar i",
    all(abs((aligned0[i] or 0) - (100.0 + i)) < 1e-9 for i in range(10)),
    f"aligned0={aligned0}",
)

print()
print("=" * 72)
print("TEST 3 — a missing leading series is None everywhere, NOT zero")
print("=" * 72)

empty = L.align_to_bars([], bars, max_lag_bars=1)
check(
    "an empty series aligns to all-None",
    all(v is None for v in empty),
    f"empty={empty}",
)
check(
    "an empty series does not align to zeros",
    not any(v == 0 for v in empty),
    "a missing measurement became a zero, which reads as 'no expected "
    "movement' rather than 'could not measure'",
)

print()
print("=" * 72)
print("TEST 4 — realised volatility is shifted so no bar uses its own close")
print("=" * 72)

closes = [100.0 + (i if i % 3 else -i) for i in range(40)]
feats = L.build_leading_features(
    [(T0 + i * DAY, 30.0) for i in range(40)],
    [T0 + i * DAY for i in range(40)],
    closes=closes, rv_window=5, label="synthetic")

check(
    "the feature block has the same length as the bar grid",
    len(feats["iv_level"]) == 40 and len(feats["vrp"]) == 40,
    f"len iv={len(feats['iv_level'])} vrp={len(feats['vrp'])}",
)
check(
    "the realised series starts with None (warm-up)",
    feats["rv_level"][0] is None,
    f"rv_level[0]={feats['rv_level'][0]}",
)
# The realised series at bar i must be the one computed from closes
# up to i-1, so the LAST bar's realised value must not use the last
# close.
rv_raw = L.realized_vol_series(closes, window=5)
check(
    "the aligned realised series equals the raw series shifted one bar",
    feats["rv_level"][1:-1] == rv_raw[0:-2],
    "the realised series was not shifted by one bar",
)
check(
    "the VRP is populated where both sides exist",
    any(v is not None for v in feats["vrp"]),
    "the risk premium was never computed",
)

print()
print("=" * 72)
print("TEST 5 — the z-score is centred and scaled")
print("=" * 72)

z = feats["vrp_zscore"]
vals = [v for v in z if v is not None]
check("the z-score has observations", len(vals) > 3, f"n={len(vals)}")
if len(vals) > 3:
    m = sum(vals) / len(vals)
    check("the z-score mean is ~0", abs(m) < 1e-6, f"mean={m}")
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    check("the z-score variance is ~1", abs(var - 1.0) < 1e-6, f"var={var}")

print()
print("=" * 72)
print("TEST 6 — the leading source matches the market")
print("=" * 72)

src, asset, why = LC.resolve_leading_source(["BTC-USD", "ETH-USD"])
check(
    "a crypto universe resolves to Deribit's DVOL for that asset",
    src == "deribit.dvol" and asset == "BTC",
    f"got {src}/{asset} — {why}",
)
src, asset, why = LC.resolve_leading_source(["QQQ"])
check(
    "a Nasdaq universe resolves to the Nasdaq volatility index",
    src == "yahoo.chart" and asset == "^VXN",
    f"got {src}/{asset} — {why}",
)
src, asset, why = LC.resolve_leading_source(["SPY"])
check(
    "an S&P universe resolves to VIX",
    src == "yahoo.chart" and asset == "^VIX",
    f"got {src}/{asset} — {why}",
)

print()
print("=" * 72)
print("TEST 7 — the panel date conversion is UTC midnight")
print("=" * 72)

ts = LC.panel_date_timestamps(["2024-01-02", "2024-01-03"])
check(
    "two consecutive dates are 86400 seconds apart",
    abs((ts[1] - ts[0]) - 86400) < 1,
    f"delta={ts[1] - ts[0]}",
)
check(
    "the date converts to a plausible unix timestamp",
    1_700_000_000 < ts[0] < 1_800_000_000,
    f"ts={ts[0]}",
)

print()
print("=" * 72)
print("TEST 8 — the cache round-trips and reports its age")
print("=" * 72)

import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    orig = LC.CACHE_DIR
    LC.CACHE_DIR = tmp
    try:
        ser = [(1000 + i, 10.0 + i) for i in range(5)]
        LC.store_leading_series("test.src", "TEST", ser, url="http://x",
                                note="unit test")
        got, prov = LC.load_leading_series("test.src", "TEST")
        check("the cached series round-trips", got == sorted(ser),
              f"got={got}")
        check("the provenance reports the cache, not live data",
              prov.kind == "cache" or "cache" in str(prov.source),
              f"prov={prov.source} kind={getattr(prov, 'kind', None)}")
        got2, prov2 = LC.load_leading_series("test.src", "MISSING")
        check("a missing cache returns an empty series, not an error",
              got2 == [], f"got={got2}")
    finally:
        LC.CACHE_DIR = orig

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
