"""STEP 3b - write CHAIN_LANDSCAPE.md and print the two tables to stdout."""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from livehttp import CACHE_DIR  # noqa: E402

PROJECT = os.path.dirname(HERE)
DATA = os.path.join(PROJECT, "data")
DOC_PATH = os.path.join(DATA, "chain_landscape.json")
MD_PATH = os.path.join(PROJECT, "CHAIN_LANDSCAPE.md")


def load(name, default=None):
    p = os.path.join(CACHE_DIR, name)
    if not os.path.exists(p):
        return default
    try:
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


with open(DOC_PATH, "r", encoding="utf-8") as fh:
    D = json.load(fh)
LC = load("layer_claims.json", {}) or {}
EV = load("step1_evidence.json", {}) or {}
RANK = load("step3_chains.json", {}) or {}
R2 = load("step2_results.json", {}) or {}
R2D = load("step2d_results.json", {}) or {}
R2E = load("step2e_results.json", {}) or {}

chains = D["chains"]
meth = D["methodology"]
gaps = D["coverage_gaps"]


def usd(v):
    if v is None:
        return "n/a"
    return f"${v:,.0f}"


def st(v):
    return str(v) if v else "n/a"


L = []
A = L.append

A("# Chain Landscape — Memecoin Creation & Trading Networks")
A("")
A(f"**Generated:** {D['generated_at']} (UTC)  ")
A(f"**Host:** {D['host_note']}  ")
A("**Method:** every figure below comes from a live API call made in the "
  "session that produced this file. Each URL is recorded in "
  "`data/chain_landscape.json` under `sources`.")
A("")
A("---")
A("")

# ------------------------------------------------------------------ TL;DR
A("## 1. Headline")
A("")
A(f"- **Top chain by measured DEX 24h volume:** {chains[0]['name']} "
  f"({usd(chains[0]['dex_volume_24h_usd'])})")
A(f"- **Top chain by sampled memecoin market-cap share:** "
  f"{max(chains, key=lambda c: c['memecoin_mcap_share_pct'] or 0)['name']} "
  f"({max(c['memecoin_mcap_share_pct'] or 0 for c in chains):.2f}% of the "
  f"attributed sample)")
A(f"- **Memecoin market-cap sample:** N = {meth['share_sample_size']} tokens "
  f"from the CoinGecko `meme-token` category; sample market cap "
  f"{usd(meth['sample_total_market_cap_usd'])}, of which "
  f"{usd(meth['share_denominator_market_cap_usd'])} is attributable to a "
  f"chain home and {usd(meth['unattributed_market_cap_usd'])} is not.")
A(f"- **Free-endpoint reachability:** "
  f"{sum(1 for c in chains if 'HTTP 200' in (c['rpc_status'] or ''))}"
  f"/{len(chains)} of the ranked chains have a working JSON-RPC endpoint, "
  f"{sum(1 for c in chains if (c['geckoterminal_status'] or '').startswith('HTTP 2'))}"
  f"/{len(chains)} have a working GeckoTerminal pools endpoint, and "
  f"{sum(1 for c in chains if (c['dexscreener_status'] or '').startswith('HTTP 2'))}"
  f"/{len(chains)} have a working DexScreener token-pairs endpoint.")
A("- **Ranked list ≠ working endpoints.** A chain can rank highly on volume "
  "and still have no usable free RPC. Section 5 is the independent "
  "reachability test.")
A("")

# ------------------------------------------------------------- the tables
A("## 2. Ranked table — top 10 memecoin networks")
A("")
A("Primary sort key: **measured** DefiLlama per-chain DEX 24h volume "
  "(`total24h` from `https://api.llama.fi/overview/dexs/{chain}`).")
A("")
A("`mcap share` is the **sampled** estimate and is a different measure — see "
  "§3.")
A("")
A("| # | Chain | chain id | DEX 24h volume | mcap share | sample size | "
  "layer | GeckoTerminal id |")
A("|---|-------|----------|-----------------|------------|-------------|"
  "-------|-----------------|")
for c in chains:
    A(f"| {c['rank']} | {c['name']} | `{c['chain_id']}` | "
      f"{usd(c['dex_volume_24h_usd'])} | "
      f"{c['memecoin_mcap_share_pct']:.2f}% | "
      f"{c['share_sample_size']} | {c['layer']} | "
      f"`{c['geckoterminal_id'] or '—'}` |")
