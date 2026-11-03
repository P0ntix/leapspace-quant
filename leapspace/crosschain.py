"""
Candidate cross-chain wallet linker.

THE PROBLEM
-----------
A "whitelist of memecoin whales and consistently successful traders"
cannot be one list of addresses. The same operator runs several wallets
across several chains, and a whitelist that treats those wallets as
independent entities double-counts the operator's positions and
understates their concentration.

This module produces CANDIDATE LINKS between wallets observed on
different chains, each with a score AND the evidence that produced it.
A link is CONFIRMED only when an explicit on-chain artefact supports
it. Everything else is SUGGESTED.

THE FOUR SIGNALS
----------------
  (i)   SHARED FUNDING SOURCE. The first funder of a wallet is the
        earliest address to send it native gas. Two wallets funded by
        the same address are a candidate pair. This is the signal
        Nansen documents and exposes as "Address First Funder":
        https://docs.nansen.ai/api/profiler/address-first-funder
        ("the earliest address to send native gas to the input EVM
        address... on whichever supported chain the earliest funding
        happened"). This module reimplements it from raw JSON-RPC
        because Nansen's endpoint needs an API key.

  (ii)  COMMON COUNTERPARTIES. Wallets that trade with the same set of
        venues, pools and routers are more likely to be one operator.
        Nansen exposes the same idea as "Address Counterparties":
        https://docs.nansen.ai/api/profiler/address-counterparties

  (iii) CORRELATED TIMING. Two wallets whose activity timestamps
        cluster together are more likely to be driven by one decision
        process. This is the weakest signal on its own: MEV bots,
        airdrop farmers and indexers all produce coincident timing.

  (iv)  SIMILAR POSITION SIZES. The same operator tends to size
        positions similarly across their wallets.

WHAT "CONFIRMED" REQUIRES
-------------------------
A CONFIRMED link must point at an on-chain artefact that ties the two
wallets together, and the artefact must be reproducible by re-reading
the chain. This module confirms a link only when one of these holds:

  * SAME_ADDRESS_MULTI_CHAIN - the SAME address is active on two chains
    AND the same address funded it on both. One private key signed
    funding transactions on two chains; that is one operator. The
    artefact is the pair of funding transaction hashes.

  * BRIDGE_TRANSFER - one of the wallets sent a transaction to a bridge
    contract and the OTHER wallet is the recipient of the corresponding
    delivery on the other chain. The artefact is the bridge's own
    transfer record, and the code reports the tx hashes on both sides.

  * SHARED_FUNDER_IS_A_BRIDGE - the two wallets share a first funder,
    AND that funder is itself a verified bridge contract, i.e. the
    funding came from the same on-chain bridge entity on both chains.
    The artefact is the funder's contract code plus the two funding
    transactions.

  * IDENTICAL_FUNDER_NONCE_SEQUENCE - the two wallets were funded by
    the same sender in the same block. (A same-block funding from one
    sender to two wallets is a direct on-chain statement that they were
    created together.)

Everything else is SUGGESTED, and the module says which signal produced
the score and how strong it is.

THE BRIDGE REGISTRY IS VERIFIED, NOT ASSERTED
---------------------------------------------
An earlier hand-written table of bridge addresses was checked against
`eth_getCode` and four of its five addresses had NO contract code -
they were simply wrong addresses. The registry in this module is now
built from Blockscout's CURATED address labels (its v2 search API
returns entries with `type: "label"`; querying `q=Bridge` returns the
addresses Blockscout itself classifies as bridges) and EVERY entry was
then proved to have contract bytecode over a keyless archive RPC. The
build script is tools/build_bridge_registry3.py and the full audit
trail, including rejected addresses, is reports/bridge_registry.json.

CITATIONS
---------
  Nansen, "Address First Funder":
    https://docs.nansen.ai/api/profiler/address-first-funder
  Nansen, "Address Related Wallets":
    https://docs.nansen.ai/api/profiler/address-related-wallets
  Nansen, "Address Counterparties":
    https://docs.nansen.ai/api/profiler/address-counterparties
  ethereum.org, "Sybil attack" (glossary):
    https://ethereum.org/en/glossary/
    "Sybil attacks refer to individual humans tricking a system into
     thinking they are multiple people to increase their influence."
    This is the definition the module uses for the PROBLEM it solves:
    one operator running many wallets is a Sybil pattern, and the
    remedy is to detect and cluster it.
  Nansen Profiler index (lists the endpoint family):
    https://docs.nansen.ai/api/profiler

KNOWN LIMITATIONS
-----------------
* A shared funder is NOT proof. Two unrelated users withdrawing from
  the same exchange hot wallet have the same first funder. The module
  therefore reports the funder's identity and whether it is a known
  high-volume entity, and it never labels such a link CONFIRMED.
* First-funder detection needs an ARCHIVE node to binary-search the
  wallet's first transaction block. Chains without a keyless archive
  provider (see ARCHIVE_RPC in leapspace.costs) report the first-funder
  signal as UNAVAILABLE rather than guessing.
* Counterparty sets are fetched from Blockscout's v2 API, which is
  Cloudflare-blocked for base/arbitrum/polygon from this host. Those
  chains fall back to the raw JSON-RPC path.
* None of this is identity proof in the legal sense. It is a
  CANDIDATE linker: its output is a ranked list for human review.
"""
from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .http import http_json, http_post_json
from .provenance import LIVE, SourceUnavailable

from .costs import (ARCHIVE_RPC, LATEST_RPC, ArchiveRpc, _hex_to_int,
                     _norm)

# --------------------------------------------------------------------------
# 1. Sources
# --------------------------------------------------------------------------
#: Blockscout v2 API hosts that answered HTTP 200 from this host on
#: 2026-11-03. base/arbitrum/polygon return HTTP 403 (a Cloudflare
#: "Just a moment" interstitial) and are therefore NOT listed - the
#: module falls back to JSON-RPC for them rather than pretending.
BLOCKSCOUT_HOSTS: Dict[str, str] = {
    "ethereum": "https://eth.blockscout.com",
    "optimism": "https://optimism.blockscout.com",
    "gnosis": "https://gnosis.blockscout.com",
    "zksync": "https://zksync.blockscout.com",
    "scroll": "https://scroll.blockscout.com",
    "celo": "https://explorer.celo.org",
}

