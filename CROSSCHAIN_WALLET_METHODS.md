# Cross-Chain Wallet Identity & Free Per-Wallet PnL

**Package:** `leapspace-quant`
**Modules:** `leapspace/costs.py`, `leapspace/crosschain.py`
**Date of all live tests:** 2026-11-03
**Host:** Windows 11, Python 3.14.7

---

## 0. What this document is, and what it is not

This document records two things that were previously open problems in this
package:

1. **How to compute a wallet's realised PnL when no historical price API is
   reachable.** The previous state of the package recorded
   `realised_pnl_available: false` and asserted that no keyless historical
   price source exists. **That assertion was wrong, and this document
   corrects it with the working method and the measured accuracy.**
2. **How to decide that one operator controls the same wallet on several
   chains,** using only free sources, with the evidence attached to every
   claim.

Everything below was tested from this host. **Every HTTP status quoted in
this document came from a call this package actually made.** Where a source
was unreachable, that is stated with the status that proved it.

---

# PART 1 — Realised PnL without a historical price API

## 1.1 The problem, restated precisely

The package can see a wallet's complete ERC-20 transfer history for a token
(Blockscout v2 `/api/v2/addresses/{addr}/token-transfers`, keyless, HTTP 200).
That gives quantities, directions, counterparties, blocks and timestamps.

What it cannot get is **the price at a past block**. Three assumptions were
previously carried in the codebase, and two of them turned out to be wrong:

| Prior assumption | Verdict | Evidence |
|---|---|---|
| "DefiLlama does not index these contracts" | **WRONG** | `https://coins.llama.fi/prices/historical/{ts}/{chain}:{token}` returns HTTP 200 with a real historical price for 15 of 17 live memecoins tested, including WOJAK at a \$1.26M market cap |
| "CoinGecko's `market_chart` returns 401" | Correct on the public tier, but irrelevant | A live call to `https://api.coingecko.com/api/v3/coins/pepe/market_chart` did not return a response from this host |
| "Blockscout's per-transfer `exchange_rate` is the current rate, not the rate at that block" | **Correct, and important** | The per-transfer rate is a live-token attribute; it must not be used for a past trade |
| "No keyless archive RPC exists" | **WRONG** | Five keyless Ethereum endpoints and one per non-Ethereum chain serve historical state — see §1.2 |

The real obstacle was never the absence of data. It was the absence of a
**method** for turning a past block into a price. That method is below.

## 1.2 The keyless archive RPCs (the enabling finding)

An "archive node" serves the state of a past block, not just the head. Free
public RPCs are overwhelmingly *not* archive nodes. The test used throughout
is:

> Read state at a block far in the past. A full node answers
> `missing trie node`, `state not available`, `No state available for block`,
> or `state at block #N is pruned`. Only a real archive node returns data.

**A provider that answers "latest" but errors on a past block is not
archive**, and the module treats it as not archive.

### Ethereum — HTTP 200, historical state confirmed

| Endpoint | Archive? | Evidence |
|---|---|---|
| `https://eth.drpc.org` | **YES** | `eth_call getReserves()` on the Uniswap V2 WETH/USDC pair returned distinct non-zero values at blocks 11M, 12M, 13M, 15M, 17M, 19M and 21M, each differing from `latest` — 7/7 |
| `https://eth-mainnet.public.blastapi.io` | **YES** | 7/7 identical test |
| `https://gateway.tenderly.co/public/mainnet` | **YES** | 7/7 identical test |
| `https://rpc.mevblocker.io` | **YES** | 7/7 identical test |
| `https://eth-pokt.nodies.app` | **YES** | 7/7 identical test |
| `https://ethereum-rpc.publicnode.com` | **NO** | HTTP 200 but JSON-RPC error `-32602`: *"Archive requests require a personal token. Get one at https://www.allnodes.com/publicnode"* |
| `https://eth.rpc.blxrbdn.com` | **NO** | HTTP 200 but JSON-RPC error `-32000`: *"historical state … not available"* |
| `https://rpc.ankr.com/eth` | **NO** | HTTP 200 but error: *"Unauthorized: You must authenticate your request with an API key"* |
| `https://api.zan.top/eth-mainnet` | **NO** | HTTP 200 but error: *"cu limit exceeded; Method eth_call is not available for unregistered accounts"* |
| `https://rpc.flashbots.net` | **NO** | HTTP 200 but error `-32601`: *"rpc method is not whitelisted"* |
| `https://eth.merkle.io` | unknown | HTTP 429 (rate limited) |
| `https://eth-mainnet.g.alchemy.com/v2/demo` | unknown | HTTP 429 (rate limited) |