A("")
A("Volume source URL per chain (all `https://api.llama.fi/overview/dexs/"
  "{chain}?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true`):")
A("")
for c in chains:
    A(f"- **{c['name']}** — {c['dex_volume_source'] or 'n/a'}")
A("")

# ------------------------------------------------------------ methodology
A("## 3. How the two rankings were computed (and why they differ)")
A("")
A("### 3.1 Ranked by measured DEX volume — the primary ranking")
A("")
A("`https://api.llama.fi/overview/dexs/{chain}?excludeTotalDataChart=true&"
  "excludeTotalDataChartBreakdown=true` returns a `total24h` field. That is a "
  "**measured** 24-hour DEX volume for the chain, taken verbatim. No estimate "
  "is involved.")
A("")
A("> **Correction to the task premise.** The task said GeckoTerminal's "
  "`/api/v2/networks` \"gives per-network 24h DEX volume\". It does not. The "
  "live response body for each network is only:")
A("> ```json")
A("> {\"id\": \"eth\", \"type\": \"network\", \"attributes\": {\"name\": "
  "\"Ethereum\", \"coingecko_asset_platform_id\": \"ethereum\"}}")
A("> ```")
A("> There is **no volume field** on that endpoint. Per-network volume is "
  "only obtainable by summing per-pool `attributes.volume_usd.h24` from "
  "`/api/v2/networks/{id}/pools`, which is a *page-limited* sum of the top "
  "pools, not the chain total. DefiLlama's per-chain `total24h` is the "
  "complete, single-number measurement, so it is used as the primary ranking "
  "key. GeckoTerminal remains in the survey as the source of the per-chain "
  "token address needed for the DexScreener probes.")
A("")
A("### 3.2 Ranked by sampled memecoin market-cap share — a different measure")
A("")
A(f"**Sample: N = {meth['share_sample_size']} tokens.** Taken from "
  "`https://api.coingecko.com/api/v3/coins/markets?category=meme-token&"
  "vs_currency=usd&per_page=100&page=1` (100 tokens returned), then the top "
  "40 by market cap.")
A("")
A("> **Correction to the task premise (2).** The task said to read the "
  "`chains` field from `/coins/{id}`. There is no `chains` field. The live "
  "payload carries `platforms` (a `{chain_id: address}` map), "
  "`detail_platforms` and `asset_platform_id`. The survey reads `platforms`.")
A("")
A("Attribution rule:")
A("")
A("1. Each token's market cap is assigned to its **home chain** "
  "(`asset_platform_id` from `/coins/{id}`). Bridged copies are therefore "
  "not double-counted.")
A("2. Where `asset_platform_id` is null but token contracts exist, the first "
  "`platforms` entry is used as the home chain.")
A("3. Native coins with **no** contract on any chain (e.g. `dogecoin`) are "
  "**unattributed** — their market cap is the chain's own native asset, not "
  "a memecoin token on a token network. "
  f"Unattributed: {usd(meth['unattributed_market_cap_usd'])} "
  f"({', '.join(u['id'] for u in meth['unattributed']) or 'none'}).")
A("")
A(f"Denominator (attributed market cap): "
  f"**{usd(meth['share_denominator_market_cap_usd'])}**. The occurrence "
  "count column in the JSON is the *unweighted* alternative the task "
  "described (each token counted once per chain it lists); it is recorded "
  "per chain as `share_occurrence_count` / `share_occurrence_pct` and is "
  "reported separately below.")
A("")
A("| Chain | weighted mcap share | occurrence count | occurrence share |")
A("|-------|---------------------|------------------|-----------------|")
for c in chains:
    A(f"| {c['name']} | {c['memecoin_mcap_share_pct']:.2f}% | "
      f"{c['share_occurrence_count']} | {c['share_occurrence_pct']:.2f}% |")
A("")
A(f"Per-coin `/coins/{{id}}` detail was fetched live for "
  f"{meth['per_coin_detail_success']}/{meth['share_sample_size']} tokens. "
  f"Rate-limited (HTTP 429) and resolved from the bulk "
  "`/coins/list?include_platform=true` map instead: "
  f"{', '.join(meth['per_coin_detail_rate_limited'].keys()) or 'none'}.")
