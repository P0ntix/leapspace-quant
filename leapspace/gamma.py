"""
Dealer gamma exposure and option-flow measures.

Source paper: "Gamma exposure and option flow" (LeapSpace), with the NASDAQ
paper's four-axis framework supplying the execution interpretation.

What the paper actually claims, and what this module therefore computes:

  1. "Use option flow as a near-term pressure signal. Buying pressure and
     order imbalance can flag impending volatility changes."
  2. "Use gamma as a regime signal. Negative gamma suggests hedging flows
     may push volatility higher and create momentum, while positive gamma
     tends to damp volatility."
  3. "Use implied volatility as the baseline forecast."
  4. NASDAQ paper: "Normalize option flow by exposure. Raw contract counts are
     too blunt." -> all flow measures here are delta/vega/notional adjusted.

MODEL LIMITATIONS THAT MUST BE STATED WITH EVERY NUMBER (the NASDAQ paper's
own "failure modes" section):
  * Gamma is computed from a SINGLE aggregate open-interest snapshot under an
    ASSUMED dealer book. We assume customers are net long calls and net long
    puts (the standard convention): dealers are short calls, long puts.
    This assumption is NOT verifiable from open interest alone.
  * Single-stock gamma estimates are severely noisy (cited ref 27).
  * Black-Scholes gammas are biased under real smiles/skews (ref 25).
  * Open interest is a snapshot and goes stale between refreshes.
  * No live IV surface is available from the free chain endpoint, so IV is
    derived from the last trade price where present and is APPROXIMATE.

These caveats are returned inside the result object and are rendered by the
report writer, so a number never travels without its caveat.
"""

from __future__ import annotations

from .stats import norm_cdf as _norm_cdf

import datetime as _dt
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Black-Scholes greeks
# --------------------------------------------------------------------------


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def bs_greeks(spot: float, strike: float, t_years: float, rate: float,
              iv: float, dividend_yield: float = 0.0
              ) -> Dict[str, float]:
    """Black-Scholes delta, gamma, vega, theta.

    t_years <= 0 or iv <= 0 returns zeros rather than raising: an expired
    contract has no gamma, and a contract with no quoted price has no IV.
    """
    if t_years <= 0 or iv <= 0 or spot <= 0 or strike <= 0:
        return {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0}
    s = math.sqrt(t_years)
    d1 = (math.log(spot / strike) + (rate - dividend_yield + 0.5 * iv * iv) * t_years) / (iv * s)
    d2 = d1 - iv * s
    df = math.exp(-rate * t_years)
    delta_call = math.exp(-dividend_yield * t_years) * _norm_cdf(d1)
    gamma = (math.exp(-dividend_yield * t_years) * _norm_pdf(d1)) / (spot * iv * s)
    vega = spot * math.exp(-dividend_yield * t_years) * _norm_pdf(d1) * s / 100.0
    theta = (-(spot * math.exp(-dividend_yield * t_years) * _norm_pdf(d1) * iv) / (2.0 * s)
             - rate * strike * df * _norm_cdf(d2)
             + dividend_yield * spot * math.exp(-dividend_yield * t_years) * _norm_cdf(d1))
    return {
        "delta_call": delta_call,
        "delta_put": delta_call - math.exp(-dividend_yield * t_years),
        "gamma": gamma,
        "vega": vega,
        "theta": theta,
    }


def bs_price(spot: float, strike: float, t_years: float, rate: float,
             iv: float, option_type: str, dividend_yield: float = 0.0) -> float:
    """Black-Scholes European option price."""
    if t_years <= 0 or iv <= 0 or spot <= 0 or strike <= 0:
        return 0.0
    s = math.sqrt(t_years)
    d1 = (math.log(spot / strike) + (rate - dividend_yield + 0.5 * iv * iv) * t_years) / (iv * s)
    d2 = d1 - iv * s
    df_r = math.exp(-rate * t_years)
    df_q = math.exp(-dividend_yield * t_years)
    if option_type == "put":
        return (strike * df_r * _norm_cdf(-d2) - spot * df_q * _norm_cdf(-d1))
    return (spot * df_q * _norm_cdf(d1) - strike * df_r * _norm_cdf(d2))


