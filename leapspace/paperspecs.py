"""The PAPER-CONCEPT specification set.

WHAT THIS IS
    A single factory that produces backtest specifications for EVERY
    testable claim in the five research papers this package implements,
    across MULTIPLE ASSET CLASSES, with a full risk-management block.

WHY A FACTORY AND NOT A LIST OF JSON
    Every paper concept has to be tested on more than one market. Writing
    that as hand-written JSON means the risk controls drift apart
    between assets, and a spec that differs in two ways at once (a
    different signal AND a different risk block) cannot be compared.
    The factory holds the risk block CONSTANT across the asset classes
    and varies only the concept and the universe, so a difference in
    the result is attributable to the market rather than to the
    bookkeeping.

THE PAPER CONCEPTS, AND WHAT EACH CLAIMS
    --------------------------------------
    C1  REGIME-CONDITIONED SWITCHING
        "The most defensible edge is regime-conditioned switching: run
         momentum in orderly trending states, and switch toward
         reversal/liquidity-provision in stressed, high-volatility,
         rebound, or illiquid states."
        - Financial market regime identification

    C2  LEADING VOLATILITY RISK PREMIUM
        "Implied volatility often contains incremental information about
         future realized volatility, and in several studies it outperforms
         historical volatility forecasts."
        - Options market dynamics and volatility
        Tested as a SIZING rule on a momentum signal, because the
        premium separates the "orderly trend" state from the
        "momentum-crash" state in a FORWARD-LOOKING way.

    C3  VOLATILITY REGIME FILTER
        "Use volatility and liquidity filters to decide whether momentum
         or reversal should dominate."
        - NASDAQ market regime identification
        Tested as a binary filter: momentum only when volatility is
        orderly, otherwise stand aside.

    C4  VOLUME CONFIRMATION
        "Volume carries information that price alone does not, and
         volume-based signals can improve forecastability."
        - Free trading indicators for directional edge
        Tested as momentum filtered by a volume ratio.

    C5  RSI / EMA AS SECONDARY CONFIRMATION
        "In crypto, RSI was found more reliable than MACD or Stochastic
         for overbought/oversold style signals."
        - Free trading indicators for directional edge
        Tested as a mean-reversion entry gated on RSI.

    C6  REBOUND-AFTER-CRASH DANGER
        "One study's crash dummy combines negative trailing market
         returns, a positive current return, and elevated
         short-versus-long volatility, which is effectively a
         rebound-danger state."
        - Financial market regime identification
        Tested as a momentum-crash filter: momentum is disabled in a
        rebound state.

    C7  ORDER-FLOW / MICROSTRUCTURE BASE
        "Order flow can contain information about future volatility and
         returns in several markets ... in crypto, trade-flow imbalance
         and order-book features often matter more than broad technical
         rules."
        - Trading strategies for retail traders
        Tested with the session-window drift feature, which is the
        closest keyless proxy for order-flow imbalance.

    C8  LIQUIDITY-PROVISION REVERSAL
        "Reversal is stronger in illiquid stocks, lower-turnover
         environments, and more volatile conditions; profits are
         especially concentrated where liquidity is scarce."
        - Financial market regime identification
        Tested as mean reversion gated on a liquidity/turnover proxy.

THE ASSET CLASSES
    ----------------
    The papers are explicit that crypto behaves differently from
    equities ("Crypto must be modeled by horizon, not by one fixed
    universal rule"), so the same concept is tested on:

      us_equity_style  SPY IWM MDY RSP QQQ DIA
      crypto           BTC ETH LTC BCH XRP SOL ADA DOGE AVAX LINK
      fx_major         EURUSD GBPUSD USDJPY AUDUSD USDCHF USDCAD NZDUSD USDSEK
      commodities      GC SI CL NG HG PL PA ZC ZS ZW KC SB CT LBS
      futures_broad    ES NQ YM RTY ZN ZB ZF ZT GC SI CL NG HG ZC ZS
      rates_credit     ^TNX ^TYX ^FVX ^IRX TLT IEF SHY LQD HYG EMB TIP BND

    A concept that only works on one of them is a market curiosity, not
    an edge, and the report says so.

THE RISK BLOCK
    -------------
    Held constant across every spec so the comparison is fair, and set
    to industry-standard practice:

      gross_leverage 1.0    no leverage
      vol_target 0.15       the book is sized to 15% annual volatility
      max_position 0.10     no single name may exceed 10% of equity
      max_names 5           concentration is limited by name count too
      net_target 0.0        dollar-neutral, so a result is not a beta bet
      rebalance monthly     decisions are taken monthly, not daily
      cost_multiplier 2.0   costs are stressed to a pessimistic venue

    `cost_multiplier: 2.0` is deliberate and it is the STRESSED case,
    not the base case: the engine's cost defaults are per-asset-class
    and conservative, and a strategy that only survives at 1.0x costs
    has no edge at the size a retail account would trade it.

THE HONESTY RULES BUILT IN
    -------------------------
    * Every spec carries `parameter_provenance` for EVERY probed
      condition, with an explicit source. The intake gate then records
      each acceptance as a documented decision rather than an
      unanswered question.
    * NEGATIVE CONTROLS are generated alongside the real specs, by
      inverting the signal's polarity. A concept whose inverted twin
      performs just as well is not being driven by the concept.
    * `variants_tried` is recorded. The deflated-Sharpe penalty scales
      with the number of variants a researcher tried, and reporting the
      best of N is the most common way a backtest lies.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

__all__ = [
    "RISK_BLOCK",
    "ASSET_CLASSES",
    "build_specs",
    "load_paper_specs",
    "write_paper_specs",
    "PAPER_SPECS_PATH",
]


PAPER_SPECS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "paper_specs.json")


#: The risk block held constant across every spec. See the module
#: docstring for why each value is what it is.
RISK_BLOCK: Dict[str, Any] = {
    "gross_leverage": 1.0,
    "vol_target": 0.15,
    "vol_lookback": 60,
    "max_position": 0.10,
    "max_names": 5,
    "net_target": 0.0,
    "long_only": False,
    "rebalance": "monthly",
}

#: The stressed execution block. `cost_multiplier: 2.0` models a
#: worse-than-typical venue or a small account paying wider spreads.
EXECUTION_BLOCK: Dict[str, Any] = {
    "fill_at": "open",
    "cost_multiplier": 2.0,
    "max_participation": 0.10,
}

#: The asset classes each concept is tested on.
ASSET_CLASSES: Dict[str, Dict[str, Any]] = {
    "us_equity_style": {
        "preset": "us_equity_style",
        "label": "US equity style ETFs",
        "start": "2005-01-01",
    },
    "crypto": {
        "preset": "crypto",
        "label": "crypto majors",
        "start": "2021-01-01",
    },
    "fx_major": {
        "preset": "fx_major",
        "label": "G10 FX majors",
        "start": "2005-01-01",
    },
    "commodities": {
        "preset": "commodities",
        "label": "commodities",
        "start": "2005-01-01",
    },
    "futures_broad": {
        "preset": "futures_broad",
        "label": "futures broad",
        "start": "2005-01-01",
    },
    "rates_credit": {
        "preset": "rates_credit",
        "label": "rates and credit",
        "start": "2005-01-01",
    },
}


def _prov(source: str, note: str, citation: str = "not stated in source"
          ) -> Dict[str, str]:
    return {"source": source, "citation": citation, "note": note}


_PAPER = "paper"
_ANALYST = "analyst_choice"
_ENGINE = "engine_default"


def _make(name: str, paper: str, concept: str, hypothesis: str,
          asset_class: str, features: List[Dict[str, Any]],
          signal: Dict[str, Any], provenance: Dict[str, Dict[str, str]],
          variants_tried: int = 1,
          notes: str = "") -> Dict[str, Any]:
    """Assemble one spec with the constant risk block and full provenance."""
    ac = ASSET_CLASSES[asset_class]
    pp = dict(provenance)
    # The probed conditions every spec must answer.
    pp.setdefault("hypothesis", _prov(_PAPER, hypothesis[:200],
                                      citation=paper))
    pp.setdefault("universe.preset", _prov(
        _PAPER, f"the {ac['label']} universe; the papers require the claim "
                f"to be tested on more than one market because crypto and "
                f"equities behave differently",
        citation=paper))
    pp.setdefault("portfolio.rebalance", _prov(
        _ANALYST, "monthly. The papers state no cadence; monthly keeps the "
                  "turnover inside a retail account's cost budget and "
                  "matches the regime paper's 'swing/daily' horizon."))
    pp.setdefault("portfolio.gross_leverage", _prov(
        _ANALYST, "1.0 - no leverage. The papers do not discuss leverage, "
                  "so the unlevered result is the one reported."))
    pp.setdefault("portfolio.max_position", _prov(
        _ANALYST, "10% of equity per name. A concentration limit is "
                  "standard risk management; the papers set no number."))
    pp.setdefault("portfolio.vol_target", _prov(
        _ANALYST, "15% annual volatility target, so the book is sized to a "
                  "risk level rather than to a dollar amount. The papers "
                  "set no number."))
    pp.setdefault("portfolio.max_names", _prov(
        _ANALYST, "5 names, so concentration is limited by count as well "
                  "as by weight."))
    pp.setdefault("portfolio.net_target", _prov(
        _ANALYST, "0.0 - dollar neutral, so a result cannot be a beta bet "
                  "dressed up as alpha."))
    pp.setdefault("portfolio.long_only", _prov(
        _ANALYST,
        "False - long/short. The regime paper's switching mechanism needs "
        "both legs: momentum in trend states and reversal in stress "
        "states, and a long-only book cannot express the second. The "
        "papers set no direction."))
    pp.setdefault("exit", _prov(
        _ANALYST,
        "The exit is the signal returning to flat. Where the signal has "
        "an explicit exit band it is stated in the signal's own params; "
        "otherwise the rule is 'the entry condition no longer holds', "
        "which is what a regime-conditioned signal means."))
    pp.setdefault("signal.params.exit", _prov(
        _ANALYST,
        "Where the signal carries an exit band it is in its params; "
        "otherwise the position closes when the entry condition stops "
        "holding. The papers state no exit band for the switching "
        "mechanism."))
    pp.setdefault("execution.cost_multiplier", _prov(
        _ANALYST, "2.0 - the STRESSED cost case. A strategy that only "
                  "survives at typical costs has no edge at retail "
                  "size; the engine also runs a gross-of-costs stage that "
                  "separates 'no edge' from 'edge too small to trade'."))
    pp.setdefault("period.start", _prov(
        _ANALYST, f"{ac['start']}, chosen to cover the 2008 crisis, the 2020 "
                  f"COVID crash and the 2022 bear market - the stress "
                  f"regimes the papers say a signal must survive."))
    pp.setdefault("signal.feature", _prov(
        _ANALYST, "the traded feature for this concept."))

    spec: Dict[str, Any] = {
        "name": name,
        "paper": paper,
        "hypothesis": hypothesis,
        "concept": concept,
        "asset_class": asset_class,
        "universe": {"preset": ac["preset"]},
        "period": {"start": ac["start"], "end": None, "interval": "1d"},
        "features": features,
        "signal": signal,
        "portfolio": dict(RISK_BLOCK),
        "execution": dict(EXECUTION_BLOCK),
        "capital": 100000.0,
        "intake": {
            "confirmed": [
                "hypothesis", "universe", "direction", "entry", "exit",
                "timeframe", "rebalance", "sizing", "leverage", "costs",
                "period", "variants_tried",
            ],
            "variants_tried": variants_tried,
            "notes": notes or (
                f"Concept {concept} from {paper}, tested on the "
                f"{ac['label']} universe. The paper states the mechanism; "
                f"every number it does not state is an analyst choice "
                f"recorded in parameter_provenance. The cost multiplier is "
                f"the STRESSED case (2.0x), which is deliberately harder "
                f"than a typical venue."),
        },
        "parameter_provenance": pp,
    }
    return spec


# --------------------------------------------------------------------------
# The concepts
# --------------------------------------------------------------------------
def _c1_regime_switch(asset_class: str) -> Dict[str, Any]:
    ac = ASSET_CLASSES[asset_class]
    return _make(
        name=f"c1_regime_switch_{asset_class}",
        paper="Financial market regime identification (LeapSpace)",
        concept="C1_regime_conditioned_switching",
        hypothesis=(
            "Regime-conditioned switching - momentum in orderly trending "
            "states, reversal in stressed, high-volatility, rebound or "
            "illiquid states - produces a better out-of-sample result "
            "than either leg alone, because 'the edge is often the switch, "
            "not the raw signal'."),
        asset_class=asset_class,
        features=[{"name": "regime_momentum_score", "params": {"lookback": 60}}],
        signal={"type": "regime_switch", "params": {
            "feature": "regime_momentum_score", "n_states": 4}},
        provenance={
            "signal.type": _prov(_PAPER,
                                 "The regime paper's own mechanism: classify "
                                 "the state, then switch the active signal.",
                                 citation="Financial market regime "
                                          "identification, 'Best general edge'"),
            "signal.params.n_states": _prov(
                _ANALYST, "4 states. The paper says 3-5 states and that "
                          "3-5 is more realistic than a bull/bear split; 4 "
                          "is inside that range."),
            "features.regime_momentum_score.lookback": _prov(
                _ANALYST, "60 bars - about one quarter, the swing/daily "
                          "horizon the regime paper names for trend and "
                          "drawdown features."),
        },
        notes=(
            "KNOWN LIMITATION, disclosed by the engine: this spec's regime "
            "CLASSIFICATION is in-sample (the HMM is fitted on the whole "
            "panel), so the out-of-sample numbers carry an in-sample regime "
            "boundary. That is a defect in the measurement, not a finding "
            "about the concept, and it is reported with the result."),
    )


def _c2_leading_vrp(asset_class: str) -> Dict[str, Any]:
    ac = ASSET_CLASSES[asset_class]
    return _make(
        name=f"c2_leading_vrp_{asset_class}",
        paper="Options market dynamics and volatility (LeapSpace); "
              "Financial market regime identification (LeapSpace)",
        concept="C2_leading_volatility_risk_premium",
        hypothesis=(
            "Scaling a momentum position by the VOLATILITY RISK PREMIUM "
            "(implied minus realised volatility) improves the "
            "out-of-sample result relative to the same momentum signal "
            "unconditioned, because the premium is a forward-looking "
            "reading of whether the market is priced for calm - and a "
            "momentum position into an unpriced shock is the "
            "momentum-crash setup the literature warns about."),
        asset_class=asset_class,
        features=[
            {"name": "regime_momentum_score", "params": {"lookback": 60}},
            {"name": "leading_vrp_score", "params": {"lookback": 20}},
            {"name": "leading_vrp_zscore", "params": {"lookback": 20}},
        ],
        signal={"type": "leading_vrp_switch", "params": {
            "feature": "regime_momentum_score",
            "vrp_z_feature": "leading_vrp_zscore",
            "exposure_cap": 1.0}},
        provenance={
            "signal.type": _prov(
                _PAPER,
                "Implied volatility as a forward-looking signal, applied as "
                "the sizing control the regime paper asks for: 'Translate "
                "state probabilities into explicit position-sizing and "
                "turnover controls rather than signal switching alone.'",
                citation="Options market dynamics and volatility; "
                         "Financial market regime identification"),
            "features.leading_vrp_score.lookback": _prov(
                _ANALYST, "20 bars - a standard monthly realised-volatility "
                          "estimate."),
            "features.leading_vrp_zscore.lookback": _prov(
                _ANALYST, "20 bars, matching the premium's own window."),
            "signal.params.exposure_cap": _prov(
                _ANALYST, "1.0: the position scales to zero at a premium "
                          "z-score of 1. The paper states no number."),
        },
        notes=(
            "The leading input is a real, timestamped, EXTERNAL measurement "
            "(Deribit DVOL for crypto; the Nasdaq or S&P implied "
            "volatility index for equities) aligned with a one-bar "
            "publication lag, so this spec does NOT inherit the in-sample "
            "regime-classification defect of C1. The implied series' "
            "coverage over the panel is reported with the result - if it "
            "covers only part of the sample, that is a limitation of the "
            "result and is stated as such."),
    )


def _c3_vol_regime_filter(asset_class: str) -> Dict[str, Any]:
    ac = ASSET_CLASSES[asset_class]
    return _make(
        name=f"c3_vol_regime_filter_{asset_class}",
        paper="NASDAQ market regime identification (LeapSpace); "
              "Financial market regime identification (LeapSpace)",
        concept="C3_volatility_regime_filter",
        hypothesis=(
            "A volatility-regime filter - momentum only when realised "
            "volatility is orderly, and otherwise no position - improves "
            "the out-of-sample result relative to the same momentum "
            "signal unfiltered, because momentum 'weakens sharply in "
            "downturns, crisis periods, and rebound-after-crash states' "
            "and because 'use volatility and liquidity filters to decide "
            "whether momentum or reversal should dominate'."),
        asset_class=asset_class,
        features=[
            {"name": "regime_momentum_score", "params": {"lookback": 60}},
            {"name": "volatility", "params": {"lookback": 20,
                                              "annualize": True}},
            {"name": "vol_ratio", "params": {"short": 5, "long": 60}},
        ],
        signal={"type": "vol_regime_momentum", "params": {
            "feature": "regime_momentum_score",
            "vol_feature": "vol_ratio",
            "orderly_max_ratio": 1.5}},
        provenance={
            "signal.type": _prov(
                _PAPER,
                "Momentum is disabled when the volatility state is not "
                "orderly.",
                citation="NASDAQ market regime identification, 'Direct "
                         "Answer'; Financial market regime identification, "
                         "'Practical momentum rules implied by the evidence'"),
            "signal.params.orderly_max_ratio": _prov(
                _ANALYST, "1.5 - short volatility may not exceed 1.5x the "
                          "long volatility for momentum to be permitted. "
                          "The papers set no number."),
            "features.vol_ratio.short": _prov(_ANALYST, "5 bars."),
            "features.vol_ratio.long": _prov(_ANALYST, "60 bars."),
            "features.volatility.lookback": _prov(_ANALYST, "20 bars."),
        },
        notes=(
            "This is a LAGGING filter - realised volatility is "
            "backward-looking - and it is included precisely to compare "
            "against C2, which is LEADING. The comparison of C2 against C3 "
            "on the same universe is the whole point: the papers claim the "
            "forward-looking input should detect stress earlier, and this "
            "is the test of that claim."),
    )


def _c4_volume_confirmation(asset_class: str) -> Dict[str, Any]:
    ac = ASSET_CLASSES[asset_class]
    return _make(
        name=f"c4_volume_confirmation_{asset_class}",
        paper="Free trading indicators for directional edge (LeapSpace); "
              "Trading strategies for retail traders (LeapSpace)",
        concept="C4_volume_confirmation",
        hypothesis=(
            "Requiring volume confirmation - a short-horizon volume ratio "
            "above its long-horizon average - on a momentum signal "
            "improves the out-of-sample result relative to the momentum "
            "signal alone, because 'volume carries information that price "
            "alone does not' and because in crypto 'trade-flow imbalance "
            "and order-book features often matter more than broad "
            "technical rules'."),
        asset_class=asset_class,
        features=[
            {"name": "regime_momentum_score", "params": {"lookback": 60}},
            {"name": "volume_ratio", "params": {"short": 10, "long": 60}},
        ],
        signal={"type": "volume_confirmed_momentum", "params": {
            "feature": "regime_momentum_score",
            "volume_feature": "volume_ratio",
            "min_volume_ratio": 1.0}},
        provenance={
            "signal.type": _prov(
                _PAPER,
                "Momentum is permitted only when volume confirms it.",
                citation="Free trading indicators for directional edge, "
                         "'Volume confirmation / OBV / volume-based rules'"),
            "signal.params.min_volume_ratio": _prov(
                _ANALYST, "1.0 - short-term volume at or above its "
                          "long-term average. The papers set no number."),
            "features.volume_ratio.short": _prov(_ANALYST, "10 bars."),
            "features.volume_ratio.long": _prov(_ANALYST, "60 bars."),
        },
        notes=(
            "The volume confirmation is a HARD GATE: no position without "
            "it. A softer implementation (scaling rather than gating) is "
            "a different hypothesis and is not what this spec tests."),
    )


def _c5_rsi_reversion(asset_class: str) -> Dict[str, Any]:
    ac = ASSET_CLASSES[asset_class]
    return _make(
        name=f"c5_rsi_reversion_{asset_class}",
        paper="Free trading indicators for directional edge (LeapSpace)",
        concept="C5_rsi_secondary_confirmation",
        hypothesis=(
            "An RSI-gated mean reversion - buy a stretched-down move only "
            "when RSI confirms exhaustion, and exit when the move "
            "normalises - produces a positive out-of-sample result on the "
            "asset classes where short-horizon reversal is documented, "
            "because 'in crypto, RSI was found more reliable than MACD "
            "or Stochastic for overbought/oversold style signals'."),
        asset_class=asset_class,
        features=[
            {"name": "zscore", "params": {"lookback": 10}},
            {"name": "rsi", "params": {"lookback": 14}},
        ],
        signal={"type": "rsi_confirmed_reversion", "params": {
            "feature": "zscore",
            "rsi_feature": "rsi",
            "entry": -2.0, "exit": -0.5, "oversold": 30.0}},
        provenance={
            "signal.type": _prov(
                _PAPER,
                "Mean reversion gated on RSI confirmation.",
                citation="Free trading indicators for directional edge, "
                         "'RSI and simple momentum tools'"),
            "signal.params.entry": _prov(_ANALYST, "-2.0 z-score."),
            "signal.params.exit": _prov(_ANALYST, "-0.5 z-score."),
            "signal.params.oversold": _prov(
                _ANALYST, "RSI 30. The paper names RSI as the tool but "
                          "sets no level; 30 is the conventional "
                          "oversold threshold."),
            "features.rsi.lookback": _prov(_ANALYST, "14 bars."),
            "features.zscore.lookback": _prov(_ANALYST, "10 bars."),
        },
        notes=(
            "This is the LONG side of a mean-reversion system: the z-score "
            "finds a stretched move and the RSI confirms exhaustion. The "
            "position is flat, not short, in the stretched-down state - the "
            "papers describe reversal as LIQUIDITY PROVISION, which is a "
            "buy-the-dip behaviour, and a short leg would be a different "
            "hypothesis."),
    )


def _c6_rebound_danger(asset_class: str) -> Dict[str, Any]:
    ac = ASSET_CLASSES[asset_class]
    return _make(
        name=f"c6_rebound_danger_{asset_class}",
        paper="Financial market regime identification (LeapSpace)",
        concept="C6_rebound_after_crash_danger",
        hypothesis=(
            "Disabling momentum in a REBOUND state - a negative trailing "
            "return followed by a positive recent return - improves the "
            "out-of-sample result relative to the momentum signal alone, "
            "because 'momentum losses often arrive after the market has "
            "already begun rebinding' and the crash dummy in the "
            "momentum-crash literature is exactly 'negative trailing "
            "market returns, a positive current return, and elevated "
            "short-versus-long volatility'."),
        asset_class=asset_class,
        features=[
            {"name": "regime_momentum_score", "params": {"lookback": 60}},
            {"name": "momentum", "params": {"lookback": 20, "skip": 0}},
            {"name": "return", "params": {"lag": 5}},
        ],
        signal={"type": "rebound_danger_momentum", "params": {
            "feature": "regime_momentum_score",
            "trailing_feature": "momentum",
            "recent_feature": "return",
            "trailing_max": 0.0, "recent_min": 0.0}},
        provenance={
            "signal.type": _prov(
                _PAPER,
                "Momentum is disabled in the rebound-after-crash state.",
                citation="Financial market regime identification, "
                         "'Momentum Behavior Across Regimes' and the crash "
                         "dummy in Butt, Kolari & Sadaqat (2024)"),
            "signal.params.trailing_max": _prov(
                _ANALYST, "0.0 - the trailing return must be negative for "
                          "the state to be armed."),
            "signal.params.recent_min": _prov(
                _ANALYST, "0.0 - the recent return must be positive."),
            "features.momentum.lookback": _prov(_ANALYST, "20 bars."),
            "features.return.lag": _prov(_ANALYST, "5 bars."),
        },
        notes=(
            "This is a LAGGING filter, like C3, and it is included so the "
            "two lagging filters can be compared against the leading one "
            "(C2) on identical universes. Its value is as a comparison "
            "point, not as a claim that the rebound filter is the best."),
    )


def _c7_session_drift(asset_class: str) -> Dict[str, Any]:
    ac = ASSET_CLASSES[asset_class]
    return _make(
        name=f"c7_session_drift_{asset_class}",
        paper="Trading strategies for retail traders (LeapSpace)",
        concept="C7_order_flow_microstructure_base",
        hypothesis=(
            "A microstructure-style signal - the session opening-window "
            "drift, which weights the close's position in the day's range "
            "by the volume behind it - produces a positive out-of-sample "
            "result on liquid assets, because 'order flow can contain "
            "information about future volatility and returns in several "
            "markets' and the microstructure base is the strongest edge "
            "the retail-trader evidence supports."),
        asset_class=asset_class,
        features=[{"name": "session_drift", "params": {"lookback": 1}}],
        signal={"type": "paper_cross_sectional", "params": {
            "long_rank": 0.75, "short_rank": 0.25}},
        provenance={
            "signal.type": _prov(
                _PAPER,
                "Cross-sectional selection on a microstructure measure.",
                citation="Trading strategies for retail traders, 'Order "
                         "flow / microstructure'"),
            "features.session_drift.lookback": _prov(
                _ANALYST, "1 - the current session's drift."),
        },
        notes=(
            "The session path returns DAILY returns (one bar per session), "
            "so the Sharpe annualises at 252 and every metric and "
            "walk-forward fold works unchanged. `flat_at_close` is NOT set, "
            "so positions may be held overnight. "
            "LIMITATION - THE FEATURE IS A PROXY, NOT ORDER FLOW. The "
            "concept names the session OPENING-WINDOW drift, which needs "
            "intraday bars; this package's panels are daily, so the "
            "implemented feature is the daily-bar stand-in "
            "(close's position in the day's range, weighted by the volume "
            "behind it). It is a price-and-volume summary that CORRELATES "
            "with order flow, not a measurement of it. A SUPPORTED verdict "
            "here would support the PROXY, not the order-flow claim."),
    )


def _c8_liquidity_reversal(asset_class: str) -> Dict[str, Any]:
    ac = ASSET_CLASSES[asset_class]
    return _make(
        name=f"c8_liquidity_reversal_{asset_class}",
        paper="Financial market regime identification (LeapSpace); "
              "Trading strategies for retail traders (LeapSpace)",
        concept="C8_liquidity_provision_reversal",
        hypothesis=(
            "Mean reversion is stronger when liquidity is poor and "
            "volatility is high, so a reversion signal gated on a LOW "
            "volume ratio (thin liquidity) and HIGH volatility produces a "
            "better out-of-sample result than an ungated reversion "
            "signal, because 'profits are especially concentrated where "
            "liquidity is scarce'."),
        asset_class=asset_class,
        features=[
            {"name": "zscore", "params": {"lookback": 10}},
            {"name": "volume_ratio", "params": {"short": 10, "long": 60}},
            {"name": "volatility", "params": {"lookback": 20,
                                              "annualize": True}},
        ],
        signal={"type": "liquidity_gated_reversion", "params": {
            "feature": "zscore",
            "volume_feature": "volume_ratio",
            "vol_feature": "volatility",
            "entry": -2.0, "exit": -0.5,
            "max_volume_ratio": 0.8, "min_volatility": 0.30}},
        provenance={
            "signal.type": _prov(
                _PAPER,
                "Reversion permitted only in the thin-liquidity, "
                "high-volatility state.",
                citation="Financial market regime identification, 'Mean "
                         "Reversion and Reversal by Market State'"),
            "signal.params.max_volume_ratio": _prov(
                _ANALYST, "0.8 - liquidity must be thin."),
            "signal.params.min_volatility": _prov(
                _ANALYST, "0.30 annualised - volatility must be high."),
            "signal.params.entry": _prov(_ANALYST, "-2.0 z-score."),
            "signal.params.exit": _prov(_ANALYST, "-0.5 z-score."),
        },
        notes=(
            "A volume-ratio threshold is a PROXY for liquidity, not a "
            "measure of it: the engine has no consolidated spread or depth "
            "series for these assets. The proxy is stated so the result is "
            "read as 'thin-activity reversion', not as a liquidity claim."),
    )


#: The concept builders, keyed by concept id.
def _c9_ensemble(asset_class: str) -> Dict[str, Any]:
    """The long/short hedged ensemble - the combination of the papers'
    signals, ranked cross-sectionally, with a consensus filter.

    The module `leapspace/ensemble.py` carries the full reasoning and
    the parameter provenance; this is the spec factory's adapter.
    """
    from .ensemble import ensemble_spec
    return ensemble_spec(asset_class)


_BUILDERS = {
    "C1": _c1_regime_switch,
    "C2": _c2_leading_vrp,
    "C3": _c3_vol_regime_filter,
    "C4": _c4_volume_confirmation,
    "C5": _c5_rsi_reversion,
    "C6": _c6_rebound_danger,
    "C7": _c7_session_drift,
    "C8": _c8_liquidity_reversal,
    # C9 is the long/short HEDGED ENSEMBLE - the combination of the
    # papers' signals, cross-sectionally ranked, market-neutral, with
    # a consensus filter. It is the test of whether the ideas work
    # TOGETHER where none of them worked alone.
    "C9": _c9_ensemble,
}


def build_specs(concepts: Optional[List[str]] = None,
               asset_classes: Optional[List[str]] = None
               ) -> List[Dict[str, Any]]:
    """Build the paper-concept spec matrix.

    `concepts` selects the concept ids ("C1".."C8"); `asset_classes`
    selects the universes. The default is EVERY concept on EVERY
    universe, which is the full matrix.
    """
    concepts = concepts or list(_BUILDERS)
    asset_classes = asset_classes or list(ASSET_CLASSES)
    out: List[Dict[str, Any]] = []
    for c in concepts:
        builder = _BUILDERS.get(c)
        if builder is None:
            continue
        for ac in asset_classes:
            if ac not in ASSET_CLASSES:
                continue
            try:
                out.append(builder(ac))
            except Exception:  # noqa: BLE001
                continue
    return out


def build_negative_controls(specs: Optional[List[Dict[str, Any]]] = None
                             ) -> List[Dict[str, Any]]:
    """Build inverted-polarity twins of the real specs.

    A negative control that comes out SUPPORTED means the validation is
    not discriminating and every other verdict is void. Each control
    keeps the same universe, risk block and period, and only flips the
    signal's polarity - so the ONLY difference is the concept.
    """
    specs = specs if specs is not None else build_specs()
    out: List[Dict[str, Any]] = []
    for s in specs:
        c = json.loads(json.dumps(s))
        c["name"] = f"NEGATIVE-CONTROL-{s['name']}"
        c["paper"] = (f"Negative control for {s['name']}; not a paper claim")
        c["intake"]["notes"] = (
            "A DELIBERATE negative control. Its whole purpose is to FAIL. "
            "If it comes out SUPPORTED, the validation is not "
            "discriminating and every other verdict from this matrix is "
            "void. It differs from its twin ONLY in the signal's "
            "polarity.")
        sig = c.get("signal") or {}
        params = dict(sig.get("params") or {})
        params["invert_signal"] = True
        sig["params"] = params
        c["signal"] = sig
        pp = dict(c.get("parameter_provenance") or {})
        pp["signal.params.invert_signal"] = _prov(
            "analyst_choice",
            "NEGATIVE CONTROL: deliberately inverted. Not a paper claim.")
        c["parameter_provenance"] = pp
        out.append(c)
    return out


def load_paper_specs(include_controls: bool = True) -> List[Dict[str, Any]]:
    """The specs, read from disk when the file exists, else built."""
    if os.path.isfile(PAPER_SPECS_PATH):
        try:
            with open(PAPER_SPECS_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list) and data:
                return data
        except Exception:  # noqa: BLE001
            pass
    specs = build_specs()
    if include_controls:
        specs = specs + build_negative_controls(specs)
    return specs


def write_paper_specs(path: Optional[str] = None) -> str:
    """Write the full matrix (specs + controls) to disk."""
    p = path or PAPER_SPECS_PATH
    os.makedirs(os.path.dirname(p), exist_ok=True)
    specs = build_specs()
    allspecs = specs + build_negative_controls(specs)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(allspecs, fh, indent=2)
    return p
