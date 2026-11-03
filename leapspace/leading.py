"""Leading-indicator features: the forward-looking half of the regime model.

WHAT THIS IS
    A module of LEADING features - measurements that are known BEFORE
    the move they forecast - to sit beside the LAGGING features in
    `leapspace.regime` (realised volatility, trend, drawdown, liquidity).

    The existing regime model classifies the market from four
    backward-looking inputs. The papers this package implements are
    explicit that this is not the whole edge:

      "Option-implied and market-based uncertainty indicators can
       sometimes detect stress transitions EARLIER than backward-looking
       returns alone."                                  - regime paper

      "The best regime indicators ... forward-looking option/VIX signals
       can improve early stress detection."             - regime paper

      "Implied volatility often contains incremental information about
       future realized volatility, and in several studies it outperforms
       historical volatility forecasts."                 - gamma/option paper

      "The 2023 stock study also finds that low net gamma exposure
       predicts higher future realized volatility, supporting gamma
       exposure as a forward-looking volatility signal."
                                                      - gamma/option paper

      "One study's crash dummy combines negative trailing market returns,
       a positive current return, and elevated short-versus-long
       volatility, which is effectively a rebound-danger state."
                                                      - regime paper

WHAT THIS IS NOT
    * It is NOT a forecast. A leading feature is a state measurement,
      not a prediction, and it does not say what price does next.
    * It is NOT free of look-ahead. Every series here is fetched with
      its OWN timestamp and is aligned to bars by that timestamp. A
      series published with a lag is carried at its true lag, never
      shifted forward to make it look predictive.
    * It is NOT a claim that the edge exists. The features are inputs
      to the gate; whether they carry an edge is decided by the
      backtest gauntlet, not by this module.
    * It does NOT replace `leapspace.regime`. It complements it.

THE FOUR LEADING FEATURES
    1. `iv_level`        - the implied-volatility level. For equities:
                          VIX / VXN / VXD. For crypto: Deribit's DVOL
                          index. Forward-looking by construction: an
                          option price is a market's forecast of the
                          future, not a summary of the past.
    2. `vrp`             - the VOLATILITY RISK PREMIUM: implied minus
                          realised volatility. This is the cleanest
                          single leading signal here, and it is
                          DIRECTIONAL rather than a level: a high VRP
                          says options are expensive relative to what
                          is likely to happen.
    3. `iv_term_slope`   - the short-versus-long implied-volatility
                          spread. The momentum-crash literature uses
                          "elevated short-versus-long volatility" as a
                          rebound-danger state. A steeper front end
                          means near-term event risk is priced higher.
    4. `gamma_state`     - dealer gamma exposure from open interest.
                          Negative gamma amplifies moves; positive gamma
                          damps them. It predicts realised volatility
                          and, per the papers, intraday momentum.

DATA SOURCES - ALL KEYLESS, ALL FREE
    * Yahoo chart API  - ^VIX, ^VXN, ^VXD implied vol indices, and the
      spot OHLCV used for the realised-volatility counterpart.
    * Deribit public   - DVOL implied-volatility index history for BTC
      and ETH, the live option book (mark IV + open interest) and the
      live option trade tape.

    The Deribit DVOL endpoint returns at most 1000 points per call, so
    `dvol_history` PAGES BACKWARDS to build arbitrarily deep history.
    Verified: 3 pages = 3000 hourly points = 125 days.

PROVENANCE AND HONESTY
    Every fetch returns a `Provenance` recording the URL, the HTTP
    status and what was actually measured. When a source is
    unavailable the result says UNAVAILABLE with the reason - it never
    reports a zero, because a zero implied vol would read as "no
    expected movement" rather than "could not measure".

SOURCES
    Christensen & Prabhala (1998), Journal of Financial Economics 50(1),
    "The relation between implied and realized volatility".
    Ferris, Kim & Park (2010), Applied Economics Letters, "The
    informational quality of implied volatility and the volatility risk
    premium".
    Buis, Pieterse-Bloem, Verschoor & Zwinkels (2024), Journal of
    Economic Dynamics and Control, "Gamma positioning and market
    quality".
    Soebhag (2023), Journal of Empirical Finance, "Option gamma and stock
    returns".
    Baltussen, Da, Lammers & Martens (2021), Journal of Financial
    Economics 141(1), "Hedging demand and market intraday momentum".
    Butt, Kolari & Sadaqat (2024), Journal of Asset Management,
    "Market volatility, momentum, and reversal: a switching strategy".
"""
from __future__ import annotations