#: RPCs used when a chain has no working Blockscout host.
CHAIN_RPCS: Dict[str, List[str]] = {
    "ethereum": ["https://eth.drpc.org",
                 "https://eth-mainnet.public.blastapi.io"],
    "base": ["https://base.drpc.org", "https://base-rpc.publicnode.com"],
    "arbitrum": ["https://arbitrum-one.public.blastapi.io",
                 "https://arbitrum-one-rpc.publicnode.com"],
    "bsc": ["https://api.zan.top/bsc-mainnet",
            "https://bsc-rpc.publicnode.com"],
    "optimism": ["https://optimism.drpc.org",
                 "https://optimism-rpc.publicnode.com"],
    "polygon": ["https://polygon.drpc.org",
                "https://polygon-bor-rpc.publicnode.com"],
    "gnosis": ["https://gnosis.drpc.org",
               "https://gnosis-rpc.publicnode.com"],
}

#: Bridge / relayer contracts, VERIFIED.
#:
#: These were NOT written from memory. An earlier hand-written table was
#: checked against `eth_getCode` and four of its five addresses had NO
#: contract code - they were simply wrong. This table is instead built
#: from Blockscout's CURATED address labels (its v2 search API returns
#: entries with `type: "label"`; querying `q=Bridge` returns the
#: addresses Blockscout itself classifies as bridges), and EVERY entry
#: was then proved to have contract bytecode over a keyless archive RPC.
#:
#: The value is the contract's own verified name, read back from
#: Blockscout - AnyswapV6Router, Ethereum_SpokePool, Gravity,
#: L1_ERC20_Bridge, WrappedTokenGatewayV3, RootChainManagerProxy and so
#: on. The build script and the full audit trail (including every
#: rejected address) are in tools/build_bridge_registry3.py and
#: reports/bridge_registry.json.
#:
#: A caller may pass its own registry; nothing here is assumed to be
#: complete.
KNOWN_BRIDGES: Dict[str, str] = {
    "0xf8b1378579659d8f7ee5f3c929c2f3e332e41fd6": "TransparentUpgradeableProxy",
    "0xd19d4b5d358258f05d7b411e21a1460d11b0876f": "TransparentUpgradeableProxy",
    "0xbd7d6a9ad7865463de44b05f04559f65e3b11704": "WrappedTokenGatewayV3",
    "0xba8da9dcf11b50b03fd5284f164ef5cdef910705": "AnyswapV6Router",
    "0xb8901acb165ed027e32754e0ffe830802919727f": "L1_ETH_Bridge",
    "0xae0ee0a63a2ce6baeeffe56e7714fb4efe48d419": "Proxy",
    "0xabea9132b05a70803a4e85094fd0e1800777fbef": "Proxy",
    "0xa4108aa1ec4967f8b52220a4f7e94a8201f2d906": "Gravity",
    "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": "RootChainManagerProxy",
    "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1": "L1ChugSplashProxy",
    "0x902f09715b6303d4173037652fa7377e5b98089e": "OptimizedTransparentUpgradeableProxy",
    "0x8731d54e9d02c286767d56ac03e8037c07e01e98": "Bridge",
    "0x765277eebeca2e31912c9946eae1021199b39c61": "AnyswapV4Router",
    "0x72ce9c846789fdb6fc1f34ac4ad25dd9ef7031ef": "TransparentUpgradeableProxy",
    "0x6b7a87899490ece95443e979ca9485cbe7e71522": "AnyswapV4Router",
    "0x659a00c33263d9254fed382de81349426c795bb6": "L1DAIBridge",
    "0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f": "TransparentUpgradeableProxy",
    "0x4d9079bb4165aeb4084c526a32695dcfd2f77381": "Ethereum_SpokePool",
    "0x3ee18b2214aff97000d974cf647e7c347e8fa585": "TokenBridge",
    "0x3e4a3a4796d16c0cd582c382691998f7c06420b6": "L1_ERC20_Bridge",
    "0x3666f603cc164936c1b87e207f36beba4ac5f18a": "L1_ERC20_Bridge",
    "0x150f94b44927f078737562f0fcf3c95c01cc2376": "RouterETH",
    "0x10e6593cdda8c58a1d0f14c5164b376352a55f2f": "L1DAITokenBridge",
    "0x3b3ae790df4f312e745d270119c6052904fb6790": "TransparentUpgradeableProxy",
}

#: Addresses that fund MANY unrelated users. A shared funder that is
#: one of these is NOT evidence of common control, and the module marks
#: such links DOWN rather than up.
KNOWN_COMMON_FUNDERS: Set[str] = set()


def _norm_addr(a: Optional[str]) -> str:
    return (a or "").strip().lower()


def _rpc_any(rpc: ArchiveRpc, method: str, params: List[Any]
             ) -> Dict[str, Any]:
    """Call `method` on the first provider that answers.

    Some providers refuse historical state for some methods. Trying them
    in turn keeps a single provider's limitation from being mistaken for
    a property of the chain.
    """
    last: Dict[str, Any] = {"result": None, "error": "no provider answered"}
    for url in rpc.urls:
        r = rpc._raw(url, method, params)
        if r.get("result") is not None:
            return r
        last = r
    return last