A("")
A("**Where the two rankings disagree, and why.** Tron, NEAR and Arbitrum "
  "have real measured DEX volume but a near-zero share of the *top-40 "
  "market-cap* memecoin sample — their memecoin activity is in long-tail "
  "tokens, not in the top 40 by market cap. Conversely Base and Robinhood "
  "Chain have very large DEX volume but most of it is not memecoin flow in "
  "the sampled top-40. A chain in the top 10 by one measure can be absent "
  "from the other.")
A("")
A("Chain-native memecoin categories from "
  "`https://api.coingecko.com/api/v3/coins/categories` (each carries "
  "`market_cap`, `market_cap_change_24h` and `volume_24h`):")
A("")
A("| category id | name | market_cap | market_cap_change_24h | volume_24h |")
A("|-------------|------|------------|-----------------------|------------|")
import json as _json
_cats = load("step1_cg_categories.json") or {}
_n_meme = 0
for c in _cats:
    if isinstance(c, dict) and "meme" in ((c.get("id") or "").lower()) \
            and c.get("market_cap"):
        _n_meme += 1
        A(f"| `{c.get('id')}` | {c.get('name')} | "
          f"{usd(c.get('market_cap'))} | "
          f"{c.get('market_cap_change_24h')} | {usd(c.get('volume_24h'))} |")
A("")
A(f"({_n_meme} categories with a non-null market cap were returned out of "
  f"{len(_cats)} total CoinGecko categories. The aggregate `meme-token` "
  f"category carries `market_cap` "
  f"{usd(next((c.get('market_cap') for c in _cats if isinstance(c, dict) and c.get('id') == 'meme-token'), None))} "
  f"and `market_cap_change_24h` "
  f"{next((c.get('market_cap_change_24h') for c in _cats if isinstance(c, dict) and c.get('id') == 'meme-token'), None)}; "
  f"the chain-native sub-categories above are the per-chain slices of that "
  f"total.)")
A("")

# ------------------------------------------------------- L1 vs L2 section
A("## 4. L1 vs L2 vs appchain classification, with citations")
A("")
A("> **Ethereum L2s share the EVM execution environment but are SEPARATE "
  "token networks. They are not merged with Ethereum.** A Base ERC-20 and "
  "an Ethereum ERC-20 with the same address are different tokens on "
  "different networks; liquidity, holders and market cap do not pool. Every "
  "L2 below therefore gets its own row, its own `chain_id`, its own "
  "GeckoTerminal id and its own endpoint status. Polygon PoS and Polygon "
  "zkEVM are likewise separate networks and are not merged either.")
A("")
A("| Chain | Classification | Citation (URL fetched live) | Evidence |")
A("|-------|----------------|-----------------------------|----------|")
for c in chains:
    A(f"| {c['name']} | **{c['layer']}** | {c['layer_citation_url']} | "
      f"{c['layer_citation_note']} |")
A("")
A("### Notable classification findings")
A("")
A("- **Celo is no longer an L1.** Its own docs record that it \"ran as an "
  "independent L1 from April 2020 until March 2025, when it completed its "
  "migration to an Ethereum Layer 2 at block 31,056,500\" "
  "(https://docs.celo.org/learn/celo-l1, HTTP 200). It is classified **L2** "
  "here. Treating Celo as an L1 is a live-data error, not a judgement call.")
A("- **Polygon PoS is not an Ethereum rollup.** It is a standalone EVM "
  "sidechain with its own validator set and staking. **Polygon zkEVM** is a "
  "separate Ethereum zk-rollup network and is listed as a distinct chain in "
  "`data/chain_landscape.json`'s layer map — the two are not merged.")
A("- **Robinhood Chain is an Arbitrum-based L2**, per its own docs: \"a "
  "permissionless, Ethereum-compatible Layer-2 blockchain ... built on "
  "Arbitrum Dedicated Blockchains, a modular Layer-2 framework\" "
  "(https://docs.robinhood.com/chain/, HTTP 200).")
A("- **Hyperliquid is an L1**, per https://hyperliquid.gitbook.io/"
  "Hyperliquid-docs (HTTP 200): \"Hyperliquid is a layer one blockchain (L1) "
  "written and optimized from first principles.\" The separate HyperEVM "
  "network is not the same token network as the Hyperliquid L1.")
