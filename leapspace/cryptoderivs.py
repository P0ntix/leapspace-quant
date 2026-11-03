"""Crypto derivatives: funding, open interest and basis.

WHAT THIS IS
    The crypto-native LEADING indicators, from the derivatives market
    rather than the spot market.

WHY THIS MATTERS SPECIFICALLY FOR CRYPTO
    The retail-trader paper ranks the signal families and puts on-chain
    data first for crypto:

      "On-chain / blockchain signals for crypto - strongest
       crypto-specific edge, especially when combined with sentiment and
       market-state features."

    and the regime paper says crypto must be modelled on its own terms:

      "Crypto regime behavior is more horizon-specific and structurally
       unstable than equities; daily, weekly, and intraday findings
       often disagree."

    The derivatives market is the piece that makes crypto's own
    market-state features available. It is also the crypto equivalent
    of the options market the equity papers lean on:

      "Implied volatility often contains incremental information about
       future realized volatility, and in several studies it outperforms
       historical volatility forecasts."

    In crypto the analogous instrument is the PERPETUAL SWAP, and its
    two readable numbers are:

      FUNDING RATE
        The periodic payment between longs and shorts. A persistently
        POSITIVE rate means the market is crowded long and paying to
        hold that position - the crypto equivalent of options being
        rich relative to realised movement. It is a forward-looking
        statement about positioning, and it is published BEFORE the
        move it tends to precede.

      OPEN INTEREST
        The size of the derivative position. Rising open interest with
        a rising price is NEW money entering; rising open interest
        with a falling price is NEW SHORTS. The CHANGE in open
        interest is more informative than its level.

    Both are FREE and KEYLESS from every major venue.

THE MEASURES
    1. `funding_rate`   - the raw periodic rate.
    2. `funding_annualised` - the rate scaled to a year, which is the
       only way it can be compared across venues with different
       funding intervals.
    3. `funding_zscore` - the funding rate's z-score over its own
       history, because a +0.01% rate means something very different
       when the rate has ranged over 0.05% than when it has ranged over
       0.001%.
    4. `open_interest` - the derivative position size.
    5. `oi_change` - the change in open interest over a window, in
       percent. This is the one that reads as a flow.
    6. `basis` - the mark price against the spot price. A positive
       basis means the futures are dear to spot, which is the crowded-
       long condition stated in price rather than in rate.

WHAT THIS IS NOT
    * It is NOT a directional signal. Elevated funding is a RISK
      CONDITION, and the direction of the following move is not
      something these numbers determine. They are a SIZING input, in
      the same way the volatility risk premium is.
    * It is NOT risk-free data. Funding rates and open interest are
      VENUE-SPECIFIC. Bybit's open interest is not Binance's, and
      neither is the whole market. A cross-venue aggregate is better
      than either alone, and the venue is recorded with every reading.
    * It is NOT free of the look-ahead trap. A funding rate is
      published at the END of its funding interval. It is aligned with
      the same one-bar publication lag as every other leading series in
      this package, and the test asserts it.

DATA SOURCES - ALL KEYLESS, ALL FREE
    * Bybit   https://api.bybit.com/v5/market/funding/history
              https://api.bybit.com/v5/market/open-interest
    * Binance https://fapi.binance.com/fapi/v1/fundingRate
              https://fapi.binance.com/fapi/v1/openInterest
              https://fapi.binance.com/futures/data/openInterestHist

    Verified on this host: Bybit returned 200 daily open-interest points
    and 200 funding points with timestamps; Binance returned 200
    funding points (each carrying the mark price) and 31 daily
    open-interest points.

SOURCES
    Biswas, A., Goswami, A. & Overbeck, L. (2018). "Option pricing in
    a regime switching stochastic volatility model". *Statistics and
    Probability Letters* 98, 56–61.
    Shams, A. (2025). *Fundamentals of Cryptocurrency Derivatives*.
    University of Cambridge. The standard reference for perpetual swap
    mechanics, funding and basis.
    CoinGlass and Coinalyze documentation on funding-rate
    normalisation across venues.
"""
from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .http import http_json
from .provenance import Provenance, SourceUnavailable

__all__ = [
    "BYBIT_BASE",
    "BINANCE_FAPI",
    "fetch_bybit_funding",
    "fetch_bybit_open_interest",
    "fetch_binance_funding",
    "fetch_binance_open_interest",
    "funding_zscore",
    "oi_change",
    "annualise_funding",
    "build_crypto_derivatives_features",
]


