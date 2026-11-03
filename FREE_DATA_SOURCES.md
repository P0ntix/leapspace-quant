# Free data sources for memecoin & wallet data

**Generated:** 2026-11-03T02:09:34.907081+00:00

**Sources catalogued:** 156 | **verified working free:** 67 | **usable as a package fallback:** 51 | **need a key:** 30

Every HTTP status in this document and in `data/free_data_sources.json` came from a call actually made from this host during the survey. Nothing was copied from documentation. Where a source could not be reached, the real failure mode is recorded.


## Read this first - host facts that change how you probe

These were established by live probing and they invalidate the obvious approach to more than one provider.

- **ssl:** certifi's CA bundle is required - the Windows CA store mis-validates some chains (valid Let's Encrypt certs read as expired). leapspace/http.py already builds the context with certifi.where().
- **network filter:** The host sits behind a Sangfor NGAF URL filter. Blocked hosts are answered with HTTP 200 + an HTML block page, so a status code alone is not proof of data. See tools/freeprobe/validate.py.
- **coin gecko:** api.coingecko.com fails the TLS handshake (WinError 10054) from this host; pro-api.coingecko.com and www.coingecko.com answer normally.
- **reddit:** All reddit.com .json paths return HTTP 403; .rss works.
- **discord widget:** The widget endpoint only returns data for guilds that have the widget enabled.

- **A 200 status code is not proof of data.** This host sits behind a Sangfor NGAF URL filter that answers blocked requests with HTTP 200 and an HTML block page. `tools/freeprobe/validate.py` re-checks every probe body for block markers; 10 false positives were found and excluded from the 'working' list.
- **Blockscout `/api/v2/tokens` returns `{"items":[...]}`**, not a bare list. Read `items[i].address_hash`, not `items[i].address`.
- **Blockscout holder rows** put the address at `items[i].address.hash`, not `items[i].address_hash`.


## VERIFIED-WORKING-FREE (top 20)

All of these returned HTTP 2xx with real, correctly-shaped data on a live call from this host.

| # | Endpoint | Live status | Purpose |
|---|----------|-------------|---------|
| 1 | `https://coins.llama.fi/prices/historical/{unix_timestamp}/{chain}:{token_address}` | ok (HTTP 200) | Historical price for an OLD contract address at a PAST timestamp (the cost-basis fix) |
| 2 | `https://coins.llama.fi/prices/current/{chain}:{token_address}` | ok (HTTP 200) | Current price for a contract address (and batch quotes) |
| 3 | `https://coins.llama.fi/prices/historical/{unix_timestamp}/{chain1}:{addr1},{chain2}:{addr2}` | ok (HTTP 200) | Several old contracts at one past timestamp in one call |
| 4 | `https://eth.blockscout.com/api/v2/tokens/{token_address}/holders` | ok (HTTP 200) | EVM token holder list for Ethereum (top holders of the top token on this chain) |
| 5 | `https://gnosis.blockscout.com/api/v2/tokens/{token_address}/holders` | ok (HTTP 200) | EVM token holder list for Gnosis (top holders of LINK) |
| 6 | `https://api.routescan.io/v2/network/mainnet/evm/1/erc20/{token_address}/holders` | ok (HTTP 200) | EVM token holder list for Ethereum, keyless |
| 7 | `https://eth.blockscout.com/api/v2/addresses/{address}/token-transfers` | ok (HTTP 200) | Wallet token-trade history for an EVM address |
| 8 | `https://eth.blockscout.com/api/v2/tokens/{token_address}/transfers` | ok (HTTP 200) | Token-wide trade history (all transfers of one token) |
| 9 | `https://eth.blockscout.com/api/v2/addresses/{address}/internal-transactions` | ok (HTTP 200) | Wallet internal trade history for an EVM address |
| 10 | `https://api.routescan.io/v2/network/mainnet/evm/all/address/{address}/transactions` | ok (HTTP 200) | Wallet transaction history for an EVM address, keyless |
| 11 | `https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={ms}&endTime={ms}&limit={n}` | ok (HTTP 200) | Historical daily/hourly prices for a LISTED symbol |
| 12 | `https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={ms}&endTime={ms}` | ok (HTTP 200) | Historical daily prices for a listed symbol |
| 13 | `https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}` | ok (HTTP 200) | OHLCV price history for a DEX pool (contract-address based) |
| 14 | `https://api.dexscreener.com/latest/dex/tokens/{token_address}` | ok (HTTP 200) | Current price, liquidity and pool list for a contract address |
| 15 | `https://apewisdom.io/api/v1.0/filter/{filter}` | ok (HTTP 200) | Social-mention ranking of tickers (memecoin narrative signal) |
| 16 | `https://www.reddit.com/r/{subreddit}/new.rss?limit={n}` | ok (HTTP 200) | Subreddit posts as Atom/RSS - the working Reddit path from this host |
| 17 | `https://discord.com/api/guilds/{guild_id}/widget.json` | ok (HTTP 200) | Discord server name, channels and ONLINE MEMBER COUNT |
| 18 | `https://discord.com/api/v9/invites/{code}?with_counts=true` | ok (HTTP 200) | Discord server member/online counts from an invite code |
| 19 | `https://t.me/s/{channel_username}` | ok (HTTP 200) | Recent posts from a public Telegram channel |
| 20 | `https://trends.google.com/trending/rss?geo={geo}` | ok (HTTP 200) | Official Google Trends trending searches (no key) |

The full top-20 list is repeated at the end of this document for a at-a-glance check.


## NEEDS A KEY (free tier where one exists)

These were live-tested without a key. `live_status` is the real response. The free tier and its limits are stated; a paid tier is never described as free.

| Source | Live status | Needs | Free tier | Published rate limit |
|--------|-------------|-------|-----------|----------------------|
| Etherscan API V2 tokenholderlist | error (HTTP 200) - API-level error in the body despite HTTP 200 | EVM token holder list (Ethereum + some chains) | Etherscan V2 free tier: 100,000 calls/day for Ethereum. IMPORTANT: the live probe showed the free plan is LIMITED TO CHAIN ID 1 - other chain ids returned 'Free API access is not supported for this chain. Please upgrade your api plan'. | Free plan 100,000 calls/day; 5 req/s |
| Etherscan API V2 (non-Ethereum chains) | error (HTTP 200) - API-level error in the body despite HTTP 200 | EVM token holder list on non-Ethereum chains | free tier covers Ethereum only; other chains need a paid plan | Free plan 100,000 calls/day (chain 1 only) |
| Moralis token owners | dns_fail (HTTP None) | EVM token holder list | Moralis free tier: 40,000 compute units/day, 2 req/s | 40,000 CU/day; 2 req/s |
| OKLink explorer token ranking | http_404 (HTTP 404) | EVM token holder list | OKLink free tier: 100,000 data points/day | 100,000 data points/day |
| Covalent token holders | http_401 (HTTP 401) | EVM token holder list | Covalent free tier: 100,000 credits/month, 10 req/s (GOLD plan: 1,000 credits/month) | 10 req/s; 100,000 credits/month |
| Envio HyperSync | dns_fail (HTTP None) | EVM token holder list | Envio HyperSync: free tier available, key required | rate limited per plan |
| Subsquid portal datasets | ok (HTTP 200) | EVM token holder list (indexed datasets) | Subsquid: free tier for public datasets on the shared portal | portal: per-IP rate limit on the free tier |
| Goldsky metadata | http_404 (HTTP 404) | EVM token holder list (hosted subgraphs) | Goldsky free tier: 50,000 queries/month | rate limited on free plan |
| Bitquery GraphQL (free tier) | http_401 (HTTP 401) | Wallet token-trade history + holder counts | Bitquery free tier: 10,000 points/day on the free plan (public datasets); playground OAuth token required | 10,000 points/day (free) |
| Covalent balance-transfers | http_401 (HTTP 401) | Wallet token-trade history for an EVM address | Covalent free tier: 100,000 credits/month, 10 req/s | 10 req/s; 100,000 credits/month |
| Ankr Advanced token-transfers | http_404 (HTTP 404) | Wallet token-trade history for an EVM address | Ankr Advanced free tier: 10,000,000 data points/month | free tier rate limited |
| Zerion wallet transactions | http_402 (HTTP 402) | Wallet token-trade history + PnL for an EVM address | Zerion has a developer tier but the API endpoint returned HTTP 402 'Payment required' without a key | plan dependent |
| DeBank open API | http_401 (HTTP 401) | Wallet positions for an EVM address | DeBank open API: free key required (cloud.debank.com) | plan dependent |
| Alchemy public demo | http_429 (HTTP 429) | Raw JSON-RPC | Alchemy free plan: 300M compute units/month with a signup key; the 'demo' key is shared and heavily throttled | plan dependent |
| QuickNode | http_404 (HTTP 404) | Raw JSON-RPC | QuickNode free tier exists (signup required, some chains free) | plan dependent |
| Arkham Intelligence API | http_400 (HTTP 400) | Wallet trade history + asset intelligence | Arkham offers a free tier after signup; the public explorer pages are keyless | not published for free tier |
| Arkham public explorer page | http_403 (HTTP 403) | Wallet trade history (HTML page) | free, keyless, but Cloudflare-gated | n/a |
| GMGN public web API | http_403 (HTTP 403) | Wallet trade history + token info (Solana) | no documented free tier; an undocumented, unversioned web API | not published; aggressive anti-bot |
| Birdeye | http_401 (HTTP 401) | Token data + Solana OHLCV + wallet data | Birdeye free tier: 100 API calls/day, 1 call/sec (signup required) | 100 calls/day; 1 call/sec |
| SolanaTracker Data API | http_401 (HTTP 401) | Token data + wallet trade history (Solana) | SolanaTracker free tier: 40,000 requests/day (signup required) | 40,000 requests/day |
| Nansen | http_401 (HTTP 401) | Token/wallet analytics and token traders | Nansen free tier via the Nansen AI free program (key required) | credit limited on the free program |
| Bubblemaps API | http_404 (HTTP 404) | Token holder concentration / clustering | Bubblemaps: API key required for /v3 and /v4; the public site is keyless | not published |
| Growthepie | ok (HTTP 200) | Chain-level fee/revenue analytics (NOT wallet-level) | Growthepie: free, keyless public API | 50 requests/min |
| 0x API | http_404 (HTTP 404) | DEX quotes/orderbook (not wallet history) | 0x API free tier: key required (300,000 req/day on the free tier) | free tier 300,000 req/day |
| Neynar (Farcaster) | http_402 (HTTP 402) | Farcaster user/cast search | Neynar free tier: key required (100 req/min, 1,000 req/day) | 100 req/min, 1,000 req/day |
| CoinGecko pro-api (needs key) | http_401 (HTTP 401) | CoinGecko prices with the pro-api hostname | CoinGecko Pro trial/free tier requires a demo or pro key | free tier 10,000 calls/month, 30 calls/min |
| CryptoCompare histoday | http_401 (HTTP 401) | Historical daily prices by symbol | CryptoCompare free tier with a key: 50 calls/min, 5,000 calls/day | 50 calls/min, 5,000 calls/day with a key |
| CoinCap | dns_fail (HTTP None) | Historical asset prices | CoinCap free tier requires an API key (keyless access was retired) | free tier ~10,000 requests/month |
| CoinPaprika historical | http_402 (HTTP 402) | Historical daily prices by coin id | CoinPaprika free plan: recent history only; older history is paid | free plan limited |
| Dune community API | http_401 (HTTP 401) | Run/retrieve Dune queries for wallet PnL analytics | Dune community API free tier: 100 credits/day and 15 query executions/day after signup; paid tiers raise both | community tier: 15 executions/day, 100 credits/day |


# 1. EVM token holder lists


## 1.1 Sources




Blockscout is the primary: it is fully keyless, works on 13 chains from this host, and returns raw holder addresses with balances. Routescan's `erc20` holders route is the independent fallback - it is the only other keyless holder LIST found (it returns balance + percentage, which Blockscout does not). Ethplorer only gives a holder COUNT, not the list.

**BEST FREE OPTION: Blockscout v2 `/api/v2/tokens/{addr}/holders` on `eth.blockscout.com` (and 12 more chains), backed by Routescan as a second opinion**

**FALLBACK CHAIN:**

1. Blockscout holders - Ethereum (eth.blockscout.com) - `ok` (HTTP 200) - EVM token holder list for Ethereum (top holders of the top token on this chain)
2. Routescan v2 ERC-20 holders (Ethereum) - `ok` (HTTP 200) - EVM token holder list for Ethereum, keyless
3. Ethplorer getTokenInfo (public 'freekey') - `ok` (HTTP 200) - Token metadata incl. holdersCount for an EVM token
4. Honeypot.is public API - `ok` (HTTP 200) - Token safety / honeypot + holder analysis for a contract

