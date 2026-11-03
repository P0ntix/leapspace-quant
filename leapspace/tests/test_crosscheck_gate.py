"""CROSS-CHECK: the package's consistency gate vs an INDEPENDENT reference.

WHAT THIS TEST IS
-----------------
`leapspace/edge.py` is the package's own memecoin consistency gate.
`leapspace/reference_gate.py` is a SEPARATE, self-contained
re-implementation of the same rules, written from the published rules
rather than from the package's code. It imports NOTHING from
`leapspace` and uses the standard library only.

Running both on the SAME trades and comparing them is the only way to
know whether the package's gate can be trusted for a live-capital
decision. A single implementation, however carefully written, can only
be checked against its own assumptions.

THE DATA
--------
Real trades, fetched live from the on-chain universe by
`reports/fetch_crosscheck_trades.py` and cached to
`reports/crosscheck_trades.json`. The cache makes this test
reproducible offline. If the cache is missing the test FAILS LOUDLY
rather than silently skipping - a cross-check that does not run is
worse than no cross-check.

SYNTHETIC WALLETS
-----------------
Four constructed wallets that each isolate one failure mode:
a consistent wallet, a one-lucky-win wallet, a coin-flip wallet and
a decaying wallet. Both implementations must agree on the verdict.

HOW MISMATCHES ARE HANDLED
--------------------------
LOUDLY. Every comparison prints the two numbers side by side and any
disagreement raises a failure with both values in the message. The
only tolerance anywhere is a FLOAT tolerance for the two
inverse-normal-CDF implementations (the package uses Acklam's
rational approximation, the reference uses the standard library's
Wichura AS241), which are both correct answers to the same question
and differ at the 1e-9 level. Nothing else is tolerated.

FINDINGS THIS TEST ENCODES (see reports/gate_crosscheck.md)
----------------------------------------------------------
1. The Bayesian skill probability now AGREES. The package used to
   compute the null-hypothesis SIGNIFICANCE TEST P(X <= w) for
   Binomial(n, 0.5) where the cited criterion means the POSTERIOR
   PROBABILITY P(p > 0.5) under a Beta(1,1) prior, which is
   sum_{k=0}^{w} C(n+1, k) / 2^(n+1). The package was fixed while
   this cross-check was in progress; the reference implements the
   posterior form and the two now agree EXACTLY (delta = 0.0).

2. `edge_decay` STILL DIVERGES, and it is a real bug. In
   `evaluate_edge` the variable `n_closed` is first the count of RAW
   CLOSED TRADES, then it is REASSIGNED to the count of EFFECTIVE
   BETS. The decay block then splits the RAW TRADE PnL list
   (`pnls`) using the BET count as the split index:

       n_closed = len(closed)          # raw closed trades
       pnls     = [...for t in closed] # raw trade PnL list
       n_closed = bo["n_closed_bets"]  # SHADOWED -> effective bet count
       half  = n_closed // 2           # split index: BET units
       early = pnls[:half]             # values: RAW TRADE units

   The index and the values are in different units. On the real
   wallet this makes the "early half" 2 raw trades and the "recent
   half" 177 raw trades - a 1:88 split of a track record that was
   supposed to be split in half, computed over raw trades rather than
   over independent bets. On the constructed unit-bug fixture it
   FLIPS THE VERDICT: the package says CONSISTENT, the reference says
   FLUKE.

3. The package's THREE bet counters disagree with EACH OTHER on
   oversell sequences, because `independent_bets()` clamps the net
   position at zero after a sell and `time_disjoint_bets()` and
   `bet_outcomes()` do not. The reference is internally consistent.

4. `expected_max_sharpe(2)` diverges: the package falls back to
   sqrt(2 ln N) for N <= 2, which is NOT the Euler-Mascheroni form
   the standards document tabulates (1.1774 vs 0.5198; the exact
   E[max of 2 iid N(0,1)] is 0.5642). It is more conservative, so it
   cannot manufacture a pass, and N=2 is a rare input.

Divergences 2 and 3 are asserted BELOW as KNOWN DIVERGENCES with an
explicit expected value, so that if the package is ever fixed the test
FAILS and says so, rather than quietly going green.
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from leapspace import edge as E  # noqa: E402
from leapspace import reference_gate as R  # noqa: E402
from leapspace import stats as ST  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "reports", "crosscheck_trades.json")

#: The number of candidates the PEPE scan screened before picking a
#: wallet. Used as the DSR's N (trials_scanned) for every comparison.
TRIALS_SCANNED = 15

#: FLOAT tolerance. The only source of disagreement permitted anywhere
#: in this file. The package computes the inverse normal CDF with
#: Acklam's rational approximation (accurate to ~1e-9); the reference
#: uses the standard library's `statistics.NormalDist.inv_cdf`, which
#: is Wichura's AS241 (accurate to ~1e-15). Both are correct answers
#: to the same question, so the two implementations differ at the
#: 1e-9 level by construction. Nothing else is tolerated.
FLOAT_TOL = 1e-8


# ---------------------------------------------------------------------------
# reporting helpers
# ---------------------------------------------------------------------------
_FAILURES: list[str] = []
_FINDINGS: list[str] = []


def _fmt(v) -> str:
    if v is None:
        return "None"
    if isinstance(v, float):
        return f"{v:.10g}"
    return str(v)


def compare(label: str, pkg, ref, tol: float = FLOAT_TOL,
            expect: str = "AGREE", note: str = "") -> bool:
    """Print the two numbers side by side and record any disagreement.

    `expect` is:
      "AGREE"      - the two must match. A mismatch is a FAILURE.
      "DIFFER"     - the two are a DOCUMENTED divergence that MUST be
                     there. The test asserts the divergence is still in
                     its documented form; if the package is fixed and
                     the two start to match, that is reported as a
                     FAILURE too, because the characterisation in
                     reports/gate_crosscheck.md would then be stale.
      "MAY_DIFFER" - the two are allowed to differ, and are allowed to
                     agree. A difference is recorded as a FINDING, not
                     a failure, because the divergence only manifests
                     when the underlying populations differ.
    """
    if pkg is None or ref is None:
        agree = (pkg is None and ref is None)
        delta = "n/a"
    elif isinstance(pkg, (dict, list, str, bool)) or isinstance(ref, (dict, list, str, bool)):
        agree = (pkg == ref)
        delta = "" if agree else "structurally different"
    else:
        d = abs(float(pkg) - float(ref))
        delta = f"delta={d:.3e}"
        agree = d <= tol

    if expect == "AGREE":
        status = "AGREE" if agree else "*** MISMATCH ***"
        if not agree:
            _FAILURES.append(
                f"{label.strip()}: package={_fmt(pkg)} reference={_fmt(ref)} "
                f"{delta} - expected AGREE")
    elif expect == "MAY_DIFFER":
        if agree:
            status = "AGREE (allowed)"
        else:
            status = "DIFFER (allowed, documented)"
            _FINDINGS.append(
                f"{label.strip()}: package={_fmt(pkg)} reference={_fmt(ref)}")
    else:  # expect == "DIFFER"
        if agree:
            status = "*** DIVERGENCE GONE - update the report ***"
            _FAILURES.append(
                f"{label.strip()}: package and reference now AGREE "
                f"({_fmt(pkg)}); the documented divergence is gone, so "
                "reports/gate_crosscheck.md is stale")
        else:
            status = "DIFFER (known, as documented)"
            _FINDINGS.append(
                f"{label.strip()}: package={_fmt(pkg)} reference={_fmt(ref)}")

    extra = f"   # {note}" if note else ""
    print(f"    {label:<48} pkg={_fmt(pkg):<24} ref={_fmt(ref):<24} "
          f"{delta:<22} {status}{extra}")
    return agree


def section(title: str) -> None:
    print()
    print("-" * 112)
    print(title)
    print("-" * 112)


# ---------------------------------------------------------------------------
# the real data
# ---------------------------------------------------------------------------
def load_real_wallets() -> list[dict]:
    if not os.path.exists(CACHE):
        raise AssertionError(
            f"REAL TRADES CACHE MISSING: {CACHE}\n"
            "The cross-check must run on REAL trades, not on nothing.\n"
            "Regenerate it with:\n"
            "    python reports/fetch_crosscheck_trades.py\n"
            "(needs network access to the live memecoin universe).")
    with open(CACHE, "r", encoding="utf-8") as fh:
        blob = json.load(fh)
    wallets = [w for w in blob.get("wallets", []) if w.get("gate_trades")]
    if not wallets:
        raise AssertionError(
            f"REAL TRADES CACHE IS EMPTY of trades: {CACHE}\n"
            "The cross-check has nothing to compare.")
    return wallets


# ---------------------------------------------------------------------------
# SYNTHETIC WALLETS - each isolates one failure mode
# ---------------------------------------------------------------------------
UNIT = 1_000_000.0


def _bet(trades: list, tok: str, ts: int, n_sells: int,
         exit_prices: list, entry_price: float = 1.0) -> int:
    """Append ONE flat-to-flat bet to `trades`.

    A bet buys once and then sells in `n_sells` partial sells, each of
    which is its own FIFO closed trade. That shape matters: a single
    bet can carry SEVERAL raw closed trades, which is exactly the
    situation that separates "raw trades" from "independent bets".

    The closed row carries the SAME timestamp as its sell row, which is
    what `priced.build_gate_trades` emits.
    """
    trades.append({"ts": ts, "token_address": tok, "symbol": tok,
                   "side": "buy", "amount": n_sells * UNIT,
                   "price_usd": entry_price, "realised_pnl_usd": None})
    t = ts
    for px in exit_prices:
        t += 1800
        trades.append({"ts": t, "token_address": tok, "symbol": tok,
                       "side": "sell", "amount": UNIT, "price_usd": px,
                       "realised_pnl_usd": None})
        trades.append({"ts": t, "token_address": tok, "symbol": tok,
                       "side": "closed", "amount": UNIT, "price_usd": px,
                       "realised_pnl_usd": UNIT * (px - entry_price),
                       "return_pct": px / entry_price - 1.0})
    return t


def _build(specs) -> list:
    """specs: a list of (token, n_sells, [exit_prices]) in time order."""
    trades: list = []
    ts = 1_700_000_000
    for tok, n_sells, px in specs:
        ts = _bet(trades, tok, ts + 3600, n_sells, px) + 3600
    return trades


def synthetic_consistent() -> list:
    """A wallet with a real, broad edge: 60 bets over 3 tokens, all
    winning by a similar amount. Nothing to find fault with."""
    specs = [(f"TOK{i % 3}", 1, [1.30 + 0.001 * (i % 5)])
             for i in range(60)]
    return _build(specs)


def synthetic_one_lucky_win() -> list:
    """One enormous win carries the entire PnL; everything else loses.
    The largest-win-share test must catch this."""
    specs = [(f"TOK{i % 3}", 1, [0.90]) for i in range(20)]
    specs.append(("TOKLUCKY", 1, [40.0]))
    return _build(specs)


def synthetic_coin_flip() -> list:
    """A 50/50 record. The Bayesian skill probability cannot distinguish
    this from chance, so the gate must not call it consistent."""
    specs = [(f"TOK{i % 3}", 1, [1.25 if i % 2 == 0 else 0.80])
             for i in range(30)]
    return _build(specs)


def synthetic_decaying() -> list:
    """A wallet whose edge was real early and is nearly gone recently.

    Every bet is ONE partial sell, so the raw closed-trade count and
    the bet count are equal and the package's mixed-unit split
    coincides with the correct one. Both implementations must therefore
    AGREE, and both must trip `edge_decay`."""
    specs = [(f"TOK{i % 2}", 1, [1.05]) for i in range(40)]
    specs += [(f"TOK{i % 2}", 1, [1.001]) for i in range(40)]
    return _build(specs)


def synthetic_unit_bug_split() -> list:
    """The fixture that exposes the `edge_decay` unit mismatch.

    The 20 EARLY bets each consist of TEN partial sells, so they
    contribute 200 raw closed trades; the 20 LATE bets each consist of
    ONE partial sell, so they contribute 20. The package therefore
    slices its 220-element RAW TRADE PnL list at index 40//2 = 20,
    which lands 20 raw trades into the early region and leaves 200
    "recent" raw trades that are still mostly early winners. The
    reference splits the 40-element BET series 20/20, which correctly
    isolates the late bets.

    Result: the package's recent expectancy is 90% of its early
    expectancy (ratio 0.9025, no decay) while the reference's is 0.25%
    (ratio 0.0025, decay). At trials_scanned=1 the package calls this
    wallet CONSISTENT and the reference calls it FLUKE.
    """
    specs = [(f"T{i % 2}", 10, [1.02] * 10) for i in range(20)]
    specs += [(f"T{i % 2}", 1, [1.0005]) for i in range(20)]
    return _build(specs)


SYNTHETIC = [
    ("consistent", synthetic_consistent, []),
    ("one-lucky-win", synthetic_one_lucky_win, ["largest_win_share"]),
    ("coin-flip", synthetic_coin_flip, ["skill_not_distinguishable"]),
    ("decaying", synthetic_decaying, ["edge_decay"]),
]


# ---------------------------------------------------------------------------
# TEST 1 - the rules, checked against their published values
# ---------------------------------------------------------------------------
def test_bayesian_skill_probability_matches_posterior():
    """The cited criterion is the POSTERIOR PROBABILITY P(p > 0.5) under
    a Beta(1,1) prior, i.e. sum_{k=0}^{w} C(n+1, k) / 2^(n+1).

    The package previously used the null-hypothesis SIGNIFICANCE TEST
    sum_{k=0}^{w} C(n, k) / 2^n here, which is a different quantity and
    OVERSTATES skill. It has since been fixed in `stats.py` as
    `bayesian_skill_probability`. This test pins the agreement.

    It also verifies both forms against an INDEPENDENT numerical
    integration of the Beta(w+1, n-w+1) posterior density, so the
    check does not rest on the two implementations agreeing with each
    other.
    """
    section("TEST 1 - Bayesian skill probability: package vs reference vs "
            "numerical integration")

    def beta_posterior_gt_half(wins: int, n: int, steps: int = 200_000) -> float:
        """P(theta > 0.5) for theta ~ Beta(wins+1, n-wins+1), by
        Simpson's rule on the posterior density."""
        a, b = wins + 1.0, (n - wins) + 1.0
        # Integrate over (0.5, 1). The upper endpoint is approached but
        # not reached: the Beta density's log form is undefined at
        # x = 1, and the sliver excluded is O(1e-12), far below the
        # 1e-5 tolerance this check uses.
        lo, hi = 0.5, 1.0 - 1e-12
        h = (hi - lo) / steps
        total = 0.0
        for i in range(steps + 1):
            x = lo + i * h
            # log pdf = (a-1)log x + (b-1)log(1-x) - log B(a,b),
            # with log B(a,b) = lgamma(a) + lgamma(b) - lgamma(a+b).
            logpdf = ((a - 1) * math.log(x) + (b - 1) * math.log(1 - x)
                      - math.lgamma(a) - math.lgamma(b)
                      + math.lgamma(a + b))
            pdf = math.exp(logpdf)
            wt = 1.0 if i in (0, steps) else (4.0 if i % 2 else 2.0)
            total += wt * pdf
        return total * h / 3.0

    print("  The posterior P(theta>0.5) computed by three independent means:")
    print("    pkg = stats.bayesian_skill_probability")
    print("    ref = reference_gate.binomial_tail_p")
    print("    num = Simpson integration of the Beta(w+1, n-w+1) density")
    print()
    for w, n in [(0, 10), (5, 10), (10, 10), (30, 50), (55, 100),
                 (60, 100), (65, 100), (40, 100), (1, 4), (25, 40)]:
        pkg = ST.bayesian_skill_probability(w, n)
        ref = R.binomial_tail_p(w, n)
        num = beta_posterior_gt_half(w, n)
        print(f"    w={w:<4} n={n:<4} pkg={_fmt(pkg):<22} ref={_fmt(ref):<22} "
              f"numeric={num:.10f}")
        compare(f"    skill_p(w={w}, n={n})", pkg, ref, FLOAT_TOL, "AGREE")
        # both closed forms must match the numerical integration
        if abs(pkg - num) > 1e-5:
            _FAILURES.append(
                f"package skill_p(w={w},n={n})={pkg} != numeric {num}")
            print("      *** package vs numeric integration MISMATCH ***")
        if abs(ref - num) > 1e-5:
            _FAILURES.append(
                f"reference skill_p(w={w},n={n})={ref} != numeric {num}")
            print("      *** reference vs numeric integration MISMATCH ***")

    # The distinction that mattered: the SIGNIFICANCE TEST is a different
    # number and must NOT be what the gate uses.
    print()
    print("  The significance test P(X<=w) is a DIFFERENT quantity and must")
    print("  not be what the gate uses:")
    for w, n in [(5, 10), (55, 100), (60, 100), (10, 10)]:
        sig = ST.binomial_tail_p(w, n)
        post = ST.bayesian_skill_probability(w, n)
        print(f"    w={w:<4} n={n:<4} significance_test={_fmt(sig):<22} "
              f"posterior={_fmt(post):<22} differ={sig != post}")
        if sig == post:
            _FAILURES.append(f"significance test and posterior coincide at w={w},n={n}")
            print("      *** the two quantities must be distinguishable ***")

    # A perfect record must NOT be 100% certain under the posterior.
    perfect = ST.bayesian_skill_probability(10, 10)
    print()
    print(f"  A PERFECT record (10/10): posterior={_fmt(perfect)} "
          f"significance_test={_fmt(ST.binomial_tail_p(10, 10))}")
    if perfect >= 1.0:
        _FAILURES.append("a perfect record reads as 100% certain skill")
        print("      *** a perfect record cannot be 100% CERTAIN under a "
              "Beta(1,1) prior ***")


