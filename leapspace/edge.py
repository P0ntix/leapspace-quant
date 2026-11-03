"""Edge and consistency: separating a consistently profitable trader from a
one-shot winner.

This module answers the question the whitelist actually needs: not "did
this wallet make money?" but "is this wallet's edge REAL, CONSISTENT, and
not an artefact of selection, luck, or decay?"

THE FIVE WAYS A WALLET LOOKS GOOD WITHOUT BEING GOOD
----------------------------------------------------
1. **One lucky win.** A single 500x on a obscure token carries the whole
   PnL. `fluke_largest_win_share` catches it.
2. **Coin-flip win rate.** 55% over 12 trades is indistinguishable from
   chance. `bayesian_skill` catches it with an exact binomial tail, and
   `min_independent_bets` catches it before the maths even runs.
3. **Best-of-many selection.** You scanned 500 candidate wallets and kept
   the best; its Sharpe is inflated by the selection. `deflated_sharpe`
   corrects for that using the number of trials.
4. **Decay.** The edge was real and is gone. `edge_decay` compares the
   early half of the track record with the recent half.
5. **One token.** Every trade is the same token, so there is ONE bet, not
   many. `independent_bets` counts non-overlapping positions per asset.

WHAT IS CITED AND WHAT IS AN ANALYST CHOICE
--------------------------------------------
`CITED` items are in `CITED_CRITERIA` with their source. `ANALYST_CHOICE`
items are thresholds this package invented, and every one says so. The
research in AUTHORITATIVE_CONSISTENCY_STANDARDS.md is what establishes
which is which.

MATH WITHOUT SCIPY
-------------------
The Bayesian skill probability is computed EXACTLY with integer
arithmetic. For a Beta(1,1) prior and Beta-Binomial posterior, the
posterior probability that the true win rate exceeds 0.5 is identical to
the one-sided binomial tail probability of the observed win count, so
`math.comb` gives the exact answer with no floating-point cancellation.
"""
from __future__ import annotations

from . import stats as ST
from .stats import (bayesian_skill_probability, binomial_tail_p,
                     norm_cdf as _norm_cdf, norm_ppf as _norm_ppf,
                     poly as _poly)

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Cited criteria
# --------------------------------------------------------------------------
CITED_CRITERIA: Dict[str, Dict[str, Any]] = {
    "bayesian_skill": {
        "label": "Posterior probability the win rate exceeds chance",
        "authority": "Beta-Binomial conjugate model (weak uniform Beta(1,1) prior)",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "note": ("P(p > 0.5 | data) with a Beta(1,1) prior equals the "
                 "one-sided binomial tail probability of the observed win "
                 "count, so it is computed exactly."),
    },
    "min_independent_bets": {
        "label": "Minimum independent bets (not raw trades)",
        "authority": "Bailey & Lopez de Prado - independent bets, not trades",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "note": ("A 'bet' is a sequence of trades in one asset where the "
                 "position is not closed before the next opens. Overlapping "
                 "trades in the same asset are ONE bet, not many."),
    },
    "deflated_sharpe": {
        "label": "Deflated Sharpe Ratio",
        "authority": "Bailey & Lopez de Prado, 'The Deflated Sharpe Ratio'",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "note": ("Corrects an observed Sharpe for (a) the number of trials "
                 "performed and (b) non-normal returns. A Sharpe that is "
                 "not positive after deflation was selection, not skill."),
    },
    "consistency_ratio": {
        "label": "Share of periods with a positive return",
        "authority": "Professional performance-measurement practice",
        "tag": "ANALYTICS-VENDOR-CONVENTION",
        "note": ("The threshold is an analyst choice. The MEASURE itself is "
                 "standard practice; the number is not published by any "
                 "authority."),
    },
    "sortino": {
        "label": "Sortino ratio",
        "authority": "CFA Institute - 'The Sortino Ratio'",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": ("https://rpc.cfainstitute.org/sites/default/files/-/media/"
                "documents/code/gips/the-sortino-ratio.pdf"),
        "note": ("(Mean return - MAR) / downside deviation. CFA Institute "
                 "publishes the DEFINITION; it publishes no band."),
    },
    "calmar": {
        "label": "Calmar ratio",
        "authority": "Standard risk-adjusted performance measure",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "note": "Annualised return / maximum drawdown.",
    },
}

