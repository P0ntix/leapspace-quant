"""Reverse-engineer the trading process of PEPE's top holders.

WHAT THIS DOES
--------------
1. Pulls the top N holders of a memecoin (PEPE) from Blockscout's public
   API - no API key.
2. Classifies each holder. This step is ESSENTIAL and is the difference
   between a real analysis and a fake one: the largest "holders" of PEPE
   are EXCHANGE HOT WALLETS (Binance, Bybit, OKX), not traders. Blockscout
   labels them, and they are separated out before any inference runs.
3. For the remaining EOAs, pulls their full ERC-20 transfer history and
   reconstructs their memecoin allocation: what they bought, when
   relative to each token's launch, how big, how long they held, and
   what they did.
4. Summarises the PATTERNS across the surviving traders.

SOURCES (all keyless, all live)
--------------------------------
  Blockscout  https://eth.blockscout.com/api/v2/tokens/{addr}/holders
              https://eth.blockscout.com/api/v2/addresses/{addr}/token-transfers
  DexScreener https://api.dexscreener.com/latest/dex/search?q={symbol}
              (resolves a symbol to its live contract + market cap)
  Ethereum RPC eth_getTransactionByHash (token creation block)

KNOWN LIMITATIONS - READ BEFORE TRUSTING THE OUTPUT
----------------------------------------------------
* **The sample is survivorship-selected.** These are wallets that still
  hold PEPE. A trader who sold PEPE is invisible here. This is the
  survivorship bias the package's own source-reliability register warns
  about, and it means the output describes who KEPT, not who PROFITED.
* **The top of the holder list is dominated by exchanges.** After the
  exchange wallets are removed the sample is small, and every number is
  reported with its denominator.
* **"Successful trader" is not a label this module assigns.** It reports
  measured behaviour and applies the standards-grounded criteria from
  `leapspace/traders.py`, whose thresholds are mostly analyst choices -
  see that module's CRITERIA table.
* Blockscout is reachable for Ethereum only from this host; the other
  Blockscout hosts (base, bsc, arbitrum, gnosis) do not answer here.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from .http import http_json, http_post_json
from .provenance import LIVE, SourceUnavailable

BLOCKSCOUT = {
    "ethereum": "https://eth.blockscout.com",
}

#: Curated meme SYMBOLS. The ADDRESS for each is resolved live through
#: DexScreener (never hard-coded), so a wrong address cannot creep in.
MEME_SYMBOLS = [
    "PEPE", "SHIB", "FLOKI", "WIF", "BONK", "MOG", "POPCAT", "BRETT",
    "TURBO", "SPX", "TRUMP", "PNUT", "GOAT", "NEIRO", "MEW", "PENGU",
    "BOME", "CHILL", "SIGMA", "GIGA", "TOSHI", "USUAL", "MUMU", "WOJAK",
    "RETARDIO", "POPCAT", "AI16Z", "MOODENG", "MEME", "BITCAT",
]

#: Symbols that are ambiguous enough that a search result must clear a
#: liquidity floor before it is accepted as THE token by that symbol.
MIN_LIQUIDITY_USD = 50_000.0

EVM_RPC = "https://ethereum-rpc.publicnode.com"

#: Addresses that are not traders even though Blockscout reports them as
#: EOAs. The burn address is the obvious one; 0x0 and the zero address are
#: the others.
NON_TRADER_ADDRESSES = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
    "0x0000000000000000000000000000000000000001",
}


def _f(v: Any) -> float:
    """Coerce to float; None when not numeric."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0



