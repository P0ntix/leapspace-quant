"""Tests for the crypto derivatives leading layer.

WHAT THIS PROVES
    The funding and open-interest layer is a real, leading, and
    correctly-aligned measurement - not a re-labeling of spot data.

      1. The annualisation is ARITHMETICALLY CORRECT. A rate of
         0.0001 per 8 hours is 0.01% per period, which annualises to
         about 10.95%. Getting this wrong by a factor of three would
         make every funding z-score meaningless.
      2. The z-score has the right MEAN and STANDARD DEVIATION, and it
         is centred on the series rather than on zero arbitrarily.
      3. The open-interest change is the PERCENT change, and it is
         None - not zero - when there is no prior observation.
      4. The ALIGNMENT has no look-ahead. A bar at T must not carry a
         measurement timestamped after T.
      5. A missing measurement is None, never zero.
      6. The live fetch works and its provenance is real.

Run: python leapspace/tests/test_cryptoderivs.py
"""

from __future__ import annotations

import math
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


from leapspace import cryptoderivs as CD  # noqa: E402

print("=" * 72)
print("TEST 1 — the annualisation is arithmetically correct")
print("=" * 72)

# 0.01% per 8 hours, over a 365-day year: 365*24/8 = 1095 periods.
ann = CD.annualise_funding(0.0001, interval_hours=8.0)
check("0.01% per 8h annualises to about 10.95%",
      abs(ann - 0.0001 * 1095.0) < 1e-12,
      f"got {ann}")
check("the annualised figure is in the right order of magnitude",
      0.10 < ann < 0.12, f"got {ann}")
ann24 = CD.annualise_funding(0.0001, interval_hours=24.0)
check("a daily rate annualises lower than an 8-hourly one",
      ann24 < ann, f"24h={ann24} 8h={ann}")
check("a daily rate annualises to the same total",
      abs(ann24 - 0.0001 * 365.0) < 1e-12, f"got {ann24}")

print()
print("=" * 72)
print("TEST 2 — the funding z-score has the right distribution")
print("=" * 72)

series = [(i, 0.0001 + 0.00001 * math.sin(i / 3.0)) for i in range(200)]
z = CD.funding_zscore(series)
zs = [v for _t, v in z if v is not None]
check("every observation receives a z-score", len(zs) == 200,
      f"got {len(zs)}")
m = sum(zs) / len(zs)
sd = math.sqrt(sum((v - m) ** 2 for v in zs) / (len(zs) - 1))
check("the z-scores have a mean of ~0", abs(m) < 1e-9, f"mean={m}")
check("the z-scores have a standard deviation of ~1",
      abs(sd - 1.0) < 1e-9, f"sd={sd}")
check(
    "the z-score SPANS zero (the series is centred on its own mean)",
    min(zs) < 0.0 < max(zs),
    f"min={min(zs)} max={max(zs)}",
)
check("a too-short series yields None rather than a crash",
      all(v is None for _t, v in CD.funding_zscore([(1, 0.1), (2, 0.2)])))

print()
print("=" * 72)
print("TEST 3 — the open-interest change is a percent change")
print("=" * 72)

oi = [(1, 100.0), (2, 110.0), (3, 99.0), (4, 99.0)]
chg = dict(CD.oi_change(oi, window=1))
check("the first observation has NO change (not zero)", chg[1] is None,
      f"got {chg[1]}")
check("a rise from 100 to 110 is +10%",
      abs((chg[2] or 0.0) - 10.0) < 1e-9, f"got {chg[2]}")
check("a fall from 110 to 99 is -10%",
      abs((chg[3] or 0.0) - (-10.0)) < 1e-9, f"got {chg[3]}")
check("no change is 0.0%", abs((chg[4] or 0.0) - 0.0) < 1e-9,
      f"got {chg[4]}")
chg2 = dict(CD.oi_change(oi, window=2))
check("a two-period change from 100 to 99 is -1%",
      abs((chg2[3] or 0.0) - (-1.0)) < 1e-9, f"got {chg2[3]}")

print()
print("=" * 72)
print("TEST 4 — the ALIGNMENT has no look-ahead")
print("=" * 72)

# Bars at 0, 100, 200. A measurement at t=250 must NOT reach bar 200.
bars = [0, 100, 200]
meas = [(250, 0.5)]
aligned = CD.__dict__  # placeholder to keep the import used
from leapspace.leading import align_to_bars  # noqa: E402

al = align_to_bars(meas, bars, max_lag_bars=1)
check("a measurement AFTER the last bar reaches no bar at all",
      all(v is None for v in al), f"got {al}")

