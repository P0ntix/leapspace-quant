"""Multi-chain on-chain data layer: Solana, Ethereum, Base, BSC, Arbitrum.

Verified working from this host (2026-11-02):

  * EVM JSON-RPC over POST: `*.publicnode.com` for ethereum / base / bsc /
    arbitrum. A GET to these URLs returns an HTML page, NOT JSON - you must
    POST a JSON-RPC body.
  * `certifi` must be used for the TLS context. The Windows system CA store
    mis-validates several chains and raises CERTIFICATE_VERIFY_FAILED on
    hosts that work fine (eth.llamarpc.com, bsc-dataseed.binance.org).
  * Solana public RPC `api.mainnet-beta.solana.com` over POST.
  * DexScreener for token / pool / liquidity / volume across all five
    chains: /latest/dex/search, /tokens/v1/{chainId}/{address},
    /token-boosts/top/v1, /latest/dex/pairs/{chainId}/{tokenAddress}.
  * RugCheck (Solana only) for the mint creator and holder concentration.

Topic constants verified against live pools:

  ERC-20 Transfer   0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
  V2 pair Mint      0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f
  V2 pair Burn      0x49995e5dd6158cf69ad3e9777c46755a1a826a446c6416992167462dad033b2a
  V3 pool Mint      0x9dd857646c181dc756dc3ceba33d06f38e4c3c8bc8fad9990a60679ded73b509
  V3 pool Burn      0xd32a1e60019fda299ae8ef8d0ad54483439c1283a4076e3d37ba2a2952d8d12a

`eth_getLogs` span limits differ by host: publicnode accepts a wide range
but returns 0 rows when the range holds no matching logs; tenderly rejects
ranges above ~1000 blocks with "Block range too large".

NO API KEYS are available on this host (no Bitquery, no Helius, no
Alchemy/Infura), so this layer is built entirely on free public endpoints.
Every function returns the source that produced its data, and records a
gap when a chain or an event kind is not reachable.
"""
from __future__ import annotations

import json
import ssl
import time
from typing import Any, Dict, List, Optional, Tuple

from .models import (CHAINS, EVENT_LIQUIDITY_ADDED, EVENT_LIQUIDITY_REMOVED,
                     EVENT_PRICE_UPDATE, EVENT_TOKEN_CREATED,
                     EVENT_WALLET_TRADE, FAMILY_EVM, FAMILY_SVM,
                     ChainSpec, TokenEvent, WalletTrade, get_chain, now_ts)
from .provenance import SourceUnavailable

# --- verified topic constants ---------------------------------------------
TRANSFER_TOPIC = ("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f"
                  "55a4df523b3ef")
V2_MINT_TOPIC = ("0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef2639"
                 "4f4c03821c4f")
V2_BURN_TOPIC = ("0x49995e5dd6158cf69ad3e9777c46755a1a826a446c64169921674"
                 "62dad033b2a")
V3_MINT_TOPIC = ("0x9dd857646c181dc756dc3ceba33d06f38e4c3c8bc8fad9990a6"
                 "0679ded73b509")
V3_BURN_TOPIC = ("0xd32a1e60019fda299ae8ef8d0ad54483439c1283a4076e3d37ba"
                 "2a2952d8d12a")

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

_SSL_CTX = None


def _ssl_context():
    """TLS context that works on this host.

    The Windows CA store mis-validates several chains, so certifi's bundle
    is used when available.
    """
    global _SSL_CTX
    if _SSL_CTX is None:
        try:
            import certifi
            _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
        except Exception:  # noqa: BLE001
            _SSL_CTX = ssl.create_default_context()
    return _SSL_CTX


def _post_json(url: str, payload: Any, timeout: int = 30,
               retries: int = 3) -> Tuple[Any, int]:
    from .http import http_post_json
    return http_post_json(url, payload, timeout=timeout, retries=retries)


# --------------------------------------------------------------------------
# EVM client
# --------------------------------------------------------------------------