#: Analyst-chosen thresholds. Every one is an ANALYST CHOICE.
ANALYST_CHOICES: Dict[str, Any] = {
    "min_bayesian_skill": 0.95,
    "min_independent_bets": 5,
    # CITED: Bailey & Lopez de Prado, 'The Deflated Sharpe Ratio'. The
    # 0.95 acceptance bar is the paper's own, not this package's.
    # (It was 0.0 here, which only rejected a NEGATIVE deflated Sharpe
    # and was therefore far more permissive than the standard.)
    "min_deflated_sharpe": 0.95,
    "min_consistency_ratio": 0.5,
    "max_largest_win_share": 0.50,
    "max_edge_decay_ratio": 0.5,
    "min_distinct_tokens": 2,
    "min_closed_trades": 30,
    # CITED: CFA Institute (GIPS) 1.A.3 / 6.A.1(a) / 8.C.1(a) - a
    # period statistic needs enough observations to mean anything.
    "min_observations_for_period_statistic": 36,
    # CITED: CFA Institute (GIPS) - the number of positive periods.
    "min_periods_with_positive_return": 3,
}


# --------------------------------------------------------------------------
# Small statistics helpers (no SciPy)
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# Independent bets
# --------------------------------------------------------------------------
def independent_bets(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Count INDEPENDENT bets, not raw trades.

    A bet is a sequence of trades in one asset where the position is not
    closed before the next one opens. Implementation: walk each asset's
    trades in time order maintaining the running net position; a NEW bet
    starts whenever the position was flat (net == 0) before the buy.

    Raw trades and independent bets are very different numbers. A wallet
    that bought the same token 40 times over two years with a single
    position running has ONE bet, and one bet tells you nothing.
    """
    by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in trades:
        key = t.get("token_address") or t.get("symbol") or "?"
        by_token.setdefault(key, []).append(t)

    bets = 0
    per_token: Dict[str, int] = {}
    detail: List[Dict[str, Any]] = []
    for key, rows in by_token.items():
        rows = sorted(rows, key=lambda r: r.get("ts") or 0)
        net = 0.0
        in_bet = False
        token_bets = 0
        for r in rows:
            side = r.get("side")
            amt = float(r.get("amount") or 0)
            if side == "buy":
                if net <= 0:      # flat before this buy -> a new bet opens
                    in_bet = True
                net += amt
            elif side == "sell":
                net -= amt
                # A bet is counted when it CLOSES, which is what
                # `bet_outcomes` and `time_disjoint_bets` count too.
                # This function used to count every bet that OPENED,
                # so an open position counted as a bet while the other
                # two counters said there was none - the three
                # disagreed on 1335 of 2000 random leg sequences.
                # They now share one definition and one set of rules:
                #   - a buy while flat (net <= 0) opens a bet
                #   - a sell that takes net to <= 0 closes it
                #   - a sell with no open bet does NOT reset net, so a
                #     leading sell leaves the position negative
                if net <= 0 and in_bet:
                    net = 0.0
                    token_bets += 1
                    in_bet = False
        bets += token_bets
        per_token[key] = token_bets
        detail.append({"token": key, "trades": len(rows),
                       "independent_bets": token_bets,
                       "symbol": rows[0].get("symbol")})
    detail.sort(key=lambda d: -d["trades"])
    return {
        "independent_bets": bets,
        "raw_trades": len(trades),
        "distinct_tokens": len(by_token),
        "per_token": per_token,
        "detail": detail,
        "note": ("Trades in the SAME token with an open position between "
                 "them are ONE bet. Scaling in is not diversification."),
    }


# --------------------------------------------------------------------------
# The consistency / edge gate
# --------------------------------------------------------------------------

def time_disjoint_bets(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """The maximum number of bets whose HOLDING INTERVALS do not overlap.

    `independent_bets` counts non-overlapping positions WITHIN each
    asset. But a wallet holding PEPE and SHIB at the same time has two
    bets that are not independent of each other - every memecoin shares
    one risk factor, so the outcomes move together.

    This is the classic interval-scheduling problem: the maximum set of
    mutually disjoint intervals is found greedily by taking the bet with
    the earliest END time, then repeating. Bets with an unknown end
    (still open) are excluded, because an unbounded interval overlaps
    everything after it.
    """
    by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in trades:
        key = t.get("token_address") or t.get("symbol") or "?"
        by_token.setdefault(key, []).append(t)

    intervals: List[Tuple[int, int, str]] = []
    for key, rows in by_token.items():
        rows = sorted(rows, key=lambda r: r.get("ts") or 0)
        net = 0.0
        start = None
        for r in rows:
            side = r.get("side")
            amt = float(r.get("amount") or 0)
            ts = int(r.get("ts") or 0)
            if side == "buy":
                if net <= 0:
                    start = ts
                net += amt
            elif side == "sell":
                net -= amt
                if net <= 0 and start is not None:
                    intervals.append((start, ts, key))
                    net = 0.0
                    start = None
        # An open position has no bounded interval; it is excluded.
    intervals.sort(key=lambda iv: (iv[1], iv[0]))
    count = 0
    last_end = None
    for s, e, _k in intervals:
        if last_end is None or s >= last_end:
            count += 1
            last_end = e
    return {
        "time_disjoint_bets": count,
        "n_bounded_bets": len(intervals),
        "n_open_bets": sum(1 for _k, rows in by_token.items()
                           for _r in rows if False),
        "note": ("Maximum set of mutually non-overlapping holding "
                 "intervals. Bets held simultaneously in different "
                 "tokens are correlated and count once."),
    }


def bet_outcomes(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """One outcome per INDEPENDENT BET.

    A bet runs from the moment a position goes flat to the moment it
    returns to flat. Its outcome is the sum of the realised PnL of the
    closed trades that fall inside its holding interval.

    Returns:
        bets          - every bounded bet, with its pnl and interval
        effective     - the maximum set of mutually non-overlapping
                        intervals (greedy, by earliest end time)
        n_closed_bets - how many bets actually closed
        wins/losses   - counted over the EFFECTIVE bets
    """
    by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in trades:
        key = t.get("token_address") or t.get("symbol") or "?"
        by_token.setdefault(key, []).append(t)

    # ---- the closed trades, by token --------------------------------
    closed_by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in trades:
        if t.get("realised_pnl_usd") is None:
            continue
        key = t.get("token_address") or t.get("symbol") or "?"
        closed_by_token.setdefault(key, []).append(t)

    bets: List[Dict[str, Any]] = []
    for key, rows in by_token.items():
        rows = sorted(rows, key=lambda r: r.get("ts") or 0)
        net = 0.0
        start = None
        entry_idx = 0
        for r in rows:
            side = r.get("side")
            amt = float(r.get("amount") or 0)
            ts = int(r.get("ts") or 0)
            if side == "buy":
                if net <= 0:
                    start = ts
                    entry_idx = len(bets)
                net += amt
            elif side == "sell":
                net -= amt
                if net <= 0 and start is not None:
                    bets.append({"token": key, "start": start, "end": ts,
                                 "symbol": r.get("symbol"),
                                 "pnl": 0.0, "n_closed": 0})
                    start = None
                    net = 0.0

    # ---- attribute each closed trade to its bet ----------------------
    for key, cts in closed_by_token.items():
        ctoks = [b for b in bets if b["token"] == key]
        for ct in cts:
            ets = ct.get("entry_ts")
            if ets is None:
                ets = ct.get("ts")
            for b in ctoks:
                if b["start"] <= (ets or 0) <= b["end"]:
                    pnl = float(ct.get("realised_pnl_usd") or 0)
                    b["pnl"] += pnl
                    b["n_closed"] += 1
                    # The BET's return is the amount-weighted mean of its
                    # closed trades' returns. It has to be on the same
                    # per-observation scale as the bet count used in the
                    # DSR's sqrt(T-1) term.
                    amt = float(ct.get("amount") or 0)
                    rp = ct.get("return_pct")
                    if rp is not None:
                        b["ret_num"] = b.get("ret_num", 0.0) + amt * float(rp)
                        b["ret_den"] = b.get("ret_den", 0.0) + amt
                    break

    for b in bets:
        den = b.get("ret_den") or 0.0
        b["return_pct"] = (b.get("ret_num", 0.0) / den) if den else None

    # ---- the EFFECTIVE set: mutually non-overlapping intervals ------
    ordered = sorted([b for b in bets if b["end"] >= b["start"]],
                     key=lambda b: (b["end"], b["start"]))
    effective: List[Dict[str, Any]] = []
    last_end = None
    for b in ordered:
        if last_end is None or b["start"] >= last_end:
            effective.append(b)
            last_end = b["end"]

    n_closed_bets = len(effective)
    wins = sum(1 for b in effective if b["pnl"] > 0)
    losses = n_closed_bets - wins
    return {
        "bets": bets,
        "effective": effective,
        "n_bets": len(bets),
        "n_closed_bets": n_closed_bets,
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / n_closed_bets) if n_closed_bets else None,
        "total_pnl": sum(b["pnl"] for b in effective),
        "note": ("Wins and losses are counted over INDEPENDENT BETS, not "
                 "raw closed trades. A wallet with 179 closed trades "
                 "spread over 7 assets has at most a handful of "
                 "independent bets, and that is the sample the "
                 "statistical tests must use."),
    }


def drawdown_duration(returns: Sequence[float]) -> Dict[str, Any]:
    """The LONGEST underwater stretch, in observations and in days.

    Sharpe and Sortino both IGNORE duration: a strategy that fell 50%
    and recovered within one period scores the same as one that fell 50%
    and recovered over two years. The cited criteria ask for the
    duration explicitly.

    `returns` is the per-observation return series.
    """
    eq = 1.0
    peak = 1.0
    longest = 0
    cur = 0
    cur_start = 0
    longest_start = 0
    for i, r in enumerate(returns):
        eq *= (1.0 + float(r or 0.0))
        if eq >= peak:
            peak = eq
            cur = 0
            cur_start = i + 1
        else:
            cur += 1
            if cur > longest:
                longest = cur
                longest_start = cur_start
    return {"longest_underwater_observations": longest,
            "longest_underwater_start": longest_start,
            "note": ("Duration of the longest stretch below the prior "
                     "peak. Neither Sharpe nor Sortino sees it."),
            "authority": ("CFA Institute, Portfolio Performance "
                           "Evaluation - maximum drawdown and drawdown "
                           "duration")}


def posterior_split_half_stability(bets: Sequence[Dict[str, Any]]
                                    ) -> Dict[str, Any]:
    """P(theta > 0.5) on the EARLY half versus the FULL history.

    The cited criterion: "the posterior P(theta>0.5) computed on the
    early half falls materially below that computed on the full
    history". A wallet whose edge decayed has an early posterior that
    looks BETTER than its full-history posterior - the opposite of a
    wallet whose edge is improving. That inversion is the signal.
    """
    pnls = [float(b.get("pnl") or 0.0) for b in bets]
    if len(pnls) < 4:
        return {"status": "insufficient",
                "reason": ("at least 4 closed bets are needed for a "
                           "split-half comparison"),
                "authority": ("Barber, Bay & Solberg, 'Bayes Rules!' "
                              "Ch.3 - posterior stability")}
    half = len(pnls) // 2
    early = pnls[:half]
    full = pnls
    early_wins = sum(1 for p in early if p > 0)
    full_wins = sum(1 for p in full if p > 0)
    # The POSTERIOR probability P(theta > 0.5), not the null-hypothesis
    # significance test. The criterion names a posterior, so this must
    # be the posterior; the significance test overstates it.
    p_early = bayesian_skill_probability(early_wins, len(early))
    p_full = bayesian_skill_probability(full_wins, len(full))
    return {
        "status": "ok",
        "p_early_half": p_early,
        "p_full_history": p_full,
        "early_minus_full": p_early - p_full,
        "early_n": len(early), "full_n": len(full),
        "decaying": bool(p_early - p_full > 0.20),
        "note": ("A positive early-minus-full means the early half "
                 "looked BETTER than the full history - the signature "
                 "of a decaying edge."),
        "authority": ("Barber, Bay & Solberg, 'Bayes Rules!' Ch.3 - "
                      "posterior stability across a split half"),
    }


def n_required_independent_bets(p0: float = 0.50, p1: float = 0.55,
                                 alpha: float = 0.05, beta: float = 0.20,
                                 delta: float = 0.05) -> Dict[str, Any]:
    """The NIST-computed sample size for a claim about the win rate.

    This is the STANDARD bar, and it is separate from the triage
    verdict. A wallet can be CONSISTENT on a handful of bets and still
    be nowhere near the number of independent bets a published claim
    would need. Both numbers are reported so the two can never be
    confused.
    """
    try:
        from .traders import required_sample_size
        r = required_sample_size(p0=p0, p1=p1, alpha=alpha, beta=beta,
                                 delta=delta)
        return {"n_required": r.get("n_required"),
                "n_required_no_cc": r.get("n_required_no_continuity"),
                "p0": p0, "p1": p1, "alpha": alpha, "beta": beta,
                "delta": delta,
                "authority": ("NIST/SEMATECH e-Handbook 7.2.4.2, "
                              "https://www.itl.nist.gov/div898/handbook/"
                              "prc/section2/prc242.htm")}
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable",
                "reason": f"{type(exc).__name__}: {str(exc)[:120]}"}


def nist_sample_size_table() -> List[Dict[str, Any]]:
    """The NIST sample sizes for a grid of claims, for reference.

    Included because the cited criteria carry a TABLE of required
    sample sizes: the same 55%-vs-50% claim needs 637 bets, but a
    60%-vs-50% claim needs far fewer, so the bar depends on the claim.
    """
    rows = []
    for p1 in (0.55, 0.60, 0.65):
        for delta in (0.02, 0.05, 0.10):
            r = n_required_independent_bets(p1=p1, delta=delta)
            if r.get("n_required"):
                rows.append({"p0": 0.50, "p1": p1, "delta": delta,
                             "n_required": r["n_required"],
                             "alpha": 0.05, "beta": 0.20})
    return rows

def evaluate_edge(trades: Sequence[Dict[str, Any]],
                  trials_scanned: Optional[int] = None,
                  choices: Optional[Dict[str, Any]] = None,
                  periods: Optional[Sequence[Dict[str, Any]]] = None,
                  context: Optional[Dict[str, Any]] = None
                  ) -> Dict[str, Any]:
    """Judge a wallet's edge. Returns the metrics, the fluke tests, and a
    verdict that is CONSISTENT / WEAK / FLUKE / INSUFFICIENT.

    `trades` items: {ts, token_address, symbol, side, amount, price_usd,
    realised_pnl_usd}
    `trials_scanned` is how many candidate wallets were screened before
    this one was picked - it is the N in the Deflated Sharpe. Passing the
    number you actually scanned matters: scanning 500 wallets and taking
    the best needs a much higher bar than scanning 5.
    `periods` is an optional list of {period, return_pct} for the
    consistency ratio.

    `context` carries SCAN-LEVEL facts the per-wallet data cannot
    supply:
        universe_survivorship_selected (bool) - the pool omitted
            wallets that were admitted and later decayed, or the screen
            universe was not published. This REJECTS.
        first_onchain_activity_ts (int) - the wallet's first observed
            activity. A performance row dated earlier is BACKFILLED and
            REJECTS.
        chains_observed (int) - how many chains the wallet was seen on.
        vendor_labels (dict) - e.g. {"gmgn": "smart money"}. CONTEXT
            ONLY: a vendor label is never a standard and never changes
            the verdict.

    **It defaults to None, which means UNKNOWN, and an unknown N is an
    AUTOMATIC REJECT** of the selection-bias test. The cited criterion
    reads: "reject if DSR < 0.95, or PBO > 0.05, or N (number of wallets
    screened) is not recorded". A caller that forgets to state how many
    candidates it screened is asserting the least evidenced case - that
    it screened one - so the gate refuses rather than passes it.
    """
    ch = dict(ANALYST_CHOICES)
    if choices:
        ch.update(choices)

    closed = [t for t in trades if t.get("realised_pnl_usd") is not None]
    # The RAW closed-trade count and the RAW PnL series. Both are kept
    # under names that say which is which: `n_closed` used to be
    # overwritten with the BET count further down, and the raw series
    # was then sliced with that bet count as the index - which is how
    # the decay test ended up splitting the wrong list.
    n_closed_trades_raw = len(closed)
    raw_pnls = [float(t.get("realised_pnl_usd") or 0) for t in closed]
    total_pnl_raw = sum(raw_pnls)

    # ---- the INDEPENDENT BET structure ------------------------------
    # Wins, losses, the win rate and every statistical test use the
    # BET outcomes. Using raw closed trades as the sample would let a
    # wallet that scaled in 40 times inflate its own confidence.
    bo = bet_outcomes(trades)
    wins = bo["wins"]
    losses = bo["losses"]
    n_closed = bo["n_closed_bets"]      # CLOSED BETS
    total_pnl = bo["total_pnl"]
    bet_pnls = [b["pnl"] for b in bo["effective"]]

    ib = independent_bets(trades)
    n_bets = ib["independent_bets"]
    distinct_tokens = ib["distinct_tokens"]

    # THE EFFECTIVE SAMPLE SIZE. The cited criteria are explicit: "N is
    # a count of INDEPENDENT Bernoulli trials, so the input must be the
    # count of NON-OVERLAPPING trades, not raw trades." Raw closed
    # trades are reported too, but the Wilson interval, the Bayesian
    # skill probability and the DSR's sqrt(T-1) term all use the
    # independent-bet count.
    #
    # Two independent-bet counts exist and the STRICTER is used:
    #   - non-overlapping positions WITHIN each asset
    #   - mutually non-overlapping holding intervals ACROSS assets
    #     (simultaneous memecoin positions share one risk factor)
    tdb = time_disjoint_bets(trades)
    # The comment above promised the STRICTER of the two counts, but
    # the code used the bet count alone. It now really is the
    # stricter: simultaneous positions in different assets share one
    # risk factor, so they are not independent observations.
    _n_bets_closed = bo["n_closed_bets"]
    _n_bets_disjoint = tdb.get("time_disjoint_bets")
    if _n_bets_disjoint is None:
        n_eff = _n_bets_closed
    else:
        n_eff = min(_n_bets_closed, _n_bets_disjoint)
    # Both counts are reported so the stricter one is auditable.
    n_bets_closed = _n_bets_closed
    n_bets_time_disjoint = _n_bets_disjoint

    # ---- skill probability -------------------------------------------
    # The BAYESIAN SKILL PROBABILITY, not the significance test.
    # These are different quantities; using the significance
    # test here overstated skill probability and made the gate
    # lenient. See stats.bayesian_skill_probability.
    skill_p = (bayesian_skill_probability(wins, n_eff)
                if n_eff else None)
    # Wilson interval for the win rate, so the reader sees the uncertainty
    # alongside the point estimate.
    from .traders import wilson_interval
    wi = wilson_interval(wins, n_eff) if n_eff else \
        {"status": "no_sample"}

    # ---- largest win share --------------------------------------------
    largest_win = max(bet_pnls) if bet_pnls else 0.0
    largest_win_share = (largest_win / total_pnl
                         if total_pnl > 0 and largest_win > 0 else None)

    # ---- returns series for risk ratios --------------------------------
    # The per-observation return series for Sharpe/Sortino/Calmar must
    # be the BET returns, on the same scale as the bet count used in the
    # DSR's sqrt(T-1) term. Mixing bet counts with per-trade returns is
    # the unit trap the Bailey-Lopez de Prado transcription warns about.
    rets = []
    for b in bo["effective"]:
        r = b.get("return_pct")
        if r is None:
            r = b.get("return_pct_derived")
        rets.append(float(r) if r is not None else 0.0)
    sharpe = sortino = calmar = None
    g3 = g4 = None
    if len(rets) >= 2:
        mean = sum(rets) / len(rets)
        sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / (len(rets) - 1))
        sharpe = (mean / sd) if sd > 0 else None
        downside = [min(0.0, r) for r in rets]
        dd = math.sqrt(sum(r * r for r in downside) / len(rets))
        sortino = (mean / dd) if dd > 0 else None
        n = len(rets)
        m3 = sum((r - mean) ** 3 for r in rets) / n
        m4 = sum((r - mean) ** 4 for r in rets) / n
        if sd > 0:
            g3 = m3 / (sd ** 3)
            g4 = m4 / (sd ** 4)
        peak = 0.0
        maxdd = 0.0
        eq = 0.0
        for r in rets:
            eq += r
            peak = max(peak, eq)
            maxdd = min(maxdd, eq - peak)
        calmar = ((mean * n) / abs(maxdd)) if maxdd < 0 else None

    # ---- Deflated Sharpe ------------------------------------------------
    dsr = None
    dsr_detail: Dict[str, Any] = {}
    n_trials_known = trials_scanned is not None and int(trials_scanned) >= 1
    if sharpe is not None and n_trials_known:
        N = max(1, int(trials_scanned))
        g3c = g3 if g3 is not None else 0.0
        g4c = g4 if g4 is not None else 3.0
        if n_closed > 1:
            # T is the EFFECTIVE sample size (independent bets), not
            # the raw trade count. The DSR itself lives in stats.py so
            # that edge.py, pbo.py and any future consumer cannot
            # drift apart on the formula.
            T_used = max(2, n_eff) if n_eff else n_closed
            dsr, dsr_detail = ST.deflated_sharpe_ratio(
                sharpe, T_used, N, g3c, g4c)

    # ---- consistency of periods ----------------------------------------
    consistency_ratio = None
    n_periods = 0
    if periods:
        vals = [float(p.get("return_pct") or 0.0) for p in periods]
        n_periods = len(vals)
        if n_periods:
            consistency_ratio = sum(1 for v in vals if v > 0) / n_periods

    # ---- edge decay ------------------------------------------------------
    decay = None
    # The decay test splits the BET series, not the raw closed-trade
    # series. It used to slice the raw list with a BET count as the
    # index, so with 179 raw trades and 4 bets the "recent" half held
    # 177 raw trades - and because the raw list is dominated by the
    # early bets' partial sells, the ratio read 0.90 where the bet
    # split reads 0.0025. That difference FLIPS the verdict.
    if len(bet_pnls) >= 4:
        half = len(bet_pnls) // 2
        early = bet_pnls[:half]
        recent = bet_pnls[half:]
        e_exp = sum(early) / len(early) if early else 0.0
        r_exp = sum(recent) / len(recent) if recent else 0.0
        decay = {
            "early_expectancy": round(e_exp, 4),
            "recent_expectancy": round(r_exp, 4),
            "ratio": (round(r_exp / e_exp, 4)
                      if e_exp not in (0, 0.0) and e_exp > 0 else None),
            "n_early": len(early), "n_recent": len(recent),
        }

    # ---- FLUKE TESTS -----------------------------------------------------
    # Each individual test lives in `gate_tests`, so it can be read,
    # reviewed and tested on its own. `evaluate_edge` computes the
    # inputs, runs the suite, and applies the verdict precedence.
    from .gate_tests import GateContext, run_gate_tests

    # `ctx` is the scan-level context. It was defined inside the
    # removed block and used again further down, so it is defined here
    # at the top of the section instead.
    ctx = context or {}

    n_periods_positive = sum(1 for p in (periods or [])
                              if float(p.get("return_pct") or 0) > 0)

    _gt = run_gate_tests(GateContext(
        thresholds=ch,
        wins=wins,
        losses=losses,
        n_closed=n_closed,
        n_bets=n_bets,
        n_eff=n_eff,
        distinct_tokens=distinct_tokens,
        largest_win_share=largest_win_share,
        skill_p=skill_p,
        dsr=dsr,
        dsr_detail=dsr_detail,
        n_trials_known=n_trials_known,
        trials_scanned=trials_scanned,
        decay=decay,
        n_return_observations=len(rets),
        n_periods=len(periods) if periods else 0,
        n_periods_positive=n_periods_positive,
        trades=trades,
        context=context or {},
        cited_criteria=CITED_CRITERIA,
    ))
    tests = _gt["tests"]
    rejects = [t for t in tests if t["failed"]]
    definitive = _gt["definitive"]
    insufficient = _gt["insufficient"]
    _pbo = _gt["pbo"]

    # ---- verdict ---------------------------------------------------------
    # A definitive rejection binds first: a wallet with one lucky win
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
    elif n_closed == 0:
        verdict = "INSUFFICIENT"
        reason = "no closed trades with a computable PnL"
    elif consistency_ratio is not None \
            and consistency_ratio < ch["min_consistency_ratio"]:
        verdict = "WEAK"
        reason = (f"only {round(consistency_ratio*100,1)}% of periods were "
                  f"positive (threshold {ch['min_consistency_ratio']})")
    else:
        verdict = "CONSISTENT"
        reason = ("edge survives the fluke tests at "
                  f"{trials_scanned} trial(s) scanned")

    return {
        "verdict": verdict,
        "reason": reason,
        "n_closed_trades": n_closed_trades_raw,
        "n_closed_bets": n_closed,
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / n_closed) if n_closed else None,
        "wilson_interval": wi,
        "bayesian_skill_p": skill_p,
        "bayesian_skill_meaning": (
            "P(true win rate > 50%) with a uniform Beta(1,1) prior, "
            "computed as sum_{k=0}^{w} C(n+1,k)/2^(n+1) and verified "
            "against numerical integration of the Beta posterior. "
            "This is NOT the null-hypothesis significance test "
            "P(X<=w) for Binomial(n, 0.5), which is a different "
            "quantity and overstates skill probability."),
        "total_realised_pnl_usd": round(total_pnl, 2),
        "largest_win_usd": round(largest_win, 2),
        "largest_win_share": largest_win_share,
        "independent_bets": ib,
        # ---- the STANDARD bar, reported beside the triage verdict -----
        "n_required_independent_bets": n_required_independent_bets(),
        "pbo": _pbo if "_pbo" in dir() else None,
        # Tests that were NOT EVALUATED. They did not fail, and they
        # did not pass either - reporting them as a pass would be a
        # false claim of coverage.
        "tests_not_evaluated": [t["test"] for t in tests
                                if t.get("severity") == "not_evaluated"],
        "nist_sample_size_table": nist_sample_size_table(),
        # ---- the metrics the cited criteria ask for -------------------
        "drawdown_duration": drawdown_duration(rets),
        "posterior_split_half_stability": posterior_split_half_stability(
            bo["effective"]),
        "n_periods_positive": n_periods_positive,
        "n_return_observations": len(rets),
        # ---- comparability caveats, reported not enforced -------------
        "chain_coverage_ceiling": {
            "chains_observed": ctx.get("chains_observed"),
            "note": ("Nansen's published coverage is the ceiling for "
                     "how far back a wallet's history can be checked. A "
                     "wallet observed on several chains has more "
                     "opportunities than a single-chain one, which is a "
                     "COMPARABILITY caveat, not a disqualification."),
            "authority": ("Nansen, API data coverage "
                          "(https://docs.nansen.ai/api/data-coverage.md)"),
        },
        "cross_chain_comparability_report": {
            "chains_observed": ctx.get("chains_observed"),
            "comparable": (ctx.get("chains_observed") or 1) == 1,
            "note": ("A wallet seen on more than one chain has a "
                     "different opportunity set from a single-chain "
                     "wallet, so its win rate is not directly comparable "
                     "without saying so."),
            "authority": ("Nansen, API data coverage "
                          "(https://docs.nansen.ai/api/data-coverage.md)"),
        },
        # ---- VENDOR CONTEXT. NEVER a verdict input. -------------------
        "vendor_context": {
            "win_rate_band": {
                "threshold": 0.60,
                "label": "GMGN 'strong' smart-money win-rate band",
                "authority": ("GMGN smart-money profile (commercial "
                              "on-chain analytics CONVENTION, not a "
                              "professional standard)"),
                "url": ("https://raw.githubusercontent.com/GMGNAI/"
                        "gmgn-skills/main/skills/smart-money/"
                        "workflow-smart-money-profile.md"),
                "this_wallet_win_rate": (bo.get("win_rate")
                                         if bo else None),
                "clears_band": bool(bo and bo.get("win_rate")
                                    and bo["win_rate"] > 0.60),
            },
            "pnl_ratio": {
                "threshold": 1.0,
                "label": "GMGN profit-ratio band",
                "authority": ("GMGN wallet analysis (commercial on-chain "
                              "analytics CONVENTION)"),
                "url": ("https://raw.githubusercontent.com/GMGNAI/"
                        "gmgn-skills/main/skills/wallet-analysis/"
                        "workflow-wallet-analysis.md"),
                "note": ("The profit ratio is gross proceeds over gross "
                         "cost. This package reports realised PnL, not "
                         "the ratio, so the band is reported for context "
                         "and is NOT computed."),
            },
            "vendor_labels": ctx.get("vendor_labels") or {},
            "rule": ("A vendor label is CONTEXT, never a standard. It "
                     "does not change the cited verdict and must never "
                     "be presented as one."),
            "authority": ("Nansen smart-money label "
                          "(https://docs.nansen.ai/api/smart-money); "
                          "GMGN - both are commercial labels"),
        },
        "bet_outcomes": {
            "n_bets_total": bo["n_bets"],
            "n_closed_bets": bo["n_closed_bets"],
            "wins_over_bets": bo["wins"],
            "losses_over_bets": bo["losses"],
            "win_rate_over_bets": bo["win_rate"],
            # The per-bet return series. This is what the scan layer
            # feeds to the PBO, which needs one return per OBSERVATION
            # per candidate on a common scale.
            "bet_returns": [b.get("return_pct")
                            for b in bo["effective"]
                            if b.get("return_pct") is not None],
            "note": bo["note"],
        },
        "time_disjoint_bets": tdb["time_disjoint_bets"],
        "effective_sample_size": n_eff,
        "trials_scanned_known": n_trials_known,
        "sharpe_per_trade": sharpe,
        "sortino_per_trade": sortino,
        "calmar": calmar,
        "deflated_sharpe": dsr,
        "deflated_sharpe_detail": dsr_detail,
        "consistency_ratio": consistency_ratio,
        "n_periods": n_periods,
        "edge_decay": decay,
        "fluke_tests": tests,
        "rejected_by": rejects,
        "definitive_rejections": definitive,
        "insufficiencies": insufficient,
        "thresholds": ch,
        "threshold_label": "ANALYST_CHOICE unless the test cites a source",
        "cited_criteria": CITED_CRITERIA,
        "trials_scanned": trials_scanned,
        "trials_note": (
            "The number of candidate wallets screened BEFORE this one was "
            "chosen. It enters the Deflated Sharpe, so scanning 500 wallets "
            "and keeping the best sets a far higher bar than scanning 5. "
            "Under-reporting it inflates the verdict."),
    }


def screen_universe(candidates: Sequence[Dict[str, Any]],
                    trials_scanned: Optional[int] = None,
                    choices: Optional[Dict[str, Any]] = None,
                    periods_by_candidate: Optional[Dict[str, Any]] = None
                    ) -> Dict[str, Any]:
    """Screen a WHOLE universe of candidates and compute the PBO over it.

    This is the only place the Probability of Backtest Overfitting can
    be run correctly, because PBO needs the candidate matrix, not one
    wallet.

    `candidates` is a list of dicts, each with "address" and "trades"
    (the trade list `evaluate_edge` accepts). The per-candidate return
    series is derived from each candidate's closed bets.

    Returns the per-wallet verdicts plus the PBO over the universe.
    """
    verdicts = []
    series = []
    for c in candidates:
        trades = c.get("trades") or []
        v = evaluate_edge(trades, trials_scanned=trials_scanned,
                          choices=choices)
        verdicts.append({"address": c.get("address"),
                          "verdict": v.get("verdict"),
                          "reason": v.get("reason"),
                          "n_closed_trades": v.get("n_closed_trades"),
                          "n_bets_closed": (v.get("bet_outcomes") or {}
                                            ).get("n_closed_bets"),
                          "total_realised_pnl_usd": v.get(
                              "total_realised_pnl_usd"),
                          "edge": v})
        rets = [float(r) for r in
                ((v.get("bet_outcomes") or {}).get("bet_returns") or [])]
        series.append(rets)

    pbo = None
    try:
        from .pbo import probability_of_backtest_overfitting
        usable = [s for s in series if len(s) >= 4]
        if len(usable) >= 2:
            pbo = probability_of_backtest_overfitting(usable)
        else:
            pbo = {"status": "insufficient",
                    "reason": ("PBO needs at least two candidates with "
                               "4+ observations each")}
    except Exception as exc:  # noqa: BLE001
        pbo = {"status": "error",
               "reason": f"{type(exc).__name__}: {str(exc)[:120]}"}

    from collections import Counter
    dist = dict(Counter(v["verdict"] for v in verdicts))
    return {
        "status": "ok",
        "n_candidates": len(candidates),
        "n_screened": len(verdicts),
        "verdict_distribution": dist,
        "trials_scanned": trials_scanned,
        "pbo": pbo,
        "verdicts": verdicts,
        "note": ("PBO is the direct test of 'is this the best of many, or "
                 "genuinely good'. It requires the full screened "
                 "universe, which is why it lives at the scan layer and "
                 "not inside a single wallet's verdict."),
    }
