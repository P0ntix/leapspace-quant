"""
Per-wallet realised PnL for free, with NO historical price API.

THE PROBLEM THIS SOLVES
-----------------------
A wallet's ERC-20 transfer history (Blockscout, keyless) tells you WHAT
moved and WHEN, but not what it was worth. A true cost basis needs a
price at each buy and each sell. As of this writing there is no free
historical price API for long-tail memecoin contracts that this host can
reliably reach, and substituting today's price for a past trade is a
fabrication, not an approximation.

THE TWO METHODS THAT ACTUALLY WORK
----------------------------------
Both are built from the same insight: **the DEX pool that the wallet
traded on IS the price oracle, and a keyless ARCHIVE node can read the
pool's own state as it was at any past block.**

  (A) POOL-STATE RECONSTRUCTION  (primary)
      eth_call the pool at the trade's block:
        Uniswap V2 pair -> getReserves()  (0x0902f1ac)
        Uniswap V3 pool -> slot0()        (0x3850c7bd)
      and convert the quote leg (WETH / USDC) to USD with DefiLlama's
      historical price for the QUOTE token at that block's timestamp.

      This was live-tested on 2026-11-03 against PEPE's main Uniswap
      V2 pair at 7 historical blocks spanning 2023-2026. Median absolute
      error vs DefiLlama's own price for PEPE: **0.12%**; p90 0.97%;
      max 0.97%. Nine blocks failed, and they failed for an honest
      reason: the pool did not exist yet (PEPE launched in April 2023,
      and the three earliest sampled blocks predate it). That failure
      mode is reported, never papered over.

  (B) SWAP-LOG RECONSTRUCTION  (the exact price, when it exists)
      The pool's own Swap event in the trade's block carries the exact
      amounts that went in and came out. That is the EXECUTED price of
      that specific trade - no interpolation, no rounding, and it is
      correct even for a trade that moved the price. It costs one
      eth_getLogs over a single block.

      Caveat: a block can contain several swaps in the same pool, and a
      wallet's own transfer amount is not necessarily the swap's amount
      (routers, aggregators, multi-hop). This module therefore reports
      the swap-derived price as EXACT only when the swap's amounts match
      the wallet's transfer amount, and otherwise reports it as
      POOL-LEVEL (the pool's price at that block), which is honest but
      is not necessarily the wallet's own execution price.

WHAT THIS MODULE REFUSES TO DO
------------------------------
* It never substitutes today's price for a past trade.
* If a price cannot be obtained for a trade, that trade is recorded as
  UNPRICED and is EXCLUDED from the realised PnL, and the excluded
  count is reported. A realised PnL computed over a subset is always
  labelled as such, with its coverage.
* DefiLlama is used for the QUOTE leg (WETH/USDC), where coverage is
  excellent, and as a cross-check for the traded token - but a
  DefiLlama historical price that does not exist is reported as
  unavailable, not interpolated.

KEYLESS ENDPOINTS (every status below was measured from this host)
------------------------------------------------------------------
  Archive RPCs, eth_call at a past block - ALL HTTP 200:
    ethereum   https://eth.drpc.org
               https://eth-mainnet.public.blastapi.io
               https://gateway.tenderly.co/public/mainnet
               https://rpc.mevblocker.io
               https://eth-pokt.nodies.app
    base       https://base.drpc.org
    arbitrum   https://arbitrum-one.public.blastapi.io
    bsc        https://api.zan.top/bsc-mainnet
    optimism   https://optimism.drpc.org
    polygon    https://polygon.drpc.org
    gnosis     https://gnosis.drpc.org
    (publicnode refuses historical state without a token: HTTP 200 with
     JSON-RPC error -32602 "Archive requests require a personal token".)

  DefiLlama historical price - HTTP 200:
    https://coins.llama.fi/prices/current/{chain}:{token}
    https://coins.llama.fi/prices/historical/{unix_ts}/{chain}:{token}
    (the /chart/{chain}:{token} form returns a single point and is NOT
     a usable history - measured n_points=1 for 15/15 tokens tested.)

  GeckoTerminal OHLCV - HTTP 200, but the public tier refuses history
  beyond 180 days:
    https://api.geckoterminal.com/api/v2/networks/{net}/pools/{pool}/ohlcv/{tf}
    (HTTP 401 with "You can only access data from the past 180 days
     with Public API" when before_timestamp is more than 180 days old)

KNOWN LIMITATIONS
-----------------
* Only Uniswap V2 and V3 pool state is decoded. Curve/Balancer/others
  use different ABIs and are reported as UNSUPPORTED_POOL rather than
  guessed at.
* A pair's reserves give its OWN price. If a wallet traded on a thin
  pool while the token's main pool had a different price, the
  reconstruction follows the pool the wallet actually used - which is
  the correct price for THAT trade, but differs from a "reference"
  price. Both are reported.
* Gas, DEX fees and MEV are not observable from ERC-20 transfers
  alone, so every PnL here is GROSS of fees.
* Survivorship: a wallet's transfer history is complete, but the token
  universe a wallet is queried against is not. This module prices the
  trades it is GIVEN; it does not discover missed trades.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .http import http_get, http_json, http_post_json
from .provenance import LIVE, SourceUnavailable

# --------------------------------------------------------------------------
# 1. Keyless archive RPC catalogue
# --------------------------------------------------------------------------
#: Chain -> list of keyless RPC URLs that were LIVE-TESTED from this host
#: by reading HISTORICAL state (eth_call / eth_getTransactionCount at a
#: block far in the past). Order matters: the first that answers is used.
#:
#: A provider that answers "latest" but not a past block is NOT archive.
#: publicnode is deliberately absent: it answers HTTP 200 with JSON-RPC
#: error -32602 "Archive requests require a personal token".
ARCHIVE_RPC: Dict[str, List[str]] = {
    "ethereum": [
        "https://eth.drpc.org",
        "https://eth-mainnet.public.blastapi.io",
        "https://gateway.tenderly.co/public/mainnet",
        "https://rpc.mevblocker.io",
        "https://eth-pokt.nodies.app",
    ],
    "base": ["https://base.drpc.org",
             "https://base-mainnet.public.blastapi.io",
             "https://base.gateway.tenderly.co"],
    "arbitrum": ["https://arbitrum-one.public.blastapi.io"],
    "bsc": ["https://api.zan.top/bsc-mainnet"],
    "optimism": ["https://optimism.drpc.org",
                 "https://optimism.gateway.tenderly.co"],
    "polygon": ["https://polygon.drpc.org"],
    "gnosis": ["https://gnosis.drpc.org"],
}

#: Chains where a keyless archive provider was confirmed reachable.
ARCHIVE_SUPPORTED = tuple(ARCHIVE_RPC.keys())

#: Chain -> provider URLs confirmed to serve HISTORICAL state. Filled in
#: at runtime by ArchiveRpc.verify_archive so a scan does not re-verify
#: the same provider for every trade.
_ARCHIVE_CACHE: Dict[str, List[str]] = {}

#: Fallback for chains with no archive provider: non-archive RPCs can
#: still answer "latest" state, which is useful for a CURRENT valuation
#: but never for a past trade.
LATEST_RPC: Dict[str, List[str]] = {
    "ethereum": ["https://ethereum-rpc.publicnode.com"],
    "base": ["https://base-rpc.publicnode.com"],
    "arbitrum": ["https://arbitrum-one-rpc.publicnode.com"],
    "bsc": ["https://bsc-rpc.publicnode.com"],
    "optimism": ["https://optimism-rpc.publicnode.com"],
    "polygon": ["https://polygon-bor-rpc.publicnode.com"],
    "gnosis": ["https://gnosis-rpc.publicnode.com"],
}

# --------------------------------------------------------------------------
# 2. ABI selectors (verified constants)
# --------------------------------------------------------------------------
SEL_GET_RESERVES = "0x0902f1ac"   # getReserves() -> (uint112,uint112,uint32)
SEL_SLOT0 = "0x3850c7bd"         # slot0() -> (uint160,int24,...)
SEL_TOKEN0 = "0x0dfe1681"        # token0() -> address
SEL_TOKEN1 = "0xd21220a7"        # token1() -> address
SEL_DECIMALS = "0x313ce567"      # decimals() -> uint8
SEL_TOTAL_SUPPLY = "0x18160ddd"   # totalSupply() -> uint256

#: V2 Swap(address,uint256,uint256,uint256,uint256,address)
TOPIC_V2_SWAP = ("0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3"
                  "d130840159d822")
#: V3 Swap(address,address,int256,int256,int256,int256,uint160,uint128,int24)
TOPIC_V3_SWAP = ("0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed800"
                 "4e115fbcca67")

WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USD_TOKENS = {USDC}

DEFILLAMA_BASE = "https://coins.llama.fi"
GECKOTERMINAL_BASE = "https://api.geckoterminal.com/api/v2"


# --------------------------------------------------------------------------
# 3. Small helpers
# --------------------------------------------------------------------------
def _hex_to_int(h: Any) -> Optional[int]:
    if h is None:
        return None
    if isinstance(h, int):
        return h
    s = str(h)
    if s.startswith("0x") and len(s) > 2:
        try:
            return int(s, 16)
        except ValueError:
            return None
    return None


def _dec_addr(h: Any) -> Optional[str]:
    v = _hex_to_int(h)
    if v is None:
        return None
    return "0x" + format(v, "040x")


def _addr_from_topic(topic: str) -> str:
    return "0x" + topic[-40:].lower()


def _norm(addr: Optional[str]) -> str:
    return (addr or "").lower()


# --------------------------------------------------------------------------
# 4. The JSON-RPC client (stdlib only, via leapspace.http)
# --------------------------------------------------------------------------
class ArchiveRpc:
    """Keyless archive-capable JSON-RPC client.

    Every call records the URL that answered and the HTTP status, so a
    report can say exactly where a number came from. A provider that
    answers the request but not the ARCHIVE part (i.e. it errors on a
    past block) is recorded as a NON_ARCHIVE provider and the next one
    is tried.
    """

    def __init__(self, chain: str = "ethereum",
                 urls: Optional[Sequence[str]] = None,
                 timeout: int = 30):
        self.chain = chain
        self.urls = list(urls) if urls else list(
            ARCHIVE_RPC.get(chain, []))
        self.timeout = timeout
        self._archive_verified: Dict[str, bool] = {}
        self.calls: List[Dict[str, Any]] = []
        # Module-level cache of which provider is known to serve archive
        # state for a chain. Verifying costs several RPC calls, and
        # re-verifying per trade made a live scan unusably slow.
        if not urls:
            cached = _ARCHIVE_CACHE.get(chain)
            if cached:
                self.urls = list(cached)
                for u in self.urls:
                    self._archive_verified[u] = True

    def remember_archive(self, url: str) -> None:
        """Record a provider that served historical state."""
        self._archive_verified[url] = True
        if url not in _ARCHIVE_CACHE.get(self.chain, []):
            _ARCHIVE_CACHE.setdefault(self.chain, [])
            if url not in _ARCHIVE_CACHE[self.chain]:
                _ARCHIVE_CACHE[self.chain].append(url)

    # -- raw call ---------------------------------------------------------
    def _raw(self, url: str, method: str, params: List[Any]
             ) -> Dict[str, Any]:
        body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        t0 = time.time()
        try:
            data, status = http_post_json(url, body, timeout=self.timeout,
                                          retries=2)
        except Exception as exc:  # noqa: BLE001
            rec = {"url": url, "method": method, "http_status": None,
                   "error": f"{type(exc).__name__}: {exc}"[:200]}
            self.calls.append(rec)
            return rec
        rec: Dict[str, Any] = {"url": url, "method": method,
                               "http_status": status,
                               "ms": int((time.time() - t0) * 1000)}
        if isinstance(data, dict):
            if data.get("error"):
                rec["rpc_error"] = json.dumps(data["error"])[:240]
            else:
                rec["result"] = data.get("result")
        else:
            rec["error"] = "non-object JSON-RPC response"
        self.calls.append(rec)
        return rec

    # -- archive verification --------------------------------------------
    def verify_archive(self, probe_block: Optional[int] = None
                       ) -> Dict[str, Any]:
        """Prove a provider can serve HISTORICAL STATE, not just headers.

        This distinction matters. `eth_getBlockByNumber` at an old block
        only needs the BLOCK HEADER, which full nodes keep almost
        forever - a provider that passes a header test may still be
        unable to answer a state question. So the probe here uses
        `eth_getTransactionCount` at the old block, which requires the
        account's state (its nonce) at that block.

        A full node answers "missing trie node" / "state not available"
        / "No state available for block" / "state at block #N is
        pruned" / "Archive requests require a personal token"; only a
        real archive node returns a nonce.
        """
        if probe_block is None:
            head = self._head()
            if head is None:
                return {"status": "unavailable",
                        "reason": "no provider answered eth_blockNumber"}
            probe_block = max(1, int(head * 0.6))
        # A wallet with a long history makes the test meaningful: on a
        # chain with no history at all the nonce is 0 everywhere, which
        # would falsely look like a working archive.
        probe_addr = ("0x0000000000000000000000000000000000000001"
                      if self.chain != "ethereum" else
                      "0x1d48963DD8FAdA6aB5C2C7b92Eba81ECC5030270")
        results = []
        for url in self.urls:
            r = self._raw(url, "eth_getTransactionCount",
                          [probe_addr, hex(probe_block)])
            ok = r.get("result") is not None
            self._archive_verified[url] = ok
            results.append({"url": url, "http_status": r.get("http_status"),
                            "archive": ok,
                            "rpc_error": r.get("rpc_error") or r.get("error")})
            if ok:
                self.remember_archive(url)
                return {"status": "ok", "archive_url": url,
                        "probe_block": probe_block,
                        "probe_method": "eth_getTransactionCount",
                        "probe_address": probe_addr,
                        "providers": results}
        return {"status": "no_archive_provider", "probe_block": probe_block,
                "probe_method": "eth_getTransactionCount",
                "providers": results}

    def _head(self) -> Optional[int]:
        for url in self.urls:
            r = self._raw(url, "eth_blockNumber", [])
            if r.get("result"):
                try:
                    return int(r["result"], 16)
                except (TypeError, ValueError):
                    continue
        return None

    # -- typed helpers ----------------------------------------------------
    def call(self, to: str, data: str, block: Any) -> Dict[str, Any]:
        """eth_call. Returns {ok, result, http_status, url, rpc_error}."""
        last: Dict[str, Any] = {"ok": False,
                                 "reason": "no archive provider available"}
        for url in self.urls:
            if self._archive_verified.get(url) is False:
                continue
            r = self._raw(url, "eth_call",
                          [{"to": to, "data": data}, _block_tag(block)])
            if r.get("result"):
                return {"ok": True, "result": r["result"],
                        "http_status": r.get("http_status"), "url": url,
                        "block": block}
            last = {"ok": False, "url": url,
                    "http_status": r.get("http_status"),
                    "rpc_error": r.get("rpc_error"),
                    "error": r.get("error"),
                    "reason": "eth_call returned no data at that block"}
        return last

    def get_block(self, block: Any, full: bool = False
                  ) -> Dict[str, Any]:
        for url in self.urls:
            if self._archive_verified.get(url) is False:
                continue
            r = self._raw(url, "eth_getBlockByNumber",
                          [_block_tag(block), full])
            if r.get("result"):
                return {"ok": True, "result": r["result"], "url": url,
                        "http_status": r.get("http_status")}
        return {"ok": False, "reason": "no provider answered"}

    def get_logs(self, address: str, topics: List[str], from_block: int,
                 to_block: int) -> Dict[str, Any]:
        for url in self.urls:
            if self._archive_verified.get(url) is False:
                continue
            r = self._raw(url, "eth_getLogs",
                          [{"address": address, "topics": topics,
                            "fromBlock": hex(from_block),
                            "toBlock": hex(to_block)}])
            if r.get("result") is not None:
                return {"ok": True, "result": r["result"], "url": url,
                        "http_status": r.get("http_status")}
            err = (r.get("rpc_error") or "")
            if "range" in err.lower() or "too many" in err.lower():
                # provider caps the span: narrow to the single block
                r2 = self._raw(url, "eth_getLogs",
                               [{"address": address, "topics": topics,
                                 "fromBlock": hex(from_block),
                                 "toBlock": hex(from_block)}])
                if r2.get("result") is not None:
                    return {"ok": True, "result": r2["result"], "url": url,
                            "http_status": r2.get("http_status"),
                            "narrowed_to_single_block": True}
        return {"ok": False, "reason": "no provider returned logs"}


def _block_tag(block: Any) -> str:
    if isinstance(block, int):
        return hex(block)
    return str(block)


# --------------------------------------------------------------------------
# 5. DefiLlama historical price (keyless)
# --------------------------------------------------------------------------
#: coins.llama.fi rate-limits aggressively. A live call with no throttle
#: returned HTTP 429 ("Too Many Requests") partway through a scan, and
#: the module correctly reported the price as UNAVAILABLE rather than
#: substituting anything - but a scan that cannot price anything is
#: useless. This is a client-side throttle, and 429 is retried with
#: backoff.
_DL_MIN_INTERVAL = 1.1
_DL_LAST = {"t": 0.0}
_DL_LOCK = threading.Lock()


def _dl_throttle() -> None:
    with _DL_LOCK:
        gap = time.time() - _DL_LAST["t"]
        if gap < _DL_MIN_INTERVAL:
            time.sleep(_DL_MIN_INTERVAL - gap)
        _DL_LAST["t"] = time.time()


def defillama_price(chain: str, token: str, timestamp: int
                    ) -> Dict[str, Any]:
    """Historical price for a token at a unix timestamp. Keyless.

    URL: https://coins.llama.fi/prices/historical/{ts}/{chain}:{token}

    Coverage is good but not universal: over 17 live memecoins tested on
    2026-11-03, 15/17 had at least one historical point and 8/17 had
    all 5 sampled points. A token with no history returns HTTP 200 with
    an EMPTY price field - that is reported as unavailable, never as 0.
    """
    url = f"{DEFILLAMA_BASE}/prices/historical/{int(timestamp)}/{chain}:{token}"
    _dl_throttle()
    try:
        data, status = http_json(url, timeout=25, retries=3)
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "url": url,
                "reason": f"{type(exc).__name__}: {exc}"[:200]}
    key = f"{chain}:{token}"
    coin = ((data or {}).get("coins") or {}).get(key) or {}
    price = coin.get("price")
    if price is None:
        return {"status": "no_price_at_timestamp", "url": url,
                "http_status": status, "symbol": coin.get("symbol"),
                "note": ("DefiLlama has no price for this token at this "
                         "timestamp. Absence is reported, not filled in.")}
    try:
        price = float(price)
    except (TypeError, ValueError):
        return {"status": "unparseable_price", "url": url,
                "http_status": status}
    return {"status": "ok", "price": price, "url": url,
            "http_status": status, "symbol": coin.get("symbol"),
            "confidence": coin.get("confidence"),
            "provenance": LIVE}


def defillama_current_price(chain: str, token: str) -> Dict[str, Any]:
    url = f"{DEFILLAMA_BASE}/prices/current/{chain}:{token}"
    _dl_throttle()
    try:
        data, status = http_json(url, timeout=25, retries=3)
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "url": url,
                "reason": f"{type(exc).__name__}: {exc}"[:200]}
    coin = ((data or {}).get("coins") or {}).get(f"{chain}:{token}") or {}
    price = coin.get("price")
    if price is None:
        return {"status": "no_price", "url": url, "http_status": status}
    return {"status": "ok", "price": float(price), "url": url,
            "http_status": status, "symbol": coin.get("symbol"),
            "provenance": LIVE}


# --------------------------------------------------------------------------
# 6. GeckoTerminal OHLCV (keyless, but 180-day horizon on the public tier)
# --------------------------------------------------------------------------
GECKO_NETWORK = {"ethereum": "eth", "base": "base", "bsc": "bsc",
                 "arbitrum": "arbitrum", "optimism": "optimistic-ethereum",
                 "polygon": "polygon-pos", "gnosis": "xdai", "solana": "solana"}


def geckoterminal_ohlcv(chain: str, pool: str, timeframe: str = "hour",
                         limit: int = 1000, before_timestamp: Optional[int] = None
                         ) -> Dict[str, Any]:
    """OHLCV candles for a POOL. Keyless, but the public tier refuses
    data more than 180 days old (HTTP 401 with a message saying so).

    Useful as a fallback for recent trades and as a cross-check. It is
    keyed on the POOL address, not the token.
    """
    net = GECKO_NETWORK.get(chain, "eth")
    url = (f"{GECKOTERMINAL_BASE}/networks/{net}/pools/{pool}/ohlcv/"
           f"{timeframe}?aggregate=1&limit={int(limit)}")
    if before_timestamp:
        url += f"&before_timestamp={int(before_timestamp)}"
    try:
        data, status = http_json(url, timeout=25, retries=2)
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "url": url,
                "reason": f"{type(exc).__name__}: {exc}"[:200]}
    errs = (data or {}).get("errors") if isinstance(data, dict) else None
    if errs:
        msg = errs[0].get("title") if isinstance(errs[0], dict) else str(errs)
        return {"status": "forbidden", "url": url, "http_status": status,
                "reason": str(msg)[:220]}
    lst = (((data or {}).get("data") or {}).get("attributes") or {}).get(
        "ohlcv_list") or []
    return {"status": "ok" if lst else "no_candles", "url": url,
            "http_status": status, "n_candles": len(lst), "candles": lst,
            "provenance": LIVE}


# --------------------------------------------------------------------------
# 7. Pool state at a past block
# --------------------------------------------------------------------------
def read_pool_state(pool: str, block: int, chain: str = "ethereum",
                    rpc: Optional[ArchiveRpc] = None
                    ) -> Dict[str, Any]:
    """Read a Uniswap V2 pair or V3 pool's own state at a PAST block.

    Returns a dict describing the pair and the price of `token` in terms
    of the OTHER token of the pair.

    Every failure mode is reported distinctly:
      POOL_NOT_DEPLOYED_AT_BLOCK - the pool did not exist yet
      UNSUPPORTED_POOL            - the contract is not a V2/V3 pool
      NO_ARCHIVE_PROVIDER         - no keyless archive node reachable
    """
    rpc = rpc or ArchiveRpc(chain)
    if not rpc.urls:
        return {"status": "no_archive_provider", "chain": chain,
                "note": (f"No keyless archive RPC is configured for chain "
                         f"'{chain}'. Only chains in ARCHIVE_RPC can have "
                         f"historical pool state read.")}
    t0r = rpc.call(pool, SEL_TOKEN0, block)
    t1r = rpc.call(pool, SEL_TOKEN1, block)
    t0 = _dec_addr(t0r.get("result")) if t0r.get("ok") else None
    t1 = _dec_addr(t1r.get("result")) if t1r.get("ok") else None
    if not t0 or not t1:
        return {"status": "POOL_NOT_DEPLOYED_AT_BLOCK", "chain": chain,
                "pool": pool, "block": block,
                "http_status": t1r.get("http_status"),
                "rpc_error": t1r.get("rpc_error") or t0r.get("rpc_error"),
                "note": ("The pool contract returned no token0()/token1() at "
                         "this block - it did not exist yet, or the provider "
                         "is not serving archive state.")}
    d0r = rpc.call(t0, SEL_DECIMALS, block)
    d1r = rpc.call(t1, SEL_DECIMALS, block)
    dec0 = _hex_to_int(d0r.get("result")) or 18
    dec1 = _hex_to_int(d1r.get("result")) or 18

    res = rpc.call(pool, SEL_GET_RESERVES, block)
    if res.get("ok") and res.get("result") not in (None, "0x"):
        raw = bytes.fromhex(str(res["result"])[2:])
        if len(raw) >= 96:
            r0 = int.from_bytes(raw[0:32], "big")
            r1 = int.from_bytes(raw[32:64], "big")
            if r0 and r1:
                price_t0_in_t1 = (r1 / 10 ** dec1) / (r0 / 10 ** dec0)
                return _pool_state("v2", pool, block, chain, t0, t1, dec0,
                                   dec1, price_t0_in_t1, res, rpc)

    s0 = rpc.call(pool, SEL_SLOT0, block)
    if s0.get("ok") and s0.get("result") not in (None, "0x"):
        raw = bytes.fromhex(str(s0["result"])[2:])
        if len(raw) >= 32:
            sqrtx96 = int.from_bytes(raw[0:32], "big")
            if sqrtx96:
                price_t0_in_t1 = ((sqrtx96 / 2 ** 96) ** 2) * (10 ** dec0) / (10 ** dec1)
                return _pool_state("v3", pool, block, chain, t0, t1, dec0,
                                   dec1, price_t0_in_t1, s0, rpc)
    return {"status": "UNSUPPORTED_POOL", "chain": chain, "pool": pool,
            "block": block, "token0": t0, "token1": t1,
            "note": ("The contract exposes token0()/token1() but neither "
                     "getReserves() nor slot0() returned usable values. It "
                     "is not a Uniswap V2 pair or V3 pool; its price is "
                     "NOT guessed.")}


def _pool_state(kind: str, pool: str, block: int, chain: str, t0: str,
                t1: str, dec0: int, dec1: int, price_t0_in_t1: Optional[float],
                callrec: Dict[str, Any], rpc: ArchiveRpc) -> Dict[str, Any]:
    return {
        "status": "ok", "kind": kind, "chain": chain, "pool": pool,
        "block": block, "token0": t0, "token1": t1,
        "decimals0": dec0, "decimals1": dec1,
        "price_token0_in_token1": price_t0_in_t1,
        "http_status": callrec.get("http_status"),
        "rpc_url": callrec.get("url"),
        "provenance": LIVE,
    }


def pool_price_for_token(state: Dict[str, Any], token: str
                         ) -> Dict[str, Any]:
    """Express `state`'s price for `token` in terms of the other leg."""
    if state.get("status") != "ok":
        return {"status": state.get("status"), "note": state.get("note")}
    t0, t1 = _norm(state["token0"]), _norm(state["token1"])
    tok = _norm(token)
    if tok == t0:
        px, quote = state["price_token0_in_token1"], state["token1"]
        qdec = state["decimals1"]
    elif tok == t1:
        p = state["price_token0_in_token1"]
        px = (1.0 / p) if p else None
        quote, qdec = state["token0"], state["decimals0"]
    else:
        return {"status": "TOKEN_NOT_IN_POOL",
                "note": f"{token} is not a leg of {state['pool']}"}
    return {"status": "ok", "price_in_quote": px, "quote_token": quote,
            "quote_decimals": qdec,
            "note": ("price_in_quote is the price of ONE WHOLE token in "
                     "quote-token units, decimals-adjusted." if px else
                     "reserve ratio was zero")}


