# Memecoin Trader Screening — A Methodology That Works on Old and New Memes

**Package:** `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant`
**Modules:** `memecoinscan.py`, `launchscan.py`, `edge.py`, `whitelist.py`, `social.py`, `traders.py`
**CLI:** `memeflow`, `launchscan`, `edge`, `whitelist`

This is the operational method for finding memecoin traders with a *real,
consistent* edge — and it is designed to run identically on a two-year-old
token and on one that launched an hour ago.

---

## 0. The problem with the obvious approach

"Top holders of the winning token" is not a method. It is a way of
selecting on the outcome. Three things go wrong, and each one has a fix
below:

| Failure | Why it happens | Fix |
|---|---|---|
| You select exchanges, not traders | CEX hot wallets hold the largest balances of every token | classify every holder before inferring anything (§2) |
| You select winners, not skill | The sample is the wallets that still hold | screen an unbiased universe, and correct for the number of candidates (§4.3) |
| You select one lucky trade | A single 500x carries the whole PnL | explicit fluke tests (§4.2) |

---

## 1. Two entry points, one method

The same method serves both cases. What differs is **where the wallets
come from**, not what you do with them.

```
                        OLD MEME (PEPE)              NEW MEME (launched 1h ago)
                        ─────────────────            ─────────────────────────
STEP 1  find wallets    top-holder list,             transfers in the first
                        exchange wallets removed      N blocks after launch
STEP 2  get record     their history on the         their history on OTHER
                        meme universe                established memes
STEP 3  test edge       consistency gate (§4)        consistency gate (§4)
STEP 4  social check   did they buy before or       did they buy before or
                        after the narrative?         after the narrative?
STEP 5  whitelist      promote with evidence        promote with evidence
```

`memeflow` runs the OLD path. `launchscan` runs the NEW path. Both end at
the same gate.

---

## 2. Step 1 — find the right wallets, and classify them first

**Old memes.** Blockscout's holders API returns 50 per page with an
`address.metadata.tags` field naming the owner of the address. On PEPE's
top 50 that field identified **27 exchange hot wallets** — Binance ×2,
Bybit, OKX ×3, Kraken ×2, Robinhood ×2, Revolut, MEXC, Gate.io ×2, HTX,
Crypto.com ×2, Bitpanda, Poloniex, Bithumb, BTCTurk, Upbit, ChangeNow,
CoinSpot. **54% of the "top holders" were custody, not traders.**

Classification is three-way: `EXCHANGE` (tagged), `CONTRACT`
(`is_contract`), `EOA` (neither), plus an explicit burn/dead-address
exclusion.

**Second test, because tagging is not exhaustive.** Blockscout does not
tag every custodial wallet. Two of PEPE's 17 "EOAs" transacted with a
known exchange address — one moved PEPE in and out of **Robinhood's**
address. Those are custody/market-making flow, not personal trading, and
they are flagged `flows_to_exchange`.

**New memes.** The launch window is the only window in which being early
is still possible. `launchscan.early_buyers()` reads the token's
transfers, resolves the launch block from the contract's creation
transaction, and takes buyers within the first N blocks.

On a live test the very first wallet in the window **was the deployer**,
in the same block as the launch (`lag=0`, creator address identical). The
launch scan finds insiders by construction — it does not need a
hand-maintained insider list to catch them.

---

## 3. Step 2 — get each wallet's actual trading record

Free, keyless, and verified live:

| What | Source | Endpoint |
|---|---|---|
| Per-token transfer history | Blockscout | `/api/v2/addresses/{addr}/token-transfers?token={addr}` |
| Token holders + entity tags | Blockscout | `/api/v2/tokens/{addr}/holders` |
| Launch block | Blockscout + RPC | `/api/v2/addresses/{token}` → `eth_getTransactionByHash` |
| Live price / mcap / liquidity | DexScreener | `/latest/dex/search?q={symbol}` |

**Query per token, not generically.** A wallet's generic transfer history
is dominated by whatever it trades most (usually DeFi). Scanning it
returned **zero** memecoins for every wallet tested, because their recent
activity is ZRO, CRV, MORPHO, WLD. Filtering by token is the only way to
see the memecoin trades.

