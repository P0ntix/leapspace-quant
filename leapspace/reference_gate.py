"""An INDEPENDENT reference implementation of the memecoin consistency gate.

WHY THIS MODULE EXISTS
----------------------
`leapspace.edge` is the package's own gate. This module re-derives the
same gate FROM THE RULES, in a separate file, with no imports from
`leapspace` at all (stdlib only), so that the two can be compared on
the same real trades. A shared helper would make the comparison
meaningless, so there is none: every function here is written against
the published rule it implements, and the source of that rule is named
in its docstring.

WHAT THE GATE IS FOR
--------------------
A wallet that made money is not necessarily a wallet with skill. The
gate asks whether the track record is REAL, CONSISTENT, and not an
artefact of selection, luck, or decay. Five failure modes:

  1. One lucky win      - one 500x carries the whole PnL.
  2. Coin-flip win rate - 55% over 12 bets is chance.
  3. Best-of-many       - the wallet is the max of N screened candidates.
  4. Decay              - the edge was real and is gone.
  5. One token          - every trade is the same token, so there is ONE
                          bet, not many.

THE RULES THIS MODULE IMPLEMENTS
---------------------------------
Each function names its authority below. Where the package's own
`AUTHORITATIVE_CONSISTENCY_STANDARDS.md` and the package's code
disagree, the disagreement is recorded in `reports/gate_crosscheck.md`
rather than papered over here.

  bet_structure        Bailey & Lopez de Prado / Grinold: a bet is a
                       position that goes flat-to-flat in ONE asset.
                       Scaling in is not diversification.
  time_disjoint_bets   Grinold's "breadth": only NON-OVERLAPPING
                       decisions count as independent trials. Simultaneous
                       memecoin positions share one risk factor, so the
                       effective sample is the maximum set of mutually
                       non-overlapping holding intervals (classic greedy
                       interval scheduling by earliest end time).
  wilson_interval      NIST/SEMATECH e-Handbook 7.2.4.1, Wilson score
                       interval: "recommended ... for virtually all
                       combinations of n and p", and its lower limit
                       cannot go negative.
  binomial_tail_p      Barber, Bay & Solberg, "Bayes Rules!" Ch.3: the
                       Beta-Binomial posterior with a uniform Beta(1,1)
                       prior. P(theta > 0.5 | w wins in n trials) is the
                       regularised incomplete beta at 1/2, which in
                       binomial form is
                           sum_{k=0}^{w} C(n+1, k) / 2^(n+1).
                       NOTE the n+1: the posterior is over n+1 predictive
                       Bernoulli outcomes (the n observed ones plus the
                       prior's one pseudo-observation). It is NOT the
                       null-hypothesis significance test
                       P(X <= w) for X ~ Binomial(n, 0.5), which is a
                       different quantity and OVERSTATES skill.
  expected_max_sharpe  Bailey & Lopez de Prado, "The Deflated Sharpe
                       Ratio", Eq. (1): the expected maximum Sharpe over
                       N independent trials under a null of no skill,
                       with the Euler-Mascheroni refinement
                           SR0 = (1-gamma) Z^-1[1-1/N]
                                 + gamma  Z^-1[1-1/(N e)].
  deflated_sharpe      The same paper, Eq. (2):
                           DSR = Z[ (SR - SR0) sqrt(T-1)
                                    / sqrt(1 - g3 SR + ((g4-1)/4) SR^2) ].
                       T is the EFFECTIVE sample size (independent bets),
                       never the raw trade count.

THE SAMPLE-SIZE RULE (the one that decides most wallets)
---------------------------------------------------------
The cited criteria are explicit: "N is a count of INDEPENDENT Bernoulli
trials, so the input must be the count of NON-OVERLAPPING trades, not
raw trades." Every statistical test here - the Wilson interval, the
Bayesian skill probability and the DSR's sqrt(T-1) term - is therefore
computed on the EFFECTIVE sample: the number of mutually
non-overlapping holding intervals across all assets.

VENDOR BANDS ARE CONTEXT, NEVER A VERDICT INPUT
-----------------------------------------------
The GMGN win-rate band (> 0.6) and profit-ratio band (> 1.0) are
commercial conventions, not professional standards. They are reported
beside the verdict and never enter it. A vendor label cannot make a
wallet pass a statistical test.
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "bet_structure", "independent_bets", "time_disjoint_bets",
    "wilson_interval", "binomial_tail_p", "expected_max_sharpe",
    "deflated_sharpe", "evaluate", "nist_sample_size",
    "ANALYST_CHOICE_THRESHOLDS", "CITED_RULES",
]

#: The standard normal, from the stdlib. `NormalDist.inv_cdf` is
#: Wichura's AS241 (accurate to ~1e-15), which is a different algorithm
#: from the rational approximation the package uses, so a disagreement
#: here is a real disagreement rather than the same maths twice.
_ND = NormalDist()

#: Euler-Mascheroni constant (Bailey & Lopez de Prado, Eq. (1)).
_EULER_GAMMA = 0.5772156649015329


# --------------------------------------------------------------------------
# Thresholds and their provenance
# --------------------------------------------------------------------------

#: Every threshold the gate applies. Values are the package's; the
#: PROVENANCE is the point of this table. `CITED` items come from a
#: published source, `ANALYST_CHOICE` items are this package's
#: invention and are labelled as such wherever they are reported.
ANALYST_CHOICE_THRESHOLDS: Dict[str, Any] = {
    "max_largest_win_share": 0.50,
    "min_bayesian_skill": 0.95,
    "min_deflated_sharpe": 0.95,
    "max_edge_decay_ratio": 0.50,
    "min_independent_bets": 5,
    "min_distinct_tokens": 2,
    "min_closed_trades": 30,
    "min_observations_for_period_statistic": 36,
    "min_periods_with_positive_return": 3,
    "min_consistency_ratio": 0.50,
}

#: What each rule IS, and where it comes from. Kept next to the code so
#: a reader never has to guess whether a number is a standard or a
#: preference.
CITED_RULES: Dict[str, Dict[str, str]] = {
    "bayesian_skill": {
        "rule": ("P(theta > 0.5 | w wins in n independent Bernoulli trials) "
                 "under a uniform Beta(1,1) prior = "
                 "sum_{k=0}^{w} C(n+1,k) / 2^(n+1)."),
        "authority": ("Barber, Bay & Solberg, 'Bayes Rules!' Ch.3 - the "
                      "Beta-Binomial model; the regularised incomplete beta "
                      "at 1/2 in binomial form."),
        "threshold_note": ("The 0.95 bar is an ANALYST_CHOICE - no source "
                           "publishes a probability threshold for skill."),
    },
    "min_independent_bets": {
        "rule": ("A bet is a position that goes flat-to-flat in one asset. "
                 "The effective sample is the maximum set of mutually "
                 "non-overlapping holding intervals across all assets."),
        "authority": ("Bailey & Lopez de Prado, 'The Deflated Sharpe "
                      "Ratio'; Grinold's 'breadth' (count only independent "
                      "bets), restated by the CFA Institute."),
    },
    "deflated_sharpe": {
        "rule": ("DSR = Z[(SR - SR0) sqrt(T-1) / "
                 "sqrt(1 - g3 SR + ((g4-1)/4) SR^2)], with SR0 the "
                 "expected maximum Sharpe over N screened candidates."),
        "authority": ("Bailey & Lopez de Prado, 'The Deflated Sharpe "
                      "Ratio', Eq. (1) and Eq. (2)."),
        "threshold_note": ("DSR >= 0.95 is the paper's own framing; the "
                           "0.95 acceptance bar is cited, not invented."),
    },
    "wilson": {
        "rule": ("Wilson score interval for a win rate: the interval whose "
                 "coverage holds for essentially every n and p, and whose "
                 "lower limit cannot be negative."),
        "authority": ("NIST/SEMATECH e-Handbook 7.2.4.1, Wilson score "
                      "interval."),
    },
    "edge_decay": {
        "rule": ("Recent half expectancy must be at least "
                 "max_edge_decay_ratio times the early half expectancy."),
        "authority": ("ANALYST_CHOICE threshold; the measure (early vs "
                      "recent expectancy of the BET series) follows the "
                      "package's stated rule."),
    },
    "min_observations_for_period_statistic": {
        "rule": ("A period-based statistic needs enough observations to "
                 "mean anything."),
        "authority": ("CFA Institute (GIPS) 1.A.3 / 6.A.1(a) / 8.C.1(a)."),
    },
}


# --------------------------------------------------------------------------
# Small numeric helpers (stdlib only)
# --------------------------------------------------------------------------

def _norm_cdf(x: float) -> float:
    """P(Z <= x) for a standard normal."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (stdlib `statistics.NormalDist`)."""
    if p <= 0.0:
        return -8.0
    if p >= 1.0:
        return 8.0
    return _ND.inv_cdf(p)


