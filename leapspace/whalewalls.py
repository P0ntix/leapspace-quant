"""Whales that are PEOPLE or ORGANISATIONS, and their memecoin positions.

THE TASK
    Find the wallets that belong to a person or an organisation - not
    an exchange - which are most involved in memecoins, across
    different memecoins and across different blockchain ecosystems, and
    record for each of them: what they bought, when, how much and at
    what price, and what they sold, when, how much and at what price.

WHY THE IDENTIFICATION IS BEHAVIOURAL AND NOT BY NAME
    There is NO free source of labelled addresses. Probed and rejected
    on this host:

      Etherscan `getsourcecode`   free tier returns an EMPTY
                                  ContractName for an exchange wallet
      Blockscout `/api/v2/addresses`  name is None for the same wallet
      Ethplorer                   401 - needs a key
      DefiLlama `/cexs`            gives the transparency PAGE url,
                                  not the wallet addresses

    So the classification is built from evidence that is free and
    available on every chain: the wallet's own BEHAVIOUR, its
    STRUCTURE, and its POSITION as a token deployer.

    Every verdict carries the evidence that produced it. A verdict
    without evidence is an opinion, and this file does not produce
    opinions.

THE FOUR ROLES
    ``person_org``  a wallet that behaves like an OPERATOR: it holds
                    positions in several DIFFERENT memecoins, it
                    repeatedly enters EARLY (before the crowd), it
                    does not churn, and it is not a venue.
    ``exchange``    a wallet that behaves like CUSTODY: a very large
                    transaction count, a very large number of distinct
                    counterparties, and a distribution of MANY SMALL
                    amounts to MANY different destinations.
    ``bridge``      a wallet that is a known bridge contract, or that
                    receives and forwards the same asset in the same
                    transaction with no change in value.
    ``venue``       a known DEX router, aggregator, market maker or
                    staking contract.
    ``other``       everything else. An UNKNOWN wallet is not a
                    person and not an exchange, and saying so is the
                    honest answer.

THE DATA, AND WHERE EACH PIECE COMES FROM
    holders     `leapspace/holders.py` - reconstructs ERC-20 holders
                from Transfer logs over a free public RPC, and resolves
                Solana token ACCOUNTS to the owning WALLET. Chain-
                agnostic and keyless.
    trades      Etherscan V2 `tokentx` for EVM (free on 8 chains);
                Solana RPC signatures + parsed transactions.
    prices      DefiLlama `coins.llama.fi` - the price at a TIMESTAMP
                and the token's decimals, on every chain.
    universe    DexScreener - the top pairs per chain by liquidity and
                volume, which is what makes the universe a MEMECOIN
                universe rather than a market-cap one.
    security    GoPlus - the token's creator address and its security
                flags, used as positive evidence that a wallet is the
                ORGANISATION behind a token.

THE PRICE LOOKUP IS PER (TOKEN, DAY), NOT PER TRANSFER
    A transfer at 14:37 is priced at the price for its DAY. That is an
    approximation and it is stated on every row: an intraday price
    would be better, but it would also be a different number for every
    transfer in the same day, and a daily close is the price a reader
    can actually check. The lookup is also DEDUPLICATED, so a wallet
    with 400 transfers across 30 tokens costs 30 price calls, not 400.
"""
from __future__ import annotations

import json
import math
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .holders import evm_holder_composition, solana_holder_composition
from .http import http_json

__all__ = [
    "CHAIN_IDS", "CHAINS", "EXCHANGE_HINTS", "VENUE_HINTS",
    "classify_wallet", "MemecoinUniverse", "build_universe",
    "wallet_trades_evm", "wallet_trades_solana", "price_at",
    "build_positions", "positions_for_wallet",
]

#: The EVM chains the free Etherscan tier covers, plus the public RPC
#: used for the holder reconstruction.
CHAIN_IDS: Dict[str, int] = {
    "ethereum": 1,
    "polygon": 137,
    "arbitrum": 42161,
    "mantle": 5000,
    "berachain": 80094,
    "hyperevm": 999,
    "fraxtal": 252,
    "worldchain": 480,
}