**The universe is resolved live.** Addresses are never typed from memory:
each symbol is resolved through DexScreener with a $50k liquidity floor so
an impostor ticker cannot displace the real token. On Ethereum that
yielded 13 live memes (PEPE, SHIB, FLOKI, TURBO, MOG, MEME, NEIRO,
USUAL, GIGA, WOJAK, MOODENG, TRUMP, BRETT). The 17 symbols that
resolved to nothing are Solana-native memes — recorded as **gaps, not
zeros**.

---

## 4. Step 3 — the consistency gate (`leapspace/edge.py`)

This is the part that separates a trader from a fluke. Five independent
rejection tests, each with its authority attached.

### 4.1 The tests

| Test | Rejects when | Authority |
|---|---|---|
| `largest_win_share` | one trade carries >50% of total PnL | ANALYST_CHOICE |
| `skill_not_distinguishable` | P(win rate > 50%) < 0.95 | Beta-Binomial (cited) |
| `deflated_sharpe` | DSR ≤ 0 after correcting for candidates scanned | Bailey & López de Prado (cited) |
| `edge_decay` | recent expectancy < 0.5× early expectancy | ANALYST_CHOICE |
| `insufficient_independent_bets` / `single_token_only` / `too_few_closed_trades` | too few independent bets, one token, or too few trades | ANALYST_CHOICE |

**Skill probability is exact.** With a uniform Beta(1,1) prior, the
posterior probability that the true win rate exceeds 50% is *identical* to
the one-sided binomial tail probability of the observed win count. So
`math.comb` gives the exact answer with no SciPy and no floating-point
cancellation. Verified: P(X≤50|n=100) = 0.5398, P(X≤60|n=100) = 0.9824.

**Independent bets, not trades.** A bet is a sequence of trades in one
asset where the position is not closed before the next opens. Scaling into
one token 40 times is **one** bet, and one bet tells you nothing. This
was a real bug during development: counting over closed trades only
dropped the buy legs and returned 0 bets for every wallet.

**The Deflated Sharpe is the selection-bias correction.** It uses the
expected maximum Sharpe from N trials under the null, so scanning 500
wallets and keeping the best sets a far higher bar than scanning 5:

| candidates scanned | sr₀ | DSR | verdict |
|---|---|---|---|
| 1 | 0.000 | 1.0000 | CONSISTENT |
| 10 | 1.575 | 0.0000 | CONSISTENT |
| 100 | 2.531 | 0.0000 | FLUKE |
| 10,000 | 3.861 | 0.0000 | FLUKE |

**The same wallet, the same trades, gets harder to qualify as the scan
widens.** That is the whole point, and it is why the number of candidates
screened must be reported honestly with every entry.

### 4.2 Verdict precedence

A definitive rejection binds first. A wallet with one lucky win carrying
the PnL is **FLUKE** whether or not it also has too few trades — a thin
sample must not excuse a fluke. Insufficiencies alone give **INSUFFICIENT**
(cannot assess yet). Only a wallet that survives everything is
**CONSISTENT**.

### 4.3 Validated against known ground truth

Six synthetic wallets, each built with an exact win rate:

| Wallet | Verdict | Correct? |
|---|---|---|
| 80 trades, 10 tokens, 62% win | CONSISTENT | ✅ |
| one 500k win + 19 tiny wins | FLUKE | ✅ |
| 40 trades, exactly 50% win | FLUKE | ✅ |
| early wins, recent losses | FLUKE | ✅ |
| 40 trades, 1 token | INSUFFICIENT | ✅ |
| 10 trades | INSUFFICIENT | ✅ |

---

## 5. Step 4 — the social / narrative check

`social.py` measures narrative and traction, and `socialedge.py` (see
`NARRATIVE_EDGE_METHODOLOGY.md`) turns it into a lead-time test.

**What is actually measurable for free:**

| Signal | Source | Free? |
|---|---|---|
| Community membership | `t.me/s/{username}` | yes, no key |
| Community membership | `discord.com/api/v9/invites/{code}?with_counts=true` | yes, no key |
| Platform breadth | DexScreener `info.socials` | yes, no key |
| Project description | DexScreener global profile/boost lists | yes, 30 tokens each |
| Organic traction | Jupiter `organicScore`, `stats24h` | yes, Solana only |
| Risk | RugCheck full report | yes, Solana only |
| X/Twitter followers | — | **no. Pay-per-use only, ToS forbids scraping.** |

