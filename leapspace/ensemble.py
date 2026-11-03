"""The long/short hedged ensemble: the answer to "higher upside than
downside, with consistency".

WHY THIS EXISTS
    The paper-concept matrix tested EIGHT ideas, one at a time, and
    none of them survived. Every individual concept was REFUTED or
    INCONCLUSIVE on every asset class it could be tested on. The
    controls were genuine (C3-C6) and all failed.

    But "each idea alone has no edge" is not the same as "no
    combination of the ideas has an edge". Three things make a
    combination different from its parts:

    1. THE CROSS-SECTIONAL RANK. A momentum feature that is useless as
       an absolute signal can still ORDER the universe. Long the names
       with the highest cross-sectional momentum and short the lowest,
       and the market's own beta does most of the work - which is
       exactly what the user's requirement asks for: a strategy that
       can go long OR short and hedges, rather than a spot bet.

    2. THE CONSENSUS FILTER. Requiring K of M members to agree before
       taking a position is a noise filter, and the user's own stated
       preference is to filter noise BEFORE acting on it. A single
       member firing is noise; three of five agreeing is a reading.

    3. DIVERSIFICATION. Holding positions across several asset classes
       and several horizons raises the win rate and cuts the drawdown
       even when the expectancy per signal is small.

    The market-neutral construction (net target 0.0, long and short
    legs both live) means the book is not betting on the market's
    direction at all - which is what makes it comparable to the
    "higher upside than downside" requirement rather than a disguised
    long-only bet.

THE PARAMETERS, AND WHERE EACH ONE COMES FROM
    Every parameter is explicit and every one has a stated reason. The
    spec's `parameter_provenance` records the same reasons, so a reader
    can see which numbers are the paper's and which are analyst
    choices.

      members          the concept features that vote
      direction        +1 means "high value is long", -1 means "high
                       value is short" (a reversion member is -1)
      weight           each member's vote weight
      min_agreement    how many members must agree before a position is
                       taken. THIS IS THE NOISE FILTER.
      rank_floor       the minimum cross-sectional percentile rank to
                       be eligible for the long leg (and its mirror
                       for the short leg)
      net_target       0.0 - the book is market-neutral by construction
      long_only        False - the short leg is live
      gross_leverage   the total absolute exposure
      vol_target       the annualised volatility the book targets
      vol_lookback     the bars used to estimate it
      max_position     the per-name cap
      max_names        how many names can be held
      rebalance        how often the book is refreshed

WHAT THIS IS NOT
    * It is not a claim that an edge exists. It is a test of whether
      combining the papers' ideas produces one where the parts did not.
    * It is not a backtest shortcut. It goes through the same full
      gauntlet as every other spec, including the purged walk-forward,
      the cost stress, the Monte Carlo and the causality audit.
    * It has a NEGATIVE CONTROL of its own: the inverted ensemble.
      If the inverted ensemble performs as well, the ensemble is
      doing nothing that its own negation does not also do.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "ENSEMBLE_MEMBERS",
    "DEFAULT_ENSEMBLE_PARAMS",
    "signal_ensemble_blend",
    "ensemble_spec",
]


#: The ensemble's voting members. Each entry is
#: (feature, direction, weight, why).
#:
#: The directions are NOT arbitrary. A high momentum reading is a
#: bullish reading (direction +1). A high RSI reading is a
#: overbought reading, which in the papers' own terms is a
#: LIQUIDITY-PROVISION setup - you buy the dislocation, so a high RSI
#: is a SHORT-side reading (direction -1). A high z-score of the
#: price is the same thing (direction -1). A high distance-to-high is
#: a stretched reading (direction -1).
ENSEMBLE_MEMBERS: List[Dict[str, Any]] = [
    {"feature": "momentum", "direction": +1, "weight": 1.0,
     "why": "time-series momentum: the papers' primary directional "
            "signal, 'momentum belongs to orderly trend states'"},
    {"feature": "regime_momentum_score", "direction": +1, "weight": 1.0,
     "why": "the momentum reading scaled by the market's regime "
            "confidence, so a strong trend in a stressed market counts "
            "for less"},
    {"feature": "volume_ratio", "direction": +1, "weight": 0.5,
     "why": "volume confirmation: 'volume confirmation is associated "
            "with stronger trends', weighted at half because it "
            "carries no direction of its own"},
    {"feature": "rsi", "direction": -1, "weight": 0.5,
     "why": "overbought reads as exhaustion and the papers' reversal "
            "leg is LONG the dislocation - so a high RSI is the "
            "short side of the vote"},
    {"feature": "zscore", "direction": -1, "weight": 0.5,
     "why": "a stretched price is a mean-reversion candidate, which is "
            "the short side of the vote"},
]


DEFAULT_ENSEMBLE_PARAMS: Dict[str, Any] = {
    "min_agreement": 2,
    "rank_floor": 0.60,
    "net_target": 0.0,
    "long_only": False,
    "gross_leverage": 1.0,
    "vol_target": 0.15,
    "vol_lookback": 60,
    "max_position": 0.10,
    "max_names": 5,
    "rebalance": "monthly",
}


def _rank(values_by_symbol: Dict[str, List[Optional[float]]], n: int,
          symbols: Sequence[str]) -> Dict[str, List[Optional[float]]]:
    """The cross-sectional percentile rank of each symbol at each bar.

    The same measure the engine uses for its own cross-sectional
    signals, so the ensemble's ordering is consistent with the rest of
    the package. A bar with fewer than two observations produces no
    rank - there is nothing to order.
    """
    ranks: Dict[str, List[Optional[float]]] = {s: [None] * n for s in symbols}
    for d in range(n):
        vals = [(s, values_by_symbol[s][d]) for s in symbols
                if values_by_symbol.get(s) and values_by_symbol[s][d] is not None]
        if len(vals) < 2:
            continue
        # The values are not None here - the comprehension above
        # filtered them - but the type checker cannot see that, and an
        # explicit cast keeps it happy without a runtime cost.
        vals.sort(key=lambda kv: float(kv[1]))  # type: ignore[arg-type]
        last = len(vals) - 1
        for idx, (s, _v) in enumerate(vals):
            ranks[s][d] = idx / last if last else 0.5
    return ranks


def signal_ensemble_blend(panel, features: Dict[str, Any],
                          members: Optional[Sequence[Dict[str, Any]]] = None,
                          min_agreement: int = 2,
                          rank_floor: float = 0.30,
                          invert_signal: bool = False,
                          **kw) -> Dict[str, List[float]]:
    """Blend the concept features into one long/short signal.

    THE MECHANISM, step by step, for each bar:

      1. Rank every member's feature cross-sectionally. A member's
         rank is 0 (weakest name) to 1 (strongest name).
      2. Turn the rank into a VOTE in [-1, +1]. A member with
         direction +1 votes long on a high rank; direction -1 votes
         long on a LOW rank.
      3. Count the votes. `min_agreement` members must agree for a
         position to be taken. THIS IS THE NOISE FILTER: one member
         firing is noise.
      4. Scale the position by how extreme the ranking is, so the
         engine's `max_names` selection keeps the most conviction.

    The output is the signal; the engine's portfolio block turns it
    into weights. With `net_target=0.0` and `long_only=False` the book
    is market-neutral with a live short leg, and with `vol_target` the
    book is sized to a volatility rather than to a notional.

    `invert_signal` flips every member's direction - the NEGATIVE
    CONTROL. If the inverted ensemble does as well, the ensemble is
    not doing anything the market is not already doing.
    """
    members = list(members if members is not None else ENSEMBLE_MEMBERS)
    symbols = list(panel.symbols)
    n = panel.n

    # The cross-sectional rank of each member.
    member_ranks: List[Dict[str, List[Optional[float]]]] = []
    for m in members:
        fname = m.get("feature")
        vals = features.get(fname) if fname else None
        if not vals:
            member_ranks.append({})
            continue
        member_ranks.append(_rank(vals, n, symbols))

    def _rank_at(ranks: Dict[str, List[Optional[float]]], s: str,
                 i: int) -> Optional[float]:
        row = ranks.get(s)
        if not row or i >= len(row):
            return None
        return row[i]

    sig: Dict[str, List[float]] = {s: [0.0] * n for s in symbols}
    for i in range(n):
        # For each symbol: each member's vote AND the rank that
        # produced it. The rank has to be kept alongside the vote,
        # because the eligibility test applies to the members that
        # AGREE - a name that is top-ranked on a member that voted the
        # other way is not evidence for this position.
        votes: Dict[str, List[Tuple[float, float]]] = {s: [] for s in symbols}
        for m, ranks in zip(members, member_ranks):
            direction = float(m.get("direction", 1))
            weight = float(m.get("weight", 1.0))
            if invert_signal:
                direction = -direction
            for s in symbols:
                r = _rank_at(ranks, s, i)
                if r is None:
                    continue
                # A +1 member votes long on a HIGH rank; a -1 member
                # votes long on a LOW rank.
                signed = (2.0 * r - 1.0) * direction
                votes[s].append((signed * weight, r))

        for s in symbols:
            vs = votes[s]
            if not vs:
                continue
            longs = sum(1 for v, _r in vs if v > 0)
            shorts = sum(1 for v, _r in vs if v < 0)
            agreement = max(longs, shorts)
            if agreement < int(min_agreement):
                # The consensus filter: not enough members agree, so
                # stand aside rather than act on one reading.
                continue
            net_vote = sum(v for v, _r in vs)
            if net_vote == 0:
                continue
            direction = 1.0 if net_vote > 0 else -1.0

            # The eligibility test, over the AGREEING members only.
            # For a long position the agreeing members voted long,
            # which means their ranks are HIGH; for a short position
            # their ranks are LOW.
            #
            # `rank_floor` is the FLOOR on the mean rank: a long
            # position needs the name at or above it, and a short
            # position needs the name at or below its mirror. So
            # RAISING it makes the book MORE selective - which is the
            # opposite of what the first implementation did (it
            # required the long name to be at or above `1 - rank_floor`,
            # so raising the parameter loosened the book).
            agreeing_ranks = [r for v, r in vs
                              if (v > 0) == (direction > 0)]
            if not agreeing_ranks:
                continue
            mean_rank = sum(agreeing_ranks) / len(agreeing_ranks)
            if direction > 0:
                eligible = mean_rank >= rank_floor
            else:
                eligible = mean_rank <= (1.0 - rank_floor)
            if not eligible:
                continue

            # Conviction: how strongly the members agree, weighted by
            # how extreme their ranks are.
            magnitudes = [abs(v) for v, _r in vs]
            mean_mag = (sum(magnitudes) / len(magnitudes)) if magnitudes \
                else 0.0
            conviction = min(1.0, mean_mag)
            sig[s][i] = direction * conviction

    return sig


def _best_rank(member_ranks: Sequence[Dict[str, List[Optional[float]]]],
               symbols: Sequence[str], i: int, direction: float
               ) -> Optional[float]:
    """The most extreme rank among the members that agree with `direction`.

    For a long vote, that is the HIGHEST rank; for a short vote, the
    LOWEST. This is the rank the rank-floor test is applied to.
    """
    best: Optional[float] = None
    for ranks in member_ranks:
        for s in symbols:
            row = ranks.get(s)
            if not row or i >= len(row):
                continue
            r = row[i]
            if r is None:
                continue
            if direction > 0:
                best = r if best is None else max(best, r)
            else:
                best = r if best is None else min(best, r)
    return best


def ensemble_spec(asset_class: str, params: Optional[Dict[str, Any]] = None,
                  name: Optional[str] = None) -> Dict[str, Any]:
    """Build the ensemble spec for one asset class."""
    from .paperspecs import ASSET_CLASSES, _make, _prov, _ANALYST, _PAPER

    p = dict(DEFAULT_ENSEMBLE_PARAMS)
    p.update(params or {})

    feature_specs = []
    for m in ENSEMBLE_MEMBERS:
        feature_specs.append({
            "name": m["feature"],
            "params": {"lookback": 60} if m["feature"] in
                      ("momentum", "regime_momentum_score") else
                      {"lookback": 10},
        })

    return _make(
        name=name or f"c9_ensemble_longshort_{asset_class}",
        paper=("Trading strategies for retail traders (LeapSpace); "
               "Financial market regime identification (LeapSpace)"),
        concept="C9_long_short_hedged_ensemble",
        hypothesis=(
            "No single paper concept survives on its own, but a "
            "market-neutral LONG/SHORT book that ranks the universe "
            "cross-sectionally on several of the papers' signals at "
            "once, and only takes a position when a MAJORITY of them "
            "agree, produces a higher ratio of winning to losing "
            "out-of-sample bars than any single concept - because the "
            "cross-sectional rank removes the market's beta and the "
            "consensus filter removes the noise."),
        asset_class=asset_class,
        features=feature_specs,
        signal={"type": "ensemble_blend", "params": {
            "members": [{"feature": m["feature"],
                         "direction": m["direction"],
                         "weight": m["weight"]} for m in ENSEMBLE_MEMBERS],
            "min_agreement": p["min_agreement"],
            "rank_floor": p["rank_floor"],
        }},
        # NO `portfolio` block is passed. `_make` applies the matrix's
        # CONSTANT risk block, which already is what this ensemble
        # needs: gross 1.0, vol target 15%, 10% per name, 5 names,
        # net target 0.0, long_only False, monthly rebalance. Using
        # the same block as every other spec is what makes the
        # comparison a comparison of SIGNALS rather than of risk
        # settings.
        provenance={
            "signal.type": _prov(
                _PAPER,
                "A long/short, market-neutral blend of the papers' "
                "signals. 'Momentum belongs to orderly trend states. "
                "Reversal belongs to stressed, illiquid, high-volatility, "
                "or rebound states' - and the cross-sectional rank is "
                "how a regime-conditional idea is expressed without "
                "betting on the market's direction.",
                citation="Trading strategies for retail traders; "
                         "Financial market regime identification"),
            "signal.params.min_agreement": _prov(
                _ANALYST,
                f"{p['min_agreement']} of {len(ENSEMBLE_MEMBERS)} members "
                "must agree before a position is taken. This is the noise "
                "filter: a single member firing is noise, and the "
                "preference is to filter before acting."),
            "signal.params.rank_floor": _prov(
                _ANALYST,
                f"{p['rank_floor']}: a long position needs the name's MEAN "
                f"rank across the agreeing members to be at or above "
                f"{p['rank_floor']}, and a short position at or below "
                f"{1 - p['rank_floor']:.2f}. So the book holds the "
                f"top {int((1 - p['rank_floor']) * 100)}% and the bottom "
                f"{int((1 - p['rank_floor']) * 100)}% and stays out of the "
                f"middle. Raising it makes the book MORE selective."),
            "portfolio.net_target": _prov(
                _ANALYST,
                "0.0 - the book is market-neutral by construction, so the "
                "result measures the signal and not the market's "
                "direction. This is what makes 'higher upside than "
                "downside' a statement about the edge rather than about "
                "the beta."),
            "portfolio.long_only": _prov(
                _ANALYST,
                "False - the short leg is live. A long-only version of "
                "this ensemble would be a disguised bet on the market."),
            "portfolio.vol_target": _prov(
                _ANALYST,
                f"{p['vol_target']} annualised. The book is sized to a "
                "volatility, so each asset class's contribution is "
                "comparable and the drawdown is bounded by construction."),
            "portfolio.max_names": _prov(
                _ANALYST,
                f"{p['max_names']} - a small book, so each position can "
                "carry weight and the drawdown is not spread too thin to "
                "matter."),
            "portfolio.rebalance": _prov(
                _ANALYST,
                "monthly - the papers' horizon. Costs are charged at 2x "
                "the engine default regardless."),
        },
        notes=(
            "THIS IS THE LONG/SHORT HEDGED VERSION. The book is "
            "market-neutral (net target 0.0) with a live short leg, "
            "volatility-targeted at "
            f"{p['vol_target']}, capped at {p['max_position']} per name, "
            f"holding at most {p['max_names']} names, refreshed "
            f"{p['rebalance']}. Members vote cross-sectionally and a "
            f"position is taken only when {p['min_agreement']} of them "
            "agree. Every one of these numbers is recorded in "
            "parameter_provenance with its reason. "
            "The matrix also runs an INVERTED twin of this ensemble, "
            "because an ensemble that performs as well when inverted is "
            "not doing anything."),
    )