A("- **Shimmer has shut down.** https://shimmer.network/ (HTTP 200): "
  "\"As of September 30, 2026, Shimmer L1 and ShimmerEVM have officially "
  "stopped block production and sunsetted.\"")
A("")

# ------------------------------------------------------ reachability
A("## 5. Endpoint reachability matrix (Step 2)")
A("")
A("Every cell is the exact HTTP status returned by a live call from this "
  "host. `n/a` means no endpoint was tried for that service on that chain "
  "because the service does not cover it.")
A("")
A("| Chain | EVM/Solana JSON-RPC | RPC URL used | GeckoTerminal pools | "
  "DexScreener pairs | RugCheck |")
A("|-------|---------------------|--------------|--------------------|"
  "-------------------|----------|")
for c in chains:
    A(f"| {c['name']} | {c['rpc_status']} | "
      f"`{c['rpc_url'] or '—'}` | {c['geckoterminal_status']} | "
      f"{c['dexscreener_status']}"
      f"{' (' + str(c['dexscreener_pairs']) + ' pairs)' if c['dexscreener_pairs'] is not None else ''} | "
      f"{c['rugcheck_status']} |")
A("")
A("### 5.1 GeckoTerminal network ids are not the same as the other names")
A("")
A("GeckoTerminal ids, CoinGecko platform ids, DefiLlama slugs and RPC host "
  "slugs are four different namespaces. The resolved GT ids:")
A("")
A("| Chain id | GeckoTerminal id | GT display name |")
A("|----------|------------------|------------------|")
for c in chains:
    A(f"| `{c['chain_id']}` | `{c['geckoterminal_id'] or '—'}` | "
      f"{c['name']} |")
A("")
A("Examples of the mismatch: Ethereum is `eth` on GeckoTerminal but "
  "`ethereum` on CoinGecko and DefiLlama; Avalanche is `avax`; Polygon is "
  "`polygon_pos` (not `polygon`, and `polygon-zkevm` is a different network); "
  "Sui is `sui-network`; Zora is `zora-network`; World Chain is "
  "`world-chain`; zkSync is `zksync`; Cronos is `cro`; Harmony is `one`; "
  "Conflux is `cfx`.")
A("")

A("### 5.2 Per-chain RPC probe detail")
A("")
A("`eth_blockNumber` (or the chain's native method) POSTed to each host in "
  "turn until one returned a usable result. Failed hosts are listed with "
  "their real failure.")
A("")
_RPC_ALL = dict(R2.get("rpc") or {})
_RPC_ALL.update(R2E.get("rpc") or {})
for _extra in (load("step2g_results.json", {}) or {},
               load("step2h_results.json", {}) or {},
               load("step2i_results.json", {}) or {}):
    for _slug, _rec in (_extra or {}).items():
        if not isinstance(_rec, dict) or not _rec.get("attempts"):
            continue
        if (_RPC_ALL.get(_slug) or {}).get("reachable"):
            continue
        _RPC_ALL[_slug] = _rec
for c in chains:
    slug = c["chain_id"]
    rec = _RPC_ALL.get(slug) or {}
    att = rec.get("attempts") or []
    if not att:
        att = c.get("rpc_attempts") or []
    A(f"**{c['name']}**")
    A("")
    A("| URL | Result |")
    A("|-----|--------|")
    for a in att:
        note = (a.get("error") or a.get("jsonrpc_error")
                or a.get("body_head") or "")
        A(f"| `{a.get('url')}` | {a.get('status')} {str(note)[:90]} |")
    A("")

A("### 5.3 The Ankr and Subquery fallback patterns")
A("")
A("The task asked for Ankr and Subquery public RPC patterns as fallbacks. "
  "Both were tested explicitly:")
A("")
A("- **`https://rpc.ankr.com/{chain}`** — TLS "
  "`CERTIFICATE_VERIFY_FAILED: Hostname mismatch, certificate is not valid "
  "for 'rpc.ankr.com'` for **all 24 chains** tried (eth, base, bsc, "
  "arbitrum, polygon, optimism, avalanche, linea, scroll, zksync, blast, "
  "mantle, celo, berachain, fantom, soneium, abstract, unichain, worldchain, "
  "zora, sonic, hyperliquid, monad, solana). The certificate served for that "
  "host does not cover the hostname, so no Ankr chain is usable from this "
  "host — this is a host/CA issue, not a per-chain outage.")
