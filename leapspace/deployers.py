"""Deployer discovery: derive token deployers from on-chain data.

The operator brief's anti-insider filter needs to know which addresses are
token deployers, so it can exclude wallets funded by them. The operator
chose to DERIVE the deployers from on-chain data rather than hand-maintain
a list, and to seed the registry from the derived values.

That makes the registry an AUDITABLE artefact: every entry records how it
was derived, from which token, and with what evidence (a creation
transaction hash, or a RugCheck creator field), so a finding can be
traced back to the chain.

Two families, two methods:

* EVM (Ethereum / Base / BSC / Arbitrum) — the deployer is the `from`
  address of the contract-creation transaction. Found by binary-searching
  the block height for the first block where `eth_getCode` returns
  non-empty, then scanning that block's transactions for the creation tx.
* Solana — the deployer is the signer of the mint's first transaction.
  Cross-checked against RugCheck's `creator` field when available.

Every function returns the evidence alongside the address. If a deployer
cannot be determined, the function says so; it never guesses.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from .models import CHAINS, FAMILY_EVM, now_ts
from .provenance import read_json, write_json

REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "state", "deployer_registry.json")

# ERC-20 Transfer topic0.
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


# --------------------------------------------------------------------------
# EVM: contract creator
# --------------------------------------------------------------------------


def find_evm_contract_creator(chain: str, address: str,
                              max_calls: int = 60) -> Dict[str, Any]:
    """Find the address that deployed an EVM contract.

    Binary-searches the block height for the first block where the contract
    has code, then scans that block for the creation transaction.

    Returns a dict with `creator`, `creation_block`, `tx_hash`,
    `method` and `evidence`. `creator` is None when it could not be
    determined - never a guess. A host that refuses the call (403, rate
    limit) is recorded in `evidence`, not raised: a discovery routine must
    degrade, not abort the whole sweep.
    """
    from .chains import EVMClient

    if chain not in CHAINS or CHAINS[chain].family != FAMILY_EVM:
        return {"creator": None, "chain": chain, "address": address,
                "method": "evm_binary_search",
                "evidence": f"chain {chain} is not an EVM chain",
                "provenance": "LIVE"}
    try:
        client = EVMClient(chain)
        calls = {"n": 0}
        errors: List[str] = []

        def has_code(block: int):
            """True = code, False = no code, None = the CALL FAILED.

            A failed call is NOT 'no code': treating it as such biases the
            binary search and yields a confident-looking but wrong
            creation block. An error aborts the search instead.
            """
            calls["n"] += 1
            try:
                code = client.get_code(address, block)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"block {block}: {type(exc).__name__}")
                return None
            return bool(code and code not in ("0x", "0x0"))

        try:
            latest = client.block_number()
        except Exception as exc:  # noqa: BLE001
            return {"creator": None, "chain": chain, "address": address,
                    "method": "evm_binary_search",
                    "evidence": f"block_number failed: {exc}",
                    "provenance": "LIVE"}

        lo, hi = 0, latest
        at_latest = has_code(hi)
        if at_latest is None:
            return {"creator": None, "chain": chain, "address": address,
                    "method": "evm_binary_search",
                    "evidence": ("the host refused eth_getCode at the latest "
                                 f"block ({len(errors)} error(s)); the "
                                 "creation block cannot be determined"),
                    "provenance": "LIVE"}
        if not at_latest:
            return {"creator": None, "chain": chain, "address": address,
                    "method": "evm_binary_search",
                    "evidence": "no code at the latest block - the address "
                                "is not a contract",
                    "provenance": "LIVE"}

        aborted = False
        while lo < hi:
            mid = (lo + hi) // 2
            got = has_code(mid)
            if got is None:
                # An errored call tells us nothing about where the code
                # appeared. Aborting is honest; guessing is not.
                aborted = True
                break
            if got:
                hi = mid
            else:
                lo = mid + 1
            if calls["n"] >= max_calls:
                aborted = True
                break
        if aborted:
            return {"creator": None, "chain": chain, "address": address,
                    "method": "evm_binary_search",
                    "evidence": (f"the binary search was ABORTED after "
                                 f"{calls['n']} call(s) because the host "
                                 f"refused {len(errors)} of them; a "
                                 f"creation block is NOT reported, because "
                                 f"a partial search yields a WRONG block"),
                    "rpc_calls": calls["n"],
                    "provenance": "LIVE"}
        creation_block = lo

        creator, tx_hash = _scan_block_for_creation(client, creation_block,
                                                      address)
        return {
            "creator": creator,
            "chain": chain,
            "address": address,
            "creation_block": creation_block,
            "tx_hash": tx_hash,
            "method": "evm_binary_search",
            "evidence": (f"first block with code={creation_block}; "
                         f"creation tx={tx_hash}" if creator else
                         f"first block with code={creation_block}; creation "
                         f"tx not found in that block"
                         + (f"; {len(errors)} call error(s)" if errors else "")),
            "rpc_calls": calls["n"],
            "provenance": "LIVE",
        }
    except Exception as exc:  # noqa: BLE001
        return {"creator": None, "chain": chain, "address": address,
                "method": "evm_binary_search",
                "evidence": f"{type(exc).__name__}: {exc}",
                "provenance": "LIVE"}


def _scan_block_for_creation(client, block: int, address: str
                              ) -> Tuple[Optional[str], Optional[str]]:
    """Find the tx in `block` that created `address`."""
    try:
        blk = client.get_block_by_number(block, full=True)
    except Exception:  # noqa: BLE001
        return None, None
    if not blk:
        return None, None
    hashes = blk.get("transactions") or []
    if hashes and isinstance(hashes[0], str):
        # Full=false gives hashes only; fetch each until we find the match.
        for h in hashes:
            try:
                tx = client.get_transaction(h)
            except Exception:  # noqa: BLE001
                continue
            if not tx:
                continue
            if (tx.get("to") in (None, "", "0x")
                    and (tx.get("contractAddress") or "").lower()
                    == address.lower()):
                return tx.get("from"), h
        return None, None
    # Full=true gives objects inline.
    for tx in hashes:
        if (tx.get("to") in (None, "", "0x")
                and (tx.get("contractAddress") or "").lower() == address.lower()):
            return tx.get("from"), tx.get("hash")
    return None, None


# --------------------------------------------------------------------------
# Solana: mint creator
# --------------------------------------------------------------------------


def find_solana_mint_creator(mint: str,
                             use_rugcheck: bool = True) -> Dict[str, Any]:
    """Find the address that created a Solana mint.

    Primary: RugCheck's `creator` field (a real third-party index of the
    same fact). Cross-check: the signer of the mint's OLDEST transaction,
    found by paging `getSignaturesForAddress` backwards.

    Returns the creator, the method that produced it, and the evidence.
    """
    out: Dict[str, Any] = {"creator": None, "chain": "solana", "address": mint,
                           "method": "solana_mint_creator", "provenance": "LIVE",
                           "evidence": "", "cross_check": None}

    if use_rugcheck:
        try:
            rep = _rugcheck_report(mint)
            creator = (rep or {}).get("creator")
            if creator:
                out["creator"] = creator
                out["method"] = "rugcheck_creator"
                out["evidence"] = f"RugCheck report creator field (mint {mint})"
        except Exception as exc:  # noqa: BLE001
            out["evidence"] = f"rugcheck unavailable: {exc}"

    # On-chain cross-check.
    try:
        from .chains import SolanaClient
        client = SolanaClient("solana")
        oldest = _oldest_signature(client, mint)
        if oldest:
            tx = client.get_transaction(oldest)
            signers = _first_external_signer(tx, mint)
            if signers:
                out["cross_check"] = signers
                if not out["creator"]:
                    out["creator"] = signers
                    out["method"] = "solana_first_tx_signer"
                    out["evidence"] = (f"signer of the mint's oldest "
                                       f"transaction {oldest}")
                elif signers.lower() != str(out["creator"]).lower():
                    out["evidence"] += (f" | MISMATCH: oldest-tx signer "
                                        f"{signers} differs from the RugCheck "
                                        f"creator {out['creator']}")
                    out["mismatch"] = True
                else:
                    out["evidence"] += (" | cross-check agrees with the "
                                        "RugCheck creator")
    except Exception as exc:  # noqa: BLE001
        out["evidence"] += f" | on-chain cross-check failed: {exc}"

    return out


def _rugcheck_report(mint: str) -> Optional[Dict[str, Any]]:
    from .http import http_json
    data = http_json(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report")
    return data if isinstance(data, dict) else None


def _oldest_signature(client, address: str, max_pages: int = 40
                      ) -> Optional[str]:
    """Page getSignaturesForAddress backwards to the oldest signature."""
    before = None
    last = None
    for _ in range(max_pages):
        sigs = client.get_signatures_for_address(address, limit=1000, before=before)
        if not sigs:
            break
        last = sigs[-1]
        before = last.get("signature")
        if len(sigs) < 1000:
            break
    return last.get("signature") if last else None


def _first_external_signer(tx: Optional[Dict[str, Any]], mint: str
                            ) -> Optional[str]:
    """The first signer of a transaction that is not the mint itself."""
    if not tx:
        return None
    msg = ((tx.get("transaction") or {}).get("message") or {})
    keys = ((msg.get("accountKeys") or []))
    for k in keys:
        addr = k.get("pubkey") if isinstance(k, dict) else k
        if addr and addr != mint:
            return addr
    return None


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------


def seed_registry(tokens: List[Dict[str, str]],
                  registry_path: str = REGISTRY_PATH,
                  merge: bool = True) -> Dict[str, Any]:
    """Derive deployers for `tokens` and seed the registry from them.

    `tokens` is a list of {"chain": ..., "address": ...} dicts.
    Each derived deployer is stored with its evidence so a finding can be
    traced back to the chain.

    Returns the registry: {"deployers": {address: evidence}, "updated": ts}.
    """
    reg: Dict[str, Any] = {"deployers": {}, "gaps": [], "updated": now_ts()}
    gaps: List[str] = []
    if merge:
        existing = read_json(registry_path) or {}
        for addr, ev in (existing.get("deployers") or {}).items():
            reg["deployers"][addr] = ev

    for t in tokens:
        chain = (t.get("chain") or "").lower()
        address = t.get("address") or ""
        if not chain or not address:
            continue
        try:
            if chain in CHAINS and CHAINS[chain].family == FAMILY_EVM:
                res = find_evm_contract_creator(chain, address)
            elif chain == "solana":
                res = find_solana_mint_creator(address)
            else:
                continue
        except Exception as exc:  # noqa: BLE001
            gaps.append(f"{chain}:{address}: {type(exc).__name__}: {exc}")
            continue
        creator = res.get("creator")
        if not creator:
            gaps.append(f"{chain}:{address}: no creator derived "
                        f"({res.get('evidence')})")
            continue
        key = f"{chain}:{creator}"
        reg["deployers"][key] = {
            "chain": chain,
            "address": creator,
            "token": address,
            "method": res.get("method"),
            "evidence": res.get("evidence"),
            "creation_block": res.get("creation_block"),
            "tx_hash": res.get("tx_hash"),
            "cross_check": res.get("cross_check"),
            "mismatch": res.get("mismatch", False),
            "derived_at": now_ts(),
            "provenance": "LIVE",
        }
        # Write after every finding so a later failure cannot lose
        # the deployers already derived.
        reg["gaps"] = gaps
        write_json(registry_path, reg)
    reg["gaps"] = gaps
    reg["updated"] = now_ts()
    write_json(registry_path, reg)
    return reg


def load_registry(registry_path: str = REGISTRY_PATH) -> Dict[str, Any]:
    return read_json(registry_path) or {"deployers": {}, "updated": 0}


def registry_as_addresses(registry_path: str = REGISTRY_PATH) -> List[str]:
    """The derived deployer addresses, for the profiler's insider filter."""
    reg = load_registry(registry_path)
    return sorted({v.get("address") for v in (reg.get("deployers") or {}).values()
                   if v.get("address")})


if __name__ == "__main__":
    import sys

    print("DEPLOYER DISCOVERY — derived from on-chain data")
    print()
    targets = [
        {"chain": "solana",
         "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"},  # BONK
        {"chain": "ethereum",
         "address": "0x6982508145454Ce325dDbE47a25d4ec3d2311933"},     # PEPE
        {"chain": "base",
         "address": "0x532f27101965dd16442E59d40670FaF5eBB142E4"},   # BRETT
    ]
    reg = seed_registry(targets)
    found = reg.get("deployers") or {}
    print(f"derived deployers: {len(found)}")
    for key, ev in found.items():
        print(f"  {key}")
        print(f"     method={ev.get('method')}  token={ev.get('token')}")
        print(f"     evidence={str(ev.get('evidence'))[:150]}")
        if ev.get("tx_hash"):
            print(f"     creation tx={ev['tx_hash']}")
        if ev.get("cross_check"):
            print(f"     on-chain cross-check signer={ev['cross_check']}")
        if ev.get("mismatch"):
            print("     ** MISMATCH between sources **")
    if not found:
        print("  none derived - the RPC sources did not yield a creator")
    print(f"\nregistry written to {REGISTRY_PATH}")
    sys.exit(0)
