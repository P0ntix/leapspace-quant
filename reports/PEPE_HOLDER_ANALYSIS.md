# PEPE Top Holders — Allocation Patterns and Trading Process

**Run:** 2026-11-03 · **Module:** `leapspace/memecoinscan.py` · **CLI:** `python -m leapspace.cli memeflow --token 0x6982508145454ce325ddbe47a25d4ec3d2311933 --top 50`
**Raw data:** `reports/pepe_holder_scan.json` · **All figures are LIVE reads.**

---

## 1. Who the top 50 actually are

Pulled from Blockscout's public holders API, then classified:

| Class | N | What it is |
|---|---|---|
| **Exchange hot wallets** | **27** | Binance ×2, Bybit, OKX ×3, Kraken ×2, **Robinhood ×2**, Revolut, MEXC, Gate.io ×2, HTX, Crypto.com ×2, Bitpanda, Poloniex, Bithumb, BTCTurk, Upbit, ChangeNow, CoinSpot |
| Contracts (pools/vaults) | 5 | DEX pools, staking vaults |
| Burn/dead addresses | 1 | `0x…dEaD` — excluded |
| **Individual EOAs** | **17** | The only candidates for "traders" |

**54% of the "top holders" are exchanges.** Any analysis that treats the raw holder list as traders is measuring custody, not skill. Blockscout supplies the entity tags, which is what made the split possible.

Two of the 17 EOAs were then caught by a second test: they transact **with a known exchange address**. One moves PEPE in and out of **Robinhood's** address. Those two are custody/market-making flow, leaving **15 personal memecoin traders**.

## 2. The 15 personal traders

| Wallet | Memes | Live value | Top position | Median hold |
|---|---|---|---|---|
| `0xbf45fB5D20BC3D…` | 1 | $38.4M | PEPE 100% | never sold |
| `0x262190CCE7b251…` | 1 | $29.5M | PEPE 100% | never sold |
| `0x59779b3aa3540F…` | 1 | $29.5M | PEPE 100% | never sold |
| `0x72132bF09a9ee6…` | 1 | $22.2M | PEPE 100% | never sold |
| `0xd4Bb423838a663…` | 1 | $21.9M | PEPE 100% | 320d |
| `0x4879675Da42274…` | 3 | $18.2M | PEPE 80.2% / SHIB 9.9% / FLOKI 9.9% | 0.07d |
| `0x442689F3F26cBc…` | 3 | $12.5M | PEPE 75.2% / SHIB 24.6% / TURBO 0.2% | 171d |
| `0xaDFffc33cdC997…` | 1 | $12.2M | PEPE 100% | 142d |
| **`0xAf2358e9868326…`** | **5** | $12.0M | PEPE + FLOKI + SHIB + TURBO + MOODENG | **2.6d** |
| `0xEd0203625D3Ef9…` | 1 | $10.6M | PEPE 100% | 192d |
| `0xE8f2C2D63443A0…` | 2 | $10.5M | PEPE 100% | never sold |
| `0xcbC9fAD51b83a5…` | 2 | $10.0M | PEPE 100% | never sold |
| `0x80374c1F677FF6…` | 1 | $9.2M | PEPE 100% | never sold |
| `0xa5F7f1dCE1D1E4…` | 2 | $1.9M | PEPE 100% | 107d |
| *(1 further wallet, values in the JSON)* | | | | |

## 3. The patterns

**Selection.** PEPE 15/15 wallets, MOODENG 5, SHIB 3, FLOKI 2, TURBO 2, MOG 1. PEPE is universal; MOODENG is the clear second choice.

**Entry timing — the headline finding.** Measured in blocks after each token's launch block (from the contract's creation transaction):

| Entry class | Positions |
|---|---|
| late (≥100k blocks) | **24** |
| early (<10k blocks) | 1 |
| very early (<1000 blocks) | 1 |
| unknown | 2 |

**Median entry lag: 6,615,284 blocks — roughly 2.4 years after PEPE launched.** These wallets are *late* entrants. They are not snipers, not early believers, not the people who found PEPE.