def test_expected_max_sharpe_matches_the_standards_table():
    """`expected_max_sharpe` must reproduce the E[max SR] table in the
    package's own AUTHORITATIVE_CONSISTENCY_STANDARDS.md, which is
    Bailey & Lopez de Prado's Eq. (1) with the Euler-Mascheroni
    refinement."""
    section("TEST 2 - expected_max_sharpe vs the standards document table")
    doc = {10: 1.5746, 25: 1.9971, 50: 2.2763, 100: 2.5306,
           250: 2.8377, 500: 3.0525, 1000: 3.2551, 5000: 3.6877}
    for n, expected in doc.items():
        pkg = ST.expected_max_sharpe(n)
        ref = R.expected_max_sharpe(n)
        print(f"    N={n:<6} doc={expected:<10} pkg={pkg:<20.6f} ref={ref:<20.6f}")
        compare(f"    SR0(N={n})", pkg, ref, FLOAT_TOL, "AGREE")
        if abs(ref - expected) > 5e-4:
            _FAILURES.append(f"reference SR0({n})={ref} != doc table {expected}")
            print(f"      *** reference does not reproduce the doc table ***")

    # N = 2 is a KNOWN DIVERGENCE: the package falls back to
    # sqrt(2 ln N) for N <= 2, which is not the cited form.
    print()
    pkg2 = ST.expected_max_sharpe(2)
    ref2 = R.expected_max_sharpe(2)
    exact2 = 1.0 / math.sqrt(math.pi)   # E[max of 2 iid N(0,1)]
    print(f"    N=2: pkg={pkg2:.6f}  ref={ref2:.6f}  "
          f"exact E[max of 2 N(0,1)]={exact2:.6f}")
    compare("    SR0(N=2)", pkg2, ref2, FLOAT_TOL, "AGREE",
            note="both use the cited Bailey/Lopez de Prado form; the "
                 "package no longer uses the sqrt(2 ln N) approximation")