def implied_vol_from_price(price: float, spot: float, strike: float,
                           t_years: float, rate: float, option_type: str,
                           dividend_yield: float = 0.0,
                           lo: float = 0.01, hi: float = 5.0) -> Optional[float]:
    """Bisection implied vol from a traded premium. None if it does not converge.

    The premium must lie inside the no-arbitrage envelope for the bisection
    to be meaningful; outside it, the answer is None rather than a clamped
    number that would silently feed a wrong gamma.
    """
    if price is None or price <= 0 or spot <= 0 or strike <= 0 or t_years <= 0:
        return None
    intrinsic_call = max(0.0, spot - strike * math.exp(-rate * t_years))
    intrinsic_put = max(0.0, strike * math.exp(-rate * t_years) - spot)
    intrinsic = intrinsic_call if option_type == "call" else intrinsic_put
    upper = spot if option_type == "call" else strike
    if price < intrinsic - 1e-9 or price > upper + 1e-9:
        return None

    plo = bs_price(spot, strike, t_years, rate, lo, option_type, dividend_yield)
    phi = bs_price(spot, strike, t_years, rate, hi, option_type, dividend_yield)
    if plo > price or phi < price:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2.0
        pm = bs_price(spot, strike, t_years, rate, mid, option_type, dividend_yield)
        if pm > price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# --------------------------------------------------------------------------
# Expiry parsing
# --------------------------------------------------------------------------

_MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
           "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}


def parse_expiry(text: str, reference: Optional[_dt.date] = None) -> Optional[_dt.date]:
    """Parse the expiry strings the sources actually use.

    Nasdaq: "Oct 27", "January 16, 2027", "2026-11-20".
    Deribit: "27OCT26".
    Returns None when the format is not recognised — never a guess.
    """
    if not text:
        return None
    s = str(text).strip()
    ref = reference or _dt.date.today()

    # ISO
    try:
        return _dt.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        pass
    # "Oct 27"
    for fmt in ("%b %d", "%B %d"):
        try:
            d = _dt.datetime.strptime(s, fmt).date()
            year = ref.year + (1 if d.month < ref.month - 6 else 0)
            return d.replace(year=year)
        except ValueError:
            continue
    # "January 16, 2027"
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y"):
        try:
            return _dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # "2026-11-20T00:00:00Z" style
    try:
        return _dt.datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        pass
    # Deribit "27OCT26"
    for fmt in ("%d%b%y", "%d%b%Y"):
        try:
            return _dt.datetime.strptime(s.upper(), fmt).date()
        except ValueError:
            continue
    return None


def year_fraction(expiry: _dt.date, as_of: Optional[_dt.date] = None) -> float:
    ref = as_of or _dt.date.today()
    return max(0.0, (expiry - ref).days / 365.25)


# --------------------------------------------------------------------------
# Gamma exposure
# --------------------------------------------------------------------------

CONTRACT_MULTIPLIER = 100