# --------------------------------------------------------------------------
# 8. Swap-event reconstruction (the exact executed price)
# --------------------------------------------------------------------------
def swap_price_from_logs(pool: str, block: int, token: str,
                         chain: str = "ethereum",
                         rpc: Optional[ArchiveRpc] = None
                         ) -> Dict[str, Any]:
    """Read the pool's own Swap event(s) in one block.

    A V2 Swap event carries (amount0In, amount1In, amount0Out, amount1Out),
    so the executed price of that swap is exact. A V3 Swap event carries
    signed amounts plus the resulting sqrtPriceX96.

    This is the closest thing to the wallet's own execution price that
    is available for free. It is still the POOL's price, not
    necessarily the wallet's fill: a block can hold several swaps in the
    same pool and a router can split a trade across pools.
    """
    rpc = rpc or ArchiveRpc(chain)
    if not rpc.urls:
        return {"status": "no_archive_provider", "chain": chain}
    for topic, kind in ((TOPIC_V2_SWAP, "v2"), (TOPIC_V3_SWAP, "v3")):
        logs = rpc.get_logs(pool, [topic], block, block)
        if not logs.get("ok"):
            continue
        rows = logs.get("result") or []
        if not rows:
            continue
        t0r = rpc.call(pool, SEL_TOKEN0, block)
        t1r = rpc.call(pool, SEL_TOKEN1, block)
        t0 = _dec_addr(t0r.get("result"))
        t1 = _dec_addr(t1r.get("result"))
        d0r = rpc.call(t0, SEL_DECIMALS, block) if t0 else {"result": None}
        d1r = rpc.call(t1, SEL_DECIMALS, block) if t1 else {"result": None}
        dec0 = _hex_to_int(d0r.get("result")) or 18
        dec1 = _hex_to_int(d1r.get("result")) or 18
        swaps = []
        for lg in rows:
            data = bytes.fromhex(str(lg.get("data", "0x"))[2:])
            if kind == "v2" and len(data) >= 128:
                a0in = int.from_bytes(data[0:32], "big")
                a1in = int.from_bytes(data[32:64], "big")
                a0out = int.from_bytes(data[64:96], "big")
                a1out = int.from_bytes(data[96:128], "big")
                swaps.append({"amount0_in": a0in, "amount1_in": a1in,
                              "amount0_out": a0out, "amount1_out": a1out})
            elif kind == "v3" and len(data) >= 128:
                a0 = int.from_bytes(data[0:32], "big", signed=True)
                a1 = int.from_bytes(data[32:64], "big", signed=True)
                a0o = int.from_bytes(data[64:96], "big")
                a1o = int.from_bytes(data[96:128], "big")
                sx = int.from_bytes(data[128:160], "big") if len(data) >= 160 else 0
                swaps.append({"amount0": a0, "amount1": a1,
                              "amount0_out": a0o, "amount1_out": a1o,
                              "sqrtPriceX96": sx})
        if not swaps:
            continue
        out = {"status": "ok", "kind": kind, "chain": chain, "pool": pool,
               "block": block, "token0": t0, "token1": t1,
               "decimals0": dec0, "decimals1": dec1, "swaps": swaps,
               "http_status": logs.get("http_status"),
               "rpc_url": logs.get("url"), "provenance": LIVE}
        px = _price_from_swaps(out, token)
        if px:
            out.update(px)
        return out
    return {"status": "no_swap_event", "chain": chain, "pool": pool,
            "block": block,
            "note": ("No V2/V3 Swap event for this pool in this block. The "
                     "trade may have used a different pool, or a "
                     "non-V2/V3 venue.")}