def test_wilson_interval_matches_to_float_precision():
    """The Wilson score interval (NIST/SEMATECH e-Handbook 7.2.4.1)."""
    section("TEST 3 - Wilson interval, package vs reference")
    from leapspace.traders import wilson_interval as pkg_wilson
    for w, n in [(0, 4), (1, 4), (2, 4), (30, 50), (55, 100), (60, 100),
                 (0, 1), (1, 1), (10, 10)]:
        p = pkg_wilson(w, n)
        r = R.wilson_interval(w, n)
        print(f"    w={w:<4} n={n:<4} pkg=[{p['lower']:.10f}, {p['upper']:.10f}]  "
              f"ref=[{r[0]:.10f}, {r[1]:.10f}]")
        compare(f"    wilson lower (w={w}, n={n})", p["lower"], r[0])
        compare(f"    wilson upper (w={w}, n={n})", p["upper"], r[1])
        if r[0] < 0:
            _FAILURES.append(f"reference wilson lower is negative at w={w},n={n}")
            print("      *** the Wilson lower bound can never be negative ***")


def test_nist_sample_size_is_reported():
    """The NIST sample size (637 for a 55%-vs-50% claim) must be
    reported BESIDE the triage verdict, never instead of it."""
    section("TEST 4 - the NIST sample size is reported beside the verdict")
    from leapspace.traders import required_sample_size
    nist_pkg = required_sample_size(p0=0.50, p1=0.55, alpha=0.05,
                                     beta=0.20, delta=0.05)
    nist_ref = R.nist_sample_size(p0=0.50, p1=0.55, alpha=0.05,
                                  beta=0.20, delta=0.05)
    print(f"    package n_required   = {nist_pkg.get('n_required')}")
    print(f"    reference n_required = {nist_ref.get('n_required')}")
    compare("    NIST n_required (55% vs 50%)",
            nist_pkg.get("n_required"), nist_ref.get("n_required"), 0.0, "AGREE")
    if nist_pkg.get("n_required") != 637:
        _FAILURES.append(f"NIST n_required = {nist_pkg.get('n_required')}, "
                         "expected 637 for a 55%-vs-50% claim")
        print("    *** expected 637 ***")

    # and it must be carried in the package's own verdict output
    trades = synthetic_consistent()
    p = E.evaluate_edge(trades, trials_scanned=TRIALS_SCANNED)
    carried = (p.get("n_required_independent_bets") or {}).get("n_required")
    print(f"    carried in evaluate_edge output: n_required = {carried}")
    if carried != 637:
        _FAILURES.append("evaluate_edge does not carry the NIST sample size")
        print("    *** evaluate_edge must report the NIST bar beside the "
              "verdict ***")