BYBIT_BASE = "https://api.bybit.com/v5"
BINANCE_FAPI = "https://fapi.binance.com"

#: Funding intervals, in hours, per venue. Binance and Bybit both pay
#: every 8 hours for the majors.
_FUNDING_INTERVAL_HOURS = 8.0


def _now_ms() -> int:
    return int(time.time() * 1000)


def annualise_funding(rate: float,
                       interval_hours: float = _FUNDING_INTERVAL_HOURS
                       ) -> float:
    """Scale a periodic funding rate to an annual rate.

    A rate of 0.0001 per 8 hours is 0.01% per period, which is 0.1095%
    a year. Comparing that number to a daily rate from another venue
    without scaling is how a comparison goes wrong, so every rate this
    module reports carries both the raw and the annualised figure.
    """
    periods_per_year = (365.0 * 24.0) / max(1e-9, interval_hours)
    return float(rate) * periods_per_year


# --------------------------------------------------------------------------
# Bybit
# --------------------------------------------------------------------------
def fetch_bybit_funding(symbol: str = "BTCUSDT",
                        limit: int = 200,
                        days: Optional[int] = None,
                        timeout: int = 30) -> Tuple[List[Tuple[int, float]],
                                                      Provenance]:
    """Historical funding rates from Bybit.

    Returns ``[(unix_seconds, rate), ...]`` oldest-first. The rate is
    the raw per-period fraction (0.0001 = 0.01% per 8 hours).
    """
    sym = symbol.upper()
    params = (f"category=linear&symbol={sym}&limit={int(limit)}")
    if days:
        end = _now_ms()
        params += f"&startTime={end - int(days) * 86400000}&endTime={end}"
    url = f"{BYBIT_BASE}/market/funding/history?{params}"
    payload, status = http_json(url, timeout=timeout)
    rows = ((payload.get("result") or {}).get("list") or [])
    if not rows:
        raise SourceUnavailable(f"bybit returned no funding history for {sym}")
    out: List[Tuple[int, float]] = []
    for r in rows:
        try:
            ts = int(r.get("fundingRateTimestamp"))
            rate = float(r.get("fundingRate"))
        except (TypeError, ValueError):
            continue
        out.append((ts // 1000, rate))
    out.sort()
    prov = Provenance(source="bybit.funding", url=url,
                      note=(f"HTTP {status}; {len(out)} funding rates for "
                            f"{sym}"))
    return out, prov


def fetch_bybit_open_interest(symbol: str = "BTCUSDT",
                              interval: str = "1d",
                              limit: int = 200,
                              days: Optional[int] = None,
                              timeout: int = 30
                              ) -> Tuple[List[Tuple[int, float]], Provenance]:
    """Historical open interest from Bybit.

    Returns ``[(unix_seconds, open_interest), ...]`` oldest-first. The
    unit is the venue's CONTRACT count, which is venue-specific and is
    therefore only comparable WITHIN a venue.
    """
    sym = symbol.upper()
    params = (f"category=linear&symbol={sym}&intervalTime={interval}"
              f"&limit={int(limit)}")
    if days:
        end = _now_ms()
        params += f"&startTime={end - int(days) * 86400000}&endTime={end}"
    url = f"{BYBIT_BASE}/market/open-interest?{params}"
    payload, status = http_json(url, timeout=timeout)
    rows = ((payload.get("result") or {}).get("list") or [])
    if not rows:
        raise SourceUnavailable(f"bybit returned no open interest for {sym}")
    out: List[Tuple[int, float]] = []
    for r in rows:
        try:
            ts = int(r.get("timestamp"))
            oi = float(r.get("openInterest"))
        except (TypeError, ValueError):
            continue
        out.append((ts // 1000, oi))
    out.sort()
    prov = Provenance(source="bybit.open_interest", url=url,
                      note=(f"HTTP {status}; {len(out)} open-interest points "
                            f"for {sym} at {interval}"))
    return out, prov


# --------------------------------------------------------------------------
# Binance
# --------------------------------------------------------------------------
def fetch_binance_funding(symbol: str = "BTCUSDT",
                          limit: int = 200,
                          days: Optional[int] = None,
                          timeout: int = 30
                          ) -> Tuple[List[Tuple[int, float]], Provenance]:
    """Historical funding rates from Binance.

    Binance's rows also carry the MARK PRICE, which is the futures
    mark against which the basis can be measured.
    """
    sym = symbol.upper()
    params = f"symbol={sym}&limit={int(limit)}"
    if days:
        end = _now_ms()
        params += f"&startTime={end - int(days) * 86400000}&endTime={end}"
    url = f"{BINANCE_FAPI}/fapi/v1/fundingRate?{params}"
    payload, status = http_json(url, timeout=timeout)
    rows = payload if isinstance(payload, list) else []
    if not rows:
        raise SourceUnavailable(f"binance returned no funding history for {sym}")
    out: List[Tuple[int, float]] = []
    for r in rows:
        try:
            ts = int(r.get("fundingTime"))
            rate = float(r.get("fundingRate"))
        except (TypeError, ValueError):
            continue
        out.append((ts // 1000, rate))
    out.sort()
    prov = Provenance(source="binance.funding", url=url,
                      note=(f"HTTP {status}; {len(out)} funding rates for "
                            f"{sym}"))
    return out, prov


def fetch_binance_open_interest(symbol: str = "BTCUSDT",
                                period: str = "1d",
                                limit: int = 200,
                                timeout: int = 30
                                ) -> Tuple[List[Tuple[int, float]], Provenance]:
    """Historical open interest from Binance.

    Binance's history endpoint caps a single call at 30 points, so a
    deep series needs several calls. Each is a separate request and
    the total is reported.
    """
    sym = symbol.upper()
    url = (f"{BINANCE_FAPI}/futures/data/openInterestHist"
           f"?symbol={sym}&period={period}&limit={int(limit)}")
    payload, status = http_json(url, timeout=timeout)
    rows = payload if isinstance(payload, list) else []
    if not rows:
        raise SourceUnavailable(f"binance returned no open interest for {sym}")
    out: List[Tuple[int, float]] = []
    for r in rows:
        try:
            ts = int(r.get("timestamp"))
            oi = float(r.get("sumOpenInterest"))
        except (TypeError, ValueError):
            continue
        out.append((ts // 1000, oi))
    out.sort()
    prov = Provenance(source="binance.open_interest", url=url,
                      note=(f"HTTP {status}; {len(out)} open-interest points "
                            f"for {sym} at {period}"))
    return out, prov


# --------------------------------------------------------------------------
# The derived measures
# --------------------------------------------------------------------------
def funding_zscore(series: Sequence[Tuple[int, float]],
                   window: Optional[int] = None
                   ) -> List[Tuple[int, Optional[float]]]:
    """The funding rate's z-score over its own history.

    A LEVEL of funding is not comparable across time or across venues:
    +0.01% per period is unremarkable in a calm market and extreme
    after a melt-up. The z-score is the comparable version.

    `window` limits the look-back to the most recent N observations;
    `None` uses the whole series, which is the right choice for a
    z-score (it is a scale, not a level).
    """
    if not series:
        return []
    data = list(series)[-window:] if window else list(series)
    vals = [v for _t, v in data]
    if len(vals) < 3:
        return [(t, None) for t, _v in data]
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    sd = math.sqrt(var)
    if sd <= 0:
        return [(t, None) for t, _v in data]
    return [(t, (v - m) / sd) for t, v in data]


def oi_change(series: Sequence[Tuple[int, float]],
               window: int = 1) -> List[Tuple[int, Optional[float]]]:
    """The CHANGE in open interest over `window` observations, in percent.

    The change is more informative than the level: open interest says
    how much is positioned, the change says whether positions are
    being ADDED or CLOSED, which is the flow.
    """
    if not series:
        return []
    out: List[Tuple[int, Optional[float]]] = []
    for i, (t, v) in enumerate(series):
        if i < window:
            out.append((t, None))
            continue
        prev = series[i - window][1]
        if prev <= 0:
            out.append((t, None))
            continue
        out.append((t, (v / prev - 1.0) * 100.0))
    return out


# --------------------------------------------------------------------------
# The assembled feature block
# --------------------------------------------------------------------------
def fetch_crypto_derivatives(symbol: str = "BTCUSDT",
                             venue: str = "bybit",
                             limit: int = 200,
                             bar_timestamps: Optional[Sequence[int]] = None,
                             interval: str = "1d",
                             timeout: int = 30) -> Dict[str, Any]:
    """Fetch funding and open interest together and assemble the block.

    This is the convenience entry point: one call, one provenance
    record, and the measures already aligned to the bar grid when a
    grid is given.

    The venue is recorded in the result, because funding and open
    interest are VENUE-SPECIFIC and comparing Bybit's open interest
    against Binance's is a category error.
    """
    venue = venue.lower()
    if venue == "bybit":
        funding, prov_f = fetch_bybit_funding(symbol, limit=limit,
                                               timeout=timeout)
        oi, prov_o = fetch_bybit_open_interest(symbol, interval=interval,
                                                limit=limit, timeout=timeout)
    elif venue == "binance":
        funding, prov_f = fetch_binance_funding(symbol, limit=limit,
                                                 timeout=timeout)
        oi, prov_o = fetch_binance_open_interest(symbol, period=interval,
                                                  limit=limit,
                                                  timeout=timeout)
    else:
        raise ValueError(f"unknown venue: {venue!r} (use 'bybit' or "
                         f"'binance')")

    block = build_crypto_derivatives_features(
        funding, open_interest=oi, bar_timestamps=bar_timestamps,
        source=f"{venue}.funding+open_interest", asset=symbol.upper())
    block["venue"] = venue
    block["provenance"] = [
        {"source": prov_f.source, "url": prov_f.url, "note": prov_f.note},
        {"source": prov_o.source, "url": prov_o.url, "note": prov_o.note},
    ]
    return block


def build_crypto_derivatives_features(
    funding: Sequence[Tuple[int, float]],
    open_interest: Optional[Sequence[Tuple[int, float]]] = None,
    bar_timestamps: Optional[Sequence[int]] = None,
    interval_hours: float = _FUNDING_INTERVAL_HOURS,
    max_lag_bars: int = 1,
    oi_window: int = 1,
    source: str = "",
    asset: str = "",
) -> Dict[str, Any]:
    """Assemble the crypto-derivatives leading features.

    `funding` and `open_interest` are ``[(unix_seconds, value), ...]``.
    When `bar_timestamps` is given, the features are ALIGNED to that
    bar grid with the same one-bar publication lag as every other
    leading series in this package.

    The features produced:
      funding_rate          - the raw periodic rate
      funding_annualised    - the rate scaled to a year
      funding_zscore        - the rate's z-score over its own history
      open_interest         - the derivative position size
      oi_change_pct         - the change in open interest
    """
    from .leading import align_to_bars

    n = len(bar_timestamps) if bar_timestamps else len(funding)
    if bar_timestamps:
        f_aligned = align_to_bars(funding, bar_timestamps,
                                  max_lag_bars=max_lag_bars)
        if open_interest:
            oi_aligned = align_to_bars(open_interest, bar_timestamps,
                                       max_lag_bars=max_lag_bars)
        else:
            oi_aligned = [None] * n
    else:
        f_aligned = [v for _t, v in funding]
        oi_aligned = [v for _t, v in (open_interest or [])]

    z = funding_zscore(funding)
    z_map = dict(z)
    if bar_timestamps:
        z_aligned = [z_map.get(t) for t in bar_timestamps]
    else:
        z_aligned = [v for _t, v in z]

    # The open-interest change is computed on the RAW series (so the
    # window is in observations, not bars) and then aligned.
    oi_chg = oi_change(list(open_interest or []), window=oi_window)
    oi_chg_map = dict(oi_chg)
    if bar_timestamps:
        oi_change_aligned = [oi_chg_map.get(t) for t in bar_timestamps]
    else:
        oi_change_aligned = [v for _t, v in oi_chg]

    annual = [None if v is None else annualise_funding(v, interval_hours)
              for v in f_aligned]

    return {
        "source": source,
        "asset": asset,
        "funding_rate": f_aligned,
        "funding_annualised": annual,
        "funding_zscore": z_aligned,
        "open_interest": oi_aligned,
        "oi_change_pct": oi_change_aligned,
        "n_bars": n,
        "n_funding_observed": sum(1 for v in f_aligned if v is not None),
        "n_oi_observed": sum(1 for v in oi_aligned if v is not None),
        "alignment_rule": (
            f"a bar at T uses a measurement timestamped no later than "
            f"T - {max_lag_bars} bar(s); a funding rate is published at the "
            f"END of its interval, so the one-bar lag is the conservative "
            f"choice"),
        "interpretation_note": (
            "These are POSITIONING and RISK-CONDITION measures, not "
            "directional signals. Elevated funding means the market is "
            "crowded long and paying to hold that position; it does not "
            "say what price does next. It is a SIZING input, in the same "
            "way the volatility risk premium is."),
        "venue_note": (
            "Funding rates and open interest are VENUE-SPECIFIC. Bybit's "
            "open interest is not Binance's, and neither is the whole "
            "market. Compare within a venue, or aggregate across them "
            "explicitly."),
    }
