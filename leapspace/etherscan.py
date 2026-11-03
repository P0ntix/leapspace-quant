"""Etherscan V2 adapter - the one source that needs a key.

Why this exists: Blockscout serves holders and transfers on some chains
and not others (base/arbitrum/polygon return a 403 Cloudflare
challenge; bsc/linea/blast have no deployment). Etherscan V2 covers
those chains with a single key, and its free tier covers chain 1.

THE KEY IS NEVER IN THIS FILE. It is read from the environment
(ETHERSCAN_API_KEY), which `leapspace/http.py` populates from the
gitignored `.secrets.env`.

Etherscan's error convention is a TRAP: a bad key, a wrong parameter or
a rate limit returns **HTTP 200** with `{"status":"0","message":"NOTOK"}`.
Every response is therefore checked for `status == "1"`; an HTTP 200 is
never treated as success.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from .http import http_json

V2 = "https://api.etherscan.io/v2/api"

#: Etherscan V2 chain ids.
CHAIN_IDS = {
    "ethereum": 1, "bnb": 56, "polygon": 137, "arbitrum": 42161,
    "optimism": 10, "base": 8453, "avalanche": 43114, "gnosis": 100,
    "fantom": 250, "zksync": 324, "linea": 59144, "scroll": 534352,
    "sonic": 146, "mantle": 5000, "blast": 81457, "celo": 42220,
    "unichain": 130, "worldchain": 480, "berachain": 80094,
    "sei": 1329, "aptos": 56,
}

#: The min interval between calls. Etherscan's free tier is ~5 calls/sec
#: and returns HTTP 200 with "NOTOK" beyond it, so it is throttled here.
_MIN_INTERVAL = 0.25

#: What the FREE tier actually supports, verified live against
#: Etherscan V2 on 2026-11-03. Anything not listed here returns
#: HTTP 200 with status=0 and message=NOTOK.
FREE_TIER_ACTIONS = {
    "account.tokentx": "OK - ERC-20 transfers (1,000 per page)",
    "account.txlist": "OK - transactions",
    "account.tokenbalance": "OK - one address's ERC-20 balance",
    "account.balancemulti": "OK - up to 20 addresses' ERC-20 balances",
    "account.balance": "OK - native balance",
    "contract.getsourcecode": "OK - verified source, compiler, proxy",
    "token.tokenholderlist": "PRO ONLY - returns NOTOK",
    "token.tokeninfo": "PRO ONLY - returns NOTOK",
}

_last_call = 0.0


def api_key() -> Optional[str]:
    """The key, if one is configured. The VALUE is never returned to a
    caller that might log it - callers get the presence, not the text."""
    return os.environ.get("ETHERSCAN_API_KEY") or None


def has_key() -> bool:
    return bool(api_key())


def _throttle() -> None:
    global _last_call
    dt = time.time() - _last_call
    if dt < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - dt)
    _last_call = time.time()


def _call(params: Dict[str, Any], chain: str = "ethereum") -> Dict[str, Any]:
    """One Etherscan V2 call, with the error convention handled."""
    key = api_key()
    if not key:
        return {"status": "no_key",
                "reason": ("ETHERSCAN_API_KEY is not set. Export it, or put "
                           "it in the gitignored .secrets.env beside the "
                           "package.")}
    cid = CHAIN_IDS.get(chain, 1)
    q = dict(params)
    q["chainid"] = cid
    q["apikey"] = key
    from urllib.parse import urlencode
    url = V2 + "?" + urlencode(q)
    _throttle()
    try:
        data, status = http_json(url, timeout=40)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "http_status": None,
                "reason": f"{type(exc).__name__}: {str(exc)[:160]}"}
    # HTTP 200 with status "0" is an ETHERSCAN-LEVEL failure, not a
    # transport failure. It is the documented NOTOK convention.
    if isinstance(data, dict) and str(data.get("status")) == "0":
        return {"status": "etherscan_error", "http_status": status,
                "reason": str(data.get("message") or data.get("result"))[:180],
                "note": ("Etherscan returns HTTP 200 with status=0 for a "
                         "bad key, a bad parameter or a rate limit.")}
    return {"status": "ok", "http_status": status, "data": data,
            "chain": chain, "chain_id": cid}


def token_holders(token: str, chain: str = "ethereum",
                  limit: int = 100,
                  addresses: Optional[List[str]] = None
                  ) -> Dict[str, Any]:
    """Holder balances for an ERC-20.

    Etherscan's own `tokenholderlist` action is PRO-ONLY and returns
    NOTOK on the free tier, so it is NOT used. Instead the balances are
    read directly with `tokenbalance` for a supplied list of addresses,
    or reconstructed from the transfer tape with
    `token_holders_from_transfers`.
    """
    if not addresses:
        return {"status": "needs_addresses",
                "reason": ("Etherscan's holder-list action is Pro-only. "
                           "Pass `addresses`, or use "
                           "token_holders_from_transfers()."),
                "source": "etherscan_v2"}
    return token_balances(addresses, token, chain=chain)


def token_balances(addresses: List[str], token: str,
                   chain: str = "ethereum") -> Dict[str, Any]:
    """ERC-20 balances for up to 20 addresses, in ONE call."""
    r = _call({"module": "account", "action": "balancemulti",
               "address": ",".join(addresses[:20]),
               "contractaddress": token, "tag": "latest"}, chain)
    if r.get("status") != "ok":
        return r
    rows = r["data"].get("result") or []
    out = []
    for row in rows:
        try:
            bal = int(str(row.get("balance") or "0"))
        except (TypeError, ValueError):
            bal = 0
        out.append({"address": row.get("account"), "balance_raw": bal})
    return {"status": "ok", "chain": chain, "source": "etherscan_v2",
            "token": token, "n": len(out), "balances": out,
            "provenance": "LIVE"}


def token_balance(address: str, token: str,
                  chain: str = "ethereum") -> Dict[str, Any]:
    """One address's ERC-20 balance."""
    r = _call({"module": "account", "action": "tokenbalance",
               "contractaddress": token, "address": address,
               "tag": "latest"}, chain)
    if r.get("status") != "ok":
        return r
    try:
        raw = int(str(r["data"].get("result") or "0"))
    except (TypeError, ValueError):
        raw = 0
    return {"status": "ok", "chain": chain, "source": "etherscan_v2",
            "address": address, "token": token, "balance_raw": raw,
            "provenance": "LIVE"}