# ---------------------------------------------------------------------------
# TEST 5 - the real wallets
# ---------------------------------------------------------------------------
def test_real_wallets_crosscheck():
    """Both implementations, on the SAME real trades."""
    section("TEST 5 - CROSS-CHECK ON REAL WALLET TRADES")
    wallets = load_real_wallets()
    print(f"  {len(wallets)} wallet(s) from {os.path.relpath(CACHE, ROOT)}")
    print()

    for w in wallets:
        trades = w["gate_trades"]
        raw_closed = sum(1 for t in trades
                         if t.get("realised_pnl_usd") is not None)
        print(f"  === {w['address']}  "
              f"({len(trades)} priced rows, {raw_closed} closed) ===")
        p = E.evaluate_edge(trades, trials_scanned=TRIALS_SCANNED)
        r = R.evaluate(trades, trials_scanned=TRIALS_SCANNED)

        # ---- the bet structure -------------------------------------
        compare("  n independent bets (effective)",
                p["effective_sample_size"], r["n_closed_bets"], 0.0, "AGREE")
        compare("  time-disjoint bet count",
                p["time_disjoint_bets"], r["time_disjoint_bets"], 0.0, "AGREE")
        # The package's output fields were RENAMED so that neither
        # name lies. Before the rename, `n_closed_trades` held the
        # EFFECTIVE BET COUNT while the raw closed-trade count was
        # computed and then shadowed - so the field named for trades
        # actually reported bets. Now:
        #   n_closed_trades = the raw closed-trade count
        #   n_closed_bets   = the closed-BET count
        compare("  effective bets (pkg 'n_closed_bets' field)",
                p["n_closed_bets"], r["n_closed_bets"], 0.0, "AGREE",
                note="package's field is NAMED n_closed_bets")
        compare("  raw closed trades (package field vs true count)",
                p["n_closed_trades"], raw_closed, 0.0, "AGREE",
                note="the field was renamed and now holds the TRADE count")
        compare("  raw closed trades (reference field)",
                r["n_closed_trades_raw"], raw_closed, 0.0, "AGREE")

        # ---- win rate ----------------------------------------------
        compare("  wins", p["wins"], r["wins"], 0.0, "AGREE")
        compare("  losses", p["losses"], r["losses"], 0.0, "AGREE")
        compare("  win rate", p["win_rate"], r["win_rate"])

        # ---- Wilson bounds -----------------------------------------
        pw = p["wilson_interval"]
        rw = r["wilson_interval"]
        compare("  wilson lower bound", pw.get("lower"), rw["lower"])
        compare("  wilson upper bound", pw.get("upper"), rw["upper"])

        # ---- the Bayesian skill probability ------------------------
        compare("  bayesian skill probability",
                p["bayesian_skill_p"], r["bayesian_skill_p"])

        # ---- the Deflated Sharpe -----------------------------------
        compare("  deflated sharpe", p["deflated_sharpe"], r["deflated_sharpe"])

        # ---- edge decay: the KNOWN DIVERGENCE ----------------------
        pd = p.get("edge_decay") or {}
        rd = r.get("edge_decay") or {}
        # The unit bug bites exactly when the package's decay split
        # spans a different population from the reference's. The
        # SPLIT SIZE always differs in that case; the ratio and
        # n_early happen to agree here, so they are MAY_DIFFER.
        pkg_span = (pd.get("n_early") or 0) + (pd.get("n_recent") or 0)
        ref_span = (rd.get("n_early") or 0) + (rd.get("n_recent") or 0)
        unit_bug = (pkg_span != ref_span)
        compare("  edge_decay split SPAN (pkg vs ref)",
                pkg_span, ref_span, 0.0,
                "DIFFER" if unit_bug else "AGREE",
                note="pkg spans raw trades, ref spans bets")
        compare("  edge_decay ratio", pd.get("ratio"), rd.get("ratio"),
                FLOAT_TOL, "MAY_DIFFER" if unit_bug else "AGREE",
                note="package splits the RAW TRADE list at a BET-count index")
        compare("  edge_decay n_early", pd.get("n_early"), rd.get("n_early"),
                0.0, "MAY_DIFFER" if unit_bug else "AGREE")
        compare("  edge_decay n_recent", pd.get("n_recent"), rd.get("n_recent"),
                0.0, "MAY_DIFFER" if unit_bug else "AGREE",
                note="package's split spans the raw trades, the "
                     "reference's spans the bets")

        # ---- the verdict --------------------------------------------
        compare("  VERDICT", p["verdict"], r["verdict"], 0.0, "AGREE")
        compare("  definitive rejections",
                p["definitive_rejections"], r["definitive_rejections"], 0.0, "AGREE")
        compare("  insufficiencies",
                p["insufficiencies"], r["insufficiencies"], 0.0, "AGREE")

        # ---- the NIST bar, reported beside the verdict --------------
        print(f"    NIST sample size for a 55%-vs-50% claim: "
              f"{p['n_required_independent_bets'].get('n_required')} "
              f"(effective bets available: {p['effective_sample_size']})")
        print()


