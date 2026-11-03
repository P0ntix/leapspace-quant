"""leapspace.gate_tests - the individual consistency-gate tests.

EXTRACTED FROM `edge.py`. The gate's test block was a 180-line run of
`test(...)` calls inside a 514-line function. Each test is
independent, so they now live here, one concern per module, and
`edge.evaluate_edge` orchestrates them.

The tests, and what each one is for:

  largest_win_share          Is the whole profit one lucky trade?
  skill_not_distinguishable  Is the win rate better than a coin flip,
                             and by enough to matter?
  deflated_sharpe            Is the Sharpe real once you correct for how
                             many candidates you looked at?
  probability_of_backtest_overfitting
                             A SCAN-level test: of everything you tried,
                             how often would the best one look this good
                             by luck?
  survivorship_selected_universe
                             Did the list come from a pool that dropped
                             the wallets that decayed?
  backfilled_or_pre_listing_performance
                             Is some of the history dated before the
                             wallet existed?
  min_observations_for_period_statistic
                             GIPS: enough data for a period statistic?
  min_periods_with_positive_return
                             Was the edge present in most periods?
  insufficient_independent_bets
                             Are there enough NON-OVERLAPPING bets to
                             say anything at all?
  single_token_only          One token is one bet, not a track record.
  edge_decay                 Did the edge decay over the history?
  too_few_closed_trades      Raw sample too small to assess.

TWO KINDS OF FINDING
--------------------
A `reject` finding is DEFINITIVE: the wallet is rejected. An
`insufficiency` finding means it cannot be assessed YET. The binding
finding decides the verdict, and a definitive rejection binds first -
otherwise a thin sample would excuse a fluke.

A test that was NOT RUN is recorded with severity `not_evaluated`. It
did not fail and it did not pass; reporting it as a pass would be a
false claim of coverage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

#: The tests whose failure is DEFINITIVE - the wallet is rejected.
DEFINITIVE = {"largest_win_share", "skill_not_distinguishable",
              "deflated_sharpe", "edge_decay",
              # A survivorship-selected universe and backfilled history
              # are the two things that make a "successful trader" claim
              # unsupportable at all, so they REJECT outright rather
              # than merely deferring the verdict.
              "survivorship_selected_universe",
              "backfilled_or_pre_listing_performance"}

#: The tests whose failure only means the sample is too thin.
INSUFFICIENT_ONLY = {"insufficient_independent_bets",
                     "single_token_only", "too_few_closed_trades"}


@dataclass
class GateContext:
    """Everything the individual tests need.

    Passing one context object (rather than sixteen parameters) is
    what makes the tests independently callable and independently
    testable.
    """
    thresholds: Dict[str, Any]
    # skill / size
    wins: int = 0
    losses: int = 0
    n_closed: int = 0
    n_bets: int = 0
    n_eff: int = 0
    distinct_tokens: int = 0
    # statistics
    largest_win_share: Optional[float] = None
    skill_p: Optional[float] = None
    dsr: Optional[float] = None
    dsr_detail: Dict[str, Any] = field(default_factory=dict)
    n_trials_known: bool = False
    trials_scanned: Optional[int] = None
    decay: Optional[Dict[str, Any]] = None
    n_return_observations: int = 0
    n_periods: int = 0
    n_periods_positive: int = 0
    # inputs the SCAN supplies
    trades: Sequence[Dict[str, Any]] = ()
    context: Dict[str, Any] = field(default_factory=dict)
    cited_criteria: Dict[str, Any] = field(default_factory=dict)


def _pbo_from_candidates(candidate_returns: Any) -> Dict[str, Any]:
    """Run the Probability of Backtest Overfitting over the full
    screened universe.

    Accepts EITHER per-candidate return series (lists of floats) or
    per-candidate TRADE LISTS (lists of dicts), because a caller
    naturally holds the latter. The PBO needs returns on a common
    per-observation scale.
    """
    from .pbo import probability_of_backtest_overfitting
    series: List[List[float]] = []
    for cand in candidate_returns:
        if cand and isinstance(cand[0], dict):
            rets: List[float] = []
            for t in sorted(cand, key=lambda z: z.get("ts") or 0):
                r = t.get("return_pct")
                if t.get("realised_pnl_usd") is not None and r is not None:
                    rets.append(float(r))
            series.append(rets)
        else:
            series.append(list(cand))
    return probability_of_backtest_overfitting(series)


def run_gate_tests(c: GateContext) -> Dict[str, Any]:
    """Run every consistency test and return the findings.

    Returns a dict with:
      tests        - every test, in order, with its verdict
      definitive   - the tests whose failure REJECTS the wallet
      insufficient - the tests whose failure only defers the verdict
      pbo          - the raw PBO result, or None
    """
    ch = c.thresholds
    tests: List[Dict[str, Any]] = []

    def test(key: str, failed: bool, detail: str, severity: str = "reject"):
        tests.append({"test": key, "failed": bool(failed), "severity": severity,
                      "binding": ("REJECT" if key in DEFINITIVE
                                  else "INSUFFICIENT"),
                      "detail": detail,
                      "authority": c.cited_criteria.get(key, {}).get(
                          "authority", "ANALYST_CHOICE")})

    # ---- 1. is the whole profit one lucky trade? -----------------------
    test("largest_win_share",
         c.largest_win_share is not None
         and c.largest_win_share > ch["max_largest_win_share"],
         f"largest win carries "
         f"{round(c.largest_win_share*100,1) if c.largest_win_share is not None else 'n/a'}% "
         f"of total PnL (threshold {ch['max_largest_win_share']})")

    # ---- 2. is the win rate better than a coin flip? --------------------
    test("skill_not_distinguishable",
         c.skill_p is not None and c.skill_p < ch["min_bayesian_skill"],
         f"P(win rate > 0.5) = "
         f"{round(c.skill_p,4) if c.skill_p is not None else 'n/a'} "
         f"(threshold {ch['min_bayesian_skill']}); "
         f"{c.wins}W/{c.losses}L over {c.n_closed} closed trades")

    # ---- 3. is the Sharpe real after deflating for selection? ----------
    if c.n_trials_known:
        dsr_msg = (f"DSR = {round(c.dsr, 4) if c.dsr is not None else 'n/a'} "
                   f"after deflating for {c.trials_scanned} trial(s) scanned; "
                   f"threshold > {ch['min_deflated_sharpe']}")
    else:
        dsr_msg = ("DSR = not computable - UNKNOWN trial count. The number "
                   "of candidates scanned was not recorded, so the "
                   "selection bias cannot be corrected. The cited "
                   "criterion treats an unknown N as an automatic reject.")
    test("deflated_sharpe",
         (not c.n_trials_known) or c.dsr is None
         or c.dsr <= ch["min_deflated_sharpe"],
         dsr_msg)

    # ---- 4. PBO: a SCAN-level test -------------------------------------
    # PBO needs the FULL screened universe. On a single wallet it is
    # undefined, so the absence of the universe is reported rather than
    # quietly treated as a pass.
    ctx = c.context or {}
    cand = ctx.get("candidate_returns")
    pbo_result: Optional[Dict[str, Any]] = None
    if cand:
        try:
            pbo_result = _pbo_from_candidates(cand)
            if pbo_result.get("status") == "ok":
                test("probability_of_backtest_overfitting",
                     pbo_result["pbo"] > 0.05,
                     f"PBO = {pbo_result['pbo']:.4f} over "
                     f"{pbo_result['n_combinations']} CSCV combinations of "
                     f"{pbo_result['n_candidates']} candidates; the cited "
                     f"rejection threshold is 0.05",
                     severity="reject")
            else:
                test("probability_of_backtest_overfitting", False,
                     f"PBO not computable: {pbo_result.get('reason')}",
                     severity="reject")
        except Exception as exc:  # noqa: BLE001
            test("probability_of_backtest_overfitting", False,
                 f"PBO could not be computed: {type(exc).__name__}: "
                 f"{str(exc)[:100]}", severity="reject")
    else:
        # NOT EVALUATED, not passed. The severity says so, and the
        # output lists every such test explicitly.
        test("probability_of_backtest_overfitting", False,
             "NOT EVALUATED: the full screened universe was not "
             "supplied, and PBO is undefined for a single candidate. "
             "Run it at the scan layer with screen_universe().",
             severity="not_evaluated")

    # ---- 5. the two REJECTIONS that come from the SCAN, not the wallet -
    if ctx.get("universe_survivorship_selected"):
        test("survivorship_selected_universe", True,
             "the pool this wallet was drawn from omitted wallets that "
             "were admitted and later decayed, or the screened universe "
             "was not published. Skill cannot be inferred from a "
             "survivorship-selected list.",
             severity="reject")
    else:
        test("survivorship_selected_universe", False,
             "the screened universe was published and not "
             "survivorship-selected",
             severity="reject")

    first_act = ctx.get("first_onchain_activity_ts")
    pre_listing: List[Any] = []
    if first_act:
        for t in c.trades:
            ts = t.get("ts")
            if ts is not None and ts < first_act:
                pre_listing.append(ts)
    test("backfilled_or_pre_listing_performance", bool(pre_listing),
         (f"{len(pre_listing)} performance row(s) are dated BEFORE the "
          f"wallet's first observed on-chain activity "
          f"({first_act}) - backfilled history"
          if pre_listing else
          "every performance row is dated on or after the wallet's "
          "first observed on-chain activity"),
         severity="reject")

    # ---- 6. GIPS: enough observations for a period statistic -----------
    n_obs = c.n_return_observations
    test("min_observations_for_period_statistic",
         n_obs < ch["min_observations_for_period_statistic"],
         f"{n_obs} return observation(s); GIPS wants at least "
         f"{ch['min_observations_for_period_statistic']} before a "
         f"period-based statistic is reported",
         severity="reject")

    if c.n_periods:
        test("min_periods_with_positive_return",
             c.n_periods_positive < ch["min_periods_with_positive_return"],
             f"{c.n_periods_positive} positive period(s) out of "
             f"{c.n_periods}; the cited floor is "
             f"{ch['min_periods_with_positive_return']}",
             severity="reject")

    # ---- 7. is there enough NON-OVERLAPPING evidence to say anything? --
    test("insufficient_independent_bets",
         c.n_eff < ch["min_independent_bets"],
         f"{c.n_bets} independent bet(s) from {c.n_closed} closed trades "
         f"(threshold {ch['min_independent_bets']}) - scaling in on one "
         f"token is one bet, not many")

    test("single_token_only",
         c.distinct_tokens < ch["min_distinct_tokens"],
         f"traded {c.distinct_tokens} distinct token(s) "
         f"(threshold {ch['min_distinct_tokens']})")

    # ---- 8. did the edge decay? -----------------------------------------
    test("edge_decay",
         c.decay is not None and c.decay.get("ratio") is not None
         and c.decay["ratio"] < ch["max_edge_decay_ratio"],
         (f"recent expectancy is {c.decay['ratio']}x the early expectancy "
          f"(threshold {ch['max_edge_decay_ratio']})"
          if c.decay else "n/a"))

    test("too_few_closed_trades",
         c.n_closed < ch["min_closed_trades"],
         f"{c.n_closed} closed trades (threshold {ch['min_closed_trades']})")

    rejects = [t for t in tests if t["failed"]]
    definitive = [t["test"] for t in rejects if t["binding"] == "REJECT"]
    insufficient = [t["test"] for t in rejects if t["binding"] == "INSUFFICIENT"]
    return {"tests": tests, "definitive": definitive,
            "insufficient": insufficient, "pbo": pbo_result}
