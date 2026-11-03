"""Price a wallet's memecoin trades at HISTORICAL prices and compute a real
cost basis, then run the consistency gate on the result.

WHAT THIS CLOSES
----------------
Until now the package could see a wallet's full transfer history but not
the price at the time of each trade, so realised PnL was unpriceable.
It IS priceable: DefiLlama's historical endpoint works keylessly

    https://coins.llama.fi/prices/historical/{unix_ts}/{chain}:{token}

Note the COLON between chain and token. The comma form returns
`{"coins": {}}` and looks like a dead endpoint - it is not.

The pipeline is:

    transfer history
      -> per-event (ts, qty) buys and sells
      -> historical price at each timestamp (DefiLlama)
      -> FIFO / weighted-average cost basis (leapspace.costs)
      -> closed trades with realised PnL
      -> the consistency gate (leapspace.edge)
      -> the whitelist (leapspace.whitelist)

EVERY trade that cannot be priced is reported as UNPRICED and excluded
from the PnL. It is never silently valued at today's price.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .costs import defillama_price
from .http import http_json

#: Minimum seconds between calls to DefiLlama, per host. The service
#: returns HTTP 429 when pushed, so this is deliberately slow. Combined
#: with the hourly deduplication and the shared cache, a 15-wallet scan
#: needs a few dozen requests instead of several hundred.
_MIN_INTERVAL = 1.1


class _Throttle:
    """A simple per-host rate limiter."""

    def __init__(self, interval: float = _MIN_INTERVAL) -> None:
        self.interval = interval
        self._last = 0.0

    def wait(self) -> None:
        dt = time.time() - self._last
        if dt < self.interval:
            time.sleep(self.interval - dt)
        self._last = time.time()


#: DefiLlama's historical store is HOURLY. Two trades in the same hour
#: share a price, so requests are deduplicated by hour. This is the
#: difference between hundreds of calls (which get HTTP 429) and a
#: handful.
_HOUR = 3600

#: Module-level cache: (chain, contract, hour_bucket) -> price or None.
#: Shared across every wallet in a scan, because most wallets trade the
#: same few tokens in the same few hours.
_PRICE_CACHE: Dict[Any, Any] = {}


def _cached_price(chain: str, contract: str, ts: int,
                  throttle: Optional[_Throttle] = None
                  ) -> Dict[str, Any]:
    key = (chain, contract.lower(), int(ts) // _HOUR)
    if key in _PRICE_CACHE:
        return _PRICE_CACHE[key]
    if throttle:
        throttle.wait()
    r = defillama_price(chain, contract, int(ts))
    out = ({"status": "ok", "price": float(r["price"])}
           if r.get("status") == "ok" and r.get("price") is not None
           else {"status": "unpriced",
                 "reason": r.get("reason") or r.get("status") or "no price"})
    _PRICE_CACHE[key] = out
    return out


def clear_price_cache() -> None:
    """Empty the shared price cache."""
    _PRICE_CACHE.clear()


def _token_price(chain: str, contract: str, ts: int,
                 throttle: Optional[_Throttle] = None) -> Dict[str, Any]:
    """The historical price of a token at a timestamp.

    Returns a dict with either a price or a reason. Never substitutes
    today's price for a missing historical one.
    """
    if not ts:
        return {"status": "unpriced", "reason": "no timestamp on the event"}
    if throttle:
        throttle.wait()
    r = defillama_price(chain, contract, int(ts))
    if r.get("status") == "ok" and r.get("price") is not None:
        return {"status": "ok", "price": float(r["price"])}
    return {"status": "unpriced",
            "reason": r.get("reason") or r.get("status") or "no price"}


def price_position_events(position: Dict[str, Any],
                          chain: str = "ethereum",
                          throttle: Optional[_Throttle] = None
                          ) -> Dict[str, Any]:
    """Price every buy and sell event of one position."""
    contract = position.get("address")
    if not contract:
        return {"status": "unpriced", "reason": "position has no contract",
                "trades": [], "n_unpriced": 0, "reasons": {}}
    out: Dict[str, Any] = {
        "symbol": position.get("symbol"),
        "contract": contract,
        "chain": chain,
        "trades": [],
        "n_unpriced": 0,
        "reasons": {},
    }
    for side, key in (("buy", "buy_events"), ("sell", "sell_events")):
        for ev in position.get(key) or []:
            p = _cached_price(chain, contract, ev.get("ts"), throttle)
            if p["status"] != "ok":
                out["n_unpriced"] += 1
                r = str(p.get("reason"))[:120]
                out["reasons"][r] = out["reasons"].get(r, 0) + 1
                continue
            out["trades"].append({
                "ts": ev.get("ts"),
                "block": ev.get("block"),
                "token": contract,
                "symbol": position.get("symbol"),
                "side": side,
                "qty": ev.get("qty"),
                "price_usd": p["price"],
                "pool": position.get("pool_address"),
            })
    out["trades"].sort(key=lambda t: (t.get("ts") or 0))
    return out


def price_wallet_positions(profile: Dict[str, Any],
                            chain: str = "ethereum",
                            max_events: int = 400,
                            throttle: Optional[_Throttle] = None,
                            method: str = "auto",
                            max_blocks: int = 40) -> Dict[str, Any]:
    """Price every position of one wallet profile.

    `method`:
      "pool"       - read the DEX pool's reserves at each trade's block
                     (the true execution price, keyless archive RPC)
      "defillama"  - DefiLlama's historical index price
      "auto"       - pool first, DefiLlama for whatever the pool cannot
                     price. The result records WHICH method priced each
                     trade.
    """
    from .priceatblock import price_events_by_block, usd_price_at_block

    th = throttle or _Throttle()
    events: List[Dict[str, Any]] = []
    per_token: List[Dict[str, Any]] = []
    for pos in profile.get("positions") or []:
        for side, key in (("buy", "buy_events"), ("sell", "sell_events")):
            for ev in pos.get(key) or []:
                events.append({
                    "ts": ev.get("ts"), "block": ev.get("block"),
                    "token": pos.get("address"), "symbol": pos.get("symbol"),
                    "side": side, "qty": ev.get("qty"),
                })

    trades: List[Dict[str, Any]] = []
    n_unpriced = 0
    reasons: Dict[str, int] = {}

    if method in ("pool", "auto"):
        poolres = price_events_by_block(events, chain=chain,
                                        max_blocks=max_blocks)
        trades.extend(poolres.get("trades") or [])
        n_unpriced += poolres.get("n_unpriced") or 0
        for k, v in (poolres.get("reasons") or {}).items():
            reasons[f"pool: {k}"] = v
        priced_keys = {(t.get("token"), t.get("block")) for t in trades}
        remaining = [e for e in events
                     if (e.get("token"), e.get("block")) not in priced_keys]
    else:
        remaining = events

    if method in ("defillama", "auto") and remaining:
        for pos in profile.get("positions") or []:
            contract = pos.get("address")
            if not contract:
                continue
            r = price_position_events(pos, chain=chain, throttle=th)
            already = {(t.get("token"), t.get("block")) for t in trades}
            for t in r["trades"]:
                if (t.get("token"), t.get("block")) in already:
                    continue
                t["price_source"] = "DefiLlama historical index"
                trades.append(t)
            n_unpriced += r["n_unpriced"]
            for k, v in r["reasons"].items():
                reasons[f"defillama: {k}"] = v

    trades.sort(key=lambda t: (t.get("ts") or 0))
    per_token = []
    seen = set()
    for t in trades:
        k = t.get("token")
        if k in seen:
            continue
        seen.add(k)
        per_token.append({"symbol": t.get("symbol"), "contract": k})

    return {
        "status": "ok",
        "address": profile.get("address"),
        "chain": chain,
        "method": method,
        "n_trades": len(trades),
        "n_unpriced": n_unpriced,
        "unpriced_reasons": reasons,
        "trades": trades,
        "per_token": per_token,
        "provenance": "LIVE",
        "source": ("Uniswap V2 pair reserves at each trade's block "
                   "(keyless archive RPC) and/or DefiLlama historical index"),
    }


def fifo_closed_trades(trades: List[Dict[str, Any]],
                       price_field: str = "price_usd",
                       qty_field: str = "qty") -> List[Dict[str, Any]]:
    """Match buys to sells FIFO and produce CLOSED trades.

    Each closed trade carries the realised PnL and the return, which is
    what the consistency gate needs. A sell larger than the open
    inventory closes only the inventory that exists and is reported as
    over-sold rather than inventing a loss.
    """
    by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in trades:
        key = (t.get("token") or t.get("token_address") or "?").lower()
        by_token.setdefault(key, []).append(t)

    closed: List[Dict[str, Any]] = []
    for token, rows in by_token.items():
        rows = sorted(rows, key=lambda r: (r.get("ts") or 0))
        queue: List[Dict[str, Any]] = []     # FIFO lots
        for r in rows:
            side = r.get("side")
            qty = float(r.get(qty_field) or 0)
            price = r.get(price_field)
            if price is None:
                continue
            if side == "buy":
                queue.append({"qty": qty, "price": float(price),
                              "ts": r.get("ts")})
                continue
            if side != "sell":
                continue
            remaining = qty
            while remaining > 1e-12 and queue:
                lot = queue[0]
                take = min(remaining, lot["qty"])
                if take <= 0:
                    queue.pop(0)
                    continue
                cost = take * lot["price"]
                proceeds = take * float(price)
                closed.append({
                    "ts": r.get("ts"),
                    "token": token,
                    "symbol": r.get("symbol"),
                    "side": "closed",
                    "amount": take,
                    "price_usd": float(price),
                    "entry_price_usd": lot["price"],
                    "cost_usd": cost,
                    "proceeds_usd": proceeds,
                    "realised_pnl_usd": proceeds - cost,
                    "return_pct": ((float(price) / lot["price"]) - 1.0)
                    if lot["price"] else None,
                    "hold_seconds": (r.get("ts") or 0) - (lot["ts"] or 0),
                    "entry_ts": lot["ts"],
                })
                lot["qty"] -= take
                remaining -= take
                if lot["qty"] <= 1e-12:
                    queue.pop(0)
    closed.sort(key=lambda c: c.get("ts") or 0)
    return closed


def build_gate_trades(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert priced transfer events into the trade shape `edge.py` wants.

    `edge.py` reads `amount` and `realised_pnl_usd`; it also needs the
    OPEN legs to count independent bets, so the priced events are kept
    alongside the closed trades.
    """
    out: List[Dict[str, Any]] = []
    for t in trades:
        out.append({
            "ts": t.get("ts"),
            "token_address": t.get("token") or t.get("token_address"),
            "symbol": t.get("symbol"),
            "side": t.get("side"),
            "amount": t.get("qty") if t.get("qty") is not None
            else t.get("amount"),
            "price_usd": t.get("price_usd"),
            "realised_pnl_usd": None,
        })
    for c in fifo_closed_trades(trades):
        out.append({
            "ts": c.get("ts"),
            "token_address": c.get("token"),
            "symbol": c.get("symbol"),
            "side": "closed",
            "amount": c.get("amount"),
            "price_usd": c.get("price_usd"),
            "realised_pnl_usd": c.get("realised_pnl_usd"),
            "return_pct": c.get("return_pct"),
        })
    return out