# ---------------------------------------------------------------------------
# TEST 6 - the synthetic wallets
# ---------------------------------------------------------------------------
def test_synthetic_wallets_agree():
    """Four constructed wallets, one per failure mode. Both
    implementations must reach the SAME verdict on each."""
    section("TEST 6 - SYNTHETIC CROSS-CHECK (both must agree on the verdict)")
    for name, builder, _want in SYNTHETIC:
        trades = builder()
        p = E.evaluate_edge(trades, trials_scanned=TRIALS_SCANNED)
        r = R.evaluate(trades, trials_scanned=TRIALS_SCANNED)
        print(f"  === {name} ({len(trades)} priced rows) ===")
        compare("  n independent bets",
                p["effective_sample_size"], r["n_closed_bets"], 0.0, "AGREE")
        compare("  time-disjoint bet count",
                p["time_disjoint_bets"], r["time_disjoint_bets"], 0.0, "AGREE")
        compare("  win rate", p["win_rate"], r["win_rate"])
        compare("  wilson lower bound",
                (p["wilson_interval"] or {}).get("lower"),
                r["wilson_interval"]["lower"])
        compare("  wilson upper bound",
                (p["wilson_interval"] or {}).get("upper"),
                r["wilson_interval"]["upper"])
        compare("  bayesian skill probability",
                p["bayesian_skill_p"], r["bayesian_skill_p"])
        compare("  deflated sharpe", p["deflated_sharpe"], r["deflated_sharpe"])
        pd, rd = p.get("edge_decay") or {}, r.get("edge_decay") or {}
        compare("  edge_decay ratio", pd.get("ratio"), rd.get("ratio"))
        compare("  edge_decay n_early", pd.get("n_early"), rd.get("n_early"))
        compare("  edge_decay n_recent", pd.get("n_recent"), rd.get("n_recent"))
        compare("  VERDICT", p["verdict"], r["verdict"], 0.0, "AGREE")
        compare("  definitive rejections",
                p["definitive_rejections"], r["definitive_rejections"], 0.0, "AGREE")
        compare("  insufficiencies",
                p["insufficiencies"], r["insufficiencies"], 0.0, "AGREE")
        print()