**The validity trap.** A **nonexistent** Telegram channel still returns
HTTP 200 — its title reads `Telegram: Contact @name`, not
`Telegram: View @name`. Only the latter is a channel with a member count.
The parser requires the `View` title *and* a member count; otherwise the
platform is reported **unmeasured**, never zero.

**Membership vs reach.** Telegram and Discord are membership; X, TikTok,
Instagram, YouTube, Reddit, Threads are reach. On live data BONK scored
7.0 with Telegram + Discord, while Ethereum PEPE scored 1.0 with the
explicit reason *"broadcast only — reach without membership"*.

---

## 6. Step 5 — the whitelist (`leapspace/whitelist.py`)

An entry carries: the address(es), the chains, the edge verdict and its
metrics, the **evidence** (which trades, which tokens, which period), the
**number of candidates scanned**, and a timestamp + reason for every
transition.

Statuses: `WHITELISTED` · `WATCH` · `FLUKE` (rejected, retained in the
record) · `RETIRED` (left the forward cohort, history retained).

**Nothing is ever deleted.** A retired wallet leaves the forward cohort
but its evaluation history stays in the reported record — CFA Institute
GIPS 3.A.9: *"Terminated portfolios must be included in the historical
performance of the composite up to the last full measurement period."*
Rejected candidates are counted and reported too, because that count is
what the Deflated Sharpe is corrected for and the scan's selection bias
must be visible.

**Cross-chain.** An entry is keyed on a *canonical identity*: one address,
or a cluster id established by `crosschain.py` with traceable on-chain
evidence. A link that is only SUGGESTED is stored as a suggestion and is
never merged into a confirmed identity.

---

## 7. What this method CANNOT tell you

- **It cannot compute realised PnL from a true cost basis** on this host
  yet. No keyless historical price source exists for these contracts:
  DefiLlama does not index them by contract, CoinGecko's `market_chart`
  returns 401, and Blockscout's per-transfer `exchange_rate` is the
  *current* rate, not the rate at that block. All values are at today's
  live price — exact for a current portfolio, **not** a cost basis. See
  `CROSSCHAIN_WALLET_METHODS.md` and `costs.py` for the options and their
  bias.
- **It cannot infer skill from a survivorship-selected holder list.** The
  PEPE scan's honest finding was that the median holder entered **2.4
  years after launch** with a 100% single-token position — late
  accumulators of the one meme that won, not traders. That is why the
  NEW-meme path exists: it screens an unbiased universe of early buyers
  and tests their prior records.
- **It does not claim a "successful trader" label.** The thresholds are
  mostly analyst choices and say so. What is cited is the sample-size
  formula, the Wilson interval, the Beta-Binomial skill probability, the
  Deflated Sharpe, and the GIPS retention rule.

---

## 8. Reproduce

```bash
# OLD meme: top holders -> classified -> allocation patterns
python -m leapspace.cli memeflow --token 0x6982508145454ce325ddbe47a25d4ec3d2311933 --top 50

# NEW meme: launch window -> early buyers -> prior records -> edge gate
python -m leapspace.cli launchscan --token <new memecoin> --window 1000

# The consistency gate on any trade list
python -m leapspace.cli edge --trades trades.json --trials 500

# The whitelist
python -m leapspace.cli whitelist
python -m leapspace.cli whitelist --wallet 0x... --trades trades.json --trials 500
```

---

## 9. Source register

| Source | URL | Role |
|---|---|---|
| Blockscout | `https://eth.blockscout.com/api/v2/...` | holders, transfers, creation tx |
| Ethereum RPC | `https://ethereum-rpc.publicnode.com` | launch block + timestamp |
| DexScreener | `https://api.dexscreener.com/latest/dex/search?q=` | token universe, prices |
| Telegram | `https://t.me/s/{username}` | community size |
| Discord | `https://discord.com/api/v9/invites/{code}?with_counts=true` | community size |
| Jupiter | `https://lite-api.jup.ag/tokens/v2/search?query=` | organic traction (Solana) |
| RugCheck | `https://api.rugcheck.xyz/v1/tokens/{mint}/report` | risk + insider flags (Solana) |
| NIST | `https://www.itl.nist.gov/div898/handbook/prc/section2/prc242.htm` | sample size |
| NIST | `https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm` | Wilson interval |
| CFA Institute | `https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/sharpe-ratio-and-the-information-ratio.pdf` | Sharpe definition |
| CFA Institute (GIPS) | `https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf` | 3.A.9 retention, 2.B.7 fee basis |