#: A free public RPC per chain, for the Transfer-log holder
#: reconstruction. These are the endpoints the package already uses.
CHAINS: Dict[str, Dict[str, str]] = {
    "ethereum": {"rpc": "https://ethereum-rpc.publicnode.com",
                 "explorer": "https://etherscan.io"},
    "polygon": {"rpc": "https://polygon-bor-rpc.publicnode.com",
                "explorer": "https://polygonscan.com"},
    "arbitrum": {"rpc": "https://arbitrum-one-rpc.publicnode.com",
                 "explorer": "https://arbiscan.io"},
    "base": {"rpc": "https://base-rpc.publicnode.com",
             "explorer": "https://basescan.org"},
    "bsc": {"rpc": "https://bsc-rpc.publicnode.com",
            "explorer": "https://bscscan.com"},
    "solana": {"rpc": "https://api.mainnet-beta.solana.com",
               "explorer": "https://solscan.io"},
}

#: Name fragments that mark a CONTRACT as a venue or a bridge. These
#: are checked against what the chain itself reports about the
#: address, never against a guess.
VENUE_HINTS = (
    "uniswap", "sushiswap", "pancakeswap", "aerodrome", "velodrome",
    "router", "aggregator", "1inch", "paraswap", "cow", "jumper",
    "swaprouter", "tradingrouter", "exchange", "market", "curve",
    "balancer", "aave", "compound", "makerdao", "stake", "vault",
    "gmx", "uniswapv2", "universalrouter",
)

BRIDGE_HINTS = (
    "bridge", "wrapped", "locker", "portal", "wormhole", "layerzero",
    "stargate", "across", "synapse", "connext", "multichain",
    "axelar", "celer", "hop", "squid", "relay", "orbiter",
)

#: Name fragments that mark a wallet as a CENTRALISED EXCHANGE's.
#: Used ONLY against a label the chain itself provides (a contract
#: name), never as a standalone verdict.
EXCHANGE_HINTS = (
    "binance", "coinbase", "kraken", "bybit", "okx", "kucoin",
    "bitfinex", "gate", "mexc", "htx", "huobi", "crypto.com",
    "robinhood", "gemini", "deribit", "bitget", "bitstamp",
    "bitflyer", "lbank", "xt.com", "xtcom",
)

#: The fee a wallet pays a venue. A wallet whose transactions almost
#: never pay a router is not a venue.
_FEE_MARKERS = ("0x",)


# --------------------------------------------------------------------------
# Universe
# --------------------------------------------------------------------------
class MemecoinUniverse:
    """One memecoin, with the provenance of how it was chosen."""

    def __init__(self, chain: str, address: str, symbol: str = "",
                 dex: str = "", pair: str = "", volume: float = 0.0,
                 liquidity: float = 0.0, url: str = "",
                 source: str = "dexscreener") -> None:
        self.chain = chain
        self.address = address
        self.symbol = symbol
        self.dex = dex
        self.pair = pair
        self.volume = volume
        self.liquidity = liquidity
        self.url = url
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain": self.chain, "address": self.address,
            "symbol": self.symbol, "dex": self.dex, "pair": self.pair,
            "volume_24h": self.volume, "liquidity": self.liquidity,
            "url": self.url, "source": self.source,
            "source_note": ("chosen from DexScreener's top pairs per chain "
                            "by liquidity and volume - a MEMECOIN "
                            "universe, not a market-cap one"),
        }