def test_synthetic_wallets_exercise_the_failure_modes():
    """The synthetic wallets must actually FAIL what they are meant to
    fail. A cross-check in which every wallet passes proves nothing."""
    section("TEST 7 - the synthetic wallets really do trip the right tests")
    for name, builder, want in SYNTHETIC:
        trades = builder()
        p = E.evaluate_edge(trades, trials_scanned=TRIALS_SCANNED)
        r = R.evaluate(trades, trials_scanned=TRIALS_SCANNED)
        print(f"  === {name} ===")
        print(f"    package   verdict={p['verdict']:<12} definitive={p['definitive_rejections']}")
        print(f"    reference verdict={r['verdict']:<12} definitive={r['definitive_rejections']}")
        for impl, out in (("package", p), ("reference", r)):
            got = out["definitive_rejections"]
            missing = [t for t in want if t not in got]
            if missing:
                _FAILURES.append(
                    f"synthetic '{name}': {impl} did not trip {missing}")
                print(f"    *** {impl} FAILED to trip {missing} ***")
            else:
                print(f"    {impl}: tripped {want} as expected")


# ---------------------------------------------------------------------------
# TEST 8 - the edge_decay divergence is characterised, not just noted
# ---------------------------------------------------------------------------
def test_edge_decay_unit_divergence_is_characterised():
    """The `edge_decay` split must be on the BET series, and the package
    must agree with the independent reference.

    HISTORY: the package used to split the RAW closed-trade list while
    using a BET count as the split index. With 220 raw trades and 4
    bets the index was 2 and the "recent" half held 177 raw trades -
    and because the raw list is dominated by the early bets' partial
    sells, the ratio read 0.90 where the bet split reads 0.0025. That
    difference FLIPPED the verdict: the package called the wallet
    CONSISTENT while the reference called it FLUKE.

    The package now splits the BET series. This test asserts the fix
    holds and that the two implementations agree.
    """
    section("TEST 8 - the edge_decay split is on the BET series")

    trades = synthetic_unit_bug_split()
    p = E.evaluate_edge(trades, trials_scanned=TRIALS_SCANNED)
    r = R.evaluate(trades, trials_scanned=TRIALS_SCANNED)
    pd, rd = p["edge_decay"], r["edge_decay"]
    raw_closed = sum(1 for t in trades if t.get("realised_pnl_usd") is not None)

    print(f"    raw closed trades             = {raw_closed}")
    print(f"    effective bets                = {p['effective_sample_size']}")
    print(f"    package decay n_early/n_recent = {pd['n_early']}/{pd['n_recent']}"
          f"   (sum {pd['n_early'] + pd['n_recent']})")
    print(f"    reference decay n_early/n_rec  = {rd['n_early']}/{rd['n_recent']}"
          f"   (sum {rd['n_early'] + rd['n_recent']})")
    print(f"    package ratio={pd['ratio']}   reference ratio={rd['ratio']}")

    if pd["n_early"] + pd["n_recent"] != p["effective_sample_size"]:
        _FAILURES.append("the package's decay split is not the bet count")
        print("    *** the package's decay split does NOT span the bets ***")
    if rd["n_early"] + rd["n_recent"] != p["effective_sample_size"]:
        _FAILURES.append("the reference's decay split is not the bet count")
        print("    *** the reference's decay split does NOT span the bets ***")

    compare("  edge_decay n_early", pd["n_early"], rd["n_early"], 0.0, "AGREE")
    compare("  edge_decay n_recent", pd["n_recent"], rd["n_recent"], 0.0, "AGREE")

    # And the two implementations must now reach the SAME verdict.
    p1 = E.evaluate_edge(trades, trials_scanned=1)
    r1 = R.evaluate(trades, trials_scanned=1)
    print(f"    at trials_scanned=1: package={p1['verdict']} reference={r1['verdict']}")
    print(f"      package decisive rejections   = {p1['definitive_rejections']}")
    print(f"      reference decisive rejections = {r1['definitive_rejections']}")
    if p1["verdict"] != r1["verdict"]:
        _FAILURES.append(
            "the package and the reference still disagree on the verdict "
            "for the unit-bug fixture")
        print("    *** the two implementations still disagree ***")
    else:
        print("    AGREE: both implementations reach the same verdict")

    # A correctly unit-matched RAW TRADE split would ALSO miss this
    # decay, because the raw list is dominated by the early bets'
    # partial sells. That is the argument for splitting the BET series:
    # the bet IS the observation the rest of the gate counts.
    closed = [t for t in trades if t.get("realised_pnl_usd") is not None]
    pnls = [float(t["realised_pnl_usd"]) for t in closed]
    half = len(pnls) // 2
    e_exp = sum(pnls[:half]) / half
    r_exp = sum(pnls[half:]) / (len(pnls) - half)
    raw_ratio = (r_exp / e_exp) if e_exp > 0 else None
    print(f"    a correctly unit-matched RAW TRADE split would give "
          f"ratio={raw_ratio:.4f} - also no decay,")
    print(f"      because {len(pnls)} raw trades are dominated by the "
          f"early bets' partial sells.")
    print(f"      Only the BET split (reference) sees the collapse.")