def realised_pnl_and_edge(priced: Dict[str, Any],
                          trials_scanned: int = 1,
                          basis: str = "fifo") -> Dict[str, Any]:
    """Compute realised PnL and run the consistency gate on priced trades.

    The trades arriving here are ALREADY priced (by DefiLlama's
    historical endpoint), so the cost-basis engine is called directly.
    `costs.wallet_realised_pnl` is deliberately NOT used here: it
    re-prices every trade through the archive-RPC pool-state path, which
    is a different (and slower) method and would replace a price we
    already have with one we do not.
    """
    from .costs import fifo_cost_basis, weighted_average_cost_basis
    from .edge import evaluate_edge

    raw = priced.get("trades") or []
    engine = (fifo_cost_basis(raw) if basis == "fifo"
              else weighted_average_cost_basis(raw))
    gate_trades = build_gate_trades(raw)
    closed = [t for t in gate_trades if t.get("realised_pnl_usd") is not None]
    edge = evaluate_edge(gate_trades, trials_scanned=trials_scanned)
    return {
        "pnl": engine,
        "edge": edge,
        "verdict": edge.get("verdict"),
        "n_closed_trades": len(closed),
        "n_trades_priced": priced.get("n_trades"),
        "n_unpriced": priced.get("n_unpriced"),
        "closed_trades": closed,
        "fee_basis": ("GROSS of gas, DEX fees and MEV - none of these are "
                      "observable from ERC-20 transfers alone. A net figure "
                      "would require per-swap gas and fee logs."),
    }


def screen_wallet(address: str, universe: Dict[str, Any],
                  chain: str = "ethereum",
                  trials_scanned: int = 1,
                  max_items: int = 400) -> Dict[str, Any]:
    """Full pipeline for one wallet: history -> prices -> PnL -> gate."""
    from .memecoinscan import wallet_memecoin_profile

    prof = wallet_memecoin_profile(address, universe, chain=chain,
                                   max_items=max_items)
    if prof.get("status") != "ok":
        return {"status": prof.get("status"), "address": address,
                "reason": prof.get("reason")}
    priced = price_wallet_positions(prof, chain=chain)
    res = realised_pnl_and_edge(priced, trials_scanned=trials_scanned)
    res.update({
        "status": "ok",
        "address": address,
        "chain": chain,
        "n_meme_tokens": prof.get("n_meme_tokens_bought"),
        "n_meme_tokens_closed": prof.get("n_meme_tokens_closed"),
        "entry_class_breakdown": prof.get("entry_class_breakdown"),
        "median_hold_days": prof.get("median_hold_days"),
        "flows_to_exchange": prof.get("flows_to_exchange"),
        "priced": {k: v for k, v in priced.items() if k != "trades"},
        "trades": priced.get("trades"),
    })
    return res