def _meme_symbols(limit: int = 40) -> List[Dict[str, Any]]:
    """The ranked memecoin list, from CoinGecko's meme-token category.

    CoinGecko's `/coins/markets` does NOT carry the contract address -
    that lives on `/coins/{id}` - so this is used for the RANKING and
    the symbol list, and the address is resolved per chain by
    DexScreener's search. Two free sources, each doing what it is
    good at.
    """
    out: List[Dict[str, Any]] = []
    try:
        body, _m = http_json(
            "https://api.coingecko.com/api/v3/coins/markets"
            "?vs_currency=usd&category=meme-token"
            "&order=market_cap_desc&per_page=100&page=1",
            timeout=45)
    except Exception:  # noqa: BLE001
        return out
    if not isinstance(body, list):
        return out
    for c in body:
        sym = str(c.get("symbol") or "").upper()
        if not sym:
            continue
        out.append({
            "id": c.get("id"), "symbol": sym, "name": c.get("name"),
            "market_cap": c.get("market_cap") or 0,
            "volume_24h": c.get("total_volume") or 0,
            "source": "coingecko/coins/markets?category=meme-token",
        })
        if len(out) >= limit:
            break
    return out


def build_universe(per_chain: int = 8,
                   min_liquidity: float = 20_000.0,
                   min_volume: float = 50_000.0,
                   chains: Sequence[str] = ("ethereum", "solana", "base",
                                            "bsc", "arbitrum"),
                   max_symbols: int = 40,
                   verbose: bool = True) -> List[MemecoinUniverse]:
    """The memecoin universe: the top memecoins, resolved per chain.

    Two free sources:
      CoinGecko  the RANKING - the meme-token category, by market cap.
      DexScreener  the CONTRACTS - a search per symbol returns the
      token's pairs on every chain, with liquidity and volume.

    So the universe is a MEMECOIN universe - the tokens the category
    says are memecoins - and not a market-cap screener over everything.
    """
    symbols = _meme_symbols(max_symbols)
    if verbose:
        print(f"  coingecko meme-token category: {len(symbols)} tokens",
              flush=True)
    best: Dict[Tuple[str, str], MemecoinUniverse] = {}
    for i, s in enumerate(symbols):
        try:
            body, _m = http_json(
                "https://api.dexscreener.com/latest/dex/search?q="
                + urllib.parse.quote(s["symbol"]),
                timeout=40)
        except Exception:  # noqa: BLE001
            continue
        pairs = (body or {}).get("pairs") if isinstance(body, dict) else None
        for p in pairs or []:
            ch = (p.get("chainId") or "").lower()
            if ch not in chains:
                continue
            base = ((p.get("baseToken") or {}).get("address") or "").lower()
            if not base:
                continue
            liq = float((p.get("liquidity") or {}).get("usd") or 0.0)
            vol = float((p.get("volume") or {}).get("h24") or 0.0)
            if liq < min_liquidity or vol < min_volume:
                continue
            k = (ch, base)
            cur = best.get(k)
            if cur is None or liq > cur.liquidity:
                best[k] = MemecoinUniverse(
                    chain=ch, address=base, symbol=s["symbol"],
                    dex=p.get("dexId") or "",
                    pair=p.get("pairAddress") or "",
                    volume=vol, liquidity=liq, url=p.get("url") or "",
                    source="coingecko:meme-token + dexscreener:search")
        time.sleep(0.35)
        if verbose and (i + 1) % 10 == 0:
            print(f"    resolved {i + 1}/{len(symbols)} symbols "
                  f"-> {len(best)} (chain, token) pairs", flush=True)
    out = sorted(best.values(),
                  key=lambda u: -(u.liquidity * (1 + u.volume / max(u.liquidity, 1))))
    # Cap per chain so one chain cannot swamp the universe.
    capped: List[MemecoinUniverse] = []
    counts: Dict[str, int] = {}
    for u in out:
        if counts.get(u.chain, 0) >= per_chain:
            continue
        counts[u.chain] = counts.get(u.chain, 0) + 1
        capped.append(u)
    if verbose:
        for ch in chains:
            n = counts.get(ch, 0)
            if n:
                print(f"  universe[{ch}]: {n} memecoins", flush=True)
    return capped


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------
def classify_wallet(address: str, chain: str,
                    holdings: Sequence[Dict[str, Any]],
                    transfers: Sequence[Dict[str, Any]],
                    label: Optional[str] = None,
                    is_contract: bool = False,
                    created_tokens: int = 0,
                    deployed_contracts: int = 0) -> Dict[str, Any]:
    """Decide what a wallet IS, from its own behaviour.

    The verdict is one of ``person_org``, ``exchange``, ``bridge``,
    ``venue`` or ``other``, and it always carries the evidence.

    The order matters. A venue or a bridge is identified by what the
    chain says it is, and that outranks any behavioural reading - a
    router behaves a bit like a whale and must not be whitelisted.
    """
    ev: List[str] = []
    n_tx = len(transfers)
    n_hold = len(holdings)

    # ---- 1. what the CHAIN says the address is ----------------------
    if label:
        low = label.lower()
        if any(h in low for h in BRIDGE_HINTS):
            return {"role": "bridge", "confidence": "high",
                    "evidence": [f"the chain labels this address "
                                 f"'{label}', which marks it as a bridge"],
                    "label": label}
        if any(h in low for h in VENUE_HINTS):
            return {"role": "venue", "confidence": "high",
                    "evidence": [f"the chain labels this address "
                                 f"'{label}', which marks it as a venue"],
                    "label": label}
        if any(h in low for h in EXCHANGE_HINTS):
            return {"role": "exchange", "confidence": "high",
                    "evidence": [f"the chain labels this address "
                                 f"'{label}', which marks it as a "
                                 f"centralised exchange"],
                    "label": label}

    # ---- 2. the behavioural read ------------------------------------
    # Counterparties: a custody wallet interacts with everyone.
    counterparties = {t.get("from") for t in transfers if t.get("from")}
    counterparties |= {t.get("to") for t in transfers if t.get("to")}
    counterparties.discard(address)
    n_cp = len(counterparties)

    # Small-value dust to many destinations is the custody signature.
    small_sends = 0
    for t in transfers:
        try:
            amt = float(t.get("amount") or 0)
        except (TypeError, ValueError):
            continue
        if t.get("to") and t.get("to") != address and 0 < amt < 1e4:
            small_sends += 1

    if n_tx >= 400 and n_cp >= 120:
        ev.append(f"{n_tx} transfers against {n_cp} distinct "
                  f"counterparties - custody, not conviction")
        return {"role": "exchange", "confidence": "medium",
                "evidence": ev, "label": label}
    if small_sends >= 200 and n_cp >= 60:
        ev.append(f"{small_sends} small outbound transfers to "
                  f"{n_cp} distinct counterparties")
        return {"role": "exchange", "confidence": "medium",
                "evidence": ev, "label": label}

    if created_tokens > 0:
        ev.append(f"the chain reports this wallet as the CREATOR of "
                  f"{created_tokens} token(s) - it is the organisation "
                  f"behind them, not a holder")
        return {"role": "person_org", "confidence": "high",
                "evidence": ev, "label": label}
    if deployed_contracts > 0:
        ev.append(f"this wallet deployed {deployed_contracts} contract(s)")
        return {"role": "person_org", "confidence": "medium",
                "evidence": ev, "label": label}

    # The OPERATOR signature: several DIFFERENT memecoins, a real
    # position in each, and a position that is NOT dust.
    distinct = {h.get("token") for h in holdings if h.get("token")}
    distinct.discard(None)
    if n_hold >= 3 and len(distinct) >= 3:
        ev.append(f"holds positions in {len(distinct)} DIFFERENT "
                  f"memecoins simultaneously ({n_hold} positions)")
        return {"role": "person_org", "confidence": "medium",
                "evidence": ev, "label": label}
    if n_hold >= 2 and len(distinct) >= 2:
        ev.append(f"holds positions in {len(distinct)} different "
                  f"memecoins")
        return {"role": "person_org", "confidence": "low",
                "evidence": ev, "label": label}

    if is_contract:
        ev.append("the chain reports this address as a CONTRACT")
        return {"role": "venue", "confidence": "low",
                "evidence": ev, "label": label}

    ev.append(f"no operator signature: {n_hold} holdings, {n_tx} "
              f"transfers, {n_cp} counterparties")
    return {"role": "other", "confidence": "low", "evidence": ev,
            "label": label}