@dataclass
class GammaExposure:
    underlying: str
    spot: Optional[float]
    as_of: Optional[str]
    net_gamma: float = 0.0
    call_gamma: float = 0.0
    put_gamma: float = 0.0
    gross_gamma: float = 0.0
    gamma_by_expiry: Dict[str, float] = field(default_factory=dict)
    max_pain_strike: Optional[float] = None
    zero_gamma_strike: Optional[float] = None
    n_contracts: int = 0
    total_oi: float = 0.0
    total_volume: float = 0.0
    assumptions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    provenance_note: str = ""

    @property
    def sign(self) -> Optional[int]:
        if abs(self.net_gamma) < 1e-9:
            return 0
        return 1 if self.net_gamma > 0 else -1

    @property
    def state(self) -> str:
        """The paper's regime read of the gamma sign."""
        s = self.sign
        if s is None:
            return "unknown"
        if s > 0:
            return "positive_gamma_damping"
        if s < 0:
            return "negative_gamma_amplifying"
        return "flat_gamma"

    def interpretation(self) -> str:
        """The NASDAQ paper's execution mapping, in its own terms."""
        st = self.state
        if st == "negative_gamma_amplifying":
            return ("Negative net gamma: hedging flows may amplify price moves. "
                    "Paper guidance: treat as a momentum/breakout regime; follow "
                    "breaks, use faster exits, more aggressive execution.")
        if st == "positive_gamma_damping":
            return ("Positive net gamma: hedging flows tend to damp moves. "
                    "Paper guidance: treat as a mean-reversion/pinning regime; "
                    "fade extensions, use passive execution, smaller targets.")
        if st == "flat_gamma":
            return ("Net gamma approximately zero: the model cannot determine a "
                    "damping/amplifying state. Do not infer one.")
        return ("Net gamma could not be computed (insufficient or unusable "
                "open interest). No regime read is possible.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "underlying": self.underlying,
            "spot": self.spot,
            "as_of": self.as_of,
            "net_gamma": self.net_gamma,
            "call_gamma": self.call_gamma,
            "put_gamma": self.put_gamma,
            "gross_gamma": self.gross_gamma,
            "gamma_by_expiry": self.gamma_by_expiry,
            "max_pain_strike": self.max_pain_strike,
            "zero_gamma_strike": self.zero_gamma_strike,
            "n_contracts": self.n_contracts,
            "total_open_interest": self.total_oi,
            "total_volume": self.total_volume,
            "sign": self.sign,
            "state": self.state,
            "interpretation": self.interpretation(),
            "assumptions": self.assumptions,
            "warnings": self.warnings,
            "provenance": self.provenance_note,
        }


DEFAULT_ASSUMPTIONS = [
    "Dealer positioning is ASSUMED from customer-side open interest: "
    "customers net long calls and net long puts, so dealers are short calls "
    "and long puts. Open interest alone cannot verify this.",
    "Gamma is Black-Scholes with a flat volatility surface per contract; "
    "real smiles and smirks bias these estimates (paper ref 25).",
    "IV is derived from last-trade prices where available and is APPROXIMATE; "
    "some contracts have no usable quote and are excluded.",
    "Expiry year inference assumes the next occurrence of the stated month.",
]