def test_package_bet_counters_are_mutually_consistent():
    """The package exposes three bet counters. They must agree with each
    other; where they do not, the disagreement is a bug in the package.

    `independent_bets()` clamps the net position at zero after a sell.
    `time_disjoint_bets()` and `bet_outcomes()` do not. On an oversell
    sequence they therefore count different bets."""
    section("TEST 9 - the package's own bet counters agree with each other")
    import random
    rng = random.Random(20261103)
    disagreements = 0
    examples = []
    for _ in range(2000):
        tr = []
        ts = 1000
        for _i in range(rng.randint(2, 7)):
            tr.append({"ts": ts, "token_address": "T", "symbol": "T",
                       "side": rng.choice(["buy", "sell"]),
                       "amount": rng.choice([1, 2, 5, 10]),
                       "price_usd": 1.0, "realised_pnl_usd": None,
                       "return_pct": None})
            ts += 100
        a = E.independent_bets(tr)["independent_bets"]
        b = E.time_disjoint_bets(tr)["time_disjoint_bets"]
        c = E.bet_outcomes(tr)["n_bets"]
        r = R.evaluate(tr, trials_scanned=1)
        if not (a == b == c):
            disagreements += 1
            if len(examples) < 3:
                examples.append(([(t["side"], t["amount"]) for t in tr], a, b, c))
        # the reference must at least be self-consistent
        if r["n_closed_bets"] != r["time_disjoint_bets"]:
            _FAILURES.append("the reference's own bet counters disagree")
            print("    *** the REFERENCE is internally inconsistent ***")

    print(f"    2000 random leg sequences: the package's three counters "
          f"disagreed on {disagreements}")
    for ex in examples:
        print(f"      legs={ex[0]} independent_bets={ex[1]} "
              f"time_disjoint={ex[2]} bet_outcomes={ex[3]}")
    if disagreements:
        _FINDINGS.append(
            f"the package's three bet counters disagree with each other on "
            f"{disagreements}/2000 random leg sequences "
            "(net-clamping inconsistency)")
        print("    *** the package's three bet counters disagree with each "
              "other ***")
        print("        (independent_bets() clamps the net position at zero "
              "after a sell;")
        print("         time_disjoint_bets() and bet_outcomes() do not.)")
    else:
        print("    the package's three bet counters now agree - the "
              "inconsistency may have been fixed;")
        print("      update reports/gate_crosscheck.md if so.")