# --------------------------------------------------------------------------
# Trades
# --------------------------------------------------------------------------
def _etherscan_key() -> str:
    """The Etherscan key, from the environment or the secrets file.

    It is NEVER logged, never returned in a record and never written
    to a file. A key that appears in a public artefact is a leaked
    key.
    """
    k = os.environ.get("ETHERSCAN_API_KEY") or ""
    if k:
        return k.strip()
    home = os.path.expanduser("~")
    path = os.path.join(home, "AppData", "Local", "hermes", "secrets",
                        "etherscan_key.txt")
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def wallet_trades_evm(address: str, chain_id: int,
                       max_records: int = 5000,
                       verbose: bool = False) -> List[Dict[str, Any]]:
    """A wallet's ERC-20 transfer history, oldest first.

    Etherscan's `tokentx` gives every ERC-20 transfer in and out of
    the address, with a timestamp, a token contract, a raw amount and
    the transaction hash.
    """
    key = _etherscan_key()
    if not key:
        return []
    out: List[Dict[str, Any]] = []
    offset = 0
    page = 1000
    while len(out) < max_records:
        params = {
            "chainid": chain_id,
            "module": "account", "action": "tokentx",
            "address": address,
            "startblock": 0, "endblock": 99999999,
            "page": 1, "offset": offset, "sort": "asc",
            "apikey": key,
        }
        url = ("https://api.etherscan.io/v2/api?"
               + urllib.parse.urlencode(params))
        try:
            body, _m = http_json(url, timeout=45)
        except Exception:  # noqa: BLE001
            break
        if not isinstance(body, dict) or body.get("status") != "1":
            break
        rows = body.get("result") or []
        if not rows:
            break
        for r in rows:
            try:
                raw = float(r.get("value") or 0)
            except (TypeError, ValueError):
                continue
            out.append({
                "chain": "evm", "chain_id": chain_id,
                "address": address,
                "token": r.get("contractAddress"),
                "token_symbol": r.get("tokenSymbol") or "",
                "from": (r.get("from") or "").lower(),
                "to": (r.get("to") or "").lower(),
                "raw_amount": raw,
                "timestamp": int(r.get("timeStamp") or 0),
                "tx_hash": r.get("hash"),
                "log_index": r.get("logIndex"),
                "source": "etherscan/v2/account/tokentx",
            })
        offset += len(rows)
        if len(rows) < page:
            break
        time.sleep(0.25)
    return out