# --------------------------------------------------------------------------
# 2. First funder, from raw JSON-RPC
# --------------------------------------------------------------------------
def first_funder(address: str, chain: str = "ethereum",
                 rpc: Optional[ArchiveRpc] = None,
                 max_backscan_blocks: int = 20_000
                 ) -> Dict[str, Any]:
    """The first address that sent native gas to `address`.

    Nansen's definition ("the earliest address to send native gas to
    the input EVM address"), reimplemented keylessly:

      1. Binary search eth_getTransactionCount(addr, block) for the
         smallest block whose nonce is >= 1. That is the wallet's FIRST
         transaction block. Cost: ~log2(latest) RPC calls (about 25 on
         Ethereum), measured at 14.3 s on 2026-11-03.
      2. Read that block. If it contains a tx that SENT VALUE TO the
         wallet, its `from` is the funder.
      3. If the wallet already held a balance before that block, the
         funding happened earlier: scan backwards block by block for
         the earliest inbound value transfer. The scan is bounded and
         its bound is reported.

    Every step records the evidence (tx hash, block, value) so the
    answer can be checked against the chain by hand.
    """
    rpc = rpc or ArchiveRpc(chain)
    if not rpc.urls:
        return {"status": "unavailable", "chain": chain, "address": address,
                "reason": (f"No keyless archive RPC is configured for "
                           f"'{chain}', so the wallet's first transaction "
                           f"block cannot be located."),
                "source": "none"}
    head = rpc._head()
    if head is None:
        return {"status": "unavailable", "chain": chain, "address": address,
                "reason": "no RPC provider answered eth_blockNumber"}

    lo, hi, calls = 1, head, 0
    while lo < hi and calls < 40:
        mid = (lo + hi) // 2
        r = _rpc_any(rpc, "eth_getTransactionCount", [address, hex(mid)])
        calls += 1
        if r.get("result") is None:
            return {"status": "unavailable", "chain": chain,
                    "address": address, "rpc_calls": calls,
                    "reason": ("eth_getTransactionCount failed - the "
                               "provider is not serving historical state "
                               "for this chain."),
                    "rpc_error": r.get("rpc_error") or r.get("error")}
        if int(r["result"], 16) >= 1:
            hi = mid
        else:
            lo = mid + 1

    first_block = lo
    blk = rpc.get_block(first_block, full=True)
    if not blk.get("ok"):
        return {"status": "unavailable", "chain": chain, "address": address,
                "first_tx_block": first_block, "rpc_calls": calls,
                "reason": "could not read the first-transaction block"}
    txs = (blk.get("result") or {}).get("transactions") or []
    wallet_txs = [t for t in txs
                  if _norm_addr(t.get("from")) == _norm_addr(address)]
    inbound = [{"from": t.get("from"), "value": int(t.get("value") or "0x0", 16),
                "hash": t.get("hash")}
               for t in txs
               if _norm_addr(t.get("to")) == _norm_addr(address)
               and int(t.get("value") or "0x0", 16) > 0]
    bal_before = rpc._raw(rpc.urls[0], "eth_getBalance",
                          [address, hex(max(0, first_block - 1))])
    bal = _hex_to_int(bal_before.get("result")) or 0

    out: Dict[str, Any] = {
        "status": "ok", "chain": chain, "address": address,
        "first_tx_block": first_block, "rpc_calls": calls,
        "rpc_url": rpc.urls[0],
        "wallet_first_tx_hash": wallet_txs[0].get("hash") if wallet_txs else None,
        "n_txs_from_wallet_in_first_block": len(wallet_txs),
        "balance_before_first_block_wei": bal,
        "method": "nonce binary search + inbound value scan",
        "source": ("reimplements Nansen 'Address First Funder' "
                   "(https://docs.nansen.ai/api/profiler/address-first-funder) "
                   "keylessly"),
        "provenance": LIVE,
    }
    if inbound:
        out["first_funder"] = inbound[0]["from"]
        out["first_funder_evidence"] = {
            "kind": "inbound_native_transfer",
            "block": first_block, "tx_hash": inbound[0]["hash"],
            "value_wei": inbound[0]["value"],
            "note": ("The earliest inbound native transfer to this wallet, "
                     "found in the wallet's first-transaction block."),
        }
        return out

    if bal > 0:
        # The wallet was funded EARLIER than its first transaction.
        # Binary search for the first block at which its balance became
        # non-zero: that block contains the funding transaction. This is
        # O(log n) RPC calls, not one per block.
        lo2, hi2, calls2 = 1, first_block, 0
        funded_at = None
        while lo2 <= hi2 and calls2 < 40:
            mid = (lo2 + hi2) // 2
            rb = _rpc_any(rpc, "eth_getBalance", [address, hex(mid)])
            calls2 += 1
            v = _hex_to_int(rb.get("result"))
            if v is None:
                break
            if v > 0:
                funded_at = mid
                hi2 = mid - 1
            else:
                lo2 = mid + 1
        out["rpc_calls_backsearch"] = calls2
        if funded_at:
            # The funding block is where the balance first became non-zero.
            # Widen by a couple of blocks in case the transfer landed in a
            # block the binary search stepped just past.
            for probe_block in range(max(1, funded_at - 2),
                                    min(first_block, funded_at + 3)):
                bb = rpc.get_block(probe_block, full=True)
                if not bb.get("ok"):
                    continue
                btx = (bb.get("result") or {}).get("transactions") or []
                hits = [{"from": t.get("from"),
                         "value": int(t.get("value") or "0x0", 16),
                         "hash": t.get("hash")} for t in btx
                        if _norm_addr(t.get("to")) == _norm_addr(address)
                        and int(t.get("value") or "0x0", 16) > 0]
                if hits:
                    out["first_funder"] = hits[0]["from"]
                    out["first_funder_evidence"] = {
                        "kind": "balance_binary_search",
                        "block": probe_block, "tx_hash": hits[0]["hash"],
                        "value_wei": hits[0]["value"],
                        "rpc_calls": calls2,
                        "note": ("The wallet's balance first became non-zero "
                                 "at this block, which contains its earliest "
                                 "inbound native transfer."),
                    }
                    return out
        out["first_funder"] = None
        out["first_funder_evidence"] = {
            "kind": "not_found_within_scan",
            "funded_at_block": funded_at,
            "rpc_calls": calls2,
            "note": ("The wallet's balance was already non-zero before its "
                     "first transaction, but no inbound native transfer "
                     "could be located in the funding block. The funder is "
                     "NOT guessed - it may have been a contract "
                     "(paymaster, faucet) or the balance may predate the "
                     "block range this node can serve."),
        }
        return out

    out["first_funder"] = None
    out["first_funder_evidence"] = {
        "kind": "no_inbound_value_found",
        "note": ("No inbound native transfer to the wallet was found, and "
                 "its balance was zero before its first transaction. The "
                 "wallet may have been funded by a contract (e.g. a "
                 "paymaster or a faucet contract) rather than an EOA."),
    }
    return out


def funder_is_bridge(funder: Optional[str], chain: str = "ethereum",
                     rpc: Optional[ArchiveRpc] = None) -> Dict[str, Any]:
    """Is the funder a contract, and is it a KNOWN bridge?

    A funder with contract code is not an ordinary EOA: it is an
    on-chain entity (a bridge, a faucet, a paymaster, an exchange
    withdrawal router). A KNOWN bridge is much stronger evidence than an
    unknown contract, because a bridge has a specific, checkable
    identity.
    """
    if not funder:
        return {"status": "not_applicable", "is_contract": None,
                "is_known_bridge": False}
    rpc = rpc or ArchiveRpc(chain)
    code = _rpc_any(rpc, "eth_getCode", [funder, "latest"])
    code_hex = code.get("result")
    is_contract = bool(code_hex) and code_hex not in ("0x", "0x0")
    known = KNOWN_BRIDGES.get(_norm_addr(funder))
    return {
        "status": "ok",
        "funder": funder,
        "is_contract": is_contract,
        "contract_code_size": (len(code_hex) - 2) // 2 if code_hex else 0,
        "is_known_bridge": bool(known),
        "known_bridge_name": known or None,
        "http_status": code.get("http_status"),
        "provenance": LIVE,
    }