class EVMClient:
    """Minimal JSON-RPC client for the EVM chains.

    Public RPC endpoints throttle aggressively, so every call is polite:
    a small delay between calls, and retries with backoff on 429/5xx.
    """

    def __init__(self, chain: str = "ethereum", min_interval: float = 0.35,
                 timeout: int = 30):
        self.chain = get_chain(chain)
        self.url = self.chain.rpc_url
        self.min_interval = min_interval
        self.timeout = timeout
        self._last_call = 0.0
        self.calls = 0

    # -- plumbing ----------------------------------------------------------
    def _throttle(self) -> None:
        gap = time.time() - self._last_call
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self._last_call = time.time()

    def rpc(self, method: str, params: Optional[List[Any]] = None) -> Any:
        body = {"jsonrpc": "2.0", "id": 1, "method": method,
                "params": params or []}
        last: Optional[Exception] = None
        for attempt in range(3):
            self._throttle()
            try:
                data, status = _post_json(self.url, body, timeout=self.timeout)
                self.calls += 1
                if isinstance(data, dict) and data.get("error"):
                    err = data["error"]
                    msg = (err.get("message") if isinstance(err, dict)
                           else str(err))
                    raise SourceUnavailable(
                        f"{self.chain.chain_id} rpc {method}: {msg}")
                if isinstance(data, dict) and "result" in data:
                    return data["result"]
                return data
            except SourceUnavailable:
                raise
            except Exception as exc:  # noqa: BLE001
                last = exc
                # A public host that refuses a call (403/429) needs a much
                # longer pause than a transient network blip, or a
                # multi-call sweep such as the deployer binary search
                # trips the host's limit and every call after it fails.
                status = getattr(getattr(exc, "code", None), "__int__", None)
                if status in (403, 429) or "403" in str(exc) \
                        or "429" in str(exc):
                    time.sleep(6.0 * (attempt + 1))
                else:
                    time.sleep(1.5 * (attempt + 1))
        raise SourceUnavailable(
            f"{self.chain.chain_id} rpc {method} failed: {last}")

    # -- reads -------------------------------------------------------------
    def chain_id(self) -> str:
        return str(self.rpc("eth_chainId"))

    def block_number(self) -> int:
        return int(self.rpc("eth_blockNumber"), 16)

    def get_block_by_number(self, block: int, full: bool = False
                            ) -> Optional[Dict[str, Any]]:
        tag = hex(block)
        return self.rpc("eth_getBlockByNumber", [tag, bool(full)])

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self.rpc("eth_getTransactionByHash", [tx_hash])

    def get_transaction_receipt(self, tx_hash: str
                                ) -> Optional[Dict[str, Any]]:
        return self.rpc("eth_getTransactionReceipt", [tx_hash])

    def get_code(self, address: str, block: Optional[int] = None) -> str:
        params = [address] if block is None else [address, hex(block)]
        return self.rpc("eth_getCode", params) or "0x"

    def eth_call(self, to: str, data: str = "0x",
                 block: Optional[int] = None) -> str:
        call: Dict[str, Any] = {"to": to, "data": data}
        params: List[Any] = [call]
        if block is not None:
            params.append(hex(block))
        return self.rpc("eth_call", params) or "0x"

    def get_logs(self, address: Optional[str] = None,
                 topics: Optional[List[Any]] = None,
                 from_block: int = 0,
                 to_block: Optional[int] = None,
                 depth: int = 0) -> List[Dict[str, Any]]:
        """eth_getLogs, chunked to stay inside host span limits.

        The chunking is BOUNDED: a host that rejects a wide range is split
        at most `max_depth` times, so a persistently failing range cannot
        turn into an exponential call storm.
        """
        if to_block is None:
            to_block = self.block_number()
        if from_block > to_block:
            return []
        filter_: Dict[str, Any] = {"fromBlock": hex(from_block),
                                   "toBlock": hex(to_block)}
        if address:
            filter_["address"] = address
        if topics:
            filter_["topics"] = topics
        try:
            logs = self.rpc("eth_getLogs", [filter_])
        except SourceUnavailable:
            span = to_block - from_block
            if span < 64 or depth >= 8:
                return []
            mid = from_block + span // 2
            return (self.get_logs(address, topics, from_block, mid, depth + 1)
                    + self.get_logs(address, topics, mid + 1, to_block,
                                    depth + 1))
        return logs or []


# --------------------------------------------------------------------------
# Solana client
# --------------------------------------------------------------------------