A("- **`https://rpc.subquery.network/public/{chain}`** — HTTP **404** for "
  "**all 22 chains** tried (ethereum, base, bsc, arbitrum, polygon, "
  "optimism, avalanche, linea, scroll, zksync, blast, mantle, celo, "
  "berachain, fantom, soneium, abstract, unichain, worldchain, zora, sonic, "
  "hyperliquid, monad). The public path prefix no longer serves RPC.")
A("")
A("Working publicnode fallbacks that were found for the chains whose "
  "publicnode slug 404s or errors (all verified live):")
A("")
A("| Chain | publicnode slug result | Working free RPC found |")
A("|-------|-------------------------|------------------------|")
_detail = gaps.get("no_public_rpc_found_detail") or {}
_found = {
    "blast": "https://rpc.blast.io (HTTP 200)",
    "fantom": "https://rpc3.fantom.network (HTTP 200)",
    "abstract": "https://abstract.drpc.org (HTTP 200)",
    "worldchain": "https://worldchain.drpc.org (HTTP 200)",
    "zora": "https://rpc.zora.energy (HTTP 200)",
    "monad": "https://rpc.monad.xyz (HTTP 200)",
    "plasma": "https://rpc.plasma.to (HTTP 200)",
    "hyperliquid": "https://rpc.hyperliquid.xyz/evm (HTTP 200)",
    "bob": "https://bob.drpc.org (HTTP 200)",
    "harmony": "https://api.harmony.one (HTTP 200)",
    "injective": "https://injective.drpc.org (HTTP 200)",
    "near": "https://near.drpc.org (HTTP 200, `status` method)",
    "ton": "https://toncenter.com/api/v2/jsonRPC (HTTP 200, "
           "`getMasterchainInfo`)",
    "aptos": "https://fullnode.mainnet.aptoslabs.com/v1 (HTTP 200, REST)",
    "cardano": "https://api.koios.rest/api/v1/tip (HTTP 200, REST)",
    "hedera": "https://mainnet-public.mirrornode.hedera.com/api/v1/network/"
              "supply (HTTP 200, REST)",
    "sui": "https://sui-mainnet.gateway.tatum.io/graphql (HTTP 200, GraphQL "
           "`chainIdentifier`)",
    "xrpl": "https://xrpl.drpc.org (HTTP 200 on `eth_blockNumber`; its native "
            "`ledger_current` is not exposed)",
    "litecoin": "https://api.blockchair.com/litecoin/stats (HTTP 200, REST; "
                "no JSON-RPC found)",
}
_rpc_all = dict(R2.get("rpc") or {})
_rpc_all.update(R2E.get("rpc") or {})
for slug in sorted(_rpc_all):
    rec = _rpc_all[slug] or {}
    pn = None
    for a in (rec.get("attempts") or []):
        u = a.get("url") or ""
        if "publicnode.com" in u:
            pn = f"{a.get('status')} — `{u.split('//')[1].split('/')[0]}`"
            break
    if not pn:
        pn = "no publicnode host for this chain"
    fb = _found.get(slug, "**no working free RPC found**")
    A(f"| {slug} | {pn} | {fb} |")
A("")

A("### 5.4 Solana RPC hosts")
A("")
A("| URL | getSlot |")
A("|-----|---------|")
for u, rec in sorted((R2D.get("solana_all") or {}).items()):
    note = ""
    if rec.get("ok"):
        note = f"OK slot={rec.get('result')}"
    elif rec.get("jsonrpc_error"):
        note = rec["jsonrpc_error"][:120]
    A(f"| `{u}` | {rec.get('status')} {note} |")
A("")

A("### 5.5 RugCheck — Solana only")
A("")
A("| Call | URL | Status |")
A("|------|-----|--------|")
_rug = load("step2c_results.json", {}) or {}
for tag, rec in sorted((_rug.get("rugcheck") or {}).items()):
    A(f"| {tag} | `{rec.get('url')}` | {rec.get('status')} |")