- **Blockscout holders - Ethereum (eth.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://eth.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0xF977814e90dA44bFA03b6295A0616a897441aceC","implementations":[],"is_contract":false,"is_scam":false,"is_verified":false,"metadata":{"tags":[{"meta`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token ). Discover the chain's tokens first with https://eth.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - Gnosis (gnosis.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://gnosis.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0x1FCc3B22955e76Ca48bF025f1A6993685975Bb9e","implementations":[],"is_contract":true,"is_scam":false,"is_verified":true,"metadata":{"tags":[{"meta":`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0xE2e73A1c69ecF83F464EFCE6A5be353a37cA09b2). Discover the chain's tokens first with https://gnosis.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - OP Mainnet (optimism.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://optimism.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0x66753c4e3fC84f1eD0e3C267C927284E9d90C572","implementations":[{"address_hash":"0x697aF34263Bc8E5E6B0e6b0C37A1EC58CeDE2cE9","name":"HubInstance"}],`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85). Discover the chain's tokens first with https://optimism.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - Scroll (scroll.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://scroll.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0x340F07c2736f5022EA5e1afa8d09B04CEB7378EA","implementations":[{"address_hash":"0xFf51A5898e281Db6DfC7855790607438dF2ca44b","name":"Safe"}],"is_con`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x06eFdBFf2a14a7c8E15944D1F4A48F9F95F663A4). Discover the chain's tokens first with https://scroll.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - zkSync (zksync.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://zksync.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0x621425a1Ef6abE91058E9712575dcc4258F8d091","implementations":[],"is_contract":true,"is_scam":false,"is_verified":false,"metadata":null,"name":null`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x493257fD37EDB34451f62EDf8D2a0C418852bA4C). Discover the chain's tokens first with https://zksync.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - Cronos (cronos.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://cronos.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0xc9219731ADFA70645Be14cD5d30507266f2092c5","implementations":[],"is_contract":false,"is_scam":false,"is_verified":false,"metadata":null,"name":nul`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x3D7F2C478aAfdB65542BCB44bCeeC05849999d2D). Discover the chain's tokens first with https://cronos.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - Rootstock (rootstock.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://rootstock.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0x85a6dC1E19ea051c0DA93290D030f3edbd99B159","implementations":[],"is_contract":true,"is_scam":false,"is_verified":true,"metadata":null,"name":"EVM2`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x938d84942F5d924070a6Bb82F8e56a5E2B3098a4). Discover the chain's tokens first with https://rootstock.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - Celo (celo.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://celo.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0x5754284f345afc66a98fbB0a0Afe71e0F007B949","implementations":[],"is_contract":false,"is_scam":false,"is_verified":false,"metadata":{"tags":[{"meta`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e). Discover the chain's tokens first with https://celo.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - Filecoin (filecoin.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://filecoin.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"filecoin":{"id":null,"actor_type":null,"robust":"f410fq3bblotbp7wfmbnwly5643mgaen4qc4ajzvtvby"},"ens_domain_name":null,"hash":"0x86c215BA617Fec5605B65E3Bee6D86011bc80B80","imple`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x7B90337f65fAA2B2B8ed583ba1Ba6EB0C9D7eA44). Discover the chain's tokens first with https://filecoin.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - Unichain (unichain.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://unichain.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0xB5A2a236581dbd6BCECD8A25EeBFF140595f138C","implementations":[],"is_contract":false,"is_scam":false,"is_verified":false,"metadata":null,"name":nul`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x078D782b760474a361dDA0AF3839290b0EF57AD6). Discover the chain's tokens first with https://unichain.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - ApeChain (apechain.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://apechain.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0x52EB14201fAC868Bd412A4c281c63D9873f42828","implementations":[],"is_contract":true,"is_scam":false,"is_verified":true,"metadata":null,"name":"EVM2`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0xf575731b78981B86d34321d875A3D25a48479be6). Discover the chain's tokens first with https://apechain.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - Soneium (soneium.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://soneium.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0xDC36fcb1497dd6E0Ea23d22Ce942B433cfAF0660","implementations":[],"is_contract":false,"is_scam":false,"is_verified":false,"metadata":null,"name":nul`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x0555E30da8f98308EdB960aa94C0Db47230d2B9c). Discover the chain's tokens first with https://soneium.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders - HashKey (hashkey.blockscout.com)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://hashkey.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key, no signup
  - Rate limit: not published for the Blockscout v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0x52BBA039148BA03cac62Ab77540B7dd167925116","implementations":[],"is_contract":true,"is_scam":false,"is_verified":false,"metadata":null,"name":null`
  - Notes: Verified live: HTTP 200, 50 holder rows returned (token 0x6485e0EF23bf930fa8F232715Ae4d915750cF3F8). Discover the chain's tokens first with https://hashkey.blockscout.com/api/v2/tokens?type=ERC-20 (returns {"items":[...]} with address_hash + holders_count).

- **Blockscout holders (Ethereum) - PEPE specifically** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://eth.blockscout.com/api/v2/tokens/{token_address}/holders`
  - Free tier: fully free, no key
  - Rate limit: not published for the v2 public API
  - Live body: `{"items":[{"address":{"ens_domain_name":null,"hash":"0xF977814e90dA44bFA03b6295A0616a897441aceC","implementations":[],"is_contract":false,"is_scam":false,"is_verified":false,"metadata":{"tags":[{"meta`
  - Notes: Live probe returned HTTP 200 with 50 rows; top holder 0xF977814e90dA44bFA03b6295A0616a897441aceC with balance 50162736194264694000000000000000. Item shape: {address:{hash,is_contract,...}, token_id, value} - the address is at items[i].address.hash, NOT items[i].address_hash.

- **Routescan v2 ERC-20 holders (Ethereum)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.routescan.io/v2/network/mainnet/evm/1/erc20/{token_address}/holders`
  - Free tier: free tier: 10,000 requests/month on the community plan; the v2 address routes work keyless
  - Rate limit: community tier 10,000 req/month; keyless routes are IP-throttled
  - Live body: `{"items":[{"chainId":"1","address":"0xF977814e90dA44bFA03b6295A0616a897441aceC","balance":"50162736194264694000000000000000","percentage":0.119239},{"chainId":"1","address":"0x1d48963DD8FAdA6aB5C2C7b9`
  - Notes: Live probe returned HTTP 200 with items[] of {chainId, address, balance, percentage} - a real keyless holder list. NOTE the path needs an explicit chain id (evm/1/erc20/...): the evm/all/token/{addr}/holders form returned HTTP 404.

- **Routescan v2 Etherscan-compatible proxy** - `error` (HTTP 200) | key: free | fallback: no
  - URL: `https://api.routescan.io/v2/network/mainnet/evm/all/etherscan/api?module=token&action=tokenholderlist&contractaddress={token_address}`
  - Free tier: free tier: 10,000 requests/month community plan
  - Rate limit: community tier 10,000 req/month
  - Live body: `{"status":"0","message":"An error occurred","result":null}`
  - Notes: Live probe returned HTTP 200 but the JSON body was {status:'0', message:'An error occurred', result:null} - the route exists but the Etherscan token module is not served. Use the erc20 holders route instead.

- **Ethplorer getTokenInfo (public 'freekey')** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.ethplorer.io/getTokenInfo/{token_address}?apiKey=freekey`
  - Free tier: Ethplorer public 'freekey' works keyless
  - Rate limit: free tier rate limited
  - Live body: `{"address":"0x6982508145454ce325ddbe47a25d4ec3d2311933","decimals":"18","lastUpdated":1793669405,"name":"Pepe","owner":"0x0000000000000000000000000000000000000000","contractInfo":{"creatorAddress":"0x`
  - Notes: Live probe returned HTTP 200 with address, decimals, name, symbol, owner, contractInfo, price, totalSupply, transfersCount, txsCount, holdersCount (548 holders for PEPE). Note it gives the holder COUNT, not the holder LIST.

- **Honeypot.is public API** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.honeypot.is/v2/IsHoneypot?address={token_address}&chainID={chain_id}`
  - Free tier: free, no key (rate limited)
  - Rate limit: free tier rate limited
  - Live body: `{"token":{"name":"Pepe", "symbol":"PEPE", "decimals":18, "address":"0x6982508145454Ce325dDbE47a25d4ec3d2311933", "totalHolders":599953}, "withToken":{"name":"Wrapped Ether", "symbol":"WETH", "decimals`
  - Notes: Live probe returned HTTP 200 with token{}, summary{}, honeypotResult{}, simulationResult{}, holderAnalysis{}, flags[], contractCode, chain, router, pair, pairAddress. Useful as a pre-filter before pulling holder lists.


### 1.2 Blockscout hosts that do NOT work from this host

Every one of these was live-tested. `http_404` means no Blockscout deployment at that hostname; `http_403` means a Cloudflare challenge.

- `https://base.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_403** (HTTP 403)
- `https://arbitrum.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_403** (HTTP 403)
- `https://polygon.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_403** (HTTP 403)
- `https://bsc.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://linea.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://blast.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://sonic.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://mantle.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://flare.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://fraxtal.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://metis.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://mode.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://sei.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://taiko.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://worldchain.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://zora.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://ink.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://story.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://berachain.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://monad.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://lisk.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://abstract.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://hyperliquid.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://opera.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://manta.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://moonbeam.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://moonriver.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://evmos.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://harmony.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://algorand.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://iotex.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://viction.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://zkevm.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://mordor.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://memecore.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://milkomeda.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://bob.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://shape.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://opbnb.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://redstone.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://sophon.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://gobi.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://syshub.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://petopia.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://flare-testnet.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://lightlink.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://liquidstake.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://morpheus.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://rise.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://functionum.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://kinto.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)
- `https://lambda.blockscout.com/api/v2/tokens/{token_address}/holders` -> **http_404** (HTTP 404)


### 1.3 Keyed holder sources

- **Etherscan API V2 tokenholderlist** - `error` (HTTP 200) | key: KEY | fallback: no
  - URL: `https://api.etherscan.io/v2/api?chainid={chain_id}&module=token&action=tokenholderlist&contractaddress={token_address}&apikey={key}`
  - Free tier: Etherscan V2 free tier: 100,000 calls/day for Ethereum. IMPORTANT: the live probe showed the free plan is LIMITED TO CHAIN ID 1 - other chain ids returned 'Free API access is not supported for this chain. Please upgrade your api plan'.
  - Rate limit: Free plan 100,000 calls/day; 5 req/s
  - Live body: `{"status":"0","message":"NOTOK","result":"Missing/Invalid API Key"}`
  - Notes: Live probe with NO key returned HTTP 200 whose body was {status:'0', message:'NOTOK', result:'Missing/Invalid API Key'}. Etherscan signals failure in the JSON body, not the HTTP status - the caller must check body['status']. A placeholder key produced the same NOTOK payload. Chains 56/8453/10/100 answered 'Free API access is not supported for this chain'; chains 534352/324/81457/25/31 answered 'Missing or unsupported chainid'.

- **Etherscan API V2 (non-Ethereum chains)** - `error` (HTTP 200) | key: KEY | fallback: no
  - URL: `https://api.etherscan.io/v2/api?chainid={chain_id}&module=token&action=tokenholderlist&contractaddress={token_address}&apikey={key}`
  - Free tier: free tier covers Ethereum only; other chains need a paid plan
  - Rate limit: Free plan 100,000 calls/day (chain 1 only)
  - Live body: `{"status":"0","message":"NOTOK","result":"Free API access is not supported for this chain. Please upgrade your api plan for full chain coverage. https://etherscan.io/apis"}`
  - Notes: Live probe (no key) returned HTTP 200 + 'Free API access is not supported for this chain. Please upgrade your api plan for full chain coverage.' Even with a key the free plan is chain-1 only.

- **Moralis token owners** - `dns_fail` | key: KEY | fallback: no
  - URL: `https://api.moralis.io/api/v2/{chain}/tokens/{token_address}/owners`
  - Free tier: Moralis free tier: 40,000 compute units/day, 2 req/s
  - Rate limit: 40,000 CU/day; 2 req/s
  - Live body: `EXCEPTION ConnectionError: HTTPSConnectionPool(host='api.moralis.io', port=443): Max retries exceeded with url: /api/v2/eth/tokens/0x6982508145454ce325ddbe47a25d4ec3d2311933/owners (Caused by NameReso`
  - Notes: Live probe failed at DNS: api.moralis.io did not resolve from this host (gaierror). The host is blocked/unresolvable here, not merely keyed.

- **OKLink explorer token ranking** - `http_404` (HTTP 404) | key: KEY | fallback: no
  - URL: `https://www.oklink.com/api/v5/explorer/token/token-ranking?chainShortName={chain}`
  - Free tier: OKLink free tier: 100,000 data points/day
  - Rate limit: 100,000 data points/day
  - Live body: `{"code":"50404","data":[],"msg":"URL not found."}`
  - Notes: Live probe returned HTTP 404 with body {code:'50404', msg:'URL not found.'} for this path - the endpoint path is wrong or moved. OKLink needs an API key anyway.

- **Covalent token holders** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://api.covalenthq.com/v1/{chain}/tokens/{token_address}/holders_v2/`
  - Free tier: Covalent free tier: 100,000 credits/month, 10 req/s (GOLD plan: 1,000 credits/month)
  - Rate limit: 10 req/s; 100,000 credits/month
  - Live body: `<html> <head><title>401 Authorization Required</title></head> <body> <center><h1>401 Authorization Required</h1></center> <hr><center>nginx/1.19.10</center> </body> </html> <!-- a padding to disable M`
  - Notes: Live probe returned HTTP 401 - key required.

- **Envio HyperSync** - `dns_fail` | key: KEY | fallback: no
  - URL: `https://hypersync.enviodev.com`
  - Free tier: Envio HyperSync: free tier available, key required
  - Rate limit: rate limited per plan
  - Live body: `EXCEPTION ConnectionError: HTTPSConnectionPool(host='hypersync.enviodev.com', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='hypersync.enviodev.com',`
  - Notes: Live probe failed at DNS: hypersync.enviodev.com did not resolve from this host.

- **Subsquid portal datasets** - `ok` (HTTP 200) | key: KEY | fallback: no
  - URL: `https://portal.sqd.dev/datasets`
  - Free tier: Subsquid: free tier for public datasets on the shared portal
  - Rate limit: portal: per-IP rate limit on the free tier
  - Live body: `[{"dataset":"alpen-testnet","aliases":[],"real_time":true},{"dataset":"arbitrum-one","aliases":[],"real_time":true},{"dataset":"arbitrum-sepolia","aliases":[],"real_time":true},{"dataset":"avalanche-m`
  - Notes: Live probe returned HTTP 200 with 109 dataset entries (ethereum-mainnet, ethereum-mainnet-tb, ethereum-sepolia, ethereum-hoodi, arbitrum-one, ...). The GraphQL query endpoint path was NOT resolvable from this host (404 on /datasets/{name}/graphql, 405 on POST to /datasets/{name}), so treat Subsquid as a dataset DIRECTORY that is usable here, not a confirmed query source.

- **Goldsky metadata** - `http_404` (HTTP 404) | key: KEY | fallback: no
  - URL: `https://goldsky.com/api/metadata`
  - Free tier: Goldsky free tier: 50,000 queries/month
  - Rate limit: rate limited on free plan
  - Live body: `<!DOCTYPE html><html lang="en"><head><meta charSet="utf-8" data-next-head=""/><meta http-equiv="Content-Type" content="text/html; charset=utf-8" data-next-head=""/><meta name="viewport" content="width`
  - Notes: Live probe returned HTTP 404 - neither /api/metadata nor /api/metadata/subgraphs nor api.goldsky.com/metadata resolved.

- **Bitquery GraphQL (free tier)** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://streaming.bitquery.io/eap`
  - Free tier: Bitquery free tier: 10,000 points/day on the free plan (public datasets); playground OAuth token required
  - Rate limit: 10,000 points/day (free)
  - Live body: `Unauthorized. Provide Authorization as documented at https://docs.bitquery.io/docs/category/authorization`
  - Notes: Live probe returned HTTP 401 - OAuth token required.


# 2. Wallet token-trade history and per-wallet PnL


## 2.1 Sources




**There is no keyless per-wallet PnL source from this host.** No free provider returns a computed profit-and-loss figure without a key. What IS keyless is the raw transaction and token-transfer tape: Blockscout's address endpoints and Routescan's address transactions. A real PnL number must be computed locally from those transfers plus a price series (see section 3) - which is exactly why the DefiLlama historical price fix in section 3 matters.

Also note: the holder lists in section 1 plus the transfer tape give concentration analysis without any key at all.

**BEST FREE OPTION: Blockscout v2 address endpoints on eth.blockscout.com + Routescan v2 address transactions**

**FALLBACK CHAIN:**

1. Blockscout address token-transfers (Ethereum) - `ok` (HTTP 200) - Wallet token-trade history for an EVM address
2. Routescan v2 address transactions - `ok` (HTTP 200) - Wallet transaction history for an EVM address, keyless
3. Blockscout internal transactions (Ethereum) - `ok` (HTTP 200) - Wallet internal trade history for an EVM address
4. Blockscout token-wide transfers (Ethereum) - `ok` (HTTP 200) - Token-wide trade history (all transfers of one token)
5. Blockscout address token-transfers (Optimism host) - `ok` (HTTP 200) - Wallet token-trade history on OP Mainnet
6. Ethplorer (public 'freekey') - `ok` (HTTP 200) - Wallet balances/positions + token holder COUNT for an EVM address
7. PublicNode (keyless RPC) - `ok` (HTTP 200) - Raw JSON-RPC for wallet/token history (needs block paging)
8. drpc.org (keyless RPC) - `ok` (HTTP 200) - Raw JSON-RPC for wallet/token history (needs block paging)

- **Blockscout address token-transfers (Ethereum)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://eth.blockscout.com/api/v2/addresses/{address}/token-transfers`
  - Free tier: fully free, no key
  - Rate limit: not published for the v2 public API
  - Live body: `{"items":[{"block_hash":"0x0d6c7b9293c057fa91f1202614ece4ebbfaa4c525f538a77f843a780802d3196","block_number":26317304,"from":{"ens_domain_name":null,"hash":"0x700E0841CE0892969d2f9Cf523C6298B3eF056a6",`
  - Notes: Live probe returned HTTP 200 with items[] of block_hash, block_number, from{}, to{}, token, total. The same route on the heavy Binance address 0x28C6c062... returned HTTP 500 'Internal server error' - retry with a lighter address or a narrower time filter.

- **Blockscout address transactions (Ethereum)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://eth.blockscout.com/api/v2/addresses/{address}/transactions`
  - Free tier: fully free, no key
  - Rate limit: not published for the v2 public API
  - Live body: `{"items":[{"priority_fee":null,"raw_input":"0xa9059cbb000000000000000000000000a023f08c70a23abc7edfc5b6b5e171d78dfc947e0000000000000000000000000000000000000000000008a824bc641be7144148","is_pending_upda`
  - Notes: Live probe returned HTTP 200 with items[] (tx hash, block, method, status). The heavy Binance address returned HTTP 500.

- **Blockscout internal transactions (Ethereum)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://eth.blockscout.com/api/v2/addresses/{address}/internal-transactions`
  - Free tier: fully free, no key
  - Rate limit: not published for the v2 public API
  - Live body: `{"items":[{"block_number":26301828,"created_contract":null,"error":null,"from":{"ens_domain_name":null,"hash":"0x28C6c06298d514Db089934071355E5743bf21d60","implementations":[{"address_hash":"0x63e842B`
  - Notes: Live probe returned HTTP 200 with items[] + next_page_params. Worked even on the heavy address (unlike /token-transfers).

- **Blockscout address token-transfers (Optimism host)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://optimism.blockscout.com/api/v2/addresses/{address}/token-transfers`
  - Free tier: fully free, no key
  - Rate limit: not published for the v2 public API
  - Live body: `{"items":[{"block_hash":"0xcb4be4ab9b5018bbc42a242bcf05cebad8fd1681724ffcf9f6c6493c965c287a","block_number":158443243,"from":{"ens_domain_name":null,"hash":"0x0000000000000000000000000000000000000000"`
  - Notes: Live probe returned HTTP 200 on the heavy address - a second host to spread load across.

- **Blockscout token-wide transfers (Ethereum)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://eth.blockscout.com/api/v2/tokens/{token_address}/transfers`
  - Free tier: fully free, no key
  - Rate limit: not published for the v2 public API
  - Live body: `{"items":[{"block_hash":"0x51b54c816deb50054d6a0fab865d863a9f3073de153a956b4ad4ab4790a67fec","block_number":26330988,"from":{"ens_domain_name":null,"hash":"0xE155Fa02B6fC396195416967b1F0fefbee12986c",`
  - Notes: Live probe returned HTTP 200 with items[] (block_hash, block_number, from{}, to{}, token). Best keyless route for a token's full trade tape.

- **Routescan v2 address transactions** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.routescan.io/v2/network/mainnet/evm/all/address/{address}/transactions`
  - Free tier: free tier: 10,000 requests/month community plan; this route is keyless
  - Rate limit: community tier 10,000 req/month
  - Live body: `{"items":[{"type":"evm_tx","id":"0xeabf0843c6bd8a061382a4650abbf36c905816e62482da7bee68d76b0b15a412","chainId":"1","timestamp":"2026-10-30T08:44:11.000Z","blockNumber":26304457,"blockHash":"0xdf030837`
  - Notes: Live probe returned HTTP 200 with items[] of {type, id, chainId, timestamp, ...} plus a link{} cursor for pagination.

- **Ethplorer (public 'freekey')** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.ethplorer.io/getAddressInfo/{address}?apiKey=freekey`
  - Free tier: Ethplorer publishes a working shared key literally named 'freekey'; free tier otherwise needs signup
  - Rate limit: free tier rate limited (not published precisely)
  - Live body: `{"address":"0x28c6c06298d514db089934071355e5743bf21d60","ETH":{"price":{"rate":2258.960019765867,"diff":-1.41,"diff7d":-2.65,"ts":1793669358.189,"marketCapUsd":276013654688.86945,"availableSupply":122`
  - Notes: Live probe returned HTTP 200 with address, ETH balance/price, contractInfo and tokens[] - a wallet position snapshot, NOT a trade history.


### 2.2 Solana (memecoins are mostly Solana)

The EVM sweep above is incomplete on its own - most memecoins live on Solana, and these sources are keyless too.

- **Jupiter token search (Solana)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://lite-api.jup.ag/tokens/v2/search?query={mint_or_symbol}`
  - Free tier: free, no key (Jupiter public API)
  - Rate limit: ~60 requests/minute on the public tier
  - Live body: `[{"id":"DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263","name":"Bonk","symbol":"Bonk","icon":"https://arweave.net/hQiPZOsRZXGXBJd_82PhVdlM_hACsT_q6wqwf5cSY7I","decimals":5,"dev":"9AhKqLR67hwapvG8SA2JFXa`
  - Notes: Live probe returned HTTP 200 with a JSON array of token records (id, name, symbol, icon, decimals, dev, circSupply, totalSupply, tokenProgram) for BONK. /tokens/v1/{mint} returned HTTP 404 - use the v2 search route.

- **RugCheck report (Solana)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.rugcheck.xyz/v1/tokens/{mint}/report`
  - Free tier: free, no key (RugCheck public API)
  - Rate limit: rate limited; the site asks for an API key for higher limits
  - Live body: `{"mint":"DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263","tokenProgram":"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA","creator":"9AhKqLR67hwapvG8SA2JFXaCshXc9nALJjpKaHZrsbkw","creatorBalance":0,"token":`
  - Notes: Live probe returned HTTP 200 with mint, tokenProgram, creator, creatorBalance, token{mintAuthority, freezeAuthority, supply, decimals}, token_extended, markets, lockers, totalHolders, graphInsidersDetected etc. The /trades and /holders sub-routes returned HTTP 404 - the report route is the usable one.

- **Solana public JSON-RPC (keyless)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://solana-rpc.publicnode.com`
  - Free tier: free, keyless public RPC (heavily rate limited)
  - Rate limit: provider specific; Solana public RPCs typically ~10 req/s and 40k CU
  - Live body: `{"jsonrpc":"2.0","result":[],"id":1}`
  - Notes: Live probe: getSlot returned HTTP 200 and a real getSignaturesForAddress call for 5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9 returned HTTP 200 with result[] (empty for that address, but the route works and returns JSON-RPC, not an error). api.mainnet-beta.solana.com also returned HTTP 200; rpc.ankr.com/solana returned HTTP 403.

- **Dexscreener (Solana)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.dexscreener.com/latest/dex/tokens/{mint}`
  - Free tier: free: 300 req/min for pair/token lookups
  - Rate limit: 300 req/min (pairs & tokens endpoints)
  - Live body: `{"schemaVersion":"1.0.0","pairs":[{"chainId":"solana","dexId":"orca","url":"https://dexscreener.com/solana/5zpyutju9ee6jfymdgok7f6s5kczqtc9fomp3uekuya9","pairAddress":"5zpyutJu9ee6jFymDGoK7F6S5Kczqtc9`
  - Notes: Live probe returned HTTP 200 with pairs[] for the BONK mint (orca pair 5zpyutJu9ee6jFymDGoK7F6S5Kczqtc9FomP3ueKuyA9 with baseToken, liquidity and priceUSD). The /latest/dex/search?q= route also returned HTTP 200.


### 2.3 Keyless raw RPC providers (for on-chain paging)

These answer `eth_blockNumber` without a key, but the free plans cap `eth_getLogs` hard, so they are usable for spot reads and short windows rather than a full history backfill.

- **PublicNode (keyless RPC)** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://ethereum-rpc.publicnode.com`
  - Free tier: free, keyless public RPC endpoint
  - Rate limit: provider specific, ~10-50 req/s
  - Live body: `{"jsonrpc":"2.0","result":"0x191c7de","id":1}`
  - Notes: Live probe: eth_blockNumber returned HTTP 200; eth_getLogs returned HTTP 403 {message:'Archive requests require a personal token'} - free for basic calls only.

- **drpc.org (keyless RPC)** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://eth.drpc.org`
  - Free tier: free, keyless public RPC endpoint
  - Rate limit: provider specific, ~10-50 req/s
  - Live body: `{"id":1,"jsonrpc":"2.0","result":"0x191c7dd"}`
  - Notes: Live probe: eth_blockNumber returned HTTP 200. eth_getLogs is accepted but the free plan caps the block range at 10,000 and rejects a null topic slot with 'Invalid variadic value or array type' - pass concrete topics.

- **1rpc.io (keyless RPC)** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://1rpc.io/eth`
  - Free tier: free, keyless public RPC endpoint
  - Rate limit: provider specific, ~10-50 req/s
  - Live body: `{"jsonrpc":"2.0","id":1,"result":"0x191c7de"}`
  - Notes: Live probe: eth_blockNumber returned HTTP 200. eth_getLogs is capped at a 50-block range on the free plan ('eth_getLogs is limited to 0 - 50 blocks range').

- **Flashbots RPC (keyless RPC)** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://rpc.flashbots.net`
  - Free tier: free, keyless public RPC endpoint
  - Rate limit: provider specific, ~10-50 req/s
  - Live body: `{"jsonrpc":"2.0","result":"0x191c7de","id":1}`
  - Notes: Live probe: eth_blockNumber returned HTTP 200. eth_getLogs over a wide range returned HTTP 504, and over a narrow range 'Invalid params'.

- **llamaRPC** - `http_525` (HTTP 525) | key: free | fallback: no
  - URL: `https://eth.llamarpc.com`
  - Free tier: free, keyless public RPC endpoint
  - Rate limit: provider specific, ~10-50 req/s
  - Live body: `{"type":"https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-525/","title":"Error 525: SSL handshake failed","status":525,"detail":"The SSL/TLS hand`
  - Notes: Live probe returned HTTP 525 (Cloudflare SSL handshake failed).

- **BlockPI** - `http_503` (HTTP 503) | key: free | fallback: no
  - URL: `https://ethereum.blockpi.network/v1/rpc/public`
  - Free tier: free, keyless public RPC endpoint
  - Rate limit: provider specific, ~10-50 req/s
  - Live body: `{"jsonrpc":"2.0","error":{"code":100021,"message":"Apikey not found"}}`
  - Notes: Live probe returned HTTP 503.


### 2.4 Keyed wallet-history sources

- **Covalent balance-transfers** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://api.covalenthq.com/v1/{chain}/address/{address}/transactions_v2/`
  - Free tier: Covalent free tier: 100,000 credits/month, 10 req/s
  - Rate limit: 10 req/s; 100,000 credits/month
  - Live body: `<html> <head><title>401 Authorization Required</title></head> <body> <center><h1>401 Authorization Required</h1></center> <hr><center>nginx/1.19.10</center> </body> </html> <!-- a padding to disable M`
  - Notes: Live probe returned HTTP 401 - key required.

- **Ankr Advanced token-transfers** - `http_404` (HTTP 404) | key: KEY | fallback: no
  - URL: `https://rpc.ankr.com/v2/{chain}/address/{address}/token-transfers`
  - Free tier: Ankr Advanced free tier: 10,000,000 data points/month
  - Rate limit: free tier rate limited
  - Live body: `<html> <head><title>404 Not Found</title></head> <body> <center><h1>404 Not Found</h1></center> <hr><center>nginx</center> </body> </html> <!-- a padding to disable MSIE and Chrome friendly error page`
  - Notes: Live probe returned HTTP 404 with body {} for every path variant tried (/v2/{chain}/address/{addr}/token-transfers, /token_transfers, /multichain/address/..., /multichain/{chain}/address/...) both with and without a key. Ankr's public RPC (rpc.ankr.com/eth) answers eth_blockNumber but rejects eth_getLogs with 'Unauthorized: You must authenticate your request with an API key'.

- **Zerion wallet transactions** - `http_402` (HTTP 402) | key: KEY | fallback: no
  - URL: `https://api.zerion.io/v1/wallets/{address}/transactions`
  - Free tier: Zerion has a developer tier but the API endpoint returned HTTP 402 'Payment required' without a key
  - Rate limit: plan dependent
  - Live body: `{ "errors": [ { "title": "Payment required", "detail": "Provide an API key via \"Authorization: Basic <base64(api_key:)>\" or pay using one of the methods advertised in response headers" } ] }`
  - Notes: Live probe returned HTTP 402 with {errors:[{title:'Payment required', detail:'Provide an API key via "Authorization: Basic <base64>" ...'}]}.

- **DeBank open API** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://pro-openapi.debank.com/v1/user/total_balance?id={address}`
  - Free tier: DeBank open API: free key required (cloud.debank.com)
  - Rate limit: plan dependent
  - Live body: `{"message": "You are not authorized to access the URL, you can get your access key from https://cloud.debank.com."}`
  - Notes: Live probe returned HTTP 401 {message:'You are not authorized to access the URL, you can get your access key from https://cloud.debank.com.'}.

- **Alchemy public demo** - `http_429` (HTTP 429) | key: KEY | fallback: no
  - URL: `https://eth-mainnet.g.alchemy.com/v2/demo`
  - Free tier: Alchemy free plan: 300M compute units/month with a signup key; the 'demo' key is shared and heavily throttled
  - Rate limit: plan dependent
  - Notes: Live probe returned HTTP 429 on both GET and POST - the shared demo key is rate limited from this host.

- **QuickNode** - `http_404` (HTTP 404) | key: KEY | fallback: no
  - URL: `https://api.quicknode.com/token/{chain}/{network}/`
  - Free tier: QuickNode free tier exists (signup required, some chains free)
  - Rate limit: plan dependent
  - Live body: `<html> <head><title>404 Not Found</title></head> <body> <center><h1>404 Not Found</h1></center> <hr><center>nginx</center> <script>(function(){function c(){var b=a.contentDocument||(a.contentWindow&&a`
  - Notes: Live probe returned HTTP 404 for this path shape.

- **Arkham Intelligence API** - `http_400` (HTTP 400) | key: KEY | fallback: no
  - URL: `https://api.arkhamintelligence.com/intelligence/address/{address}?startTime={unix}&endTime={unix}`
  - Free tier: Arkham offers a free tier after signup; the public explorer pages are keyless
  - Rate limit: not published for free tier
  - Live body: `{"message":"invalid timestamp format, please sign up for an api key :)"}`
  - Notes: Live probe returned HTTP 400 {message:'invalid timestamp format, please sign up for an api key :)'} - the endpoint exists and wants a key plus start/end unix timestamps.

- **Arkham public explorer page** - `http_403` (HTTP 403) | key: KEY | fallback: no
  - URL: `https://intel.arkm.com/explorer/address/{address}`
  - Free tier: free, keyless, but Cloudflare-gated
  - Rate limit: n/a
  - Live body: `<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=Edge"><meta nam`
  - Notes: Live probe returned HTTP 403 with a Cloudflare 'Just a moment...' challenge page. Resolves and is reachable in a browser; not usable from a plain HTTP client here.

- **GMGN public web API** - `http_403` (HTTP 403) | key: KEY | fallback: no
  - URL: `https://gmgn.ai/defi/quotation/v1/wallet/sol/{address}/info`
  - Free tier: no documented free tier; an undocumented, unversioned web API
  - Rate limit: not published; aggressive anti-bot
  - Live body: `<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=Edge"><meta nam`
  - Notes: Live probe returned HTTP 403 with a Cloudflare 'Just a moment...' challenge page on every gmgn.ai endpoint tried (wallet info, swaps, token info, wallet rank).

- **Birdeye** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://public-api.birdeye.so/defi/token_overview?address={mint}`
  - Free tier: Birdeye free tier: 100 API calls/day, 1 call/sec (signup required)
  - Rate limit: 100 calls/day; 1 call/sec
  - Live body: `{"success":false,"message":"Unauthorized"}`
  - Notes: Live probe returned HTTP 401 {success:false, message:'Unauthorized'} for both token_overview and the OHLCV route.

- **SolanaTracker Data API** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://data.solanatracker.io/v0/token/{mint}/trades`
  - Free tier: SolanaTracker free tier: 40,000 requests/day (signup required)
  - Rate limit: 40,000 requests/day
  - Live body: `{"error":"API key is required"}`
  - Notes: Live probe on the correct host (data.solanatracker.io - the main host returns 404 'This is not the Data API endpoint') returned HTTP 401 - key required.

- **Nansen** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://api.nansen.ai/api/beta/analytics/token`
  - Free tier: Nansen free tier via the Nansen AI free program (key required)
  - Rate limit: credit limited on the free program
  - Live body: `{ "message":"No API key found in request", "request_id":"e276c95a05c5832b1f7562119515ac33" }`
  - Notes: Live probe returned HTTP 401 {message:'No API key found in request'}.

- **Bubblemaps API** - `http_404` (HTTP 404) | key: KEY | fallback: no
  - URL: `https://api.bubblemaps.io/v4/asset/{chain}/{token_address}`
  - Free tier: Bubblemaps: API key required for /v3 and /v4; the public site is keyless
  - Rate limit: not published
  - Live body: `{"detail":"Not Found"}`
  - Notes: Live probe returned HTTP 404 {detail:'Not Found'} on /v4/asset, /v3/token and /v3/cluster. The website itself (bubblemaps.io) returned HTTP 200.

- **Growthepie** - `ok` (HTTP 200) | key: KEY | fallback: no
  - URL: `https://api.growthepie.xyz/v1/fundamentals.json`
  - Free tier: Growthepie: free, keyless public API
  - Rate limit: 50 requests/min
  - Live body: `[{"metric_key": "aa_last7d", "origin_key": "arbitrum", "date": "2026-08-04", "value": 626336.0}, {"metric_key": "aa_last7d", "origin_key": "arbitrum", "date": "2026-08-05", "value": 626735.0}, {"metri`
  - Notes: Live probe returned HTTP 200 with a JSON array of daily metric rows (metric_key, origin_key, date, value). Chain/protocol level only - it cannot answer a per-wallet PnL question.

- **0x API** - `http_404` (HTTP 404) | key: KEY | fallback: no
  - URL: `https://api.0x.org/swap/v1/sources?chainId={chain_id}`
  - Free tier: 0x API free tier: key required (300,000 req/day on the free tier)
  - Rate limit: free tier 300,000 req/day
  - Live body: `{ "message":"no Route matched with those values", "request_id":"f0f5097e8beca405b6ac98314811f21f" }`
  - Notes: Live probe returned HTTP 404 {message:'no Route matched with those values'} for /swap/v1/sources and /sra/v4/orders; /swap/allowance-holder/allowances returned HTTP 401. 0x is a trading API, not a wallet-history API.


# 3. Historical prices (the critical gap)


## 3.1 The answer to the cost-basis gap




**REQUIREMENT: can a source return a price for an OLD contract address at a PAST timestamp? YES - DefiLlama's historical endpoint does exactly that, keyless.**

Live proof for PEPE `0x6982508145454ce325ddbe47a25d4ec3d2311933`:

| Requested timestamp | Price returned | Source timestamp | Confidence |
|---|---|---|---|
| 2023-05-01 (1682899200) | 7.28384e-07 | 1682899064 | 0.99 |
| 2023-05-15 (1684108800) | 1.8e-06 | 1684108663 | 0.99 |
| 2024-06-01 (1717200000) | 1.543e-05 | 1717200125 | 0.99 |

And for other old contracts: SHIB `0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE` at 2021-06-01 -> 9.221710319349999e-06; BONK (solana) at 2023-12-01 -> 3.86e-06; USDC (`coingecko:usd-coin`) at 2020-06-01 -> 1.0027976722856158.

### THE URL FORM IS THE WHOLE TRAP

The chain:address pair must be **colon**-joined. All three wrong forms were live-tested:

| Form | Live result |
|---|---|
| `/prices/historical/{ts}/ethereum:{addr}` | **200, real price** |
| `/prices/historical/{ts}/ethereum,{addr}` | 200 but body `{"coins":{}}` (EMPTY) |
| `/prices/historical/{ts}/ethereum/{addr}` | 404 route not found |

The comma form is the dangerous one: it returns HTTP 200 with an empty object, which looks like success. The slash form 404s loudly, which is safer.

### COVERAGE IS NOT UNIVERSAL

The endpoint only answers for tokens DefiLlama has indexed AND for timestamps inside the indexed window. Live-tested empty responses (`{"coins":{}}` with HTTP 200): SHIB at 2020-05-11, FLOKI `0xfb5B838b6cfEEdC2873aB27866079AC55363D37e` at 2022-02, WIF `EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm` at 2023-11, and `coingecko:doge` at 2021-06. **Always check for an empty `coins{}` - a 200 is not a price.**

### GeckoTerminal is a RECENT-history source only

Its OHLCV endpoint works keyless and returns real candles, but the free tier only reaches back ~6 months (184 daily candles for the PEPE/WETH pool, oldest 2026-07-27). Paging backwards with `?before_timestamp=` returned **HTTP 401 - paid**. So GeckoTerminal cannot price a 2023 position; it is a cross-check on recent prices and a way to convert a contract address into a pool address.

### SYMBOL-BASED CEX HISTORY is a different axis

Binance, MEXC, Gate.io, Bitget, Bybit and Coinbase all serve real 2023 daily candles keyless (PEPEUSDT from 2023-05-01 on MEXC/Gate, 2023-05-04 on Binance/Bitget). But these price the TICKER on an exchange, not a specific contract address - use them for a price series or a sanity cross-check, not to price an arbitrary contract.

### SOLANA PRICE COVERAGE

DefiLlama's historical endpoint works for Solana mints too - BONK (DezXAZ8z...) at 2023-12-01 returned a real price. But coverage is per-token: WIF (EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm) at the same timestamp returned an empty coins{} object. Jupiter's price API gives a current price for any Solana mint keyless but has no history.

**BEST FREE OPTION: DefiLlama `coins.llama.fi/prices/historical/{unix_timestamp}/{chain}:{address}`**

**FALLBACK CHAIN:**

1. DefiLlama historical price by contract address - `ok` (HTTP 200) - Historical price for an OLD contract address at a PAST timestamp (the cost-basis fix)
2. DefiLlama historical price - multi-contract batch - `ok` (HTTP 200) - Several old contracts at one past timestamp in one call
3. GeckoTerminal OHLCV (per pool) - `ok` (HTTP 200) - OHLCV price history for a DEX pool (contract-address based)
4. Binance public klines - `ok` (HTTP 200) - Historical daily/hourly prices for a LISTED symbol
5. MEXC public klines - `ok` (HTTP 200) - Historical daily prices for a listed symbol
6. Coinbase Exchange public candles - `ok` (HTTP 200) - Historical daily prices for a listed USD pair
7. Gate.io public candlesticks - `ok` (HTTP 200) - Historical daily prices for a listed pair
8. Bitget public candles - `ok` (HTTP 200) - Historical daily prices for a listed symbol
9. Bybit public kline - `ok` (HTTP 200) - Historical daily prices for a listed symbol
10. Dexscreener public API - `ok` (HTTP 200) - Current price, liquidity and pool list for a contract address

- **DefiLlama historical price by contract address** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://coins.llama.fi/prices/historical/{unix_timestamp}/{chain}:{token_address}`
  - Free tier: fully free, no key
  - Rate limit: not published for coins.llama.fi (best-effort)
  - Live body: `{"coins":{"ethereum:0x6982508145454ce325ddbe47a25d4ec3d2311933":{"decimals":18,"symbol":"PEPE","price":7.28384e-7,"timestamp":1682899064,"confidence":0.99}}}`
  - Notes: THIS IS THE ANSWER TO THE CRITICAL GAP. Live probes returned real prices for old contracts at past timestamps: PEPE at 2023-05-01 -> 7.28384e-07 (timestamp 1682899064, confidence 0.99); PEPE at 2023-05-15 -> 1.8e-06; PEPE at 2024-06-01 -> 1.543e-05; SHIB at 2021-06-01 -> 9.2217e-06; BONK (solana) at 2023-12-01 -> 3.86e-06; USDC (coingecko:usd-coin) at 2020-06-01 -> 1.0028. URL FORM IS CRITICAL: the chain:address pair must be COLON-JOINED. The comma form /prices/historical/{ts}/ethereum,{addr} returns HTTP 200 with an EMPTY {"coins":{}} body and the slash form /{ts}/ethereum/{addr} returns HTTP 404.

- **DefiLlama historical price - multi-contract batch** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://coins.llama.fi/prices/historical/{unix_timestamp}/{chain1}:{addr1},{chain2}:{addr2}`
  - Free tier: fully free, no key
  - Rate limit: not published for coins.llama.fi
  - Live body: `{"coins":{"ethereum:0x6982508145454ce325ddbe47a25d4ec3d2311933":{"decimals":18,"symbol":"PEPE","price":7.28384e-7,"timestamp":1682899064,"confidence":0.99},"ethereum:0x95aD61b0a150d79219dCF64E1E6Cc01f`
  - Notes: Live probe returned HTTP 200 with 3 priced coins for one timestamp: PEPE 7.28384e-07, SHIB 1.016e-05, USDC 1.00. Format = comma-separated chain:address pairs.

- **DefiLlama current price by contract address** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://coins.llama.fi/prices/current/{chain}:{token_address}`
  - Free tier: fully free, no key
  - Rate limit: not published for coins.llama.fi
  - Live body: `{"coins":{"ethereum:0x6982508145454ce325ddbe47a25d4ec3d2311933":{"decimals":18,"symbol":"PEPE","price":7.28384e-7,"timestamp":1682899064,"confidence":0.99}}}`
  - Notes: Live probe returned HTTP 200 with {"coins":{"ethereum:0x6982...1933":{decimals:18, symbol:PEPE, price:4.81e-06, timestamp:1793669143, confidence:0.999}}}. Batch form (comma-separated colon-pairs) returned 3 coins. NOTE the comma form WITHOUT the colon inside each pair (ethereum,{addr}) returns HTTP 200 but an EMPTY coins{} - a silent failure that looks like success.

- **DefiLlama chart by contract address** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://coins.llama.fi/chart/{chain}:{token_address}`
  - Free tier: fully free, no key
  - Rate limit: not published for coins.llama.fi
  - Live body: `{"coins":{"ethereum:0x6982508145454ce325ddbe47a25d4ec3d2311933":{"symbol":"PEPE","confidence":0.99,"decimals":18,"prices":[{"timestamp":1793669151,"price":0.0000048107957436391246}]}}}`
  - Notes: Live probe returned HTTP 200 but the series was a single point (n_points=1, the current price) - the free chart endpoint does NOT give history. Use /prices/historical for past prices. The slash form /chart/ethereum/{addr} is HTTP 404.

- **DefiLlama historical price - coverage limits** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://coins.llama.fi/prices/historical/{unix_timestamp}/{chain}:{token_address}`
  - Free tier: fully free, no key
  - Rate limit: not published
  - Live body: `{"coins":{}}`
  - Notes: Live probe returned HTTP 200 with an EMPTY {"coins":{}} for SHIB at 2020-05-11 (before its data starts) and also empty for FLOKI (0xfb5B...D37e) at 2022-02, for WIF (EKpQ...cjm) at 2023-11, and for coingecko:doge at 2021-06. So the endpoint only answers for tokens DefiLlama actually indexed AND for timestamps inside the indexed window - always check for an empty coins{}.

- **GeckoTerminal OHLCV (per pool)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}`
  - Free tier: free: 30 calls/minute
  - Rate limit: 30 calls/minute (free tier)
  - Live body: `{"data":{"id":"cc8e87f3-5b29-4ddc-979f-517f1f6cfd51","type":"ohlcv_request_response","attributes":{"ohlcv_list":[[1793664000,4.77051590847102e-06,4.85069549821953e-06,4.74313723687821e-06,4.7912793896`
  - Notes: Live probes returned HTTP 200 with real candles: PEPE/WETH pool 0xa43fe16908251ee70ef74718545e4fe6c5ccec9f, day timeframe, 184 candles (oldest 2026-07-27, newest 2026-11-03); hour and minute timeframes also HTTP 200. CAVEAT: the free tier only reaches back ~6 months (184 daily candles) - limit=1000 returns the same 184 rows. Paging backwards with ?before_timestamp= is PAID: the probe returned HTTP 401. So GeckoTerminal is a good RECENT-history source but CANNOT reach a 2023 price.

- **GeckoTerminal pool discovery by token** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{token_address}/pools`
  - Free tier: free: 30 calls/minute
  - Rate limit: 30 calls/minute (free tier)
  - Live body: `{"data":[{"id":"eth_0xa43fe16908251ee70ef74718545e4fe6c5ccec9f","type":"pool","attributes":{"base_token_price_usd":"0.000004791040669","base_token_price_native_currency":"0.00000000212676835062084","q`
  - Notes: Live probe returned HTTP 200 with 20 PEPE pools; the deepest is PEPE/WETH 0xa43fe16908251ee70ef74718545e4fe6c5ccec9f with base_token_price_usd 0.000004791040669. Use this to convert a contract address into a pool address for the OHLCV endpoint.

- **Binance public klines** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={ms}&endTime={ms}&limit={n}`
  - Free tier: fully free, no key
  - Rate limit: 1200 request weight/min per IP
  - Live body: `[[1683244800000,"0.00000197","0.00000439","0.00000197","0.00000373","46108639000543.00",1683331199999,"154291982.66948946",477819,"24373246666898.00","81772634.23419222","0"],[1683331200000,"0.0000037`
  - Notes: Live probes returned HTTP 200 with real 2023 candles: PEPEUSDT 1d from 2023-05-04 (open 0.00000197, close 0.00000373), SHIBUSDT from 2023-05-01, DOGEUSDT from 2023-05-01. BONKUSDT returned HTTP 200 with an EMPTY [] - the pair did not exist in that window. IMPORTANT: this is SYMBOL-based, so it gives the exchange price of the ticker, not a specific contract - use it for a price series, not to price an arbitrary contract address.

- **Binance public klines - alternate hosts** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api1.binance.com/api/v3/klines?symbol={symbol}&interval={interval}`
  - Free tier: fully free, no key
  - Rate limit: 1200 request weight/min per IP
  - Live body: `[[1683244800000,"0.00000197","0.00000439","0.00000197","0.00000373","46108639000543.00",1683331199999,"154291982.66948946",477819,"24373246666898.00","81772634.23419222","0"],[1683331200000,"0.0000037`
  - Notes: Live probes returned HTTP 200 with identical candles on api1.binance.com and data-api.binance.vision (market-data only, no trading). api.binance.us also returned HTTP 200 but its PEPEUSDT series starts 2024-12 - use it only as a last resort.

- **MEXC public klines** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={ms}&endTime={ms}`
  - Free tier: fully free, no key
  - Rate limit: not published (public endpoint)
  - Live body: `[[1682899200000,"0.00000072","0.0000015225","0.000000687","0.000001175","68724323372314",1682985600000,"73123917.2915272009"],[1682985600000,"0.000001175","0.00000145","0.000001","0.0000011495","30258`
  - Notes: Live probe returned HTTP 200 with 7 real daily PEPEUSDT candles starting exactly 2023-05-01 (open 0.00000072, close 0.000001175) - earlier than Binance's PEPE series.

- **Gate.io public candlesticks** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair={pair}&interval={interval}&from={unix}&to={unix}`
  - Free tier: fully free, no key
  - Rate limit: public endpoints are rate limited
  - Live body: `[["1682899200","49396192.05484662","0.000001175","0.0000015","0.0000006865","0.00000072526","45231788689453.62500000","true"],["1682985600","28290418.07782433","0.00000114972","0.00000143742","0.00000`
  - Notes: Live probe returned HTTP 200 with 7 real daily PEPE_USDT candles from 2023-05-01.

- **Bitget public candles** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.bitget.com/api/v2/spot/market/candles?symbol={symbol}&granularity={gran}&startTime={ms}&endTime={ms}`
  - Free tier: fully free, no key
  - Rate limit: public endpoints are rate limited
  - Live body: `{"code":"00000","msg":"success","requestTime":1793670042247,"data":[["1682956800000","0.00000097626","0.0000014325","0.00000086804","0.000001037","7880848663308","9053232.02440136341","9053232.0244013`
  - Notes: Live probe returned HTTP 200 (code 00000) with real daily PEPEUSDT candles from 2023-05-04.

- **Bybit public kline** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.bybit.com/v5/market/kline?category=spot&symbol={symbol}&interval={interval}&start={ms}&end={ms}&limit={n}`
  - Free tier: fully free, no key
  - Rate limit: public endpoints ~10 req/s
  - Live body: `{"retCode":0,"retMsg":"OK","result":{"category":"spot","symbol":"PEPEUSDT","list":[["1683417600000","0.0000026253","0.0000031247","0.0000024","0.0000027862","5706628723748","15535646.8688400607"],["16`
  - Notes: Live probe returned HTTP 200 (retCode 0) with real daily PEPEUSDT candles for the May-2023 window.

- **Coinbase Exchange public candles** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.exchange.coinbase.com/products/{product}/candles?granularity={sec}&start={iso}&end={iso}`
  - Free tier: public market data is free and unauthenticated
  - Rate limit: public endpoints ~10 req/s
  - Live body: `[[1683417600,0.00000931,0.00000955,0.00000948,0.00000936,581875831217],[1683331200,0.00000919,0.00001007,0.00001001,0.00000947,1174878223654],[1683244800,0.00000976,0.0000104,0.0000099,0.00001002,7796`
  - Notes: Live probes returned HTTP 200 with 7 daily candles for SHIB-USD and DOGE-USD in the May-2023 window (e.g. SHIB 9.36e-06 close). PEPE-USD returned HTTP 200 with an EMPTY [] for that window - the product exists (the /products/PEPE-USD route returned HTTP 200) but has no history there. Candles are [time, low, high, open, close, volume], newest first.

- **OKX public candles** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://www.okx.com/api/v5/market/history-candles?instId={inst_id}&bar={bar}&after={ms}&before={ms}&limit={n}`
  - Free tier: fully free, no key
  - Rate limit: public endpoints ~20 req/2s per IP
  - Live body: `{"code":"0","data":[],"msg":""}`
  - Notes: Live probe returned HTTP 200 (code 0) but with an EMPTY data[] for PEPE-USDT in the May-2023 window - OKX did not list the pair then. The route works, the data does not exist for that period.

- **Dexscreener public API** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.dexscreener.com/latest/dex/tokens/{token_address}`
  - Free tier: free: 300 req/min for the pair/token lookup endpoints
  - Rate limit: 300 req/min (pairs & tokens endpoints)
  - Live body: `{"schemaVersion":"1.0.0","pairs":[{"chainId":"ethereum","dexId":"uniswap","url":"https://dexscreener.com/ethereum/0xa43fe16908251ee70ef74718545e4fe6c5ccec9f","pairAddress":"0xA43fe16908251ee70EF747185`
  - Notes: Live probe returned HTTP 200 with 30 pairs for the PEPE contract and HTTP 200 with 30 pairs for a Solana token. The token-pairs v1 route also worked. CURRENT PRICE ONLY - no history.

- **Honeypot.is public API** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.honeypot.is/v2/IsHoneypot?address={token_address}&chainID={chain_id}`
  - Free tier: free, no key (rate limited)
  - Rate limit: free tier rate limited
  - Live body: `{"token":{"name":"Pepe", "symbol":"PEPE", "decimals":18, "address":"0x6982508145454Ce325dDbE47a25d4ec3d2311933", "totalHolders":599953}, "withToken":{"name":"Wrapped Ether", "symbol":"WETH", "decimals`
  - Notes: Live probe returned HTTP 200 with token{}, summary{}, honeypotResult{}, simulationResult{}, holderAnalysis{}, flags[], contractCode, chain, router, pair, pairAddress. Useful as a pre-filter before pulling holder lists.

- **Jupiter price API (Solana)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://lite-api.jup.ag/price/v3?ids={mint}`
  - Free tier: free, no key (Jupiter public API)
  - Rate limit: ~60 requests/minute on the public tier
  - Live body: `{"DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263":{"createdAt":"2024-06-07T10:26:40.709Z","liquidity":5914685.583631858,"usdPrice":0.000002774353182991012,"blockId":464724482,"decimals":5,"priceChange24`
  - Notes: Live probe returned HTTP 200 with {DezXAZ8z...:{createdAt, liquidity:5914685.58, usdPrice:2.774353182991012e-06, blockId, decimals, priceChange24h}} - keyed by mint address, so it works for any Solana memecoin. CURRENT PRICE ONLY.

- **DefiLlama historical price (Solana leg)** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://coins.llama.fi/prices/historical/{unix_timestamp}/solana:{mint}`
  - Free tier: fully free, no key
  - Rate limit: not published for coins.llama.fi
  - Live body: `{"coins":{}}`
  - Notes: Live probe for WIF (EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm) at 2023-12-01 returned HTTP 200 with an EMPTY coins{} object - WIF is not in DefiLlama's index, while BONK (DezXAZ8z...) at the same timestamp returned a real price. Solana coverage is per-token, not universal.


### 3.2 Price sources that are NOT usable keyless

- **CoinGecko public API (api.coingecko.com)** - `conn_fail` | key: free | fallback: no
  - URL: `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={id}`
  - Free tier: CoinGecko free (Demo) tier: 10,000 calls/month, ~30 calls/min, demo key required for market_chart
  - Rate limit: Demo tier: 10,000 calls/month, 30 calls/min
  - Live body: `EXCEPTION ConnectionError: ('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None))`
  - Notes: IMPORTANT HOST FACT: api.coingecko.com is UNREACHABLE from this host. Four separate live probes all failed with ConnectionResetError (WinError 10054) during the TLS handshake, and the raw TLS handshake to the resolved Cloudflare IPs (104.20.41.132, 172.66.172.219) fails the same way. Plain HTTP does not help - it 302s to the local URL filter at 192.168.8.1/urlfilter and returns a 'Sangfor NGAF' block page WITH HTTP 200 (a false positive). pro-api.coingecko.com answers normally (HTTP 401 'API Key Missing') and www.coingecko.com answers (HTTP 404 on API paths), so the block is hostname-specific. Do not treat any 200 from this host as CoinGecko data.

- **CoinGecko pro-api (needs key)** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://pro-api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={id}`
  - Free tier: CoinGecko Pro trial/free tier requires a demo or pro key
  - Rate limit: free tier 10,000 calls/month, 30 calls/min
  - Live body: `{"status":{"error_code":10002,"error_message":"API Key Missing"}}`
  - Notes: Live probe returned HTTP 401 {status:{error_code:10002, error_message:'API Key Missing'}} - this hostname's TLS WORKS from here, unlike api.coingecko.com. A key would make it usable.

- **CryptoCompare histoday** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym={quote}&toTs={unix}&limit={n}`
  - Free tier: CryptoCompare free tier with a key: 50 calls/min, 5,000 calls/day
  - Rate limit: 50 calls/min, 5,000 calls/day with a key
  - Live body: `{"Data":{},"Err":{"type":2,"message":"API key required, please refer to the documentation at https://developers.coindesk.com/","http_status_code":401,"frontend":{"type":2,"message":"API key required, `
  - Notes: Live probe returned HTTP 401 with {Data:{}, Err:{type:2, message:'API key required, please refer to the documentation at https://developers.coindesk.com/'}} - the KEYLESS tier was retired.

- **CoinCap** - `dns_fail` | key: KEY | fallback: no
  - URL: `https://api.coincap.io/v2/assets/{slug}/history?interval=d1&start={ms}&end={ms}`
  - Free tier: CoinCap free tier requires an API key (keyless access was retired)
  - Rate limit: free tier ~10,000 requests/month
  - Live body: `EXCEPTION ConnectionError: HTTPSConnectionPool(host='api.coincap.io', port=443): Max retries exceeded with url: /v2/assets/pepe/history?interval=d1&start=1682899200000&end=1683484800000 (Caused by Nam`
  - Notes: Live probe failed at DNS: api.coincap.io does not resolve from this host (NameResolutionError), so the endpoint could not be reached at all, key or no key.

- **Yahoo Finance chart API** - `http_404` (HTTP 404) | key: free | fallback: no
  - URL: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={unix}&period2={unix}&interval=1d`
  - Free tier: free, keyless (unofficial use)
  - Rate limit: not published; aggressively throttled
  - Live body: `{"chart":{"result":null,"error":{"code":"Not Found","description":"No data found, symbol may be delisted"}}}`
  - Notes: Live probe for PEPE-USD returned HTTP 200 with {chart:{result:null, error:{code:'Not Found', description:'No data found, symbol may be delisted'}}} - PEPE-USD is not a Yahoo symbol. Yahoo is not a memecoin price source.

- **CoinPaprika historical** - `http_402` (HTTP 402) | key: KEY | fallback: no
  - URL: `https://api.coinpaprika.com/v1/tickers/{coin_id}/historical?start={iso}&interval=1d`
  - Free tier: CoinPaprika free plan: recent history only; older history is paid
  - Rate limit: free plan limited
  - Live body: `{"error":"Getting daily historical data before 2025-11-03 01:40:44.922966559 +0000 UTC is not allowed in this plan. Check plans on coinpaprika.com/api"}`
  - Notes: Live probe returned HTTP 402 {error:'Getting daily historical data before 2025-11-03 ... is not allowed in this plan.'} - the free plan refuses history older than ~12 months. The ticker id 'pep-pepe' was also HTTP 404 'id not found'.

- **CoinLore public API** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://api.coinlore.net/api/ticker/?id={id}`
  - Free tier: free, no key
  - Rate limit: not published
  - Live body: `[{"id":"90","symbol":"BTC","name":"Bitcoin","nameid":"bitcoin","rank":1,"price_usd":"77232.94","percent_change_24h":"-1.60","percent_change_1h":"0.22","percent_change_7d":"-3.17","price_btc":"1.00","m`
  - Notes: Live probe returned HTTP 200 with a list of tickers (BTC at $77,232.94). Mainstream coins only - no memecoin contract coverage, and no history.


# 4. Social / narrative for memecoins


## 4.1 Sources




**Reddit's JSON API is confirmed blocked from this host** - every `.json` path returned HTTP 403 with a 189,908-byte block page ('You've been blocked by network security'): the subreddit root, old.reddit.com, oauth.reddit.com, api.reddit.com, site-wide search and a deep-link comments path. **The RSS path works** - `https://www.reddit.com/r/{sub}/new.rss` returned HTTP 200 with a valid Atom feed. Use RSS.

**ApeWisdom has a silent-failure trap.** The commonly quoted `/api/` and `/api/top-tokens/` return the DOCS HTML page with HTTP 200 - a false positive. The working path is `/api/v1.0/filter/{filter}` and returns real JSON. Use filter `all` (the `crypto` filter probed empty).

**The Discord widget only works for guilds that enable it** - guild `1162499246503759962` (r/Pepecoin) returned HTTP 200 with `members[]` and `presence_count`; a disabled guild returned HTTP 403 and an unknown id HTTP 404. The invite endpoint gives you a real guild id and member counts, and works keyless.

**BEST FREE OPTION: Telegram `t.me/s/{channel}` for channel posts, Reddit `.rss` for subreddit posts, Discord widget for online-member counts, ApeWisdom for mention ranking**

**FALLBACK CHAIN:**

1. Telegram public channel preview (t.me/s) - `ok` (HTTP 200) - Recent posts from a public Telegram channel
2. Reddit public RSS (WORKS where .json is blocked) - `ok` (HTTP 200) - Subreddit posts as Atom/RSS - the working Reddit path from this host
3. ApeWisdom v1.0 JSON API - `ok` (HTTP 200) - Social-mention ranking of tickers (memecoin narrative signal)
4. Discord server widget (guilds with the widget enabled) - `ok` (HTTP 200) - Discord server name, channels and ONLINE MEMBER COUNT
5. Discord public invite metadata - `ok` (HTTP 200) - Discord server member/online counts from an invite code
6. Google Trends trending RSS - `ok` (HTTP 200) - Official Google Trends trending searches (no key)
7. Warpcast public API - `ok` (HTTP 200) - Farcaster profile by username
8. Bluesky public API - `ok` (HTTP 200) - Bluesky actor/post search for social narrative
9. Telegram public USER preview (t.me/s) - `ok` (HTTP 200) - Public profile of a Telegram user

- **Telegram public channel preview (t.me/s)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://t.me/s/{channel_username}`
  - Free tier: fully free, no key
  - Rate limit: not published; Telegram throttles by IP
  - Live body: `<!DOCTYPE html> <html> <head> <meta charset="utf-8"> <title>Telegram: Contact @coinbase</title> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <script>location.hash=''</script>`
  - Notes: Live probes returned HTTP 200 for channels: /s/coinbase (10,786 bytes, title 'Telegram: Contact @coinbase') and /s/BitcoinMagazine (10,858 bytes). ?embed=1&mode=tme also returned HTTP 200 with the same content. Note the byte counts are small - this is the PREVIEW page; parse the .tgme_widget_message blocks.

- **Telegram public USER preview (t.me/s)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://t.me/s/{username}`
  - Free tier: fully free, no key
  - Rate limit: not published
  - Live body: `<!DOCTYPE html> <html> <head> <meta charset="utf-8"> <title>Pavel Durov – Telegram</title> <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, u`
  - Notes: Live probe of /s/durov returned HTTP 200 with title 'Pavel Durov - Telegram' and 147,620 bytes - a USER profile page, not a channel post feed. Channel preview and user preview are different shapes on the same route.

- **Telegram channel landing page** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://t.me/{channel_username}`
  - Free tier: fully free, no key
  - Rate limit: not published
  - Live body: `<!DOCTYPE html> <html> <head> <meta charset="utf-8"> <title>Telegram: Contact @coinbase</title> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <script>location.hash=''</script>`
  - Notes: Live probe returned HTTP 200 with title 'Telegram: Contact @coinbase'.

- **Telegram widget embed** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://t.me/{channel_username}?embed=1`
  - Free tier: fully free, no key
  - Rate limit: not published
  - Live body: `<!DOCTYPE html> <html> <head> <meta charset="utf-8"> <title>Telegram Widget</title> <base target="_blank"> <script>document.cookie="stel_dt="+encodeURIComponent((new Date).getTimezoneOffset())+";path=`
  - Notes: Live probe returned HTTP 200 with title 'Telegram Widget' (4,842 bytes of inline JS).

- **Reddit public RSS (WORKS where .json is blocked)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://www.reddit.com/r/{subreddit}/new.rss?limit={n}`
  - Free tier: free, keyless
  - Rate limit: same as the web app, ~10 req/min anonymous
  - Live body: `<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/"><category term="CryptoCurrency" label="r/CryptoCurrency"/><updated>2026-11-0`
  - Notes: THE WORKING REDDIT PATH. Live probe returned HTTP 200 with an Atom feed (12,878 bytes, title 'newest submissions : CryptoCurrency'). NOTE /r/wallstreetcoins/top.rss returned HTTP 404 with feed title 'WallStreetCoins: banned' - the subreddit is banned, and RSS reports that as 404 rather than 403.

- **Reddit public JSON** - `http_403` (HTTP 403) | key: free | fallback: no
  - URL: `https://www.reddit.com/r/{subreddit}/new.json?limit={n}`
  - Free tier: Reddit's public JSON is free but IP-gated
  - Rate limit: ~10 req/min anonymous; 429 otherwise
  - Live body: `<body class=theme-beta><div><style>.theme-light,:root{--rem360:22.5rem;--rem320:20rem;--rem192:12rem;--rem144:9rem;--rem128:8rem;--rem96:6rem;--rem90:5.625rem;--rem88:5.5rem;--rem64:4rem;--rem56:3.5re`
  - Notes: CONFIRMED BLOCKED from this host: HTTP 403 with a 189,908-byte Cloudflare/Reddit block page ('You've been blocked by network security'). The same 403 came back for old.reddit.com, oauth.reddit.com, api.reddit.com, www.reddit.com/search.json and a deep-link comments .json. ALL .json paths are blocked.

- **ApeWisdom v1.0 JSON API** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://apewisdom.io/api/v1.0/filter/{filter}`
  - Free tier: free, keyless
  - Rate limit: not published
  - Live body: `{"count":640,"pages":7,"current_page":1,"results":[{"rank":1,"ticker":"AAPL","name":"Apple","mentions":230,"upvotes":632,"rank_24h_ago":14,"mentions_24h_ago":21},{"rank":2,"ticker":"SPY","name":"SPDR `
  - Notes: Live probe returned HTTP 200 application/json with {count:640, pages:7, current_page:1, results:[{rank, ticker, name, mentions, upvotes, rank_24h_ago, mentions_24h_ago}]}. CRITICAL PATH NOTE: the commonly quoted '/api/' and '/api/top-tokens/' return the DOCS HTML page with HTTP 200 - a silent false positive. The working path is '/api/v1.0/filter/{filter}' (filters: all, all-stocks, crypto). The 'crypto' filter probed empty (count:0), so use 'all'.

- **Discord server widget (guilds with the widget enabled)** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://discord.com/api/guilds/{guild_id}/widget.json`
  - Free tier: fully free, no key
  - Rate limit: not published; Discord throttles by IP
  - Live body: `{"id":"1162499246503759962","name":"r/Pepecoin","instant_invite":"https://discord.com/invite/85x3XKk9","channels":[{"id":"1434699552346345583","name":"Ribbit Lounge 1","position":8},{"id":"14347000781`
  - Notes: Live probe returned HTTP 200 for guild 1162499246503759962 (r/Pepecoin) with id, name, instant_invite, channels[] and members[] + presence_count - the online-member count is the narrative signal. It only works for guilds that ENABLE the widget: guild 1085633062735458424 returned HTTP 403 (widget disabled) and unknown ids returned HTTP 404 'Unknown Guild'.

- **Discord public invite metadata** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://discord.com/api/v9/invites/{code}?with_counts=true`
  - Free tier: fully free, no key
  - Rate limit: not published; Discord throttles by IP (429 common)
  - Live body: `{"type":0,"code":"qaQa6M6mN2","inviter":{"id":"200642763459395585","username":"theonlynom","avatar":"110a0cad4a75cde5d47d3892c61d2adb","discriminator":"0","public_flags":0,"flags":0,"banner":null,"acc`
  - Notes: Live probe returned HTTP 200 with code, guild{id,name,...}, approximate_member_count and approximate_presence_count. Also used it to resolve a REAL guild id for the widget test.

- **Discord widget iframe page** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://discord.com/widget?id={guild_id}&theme=dark`
  - Free tier: fully free, no key
  - Rate limit: not published
  - Live body: `<!doctype html> <html> <head> <meta charset="utf-8" /> <title>Discord Widget</title> <meta name="viewport" content="width=device-width, initial-scale=1.0"><link href="/assets/fdf2a99770058b1f.css" rel`
  - Notes: Live probe returned HTTP 200 with title 'Discord Widget' (1,768 bytes of HTML).

- **Google Trends trending RSS** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://trends.google.com/trending/rss?geo={geo}`
  - Free tier: free, keyless, official
  - Rate limit: not published; Google returns 429 under load
  - Live body: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?> <rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:ht="https://trends.google.com/trending/rss" version="2.0"> <channel> <title>Daily Search Tre`
  - Notes: Live probe returned HTTP 200 with 10 <item> entries (e.g. 'ken paxton', 'kyle monangai', 'seattle'). This is the STABLE keyless Trends route - the /trends/api/explore JSON endpoint returned HTTP 400 for the pytrends-shaped payload and HTTP 429 for another, and /trends/api/dailytrends returned HTTP 404.

- **Nostr public relay (websocket)** - `conn_fail` | key: free | fallback: no
  - URL: `wss://{relay}/`
  - Free tier: free, keyless public relays
  - Rate limit: relay specific
  - Live body: `{"relay": "wss://relay.damus.io", "events": [], "eose": false, "ok": false}`
  - Notes: The relay HTTPS roots answered HTTP 200 (relay.damus.io and nos.lol both served a 'strfry: a nostr relay' page), so the hosts are reachable, but a REQ over websocket did not return events in this probe (relay.nostr.band timed out during the opening handshake). Treat Nostr as reachable-but-not-yet-proven for data retrieval; the 'websockets' library IS installed on this host.

- **Warpcast public API** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://api.warpcast.com/v2/user-by-username?username={fname}`
  - Free tier: free, keyless public API
  - Rate limit: not published
  - Live body: `{"result":{"user":{"fid":3,"displayName":"Dan Romero","profile":{"bio":{"text":"Interested in technology and other stuff.","mentions":[],"channelMentions":[]},"location":{"placeId":"","description":""`
  - Notes: Live probe returned HTTP 200 with result.user{fid, displayName, profile{bio, location}, ...}. Note all the public Farcaster HUBS failed DNS from this host (hub.pinata.cloud, nemes.farcaster.xyz, hub.farcaster.standardcrypto.vc, sneaker.farcaster.xyz, dehub.farcaster.xyz, hub-2.decent.land, farcasterhub.com, nemes-testnet.farcaster.xyz) while api.warpcast.com and hub-api.neynar.com resolved.

- **Bluesky public API** - `ok` (HTTP 200) | key: free | fallback: YES
  - URL: `https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors?q={query}&limit={n}`
  - Free tier: free, keyless public AppView
  - Rate limit: public rate limited
  - Live body: `{"actors":[{"did":"did:plc:s6tptx6es7ibyqab3j6hx5wm","handle":"cryptotheism.bsky.social","displayName":"Brain Dracula","avatar":"https://cdn.bsky.app/img/avatar/plain/did:plc:s6tptx6es7ibyqab3j6hx5wm/`
  - Notes: Live probe of app.bsky.actor.searchActors returned HTTP 200 with actors[{did, handle, displayName, avatar}]. NOTE app.bsky.feed.searchPosts returned HTTP 403 - POST SEARCH is blocked from this host while ACTOR SEARCH works.

- **Mastodon public search API** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://{instance}/api/v2/search?q={query}&type={type}&limit={n}`
  - Free tier: free, keyless
  - Rate limit: instance specific
  - Live body: `{"accounts":[],"statuses":[],"hashtags":[],"collections":[]}`
  - Notes: Live probe of mastodon.social/api/v2/search?q=pepe returned HTTP 200 with {accounts:[], statuses:[], hashtags:[], collections:[]} - the endpoint works but returned no matches for 'pepe'.

- **TikTok oEmbed** - `ok` (HTTP 200) | key: free | fallback: no
  - URL: `https://www.tiktok.com/oembed?url=https://www.tiktok.com/@{handle}`
  - Free tier: free, keyless
  - Rate limit: not published
  - Live body: `{"version":"1.0","type":"rich","title":"Pepe Coin Memes's Creator Profile","author_url":"https://www.tiktok.com/@pepecoin","author_name":"Pepe Coin Memes","width":"100%","height":"100%","html":"<block`
  - Notes: Live probe returned HTTP 200 with {version, type:'rich', title:'Pepe Coin Memes\'s Creator Profile', author_url, author_name, html}.


# 5. Dune / off-chain analytics


## 5.1 Sources




**Verified by fetching: nothing on Dune is usable from this host without an API key.**

- `api.dune.com/api/v1/query/{id}/results` -> **HTTP 401** `{"error":"invalid API Key"}`
- `api.dune.com/api/v1/query/results` -> **HTTP 401** (same body)
- `api.dune.com/api/v1/execution/{id}/status` -> **HTTP 402** 'A valid payment credential is required to access this resource'
- `dune.com/queries/{id}`, `dune.com/embeds/queries/{id}`, `dune.com/api/embeds/{id}`, `dune.com/dashboards`, `dune.com/queries?q=...` and `core-api.dune.com` -> all **HTTP 403** with a 5,659-byte Cloudflare 'Attention Required!' challenge page

A placeholder key produced the same 401.

**What the community dashboards expose about wallet PnL:** the dashboards themselves are the only place that information exists, and they are Cloudflare-gated here. The community API free tier (100 credits/day, 15 executions/day after signup) is the route to the same underlying queries - so if wallet-PnL analytics are needed, sign up for the free community API key rather than fighting the web app.

**The package's own alternative:** per-wallet PnL does not need Dune. Combine the keyless Blockscout/Routescan transfer tape (section 2) with the keyless DefiLlama historical prices (section 3) and compute PnL locally. That is the whole point of the DefiLlama fix.

**BEST FREE OPTION: None. Dune has no keyless path from this host.**

**FALLBACK CHAIN:**

1. Dune community API - `http_401` (HTTP 401) - Run/retrieve Dune queries for wallet PnL analytics
2. Dune public query/dashboard pages - `http_403` (HTTP 403) - Read a published Dune dashboard without a key
3. Dune public dashboard exposure of wallet PnL - `http_403` (HTTP 403) - What the community dashboards expose about wallet PnL without a key

- **Dune community API** - `http_401` (HTTP 401) | key: KEY | fallback: no
  - URL: `https://api.dune.com/api/v1/query/{query_id}/results`
  - Free tier: Dune community API free tier: 100 credits/day and 15 query executions/day after signup; paid tiers raise both
  - Rate limit: community tier: 15 executions/day, 100 credits/day
  - Live body: `{"error":"invalid API Key"}`
  - Notes: Live probe returned HTTP 401 {error:'invalid API Key'} for /api/v1/query/{id}/results and /api/v1/query/results; the /api/v1/execution/{id}/status route returned HTTP 402 ('A valid payment credential is required'). A placeholder key also returned 401. KEY REQUIRED for every route.

- **Dune public query/dashboard pages** - `http_403` (HTTP 403) | key: free | fallback: no
  - URL: `https://dune.com/queries/{query_id}`
  - Free tier: public dashboards are readable in a browser; the API behind them is keyed
  - Rate limit: n/a
  - Live body: `<!DOCTYPE html> <!--[if lt IE 7]> <html class="no-js ie6 oldie" lang="en-US"> <![endif]--> <!--[if IE 7]> <html class="no-js ie7 oldie" lang="en-US"> <![endif]--> <!--[if IE 8]> <html class="no-js ie8`
  - Notes: Live probes of dune.com/queries/1, dune.com/embeds/queries/1, dune.com/api/embeds/1, dune.com/dashboards, dune.com/queries?q=... and core-api.dune.com all returned HTTP 403 with a 5,659-byte Cloudflare 'Attention Required!' challenge page. dune.com is Cloudflare-gated from this host for non-browser clients.

- **Dune public dashboard exposure of wallet PnL** - `http_403` (HTTP 403) | key: free | fallback: no
  - URL: `https://dune.com/dashboards`
  - Free tier: n/a - none of it is reachable keyless from this host
  - Rate limit: n/a
  - Live body: `<!DOCTYPE html> <!--[if lt IE 7]> <html class="no-js ie6 oldie" lang="en-US"> <![endif]--> <!--[if IE 7]> <html class="no-js ie7 oldie" lang="en-US"> <![endif]--> <!--[if IE 8]> <html class="no-js ie8`
  - Notes: Verified by fetching: NO Dune surface is usable from this host without a key. The web app, the embeds and core-api are all Cloudflare-403; the API is 401/402. Wallet PnL on Dune is only reachable with a community API key.


# Appendix A - method

- Probe harness: `tools/freeprobe/` (`runner.py` + `stage1..stage16`), reusing `leapspace/http.py` for the browser UA and the certifi TLS context.
- Every source row in `data/free_data_sources.json` carries the `probe_names` and `probe_stage` it came from, so any status can be re-derived from `reports/freeprobe/stage*.json`.
- `tools/freeprobe/validate.py` re-checks every probe body for Cloudflare/Sangfor block markers. 10 HTTP-200 false positives were found this way and are recorded as failures, not successes.
- Test tokens: PEPE `0x6982508145454ce325ddbe47a25d4ec3d2311933` (Ethereum, Apr-2023), SHIB `0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE` (Ethereum, May-2020), BONK `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263` (Solana).


# Appendix B - the whole catalogue

| Source | Category | Live status | Key? | Fallback? |
|--------|----------|-------------|------|-----------|
| Blockscout holders - Ethereum (eth.blockscout.com) | EVM token holder list for Ethereum (to | ok (200) | no | YES |
| Blockscout holders - Gnosis (gnosis.blockscout.com) | EVM token holder list for Gnosis (top  | ok (200) | no | YES |
| Blockscout holders - OP Mainnet (optimism.blockscout.com) | EVM token holder list for OP Mainnet ( | ok (200) | no | YES |
| Blockscout holders - Scroll (scroll.blockscout.com) | EVM token holder list for Scroll (top  | ok (200) | no | YES |
| Blockscout holders - zkSync (zksync.blockscout.com) | EVM token holder list for zkSync (top  | ok (200) | no | YES |
| Blockscout holders - Cronos (cronos.blockscout.com) | EVM token holder list for Cronos (top  | ok (200) | no | YES |
| Blockscout holders - Rootstock (rootstock.blockscout.com) | EVM token holder list for Rootstock (t | ok (200) | no | YES |
| Blockscout holders - Celo (celo.blockscout.com) | EVM token holder list for Celo (top ho | ok (200) | no | YES |
| Blockscout holders - Filecoin (filecoin.blockscout.com) | EVM token holder list for Filecoin (to | ok (200) | no | YES |
| Blockscout holders - Unichain (unichain.blockscout.com) | EVM token holder list for Unichain (to | ok (200) | no | YES |
| Blockscout holders - ApeChain (apechain.blockscout.com) | EVM token holder list for ApeChain (to | ok (200) | no | YES |
| Blockscout holders - Soneium (soneium.blockscout.com) | EVM token holder list for Soneium (top | ok (200) | no | YES |
| Blockscout holders - HashKey (hashkey.blockscout.com) | EVM token holder list for HashKey (top | ok (200) | no | YES |
| Blockscout - Base (base.blockscout.com) | EVM token holder list for Base | http_403 (403) | no | no |
| Blockscout - Arbitrum One (arbitrum.blockscout.com) | EVM token holder list for Arbitrum One | http_403 (403) | no | no |
| Blockscout - Polygon (polygon.blockscout.com) | EVM token holder list for Polygon | http_403 (403) | no | no |
| Blockscout - BNB Smart Chain (bsc.blockscout.com) | EVM token holder list for BNB Smart Ch | http_404 (404) | no | no |
| Blockscout - Linea (linea.blockscout.com) | EVM token holder list for Linea | http_404 (404) | no | no |
| Blockscout - Blast (blast.blockscout.com) | EVM token holder list for Blast | http_404 (404) | no | no |
| Blockscout - Sonic (sonic.blockscout.com) | EVM token holder list for Sonic | http_404 (404) | no | no |
| Blockscout - Mantle (mantle.blockscout.com) | EVM token holder list for Mantle | http_404 (404) | no | no |
| Blockscout - Flare (flare.blockscout.com) | EVM token holder list for Flare | http_404 (404) | no | no |
| Blockscout - Fraxtal (fraxtal.blockscout.com) | EVM token holder list for Fraxtal | http_404 (404) | no | no |
| Blockscout - Metis (metis.blockscout.com) | EVM token holder list for Metis | http_404 (404) | no | no |
| Blockscout - Mode (mode.blockscout.com) | EVM token holder list for Mode | http_404 (404) | no | no |
| Blockscout - Sei (sei.blockscout.com) | EVM token holder list for Sei | http_404 (404) | no | no |
| Blockscout - Taiko (taiko.blockscout.com) | EVM token holder list for Taiko | http_404 (404) | no | no |
| Blockscout - World Chain (worldchain.blockscout.com) | EVM token holder list for World Chain | http_404 (404) | no | no |
| Blockscout - Zora (zora.blockscout.com) | EVM token holder list for Zora | http_404 (404) | no | no |
| Blockscout - Ink (ink.blockscout.com) | EVM token holder list for Ink | http_404 (404) | no | no |
| Blockscout - Story (story.blockscout.com) | EVM token holder list for Story | http_404 (404) | no | no |
| Blockscout - Berachain (berachain.blockscout.com) | EVM token holder list for Berachain | http_404 (404) | no | no |
| Blockscout - Monad (monad.blockscout.com) | EVM token holder list for Monad | http_404 (404) | no | no |
| Blockscout - Lisk (lisk.blockscout.com) | EVM token holder list for Lisk | http_404 (404) | no | no |
| Blockscout - Abstract (abstract.blockscout.com) | EVM token holder list for Abstract | http_404 (404) | no | no |
| Blockscout - Hyperliquid (hyperliquid.blockscout.com) | EVM token holder list for Hyperliquid | http_404 (404) | no | no |
| Blockscout - Opera (opera.blockscout.com) | EVM token holder list for Opera | http_404 (404) | no | no |
| Blockscout - Manta (manta.blockscout.com) | EVM token holder list for Manta | http_404 (404) | no | no |
| Blockscout - Moonbeam (moonbeam.blockscout.com) | EVM token holder list for Moonbeam | http_404 (404) | no | no |
| Blockscout - Moonriver (moonriver.blockscout.com) | EVM token holder list for Moonriver | http_404 (404) | no | no |
| Blockscout - Evmos (evmos.blockscout.com) | EVM token holder list for Evmos | http_404 (404) | no | no |
| Blockscout - Harmony (harmony.blockscout.com) | EVM token holder list for Harmony | http_404 (404) | no | no |
| Blockscout - Algorand (algorand.blockscout.com) | EVM token holder list for Algorand | http_404 (404) | no | no |
| Blockscout - IoTeX (iotex.blockscout.com) | EVM token holder list for IoTeX | http_404 (404) | no | no |
| Blockscout - Viction (viction.blockscout.com) | EVM token holder list for Viction | http_404 (404) | no | no |
| Blockscout - Polygon zkEVM (zkevm.blockscout.com) | EVM token holder list for Polygon zkEV | http_404 (404) | no | no |
| Blockscout - Mordor (mordor.blockscout.com) | EVM token holder list for Mordor | http_404 (404) | no | no |
| Blockscout - Memecore (memecore.blockscout.com) | EVM token holder list for Memecore | http_404 (404) | no | no |
| Blockscout - Milkomeda (milkomeda.blockscout.com) | EVM token holder list for Milkomeda | http_404 (404) | no | no |
| Blockscout - BOB (bob.blockscout.com) | EVM token holder list for BOB | http_404 (404) | no | no |
| Blockscout - Shape (shape.blockscout.com) | EVM token holder list for Shape | http_404 (404) | no | no |
| Blockscout - opBNB (opbnb.blockscout.com) | EVM token holder list for opBNB | http_404 (404) | no | no |
| Blockscout - Redstone (redstone.blockscout.com) | EVM token holder list for Redstone | http_404 (404) | no | no |
| Blockscout - Sophon (sophon.blockscout.com) | EVM token holder list for Sophon | http_404 (404) | no | no |
| Blockscout - Gobi (gobi.blockscout.com) | EVM token holder list for Gobi | http_404 (404) | no | no |
| Blockscout - Syshub (syshub.blockscout.com) | EVM token holder list for Syshub | http_404 (404) | no | no |
| Blockscout - Petopia (petopia.blockscout.com) | EVM token holder list for Petopia | http_404 (404) | no | no |
| Blockscout - Flare Testnet (flare-testnet.blockscout.com) | EVM token holder list for Flare Testne | http_404 (404) | no | no |
| Blockscout - Lightlink (lightlink.blockscout.com) | EVM token holder list for Lightlink | http_404 (404) | no | no |
| Blockscout - LiquidStake (liquidstake.blockscout.com) | EVM token holder list for LiquidStake | http_404 (404) | no | no |
| Blockscout - Morpheus (morpheus.blockscout.com) | EVM token holder list for Morpheus | http_404 (404) | no | no |
| Blockscout - Rise (rise.blockscout.com) | EVM token holder list for Rise | http_404 (404) | no | no |
| Blockscout - Functionum (functionum.blockscout.com) | EVM token holder list for Functionum | http_404 (404) | no | no |
| Blockscout - Kinto (kinto.blockscout.com) | EVM token holder list for Kinto | http_404 (404) | no | no |
| Blockscout - Lambda (lambda.blockscout.com) | EVM token holder list for Lambda | http_404 (404) | no | no |
| Routescan v2 ERC-20 holders (Ethereum) | EVM token holder list for Ethereum, ke | ok (200) | no | YES |
| Routescan v2 address transactions | Wallet transaction history for an EVM  | ok (200) | no | YES |
| Routescan v2 Etherscan-compatible proxy | EVM token holder list via an Etherscan | error (200) | no | no |
| Etherscan API V2 tokenholderlist | EVM token holder list (Ethereum + some | error (200) | yes | no |
| Etherscan API V2 (non-Ethereum chains) | EVM token holder list on non-Ethereum  | error (200) | yes | no |
| Moralis token owners | EVM token holder list | dns_fail (None) | yes | no |
| OKLink explorer token ranking | EVM token holder list | http_404 (404) | yes | no |
| Covalent token holders | EVM token holder list | http_401 (401) | yes | no |
| Envio HyperSync | EVM token holder list | dns_fail (None) | yes | no |
| Subsquid portal datasets | EVM token holder list (indexed dataset | ok (200) | yes | no |
| Goldsky metadata | EVM token holder list (hosted subgraph | http_404 (404) | yes | no |
| Bitquery GraphQL (free tier) | Wallet token-trade history + holder co | http_401 (401) | yes | no |
| Blockscout address token-transfers (Ethereum) | Wallet token-trade history for an EVM  | ok (200) | no | YES |
| Blockscout address transactions (Ethereum) | Wallet transaction history for an EVM  | ok (200) | no | YES |
| Blockscout internal transactions (Ethereum) | Wallet internal trade history for an E | ok (200) | no | YES |
| Blockscout address token-transfers (Optimism host) | Wallet token-trade history on OP Mainn | ok (200) | no | YES |
| Blockscout token-wide transfers (Ethereum) | Token-wide trade history (all transfer | ok (200) | no | YES |
| Ethplorer (public 'freekey') | Wallet balances/positions + token hold | ok (200) | no | YES |
| Ethplorer getTokenInfo (public 'freekey') | Token metadata incl. holdersCount for  | ok (200) | no | YES |
| Blockscout holders (Ethereum) - PEPE specifically | EVM token holder list for an OLD contr | ok (200) | no | YES |
| Covalent balance-transfers | Wallet token-trade history for an EVM  | http_401 (401) | yes | no |
| Ankr Advanced token-transfers | Wallet token-trade history for an EVM  | http_404 (404) | yes | no |
| Zerion wallet transactions | Wallet token-trade history + PnL for a | http_402 (402) | yes | no |
| DeBank open API | Wallet positions for an EVM address | http_401 (401) | yes | no |
| Alchemy public demo | Raw JSON-RPC | http_429 (429) | yes | no |
| QuickNode | Raw JSON-RPC | http_404 (404) | yes | no |
| Arkham Intelligence API | Wallet trade history + asset intellige | http_400 (400) | yes | no |
| Arkham public explorer page | Wallet trade history (HTML page) | http_403 (403) | yes | no |
| GMGN public web API | Wallet trade history + token info (Sol | http_403 (403) | yes | no |
| Birdeye | Token data + Solana OHLCV + wallet dat | http_401 (401) | yes | no |
| SolanaTracker Data API | Token data + wallet trade history (Sol | http_401 (401) | yes | no |
| Nansen | Token/wallet analytics and token trade | http_401 (401) | yes | no |
| Bubblemaps API | Token holder concentration / clusterin | http_404 (404) | yes | no |
| Growthepie | Chain-level fee/revenue analytics (NOT | ok (200) | yes | no |
| 0x API | DEX quotes/orderbook (not wallet histo | http_404 (404) | yes | no |
| Neynar (Farcaster) | Farcaster user/cast search | http_402 (402) | yes | no |
| PublicNode (keyless RPC) | Raw JSON-RPC for wallet/token history  | ok (200) | no | no |
| drpc.org (keyless RPC) | Raw JSON-RPC for wallet/token history  | ok (200) | no | no |
| 1rpc.io (keyless RPC) | Raw JSON-RPC for wallet/token history  | ok (200) | no | no |
| Flashbots RPC (keyless RPC) | Raw JSON-RPC for wallet/token history  | ok (200) | no | no |
| llamaRPC | Raw JSON-RPC for wallet/token history  | http_525 (525) | no | no |
| BlockPI | Raw JSON-RPC for wallet/token history  | http_503 (503) | no | no |
| DefiLlama historical price by contract address | Historical price for an OLD contract a | ok (200) | no | YES |
| DefiLlama current price by contract address | Current price for a contract address ( | ok (200) | no | YES |
| DefiLlama chart by contract address | Price series for a contract address | ok (200) | no | no |
| DefiLlama historical price - multi-contract batch | Several old contracts at one past time | ok (200) | no | YES |
| DefiLlama historical price - coverage limits | Know where the historical endpoint has | ok (200) | no | no |
| GeckoTerminal OHLCV (per pool) | OHLCV price history for a DEX pool (co | ok (200) | no | YES |
| GeckoTerminal pool discovery by token | Find the pools for a contract address  | ok (200) | no | YES |
| Binance public klines | Historical daily/hourly prices for a L | ok (200) | no | YES |
| Binance public klines - alternate hosts | Historical prices when api.binance.com | ok (200) | no | YES |
| Coinbase Exchange public candles | Historical daily prices for a listed U | ok (200) | no | YES |
| MEXC public klines | Historical daily prices for a listed s | ok (200) | no | YES |
| Gate.io public candlesticks | Historical daily prices for a listed p | ok (200) | no | YES |
| Bitget public candles | Historical daily prices for a listed s | ok (200) | no | YES |
| Bybit public kline | Historical daily prices for a listed s | ok (200) | no | YES |
| OKX public candles | Historical daily prices for a listed p | ok (200) | no | no |
| Dexscreener public API | Current price, liquidity and pool list | ok (200) | no | YES |
| CoinGecko public API (api.coingecko.com) | CoinGecko prices, market data and comm | conn_fail (None) | no | no |
| CoinGecko pro-api (needs key) | CoinGecko prices with the pro-api host | http_401 (401) | yes | no |
| CryptoCompare histoday | Historical daily prices by symbol | http_401 (401) | yes | no |
| CoinCap | Historical asset prices | dns_fail (None) | yes | no |
| Yahoo Finance chart API | Historical daily prices for a symbol | http_404 (404) | no | no |
| CoinPaprika historical | Historical daily prices by coin id | http_402 (402) | yes | no |
| Honeypot.is public API | Token safety / honeypot + holder analy | ok (200) | no | YES |
| CoinLore public API | Current prices and market caps | ok (200) | no | no |
| Telegram public channel preview (t.me/s) | Recent posts from a public Telegram ch | ok (200) | no | YES |
| Telegram public USER preview (t.me/s) | Public profile of a Telegram user | ok (200) | no | YES |
| Telegram channel landing page | Channel metadata / subscriber count fo | ok (200) | no | no |
| Telegram widget embed | Telegram channel post widget (embeddab | ok (200) | no | no |
| Discord public invite metadata | Discord server member/online counts fr | ok (200) | no | YES |
| Discord server widget (guilds with the widget enabled) | Discord server name, channels and ONLI | ok (200) | no | YES |
| Discord widget iframe page | HTML page hosting the Discord widget | ok (200) | no | no |
| Reddit public JSON | Subreddit posts/comments as JSON | http_403 (403) | no | no |
| Reddit public RSS (WORKS where .json is blocked) | Subreddit posts as Atom/RSS | ok (200) | no | YES |
| ApeWisdom v1.0 JSON API | Social-mention ranking of tickers (mem | ok (200) | no | YES |
| Google Trends trending RSS | Official Google Trends trending search | ok (200) | no | YES |
| Nostr public relay (websocket) | Nostr notes by kind (social feed) | conn_fail (None) | no | no |
| Warpcast public API | Farcaster profile by username | ok (200) | no | YES |
| Bluesky public API | Bluesky actor/post search for social n | ok (200) | no | YES |
| Mastodon public search API | Cross-instance social search | ok (200) | no | no |
| TikTok oEmbed | TikTok profile metadata for a token's  | ok (200) | no | no |
| Dune community API | Run/retrieve Dune queries for wallet P | http_401 (401) | yes | no |
| Dune public query/dashboard pages | Read a published Dune dashboard withou | http_403 (403) | no | no |
| Dune public dashboard exposure of wallet PnL | What the community dashboards expose a | http_403 (403) | no | no |
| Jupiter token search (Solana) | Solana token discovery / metadata by m | ok (200) | no | YES |
| Jupiter price API (Solana) | Current price + liquidity + 24h change | ok (200) | no | YES |
| RugCheck report (Solana) | Token risk report, authorities, LP sta | ok (200) | no | YES |
| Dexscreener (Solana) | Current price, liquidity and pair list | ok (200) | no | YES |
| Solana public JSON-RPC (keyless) | Solana wallet transaction history via  | ok (200) | no | YES |
| DefiLlama historical price (Solana leg) | Historical price for a Solana memecoin | ok (200) | no | no |


# Appendix C - TOP-20 VERIFIED-WORKING-FREE ENDPOINTS

For a quick check. Every row returned HTTP 2xx with real data on a live call from this host.

| # | Endpoint | Live status | HTTP | Purpose |
|---|----------|-------------|------|---------|
| 1 | `https://coins.llama.fi/prices/historical/{unix_timestamp}/{chain}:{token_address}` | ok | 200 | Historical price for an OLD contract address at a PAST timestamp (the cost-basis fix) |
| 2 | `https://coins.llama.fi/prices/current/{chain}:{token_address}` | ok | 200 | Current price for a contract address (and batch quotes) |
| 3 | `https://coins.llama.fi/prices/historical/{unix_timestamp}/{chain1}:{addr1},{chain2}:{addr2}` | ok | 200 | Several old contracts at one past timestamp in one call |
| 4 | `https://eth.blockscout.com/api/v2/tokens/{token_address}/holders` | ok | 200 | EVM token holder list for Ethereum (top holders of the top token on this chain) |
| 5 | `https://gnosis.blockscout.com/api/v2/tokens/{token_address}/holders` | ok | 200 | EVM token holder list for Gnosis (top holders of LINK) |
| 6 | `https://api.routescan.io/v2/network/mainnet/evm/1/erc20/{token_address}/holders` | ok | 200 | EVM token holder list for Ethereum, keyless |
| 7 | `https://eth.blockscout.com/api/v2/addresses/{address}/token-transfers` | ok | 200 | Wallet token-trade history for an EVM address |
| 8 | `https://eth.blockscout.com/api/v2/tokens/{token_address}/transfers` | ok | 200 | Token-wide trade history (all transfers of one token) |
| 9 | `https://eth.blockscout.com/api/v2/addresses/{address}/internal-transactions` | ok | 200 | Wallet internal trade history for an EVM address |
| 10 | `https://api.routescan.io/v2/network/mainnet/evm/all/address/{address}/transactions` | ok | 200 | Wallet transaction history for an EVM address, keyless |
| 11 | `https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={ms}&endTime={ms}&limit={n}` | ok | 200 | Historical daily/hourly prices for a LISTED symbol |
| 12 | `https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={ms}&endTime={ms}` | ok | 200 | Historical daily prices for a listed symbol |
| 13 | `https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}` | ok | 200 | OHLCV price history for a DEX pool (contract-address based) |
| 14 | `https://api.dexscreener.com/latest/dex/tokens/{token_address}` | ok | 200 | Current price, liquidity and pool list for a contract address |
| 15 | `https://apewisdom.io/api/v1.0/filter/{filter}` | ok | 200 | Social-mention ranking of tickers (memecoin narrative signal) |
| 16 | `https://www.reddit.com/r/{subreddit}/new.rss?limit={n}` | ok | 200 | Subreddit posts as Atom/RSS - the working Reddit path from this host |
| 17 | `https://discord.com/api/guilds/{guild_id}/widget.json` | ok | 200 | Discord server name, channels and ONLINE MEMBER COUNT |
| 18 | `https://discord.com/api/v9/invites/{code}?with_counts=true` | ok | 200 | Discord server member/online counts from an invite code |
| 19 | `https://t.me/s/{channel_username}` | ok | 200 | Recent posts from a public Telegram channel |
| 20 | `https://trends.google.com/trending/rss?geo={geo}` | ok | 200 | Official Google Trends trending searches (no key) |