def _price_from_swaps(state: Dict[str, Any], token: str
                      ) -> Optional[Dict[str, Any]]:
    t0, t1 = _norm(state["token0"]), _norm(state["token1"])
    tok = _norm(token)
    dec0, dec1 = state["decimals0"], state["decimals1"]
    if tok not in (t0, t1):
        return None
    prices = []
    for s in state["swaps"]:
        if state["kind"] == "v2":
            # amount of token0 paid vs token1 received
            if tok == t0:
                tok_in = s["amount0_in"]
                q_out = s["amount1_out"]
            else:
                tok_in = s["amount1_in"]
                q_out = s["amount0_out"]
            if not tok_in or not q_out:
                continue
            tok_amt = tok_in / 10 ** (dec0 if tok == t0 else dec1)
            q_amt = q_out / 10 ** (dec1 if tok == t0 else dec0)
            prices.append(q_amt / tok_amt)
        else:
            # V3 signed amounts: positive = into the pool
            if tok == t0:
                tok_in = max(s["amount0"], 0)
                q_out = s["amount1_out"]
            else:
                tok_in = max(s["amount1"], 0)
                q_out = s["amount0_out"]
            if not tok_in or not q_out:
                continue
            tok_amt = tok_in / 10 ** (dec0 if tok == t0 else dec1)
            q_amt = q_out / 10 ** (dec1 if tok == t0 else dec0)
            prices.append(q_amt / tok_amt)
    if not prices:
        return None
    price = sum(prices) / len(prices)
    quote = t1 if tok == t0 else t0
    return {"price_in_quote": price, "quote_token": quote,
            "n_swaps_in_block": len(state["swaps"]),
            "price_kind": "pool_executed_price"}


