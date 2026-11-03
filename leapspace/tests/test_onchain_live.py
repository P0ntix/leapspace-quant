"""Live end-to-end check of the on-chain wallet tracker."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from leapspace.onchain import (analyse_wallet, cluster_wallets, concentration_report,
                               get_asset_holders, get_balance, get_signatures,
                               get_token_accounts, WalletProfile)

# Real, publicly documented Solana addresses used only as live API probes.
ADDRS = [
    "JUP6LkbZbjS1jKKwapdHNy76zcZ3dLUZoi5QNyVTaV4",   # Jupiter v6 aggregator
    "So11111111111111111111111111111111111111112",   # wSOL mint
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",   # USDC mint
]
ADDR = ADDRS[0]

print("== signatures ==")
try:
    sigs, prov = get_signatures(ADDR, limit=5)
    print(f"  {prov.disclosure()}")
    for s in sigs[:3]:
        print(f"   sig={s.get('signature','')[:24]}... blockTime={s.get('blockTime')} err={s.get('err')}")
except Exception as e:
    print("  ERR", type(e).__name__, e)

print("\n== balance ==")
try:
    bal, p = get_balance(ADDR)
    print(f"  {p.disclosure()} -> {bal} SOL")
except Exception as e:
    print("  ERR", type(e).__name__, e)

print("\n== token accounts ==")
try:
    accts, p = get_token_accounts(ADDR)
    print(f"  {p.disclosure()}")
    for a in accts[:3]:
        info = (a.get("account") or {}).get("data", {}).get("parsed", {}).get("info", {})
        print(f"   mint={info.get('mint')} owner={info.get('owner')}")
except Exception as e:
    print("  ERR", type(e).__name__, e)

print("\n== wallet profile (10 txs) ==")
try:
    prof = analyse_wallet(ADDR, tx_limit=10)
    d = prof.to_dict()
    for k in ("address", "n_signatures", "n_transactions_fetched",
              "n_failed_transactions", "unique_counterparties",
              "unique_token_mints", "native_outflow_sol", "native_inflow_sol"):
        print(f"  {k} = {d[k]}")
    print(f"  top_counterparties = {d['top_counterparties'][:3]}")
    print(f"  loops = {len(d['loop_transactions'])}")
    print(f"  self_trades = {len(d['self_trades'])}")
    if d["warnings"]:
        print(f"  warnings = {d['warnings']}")
except Exception as e:
    print("  ERR", type(e).__name__, e)

print("\n== concentration report (USDC mint) ==")
try:
    rep, provs = concentration_report("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    print(f"  accounts_covered={rep['accounts_covered']}")
    print(f"  top1_pct={rep['top1_pct_of_covered']} top10_pct={rep['top10_pct_of_covered']}")
    print(f"  read: {rep['structural_risk_read']}")
except Exception as e:
    print("  ERR", type(e).__name__, e)

print("\n== clustering ==")
try:
    ws = [analyse_wallet(a, tx_limit=4) for a in
          ["5tzFkiKscXHK5MSCGfPXu6gT9sJNbbkPkvS7Tx2G2WsX",
           "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"]]
    cl = cluster_wallets(ws)
    print(f"  wallets={cl['n_wallets']} clusters={cl['n_clusters']}")
except Exception as e:
    print("  ERR", type(e).__name__, e)
