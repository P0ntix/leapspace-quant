"""Probability of Backtest Overfitting (PBO) and the multiple-testing
corrections that decide whether a "best of many" selection is a finding or
an artefact.

WHY THIS MODULE EXISTS
-----------------------
`leapspace/edge.py` can only judge ONE wallet at a time, and it can only
deflate for a trial count the caller supplies. This module handles the
other half of the problem: the SELECTION PROCESS ITSELF. If you scanned N
candidates and kept the best one, the winner's Sharpe is inflated by the
selection. There are two published ways to price that inflation:

1. **PBO** - Bailey, Borwein, Lopez de Prado & Zhu (2016). Run the whole
   selection procedure on every combinatorial split of the sample and ask
   how often the in-sample winner lands in the BOTTOM HALF out of sample.
   A high PBO means the selection was noise-fitting; the paper's customary
   line is to reject a model whose PBO exceeds 0.05.
2. **Multiple-testing corrections** - Bonferroni (family-wise error rate),
   Benjamini-Hochberg (false discovery rate) and the Harvey-Liu-Zhu
   t-statistic hurdle. These say how strong a result must be before it
   survives the knowledge that N hypotheses were tried.

WHAT IS CITED AND WHAT IS AN ANALYST CHOICE
--------------------------------------------
`CITED_CRITERIA` holds the published rules with their authority, tag and
URL. `ANALYST_CHOICES` holds thresholds this package invented (there are
very few, and they say so). The rules implemented here are transcribed
from the papers named in `CITED_CRITERIA`; none of them was paraphrased
and presented as an author's.

THE SCALE TRAP (READ THIS BEFORE CHANGING THE SHARPE CODE)
------------------------------------------------------------
Every Sharpe ratio in this module is computed from PER-OBSERVATION
returns, using the sample standard deviation (ddof = 1) of exactly those
returns:

    Sharpe(x) = mean(x) / stdev(x),  stdev over ddof = 1

The scale is stated because the package already lost time to the same
class of bug in the Deflated Sharpe Ratio (SR-hat, SR0, gamma3 and
gamma4 must all live on the SAME per-observation scale, or the statistic
silently reads 0 or 1). Here the danger is milder but real: CSCV ranks
candidates by Sharpe computed over DIFFERENT row subsets (the in-sample
half and the out-of-sample half), so the subset length and the
standard-deviation convention must be identical on both sides. They are:
every candidate in a given combination is scored on the same rows with
the same formula, so the ddof choice cannot change a ranking, and the
absolute Sharpe value is never published - only the rank is used.

The Sharpe values are per-observation and NOT annualised. Annualisation
is a monotone transform applied identically to every candidate, so it
cannot change any CSCV ranking either; it is omitted so that the
published numbers can be read directly.

CITATION URL NOTES (verified from this host, 2026-11-03)
--------------------------------------------------------
* NIST Bonferroni: the handbook page lives at
  `.../handbook/prc/section4/prc473.htm` (HTTP 200, section 7.4.7.3
  "Bonferroni's method"). The `section2/prc473.htm` path returns HTTP 302
  to a generic landing page, so the section 4 path is the one cited.
* Harvey-Liu-Zhu: the working copy is
  `.../charvey/Research/Published_Papers/P118_and_the_cross.PDF` (HTTP
  200, 27 pages). The `.../charvey/Rev/Research/SSRN-id935099.pdf` path
  returns HTTP 404 from this host, so the working copy is cited.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Cited criteria
# --------------------------------------------------------------------------
CITED_CRITERIA: Dict[str, Dict[str, Any]] = {
    "probability_of_backtest_overfitting": {
        "label": "Probability of Backtest Overfitting (PBO) via CSCV",
        "authority": ("Bailey, Borwein, Lopez de Prado & Zhu, 'The "
                      "Probability of Backtest Overfitting', Journal of "
                      "Computational Finance 19(4), 2016"),
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": "http://www.davidhbailey.com/dhbpapers/backtest-prob.pdf",
        "note": ("Algorithm 2.3 (CSCV): partition the rows of the "
                 "candidate-by-time matrix into an even number S of equal "
                 "blocks, take ALL C(S, S/2) combinations of S/2 blocks as "
                 "the in-sample set with the complement as the out-of-sample "
                 "set, keep the in-sample best candidate n*, and record its "
                 "out-of-sample RELATIVE RANK. The logit of that rank is "
                 "lambda = ln(omega/(1-omega)); PBO is the integral of the "
                 "relative frequency of lambda over (-inf, 0]. Rank 1 is "
                 "the WORST out-of-sample performer, so lambda <= 0 means "
                 "the in-sample winner finished at or below the "
                 "out-of-sample median."),
    },
    "bonferroni_alpha_per_test": {
        "label": "Bonferroni-adjusted significance level for N tests",
        "authority": ("National Institute of Standards and Technology "
                      "(NIST/SEMATECH e-Handbook of Statistical Methods), "
                      "7.4.7.3 'Bonferroni's method'"),
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": ("https://www.itl.nist.gov/div898/handbook/prc/section4/"
                "prc473.htm"),
        "note": ("'one can construct each interval with confidence "
                 "coefficient (1 - alpha/g), and the Bonferroni inequality "
                 "insures that the overall confidence coefficient is at "
                 "least 1 - alpha'. The per-test level is alpha/g, so a "
                 "per-test p-value is significant at the family level only "
                 "if p <= alpha_family / g."),
    },
    "bh_fdr_procedure": {
        "label": "Benjamini-Hochberg false-discovery-rate procedure",
        "authority": ("Benjamini & Hochberg, 'Controlling the false "
                      "discovery rate: a practical and powerful approach "
                      "to multiple testing', J. R. Statist. Soc. B 57(1), "
                      "289-300 (1995)"),
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": "https://www.math.tau.ac.il/~yekutiel/eBayes/bh_1995.pdf",
        "note": ("Procedure (1): 'let k be the largest i for which "
                 "P_(i) <= (i/m) q*; then reject all H_(i), i = 1, 2, ..., "
                 "k'. The paper's own worked example (section 3.2) is the "
                 "rt-PA/APSAC trial with 15 ordered p-values at q* = 0.05, "
                 "which rejects the first FOUR."),
    },
    "multiple_testing_t_statistic_hurdle": {
        "label": "Minimum t-statistic for a newly discovered signal",
        "authority": ("Harvey, Liu & Zhu, '...and the Cross-Section of "
                      "Expected Returns', Review of Financial Studies "
                      "29(1), 2016"),
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": ("https://people.duke.edu/~charvey/Research/Published_Papers/"
                "P118_and_the_cross.PDF"),
        "note": ("'We argue that a newly discovered factor today should "
                 "have a t-statistic that exceeds 3.0.' The paper also "
                 "argues 3.0 is itself too low, and its recommended "
                 "cutoffs increase through time as more factors are data "
                 "mined, so the hurdle RISES with the number of "
                 "candidates tried."),
    },
}

#: Analyst-chosen thresholds. Every one is an ANALYST CHOICE.
ANALYST_CHOICES: Dict[str, Any] = {
    # The line Bailey et al. themselves call "a customary approach" for
    # REJECTING an overfit model (CITED in the paper, Section 3.1).
    "max_pbo": 0.05,
    # The family-level alpha used when none is supplied (ANALYST CHOICE:
    # the Bonferroni and BH methods are published for any alpha; 0.05 is
    # this package's default family level).
    "default_family_alpha": 0.05,
}


# --------------------------------------------------------------------------
# Small helpers (no SciPy)
# --------------------------------------------------------------------------
def _sharpe(returns: Sequence[float]) -> float:
    """Sharpe ratio of PER-OBSERVATION returns, sample stdev (ddof = 1).

    Convention, stated because the package has already been bitten by a
    unit mismatch elsewhere: the inputs are per-observation returns (not
    per-period aggregates, not annualised), the standard deviation uses
    the n - 1 denominator, and no annualisation factor is applied. Only
    the RANK of this number is used by the CSCV procedure, and every
    candidate in a combination is scored on the same rows with the same
    formula, so the convention cannot reorder anything.

    Degenerate input: a zero-variance series has no finite Sharpe. The
    limit is used rather than a made-up number - a constant positive
    series is +inf (it is the best possible risk-adjusted outcome), a
    constant negative series is -inf, and an all-zero series is 0.0 (the
    sign of the numerator is genuinely undefined). These are ranking
    inputs only; they are never published as Sharpe values.
    """
    n = len(returns)
    if n == 0:
        return 0.0
    mean = sum(returns) / n
    if n < 2:
        return 0.0
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    sd = math.sqrt(var)
    if sd > 0.0:
        return mean / sd
    if mean > 0.0:
        return math.inf
    if mean < 0.0:
        return -math.inf
    return 0.0


def _median(values: Sequence[float]) -> float:
    """Median of a non-empty sequence (stdlib statistics)."""
    return float(statistics.median(list(values)))


def _fraction_to(p: float, q: float) -> int:
    """Largest k with p_(k) <= (k/m) * q, by the Benjamini-Hochberg rule.

    The comparison is done in EXACT rational arithmetic on the binary
    values of the inputs. That matters: the procedure's own worked
    examples contain exact ties (for example p_(6) = 0.06 against a
    critical value of (6/10) * 0.10 = 0.06), and binary floating point
    decides such a tie by a rounding artefact rather than by the rule.
    The paper's rule is 'the largest i for which P_(i) <= (i/m) q*', so a
    tie is INCLUDED.
    """
    from fractions import Fraction

    m = len(p)
    best = 0
    for i, pv in enumerate(p, start=1):
        critical = Fraction(i, m) * Fraction(q)
        if Fraction(pv) <= critical:
            best = i
    return best


# --------------------------------------------------------------------------
# PBO
# --------------------------------------------------------------------------
def probability_of_backtest_overfitting(
        candidate_returns: Sequence[Sequence[float]],
        n_splits: Optional[int] = None,
        n_partitions: int = 8,
        test_fraction: float = 0.5) -> Dict[str, Any]:
    """Probability of Backtest Overfitting via CSCV.

    Implements Bailey, Borwein, Lopez de Prado & Zhu, 'The Probability of
    Backtest Overfitting', Algorithm 2.3 (Section 2.2) and the PBO
    estimator of Section 3.1, exactly:

    1. Build the matrix M of order (T x N): column n is the per-
       observation return series of candidate n, and the rows are
       synchronous across candidates.
    2. Partition the rows into an EVEN number S of disjoint blocks of
       equal dimensions (S = n_partitions).
    3. Form ALL combinations of S/2 blocks. There are C(S, S/2) of them
       (70 when S = 8). Each combination is the in-sample set; its
       complement is the out-of-sample set. Because the complement of a
       combination is itself another combination, every partition is
       evaluated twice with the roles swapped - the paper notes this
       explicitly ("each training subset combination is re-used as
       testing subset and vice-versa").
    4. For each combination: pick n* = the candidate with the highest
       in-sample Sharpe; compute the out-of-sample Sharpe of every
       candidate; take the RELATIVE RANK of n* among them, where rank 1
       is the WORST out-of-sample performer; omega = rank / (N + 1).
    5. lambda_c = ln(omega / (1 - omega)). f(lambda) is the relative
       frequency of each lambda across the combinations.
    6. PBO = the integral of f(lambda) over (-infinity, 0], i.e. the
       share of combinations in which the in-sample winner finished at
       or below the out-of-sample median.

    Args:
        candidate_returns: a list of per-candidate return SERIES. Each
            series is a list of per-observation returns (floats). All
            series must have the same length T, otherwise a ValueError
            is raised stating the lengths - the matrix must be true, as
            the paper requires ("the same number of rows for each column,
            where observations are synchronous for every row").
        n_splits: alias for n_partitions (the number of equal row
            blocks S). When supplied it takes precedence over
            n_partitions.
        n_partitions: the even number S of disjoint blocks. Default 8.
        test_fraction: the published CSCV is combinatorially SYMMETRIC -
            S/2 blocks in sample and S/2 out of sample - so 0.5 is the
            only supported value. Any other value is refused with an
            explanation rather than silently approximated.

    Returns:
        A dict. On success: status "ok" with keys pbo, n_combinations,
        n_candidates, n_periods, omega_bar (the median omega),
        lambda_median (the median logit), interpretation, citation, plus
        supporting detail. On insufficient or invalid input: a dict with
        a "status" of "insufficient" or "error" and a "reason". Nothing
        is ever approximated into existence.
    """
    crit = CITED_CRITERIA["probability_of_backtest_overfitting"]
    citation = ("Bailey, Borwein, Lopez de Prado & Zhu, 'The Probability of "
                "Backtest Overfitting', Journal of Computational Finance "
                "19(4), 2016; http://www.davidhbailey.com/dhbpapers/"
                "backtest-prob.pdf")

    # ---- the S used to partition the rows -----------------------------
    # n_splits is an accepted ALIAS for n_partitions (the number of
    # equal row blocks S). When it is supplied it WINS, because it is the
    # value the caller actually chose; n_partitions keeps its default of
    # 8. Reporting an error when the two disagree would make
    # n_splits=16 unusable unless the caller also restated 16.
    if n_splits is not None:
        partitions = int(n_splits)
    else:
        partitions = int(n_partitions)
    if partitions < 2:
        return {"status": "error",
                "reason": (f"n_partitions must be at least 2 (the paper "
                           f"uses S = 16 in practice, 8 here); got "
                           f"{partitions}.")}
    if partitions % 2 != 0:
        return {"status": "error",
                "reason": (f"n_partitions must be EVEN: CSCV takes all "
                           f"C(S, S/2) combinations of S/2 blocks, so an "
                           f"odd S has no half. Got S = {partitions}.")}
    if abs(float(test_fraction) - 0.5) > 1e-12:
        return {"status": "error",
                "reason": (f"test_fraction = {test_fraction} is not "
                           f"supported. The published CSCV is "
                           f"combinatorially SYMMETRIC (S/2 blocks in "
                           f"sample, S/2 out of sample), so the only "
                           f"correct value is 0.5.")}
    half = partitions // 2

    # ---- the candidate set -------------------------------------------
    if candidate_returns is None:
        return {"status": "insufficient",
                "reason": "no candidate return series were supplied."}
    series = [list(s) for s in candidate_returns]
    n_candidates = len(series)
    if n_candidates < 2:
        return {"status": "insufficient",
                "reason": (f"PBO needs at least 2 candidates to have an "
                           f"out-of-sample RANK for the in-sample winner; "
                           f"got {n_candidates}. A single candidate has no "
                           f"ranking, so PBO is undefined for it and is "
                           f"NOT approximated (this is the computational "
                           f"reason the SEC's extracted-performance rule "
                           f"206(4)-1(d)(5) matters).")}

    lengths = {len(s) for s in series}
    if len(lengths) > 1:
        detail = ", ".join(f"candidate {i}: {len(s)}"
                           for i, s in enumerate(series))
        raise ValueError(
            "candidate return series must all have the same length T (the "
            "matrix must be true, with synchronous rows across candidates); "
            f"got {detail}.")

    n_periods = len(series[0])
    if n_periods < 4:
        return {"status": "insufficient",
                "reason": (f"T = {n_periods} observations is too few: each "
                           f"combination scores an in-sample and an "
                           f"out-of-sample Sharpe, and each needs at least "
                           f"2 observations. Need T >= 4.")}
    if n_periods % partitions != 0:
        usable = [s for s in range(partitions, 1, -1)
                  if s % 2 == 0 and n_periods % s == 0]
        hint = (f" Use n_partitions={usable[0]} instead."
                if usable else
                f" Use an observation count divisible by {partitions}.")
        return {"status": "error",
                "reason": (f"T = {n_periods} observations cannot be split "
                           f"into {partitions} blocks of EQUAL dimensions, "
                           f"which the paper requires." + hint)}
    for i, s in enumerate(series):
        for r in s:
            if not math.isfinite(float(r)):
                return {"status": "error",
                        "reason": (f"candidate {i} contains a non-finite "
                                   f"return ({r}); Sharpe cannot be "
                                   f"computed from it.")}

    # ---- CSCV ---------------------------------------------------------
    # Blocks are contiguous row ranges of equal length.
    block_len = n_periods // partitions
    blocks: List[List[int]] = []
    for b in range(partitions):
        start = b * block_len
        blocks.append(list(range(start, start + block_len)))

    def _combinations(k: int, n: int) -> List[Tuple[int, ...]]:
        """All k-SUBSETS of range(n), in lexicographic order.

        A SUBSET has DISTINCT elements, each greater than the last.
        The previous version of this function returned tuples with
        REPEATED elements - for k=4, n=8 it produced (0,0,0,0),
        (0,0,0,1), (0,0,1,0) and so on, and NOT ONE of its 70 tuples was
        a valid 4-subset. That silently broke the procedure: the CSCV
        in-sample set is S/2 BLOCKS of the matrix, so a tuple like
        (0,0,0,0) makes the in-sample row set one block repeated four
        times instead of half the matrix, and the resulting PBO was
        not the published statistic at all.

        The remainder is restricted to elements AFTER `first`, and
        offset accordingly, which is what makes the elements distinct
        and increasing.
        """
        if k == 0:
            return [()]
        out: List[Tuple[int, ...]] = []
        for first in range(n - k + 1):
            for rest in _combinations(k - 1, n - first - 1):
                out.append((first,) + tuple(x + first + 1 for x in rest))
        return out

    combos = _combinations(half, partitions)
    all_rows = set(range(n_periods))

    omegas: List[float] = []
    lambdas: List[float] = []
    n_star_counts: Dict[int, int] = {}

    for combo in combos:
        is_rows: List[int] = []
        for b in combo:
            is_rows.extend(blocks[b])
        oos_rows = sorted(all_rows - set(is_rows))

        # (c)/(d) - performance statistics of the N candidates on each
        # side. Every candidate is scored on the SAME rows.
        is_sharpe = [_sharpe([s[r] for r in is_rows]) for s in series]
        oos_sharpe = [_sharpe([s[r] for r in oos_rows]) for s in series]

        # (e) - the in-sample winner. Ties are broken by candidate index
        # so the procedure is deterministic and reproducible.
        n_star = max(range(n_candidates),
                     key=lambda i: (is_sharpe[i], -i))
        n_star_counts[n_star] = n_star_counts.get(n_star, 0) + 1

        # (f) - the RELATIVE RANK of n* out of sample, where rank 1 is
        # the WORST performer. Ties are broken by candidate index.
        order = sorted(range(n_candidates),
                       key=lambda i: (oos_sharpe[i], i))
        rank = order.index(n_star) + 1

        omega = rank / (n_candidates + 1)
        lam = math.log(omega / (1.0 - omega))
        omegas.append(omega)
        lambdas.append(lam)

    # ---- the estimator -------------------------------------------------
    # PBO = integral of f(lambda) over (-inf, 0]. f is the relative
    # frequency of each lambda across the combinations, so the integral
    # is the share of combinations with lambda <= 0.
    n_combinations = len(lambdas)
    pbo = sum(1 for lam in lambdas if lam <= 0.0) / n_combinations

    omega_bar = _median(omegas)
    lambda_median = _median(lambdas)
    threshold = float(ANALYST_CHOICES["max_pbo"])

    if pbo <= threshold:
        meaning = ("the in-sample winner stayed at or above the "
                   "out-of-sample median in most splits, so the selection "
                   "is unlikely to be an artefact of the search")
    elif pbo < 0.5:
        meaning = ("the in-sample winner fell to or below the "
                   "out-of-sample median in a substantial share of splits, "
                   "so the selection is partly an artefact of the search")
    else:
        meaning = ("the in-sample winner fell to or below the "
                   "out-of-sample median in MOST splits, which is what "
                   "selection on noise looks like: the backtest winner is "
                   "not better out of sample than the other candidates")
    interpretation = (
        f"PBO = {pbo:.4f} over {n_combinations} CSCV combinations of "
        f"{n_candidates} candidates and {n_periods} observations: "
        f"{meaning}. Bailey et al. call rejecting a model whose PBO "
        f"exceeds {threshold} a customary approach. Read it as: the "
        f"chance that this selection procedure is pure overfitting is "
        f"about {pbo * 100:.1f}%. The median relative out-of-sample rank "
        f"of the in-sample winner was {omega_bar:.3f} "
        f"(1.0 = best of {n_candidates}); a median logit of "
        f"{lambda_median:.4f} means "
        + ("a consistent in-sample/out-of-sample winner"
           if lambda_median > 0 else
           "an in-sample winner that does not hold up out of sample")
        + ". A PBO needs the FULL screened universe: it cannot be run on "
          "one wallet in isolation.")

    return {
        "status": "ok",
        "pbo": float(pbo),
        "n_combinations": int(n_combinations),
        "n_candidates": int(n_candidates),
        "n_periods": int(n_periods),
        "omega_bar": omega_bar,
        "lambda_median": float(lambda_median),
        "interpretation": interpretation,
        "citation": citation,
        "pbo_rejection_threshold": threshold,
        "passes_rejection_threshold": bool(pbo <= threshold),
        "n_partitions": int(partitions),
        "combinations_per_split": int(n_combinations),
        "sharpe_convention": ("per-observation returns, sample stdev "
                              "(ddof = 1), no annualisation; only the "
                              "rank is used"),
        "selected_candidate_counts": n_star_counts,
        "lambda_values": [float(x) for x in lambdas],
        "criteria": crit,
    }


# --------------------------------------------------------------------------
# Multiple-testing corrections
# --------------------------------------------------------------------------
def bonferroni_alpha(n_tests: int, family_alpha: float = 0.05) -> float:
    """The per-test significance level that controls the family-wise error
    rate across `n_tests` tests: alpha_per_test = alpha_family / n_tests.

    A test is significant at the FAMILY level only if its p-value is at
    or below the returned level.

    Citation (NIST/SEMATECH e-Handbook of Statistical Methods, 7.4.7.3
    "Bonferroni's method"; https://www.itl.nist.gov/div898/handbook/prc/
    section4/prc473.htm): "one can construct each interval with confidence
    coefficient (1 - alpha/g), and the Bonferroni inequality insures that
    the overall confidence coefficient is at least 1 - alpha".

    The family alpha defaults to 0.05 (this package's default family
    level - ANALYST CHOICE; the method itself is published for any
    alpha).

    Args:
        n_tests: the number of tests in the family. Must be >= 1.
        family_alpha: the family-wise error rate to control.

    Returns:
        The per-test alpha, as a float.

    Raises:
        ValueError: if n_tests < 1, or family_alpha is not in (0, 1].
    """
    if not isinstance(n_tests, int) or isinstance(n_tests, bool):
        raise ValueError(f"n_tests must be an integer, got {n_tests!r}.")
    if n_tests < 1:
        raise ValueError(
            f"n_tests must be at least 1: there is no family to correct "
            f"for; got {n_tests}.")
    if not (0.0 < float(family_alpha) <= 1.0):
        raise ValueError(
            f"family_alpha must be in (0, 1], got {family_alpha}.")
    return float(family_alpha) / float(n_tests)


def benjamini_hochberg(pvalues: Sequence[float],
                       q: float = 0.05) -> Dict[str, Any]:
    """The Benjamini-Hochberg false-discovery-rate procedure.

    Citation (Benjamini & Hochberg, 'Controlling the false discovery rate:
    a practical and powerful approach to multiple testing', J. R. Statist.
    Soc. B 57(1), 289-300, 1995; https://www.math.tau.ac.il/~yekutiel/
    eBayes/bh_1995.pdf): "let k be the largest i for which
    P_(i) <= (i/m) q*; then reject all H_(i), i = 1, 2, ..., k."

    This controls the expected PROPORTION of falsely rejected hypotheses
    (the false discovery rate) rather than the probability of any false
    rejection (the family-wise error rate), so it is more powerful than
    Bonferroni when most candidates are genuinely skilled. It needs no
    independence assumption for the rejected set to be FDR-controlling
    under the paper's Theorem 1; for CORRELATED candidates under
    arbitrary dependence use the Benjamini-Hochberg-Yekutieli variant
    (Harvey, Liu & Zhu, Table 3).

    The comparison p_(i) <= (i/m) q is made in exact rational arithmetic
    so that an exact tie is decided by the rule (INCLUDED) rather than by
    a binary floating-point rounding artefact.

    Args:
        pvalues: the per-candidate p-values, each in [0, 1].
        q: the target false discovery rate (the paper's q*).

    Returns:
        A dict. On success: status "ok" with n_tests, threshold (the
        rejected count k), rejected (a list of {index, pvalue, rank} for
        each rejected hypothesis, in rank order), alpha and citation. For
        an empty input: status "empty". For invalid input: status
        "error" with a reason.
    """
    crit = CITED_CRITERIA["bh_fdr_procedure"]
    citation = ("Benjamini & Hochberg, 'Controlling the false discovery "
                "rate: a practical and powerful approach to multiple "
                "testing', J. R. Statist. Soc. B 57(1), 289-300 (1995); "
                "https://www.math.tau.ac.il/~yekutiel/eBayes/bh_1995.pdf")

    if pvalues is None:
        return {"status": "error",
                "reason": "no p-values were supplied."}
    if not (0.0 < float(q) <= 1.0):
        return {"status": "error",
                "reason": f"q (the target false discovery rate) must be in "
                          f"(0, 1], got {q}."}

    vals: List[float] = []
    for i, p in enumerate(pvalues):
        try:
            pv = float(p)
        except (TypeError, ValueError):
            return {"status": "error",
                    "reason": f"p-value at index {i} is not a number: {p!r}"}
        if not math.isfinite(pv) or not (0.0 <= pv <= 1.0):
            return {"status": "error",
                    "reason": f"p-value at index {i} must be in [0, 1], got "
                              f"{p}."}
        vals.append(pv)

    m = len(vals)
    if m == 0:
        return {"status": "empty",
                "reason": "no p-values supplied; nothing to test.",
                "n_tests": 0,
                "alpha": float(q),
                "citation": citation}

    # Order ascending; ties keep their original index order so the
    # procedure is deterministic.
    order = sorted(range(m), key=lambda i: (vals[i], i))
    sorted_p = [vals[i] for i in order]

    k = _fraction_to(sorted_p, float(q))

    rejected = []
    for rank, idx in enumerate(order[:k], start=1):
        rejected.append({"index": int(idx),
                         "pvalue": float(vals[idx]),
                         "rank": int(rank)})

    return {
        "status": "ok",
        "n_tests": int(m),
        "threshold": int(k),
        "rejected": rejected,
        "alpha": float(q),
        "citation": citation,
        "n_rejected": int(k),
        "rejected_indices": [r["index"] for r in rejected],
        "critical_value_at_k": (float((k / m) * q) if k else 0.0),
        "note": ("k is the largest i with P_(i) <= (i/m)*q; the first k "
                 "hypotheses in ascending p-value order are rejected. "
                 "Comparison is exact-rational, so an exact tie is "
                 "INCLUDED as the rule requires."),
        "criteria": crit,
    }


def multiple_testing_t_statistic_hurdle(n_tests: int,
                                         alpha: float = 0.05) -> Dict[str, Any]:
    """The Harvey-Liu-Zhu t-statistic hurdle for a newly discovered signal.

    Citation (Harvey, Liu & Zhu, '...and the Cross-Section of Expected
    Returns', Review of Financial Studies 29(1), 2016;
    https://people.duke.edu/~charvey/Research/Published_Papers/
    P118_and_the_cross.PDF): "We argue that a newly discovered factor
    today should have a t-statistic that exceeds 3.0." The paper argues
    that 3.0 is itself too low, and its recommended cutoffs increase
    through time as more factors are data mined - i.e. the hurdle RISES
    with the number of candidates screened.

    The 3.0 returned here is an APPROXIMATION, and this function says so:
    it is the paper's headline figure for a screen in the low hundreds of
    candidates, it does not depend on n_tests, and the paper's own
    reasoning implies the effective bar for a screen of n_tests
    candidates is HIGHER than 3.0, not lower. The value is therefore a
    FLOOR, never a discount.

    Args:
        n_tests: the number of candidates screened before the one being
            judged was selected.
        alpha: the family-level alpha the screen is run at. Reported
            for traceability; the paper's 3.0 is stated at its own
            baseline (5% family level).

    Returns:
        A dict with status "ok", n_tests, hurdle (a float, never below
        3.0), family_alpha, note and citation.
    """
    crit = CITED_CRITERIA["multiple_testing_t_statistic_hurdle"]
    citation = ("Harvey, Liu & Zhu, '...and the Cross-Section of Expected "
                "Returns', Review of Financial Studies 29(1), 2016; "
                "https://people.duke.edu/~charvey/Research/Published_Papers/"
                "P118_and_the_cross.PDF")

    if not isinstance(n_tests, int) or isinstance(n_tests, bool):
        raise ValueError(f"n_tests must be an integer, got {n_tests!r}.")
    if n_tests < 1:
        raise ValueError(
            f"n_tests must be at least 1: there is no screen to adjust "
            f"for; got {n_tests}.")
    if not (0.0 < float(alpha) <= 1.0):
        raise ValueError(f"alpha must be in (0, 1], got {alpha}.")

    # 3.0 is the paper's published headline hurdle. It is not computed
    # from n_tests and is not presented as if it were.
    hurdle = 3.0

    note = (
        f"Hurdle {hurdle:.1f} is the paper's headline requirement for a "
        f"newly discovered signal ('a newly discovered factor today "
        f"should have a t-statistic that exceeds 3.0'), applied here to a "
        f"screen of {n_tests} candidate(s) at family alpha "
        f"{float(alpha)}. APPROXIMATION, and it is a FLOOR: the paper "
        f"argues 3.0 is already too low and that its recommended cutoffs "
        f"increase through time as more factors are data mined, so the "
        f"hurdle RISES with the number of candidates screened - with "
        f"{n_tests} candidate(s) the effective bar is at least "
        f"{hurdle:.1f} and arguably higher. This value is not derived "
        f"from n_tests and must not be read as falling as the screen "
        f"grows. Harvey-Liu also note the multiple-testing haircut on a "
        f"Sharpe ratio is NONLINEAR: high Sharpes are mildly penalised, "
        f"marginal Sharpes heavily.")

    return {
        "status": "ok",
        "n_tests": int(n_tests),
        "hurdle": float(hurdle),
        "family_alpha": float(alpha),
        "note": note,
        "citation": citation,
        "is_floor": True,
        "criteria": crit,
    }


def harvey_liu_zhu_hurdle(n_tests: int, alpha: float = 0.05) -> Dict[str, Any]:
    """Alias of `multiple_testing_t_statistic_hurdle` (same citation, same
    value, same floor semantics)."""
    return multiple_testing_t_statistic_hurdle(n_tests, alpha)