import math
import re
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .http import http_json
from .provenance import LIVE, Provenance, SourceUnavailable

__all__ = [
    "DERIBIT_DVOL",
    "EQUITY_VOL_INDICES",
    "implied_vol_series",
    "realized_vol_series",
    "volatility_risk_premium",
    "iv_term_slope",
    "dvol_history",
    "deribit_gamma_exposure",
    "deribit_option_flow",
    "build_leading_features",
    "align_to_bars",
    "leading_cache_path",
    "load_leading_series",
    "store_leading_series",
    "resolve_leading_source",
    "series_for_panel",
]


#: Deribit's public API root.
DERIBIT_DVOL = "https://www.deribit.com/api/v2/public"

#: Equity implied-volatility indices, by the Yahoo symbol. ^VXN is the
#: Nasdaq-100 volatility index, which is the one the NASDAQ paper's
#: regime work actually needs; ^VXD is the Dow's.
EQUITY_VOL_INDICES = {
    "^VIX": {"label": "S&P 500 implied volatility", "asset": "us_equity"},
    "^VXN": {"label": "Nasdaq-100 implied volatility", "asset": "us_equity"},
    "^VXD": {"label": "Dow Jones implied volatility", "asset": "us_equity"},
}

#: Annualisation factor for daily bars.
_ANN = math.sqrt(252.0)

#: Deribit instrument name: BTC-26DEC26-100000-C
_INSTRUMENT_RE = re.compile(
    r"^(?P<ccy>[A-Z0-9]+)-(?P<exp>\d{1,2}[A-Z]{3}\d{2})-(?P<strike>\d+)-(?P<kind>[CP])$"
)

_MONTHS = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
           "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}


def _now_ms() -> int:
    return int(time.time() * 1000)


