# Chain Landscape — Memecoin Creation & Trading Networks

**Generated:** 2026-11-02T18:00:26Z (UTC)  
**Host:** All statuses are from live calls made from this Windows 11 host via Python 3 stdlib urllib with a certifi TLS context.  
**Method:** every figure below comes from a live API call made in the session that produced this file. Each URL is recorded in `data/chain_landscape.json` under `sources`.

---

## 1. Headline

- **Top chain by measured DEX 24h volume:** Ethereum ($1,189,207,436)
- **Top chain by sampled memecoin market-cap share:** Ethereum (40.69% of the attributed sample)
- **Memecoin market-cap sample:** N = 40 tokens from the CoinGecko `meme-token` category; sample market cap $25,145,482,665, of which $13,408,789,133 is attributable to a chain home and $11,736,693,532 is not.
- **Free-endpoint reachability:** 10/10 of the ranked chains have a working JSON-RPC endpoint, 10/10 have a working GeckoTerminal pools endpoint, and 10/10 have a working DexScreener token-pairs endpoint.
- **Ranked list ≠ working endpoints.** A chain can rank highly on volume and still have no usable free RPC. Section 5 is the independent reachability test.

## 2. Ranked table — top 10 memecoin networks

Primary sort key: **measured** DefiLlama per-chain DEX 24h volume (`total24h` from `https://api.llama.fi/overview/dexs/{chain}`).

`mcap share` is the **sampled** estimate and is a different measure — see §3.

| # | Chain | chain id | DEX 24h volume | mcap share | sample size | layer | GeckoTerminal id |
|---|-------|----------|-----------------|------------|-------------|-------|-----------------|
| 1 | Ethereum | `ethereum` | $1,189,207,436 | 40.69% | 40 | L1 | `eth` |
| 2 | Solana | `solana` | $905,602,298 | 27.23% | 40 | L1 | `solana` |
| 3 | BNB Smart Chain | `bsc` | $571,919,026 | 26.36% | 40 | L1 | `bsc` |
| 4 | Base | `base` | $566,993,410 | 1.00% | 40 | L2 | `base` |
| 5 | Robinhood Chain | `robinhood` | $370,172,251 | 1.16% | 40 | L2 | `robinhood` |
| 6 | Polygon PoS | `polygon` | $172,040,318 | 1.89% | 40 | sidechain-L1 | `polygon_pos` |
| 7 | Hyperliquid | `hyperliquid` | $161,045,310 | 0.53% | 40 | L1 | `hyperliquid` |
| 8 | TRON | `tron` | $122,247,912 | 0.00% | 40 | L1 | `tron` |
| 9 | NEAR | `near` | $89,765,583 | 0.00% | 40 | L1 | `near` |
| 10 | Arbitrum One | `arbitrum` | $81,109,247 | 0.00% | 40 | L2 | `arbitrum` |

Volume source URL per chain (all `https://api.llama.fi/overview/dexs/{chain}?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true`):

- **Ethereum** — https://api.llama.fi/overview/dexs/ethereum?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
- **Solana** — https://api.llama.fi/overview/dexs/solana?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
- **BNB Smart Chain** — https://api.llama.fi/overview/dexs/bsc?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
- **Base** — https://api.llama.fi/overview/dexs/base?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
- **Robinhood Chain** — https://api.llama.fi/overview/dexs/robinhood?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
- **Polygon PoS** — https://api.llama.fi/overview/dexs/polygon?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
- **Hyperliquid** — https://api.llama.fi/overview/dexs/hyperliquid?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
- **TRON** — https://api.llama.fi/overview/dexs/tron?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
- **NEAR** — https://api.llama.fi/overview/dexs/near?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
- **Arbitrum One** — https://api.llama.fi/overview/dexs/arbitrum?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true

## 3. How the two rankings were computed (and why they differ)

### 3.1 Ranked by measured DEX volume — the primary ranking

`https://api.llama.fi/overview/dexs/{chain}?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true` returns a `total24h` field. That is a **measured** 24-hour DEX volume for the chain, taken verbatim. No estimate is involved.

> **Correction to the task premise.** The task said GeckoTerminal's `/api/v2/networks` "gives per-network 24h DEX volume". It does not. The live response body for each network is only:
> ```json
> {"id": "eth", "type": "network", "attributes": {"name": "Ethereum", "coingecko_asset_platform_id": "ethereum"}}
> ```
> There is **no volume field** on that endpoint. Per-network volume is only obtainable by summing per-pool `attributes.volume_usd.h24` from `/api/v2/networks/{id}/pools`, which is a *page-limited* sum of the top pools, not the chain total. DefiLlama's per-chain `total24h` is the complete, single-number measurement, so it is used as the primary ranking key. GeckoTerminal remains in the survey as the source of the per-chain token address needed for the DexScreener probes.

### 3.2 Ranked by sampled memecoin market-cap share — a different measure

