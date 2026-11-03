"""STEP 1c - CoinGecko per-coin detail for the top-40 meme tokens, patiently.

The task asks for /coins/{id} on the top ~40 tokens to read the per-token
chain field. Two facts found by probing this host:

  1. The field is called `platforms` (a {chain_id: address} map), with
     `detail_platforms` alongside it. There is NO `chains` field on
     /coins/{id}. The bulk endpoint /coins/list?include_platform=true
     carries the SAME `platforms` map for every coin in one call.
  2. CoinGecko's free tier 429s aggressively; the honest behaviour is to
     pace the calls, record the real status per coin, and fall back to the
     bulk map for anything that stays rate-limited.

Resumable: each coin's response is cached under step1_cg_coin_<id>.json.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from livehttp import CACHE_DIR, fetch_json  # noqa: E402

CG_BASE = "https://api.coingecko.com/api/v3"
LOG_PATH = os.path.join(CACHE_DIR, "step1c_progress.log")
BUNDLE = os.path.join(CACHE_DIR, "step1_bundle.json")
OUT = os.path.join(CACHE_DIR, "step1_coin_detail.json")

PACE = float(os.environ.get("CG_PACE", "9"))
MAX_ROUNDS = int(os.environ.get("CG_ROUNDS", "4"))


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


with open(BUNDLE, "r", encoding="utf-8") as fh:
    B = json.load(fh)

meme = B.get("meme_markets") or []
top40 = sorted([x for x in meme if isinstance(x, dict)],
                key=lambda x: float(x.get("market_cap") or 0), reverse=True)[:40]
ids = [x["id"] for x in top40]
log(f"top-{len(ids)} meme tokens: {ids[:8]} ...")

detail: dict[str, dict] = {}
status: dict[str, str] = {}
for rnd in range(MAX_ROUNDS):
    todo = [c for c in ids if c not in detail]
    if not todo:
        break
    log(f"round {rnd + 1}/{MAX_ROUNDS}: {len(todo)} to fetch")
    for i, cid in enumerate(todo, 1):
        nm = f"cg_coin_{cid}"
        path = os.path.join(CACHE_DIR, f"step1_{nm}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    blob = json.load(fh)
                if blob.get("status") == 200 and isinstance(blob.get("data"), dict):
                    d = blob["data"]
                    detail[cid] = {
                        "id": d.get("id"),
                        "asset_platform_id": d.get("asset_platform_id"),
                        "platforms": d.get("platforms"),
                        "detail_platforms": list(
                            (d.get("detail_platforms") or {}).keys()),
                    }
                    status[cid] = f"HTTP 200 (cached {blob.get('fetched_at')})"
                    continue
            except (OSError, ValueError):
                pass
        u = (f"{CG_BASE}/coins/{cid}?localization=false&tickers=false"
             "&market_data=false&community_data=false&developer_data=false"
             "&sparkline=false")
        d, r = fetch_json(nm, u, retries=0, retry_429=0)
        status[cid] = (f"HTTP {r.status}" if r.status is not None
                       else f"ERROR {r.error}")
        if isinstance(d, dict) and "platforms" in d:
            detail[cid] = {
                "id": d.get("id"),
                "asset_platform_id": d.get("asset_platform_id"),
                "platforms": d.get("platforms"),
                "detail_platforms": list((d.get("detail_platforms") or {}).keys()),
            }
        if i % 10 == 0:
            log(f"    {i}/{len(todo)} ok={len(detail)} "
                f"last={cid} {status.get(cid)}")
        time.sleep(PACE)
    log(f"round {rnd + 1} done: detail={len(detail)}/{len(ids)}")
    if len(detail) >= len(ids):
        break
    time.sleep(30)

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"detail": detail, "status": status,
               "sample_size": len(ids),
               "sample_ids": ids,
               "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              fh, indent=1, default=str)
log(f"SAVED {OUT} detail={len(detail)}/{len(ids)}")
log("DONE")
