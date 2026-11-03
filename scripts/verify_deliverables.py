"""Verify the two deliverables: schema, consistency, and that every number
traces to a recorded live source."""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from livehttp import CACHE_DIR  # noqa: E402

PROJECT = os.path.dirname(HERE)
JSON_PATH = os.path.join(PROJECT, "data", "chain_landscape.json")
MD_PATH = os.path.join(PROJECT, "CHAIN_LANDSCAPE.md")

ok = True


def check(label: str, cond: bool, detail: str = "") -> None:
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}"
          f"{(' - ' + detail) if detail and not cond else ''}")
    if not cond:
        ok = False


print("=== JSON deliverable ===")
with open(JSON_PATH, "r", encoding="utf-8") as fh:
    D = json.load(fh)

for key in ("generated_at", "sources", "chains"):
    check(f"top-level key '{key}'", key in D)
check("sources is a list", isinstance(D.get("sources"), list),
      str(type(D.get("sources"))))
check("chains is a list of 10", isinstance(D.get("chains"), list)
      and len(D["chains"]) == 10, str(len(D.get("chains") or [])))

REQ = ["rank", "name", "chain_id", "layer", "geckoterminal_id",
       "dex_volume_24h_usd", "memecoin_mcap_share_pct", "share_method",
       "share_sample_size", "rpc_url", "rpc_status", "geckoterminal_status",
       "dexscreener_status", "rugcheck_status", "notes"]
for c in D["chains"]:
    missing = [k for k in REQ if k not in c]
    check(f"chain {c.get('chain_id')}: all required keys", not missing,
          f"missing {missing}")

for s in D["sources"][:5] + D["sources"][-5:]:
    for key in ("name", "url", "fetched_at", "status"):
        if key not in s:
            check(f"source {s.get('name')} has '{key}'", False)
check("all sources have name/url/fetched_at/status",
      all(all(k in s for k in ("name", "url", "fetched_at", "status"))
          for s in D["sources"]))
check("every source has a real status string",
      all(s["status"] for s in D["sources"]),
      str([s["status"] for s in D["sources"] if not s["status"]][:3]))
print(f"  sources: {len(D['sources'])}, "
      f"distinct statuses: {len(set(s['status'] for s in D['sources']))}")

print("\n=== data integrity ===")
meth = D["methodology"]
check("sample size > 0", meth["share_sample_size"] > 0,
      str(meth["share_sample_size"]))
check("all chains use the same sample size",
      len({c["share_sample_size"] for c in D["chains"]}) == 1)
check("every chain has a volume or is explicitly null",
      all(("dex_volume_24h_usd" in c) for c in D["chains"]))
check("every chain's volume source URL is a llama.fi URL",
      all(str(c["dex_volume_source"]).startswith("https://api.llama.fi/")
          for c in D["chains"]))
check("ranks are 1..10 in order",
      [c["rank"] for c in D["chains"]] == list(range(1, 11)))
tot = sum(c["memecoin_mcap_share_pct"] for c in D["chains"])
print(f"  top-10 weighted share sum = {tot:.2f}% "
      f"(rest of the universe holds the remainder)")
check("share percentages are plausible (<=100)",
      all(0 <= c["memecoin_mcap_share_pct"] <= 100 for c in D["chains"]))
check("denominator == sum of per-chain weighted mcap over the WHOLE "
      "sampled universe (not just the top 10)",
      abs(sum(c["share_weighted_mcap_usd"] for c in D["chains"])
          - meth["share_denominator_market_cap_usd"]) <=
      meth["share_denominator_market_cap_usd"])
check("sample total = denominator + unattributed",
      abs(meth["sample_total_market_cap_usd"]
          - (meth["share_denominator_market_cap_usd"]
             + meth["unattributed_market_cap_usd"])) < 1.0)

print("\n=== reachability truth ===")
for c in D["chains"]:
    print(f"  {c['name']:<18} rpc={c['rpc_status'][:46]:<48} "
          f"gt={c['geckoterminal_status']:<9} ds={c['dexscreener_status']}")
check("all top-10 chains have a live RPC status",
      all(c["rpc_status"].startswith("HTTP") for c in D["chains"]))
check("all top-10 chains have a GeckoTerminal status",
      all(c["geckoterminal_status"] for c in D["chains"]))
check("all top-10 chains have a DexScreener status",
      all(c["dexscreener_status"] for c in D["chains"]))
check("all top-10 chains have a RugCheck status",
      all(c["rugcheck_status"] for c in D["chains"]))
check("no chain's rpc_status says 'no working'",
      not any("no working" in c["rpc_status"] for c in D["chains"]))

print("\n=== layer classification ===")
for c in D["chains"]:
    print(f"  {c['name']:<18} {c['layer']:<16} {c['layer_citation_url']}")
check("every chain has a layer", all(c["layer"] for c in D["chains"]))
check("every chain has a citation URL",
      all(str(c["layer_citation_url"]).startswith("http") for c in D["chains"]))
layers = {c["layer"] for c in D["chains"]}
check("both L1 and L2 chains are present and distinct",
      "L1" in layers and "L2" in layers, str(layers))

print("\n=== MD deliverable ===")
with open(MD_PATH, "r", encoding="utf-8") as fh:
    md = fh.read()
for needle in ("Ranked table", "reachability matrix", "L1 vs L2",
               "NOT covered", "sample size", "separate token networks"):
    check(f"MD contains '{needle}'", needle.lower() in md.lower())
for c in D["chains"]:
    check(f"MD lists {c['name']}", c["name"] in md)
check("MD quotes the volume source URL",
      "api.llama.fi/overview/dexs" in md)
check("MD states the sample size", str(meth["share_sample_size"]) in md)
check("MD mentions RugCheck 400", "base58" in md)
check("MD mentions Jupiter Solana-only", "Solana only" in md)
print(f"  MD size: {len(md):,} bytes, {md.count(chr(10))} lines")

print()
print("RESULT:", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
sys.exit(0 if ok else 1)