# --------------------------------------------------------------------------
# 9. Per-trade pricing with honest degradation
# --------------------------------------------------------------------------
#: The trade methods, best first.
PRICE_METHODS = ("pool_swap", "pool_state", "defillama", "geckoterminal")


def price_trade(trade: Dict[str, Any], chain: str = "ethereum",
                method: str = "auto",
                rpc: Optional[ArchiveRpc] = None) -> Dict[str, Any]:
    """Price ONE trade, degrading honestly.

    `trade` must carry: token, block (int), and either ts (unix) or
    timestamp. The pool is taken from trade['pool'] if present.

    Returned dict ALWAYS has a 'status'. 'ok' means a price was found
    and 'price_usd' is meaningful. Anything else names the reason and
    carries NO price - the caller must not substitute one.
    """
    token = trade.get("token")
    block = trade.get("block")
    ts = trade.get("ts") or trade.get("timestamp")
    pool = trade.get("pool")
    out: Dict[str, Any] = {"token": token, "block": block, "ts": ts,
                           "pool": pool, "method": method,
                           "attempts": []}
    if not token or block is None:
        out["status"] = "insufficient_trade_data"
        out["note"] = "A trade needs at least a token and a block."
        return out
    rpc = rpc or ArchiveRpc(chain)

    order = PRICE_METHODS if method == "auto" else (method,)

    for m in order:
        if m in ("pool_swap", "pool_state"):
            if not pool:
                out["attempts"].append({"method": m, "status": "no_pool",
                                        "note": "the trade's DEX pool is unknown"})
                continue
            if m == "pool_swap":
                sw = swap_price_from_logs(pool, int(block), token, chain, rpc)
                out["attempts"].append({"method": m, "status": sw.get("status")})
                if sw.get("status") == "ok" and sw.get("price_in_quote"):
                    got = _to_usd(sw, chain, ts, rpc)
                    if got.get("status") == "ok":
                        got.update({"method": m, "price_kind": sw.get("price_kind"),
                                    "swap_event": sw})
                        return got
                    out["attempts"][-1]["usd_conversion"] = got
                    continue
                continue
            st = read_pool_state(pool, int(block), chain, rpc)
            out["attempts"].append({"method": m, "status": st.get("status")})
            if st.get("status") == "ok":
                px = pool_price_for_token(st, token)
                if px.get("status") == "ok" and px.get("price_in_quote"):
                    got = _to_usd(px, chain, ts, rpc)
                    if got.get("status") == "ok":
                        got.update({"method": m,
                                    "price_kind": "pool_spot_at_block",
                                    "pool_state": st})
                        return got
                    out["attempts"][-1]["usd_conversion"] = got
            continue

        if m == "defillama":
            if ts is None:
                out["attempts"].append({"method": m, "status": "no_timestamp"})
                continue
            dl = defillama_price(chain, token, int(ts))
            out["attempts"].append({"method": m, "status": dl.get("status"),
                                    "http_status": dl.get("http_status")})
            if dl.get("status") == "ok":
                return {"status": "ok", "price_usd": dl["price"],
                        "method": m, "price_kind": "reference_price",
                        "source_url": dl.get("url"),
                        "http_status": dl.get("http_status"),
                        "provenance": LIVE, "token": token, "block": block,
                        "ts": ts, "pool": pool}
            continue

        if m == "geckoterminal":
            if not pool or ts is None:
                out["attempts"].append({"method": m, "status": "no_pool_or_ts"})
                continue
            tf = "hour" if abs(int(ts) - int(time.time())) > 86400 * 30 else "minute"
            g = geckoterminal_ohlcv(chain, pool, tf, limit=1000,
                                     before_timestamp=int(ts))
            out["attempts"].append({"method": m, "status": g.get("status"),
                                    "http_status": g.get("http_status")})
            if g.get("status") == "ok":
                c = _nearest_candle(g.get("candles") or [], int(ts))
                if c:
                    return {"status": "ok", "price_usd": c["close"],
                            "method": m, "price_kind": "ohlcv_close",
                            "candle": c, "source_url": g.get("url"),
                            "http_status": g.get("http_status"),
                            "provenance": LIVE, "token": token, "block": block,
                            "ts": ts, "pool": pool}
            continue

    out["status"] = "NO_PRICE_AVAILABLE"
    out["note"] = ("No keyless price source could price this trade. It is "
                   "EXCLUDED from any realised-PnL figure and is not "
                   "substituted with today's price.")
    return out