def compute_gamma_exposure(chain: Dict[str, Any], spot: Optional[float] = None,
                           rate: float = 0.04,
                           dividend_yield: float = 0.0,
                           as_of_date: Optional[_dt.date] = None,
                           min_oi: float = 1.0,
                           ) -> GammaExposure:
    """Compute dealer net gamma exposure from an option chain."""
    underlying = chain.get("underlying", "?")
    spot = spot if spot is not None else chain.get("spot")
    warnings: List[str] = []
    if not spot:
        warnings.append("Underlying price unavailable; gamma cannot be scaled to "
                        "notional and is reported in contract units only.")
    ref = as_of_date or _dt.date.today()

    res = GammaExposure(underlying=underlying, spot=spot, as_of=chain.get("as_of"),
                        assumptions=list(DEFAULT_ASSUMPTIONS), warnings=warnings)

    by_exp: Dict[str, float] = {}
    oi_by_strike: Dict[float, float] = {}
    for c in chain.get("contracts", []):
        oi = c.get("open_interest") or 0.0
        vol = c.get("volume") or 0.0
        res.n_contracts += 1
        res.total_oi += oi
        res.total_volume += vol
        if oi < min_oi:
            continue
        exp = parse_expiry(c.get("expiry", ""), ref)
        if exp is None:
            warnings.append(f"Unparsed expiry {c.get('expiry')!r} — contract excluded.")
            continue
        t = year_fraction(exp, ref)
        if t <= 0:
            continue
        strike = c.get("strike")
        iv = c.get("implied_vol")
        if iv is None:
            last = c.get("last")
            if last is None or last <= 0:
                continue
            iv = implied_vol_from_price(float(last), float(spot or strike),
                                        float(strike), t, rate, c["type"],
                                        dividend_yield)
            if iv is None:
                continue
        g = bs_greeks(float(spot or strike), float(strike), t, rate,
                      float(iv), dividend_yield)["gamma"]
        # Dealer sign convention: dealers short calls, long puts.
        signed_gamma = -g * oi * CONTRACT_MULTIPLIER if c["type"] == "call" else \
                       +g * oi * CONTRACT_MULTIPLIER
        res.call_gamma += signed_gamma if c["type"] == "call" else 0.0
        res.put_gamma += signed_gamma if c["type"] == "put" else 0.0
        res.net_gamma += signed_gamma
        res.gross_gamma += abs(signed_gamma)
        by_exp[c["expiry"]] = by_exp.get(c["expiry"], 0.0) + signed_gamma
        oi_by_strike[strike] = oi_by_strike.get(strike, 0.0) + oi

    res.gamma_by_expiry = by_exp
    if oi_by_strike:
        # Max pain: the strike where open interest is most concentrated
        # against the holder side — approximated by the strike with the
        # largest total OI differential between calls and puts.
        call_oi: Dict[float, float] = {}
        put_oi: Dict[float, float] = {}
        for c in chain.get("contracts", []):
            if (c.get("open_interest") or 0) < min_oi:
                continue
            tgt = call_oi if c["type"] == "call" else put_oi
            tgt[c["strike"]] = tgt.get(c["strike"], 0.0) + (c.get("open_interest") or 0.0)
        strikes = sorted(set(call_oi) | set(put_oi))
        if strikes:
            res.max_pain_strike = max(
                strikes, key=lambda k: (put_oi.get(k, 0.0) - call_oi.get(k, 0.0)))
        # Zero gamma: the strike where cumulative net gamma crosses zero.
        # Cumulative net gamma over strikes is the standard approximation.
        cum = 0.0
        prev = 0.0
        for k in sorted(oi_by_strike):
            call_g = 0.0
            put_g = 0.0
            for c in chain.get("contracts", []):
                if c.get("strike") != k or (c.get("open_interest") or 0) < min_oi:
                    continue
                exp = parse_expiry(c.get("expiry", ""), ref)
                if exp is None:
                    continue
                t = year_fraction(exp, ref)
                if t <= 0:
                    continue
                iv = c.get("implied_vol") or 0.25
                g = bs_greeks(float(spot or k), float(k), t, rate, float(iv),
                              dividend_yield)["gamma"]
                oi = c.get("open_interest") or 0.0
                if c["type"] == "call":
                    call_g += -g * oi * CONTRACT_MULTIPLIER
                else:
                    put_g += +g * oi * CONTRACT_MULTIPLIER
            cum += call_g + put_g
            if prev != 0 and (prev > 0) != (cum > 0):
                res.zero_gamma_strike = k
                break
            prev = cum
    return res


# --------------------------------------------------------------------------
# Option flow — exposure-adjusted, never raw contract counts
# --------------------------------------------------------------------------


@dataclass
class OptionFlow:
    underlying: str
    call_volume: float = 0.0
    put_volume: float = 0.0
    call_oi: float = 0.0
    put_oi: float = 0.0
    net_delta_flow: float = 0.0
    net_vega_flow: float = 0.0
    net_notional_flow: float = 0.0
    put_call_volume_ratio: Optional[float] = None
    put_call_oi_ratio: Optional[float] = None
    directional_flow: float = 0.0
    volume_implied: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    provenance_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "underlying": self.underlying,
            "call_volume": self.call_volume,
            "put_volume": self.put_volume,
            "call_open_interest": self.call_oi,
            "put_open_interest": self.put_oi,
            "net_delta_flow": self.net_delta_flow,
            "net_vega_flow": self.net_vega_flow,
            "net_notional_flow": self.net_notional_flow,
            "put_call_volume_ratio": self.put_call_volume_ratio,
            "put_call_oi_ratio": self.put_call_oi_ratio,
            "directional_flow": self.directional_flow,
            "volume_implied": self.volume_implied,
            "warnings": self.warnings,
            "provenance": self.provenance_note,
        }