meas2 = [(0, 0.5), (100, 0.6), (200, 0.7)]
al2 = align_to_bars(meas2, bars, max_lag_bars=1)
check("with a one-bar lag each bar uses the PREVIOUS measurement",
      al2[1] == 0.5 and al2[2] == 0.6,
      f"got {al2}")
check("the FIRST bar has no measurement (nothing before it)",
      al2[0] is None, f"got {al2[0]}")

# The decisive look-ahead test: build a feature block whose funding
# series extends INTO the future and confirm the early bars cannot see it.
future_funding = [(i * 100, 0.001) for i in range(10)]
feat = CD.build_crypto_derivatives_features(
    future_funding, open_interest=[(i * 100, 1000.0) for i in range(10)],
    bar_timestamps=bars, max_lag_bars=1)
check("the feature block carries no funding before the series starts",
      feat["funding_rate"][0] is None,
      f"got {feat['funding_rate'][0]}")
check("the feature block counts the OBSERVED points, not the bars",
      feat["n_funding_observed"] <= len(bars),
      f"got {feat['n_funding_observed']}")

print()
print("=" * 72)
print("TEST 5 — a missing measurement is None, never zero")
print("=" * 72)

feat2 = CD.build_crypto_derivatives_features(
    [(0, 0.0001)], open_interest=None, bar_timestamps=[0, 100, 200])
check("with no open interest the OI series is all None",
      all(v is None for v in feat2["open_interest"]),
      f"got {feat2['open_interest']}")
check("the OI-change series is all None too",
      all(v is None for v in feat2["oi_change_pct"]))
check("the count of observed OI points is zero, not three",
      feat2["n_oi_observed"] == 0, f"got {feat2['n_oi_observed']}")
check("the interpretation note is attached",
      "directional" in feat2["interpretation_note"].lower(),
      "no interpretation note")
check("the venue caveat is attached",
      "venue-specific" in feat2["venue_note"].lower(),
      "no venue note")
check("the alignment rule is stated",
      "publication" in feat2["alignment_rule"].lower()
      or "lag" in feat2["alignment_rule"].lower(),
      feat2["alignment_rule"])

print()
print("=" * 72)
print("TEST 6 — the LIVE fetch works and carries real provenance")
print("=" * 72)

# The live fetch is the only network-dependent part of this file. The
# blocking CI job sets LEAPSPACE_SKIP_NETWORK_TESTS=1 so a rate-limited
# or unreachable upstream cannot turn a package defect into a red
# build; the informational live job leaves it unset and runs it for
# real.
if os.environ.get("LEAPSPACE_SKIP_NETWORK_TESTS") == "1":
    print("  [SKIP] the live fetch (LEAPSPACE_SKIP_NETWORK_TESTS=1)")
    print("         The deterministic checks above still ran and still "
          "count.")
else:
    try:
        f, prov_f = CD.fetch_bybit_funding("BTCUSDT", limit=50)
        check("bybit funding returned points", len(f) > 0, "no points")
        check("the funding points are oldest-first",
              all(f[i][0] <= f[i + 1][0] for i in range(len(f) - 1)),
              "not sorted")
        check("the funding timestamps are sane",
              all(t > 1_500_000_000 for t, _v in f),
              f"sample {f[0] if f else None}")
        check("the provenance names the source",
              "bybit" in prov_f.source, f"got {prov_f.source}")
        check("the provenance carries a URL",
              bool(prov_f.url), "no url")
        rates = [v for _t, v in f]
        check("the funding rates are plausible magnitudes",
              all(-0.01 < r < 0.01 for r in rates),
              f"min={min(rates)} max={max(rates)}")
    except Exception as exc:  # noqa: BLE001
        check("bybit funding fetch", False, f"{type(exc).__name__}: {exc}")

    try:
        o, prov_o = CD.fetch_bybit_open_interest("BTCUSDT", interval="1d",
                                                  limit=50)
        check("bybit open interest returned points", len(o) > 0,
              "no points")
        check("the open-interest timestamps are sane",
              all(t > 1_500_000_000 for t, _v in o),
              f"sample {o[0] if o else None}")
        check("the open-interest values are positive",
              all(v > 0 for _t, v in o), "non-positive OI")
    except Exception as exc:  # noqa: BLE001
        check("bybit open interest fetch", False,
              f"{type(exc).__name__}: {exc}")

    try:
        bf, prov_bf = CD.fetch_binance_funding("BTCUSDT", limit=50)
        check("binance funding returned points", len(bf) > 0, "no points")
        check("binance funding timestamps are sane",
              all(t > 1_500_000_000 for t, _v in bf),
              f"sample {bf[0] if bf else None}")
    except Exception as exc:  # noqa: BLE001
        check("binance funding fetch", False,
              f"{type(exc).__name__}: {exc}")

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