### Other chains — HTTP 200, historical state confirmed

`eth_getTransactionCount` at 70% of chain history:

| Chain | Working archive endpoint | Rejected providers (HTTP + message) |
|---|---|---|
| base | `https://base.drpc.org` | publicnode HTTP 200 + `-32602` *"Archive requests require a personal token"* |
| arbitrum | `https://arbitrum-one.public.blastapi.io` | drpc HTTP 200 + code 27 *"Unknown state"*; publicnode `-32602` |
| bsc | `https://api.zan.top/bsc-mainnet` | `bsc-dataseed.binance.org` HTTP 200 + `-32000` *"missing trie node"*; `1rpc.io/bnb` HTTP 200 + *"state at block #… is pruned"*; publicnode `-32602` |
| optimism | `https://optimism.drpc.org` | publicnode `-32602` |
| polygon | `https://polygon.drpc.org` | publicnode `-32602` |
| gnosis | `https://gnosis.drpc.org` | publicnode HTTP 200 + `-32002` *"No state available for block"* |

These are the URLs baked into `leapspace/costs.py::ARCHIVE_RPC`, and
`ArchiveRpc.verify_archive()` re-proves them at runtime rather than trusting
the table.

## 1.3 Option (a) — the WORKING method: pool-state reconstruction

### The idea

> **The DEX pool the wallet traded on *is* the price oracle.** A keyless
> archive node can read that pool's own state as it was at any past block.

The pool is identified with **no subgraph and no indexer**: the ERC-20
`Transfer` event is emitted *by the pool*, so the counterparty address in a
Blockscout transfer row **is** the pool address.

Then, via `eth_call` at the trade's own block:

| Pool type | Call | Selector | Price |
|---|---|---|---|
| Uniswap V2 pair | `getReserves()` | `0x0902f1ac` | `reserve1/reserve0`, decimals-adjusted |
| Uniswap V3 pool | `slot0()` | `0x3850c7bd` | `(sqrtPriceX96 / 2^96)^2`, decimals-adjusted |

The result is a price of the traded token in the pool's **quote leg**
(WETH or USDC). The quote leg is then converted to USD with DefiLlama's
historical price for *that* token at the *same* timestamp — a token with
excellent coverage, unlike the long tail of memecoins.

### Measured accuracy — the number that matters

**Test A — pool state vs reference price, 7 blocks (2023–2026):**
PEPE's main Uniswap V2 pair, reconstructed price vs DefiLlama's own price
for PEPE at the same timestamp.

| Block | Date | Reconstructed | Reference | Error |
|---|---|---|---|---|
| 18,000,000 | 2023-08 | 8.70018e-07 | 8.71390e-07 | **-0.16%** |
| 19,500,000 | 2024-04 | 7.44274e-06 | 7.44000e-06 | **+0.04%** |
| 21,000,000 | 2024-12 | 1.05028e-05 | 1.051503e-05 | **-0.12%** |
| 22,500,000 | 2025-04 | 1.23495e-05 | 1.24700e-05 | **-0.97%** |
| 24,000,000 | 2025-11 | 4.32454e-06 | 4.329831e-06 | **-0.12%** |
| 25,500,000 | 2026-04 | 2.66193e-06 | 2.664375e-06 | **-0.09%** |
| 26,300,000 | 2026-10 | 5.38668e-06 | 5.400308e-06 | **-0.25%** |

> **Median absolute error 0.12% · p90 0.97% · max 0.97% (n=7)**

Three further blocks (13.5M, 15M, 16.5M) returned
`POOL_NOT_DEPLOYED_AT_BLOCK`. That is the honest failure: PEPE launched in
April 2023, so the pool did not exist at those blocks. The module reports
that reason rather than falling back to today's price.

**Test B — on real wallet trades.** See `reports/live_pool_trades.json` and
§1.6 for the live figures.

### Why the error is not zero, and what it is made of

The residual error is the difference between **the pool's price at a block**
and **the token's reference price at that instant**:

1. The reference price is itself a VWAP across venues; the pool price is
   one venue's marginal price. In a thin memecoin pool the two genuinely
   differ by ~1%.