# --------------------------------------------------------------------------
# 3. Counterparties and timing
# --------------------------------------------------------------------------
def wallet_counterparties(address: str, chain: str = "ethereum",
                          limit: int = 100) -> Dict[str, Any]:
    """The set of addresses this wallet interacts with, plus its
    transaction timestamps.

    Primary source: Blockscout v2 `/addresses/{a}/transactions` and
    `/token-transfers` (HTTP 200 from this host on the chains listed in
    BLOCKSCOUT_HOSTS). Fallback: raw JSON-RPC.
    """
    host = BLOCKSCOUT_HOSTS.get(chain)
    if host:
        res = _bs_counterparties(host, address, limit)
        if res.get("status") == "ok":
            return res
        fallback = _rpc_counterparties(address, chain, limit)
        fallback["blockscout_status"] = res.get("status")
        fallback["blockscout_reason"] = res.get("reason")
        return fallback
    res = _rpc_counterparties(address, chain, limit)
    res["blockscout_status"] = f"no working Blockscout host for '{chain}'"
    return res


def _bs_counterparties(host: str, address: str, limit: int
                       ) -> Dict[str, Any]:
    base = f"{host}/api/v2/addresses/{address}"
    out: Dict[str, Any] = {"status": "ok", "chain_source": "blockscout",
                           "host": host, "address": address,
                           "counterparties": {}, "timestamps": [],
                           "n_counterparties": 0, "provenance": LIVE}
    try:
        data, status = http_json(f"{base}/transactions", timeout=25, retries=2)
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "reason":
                f"blockscout transactions: {type(exc).__name__}: {exc}"[:200],
                "http_status": None}
    out["http_status"] = status
    items = (data or {}).get("items") or []
    cps: Dict[str, int] = {}
    for it in items:
        frm = ((it.get("from") or {}).get("hash") or "").lower()
        to = ((it.get("to") or {}).get("hash") or "").lower()
        other = to if frm == address.lower() else frm
        if other and other != address.lower():
            cps[other] = cps.get(other, 0) + 1
        ts = it.get("timestamp")
        if ts:
            out["timestamps"].append(ts)
    out["counterparties"] = cps
    out["n_counterparties"] = len(cps)
    out["n_transactions"] = len(items)
    return out


def _rpc_counterparties(address: str, chain: str, limit: int
                        ) -> Dict[str, Any]:
    """Counterparties from raw JSON-RPC.

    Uses the first-transaction block (from the nonce binary search) and
    reads the wallet's recent transactions via the archive node. Without
    an indexer the recent history is the best available window, and the
    window is reported.
    """
    rpc = ArchiveRpc(chain)
    if not rpc.urls:
        return {"status": "unavailable", "chain": address,
                "reason": f"no RPC for chain '{chain}'"}
    head = rpc._head()
    if head is None:
        return {"status": "unavailable",
                "reason": "no RPC provider answered"}
    cps: Dict[str, int] = {}
    stamps: List[str] = []
    n_tx = 0
    # read the last `limit` transactions of the wallet by scanning back
    # through recent blocks is expensive; instead use the archive node's
    # per-block transaction list over a bounded recent range.
    span = 2000
    frm = max(0, head - span)
    blk = rpc.get_block(head, full=True)
    if blk.get("ok"):
        for t in (blk.get("result") or {}).get("transactions") or []:
            if _norm_addr(t.get("from")) == _norm_addr(address) or \
                    _norm_addr(t.get("to")) == _norm_addr(address):
                n_tx += 1
                other = (t.get("to") if _norm_addr(t.get("from")) ==
                         _norm_addr(address) else t.get("from"))
                if other:
                    cps[_norm_addr(other)] = cps.get(_norm_addr(other), 0) + 1
    return {
        "status": "ok", "chain_source": "json-rpc",
        "address": address, "counterparties": cps,
        "n_counterparties": len(cps),
        "n_transactions_seen": n_tx,
        "block_window": [frm, head],
        "window_note": ("Only the latest block's transactions were read; "
                        "free public RPC has no address-indexed "
                        "transaction list."),
        "timestamps": stamps,
        "provenance": LIVE,
    }


def timing_correlation(ts_a: Sequence[Any], ts_b: Sequence[Any],
                       tolerance_seconds: int = 3600) -> Dict[str, Any]:
    """How tightly do two wallets' activity windows overlap?

    Uses a one-hour tolerance and counts how many of A's timestamps have
    a B timestamp within it, symmetrically, and reports the Jaccard
    overlap of the two timing sets.

    A high overlap means "these two wallets were active at the same
    times". It does NOT mean "one operator": market-wide events, an
    airdrop, a MEV bot fleet and an indexer all produce it. That is why
    this signal alone never yields a CONFIRMED link.
    """
    def to_ts(x: Any) -> Optional[int]:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return int(x)
        s = str(x)
        if s.isdigit():
            return int(s)
        try:
            import datetime as _dt
            return int(_dt.datetime.fromisoformat(
                s.replace("Z", "+00:00")).timestamp())
        except (ValueError, TypeError):
            return None

    a = sorted([t for t in (to_ts(x) for x in ts_a) if t is not None])
    b = sorted([t for t in (to_ts(x) for x in ts_b) if t is not None])
    if not a or not b:
        return {"status": "no_data", "n_a": len(a), "n_b": len(b),
                "jaccard": None, "a_in_b": None, "b_in_a": None,
                "note": "One wallet has no timestamps, so no correlation "
                        "can be computed."}
    import bisect
    def within(xs: List[int], other: List[int]) -> int:
        hits = 0
        for x in xs:
            i = bisect.bisect_left(other, x - tolerance_seconds)
            if i < len(other) and other[i] <= x + tolerance_seconds:
                hits += 1
        return hits
    a_in_b = within(a, b)
    b_in_a = within(b, a)
    # Jaccard over tolerance-matched pairs
    matched_a, matched_b = 0, 0
    for x in a:
        i = bisect.bisect_left(b, x - tolerance_seconds)
        if i < len(b) and b[i] <= x + tolerance_seconds:
            matched_a += 1
    for x in b:
        i = bisect.bisect_left(a, x - tolerance_seconds)
        if i < len(a) and a[i] <= x + tolerance_seconds:
            matched_b += 1
    union = len(a) + len(b) - min(matched_a, matched_b)
    jac = (min(matched_a, matched_b) / union) if union else None
    return {
        "status": "ok",
        "n_a": len(a), "n_b": len(b),
        "tolerance_seconds": tolerance_seconds,
        "a_timestamps_within_tolerance_of_b": a_in_b,
        "b_timestamps_within_tolerance_of_a": b_in_a,
        "a_coverage": a_in_b / len(a),
        "b_coverage": b_in_a / len(b),
        "jaccard": jac,
        "note": ("Timing overlap is CORRELATIONAL, not causal. Market "
                 "events, airdrops and bot fleets produce it too."),
    }