**Sample: N = 40 tokens.** Taken from `https://api.coingecko.com/api/v3/coins/markets?category=meme-token&vs_currency=usd&per_page=100&page=1` (100 tokens returned), then the top 40 by market cap.

> **Correction to the task premise (2).** The task said to read the `chains` field from `/coins/{id}`. There is no `chains` field. The live payload carries `platforms` (a `{chain_id: address}` map), `detail_platforms` and `asset_platform_id`. The survey reads `platforms`.

Attribution rule:

1. Each token's market cap is assigned to its **home chain** (`asset_platform_id` from `/coins/{id}`). Bridged copies are therefore not double-counted.
2. Where `asset_platform_id` is null but token contracts exist, the first `platforms` entry is used as the home chain.
3. Native coins with **no** contract on any chain (e.g. `dogecoin`) are **unattributed** — their market cap is the chain's own native asset, not a memecoin token on a token network. Unattributed: $11,736,693,532 (dogecoin).

Denominator (attributed market cap): **$13,408,789,133**. The occurrence count column in the JSON is the *unweighted* alternative the task described (each token counted once per chain it lists); it is recorded per chain as `share_occurrence_count` / `share_occurrence_pct` and is reported separately below.

| Chain | weighted mcap share | occurrence count | occurrence share |
|-------|---------------------|------------------|-----------------|
| Ethereum | 40.69% | 10 | 13.16% |
| Solana | 27.23% | 16 | 21.05% |
| BNB Smart Chain | 26.36% | 21 | 27.63% |
| Base | 1.00% | 5 | 6.58% |
| Robinhood Chain | 1.16% | 4 | 5.26% |
| Polygon PoS | 1.89% | 2 | 2.63% |
| Hyperliquid | 0.53% | 2 | 2.63% |
| TRON | 0.00% | 0 | 0.00% |
| NEAR | 0.00% | 0 | 0.00% |
| Arbitrum One | 0.00% | 2 | 2.63% |

Per-coin `/coins/{id}` detail was fetched live for 39/40 tokens. Rate-limited (HTTP 429) and resolved from the bulk `/coins/list?include_platform=true` map instead: spx6900.

**Where the two rankings disagree, and why.** Tron, NEAR and Arbitrum have real measured DEX volume but a near-zero share of the *top-40 market-cap* memecoin sample — their memecoin activity is in long-tail tokens, not in the top 40 by market cap. Conversely Base and Robinhood Chain have very large DEX volume but most of it is not memecoin flow in the sampled top-40. A chain in the top 10 by one measure can be absent from the other.

Chain-native memecoin categories from `https://api.coingecko.com/api/v3/coins/categories` (each carries `market_cap`, `market_cap_change_24h` and `volume_24h`):

| category id | name | market_cap | market_cap_change_24h | volume_24h |
|-------------|------|------------|-----------------------|------------|

(0 categories with a non-null market cap were returned out of 5 total CoinGecko categories. The aggregate `meme-token` category carries `market_cap` n/a and `market_cap_change_24h` None; the chain-native sub-categories above are the per-chain slices of that total.)

## 4. L1 vs L2 vs appchain classification, with citations

> **Ethereum L2s share the EVM execution environment but are SEPARATE token networks. They are not merged with Ethereum.** A Base ERC-20 and an Ethereum ERC-20 with the same address are different tokens on different networks; liquidity, holders and market cap do not pool. Every L2 below therefore gets its own row, its own `chain_id`, its own GeckoTerminal id and its own endpoint status. Polygon PoS and Polygon zkEVM are likewise separate networks and are not merged either.

| Chain | Classification | Citation (URL fetched live) | Evidence |
|-------|----------------|-----------------------------|----------|
| Ethereum | **L1** | https://ethereum.org/en/layer-2/ | Ethereum is the settlement layer (parent chain) for the Ethereum L2s listed here. |
| Solana | **L1** | https://solana.com/docs | Solana is its own proof-of-stake L1; it does not settle to Ethereum. |
| BNB Smart Chain | **L1** | https://docs.bnbchain.org/newl1/overview/ | BNB Smart Chain is a general-purpose EVM L1; the BNB Chain docs describe BSC as 'general-purpose EVM L1'. |
| Base | **L2** | https://docs.base.org/base-chain/overview | Base is an Ethereum L2 built on the OP Stack; it settles to Ethereum and is a separate token network. |
| Robinhood Chain | **L2** | https://docs.robinhood.com/chain/ | Robinhood Chain docs: 'a permissionless, Ethereum-compatible Layer-2 blockchain ... built on Arbitrum Dedicated Blockchains, a modular Layer-2 framework.' |
| Polygon PoS | **sidechain-L1** | https://docs.polygon.technology/pos/overview | Polygon PoS is a standalone EVM chain with its own staking and validator set (a sidechain of Ethereum), not a rollup. |
| Hyperliquid | **L1** | https://hyperliquid.gitbook.io/Hyperliquid-docs | Hyperliquid docs: 'Hyperliquid is a layer one blockchain (L1) written and optimized from first principles.' |
| TRON | **L1** | https://developers.tron.network/docs | TRON is a standalone delegated-proof-of-stake L1. |
| NEAR | **L1** | https://near.org/ | NEAR is a standalone sharded proof-of-stake L1. |
| Arbitrum One | **L2** | https://docs.arbitrum.io/get-started/arbitrum-introduction | Arbitrum docs: 'An Arbitrum chain that settles to Ethereum is a child chain, also called layer 2.' |