A("")
A("**Conclusion:** RugCheck serves **Solana only**.")
A("")
A("- A Solana mint returns HTTP 200 on `/v1/tokens/{mint}/report/summary` "
  "and `/v1/tokens/{mint}/report`. The `report` payload carries the top "
  "holders under `topHolders` (20 entries, each with `address`, `owner`, "
  "`amount`, `pct`, `insider`).")
A("- **`/holders/top` is not a valid path.** Both `/holders/top` and "
  "`/holders` return HTTP 404 `PAGE_NOT_FOUND`. The top-holder data lives "
  "inside `/report` → `topHolders`, not on a separate holders endpoint. "
  "`/lockers` returns HTTP 401 (requires a RugCheck API token).")
A("- Every **EVM** address returns HTTP 400 "
  "`{\"error\":\"decode: base58: invalid base58 character\"}` — RugCheck "
  "base58-decodes the mint, so a `0x…` address cannot be served.")
A("- The **chain-prefixed** form `/v1/tokens/{chain}/{address}/…` returns "
  "HTTP 404 `PAGE_NOT_FOUND` for `base`, `bsc`, `ethereum` and `solana` — "
  "there is no multi-chain route on this API.")
A("")

A("### 5.6 Jupiter — Solana only")
A("")
A("| Call | URL | Status | Results |")
A("|------|-----|--------|---------|")
for tag, rec in sorted((_rug.get("jupiter") or {}).items()):
    extra = ""
    if rec.get("n_results") is not None:
        extra = f"{rec.get('n_results')} tokens"
    A(f"| {tag} | `{rec.get('url')}` | {rec.get('status')} | {extra} |")
A("")
A("**Conclusion:** Jupiter's `/tokens/v2/search` indexes **Solana only**.")
A("")
A("- `?query=pepe` → 20 results, all Solana SPL mints (base58 ids such as "
  "`PEPEqnuuCDbBC89p1u9vpnP1KQ2oj1xTcQBsjt9X55m`, many with the `pump` "
  "suffix from pump.fun).")
A("- `?query=0x1` → 20 results, all Solana SPL mints whose *names* happen to "
  "contain \"0x\"; the query is a substring match on name/symbol, not an "
  "address lookup.")
A("- `?query=<an exact Base address>` → **0 results**. Same for an exact "
  "Ethereum address and an exact BSC address.")
A("- On `?query=pepe` and `?tag=verified` (4,083 results), the count of "
  "ids beginning with `0x` was **0**. Every returned token carries "
  "`tokenProgram`/`decimals`/`usdPrice` — the Solana SPL shape. Jupiter's "
  "response has no `chainId` field, so chain cannot be read from it; the "
  "evidence is the id format and the `tokenProgram` field.")
A("")

A("## 6. What is NOT covered, and why")
A("")
A("### 6.1 Chains with no working free JSON-RPC")
A("")
A("Every chain in the surveyed set that was probed and had **no** host "
  "return a usable result:")
A("")
A("| Chain | Every host tried and its real failure |")
A("|-------|----------------------------------------|")
_detail = gaps.get("no_public_rpc_found_detail") or {}
for slug in sorted(_detail):
    attempts = _detail[slug]
    if not attempts:
        A(f"| {slug} | (no attempt recorded) |")
        continue
    parts = []
    for url, status, note in attempts:
        note = (note or "").replace("|", "/")[:70]
        parts.append(f"`{url}` → {status} {note}")
    A(f"| {slug} | {'<br>'.join(parts)} |")
A("")
A("**swellchain**, **evmos**, **sophon**, **conflux** and **dogechain** had "
  "every free host fail (publicnode/drpc 404, no other public endpoint "
  "reachable). **shimmer**'s host returns HTTP 502 and the chain has "
  "sunset (September 30, 2026). **litecoin** has no JSON-RPC at all — only "
  "a REST stats endpoint (https://api.blockchair.com/litecoin/stats, HTTP "
  "200). **xrpl** answers `eth_blockNumber` on drpc but does not expose its "
  "native `ledger_current`. These chains still appear in the landscape "
  "data with their volume and layer classification; what is missing is a "
  "usable JSON-RPC endpoint.")
A("")
A("### 6.2 Services that do not cover EVM chains at all")
A("")
A("- **RugCheck** — Solana only (§5.5). Every EVM address → HTTP 400 "
  "base58 decode error; every chain-prefixed path → HTTP 404.")