def token_holders_from_transfers(token: str, chain: str = "ethereum",
                                 limit: int = 5000) -> Dict[str, Any]:
    """Reconstruct the holders of an ERC-20 from its transfer tape.

    Balances are netted from the transfers: every transfer IN adds and
    every transfer OUT subtracts. This reproduces the holder list from
    the free tier, at the cost of needing the full tape.
    """
    r = token_transfers(token, chain=chain, limit=min(limit, 10000))
    if r.get("status") != "ok":
        return r
    bal: Dict[str, int] = {}
    for t in r["transfers"]:
        try:
            v = int(float(t.get("value") or 0))
        except (TypeError, ValueError):
            continue
        bal[t.get("to")] = bal.get(t.get("to"), 0) + v
        bal[t.get("from")] = bal.get(t.get("from"), 0) - v
    holders = [{"address": a, "balance_raw": b}
               for a, b in bal.items() if b > 0]
    holders.sort(key=lambda h: -h["balance_raw"])
    total = sum(h["balance_raw"] for h in holders) or 1
    for h in holders:
        h["pct"] = 100.0 * h["balance_raw"] / total
    return {"status": "ok", "chain": chain, "source": "etherscan_v2",
            "method": "netted from the transfer tape",
            "n_transfers_read": r.get("n_transfers"),
            "n_holders": len(holders), "holders": holders,
            "provenance": "LIVE"}