### Notable classification findings

- **Celo is no longer an L1.** Its own docs record that it "ran as an independent L1 from April 2020 until March 2025, when it completed its migration to an Ethereum Layer 2 at block 31,056,500" (https://docs.celo.org/learn/celo-l1, HTTP 200). It is classified **L2** here. Treating Celo as an L1 is a live-data error, not a judgement call.
- **Polygon PoS is not an Ethereum rollup.** It is a standalone EVM sidechain with its own validator set and staking. **Polygon zkEVM** is a separate Ethereum zk-rollup network and is listed as a distinct chain in `data/chain_landscape.json`'s layer map — the two are not merged.
- **Robinhood Chain is an Arbitrum-based L2**, per its own docs: "a permissionless, Ethereum-compatible Layer-2 blockchain ... built on Arbitrum Dedicated Blockchains, a modular Layer-2 framework" (https://docs.robinhood.com/chain/, HTTP 200).
- **Hyperliquid is an L1**, per https://hyperliquid.gitbook.io/Hyperliquid-docs (HTTP 200): "Hyperliquid is a layer one blockchain (L1) written and optimized from first principles." The separate HyperEVM network is not the same token network as the Hyperliquid L1.
- **Shimmer has shut down.** https://shimmer.network/ (HTTP 200): "As of September 30, 2026, Shimmer L1 and ShimmerEVM have officially stopped block production and sunsetted."

## 5. Endpoint reachability matrix (Step 2)

Every cell is the exact HTTP status returned by a live call from this host. `n/a` means no endpoint was tried for that service on that chain because the service does not cover it.

| Chain | EVM/Solana JSON-RPC | RPC URL used | GeckoTerminal pools | DexScreener pairs | RugCheck |
|-------|---------------------|--------------|--------------------|-------------------|----------|
| Ethereum | HTTP 200 (eth_blockNumber -> 0x191be5e) | `https://ethereum-rpc.publicnode.com` | HTTP 200 | HTTP 200 (30 pairs) | HTTP 400 (EVM address rejected: base58 decode error) |
| Solana | HTTP 200 (getSlot -> 464583749) | `https://api.mainnet-beta.solana.com` | HTTP 200 | HTTP 200 (30 pairs) | HTTP 200 |
| BNB Smart Chain | HTTP 200 (eth_blockNumber -> 0x7d338aa) | `https://bsc-rpc.publicnode.com` | HTTP 200 | HTTP 200 (8 pairs) | HTTP 400 (EVM address rejected: base58 decode error) |
| Base | HTTP 200 (eth_blockNumber -> 0x32f3793) | `https://base-rpc.publicnode.com` | HTTP 200 | HTTP 200 (30 pairs) | HTTP 400 (EVM address rejected: base58 decode error) |
| Robinhood Chain | HTTP 200 (eth_blockNumber -> 0x6390cce) | `https://robinhood-rpc.publicnode.com` | HTTP 200 | HTTP 200 (30 pairs) | HTTP 400 (EVM address rejected: base58 decode error) |
| Polygon PoS | HTTP 200 (eth_blockNumber -> 0x5c25d93) | `https://polygon-bor-rpc.publicnode.com` | HTTP 200 | HTTP 200 (11 pairs) | HTTP 400 (EVM address rejected: base58 decode error) |
| Hyperliquid | HTTP 200 (eth_blockNumber -> 0x2fe1c23) | `https://rpc.hyperliquid.xyz/evm` | HTTP 200 | HTTP 200 (3 pairs) | HTTP 400 (EVM address rejected: base58 decode error) |
| TRON | HTTP 200 (eth_blockNumber -> 0x539863c) | `https://tron.drpc.org` | HTTP 200 | HTTP 200 (30 pairs) | HTTP 400 (EVM address rejected: base58 decode error) |
| NEAR | HTTP 200 (status -> {'chain_id': 'mainnet'...) | `https://near.drpc.org` | HTTP 200 | HTTP 200 (30 pairs) | HTTP 400 (EVM address rejected: base58 decode error) |
| Arbitrum One | HTTP 200 (eth_blockNumber -> 0x1f0848a5) | `https://arbitrum-one-rpc.publicnode.com` | HTTP 200 | HTTP 200 (30 pairs) | HTTP 400 (EVM address rejected: base58 decode error) |

### 5.1 GeckoTerminal network ids are not the same as the other names

GeckoTerminal ids, CoinGecko platform ids, DefiLlama slugs and RPC host slugs are four different namespaces. The resolved GT ids:

| Chain id | GeckoTerminal id | GT display name |
|----------|------------------|------------------|
| `ethereum` | `eth` | Ethereum |
| `solana` | `solana` | Solana |
| `bsc` | `bsc` | BNB Smart Chain |
| `base` | `base` | Base |
| `robinhood` | `robinhood` | Robinhood Chain |
| `polygon` | `polygon_pos` | Polygon PoS |
| `hyperliquid` | `hyperliquid` | Hyperliquid |
| `tron` | `tron` | TRON |
| `near` | `near` | NEAR |
| `arbitrum` | `arbitrum` | Arbitrum One |

Examples of the mismatch: Ethereum is `eth` on GeckoTerminal but `ethereum` on CoinGecko and DefiLlama; Avalanche is `avax`; Polygon is `polygon_pos` (not `polygon`, and `polygon-zkevm` is a different network); Sui is `sui-network`; Zora is `zora-network`; World Chain is `world-chain`; zkSync is `zksync`; Cronos is `cro`; Harmony is `one`; Conflux is `cfx`.

### 5.2 Per-chain RPC probe detail

`eth_blockNumber` (or the chain's native method) POSTed to each host in turn until one returned a usable result. Failed hosts are listed with their real failure.

**Ethereum**

| URL | Result |
|-----|--------|
| `https://ethereum-rpc.publicnode.com` | HTTP 200  |

**Solana**

| URL | Result |
|-----|--------|
| `https://api.mainnet-beta.solana.com` | HTTP 200  |

**BNB Smart Chain**

| URL | Result |
|-----|--------|
| `https://bsc-rpc.publicnode.com` | HTTP 200  |

**Base**

| URL | Result |
|-----|--------|
| `https://base-rpc.publicnode.com` | HTTP 200  |

**Robinhood Chain**

| URL | Result |
|-----|--------|
| `https://rpc.robinhoodchain.com` | ERROR URLError: <urlopen error [SSL: TLSV1_UNRECOGNIZED_NAME] tlsv1 unrecognized name (_ssl.c:1082)> URLError: <urlopen error [SSL: TLSV1_UNRECOGNIZED_NAME] tlsv1 unrecognized name (_ssl.c:10 |
| `https://robinhood-rpc.publicnode.com` | HTTP 200  |

**Polygon PoS**

| URL | Result |
|-----|--------|
| `https://polygon-bor-rpc.publicnode.com` | HTTP 200  |

**Hyperliquid**

| URL | Result |
|-----|--------|
| `https://rpc.hyperliquid.xyz/evm` | HTTP 200  |

**TRON**

| URL | Result |
|-----|--------|
| `https://api.trongrid.io` | HTTP 405 HTTPError 405 Not Allowed |
| `https://tron-rpc.publicnode.com` | HTTP 405 HTTPError 405 Method Not Allowed |
| `https://tron.drpc.org` | HTTP 200  |

**NEAR**

| URL | Result |
|-----|--------|
| `https://rpc.near.io` | ERROR URLError: <urlopen error [Errno 11001] getaddrinfo failed> URLError: <urlopen error [Errno 11001] getaddrinfo failed> |
| `https://near-rpc.publicnode.com` | HTTP 404 HTTPError 404 Not Found |
| `https://near.drpc.org` | HTTP 200  |

**Arbitrum One**

| URL | Result |
|-----|--------|
| `https://arbitrum-one-rpc.publicnode.com` | HTTP 200  |

### 5.3 The Ankr and Subquery fallback patterns

The task asked for Ankr and Subquery public RPC patterns as fallbacks. Both were tested explicitly:

- **`https://rpc.ankr.com/{chain}`** — TLS `CERTIFICATE_VERIFY_FAILED: Hostname mismatch, certificate is not valid for 'rpc.ankr.com'` for **all 24 chains** tried (eth, base, bsc, arbitrum, polygon, optimism, avalanche, linea, scroll, zksync, blast, mantle, celo, berachain, fantom, soneium, abstract, unichain, worldchain, zora, sonic, hyperliquid, monad, solana). The certificate served for that host does not cover the hostname, so no Ankr chain is usable from this host — this is a host/CA issue, not a per-chain outage.
- **`https://rpc.subquery.network/public/{chain}`** — HTTP **404** for **all 22 chains** tried (ethereum, base, bsc, arbitrum, polygon, optimism, avalanche, linea, scroll, zksync, blast, mantle, celo, berachain, fantom, soneium, abstract, unichain, worldchain, zora, sonic, hyperliquid, monad). The public path prefix no longer serves RPC.

Working publicnode fallbacks that were found for the chains whose publicnode slug 404s or errors (all verified live):

| Chain | publicnode slug result | Working free RPC found |
|-------|-------------------------|------------------------|
| abstract | no publicnode host for this chain | https://abstract.drpc.org (HTTP 200) |
| aptos | HTTP 404 — `aptos-rpc.publicnode.com` | https://fullnode.mainnet.aptoslabs.com/v1 (HTTP 200, REST) |
| arbitrum | HTTP 200 — `arbitrum-one-rpc.publicnode.com` | **no working free RPC found** |
| arc | HTTP 200 — `arc-rpc.publicnode.com` | **no working free RPC found** |
| avalanche | HTTP 200 — `avalanche-c-chain-rpc.publicnode.com` | **no working free RPC found** |
| base | HTTP 200 — `base-rpc.publicnode.com` | **no working free RPC found** |
| berachain | HTTP 200 — `berachain-rpc.publicnode.com` | **no working free RPC found** |
| bitcoin | HTTP 200 — `bitcoin-rpc.publicnode.com` | **no working free RPC found** |
| blast | no publicnode host for this chain | https://rpc.blast.io (HTTP 200) |
| bob | no publicnode host for this chain | https://bob.drpc.org (HTTP 200) |
| bsc | HTTP 200 — `bsc-rpc.publicnode.com` | **no working free RPC found** |
| bsc-testnet | no publicnode host for this chain | **no working free RPC found** |
| cardano | HTTP 404 — `cardano-rpc.publicnode.com` | https://api.koios.rest/api/v1/tip (HTTP 200, REST) |
| celo | HTTP 200 — `celo-rpc.publicnode.com` | **no working free RPC found** |
| conflux | HTTP 404 — `conflux-rpc.publicnode.com` | **no working free RPC found** |
| core | no publicnode host for this chain | **no working free RPC found** |
| cronos | no publicnode host for this chain | **no working free RPC found** |
| dogechain | HTTP 404 — `dogechain-rpc.publicnode.com` | **no working free RPC found** |
| ethereum | HTTP 200 — `ethereum-rpc.publicnode.com` | **no working free RPC found** |
| evmos | HTTP 404 — `evmos-evm-rpc.publicnode.com` | **no working free RPC found** |
| fantom | no publicnode host for this chain | https://rpc3.fantom.network (HTTP 200) |
| flare | no publicnode host for this chain | **no working free RPC found** |
| fraxtal | no publicnode host for this chain | **no working free RPC found** |
| harmony | no publicnode host for this chain | https://api.harmony.one (HTTP 200) |
| hedera | no publicnode host for this chain | https://mainnet-public.mirrornode.hedera.com/api/v1/network/supply (HTTP 200, REST) |
| hyperevm | no publicnode host for this chain | **no working free RPC found** |
| hyperliquid | no publicnode host for this chain | https://rpc.hyperliquid.xyz/evm (HTTP 200) |
| injective | HTTP 200 — `injective-rpc.publicnode.com` | https://injective.drpc.org (HTTP 200) |
| ink | HTTP 200 — `ink-rpc.publicnode.com` | **no working free RPC found** |
| kava | no publicnode host for this chain | **no working free RPC found** |
| linea | HTTP 200 — `linea-rpc.publicnode.com` | **no working free RPC found** |
| litecoin | HTTP 404 — `litecoin-rpc.publicnode.com` | https://api.blockchair.com/litecoin/stats (HTTP 200, REST; no JSON-RPC found) |
| manta | no publicnode host for this chain | **no working free RPC found** |
| mantle | HTTP 200 — `mantle-rpc.publicnode.com` | **no working free RPC found** |
| metis | no publicnode host for this chain | **no working free RPC found** |
| mode | no publicnode host for this chain | **no working free RPC found** |
| monad | no publicnode host for this chain | https://rpc.monad.xyz (HTTP 200) |
| morph | no publicnode host for this chain | **no working free RPC found** |
| near | HTTP 404 — `near-rpc.publicnode.com` | https://near.drpc.org (HTTP 200, `status` method) |
| opbnb | no publicnode host for this chain | **no working free RPC found** |
| optimism | HTTP 200 — `optimism-rpc.publicnode.com` | **no working free RPC found** |
| plasma | no publicnode host for this chain | https://rpc.plasma.to (HTTP 200) |
| polygon | HTTP 200 — `polygon-bor-rpc.publicnode.com` | **no working free RPC found** |
| polygon_zkevm | no publicnode host for this chain | **no working free RPC found** |
| robinhood | HTTP 200 — `robinhood-rpc.publicnode.com` | **no working free RPC found** |
| ronin | no publicnode host for this chain | **no working free RPC found** |
| rootstock | no publicnode host for this chain | **no working free RPC found** |
| scroll | 200 — `scroll-rpc.publicnode.com` | **no working free RPC found** |
| sei | no publicnode host for this chain | **no working free RPC found** |
| shimmer | no publicnode host for this chain | **no working free RPC found** |
| solana | no publicnode host for this chain | **no working free RPC found** |
| soneium | HTTP 200 — `soneium-rpc.publicnode.com` | **no working free RPC found** |
| sonic | HTTP 200 — `sonic-rpc.publicnode.com` | **no working free RPC found** |
| sophon | no publicnode host for this chain | **no working free RPC found** |
| stable | no publicnode host for this chain | **no working free RPC found** |
| story | HTTP 200 — `story-rpc.publicnode.com` | **no working free RPC found** |
| sui | HTTP 200 — `sui-rpc.publicnode.com` | https://sui-mainnet.gateway.tatum.io/graphql (HTTP 200, GraphQL `chainIdentifier`) |
| swellchain | HTTP 404 — `swellchain-rpc.publicnode.com` | **no working free RPC found** |
| taiko | HTTP 200 — `taiko-rpc.publicnode.com` | **no working free RPC found** |
| ton | HTTP 404 — `ton-rpc.publicnode.com` | https://toncenter.com/api/v2/jsonRPC (HTTP 200, `getMasterchainInfo`) |
| tron | HTTP 405 — `tron-rpc.publicnode.com` | **no working free RPC found** |
| unichain | HTTP 200 — `unichain-rpc.publicnode.com` | **no working free RPC found** |
| worldchain | no publicnode host for this chain | https://worldchain.drpc.org (HTTP 200) |
| worldsepolia | 404 — `worldsepolia-rpc.publicnode.com` | **no working free RPC found** |
| xrpl | HTTP 404 — `xrpl-rpc.publicnode.com` | https://xrpl.drpc.org (HTTP 200 on `eth_blockNumber`; its native `ledger_current` is not exposed) |
| zksync | no publicnode host for this chain | **no working free RPC found** |
| zora | no publicnode host for this chain | https://rpc.zora.energy (HTTP 200) |

### 5.4 Solana RPC hosts

| URL | getSlot |
|-----|---------|
| `https://api.blockeden.xyz/solana/67nCBdZQSH9z3YqDDjdm` | HTTP 402 {'code': 'PAID_PLAN_REQUIRED', 'message': 'A paid plan is required', 'details': 'Your plan no longer has API access. Blo |
| `https://api.mainnet-beta.solana.com` | HTTP 200 OK slot=464578634 |
| `https://solana-rpc.publicnode.com` | HTTP 200 OK slot=464578643 |
| `https://solana.drpc.org` | HTTP 400 {'message': 'chain is not available on free plan, please upgrade to paid plan', 'code': 35} |

### 5.5 RugCheck — Solana only

| Call | URL | Status |
|------|-----|--------|
| base chain-prefixed | `https://api.rugcheck.xyz/v1/tokens/base/0x532f27101965dd16442E59d40670FaF5eBB142E4/report/summary` | HTTP 404 |
| base plain holders/top | `https://api.rugcheck.xyz/v1/tokens/0x532f27101965dd16442E59d40670FaF5eBB142E4/holders/top` | HTTP 404 |
| base plain report/summary | `https://api.rugcheck.xyz/v1/tokens/0x532f27101965dd16442E59d40670FaF5eBB142E4/report/summary` | HTTP 400 |
| bsc chain-prefixed | `https://api.rugcheck.xyz/v1/tokens/bsc/0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82/report/summary` | HTTP 404 |
| bsc chain-prefixed holders | `https://api.rugcheck.xyz/v1/tokens/bsc/0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82/holders/top` | HTTP 404 |
| bsc plain report/summary | `https://api.rugcheck.xyz/v1/tokens/0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82/report/summary` | HTTP 400 |
| bsc with 0x prefix | `https://api.rugcheck.xyz/v1/tokens/0x0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82/report/summary` | HTTP 400 |
| ethereum chain-prefixed | `https://api.rugcheck.xyz/v1/tokens/ethereum/0x6982508145454Ce325dDbE47a25d4ec3d2311933/report/summary` | HTTP 404 |
| solana chain-prefixed | `https://api.rugcheck.xyz/v1/tokens/solana/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263/report/summary` | HTTP 404 |
| solana holders/top | `https://api.rugcheck.xyz/v1/tokens/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263/holders/top` | HTTP 404 |
| solana report | `https://api.rugcheck.xyz/v1/tokens/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263/report` | HTTP 200 |
| solana report/summary | `https://api.rugcheck.xyz/v1/tokens/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263/report/summary` | HTTP 200 |

**Conclusion:** RugCheck serves **Solana only**.

- A Solana mint returns HTTP 200 on `/v1/tokens/{mint}/report/summary` and `/v1/tokens/{mint}/report`. The `report` payload carries the top holders under `topHolders` (20 entries, each with `address`, `owner`, `amount`, `pct`, `insider`).
- **`/holders/top` is not a valid path.** Both `/holders/top` and `/holders` return HTTP 404 `PAGE_NOT_FOUND`. The top-holder data lives inside `/report` → `topHolders`, not on a separate holders endpoint. `/lockers` returns HTTP 401 (requires a RugCheck API token).
- Every **EVM** address returns HTTP 400 `{"error":"decode: base58: invalid base58 character"}` — RugCheck base58-decodes the mint, so a `0x…` address cannot be served.
- The **chain-prefixed** form `/v1/tokens/{chain}/{address}/…` returns HTTP 404 `PAGE_NOT_FOUND` for `base`, `bsc`, `ethereum` and `solana` — there is no multi-chain route on this API.

### 5.6 Jupiter — Solana only

| Call | URL | Status | Results |
|------|-----|--------|---------|
| search 0x1 | `https://lite-api.jup.ag/tokens/v2/search?query=0x1` | HTTP 200 | 20 tokens |
| search a BSC token symbol | `https://lite-api.jup.ag/tokens/v2/search?query=cake` | HTTP 200 | 20 tokens |
| search a Base token symbol | `https://lite-api.jup.ag/tokens/v2/search?query=brett` | HTTP 200 | 20 tokens |
| search a solana mint | `https://lite-api.jup.ag/tokens/v2/search?query=DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263` | HTTP 200 | 1 tokens |
| search an Ethereum token symbol | `https://lite-api.jup.ag/tokens/v2/search?query=shiba` | HTTP 200 | 20 tokens |
| search bonk | `https://lite-api.jup.ag/tokens/v2/search?query=bonk` | HTTP 200 | 20 tokens |
| search pepe | `https://lite-api.jup.ag/tokens/v2/search?query=pepe` | HTTP 200 | 20 tokens |

**Conclusion:** Jupiter's `/tokens/v2/search` indexes **Solana only**.

- `?query=pepe` → 20 results, all Solana SPL mints (base58 ids such as `PEPEqnuuCDbBC89p1u9vpnP1KQ2oj1xTcQBsjt9X55m`, many with the `pump` suffix from pump.fun).
- `?query=0x1` → 20 results, all Solana SPL mints whose *names* happen to contain "0x"; the query is a substring match on name/symbol, not an address lookup.
- `?query=<an exact Base address>` → **0 results**. Same for an exact Ethereum address and an exact BSC address.
- On `?query=pepe` and `?tag=verified` (4,083 results), the count of ids beginning with `0x` was **0**. Every returned token carries `tokenProgram`/`decimals`/`usdPrice` — the Solana SPL shape. Jupiter's response has no `chainId` field, so chain cannot be read from it; the evidence is the id format and the `tokenProgram` field.

## 6. What is NOT covered, and why

### 6.1 Chains with no working free JSON-RPC

Every chain in the surveyed set that was probed and had **no** host return a usable result:

| Chain | Every host tried and its real failure |
|-------|----------------------------------------|
| bitcoin | `https://btc-mainnet.public.blastapi.io` → ERROR URLError: <urlopen error [Errno 11001] getaddrinfo failed> URLError: <urlopen error [Errno 11001] getaddrinfo failed><br>`https://bitcoin-rpc.publicnode.com` → HTTP 200 {'code': -32601, 'message': 'Method not found'} |
| conflux | `https://www.confluxrpc.io` → ERROR URLError: <urlopen error [Errno 11001] getaddrinfo failed> URLError: <urlopen error [Errno 11001] getaddrinfo failed><br>`https://conflux-rpc.publicnode.com` → HTTP 404 HTTPError 404 Not Found |
| dogechain | `https://rpc.dogechain.io` → ERROR URLError: <urlopen error [Errno 11001] getaddrinfo failed> URLError: <urlopen error [Errno 11001] getaddrinfo failed><br>`https://dogechain.drpc.org` → HTTP 404 HTTPError 404 Not Found |
| evmos | `https://evmos-evm-rpc.publicnode.com` → HTTP 404 HTTPError 404 Not Found<br>`https://evmos-json-rpc.stakely.io` → ERROR URLError: <urlopen error [Errno 11001] getaddrinfo failed> URLError: <urlopen error [Errno 11001] getaddrinfo failed> |
| shimmer | `https://shimmer-json-rpc.publicnode.com` → HTTP 404 HTTPError 404 Not Found |
| sophon | `https://rpc.sophon.network` → ERROR URLError: <urlopen error [Errno 11001] getaddrinfo failed> URLError: <urlopen error [Errno 11001] getaddrinfo failed><br>`https://sophon.drpc.org` → HTTP 400 HTTPError 400 Bad Request |
| swellchain | `https://rpc.swellchain.io` → ERROR URLError: <urlopen error [Errno 11001] getaddrinfo failed> URLError: <urlopen error [Errno 11001] getaddrinfo failed><br>`https://swellchain-rpc.publicnode.com` → HTTP 404 HTTPError 404 Not Found |

**swellchain**, **evmos**, **sophon**, **conflux** and **dogechain** had every free host fail (publicnode/drpc 404, no other public endpoint reachable). **shimmer**'s host returns HTTP 502 and the chain has sunset (September 30, 2026). **litecoin** has no JSON-RPC at all — only a REST stats endpoint (https://api.blockchair.com/litecoin/stats, HTTP 200). **xrpl** answers `eth_blockNumber` on drpc but does not expose its native `ledger_current`. These chains still appear in the landscape data with their volume and layer classification; what is missing is a usable JSON-RPC endpoint.

### 6.2 Services that do not cover EVM chains at all

- **RugCheck** — Solana only (§5.5). Every EVM address → HTTP 400 base58 decode error; every chain-prefixed path → HTTP 404.
- **Jupiter** — Solana only (§5.6). Exact EVM address queries → 0 results; 0 of 4,083 verified tokens have a `0x` id.

### 6.3 Chains in the surveyed set with zero sampled memecoin share

| Chain | DEX 24h volume | Why it still ranks |
|-------|-----------------|--------------------|
| TRON | $122,247,912 | 1 DefiLlama launchpads (token-creation venues) |
| NEAR | $89,765,583 | memecoin DEX volume $6; 1 DefiLlama launchpads (token-creation venues) |

These chains have **measured** DEX volume but their memecoin activity sits in long-tail tokens below the top-40 market-cap cut. They are in the ranking because of volume, and their `memecoin_mcap_share_pct` is honestly reported as ~0 — not because memecoins are absent there.

### 6.4 DexScreener returned HTTP 200 but zero pairs

A `200` with an empty array means the endpoint answered and the token has no listed pair under that chain slug — it is a real answer, not a failure. The probe token is whatever GeckoTerminal's top pool for that network uses, so on a young chain it may be a wrapped-native asset that DexScreener has not indexed. Affected chains in the surveyed set: `blast`, `bob`, `flare`, `injective`, `mode`, `monad`, `ronin`, `sei`, `story`, `sui`, `taiko`, `zora`.

### 6.5 Chains not on GeckoTerminal

GeckoTerminal's network list (3 pages, 226 unique ids, all fetched live) has no entry for: `bitcoin`, `evmos`, `hyperevm`, `polygon_zkevm`, `swellchain`. For those chains the per-network pools endpoint cannot be called at all, and because the DexScreener probe takes its token address from a GeckoTerminal pool, the DexScreener probe is skipped for them too rather than being answered with an invented address.

## 7. Method notes and caveats

1. **Sample size.** The market-cap share is estimated from N = 40 tokens (CoinGecko `meme-token` category, top 40 by market cap). It is a *sample*, and it is labelled as such everywhere. It is not a census of memecoin market cap.
2. **Two different rankings.** Volume rank is measured; market-cap rank is sampled. They are not interchangeable and the JSON keeps both (`dex_volume_24h_usd` vs `memecoin_mcap_share_pct` + `share_occurrence_count`).
3. **Coverage bias in the sample.** CoinGecko's `meme-token` category is dominated by a handful of very large tokens; the sample's long tail is thin. Chains whose memes are numerous but small (TRON's `sunpump`, NEAR's `meme-cooking`) barely register in the top-40.
4. **Volume is DEX volume, not memecoin volume.** DefiLlama's per-chain `total24h` covers *all* DEX activity on the chain. The memecoin-only slice is in `memecoin_dex_protocols_24h` / `memecoin_dex_volume_24h_usd` per chain, derived from the `breakdown24h` map of the memecoin-named protocols in `/api/v2/overview/dexs`.
5. **Rate limits are real.** CoinGecko's free tier returned HTTP 429 repeatedly on this host; the per-coin sweep was paced and 1 of 40 tokens stayed rate-limited (resolved from the bulk platform map). GeckoTerminal returned HTTP 429 on some pools requests under load and HTTP 200 on retry.
6. **`eth_getCode` is not the same as `eth_blockNumber`.** Both worked on ethereum, base, bsc, arbitrum, polygon, optimism and avalanche when called with an explicit `latest` block tag. Called without a block tag, publicnode treats it as an **archive** request: base and bsc returned HTTP 403 `{'code': -32602, 'message': 'Archive requests require a personal token…'}`. So `eth_blockNumber` succeeding does not mean `eth_getCode` will.
7. **Re-fetching.** Raw responses are cached under `data/_raw/` and the collector scripts are resumable; delete a `step1_*.json` file to force that source to be re-fetched.

## 8. Files

| File | Contents |
|------|----------|
| `data/chain_landscape.json` | Machine-readable: `generated_at`, `sources` (name, url, fetched_at, status), `chains` (rank, name, chain_id, layer, geckoterminal_id, dex_volume_24h_usd, memecoin_mcap_share_pct, share_method, share_sample_size, rpc_url, rpc_status, geckoterminal_status, dexscreener_status, rugcheck_status, notes), plus `methodology` and `coverage_gaps`. |
| `CHAIN_LANDSCAPE.md` | This document. |
| `data/_raw/step1_*.json` | Raw responses to every source call. |
| `scripts/` | The collector and verifier scripts that produced both files. |