def _token_key(t: Dict[str, Any]) -> str:
    """The asset a trade belongs to.

    Rule: one asset = one contract address. The symbol is only a
    fallback, because two different contracts can share a ticker.
    """
    return t.get("token_address") or t.get("token") or t.get("symbol") or "?"


def _ts(t: Dict[str, Any]) -> int:
    return int(t.get("ts") or 0)


def _is_leg(t: Dict[str, Any]) -> bool:
    """Is this row a position-changing event (a raw leg)?

    Rule: a trade carries a side. `buy`/`sell` legs move the position;
    a row that only carries a realised PnL is an OUTCOME, not a leg.
    """
    return t.get("side") in ("buy", "sell")


def _is_closed(t: Dict[str, Any]) -> bool:
    """Is this row a CLOSED trade (a realised outcome)?

    Rule: a closed trade is one with a computable realised PnL.
    """
    return t.get("realised_pnl_usd") is not None


# --------------------------------------------------------------------------
# The bet structure
# --------------------------------------------------------------------------

def _flat_to_flat_bets(trades: Sequence[Dict[str, Any]]
                        ) -> List[Dict[str, Any]]:
    """Every bounded (flat-to-flat) bet, per asset, with its interval.

    THE RULE. A bet is a sequence of trades in ONE asset where the
    position is not closed before the next one opens
    (Bailey & Lopez de Prado; Grinold's breadth). Concretely, walk the
    asset's legs in time order holding the net position:

      - a BUY taken while the position is flat OPENS a bet, and the bet's
        start is that buy's timestamp;
      - further buys while the position is open are SCALING IN and stay
        inside the same bet - they are not new bets;
      - a SELL that returns the position to flat CLOSES the bet, and the
        bet's end is that sell's timestamp;
      - a position still open at the end of the data has NO bounded
        interval (an unbounded interval overlaps everything after it) and
        is excluded from every count of independent bets.

    The net position is floored at zero. A wallet cannot hold a negative
    balance of a token, so a sell with no matching buy (an airdrop or a
    transfer out) leaves the position flat and opens no bet.

    Returns a list of dicts with token / symbol / start / end, one per
    bounded bet, in per-asset order.
    """
    by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in trades:
        if not _is_leg(t):
            continue
        by_token.setdefault(_token_key(t), []).append(t)

    bets: List[Dict[str, Any]] = []
    for key, rows in by_token.items():
        rows = sorted(rows, key=_ts)
        net = 0.0
        start: Optional[int] = None
        for r in rows:
            side = r.get("side")
            amt = float(r.get("amount") or 0)
            ts = _ts(r)
            if side == "buy":
                if net <= 0.0:          # flat before this buy -> new bet
                    start = ts
                net += amt
            elif side == "sell":
                net -= amt
                if net <= 0.0:
                    if start is not None:
                        bets.append({
                            "token": key,
                            "symbol": r.get("symbol"),
                            "start": start,
                            "end": ts,
                            "pnl": 0.0,
                            "n_closed": 0,
                            "return_pct": None,
                        })
                    start = None
                    net = 0.0      # the position is flat, never negative
    return bets