A("- **Jupiter** — Solana only (§5.6). Exact EVM address queries → 0 "
  "results; 0 of 4,083 verified tokens have a `0x` id.")
A("")
A("### 6.3 Chains in the surveyed set with zero sampled memecoin share")
A("")
A("| Chain | DEX 24h volume | Why it still ranks |")
A("|-------|-----------------|--------------------|")
for c in chains:
    if (c["share_occurrence_count"] or 0) == 0:
        why = []
        if c.get("memecoin_dex_volume_24h_usd"):
            why.append(f"memecoin DEX volume "
                       f"{usd(c['memecoin_dex_volume_24h_usd'])}")
        if c.get("defillama_launchpad_count"):
            why.append(f"{c['defillama_launchpad_count']} DefiLlama launchpads "
                       "(token-creation venues)")
        A(f"| {c['name']} | {usd(c['dex_volume_24h_usd'])} | "
          f"{'; '.join(why) or 'measured DEX volume'} |")
A("")
A("These chains have **measured** DEX volume but their memecoin activity "
  "sits in long-tail tokens below the top-40 market-cap cut. They are in "
  "the ranking because of volume, and their `memecoin_mcap_share_pct` is "
  "honestly reported as ~0 — not because memecoins are absent there.")
A("")
A("### 6.4 DexScreener returned HTTP 200 but zero pairs")
A("")
A("A `200` with an empty array means the endpoint answered and the token "
  "has no listed pair under that chain slug — it is a real answer, not a "
  "failure. The probe token is whatever GeckoTerminal's top pool for that "
  "network uses, so on a young chain it may be a wrapped-native asset that "
  "DexScreener has not indexed. Affected chains in the surveyed set: "
  + (", ".join(f"`{x}`" for x in gaps.get("dexscreener_no_pairs") or [])
     or "none") + ".")
A("")
A("### 6.5 Chains not on GeckoTerminal")
A("")
A("GeckoTerminal's network list (3 pages, 226 unique ids, all fetched "
  "live) has no entry for: "
  + ", ".join(f"`{x}`" for x in gaps["not_on_geckoterminal"]) + ". For "
  "those chains the per-network pools endpoint cannot be called at all, "
  "and because the DexScreener probe takes its token address from a "
  "GeckoTerminal pool, the DexScreener probe is skipped for them too "
  "rather than being answered with an invented address.")
A("")

A("## 7. Method notes and caveats")
A("")
A(f"1. **Sample size.** The market-cap share is estimated from "
  f"N = {meth['share_sample_size']} tokens (CoinGecko `meme-token` category, "
  f"top 40 by market cap). It is a *sample*, and it is labelled as such "
  "everywhere. It is not a census of memecoin market cap.")
A("2. **Two different rankings.** Volume rank is measured; market-cap rank "
  "is sampled. They are not interchangeable and the JSON keeps both "
  "(`dex_volume_24h_usd` vs `memecoin_mcap_share_pct` + "
  "`share_occurrence_count`).")
A("3. **Coverage bias in the sample.** CoinGecko's `meme-token` category is "
  "dominated by a handful of very large tokens; the sample's long tail is "
  "thin. Chains whose memes are numerous but small (TRON's `sunpump`, NEAR's "
  "`meme-cooking`) barely register in the top-40.")
A("4. **Volume is DEX volume, not memecoin volume.** DefiLlama's "
  "per-chain `total24h` covers *all* DEX activity on the chain. The "
  "memecoin-only slice is in `memecoin_dex_protocols_24h` / "
  "`memecoin_dex_volume_24h_usd` per chain, derived from the "
  "`breakdown24h` map of the memecoin-named protocols in "
  "`/api/v2/overview/dexs`.")
A("5. **Rate limits are real.** CoinGecko's free tier returned HTTP 429 "
  "repeatedly on this host; the per-coin sweep was paced and 1 of 40 "
  "tokens stayed rate-limited (resolved from the bulk platform map). "
  "GeckoTerminal returned HTTP 429 on some pools requests under load and "
  "HTTP 200 on retry.")
