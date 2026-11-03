"""
Alerts — price, information and action — derived from the research papers.

The user asked for "price/information/action alerts based on the research
papers". Each alert category maps to specific claims in the papers:

PRICE alerts  (paper: Financial market regime identification; NASDAQ market
               regime identification; Options market dynamics and volatility)
  * Drawdown / stress expansion — the regime papers' vol-change and drawdown
    features, and the momentum-crash literature they cite.
  * Regime TRANSITION — the papers' core claim is that the regime changed,
    not that the price moved. A transition alert carries the posterior
    probabilities, not just the price.
  * Gamma-state flip — "Negative gamma suggests hedging flows may push
    volatility higher and create momentum, while positive gamma tends to damp
    volatility."
  * Option-flow pressure — "Use option flow as a near-term pressure signal."

INFORMATION alerts  (papers: all; plus the US disclosure skill)
  * US officials' disclosures across the legislative, executive and judicial
    branches, with the asset and the value band.
  * On-chain wallet clustering, insider flags and concentration.
  * Meme-coin structural events (authority, concentration, liquidity decay).

ACTION alerts  (papers: NASDAQ market regime identification — "Execution
               Rules by Regime"; Gamma exposure and option flow)
  * The paper's own execution mapping: follow vs fade, reduce size, or stand
    aside, with the gamma state and the regime posterior as the reason.

EVERY threshold in this module is an ANALYST CHOICE unless the cited paper
states the number. They are collected in `ALERT_THRESHOLDS` and rendered with
every alert set so a reader can see exactly what fired.

Nothing here invents data. Every alert carries the provenance of the value it
is based on, and an alert whose source was unreachable is not emitted — the
gap is reported instead.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .provenance import Provenance, SourceUnavailable, read_json, write_json

HIGH, MEDIUM, LOW = "HIGH", "MEDIUM", "LOW"
PRICE, INFORMATION, ACTION = "price", "information", "action"

# --------------------------------------------------------------------------
# Thresholds — every one is an analyst choice unless the citation says the
# paper states it. Nothing here is presented as a paper result.
# --------------------------------------------------------------------------

ALERT_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "drawdown_pct": {"value": 0.10, "source": "analyst_choice",
                     "note": "Regime papers name drawdown as a core feature but set no level."},
    "drawdown_pct_hard": {"value": 0.20, "source": "analyst_choice",
                           "note": "A second, harder drawdown band."},
    "vol_expansion_ratio": {"value": 1.5, "source": "analyst_choice",
                            "note": ("Short/long realised-vol ratio. The papers "
                                     "name 'volatility level and change' as a "
                                     "feature without a threshold.")},
    "regime_transition_conf": {"value": 0.55, "source": "analyst_choice",
                                "note": ("Posterior probability required to call "
                                         "a regime. The papers argue for soft "
                                         "probabilities but set no cut.")},
    "regime_transition_min_bars": {"value": 5, "source": "analyst_choice",
                                    "note": "Minimum bars in the new regime before it counts as a transition."},
    "gamma_flip": {"value": 0.0, "source": "analyst_choice",
                   "note": ("Net gamma sign change. The paper's claim is "
                            "directional (positive damps, negative amplifies) "
                            "but it states no numeric band.")},
    "put_call_volume_ratio": {"value": 1.2, "source": "analyst_choice",
                               "note": ("Put/call volume ratio. The paper says "
                                        "raw counts are too blunt and flow must "
                                        "be exposure-adjusted, but sets no "
                                        "ratio threshold.")},
    "disclosure_value_usd": {"value": 1_000_000.0, "source": "analyst_choice",
                             "note": ("Minimum disclosed value band floor. The "
                                      "disclosure skill's default asset "
                                      "threshold is $100k for a watchlist; "
                                      "$1M is used here for market-impact "
                                      "relevance.")},
    "top_holder_pct": {"value": 20.0, "source": "analyst_choice",
                       "note": ("Meme-coin paper's structural-safety layer; it "
                                "cites the Libra case (92.8% creator control) "
                                "but sets no threshold.")},
    "insider_holders": {"value": 1, "source": "analyst_choice",
                        "note": "Any insider-flagged holder in the top 20."},
    "liquidity_drop_pct": {"value": 0.30, "source": "analyst_choice",
                           "note": "Liquidity decline that makes exit quality a concern."},
}


def _t(key: str) -> Any:
    return ALERT_THRESHOLDS[key]["value"]


@dataclass
class Alert:
    category: str
    severity: str
    title: str
    detail: str
    threshold: str
    source: str
    paper: str
    timestamp: str = ""
    action: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    provenance: str = ""

    def fingerprint(self) -> str:
        raw = f"{self.category}|{self.title}|{self.data.get('symbol', '')}|" \
              f"{self.data.get('key', '')}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "threshold": self.threshold,
            "source": self.source,
            "paper": self.paper,
            "timestamp": self.timestamp,
            "action": self.action,
            "data": self.data,
            "provenance": self.provenance,
            "fingerprint": self.fingerprint(),
        }

    def render(self) -> str:
        lines = [f"[{self.severity}] {self.category.upper()} — {self.title}"]
        lines.append(f"  when:      {self.timestamp or 'n/a'}")
        lines.append(f"  what:      {self.detail}")
        lines.append(f"  threshold: {self.threshold}")
        if self.action:
            lines.append(f"  action:    {self.action}")
        lines.append(f"  paper:     {self.paper}")
        lines.append(f"  source:    {self.source}")
        if self.provenance:
            lines.append(f"  data:      {self.provenance}")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Price alerts
# --------------------------------------------------------------------------


def price_alerts_from_bars(symbol: str, bars: Sequence[Dict[str, Any]],
                           provenance: str = "") -> List[Alert]:
    """Drawdown and volatility-expansion alerts from real OHLCV."""
    out: List[Alert] = []
    if len(bars) < 70:
        return out
    closes = [(b.get("close"), b.get("date")) for b in bars if b.get("close")]
    if len(closes) < 70:
        return out
    prices = [c for c, _ in closes]
    dates = [d for _, d in closes]

    # Rolling peak and drawdown.
    peak = prices[0]
    peak_date = dates[0]
    dd_series: List[Tuple[str, float]] = []
    for d, c in zip(dates, prices):
        if c > peak:
            peak, peak_date = c, d
        dd_series.append((d, c / peak - 1.0))
    last_d, last_dd = dd_series[-1]
    hard = _t("drawdown_pct_hard")
    soft = _t("drawdown_pct")
    if last_dd <= -hard:
        out.append(Alert(
            category=PRICE, severity=HIGH,
            title=f"{symbol} in a {abs(last_dd):.1%} drawdown",
            detail=(f"Price is {abs(last_dd):.1%} below its rolling peak "
                    f"(peak {peak_date}). The regime papers treat deep "
                    f"drawdown as a stress-regime marker and the "
                    f"momentum-crash literature they cite associates losses "
                    f"with prior declines and rebounds."),
            threshold=f"drawdown <= -{hard:.0%}",
            source=f"market data for {symbol}",
            paper="Financial market regime identification (LeapSpace); "
                  "NASDAQ market regime identification (LeapSpace)",
            timestamp=last_d,
            action=("Momentum off. The papers put a post-decline rebound in "
                    "the crash/rebound state where momentum crashes live; "
                    "reversal/liquidity-provision is the paper's alternative."),
            data={"symbol": symbol, "key": "drawdown_hard",
                  "drawdown": last_dd, "peak": peak, "peak_date": peak_date},
            provenance=provenance))
    elif last_dd <= -soft:
        out.append(Alert(
            category=PRICE, severity=MEDIUM,
            title=f"{symbol} drawdown {abs(last_dd):.1%}",
            detail=(f"Price is {abs(last_dd):.1%} below its rolling peak. "
                    f"The regime papers use drawdown depth as one of the four "
                    f"core regime features alongside volatility, trend and "
                    f"liquidity."),
            threshold=f"drawdown <= -{soft:.0%}",
            source=f"market data for {symbol}",
            paper="Financial market regime identification (LeapSpace)",
            timestamp=last_d,
            action="Watch for a regime transition; a drawdown alone is not a "
                   "regime change.",
            data={"symbol": symbol, "key": "drawdown_soft",
                  "drawdown": last_dd, "peak": peak, "peak_date": peak_date},
            provenance=provenance))

    # Volatility expansion: short/long realised volatility ratio.
    rets: List[float] = []
    rdates: List[str] = []
    for i in range(1, len(prices)):
        prev, cur = prices[i - 1], prices[i]
        if prev and cur and prev > 0 and cur > 0:
            rets.append(cur / prev - 1.0)
            rdates.append(dates[i])
    if len(rets) >= 120:

        def _rv(n: int) -> List[Optional[float]]:
            outv: List[Optional[float]] = [None] * len(rets)
            for i in range(n - 1, len(rets)):
                w = rets[i - n + 1:i + 1]
                m = sum(w) / len(w)
                var = sum((x - m) ** 2 for x in w) / (len(w) - 1)
                outv[i] = var ** 0.5
            return outv

        short = _rv(20)
        long = _rv(60)
        ratio = None
        for i in range(len(short) - 1, -1, -1):
            if short[i] and long[i]:
                ratio = short[i] / long[i]
                break
        thr = _t("vol_expansion_ratio")
        if ratio and ratio >= thr:
            out.append(Alert(
                category=PRICE, severity=MEDIUM,
                title=f"{symbol} volatility expanding ({ratio:.2f}x)",
                detail=(f"20-day realised volatility is {ratio:.2f}x its "
                        f"60-day level. The papers treat volatility CHANGE as "
                        f"a regime feature distinct from its level, and cite "
                        f"log-scale realised-variance models as performing "
                        f"better precisely because they handle heteroscedastic "
                        f"measurement error."),
                threshold=f"short/long realised-vol ratio >= {thr}",
                source=f"market data for {symbol}",
                paper="Financial market regime identification (LeapSpace); "
                      "NASDAQ market regime identification (LeapSpace)",
                timestamp=rdates[-1] if rdates else "",
                action="Expect the regime classifier to move toward a "
                       "high-volatility or stress state.",
                data={"symbol": symbol, "key": "vol_expansion", "ratio": ratio},
                provenance=provenance))
    return out


def regime_transition_alerts(regime_result: Any, symbol: str = "MARKET",
                              provenance: str = "") -> List[Alert]:
    """Alert on a regime STATE CHANGE, with the posterior probabilities."""
    out: List[Alert] = []
    if regime_result is None:
        return out
    labels = regime_result.label_series_filtered
    conf = _t("regime_transition_conf")
    min_bars = _t("regime_transition_min_bars")
    p_by_label = regime_result.probability_of

    # Find the most recent confirmed transition.
    i = len(labels) - 1
    while i >= 1 and (not labels[i] or labels[i] == labels[i - 1]):
        i -= 1
    if i < 1 or not labels[i]:
        return out
    new_label = labels[i]
    old_label = labels[i - 1]
    if new_label == old_label:
        return out
    # Require the new state to have persisted.
    j = i
    while j > 0 and labels[j] == new_label:
        j -= 1
    held = i - j
    if held < min_bars:
        return out
    p_new = p_by_label(new_label)
    p_new_val = p_new[i] if i < len(p_new) else None
    if p_new_val is None or p_new_val < conf:
        return out
    prev = regime_result.probability_of(new_label)
    prev_val = prev[j - 1] if 0 < j - 1 < len(prev) else None

    behaviour = {
        "tranquil_uptrend": "momentum on, reversal off, full size",
        "high_vol_uptrend": "momentum reduced/selective, reduced size",
        "range_chop": "momentum off, short-horizon mean reversion, low exposure",
        "regular_bear": "momentum off, cautious, reduced size, some reversal setups",
        "crash_rebound": "momentum OFF, reversal/liquidity-provision favoured, minimal size",
    }.get(new_label, "unspecified")
    out.append(Alert(
        category=PRICE, severity=HIGH,
        title=f"Regime transition: {old_label} → {new_label}",
        detail=(f"The market regime moved from '{old_label}' to '{new_label}' "
                f"and has held for {held} bars. Posterior probability of the "
                f"new state: {p_new_val:.0%}"
                + (f" (was {prev_val:.0%})" if prev_val is not None else "")
                + f". The papers' mapping for this state is: {behaviour}."),
        threshold=f"posterior of new state >= {conf:.0%} and held >= {min_bars} bars",
        source=f"regime model on {symbol}",
        paper="Financial market regime identification (LeapSpace); "
              "NASDAQ market regime identification (LeapSpace)",
        action=f"Adjust posture per the paper: {behaviour}.",
        data={"symbol": symbol, "key": f"regime_transition_{new_label}",
              "from": old_label, "to": new_label, "held_bars": held,
              "posterior": p_new_val},
        provenance=provenance))
    return out


def gamma_alerts(gamma: Any, flow: Any = None, provenance: str = "") -> List[Alert]:
    """Gamma-state and option-flow pressure alerts."""
    out: List[Alert] = []
    if gamma is None:
        return out
    symbol = gamma.underlying
    if gamma.sign is not None and gamma.sign != 0:
        sev = HIGH if gamma.sign < 0 else MEDIUM
        out.append(Alert(
            category=PRICE, severity=sev,
            title=f"{symbol} net gamma {gamma.sign:+d} "
                  f"({'amplifying' if gamma.sign < 0 else 'damping'})",
            detail=(f"Net gamma is {gamma.net_gamma:,.0f} (call leg "
                    f"{gamma.call_gamma:,.0f}, put leg {gamma.put_gamma:,.0f}). "
                    f"{gamma.interpretation()}"),
            threshold="sign of net dealer gamma",
            source=f"option chain for {symbol}",
            paper="Options market dynamics and volatility (LeapSpace); "
                  "NASDAQ market regime identification (LeapSpace)",
            action=("Follow breaks with faster exits and more aggressive "
                    "execution." if gamma.sign < 0 else
                    "Fade extensions with passive execution and smaller targets."),
            data={"symbol": symbol, "key": "gamma_state",
                  "net_gamma": gamma.net_gamma, "sign": gamma.sign,
                  "state": gamma.state},
            provenance=provenance))
    if flow is not None and flow.put_call_volume_ratio is not None:
        ratio = flow.put_call_volume_ratio
        thr = _t("put_call_volume_ratio")
        if ratio >= thr:
            out.append(Alert(
                category=PRICE, severity=MEDIUM,
                title=f"{symbol} put/call volume ratio {ratio:.2f}",
                detail=(f"Put volume is {ratio:.2f}x call volume on "
                        f"{flow.call_volume:,.0f} calls vs "
                        f"{flow.put_volume:,.0f} puts. The papers establish "
                        f"that flow must be exposure-adjusted and that "
                        f"volatility-strategy flow predicts realised "
                        f"volatility but NOT next-day returns — so this is a "
                        f"volatility-pressure read, not a direction call. "
                        f"Exposure-adjusted net delta flow: "
                        f"{flow.net_delta_flow:,.0f}."),
                threshold=f"put/call volume ratio >= {thr}",
                source=f"option chain for {symbol}",
                paper="Options market dynamics and volatility (LeapSpace); "
                      "NASDAQ market regime identification (LeapSpace)",
                action="Read as volatility demand, not as a bearish signal.",
                data={"symbol": symbol, "key": "pc_volume_ratio",
                      "ratio": ratio, "net_delta_flow": flow.net_delta_flow},
                provenance=provenance))
    return out


# --------------------------------------------------------------------------
# Information alerts
# --------------------------------------------------------------------------


def disclosure_alerts(disclosure_report: Dict[str, Any],
                      assets_by_filing: Optional[Dict[str, List[Dict[str, Any]]]] = None,
                      provenance: str = "") -> List[Alert]:
    """Alerts from US officials' disclosures, all three branches."""
    out: List[Alert] = []
    threshold = _t("disclosure_value_usd")
    branch_labels = {
        "legislative_house": ("Legislative", "House of Representatives"),
        "executive_oge": ("Executive", "Office of Government Ethics"),
        "judicial": ("Judicial", "Federal Judiciary"),
    }
    assets_by_filing = assets_by_filing or {}
    for key, (branch, body) in branch_labels.items():
        b = (disclosure_report.get("branches") or {}).get(key)
        if not b:
            continue
        for filing in b.get("sample", []) or []:
            assets = assets_by_filing.get(filing.get("pdf_url", ""), [])
            for a in assets:
                if a.get("is_exempt"):
                    continue
                vlow = a.get("value_low")
                if vlow is None or vlow < threshold:
                    continue
                out.append(Alert(
                    category=INFORMATION, severity=HIGH,
                    title=f"{branch}: {filing.get('name')} disclosed "
                          f"{a.get('ticker') or a.get('description')}",
                    detail=(f"{body} filing ({filing.get('doc_label') or filing.get('filing_type')}"
                            f"{', ' + filing.get('filing_date') if filing.get('filing_date') else ''}). "
                            f"Asset: {a.get('description')} "
                            f"({a.get('ticker') or 'no ticker'}), value band "
                            f"{a.get('value_band') or 'unknown'}."),
                    threshold=f"disclosed value floor >= ${threshold:,.0f}",
                    source=filing.get("pdf_url") or body,
                    paper="US officials' financial disclosure (legislative / "
                          "executive / judicial)",
                    timestamp=filing.get("filing_date") or "",
                    action=("Check the market impact window (1/5/20 trading "
                            "days vs the benchmark) before treating this as "
                            "an actionable signal."),
                    data={"symbol": a.get("ticker"), "key": f"disclosure_{branch}",
                          "branch": branch, "filer": filing.get("name"),
                          "value_low": vlow, "value_high": a.get("value_high"),
                          "url": filing.get("pdf_url")},
                    provenance=provenance))
    return out


