"""Ground truth for the consistency gate.

Six synthetic wallets, each built to fail or pass in one specific way,
plus a numerical check of the Bayesian skill probability.

WHY THIS LIVES IN THE PACKAGE AND NOT IN SCRATCH
------------------------------------------------
A ground-truth suite that lives outside the package is a suite that
gets cleaned up and never runs again. These are the cases that decide
whether the gate can be trusted, so they ship with the code.

THE SKILL PROBABILITY IS CHECKED NUMERICALLY
--------------------------------------------
The gate once used the null-hypothesis SIGNIFICANCE TEST
(P(X <= w) for Binomial(n, 0.5)) where the cited criteria mean the
BAYESIAN POSTERIOR PROBABILITY (P(p > 0.5) with a Beta(1,1) prior).
They are different quantities, and the significance test OVERSTATES
skill probability - so the gate was lenient in exactly the direction
that matters.

The starkest symptom: a PERFECT record (w wins from w bets) has
P(X <= w) = 1.0 under the significance test, so every flawless wallet
read as 100% certain skill. The true posterior for 3 wins from 3 bets
is 0.9375, and for 1 win from 1 bet it is 0.75.

The check below integrates the Beta(w+1, n-w+1) posterior density
numerically (Simpson's rule, written from the definition) and requires
the package's function to match it. If someone swaps the two
functions again, this fails loudly.
"""
from __future__ import annotations

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from leapspace import edge as E  # noqa: E402
from leapspace.stats import (bayesian_skill_probability,  # noqa: E402
                             binomial_tail_p)

FAILED: list = []
PASSED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED
    if condition:
        PASSED += 1
        print(f"  [OK]   {name}")
    else:
        FAILED.append(name)
        print(f"  [FAIL] {name}  {detail}")


