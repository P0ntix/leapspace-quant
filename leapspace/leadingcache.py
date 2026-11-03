"""Cache and panel-resolution helpers for the leading-indicator features.

This is a separate module so `leapspace.leading` stays about MEASUREMENT
and this one stays about PLUMBING: where the series is stored, how it is
resolved for a given panel, and how it is aligned to a date axis.

WHY A CACHE
    The leading series are HISTORICAL and expensive to refetch (DVOL
    pagination is one request per 1000 points). A backtest re-reads
    the same series once per feature evaluation, so it is cached on
    disk under `data/cache/leading/`.

    The cache is keyed by the SOURCE and the ASSET, and it records the
    FETCH TIME and the SOURCE URL. A cached series is always reported
    as CACHE provenance, never as fresh live data - the same rule the
    package's HTTP layer already applies.

WHY A SEPARATE MODULE
    `leapspace.leading` answers "what does this measurement mean". This
    one answers "where does it live and how does it line up with this
    panel". Keeping them apart means the measurement code has no
    filesystem knowledge, so it can be unit-tested with plain lists.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .provenance import CACHE, LIVE, Provenance
from .leading import dvol_history, implied_vol_series

__all__ = [
    "CACHE_DIR",
    "leading_cache_path",
    "store_leading_series",
    "load_leading_series",
    "resolve_leading_source",
    "series_for_panel",
    "panel_date_timestamps",
]


#: Where the leading series are cached. Inside the repository's data
#: cache, which is gitignored, because it is regenerable.
CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "cache", "leading")

#: How old a cached leading series may be before it is refetched. The
#: series are historical bars, so a day-old cache is fine; the LIVE
#: measurements (gamma, flow) are never cached.
MAX_AGE_SECONDS = 24 * 3600


def leading_cache_path(source: str, asset: str) -> str:
    """Where the cached series for (source, asset) lives."""
    safe = "".join(c if c.isalnum() or c in "-_." else "_"
                   for c in f"{source}_{asset}")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def store_leading_series(source: str, asset: str,
                          series: Sequence[Tuple[int, float]],
                          url: str = "", note: str = "") -> str:
    """Write a leading series to the cache and return the path."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = leading_cache_path(source, asset)
    payload = {
        "source": source,
        "asset": asset,
        "fetched_at": int(time.time()),
        "url": url,
        "note": note,
        "points": [[int(t), float(v)] for t, v in series],
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    os.replace(tmp, path)
    return path


def load_leading_series(source: str, asset: str,
                         max_age_seconds: Optional[int] = MAX_AGE_SECONDS
                         ) -> Tuple[List[Tuple[int, float]], Provenance]:
    """Read a cached leading series.

    Returns an empty list and an UNAVAILABLE-shaped provenance when the
    cache is missing, stale, or unreadable. A caller that cannot get a
    leading series must be able to say so; it must never receive a
    silent zero.
    """
    path = leading_cache_path(source, asset)
    if not os.path.isfile(path):
        return [], Provenance(source=f"cache:{source}", url=path,
                              note=f"no cached leading series at {path}",
                              kind=CACHE)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return [], Provenance(source=f"cache:{source}", url=path,
                              note=f"cached leading series unreadable: "
                                   f"{type(exc).__name__}: {str(exc)[:120]}",
                              kind=CACHE)
    fetched = int(payload.get("fetched_at") or 0)
    age = int(time.time()) - fetched
    if max_age_seconds is not None and age > max_age_seconds:
        return [], Provenance(source=f"cache:{source}", url=path,
                              note=f"cached leading series is stale "
                                   f"({age}s old, limit {max_age_seconds}s)",
                              kind=CACHE)
    pts = payload.get("points") or []
    series = [(int(p[0]), float(p[1])) for p in pts if len(p) >= 2]
    series.sort()
    prov = Provenance(source=f"cache:{payload.get('source', source)}",
                      url=payload.get("url") or path,
                      note=(f"{len(series)} cached points, fetched "
                            f"{age}s ago; {payload.get('note', '')}"),
                      kind=CACHE)
    return series, prov


# --------------------------------------------------------------------------
# Resolving which leading source applies to a panel
# --------------------------------------------------------------------------
#: Crypto assets and the Deribit currency that prices their options.
_CRYPTO_CCY = {
    "BTC": "BTC", "BITCOIN": "BTC",
    "ETH": "ETH", "ETHEREUM": "ETH",
    "SOL": "SOL", "SOLANA": "SOL",
}


def resolve_leading_source(symbols: Sequence[str]
                           ) -> Tuple[str, str, str]:
    """Decide which leading series applies to a panel's universe.

    Returns ``(source, asset, why)``:
      * ``("deribit.dvol", "BTC", ...)`` for a crypto universe
      * ``("yahoo.chart", "^VXN", ...)`` for a Nasdaq-like universe
      * ``("yahoo.chart", "^VIX", ...)`` for other equity universes

    The choice is made from the SYMBOLS, not from a guess: a panel of
    BTC/ETH is priced by Deribit's own options, and a Nasdaq panel is
    priced by the Nasdaq volatility index. Using the wrong one would
    import a LEADING indicator from a market the panel does not trade,
    which is a category error rather than a modelling choice.

    The symbol forms handled are the ones the engine actually produces:
    ``BTC-USD`` (Yahoo's crypto form), ``BTC/USD``, ``BTC-USD-PERP`` and
    a bare ``BTC``.
    """
    syms = [str(s or "").upper() for s in symbols]
    for s in syms:
        base = s.split("-")[0].split("/")[0]
        if base in _CRYPTO_CCY:
            ccy = _CRYPTO_CCY[base]
            return ("deribit.dvol", ccy,
                    f"the universe contains {s}, whose options are priced on "
                    f"Deribit as {ccy}")
    for s in syms:
        base = s.split("-")[0].split("/")[0]
        if base in ("QQQ", "NDX", "QQQM", "QQQS"):
            return ("yahoo.chart", "^VXN",
                    "the universe is Nasdaq-like, so the Nasdaq-100 "
                    "implied volatility index is the matching leading "
                    "indicator")
    return ("yahoo.chart", "^VIX",
            "the universe is not crypto and not Nasdaq-like, so the S&P 500 "
            "implied volatility index is used")


def panel_date_timestamps(dates: Sequence[str]) -> List[int]:
    """Convert the engine's ``YYYY-MM-DD`` date strings to unix seconds.

    The engine builds its date axis with
    ``datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")``,
    so the inverse is the UTC midnight of that calendar date. Using UTC
    midnight - not local midnight - keeps the alignment identical on
    every host, which matters because a timezone slip here would shift
    a leading indicator by a whole bar.
    """
    import calendar
    out: List[int] = []
    for d in dates:
        try:
            y, m, dd = str(d).split("-")
            out.append(int(calendar.timegm((int(y), int(m), int(dd),
                                             0, 0, 0, 0, 0, 0))))
        except Exception:  # noqa: BLE001
            out.append(0)
    return out


def series_for_panel(panel: Any,
                     source: Optional[str] = None,
                     asset: Optional[str] = None,
                     allow_fetch: bool = True) -> Tuple[
                         List[Tuple[int, float]], Dict[str, Any]]:
    """Get the leading series for a panel, fetching and caching if needed.

    Returns ``(series, info)`` where ``info`` names the source, the
    asset, the provenance and whether the series was fetched or read
    from the cache. A failure returns an empty series with the reason
    in ``info`` - never a silent zero series.
    """
    symbols = list(getattr(panel, "symbols", []) or [])
    if source is None or asset is None:
        source, asset, why = resolve_leading_source(symbols)
    else:
        why = "source and asset were supplied explicitly"

    series, prov = load_leading_series(source, asset)
    fetched = False
    if not series and allow_fetch:
        try:
            if source == "deribit.dvol":
                # DAILY resolution for a daily panel: the endpoint caps
                # each call at 1000 points, so at 1 point/day a single
                # page covers 1000 days and the pagination reaches back
                # years. At HOURLY resolution the same page budget
                # covers only ~41 days, which would leave the leading
                # feature missing over most of a multi-year panel.
                # Verified: 3 pages at daily resolution = 2051 points
                # spanning 2021-03-24 to today, in under 4 seconds.
                series, prov = dvol_history(asset, days=2600,
                                            resolution=86400, max_pages=6)
            else:
                series, prov = implied_vol_series(asset, rng="5y")
            store_leading_series(source, asset, series,
                                  url=getattr(prov, "url", ""),
                                  note=getattr(prov, "note", ""))
            fetched = True
        except Exception as exc:  # noqa: BLE001
            info = {
                "source": source, "asset": asset, "why": why,
                "ok": False, "fetched": False,
                "reason": f"{type(exc).__name__}: {str(exc)[:160]}",
                "n_points": 0,
            }
            return [], info

    info = {
        "source": source, "asset": asset, "why": why,
        "ok": bool(series), "fetched": fetched,
        "reason": "" if series else "no leading series available",
        "n_points": len(series),
        "provenance": getattr(prov, "source", ""),
        "provenance_note": getattr(prov, "note", ""),
    }
    return series, info