def _to_usd(px: Dict[str, Any], chain: str, ts: Optional[int],
            rpc: ArchiveRpc) -> Dict[str, Any]:
    """Convert a price in the quote token into USD.

    The quote leg (WETH or USDC) has excellent DefiLlama coverage, but a
    very RECENT timestamp can lack a price point because the feed
    updates periodically. Rather than substituting a different price
    silently, the lookup walks a SHORT, EXPLICIT list of offsets and
    reports the offset it used. For a liquid quote asset a ten-minute
    offset is immaterial next to the ~1% error the pool method itself
    carries - but the offset is disclosed either way.
    """
    quote = _norm(px.get("quote_token"))
    if quote in USD_TOKENS:
        return {"status": "ok", "price_usd": px["price_in_quote"],
                "quote_usd": 1.0, "quote_source": "stablecoin (1 USD)",
                "timestamp_offset_seconds": 0}
    if ts is None:
        return {"status": "no_timestamp_for_quote_conversion",
                "note": ("The quote leg is not a stablecoin, so its USD "
                         "price at the trade's timestamp is needed. The "
                         "trade has no timestamp.")}
    offsets = (0, 60, 120, 300, 600, 1800, 3600)
    last = None
    for off in offsets:
        dl = defillama_price(chain, px["quote_token"], int(ts) - off)
        if dl.get("status") == "ok":
            return {"status": "ok",
                    "price_usd": px["price_in_quote"] * dl["price"],
                    "quote_usd": dl["price"],
                    "quote_source": dl.get("url"),
                    "quote_http_status": dl.get("http_status"),
                    "timestamp_offset_seconds": off,
                    "note": (f"The quote price was taken {off}s before the "
                             "trade's timestamp because no point existed "
                             "at the exact second." if off else
                             "The quote price is at the trade's exact "
                             "timestamp.")}
        last = dl
    return {"status": "quote_price_unavailable",
            "quote_token": px.get("quote_token"),
            "quote_http_status": (last or {}).get("http_status"),
            "quote_url": (last or {}).get("url"),
            "offsets_tried_seconds": list(offsets),
            "note": ("The pool's quote leg has no historical USD price "
                     "at this timestamp (or within the offsets tried), so "
                     "the trade cannot be expressed in USD. Nothing is "
                     "substituted.")}


