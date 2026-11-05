"""Collect the memecoin whale wallets and their positions.

WHERE THIS WRITES
    `ELFA_STORAGE_ROOT` (default: the user's storage directory), under
    a directory that is EXPLICITLY NOT the Elfa data:

        <root>/non_elfa_data/

    because the user asked for the Elfa-collected data and this
    data to be SEPARATE, and to be clear about where each came from.

THE PIPELINE
    1. UNIVERSE     the top memecoin pairs per chain, from DexScreener.
    2. HOLDERS      the holder set per memecoin, reconstructed from
                    Transfer logs over a free public RPC (EVM) or from
                    the Solana RPC's token accounts.
    3. CLASSIFY     each holder: person/organisation, exchange,
                    bridge, venue, or unknown - from behaviour and
                    structure, with the evidence recorded.
    4. TRADES       the FULL token history of every person/organisation
                    wallet.
    5. PRICES       each transfer priced from DeFiLlama's coins API at
                    the day it happened.
    6. POSITIONS    buys and sells with dates, amounts and prices; net
                    holding, cost basis, realised P&L.
    7. WHITELIST    the wallet list, with every position attached.

NO ELFA. The user asked for free sources only and explicitly not
Elfa for this task, so nothing in this pipeline calls api.elfa.ai.
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from leapspace.elfa import DEFAULT_STORAGE_ROOT  # noqa: E402
from leapspace.holders import (  # noqa: E402
    evm_holder_composition, solana_holder_composition,
)
from leapspace.whalewalls import (  # noqa: E402
    CHAIN_IDS, CHAINS, build_positions, build_universe,
    classify_wallet, wallet_trades_evm, wallet_trades_solana,
)

OUT_SUBDIR = "non_elfa_data"


def _w(path: str, rows: List[Dict[str, Any]]) -> int:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, default=str) + "\n")
    return len(rows)


def collect(root: str,
            per_chain: int = 6,
            chains: Tuple[str, ...] = ("ethereum", "solana", "base"),
            max_wallets: int = 12,
            verbose: bool = True) -> Dict[str, Any]:
    out = os.path.join(root, OUT_SUBDIR)
    os.makedirs(out, exist_ok=True)
    manifest: Dict[str, Any] = {
        "title": "Memecoin whale wallets - persons and organisations",
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elfa_used": False,
        "elfa_note": ("the user asked for free sources only and NOT "
                      "Elfa for this task, so nothing here calls "
                      "api.elfa.ai. This directory is separate from the "
                      "Elfa data by request."),
        "sources": {
            "universe": "DexScreener ranked pairs (free, no key)",
            "holders_evm": ("leapspace/holders.py evm_holder_composition "
                            "- ERC-20 holders reconstructed from Transfer "
                            "logs over a free public RPC"),
            "holders_solana": ("leapspace/holders.py "
                               "solana_holder_composition - token ACCOUNTS "
                               "resolved to the owning WALLET"),
            "trades_evm": "Etherscan V2 account/tokentx (free tier)",
            "trades_solana": ("Solana RPC getSignaturesForAddress + "
                              "getTransaction, parsed"),
            "prices": ("DeFiLlama coins.llama.fi - price at a timestamp, "
                       "and decimals, on every chain"),
        },
        "datasets": {},
    }

    # ---- 1. the universe ---------------------------------------------
    print("== 1. the memecoin universe ==", flush=True)
    universe = build_universe(per_chain=per_chain, chains=chains,
                              verbose=verbose)
    upath = os.path.join(out, "universe", "memecoins.jsonl")
    n = _w(upath, [u.to_dict() for u in universe])
    manifest["datasets"]["universe"] = {
        "file": os.path.relpath(upath, root), "rows": n,
        "chains": list(chains)}
    print(f"  {n} memecoins across {len(chains)} chains", flush=True)

    # ---- 2. the holders ----------------------------------------------
    print("\n== 2. the holder sets ==", flush=True)
    holder_rows: List[Dict[str, Any]] = []
    for u in universe:
        try:
            if u.chain == "solana":
                comp = solana_holder_composition(CHAINS["solana"]["rpc"],
                                                 u.address, top_n=30)
            else:
                comp = evm_holder_composition(CHAINS[u.chain]["rpc"],
                                              u.address, top_n=30)
        except Exception as exc:  # noqa: BLE001
            if verbose:
                print(f"  {u.chain}/{u.symbol}: holders failed "
                      f"({type(exc).__name__})", flush=True)
            continue
        holders = comp.get("holders") or comp.get("top") or []
        for h in holders:
            holder_rows.append({
                "chain": u.chain, "token": u.address,
                "token_symbol": u.symbol, "dex": u.dex,
                "wallet": h.get("address"),
                "amount": h.get("amount"),
                "pct": h.get("pct") or h.get("percent"),
                "source": ("solana/rpc:getTokenLargestAccounts"
                           if u.chain == "solana"
                           else "evm_rpc:eth_getLogs(Transfer)"),
                "source_note": ("the holder set is reconstructed over the "
                                "scanned block range, which is reported "
                                "by the holders module - it is not a "
                                "global snapshot"),
            })
        if verbose:
            print(f"  {u.chain}/{u.symbol}: {len(holders)} holders",
                  flush=True)
        time.sleep(0.4)
    hpath = os.path.join(out, "holders", "memecoin_holders.jsonl")
    n = _w(hpath, holder_rows)
    manifest["datasets"]["holders"] = {
        "file": os.path.relpath(hpath, root), "rows": n}
    print(f"  {n} holder records", flush=True)

    # ---- 3. the candidates -------------------------------------------
    # One candidate per wallet, with the tokens it holds.
    cand: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for h in holder_rows:
        w = h.get("wallet")
        if not w:
            continue
        k = (h["chain"], w)
        c = cand.setdefault(k, {"chain": h["chain"], "address": w,
                                "tokens": {}, "count": 0})
        c["count"] += 1
        c["tokens"][h["token"]] = {
            "symbol": h.get("token_symbol"), "amount": h.get("amount"),
            "pct": h.get("pct")}
    # Rank by how many DIFFERENT memecoins the wallet appears in.
    ranked = sorted(cand.values(), key=lambda c: (-c["count"], c["address"]))
    print(f"\n== 3. {len(ranked)} candidate wallets, ranked by the "
          f"number of different memecoins ==", flush=True)

    # ---- 4. classify, then pull the full history for the operators ---
    print("\n== 4. classifying and pulling the trade history ==", flush=True)
    classified: List[Dict[str, Any]] = []
    wallet_rows: List[Dict[str, Any]] = []
    position_rows: List[Dict[str, Any]] = []
    seen_wallets = 0
    for c in ranked:
        if seen_wallets >= max_wallets:
            break
        chain = c["chain"]
        mints = list(c["tokens"].keys())
        # The behavioural evidence needs the wallet's own history.
        try:
            if chain == "solana":
                transfers = wallet_trades_solana(c["address"],
                                                  mints=mints)
            else:
                transfers = wallet_trades_evm(
                    c["address"], CHAIN_IDS.get(chain, 1), max_records=3000)
        except Exception as exc:  # noqa: BLE001
            if verbose:
                print(f"  {c['address'][:12]}: history failed "
                      f"({type(exc).__name__})", flush=True)
            continue
        if not transfers:
            continue
        seen_wallets += 1
        holdings = [{"token": t, "amount": v.get("amount"),
                     "symbol": v.get("symbol")}
                    for t, v in c["tokens"].items()]
        verdict = classify_wallet(
            c["address"], chain, holdings, transfers,
            created_tokens=0, deployed_contracts=0)
        classified.append({**c, "tokens": c["tokens"], **verdict,
                           "n_transfers": len(transfers)})
        wallet_rows.extend(transfers)
        if verdict["role"] == "person_org":
            positions = build_positions(transfers, chain)
            for p in positions:
                position_rows.append({"address": c["address"],
                                       "chain": chain, **p})
            if verbose:
                print(f"  {chain} {c['address'][:14]}... -> "
                      f"PERSON_ORG ({len(positions)} positions)", flush=True)
        else:
            if verbose:
                print(f"  {chain} {c['address'][:14]}... -> "
                      f"{verdict['role']}", flush=True)
        time.sleep(0.3)

    cpath = os.path.join(out, "wallets", "classified_wallets.jsonl")
    n = _w(cpath, classified)
    manifest["datasets"]["classified_wallets"] = {
        "file": os.path.relpath(cpath, root), "rows": n,
        "note": ("every wallet carries its ROLE and the EVIDENCE for it; "
                 "a verdict without evidence is not in this file")}
    tpath = os.path.join(out, "wallets", "wallet_trades.jsonl")
    n = _w(tpath, wallet_rows)
    manifest["datasets"]["wallet_trades"] = {
        "file": os.path.relpath(tpath, root), "rows": n}
    ppath = os.path.join(out, "wallets", "whitelist_positions.jsonl")
    n = _w(ppath, position_rows)
    manifest["datasets"]["whitelist_positions"] = {
        "file": os.path.relpath(ppath, root), "rows": n,
        "note": ("one row per (wallet, token) with EVERY buy and every "
                 "sell: date, amount, price and notional")}

    # ---- 5. the whitelist --------------------------------------------
    wl: List[Dict[str, Any]] = []
    for c in classified:
        if c["role"] != "person_org":
            continue
        mine = [p for p in position_rows if p["address"] == c["address"]]
        wl.append({
            "address": c["address"],
            "chain": c["chain"],
            "label": c.get("label"),
            "confidence": c.get("confidence"),
            "evidence": c.get("evidence"),
            "n_memecoins_held": c["count"],
            "tokens": c["tokens"],
            "n_transfers": c.get("n_transfers"),
            "total_cost_basis_usd": round(sum(
                p.get("cost_basis_usd") or 0 for p in mine), 2),
            "total_realised_pnl_usd": round(sum(
                p.get("realised_pnl_usd") or 0 for p in mine), 2),
            "positions": mine,
        })
    wl.sort(key=lambda w: -w["total_cost_basis_usd"])
    wpath = os.path.join(out, "whitelist.json")
    with open(wpath, "w", encoding="utf-8") as fh:
        json.dump({"generated_at": manifest["collected_at"],
                   "note": ("the whitelist of wallets judged to belong to a "
                            "PERSON or an ORGANISATION, with every "
                            "memecoin position attached"),
                   "wallets": wl}, fh, indent=2, default=str)
    manifest["datasets"]["whitelist"] = {
        "file": os.path.relpath(wpath, root),
        "wallets": len(wl),
        "note": "the deliverable: wallets plus their full position history"}

    manifest["totals"] = {
        "memecoins": len(universe),
        "holder_records": len(holder_rows),
        "wallets_examined": seen_wallets,
        "wallets_person_org": len(wl),
        "trades": len(wallet_rows),
        "position_rows": len(position_rows),
    }
    mp = os.path.join(out, "manifest.json")
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, default=str)
    print(f"\ndone: {manifest['totals']}", flush=True)
    print(f"manifest: {mp}", flush=True)
    return manifest


def main() -> int:
    root = os.environ.get("ELFA_STORAGE_ROOT", DEFAULT_STORAGE_ROOT)
    per_chain = int(os.environ.get("WHALE_PER_CHAIN", "6"))
    max_wallets = int(os.environ.get("WHALE_MAX_WALLETS", "12"))
    chains = tuple(os.environ.get("WHALE_CHAINS",
                                  "ethereum,solana,base").split(","))
    print(f"memecoin whale collection -> {os.path.join(root, OUT_SUBDIR)}",
          flush=True)
    collect(root, per_chain=per_chain, chains=chains,
            max_wallets=max_wallets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