# --------------------------------------------------------------------------
# the ground-truth wallet generator
# --------------------------------------------------------------------------
def make_wallet(n_bets: int = 60, win_rate: float = 0.7, tokens: int = 3,
                seed: int = 1, decay: bool = False, vary: bool = True,
                pnl: float = 10.0, spacing: int = 7200) -> list:
    """Build a synthetic trade history.

    A "bet" is a buy leg followed by a sell leg for the same token.
    `vary` makes the win and loss SIZES differ between bets: a
    constant return series has zero variance, so its Sharpe is
    undefined and the Deflated Sharpe cannot be computed at all.
    """
    rg = random.Random(seed)
    out = []
    for i in range(n_bets):
        tok = f"T{i % tokens}"
        win = rg.random() < win_rate
        mult = 1.0 if (not decay or i < n_bets // 2) else 0.1
        gain = pnl * (0.6 + rg.random() * 0.8) * mult if vary else pnl * mult
        loss = -pnl * (0.3 + rg.random() * 0.4) * mult
        out.append({"ts": 1000 + i * spacing, "token_address": tok,
                    "symbol": tok, "side": "buy", "amount": 100,
                    "price_usd": 1.0, "realised_pnl_usd": None})
        out.append({"ts": 1000 + i * spacing + spacing // 2,
                    "token_address": tok, "symbol": tok, "side": "sell",
                    "amount": 100, "price_usd": 1.05 if win else 0.95,
                    "realised_pnl_usd": gain if win else loss,
                    "return_pct": 0.05 if win else -0.03})
    return out


def make_one_big_win(n_bets: int = 10) -> list:
    """One trade carries the entire profit; everything else loses."""
    out = []
    for i in range(n_bets):
        tok = f"T{i % 3}"
        big = (i == 0)
        out.append({"ts": 1000 + i * 7200, "token_address": tok,
                    "symbol": tok, "side": "buy", "amount": 100,
                    "price_usd": 1.0, "realised_pnl_usd": None})
        out.append({"ts": 1000 + i * 7200 + 3600, "token_address": tok,
                    "symbol": tok, "side": "sell", "amount": 100,
                    "price_usd": 1.05 if big else 0.95,
                    "realised_pnl_usd": 4000.0 if big else -5.0,
                    "return_pct": 0.05 if big else -0.02})
    return out


# --------------------------------------------------------------------------
# 1. the Bayesian skill probability, checked by numerical integration
# --------------------------------------------------------------------------
def beta_pdf(x: float, a: int, b: int) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    log_pdf = ((a - 1) * math.log(x) + (b - 1) * math.log(1.0 - x)
               - math.lgamma(a) - math.lgamma(b) + math.lgamma(a + b))
    return math.exp(log_pdf)


def posterior_prob_above_half(wins: int, n: int) -> float:
    """P(p > 0.5) for a Beta(1,1) prior, by numerical integration."""
    a, b = wins + 1, n - wins + 1
    steps = 100000
    h = 0.5 / steps
    total = beta_pdf(0.5, a, b) + beta_pdf(1.0, a, b)
    for i in range(1, steps):
        x = 0.5 + i * h
        total += beta_pdf(x, a, b) * (4 if i % 2 else 2)
    return total * h / 3


print("=" * 74)
print("1. THE BAYESIAN SKILL PROBABILITY")
print("=" * 74)
for w, n in [(1, 1), (2, 4), (5, 10), (7, 10), (9, 10), (40, 80),
             (55, 100), (60, 100)]:
    exact = posterior_prob_above_half(w, n)
    got = bayesian_skill_probability(w, n)
    check(f"skill probability {w}/{n} matches the Beta posterior",
          got is not None and abs(got - exact) < 1e-5,
          f"package={got} integrated={exact}")

check("the skill probability is NOT the significance test",
      abs(bayesian_skill_probability(5, 10) - binomial_tail_p(5, 10)) > 1e-6,
      "the two must differ; if they are equal the conflation is back")
check("a PERFECT record no longer reads as certain skill",
      bayesian_skill_probability(3, 3) < 1.0,
      f"3 wins from 3 bets reads {bayesian_skill_probability(3, 3)}")
check("the significance test still computes what it says it does",
      abs(binomial_tail_p(55, 100)
          - sum(math.comb(100, k) for k in range(56)) / 2 ** 100) < 1e-12,
      f"got {binomial_tail_p(55, 100)}")

# The expected maximum Sharpe under the null, SR0. These are the
# PUBLISHED values of Bailey & Lopez de Prado's Eq. (3), pinned so the
# selection correction cannot drift again. SR0(2) was previously
# computed as sqrt(2*ln N) = 1.1774, which is the asymptotic
# approximation, not the published formula; the real value is 0.5198.
from leapspace.stats import expected_max_sharpe as SR0  # noqa: E402

check("SR0(1) = 0 (no selection when one candidate was screened)",
      abs(SR0(1)) < 1e-12, f"got {SR0(1)}")
check("SR0(2) = 0.5198 (the published formula, not sqrt(2*ln N))",
      abs(SR0(2) - 0.5197553443) < 1e-8, f"got {SR0(2)}")
check("SR0(10) = 1.5746",
      abs(SR0(10) - 1.5745983013) < 1e-8, f"got {SR0(10)}")
check("SR0(100) = 2.5306",
      abs(SR0(100) - 2.5306028932) < 1e-8, f"got {SR0(100)}")
check("SR0 is increasing in the number of trials",
      SR0(1) < SR0(2) < SR0(10) < SR0(100),
      f"got {SR0(1)}, {SR0(2)}, {SR0(10)}, {SR0(100)}")

# --------------------------------------------------------------------------
# 2. the six ground-truth wallets
# --------------------------------------------------------------------------
print()
print("=" * 74)
print("2. THE SIX GROUND-TRUTH WALLETS")
print("=" * 74)

v = E.evaluate_edge(make_wallet(60, 0.75, 3, 1), trials_scanned=1)
check("a genuinely consistent wallet is CONSISTENT",
      v["verdict"] == "CONSISTENT",
      f"got {v['verdict']}: {v['reason'][:90]}")
check("a consistent wallet's skill probability clears 0.95",
      (v.get("bayesian_skill_p") or 0) >= 0.95,
      f"got {v.get('bayesian_skill_p')}")
check("a consistent wallet reports enough independent bets",
      (v.get("effective_sample_size") or 0) >= 30,
      f"got {v.get('effective_sample_size')}")
check("a consistent wallet is not rejected by anything",
      not v.get("rejected_by"),
      f"got {[t['test'] for t in v.get('rejected_by', [])]}")

# The selection correction bites as the number of screened candidates
# grows. This wallet's Sharpe is 1.13, so it survives the correction
# for 1 and 2 candidates (SR0(2) = 0.52) and is rejected from 3
# candidates upward (SR0(3) = 0.85, SR0(10) = 1.57).
#
# NOTE: this used to assert rejection at N = 2, which passed only
# because SR0(2) was wrongly computed as sqrt(2*ln N) = 1.1774. With
# the published formula the wallet correctly survives two candidates,
# so the assertion moved to N = 3 - and the SR0 values are now pinned
# above so the formula cannot drift back.
v2 = E.evaluate_edge(make_wallet(60, 0.75, 3, 1), trials_scanned=3)
check("the same wallet is REJECTED once three candidates were screened",
      v2["verdict"] == "FLUKE" and
      "deflated_sharpe" in [t["test"] for t in v2.get("rejected_by", [])],
      f"got {v2['verdict']}: {v2['reason'][:80]}")
check("the Deflated Sharpe falls as the number of screened candidates grows",
      (E.evaluate_edge(make_wallet(60, 0.75, 3, 1),
                       trials_scanned=1).get("deflated_sharpe") or 0)
      > (v2.get("deflated_sharpe") or 0)
      > (E.evaluate_edge(make_wallet(60, 0.75, 3, 1),
                         trials_scanned=10).get("deflated_sharpe") or 0),
      "the selection correction must tighten as N grows")

v = E.evaluate_edge(make_wallet(60, 0.2, 3, 2), trials_scanned=1)
check("a mostly-losing wallet is FLUKE", v["verdict"] == "FLUKE",
      f"got {v['verdict']}")
check("the skill test is what rejects it",
      "skill_not_distinguishable" in [t["test"] for t in v.get("rejected_by", [])],
      f"got {[t['test'] for t in v.get('rejected_by', [])]}")

v = E.evaluate_edge(make_wallet(60, 0.5, 3, 3), trials_scanned=1)
check("a coin-flip wallet is FLUKE", v["verdict"] == "FLUKE",
      f"got {v['verdict']}: {v['reason'][:80]}")

v = E.evaluate_edge(make_wallet(60, 0.8, 3, 4, decay=True), trials_scanned=1)
check("a decaying wallet is FLUKE", v["verdict"] == "FLUKE",
      f"got {v['verdict']}: {v['reason'][:80]}")
check("the decay test is what rejects it",
      "edge_decay" in [t["test"] for t in v.get("rejected_by", [])],
      f"got {[t['test'] for t in v.get('rejected_by', [])]}")

v = E.evaluate_edge(make_wallet(60, 0.75, 3, 5), trials_scanned=None)
check("an UNKNOWN trial count is an automatic rejection",
      v["verdict"] == "FLUKE" and
      "deflated_sharpe" in [t["test"] for t in v.get("rejected_by", [])],
      f"got {v['verdict']}: {v['reason'][:80]}")

v = E.evaluate_edge(make_wallet(40, 0.75, 1, 3), trials_scanned=1)
check("a wallet that traded only ONE token is INSUFFICIENT",
      v["verdict"] == "INSUFFICIENT",
      f"got {v['verdict']}: {v['reason'][:80]}")

v = E.evaluate_edge(make_one_big_win(10), trials_scanned=1)
check("one lucky win carrying the whole profit is FLUKE",
      v["verdict"] == "FLUKE" and
      "largest_win_share" in [t["test"] for t in v.get("rejected_by", [])],
      f"got {v['verdict']}: {[t['test'] for t in v.get('rejected_by', [])]}")

# --------------------------------------------------------------------------
# 3. the verdict precedence
# --------------------------------------------------------------------------
print()
print("=" * 74)
print("3. VERDICT PRECEDENCE")
print("=" * 74)
v = E.evaluate_edge(make_wallet(3, 0.9, 1, 8), trials_scanned=1)
check("a definitive rejection outranks an insufficiency",
      v["verdict"] == "FLUKE",
      f"got {v['verdict']} (rejections "
      f"{[t['test'] for t in v.get('rejected_by', [])]}, insuff "
      f"{v.get('insufficiencies')})")

v = E.evaluate_edge(make_wallet(60, 0.75, 3, 9), trials_scanned=1)
check("PBO is reported as NOT EVALUATED without the full universe",
      "probability_of_backtest_overfitting" in (v.get("tests_not_evaluated")
                                                or []),
      f"got {v.get('tests_not_evaluated')}")

# --------------------------------------------------------------------------
print()
print("=" * 74)
print(f"RESULT: {PASSED} passed, {len(FAILED)} failed")
if FAILED:
    for f in FAILED:
        print(f"  FAILED: {f}")
print("=" * 74)
sys.exit(1 if FAILED else 0)
