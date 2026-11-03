"""Fetch live priced trades for a handful of wallets and CACHE them.

The package's own artefact reports/pepe_priced_edge.json carries only
COUNTS and verdicts - it has no trade lists - so a cross-check on real
trades has to go back to the live sources.

This script is the ONE-TIME fetcher. It writes reports/crosscheck_trades.json,
and the cross-check test reads that cache, so the test is reproducible
offline afterwards.

Run:  python reports/fetch_crosscheck_trades.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from leapspace.memecoinscan import memecoin_universe, wallet_memecoin_profile
from leapspace.priced import price_wallet_positions, build_gate_trades, \
    fifo_closed_trades

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "reports", "crosscheck_trades.json")

# Wallets the package's own artefact screened (reports/pepe_priced_edge.json).
# These are REAL wallets with REAL on-chain history, so the cross-check runs
# on real data rather than a toy.
WALLETS = [
    "0x3f9a8345729eA842708E080e238C92731e5699b8",   # 20 closed trades in the artefact
    "0xaDFffc33cdC9970349CBcEa3D73Ec343d6ed116D",   # 13 closed
    "0xEd0203625D3Ef97f8f52AaaD9EAabacE4418cAF3",   # 18 closed
    "0xa5F7f1dCE2D1E4c59A28668c51355CDa047D1459",   # 13 closed
    "0x442689F3F26cBcCc2E288DaEa986b9d67346149a",   # 16 closed
    "0xd4Bb423838a66345f5D6860437Cef53e540B5f13",   # 5 closed
]


def main() -> int:
    t0 = time.time()
    print("[1/3] live memecoin universe ...", flush=True)
    uni = memecoin_universe()
    print(f"      {uni['n']} tokens, {len(uni.get('gaps') or [])} gaps, "
          f"{time.time() - t0:.1f}s", flush=True)

    def one(addr: str) -> dict:
        t = time.time()
        rec = {"address": addr}
        prof = wallet_memecoin_profile(addr, uni, chain="ethereum",
                                       max_items=400)
        rec["profile_status"] = prof.get("status")
        rec["n_meme_tokens_bought"] = prof.get("n_meme_tokens_bought")
        rec["n_meme_tokens_closed"] = prof.get("n_meme_tokens_closed")
        if prof.get("status") != "ok":
            rec["reason"] = str(prof.get("reason"))[:200]
            rec["seconds"] = round(time.time() - t, 1)
            print(f"      {addr} profile={prof.get('status')} "
                  f"({rec['seconds']}s)", flush=True)
            return rec
        priced = price_wallet_positions(prof, chain="ethereum", method="auto")
        rec["n_trades_priced"] = priced.get("n_trades")
        rec["n_unpriced"] = priced.get("n_unpriced")
        rec["unpriced_reasons"] = priced.get("unpriced_reasons")
        raw = priced.get("trades") or []
        rec["priced_trades"] = raw
        rec["closed_trades"] = fifo_closed_trades(raw)
        rec["gate_trades"] = build_gate_trades(raw)
        rec["seconds"] = round(time.time() - t, 1)
        print(f"      {addr} priced={rec['n_trades_priced']} "
              f"closed={len(rec['closed_trades'])} "
              f"gate={len(rec['gate_trades'])} ({rec['seconds']}s)", flush=True)
        return rec

    print(f"[2/3] fetching {len(WALLETS)} wallets ...", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        recs = list(pool.map(one, WALLETS))

    print("[3/3] writing cache ...", flush=True)
    blob = {
        "provenance": {
            "source": ("leapspace.memecoinscan.wallet_memecoin_profile + "
                       "leapspace.priced.price_wallet_positions, LIVE"),
            "universe": {"n": uni.get("n"),
                         "tokens": [{"symbol": x.get("symbol"),
                                     "address": x.get("address"),
                                     "market_cap": x.get("market_cap")}
                                    for x in uni.get("tokens") or []]},
            "fetched_at_epoch": int(time.time()),
            "note": ("Cached so the cross-check test is reproducible offline. "
                     "Regenerate with reports/fetch_crosscheck_trades.py."),
        },
        "wallets": recs,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(blob, fh, indent=1, default=str)
    print(f"      wrote {OUT} "
          f"({os.path.getsize(OUT):,} bytes) in {time.time() - t0:.1f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