def bet_structure(trades: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One outcome per INDEPENDENT BET, with the time-disjoint flag.

    THE RULE. Each bounded flat-to-flat bet carries the realised PnL of
    the closed trades that fall inside its holding interval, and the
    per-bet return that the risk ratios and the DSR are computed from.

    A closed trade is attributed to the bet whose holding interval
    CONTAINS ITS ENTRY TIME (`entry_ts` when the trade carries one,
    otherwise the trade's own timestamp). Entry time rather than exit
    time is the right key: the PnL of a trade is the PnL of the position
    that was opened at entry, and a FIFO lot can be closed in a later
    transaction than the one that opened it.

    The BET's return is the amount-weighted mean of its closed trades'
    returns. Two reasons: a bet may close through several partial sells,
    and the mean has to be a single number per observation so that the
    DSR's sqrt(T-1) term counts the same observations the return series
    contains. (The weighting convention is an ANALYST CHOICE; the
    alternative - money-weighting by cost - is reported in
    `reports/gate_crosscheck.md`.)

    Every bet also carries `time_disjoint`: True when it belongs to the
    maximum set of mutually non-overlapping holding intervals across all
    assets. That set is the EFFECTIVE sample, and it is the sample every
    statistical test in this module uses.
    """
    bets = _flat_to_flat_bets(trades)

    # ---- attribute each closed trade to its bet ------------------------
    closed_by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in trades:
        if _is_closed(t):
            closed_by_token.setdefault(_token_key(t), []).append(t)

    for key, cts in closed_by_token.items():
        token_bets = [b for b in bets if b["token"] == key]
        for ct in cts:
            entry = ct.get("entry_ts")
            if entry is None:
                entry = ct.get("ts")
            entry = entry or 0
            for b in token_bets:
                if b["start"] <= entry <= b["end"]:
                    b["pnl"] += float(ct.get("realised_pnl_usd") or 0)
                    b["n_closed"] += 1
                    amt = float(ct.get("amount") or 0)
                    rp = ct.get("return_pct")
                    if rp is not None:
                        b["_ret_num"] = b.get("_ret_num", 0.0) + amt * float(rp)
                        b["_ret_den"] = b.get("_ret_den", 0.0) + amt
                    break
            else:
                # A closed trade outside every bet interval (e.g. a sell
                # of tokens the wallet was airdropped) belongs to no bet
                # and therefore contributes to no bet's outcome.
                pass

    for b in bets:
        den = b.get("_ret_den") or 0.0
        b["return_pct"] = (b.get("_ret_num", 0.0) / den) if den else None
        b.pop("_ret_num", None)
        b.pop("_ret_den", None)

    # ---- the EFFECTIVE set: mutually non-overlapping intervals --------
    # Greedy interval scheduling: take the bet with the earliest END
    # time, then the earliest-ending bet that starts at or after it.
    # Intervals are half-open, so a bet that starts exactly when the
    # previous one ends does not overlap it.
    #
    # The bets are returned in CHRONOLOGICAL order (by end time), not
    # grouped by asset. The order matters: the effective bets are the
    # gate's return series, and a series whose order depends on which
    # asset happened to be iterated first would make the Sharpe, the
    # skewness and the edge-decay split depend on a dictionary's
    # insertion order rather than on time.
    bets.sort(key=lambda b: (b["end"], b["start"]))
    last_end: Optional[int] = None
    for b in bets:
        b["time_disjoint"] = bool(last_end is None or b["start"] >= last_end)
        if b["time_disjoint"]:
            last_end = b["end"]
    return bets


def independent_bets(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Count the INDEPENDENT BETS, with per-asset detail.

    THE RULE. Two counts exist and both are reported.

      * `independent_bets` - the number of times a position went from
        flat to invested, summed over assets. This is the count of
        bets a wallet made inside a single asset.
      * `bounded_bets` - how many of those actually closed. A position
        still open at the end of the data is a bet whose outcome is not
        known, so it cannot enter a Bernoulli sample.

    The number of ASSETS matters too: a wallet that bought one token
    forty times, with a single position running the whole time, has ONE
    bet and ONE asset - that is not a track record.

    The EFFECTIVE sample (bets that also do not overlap in time with a
    bet in another asset) is reported by `time_disjoint_bets`.
    """
    bets = _flat_to_flat_bets(trades)
    by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in trades:
        if not _is_leg(t):
            continue
        by_token.setdefault(_token_key(t), []).append(t)

    # Count flat->invested transitions per asset. This is the same walk
    # as the bet structure, so the two can never disagree about what a
    # bet is.
    per_token: Dict[str, int] = {}
    detail: List[Dict[str, Any]] = []
    total = 0
    for key, rows in by_token.items():
        rows = sorted(rows, key=_ts)
        net = 0.0
        n = 0
        for r in rows:
            if r.get("side") == "buy":
                if net <= 0.0:
                    n += 1
                net += float(r.get("amount") or 0)
            elif r.get("side") == "sell":
                net -= float(r.get("amount") or 0)
                if net <= 0.0:
                    net = 0.0
        per_token[key] = n
        total += n
        detail.append({"token": key, "trades": len(rows),
                       "independent_bets": n,
                       "bounded_bets": sum(1 for b in bets if b["token"] == key),
                       "symbol": rows[0].get("symbol") if rows else None})
    detail.sort(key=lambda d: -d["trades"])
    return {
        "independent_bets": total,
        "bounded_bets": len(bets),
        "raw_trades": len(trades),
        "distinct_tokens": len(by_token),
        "per_token": per_token,
        "detail": detail,
        "note": ("Trades in the SAME token with an open position between "
                 "them are ONE bet. Scaling in is not diversification."),
    }


def time_disjoint_bets(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """The maximum set of mutually NON-OVERLAPPING holding intervals.

    THE RULE. Grinold's breadth: only independent decisions count as
    independent trials, and "the emphasis is on the importance of
    counting only independent bets as breadth" (Grinold 1989, restated
    by the CFA Institute). Within one asset, two positions that overlap
    are one bet. ACROSS assets, two positions held at the same time are
    still one bet for a memecoin wallet, because every memecoin shares
    one risk factor and the outcomes move together.

    So the effective sample is the classic interval-scheduling problem:
    the maximum number of mutually disjoint intervals is found greedily
    by taking the interval with the earliest END time, then repeating.
    Intervals are half-open, so [a, b) and [b, c) do not overlap.
    Positions still open at the end of the data have no bounded interval
    and are excluded, because an unbounded interval overlaps everything
    after it.
    """
    bets = _flat_to_flat_bets(trades)
    ordered = sorted(bets, key=lambda b: (b["end"], b["start"]))
    selected: List[Dict[str, Any]] = []
    last_end: Optional[int] = None
    for b in ordered:
        if last_end is None or b["start"] >= last_end:
            selected.append(b)
            last_end = b["end"]

    n_open = 0
    by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in trades:
        if _is_leg(t):
            by_token.setdefault(_token_key(t), []).append(t)
    for rows in by_token.values():
        net = 0.0
        for r in sorted(rows, key=_ts):
            if r.get("side") == "buy":
                net += float(r.get("amount") or 0)
            else:
                net -= float(r.get("amount") or 0)
                if net <= 0.0:
                    net = 0.0
        if net > 0.0:
            n_open += 1

    return {
        "time_disjoint_bets": len(selected),
        "n_bounded_bets": len(bets),
        "n_open_bets": n_open,
        "selected": [{"token": b["token"], "symbol": b["symbol"],
                      "start": b["start"], "end": b["end"]}
                     for b in selected],
        "note": ("Maximum set of mutually non-overlapping holding "
                 "intervals. Bets held simultaneously in different tokens "
                 "are correlated and count once."),
    }


# --------------------------------------------------------------------------
# The statistics
# --------------------------------------------------------------------------

def wilson_interval(wins: int, n: int, confidence: float = 0.95
                     ) -> Tuple[Optional[float], Optional[float]]:
    """The Wilson score interval for a win rate. Returns (lower, upper).

    THE RULE. NIST/SEMATECH e-Handbook 7.2.4.1. For a proportion p_hat
    observed in n trials at confidence level 1-alpha, with
    z = Z^-1(1 - alpha/2):

        centre = (p_hat + z^2 / 2n) / (1 + z^2/n)
        half   = z / (1 + z^2/n) * sqrt( p_hat(1-p_hat)/n + z^2/4n^2 )

    NIST: the Wilson interval "was recommended by Agresti and Coull for
    virtually all combinations of n and p", and "its lower limit cannot
    be negative, which the naive Wald interval cannot guarantee".

    The interval is clipped to [0, 1] because a win rate cannot leave
    that range.
    """
    if n is None or int(n) <= 0:
        return (None, None)
    n = int(n)
    wins = max(0, min(int(wins), n))
    z = _norm_ppf(1.0 - (1.0 - confidence) / 2.0)
    p = wins / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def binomial_tail_p(wins: int, n: int) -> Optional[float]:
    """P(the true win rate exceeds 50%) under a uniform Beta(1,1) prior.

    THE RULE. Barber, Bay & Solberg, "Bayes Rules!" Ch.3: with a
    Beta(1,1) prior and w successes in n independent Bernoulli trials,
    the posterior over the win rate is Beta(w+1, n-w+1), and the skill
    statistic is P(theta > 0.5 | data). The regularised incomplete beta
    at 1/2 has a closed binomial form:

        P(theta > 0.5) = sum_{k=0}^{w} C(n+1, k) / 2^(n+1)

    The n+1 IS THE POINT. The posterior integrates over n+1 predictive
    Bernoulli outcomes - the n that were observed plus the prior's one
    pseudo-observation - so the binomial that appears has n+1 trials.

    This is NOT the null-hypothesis significance test
    P(X <= w) for X ~ Binomial(n, 0.5). The two quantities are close but
    different, and the significance test OVERSTATES skill: it reads a
    perfect record as 100% certain skill, and reads 55 wins in 100 as
    0.8644 where the posterior is 0.8401.

    Exact integer arithmetic (math.comb), divided once at the end, so
    there is no floating-point cancellation.

    Returns None when there is no sample, so an unavailable skill
    probability is never mistaken for a low one.
    """
    if n is None or int(n) <= 0:
        return None
    n = int(n)
    wins = max(0, min(int(wins), n))
    total = 0
    for k in range(0, wins + 1):
        total += math.comb(n + 1, k)
    return total / float(2 ** (n + 1))


def expected_max_sharpe(n_trials: int) -> float:
    """SR0: the expected maximum Sharpe over N independent trials.

    THE RULE. Bailey & Lopez de Prado, "The Deflated Sharpe Ratio",
    Eq. (1): under a null of no skill, the best of N independent trials
    is expected to have a Sharpe of

        SR0 = sqrt(V[{SR_n}]) * ( (1-gamma) Z^-1[1 - 1/N]
                                 + gamma  Z^-1[1 - 1/(N e)] )

    with gamma the Euler-Mascheroni constant. This package (and the
    package's standards document) work in the V = 1 units, where the
    sqrt(V) factor is 1, so SR0 is the bracketed term.

    N = 1 means no selection at all, so there is nothing to deflate
    against and SR0 = 0.
    """
    n = max(1, int(n_trials))
    if n <= 1:
        return 0.0
    return ((1.0 - _EULER_GAMMA) * _norm_ppf(1.0 - 1.0 / n)
            + _EULER_GAMMA * _norm_ppf(1.0 - 1.0 / (n * math.e)))


def deflated_sharpe(sharpe: float, n_obs: int, n_trials: int,
                    skew: float = 0.0, kurtosis: float = 3.0
                    ) -> Optional[float]:
    """The Deflated Sharpe Ratio, per Bailey & Lopez de Prado Eq. (2).

    THE RULE.

        DSR = Z[ (SR - SR0) * sqrt(T - 1)
                 / sqrt( 1 - g3*SR + ((g4 - 1)/4) * SR^2 ) ]

    `n_obs` is T, the sample length, and it MUST be the effective sample
    size - the count of independent bets - with `sharpe` computed over
    exactly those observations. Feeding a raw trade count here while
    the Sharpe is per-bet is the most common way to manufacture a DSR
    that looks like skill, and it is a UNIT error: the numerator's
    sqrt(T-1) and the denominator's moments have to describe the same
    observations.

    `skew` is g3 and `kurtosis` is g4, the (non-excess) skewness and
    kurtosis of the return series, so a normal distribution has g4 = 3.

    Returns None when the inputs cannot support the statistic, so an
    unavailable DSR is never mistaken for a low one.
    """
    n_trials = max(1, int(n_trials))
    sr0 = expected_max_sharpe(n_trials)
    g3 = 0.0 if skew is None else float(skew)
    g4 = 3.0 if kurtosis is None else float(kurtosis)
    denom_var = (1.0 - g3 * float(sharpe)
                 + ((g4 - 1.0) / 4.0) * (float(sharpe) ** 2))
    if denom_var <= 0.0:
        return None
    t_used = max(2, int(n_obs))
    z = ((float(sharpe) - sr0) * math.sqrt(max(1, t_used - 1))) \
        / math.sqrt(denom_var)
    return _norm_cdf(z)


def nist_sample_size(p0: float = 0.50, p1: float = 0.55,
                     alpha: float = 0.05, beta: float = 0.20,
                     delta: float = 0.05) -> Dict[str, Any]:
    """The NIST sample size for a win-rate claim. Reported BESIDE the
    triage verdict, never as the verdict.

    THE RULE. NIST/SEMATECH e-Handbook 7.2.4.2. The number of
    independent Bernoulli trials n needed to show that a true win rate
    p1 beats p0, with significance alpha (one-sided) and power 1-beta:

        n' = ( ( z_alpha sqrt(p0(1-p0)) + z_beta sqrt(p1(1-p1)) ) / delta )^2

    with a continuity correction of 1/delta. For p0 = 0.50 against
    p1 = 0.55 at alpha = 0.05, beta = 0.20, delta = 0.05 this is
    n >= 617, or 637 with the continuity correction - about 21x the
    30-trade floor, which is why the floor is not a standard.

    This is the STANDARD bar. A wallet can be CONSISTENT on a handful of
    bets and still be nowhere near the number of independent bets a
    published claim would need; both numbers are reported so the two can
    never be confused.
    """
    z_a = _norm_ppf(1.0 - alpha)
    z_b = _norm_ppf(1.0 - beta)
    n_prime = ((z_a * math.sqrt(p0 * (1.0 - p0))
                + z_b * math.sqrt(p1 * (1.0 - p1))) / delta) ** 2
    corrected = int(math.ceil(n_prime + 1.0 / delta))
    return {
        "n_required": corrected,
        "n_required_no_continuity": int(math.ceil(n_prime)),
        "p0": p0, "p1": p1, "alpha": alpha, "beta": beta, "delta": delta,
        "authority": ("NIST/SEMATECH e-Handbook 7.2.4.2, "
                      "https://www.itl.nist.gov/div898/handbook/prc/"
                      "section2/prc242.htm"),
        "note": ("The sample size is a function of the CLAIM, not a "
                 "constant, and it counts INDEPENDENT bets."),
    }


# --------------------------------------------------------------------------
# The gate
# --------------------------------------------------------------------------

def evaluate(trades: Sequence[Dict[str, Any]],
             trials_scanned: Optional[int] = None,
             choices: Optional[Dict[str, Any]] = None,
             periods: Optional[Sequence[Dict[str, Any]]] = None,
             context: Optional[Dict[str, Any]] = None
             ) -> Dict[str, Any]:
    """Judge a wallet's edge. Returns the metrics, the fluke tests and a
    verdict of CONSISTENT / WEAK / FLUKE / INSUFFICIENT.

    THE RULES. The same decision rules as the package:

      * The fluke tests are largest-win-share, Bayesian skill, Deflated
        Sharpe, edge decay, insufficient independent bets, single-token
        and too-few-closed-trades. PBO is a SCAN-level test (it needs
        the full screened candidate matrix, so it runs over the whole
        universe, not on one wallet) and is reported here as NOT
        EVALUATED rather than as a pass.
      * A DEFINITIVE rejection binds before an insufficiency. A wallet
        whose whole profit is one lucky win is REJECTED whether or not
        it also has too few trades; otherwise a thin sample would
        excuse a fluke.
      * An UNKNOWN trial count is an AUTOMATIC REJECTION of the
        selection-bias test. The cited criterion reads "reject if
        DSR < 0.95, or PBO > 0.05, or N (number of wallets screened) is
        not recorded". A caller that forgets how many candidates it
        screened is asserting the least evidenced case, so the gate
        refuses rather than passes.
      * Every statistical test uses the EFFECTIVE sample - the number
        of mutually non-overlapping holding intervals across all assets
        - never the raw trade count.

    `trials_scanned` is how many candidate wallets were screened before
    this one was picked: the N in the Deflated Sharpe. Under-reporting
    it inflates the verdict.

    `periods` is an optional list of {period, return_pct} for the
    consistency ratio.

    `context` carries scan-level facts the per-wallet data cannot
    supply: `universe_survivorship_selected`, `first_onchain_activity_ts`,
    `chains_observed` and `vendor_labels`. Vendor labels are CONTEXT
    ONLY and never enter the verdict.
    """
    ch = dict(ANALYST_CHOICE_THRESHOLDS)
    if choices:
        ch.update(choices)

    closed_trades = [t for t in trades if _is_closed(t)]
    raw_closed = len(closed_trades)
    raw_pnls = [float(t.get("realised_pnl_usd") or 0) for t in closed_trades]
    total_pnl_raw = sum(raw_pnls)

    # ---- the independent bet structure --------------------------------
    structure = bet_structure(trades)
    effective = [b for b in structure if b.get("time_disjoint")]
    n_eff = len(effective)
    wins = sum(1 for b in effective if b["pnl"] > 0)
    losses = n_eff - wins
    win_rate = (wins / n_eff) if n_eff else None
    total_pnl = sum(b["pnl"] for b in effective)
    bet_pnls = [b["pnl"] for b in effective]

    ib = independent_bets(trades)
    tdb = time_disjoint_bets(trades)

    # ---- skill probability and the Wilson interval ---------------------
    # Both use the EFFECTIVE sample: n independent Bernoulli trials.
    skill_p = binomial_tail_p(wins, n_eff) if n_eff else None
    wilson_lo, wilson_hi = wilson_interval(wins, n_eff) if n_eff else (None, None)

    # ---- the largest win -----------------------------------------------
    largest_win = max(bet_pnls) if bet_pnls else 0.0
    largest_win_share = ((largest_win / total_pnl)
                         if total_pnl > 0 and largest_win > 0 else None)

    # ---- the return series over the BET observations -------------------
    # One observation per effective bet, on the same scale as the bet
    # count used in the DSR's sqrt(T-1) term. Mixing a bet count with
    # per-trade returns is the unit trap.
    rets = [float(b["return_pct"]) if b.get("return_pct") is not None else 0.0
            for b in effective]
    sharpe = sortino = calmar = None
    g3 = g4 = None
    g3_canonical = g4_canonical = None
    if len(rets) >= 2:
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        sd = math.sqrt(var)
        if sd > 0:
            sharpe = mean / sd
            n = len(rets)
            m3 = sum((r - mean) ** 3 for r in rets) / n
            m4 = sum((r - mean) ** 4 for r in rets) / n
            # SKEW AND KURTOSIS - AN UNSPECIFIED CONVENTION.
            #
            # Bailey & Lopez de Prado's Eq. (2) needs gamma_3 and
            # gamma_4, "the skewness and kurtosis of the returns
            # distribution". Neither the paper nor the package's
            # standards document pins the ESTIMATOR, so this is an
            # ANALYST CHOICE, and two textbook estimators are in use:
            #
            #   naive sample (used here):  g3 = m3 / s^3, g4 = m4 / s^4
            #       with m_k = (1/n) SUM (r - rbar)^k and s the
            #       sample standard deviation;
            #   population moment:         g3 = m3 / m2^1.5, g4 = m4 / m2^2
            #       with every moment normalised by 1/n, so a normal
            #       sample gives g4 = 3 EXACTLY.
            #
            # The DSR denominator 1 - g3*SR + ((g4-1)/4)*SR^2 is
            # calibrated on a normal distribution (g4 = 3), so the
            # estimator changes the size of the correction. The
            # reference uses the naive sample estimator so that the
            # end-to-end cross-check isolates the logic that IS
            # specified - the effective sample size, the bet structure,
            # the thresholds and the verdict precedence - rather than an
            # unspecified convention. The canonical alternative is
            # reported alongside as `skewness_g3_canonical` /
            # `kurtosis_g4_canonical`, and the sensitivity it implies is
            # quantified in reports/gate_crosscheck.md.
            g3 = m3 / (sd ** 3)
            g4 = m4 / (sd ** 4)
            m2 = sum((r - mean) ** 2 for r in rets) / n
            g3_canonical = m3 / (m2 ** 1.5)
            g4_canonical = m4 / (m2 ** 2)
        downside = [min(0.0, r) for r in rets]
        dd = math.sqrt(sum(r * r for r in downside) / len(rets))
        sortino = (mean / dd) if dd > 0 else None
        eq = 0.0
        peak = 0.0
        maxdd = 0.0
        for r in rets:
            eq += r
            peak = max(peak, eq)
            maxdd = min(maxdd, eq - peak)
        calmar = ((mean * len(rets)) / abs(maxdd)) if maxdd < 0 else None

    # ---- the Deflated Sharpe -------------------------------------------
    n_trials_known = trials_scanned is not None and int(trials_scanned) >= 1
    dsr = None
    dsr_detail: Dict[str, Any] = {}
    if sharpe is not None and n_trials_known and n_eff > 1:
        N = max(1, int(trials_scanned))
        g3c = g3 if g3 is not None else 0.0
        g4c = g4 if g4 is not None else 3.0
        dsr = deflated_sharpe(sharpe, max(2, n_eff), N, g3c, g4c)
        if dsr is not None:
            dsr_detail = {
                "observed_sharpe": round(sharpe, 4),
                "sr0_expected_max_from_trials": round(expected_max_sharpe(N), 4),
                "trials_scanned": N,
                "skewness_g3": round(g3c, 4),
                "kurtosis_g4": round(g4c, 4),
                "n_obs_used": max(2, n_eff),
            }

    # ---- consistency of periods ----------------------------------------
    consistency_ratio = None
    n_periods = len(periods) if periods else 0
    n_periods_positive = 0
    if periods:
        vals = [float(p.get("return_pct") or 0.0) for p in periods]
        n_periods_positive = sum(1 for v in vals if v > 0)
        if vals:
            consistency_ratio = n_periods_positive / len(vals)

    # ---- edge decay ------------------------------------------------------
    # THE RULE. Compare the early half of the track record with the
    # recent half. The track record is the BET series (the same
    # observations every other test uses), split in half by time, and
    # the ratio is recent expectancy over early expectancy.
    decay = None
    if n_eff >= 4:
        half = n_eff // 2
        early = [b["pnl"] for b in effective[:half]]
        recent = [b["pnl"] for b in effective[half:]]
        e_exp = sum(early) / len(early) if early else 0.0
        r_exp = sum(recent) / len(recent) if recent else 0.0
        decay = {
            "early_expectancy": round(e_exp, 4),
            "recent_expectancy": round(r_exp, 4),
            "ratio": (round(r_exp / e_exp, 4) if e_exp > 0 else None),
            "n_early": len(early),
            "n_recent": len(recent),
        }

    # ---- the fluke tests -------------------------------------------------
    ctx = context or {}
    tests: List[Dict[str, Any]] = []

    #: A failed DEFINITIVE test rejects the wallet. A failed
    #: INSUFFICIENT test only defers the verdict.
    DEFINITIVE = {"largest_win_share", "skill_not_distinguishable",
                  "deflated_sharpe", "edge_decay",
                  "survivorship_selected_universe",
                  "backfilled_or_pre_listing_performance"}
    INSUFFICIENT = {"insufficient_independent_bets", "single_token_only",
                    "too_few_closed_trades",
                    "min_observations_for_period_statistic",
                    "min_periods_with_positive_return"}

    def add(key: str, failed: bool, detail: str,
            severity: str = "reject") -> None:
        tests.append({
            "test": key,
            "failed": bool(failed),
            "severity": severity,
            "binding": ("REJECT" if key in DEFINITIVE else "INSUFFICIENT"),
            "detail": detail,
            "authority": CITED_RULES.get(key, {}).get(
                "authority", "ANALYST_CHOICE"),
        })

    add("largest_win_share",
        largest_win_share is not None
        and largest_win_share > ch["max_largest_win_share"],
        (f"largest win carries "
         f"{round(largest_win_share * 100, 1) if largest_win_share is not None else 'n/a'}% "
         f"of total PnL (threshold {ch['max_largest_win_share']})"))

    add("skill_not_distinguishable",
        skill_p is not None and skill_p < ch["min_bayesian_skill"],
        (f"P(win rate > 0.5) = {round(skill_p, 4) if skill_p is not None else 'n/a'} "
         f"(threshold {ch['min_bayesian_skill']}); "
         f"{wins}W/{losses}L over {n_eff} independent bets"))

    if n_trials_known:
        dsr_msg = (f"DSR = {round(dsr, 4) if dsr is not None else 'n/a'} "
                   f"after deflating for {trials_scanned} trial(s) scanned; "
                   f"threshold > {ch['min_deflated_sharpe']}")
    else:
        dsr_msg = ("DSR = not computable - UNKNOWN trial count. The number "
                   "of candidates scanned was not recorded, so the selection "
                   "bias cannot be corrected. The cited criterion treats an "
                   "unknown N as an automatic reject.")
    add("deflated_sharpe",
        (not n_trials_known) or dsr is None or dsr <= ch["min_deflated_sharpe"],
        dsr_msg)

    # PBO is a SCAN-level test: it needs the full screened universe, so
    # it is NOT EVALUATED on a single wallet - and it is reported as not
    # evaluated rather than quietly counted as a pass.
    add("probability_of_backtest_overfitting", False,
        "NOT EVALUATED: the full screened universe was not supplied, and "
        "PBO is undefined for a single candidate. Run it at the scan "
        "layer over the candidate matrix.",
        severity="not_evaluated")

    if ctx.get("universe_survivorship_selected"):
        add("survivorship_selected_universe", True,
            "the pool this wallet was drawn from omitted wallets that were "
            "admitted and later decayed, or the screened universe was not "
            "published. Skill cannot be inferred from a survivorship-"
            "selected list.")
    else:
        add("survivorship_selected_universe", False,
            "the screened universe was published and not survivorship-"
            "selected")

    first_act = ctx.get("first_onchain_activity_ts")
    pre_listing = []
    if first_act:
        pre_listing = [t.get("ts") for t in trades
                       if t.get("ts") is not None and t.get("ts") < first_act]
    add("backfilled_or_pre_listing_performance", bool(pre_listing),
        (f"{len(pre_listing)} performance row(s) are dated BEFORE the "
         f"wallet's first observed on-chain activity ({first_act}) - "
         f"backfilled history" if pre_listing else
         "every performance row is dated on or after the wallet's first "
         "observed on-chain activity"))

    add("min_observations_for_period_statistic",
        len(rets) < ch["min_observations_for_period_statistic"],
        (f"{len(rets)} return observation(s); GIPS wants at least "
         f"{ch['min_observations_for_period_statistic']} before a "
         f"period-based statistic is reported"))

    if periods:
        add("min_periods_with_positive_return",
            n_periods_positive < ch["min_periods_with_positive_return"],
            (f"{n_periods_positive} positive period(s) out of {n_periods}; "
             f"the cited floor is {ch['min_periods_with_positive_return']}"))

    add("insufficient_independent_bets",
        n_eff < ch["min_independent_bets"],
        (f"{ib['independent_bets']} independent bet(s) from {n_eff} closed "
         f"bets (threshold {ch['min_independent_bets']}) - scaling in on "
         f"one token is one bet, not many"))

    add("single_token_only",
        ib["distinct_tokens"] < ch["min_distinct_tokens"],
        (f"traded {ib['distinct_tokens']} distinct token(s) (threshold "
         f"{ch['min_distinct_tokens']})"))

    add("edge_decay",
        decay is not None and decay.get("ratio") is not None
        and decay["ratio"] < ch["max_edge_decay_ratio"],
        (f"recent expectancy is {decay['ratio']}x the early expectancy "
         f"(threshold {ch['max_edge_decay_ratio']})" if decay else "n/a"))

    add("too_few_closed_trades",
        n_eff < ch["min_closed_trades"],
        f"{n_eff} closed bets (threshold {ch['min_closed_trades']})")

    failed = [t for t in tests if t["failed"]]
    definitive = [t["test"] for t in failed if t["binding"] == "REJECT"]
    insufficient = [t["test"] for t in failed if t["binding"] == "INSUFFICIENT"]

    # ---- the verdict -----------------------------------------------------
    # A definitive rejection binds FIRST: a wallet with one lucky win
    # carrying the whole PnL is REJECTED whether or not it also has too
    # few trades. Otherwise a thin sample would excuse a fluke.
    if definitive:
        verdict = "FLUKE"
        reason = ("rejected by: " + ", ".join(definitive)
                  + (f" (also insufficient: {', '.join(insufficient)})"
                     if insufficient else ""))
    elif insufficient:
        verdict = "INSUFFICIENT"
        reason = ("not enough independent, priced bets to separate skill "
                  "from luck: " + ", ".join(insufficient))
    elif n_eff == 0:
        verdict = "INSUFFICIENT"
        reason = "no closed trades with a computable PnL"
    elif consistency_ratio is not None \
            and consistency_ratio < ch["min_consistency_ratio"]:
        verdict = "WEAK"
        reason = (f"only {round(consistency_ratio * 100, 1)}% of periods were "
                  f"positive (threshold {ch['min_consistency_ratio']})")
    else:
        verdict = "CONSISTENT"
        reason = ("edge survives the fluke tests at "
                  f"{trials_scanned} trial(s) scanned")

    nist = nist_sample_size()

    return {
        "verdict": verdict,
        "reason": reason,
        # ---- the effective sample, and the raw counts beside it --------
        "n_closed_bets": n_eff,
        "n_closed_trades_raw": raw_closed,
        "effective_sample_size": n_eff,
        "time_disjoint_bets": tdb["time_disjoint_bets"],
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "wilson_interval": {"lower": wilson_lo, "upper": wilson_hi,
                            "confidence": 0.95},
        "bayesian_skill_p": skill_p,
        "bayesian_skill_meaning": (
            "P(true win rate > 50%) with a uniform Beta(1,1) prior, i.e. "
            "the regularised incomplete beta at 1/2 in binomial form; "
            "NOT the null-hypothesis significance test"),
        "total_realised_pnl_usd": round(total_pnl, 2),
        "total_realised_pnl_usd_raw": round(total_pnl_raw, 2),
        "largest_win_usd": round(largest_win, 2),
        "largest_win_share": largest_win_share,
        "independent_bets": ib,
        "bet_outcomes": {
            "n_bets_total": len(structure),
            "n_closed_bets": n_eff,
            "wins_over_bets": wins,
            "losses_over_bets": losses,
            "win_rate_over_bets": win_rate,
            "bet_returns": [b.get("return_pct") for b in effective],
            "bets": structure,
        },
        "sharpe_per_trade": sharpe,
        "sortino_per_trade": sortino,
        "calmar": calmar,
        "skewness_g3": g3,
        "kurtosis_g4": g4,
        "deflated_sharpe": dsr,
        "deflated_sharpe_detail": dsr_detail,
        "consistency_ratio": consistency_ratio,
        "n_periods": n_periods,
        "n_periods_positive": n_periods_positive,
        "n_return_observations": len(rets),
        "edge_decay": decay,
        "fluke_tests": tests,
        "rejected_by": failed,
        "definitive_rejections": definitive,
        "insufficiencies": insufficient,
        "tests_not_evaluated": [t["test"] for t in tests
                                if t.get("severity") == "not_evaluated"],
        "thresholds": ch,
        "threshold_label": "ANALYST_CHOICE unless the test cites a source",
        "cited_rules": CITED_RULES,
        # ---- the STANDARD bar, reported beside the triage verdict -------
        "n_required_independent_bets": nist,
        "trials_scanned": trials_scanned,
        "trials_scanned_known": n_trials_known,
        "trials_note": (
            "The number of candidate wallets screened BEFORE this one was "
            "chosen. It enters the Deflated Sharpe, so scanning 500 "
            "wallets and keeping the best sets a far higher bar than "
            "scanning 5. Under-reporting it inflates the verdict."),
        # ---- VENDOR CONTEXT. NEVER a verdict input. ---------------------
        "vendor_context": {
            "win_rate_band": {
                "threshold": 0.60,
                "label": "GMGN 'strong' smart-money win-rate band",
                "authority": ("GMGN smart-money profile (commercial "
                              "on-chain analytics CONVENTION, not a "
                              "professional standard)"),
                "this_wallet_win_rate": win_rate,
                "clears_band": bool(win_rate is not None and win_rate > 0.60),
            },
            "pnl_ratio": {
                "threshold": 1.0,
                "label": "GMGN profit-ratio band",
                "authority": ("GMGN wallet analysis (commercial on-chain "
                              "analytics CONVENTION)"),
                "note": ("The profit ratio is gross proceeds over gross "
                         "cost; this gate reports realised PnL, not the "
                         "ratio, so the band is context and is NOT "
                         "computed."),
            },
            "vendor_labels": ctx.get("vendor_labels") or {},
            "rule": ("A vendor label is CONTEXT, never a standard. It does "
                     "not change the cited verdict and must never be "
                     "presented as one."),
        },
    }