# --------------------------------------------------------------------------
# 1. Equity implied volatility (Yahoo)
# --------------------------------------------------------------------------
def implied_vol_series(symbol: str = "^VIX", rng: str = "2y",
                       interval: str = "1d",
                       timeout: int = 30) -> Tuple[List[Tuple[int, float]],
                                                  Provenance]:
    """Historical implied volatility for an equity index.

    Returns ``[(unix_ts, iv), ...]`` sorted oldest-first, where the
    value is the index level (e.g. 17.42 for VIX, i.e. 17.42%).

    This is a LEADING series by construction: the index is derived from
    the prices of FUTURE options, so it embeds a forecast rather than
    a summary of realised moves.
    """
    from .market import _yahoo_symbol

    sym = _yahoo_symbol(symbol)
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?range={rng}&interval={interval}")
    payload, status = http_json(url, headers={"Accept": "application/json"},
                                 timeout=timeout)
    try:
        result = (payload.get("chart") or {}).get("result") or []
    except AttributeError:
        result = []
    if not result:
        raise SourceUnavailable(f"yahoo returned no chart result for {sym}")
    r0 = result[0]
    ts = r0.get("timestamp") or []
    quote = ((r0.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    out: List[Tuple[int, float]] = []
    for i, t in enumerate(ts):
        if i >= len(closes) or closes[i] is None:
            continue
        out.append((int(t), float(closes[i])))
    out.sort()
    if not out:
        raise SourceUnavailable(f"yahoo returned no usable closes for {sym}")
    prov = Provenance(source="yahoo.chart", url=url,
                      note=(f"HTTP {status}; {len(out)} bars of {symbol} "
                            f"implied volatility"))
    return out, prov


# --------------------------------------------------------------------------
# 2. Crypto implied volatility (Deribit DVOL)
# --------------------------------------------------------------------------
def dvol_history(currency: str = "BTC", days: int = 125,
                  resolution: int = 3600, max_pages: int = 8,
                  timeout: int = 45) -> Tuple[List[Tuple[int, float]],
                                              Provenance]:
    """Historical implied volatility for a crypto asset, from Deribit.

    Deribit's DVOL is an implied-volatility index computed from the
    asset's own option book - so it is a forward-looking measure for
    that asset, not a proxy for equity volatility.

    The endpoint returns AT MOST 1000 points per call, so this pages
    backwards until it has `days` of history or runs out of pages.
    Verified: 3 pages x 1000 hourly points = 125 days.

    Returns ``[(unix_seconds, iv), ...]`` oldest-first.
    """
    ccy = currency.upper()
    end_ms = _now_ms()
    step_ms = resolution * 1000
    collected: Dict[int, float] = {}
    pages = 0
    url_used = ""
    for _ in range(max_pages):
        start_ms = end_ms - 1000 * step_ms
        url = (f"{DERIBIT_DVOL}/get_volatility_index_data?currency={ccy}"
               f"&start_timestamp={start_ms}&end_timestamp={end_ms}"
               f"&resolution={resolution}")
        try:
            payload, status = http_json(url, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            if not collected:
                raise SourceUnavailable(
                    f"deribit DVOL unavailable for {ccy}: "
                    f"{type(exc).__name__}: {str(exc)[:140]}")
            break
        url_used = url
        rows = ((payload.get("result") or {}).get("data") or [])
        if not rows:
            break
        pages += 1
        oldest = None
        for row in rows:
            if not row or len(row) < 5:
                continue
            ts_ms = int(row[0])
            close = row[4]
            if close is None:
                continue
            collected[int(ts_ms / 1000)] = float(close)
            if oldest is None or ts_ms < oldest:
                oldest = ts_ms
        if oldest is None:
            break
        end_ms = oldest - step_ms
        if len(collected) >= days * 86400 // resolution:
            break

    if not collected:
        raise SourceUnavailable(
            f"deribit returned no DVOL history for {ccy} "
            f"(the index may not exist for that asset)")

    out = sorted(collected.items())
    prov = Provenance(source="deribit.dvol", url=url_used,
                      note=(f"{len(out)} points of {ccy} implied volatility "
                            f"over {pages} page(s) at {resolution}s"))
    return out, prov


# --------------------------------------------------------------------------
# 3. Realised volatility - the LAGGING counterpart
# --------------------------------------------------------------------------
def realized_vol_series(closes: Sequence[float],
                        window: int = 20) -> List[Optional[float]]:
    """Annualised realised volatility from closes. This is LAGGING.

    It is included here so the volatility risk premium can be computed
    against it in one place. A feature that is only ever compared with
    its own past is backward-looking by definition; pairing it with an
    implied measure is what turns it into a leading signal.
    """
    n = len(closes)
    out: List[Optional[float]] = [None] * n
    if window < 2:
        return out
    rets: List[Optional[float]] = [None] * n
    for i in range(1, n):
        p, c = closes[i - 1], closes[i]
        if p and c and p > 0 and c > 0:
            rets[i] = c / p - 1.0
    for i in range(window, n):
        w = [r for r in rets[i - window + 1:i + 1] if r is not None]
        if len(w) < window - 1:
            continue
        m = sum(w) / len(w)
        var = sum((x - m) ** 2 for x in w) / (len(w) - 1)
        out[i] = math.sqrt(var) * _ANN * 100.0  # percent, like an IV level
    return out


# --------------------------------------------------------------------------
# 4. The volatility risk premium - the directional leading signal
# --------------------------------------------------------------------------
def volatility_risk_premium(iv: Optional[float],
                             rv: Optional[float]) -> Optional[float]:
    """Implied minus realised volatility, in percentage points.

    Positive means options are priced above what the market has been
    experiencing - the premium a seller of volatility collects.
    Negative means the opposite.

    The sign is the SIGNAL, not the level: a persistently high VRP is a
    market priced for calm, which is the state in which a volatility
    shock is most disruptive. It is a directional statement about
    expected versus experienced movement, which a volatility LEVEL
    alone cannot make.
    """
    if iv is None or rv is None:
        return None
    return float(iv) - float(rv)


def iv_term_slope(short_iv: Optional[float],
                  long_iv: Optional[float]) -> Optional[float]:
    """Short-versus-long implied-volatility spread.

    Positive means near-term implied volatility is elevated relative to
    the longer-dated expectation - i.e. near-term event risk is priced
    above the horizon average.

    This is the "elevated short-versus-long volatility" component of
    the crash dummy in the momentum-crash literature (Butt, Kolari &
    Sadaqat 2024), which is the regime paper's "rebound-danger state".
    """
    if short_iv is None or long_iv is None:
        return None
    return float(short_iv) - float(long_iv)


# --------------------------------------------------------------------------
# 5. Deribit gamma exposure from open interest
# --------------------------------------------------------------------------
def deribit_gamma_exposure(currency: str = "BTC",
                            spot: Optional[float] = None,
                            timeout: int = 45) -> Tuple[Dict[str, Any],
                                                       Provenance]:
    """Dealer gamma exposure for a crypto asset, from the live option book.

    This computes a GAMMA EXPOSURE PROXY from open interest. It is a
    proxy and says so:

    * The book is the LIVE book, so this is a NOW measurement, not a
      history. It cannot be backtested from this endpoint.
    * Open interest is a DEFERRED position: it does not reveal which
      side of the trade holds the option, so whether dealers are long
      or short gamma is INFERRED under the standard assumption that
      customers are net short calls and dealers are the other side.
    * Black-Scholes gamma is biased under a real smile (the package's
      `gamma.py` says the same thing), so the magnitude is indicative.

    WHAT IT IS USEFUL FOR
        The SIGN and the relative MAGNITUDE across expiries, as a
        current regime reading: negative gamma says hedging flows are
        likely to amplify the next move.

    Returns a dict with `net_gex`, `by_expiry`, `spot`, `n_instruments`.
    """
    ccy = currency.upper()
    url = (f"{DERIBIT_DVOL}/get_book_summary_by_currency"
           f"?currency={ccy}&kind=option")
    payload, status = http_json(url, timeout=timeout)
    rows = payload.get("result") or []
    if not rows:
        raise SourceUnavailable(f"deribit returned no option book for {ccy}")

    from .gamma import bs_greeks

    # The spot price: take it from the book itself so the call does not
    # need a second request, and prefer the most common one.
    spots: Dict[float, int] = {}
    for r in rows:
        up = r.get("underlying_price")
        if up:
            spots[float(up)] = spots.get(float(up), 0) + 1
    if spot is None and spots:
        spot = max(spots.items(), key=lambda kv: kv[1])[0]
    if not spot:
        raise SourceUnavailable(f"deribit book for {ccy} carried no spot price")

    now = time.time()
    net_gex = 0.0
    by_expiry: Dict[str, Dict[str, float]] = {}
    n_used = 0
    for r in rows:
        name = r.get("instrument_name") or ""
        m = _INSTRUMENT_RE.match(name)
        if not m:
            continue
        try:
            strike = float(m.group("strike"))
            iv = float(r.get("mark_iv") or 0.0)
            oi = float(r.get("open_interest") or 0.0)
        except (TypeError, ValueError):
            continue
        if iv <= 0 or oi <= 0:
            continue
        exp = m.group("exp")
        t_years = _expiry_years(exp, now)
        if t_years is None or t_years <= 0:
            continue
        g = bs_greeks(spot=spot, strike=strike, t_years=t_years,
                      rate=float(r.get("interest_rate") or 0.0),
                      iv=iv / 100.0)
        gamma = float(g.get("gamma") or 0.0)
        if gamma <= 0:
            continue
        # Contract size for Deribit options is 1 unit of the underlying.
        gex = gamma * oi * spot
        # Dealer side is INFERRED: customers are assumed net short
        # calls, so the dealer's call gamma is negative and the put
        # gamma is positive.
        if m.group("kind") == "C":
            gex = -gex
        net_gex += gex
        slot = by_expiry.setdefault(exp, {"net_gex": 0.0, "open_interest": 0.0})
        slot["net_gex"] += gex
        slot["open_interest"] += oi
        n_used += 1

    if n_used == 0:
        raise SourceUnavailable(
            f"deribit book for {ccy} had no usable instruments for a gamma "
            f"computation")

    out = {
        "currency": ccy,
        "spot": spot,
        "net_gex": net_gex,
        "gamma_state": "negative (amplifies moves)" if net_gex < 0
        else "positive (damps moves)",
        "by_expiry": by_expiry,
        "n_instruments": n_used,
        "provenance_note": (
            "PROXY: the dealer side is INFERRED (customers assumed net "
            "short calls) and Black-Scholes gamma is biased under a real "
            "smile. Read the SIGN and the relative magnitude across "
            "expiries, not the absolute number. This is a LIVE "
            "measurement and cannot be backtested from this endpoint."),
    }
    prov = Provenance(source="deribit.book", url=url,
                      note=(f"HTTP {status}; {n_used} instruments priced into "
                            f"a {ccy} gamma proxy at spot {spot}"))
    return out, prov


def _expiry_years(exp: str, now_ts: float) -> Optional[float]:
    """Years to expiry from a Deribit expiry string like '26DEC26'."""
    m = re.match(r"^(\d{1,2})([A-Z]{3})(\d{2})$", exp or "")
    if not m:
        return None
    day = int(m.group(1))
    mon = _MONTHS.get(m.group(2))
    if mon is None:
        return None
    yy = int(m.group(3))
    year = 2000 + yy if yy < 90 else 1900 + yy
    try:
        import datetime as _dt
        d = _dt.date(year, mon, day)
    except ValueError:
        return None
    days = (d - _dt.date.fromtimestamp(now_ts)).days
    return days / 365.0


# --------------------------------------------------------------------------
# 6. Option flow - the leading directional pressure signal
# --------------------------------------------------------------------------
def deribit_option_flow(currency: str = "BTC", limit: int = 500,
                         timeout: int = 45) -> Tuple[Dict[str, Any],
                                                    Provenance]:
    """Net option flow from the live Deribit trade tape.

    Separates CALL flow from PUT flow by notional, and computes the
    put/call ratio. A put-heavy tape is a market paying for downside
    protection - which is a forward-looking statement about expected
    distribution, not a description of past moves.

    IMPORTANT LIMITATION, stated by the papers themselves: option flow
    "may reflect hedging or vol demand, not direction", and retail
    option demand is associated with LOWER option returns. So this is a
    VOLATILITY-TIMING signal, not a clean directional one. The gamma
    paper says the same: "Options order flow can inform future
    volatility, but not consistently future returns."

    Returns a dict with call/put notional, the ratio, and the trade
    count. It is a NOW measurement.
    """
    ccy = currency.upper()
    url = (f"{DERIBIT_DVOL}/get_last_trades_by_currency?currency={ccy}"
           f"&kind=option&count={limit}")
    payload, status = http_json(url, timeout=timeout)
    trades = (payload.get("result") or {}).get("trades") or []
    if not trades:
        raise SourceUnavailable(f"deribit returned no option trades for {ccy}")

    call_notional = 0.0
    put_notional = 0.0
    call_iv_weighted = 0.0
    put_iv_weighted = 0.0
    n_calls = 0
    n_puts = 0
    for t in trades:
        name = t.get("instrument_name") or ""
        m = _INSTRUMENT_RE.match(name)
        if not m:
            continue
        try:
            amount = float(t.get("amount") or 0.0)
            price = float(t.get("price") or 0.0)
            iv = float(t.get("iv") or 0.0)
        except (TypeError, ValueError):
            continue
        notional = abs(amount) * price
        if m.group("kind") == "C":
            call_notional += notional
            call_iv_weighted += notional * iv
            n_calls += 1
        else:
            put_notional += notional
            put_iv_weighted += notional * iv
            n_puts += 1

    total = call_notional + put_notional
    out = {
        "currency": ccy,
        "call_notional": call_notional,
        "put_notional": put_notional,
        "put_call_ratio": (put_notional / call_notional
                           if call_notional > 0 else None),
        "call_share": (call_notional / total if total > 0 else None),
        "call_iv_weighted": (call_iv_weighted / call_notional
                             if call_notional > 0 else None),
        "put_iv_weighted": (put_iv_weighted / put_notional
                            if put_notional > 0 else None),
        "n_trades": n_calls + n_puts,
        "n_calls": n_calls,
        "n_puts": n_puts,
        "provenance_note": (
            "LIVE tape snapshot. Flow reflects HEDGING and volatility "
            "demand as well as direction, so it is a volatility-timing "
            "input, not a directional one. The gamma paper: 'Options "
            "order flow can inform future volatility, but not "
            "consistently future returns.'"),
    }
    prov = Provenance(source="deribit.trades", url=url,
                      note=f"HTTP {status}; {out['n_trades']} option trades")
    return out, prov


# --------------------------------------------------------------------------
# 7. Alignment - the step that decides whether this is honest
# --------------------------------------------------------------------------
def align_to_bars(series: Sequence[Tuple[int, float]],
                  bar_timestamps: Sequence[int],
                  max_lag_bars: int = 1) -> List[Optional[float]]:
    """Align a timestamped series to a bar grid WITHOUT look-ahead.

    A bar at time T may only use a measurement published at or before
    T minus the publication lag. The rule used here is: the value
    carried to bar T is the most recent value whose timestamp is at or
    before ``T - max_lag_bars`` intervals of the bar spacing.

    The default `max_lag_bars=1` means a bar at T uses a measurement
    timestamped no later than the PREVIOUS bar. That is the
    conservative choice: it assumes the measurement was published
    after the bar it describes, which is true of every daily index
    print.

    A measurement with NO timestamp cannot be aligned this way, so it
    is not - it belongs to a live/now measurement, not a backtest.
    """
    if not series:
        return [None] * len(bar_timestamps)
    if len(bar_timestamps) >= 2:
        spacing = (bar_timestamps[-1] - bar_timestamps[0]) / (
            len(bar_timestamps) - 1)
    else:
        spacing = 86400.0
    if spacing <= 0:
        spacing = 86400.0
    lag = spacing * max(0, int(max_lag_bars))

    out: List[Optional[float]] = []
    j = 0
    ordered = sorted(series)
    for t in bar_timestamps:
        cutoff = t - lag
        while j + 1 < len(ordered) and ordered[j + 1][0] <= cutoff:
            j += 1
        if j < len(ordered) and ordered[j][0] <= cutoff:
            out.append(float(ordered[j][1]))
        else:
            out.append(None)
    return out


# --------------------------------------------------------------------------
# 8. The assembled leading feature set
# --------------------------------------------------------------------------
def build_leading_features(
    iv_series: Sequence[Tuple[int, float]],
    bar_timestamps: Sequence[int],
    closes: Optional[Sequence[float]] = None,
    rv_window: int = 20,
    max_lag_bars: int = 1,
    label: str = "",
    derivatives: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble the leading feature block for a bar grid.

    `iv_series` is the implied-volatility history, as
    ``[(unix_seconds, iv), ...]``. `bar_timestamps` is the bar grid the
    features are expressed on.

    Returns a dict of aligned feature series plus the provenance of
    every input. The REALISED volatility is computed from `closes` and
    aligned on the SAME grid, so the risk premium compares like with
    like.

    Features produced:
      iv_level    - the implied vol level, percent
      rv_level    - the annualised realised vol over `rv_window`, percent
      vrp         - implied minus realised, percentage points
      iv_zscore  - the implied level's z-score over the sample
      vrp_zscore - the risk premium's z-score over the sample

    When `derivatives` is supplied - the block returned by
    `leapspace.cryptoderivs.build_crypto_derivatives_features` - its
    series are merged in, so a crypto panel can carry the funding and
    open-interest measures alongside the volatility ones. A CRYPTO
    panel should: the perpetual-swap funding rate is the crypto-native
    equivalent of the implied-volatility risk premium, and it is
    leading in the same way.
    """
    n = len(bar_timestamps)
    iv_aligned = align_to_bars(iv_series, bar_timestamps,
                                max_lag_bars=max_lag_bars)

    rv_aligned: List[Optional[float]] = [None] * n
    if closes is not None and len(closes) == n:
        rv_raw = realized_vol_series(closes, window=rv_window)
        # The realised series is already indexed to the bar grid; it is
        # shifted by one bar so bar T never uses bar T's own close.
        rv_aligned = [None] + list(rv_raw[:-1]) if n > 1 else [None] * n

    vrp: List[Optional[float]] = [
        volatility_risk_premium(a, b) for a, b in zip(iv_aligned, rv_aligned)]

    def _z(series: Sequence[Optional[float]]) -> List[Optional[float]]:
        vals = [v for v in series if v is not None]
        if len(vals) < 3:
            return [None] * len(series)
        m = sum(vals) / len(vals)
        var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
        sd = math.sqrt(var)
        if sd <= 0:
            return [None] * len(series)
        return [None if v is None else (v - m) / sd for v in series]

    block = {
        "label": label,
        "iv_level": iv_aligned,
        "rv_level": rv_aligned,
        "vrp": vrp,
        "iv_zscore": _z(iv_aligned),
        "vrp_zscore": _z(vrp),
        "n_bars": n,
        "n_iv_observed": sum(1 for v in iv_aligned if v is not None),
        "alignment_rule": (
            f"a bar at T uses a measurement timestamped no later than "
            f"T - {max_lag_bars} bar(s); realised volatility is shifted one "
            f"bar so no bar uses its own close"),
        "source": "implied volatility series supplied by the caller",
    }

    # Merge the crypto-derivatives measures in, when supplied. They are
    # aligned to the SAME bar grid with the SAME publication lag, so a
    # crypto panel carries the volatility and the positioning measures
    # on one timeline.
    if derivatives:
        for key in ("funding_rate", "funding_annualised", "funding_zscore",
                    "open_interest", "oi_change_pct"):
            if key in derivatives:
                block[key] = derivatives[key]
        block["derivatives_source"] = derivatives.get("source")
        block["derivatives_venue_note"] = derivatives.get("venue_note")
        block["derivatives_interpretation_note"] = derivatives.get(
            "interpretation_note")
        block["n_derivatives_observed"] = derivatives.get("n_funding_observed")

    return block
