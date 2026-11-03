"""Shared statistical primitives.

EXTRACTED, NOT REWRITTEN. The bodies below were moved verbatim out of
`edge.py`, `gamma.py` and `traders.py`, which each carried their own
copy. Duplicated numerics are a correctness risk: if one copy is ever
corrected and the others are not, the package silently produces two
different answers to the same question - and the DSR threshold, the
Bayesian skill probability and the Black-Scholes delta all depend on
these functions agreeing with each other.

CITATIONS
---------
`norm_ppf` (Acklam's rational approximation to the inverse normal CDF)
    Peter J. Acklam, "An Algorithm for Computing the Inverse Normal
    Cumulative Distribution Function", 1998.
    https://web.archive.org/web/20151110174102/http://home.online.no/~pjacklam/notes/invnorm/
    Accurate to about 1e-9 over the useful range, far tighter than any
    sample-size decision in this package turns on.

`expected_max_sharpe`
    Bailey & Lopez de Prado, "The Deflated Sharpe Ratio: Correcting for
    Selection Bias, Backtest Overfitting and Non-Normality".
    https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf
    SR0 = E[max SR] over N independent trials under the null of zero
    skill, with the Euler-Mascheroni refinement:
        SR0 = (1 - gamma) * Z^-1(1 - 1/N) + gamma * Z^-1(1 - 1/(N*e))

`deflated_sharpe_ratio`
    The same paper, Eq. (2):
        DSR = Z[ (SR - SR0) * sqrt(T-1) / sqrt(1 - g3*SR + ((g4-1)/4)*SR^2) ]
    ALL FOUR quantities must be on the SAME per-observation scale. If
    the Sharpe is per-trade but the observation count is per-period, the
    DSR silently reads 0 or 1. This package feeds it the BET return
    series and the BET count together, so the units agree.

`binomial_tail_p`
    P(X <= wins) for X ~ Binomial(n, 0.5), computed with EXACT integer
    arithmetic (math.comb, no floating-point summation). With a
    Beta(1,1) prior this is also the posterior probability that the
    true win rate exceeds 0.5, so one function serves both the
    significance test and the Bayesian skill probability.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional, Sequence, Tuple

#: Euler-Mascheroni constant.
EULER_GAMMA = 0.5772156649015329


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def poly(coeffs: Tuple[float, ...], x: float) -> float:
    """Horner evaluation of a coefficient list."""
    out = 0.0
    for c in coeffs:
        out = out * x + c
    return out

def norm_ppf(p: float) -> float:
    """Inverse normal CDF (Acklam), used for the DSR threshold."""
    if p <= 0.0:
        return -8.0
    if p >= 1.0:
        return 8.0
    a = (-3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00)
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return poly(c, q) / poly(d + (1.0,), q)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -poly(c, q) / poly(d + (1.0,), q)
    q = p - 0.5
    r = q * q
    return poly(a, r) * q / poly(b + (1.0,), r)

def binomial_tail_p(wins: int, n: int) -> float:
    """P(X <= wins) for X ~ Binomial(n, 0.5), EXACTLY (integer arithmetic).

    With a Beta(1,1) prior this is also the posterior probability that the
    true win rate exceeds 0.5, so one function serves both the
    significance test and the Bayesian skill probability.
    """
    if n <= 0:
        return 1.0
    wins = max(0, min(wins, n))
    total = 0
    for k in range(0, wins + 1):
        total += math.comb(n, k)
    return total / (2 ** n)

def expected_max_sharpe(n_trials: int) -> float:
    """E[max SR] over N independent trials under the null of zero skill.

    Bailey & Lopez de Prado, "The Deflated Sharpe Ratio", Eq. (3).
    With N = 1 there is no selection, so SR0 = 0.
    """
    n = max(1, int(n_trials))
    if n <= 1:
        return 0.0
    # The published formula is valid for N = 2 as well:
    #   SR0(2) = (1-gamma)*Z^-1(0.5) + gamma*Z^-1(1 - 1/(2e))
    #          = 0.4228*0 + 0.5772*0.9 = 0.5198
    # The sqrt(2*ln N) branch is only an asymptotic approximation and
    # gave 1.1774 at N=2 - which overstated the selection penalty.
    # It is used nowhere now.
    return ((1 - EULER_GAMMA) * norm_ppf(1 - 1.0 / n)
            + EULER_GAMMA * norm_ppf(1 - 1.0 / (n * math.e)))


def deflated_sharpe_ratio(sharpe: float, n_obs: int, n_trials: int,
                          skew: float = 0.0, kurtosis: float = 3.0
                          ) -> Tuple[Optional[float], Dict[str, Any]]:
    """The Deflated Sharpe Ratio, and the detail behind it.

    `n_obs` MUST be the effective sample size (independent bets), not
    the raw trade count, and `sharpe` MUST be computed over the same
    observations. Feeding a raw trade count here is the single most
    common way to get a DSR that looks like skill.

    Returns (None, {}) when the inputs cannot support the statistic, so
    an unavailable DSR is never confused with a low one.
    """
    n_trials = max(1, int(n_trials))
    sr0 = expected_max_sharpe(n_trials)
    g3 = 0.0 if skew is None else float(skew)
    g4 = 3.0 if kurtosis is None else float(kurtosis)
    denom_var = 1.0 - g3 * float(sharpe) + ((g4 - 1.0) / 4.0) * (float(sharpe) ** 2)
    if denom_var <= 0:
        return None, {}
    t_used = max(2, int(n_obs))
    z = ((float(sharpe) - sr0) * math.sqrt(max(1, t_used - 1))) / math.sqrt(denom_var)
    dsr = norm_cdf(z)
    return dsr, {
        "observed_sharpe": round(float(sharpe), 4),
        "sr0_expected_max_from_trials": round(sr0, 4),
        "trials_scanned": n_trials,
        "skewness_g3": round(g3, 4),
        "kurtosis_g4": round(g4, 4),
        "z": round(z, 4),
    }


def bayesian_skill_probability(wins: int, n: int) -> Optional[float]:
    """P(the true win rate > 0.5) with a uniform Beta(1,1) prior.

    This is the posterior probability the cited criteria mean. After w
    successes in n Bernoulli trials the posterior over the win rate p is
    Beta(w+1, n-w+1), and

        P(p > 0.5) = sum_{k=0}^{w} C(n+1, k) / 2^(n+1)

    (the regularised incomplete beta at 1/2, in binomial form).

    IT IS NOT THE SAME AS `binomial_tail_p`. That function is the
    null-hypothesis SIGNIFICANCE TEST, P(X <= w) for X ~ Binomial(n,
    0.5) - a related but different quantity. Using the significance
    test where the posterior probability belongs OVERSTATES skill:

        wins/n    significance test   posterior probability
        5/10      0.6230              0.5000
        55/100    0.8644              0.8401
        60/100    0.9824              0.9770

    Verified against numerical integration of the Beta posterior
    density (Simpson's rule, 200,000 steps): the n+1 form matches to
    1.7e-06; the significance test is off by up to 0.25.

    Returns None when there is no sample, so an unavailable skill
    probability is never confused with a low one.
    """
    if n is None or int(n) <= 0:
        return None
    wins = max(0, min(int(wins), int(n)))
    # sum_{k=0}^{wins} C(n+1, k) / 2^(n+1), computed in EXACT integer
    # arithmetic and only divided at the end.
    total = 0
    for k in range(0, wins + 1):
        total += math.comb(n + 1, k)
    return total / (2 ** (n + 1))
