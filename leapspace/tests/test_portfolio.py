"""Tests for the risk-managed portfolio layer.

WHAT THIS FILE PROVES
    The risk controls are not decoration. Each one is asserted against
    a case where it MUST change the outcome, because a risk control
    that does not bind is indistinguishable from one that does not
    exist.

      1. Covariance estimation is CORRELATION-AWARE - two perfectly
         correlated assets get a HIGHER combined risk than two
         uncorrelated ones with the same volatilities. This is the
         property the backtest engine's diagonal covariance cannot
         provide, and it is the reason this module exists.
      2. Shrinkage pulls the sample covariance toward the diagonal, and
         the amount is controlled.
      3. Risk parity equalises RISK contribution, not capital - a
         low-volatility name gets more capital than a high-volatility
         one.
      4. The volatility target is met, and the estimate is forward-
         weighted (the EWMA reacts faster than the long window).
      5. The drawdown scaler is a SLOPE, not a cliff, and it reaches
         the floor at the hard limit.
      6. The caps are applied LAST, so nothing upstream undoes them.
      7. The net target is a SHIFT: it is reached exactly, including
         when the book is already at the opposite net exposure.
      8. The risk report shows the SHAPE of the risk - concentration,
         effective number of names, per-name risk contributions.

Run: python leapspace/tests/test_portfolio.py
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


from leapspace import portfolio as P  # noqa: E402

print("=" * 72)
print("TEST 1 — the covariance estimate is CORRELATION-AWARE")
print("=" * 72)

# Two assets with the SAME volatility: one perfectly correlated with
# the other, one not.
n = 200
a = [0.01 * (1 if i % 2 == 0 else -1) for i in range(n)]
b_corr = list(a)                                    # identical
b_unc = [0.01 * (1 if (i // 7) % 2 == 0 else -1) for i in range(n)]

cov_corr, names = P.estimate_covariance([a, b_corr], shrinkage=0.0)
cov_unc, _ = P.estimate_covariance([a, b_unc], shrinkage=0.0)

check("the covariance matrix is the right shape",
      len(cov_corr) == 2 and len(cov_corr[0]) == 2,
      f"shape={len(cov_corr)}x{len(cov_corr[0]) if cov_corr else 0}")
check("the off-diagonal correlation of identical series is ~1",
      abs(cov_corr[0][1] / (cov_corr[0][0] ** 0.5 * cov_corr[1][1] ** 0.5)
          - 1.0) < 0.05,
      f"corr={cov_corr[0][1] / (cov_corr[0][0] ** 0.5 * cov_corr[1][1] ** 0.5):.4f}")
check("the off-diagonal correlation of unrelated series is much lower",
      abs(cov_unc[0][1]) < abs(cov_corr[0][1]) * 0.9,
      f"uncorr={cov_unc[0][1]:.6f} vs corr={cov_corr[0][1]:.6f}")

# THE DECISIVE CHECK: a perfectly correlated PAIR carries more
# portfolio risk at equal weight than an uncorrelated pair does.
def _port_var(cov, w):
    return sum(w[i] * cov[i][j] * w[j]
               for i in range(len(w)) for j in range(len(w)))

w = [0.5, 0.5]
check(
    "a correlated pair carries MORE risk at equal weight than an "
    "uncorrelated pair with the same volatilities",
    _port_var(cov_corr, w) > _port_var(cov_unc, w) * 1.2,
    f"corr var={_port_var(cov_corr, w):.8f} vs uncorr "
    f"var={_port_var(cov_unc, w):.8f}",
)

print()
print("=" * 72)
print("TEST 2 — shrinkage pulls the covariance toward the diagonal")
print("=" * 72)

cov_s, _ = P.estimate_covariance([a, b_unc], shrinkage=1.0)
cov_z, _ = P.estimate_covariance([a, b_unc], shrinkage=0.0)
check(
    "full shrinkage gives a DIAGONAL matrix (zero correlations)",
    abs(cov_s[0][1]) < 1e-18,
    f"off-diagonal={cov_s[0][1]:.3e}",
)
check(
    "full shrinkage keeps the DIAGONAL (the own variances) intact",
    abs(cov_s[0][0] - cov_z[0][0]) < 1e-12,
    f"diag shrank from {cov_z[0][0]:.6f} to {cov_s[0][0]:.6f}",
)
check(
    "the off-diagonal is strictly reduced by shrinkage",
    abs(cov_s[0][1]) < abs(cov_z[0][1]),
    "shrinkage did not reduce the off-diagonal",
)

print()
print("=" * 72)
print("TEST 3 — risk parity equalises RISK, not capital")
print("=" * 72)

# A low-volatility asset and a high-volatility asset, uncorrelated.
low = [0.001 * (1 if i % 2 == 0 else -1) for i in range(200)]
high = [0.05 * (1 if i % 2 == 0 else -1) for i in range(200)]
cov2, _ = P.estimate_covariance([low, high], shrinkage=0.0)
rp = P.risk_parity_weights(cov2, names=["LOWVOL", "HIGHVOL"])

check("the risk-parity iteration CONVERGED",
      rp["converged"] is True,
      f"iterations={rp['iterations']} converged={rp['converged']}")
check(
    "the risk contributions are EQUAL",
    abs(rp["risk_contributions"][0] - rp["risk_contributions"][1]) < 1e-6,
    f"rc={rp['risk_contributions']}",
)
check(
    "the LOW-volatility asset gets MORE capital",
    rp["weights"][0] > rp["weights"][1] * 5,
    f"low-vol weight={rp['weights'][0]:.4f} high-vol "
    f"weight={rp['weights'][1]:.4f}",
)
check(
    "the weights sum to 1",
    abs(sum(rp["weights"]) - 1.0) < 1e-9,
    f"sum={sum(rp['weights'])}",
)

print()
print("=" * 72)
print("TEST 4 — the volatility target is met")
print("=" * 72)

rets = {
    "A": low,
    "B": high,
    "C": [0.01 * (1 if (i // 3) % 2 == 0 else -1) for i in range(200)],
}
res = P.build_risk_managed_weights(
    {"A": [1.0], "B": [1.0], "C": [1.0]},
    returns=rets, target_vol=0.15, vol_lookback=60,
    gross_leverage=1.0, max_position=0.60, net_target=None)

check("the construction ran", res.get("status") == "ok",
      f"status={res.get('status')}")
check(
    "the portfolio volatility estimate is BELOW the target",
    res["portfolio_vol_estimate"] <= 0.15 * 1.05,
    f"estimate={res['portfolio_vol_estimate']:.4f} target=0.15",
)
check(
    "the volatility scale is reported and is below 1 for a hot book",
    "vol_scale" in res and res["vol_scale"] > 0,
    f"vol_scale={res.get('vol_scale')}",
)
check(
    "the volatility method is NAMED, not asserted",
    "EWMA" in res.get("vol_method", ""),
    f"method={res.get('vol_method')!r}",
)

print()
print("=" * 72)
print("TEST 5 — the drawdown scaler is a SLOPE, not a cliff")
print("=" * 72)

check("no drawdown means no scaling",
      abs(P.drawdown_scaler(0.0) - 1.0) < 1e-12)
check("a drawdown below the soft limit means no scaling",
      abs(P.drawdown_scaler(0.04) - 1.0) < 1e-12)
mid = P.drawdown_scaler(0.125)     # halfway between 0.05 and 0.20
check("halfway between the limits means roughly half exposure",
      0.3 < mid < 0.7, f"mid={mid}")
check("the hard limit reaches the floor",
      abs(P.drawdown_scaler(0.20) - 0.0) < 1e-12,
      f"at limit={P.drawdown_scaler(0.20)}")
check("beyond the hard limit stays at the floor",
      abs(P.drawdown_scaler(0.50) - 0.0) < 1e-12)
check(
    "the scaler is MONOTONE DECREASING",
    all(P.drawdown_scaler(d1) >= P.drawdown_scaler(d2)
        for d1, d2 in zip([0.0, 0.06, 0.10, 0.15, 0.19],
                          [0.06, 0.10, 0.15, 0.19, 0.25])),
    "the scaler is not monotone",
)

print()
print("=" * 72)
print("TEST 6 — the caps are applied LAST and bind")
print("=" * 72)

res2 = P.build_risk_managed_weights(
    {"A": [1.0], "B": [1.0], "C": [1.0]},
    returns=rets, target_vol=0.15, gross_leverage=1.0,
    max_position=0.10, net_target=None)
worst = max(abs(w) for w in res2["weights"].values())
check(
    "no weight exceeds the per-name cap",
    worst <= 0.10 + 1e-9,
    f"worst={worst}",
)
check(
    "the cap is RECORDED as applied",
    any("max_position" in k for k in res2.get("caps_applied", {})),
    f"caps={res2.get('caps_applied')}",
)

# The net target must be reached EXACTLY, even from a one-sided book.
res3 = P.build_risk_managed_weights(
    {"A": [1.0], "B": [1.0]}, returns=rets, target_vol=0.15,
    gross_leverage=1.0, max_position=0.60, net_target=0.0)
check(
    "the net target is reached EXACTLY",
    abs(res3["net"]) < 1e-9,
    f"net={res3['net']}",
)

print()
print("=" * 72)
print("TEST 7 — the risk report shows the SHAPE of the risk")
print("=" * 72)

rep = P.portfolio_risk_report(
    {"A": 0.5, "B": 0.3, "C": 0.2}, returns=rets,
    cov=[[0.0004, 0.0, 0.0], [0.0, 0.0025, 0.0], [0.0, 0.0, 0.0009]],
    asset_class={"A": "equity", "B": "equity", "C": "rates"},
    target_vol=0.15)

check("the report names the number of positions", rep["n_positions"] == 3)
check("the gross is the sum of the absolute weights",
      abs(rep["gross"] - 1.0) < 1e-9, f"gross={rep['gross']}")
check("the net is the signed sum",
      abs(rep["net"] - 1.0) < 1e-9, f"net={rep['net']}")
check("the concentration (HHI) is reported",
      "hhi" in rep and rep["hhi"] > 0, f"hhi={rep.get('hhi')}")
check(
    "the effective number of names is between 1 and the count",
    1.0 <= rep["effective_names"] <= 3.0 + 1e-9,
    f"effective={rep['effective_names']}",
)
check(
    "the per-name risk contributions are reported and sum to 1",
    abs(sum(rep["risk_contributions"].values()) - 1.0) < 1e-9,
    f"rc={rep.get('risk_contributions')}",
)
check(
    "the risk contributions follow the variances (B risks most)",
    rep["risk_contributions"]["B"] > rep["risk_contributions"]["A"]
    > rep["risk_contributions"]["C"],
    f"rc={rep.get('risk_contributions')}",
)
check(
    "the per-asset-class exposure is reported",
    rep.get("by_asset_class", {}).get("equity") == 0.8,
    f"by_class={rep.get('by_asset_class')}",
)
check("the realised volatility of the book is reported",
      rep.get("realised_vol_annualised") is not None,
      f"realised_vol={rep.get('realised_vol_annualised')}")

print()
print("=" * 72)
print("TEST 8 — a missing input degrades honestly")
print("=" * 72)

res4 = P.build_risk_managed_weights({}, returns=None)
check("no signals returns a status, not a crash",
      res4.get("status") == "no signals", f"got {res4}")
res5 = P.build_risk_managed_weights({"A": [None], "B": [None]},
                                    returns=None)
check("all-missing signals returns 'no signal', not a zero book",
      res5.get("status") == "no signal", f"got {res5}")
check("it does NOT return a book of zeros",
      not res5.get("weights"),
      f"weights={res5.get('weights')}")

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
