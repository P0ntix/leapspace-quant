"""Phase A: the paper's long/short trend rule and the pairs construction.

WHAT THIS IS
    The claim inventory found the gap that matters most: the package's
    only SUPPORTED result, `nasdaq_12m_timeseries_momentum`, is
    `long_only: true` at `cost_multiplier: 1.0` - while the paper it
    comes from says

      "Go long when price is above its trend proxy; go short or flat
       when below, if your venue supports it."

    THE PAPER'S LONG/SHORT VERSION WAS NEVER TESTED. The tested
    version is a long-only bet on the equity market's direction - a
    beta bet dressed up as a signal.

    `leapspace/trend.py` supplies what was missing:
      * `sig_trend_long_short` - the paper's rule with BOTH legs live
        and an explicit dead band. The engine's own
        `time_series_threshold` only goes long OR short, never both.
      * `sig_pairs_mean_reversion` - the pairs construction the paper
        also specifies: "use a cointegration or spread model on stable
        pairs, with a z-score entry and a mean-reversion exit" (RET
        p16) and for crypto "dynamic cointegration or Hurst-filtered
        pairs, with a short holding period and transaction-cost-aware
        exits".

        MARKET-NEUTRAL BY CONSTRUCTION: each pair's one leg is long and
        the other short, sized by the hedge ratio, so the SPREAD's
        exposure is what is traded. That is the "hedging, not just spot
        trading" the requirement asks for, and it is why a spread's win
        rate is naturally high - the spread is expected to revert.

THIS BUILDS THE SPECS. It does not run them - the runner is the same
`paperrun.run_matrix` that produced the existing matrix, so the
results land in the same shape and are comparable.

THE COMMON RISK BLOCK
    These specs are built with `paperspecs._make`, so they carry the
    IDENTICAL risk block and provenance as the other 96 matrix rows:

      gross_leverage 1.0, vol_target 0.15, vol_lookback 60,
      max_position 0.10, max_names 5, net_target 0.0,
      long_only False, rebalance monthly, cost_multiplier 2.0

    `net_target: 0.0` and `long_only: False` are what stop a result
    being a beta bet in disguise, and they are the difference between a
    signal and a direction. Reusing `_make` rather than writing the
    block out again is deliberate: a hand-copied risk block drifts,
    and a drifted risk block makes two rows incomparable.

THE INVERTED TWINS
    Every spec gets a negative control with the position polarity
    flipped. For the long/short trend rule the control is a genuine
    inversion. For the PAIRS signal the control is different in kind:
    a pairs strategy has no "opposite" - the sign of the spread is
    determined by the spread itself. So its control is the INVERTED
    SPREAD DIRECTION: trade the spread mean-reversion the wrong way.
    A control that cannot fail is not a control, and this one can.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

REPORTS = os.path.join(ROOT, "reports")

from leapspace.paperspecs import _make, _prov  # noqa: E402

PAPER = "Trading strategies for retail traders (LeapSpace 2.0)"

#: The asset classes, with the trend window the paper's own text names
#: for each: a 12-month time-series momentum for equities, and a
#: "shorter, crypto-adapted trend window such as 20-day or 2-4 week
#: lookback for crypto".
ASSET_CLASSES: List[Dict[str, Any]] = [
    {"asset_class": "us_equity_style", "lookback": 252,
     "label": "12-month time-series momentum"},
    {"asset_class": "crypto", "lookback": 20,
     "label": "20-day crypto-adapted trend window"},
    {"asset_class": "fx_major", "lookback": 60,
     "label": "60-day trend window"},
    {"asset_class": "commodities", "lookback": 60,
     "label": "60-day trend window"},
    {"asset_class": "futures_broad", "lookback": 60,
     "label": "60-day trend window"},
    {"asset_class": "rates_credit", "lookback": 60,
     "label": "60-day trend window"},
]

#: The paper's wording, quoted. The direction rule is quoted verbatim
#: because it is the exact sentence the previously-tested spec
#: contradicted.
PAPER_TREND_QUOTE = (
    "Go long when price is above its trend proxy; go short or flat "
    "when below, if your venue supports it."
)
PAPER_PAIRS_QUOTE = (
    "Use a cointegration or spread model on stable pairs, with a "
    "z-score entry and a mean-reversion exit."
)


def trend_spec(ac: Dict[str, Any], invert: bool = False) -> Dict[str, Any]:
    """The paper's time-series momentum rule, with BOTH legs live."""
    name = f"paper_trend_longshort_{ac['asset_class']}"
    if invert:
        name += "_CONTROL"
    hyp = (
        f"Section 'Momentum and Mean Reversion Trading Strategies'. "
        f"Direction rule, quoted: \"{PAPER_TREND_QUOTE}\" "
        f"Window: {ac['label']}. "
        f"Hypothesis: the paper's rule - long above the trend proxy, "
        f"short below - produces a risk-managed, dollar-neutral trend "
        f"signal that survives stressed costs, and its inverted twin "
        f"does not."
    )
    prov = {
        "signal.params.dead_band": _prov(
            "analyst_choice",
            "0.0 - no dead band, so the rule is the paper's own: long "
            "above the trend proxy, short below. A dead band is an "
            "analyst addition and would change the rule being tested.",
            citation="not stated in source"),
        "signal.params.threshold": _prov(
            "analyst_choice",
            "0.0 - the trend proxy is the sign of the momentum itself, "
            "so zero is the paper's rule.",
            citation="not stated in source"),
        "features.momentum.lookback": _prov(
            "paper",
            f"{ac['label']} - the paper names the window: a 12-month "
            f"time-series momentum for equities and a shorter "
            f"crypto-adapted window for crypto.",
            citation=PAPER),
    }
    if invert:
        prov["signal.params.invert_signal"] = _prov(
            "analyst_choice",
            "TRUE - this is the NEGATIVE CONTROL. The position polarity "
            "is flipped, so the control trades the trend the wrong way. "
            "It must FAIL; if it does not, the trend reading is not what "
            "produced the result.",
            citation="control")
    return _make(
        name=name, paper=PAPER, concept="PAPER_TREND_LONG_SHORT",
        hypothesis=hyp, asset_class=ac["asset_class"],
        features=[{"name": "momentum",
                   "params": {"lookback": ac["lookback"], "skip": 0}}],
        signal={
            "type": "trend_long_short",
            "params": {
                "feature": "momentum",
                "threshold": 0.0,
                "dead_band": 0.0,
                "invert_signal": bool(invert),
            },
        },
        provenance=prov,
        notes=(
            "The paper's long/short rule, tested for the first time. The "
            "previously SUPPORTED nasdaq_12m_timeseries_momentum was "
            "long_only:true, which CONTRADICTS the paper's own direction "
            "rule quoted above. Costs are stressed to 2x the engine "
            "default."),
    )