def onchain_alerts(wallet_profiles: Sequence[Any], concentration: Optional[Dict[str, Any]] = None,
                   provenance: str = "") -> List[Alert]:
    """Alerts from wallet behaviour and holder concentration."""
    out: List[Alert] = []
    for prof in wallet_profiles:
        d = prof.to_dict() if hasattr(prof, "to_dict") else prof
        addr = d.get("address", "?")
        loops = d.get("loop_transactions") or []
        self_trades = d.get("self_trades") or []
        if loops:
            out.append(Alert(
                category=INFORMATION, severity=HIGH,
                title=f"Wallet {addr[:8]}… shows circular fund flow",
                detail=(f"{len(loops)} circular transfer pattern(s) detected "
                        f"in the sampled window. The meme-coin paper's "
                        f"manipulation layer treats looping transfers between "
                        f"related wallets as a signal that apparent liquidity "
                        f"may be coordinated rather than genuine."),
                threshold=">=1 circular transfer pair",
                source=f"on-chain transactions for {addr}",
                paper="Meme coin trading strategies (LeapSpace)",
                action="Treat this wallet's liquidity as unreliable; exclude "
                       "the token it dominates from the candidate list.",
                data={"symbol": addr, "key": "wallet_loops",
                      "loops": loops[:3]},
                provenance=provenance))
        if self_trades:
            out.append(Alert(
                category=INFORMATION, severity=MEDIUM,
                title=f"Wallet {addr[:8]}… shows self-transfers",
                detail=(f"{len(self_trades)} transfer(s) with the same sender "
                        f"and receiver. The paper lists self-trading "
                        f"structures as a manipulation marker."),
                threshold=">=1 self-transfer",
                source=f"on-chain transactions for {addr}",
                paper="Meme coin trading strategies (LeapSpace)",
                action="Discount reported volume from this wallet.",
                data={"symbol": addr, "key": "wallet_self_trade",
                      "count": len(self_trades)},
                provenance=provenance))
    if concentration:
        top1 = concentration.get("top1_pct_of_covered")
        top10 = concentration.get("top10_pct_of_covered")
        thr = _t("top_holder_pct")
        if top1 is not None and top1 >= thr:
            out.append(Alert(
                category=INFORMATION, severity=HIGH,
                title=f"Holder concentration {top1:.1f}% on "
                      f"{concentration.get('mint', '')[:8]}…",
                detail=(f"The largest covered account holds {top1:.1f}% of "
                        f"the covered supply (top 10: {top10:.1f}%). "
                        f"{concentration.get('structural_risk_read', '')}"),
                threshold=f"largest covered holder >= {thr:.0f}%",
                source="on-chain holder accounts",
                paper="Meme coin trading strategies (LeapSpace)",
                action="Reject the token on the structural-safety layer.",
                data={"symbol": concentration.get("mint"), "key": "concentration",
                      "top1_pct": top1, "top10_pct": top10},
                provenance=provenance))
    return out


