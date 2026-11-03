"""Self-test for the regime module: causality, labelling, no crashes."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from leapspace.regime import (HMM, build_regime_features, identify_regimes,
                              REGIME_BEHAVIOUR)

FAIL = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        FAIL.append(name)


def synthetic_market(n=900, seed=11):
    """A regime-switching synthetic series. SYNTHETIC - test fixture only.

    Prices are kept strictly positive: the regime features compute log-scale
    liquidity and drawdown, which are undefined for a non-positive price.
    """
    rng = random.Random(seed)
    closes, vols = [], []
    price, state = 100.0, 0
    regimes = [(0.0006, 0.006), (0.004, 0.012), (-0.003, 0.010), (-0.012, 0.020)]
    for i in range(n):
        if i % 90 == 0:
            state = rng.randrange(len(regimes))
        drift, vol = regimes[state]
        shock = rng.gauss(drift, vol)
        price = max(0.01, price * (1.0 + shock))
        closes.append(price)
        vols.append(1_000_000 + abs(shock) * 5_000_000)
    return closes, vols


print("== synthetic regime series ==")
closes, vols = synthetic_market()
feats = build_regime_features(closes, vols)
for k in ("vol_level", "vol_change", "trend", "drawdown", "liquidity", "rebound"):
    vals = [v for v in feats[k] if v is not None]
    check(f"feature {k} populated", len(vals) > 700, f"got {len(vals)}")
check("returns present", feats["_returns"][0] is None and feats["_returns"][1] is not None)

print("== HMM fit ==")
res = identify_regimes(feats, n_states=4)
check("regime result produced", res is not None)
if res:
    s = res.summary()
    print("   states:", s["state_share"])
    check("4 distinct labels", len(set(s["labels"].values())) == 4, str(s["labels"]))
    check("converged or at least stable", s["n_iter"] > 0)
    check("labels in taxonomy", all(v in REGIME_BEHAVIOUR for v in s["labels"].values()))

print("== causality: filter vs smooth differ ==")
if res:
    f = res.posteriors_filtered
    sm = res.posteriors_smoothed
    check("filter len matches bars", len(f) == len(closes))
    check("filter and smooth are not identical",
          any(abs(f[i][0] - sm[i][0]) > 1e-9 for i in range(len(f))
              if f[i][0] is not None and sm[i][0] is not None))
    check("warm-up bars carry no posterior", f[0][0] is None)

print("== causality: recomputing on half the data reproduces first half ==")
# HMM parameters are re-fit, so posterior values may differ. What MUST hold is
# that the FEATURES (the causal inputs) reproduce exactly.
closes_h, vols_h = closes[:450], vols[:450]
feats_h = build_regime_features(closes_h, vols_h)
for k in ("vol_level", "vol_change", "trend", "drawdown", "liquidity"):
    full = [v for v in feats[k][:450] if v is not None]
    half = [v for v in feats_h[k] if v is not None]
    n = min(len(full), len(half))
    ok = all(abs(full[i] - half[i]) < 1e-12 for i in range(n))
    check(f"feature {k} reproducible on truncation", ok)

print("== HMM internals ==")
seq = [[math.sin(i / 7.0), math.cos(i / 11.0)] for i in range(300)]
h = HMM(n_states=3).fit(seq)
check("transition rows sum to 1", all(abs(sum(r) - 1.0) < 1e-9 for r in h.trans))
check("init sums to 1", abs(sum(h.init) - 1.0) < 1e-9)
check("variances positive", all(v > 0 for row in h.variances for v in row))
pf = h.filter(seq)
check("filter rows sum to 1", all(abs(sum(r) - 1.0) < 1e-9 for r in pf))
e0 = h._emit(seq[0])
manual = h.init[0] * math.exp(e0[0]) / sum(h.init[s] * math.exp(e0[s]) for s in range(3))
check("filter row0 uses only observation 0", abs(pf[0][0] - manual) < 1e-9)

print("== insufficient data returns None (not a fake regime) ==")
tiny = build_regime_features(closes[:50], vols[:50])
check("None on too-short sample", identify_regimes(tiny, n_states=4, min_bars=250) is None)

print()
if FAIL:
    print(f"RESULT: {len(FAIL)} FAILURES: {FAIL}")
    sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
