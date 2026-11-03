"""The LEADING-INDICATOR specifications.

WHAT THIS IS
    Backtest specifications that use a LEADING indicator - the
    volatility risk premium, implied minus realised volatility - to
    condition the directional signal, rather than the LAGGING inputs
    (realised volatility, trend, drawdown, liquidity) the existing
    regime specs use.

WHY THIS IS A SEPARATE FILE
    The existing regime specs are faithful to the regime papers, which
    describe a BACKWARD-LOOKING classifier. This file is faithful to a
    different claim in the SAME papers:

      "Option-implied and market-based uncertainty indicators can
       sometimes detect stress transitions EARLIER than backward-looking
       returns alone."                            - regime paper

      "Implied volatility often contains incremental information about
       future realized volatility, and in several studies it outperforms
       historical volatility forecasts."          - gamma/option paper

      "The 2023 stock study also finds that low net gamma exposure
       predicts higher future realized volatility." - gamma/option paper

THE MECHANISM, STATED PLAINLY
    The volatility risk premium (VRP) is implied volatility minus
    realised volatility.

      * VRP DEPRESSED (negative) - the market is NOT paying for
        protection. Options are cheap relative to what has been
        happening. This is the orderly-trend state where momentum works,
        and it is the state the momentum-crash literature says to
        favour.

      * VRP ELEVATED (positive) - the market has priced calm and is
        paying up for protection. A volatility shock is the disruptive
        event, and a trend-following position into it is exactly the
        momentum-crash setup. So the position is scaled DOWN
        progressively as the premium rises, rather than flipped
        outright.

    So this is a SIZING rule driven by a forward-looking input, not a
    second directional opinion. That is what the regime paper asks
    for: "Translate state probabilities into explicit position-sizing
    and turnover controls rather than signal switching alone."

THE HONEST LIMITATIONS, WHICH ARE NOT HIDDEN
    * The regime CLASSIFICATION in the existing regime specs is
      in-sample (the HMM is fitted on the whole panel). These specs do
      NOT inherit that defect for their leading input: the implied
      series is a real, timestamped, external measurement, aligned with
      a one-bar publication lag.
    * The implied series' HISTORY is limited by the provider. Deribit's
      DVOL endpoint returns at most 1000 points per call and this
      module pages backwards, so depth is a function of page budget,
      not of the data being unavailable.
    * The realised-volatility side of the premium depends on the
      sample's own volatility history, so the premium is a relative
      measure. The z-score version is what the signal consumes for
      exactly that reason.
    * A leading indicator that shows no edge is a REFUTED verdict, not
      a reason to relax the test. The gauntlet decides.

SOURCES
    Christensen & Prabhala (1998), Journal of Financial Economics 50(1).
    Ferris, Kim & Park (2010), Applied Economics Letters 36(5).
    Butt, Kolari & Sadaqat (2024), Journal of Asset Management.
    Daniel & Moskowitz (2016), Journal of Financial Economics 122(2).
    Baltussen, Da, Lammers & Martens (2021), Journal of Financial
    Economics 141(1).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

__all__ = ["load_leading_specs", "LEADING_SPECS_PATH"]


LEADING_SPECS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "leading_specs.json")

#: The intake conditions that are answered BY THE PAPER and recorded
#: here. The paper states the mechanism, the universe and the risk
#: controls; it does not state the backtest window, the cost schedule,
#: the rebalance cadence or the position-size numbers, so those are
#: analyst choices and are labelled as such in
#: `parameter_provenance`.
_CONFIRMED = [
    "hypothesis", "universe", "direction", "entry", "exit", "timeframe",
    "rebalance", "sizing", "leverage", "costs", "period", "variants_tried",
]


def _base(name: str, paper: str, hypothesis: str, universe: Dict[str, Any],
          period: Dict[str, Any], features: List[Dict[str, Any]],
          signal: Dict[str, Any], portfolio: Dict[str, Any],
          execution: Dict[str, Any], capital: Dict[str, Any],
          provenance: Dict[str, Any], notes: str) -> Dict[str, Any]:
    return {
        "name": name,
        "paper": paper,
        "hypothesis": hypothesis,
        "universe": universe,
        "period": period,
        "features": features,
        "signal": signal,
        "portfolio": portfolio,
        "execution": execution,
        "capital": capital,
        "intake": {
            "confirmed": list(_CONFIRMED),
            "variants_tried": 1,
            "notes": notes,
        },
        "parameter_provenance": provenance,
    }


#: The analyst choices, recorded so the report can name them. Every one
#: of these is NOT stated by the papers.
_ANALYST = "ANALYST_CHOICE: not stated by the paper; chosen to match the "
_ENGINE = "ENGINE_DEFAULT: the engine's default; the paper states no value."


def _specs() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 1. CRYPTO — BTC/ETH, volatility risk premium sizing
    # ------------------------------------------------------------------
    out.append(_base(
        name="leading_vrp_crypto_momentum",
        paper="Options market dynamics and volatility (LeapSpace); "
              "Financial market regime identification (LeapSpace)",
        hypothesis=(
            "Conditioning a crypto momentum signal on the VOLATILITY RISK "
            "PREMIUM (implied minus realised volatility) improves the "
            "out-of-sample result relative to the same momentum signal "
            "unconditioned, because the premium is a FORWARD-LOOKING "
            "reading of whether the market is priced for calm. The "
            "papers: 'Implied volatility often contains incremental "
            "information about future realized volatility, and in several "
            "studies it outperforms historical volatility forecasts'; "
            "'Momentum belongs to orderly trend states ... Reversal "
            "belongs to stressed, illiquid, high-volatility, or rebound "
            "states.' Position size scales DOWN as the premium rises, so "
            "the momentum-crash state is entered smaller rather than "
            "flipped."),
        universe={"preset": "crypto"},
        period={"start": "2021-01-01", "end": None, "interval": "1d"},
        features=[
            {"name": "regime_momentum_score", "params": {"lookback": 20}},
            {"name": "leading_vrp_score", "params": {"rv_window": 20}},
            {"name": "leading_vrp_zscore", "params": {"rv_window": 20}},
        ],
        signal={"type": "leading_vrp_switch", "params": {
            "feature": "regime_momentum_score",
            "vrp_z_feature": "leading_vrp_zscore",
            "exposure_cap": 1.0}},
        portfolio={"max_position": 0.25, "net_target": 0.0,
                   "rebalance": "weekly"},
        execution={"fill_at": "open", "cost_multiplier": 1.0},
        capital={"start_usd": 10000.0},
        provenance={
            "universe.preset": "PAPER: crypto; the paper's crypto universe "
                               "is liquid majors (BTC, ETH).",
            "features.regime_momentum_score.lookback": _ANALYST
            + "20 bars, chosen to match the momentum horizon the paper's "
              "crypto momentum evidence uses.",
            "features.leading_vrp_score.rv_window": _ANALYST
            + "20 bars, a standard monthly realised-volatility estimate.",
            "signal.type": "PAPER: the regime papers' switching mechanism, "
                           "applied to a leading input.",
            "signal.params.exposure_cap": _ANALYST
            + "1.0 means the premium scales the position to zero at a "
              "z-score of 1 and below; the paper states no number.",
            "portfolio.max_position": _ANALYST + "25% per name.",
            "portfolio.rebalance": _ANALYST + "weekly.",
            "portfolio.net_target": _ANALYST + "0.0 (market neutral).",
            "execution.cost_multiplier": _ENGINE,
            "capital.start_usd": _ANALYST + "$10,000.",
            "period.start": _ANALYST + "2021-01-01, chosen to cover the "
            "2021 bull, the 2022 bear and the 2024-2026 range.",
        },
        notes=(
            "Distilled from the gamma/option paper's claim that implied "
            "volatility outperforms historical volatility as a forecast, "
            "and the regime paper's claim that momentum belongs to orderly "
            "trend states. The leading input is a real, timestamped, "
            "EXTERNAL measurement (Deribit DVOL) aligned with a one-bar "
            "publication lag, so this spec does NOT inherit the in-sample "
            "regime-classification defect of the lagging regime specs. "
            "The premium's DEPTH is bounded by the provider's page budget "
            "and is reported in the run output."),
    ))

    # ------------------------------------------------------------------
    # 2. US EQUITY — Nasdaq, VXN-implied premium sizing
    # ------------------------------------------------------------------
    out.append(_base(
        name="leading_vrp_nasdaq_momentum",
        paper="NASDAQ market regime identification (LeapSpace); "
              "Options market dynamics and volatility (LeapSpace)",
        hypothesis=(
            "The NASDAQ-100 implied volatility index, minus realised "
            "volatility, is a forward-looking reading of whether the "
            "index is priced for calm; scaling a Nasdaq momentum position "
            "down as that premium rises should improve the "
            "out-of-sample result relative to the same signal "
            "unconditioned. The papers: 'the best regime indicators ... "
            "forward-looking option/VIX signals can improve early stress "
            "detection'; 'elevated short-versus-long volatility, which is "
            "effectively a rebound-danger state'."),
        universe={"preset": "us_equity_style"},
        period={"start": "2005-01-01", "end": None, "interval": "1d"},
        features=[
            {"name": "regime_momentum_score", "params": {"lookback": 60}},
            {"name": "leading_vrp_score", "params": {"rv_window": 20}},
            {"name": "leading_vrp_zscore", "params": {"rv_window": 20}},
        ],
        signal={"type": "leading_vrp_switch", "params": {
            "feature": "regime_momentum_score",
            "vrp_z_feature": "leading_vrp_zscore",
            "exposure_cap": 1.0}},
        portfolio={"max_position": 0.25, "net_target": 0.0,
                   "rebalance": "monthly"},
        execution={"fill_at": "open", "cost_multiplier": 1.0},
        capital={"start_usd": 10000.0},
        provenance={
            "universe.preset": "PAPER: the NASDAQ paper concerns "
                               "NASDAQ-related equities and the Nasdaq-100 "
                               "index context.",
            "features.regime_momentum_score.lookback": _ANALYST
            + "60 bars (about one quarter), the horizon the regime paper "
              "cites for swing/daily trend features.",
            "features.leading_vrp_score.rv_window": _ANALYST
            + "20 bars.",
            "signal.type": "PAPER: the regime-switch mechanism, applied to "
                           "a leading input.",
            "signal.params.exposure_cap": _ANALYST + "1.0.",
            "portfolio.max_position": _ANALYST + "25% per name.",
            "portfolio.rebalance": _ANALYST + "monthly.",
            "portfolio.net_target": _ANALYST + "0.0.",
            "execution.cost_multiplier": _ENGINE,
            "capital.start_usd": _ANALYST + "$10,000.",
            "period.start": _ANALYST
            + "2005-01-01, to cover the 2008 crisis, the 2020 COVID crash "
              "and the 2022 bear market - the paper's own examples of "
              "stress regimes.",
        },
        notes=(
            "The leading input here is ^VXN - the NASDAQ-100 implied "
            "volatility index - because the universe is Nasdaq-like. "
            "Using VIX for a Nasdaq panel would import a leading "
            "indicator from a market the panel does not trade, which is a "
            "category error rather than a modelling choice, so the "
            "source is RESOLVED FROM THE UNIVERSE."),
    ))

    # ------------------------------------------------------------------
    # 3. THE NEGATIVE CONTROL — the same signal with the premium
    #    INVERTED. If the premium carried real information, inverting it
    #    should destroy the result. If the result survives the inversion,
    #    the premium was never doing the work.
    # ------------------------------------------------------------------
    ctrl = json.loads(json.dumps(out[0]))
    ctrl["name"] = "NEGATIVE-CONTROL-leading_vrp_crypto_inverted"
    ctrl["paper"] = ("Negative control for leading_vrp_crypto_momentum; "
                     "not a paper claim")
    ctrl["hypothesis"] = (
        "NEGATIVE CONTROL. The same crypto momentum signal, with the "
        "volatility risk premium's SIGN INVERTED, should perform WORSE "
        "than the unconditioned signal. If a spec built this way still "
        "looks good, the premium is not the thing making it work, and "
        "any SUPPORTED verdict on the real spec is suspect. This spec "
        "exists to be REFUTED.")
    ctrl["signal"]["params"]["invert_vrp"] = True
    ctrl["intake"]["notes"] = (
        "A DELIBERATE negative control, not a research claim. Its whole "
        "purpose is to fail. If it comes out SUPPORTED, the validation "
        "is not discriminating and every other verdict is void.")
    ctrl["parameter_provenance"]["signal.params.invert_vrp"] = (
        "NEGATIVE_CONTROL: deliberately inverted. Not a paper claim.")
    out.append(ctrl)

    return out


def load_leading_specs() -> List[Dict[str, Any]]:
    """The leading-indicator specs.

    They are read from `leapspace/data/leading_specs.json` when that
    file exists (so the JSON is the single source of truth and the
    report can show it), and built in code otherwise. The code path is
    the authority; the JSON is a rendered copy of it.
    """
    if os.path.isfile(LEADING_SPECS_PATH):
        try:
            with open(LEADING_SPECS_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list) and data:
                return data
        except Exception:  # noqa: BLE001
            pass
    return _specs()


def write_leading_specs(path: Optional[str] = None) -> str:
    """Write the specs to disk so they are inspectable and reportable."""
    p = path or LEADING_SPECS_PATH
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(_specs(), fh, indent=2)
    return p