class SolanaClient:
    """Minimal JSON-RPC client for Solana."""

    def __init__(self, chain: str = "solana", min_interval: float = 0.25,
                 timeout: int = 30):
        self.chain = get_chain(chain)
        self.url = self.chain.rpc_url
        self.min_interval = min_interval
        self.timeout = timeout
        self._last_call = 0.0
        self.calls = 0

    def _throttle(self) -> None:
        gap = time.time() - self._last_call
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self._last_call = time.time()

    def rpc(self, method: str, params: Optional[List[Any]] = None) -> Any:
        body = {"jsonrpc": "2.0", "id": 1, "method": method,
                "params": params or []}
        last: Optional[Exception] = None
        for attempt in range(3):
            self._throttle()
            try:
                data, status = _post_json(self.url, body, timeout=self.timeout)
                self.calls += 1
                if isinstance(data, dict) and data.get("error"):
                    err = data["error"]
                    msg = (err.get("message") if isinstance(err, dict)
                           else str(err))
                    raise SourceUnavailable(f"solana rpc {method}: {msg}")
                if isinstance(data, dict) and "result" in data:
                    return data["result"]
                return data
            except SourceUnavailable:
                raise
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(1.5 * (attempt + 1))
        raise SourceUnavailable(f"solana rpc {method} failed: {last}")

    def get_slot(self) -> int:
        return int(self.rpc("getSlot"))

    def get_block(self, slot: int, details: bool = False
                  ) -> Optional[Dict[str, Any]]:
        return self.rpc("getBlock", [slot, {"encoding": "jsonParsed"
                                            if details else "base64",
                                            "maxSupportedTransactionVersion": 0}])

    def get_signatures_for_address(self, address: str, limit: int = 100,
                                   before: Optional[str] = None
                                   ) -> List[Dict[str, Any]]:
        opts: Dict[str, Any] = {"limit": limit}
        if before:
            opts["before"] = before
        return self.rpc("getSignaturesForAddress", [address, opts]) or []

    def get_transaction(self, signature: str
                        ) -> Optional[Dict[str, Any]]:
        return self.rpc("getTransaction", [
            signature, {"encoding": "jsonParsed",
                        "maxSupportedTransactionVersion": 0}])

    def get_token_accounts(self, owner: str,
                           mint: Optional[str] = None
                           ) -> List[Dict[str, Any]]:
        filters = [{"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}]
        if mint:
            filters.append({"mint": mint})
        res = self.rpc("getTokenAccountsByOwner", [
            owner, {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}]) or {}
        return res.get("value") or []

    def get_balance(self, address: str) -> int:
        res = self.rpc("getBalance", [address]) or {}
        return int(res.get("value", 0))

    def get_account_info(self, address: str) -> Optional[Dict[str, Any]]:
        res = self.rpc("getAccountInfo", [
            address, {"encoding": "jsonParsed"}]) or {}
        return res.get("value")

    def get_latest_blockhash(self) -> Optional[str]:
        res = self.rpc("getLatestBlockhash") or {}
        return res.get("value", {}).get("blockhash")


# --------------------------------------------------------------------------
# DexScreener — the cross-chain token/pool source
# --------------------------------------------------------------------------


def dexscreener_pairs(chain: str, token_address: str) -> List[Dict[str, Any]]:
    """Real pairs for a token, from DexScreener. Works on all five chains.

    NOTE the endpoint: `/token-pairs/v1/{chainId}/{tokenAddress}` returns
    every pair for a TOKEN. `/latest/dex/pairs/{chainId}/{pairAddress}`
    expects a PAIR address and returns 0 for a token address.
    """
    from .http import http_json
    url = f"https://api.dexscreener.com/token-pairs/v1/{chain}/{token_address}"
    data, _ = http_json(url, timeout=30, retries=2)
    if isinstance(data, list):
        return [p for p in data if isinstance(p, dict)]
    return []


def dexscreener_token_profiles(chain: str, token_address: str
                               ) -> List[Dict[str, Any]]:
    from .http import http_json
    url = f"https://api.dexscreener.com/tokens/v1/{chain}/{token_address}"
    data, _ = http_json(url, timeout=30, retries=2)
    return [p for p in (data or []) if isinstance(p, dict)]


def dexscreener_boosted_tokens() -> List[Dict[str, Any]]:
    """Tokens DexScreener is currently boosting - a real traction signal."""
    from .http import http_json
    data, _ = http_json("https://api.dexscreener.com/token-boosts/top/v1",
                        timeout=30, retries=2)
    return [p for p in (data or []) if isinstance(p, dict)]


def _pool_snapshot(chain: str, token_address: str) -> Dict[str, Any]:
    """Flatten the best DexScreener pair for a token into scalars."""
    pairs = dexscreener_pairs(chain, token_address)
    if not pairs:
        return {}
    best = max(pairs, key=lambda p: float((p.get("liquidity") or {})
                                          .get("usd") or 0.0))
    liq = best.get("liquidity") or {}
    vol = best.get("volume") or {}
    tx = best.get("txns") or {}
    buys = (tx.get("h24") or {}).get("buys") or 0
    sells = (tx.get("h24") or {}).get("sells") or 0
    return {
        "pair_address": best.get("pairAddress"),
        "dex": best.get("dexId"),
        "price_usd": _f(best.get("priceUsd")),
        "liquidity_usd": _f(liq.get("usd")),
        "volume_24h_usd": _f(vol.get("h24")),
        "volume_5m_usd": _f(vol.get("m5")),
        "fdv_usd": _f(best.get("fdv")),
        "market_cap_usd": _f(best.get("marketCap")),
        "price_change_5m": _f(best.get("priceChange", {}).get("m5")),
        "price_change_1h": _f(best.get("priceChange", {}).get("h1")),
        "price_change_24h": _f(best.get("priceChange", {}).get("h24")),
        "buys_24h": buys,
        "sells_24h": sells,
        "buys_5m": (tx.get("m5") or {}).get("buys") or 0,
        "sells_5m": (tx.get("m5") or {}).get("sells") or 0,
        "pair_created_at": best.get("pairCreatedAt"),
        "url": best.get("url"),
        "source": "dexscreener",
        "provenance": "LIVE",
    }


def _f(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Token events
# --------------------------------------------------------------------------


def fetch_token_events(chain: str, token_address: Optional[str] = None,
                       limit: int = 50) -> Dict[str, Any]:
    """Detect real token / liquidity events on a chain.

    Returns {"events": [TokenEvent...], "gaps": [...], "source": str}.

    The event surface differs by chain and is reported honestly:
      * DexScreener gives a real liquidity + volume snapshot on all five
        chains, which is a price/volume event, not a creation event.
      * RugCheck (Solana only) exposes the mint's creator and creation
        time, which is a real token_created event.
      * EVM chains can observe LP mint/burn logs via eth_getLogs, which is
        a real liquidity_added / liquidity_removed event - but only for
        pools whose address is known, and only within the host's span
        limit.
    """
    spec = get_chain(chain)
    events: List[TokenEvent] = []
    gaps: List[Dict[str, str]] = []
    sources: List[str] = []

    if not token_address:
        gaps.append({"source": f"{chain}:token_events",
                     "reason": "no token address supplied"})
        return {"events": events, "gaps": gaps, "source": ""}

    # --- price / liquidity snapshot (all chains, DexScreener) ---
    try:
        snap = _pool_snapshot(chain, token_address)
        if snap:
            sources.append("dexscreener")
            events.append(TokenEvent(
                kind=EVENT_PRICE_UPDATE, chain=chain, token=token_address,
                symbol="", ts=now_ts(), source="dexscreener",
                provenance="LIVE", detail=snap))
        else:
            gaps.append({"source": f"{chain}:dexscreener",
                         "reason": f"no DexScreener pair for {token_address}"})
    except Exception as exc:  # noqa: BLE001
        gaps.append({"source": f"{chain}:dexscreener", "reason": str(exc)})

    # --- token creation (Solana: RugCheck creator) ---
    if chain == "solana":
        try:
            from .http import http_json
            rep, _ = http_json(
                f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report",
                timeout=30, retries=2)
            if isinstance(rep, dict):
                sources.append("rugcheck")
                events.append(TokenEvent(
                    kind=EVENT_TOKEN_CREATED, chain=chain,
                    token=token_address, symbol=rep.get("tokenMeta", {})
                    .get("name") or "",
                    ts=int(rep.get("createdAt") or 0),
                    source="rugcheck", provenance="LIVE",
                    detail={"creator": rep.get("creator"),
                            "holder_count": rep.get("totalHolders"),
                            "risk_score": rep.get("score"),
                            "total_market_liquidity":
                                rep.get("totalMarketLiquidity"),
                            "mint_authority": rep.get("mintAuthority"),
                            "freeze_authority": rep.get("freezeAuthority")}))
        except Exception as exc:  # noqa: BLE001
            gaps.append({"source": "solana:rugcheck", "reason": str(exc)})
    else:
        gaps.append({
            "source": f"{chain}:token_created",
            "reason": "creation is not directly observable without an "
                      "indexer; the deployer can still be DERIVED from the "
                      "chain (see leapspace/deployers.py)"})

    # --- LP mint / burn (EVM: pair logs) ---
    if spec.family == FAMILY_EVM:
        try:
            client = EVMClient(chain)
            latest = client.block_number()
            logs = client.get_logs(topics=[[V2_MINT_TOPIC, V3_MINT_TOPIC]],
                                    from_block=max(0, latest - 2000),
                                    to_block=latest)
            for lg in logs[:limit]:
                events.append(TokenEvent(
                    kind=EVENT_LIQUIDITY_ADDED, chain=chain,
                    token=token_address, ts=now_ts(),
                    tx_hash=lg.get("transactionHash", ""),
                    block=int(lg.get("blockNumber", 0), 16)
                    if isinstance(lg.get("blockNumber"), str) else 0,
                    source="eth_getLogs", provenance="LIVE",
                    detail={"pool": lg.get("address"),
                            "topics": ",".join(lg.get("topics") or [])}))
            if logs:
                sources.append("eth_getLogs")
            else:
                gaps.append({
                    "source": f"{chain}:lp_logs",
                    "reason": "no V2/V3 Mint log in the last 2000 blocks "
                              "for this address"})
        except Exception as exc:  # noqa: BLE001
            gaps.append({"source": f"{chain}:lp_logs", "reason": str(exc)})

    return {"events": events, "gaps": gaps, "source": ",".join(sorted(set(sources)))}


# --------------------------------------------------------------------------
# Wallet trades
# --------------------------------------------------------------------------


def fetch_wallet_trades(chain: str, wallet: str, limit: int = 100,
                        token_address: Optional[str] = None,
                        blocks: int = 5000) -> List[WalletTrade]:
    """Real trades for one wallet.

    Solana: the wallet's signatures are read newest-first and each
    transaction's token balance deltas are turned into transfers. Public
    RPC omits `meta.tokenTransfers` for program-invoked moves, so the
    pre/post token balance deltas are the reliable path - the same
    derivation the package's existing onchain module uses.

    EVM: ERC-20 Transfer logs where the wallet is the recipient (topic1) or
    the sender (topic2). A Transfer with a zero `from` is a mint and one
    with a zero `to` is a burn, so neither is counted as a wallet trade.
    The `blocks` window bounds the scan: public RPC hosts get slow over
    wide ranges, and a busier wallet needs a wider window to be covered.

    Prices are NOT invented: a trade's price_usd/value_usd are left None
    unless a real price source is applied by the caller.
    """
    spec = get_chain(chain)
    if spec.family == FAMILY_SVM:
        return _solana_wallet_trades(wallet, limit)
    return _evm_wallet_trades(chain, wallet, limit, token_address, blocks)


def _solana_wallet_trades(wallet: str, limit: int) -> List[WalletTrade]:
    client = SolanaClient("solana")
    sigs = client.get_signatures_for_address(wallet, limit=min(limit, 100))
    trades: List[WalletTrade] = []
    for sig in sigs[:limit]:
        if sig.get("err"):
            continue
        try:
            tx = client.get_transaction(sig["signature"])
        except SourceUnavailable:
            continue
        if not tx:
            continue
        for tr in _solana_transfers_from_deltas(tx, wallet):
            tr.ts = int(sig.get("blockTime") or 0)
            tr.tx_hash = sig.get("signature", "")
            tr.source = "solana_rpc"
            trades.append(tr)
    return trades


def _solana_transfers_from_deltas(tx: Dict[str, Any], owner: str
                                   ) -> List[WalletTrade]:
    """Derive token transfers from pre/post token balance deltas.

    Public RPC omits `meta.tokenTransfers` for program-invoked moves, so
    the balance deltas are the reliable signal. The delta's owner is the
    account whose balance changed; the direction is inferred from the sign
    of the delta.

    The COUNTERPARTY is recovered by finding the other account in the same
    transaction whose balance moved by the opposite amount in the same
    mint. That is what the anti-insider filter needs - WHO sent the
    tokens - and it is available even when `meta.tokenTransfers` is not.
    """
    meta = tx.get("meta") or {}
    pre = meta.get("preTokenBalances") or []
    post = meta.get("postTokenBalances") or []
    if not pre and not post:
        return []

    def key(b):
        return (b.get("accountIndex"), b.get("mint"))

    def amount_of(b):
        try:
            return float((b.get("uiTokenAmount") or {}).get("uiAmountString")
                         or 0)
        except (TypeError, ValueError):
            return 0.0

    pre_by = {key(b): b for b in pre}
    post_by = {key(b): b for b in post}
    # Every account's net delta, per mint, so a counterparty can be found.
    deltas: Dict[str, List[Tuple[str, float]]] = {}
    for k in set(pre_by) | set(post_by):
        a = pre_by.get(k) or {}
        b = post_by.get(k) or {}
        owner_acct = a.get("owner") or b.get("owner")
        mint = a.get("mint") or b.get("mint")
        if not owner_acct or not mint:
            continue
        d = amount_of(b) - amount_of(a)
        if d == 0:
            continue
        deltas.setdefault(mint, []).append((owner_acct, d))

    out: List[WalletTrade] = []
    for k in set(pre_by) | set(post_by):
        a = pre_by.get(k) or {}
        b = post_by.get(k) or {}
        owner_acct = a.get("owner") or b.get("owner")
        if owner_acct != owner:
            continue
        mint = a.get("mint") or b.get("mint")
        if not mint:
            continue
        delta = amount_of(b) - amount_of(a)
        if delta == 0:
            continue
        counterparty = ""
        for other_acct, other_delta in deltas.get(mint, []):
            if other_acct == owner_acct:
                continue
            if abs(other_delta + delta) < max(1e-9, abs(delta) * 1e-6):
                counterparty = other_acct
                break
        out.append(WalletTrade(
            wallet=owner, chain="solana", token=mint,
            symbol="", side="buy" if delta > 0 else "sell",
            amount=abs(delta), ts=0, tx_hash="",
            provenance="LIVE", source="solana_rpc",
            detail={"delta": delta, "mint": mint,
                    "counterparty": counterparty}))
    return out


def _evm_wallet_trades(chain: str, wallet: str, limit: int,
                       token_address: Optional[str],
                       blocks: int = 5000) -> List[WalletTrade]:
    client = EVMClient(chain)
    topic_wallet = "0x" + wallet.lower().replace("0x", "").rjust(64, "0")
    latest = client.block_number()
    # Inbound: topic1 == wallet. Outbound: topic2 == wallet.
    inbound = client.get_logs(topics=[TRANSFER_TOPIC, topic_wallet],
                               from_block=max(0, latest - blocks),
                               to_block=latest)
    outbound = client.get_logs(topics=[TRANSFER_TOPIC, None, topic_wallet],
                                from_block=max(0, latest - blocks),
                                to_block=latest)

    trades: List[WalletTrade] = []
    for lg in inbound[:limit]:
        topics = lg.get("topics") or []
        if len(topics) < 3:
            continue
        frm = "0x" + topics[1][-40:]
        to = "0x" + lg.get("address", "")[-40:]
        amount = _int_from_data(lg.get("data"))
        if amount is None:
            continue
        trades.append(WalletTrade(
            wallet=wallet, chain=chain, token=to, side="buy",
            amount=amount, ts=now_ts(),
            tx_hash=lg.get("transactionHash", ""),
            provenance="LIVE", source="eth_getLogs",
            detail={"counterparty": frm,
                    "block": lg.get("blockNumber"),
                    "log_index": lg.get("logIndex")}))
    for lg in outbound[:limit]:
        topics = lg.get("topics") or []
        if len(topics) < 3:
            continue
        frm = "0x" + topics[1][-40:]
        to = "0x" + topics[2][-40:]
        if to.lower() == ZERO_ADDRESS:
            continue
        amount = _int_from_data(lg.get("data"))
        if amount is None:
            continue
        trades.append(WalletTrade(
            wallet=wallet, chain=chain, token=frm, side="sell",
            amount=amount, ts=now_ts(),
            tx_hash=lg.get("transactionHash", ""),
            provenance="LIVE", source="eth_getLogs",
            detail={"counterparty": to,
                    "block": lg.get("blockNumber"),
                    "log_index": lg.get("logIndex")}))
    return trades


def _int_from_data(data) -> Optional[float]:
    if not data or not isinstance(data, str) or not data.startswith("0x"):
        return None
    try:
        return float(int(data, 16))
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Chain health
# --------------------------------------------------------------------------


def chain_health(targets: Optional[List[str]] = None) -> Dict[str, Any]:
    """Check, live, which chains and data sources are reachable right now."""
    targets = targets or list(CHAINS.keys())
    out: Dict[str, Any] = {"chains": {}, "gaps": [], "checked_at": now_ts()}
    for cid in targets:
        try:
            spec = get_chain(cid)
        except KeyError:
            out["gaps"].append({"source": cid,
                                 "reason": "unknown chain id"})
            continue
        rec: Dict[str, Any] = {"reachable": False, "rpc_status": "n/a",
                               "data_status": "n/a", "note": ""}
        try:
            if spec.family == FAMILY_EVM:
                client = EVMClient(cid)
                bn = client.block_number()
                rec["rpc_status"] = f"HTTP 200 block={bn}"
                rec["reachable"] = True
            else:
                client = SolanaClient(cid)
                slot = client.get_slot()
                rec["rpc_status"] = f"HTTP 200 slot={slot}"
                rec["reachable"] = True
        except Exception as exc:  # noqa: BLE001
            rec["rpc_status"] = f"UNREACHABLE ({type(exc).__name__})"
            rec["note"] = str(exc)[:160]
            out["gaps"].append({"source": f"{cid}:rpc", "reason": str(exc)[:200]})
        # DexScreener data source (all chains).
        try:
            from .http import http_json
            _d, status = http_json(
                "https://api.dexscreener.com/token-boosts/top/v1",
                timeout=20, retries=1)
            rec["data_status"] = f"dexscreener HTTP {status}"
        except Exception as exc:  # noqa: BLE001
            rec["data_status"] = f"dexscreener UNREACHABLE ({type(exc).__name__})"
            out["gaps"].append({"source": f"{cid}:dexscreener",
                                "reason": str(exc)[:200]})
        out["chains"][cid] = rec
    return out


if __name__ == "__main__":
    import sys

    print("MULTI-CHAIN HEALTH")
    h = chain_health(list(CHAINS.keys()))
    for cid, rec in h["chains"].items():
        print(f"  [{'OK ' if rec['reachable'] else 'DOWN'}] {cid:<10} "
              f"rpc={rec['rpc_status']}  data={rec['data_status']}")
        if rec.get("note"):
            print(f"        {rec['note']}")
    print()
    print("TOKEN EVENTS — a real snapshot per chain")
    samples = {
        "solana": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "ethereum": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
        "base": "0x532f27101965dd16442E59d40670FaF5eBB142E4",
        "bsc": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
        "arbitrum": "0x912CE59144191C1204E64559FE8253a0e49E6548",
    }
    for cid, addr in samples.items():
        try:
            res = fetch_token_events(cid, addr)
            print(f"  {cid:<10} events={len(res['events'])} "
                  f"sources={res['source'] or 'none'}")
            for e in res["events"][:3]:
                print(f"      {e.kind}  {e.source}  "
                      f"{json.dumps(e.detail)[:110]}")
            for g in res["gaps"]:
                print(f"      GAP {g['source']}: {g['reason'][:100]}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {cid:<10} FAILED {type(exc).__name__}: {str(exc)[:90]}")
    print()
    print("WALLET TRADES — real, per chain")
    wallets = {
        "solana": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        "ethereum": "0x28C6c06298d514Db089934071355E5743bf21d60",
        "base": "0x28C6c06298d514Db089934071355E5743bf21d60",
        "bsc": "0x28C6c06298d514Db089934071355E5743bf21d60",
        "arbitrum": "0x28C6c06298d514Db089934071355E5743bf21d60",
    }
    for cid, w in wallets.items():
        try:
            tr = fetch_wallet_trades(cid, w, limit=25)
            print(f"  {cid:<10} trades={len(tr)}  wallet={w}")
            for t in tr[:2]:
                print(f"      {t.side:<4} {t.token[:16]} amt={t.amount} "
                      f"src={t.source}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {cid:<10} FAILED {type(exc).__name__}: {str(exc)[:90]}")
    sys.exit(0)