def memecoin_alerts(screen: Dict[str, Any], provenance: str = "") -> List[Alert]:
    """Alerts from a meme-coin screen result."""
    out: List[Alert] = []
    for r in screen.get("results", []) or []:
        symbol = r.get("symbol") or r.get("mint", "?")
        if not r.get("passed"):
            disq = r.get("disqualifiers") or []
            if disq:
                out.append(Alert(
                    category=INFORMATION, severity=MEDIUM,
                    title=f"{symbol} failed the meme-coin screen",
                    detail="; ".join(disq[:4]),
                    threshold="any hard layer failed "
                              "(structural safety / exit quality / survival / "
                              "manipulation)",
                    source="Jupiter + RugCheck + DexScreener",
                    paper="Meme coin trading strategies (LeapSpace)",
                    action="Exclude from the candidate list.",
                    data={"symbol": symbol, "key": "memecoin_fail",
                          "disqualifiers": disq},
                    provenance=provenance))
        else:
            out.append(Alert(
                category=INFORMATION, severity=MEDIUM,
                title=f"{symbol} passed the meme-coin screen",
                detail="; ".join(r.get("reasons", [])[:3]),
                threshold="all four hard layers passed",
                source="Jupiter + RugCheck + DexScreener",
                paper="Meme coin trading strategies (LeapSpace)",
                action="Still requires a wallet-level manipulation check on "
                       "the top holders before entry.",
                data={"symbol": symbol, "key": "memecoin_pass",
                      "score": r.get("score")},
                provenance=provenance))
    return out


