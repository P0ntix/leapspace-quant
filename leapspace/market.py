"""
Market data: OHLCV, options chains, crypto prices.

Every fetch returns (payload, Provenance). A source that cannot be reached
raises SourceUnavailable; the caller records it. Nothing is estimated.

Sources, all verified live from this host before being wired in:
  yahoo_chart      — daily/weekly OHLCV for equities, ETFs, indices, crypto.
  nasdaq_options   — US equity/ETF option chains WITH open interest and
                     volume per contract (the option-FLOW input).
  deribit_public   — crypto option instruments, book summaries, last trades.
  coingecko        — crypto spot prices.
  dexscreener      — DEX pair data for meme-coin screening (liquidity, volume,
                     buys/sells, age).
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .http import CachedFetcher, HttpError, http_get, http_json, http_post_json
from .provenance import Provenance, SourceUnavailable

# --------------------------------------------------------------------------
# Yahoo OHLCV
# --------------------------------------------------------------------------


def _yahoo_symbol(sym: str) -> str:
    s = sym.upper()
    if s in ("SP500", "SPX"):
        return "^GSPC"
    if s in ("NASDAQ", "NDX", "NASDAQ100"):
        return "^NDX"
    if s in ("DOW", "DJI"):
        return "^DJI"
    if s in ("VIX", "VIXINDEX"):
        return "^VIX"
    return s


def fetch_ohlcv(symbol: str, rng: str = "10y", interval: str = "1d",
                fetcher: Optional[CachedFetcher] = None,
                refresh: bool = False,
                timeout: int = 30) -> Tuple[List[Dict[str, Any]], Provenance]:
    """Fetch OHLCV bars from the Yahoo chart API.

    Returns (bars, provenance) where each bar is
    {date, open, high, low, close, volume, adjclose}.
    """
    sym = _yahoo_symbol(symbol)
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?range={rng}&interval={interval}&includeAdjustedClose=true")
    headers = {"Accept": "application/json"}
    if fetcher is not None:
        payload, prov = fetcher.get_json(f"yahoo_{sym}_{interval}", url,
                                         params={"range": rng, "interval": interval},
                                         headers=headers, refresh=refresh,
                                         timeout=timeout, source="yahoo.chart")
    else:
        payload, status = http_json(url, headers=headers, timeout=timeout)
        prov = Provenance(source="yahoo.chart", url=url, note=f"HTTP {status}")
    try:
        result = payload["chart"]["result"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise SourceUnavailable(f"unexpected yahoo payload shape: {exc}") from exc
    ts = result.get("timestamp") or []
    q = result.get("indicators", {}).get("quote", [{}])[0]
    adj = (result.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose") or []
    bars: List[Dict[str, Any]] = []
    for i, t in enumerate(ts):
        c = q.get("close", [None] * len(ts))[i] if i < len(q.get("close", [])) else None
        if c is None:
            continue
        d = _dt.datetime.fromtimestamp(t, _dt.timezone.utc).strftime("%Y-%m-%d")
        bars.append({
            "date": d,
            "open": q.get("open", [None] * len(ts))[i] if i < len(q.get("open", [])) else None,
            "high": q.get("high", [None] * len(ts))[i] if i < len(q.get("high", [])) else None,
            "low": q.get("low", [None] * len(ts))[i] if i < len(q.get("low", [])) else None,
            "close": c,
            "adjclose": adj[i] if i < len(adj) and adj[i] is not None else c,
            "volume": q.get("volume", [None] * len(ts))[i] if i < len(q.get("volume", [])) else None,
        })
    if not bars:
        raise SourceUnavailable(f"yahoo returned no usable bars for {sym}")
    prov.note = (prov.note + f"; {len(bars)} bars {bars[0]['date']}..{bars[-1]['date']}"
                 ).strip("; ")
    return bars, prov


def fetch_many_ohlcv(symbols: Sequence[str], rng: str = "10y",
                     interval: str = "1d",
                     fetcher: Optional[CachedFetcher] = None,
                     refresh: bool = False
                     ) -> Tuple[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]], List[Provenance]]:
    """Fetch several symbols. Returns (bars_by_symbol, failures, provenances)."""
    out: Dict[str, List[Dict[str, Any]]] = {}
    failures: List[Dict[str, Any]] = []
    provs: List[Provenance] = []
    for s in symbols:
        try:
            bars, prov = fetch_ohlcv(s, rng=rng, interval=interval,
                                     fetcher=fetcher, refresh=refresh)
            out[s] = bars
            provs.append(prov)
        except SourceUnavailable as exc:
            failures.append({"symbol": s, "error": str(exc),
                             "disclosure": (f"SOURCE UNAVAILABLE — no data was "
                                            f"substituted for {s}.")})
    return out, failures, provs


def closes_and_volumes(bars: Sequence[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
    cs = [float(b["close"]) for b in bars if b.get("close") is not None]
    vs = [float(b.get("volume") or 0.0) for b in bars if b.get("close") is not None]
    return cs, vs


# --------------------------------------------------------------------------
# US option chains — Nasdaq public API (open interest + volume per contract)
# --------------------------------------------------------------------------

NASDAQ_OPTION_CHAIN = ("https://api.nasdaq.com/api/quote/{sym}/option-chain"
                       "?assetclass={ac}&fromdate={fd}&todate={td}&limit=5000")

NASDAQ_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nasdaq.com/",
    "Origin": "https://www.nasdaq.com",
    "Accept-Language": "en-US,en;q=0.9",
}


def _num(v: Any) -> Optional[float]:
    """Nasdaq uses the string '--' for a missing value."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("$", "")
    if s in ("", "--", "N/A", "NA", "null", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _asset_class(symbol: str) -> str:
    s = symbol.upper()
    if s.startswith("^"):
        return "index"
    if len(s) <= 4 and s.isalpha():
        return "etf"
    return "stocks"


def _parse_last_trade(text: Any) -> Tuple[Optional[float], Optional[str]]:
    """Nasdaq returns the underlying's last trade as a formatted string.

    Observed live: "LAST TRADE: $712.2 (AS OF OCT 27, 2026)".
    Returns (price, as_of_text). None when the string does not parse — a
    gamma number scaled by a wrong spot is worse than no gamma.
    """
    if text is None:
        return None, None
    if isinstance(text, (int, float)):
        return float(text), None
    s = str(text)
    price = None
    m = re.search(r"\$\s*([0-9]+(?:\.[0-9]+)?)", s)
    if m:
        price = float(m.group(1))
    else:
        n = _num(s)
        price = n
    as_of = None
    m2 = re.search(r"AS OF\s+(.+?)\)?$", s, re.IGNORECASE)
    if m2:
        as_of = m2.group(1).strip()
    return price, as_of


def fetch_option_chain(symbol: str, from_date: Optional[str] = None,
                       to_date: Optional[str] = None,
                       fetcher: Optional[CachedFetcher] = None,
                       refresh: bool = False,
                       timeout: int = 60
                       ) -> Tuple[Dict[str, Any], Provenance]:
    """Fetch the full option chain for a US symbol.

    Returns a dict with:
      underlying, spot, as_of, expirations, contracts
    where each contract has: type ('call'|'put'), strike, expiry, volume,
    open_interest, last, bid, ask.

    The Nasdaq chain is DELAYED and its open interest is a snapshot — the
    provenance records that, because gamma computed from stale OI is stale
    gamma. This is exactly the failure mode the NASDAQ paper warns about.
    """
    today = _dt.date.today()
    fd = from_date or today.strftime("%Y-%m-%d")
    td = to_date or (today + _dt.timedelta(days=120)).strftime("%Y-%m-%d")
    url = NASDAQ_OPTION_CHAIN.format(sym=symbol.upper(), ac=_asset_class(symbol),
                                     fd=fd, td=td)
    if fetcher is not None:
        payload, prov = fetcher.get_json(f"nasdaq_opt_{symbol}_{fd}", url,
                                         params={"fd": fd, "td": td},
                                         headers=NASDAQ_HEADERS, refresh=refresh,
                                         timeout=timeout, source="nasdaq.option-chain")
    else:
        payload, status = http_json(url, headers=NASDAQ_HEADERS, timeout=timeout)
        prov = Provenance(source="nasdaq.option-chain", url=url, note=f"HTTP {status}")
    data = payload.get("data") or {}
    table = data.get("table") or {}
    rows = table.get("rows") or []
    as_of = table.get("asOf")
    last_trade = data.get("lastTrade")
    spot, spot_as_of = _parse_last_trade(last_trade)
    if as_of is None:
        as_of = spot_as_of

    contracts: List[Dict[str, Any]] = []
    for r in rows:
        strike = _num(r.get("strike"))
        if strike is None:
            continue
        exp = r.get("expiryDate") or r.get("expirygroup") or ""
        for side, pre in (("call", "c"), ("put", "p")):
            oi = _num(r.get(f"{pre}_Openinterest"))
            vol = _num(r.get(f"{pre}_Volume"))
            if oi is None and vol is None:
                continue
            contracts.append({
                "type": side,
                "strike": strike,
                "expiry": exp,
                "volume": vol or 0.0,
                "open_interest": oi or 0.0,
                "last": _num(r.get(f"{pre}_Last")),
                "bid": _num(r.get(f"{pre}_Bid")),
                "ask": _num(r.get(f"{pre}_Ask")),
                "contract": (r.get("drillDownURL") or "").rsplit("/", 1)[-1] or None,
            })
    if not contracts:
        raise SourceUnavailable(
            f"nasdaq option chain for {symbol} returned no contracts with OI/volume")
    prov.note = (f"HTTP 200; {len(contracts)} contracts; chain as-of {as_of}; "
                 f"underlying last {last_trade}; DELAYED data, OI is a snapshot")
    return {
        "underlying": symbol.upper(),
        "spot": spot,
        "as_of": as_of,
        "last_trade": last_trade,
        "expirations": sorted({c["expiry"] for c in contracts if c["expiry"]}),
        "contracts": contracts,
    }, prov


# --------------------------------------------------------------------------
# Deribit — crypto options (no key required for public endpoints)
# --------------------------------------------------------------------------

DERIBIT = "https://www.deribit.com/api/v2/public"


def fetch_deribit_instruments(currency: str = "BTC") -> Tuple[List[Dict[str, Any]], Provenance]:
    url = (f"{DERIBIT}/get_instruments?currency={currency.upper()}"
           f"&kind=option&expired=false")
    payload, status = http_json(url, timeout=45)
    result = payload.get("result") or []
    if not result:
        raise SourceUnavailable(f"deribit returned no instruments for {currency}")
    prov = Provenance(source="deribit.public", url=url,
                      note=f"HTTP {status}; {len(result)} live instruments")
    return result, prov


def fetch_deribit_book(currency: str = "BTC", kind: str = "option"
                        ) -> Tuple[List[Dict[str, Any]], Provenance]:
    url = f"{DERIBIT}/get_book_summary_by_currency?currency={currency.upper()}&kind={kind}"
    payload, status = http_json(url, timeout=45)
    result = payload.get("result") or []
    if not result:
        raise SourceUnavailable(f"deribit returned no book summary for {currency}")
    prov = Provenance(source="deribit.public", url=url,
                      note=f"HTTP {status}; {len(result)} instruments in book")
    return result, prov


def fetch_deribit_trades(currency: str = "BTC", kind: str = "option",
                         limit: int = 100) -> Tuple[List[Dict[str, Any]], Provenance]:
    url = (f"{DERIBIT}/get_last_trades_by_currency?currency={currency.upper()}"
           f"&kind={kind}&count={limit}")
    payload, status = http_json(url, timeout=45)
    result = (payload.get("result") or {}).get("trades") or []
    if not result:
        raise SourceUnavailable(f"deribit returned no trades for {currency}")
    prov = Provenance(source="deribit.public", url=url,
                      note=f"HTTP {status}; {len(result)} recent trades")
    return result, prov


# --------------------------------------------------------------------------
# CoinGecko — crypto spot
# --------------------------------------------------------------------------

def fetch_coingecko_prices(coin_ids: Sequence[str], vs: str = "usd"
                           ) -> Tuple[Dict[str, float], Provenance]:
    ids = ",".join(coin_ids)
    url = (f"https://api.coingecko.com/api/v3/simple/price?ids={ids}"
           f"&vs_currencies={vs}&include_24hr_change=true")
    payload, status = http_json(url, timeout=30)
    if not isinstance(payload, dict) or not payload:
        raise SourceUnavailable(f"coingecko returned no prices for {ids}")
    out: Dict[str, float] = {}
    for cid, row in payload.items():
        if isinstance(row, dict) and row.get(vs) is not None:
            out[cid] = float(row[vs])
    prov = Provenance(source="coingecko.simple_price", url=url,
                      note=f"HTTP {status}; {len(out)} prices")
    return out, prov


# --------------------------------------------------------------------------
# DexScreener — meme-coin DEX market data
# --------------------------------------------------------------------------

DEXSCREENER_SEARCH = "https://api.dexscreener.com/latest/dex/search?q={q}"
DEXSCREENER_TOKEN_PAIRS = "https://api.dexscreener.com/token-pairs/v1/{chain}/{addr}"


def fetch_dex_pairs(query: str, limit: int = 30
                     ) -> Tuple[List[Dict[str, Any]], Provenance]:
    url = DEXSCREENER_SEARCH.format(q=query)
    payload, status = http_json(url, timeout=30)
    pairs = payload.get("pairs") or []
    if not pairs:
        raise SourceUnavailable(f"dexscreener returned no pairs for '{query}'")
    prov = Provenance(source="dexscreener.search", url=url,
                      note=f"HTTP {status}; {len(pairs)} pairs (returned {min(limit, len(pairs))})")
    return pairs[:limit], prov


def normalise_dex_pair(p: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a DexScreener pair into the fields the meme-coin screen needs.

    Field names verified live: priceUsd, priceChange, liquidity.usd,
    volume.h24/h6/m5, fdv, marketCap, pairCreatedAt, txns.h24.buys/sells,
    info, chainId, dexId, baseToken, quoteToken.
    """
    liq = p.get("liquidity") or {}
    vol = p.get("volume") or {}
    txns = p.get("txns") or {}
    h24 = txns.get("h24") or {}
    h1 = txns.get("h1") or {}
    info = p.get("info") or {}
    base = p.get("baseToken") or {}
    quote = p.get("quoteToken") or {}
    # DexScreener returns priceChange as an OBJECT {m5, h1, h6, h24}, not a
    # scalar. Reading it as a scalar silently produced None for every
    # token, so the change fields are read from the object.
    chg = p.get("priceChange") or {}
    if not isinstance(chg, dict):
        chg = {}
    return {
        "chain": p.get("chainId"),
        "dex": p.get("dexId"),
        "pair": p.get("pairAddress"),
        "base_symbol": base.get("symbol"),
        "base_address": base.get("address"),
        "quote_symbol": quote.get("symbol"),
        "price_usd": _num(p.get("priceUsd")),
        "price_change_24h": _num(chg.get("h24")),
        "price_change_1h": _num(chg.get("h1")),
        "price_change_5m": _num(chg.get("m5")),
        "price_change_6h": _num(chg.get("h6")),
        "liquidity_usd": _num(liq.get("usd")),
        "volume_24h": _num(vol.get("h24")),
        "volume_6h": _num(vol.get("h6")),
        "volume_5m": _num(vol.get("m5")),
        "fdv": _num(p.get("fdv")),
        "market_cap": _num(p.get("marketCap")),
        "created_at_ms": p.get("pairCreatedAt"),
        "buys_24h": h24.get("buys"),
        "sells_24h": h24.get("sells"),
        "buys_1h": h1.get("buys"),
        "sells_1h": h1.get("sells"),
        "websites": info.get("websites") or [],
        "socials": (info.get("socials") or []),
        "image_url": info.get("imageUrl"),
        # A designed header image is community-identity evidence, and
        # DexScreener's categories are a narrative taxonomy when present.
        "info_header": info.get("header"),
        "info_categories": info.get("categories") or [],
    }