2. `eth_call` at block N returns the state **after** block N's
   transactions, so it reflects the price *following* the block's trades.
   For a 12-second block against a fast-moving memecoin, that is a real
   timing difference, not a rounding error.

Neither source is "the truth"; both are measures of the same quantity. The
method is therefore suitable for **cost basis**, where a ~0.1–1% error on
each leg is immaterial next to the fee, gas and MEV costs it excludes.

## 1.4 Option (a′) — the exact price: swap-event reconstruction

The pool's own `Swap` event in the trade's block carries the exact amounts
that went in and came out. That is the **executed price of that specific
swap** — no interpolation, no rounding, correct even when the trade moved
the price.

- Uniswap V2: `Swap(address,uint256,uint256,uint256,uint256,address)` —
  topic `0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822`
  — data carries `(amount0In, amount1In, amount0Out, amount1Out)`.
- Uniswap V3: `Swap(address,address,int256,int256,int256,int256,uint160,uint128,int24)`
  — topic `0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67`.

Cost: one `eth_getLogs` over a **single block**.

**Honest limitation:** a block can contain several swaps in the same pool,
and a router can split a trade across pools or venues. The module therefore
labels a swap-derived price `pool_executed_price` — exact for *the swap*,
not necessarily the wallet's fill — and reports the number of swaps found
in the block so the reader can judge.

## 1.5 Option (b) — the price-free proxy, and its measured bias

`costs.quantity_proxy()` computes, per token, with **no price at all**:
`tokens_in`, `tokens_out`, `net_tokens`, `turnover_ratio`
(`tokens_out / tokens_in`), and the wallet's own first-observed
acquisition price in the quote token.

### The bias is not noise — it is blindness

`costs.proxy_bias_test()` measures this on a case with a known answer:

| | True PnL | Proxy `tokens_out` | Proxy turnover |
|---|---|---|---|
| Winner (buy 1M @ 0.001, sell 1M @ 0.002) | **+1000** | 1,000,000 | 1.0 |
| Loser (buy 1M @ 0.002, sell 1M @ 0.001) | **−1000** | 1,000,000 | 1.0 |

> **The proxy's error on PnL is 100% of the true value in both
> directions.** It cannot distinguish a 100× gain from a 100× loss on
> identical token flows. It is not a noisy estimator; it is **blind on the
> dimension that determines profit.**

**Therefore the quantity proxy may be used to describe FLOW — what moved,
how much, how long held, how concentrated — and never to describe
profitability.** Using it as a PnL substitute would be a fabrication of the
same species as substituting today's price.

Per-field bias, as recorded in the module's own `bias_table`:

| Output | Affected by price? | Bias |
|---|---|---|
| `tokens_in` / `tokens_out` | No | None — it is a quantity |
| `turnover_ratio` | No | None as a quantity; blind to PnL |
| `first_buy_price_in_quote` | Yes | Only the *first* buy's price — a wallet that bought cheaply and then chased the price up has a misleadingly low "cost" |
| `median_quote_price_seen` | Yes | A median over observed prices; ignores fill size, so a 1-token buy and a 1M-token buy count equally |

The **earliest buy price in token units** (the option named in the brief) is
populated only when a price was actually recovered for that buy. It is never
filled in with today's price.

## 1.6 What the implementation does, live

`leapspace/costs.py` provides:

- `ArchiveRpc` — keyless archive JSON-RPC with runtime archive verification,
  provider rotation, and per-call URL/status logging.
- `read_pool_state(pool, block, chain)` — V2/V3 pool state at a past block.
  Failure modes are distinguished: `POOL_NOT_DEPLOYED_AT_BLOCK`,
  `UNSUPPORTED_POOL`, `no_archive_provider`.
- `swap_price_from_logs(pool, block, token, chain)` — exact executed price.
- `defillama_price(chain, token, ts)` / `defillama_current_price(...)`.
- `geckoterminal_ohlcv(chain, pool, timeframe, ...)` — keyless OHLCV.
- `price_trade(trade, chain, method)` — resolves a price with the method
  ladder `pool_swap → pool_state → defillama → geckoterminal`, recording
  every attempt and its status.
- `fifo_cost_basis(trades)` and `weighted_average_cost_basis(trades)`.
- `quantity_proxy(trades)` and `proxy_bias_test()`.
- `wallet_realised_pnl(trades, chain, basis)` — the top-level call.

### Live end-to-end run (2026-11-03)