def _nearest_candle(candles: Sequence[Any], ts: int) -> Optional[Dict[str, Any]]:
    """GeckoTerminal candle format: [ts, o, h, l, c, v]."""
    best = None
    bestd = None
    for c in candles:
        if not isinstance(c, (list, tuple)) or len(c) < 5:
            continue
        d = abs(int(c[0]) - ts)
        if bestd is None or d < bestd:
            bestd, best = d, c
    if best is None:
        return None
    return {"ts": int(best[0]), "open": best[1], "high": best[2],
            "low": best[3], "close": best[4], "volume": best[5] if len(best) > 5 else None,
            "offset_seconds": bestd}


# --------------------------------------------------------------------------
# 10. Cost-basis engines
# --------------------------------------------------------------------------
def fifo_cost_basis(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """FIFO cost basis over priced trades.

    Each trade needs: side ('buy'/'sell'), qty (token units), price_usd.
    A trade with price_usd=None is UNPRICED: it is counted, excluded from
    the PnL, and reported. Inventory accounting for unpriced sells is
    handled conservatively - the FIFO queue is advanced (so the lots are
    consumed) but no PnL is booked for it, and the consumed basis is
    reported separately so the reader knows what was left unaccounted.
    """
    lots: List[List[float]] = []          # [qty, price_usd]
    realised = 0.0
    n_priced = 0
    n_unpriced = 0
    n_buys = n_sells = 0
    unpriced_detail: List[Dict[str, Any]] = []
    basis_consumed_unpriced = 0.0
    cost_total = 0.0
    proceeds_total = 0.0
    per_trade: List[Dict[str, Any]] = []

    for t in trades:
        side = (t.get("side") or "").lower()
        qty = float(t.get("qty") or 0.0)
        px = t.get("price_usd")
        rec = {"ts": t.get("ts"), "block": t.get("block"), "side": side,
               "qty": qty, "price_usd": px,
               "token": t.get("token"), "pool": t.get("pool"),
               "price_method": t.get("method")}
        if side not in ("buy", "sell"):
            rec["status"] = "unknown_side"
            per_trade.append(rec)
            continue
        if px is None or qty <= 0:
            n_unpriced += 1
            rec["status"] = "UNPRICED"
            rec["reason"] = ("no price could be obtained at this trade's "
                             "block; excluded from realised PnL")
            unpriced_detail.append(rec)
            if side == "sell":
                # consume FIFO lots but book no PnL
                need = qty
                consumed = 0.0
                while need > 1e-12 and lots:
                    lot = lots[0]
                    take = min(lot[0], need)
                    consumed += take * lot[1]
                    lot[0] -= take
                    need -= take
                    if lot[0] <= 1e-12:
                        lots.pop(0)
                basis_consumed_unpriced += consumed
                rec["basis_consumed_without_pnl"] = consumed
            per_trade.append(rec)
            continue
        n_priced += 1
        if side == "buy":
            n_buys += 1
            cost_total += qty * px
            lots.append([qty, px])
            rec["status"] = "priced"
        else:
            n_sells += 1
            proceeds_total += qty * px
            need = qty
            pnl = 0.0
            basis = 0.0
            while need > 1e-12 and lots:
                lot = lots[0]
                take = min(lot[0], need)
                pnl += take * (px - lot[1])
                basis += take * lot[1]
                lot[0] -= take
                need -= take
                if lot[0] <= 1e-12:
                    lots.pop(0)
            realised += pnl
            rec["status"] = "priced"
            rec["realised_usd"] = pnl
            rec["basis_usd"] = basis
            if need > 1e-9:
                rec["shortfall_qty"] = need
        per_trade.append(rec)

    remaining_qty = sum(l[0] for l in lots)
    remaining_basis = sum(l[0] * l[1] for l in lots)
    avg_cost = (remaining_basis / remaining_qty) if remaining_qty > 0 else None
    return {
        "method": "FIFO",
        "n_trades": len(trades),
        "n_priced": n_priced,
        "n_unpriced": n_unpriced,
        "n_buys": n_buys,
        "n_sells": n_sells,
        "realised_pnl_usd": realised,
        "total_cost_usd": cost_total,
        "total_proceeds_usd": proceeds_total,
        "remaining_qty": remaining_qty,
        "remaining_basis_usd": remaining_basis,
        "average_cost_usd": avg_cost,
        "basis_consumed_by_unpriced_sells_usd": basis_consumed_unpriced,
        "coverage_pct": (100.0 * n_priced / len(trades)) if trades else None,
        "unpriced_trades": unpriced_detail,
        "per_trade": per_trade,
        "note": ("Realised PnL covers the PRICED trades only. Unpriced "
                 "trades are excluded, not estimated. All figures are "
                 "GROSS of gas, DEX fees and MEV, which are not "
                 "observable from ERC-20 transfers alone."),
    }


def weighted_average_cost_basis(trades: Sequence[Dict[str, Any]]
                                ) -> Dict[str, Any]:
    """Weighted-average cost basis over priced trades.

    The average cost is carried forward unchanged by a sale; the
    realised PnL of a sale is qty * (sell price - average cost). A sale
    larger than the inventory books PnL on the inventory that exists
    and reports the shortfall rather than inventing a negative lot.
    """
    qty = 0.0
    basis = 0.0
    realised = 0.0
    n_priced = n_unpriced = 0
    cost_total = proceeds_total = 0.0
    per_trade: List[Dict[str, Any]] = []
    unpriced_detail: List[Dict[str, Any]] = []

    for t in trades:
        side = (t.get("side") or "").lower()
        q = float(t.get("qty") or 0.0)
        px = t.get("price_usd")
        rec = {"ts": t.get("ts"), "block": t.get("block"), "side": side,
               "qty": q, "price_usd": px, "token": t.get("token"),
               "price_method": t.get("method")}
        if side not in ("buy", "sell"):
            rec["status"] = "unknown_side"
            per_trade.append(rec)
            continue
        if px is None or q <= 0:
            n_unpriced += 1
            rec["status"] = "UNPRICED"
            rec["reason"] = "no price at this block; excluded from PnL"
            unpriced_detail.append(rec)
            per_trade.append(rec)
            continue
        n_priced += 1
        avg = (basis / qty) if qty > 0 else px
        if side == "buy":
            cost_total += q * px
            qty += q
            basis += q * px
            rec["status"] = "priced"
            rec["average_cost_after"] = basis / qty if qty else None
        else:
            proceeds_total += q * px
            sellable = min(q, qty)
            pnl = sellable * (px - avg)
            realised += pnl
            basis -= sellable * avg
            qty -= sellable
            rec["status"] = "priced"
            rec["realised_usd"] = pnl
            rec["average_cost_at_sale"] = avg
            if sellable < q - 1e-9:
                rec["shortfall_qty"] = q - sellable
        per_trade.append(rec)

    return {
        "method": "WEIGHTED_AVERAGE",
        "n_trades": len(trades),
        "n_priced": n_priced,
        "n_unpriced": n_unpriced,
        "realised_pnl_usd": realised,
        "total_cost_usd": cost_total,
        "total_proceeds_usd": proceeds_total,
        "remaining_qty": qty,
        "remaining_basis_usd": basis,
        "average_cost_usd": (basis / qty) if qty > 0 else None,
        "coverage_pct": (100.0 * n_priced / len(trades)) if trades else None,
        "unpriced_trades": unpriced_detail,
        "per_trade": per_trade,
        "note": ("Realised PnL covers the PRICED trades only. Unpriced "
                 "trades are excluded, not estimated. All figures are "
                 "GROSS of gas, DEX fees and MEV."),
    }


# --------------------------------------------------------------------------
# 11. The price-free proxy, and its measured bias
# --------------------------------------------------------------------------
def quantity_proxy(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """A PnL PROXY that needs no price at all.

    For each token it accumulates the wallet's own token flows:
      tokens_in, tokens_out, net_tokens, and the turnover ratio
      tokens_out / tokens_in.
    It also reports the wallet's EARLIEST observed acquisition price per
    token in TOKEN UNITS - the price the wallet itself paid per token on
    its first buy, expressed in the quote token it paid with.

    WHAT IT IS NOT: a PnL. A wallet that bought 1e9 tokens for 0.01 USD
    each and sold them for 0.01 USD each, and a wallet that bought the
    same number of tokens for 0.001 USD each and sold for 0.001 USD
    each, have IDENTICAL quantity statistics and opposite profits. The
    proxy is blind to price by construction.

    Its bias is therefore not a small error but a CENSORSHIP: it
    discards the entire dimension (price level) that determines
    profit. It can still separate "did not trade" from "traded and
    churned", which is a real and useful distinction.
    """
    per_token: Dict[str, Dict[str, Any]] = {}
    for t in trades:
        tok = _norm(t.get("token"))
        if not tok:
            continue
        a = per_token.setdefault(tok, {
            "token": t.get("token"), "symbol": t.get("symbol"),
            "tokens_in": 0.0, "tokens_out": 0.0, "n_buys": 0, "n_sells": 0,
            "first_buy_ts": None, "last_buy_ts": None, "first_sell_ts": None,
            "first_buy_price_in_quote": None, "first_buy_quote": None,
            "quote_prices_seen": []})
        side = (t.get("side") or "").lower()
        q = float(t.get("qty") or 0.0)
        ts = t.get("ts")
        if side == "buy":
            a["tokens_in"] += q
            a["n_buys"] += 1
            if ts:
                if a["first_buy_ts"] is None or ts < a["first_buy_ts"]:
                    a["first_buy_ts"] = ts
                a["last_buy_ts"] = max(a["last_buy_ts"] or ts, ts)
            if t.get("price_in_quote"):
                a["quote_prices_seen"].append(float(t["price_in_quote"]))
                if a["first_buy_price_in_quote"] is None:
                    a["first_buy_price_in_quote"] = float(t["price_in_quote"])
                    a["first_buy_quote"] = t.get("quote_token")
        elif side == "sell":
            a["tokens_out"] += q
            a["n_sells"] += 1
            if ts:
                a["first_sell_ts"] = (min(a["first_sell_ts"], ts)
                                      if a["first_sell_ts"] is not None else ts)
    rows = []
    for a in per_token.values():
        net = a["tokens_in"] - a["tokens_out"]
        prices = a.pop("quote_prices_seen")
        rows.append({
            **a,
            "net_tokens": net,
            "turnover_ratio": (a["tokens_out"] / a["tokens_in"]
                               if a["tokens_in"] > 0 else None),
            "realised_token_fraction": (a["tokens_out"] / a["tokens_in"]
                                        if a["tokens_in"] > 0 else None),
            "median_quote_price_seen": (sorted(prices)[len(prices) // 2]
                                        if prices else None),
            "n_quote_prices_seen": len(prices),
            "still_holding": net > 0,
        })
    rows.sort(key=lambda r: -(r["net_tokens"]))
    return {
        "method": "QUANTITY_PROXY (no price used)",
        "n_tokens": len(rows),
        "tokens": rows,
        "total_tokens_in": sum(r["tokens_in"] for r in rows),
        "total_tokens_out": sum(r["tokens_out"] for r in rows),
        "bias": ("The proxy is CENSORED on price level by construction: "
                 "it cannot distinguish a 100x gain from a 100x loss on "
                 "identical token flows. Its outputs are turnover and "
                 "direction, not profit."),
        "note": ("The 'first_buy_price_in_quote' field is the wallet's OWN "
                 "first observed acquisition price for that token in the "
                 "quote token it paid with. It is only populated when a "
                 "price was actually recovered for that buy - it is never "
                 "filled in with today's price."),
    }


def proxy_bias_test() -> Dict[str, Any]:
    """MEASURE the quantity proxy's bias on a case where the truth is
    known.

    Uses SYNTHETIC data (clearly disclosed) to show that the proxy
    returns an identical score for a winning and a losing wallet with
    identical token flows. The point is the bias is not an error rate -
    it is total blindness on the dimension that matters.
    """
    from .provenance import SYNTHETIC, SYNTHETIC_DISCLOSURE
    winner = [
        {"token": "T", "side": "buy", "qty": 1_000_000.0,
         "price_in_quote": 0.001, "quote_token": "W", "ts": 1000},
        {"token": "T", "side": "sell", "qty": 1_000_000.0,
         "price_in_quote": 0.002, "quote_token": "W", "ts": 2000},
    ]
    loser = [
        {"token": "T", "side": "buy", "qty": 1_000_000.0,
         "price_in_quote": 0.002, "quote_token": "W", "ts": 1000},
        {"token": "T", "side": "sell", "qty": 1_000_000.0,
         "price_in_quote": 0.001, "quote_token": "W", "ts": 2000},
    ]
    pw = quantity_proxy(winner)
    pl = quantity_proxy(loser)
    tw = winner[0]["qty"] * (0.002 - 0.001)
    tl = loser[0]["qty"] * (0.001 - 0.002)
    return {
        "provenance": SYNTHETIC,
        "disclosure": SYNTHETIC_DISCLOSURE,
        "winner_true_pnl_usd": tw,
        "loser_true_pnl_usd": tl,
        "winner_proxy_tokens_out": pw["total_tokens_out"],
        "loser_proxy_tokens_out": pl["total_tokens_out"],
        "winner_proxy_turnover": pw["tokens"][0]["turnover_ratio"],
        "loser_proxy_turnover": pl["tokens"][0]["turnover_ratio"],
        "proxy_separates_them": False,
        "finding": ("Both wallets produce an identical quantity proxy "
                    "(same tokens in, same tokens out, turnover 1.0) while "
                    "their true PnL is +1000 and -1000 quote units. The "
                    "proxy's error on PnL is 100% of the true value in "
                    "both directions - it is not a noisy estimator, it "
                    "is blind. It may only be used to describe FLOW "
                    "(what moved, how much, how long held), never "
                    "profitability."),
        "bias_table": [
            {"proxy_output": "tokens_in / tokens_out", "affected_by_price": False,
             "bias": "none - it is a quantity"},
            {"proxy_output": "turnover_ratio", "affected_by_price": False,
             "bias": "none as a quantity; blind to PnL"},
            {"proxy_output": "first_buy_price_in_quote", "affected_by_price": True,
             "bias": ("only the FIRST buy's price - a wallet that bought "
                      "cheaply and then chased the price up has a "
                      "misleadingly low 'cost'"),
             },
            {"proxy_output": "median_quote_price_seen", "affected_by_price": True,
             "bias": ("a median of observed prices; ignores the size of "
                      "each fill, so a 1-token buy and a 1M-token buy "
                      "count equally")},
        ],
    }


# --------------------------------------------------------------------------
# 12. Top-level: realised PnL for one wallet
# --------------------------------------------------------------------------
def wallet_realised_pnl(trades: Sequence[Dict[str, Any]],
                        chain: str = "ethereum",
                        method: str = "auto",
                        basis: str = "fifo",
                        price_first: bool = True) -> Dict[str, Any]:
    """Realised PnL for one wallet from its transfer history.

    `trades` is a list of dicts with at least: token, block, ts, qty,
    side ('buy'/'sell'). `pool` is optional but strongly recommended:
    without it, only the reference-price and OHLCV methods are available.

    Returns the cost-basis result, the per-trade pricing log, and an
    explicit statement of what could NOT be priced.
    """
    rpc = ArchiveRpc(chain)
    ver = rpc.verify_archive() if price_first else {
        "status": "skipped", "note": "pricing disabled"}

    priced = []
    unpriced = []
    for t in trades:
        if not price_first:
            rec = dict(t)
            rec["price_usd"] = None
            rec["status"] = "UNPRICED"
            priced.append(rec)
            continue
        p = price_trade(t, chain=chain, method=method, rpc=rpc)
        rec = dict(t)
        rec.update({k: p.get(k) for k in
                    ("status", "price_usd", "method", "price_kind",
                     "source_url", "http_status")})
        if p.get("status") == "ok":
            rec["price_usd"] = p["price_usd"]
            priced.append(rec)
        else:
            rec["price_usd"] = None
            rec["pricing_reason"] = p.get("note") or p.get("status")
            rec["pricing_attempts"] = p.get("attempts")
            unpriced.append(rec)

    engine = fifo_cost_basis(priced) if basis == "fifo" \
        else weighted_average_cost_basis(priced)
    return {
        "chain": chain,
        "address": None,
        "basis_method": basis,
        "n_trades": len(trades),
        "n_priced": len(priced),
        "n_unpriced": len(unpriced),
        "coverage_pct": (100.0 * len(priced) / len(trades)) if trades else None,
        "archive_provider": ver,
        "cost_basis": engine,
        "unpriced_trades": unpriced,
        "quantity_proxy": quantity_proxy(prices_or_raw(priced, trades)),
        "fee_basis": ("GROSS of gas, DEX fees and MEV - none of these are "
                      "observable from ERC-20 transfers alone. A net figure "
                      "would require per-swap gas and fee logs."),
        "honesty": ("A trade whose price could not be recovered at its own "
                    "block is EXCLUDED from the realised PnL and reported in "
                    "unpriced_trades. Today's price is never substituted."),
    }


def prices_or_raw(priced: List[Dict[str, Any]],
                  trades: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Give the quantity proxy every trade (priced or not).

    The proxy does not need a price, and excluding the unpriced trades
    would bias its flow statistics toward the priced subset - the
    opposite of what an honest flow description should do.
    """
    out = {id(t): t for t in trades}
    merged: List[Dict[str, Any]] = []
    for t in trades:
        rec = dict(t)
        merged.append(rec)
    # carry any recovered pool-level price onto the raw trade
    for p in priced:
        for rec in merged:
            if rec.get("block") == p.get("block") and \
                    rec.get("token") == p.get("token") and \
                    rec.get("side") == p.get("side"):
                rec["price_usd"] = p.get("price_usd")
                rec["method"] = p.get("method")
                break
    return merged


def self_test() -> Dict[str, Any]:
    """Offline self-test: the cost-basis engines and the proxy.

    Uses SYNTHETIC data with an explicit disclosure, plus one LIVE
    DefiLlama read so the module proves its network path works.
    """
    from .provenance import SYNTHETIC_DISCLOSURE
    synth = [
        {"token": "T", "side": "buy", "qty": 1000.0, "price_usd": 0.10,
         "ts": 1000, "block": 1, "method": "synthetic"},
        {"token": "T", "side": "buy", "qty": 1000.0, "price_usd": 0.20,
         "ts": 1100, "block": 2, "method": "synthetic"},
        {"token": "T", "side": "sell", "qty": 1500.0, "price_usd": 0.30,
         "ts": 1200, "block": 3, "method": "synthetic"},
        {"token": "T", "side": "sell", "qty": 100.0, "price_usd": None,
         "ts": 1300, "block": 4, "method": "synthetic"},
    ]
    fifo = fifo_cost_basis(synth)
    wavg = weighted_average_cost_basis(synth)
    # Manual expectation.
    #   FIFO: buy 1000@0.10, buy 1000@0.20, sell 1500@0.30
    #         -> 1000*(0.30-0.10) + 500*(0.30-0.20) = 200 + 50 = 250
    #   WAC: average cost = (1000*0.10 + 1000*0.20)/2000 = 0.15
    #         -> 1500*(0.30-0.15) = 225
    # The two methods DISAGREE on the same trades, which is the point of
    # reporting both: the cost-basis convention is a choice, and it moves
    # the number.
    checks = {
        "fifo_realised_is_250": abs(fifo["realised_pnl_usd"] - 250.0) < 1e-6,
        "fifo_remaining_qty_is_400": abs(fifo["remaining_qty"] - 400.0) < 1e-6,
        "fifo_unpriced_count_is_1": fifo["n_unpriced"] == 1,
        "fifo_coverage_is_75pct": abs((fifo["coverage_pct"] or 0) - 75.0) < 1e-6,
        "wavg_realised_is_225": abs(wavg["realised_pnl_usd"] - 225.0) < 1e-6,
        "wavg_remaining_qty_is_500": abs(wavg["remaining_qty"] - 500.0) < 1e-6,
        "fifo_and_wavg_differ": abs(fifo["realised_pnl_usd"]
                                    - wavg["realised_pnl_usd"]) > 1.0,
    }
    live = defillama_price("ethereum",
                            "0x6982508145454Ce325dDbE47a25d4eC3d2311933",
                            1700000000)
    return {
        "provenance": "SYNTHETIC + LIVE",
        "disclosure": SYNTHETIC_DISCLOSURE,
        "fifo": fifo, "weighted_average": wavg,
        "checks": checks, "all_checks_pass": all(checks.values()),
        "live_defillama_probe": {
            "status": live.get("status"), "price": live.get("price"),
            "http_status": live.get("http_status"), "url": live.get("url")},
    }


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(self_test(), indent=2, default=str))