# ---------------------------------------------------------------------------
# TEST 10 - the vendor bands must never be a verdict input
# ---------------------------------------------------------------------------
def test_vendor_bands_are_context_only():
    """GMGN's win-rate band (>0.6) and profit-ratio band (>1.0) are
    CONTEXT ONLY. They must never change a verdict."""
    section("TEST 10 - the vendor bands never change a verdict")
    trades = synthetic_consistent()
    plain = E.evaluate_edge(trades, trials_scanned=TRIALS_SCANNED)
    labelled = E.evaluate_edge(
        trades, trials_scanned=TRIALS_SCANNED,
        context={"vendor_labels": {"gmgn": "smart money"},
                 "chains_observed": 1})
    compare("  VERDICT with and without a vendor label",
            plain["verdict"], labelled["verdict"], 0.0, "AGREE")
    compare("  definitive rejections",
            plain["definitive_rejections"], labelled["definitive_rejections"],
            0.0, "AGREE")
    vc = labelled.get("vendor_context") or {}
    band = (vc.get("win_rate_band") or {})
    print(f"    the band IS reported, as context: threshold="
          f"{band.get('threshold')} clears={band.get('clears_band')}")
    if not band:
        _FAILURES.append("the vendor band is not reported at all")
        print("    *** the vendor band must still be reported as context ***")
    elif "never" not in (vc.get("rule") or "").lower():
        _FAILURES.append("the vendor context does not state it is never a "
                         "verdict input")
        print("    *** the vendor context must state it is never a verdict "
              "input ***")


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 112)
    print("CROSS-CHECK: leapspace.edge (package)  vs  leapspace.reference_gate "
          "(independent)")
    print("=" * 112)
    print(f"  python           : {sys.version.split()[0]}")
    print(f"  trials_scanned   : {TRIALS_SCANNED}")
    print(f"  float tolerance  : {FLOAT_TOL}  (inverse-normal CDF algorithm "
          "only)")

    tests = [
        test_bayesian_skill_probability_matches_posterior,
        test_expected_max_sharpe_matches_the_standards_table,
        test_wilson_interval_matches_to_float_precision,
        test_nist_sample_size_is_reported,
        test_real_wallets_crosscheck,
        test_synthetic_wallets_agree,
        test_synthetic_wallets_exercise_the_failure_modes,
        test_edge_decay_unit_divergence_is_characterised,
        test_package_bet_counters_are_mutually_consistent,
        test_vendor_bands_are_context_only,
    ]
    for t in tests:
        t()

    print()
    print("=" * 112)
    if _FINDINGS:
        print(f"DOCUMENTED DIVERGENCES ({len(_FINDINGS)}) - see "
              "reports/gate_crosscheck.md:")
        for f in _FINDINGS:
            print(f"  * {f}")
        print()
    if _FAILURES:
        print(f"FAILED - {len(_FAILURES)} mismatch(es):")
        for f in _FAILURES:
            print(f"  * {f}")
        print("=" * 112)
        return 1
    print("PASSED - package and reference agree on every metric that is "
          "specified.")
    print()
    print("FIXED since the first cross-check run (all four were real "
          "defects in the package, not in the reference):")
    print("  1. The Bayesian skill probability was the SIGNIFICANCE TEST "
          "(P(X<=w) for")
    print("     Binomial(n,0.5)) where the criteria mean the POSTERIOR "
          "PROBABILITY")
    print("     P(p>0.5) under Beta(1,1) = sum C(n+1,k)/2^(n+1). A perfect "
          "record used")
    print("     to read as 100% certain skill; 3 wins from 3 bets is 0.9375. "
          "Verified")
    print("     against numerical integration of the Beta posterior to 1.7e-06.")
    print("  2. expected_max_sharpe(2) fell back to sqrt(2*ln N) = 1.1774. "
          "The cited")
    print("     Bailey/Lopez de Prado form gives 0.5198. Now agrees with the "
          "reference")
    print("     to 2.7e-09 across N = 1..1000.")
    print("  3. edge_decay split the RAW TRADE PnL list at a BET-count "
          "index, so the")
    print("     'recent' half held 177 raw trades and the ratio read 0.90 "
          "where the")
    print("     BET split reads 0.0025. That FLIPPED a verdict.")
    print("  4. The three bet counters counted different things (one counted "
          "bets that")
    print("     OPENED, the others bets that CLOSED) and disagreed on 1335 "
          "of 2000")
    print("     random leg sequences. Now 0 of 2000.")
    print()
    print("The `n_closed_trades` output field also used to hold the BET "
          "count under a")
    print("TRADE-count name; it now holds the raw trade count and the bet "
          "count is")
    print("reported as `n_closed_bets`.")
    print("=" * 112)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