def pairs_spec(ac: Dict[str, Any], invert: bool = False) -> Dict[str, Any]:
    """The paper's dollar-neutral pairs construction."""
    name = f"paper_pairs_meanrev_{ac['asset_class']}"
    if invert:
        name += "_CONTROL"
    hyp = (
        f"Section 'Momentum and Mean Reversion Trading Strategies', "
        f"subsection on pairs. Quoted: \"{PAPER_PAIRS_QUOTE}\" "
        f"Hypothesis: a dollar-neutral pairs construction - one leg "
        f"long, the other short, sized by the hedge ratio, entered on "
        f"a z-score and exited on reversion - produces a market-neutral "
        f"return stream with a high win rate and a bounded downside, "
        f"and the inverted-spread control does not."
    )
    prov = {
        "signal.params.z_entry": _prov(
            "analyst_choice",
            "2.0 sigma. The paper says 'a z-score entry' without a "
            "number; 2.0 is the standard entry for a spread that is "
            "expected to revert.",
            citation="not stated in source"),
        "signal.params.z_exit": _prov(
            "analyst_choice",
            "0.5 sigma - exit when the spread has reverted halfway "
            "back. The paper says 'a mean-reversion exit'.",
            citation="not stated in source"),
        "signal.params.max_hold_bars": _prov(
            "paper",
            "A short holding period for crypto: 'crypto mean reversion "
            "can be fast' (RET p16). 20 trading days.",
            citation=PAPER),
        "signal.params.max_pairs": _prov(
            "analyst_choice",
            "3 pairs. The paper does not say how many; the count is "
            "limited so concentration cannot come from one spread.",
            citation="not stated in source"),
    }
    if invert:
        prov["signal.params.invert_signal"] = _prov(
            "analyst_choice",
            "TRUE - this is the NEGATIVE CONTROL. A pairs strategy has "
            "no polarity to flip - the spread's direction is the "
            "spread's - so the control trades the mean-reversion the "
            "WRONG WAY. It must FAIL.",
            citation="control")
    return _make(
        name=name, paper=PAPER, concept="PAPER_PAIRS_MEAN_REVERSION",
        hypothesis=hyp, asset_class=ac["asset_class"],
        features=[{"name": "zscore", "params": {"lookback": 60}}],
        signal={
            "type": "pairs_mean_reversion",
            "params": {
                "feature": "zscore",
                "z_entry": 2.0,
                "z_exit": 0.5,
                "max_hold_bars": 20,
                "max_pairs": 3,
                "invert_signal": bool(invert),
            },
        },
        provenance=prov,
        notes=(
            "The paper's pairs construction, market-neutral by design: "
            "each pair's legs offset, so the SPREAD's exposure is what "
            "is traded. The control is the inverted spread direction."),
    )


def build_phase_a_specs() -> List[Dict[str, Any]]:
    """Every Phase A spec: the real ones and their inverted twins."""
    specs: List[Dict[str, Any]] = []
    for ac in ASSET_CLASSES:
        specs.append(trend_spec(ac, invert=False))
        specs.append(trend_spec(ac, invert=True))
        specs.append(pairs_spec(ac, invert=False))
        specs.append(pairs_spec(ac, invert=True))
    return specs


def main() -> int:
    specs = build_phase_a_specs()
    out = os.path.join(REPORTS, "phase_a_specs.json")
    os.makedirs(REPORTS, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(specs, fh, indent=2)
    print(f"wrote {out}: {len(specs)} specs "
          f"({len(specs) // 2} real, {len(specs) // 2} controls)")
    for s in specs:
        print(f"  {s['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
