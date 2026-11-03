"""Launch scan: identify early buyers of a NEW memecoin and test whether
they are already-consistent traders.

THE PROBLEM THIS SOLVES
-----------------------
The PEPE holder scan works because PEPE has years of history: its holders
can be listed and their positions measured. A meme that launched an hour
ago has no holder list worth reading, no history, and no PnL.

But you do not need the NEW token's history to judge the wallets in it.
What you need is each wallet's PRIOR record on OTHER memes. So:

  1. Find the wallets that bought the new token EARLY - within the first
     N blocks of its launch. That window is the only window in which
     being early is still possible.
  2. For each of them, pull their track record on the established meme
     universe (Blockscout, keyless).
  3. Run the consistency gate (`leapspace.edge`) on that record. A wallet
     that wins on a new launch because it has a real edge is worth
     following; a wallet that wins because it got lucky is not.
  4. The number of candidates SCANNED is carried into the Deflated
     Sharpe, so screening 300 early buyers sets a far higher bar than
     screening 3.

This is the same methodology as the holder scan, with the roles
reversed: instead of "who holds the winner", it is "who arrived early,
and do they have a record".

THE LIMITATIONS ARE REAL AND STATED
-----------------------------------
* A brand-new token's transfer history may exceed the page budget, in
  which case the earliest transfers are NOT reached and the scan says
  so rather than pretending to see the start.
* A wallet's prior record is measured on OTHER tokens. A wallet with no
  prior memecoin history is reported as INSUFFICIENT, not as skilful.
* Early arrival is NECESSARY but not SUFFICIENT for edge. Both are
  reported separately.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .http import http_json

#: Blockscout host per chain. Only the chains whose Blockscout instance
#: answers from this host are included; the rest are a documented gap.
BLOCKSCOUT_HOSTS = {
    "ethereum": "https://eth.blockscout.com",
}

EVM_RPC = "https://ethereum-rpc.publicnode.com"


def _bs(path: str, params: Optional[Dict[str, Any]] = None,
        chain: str = "ethereum", timeout: int = 30) -> Any:
    host = BLOCKSCOUT_HOSTS.get(chain)
    if not host:
        from .provenance import SourceUnavailable
        raise SourceUnavailable(
            f"Blockscout is not reachable for chain '{chain}' from this host")
    url = host + path
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode(params)
    data, _ = http_json(url, timeout=timeout)
    return data


def _rpc(method: str, params: List[Any], timeout: int = 30) -> Any:
    from .http import http_post_json
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    data, _ = http_post_json(EVM_RPC, body, timeout=timeout)
    if isinstance(data, dict) and data.get("error"):
        err = data["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        from .provenance import SourceUnavailable
        raise SourceUnavailable(f"rpc {method}: {msg}")
    return (data or {}).get("result")


def token_launch(token: str, chain: str = "ethereum") -> Dict[str, Any]:
    """The launch block and creation transaction of a token."""
    addr = _bs(f"/api/v2/addresses/{token}", chain=chain)
    out: Dict[str, Any] = {"token": token, "chain": chain,
                            "status": "unavailable"}
    if not isinstance(addr, dict):
        return out
    txh = addr.get("creation_transaction_hash")
    out["creator"] = addr.get("creator_address_hash")
    if not txh:
        out["reason"] = "no creation transaction on this record"
        return out
    out["creation_tx"] = txh
    try:
        tx = _rpc("eth_getTransactionByHash", [txh])
        bn = (tx or {}).get("blockNumber")
        if bn:
            out["launch_block"] = int(bn, 16)
            out["status"] = "ok"
            try:
                blk = _rpc("eth_getBlockByNumber", [bn, False])
                ts = int((blk or {}).get("timestamp", "0x0"), 16)
                if ts:
                    out["launch_timestamp"] = ts
            except Exception:  # noqa: BLE001
                pass
    except Exception as exc:  # noqa: BLE001
        out["reason"] = f"{type(exc).__name__}: {str(exc)[:140]}"
    return out


def fetch_token_transfers(token: str, chain: str = "ethereum",
                          max_pages: int = 40) -> Dict[str, Any]:
    """ALL transfers of a token, paginated.

    Blockscout returns newest-first with a cursor. For a NEW token the
    whole history fits in a handful of pages, which is exactly what makes
    the launch scan feasible.
    """
    rows: List[Dict[str, Any]] = []
    params: Dict[str, Any] = {}
    pages = 0
    exhausted = False
    while pages < max_pages:
        data = _bs(f"/api/v2/tokens/{token}/transfers", params, chain=chain)
        pages += 1
        if not isinstance(data, dict):
            break
        items = data.get("items") or []
        if not items:
            exhausted = True
            break
        for it in items:
            tok = it.get("token") or {}
            total = it.get("total")
            if isinstance(total, dict):
                raw = total.get("value")
                dec = total.get("decimals")
            else:
                raw = total
                dec = tok.get("decimals")
            rows.append({
                "token_address": tok.get("address_hash") or tok.get("address"),
                "symbol": tok.get("symbol"),
                "decimals": dec,
                "from": (it.get("from") or {}).get("hash"),
                "to": (it.get("to") or {}).get("hash"),
                "amount_raw": raw,
                "block_number": it.get("block_number"),
                "timestamp": it.get("timestamp"),
                "tx_hash": it.get("transaction_hash"),
                "type": it.get("type"),
            })
        nxt = data.get("next_page_params")
        if not nxt:
            exhausted = True
            break
        params = dict(nxt)
        time.sleep(0.25)
    rows.sort(key=lambda r: (r.get("block_number") or 0))
    return {
        "status": "ok",
        "token": token,
        "n_transfers": len(rows),
        "pages_fetched": pages,
        "history_fully_read": exhausted,
        "transfers": rows,
        "note": ("Blockscout returns newest-first; the rows are re-sorted "
                 "oldest-first here. If history_fully_read is False the "
                 "EARLIEST transfers were not reached - the launch window "
                 "cannot be identified and the scan must say so."),
    }


def early_buyers(token: str, chain: str = "ethereum",
                  window_blocks: int = 1000,
                  max_pages: int = 40) -> Dict[str, Any]:
    """Wallets that bought the token within `window_blocks` of its launch."""
    launch = token_launch(token, chain)
    if launch.get("status") != "ok":
        return {"status": "unavailable", "reason": launch.get("reason"),
                "buyers": [], "token": token}
    hist = fetch_token_transfers(token, chain, max_pages=max_pages)
    if not hist.get("history_fully_read"):
        return {
            "status": "insufficient_history",
            "token": token,
            "reason": (f"read {hist['n_transfers']} transfers over "
                       f"{hist['pages_fetched']} pages without reaching the "
                       f"start of this token's history; the launch window "
                       f"cannot be identified"),
            "launch": launch,
            "buyers": [],
        }

    lb = launch["launch_block"]
    cutoff = lb + window_blocks
    buyers: Dict[str, Dict[str, Any]] = {}
    for t in hist["transfers"]:
        blk = t.get("block_number")
        if blk is None or blk > cutoff:
            continue
        frm = (t.get("from") or "").lower()
        to = (t.get("to") or "").lower()
        if not to or to == frm:
            continue
        try:
            amt = float(t.get("amount_raw") or 0) / (10 ** int(
                t.get("decimals") or 18))
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        b = buyers.setdefault(to, {
            "address": t.get("to"), "bought": 0.0, "n_buys": 0,
            "first_block": blk, "last_block": blk,
            "first_timestamp": t.get("timestamp"),
        })
        b["bought"] += amt
        b["n_buys"] += 1
        b["last_block"] = max(b["last_block"], blk)
        if b["first_block"] == blk:
            b["first_timestamp"] = t.get("timestamp")

    out = []
    for b in buyers.values():
        b["entry_lag_blocks"] = b["first_block"] - lb
        b["entry_class"] = _entry_class(b["entry_lag_blocks"])
        out.append(b)
    out.sort(key=lambda r: (r["first_block"], -r["bought"]))
    return {
        "status": "ok",
        "token": token,
        "chain": chain,
        "launch": launch,
        "window_blocks": window_blocks,
        "n_buyers_in_window": len(out),
        "buyers": out,
        "note": ("Only buyers INSIDE the window are listed. A wallet that "
                 "bought after it is not an early buyer and is not here."),
    }


def _entry_class(lag: Optional[int]) -> str:
    if lag is None:
        return "unknown"
    if lag < 10:
        return "sniper (<10 blocks)"
    if lag < 100:
        return "very early (<100 blocks)"
    if lag < 1000:
        return "early (<1000 blocks)"
    return "within window (<1000+ blocks)"


def screen_early_buyers(token: str, chain: str = "ethereum",
                        window_blocks: int = 1000,
                        universe: Optional[Dict[str, Any]] = None,
                        max_candidates: int = 25,
                        max_pages: int = 40,
                        early: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Find early buyers of a token and test each against the edge gate.

    The number of candidates SCANNED is carried into the Deflated Sharpe,
    so screening many early buyers raises the bar for each of them.

    `early` accepts an already-computed `early_buyers()` result, which
    avoids re-fetching the token's whole transfer history. That matters:
    Blockscout rate-limits, and the redundant fetch was failing on
    tokens whose history had already been read successfully.
    """
    from .edge import evaluate_edge
    from .memecoinscan import memecoin_universe, wallet_memecoin_profile

    uni = universe if universe is not None else memecoin_universe()
    eb = early if early is not None else early_buyers(
        token, chain=chain, window_blocks=window_blocks, max_pages=max_pages)
    if eb.get("status") != "ok":
        return {"status": eb.get("status"), "token": token,
                "reason": eb.get("reason"), "candidates": [],
                "launch": eb.get("launch")}

    buyers = eb["buyers"][:max_candidates]
    results = []
    for b in buyers:
        addr = b["address"]
        try:
            prof = wallet_memecoin_profile(addr, uni, chain=chain,
                                           max_items=200)
        except Exception as exc:  # noqa: BLE001
            results.append({"address": addr, "status": "error",
                            "reason": f"{type(exc).__name__}: {exc}"})
            continue
        trades = []
        for pos in prof.get("positions") or []:
            if pos.get("n_buys"):
                trades.append({
                    "ts": pos.get("first_buy") or 0,
                    "token_address": pos.get("address"),
                    "symbol": pos.get("symbol"), "side": "buy",
                    "amount": pos.get("bought"), "price_usd": pos.get("price_usd"),
                    "realised_pnl_usd": None, "return_pct": None,
                })
            if pos.get("n_sells"):
                trades.append({
                    "ts": pos.get("first_sell") or 0,
                    "token_address": pos.get("address"),
                    "symbol": pos.get("symbol"), "side": "sell",
                    "amount": pos.get("sold"), "price_usd": pos.get("price_usd"),
                    "realised_pnl_usd": pos.get("realised_usd"),
                    "return_pct": None,
                })
        edge = evaluate_edge(trades, trials_scanned=len(buyers))
        results.append({
            "address": addr,
            "status": "ok",
            "entry_lag_blocks": b["entry_lag_blocks"],
            "entry_class": b["entry_class"],
            "bought_tokens": b["bought"],
            "n_buys_in_window": b["n_buys"],
            "prior_meme_tokens": prof.get("n_meme_tokens_bought"),
            "edge_verdict": edge.get("verdict"),
            "edge_reason": edge.get("reason"),
            "skill_p": edge.get("bayesian_skill_p"),
            "independent_bets": (edge.get("independent_bets") or {}
                                 ).get("independent_bets"),
            "deflated_sharpe": edge.get("deflated_sharpe"),
            "rejected_by": edge.get("rejected_by"),
            "edge": edge,
        })

    ranked = sorted(
        [r for r in results if r.get("status") == "ok"],
        key=lambda r: ({"CONSISTENT": 0, "WEAK": 1, "INSUFFICIENT": 2,
                        "FLUKE": 3}.get(r.get("edge_verdict"), 4)))
    return {
        "status": "ok",
        "token": token,
        "chain": chain,
        "launch": eb.get("launch"),
        "window_blocks": window_blocks,
        "candidates_scanned": len(buyers),
        "n_in_window": eb.get("n_buyers_in_window"),
        "candidates": ranked,
        "note": ("candidates_scanned is the number of wallets examined; it "
                 "enters the Deflated Sharpe, so a wider screen raises the "
                 "bar for every one of them."),
    }