# --------------------------------------------------------------------------
# Action alerts — the papers' own execution mapping
# --------------------------------------------------------------------------


def action_alerts(regime_result: Any = None, gamma: Any = None,
                   flow: Any = None, symbol: str = "MARKET",
                   provenance: str = "") -> List[Alert]:
    """The ACTION layer: what the papers say to DO, given the current state.

    This is the part the papers are most specific about:

      NASDAQ paper, "Execution Rules by Regime":
        "Use more passive execution when depth is adequate, spreads are
         narrower, and imbalance is not strongly one-sided"
        "Use more aggressive execution when imbalance is one-sided,
         volatility is elevated, spreads reflect informed trading, or
         immediacy is critical"
        "Reduce size or avoid trading in low-depth, high-fragility states"
        "Fade less and follow more when short-gamma dynamics likely amplify
         price movement"
        "Fade more and chase less when gamma is stabilizing and strike
         pinning is plausible"

      Gamma paper, "Practical interpretation":
        "Use option flow as a near-term pressure signal"
        "Use gamma as a regime signal"
        "Use implied volatility as the baseline forecast"
    """
    out: List[Alert] = []

    # --- regime-driven action -------------------------------------------
    if regime_result is not None:
        labels = regime_result.label_series_filtered
        if labels and labels[-1]:
            label = labels[-1]
            p = regime_result.probability_of(label)
            p_val = p[-1] if p else None
            actions = {
                "tranquil_uptrend": (
                    "MOMENTUM ON. Run momentum in this orderly trend state; "
                    "reversal off. Full size is appropriate.",
                    "Financial market regime identification (LeapSpace)"),
                "high_vol_uptrend": (
                    "MOMENTUM REDUCED. The market is trending but volatility is "
                    "high — take momentum selectively and cut size. The papers "
                    "treat high-volatility states as distinct from calm trends.",
                    "Financial market regime identification (LeapSpace)"),
                "range_chop": (
                    "MOMENTUM OFF, MEAN REVERSION ON. In a range/chop state the "
                    "papers favour short-horizon mean reversion over trend "
                    "following, and low exposure.",
                    "Financial market regime identification (LeapSpace); "
                    "Free trading indicators for directional edge (LeapSpace)"),
                "regular_bear": (
                    "MOMENTUM OFF, CAUTIOUS. Reduce size; some reversal setups "
                    "are available. Momentum weakens sharply in downturns.",
                    "Financial market regime identification (LeapSpace)"),
                "crash_rebound": (
                    "MOMENTUM OFF — THIS IS THE MOMENTUM-CRASH STATE. The "
                    "papers link momentum crashes to high volatility, prior "
                    "declines and rebounds. Use reversal/liquidity-provision "
                    "instead, at minimal size.",
                    "Financial market regime identification (LeapSpace)"),
            }
            if label in actions:
                text, paper = actions[label]
                out.append(Alert(
                    category=ACTION,
                    severity=HIGH if label == "crash_rebound" else MEDIUM,
                    title=f"{symbol}: {label.replace('_', ' ')}",
                    detail=(f"Current regime is '{label}'"
                            + (f" with posterior {p_val:.0%}" if p_val is not None else "")
                            + f". {text}"),
                    threshold="current regime state",
                    source="regime model",
                    paper=paper,
                    action=text,
                    data={"symbol": symbol, "key": f"action_regime_{label}",
                          "regime": label, "posterior": p_val},
                    provenance=provenance))

    # --- gamma-driven action --------------------------------------------
    if gamma is not None and gamma.sign is not None and gamma.sign != 0:
        if gamma.sign < 0:
            text = ("SHORT GAMMA: FADE LESS, FOLLOW MORE. Hedging flows may "
                    "amplify the move. Follow breaks, use faster exits, and "
                    "be more aggressive with execution.")
        else:
            text = ("POSITIVE GAMMA: FADE MORE, CHASE LESS. Hedging flows tend "
                    "to damp the move and pinning is plausible. Fade "
                    "extensions, use passive execution, smaller targets.")
        out.append(Alert(
            category=ACTION, severity=HIGH if gamma.sign < 0 else MEDIUM,
            title=f"{symbol}: execution posture from gamma",
            detail=(f"{text} Net gamma {gamma.net_gamma:,.0f}; max-pain "
                    f"strike {gamma.max_pain_strike}; zero-gamma strike "
                    f"{gamma.zero_gamma_strike}."),
            threshold="sign of net dealer gamma",
            source=f"option chain for {gamma.underlying}",
            paper="NASDAQ market regime identification (LeapSpace); "
                  "Options market dynamics and volatility (LeapSpace)",
            action=text,
            data={"symbol": gamma.underlying, "key": "action_gamma",
                  "sign": gamma.sign},
            provenance=provenance))

    # --- flow-driven action ---------------------------------------------
    if flow is not None and flow.put_call_volume_ratio is not None:
        ratio = flow.put_call_volume_ratio
        thr = _t("put_call_volume_ratio")
        if ratio >= thr:
            out.append(Alert(
                category=ACTION, severity=MEDIUM,
                title=f"{flow.underlying}: treat flow as volatility pressure",
                detail=(f"Put/call volume ratio {ratio:.2f}. The papers' "
                        f"finding is that volatility-strategy order flow "
                        f"predicts next-day REALISED VOLATILITY but not "
                        f"next-day index returns, and that flow may reflect "
                        f"hedging or vol demand rather than informed "
                        f"direction. Use it as a volatility-context variable, "
                        f"not as a directional vote."),
                threshold=f"put/call volume ratio >= {thr}",
                source=f"option chain for {flow.underlying}",
                paper="Options market dynamics and volatility (LeapSpace); "
                      "NASDAQ market regime identification (LeapSpace)",
                action="Do not read this as a directional signal; use it to "
                       "set volatility expectations and position size.",
                data={"symbol": flow.underlying, "key": "action_flow",
                      "ratio": ratio},
                provenance=provenance))
    return out


