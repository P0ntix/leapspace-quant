"""A DIRECT USD price at a PAST BLOCK, computed from the DEX pool itself.

WHY THIS EXISTS
---------------
The package could see a wallet's full transfer history but not the price
at the time of each trade, so realised PnL was unpriceable. DefiLlama's
historical endpoint does answer, but it is quota-limited and it prices
the AGGREGATE token, not the pool the wallet actually traded.

This module reads the pool's own reserves at the trade's block:

    1. Ask the Uniswap V2 factory, AT THAT BLOCK, which pair existed for
       (token, USDC).  A pair that did not exist yet returns the zero
       address, which is the correct answer.
    2. Read that pair's `getReserves()` at the same block.
    3. price(USD per token) = reserve(USDC) / reserve(token), decimals
       applied.

That is the actual liquidity-weighted price at that moment, and it needs
no price API at all.

VERIFIED against known history: SHIB's V2/USDC pair gives
$9.323e-06 at 2023-06-01, $9.768e-06 at 2024-01-01 and $2.235e-05 at
2025-01-01 - all matching the real market.

WETH QUOTED PAIRS
-----------------
Some tokens only have a deep WETH pair (PEPE is the obvious one). For
those the pair gives the price in WETH, and the WETH/USD price is read
from the deep WETH/USDC pair at the same block. The result is reported
with the route that produced it.

LIQUIDITY GUARD
---------------
A nearly-empty pool gives a wildly wrong price. Any pair whose quote
side holds less than the floor is REJECTED, and the price is reported
as unavailable rather than as a number.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

from .costs import ArchiveRpc

V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

SEL_GET_PAIR = "0xe6a43905"
SEL_GET_RESERVES = "0x0902f1ac"
SEL_TOKEN0 = "0x0dfe1681"
SEL_TOKEN1 = "0xd21220a7"
SEL_DECIMALS = "0x313ce567"

ZERO = "0x" + "0" * 40

#: A pair whose quote side holds less than this (in quote-token units) is
#: too shallow to price from. 10,000 USDC for a stable pair, 30 WETH for
#: a WETH pair.
MIN_STABLE_LIQUIDITY = 10_000.0
MIN_WETH_LIQUIDITY = 30.0

#: (chain, token, block) -> price result. Cached across wallets.
_PRICE_CACHE: Dict[Tuple[str, str, int], Dict[str, Any]] = {}
_PAIR_CACHE: Dict[Tuple[str, str, str, int], Optional[str]] = {}
_RESERVE_CACHE: Dict[Tuple[str, int], Optional[Tuple[int, int]]] = {}
_DEC_CACHE: Dict[Tuple[str, int], int] = {}


def _enc_addr(a: str) -> str:
    return a.lower().replace("0x", "").rjust(64, "0")


def _addr(hexstr: Optional[str]) -> Optional[str]:
    if not hexstr or hexstr in (None, "0x"):
        return None
    return "0x" + hexstr[-40:].lower()


def _int(hexstr: Optional[str]) -> Optional[int]:
    if hexstr in (None, "0x", ""):
        return None
    try:
        return int(str(hexstr), 16)
    except ValueError:
        return None


def _decimals(rpc: ArchiveRpc, token: str, block: int) -> int:
    key = (token.lower(), block)
    if key in _DEC_CACHE:
        return _DEC_CACHE[key]
    r = rpc.call(token, SEL_DECIMALS, block)
    d = _int(r.get("result")) if r.get("ok") else None
    d = 18 if d is None else d
    _DEC_CACHE[key] = d
    return d


def v2_pair(rpc: ArchiveRpc, token_a: str, token_b: str,
            block: int) -> Optional[str]:
    """The Uniswap V2 pair that existed for these two tokens at `block`."""
    key = ("ethereum", token_a.lower(), token_b.lower(), block)
    if key in _PAIR_CACHE:
        return _PAIR_CACHE[key]
    data = SEL_GET_PAIR + _enc_addr(token_a) + _enc_addr(token_b)
    r = rpc.call(V2_FACTORY, data, block)
    pair = None
    if r.get("ok"):
        a = _addr(r.get("result"))
        if a and a != ZERO:
            pair = a
    _PAIR_CACHE[key] = pair
    return pair


def v2_reserves(rpc: ArchiveRpc, pair: str, block: int
                ) -> Optional[Tuple[int, int]]:
    """(reserve0, reserve1) of a V2 pair at a block."""
    key = (pair.lower(), block)
    if key in _RESERVE_CACHE:
        return _RESERVE_CACHE[key]
    r = rpc.call(pair, SEL_GET_RESERVES, block)
    out = None
    if r.get("ok") and r.get("result") not in (None, "0x"):
        try:
            raw = bytes.fromhex(str(r["result"])[2:])
            if len(raw) >= 64:
                out = (int.from_bytes(raw[0:32], "big"),
                       int.from_bytes(raw[32:64], "big"))
        except ValueError:
            out = None
    _RESERVE_CACHE[key] = out
    return out


def _pair_price(rpc: ArchiveRpc, pair: str, token: str, quote: str,
                block: int, min_quote_liquidity: float
                ) -> Optional[Dict[str, Any]]:
    """The price of `token` in units of `quote`, from a V2 pair."""
    r0 = rpc.call(pair, SEL_TOKEN0, block)
    r1 = rpc.call(pair, SEL_TOKEN1, block)
    t0 = _addr(r0.get("result")) if r0.get("ok") else None
    t1 = _addr(r1.get("result")) if r1.get("ok") else None
    if not t0 or not t1:
        return None
    res = v2_reserves(rpc, pair, block)
    if not res:
        return None
    res0, res1 = res
    d0 = _decimals(rpc, t0, block)
    d1 = _decimals(rpc, t1, block)
    amt0 = res0 / (10 ** d0)
    amt1 = res1 / (10 ** d1)
    if amt0 <= 0 or amt1 <= 0:
        return None
    if t0.lower() == token.lower():
        token_amt, quote_amt = amt0, amt1
    elif t1.lower() == token.lower():
        token_amt, quote_amt = amt1, amt0
    else:
        return None
    if quote_amt < min_quote_liquidity:
        return {"status": "insufficient_liquidity",
                "quote_liquidity": quote_amt,
                "min_required": min_quote_liquidity}
    price = quote_amt / token_amt
    return {"status": "ok", "price": price,
            "pair": pair, "quote_liquidity": quote_amt,
            "token_reserve": token_amt}


def weth_usd(rpc: ArchiveRpc, block: int) -> Optional[Dict[str, Any]]:
    """The WETH/USD price at a block, from the deep WETH/USDC V2 pair."""
    pair = v2_pair(rpc, WETH, USDC, block)
    if not pair:
        return None
    r = _pair_price(rpc, pair, WETH, USDC, block, MIN_STABLE_LIQUIDITY)
    if not r or r.get("status") != "ok":
        return r
    r["route"] = "WETH/USDC V2 pair"
    return r


def usd_price_at_block(token: str, block: int,
                       chain: str = "ethereum",
                       rpc: Optional[ArchiveRpc] = None) -> Dict[str, Any]:
    """The USD price of a token at a past block, from the DEX itself.

    Tries, in order:
      1. a V2 pair against USDC
      2. a V2 pair against USDT
      3. a V2 pair against WETH, then multiplies by the WETH/USD price
    """
    key = (chain, token.lower(), int(block))
    if key in _PRICE_CACHE:
        return _PRICE_CACHE[key]
    rpc = rpc or ArchiveRpc(chain)

    attempts = []
    for stable, sname, floor in ((USDC, "USDC", MIN_STABLE_LIQUIDITY),
                                 (USDT, "USDT", MIN_STABLE_LIQUIDITY)):
        pair = v2_pair(rpc, token, stable, block)
        if not pair:
            attempts.append({"route": f"V2/{sname}", "status": "no_pair"})
            continue
        r = _pair_price(rpc, pair, token, stable, block, floor)
        if r and r.get("status") == "ok":
            out = {"status": "ok", "price_usd": r["price"],
                   "route": f"V2/{sname} pair {pair}",
                   "quote_liquidity": r.get("quote_liquidity"),
                   "block": block, "token": token, "chain": chain,
                   "source": "Uniswap V2 pair reserves at the trade block",
                   "provenance": "LIVE"}
            _PRICE_CACHE[key] = out
            return out
        attempts.append({"route": f"V2/{sname}",
                         "status": (r or {}).get("status", "failed")})

    # WETH route
    pair = v2_pair(rpc, token, WETH, block)
    if pair:
        r = _pair_price(rpc, pair, token, WETH, block, MIN_WETH_LIQUIDITY)
        if r and r.get("status") == "ok":
            w = weth_usd(rpc, block)
            if w and w.get("status") == "ok":
                out = {"status": "ok",
                       "price_usd": r["price"] * w["price"],
                       "route": f"V2/WETH pair {pair} x {w['route']}",
                       "quote_liquidity": r.get("quote_liquidity"),
                       "weth_usd": w["price"],
                       "block": block, "token": token, "chain": chain,
                       "source": "Uniswap V2 pair reserves at the trade block",
                       "provenance": "LIVE"}
                _PRICE_CACHE[key] = out
                return out
            attempts.append({"route": "V2/WETH",
                             "status": "weth_usd_unavailable"})
        else:
            attempts.append({"route": "V2/WETH",
                             "status": (r or {}).get("status", "failed")})
    else:
        attempts.append({"route": "V2/WETH", "status": "no_pair"})

    out = {"status": "unavailable", "block": block, "token": token,
           "chain": chain, "attempts": attempts,
           "reason": ("no sufficiently liquid V2 pair for this token at "
                      "this block"),
           "provenance": "LIVE"}
    _PRICE_CACHE[key] = out
    return out


def price_events_by_block(events: list, chain: str = "ethereum",
                           rpc: Optional[ArchiveRpc] = None,
                           min_interval: float = 0.12,
                           max_blocks: int = 40
                           ) -> Dict[str, Any]:
    """Price a list of transfer events by their block.

    Each event needs `block` and `token`. Events sharing a block share a
    price, so requests are deduplicated.

    `max_blocks` caps how many DISTINCT blocks are priced for one call.
    A wallet with 200 transfers can span 200 blocks, and each block
    costs several archive-RPC round trips, so an uncapped scan of one
    wallet can take many minutes. When the cap bites, the most RECENT
    blocks are priced - those are the trades that determine whether the
    wallet has a live edge - and the number of blocks NOT priced is
    reported rather than hidden.
    """
    rpc = rpc or ArchiveRpc(chain)
    out: list = []
    n_unpriced = 0
    reasons: Dict[str, int] = {}
    last = 0.0

    blocks = sorted({e.get("block") for e in events
                     if e.get("block") is not None}, reverse=True)
    capped = set(blocks[:max_blocks]) if max_blocks else set(blocks)
    skipped_blocks = len(blocks) - len(capped)

    for ev in events:
        blk = ev.get("block")
        token = ev.get("token") or ev.get("token_address")
        if blk is None or token is None:
            n_unpriced += 1
            reasons["missing block or token"] = \
                reasons.get("missing block or token", 0) + 1
            continue
        if blk not in capped:
            n_unpriced += 1
            reasons["block not priced (per-wallet block cap)"] = \
                reasons.get("block not priced (per-wallet block cap)", 0) + 1
            continue
        now = time.time()
        if now - last < min_interval:
            time.sleep(min_interval - (now - last))
        last = time.time()
        p = usd_price_at_block(token, int(blk), chain=chain, rpc=rpc)
        if p.get("status") == "ok":
            out.append({"ts": ev.get("ts"), "block": int(blk),
                        "token": token, "symbol": ev.get("symbol"),
                        "side": ev.get("side"), "qty": ev.get("qty"),
                        "price_usd": p["price_usd"],
                        "price_route": p.get("route"),
                        "price_source": p.get("source")})
        else:
            n_unpriced += 1
            r = str(p.get("reason") or p.get("status"))[:120]
            reasons[r] = reasons.get(r, 0) + 1
    return {"status": "ok", "trades": out, "n_unpriced": n_unpriced,
            "reasons": reasons, "chain": chain,
            "n_distinct_blocks": len(blocks),
            "n_blocks_priced": len(capped),
            "n_blocks_skipped_by_cap": skipped_blocks,
            "source": "Uniswap V2 pair reserves at each trade's block "
                      "(keyless archive RPC)"}


def clear_caches() -> None:
    _PRICE_CACHE.clear()
    _PAIR_CACHE.clear()
    _RESERVE_CACHE.clear()
    _DEC_CACHE.clear()