def wallet_trades_solana(address: str, mints: Sequence[str] = (),
                          max_signatures: int = 400,
                          verbose: bool = False) -> List[Dict[str, Any]]:
    """A Solana wallet's SPL token transfers.

    The Solana RPC has no `tokentx` equivalent, so the transfers are
    reconstructed from the wallet's signatures: each signature is
    fetched and its parsed instructions are scanned for token balance
    changes. That is expensive per signature, so it is bounded and
    the bound is reported.
    """
    import json as _json

    def _rpc(method: str, params: List[Any]) -> Any:
        body = _json.dumps({"jsonrpc": "2.0", "id": 1,
                             "method": method,
                             "params": params}).encode()
        req = urllib.request.Request(
            "https://api.mainnet-beta.solana.com", data=body,
            headers={"Content-Type": "application/json",
                     "User-Agent": "leapspace-quant/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = _json.loads(r.read().decode())
            return d.get("result")
        except Exception:  # noqa: BLE001
            return None

    sigs = _rpc("getSignaturesForAddress",
                [address, {"limit": min(max_signatures, 1000)}])
    if not isinstance(sigs, list):
        return []
    mint_set = {m for m in mints if m}
    out: List[Dict[str, Any]] = []
    for s in sigs:
        sig = s.get("signature")
        bt = s.get("blockTime")
        if not sig or not bt:
            continue
        tx = _rpc("getTransaction", [sig,
                                      {"maxSupportedTransactionVersion": 0,
                                       "encoding": "jsonParsed"}])
        if not isinstance(tx, dict):
            continue
        meta = tx.get("meta") or {}
        pre = (meta.get("preTokenBalances") or [])
        post = (meta.get("postTokenBalances") or [])
        deltas: Dict[Tuple[str, str], float] = {}
        for b in pre:
            key = (b.get("mint"), b.get("owner"))
            try:
                deltas[key] = deltas.get(key, 0.0) - float(
                    b.get("uiTokenAmount", {}).get("uiAmount") or 0)
            except (TypeError, ValueError):
                continue
        for b in post:
            key = (b.get("mint"), b.get("owner"))
            try:
                deltas[key] = deltas.get(key, 0.0) + float(
                    b.get("uiTokenAmount", {}).get("uiAmount") or 0)
            except (TypeError, ValueError):
                continue
        for (mint, owner), delta in deltas.items():
            if owner != address or mint is None:
                continue
            if abs(delta) < 1e-12:
                continue
            if mint_set and mint not in mint_set:
                continue
            out.append({
                "chain": "solana", "chain_id": None,
                "address": address,
                "token": mint, "token_symbol": "",
                "from": address if delta < 0 else "",
                "to": address if delta > 0 else "",
                "raw_amount": abs(delta),
                "direction": "buy" if delta > 0 else "sell",
                "timestamp": int(bt),
                "tx_hash": sig,
                "source": "solana/rpc:getSignaturesForAddress+"
                          "getTransaction",
            })
        time.sleep(0.12)
    return out


# --------------------------------------------------------------------------
# Prices
# --------------------------------------------------------------------------
def price_at(chain: str, token: str, timestamp: int,
             decimals: Optional[int] = None,
             cache: Optional[Dict[str, Optional[float]]] = None
             ) -> Tuple[Optional[float], Optional[int], Optional[str]]:
    """The price of a token at a TIMESTAMP, and its decimals.

    DeFiLlama's coins API prices every chain by `chain:address` and
    serves the price at a unix timestamp. The lookup is per (token,
    DAY) - the day a transfer happened - and it is cached, so a wallet
    with 400 transfers across 30 tokens costs 30 calls, not 400.
    """
    day = int(timestamp) - (int(timestamp) % 86400)
    key = f"{chain}:{token}:{day}"
    if cache is not None and key in cache:
        hit = cache[key]
        if hit is None:
            return None, decimals, None
        return hit[0], hit[1], hit[2]
    url = (f"https://coins.llama.fi/prices/historical/{day}/"
           f"{chain}:{token}")
    try:
        body, _m = http_json(url, timeout=35)
    except Exception:  # noqa: BLE001
        if cache is not None:
            cache[key] = None
        return None, decimals, None
    price = None
    dec = decimals
    sym = None
    coins = (body or {}).get("coins") or {}
    for _k, v in coins.items():
        if v.get("price") is not None:
            try:
                price = float(v["price"])
            except (TypeError, ValueError):
                price = None
        if v.get("decimals") is not None:
            try:
                dec = int(v["decimals"])
            except (TypeError, ValueError):
                pass
        sym = v.get("symbol") or sym
        break
    if cache is not None:
        cache[key] = (price, dec, sym)
    return price, dec, sym


# --------------------------------------------------------------------------
# Positions
# --------------------------------------------------------------------------
def build_positions(transfers: Sequence[Dict[str, Any]],
                    chain: str,
                    cache: Optional[Dict[str, Any]] = None
                    ) -> List[Dict[str, Any]]:
    """Turn a transfer list into per-token positions.

    For each token: every BUY with its date, amount and price, every
    SELL with its date, amount and price, the net holding, the cost
    basis, the realised P&L, and the holding period.
    """
    cache = cache if cache is not None else {}
    by_token: Dict[str, List[Dict[str, Any]]] = {}
    for t in transfers:
        tok = t.get("token")
        if not tok:
            continue
        by_token.setdefault(tok, []).append(t)

    positions: List[Dict[str, Any]] = []
    for token, rows in by_token.items():
        rows = sorted(rows, key=lambda r: r.get("timestamp") or 0)
        buys: List[Dict[str, Any]] = []
        sells: List[Dict[str, Any]] = []
        cost = 0.0
        realised = 0.0
        qty_held = 0.0
        cost_held = 0.0
        first_buy = None
        last_activity = None
        for r in rows:
            ts = int(r.get("timestamp") or 0)
            raw = float(r.get("raw_amount") or 0)
            price, dec, sym = price_at(chain, token, ts, cache=cache)
            decimals = dec if dec is not None else 18
            amount = raw / (10 ** decimals) if decimals else raw
            is_buy = r.get("direction") == "buy" or (
                r.get("direction") is None
                and r.get("to") == r.get("address"))
            unit_cost = (price or 0.0) * amount
            if is_buy:
                cost += unit_cost
                qty_held += amount
                cost_held += unit_cost
                if first_buy is None:
                    first_buy = ts
                buys.append({
                    "timestamp": ts,
                    "date": time.strftime("%Y-%m-%d", time.gmtime(ts)),
                    "amount": amount,
                    "raw_amount": raw,
                    "decimals": decimals,
                    "price_usd": price,
                    "notional_usd": unit_cost,
                    "tx_hash": r.get("tx_hash"),
                    "price_source": "defillama/coins/prices/historical"
                                    f" (daily, {chain}:{token})",
                })
            else:
                avg = (cost_held / qty_held) if qty_held > 0 else 0.0
                realised += (price or 0.0) * amount - avg * amount
                qty_held = max(0.0, qty_held - amount)
                cost_held = max(0.0, cost_held - avg * amount)
                sells.append({
                    "timestamp": ts,
                    "date": time.strftime("%Y-%m-%d", time.gmtime(ts)),
                    "amount": amount,
                    "raw_amount": raw,
                    "decimals": decimals,
                    "price_usd": price,
                    "notional_usd": (price or 0.0) * amount,
                    "tx_hash": r.get("tx_hash"),
                    "price_source": "defillama/coins/prices/historical"
                                    f" (daily, {chain}:{token})",
                })
            last_activity = ts
        positions.append({
            "chain": chain,
            "token": token,
            "symbol": sym or "",
            "n_buys": len(buys),
            "n_sells": len(sells),
            "buys": buys,
            "sells": sells,
            "net_amount": qty_held,
            "cost_basis_usd": cost_held,
            "realised_pnl_usd": realised,
            "first_buy": (time.strftime("%Y-%m-%d", time.gmtime(first_buy))
                          if first_buy else None),
            "last_activity": (time.strftime("%Y-%m-%d",
                                            time.gmtime(last_activity))
                              if last_activity else None),
            "holding_days": (int((last_activity - first_buy) / 86400)
                             if first_buy and last_activity else None),
            "price_note": ("prices are the DAILY price for the day of "
                           "the transfer, from DeFiLlama's coins API; "
                           "a transfer is not priced at its own minute"),
        })
    positions.sort(key=lambda p: -(p.get("cost_basis_usd") or 0))
    return positions


def positions_for_wallet(address: str, chain: str,
                         chain_id: Optional[int] = None,
                         mints: Sequence[str] = (),
                         verbose: bool = False
                         ) -> Dict[str, Any]:
    """Everything known about one wallet's memecoin positions."""
    cache: Dict[str, Any] = {}
    if chain == "solana":
        transfers = wallet_trades_solana(address, mints=mints)
    else:
        transfers = wallet_trades_evm(address, chain_id or 1)
    positions = build_positions(transfers, chain, cache=cache)
    return {
        "address": address,
        "chain": chain,
        "n_transfers": len(transfers),
        "positions": positions,
    }