# --------------------------------------------------------------------------
# Engine: collect, dedupe against prior state, render
# --------------------------------------------------------------------------


class AlertEngine:
    """Collects alerts, suppresses repeats against a state file, renders."""

    def __init__(self, state_path: Optional[str] = None):
        self.state_path = state_path
        self.alerts: List[Alert] = []
        self.gaps: List[Dict[str, Any]] = []
        self._prior: set = set()
        if state_path:
            blob = read_json(state_path, {}) or {}
            self._prior = set(blob.get("fingerprints") or [])

    def add(self, alerts: Sequence[Alert]) -> None:
        self.alerts.extend(alerts)

    def add_gap(self, gap: Dict[str, Any]) -> None:
        self.gaps.append(gap)

    def new_alerts(self) -> List[Alert]:
        """Alerts not seen in a previous run."""
        out = []
        seen = set()
        for a in self.alerts:
            fp = a.fingerprint()
            if fp in self._prior or fp in seen:
                continue
            seen.add(fp)
            out.append(a)
        return out

    def render(self, only_new: bool = True, show_thresholds: bool = True) -> str:
        items = self.new_alerts() if only_new else self.alerts
        order = {HIGH: 0, MEDIUM: 1, LOW: 2}
        items = sorted(items, key=lambda a: (order.get(a.severity, 3),
                                             a.category))
        lines: List[str] = []
        if items:
            lines.append("=" * 72)
            lines.append("ALERTS")
            lines.append("=" * 72)
            for a in items:
                lines.append(a.render())
                lines.append("")
        else:
            lines.append("No new alerts (quiet tick).")
            lines.append("")
        if self.gaps:
            lines.append("=" * 72)
            lines.append("SOURCE GAPS — no data was substituted for these")
            lines.append("=" * 72)
            for g in self.gaps:
                lines.append(f"- {g.get('source')}: {g.get('reason')}")
            lines.append("")
        if show_thresholds:
            lines.append("=" * 72)
            lines.append("THRESHOLDS USED (all analyst choices unless noted)")
            lines.append("=" * 72)
            for k, v in ALERT_THRESHOLDS.items():
                lines.append(f"- {k} = {v['value']}  [{v['source']}] {v['note']}")
            lines.append("")
        return "\n".join(lines)

    def save_state(self) -> Optional[str]:
        if not self.state_path:
            return None
        fps = list(self._prior) + [a.fingerprint() for a in self.alerts]
        # Keep the last 500 fingerprints.
        write_json(self.state_path, {"fingerprints": fps[-500:],
                                     "updated_at": _dt.datetime.now(
                                         _dt.timezone.utc).isoformat()})
        return self.state_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alerts": [a.to_dict() for a in self.alerts],
            "new_count": len(self.new_alerts()),
            "gaps": self.gaps,
            "thresholds": ALERT_THRESHOLDS,
        }
