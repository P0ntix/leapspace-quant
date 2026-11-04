"""Collect the market data: prices, funding, open interest, positioning,
liquidations - into the user's storage directory, JOINED to the Elfa
attention data.

WHY THIS IS A SEPARATE COLLECTOR
    Elfa gives attention and positioning. It gives no price. A feature
    that claims "social attention predicts price" needs both, on the
    same clock. So the symbol list here is driven by WHAT ELFA SAID
    was being talked about - the tokens with the highest mention counts
    in the collected Elfa series - and then the price, funding and
    positioning history for exactly those symbols is fetched.

    That is the point: the universe is chosen by attention, not by
    market cap, so a memecoin that the crowd is discussing but that no
    cap-screened universe would include still gets a price series.

THE SYMBOL JOIN
    Elfa names tokens in lowercase ("pepe", "btc"). Binance perpetuals
    are uppercase and sometimes SCALED ("1000PEPEUSDT", not
    "PEPEUSDT"). So the join tries, in order:
        PEPE  ->  PEPEUSDT      (spot)
               ->  1000PEPEUSDT (perp)
    and records WHICH one was used on every row, because "the price of
    PEPE" is ambiguous and a dataset that does not say which contract
    it used is a dataset nobody can check.

EVERY ROW IS POINT-IN-TIME AND PROVENANCED
    Each row carries its source, its interval and its fetch timestamp.
    A price row with no source is a number nobody can trace.
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from leapspace.elfa import DEFAULT_STORAGE_ROOT  # noqa: E402
from leapspace.marketfeed import (  # noqa: E402
    MAJORS, collect_liquidation_stream, fetch_funding_history,
    fetch_klines, fetch_long_short_ratios, fetch_open_interest_hist,
    fetch_taker_long_short, list_perp_symbols, list_spot_symbols,
    ms_to_date, ms_to_iso,
)

DAY_MS = 86_400_000


def _write(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, default=str) + "\n")


def top_attended_tokens(elfa_root: str, limit: int = 40
                        ) -> List[Tuple[str, int]]:
    """The tokens with the most mentions in the collected Elfa series.

    Ranked by the TOTAL mentions across every collected window, so a
    token that spiked once does not outrank one that was discussed
    steadily for a month.
    """
    path = os.path.join(elfa_root, "elfa", "trending_tokens_daily.jsonl")
    totals: Dict[str, int] = {}
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            tok = r.get("token")
            cnt = r.get("current_count") or 0
            if not tok:
                continue
            totals[tok] = totals.get(tok, 0) + int(cnt)
    return sorted(totals.items(), key=lambda kv: -kv[1])[:limit]


def resolve_symbol(token: str, perps: List[str],
                   spots: List[str]) -> Optional[Dict[str, str]]:
    """Map an Elfa token name to a tradable Binance symbol.

    Returns the symbol AND the market, because PEPE has a spot pair and
    a SCALED perpetual, and the two have different prices.
    """
    t = token.strip().upper()
    candidates = [
        (f"{t}USDT", "perp"), (f"1000{t}USDT", "perp"),
        (f"1{t}USDT", "perp"), (f"{t}USDT", "spot"),
        (f"1000{t}USDT", "spot"),
    ]
    for sym, market in candidates:
        if market == "perp" and sym in perps:
            return {"symbol": sym, "market": "perp", "elfa_token": token}
        if market == "spot" and sym in spots:
            return {"symbol": sym, "market": "spot", "elfa_token": token}
    return None


def main() -> int:
    out_root = os.environ.get("ELFA_STORAGE_ROOT", DEFAULT_STORAGE_ROOT)
    mroot = os.path.join(out_root, "market")
    os.makedirs(mroot, exist_ok=True)
    print(f"market collection -> {mroot}", flush=True)

    perps = list_perp_symbols()
    spots = list_spot_symbols()
    print(f"  Binance: {len(perps)} perps, {len(spots)} spot pairs",
          flush=True)

    # ---- the universe: what Elfa says people are talking about -------
    attended = top_attended_tokens(out_root, limit=45)
    resolved: List[Dict[str, str]] = []
    seen = set()
    for token, _mentions in attended:
        r = resolve_symbol(token, perps, spots)
        if r and r["symbol"] not in seen:
            seen.add(r["symbol"])
            resolved.append(r)
    # The majors are always included, whether or not anyone is talking
    # about them - a regime feature needs them.
    for sym in MAJORS:
        if sym not in seen:
            r = resolve_symbol(sym[:-4], perps, spots)
            if r and r["symbol"] not in seen:
                seen.add(r["symbol"])
                resolved.append(r)
    print(f"  universe: {len(resolved)} symbols "
          f"(from {len(attended)} attended tokens + majors)", flush=True)
    for r in resolved[:12]:
        print(f"     {r['elfa_token']:>12s} -> {r['symbol']:<16s} "
              f"({r['market']})", flush=True)

    manifest: Dict[str, Any] = {
        "source": "Binance public market data",
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "storage_root": out_root,
        "symbols": resolved,
        "datasets": {},
    }
    now_ms = int(time.time() * 1000)

    # ---- 1. the price series ----------------------------------------
    price_rows: List[Dict[str, Any]] = []
    for i, r in enumerate(resolved, 1):
        for interval, pages, market in (("1h", 3, r["market"]),
                                        ("1d", 3, r["market"])):
            try:
                bars = fetch_klines(r["symbol"], interval,
                                    start_ms=now_ms - 400 * DAY_MS,
                                    max_pages=pages, market=market)
            except Exception as exc:  # noqa: BLE001
                print(f"    {r['symbol']} {interval} failed: "
                      f"{type(exc).__name__}", flush=True)
                continue
            for b in bars:
                b["elfa_token"] = r["elfa_token"]
                b["market"] = r["market"]
                b["date"] = ms_to_date(b["open_time"])
                b["iso"] = ms_to_iso(b["open_time"])
            price_rows.extend(bars)
            if verbose_on(i, len(resolved)):
                print(f"    prices {i}/{len(resolved)} {r['symbol']} "
                      f"{interval}: {len(bars)} bars", flush=True)
    p = os.path.join(mroot, "prices_binance.jsonl")
    _write(p, price_rows)
    manifest["datasets"]["prices_binance"] = {
        "file": os.path.relpath(p, out_root), "rows": len(price_rows),
        "intervals": ["1h", "1d"],
        "note": ("OHLCV for the attention-selected universe; every row "
                 "records which Binance contract it came from")}

    # ---- 2. funding, open interest and positioning ------------------
    deriv_rows: List[Dict[str, Any]] = []
    funding_rows: List[Dict[str, Any]] = []
    for i, r in enumerate(resolved, 1):
        if r["market"] != "perp":
            continue
        sym = r["symbol"]
        try:
            f = fetch_funding_history(sym, limit=1000, max_pages=4)
            for x in f:
                x["elfa_token"] = r["elfa_token"]
                x["date"] = ms_to_date(x["funding_time"])
                x["iso"] = ms_to_iso(x["funding_time"])
            funding_rows.extend(f)
        except Exception as exc:  # noqa: BLE001
            print(f"    funding {sym} failed: {type(exc).__name__}",
                  flush=True)
        for fn in (fetch_open_interest_hist, fetch_taker_long_short,
                   fetch_long_short_ratios):
            try:
                rows = fn(sym, period="1h", limit=500, max_pages=2)
            except Exception as exc:  # noqa: BLE001
                print(f"    {fn.__name__} {sym} failed: "
                      f"{type(exc).__name__}", flush=True)
                continue
            for x in rows:
                x["elfa_token"] = r["elfa_token"]
                x["date"] = ms_to_date(x["timestamp"])
                x["iso"] = ms_to_iso(x["timestamp"])
            deriv_rows.extend(rows)
        if verbose_on(i, len(resolved)):
            print(f"    derivatives {i}/{len(resolved)} {sym}: "
                  f"{len(deriv_rows)} cumulative rows", flush=True)
    p = os.path.join(mroot, "funding_binance.jsonl")
    _write(p, funding_rows)
    manifest["datasets"]["funding_binance"] = {
        "file": os.path.relpath(p, out_root), "rows": len(funding_rows),
        "note": "the REALISED funding rate with its mark price"}
    p = os.path.join(mroot, "derivatives_binance.jsonl")
    _write(p, deriv_rows)
    manifest["datasets"]["derivatives_binance"] = {
        "file": os.path.relpath(p, out_root), "rows": len(deriv_rows),
        "series": ["openInterestHist", "takerlongshortRatio",
                   "topLongShortAccountRatio",
                   "globalLongShortAccountRatio"],
        "note": ("open interest, taker buy/sell VOLUME ratio, and the "
                 "top-trader and global account long/short ratios - the "
                 "positioning layer the regime paper asks for")}

    # ---- 3. the liquidation stream ---------------------------------
    seconds = int(os.environ.get("ELFA_LIQUIDATION_SECONDS", "60"))
    print(f"  capturing the liquidation stream for {seconds}s...", flush=True)
    liq = collect_liquidation_stream(
        seconds=seconds,
        out_path=os.path.join(mroot, "liquidations_binance.jsonl"))
    for r in liq:
        r["date"] = ms_to_date(r["trade_time"])
        r["iso"] = ms_to_iso(r["trade_time"])
    p = os.path.join(mroot, "liquidations_binance.jsonl")
    manifest["datasets"]["liquidations_binance"] = {
        "file": os.path.relpath(p, out_root), "rows": len(liq),
        "capture_seconds": seconds,
        "note": ("FORWARD-TESTING feed from the Binance WebSocket "
                 "!forceOrder@arr. The REST allForceOrders endpoint now "
                 "returns 404, so the stream is the source. Liquidations "
                 "are sparse - an empty capture is normal, not a "
                 "failure.")}

    manifest["totals"] = {
        "price_rows": len(price_rows),
        "funding_rows": len(funding_rows),
        "derivatives_rows": len(deriv_rows),
        "liquidation_rows": len(liq),
        "total_rows": len(price_rows) + len(funding_rows) + len(deriv_rows)
        + len(liq),
    }
    mp = os.path.join(out_root, "manifest_market.json")
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, default=str)
    t = manifest["totals"]
    print(f"\ndone: {t['total_rows']} rows "
          f"(prices {t['price_rows']}, funding {t['funding_rows']}, "
          f"derivatives {t['derivatives_rows']}, "
          f"liquidations {t['liquidation_rows']})", flush=True)
    print(f"manifest: {mp}", flush=True)
    return 0


def verbose_on(i: int, n: int) -> bool:
    return i == 1 or i % 5 == 0 or i == n


if __name__ == "__main__":
    raise SystemExit(main())
