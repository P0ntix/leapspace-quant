"""Offline checks for the PBO module (`leapspace/pbo.py`).

Run:  python leapspace/tests/test_pbo.py      (offline, deterministic)

Every fixture here is SYNTHETIC and built from a fixed seed, so the
checks are reproducible: the same seeds give the same numbers on every
run and on every machine. No network access is required or attempted.

THE MOST IMPORTANT CHECK: THE CSCV COMBINATION GENERATOR
--------------------------------------------------------
The published procedure needs the k-SUBSETS of the S row blocks. A
first implementation of this module returned tuples with REPEATED
elements - for k=4, n=8 it produced (0,0,0,0), (0,0,0,1) and so on,
and NOT ONE of its 70 tuples was a valid 4-subset. That silently broke
the procedure: the in-sample set became one block repeated four times
instead of half the matrix, so the resulting PBO was not the published
statistic at all. The module is therefore pinned to an INDEPENDENT
reference implementation of the paper's Algorithm 2.3 below.

WHAT IS BEING CHECKED, AND WHY IT IS BUILT THIS WAY
-----------------------------------------------------
The two headline PBO checks are the interesting ones, because a PBO
implementation can look plausible and still be wrong. Both are built so
that the EXPECTED ANSWER IS KNOWN IN ADVANCE from how the data was
constructed, rather than from whatever the code happens to output:

(a) A matrix in which ONE candidate genuinely dominates - it has the
    highest Sharpe in BOTH halves of the sample, so it is genuinely the
    best strategy rather than the luckiest. The in-sample winner should
    therefore also be a good out-of-sample performer and the PBO should
    be LOW. The test asserts the PREMISE as well as the conclusion: it
    checks that the dominant candidate really does have the top Sharpe
    in both halves before trusting the PBO it produces.

(b) A universe built from PURE NOISE, from which only the best-of-many
    candidates were kept. Every candidate in the retained universe is a
    noise series; the only reason any of them was kept is that it had
    the highest Sharpe in the FULL sample. The best of many noise series
    is mostly noise, so the in-sample winner should land below the
    median out of sample and the PBO should be HIGH. The test checks the
    mechanism directly as well: the winner's out-of-sample Sharpe must
    be much weaker than its in-sample Sharpe.

Note the contrast with the "plain iid noise" check that is also here:
with N exchangeable noise candidates and NO selection step, the
in-sample winner's out-of-sample rank is uniform, so PBO ~ 0.5. The
whole point of PBO is that a selection step (keep the best of many)
moves that from 0.5 towards 1.0, and both facts are checked.
"""
from __future__ import annotations

import itertools
import math
import random
import statistics
import sys

sys.path.insert(0, r"C:\Users\HP\AppData\Local\hermes\projects"
                   r"\leapspace-quant")

from leapspace.pbo import (CITED_CRITERIA,  # noqa: E402
                           benjamini_hochberg,
                           bonferroni_alpha,
                           harvey_liu_zhu_hurdle,
                           multiple_testing_t_statistic_hurdle,
                           probability_of_backtest_overfitting)

FAILS = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}"
          + (f"  {detail}" if detail else ""))
    if not cond:
        FAILS.append(name)


def _sharpe(xs):
    """Sample (ddof=1) Sharpe of per-observation returns.

    The same convention leapspace.pbo uses, restated here so the test
    can check the PREMISE of fixture (a) independently of the module.
    """
    n = len(xs)
    if n < 2:
        return 0.0
    mean = sum(xs) / n
    var = sum((r - mean) ** 2 for r in xs) / (n - 1)
    sd = math.sqrt(var)
    if sd > 0:
        return mean / sd
    return math.inf if mean > 0 else (-math.inf if mean < 0 else 0.0)