A("6. **`eth_getCode` is not the same as `eth_blockNumber`.** Both worked "
  "on ethereum, base, bsc, arbitrum, polygon, optimism and avalanche when "
  "called with an explicit `latest` block tag. Called without a block tag, "
  "publicnode treats it as an **archive** request: base and bsc returned "
  "HTTP 403 `{'code': -32602, 'message': 'Archive requests require a "
  "personal token…'}`. So `eth_blockNumber` succeeding does not mean "
  "`eth_getCode` will.")
A("7. **Re-fetching.** Raw responses are cached under `data/_raw/` and the "
  "collector scripts are resumable; delete a `step1_*.json` file to force "
  "that source to be re-fetched.")
A("")

A("## 8. Files")
A("")
A("| File | Contents |")
A("|------|----------|")
A("| `data/chain_landscape.json` | Machine-readable: `generated_at`, "
  "`sources` (name, url, fetched_at, status), `chains` (rank, name, "
  "chain_id, layer, geckoterminal_id, dex_volume_24h_usd, "
  "memecoin_mcap_share_pct, share_method, share_sample_size, rpc_url, "
  "rpc_status, geckoterminal_status, dexscreener_status, rugcheck_status, "
  "notes), plus `methodology` and `coverage_gaps`. |")
A("| `CHAIN_LANDSCAPE.md` | This document. |")
A("| `data/_raw/step1_*.json` | Raw responses to every source call. |")
A("| `scripts/` | The collector and verifier scripts that produced both "
  "files. |")
A("")

md = "\n".join(L) + "\n"
with open(MD_PATH, "w", encoding="utf-8") as fh:
    fh.write(md)
print(f"wrote {MD_PATH} ({len(md):,} bytes)")

# ---------------------------------------------------------------- stdout
print()
print("=" * 108)
print("RANKED TABLE - top 10 memecoin networks (primary sort: measured "
      "DefiLlama DEX 24h volume)")
print("=" * 108)
print(f"{'#':<3}{'Chain':<20}{'chain id':<14}{'DEX 24h vol':>16}"
      f"{'mcap share':>12}{'N':>5}{'occ':>5}  {'layer':<15}{'GT id'}")
for c in chains:
    print(f"{c['rank']:<3}{c['name']:<20}{c['chain_id']:<14}"
          f"{usd(c['dex_volume_24h_usd']):>16}"
          f"{(str(c['memecoin_mcap_share_pct']) + '%'):>12}"
          f"{c['share_sample_size']:>5}{c['share_occurrence_count']:>5}  "
          f"{c['layer']:<15}{c['geckoterminal_id'] or '-'}")
print()
print(f"volume source: https://api.llama.fi/overview/dexs/{{chain}}"
      f"?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
print(f"mcap share: SAMPLED over N={meth['share_sample_size']} CoinGecko "
      f"meme-token coins; attributed denominator "
      f"{usd(meth['share_denominator_market_cap_usd'])}; "
      f"{usd(meth['unattributed_market_cap_usd'])} unattributed "
      f"(native coin, no token contract)")
print()
print("=" * 108)
print("REACHABILITY MATRIX - exact HTTP status from this host")
print("=" * 108)
print(f"{'Chain':<20}{'JSON-RPC':<44}{'GeckoTerminal':<18}"
      f"{'DexScreener':<22}{'RugCheck'}")
for c in chains:
    print(f"{c['name']:<20}{c['rpc_status'][:42]:<44}"
          f"{str(c['geckoterminal_status'])[:16]:<18}"
          f"{str(c['dexscreener_status'])[:20]:<22}"
          f"{str(c['rugcheck_status'])[:30]}")
print()
print("Legend: HTTP nnn = exact status returned by a live call. "
      "SKIPPED = no address available (chain absent from GeckoTerminal).")
print("Not covered: RugCheck (EVM -> HTTP 400 base58 error, chain-prefixed "
      "-> 404); Jupiter (Solana only, EVM address queries -> 0 results).")
print()
print("NOT COVERED - no GeckoTerminal network:",
      ", ".join(gaps["not_on_geckoterminal"]))
print("NOT COVERED - no working free RPC:",
      ", ".join(gaps["no_public_rpc_found"]))
print("Ankr pattern rpc.ankr.com/<chain>: TLS hostname mismatch, all 24 "
      "chains")
print("Subquery pattern rpc.subquery.network/public/<chain>: HTTP 404, "
      "all 22 chains")