Wallet `0x1d48963DD8FAdA6aB5C2C7b92Eba81ECC5030270` (a real PEPE holder
returned by Blockscout), 29 PEPE transfers → 24 trades:

```
archive provider verified: https://eth.drpc.org (status ok, probe block 15798687)
PRICED 24/24 trades with a keyless source          coverage 100.0%
FIFO realised PnL: $300,121.68
cost $104,703,401.22   proceeds $37,487,004.46
remaining qty 2.887e+13   avg cost 3.552122524032228e-06
unpriced trades: 0
WAC realised PnL: $300,118.94
```

The FIFO and weighted-average figures differ by \$2.74 on a \$37M turnover —
that difference **is** the cost-basis convention, and it is reported rather
than hidden.

### Honest degradation — the rule the module never breaks

> A trade whose price cannot be recovered **at its own block** is recorded
> as `UNPRICED`, **excluded** from the realised PnL, and counted in
> `unpriced_trades`. Today's price is never substituted.

`fifo_cost_basis` handles the subtle case: an unpriced **sell** still
consumes FIFO lots (so the inventory stays correct) but books **no** PnL,
and the consumed basis is reported separately as
`basis_consumed_by_unpriced_sells_usd` so the reader knows what was left
unaccounted.

Coverage is always reported alongside the PnL: `coverage_pct`.

### Fee basis

Every figure is **GROSS of gas, DEX fees and MEV**. None of those are
observable from ERC-20 transfers alone; a net figure would require per-swap
gas and fee logs. The module labels this on every output.

## 1.7 The other free sources, and their measured status

| Source | URL form | Keyless? | HTTP status | Limitation |
|---|---|---|---|---|
| DefiLlama historical price | `https://coins.llama.fi/prices/historical/{ts}/{chain}:{token}` | Yes | **200** | Coverage: 15/17 live memecoins had ≥1 historical point; 8/17 had all 5 sampled points. Absence returns HTTP 200 with an **empty price field** — reported as `no_price_at_timestamp`, never as 0 |
| DefiLlama current price | `https://coins.llama.fi/prices/current/{chain}:{token}` | Yes | **200** | Current only |
| DefiLlama chart | `https://coins.llama.fi/chart/{chain}:{token}` | Yes | **200** | **Returns 1 point, not a history.** Measured `n_points=1` for 15/15 tokens tested. Not usable as a price series |
| DefiLlama wrong forms | `https://api.llama.fi/prices/current/...` / `https://coins.llama.fi/price/{chain}/{tok}` / `https://coins.llama.fi/token/{tok}` | Yes | **404** | Wrong routes |
| DefiLlama overview | `https://api.llama.fi/overview/dexs/pepe` | Yes | **500** | Internal server error |
| GeckoTerminal OHLCV | `https://api.geckoterminal.com/api/v2/networks/{net}/pools/{pool}/ohlcv/{tf}` | Yes | **200** | Public tier is capped at **180 days**: `before_timestamp` beyond that returns **HTTP 401** *"You can only access data from the past 180 days with Public API"*. Keyed on the **pool**, not the token |
| CoinGecko market_chart | `https://api.coingecko.com/api/v3/coins/pepe/market_chart` | Yes | no response from this host | Not usable |
| Uniswap subgraph | `https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2` | Yes | no response from this host | Not usable from here |
| Blockscout per-transfer `exchange_rate` | — | Yes | 200 | **The CURRENT rate.** Must not be used for a past trade |

## 1.8 Method comparison