def compute_option_flow(chain: Dict[str, Any], spot: Optional[float] = None,
                        rate: float = 0.04, dividend_yield: float = 0.0,
                        as_of_date: Optional[_dt.date] = None,
                        ) -> OptionFlow:
    """Exposure-adjusted option flow.

    Raw contract counts are explicitly rejected by the NASDAQ paper. Three
    normalisations are computed:
      * delta-adjusted  (directional pressure)
      * vega-adjusted   (volatility demand)
      * notional-adjusted (dollar pressure)

    The paper's finding (ref 24) is that volatility-strategy order flow
    predicts realised volatility while NOT predicting index returns — so
    directional and vega flow are reported separately and never summed into
    one "bullish" number.
    """
    spot = spot if spot is not None else chain.get("spot")
    ref = as_of_date or _dt.date.today()
    flow = OptionFlow(underlying=chain.get("underlying", "?"),
                      provenance_note=chain.get("as_of", ""))

    for c in chain.get("contracts", []):
        vol = c.get("volume") or 0.0
        oi = c.get("open_interest") or 0.0
        strike = float(c.get("strike") or 0.0)
        if c["type"] == "call":
            flow.call_volume += vol
            flow.call_oi += oi
        else:
            flow.put_volume += vol
            flow.put_oi += oi
        if vol <= 0:
            continue
        exp = parse_expiry(c.get("expiry", ""), ref)
        if exp is None:
            continue
        t = year_fraction(exp, ref)
        if t <= 0:
            continue
        iv = c.get("implied_vol") or 0.25
        g = bs_greeks(float(spot or strike), strike, t, rate, float(iv),
                      dividend_yield)
        # Signed by side: a call buy is positive delta pressure, a put buy is
        # negative. Sign convention: positive = bullish/directional pressure.
        sign = 1.0 if c["type"] == "call" else -1.0
        flow.net_delta_flow += sign * abs(g["delta_call"]) * vol
        flow.net_vega_flow += sign * g["vega"] * vol
        flow.net_notional_flow += sign * vol * strike * CONTRACT_MULTIPLIER

    if flow.call_volume > 0:
        flow.put_call_volume_ratio = flow.put_volume / flow.call_volume
    if flow.call_oi > 0:
        flow.put_call_oi_ratio = flow.put_oi / flow.call_oi

    total_delta = flow.net_delta_flow
    gross = sum(abs(v) for v in [flow.net_delta_flow])
    flow.directional_flow = (total_delta / gross) if gross else 0.0

    if flow.put_call_volume_ratio is not None:
        # A simple, disclosed mapping of the put/call volume ratio to an
        # implied volatility level. This is an ANALYST MAPPING, not a paper
        # result: the papers establish the mechanism, not this calibration.
        flow.volume_implied = max(0.05, min(1.50, 0.20 * flow.put_call_volume_ratio + 0.15))
        flow.warnings.append(
            "volume_implied is an analyst mapping from the put/call volume "
            "ratio, not a value published by the source and not a paper result.")
    return flow


def merge_flow_and_gamma(flow: OptionFlow, gamma: GammaExposure
                         ) -> Dict[str, Any]:
    """The paper's combined read: flow says what pressure exists, gamma says
    what the market will do with it."""
    out = {
        "flow": flow.to_dict(),
        "gamma": gamma.to_dict(),
        "combined_state": gamma.state,
        "note": ("Option flow (pressure) and gamma (amplification) are "
                 "independent axes. The papers state them separately and do "
                 "not provide a calibrated joint rule, so no combined "
                 "directional call is made here."),
    }
    if flow.volume_implied is not None:
        out["iv_context"] = {
            "volume_implied": flow.volume_implied,
            "note": "IV is the baseline volatility forecast per the paper; "
                    "this is the volume-derived estimate only.",
        }
    return out