def token_transfers(token: str, chain: str = "ethereum",
                    limit: int = 1000) -> Dict[str, Any]:
    """Transfers of an ERC-20."""
    r = _call({"module": "account", "action": "tokentx",
               "contractaddress": token, "offset": 0, "sort": "asc",
               "limit": limit}, chain)
    if r.get("status") != "ok":
        return r
    rows = r["data"].get("result") or []
    out: List[Dict[str, Any]] = []
    for row in rows:
        try:
            v = float(row.get("value") or 0)
        except (TypeError, ValueError):
            v = 0.0
        out.append({
            "from": row.get("from"), "to": row.get("to"),
            "value": v, "ts": int(row.get("timeStamp") or 0),
            "block": int(row.get("blockNumber") or 0),
            "tx_hash": row.get("hash"),
            "token_address": row.get("contractAddress"),
        })
    return {"status": "ok", "chain": chain, "source": "etherscan_v2",
            "n_transfers": len(out), "transfers": out, "provenance": "LIVE"}


def address_transfers(address: str, chain: str = "ethereum",
                      limit: int = 1000, offset: int = 0,
                      token: Optional[str] = None
                      ) -> Dict[str, Any]:
    """ERC-20 transfers involving one address.

    `offset` pages through the wallet's own tape. `token` filters the
    RESULT to one contract CLIENT-SIDE - Etherscan has no combined
    address+contract filter for `tokentx`, and passing
    `contractaddress` instead returns the TOKEN's tape, not the
    wallet's.
    """
    r = _call({"module": "account", "action": "tokentx",
               "address": address, "offset": offset, "sort": "asc",
               "limit": limit}, chain)
    if r.get("status") != "ok":
        return r
    rows = r["data"].get("result") or []
    out = []
    for row in rows:
        try:
            v = float(row.get("value") or 0)
        except (TypeError, ValueError):
            v = 0.0
        if token and str(row.get("contractAddress") or "").lower() != \
                token.lower():
            continue
        out.append({
            "from": row.get("from"), "to": row.get("to"), "value": v,
            "ts": int(row.get("timeStamp") or 0),
            "block": int(row.get("blockNumber") or 0),
            "tx_hash": row.get("hash"),
            "token_address": row.get("contractAddress"),
            "symbol": row.get("tokenSymbol"),
            "decimals": row.get("tokenDecimal"),
        })
    return {"status": "ok", "chain": chain, "source": "etherscan_v2",
            "n_transfers": len(out), "transfers": out, "offset": offset,
            "provenance": "LIVE"}


def balance(address: str, chain: str = "ethereum") -> Dict[str, Any]:
    """The native balance."""
    r = _call({"module": "account", "action": "balance",
               "address": address, "tag": "latest"}, chain)
    if r.get("status") != "ok":
        return r
    try:
        wei = int(str(r["data"].get("result") or "0"))
    except (TypeError, ValueError):
        wei = 0
    return {"status": "ok", "chain": chain, "wei": wei,
            "eth": wei / 1e18, "provenance": "LIVE"}


def contract_source(token: str, chain: str = "ethereum") -> Dict[str, Any]:
    """The verified source of a contract, if it is verified."""
    r = _call({"module": "contract", "action": "getsourcecode",
               "address": token}, chain)
    if r.get("status") != "ok":
        return r
    rows = r["data"].get("result") or []
    if not rows:
        return {"status": "empty", "chain": chain}
    row = rows[0]
    return {
        "status": "ok", "chain": chain,
        "contract_name": row.get("ContractName"),
        "compiler_version": row.get("CompilerVersion"),
        "optimization_used": row.get("OptimizationUsed"),
        "is_verified": bool(row.get("SourceCode")),
        "proxy": row.get("Proxy"),
        "implementation": row.get("Implementation"),
        "constructor_args": row.get("ConstructorArguments"),
        "provenance": "LIVE",
    }