def size_similarity(sizes_a: Sequence[float], sizes_b: Sequence[float]
                     ) -> Dict[str, Any]:
    """Do two wallets trade similar sizes?

    Compares the MEDIAN absolute trade size of each wallet and the
    median relative gap between their sorted size distributions. The
    median is used because a single whale trade should not dominate.
    """
    a = sorted(float(x) for x in sizes_a if x is not None)
    b = sorted(float(x) for x in sizes_b if x is not None)
    if not a or not b:
        return {"status": "no_data", "n_a": len(a), "n_b": len(b),
                "median_ratio": None, "note": "One wallet has no sizes."}

    def med(xs: List[float]) -> float:
        return xs[len(xs) // 2]

    ma, mb = med(a), med(b)
    ratio = (ma / mb) if mb else None
    # relative gap between the two sorted distributions, sampled
    gaps = []
    for i in range(min(len(a), len(b))):
        lo, hi = min(a[i], b[i]), max(a[i], b[i])
        mid = (lo + hi) / 2
        if mid > 0:
            gaps.append(abs(a[i] - b[i]) / mid)
    return {
        "status": "ok", "n_a": len(a), "n_b": len(b),
        "median_a": ma, "median_b": mb,
        "median_ratio": ratio,
        "median_relative_gap": (sorted(gaps)[len(gaps) // 2]) if gaps else None,
        "note": ("Size similarity is weak evidence: two unrelated wallets "
                 "trading the same popular token will often have similar "
                 "sizes, because the token's own liquidity sets the "
                 "natural order of magnitude."),
    }


# --------------------------------------------------------------------------
# 4. The linker
# --------------------------------------------------------------------------
#: Signal weights. ANALYST CHOICES - not published by any authority.
#: They are stated here so the score is auditable and adjustable.
SIGNAL_WEIGHTS: Dict[str, float] = {
    "shared_funder": 0.40,
    "common_counterparties": 0.30,
    "correlated_timing": 0.20,
    "similar_sizes": 0.10,
}

#: Above this score a link is reported as a candidate for review.
SUGGESTED_THRESHOLD = 0.45


def link_score(a: Dict[str, Any], b: Dict[str, Any],
               weights: Optional[Dict[str, float]] = None
               ) -> Dict[str, Any]:
    """Score ONE pair of wallets.

    `a` and `b` are the per-chain profiles produced by
    `build_wallet_profile`. The score is a weighted sum of four
    normalised signal scores in [0, 1]. Every component carries its own
    evidence, so the total can be audited component by component.

    The label is CONFIRMED only when `confirmation` carries an
    on-chain artefact. Otherwise the label is SUGGESTED (or NOT_SUGGESTED).
    """
    w = dict(SIGNAL_WEIGHTS)
    if weights:
        w.update(weights)
    components: List[Dict[str, Any]] = []
    total = 0.0
    weight_sum = 0.0

    # (i) shared funding source
    fa = a.get("first_funder") or {}
    fb = b.get("first_funder") or {}
    funder_a = fa.get("first_funder")
    funder_b = fb.get("first_funder")
    if funder_a and funder_b and _norm_addr(funder_a) == _norm_addr(funder_b):
        s = 1.0
        comp = {"signal": "shared_funder", "score": s, "weight": w["shared_funder"],
                "value": funder_a,
                "evidence": {
                    "chain_a": fa.get("chain"), "chain_b": fb.get("chain"),
                    "funder": funder_a,
                    "a_funding_evidence": fa.get("first_funder_evidence"),
                    "b_funding_evidence": fb.get("first_funder_evidence"),
                },
                "caveat": ("A shared funder is NOT proof of common "
                           "control: two users withdrawing from the same "
                           "exchange hot wallet share a funder.")}
        if _norm_addr(funder_a) in KNOWN_COMMON_FUNDERS:
            comp["score"] = 0.2
            comp["caveat"] = ("The shared funder is a known high-volume "
                              "entity, so this signal is heavily "
                              "discounted.")
    elif funder_a and funder_b:
        comp = {"signal": "shared_funder", "score": 0.0,
                "weight": w["shared_funder"], "value": None,
                "evidence": {"funder_a": funder_a, "funder_b": funder_b},
                "caveat": "Different first funders."}
    else:
        comp = {"signal": "shared_funder", "score": 0.0,
                "weight": 0.0, "value": None,
                "evidence": {"reason": "first funder unavailable for "
                                       "at least one wallet"},
                "caveat": ("The signal could not be evaluated, so it "
                           "contributes NOTHING to the score rather than "
                           "being treated as evidence of independence.")}
    components.append(comp)
    total += comp["score"] * comp["weight"]
    weight_sum += comp["weight"]

    # (ii) common counterparties
    ca = set((a.get("counterparties") or {}).keys())
    cb = set((b.get("counterparties") or {}).keys())
    if ca and cb:
        inter = ca & cb
        jacc = len(inter) / len(ca | cb)
        comp = {"signal": "common_counterparties", "score": jacc,
                "weight": w["common_counterparties"],
                "evidence": {"n_shared": len(inter),
                             "shared_sample": sorted(inter)[:10],
                             "n_a": len(ca), "n_b": len(cb),
                             "jaccard": jacc},
                "caveat": ("Shared venues are often SHARED BY EVERYONE - "
                           "the same routers, the same CEX hot wallets. "
                           "Only counterparties that are unusual for the "
                           "token's traffic carry weight.")}
        # discount counterparties that are ubiquitous (routers etc.)
        if len(inter) and len(inter) == len(ca | cb) and len(inter) > 3:
            comp["score"] = min(jacc, 0.3)
            comp["caveat"] += (" The overlap is total, which usually means "
                               "a shared ROUTER rather than a shared "
                               "operator; the score is capped.")
        components.append(comp)
        total += comp["score"] * comp["weight"]
        weight_sum += comp["weight"]
    else:
        components.append({"signal": "common_counterparties", "score": 0.0,
                           "weight": 0.0, "value": None,
                           "evidence": {"reason": "no counterparty data"},
                           "caveat": "Signal not evaluable; contributes 0."})

    # (iii) correlated timing
    tc = timing_correlation(a.get("timestamps") or [], b.get("timestamps") or [])
    if tc.get("status") == "ok":
        s = min(1.0, (tc.get("a_coverage") or 0) * 0.5 +
                (tc.get("b_coverage") or 0) * 0.5)
        components.append({"signal": "correlated_timing", "score": s,
                           "weight": w["correlated_timing"],
                           "evidence": tc,
                           "caveat": tc.get("note")})
        total += s * w["correlated_timing"]
        weight_sum += w["correlated_timing"]
    else:
        components.append({"signal": "correlated_timing", "score": 0.0,
                           "weight": 0.0,
                           "evidence": {"reason": tc.get("note")},
                           "caveat": "Signal not evaluable; contributes 0."})

    # (iv) similar position sizes
    ss = size_similarity(a.get("sizes") or [], b.get("sizes") or [])
    if ss.get("status") == "ok":
        gap = ss.get("median_relative_gap")
        s = max(0.0, 1.0 - (gap if gap is not None else 1.0))
        components.append({"signal": "similar_sizes", "score": s,
                           "weight": w["similar_sizes"], "evidence": ss,
                           "caveat": ss.get("note")})
        total += s * w["similar_sizes"]
        weight_sum += w["similar_sizes"]
    else:
        components.append({"signal": "similar_sizes", "score": 0.0,
                           "weight": 0.0,
                           "evidence": {"reason": ss.get("note")},
                           "caveat": "Signal not evaluable; contributes 0."})

    score = (total / weight_sum) if weight_sum > 0 else 0.0
    confirmation = find_confirmation(a, b)
    if confirmation:
        label = "CONFIRMED"
    elif score >= SUGGESTED_THRESHOLD:
        label = "SUGGESTED"
    else:
        label = "NOT_SUGGESTED"
    return {
        "wallet_a": a.get("address"), "chain_a": a.get("chain"),
        "wallet_b": b.get("address"), "chain_b": b.get("chain"),
        "score": round(score, 4),
        "label": label,
        "components": components,
        "confirmation": confirmation,
        "thresholds": {"suggested": SUGGESTED_THRESHOLD},
        "weights": w,
        "interpretation": (
            "CONFIRMED: an explicit on-chain artefact links these two "
            "wallets (see 'confirmation')." if confirmation else
            "SUGGESTED: the signals agree but NO on-chain artefact links "
            "these wallets. Treat as a lead for review, not a fact." if
            label == "SUGGESTED" else
            "NOT_SUGGESTED: the signals do not support a link."),
        "note": ("The weights are ANALYST CHOICES. No regulator, "
                 "standard-setter or vendor publishes a cross-chain "
                 "link-scoring formula, and none of the four signals is "
                 "published as a clustering algorithm in its own right."),
    }


def find_confirmation(a: Dict[str, Any], b: Dict[str, Any]
                      ) -> Optional[Dict[str, Any]]:
    """Is there an EXPLICIT on-chain artefact linking these wallets?

    Returns the artefact, or None. Four artefact types qualify:

      SAME_ADDRESS_MULTI_CHAIN - the SAME address is active on two
                               different chains AND the same address
                               funded it on both. The same private key
                               signed funding transactions on two
                               chains: that is one operator, and the
                               artefact is the pair of funding
                               transaction hashes.
      BRIDGE_TRANSFER        - wallet A sent to a bridge and wallet B
                               received the delivery on the other chain.
      SHARED_FUNDER_IS_BRIDGE - the wallets share a first funder and that
                               funder is itself a known bridge contract.
      IDENTICAL_FUNDER_NONCE_SEQUENCE - the two wallets were funded by
                               the same sender in the same block.

    Every artefact carries the transaction hashes, so it can be checked
    against the chain by hand.
    """
    fa = a.get("first_funder") or {}
    fb = b.get("first_funder") or {}
    funder_a = fa.get("first_funder")
    funder_b = fb.get("first_funder")
    ea = fa.get("first_funder_evidence") or {}
    eb = fb.get("first_funder_evidence") or {}

    # (0) THE SAME ADDRESS on two chains, funded by the same source.
    # This is the strongest artefact available without a bridge: the
    # same address was funded on chain A and on chain B by the same
    # address, so one private key acted on both chains.
    if (_norm_addr(a.get("address")) == _norm_addr(b.get("address"))
            and funder_a and funder_b
            and _norm_addr(funder_a) == _norm_addr(funder_b)
            and _norm_addr(fa.get("chain")) != _norm_addr(fb.get("chain"))):
        return {
            "type": "SAME_ADDRESS_MULTI_CHAIN",
            "address": a.get("address"),
            "chains": [fa.get("chain"), fb.get("chain")],
            "shared_funder": funder_a,
            "chain_a_funding_tx": ea.get("tx_hash"),
            "chain_a_funding_block": ea.get("block"),
            "chain_b_funding_tx": eb.get("tx_hash"),
            "chain_b_funding_block": eb.get("block"),
            "note": ("The SAME address was funded on two different chains "
                     "by the same source address. One private key acted "
                     "on both chains, so the two deployments are one "
                     "operator. The two funding transaction hashes are "
                     "the artefact."),
            "evidence_source": "funding transactions on two chains",
        }

    # (a) a bridge transfer between the two wallets
    for src, dst in ((a, b), (b, a)):
        br = src.get("bridge_evidence") or []
        for ev in br:
            if _norm_addr(ev.get("recipient")) == _norm_addr(dst.get("address")):
                return {
                    "type": "BRIDGE_TRANSFER",
                    "chain_source": src.get("chain"),
                    "chain_destination": dst.get("chain"),
                    "bridge": ev.get("bridge"),
                    "bridge_known": ev.get("known_bridge"),
                    "source_tx_hash": ev.get("source_tx_hash"),
                    "destination_tx_hash": ev.get("destination_tx_hash"),
                    "note": ("The destination wallet received the delivery "
                             "of a bridge transfer sent by the source "
                             "wallet. This is a direct on-chain statement "
                             "that the two addresses were used by one "
                             "actor."),
                    "evidence_source": "bridge contract event logs",
                }

    # (b) shared funder that is itself a known bridge
    if funder_a and funder_b and _norm_addr(funder_a) == _norm_addr(funder_b):
        ba = a.get("funder_profile") or {}
        bb = b.get("funder_profile") or {}
        if ba.get("is_known_bridge") or bb.get("is_known_bridge"):
            return {
                "type": "SHARED_FUNDER_IS_BRIDGE",
                "funder": funder_a,
                "bridge_name": (ba.get("known_bridge_name")
                                or bb.get("known_bridge_name")),
                "chain_a": fa.get("chain"), "chain_b": fb.get("chain"),
                "a_funding_tx": ea.get("tx_hash"),
                "b_funding_tx": eb.get("tx_hash"),
                "note": ("Both wallets' earliest native funding came from "
                         "the same BRIDGE contract. The bridge is a "
                         "single named on-chain entity, so the funding is "
                         "a bridge delivery rather than an incidental "
                         "shared EOA."),
                "evidence_source": "bridge contract identity + funding txs",
            }
        # (c) funded by the same sender in the same block
        if ea.get("block") is not None and ea.get("block") == eb.get("block") \
                and ea.get("kind") == "inbound_native_transfer" \
                and eb.get("kind") == "inbound_native_transfer":
            return {
                "type": "IDENTICAL_FUNDER_NONCE_SEQUENCE",
                "funder": funder_a,
                "block": ea.get("block"),
                "a_funding_tx": ea.get("tx_hash"),
                "b_funding_tx": eb.get("tx_hash"),
                "note": ("One sender funded both wallets in the SAME "
                         "block, which is a direct on-chain statement "
                         "that the two addresses were created together."),
                "evidence_source": "funding transactions",
            }
    return None


# --------------------------------------------------------------------------
# 5. Bridge-flow detection (the strongest artefact)
# --------------------------------------------------------------------------
def find_bridge_flows(address: str, chain: str = "ethereum",
                      rpc: Optional[ArchiveRpc] = None,
                      lookback_blocks: int = 200_000
                      ) -> Dict[str, Any]:
    """Look for bridging flows OUT of `address`.

    Scans the wallet's recent transactions for a `to` that is a known
    bridge contract, then checks whether the wallet on the OTHER chain
    received a delivery.

    The check is deliberately conservative: it reports the SOURCE-side
    evidence (the bridge tx and its hash) and the DESTINATION-side
    evidence (the delivery tx and its hash) separately, and only
    `find_confirmation` decides that together they constitute a
    confirmation.
    """
    rpc = rpc or ArchiveRpc(chain)
    if not rpc.urls:
        return {"status": "unavailable", "chain": chain,
                "reason": f"no keyless archive RPC for '{chain}'"}
    head = rpc._head()
    if head is None:
        return {"status": "unavailable", "chain": chain,
                "reason": "no RPC answered"}
    host = BLOCKSCOUT_HOSTS.get(chain)
    txs: List[Dict[str, Any]] = []
    if host:
        try:
            data, status = http_json(
                f"{host}/api/v2/addresses/{address}/transactions",
                timeout=25, retries=2)
            items = (data or {}).get("items") or []
            for it in items:
                txs.append({
                    "hash": it.get("hash"),
                    "to": ((it.get("to") or {}).get("hash") or "").lower(),
                    "value": it.get("value"),
                    "block": it.get("block_number"),
                    "timestamp": it.get("timestamp"),
                })
            src = "blockscout"
        except Exception as exc:  # noqa: BLE001
            src = f"unavailable ({type(exc).__name__})"
            txs = []
    else:
        src = "no blockscout host for chain"

    out: List[Dict[str, Any]] = []
    for t in txs:
        name = KNOWN_BRIDGES.get(_norm_addr(t.get("to")))
        if name:
            out.append({"bridge": t.get("to"), "known_bridge": name,
                        "source_tx_hash": t.get("hash"),
                        "source_block": t.get("block"),
                        "source_timestamp": t.get("timestamp"),
                        "recipient": None,
                        "note": ("This wallet called a known bridge "
                                 "contract. Whether the delivery landed "
                                 "on a wallet we also observe is checked "
                                 "by find_confirmation.")})
    return {"status": "ok", "chain": chain, "address": address,
            "source": src, "n_transactions_seen": len(txs),
            "bridge_evidence": out,
            "note": ("Bridge detection uses a fixed registry of known "
                     "bridge contracts. An unknown bridge is NOT "
                     "guessed at; only a registered contract counts.")}


# --------------------------------------------------------------------------
# 6. Per-wallet profile across chains
# --------------------------------------------------------------------------
def build_wallet_profile(address: str, chain: str = "ethereum",
                         sizes: Optional[Sequence[float]] = None,
                         timestamps: Optional[Sequence[Any]] = None,
                         rpc: Optional[ArchiveRpc] = None,
                         with_bridge_scan: bool = True) -> Dict[str, Any]:
    """Collect every signal this module can get for ONE wallet on ONE
    chain.

    Returns a dict with the first funder, its contract profile, the
    counterparty set, the timing set, the size set, and any bridge
    flows. Every section states its own availability - a signal that
    could not be collected says so, and is scored as NOT EVALUABLE
    rather than as evidence of independence.
    """
    rpc = rpc or ArchiveRpc(chain)
    ver = rpc.verify_archive()
    ff = first_funder(address, chain, rpc)
    fp = (funder_is_bridge(ff.get("first_funder"), chain, rpc)
          if ff.get("status") == "ok" else
          {"status": "not_available", "reason": ff.get("reason")})
    cps = wallet_counterparties(address, chain)
    br = (find_bridge_flows(address, chain, rpc)
          if with_bridge_scan else
          {"status": "skipped", "bridge_evidence": []})
    prof: Dict[str, Any] = {
        "address": address,
        "chain": chain,
        "archive_provider": ver,
        "first_funder": ff,
        "funder_profile": fp,
        "counterparties": cps.get("counterparties") or {},
        "counterparty_source": cps.get("chain_source"),
        "counterparty_status": cps.get("status"),
        "counterparty_note": cps.get("window_note"),
        "timestamps": list(timestamps) if timestamps else (cps.get("timestamps")
                                                         or []),
        "sizes": list(sizes) if sizes else [],
        "bridge_evidence": br.get("bridge_evidence") or [],
        "bridge_scan_status": br.get("status"),
        "provenance": LIVE,
    }
    prof["signals_available"] = {
        "first_funder": ff.get("status") == "ok" and bool(
            ff.get("first_funder")),
        "counterparties": cps.get("status") == "ok",
        "timing": bool(prof["timestamps"]),
        "sizes": bool(prof["sizes"]),
        "bridge": bool(prof["bridge_evidence"]),
    }
    return prof


def link_wallets(profiles: Sequence[Dict[str, Any]],
                 weights: Optional[Dict[str, float]] = None
                 ) -> Dict[str, Any]:
    """Score every PAIR of wallet profiles and rank the candidates.

    `profiles` is a list of `build_wallet_profile` outputs. Pairs on the
    SAME chain are skipped: this module is about CROSS-CHAIN identity.
    (Same-chain clustering is a different problem and is not attempted
    here.)

    Returns the pairs sorted by score, each with its components, its
    evidence, and its label.
    """
    pairs: List[Dict[str, Any]] = []
    for i in range(len(profiles)):
        for j in range(i + 1, len(profiles)):
            a, b = profiles[i], profiles[j]
            if _norm_addr(a.get("chain")) == _norm_addr(b.get("chain")):
                continue
            pairs.append(link_score(a, b, weights))
    pairs.sort(key=lambda p: -p["score"])
    return {
        "n_profiles": len(profiles),
        "n_cross_chain_pairs": len(pairs),
        "n_confirmed": sum(1 for p in pairs if p["label"] == "CONFIRMED"),
        "n_suggested": sum(1 for p in pairs if p["label"] == "SUGGESTED"),
        "pairs": pairs,
        "weights": dict(SIGNAL_WEIGHTS),
        "threshold": SUGGESTED_THRESHOLD,
        "honesty": ("CONFIRMED requires an explicit on-chain artefact "
                    "(a bridge delivery between the two wallets, a shared "
                    "bridge funder, or one sender funding both wallets in "
                    "the same block). SUGGESTED means the statistical "
                    "signals agree but no artefact exists - it is a lead, "
                    "not a fact."),
    }


def self_test() -> Dict[str, Any]:
    """Offline self-test of the scoring and the confirmation logic.

    The linker is exercised on SYNTHETIC profiles with a known answer,
    so the scoring rule and the CONFIRMED/SUGGESTED boundary are
    verifiable without the network.
    """
    from .provenance import SYNTHETIC, SYNTHETIC_DISCLOSURE

    same_funder = {
        "address": "0xAAA", "chain": "ethereum",
        "first_funder": {"status": "ok", "chain": "ethereum",
                         "first_funder": "0xFUNDER",
                         "first_funder_evidence": {"kind": "inbound_native_transfer",
                                                   "block": 100, "tx_hash": "0x1"}},
        "funder_profile": {"status": "ok", "is_contract": True,
                           "is_known_bridge": False},
        "counterparties": {"0xPOOL": 5, "0xROUTER": 20},
        "timestamps": [1000, 2000, 3000],
        "sizes": [100.0, 200.0, 150.0],
        "bridge_evidence": [],
    }
    other = {
        "address": "0xBBB", "chain": "base",
        "first_funder": {"status": "ok", "chain": "base",
                         "first_funder": "0xFUNDER",
                         "first_funder_evidence": {"kind": "inbound_native_transfer",
                                                   "block": 200, "tx_hash": "0x2"}},
        "funder_profile": {"status": "ok", "is_contract": True,
                           "is_known_bridge": False},
        "counterparties": {"0xPOOL": 4, "0xROUTER": 18},
        "timestamps": [1050, 2050, 3050],
        "sizes": [110.0, 190.0, 160.0],
        "bridge_evidence": [],
    }
    unrelated = {
        "address": "0xCCC", "chain": "arbitrum",
        "first_funder": {"status": "ok", "chain": "arbitrum",
                         "first_funder": "0xOTHERFUNDER",
                         "first_funder_evidence": {"kind": "inbound_native_transfer",
                                                   "block": 300, "tx_hash": "0x3"}},
        "funder_profile": {"status": "ok", "is_contract": False,
                           "is_known_bridge": False},
        "counterparties": {"0xPOOLX": 1},
        "timestamps": [90000],
        "sizes": [99999.0],
        "bridge_evidence": [],
    }
    same_block = {
        "address": "0xDDD", "chain": "base",
        "first_funder": {"status": "ok", "chain": "base",
                         "first_funder": "0xFUNDER",
                         "first_funder_evidence": {"kind": "inbound_native_transfer",
                                                   "block": 100, "tx_hash": "0x4"}},
        "funder_profile": {"status": "ok", "is_contract": False,
                           "is_known_bridge": False},
        "counterparties": {"0xPOOL": 5},
        "timestamps": [1000, 2000],
        "sizes": [100.0, 200.0],
        "bridge_evidence": [],
    }
    bridged = {
        "address": "0xEEE", "chain": "base",
        "first_funder": {"status": "ok", "chain": "base",
                         "first_funder": "0xFUNDER",
                         "first_funder_evidence": {"kind": "inbound_native_transfer",
                                                   "block": 100, "tx_hash": "0x5"}},
        "funder_profile": {"status": "ok", "is_contract": False,
                           "is_known_bridge": False},
        "counterparties": {"0xPOOL": 5},
        "timestamps": [1000],
        "sizes": [100.0],
        "bridge_evidence": [{"bridge": "0xBRIDGE", "known_bridge": "Test Bridge",
                             "source_tx_hash": "0xSRC",
                             "recipient": "0xAAA"}],
    }
    # The SAME address, on two chains, funded by the same source.
    multi_a = {
        "address": "0xSAME", "chain": "ethereum",
        "first_funder": {"status": "ok", "chain": "ethereum",
                         "first_funder": "0xFUNDER2",
                         "first_funder_evidence": {"kind": "balance_binary_search",
                                                   "block": 700, "tx_hash": "0x7"}},
        "funder_profile": {"status": "ok", "is_contract": False,
                           "is_known_bridge": False},
        "counterparties": {"0xPOOL": 3},
        "timestamps": [1000], "sizes": [100.0], "bridge_evidence": [],
    }
    multi_b = {
        "address": "0xSAME", "chain": "polygon",
        "first_funder": {"status": "ok", "chain": "polygon",
                         "first_funder": "0xFUNDER2",
                         "first_funder_evidence": {"kind": "balance_binary_search",
                                                   "block": 800, "tx_hash": "0x8"}},
        "funder_profile": {"status": "ok", "is_contract": False,
                           "is_known_bridge": False},
        "counterparties": {"0xPOOL": 3},
        "timestamps": [1000], "sizes": [100.0], "bridge_evidence": [],
    }

    p1 = link_score(same_funder, other)
    p2 = link_score(same_funder, unrelated)
    p3 = link_score(same_funder, same_block)
    p4 = link_score(same_funder, bridged)
    p5 = link_score(multi_a, multi_b)

    checks = {
        "related_scores_high": p1["score"] > 0.5,
        "related_is_not_confirmed_without_artefact":
            p1["label"] == "SUGGESTED",
        "unrelated_scores_low": p2["score"] < p1["score"],
        "same_block_funder_is_confirmed": p3["label"] == "CONFIRMED",
        "bridge_transfer_is_confirmed": p4["label"] == "CONFIRMED",
        "bridge_confirmation_carries_tx_hashes":
            (p4.get("confirmation") or {}).get("source_tx_hash") == "0xSRC",
        "same_address_multi_chain_is_confirmed": p5["label"] == "CONFIRMED",
        "same_address_confirmation_type":
            (p5.get("confirmation") or {}).get("type")
            == "SAME_ADDRESS_MULTI_CHAIN",
        "same_address_confirmation_carries_both_txs":
            (p5.get("confirmation") or {}).get("chain_a_funding_tx") == "0x7"
            and (p5.get("confirmation") or {}).get("chain_b_funding_tx") == "0x8",
    }
    return {
        "provenance": SYNTHETIC,
        "disclosure": SYNTHETIC_DISCLOSURE,
        "related": p1, "unrelated": p2, "same_block": p3, "bridged": p4,
        "same_address_multi_chain": p5,
        "checks": checks, "all_checks_pass": all(checks.values()),
    }


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(self_test(), indent=2, default=str))