def _parse_ts(v: Any) -> Optional[int]:
    """Blockscout timestamps are ISO strings. They are NOT integers."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    t = str(v).strip().replace("Z", "+00:00")
    try:
        import datetime as _dt
        return int(_dt.datetime.fromisoformat(t).timestamp())
    except (ValueError, TypeError, OSError):
        return None


def _bs_get(path: str, params: Optional[Dict[str, Any]] = None,
            chain: str = "ethereum", timeout: int = 30
            ) -> Tuple[Optional[int], Any]:
    host = BLOCKSCOUT.get(chain)
    if not host:
        return None, SourceUnavailable(
            f"Blockscout is not reachable for chain '{chain}' from this host "
            f"(verified: base/bsc/arbitrum/gnosis hosts do not answer)")
    url = host + path
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode(params)
    try:
        data, status = http_json(url, timeout=timeout)
        return status, data
    except Exception as exc:  # noqa: BLE001
        return None, SourceUnavailable(f"{url}: {type(exc).__name__}: {exc}")


# --------------------------------------------------------------------------
# 1. Holders
# --------------------------------------------------------------------------
def _holder_entity(holder: Dict[str, Any]) -> Tuple[str, str]:
    """Classify a holder: EXCHANGE / CONTRACT / EOA / UNKNOWN.

    Blockscout attaches `metadata.tags` with a `main_entity` label (e.g.
    "Binance", "Bybit", "OKX") to addresses it recognises as belonging to
    a known entity. Those are hot wallets and custody for other people's
    money - they are NOT traders and must be separated out.
    """
    addr = holder.get("address") or {}
    if addr.get("is_contract"):
        return "CONTRACT", ""
    tags = (addr.get("metadata") or {}).get("tags") or []
    names = []
    for t in tags:
        if isinstance(t, dict):
            meta = t.get("meta") or {}
            n = meta.get("main_entity") or meta.get("tooltipUrl")
            if n:
                names.append(str(n))
    if names:
        return "EXCHANGE", names[0]
    if addr.get("is_verified"):
        return "CONTRACT", addr.get("name") or ""
    return "EOA", ""


def fetch_top_holders(token: str, chain: str = "ethereum", limit: int = 50
                      ) -> Dict[str, Any]:
    """Top holders of an ERC-20, with entity classification."""
    out: List[Dict[str, Any]] = []
    params: Dict[str, Any] = {}
    pages = 0
    while len(out) < limit and pages < 6:
        st, data = _bs_get(f"/api/v2/tokens/{token}/holders", params,
                           chain=chain)
        pages += 1
        if isinstance(data, Exception):
            return {"status": "unavailable", "reason": str(data),
                    "holders": [], "chain": chain, "token": token}
        items = (data or {}).get("items") or []
        if not items:
            break
        for it in items:
            a = it.get("address") or {}
            kind, entity = _holder_entity(it)
            out.append({
                "address": a.get("hash"),
                "value": it.get("value"),
                "kind": kind,
                "entity": entity,
                "is_contract": bool(a.get("is_contract")),
                "is_verified": bool(a.get("is_verified")),
                "name": a.get("name"),
            })
        np_ = (data or {}).get("next_page_params")
        if not np_:
            break
        params = {k: v for k, v in np_.items()}
        time.sleep(0.8)
    out = out[:limit]
    exch = [h for h in out if h["kind"] == "EXCHANGE"]
    contracts = [h for h in out if h["kind"] == "CONTRACT"]
    eoa = [h for h in out if h["kind"] == "EOA"]
    dead = [h for h in eoa
            if (h["address"] or "").lower() in NON_TRADER_ADDRESSES]
    eoa = [h for h in eoa
           if (h["address"] or "").lower() not in NON_TRADER_ADDRESSES]
    return {
        "status": "ok",
        "chain": chain,
        "token": token,
        "n_requested": limit,
        "n_returned": len(out),
        "pages_fetched": pages,
        "holders": out,
        "breakdown": {
            "exchange_hot_wallets": len(exch),
            "contracts_pools_vaults": len(contracts),
            "individual_eoa": len(eoa),
            "burn_or_dead_excluded": len(dead),
        },
        "note": ("Exchange hot wallets hold other people's money. They are "
                 "NOT traders and are excluded from the behavioural "
                 "analysis. Burn/dead addresses are excluded too."),
        "source": f"{BLOCKSCOUT.get(chain)}/api/v2/tokens/{token}/holders",
        "provenance": LIVE,
    }


# --------------------------------------------------------------------------
# 2. The memecoin universe - resolved LIVE, never hard-coded
# --------------------------------------------------------------------------
def memecoin_universe(symbols: Optional[List[str]] = None,
                      chain: str = "ethereum") -> Dict[str, Any]:
    """Resolve meme symbols to live contract addresses via DexScreener.

    Addresses are never typed from memory: each is read from a live
    DexScreener pair record, together with its price, liquidity and
    market cap at that moment.
    """
    syms = symbols or MEME_SYMBOLS
    out: List[Dict[str, Any]] = []
    seen = set()
    gaps: List[Dict[str, Any]] = []
    for sym in syms:
        try:
            data, status = http_json(
                f"https://api.dexscreener.com/latest/dex/search?q={sym}",
                timeout=25)
        except Exception as exc:  # noqa: BLE001
            gaps.append({"symbol": sym,
                         "reason": f"{type(exc).__name__}: {str(exc)[:110]}"})
            continue
        # The endpoint returns {"schemaVersion": ..., "pairs": [...]}, NOT a
        # bare list. Reading it as a list silently resolves nothing.
        if isinstance(data, dict):
            pairs = data.get("pairs") or []
        elif isinstance(data, list):
            pairs = data
        else:
            pairs = []
        if not pairs:
            gaps.append({"symbol": sym, "reason": "no search results"})
            continue
        best = None
        for p in pairs:
            if (p.get("chainId") or "") != chain:
                continue
            bt = p.get("baseToken") or {}
            if (bt.get("symbol") or "").upper() != sym.upper():
                continue
            liq = _f((p.get("liquidity") or {}).get("usd"))
            mc = _f(p.get("marketCap"))
            if liq < MIN_LIQUIDITY_USD:
                continue
            # Pick by MARKET CAP, not liquidity: for a ticker with several
            # same-symbol listings, the one with the real float is the one
            # people mean, and liquidity alone can favour a thin clone.
            if best is None or mc > (best.get("_mc") or 0):
                best = {**p, "_liq": liq, "_mc": mc}
        if best is None:
            gaps.append({"symbol": sym,
                         "reason": f"no {chain} pair above the "
                                   f"${MIN_LIQUIDITY_USD:,.0f} liquidity floor"})
            continue
        addr = (best.get("baseToken") or {}).get("address")
        if addr in seen:
            continue
        seen.add(addr)
        out.append({
            "symbol": sym,
            "address": addr,
            "name": (best.get("baseToken") or {}).get("name"),
            "price_usd": best.get("priceUsd"),
            "liquidity_usd": (best.get("liquidity") or {}).get("usd"),
            "volume_24h_usd": (best.get("volume") or {}).get("h24"),
            "market_cap": best.get("marketCap"),
            "fdv": best.get("fdv"),
            "price_change_24h": (best.get("priceChange") or {}).get("h24"),
            "pair_created_at": best.get("pairCreatedAt"),
            "dex": best.get("dexId"),
            "socials": [s.get("type") for s in
                        ((best.get("info") or {}).get("socials") or [])],
            "source": "dexscreener:latest/dex/search",
        })
        time.sleep(0.35)
    out.sort(key=lambda r: -(r.get("market_cap") or 0))
    return {
        "status": "ok",
        "chain": chain,
        "n": len(out),
        "tokens": out,
        "gaps": gaps,
        "note": ("Addresses and market data are live DexScreener reads. "
                 "The liquidity floor exists so an illiquid impostor token "
                 "with the same ticker cannot displace the real one."),
        "provenance": LIVE,
    }


def _etherscan_fallback(address: str, chain: str,
                         token: Optional[str], max_items: int) -> Dict[str, Any]:
    """The same transfer tape, from Etherscan, when Blockscout fails.

    The key comes from the environment (never a literal). If no key is
    configured this returns a reason, and the caller reports the source
    gap rather than pretending the wallet had no trades.
    """
    from .etherscan import address_transfers, token_transfers

    try:
        # The WALLET's own tape, paginated. Asking Etherscan for the
        # TOKEN's tape and filtering for the wallet returns only the
        # rows in the token's FIRST page - a silent, badly short
        # history. So: the wallet's tape, then filter client-side.
        rows: List[Dict[str, Any]] = []
        offset = 0
        pages = 0
        page = 1000
        while len(rows) < max_items and pages < 12:
            r = address_transfers(address, chain=chain, limit=page,
                                  offset=offset, token=token)
            if r.get("status") != "ok":
                if not rows:
                    return {"status": "unavailable",
                            "reason": r.get("reason") or r.get("status")}
                break
            got = r.get("transfers") or []
            pages += 1
            if not got:
                break
            for t in got:
                rows.append({
                    "token_address": t.get("token_address"),
                    "symbol": t.get("symbol"),
                    "decimals": t.get("decimals") or 18,
                    "from": t.get("from"), "to": t.get("to"),
                    "total": str(int(float(t.get("value") or 0))),
                    "type": None,
                    "block_number": t.get("block"),
                    "timestamp": None, "ts": t.get("ts"),
                    "tx_hash": t.get("tx_hash"),
                })
            offset += page
            if len(got) < page:
                break
        note = ("Blockscout failed; served by Etherscan V2 instead, from "
                "the WALLET's own transfer tape. The decimals are read "
                "from Etherscan where it supplies them and ASSUMED 18 "
                "otherwise, so amounts are only as good as that "
                "assumption.")
        if len(rows) >= max_items:
            note += (" The page budget was reached, so this history may "
                     "be TRUNCATED - it is not the wallet's complete "
                     "history for this token.")
        return {"status": "ok", "source": "etherscan_v2",
                "transfers": rows, "pages_fetched": pages,
                "note": note}
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable",
                "reason": f"{type(exc).__name__}: {str(exc)[:160]}"}

# --------------------------------------------------------------------------
# 3. A wallet's transfer history
# --------------------------------------------------------------------------
def fetch_token_transfers(address: str, chain: str = "ethereum",
                          max_items: int = 400,
                          token: Optional[str] = None) -> Dict[str, Any]:
    """A wallet's ERC-20 transfer history from Blockscout.

    `token` restricts the query to one contract. That is not just an
    optimisation: a sophisticated wallet's most recent transfers are
    DeFi, so scanning generic pages MISSES its older memecoin trades
    entirely. Filtering by token is the only way to see them.
    """
    rows: List[Dict[str, Any]] = []
    params: Dict[str, Any] = {"type": "ERC-20"}
    if token:
        params["token"] = token
    pages = 0
    while len(rows) < max_items and pages < 10:
        st, data = _bs_get(f"/api/v2/addresses/{address}/token-transfers",
                           params, chain=chain)
        pages += 1
        if isinstance(data, Exception):
            # Blockscout returns HTTP 500 on very busy addresses. That
            # was observed live on a PEPE holder, so the scan must not
            # lose the wallet - fall back to Etherscan, which serves the
            # same transfer tape.
            fb = _etherscan_fallback(address, chain, token, max_items)
            if fb.get("status") == "ok":
                return fb
            return {"status": "unavailable", "reason": str(data),
                    "transfers": [], "fallback_error": fb.get("reason")}
        items = (data or {}).get("items") or []
        if not items:
            break
        for it in items:
            tok = it.get("token") or {}
            frm = (it.get("from") or {}).get("hash")
            to = (it.get("to") or {}).get("hash")
            # `total` is an OBJECT: {"decimals": "18", "value": "123..."}.
            # Reading it as a string silently discards every transfer.
            total_obj = it.get("total")
            if isinstance(total_obj, dict):
                raw_amount = total_obj.get("value")
                total_decimals = total_obj.get("decimals")
            else:
                raw_amount = total_obj
                total_decimals = tok.get("decimals")
            rows.append({
                "token_address": tok.get("address_hash") or tok.get("address"),
                "symbol": tok.get("symbol"),
                "decimals": total_decimals or tok.get("decimals"),
                "from": frm,
                "to": to,
                "total": raw_amount,
                "type": it.get("type"),
                "block_number": it.get("block_number"),
                "timestamp": it.get("timestamp"),
                "ts": _parse_ts(it.get("timestamp")),
                "tx_hash": it.get("transaction_hash"),
            })
        np_ = (data or {}).get("next_page_params")
        if not np_:
            break
        params = {k: v for k, v in np_.items()}
        params.setdefault("type", "ERC-20")
        if token:
            params.setdefault("token", token)
        time.sleep(0.5)
    rows = rows[:max_items]
    return {
        "status": "ok",
        "address": address,
        "chain": chain,
        "token_filter": token,
        "n_transfers": len(rows),
        "pages_fetched": pages,
        "transfers": rows,
        "note": ("Blockscout returns newest first. Without a token filter "
                 "the window is the wallet's most recent activity, which "
                 "for an active DeFi wallet contains no memecoins at all."),
        "provenance": LIVE,
    }


# --------------------------------------------------------------------------
# 4. Token launch block (for entry-timing analysis)
# --------------------------------------------------------------------------
_LAUNCH_CACHE: Dict[str, Any] = {}


def token_launch_block(token: str, chain: str = "ethereum"
                       ) -> Dict[str, Any]:
    """The block a token was created in, and its creation timestamp.

    Found from the token's creation transaction. If that cannot be
    resolved, the analysis reports the timing as UNAVAILABLE rather than
    guessing - an entry-lag measured from the wrong origin is worse than
    no entry-lag at all.
    """
    key = f"{chain}:{token}"
    if key in _LAUNCH_CACHE:
        return _LAUNCH_CACHE[key]
    out: Dict[str, Any] = {"token": token, "chain": chain,
                            "status": "unavailable"}
    # The TOKEN endpoint has no creation info. The ADDRESS endpoint for
    # the contract does: creation_transaction_hash.
    st, data = _bs_get(f"/api/v2/addresses/{token}", chain=chain)
    if not isinstance(data, Exception) and isinstance(data, dict):
        txh = data.get("creation_transaction_hash")
        out["creator"] = data.get("creator_address_hash")
        if txh:
            try:
                body = {"jsonrpc": "2.0", "id": 1,
                        "method": "eth_getTransactionByHash",
                        "params": [txh]}
                r, _ = http_post_json(EVM_RPC, body, timeout=25)
                blk = (r or {}).get("result") or {}
                if blk.get("blockNumber"):
                    bn = int(blk["blockNumber"], 16)
                    out["creation_tx"] = txh
                    out["launch_block"] = bn
                    out["status"] = "ok"
                    try:
                        b2 = {"jsonrpc": "2.0", "id": 1,
                              "method": "eth_getBlockByNumber",
                              "params": [blk["blockNumber"], False]}
                        r2, _ = http_post_json(EVM_RPC, b2, timeout=25)
                        ts = int(((r2 or {}).get("result") or {})
                                 .get("timestamp", "0x0"), 16)
                        if ts:
                            out["launch_timestamp"] = ts
                    except Exception:  # noqa: BLE001
                        pass
            except Exception as exc:  # noqa: BLE001
                out["reason"] = f"{type(exc).__name__}: {str(exc)[:110]}"
    _LAUNCH_CACHE[key] = out
    return out


# --------------------------------------------------------------------------
# 5. The behavioural profile of one wallet
# --------------------------------------------------------------------------
def wallet_memecoin_profile(address: str, universe: Dict[str, Any],
                             chain: str = "ethereum",
                             max_items: int = 400,
                             known_exchange_addresses: Optional[Dict[str, str]] = None
                             ) -> Dict[str, Any]:
    """Reconstruct a wallet's memecoin allocation and trading process.

    `known_exchange_addresses` maps address -> entity name for the
    exchange hot wallets found in the holder list. A wallet that transacts
    with one of them is moving custody or market-making flow, not
    personal trading, and is flagged as such.
    """
    uni = {t["address"].lower(): t for t in (universe.get("tokens") or [])}
    # Query PER TOKEN. A wallet's generic transfer history is dominated by
    # whatever it trades most (usually DeFi), so the memecoin trades would
    # be invisible inside it.
    #
    # The per-token calls are independent, so they run CONCURRENTLY. Done
    # serially, Blockscout's intermittent 500s plus the polite delay made
    # this minutes per wallet; the scan is 13 calls x every wallet.
    all_rows: List[Dict[str, Any]] = []
    per_token_gaps: List[Dict[str, Any]] = []
    metas = list(uni.items())

    def _one(meta: Tuple[str, Dict[str, Any]]) -> Tuple[Dict[str, Any],
                                                         List[Dict[str, Any]]]:
        m = meta[1]
        h = fetch_token_transfers(address, chain=chain, max_items=200,
                                  token=m["address"])
        if h.get("status") != "ok":
            return h, [{"token": m.get("symbol"),
                        "reason": str(h.get("reason"))[:120]}]
        return h, []

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=6) as pool:
        for hist, gaps in pool.map(_one, metas):
            if gaps:
                per_token_gaps.extend(gaps)
                continue
            all_rows.extend(hist["transfers"])
    if not all_rows and per_token_gaps:
        return {"address": address, "status": "unavailable",
                "reason": per_token_gaps[0]["reason"], "positions": [],
                "gaps": per_token_gaps}

    # --- aggregate per token ------------------------------------------
    agg: Dict[str, Dict[str, Any]] = {}
    for t in all_rows:
        ta = (t.get("token_address") or "").lower()
        if ta not in uni:
            continue
        meta = uni[ta]
        try:
            amt = float(t.get("total") or 0) / (10 ** int(
                meta.get("decimals") or t.get("decimals") or 18))
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        # Counterparty classification: is the other side an exchange?
        other = (t.get("from") or "").lower() if (
            (t.get("to") or "").lower() == address.lower()) else (
            t.get("to") or "").lower()
        ent = (known_exchange_addresses or {}).get(other)
        a = agg.setdefault(ta, {
            "symbol": meta.get("symbol"), "address": ta,
            "price_usd": meta.get("price_usd"),
            "liquidity_usd": meta.get("liquidity_usd"),
            "market_cap": meta.get("market_cap"),
            "bought": 0.0, "sold": 0.0, "n_buys": 0, "n_sells": 0,
            "first_buy": None, "last_buy": None, "first_sell": None,
            "first_block": None, "cost_usd": 0.0, "proceeds_usd": 0.0,
        })
        if (t.get("to") or "").lower() == address.lower():
            a["bought"] += amt
            a["n_buys"] += 1
            a["cost_usd"] += amt * float(meta.get("price_usd") or 0)
            ts = t.get("ts")
            if ts:
                a["first_buy"] = min(a["first_buy"] or ts, ts)
                a["last_buy"] = max(a["last_buy"] or ts, ts)
                a["buy_timestamps"] = a.get("buy_timestamps", []) + [ts]
            # PER-EVENT record. Without this the position is only an
            # aggregate and no cost basis (FIFO or weighted-average) can
            # be computed - the quantities have to travel with their
            # timestamps.
            a["buy_events"] = a.get("buy_events", []) + [{
                "ts": ts, "qty": amt,
                "block": t.get("block_number"),
                "tx": t.get("tx_hash"),
            }]
            if ent:
                a["exchange_counterparties"] = a.get(
                    "exchange_counterparties", {}) | {ent: 1}
        elif (t.get("from") or "").lower() == address.lower():
            a["sold"] += amt
            a["n_sells"] += 1
            a["proceeds_usd"] += amt * float(meta.get("price_usd") or 0)
            ts = t.get("ts")
            if ts:
                a["first_sell"] = min(a["first_sell"] or ts, ts)
                a["sell_timestamps"] = a.get("sell_timestamps", []) + [ts]
            a["sell_events"] = a.get("sell_events", []) + [{
                "ts": ts, "qty": amt,
                "block": t.get("block_number"),
                "tx": t.get("tx_hash"),
            }]
            if ent:
                a["exchange_counterparties"] = a.get(
                    "exchange_counterparties", {}) | {ent: 1}
        blk = t.get("block_number")
        if blk is not None:
            a["first_block"] = min(a["first_block"] or blk, blk)

    # Warm the launch-block cache for every token this wallet touched, in
    # parallel. It is keyed per token and shared across wallets, so this
    # is paid once per token for the whole scan.
    from concurrent.futures import ThreadPoolExecutor
    touched = list(agg.keys())
    if touched:
        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(lambda ta: token_launch_block(ta, chain), touched))

    positions = []
    for a in agg.values():
        net = a["bought"] - a["sold"]
        held = net > 0
        # Realised + unrealised at the live price.
        realised = a["proceeds_usd"] - (a["sold"] * float(
            a["price_usd"] or 0)) if a["n_sells"] else 0.0
        unrealised = net * float(a["price_usd"] or 0) if held else 0.0
        # Entry lag from launch.
        entry_lag = None
        if a["first_block"] is not None:
            lt = token_launch_block(a["address"], chain)
            if lt.get("status") == "ok":
                entry_lag = a["first_block"] - lt["launch_block"]
        hold_days = None
        if a["first_buy"] and a["first_sell"]:
            hold_days = round((a["first_sell"] - a["first_buy"]) / 86400.0, 2)
        # Median hold across ALL round trips: for each sell, how long
        # since the wallet's first buy of that token.
        all_holds = []
        for st_ in (a.get("sell_timestamps") or []):
            if a.get("first_buy"):
                try:
                    all_holds.append((st_ - a["first_buy"]) / 86400.0)
                except TypeError:
                    pass
        median_hold = (round(sorted(all_holds)[len(all_holds) // 2], 2)
                       if all_holds else None)
        # Buy cadence: how many separate buying events.
        buy_events = len(set(a.get("buy_timestamps") or []))
        exch_cp = a.get("exchange_counterparties") or {}
        positions.append({
            **a,
            "net_tokens": net,
            "still_holding": held,
            "position_value_usd": round(unrealised, 2),
            "realised_usd": round(realised, 2),
            "entry_lag_blocks": entry_lag,
            "entry_class": _entry_class(entry_lag),
            "hold_days_first_round_trip": hold_days,
            "median_hold_days": median_hold,
            "n_buy_events": buy_events,
            "exchange_counterparties": exch_cp,
            "flows_to_exchange": bool(exch_cp),
            "alloc_pct": None,     # filled in below
        })

    positions.sort(key=lambda p: -(p.get("position_value_usd") or 0))
    # ALLOCATION: the share of this wallet's live memecoin portfolio each
    # token represents. This is the "how did they allocate money" answer,
    # and it is computed at TODAY's live price, which is exact for a
    # current portfolio. It is NOT a cost basis.
    total_now = sum(p.get("position_value_usd") or 0 for p in positions)
    for p in positions:
        p["alloc_pct"] = (round((p.get("position_value_usd") or 0) / total_now
                                * 100, 2) if total_now else None)

    # --- aggregate statistics -----------------------------------------
    traded = [p for p in positions if p["n_buys"] > 0]
    closed = [p for p in positions if p["n_buys"] > 0 and p["n_sells"] > 0]
    still = [p for p in positions if p["still_holding"]]
    entry_classes: Dict[str, int] = {}
    for p in positions:
        c = p.get("entry_class") or "unknown"
        entry_classes[c] = entry_classes.get(c, 0) + 1
    lags = [p["entry_lag_blocks"] for p in positions
            if p.get("entry_lag_blocks") is not None]
    holds = [p["hold_days_first_round_trip"] for p in positions
             if p.get("hold_days_first_round_trip") is not None]
    sizes = [p["position_value_usd"] for p in positions
             if p.get("position_value_usd")]

    # "cost" here is the value of the tokens bought AT TODAY'S PRICE. It
    # is NOT what the wallet paid, because no keyless historical price
    # source is available for these contracts (Blockscout's per-transfer
    # exchange_rate is the CURRENT rate, not the rate at that block).
    # It is therefore reported under an honest name and never used as a
    # profit figure.
    total_bought_at_current_price = sum(p["cost_usd"] for p in positions)
    total_now = sum(p["position_value_usd"] for p in positions)
    total_realised_at_current_price = sum(p["realised_usd"] for p in positions)
    n_exch_flow = sum(1 for p in positions if p.get("flows_to_exchange"))
    hold_days_all = [p["median_hold_days"] for p in positions
                     if p.get("median_hold_days") is not None]
    buys_per_token = [p["n_buys"] for p in positions if p.get("n_buys")]

    return {
        "address": address,
        "chain": chain,
        "status": "ok",
        "n_transfers_scanned": len(all_rows),
        "n_meme_tokens_touched": len(positions),
        "n_meme_tokens_bought": len(traded),
        "n_meme_tokens_closed": len(closed),
        "n_meme_tokens_still_held": len(still),
        "total_current_value_usd": round(total_now, 2),
        "total_bought_at_current_price_usd": round(
            total_bought_at_current_price, 2),
        "total_sold_at_current_price_usd": round(
            total_realised_at_current_price, 2),
        "realised_pnl_available": False,
        "realised_pnl_reason": (
            "No keyless historical price source exists for these contracts "
            "on this host: DefiLlama's price API does not index them by "
            "contract, CoinGecko's market_chart returns 401, and "
            "Blockscout's per-transfer exchange_rate is the CURRENT rate "
            "rather than the rate at that block. Realised PnL from a true "
            "cost basis is therefore NOT computed."),
        "n_positions_with_exchange_flow": n_exch_flow,
        "flows_to_exchange": n_exch_flow > 0,
        "median_entry_lag_blocks": (sorted(lags)[len(lags) // 2]
                                    if lags else None),
        "entry_class_breakdown": entry_classes,
        "median_hold_days": (sorted(hold_days_all)[len(hold_days_all) // 2]
                             if hold_days_all else None),
        "median_buys_per_token": (sorted(buys_per_token)[
            len(buys_per_token) // 2] if buys_per_token else None),
        "median_position_value_usd": (sorted(sizes)[len(sizes) // 2]
                                      if sizes else None),
        "positions": positions,
        "source": f"{BLOCKSCOUT.get(chain)}/api/v2/addresses/"
                   f"{address}/token-transfers",
        "provenance": LIVE,
    }


def _entry_class(lag_blocks: Optional[int]) -> str:
    """Classify entry timing. Thresholds are ANALYST CHOICES."""
    if lag_blocks is None:
        return "unknown"
    if lag_blocks < 100:
        return "sniper (<100 blocks)"
    if lag_blocks < 1_000:
        return "very early (<1000 blocks)"
    if lag_blocks < 10_000:
        return "early (<10k blocks)"
    if lag_blocks < 100_000:
        return "mid (<100k blocks)"
    return "late (>=100k blocks)"