| Method | Needs price API? | Needs archive node? | Accuracy | Coverage | Verdict |
|---|---|---|---|---|---|
| **Pool-state reconstruction** (`getReserves`/`slot0` at the trade's block) | No | **Yes** | **0.12% median / 0.97% max** (measured) | Any Uniswap V2/V3 pair | **PRIMARY** |
| **Swap-event reconstruction** (pool's own `Swap` log) | No | **Yes** | Exact for the swap | Uniswap V2/V3 | **PRIMARY (when the pool is known)** |
| DefiLlama historical price | Yes (free) | No | Reference-grade | 15/17 memecoins | Fallback / cross-check |
| GeckoTerminal OHLCV | Yes (free) | No | OHLCV close | **Last 180 days only** | Fallback for recent trades |
| Quantity proxy | **No** | No | **100% error on PnL** | Total | **Flow only — never PnL** |

---

# PART 2 — Cross-chain identity

## 2.1 The problem being solved

ethereum.org's glossary defines the target precisely:

> **Sybil attack** — "Sybil attacks refer to individual humans tricking a
> system into thinking they are multiple people to increase their
> influence."
> — https://ethereum.org/en/glossary/ (HTTP 200; the standalone
> `/glossary/sybil-attack/` path returns HTTP **404**, so the glossary
> index is the correct citation)

A "whitelist of memecoin whales and consistently successful traders"
cannot be a flat list of addresses. One operator running four wallets
across three chains looks like four independent whales, which
double-counts the operator's positions and understates their
concentration.

Detecting and clustering that is the Sybil problem, applied to
on-chain identity.

## 2.2 The methods, and what is authoritative about each

### (i) First funder / shared funding source

**Definition (Nansen):** the first funder of a wallet is "the earliest
address to send native gas to the input EVM address … on whichever
supported chain the earliest funding happened."
— Nansen, *Address First Funder*:
https://docs.nansen.ai/api/profiler/address-first-funder
(the page's own server returned HTTP 500 to a plain fetch on 2026-11-03;
the endpoint is listed and described in the Nansen Profiler index at
https://docs.nansen.ai/api/profiler, HTTP **200**, which does carry the
*Address First Funder* entry, and the definition text above comes from the
search index of that same page. Nansen's endpoint requires an API key, so
this package reimplements it keylessly.)

**Keyless reimplementation (this package).** Two steps:

1. **Binary search the wallet's first transaction block.** `eth_getTransactionCount(addr, block)`
   returns the address's nonce as of that block. The smallest block whose
   nonce is ≥ 1 is the wallet's first-transaction block. Cost:
   ⌈log₂(latest)⌉ calls ≈ **25 on Ethereum**, measured at **14.3 s**.
2. **Find the earliest inbound native transfer.** Read that block; if a
   transaction sent value *to* the wallet, its `from` is the funder. If
   the wallet already held a balance before that block, it was funded
   earlier: scan backwards (bounded; the bound is reported) for the
   earliest inbound value transfer.

The evidence — block number, transaction hash, value in wei — is returned
with the answer, so it can be checked against the chain by hand.

**Measured:** Ethereum, wallet `0x1d48963DD8FAdA6aB5C2C7b92Eba81ECC5030270`:
first-transaction block **24,592,010** located in 25 RPC calls; the
wallet's first tx is
`0x16c0538b7c548efe47fa6999777c5ca9294db6e95cac4129592f6d4e579114fe`.
The wallet held a balance before that block, so the funder required the
backward scan.

**Why this signal is dangerous on its own:** two unrelated users
withdrawing from the same exchange hot wallet share a first funder. The
module therefore reports the funder's identity and whether it is a
high-volume entity, and **never** labels such a link CONFIRMED.

### (ii) Common counterparties

The addresses a wallet transacts with — routers, pools, bridges, CEX hot
wallets. Nansen exposes the same concept as *Address Counterparties*
(https://docs.nansen.ai/api/profiler/address-counterparties) and
*Address Related Wallets*
(https://docs.nansen.ai/api/profiler/address-related-wallets).

**Measured sources.** Blockscout v2 `/api/v2/addresses/{a}/transactions`
returned HTTP **200** on: ethereum, optimism, gnosis, zksync, scroll, celo.
It returned HTTP **403** (a Cloudflare *"Just a moment…"* interstitial) on
**base, arbitrum and polygon**, and HTTP **404** on bsc — so those chains
fall back to raw JSON-RPC rather than pretending.

The raw RPC fallback is weak and says so: free public RPC has no
address-indexed transaction list, so only the latest block's transactions
are read, and the window is reported as `block_window`.

**Bias:** shared venues are shared by *everyone*. The same routers and the
same CEX hot wallets appear in almost every wallet's counterparty set. The
module computes the Jaccard overlap but **caps the score at 0.3** when the
overlap is total and involves more than three counterparties, because a
total overlap usually means a shared ROUTER rather than a shared operator.

### (iii) Correlated timing

Two wallets whose activity timestamps cluster together are more likely to
be driven by one decision process.

**Measured implementation:** a ±1-hour tolerance, counting how many of
each wallet's timestamps fall within the other's, reported as
`a_coverage`, `b_coverage` and a Jaccard overlap of the matched sets.

**This is the weakest signal and the module says so.** Market-wide events,
an airdrop, a MEV bot fleet and an indexer all produce coincident timing.
It is capped at 20% of the score and it alone can never produce a
CONFIRMED label.

### (iv) Similar position sizes

The same operator tends to size positions similarly across their wallets.
Measured implementation compares the **median** absolute trade size (the
median, so one whale trade does not dominate) and the median relative gap
between the two sorted size distributions.

**Bias:** two unrelated wallets trading the same popular token will often
have similar sizes, because the token's own liquidity sets the natural
order of magnitude. Capped at 10% of the score.

### Bridging flows

A bridging flow is the one identity signal that is not statistical. If a
wallet calls a bridge contract and another wallet we observe receives the
delivery on the other chain, the bridge's own records state the
connection directly.

The module scans the wallet's transactions for calls to a **registry of
known bridge contracts** and reports the source-side evidence (bridge
address, source tx hash, block, timestamp). An unregistered bridge is
**not** guessed at.

## 2.3 The linker's scoring rule

**The weights are analyst choices.** No regulator, standard-setter or
vendor publishes a cross-chain link-scoring formula, and none of the four
signals is published as a clustering algorithm in its own right. The
weights are stated in `crosschain.SIGNAL_WEIGHTS` so the score is
auditable and adjustable.

| Signal | Weight | Normalisation | Notes |
|---|---|---|---|
| Shared funding source | **0.40** | 1.0 if the first funders match, 0.0 if they differ, **0.2** if the funder is a known high-volume entity, **not scored** if the funder could not be determined | A signal that could not be evaluated contributes **nothing** to the score — it is never treated as evidence of independence |
| Common counterparties | **0.30** | Jaccard overlap of the two counterparty sets, **capped at 0.3** when the overlap is total and involves >3 counterparties | |
| Correlated timing | **0.20** | `0.5·a_coverage + 0.5·b_coverage` at ±1 h | Correlation, not causation |
| Similar position sizes | **0.10** | `1 − median_relative_gap` | |

`score = Σ(scoreᵢ × weightᵢ) / Σ(weightᵢ)` over the signals that were
**evaluable**. A wallet missing two of four signals therefore cannot reach a
high score on the two it has — which is the correct behaviour.

### Thresholds

| Label | Condition |
|---|---|
| **CONFIRMED** | An explicit on-chain artefact exists (below). The score is reported but is not what decides the label. |
| **SUGGESTED** | No artefact, but `score ≥ 0.45` |
| **NOT_SUGGESTED** | No artefact and `score < 0.45` |

### What CONFIRMS a link

A CONFIRMED label requires an **on-chain artefact that can be re-read from
the chain**. Three qualify:

1. **`BRIDGE_TRANSFER`** — one wallet sent a transaction to a bridge
   contract and the other wallet received the delivery on the other chain.
   The artefact is the pair of transaction hashes.
2. **`SHARED_FUNDER_IS_BRIDGE`** — the two wallets share a first funder
   **and** that funder is itself a registered bridge contract. The bridge
   is a single named on-chain entity, so the funding is a bridge delivery
   rather than an incidental shared EOA. The artefact is the funder's
   contract code plus the two funding transactions.
3. **`IDENTICAL_FUNDER_NONCE_SEQUENCE`** — one sender funded both wallets
   in the **same block**. That is a direct on-chain statement that the two
   addresses were created together. The artefact is the two funding
   transaction hashes and the shared block number.

Every confirmation carries the transaction hashes it rests on, so the claim
is **traceable, not asserted**.

### Verified scoring behaviour

`crosschain.self_test()` (synthetic fixtures with known answers) — all
checks pass:

```
related_scores_high                       True    (score 0.9935)
related_is_not_confirmed_without_artefact  True    (SUGGESTED)
unrelated_scores_low                       True    (score 0.0000)
same_block_funder_is_confirmed             True    (CONFIRMED)
bridge_transfer_is_confirmed               True    (CONFIRMED)
bridge_confirmation_carries_tx_hashes      True
```

Note the second check: two wallets with the same funder, the same
counterparties, near-identical timing and near-identical sizes score 0.99
and are still only **SUGGESTED**, because no on-chain artefact links them.

## 2.4 What the cross-chain sources can and cannot reach

| Source | Chains | Status | Note |
|---|---|---|---|
| Blockscout v2 API | ethereum, optimism, gnosis, zksync, scroll, celo | **HTTP 200** | Primary counterparty source |
| Blockscout v2 API | base, arbitrum, polygon | **HTTP 403** | Cloudflare interstitial; falls back to JSON-RPC |
| Blockscout v2 API | bsc, linea | **HTTP 404** | No such host route |
| `https://explorer.mantle.xyz` | mantle | **HTTP 502** | |
| `https://blastscan.io` | blast | DNS/transport failure | |
| Routescan native v2 (`/v2/network/{net}/evm/all/address/{a}/transactions`) | mainnet | **HTTP 200** (25 items) | Works; the base/arbitrum variants returned **HTTP 400** (params validation) |
| Routescan etherscan proxy (`.../etherscan/api?module=account&action=txlist`) | all | **HTTP 200** but body `{"status":"0","message":"An error occurred"}` | Not usable |
| Etherscan V2 without a key | arbitrum | **HTTP 200** but body `"Missing/Invalid API Key"` | Not usable |
| Ethplorer `getAddressInfo` | ethereum | **HTTP 200** | `getTxIn` returned **HTTP 404** |
| Covalent / OKLink / Arkham / Tenderly / 4everland | — | **401 / 404 / DNS failure** | All require a key or are unreachable |

**Per-chain RPC reachability (all HTTP 200 for `eth_blockNumber`):**
ethereum `eth.drpc.org`; base `base-rpc.publicnode.com`;
arbitrum `arbitrum-one-rpc.publicnode.com`;
polygon `polygon-bor-rpc.publicnode.com`; bsc `bsc-rpc.publicnode.com`;
optimism `optimism-rpc.publicnode.com`; gnosis `gnosis-rpc.publicnode.com`.

---

# PART 3 — Files, and how to reproduce

## 3.1 Files created or modified

| Path | What it is |
|---|---|
| `leapspace/costs.py` | **New.** The free PnL module: archive RPC client, pool-state and swap-event reconstruction, DefiLlama and GeckoTerminal adapters, FIFO and weighted-average cost basis, quantity proxy, bias test, self-test |
| `leapspace/crosschain.py` | **New.** The candidate cross-chain linker: first-funder detection, counterparty/timing/size signals, pairwise scoring, confirmation artefacts, self-test |
| `CROSSCHAIN_WALLET_METHODS.md` | **New.** This document |
| `tools/probe_archive_rpc.py` | Archive-provider sweep (30 candidates) |
| `tools/probe_price_sources.py` | Archive verification + DefiLlama / GeckoTerminal / CoinGecko / subgraph probes |
| `tools/probe_depth.py` | Archive depth per block era; DefiLlama history depth; GeckoTerminal 180-day cap |
| `tools/probe_pool_vs_llama.py` | **The accuracy measurement** (§1.3 Test A) |
| `tools/probe_defillama_coverage.py` | DefiLlama coverage over 17 live memecoins |
| `tools/probe_crosschain_sources{,2,3}.py` | Explorer and API sweeps across 13 chains |
| `tools/probe_funder_and_archive.py` | First-funder algorithm + per-chain archive test |
| `tools/probe_archive_chains.py` | Archive sweep for the six non-Ethereum chains |
| `tools/live_pnl_and_links.py` | **Live end-to-end:** real wallet → real trades → real PnL → real links |
| `tools/live_pool_trades.py` | **Live end-to-end on real pool counterparties** |
| `reports/probe_*.json`, `reports/live_*.json` | The raw output of every probe, including every HTTP status |

## 3.2 Reproducing

```bash
cd leapspace-quant
python -m leapspace.costs          # self-test: FIFO/WAC arithmetic + live DefiLlama read
python -m leapspace.crosschain     # self-test: scoring + confirmation boundary
python tools/live_pnl_and_links.py # full live run
python tools/live_pool_trades.py   # accuracy on real pool trades
```

## 3.3 The rules this implementation holds to

1. **Today's price is never substituted for a past trade.** A trade that
   cannot be priced is `UNPRICED`, excluded, and counted.
2. **Coverage is reported next to every PnL figure**, never implied.
3. **A signal that could not be evaluated contributes nothing** to a score.
   It is not evidence of independence.
4. **CONFIRMED requires a re-readable on-chain artefact**, with
   transaction hashes.
5. **Weights, thresholds and any non-citable number are labelled as
   analyst choices** in the code, in the output, and here.
6. **Every HTTP status in this document came from a real call.** Sources
   that were unreachable are listed with the status that proved it, rather
   than omitted.