def reference_pbo(series, S=8):
    """An independent implementation of the published CSCV procedure.

    Written straight from Bailey, Borwein, Lopez de Prado & Zhu,
    'The Probability of Backtest Overfitting', Algorithm 2.3: partition
    the rows into S equal blocks, take all C(S, S/2) combinations as the
    in-sample set with the complement out of sample, keep the in-sample
    Sharpe winner, and record its RELATIVE out-of-sample rank (rank 1 =
    worst) as omega = rank / (N + 1). PBO is the share of combinations
    whose logit ln(omega / (1 - omega)) is <= 0.
    """
    T = len(series[0])
    N = len(series)
    size = T // S
    blocks = [list(range(i * size, (i + 1) * size)) for i in range(S)]
    all_rows = set(range(T))
    omegas = []
    for combo in itertools.combinations(range(S), S // 2):
        is_rows = [r for b in combo for r in blocks[b]]
        oos_rows = sorted(all_rows - set(is_rows))
        is_sh = [_sharpe([s[r] for r in is_rows]) for s in series]
        oos_sh = [_sharpe([s[r] for r in oos_rows]) for s in series]
        n_star = max(range(N), key=lambda i: (is_sh[i], -i))
        order = sorted(range(N), key=lambda i: (oos_sh[i], i))
        rank = order.index(n_star) + 1
        omegas.append(rank / (N + 1))
    return (sum(1 for w in omegas if w <= 0.5) / len(omegas),
            statistics.median(omegas))


# --------------------------------------------------------------------------
# Synthetic fixtures (deterministic seeds throughout)
# --------------------------------------------------------------------------
T_PERIODS = 200
N_CANDIDATES = 8
N_PARTITIONS = 8          # -> C(8, 4) = 70 CSCV combinations
SEED_DOMINANT = 1
SEED_NOISE = 1


def dominant_matrix(seed=SEED_DOMINANT, n=N_CANDIDATES, t=T_PERIODS):
    """One candidate genuinely dominates; the rest are zero-drift noise.

    The dominant candidate has a positive drift and the SAME volatility
    as the others, so it has the highest Sharpe in every window, not
    just on average. That is what makes the expected PBO LOW.
    """
    rng = random.Random(seed)
    matrix = []
    for i in range(n):
        mu = 0.004 if i == 0 else 0.0
        matrix.append([rng.gauss(mu, 0.005) for _ in range(t)])
    return matrix


def noise_universe(seed=SEED_NOISE, pool_size=400, keep=N_CANDIDATES,
                   t=T_PERIODS):
    """Best-of-many PURE NOISE: draw a big pool of noise series and keep
    only the ones with the highest full-sample Sharpe.

    Nothing in the retained universe has skill. The only reason any of
    them was kept is that it was the best of many - which is precisely
    the situation PBO exists to detect, and the reason the expected PBO
    is HIGH.
    """
    rng = random.Random(seed)
    pool = [[rng.gauss(0.0, 0.01) for _ in range(t)]
            for _ in range(pool_size)]
    pool.sort(key=lambda s: -_sharpe(s))
    return pool[:keep]


def main() -> int:
    print("=" * 72)
    print("PBO AND MULTIPLE-TESTING CHECKS (offline, synthetic, seeded)")
    print("=" * 72)

    print()
    print("1. THE CSCV COMBINATION GENERATOR")
    # The published procedure needs the k-SUBSETS of the S blocks.
    # A first implementation produced tuples with repeated elements,
    # which silently broke the row split.
    rng = random.Random(3)
    series = [[rng.gauss(0.0, 0.01) for _ in range(64)] for _ in range(12)]
    res = probability_of_backtest_overfitting(series, n_partitions=8)
    check("the module forms exactly C(S, S/2) combinations",
          res.get("n_combinations") == math.comb(8, 4) == 70,
          f"n_combinations = {res.get('n_combinations')}, "
          f"C(8,4) = {math.comb(8, 4)}")
    res16 = probability_of_backtest_overfitting(
        [[rng.gauss(0.0, 0.01) for _ in range(128)] for _ in range(4)],
        n_partitions=16)
    check("and C(16, 8) = 12870 at the paper's preferred S = 16",
          res16.get("n_combinations") == math.comb(16, 8) == 12870,
          f"n_combinations = {res16.get('n_combinations')}")

    print()
    print("2. THE MODULE MATCHES AN INDEPENDENT REFERENCE")
    for label, seed in (("noise", 5), ("noise2", 17), ("noise3", 91)):
        rg = random.Random(seed)
        series = [[rg.gauss(0.0, 0.01) for _ in range(32)]
                  for _ in range(12)]
        ref, ref_omega = reference_pbo(series)
        mod = probability_of_backtest_overfitting(series)
        got = mod.get("pbo")
        check(f"module == reference ({label})",
              got is not None and abs(got - ref) < 1e-9,
              f"module={got} reference={ref}")
        check(f"module median omega == reference ({label})",
              abs(mod.get("omega_bar", -1) - ref_omega) < 1e-9,
              f"module={mod.get('omega_bar')} reference={ref_omega}")

    print()
    print("3. (a) PBO LOW WHEN ONE CANDIDATE GENUINELY DOMINATES")
    m = dominant_matrix()
    half = len(m[0]) // 2
    first = [_sharpe(s[:half]) for s in m]
    second = [_sharpe(s[half:]) for s in m]
    # The PREMISE, checked first: the dominant candidate must really have
    # the top Sharpe in BOTH halves, or the expected PBO is not knowable.
    check("premise: dominant candidate has the top Sharpe in the first half",
          first[0] == max(first),
          f"first-half Sharpes: {[round(x, 3) for x in first]}")
    check("premise: dominant candidate has the top Sharpe in the second half",
          second[0] == max(second),
          f"second-half Sharpes: {[round(x, 3) for x in second]}")
    r_dom = probability_of_backtest_overfitting(m, n_partitions=N_PARTITIONS)
    # NOTE: `r_dom.get("pbo") or 1` would be WRONG here - a PBO of
    # exactly 0.0 is FALSY, so `or` would turn a perfect score into 1
    # and the check would fail. Compare the value, not its truthiness.
    pbo_dom = r_dom.get("pbo")
    check("PBO is low when one candidate genuinely dominates",
          pbo_dom is not None and pbo_dom < 0.5, f"pbo={pbo_dom}")
    check("PBO is well under the paper's 0.05 rejection line",
          pbo_dom is not None and pbo_dom < 0.05, f"pbo={pbo_dom}")
    check("the median relative OOS rank of the winner is high (> 0.5)",
          r_dom.get("omega_bar", -1) > 0.5,
          f"omega_bar={r_dom.get('omega_bar')}")
    check("the median logit is positive (the winner holds up OOS)",
          r_dom.get("lambda_median", -1) > 0,
          f"lambda_median={r_dom.get('lambda_median')}")
    check("the dominant candidate is the in-sample winner in most splits",
          r_dom.get("selected_candidate_counts", {}).get(0, 0)
          >= 0.5 * r_dom.get("n_combinations", 1),
          f"selected counts: {r_dom.get('selected_candidate_counts')}")
    check("the citation carries the Bailey/Borwein/Lopez de Prado/Zhu URL",
          "backtest-prob.pdf" in r_dom.get("citation", ""),
          r_dom.get("citation", "")[:80])
    check("the interpretation states what the PBO means",
          "PBO" in r_dom.get("interpretation", "")
          and len(r_dom.get("interpretation", "")) > 80,
          r_dom.get("interpretation", "")[:80])

    print()
    print("4. (b) PBO HIGH WHEN THE WINNER WAS BEST OF MANY PURE NOISE")
    uni = noise_universe()
    r_noise = probability_of_backtest_overfitting(uni,
                                                   n_partitions=N_PARTITIONS)
    check("PBO is high (> 0.5) for a best-of-many noise universe",
          r_noise.get("pbo", -1) > 0.5, f"pbo={r_noise.get('pbo')}")
    check("the median relative OOS rank of the winner is poor (<= 0.5)",
          r_noise.get("omega_bar", 1) <= 0.5,
          f"omega_bar={r_noise.get('omega_bar')}")
    check("the median logit is negative (the winner does NOT hold up OOS)",
          r_noise.get("lambda_median", 1) <= 0,
          f"lambda_median={r_noise.get('lambda_median')}")
    # The MECHANISM, checked directly: a best-of-many noise pick has a
    # much weaker out-of-sample Sharpe than in-sample Sharpe.
    half = len(uni[0]) // 2
    is_sh = [_sharpe(s[:half]) for s in uni]
    oos_sh = [_sharpe(s[half:]) for s in uni]
    best = max(range(len(uni)), key=lambda i: is_sh[i])
    check("the in-sample best of the noise universe has a weaker OOS "
          "Sharpe than IS Sharpe",
          oos_sh[best] < is_sh[best],
          f"IS {is_sh[best]:.3f} -> OOS {oos_sh[best]:.3f}")
    # It is not luck of one seed: the same construction must give a high
    # PBO across independent seeds.
    pbos = []
    for seed in range(1, 9):
        r_s = probability_of_backtest_overfitting(
            noise_universe(seed=seed), n_partitions=N_PARTITIONS)
        pbos.append(r_s.get("pbo", -1))
    check("PBO stays high across 8 independent noise seeds (all > 0.5)",
          all(p > 0.5 for p in pbos),
          f"PBOs: {[round(p, 4) for p in pbos]}")
    check("the median PBO across noise seeds is high (> 0.6)",
          statistics.median(pbos) > 0.6,
          f"median={statistics.median(pbos):.4f}")

    print()
    print("5. THE NULL: PLAIN IID NOISE, NO SELECTION STEP")
    # With N exchangeable noise candidates and no selection, the
    # in-sample winner's out-of-sample rank is uniform, so PBO ~ 0.5.
    # The selection step in check 4 is what moves it towards 1.0.
    vals = []
    for seed in range(12):
        rg = random.Random(seed)
        s = [[rg.gauss(0.0, 0.01) for _ in range(64)] for _ in range(8)]
        rr = probability_of_backtest_overfitting(s, n_partitions=8)
        if rr.get("status") == "ok":
            vals.append(rr["pbo"])
    mean = sum(vals) / len(vals)
    check("mean PBO on plain iid noise is ~0.5 (no selection, no edge)",
          0.3 <= mean <= 0.7, f"mean={mean:.4f} over {len(vals)} seeds")
    check("PBO in [0,1] on plain noise",
          all(0.0 <= v <= 1.0 for v in vals), f"{len(vals)} values")

    print()
    print("6. (e) PBO IS ALWAYS IN [0, 1]")
    ok = True
    seen = set()
    for seed in range(1, 7):
        for n in (2, 3, 8, 16):
            rg = random.Random(seed * 100 + n)
            s = [[rg.gauss(0.0, 0.01) for _ in range(64)] for _ in range(n)]
            rr = probability_of_backtest_overfitting(s, n_partitions=8)
            p = rr.get("pbo")
            seen.add(p)
            if not (isinstance(p, float) and math.isfinite(p)
                    and 0.0 <= p <= 1.0):
                ok = False
    check("every PBO over 24 random matrices is a float in [0, 1]", ok,
          f"distinct values: {sorted(seen)}")
    ramp = [[0.10] * 64, [-0.10] * 64]
    r_ramp = probability_of_backtest_overfitting(ramp, n_partitions=8)
    check("a maximally separated pair still gives a PBO in [0, 1]",
          isinstance(r_ramp.get("pbo"), float)
          and 0.0 <= r_ramp["pbo"] <= 1.0, f"pbo={r_ramp.get('pbo')}")

    print()
    print("7. (c) AND (d) DEGENERATE INPUTS")
    r = probability_of_backtest_overfitting([[0.1, 0.2, 0.3]])
    check("(c) one candidate -> status 'insufficient', not a number",
          r.get("status") == "insufficient" and r.get("pbo") is None,
          f"status={r.get('status')}")
    check("(c) the reason says PBO is undefined for a single candidate",
          "undefined" in r.get("reason", "").lower(),
          r.get("reason", "")[:100])
    r_empty = probability_of_backtest_overfitting([])
    check("(c) an empty candidate list also returns an honest status",
          r_empty.get("status") == "insufficient"
          and r_empty.get("pbo") is None,
          f"status={r_empty.get('status')}")
    try:
        probability_of_backtest_overfitting([[0.1, 0.2], [0.1]])
        check("(d) mismatched lengths raise", False, "no exception")
    except ValueError as exc:
        check("(d) mismatched lengths raise ValueError", True,
              str(exc)[:90])
    # Matching lengths are accepted. n_partitions=4 is used because the
    # default of 8 needs at least 8 observations to split into equal
    # blocks; T = 8 with S = 4 gives blocks of 2 rows.
    ok_res = probability_of_backtest_overfitting(
        [[0.1, 0.2, 0.3, 0.0, 0.1, 0.2, 0.0, 0.1],
         [0.0, 0.1, 0.0, 0.2, 0.1, 0.0, 0.1, 0.0]],
        n_partitions=4)
    check("(d) matching lengths are accepted",
          ok_res.get("status") == "ok",
          f"status={ok_res.get('status')} reason={ok_res.get('reason')}")

    print()
    print("8. (f) BONFERRONI")
    check("bonferroni_alpha(10, 0.05) == 0.005",
          abs(bonferroni_alpha(10, 0.05) - 0.005) < 1e-12,
          bonferroni_alpha(10, 0.05))
    check("bonferroni_alpha(1, 0.05) == 0.05",
          abs(bonferroni_alpha(1, 0.05) - 0.05) < 1e-12,
          bonferroni_alpha(1, 0.05))
    check("bonferroni_alpha(100, 0.05) == 0.0005",
          abs(bonferroni_alpha(100, 0.05) - 0.0005) < 1e-12,
          bonferroni_alpha(100, 0.05))
    check("the per-test alpha falls as n_tests rises (strict control)",
          bonferroni_alpha(1000, 0.05) < bonferroni_alpha(10, 0.05),
          f"{bonferroni_alpha(1000, 0.05)} vs {bonferroni_alpha(10, 0.05)}")
    try:
        bonferroni_alpha(0, 0.05)
        check("n_tests < 1 is rejected", False, "no error raised")
    except ValueError:
        check("n_tests < 1 is rejected", True)
    check("the NIST Bonferroni citation is carried in the criteria",
          "prc473.htm" in CITED_CRITERIA["bonferroni_alpha_per_test"]["url"],
          CITED_CRITERIA["bonferroni_alpha_per_test"]["url"])

    print()
    print("9. (g) BENJAMINI-HOCHBERG")
    # PRIMARY REFERENCE: the paper's OWN worked example, section 3.2 -
    # the rt-PA/APSAC myocardial-infarction trial, 15 ordered p-values
    # at q* = 0.05. The paper's own text says: "The first p-value to
    # satisfy the constraint is P_(4) ... Thus we reject the FOUR
    # hypotheses having p-values which are less than or equal to 0.013."
    paper = [0.0001, 0.0004, 0.0019, 0.0095, 0.0201, 0.0278, 0.0298,
             0.0344, 0.0459, 0.3240, 0.4262, 0.5719, 0.6528, 0.7590,
             1.000]
    gp = benjamini_hochberg(paper, q=0.05)
    check("(g) BH on the paper's own example rejects the first FOUR",
          gp.get("threshold") == 4 and gp.get("rejected_indices")
          == [0, 1, 2, 3],
          f"threshold={gp.get('threshold')} "
          f"rejected={gp.get('rejected_indices')}")
    check("(g) the rejected entries carry index, p-value and rank",
          all(set(e) == {"index", "pvalue", "rank"} for e in gp["rejected"])
          and [e["rank"] for e in gp["rejected"]] == [1, 2, 3, 4],
          gp["rejected"])
    check("(g) the BH citation carries the paper URL",
          "bh_1995.pdf" in gp.get("citation", ""), gp.get("citation", "")[:80])

    # The 10-value list named in the task brief. Two claims in the brief
    # do not survive checking against the paper, so the expected value
    # below is set from the RULE, not from the brief:
    #   * it is NOT the paper's own example - the paper's example is the
    #     15-value rt-PA list checked just above;
    #   * the paper's procedure (1) is 'the largest i for which
    #     P_(i) <= (i/m) q*'. At m = 10 and q = 0.10 the critical value
    #     at rank 6 is exactly 0.060, which EQUALS P_(6) = 0.060, so
    #     rank 6 SATISFIES the rule and the step-up procedure rejects
    #     SIX. A strict '<' variant of the rule would reject five, but
    #     that is not the rule the paper prints, and the same value is
    #     what R's p.adjust(method = "BH") produces.
    brief = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205,
             0.212, 0.216]
    gb = benjamini_hochberg(brief, q=0.10)
    check("(g) the brief's 10-value list at q=0.10 rejects SIX (rank 6 ties "
          "its critical value exactly and the rule includes ties)",
          gb.get("threshold") == 6 and gb.get("rejected_indices")
          == [0, 1, 2, 3, 4, 5],
          f"threshold={gb.get('threshold')} "
          f"rejected={gb.get('rejected_indices')}")
    check("(g) ranks 3 and 4 are rejected even though they fail their own "
          "critical values (the step-up property)",
          gb.get("threshold") == 6, f"threshold={gb.get('threshold')}")
    check("(g) the rejected set is the FIRST k in ascending p-value order",
          [e["pvalue"] for e in gb["rejected"]] == sorted(brief)[:6],
          gb["rejected"])

    check("(g) BH on an empty list -> honest status",
          benjamini_hochberg([], q=0.1).get("status") == "empty")
    bad = benjamini_hochberg([0.5, 1.5], q=0.05)
    check("(g) an out-of-range p-value -> status 'error' with a reason",
          bad.get("status") == "error" and "reason" in bad, bad)
    check("(g) q outside (0, 1] is rejected",
          benjamini_hochberg([0.01], q=0).get("status") == "error")

    print()
    print("10. (h) THE T-STATISTIC HURDLE")
    th = multiple_testing_t_statistic_hurdle(100)
    check("(h) the hurdle is at least 3.0",
          (th.get("hurdle") or 0) >= 3.0, f"hurdle={th.get('hurdle')}")
    check("(h) the hurdle is a float",
          isinstance(th.get("hurdle"), float), repr(th.get("hurdle")))
    check("(h) n_tests and family_alpha are reported",
          th.get("n_tests") == 100 and th.get("family_alpha") == 0.05,
          f"{th.get('n_tests')}, {th.get('family_alpha')}")
    check("(h) the note states it is an approximation",
          "approximation" in th.get("note", "").lower(),
          th.get("note", "")[:100])
    check("(h) the note states the hurdle RISES with the number of "
          "candidates",
          "rises" in th.get("note", "").lower(), th.get("note", "")[:100])
    check("(h) the note says 3.0 is a floor, not a discount",
          "floor" in th.get("note", "").lower(), th.get("note", "")[:100])
    check("(h) the citation carries the HLZ paper",
          "charvey" in th.get("citation", "").lower(),
          th.get("citation", "")[:80])
    all_ok = True
    for n in (1, 10, 100, 1000, 10000):
        r_n = multiple_testing_t_statistic_hurdle(n)
        if not (isinstance(r_n.get("hurdle"), float)
                and r_n["hurdle"] >= 3.0):
            all_ok = False
    check("(h) the hurdle is a float >= 3.0 for n_tests = 1, 10, 100, "
          "1000 and 10000", all_ok)
    alias = harvey_liu_zhu_hurdle(100)
    check("(h) harvey_liu_zhu_hurdle is an alias with the same value",
          alias.get("hurdle") == th.get("hurdle")
          and alias.get("citation") == th.get("citation"),
          f"{alias.get('hurdle')} vs {th.get('hurdle')}")

    print()
    print("11. DETERMINISM AND CITATION HYGIENE")
    uni = noise_universe()
    a = probability_of_backtest_overfitting(uni, n_partitions=N_PARTITIONS)
    b = probability_of_backtest_overfitting(uni, n_partitions=N_PARTITIONS)
    check("the same input gives the same PBO (deterministic)",
          a.get("pbo") == b.get("pbo"), f"{a.get('pbo')} vs {b.get('pbo')}")
    check("the same input gives the same lambdas (deterministic)",
          a.get("lambda_values") == b.get("lambda_values"),
          "lambda lists differ")
    check("every published rule carries a citation URL",
          all(v.get("url") for v in CITED_CRITERIA.values()),
          [k for k, v in CITED_CRITERIA.items() if not v.get("url")])
    check("every criteria entry carries an authority and a tag",
          all(v.get("authority") and v.get("tag")
              for v in CITED_CRITERIA.values()),
          [k for k, v in CITED_CRITERIA.items()
           if not (v.get("authority") and v.get("tag"))])
    alias_res = probability_of_backtest_overfitting(uni,
                                                    n_splits=N_PARTITIONS)
    check("n_splits works as an alias for n_partitions",
          alias_res.get("n_combinations") == a.get("n_combinations"),
          f"{alias_res.get('n_combinations')} vs {a.get('n_combinations')}")
    check("an odd number of partitions is refused with a reason",
          probability_of_backtest_overfitting(uni, n_partitions=7)
          .get("status") == "error", "expected an error status")
    check("a non-symmetric test_fraction is refused with a reason",
          probability_of_backtest_overfitting(uni, test_fraction=0.6)
          .get("status") == "error", "expected an error status")

    print()
    print("=" * 72)
    if FAILS:
        print(f"RESULT: {len(FAILS)} FAILURE(S) out of {CHECKS} checks")
        for name in FAILS:
            print(f"  FAIL  {name}")
        print("=" * 72)
        return 1
    print(f"RESULT: ALL {CHECKS} CHECKS PASS")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