**Allocation concentration.** Median largest-position share **100%** (range 75.2%–100%). Ten of fifteen are 100% single-token.

**Sizing and cadence.** Median position $10.6M, median **6 buys per token**, median hold **142 days** (n=8).

## 4. Two archetypes, one of which is not a trader

**Archetype A — concentrated late accumulator (10 of 15).** 100% PEPE, median 6 buys, never sold, median entry lag 6.9M blocks. These are holders of a token that already succeeded, buying on the way up or after. Their "process" is not a trading process.

**Archetype B — diversified late accumulator (4 of 15).** 2–3 memes, holds from 0.07 days to 320 days, still 75–80% PEPE.

**Archetype C — the one genuine active trader (`0xAf2358e9868326…`).** Five memes, median hold **2.62 days**, and the only early entries in the sample: **TURBO at 745 blocks** and **PEPE at 1,440 blocks** after launch. It also bought SHIB 34 times and FLOKI 5 times, and exited FLOKI, SHIB and TURBO entirely while keeping PEPE and MOODENG. Its pattern: *buy almost immediately after launch, scale in with many small orders, rotate out of the laggards, keep the winner.*

## 5. What this does and does not support

**It does not support "top PEPE holders are successful memecoin traders."** The median holder entered ~2.4 years after launch with a 100% single-token position and a 142-day hold. That is not a repeatable trading process — it is what surviving in the one meme that worked looks like. **The sample is selected on the outcome**: these wallets still hold PEPE, and the traders who sold PEPE are invisible here. This is the survivorship bias the package's own source-reliability register warns about (GIPS 3.A.9's analogue).

**It does support one narrow finding:** among this sample there is exactly one wallet that looks like an active early memecoin trader, and its signature is *enter within ~1,000–1,500 blocks of launch, scale in with many small buys, rotate out losers, keep the winner*. One wallet is an anecdote, not a strategy — it is a lead to test on a larger, less biased sample, not a conclusion.

### Measured limitations

- **Realised PnL is NOT computed.** No keyless historical price source exists for these contracts from this host: DefiLlama's price API does not index them by contract (`{"coins": {}}`), CoinGecko's `market_chart` returns **401**, and Blockscout's per-transfer `exchange_rate` is the **current** rate (verified constant at 0.00000471 across rows spanning October), not the rate at that block. All values here are at **today's live price** — exact for a current portfolio, but **not a cost basis**.
- **Windowing.** Blockscout returns newest-first, and the per-token query is capped at 200 transfers per token per wallet. A wallet's oldest trades may be absent.
- **Ethereum only.** Blockscout's base/bsc/arbitrum/gnosis hosts do not answer from this host; RugCheck and Jupiter are Solana-only. Solana-native memes (WIF, BONK, POPCAT, PNUT…) are therefore outside the universe — 17 of the 30 requested symbols resolved to nothing *because they are not on Ethereum*, which is recorded as a gap rather than a zero.
- **13-token universe**, live from DexScreener with a $50k liquidity floor so an impostor ticker cannot displace the real token.

## 6. Reproduce

```bash
python -m leapspace.cli memeflow --token 0x6982508145454ce325ddbe47a25d4ec3d2311933 --top 50
python -m leapspace.cli memeflow --token <any ethereum memecoin> --top 50 --json
```

### Sources

| Source | URL | Used for |
|---|---|---|
| Blockscout | `https://eth.blockscout.com/api/v2/tokens/{addr}/holders` | Top 50 holders, entity tags |
| Blockscout | `https://eth.blockscout.com/api/v2/addresses/{addr}/token-transfers?token={addr}` | Per-wallet, per-token history |
| Blockscout | `https://eth.blockscout.com/api/v2/addresses/{token}` | Creation tx → launch block |
| Ethereum RPC | `https://ethereum-rpc.publicnode.com` | `eth_getTransactionByHash`, `eth_getBlockByNumber` |
| DexScreener | `https://api.dexscreener.com/latest/dex/search?q={symbol}` | Token addresses + live price/market cap |
