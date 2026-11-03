# Narrative-Edge Methodology

**Finding memecoin wallets that bought BEFORE the social traction spike — and proving they did.**

Package: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\`
Implementation: `leapspace/socialedge.py` (stdlib + `leapspace/http.py` only)
Tests: `leapspace/tests/test_socialedge.py` — **105/105 checks pass, including live calls**
Live verification date: **2026-11-03**

Every HTTP status in this document came from a real call made from this host on
2026-11-03. Every threshold marked `ANALYST_CHOICE` is an operator default, not a
paper-stated value, and is re-scorable in code.

---

## PART 1 — THE FREE SOCIAL SURFACE, LIVE-VERIFIED

### 1.1 What works

| Surface | Exact URL | Key? | HTTP | Response shape | Live result (2026-11-03) |
|---|---|---|---|---|---|
| **Telegram channel preview** | `https://t.me/s/{username}` | none | **200** | HTML | `Official_Bonk_Inu` → **11 004 members, 178 online** |
| **Telegram post timestamps** | `https://t.me/s/{username}` | none | **200** | HTML `<time datetime>` | `pepecoinchannel` → **20 posts, 20 timestamps**, window 336.16 h |
| **Discord invite + counts** | `https://discord.com/api/v9/invites/{code}?with_counts=true` | none | **200** | JSON | `qaQa6M6mN2` → **32 581 members, 1 772 presence**, guild "Bonk" |
| **Discord invite, no counts** | `https://discord.com/api/v9/invites/{code}` | none | **200** | JSON, **no count fields** | verified: the count keys are absent without `with_counts=true` |
| **Google Trends (pytrends)** | `https://trends.google.com/trends/api/...` | none | **200** | DataFrame w/ `date` index | `bonk`+`pepe`, "now 7-d" → **169 rows × 3 cols**, hourly, `2026-10-27 01:00` → `2026-11-03 01:00`; "today 3-m" → **93 rows**; `related_queries()` returns rising + top frames |
| **Nostr relay (nos.lol)** | `wss://nos.lol/` (raw WebSocket) | none | **101 Switching Protocols** | NIP-01 frames | kind-0 metadata + kind-1 notes retrieved; NIP-11 info at `https://nos.lol/` → **200** |
| **Nostr relay (relay.primal.net)** | `wss://relay.primal.net/` | none | **101** | NIP-01 frames | kind-0 metadata retrieved (3 events + EOSE) |
| **Nostr relay (relay.damus.io)** | `wss://relay.damus.io/` | none | **101** (intermittent **503**) | NIP-01 frames | NIP-11 HTTP info → **200**; WS handshake returned 503 on one attempt, 101 on another |
| **Bluesky public API** | `https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors?q=…` | none | **200** | JSON | `q=bonk` → 3 actors incl. `lekroox.bsky.social` |
| **Bluesky author feed** | `https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=…` | none | **200** | JSON | 14 940 bytes of real posts w/ timestamps |
| **Farcaster (Warpcast client)** | `https://api.warpcast.com/v2/user-by-username?username={name}` | none | **200** | JSON | `bonk` → fid 196356, **74 followers**, custody `0xa8fba3aa…`, **solanaWallets `7BURc7fW…`** labelled `primary`/`warpcast` |
| **Mastodon (any instance)** | `https://{instance}/api/v1/accounts/lookup?acct={name}` | none | **200** | JSON | `mastodon.social/api/v1/accounts/lookup?acct=Gargron` → 2 085 bytes |
| **Wayback CDX index** | `https://web.archive.org/cdx/search/cdx?url=t.me/s/{ch}*&output=json` | none | **200** | JSON rows | `t.me/s/bonk*` → **60 capture rows**; `pepecoinchannel` → 8; `bonkinu` → 8; `Official_Bonk_Inu` → **0** |
| **Wayback replay** | `https://web.archive.org/web/{ts}id_/{url}` | none | **200** (frequent **429**) | archived HTML | `t.me/s/pepecoinchannel@20230424004827` → **31 508 bytes**, title "PePe Coin BSC Chanel – Telegram", 5 post timestamps |
| **DexScreener token pairs** | `https://api.dexscreener.com/token-pairs/v1/{chain}/{token}` | none | **200** | JSON list | BONK → **30 pairs**, socials = `{type, url}` live shape |
| **DexScreener global lists** | `https://api.dexscreener.com/token-profiles/latest/v1` and `/token-boosts/top/v1` | none | **200** | JSON list | 24 490 / 26 695 bytes; carry the project's written description |
| **GeckoTerminal trending** | `https://api.geckoterminal.com/api/v2/networks/solana/trending_pools?page=1` | none | **200** | JSON | 31 212 bytes |
| **DefiLlama protocols** | `https://api.llama.fi/protocols` | none | **200** | JSON | 9.5 MB |

### 1.2 What does NOT work (and the exact failure)

| Surface | URL | HTTP | Verdict |
|---|---|---|---|
| **Telegram, nonexistent channel** | `https://t.me/s/this_channel_does_not_exist_9z8x7` | **200** | **THE TRAP.** Title is "Telegram Messenger", not "Telegram: View @name". No member count. Must be rejected by the *title*, not the status code. |
| **Telegram, Contact shape** | `https://t.me/s/bonkcoin`, `https://t.me/s/OriginalFrogInu` | **200** | Title "Telegram: Contact @name" — a real username that is not a public channel. No count. |
| **Telegram, personal profile** | `https://t.me/s/durov` | **200** | Title "Pavel Durov – Telegram", 20 posts, **no member count**. |
| **Telegram, private invite** | `https://t.me/s/+AbCdEfGhIjKl` | **200** | Title "Telegram: Join Group Chat", no count. |
| **Discord widget API** | `https://discord.com/api/guilds/{id}/widget.json` | **403 Forbidden** | Tested on 4 guild ids including BONK's real `1085633062735458424`. **Do not build on it.** The invite API needs no widget. |
| **Discord, bogus invite** | `https://discord.com/api/v9/invites/zzzznotreal9999?with_counts=true` | **404** | Correct behaviour. Report as unavailable, never as 0 members. |
| **Reddit listing JSON** | `https://www.reddit.com/r/{sub}/new.json?limit=5` | **403 Blocked** | Also 403: `/r/{sub}.json`, `/search.json`, `/comments.json`, `/top.json`, `/about.json`, `api.reddit.com`, `oauth.reddit.com` |
| **Reddit OAuth token (no creds)** | `https://www.reddit.com/api/v1/access_token` | **401** | Needs a registered free OAuth app. |
| **Reddit `old.reddit.com` .json** | `https://old.reddit.com/r/CryptoCurrency/new.json` | **200 but HTML** | Returns the HTML shell, not JSON. A 200 here is NOT a working API. |
| **Reddit RSS** | `https://www.reddit.com/r/CryptoCurrency/new/.rss?limit=5` | **200, then 429** | **The one Reddit path that works.** `application/atom+xml`, 5 `<entry>` elements with real titles and `<updated>`. But the 2nd and 3rd calls in a burst → **429 Too Many Requests**. Rate-limit hard: pace it. |
| **ApeWisdom API** | `https://api.apewisdom.io/v1/top-tokens/crypto` | **DNS NXDOMAIN** | **The API host no longer exists.** Confirmed two ways: `socket.getaddrinfo` → `gaierror [Errno 11001]`, and Cloudflare DoH `https://cloudflare-dns.com/dns-query?name=api.apewisdom.io` → **DNS Status 3 (NXDOMAIN)**. `www.apewisdom.io` resolves (104.21.25.90) and returns 200, but `/api/v1/...` serves the **HTML marketing page**, not JSON. SNI-pinning the resolved IP fails with `SSL: SSLV3_ALERT_HANDSHAKE_FAILURE`. |
| **Neynar** | `https://api.neynar.com/v2/fid/1` | **401** | Needs an API key. |
| **Neynar hub** | `https://hub-api.neynar.com/v1/info` | **402 Payment Required** | Keyless is not offered. |
| **Warpcast search** | `https://api.warpcast.com/v2/user-search?q=bonk` | **404** | Use `/v2/user-by-username?username=` instead — that works and is 200. |
| **Warpcast recent casts** | `https://api.warpcast.com/v2/recent-casts?limit=2` | **401** | No keyless cast feed. |
| **Google Trends raw explore** | `https://trends.google.com/trends/api/explore?…` | **429** | Direct call needs the cookie+token flow. **pytrends does this for you and works** (see below). |
| **Bluesky searchPosts** | `https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=bonk` | **403** | Search is blocked; `searchActors` and `getAuthorFeed` are not. |
| **Nostr NIP-05 name lookup** | `https://{name}.nostr.band/.well-known/nostr.json?name={name}` | **DNS NXDOMAIN** | `bob`/`satoshi`/`bonk`/`jack` all fail to resolve. |
| **Nostr relay list filter** | `["REQ", sub, [filter]]` | n/a | **Trap:** strfry relays reject a LIST filter — `"ERROR: bad req: provided filter is not an object"`. Pass a **dict**: `["REQ", sub, {"kinds":[0],"limit":3}]`. |
| **CoinGecko community_data** | `https://api.coingecko.com/api/v3/coins/bonk?community_data=true` | **200 then 429/timeout** | `community_data` was REMOVED on 28 Aug 2026. `links` still works. |
| **CoinCap** | `https://api.coincap.io/v2/assets?limit=2` | **DNS failure** | Not reachable from this host. |
| **Birdeye** | `https://api.birdeye.so/defi/token_overview?address=…` | **401/error** | Key required. |
| **Pump.fun frontend** | `https://frontend-api-v3.pump.fun/coins/mosttrending` | **403** | Blocked. |
| **Solscan public** | `https://public-api.solscan.io/token/meta?tokenAddress=…` | **401/error** | Key required. |
| **LunarCrush** | `https://lunarcrush.com/api4/public/coins/list/v1` | **401** | Key required. |
| **Santiment GraphQL** | `https://api.santiment.net/graphql` | **400** | Key required. |
| **CryptoPanic** | `https://cryptopanic.com/api/v1/posts/?auth_token=` | **403** | Token required. |
| **X / Twitter** | — | — | **No free tier, no free endpoint.** Pay-per-use only ($0.005/post read, $0.010/user read), ToS forbids scraping. A free screener CANNOT measure X follower counts or mention velocity. |
| **Nitter** | `https://nitter.poast.org/bonk` | **DNS failure** | Not reachable. |
| **YouTube RSS** | `https://www.youtube.com/feeds/videos.xml?channel_id=…` | **429** | YouTube HTML page itself is 200 (875 461 bytes) but the API needs a key. |
| **CoinGecko/GeckoTerminal pool by token** | `…/pools/{token_address}` | **error** | GeckoTerminal pools need a **POOL** address, not a token address. |

### 1.3 Two render shapes on Telegram — and why they matter

`https://t.me/s/{username}` returns one of **two** shapes, and which one you get is
a property of the channel, not of the request. Live-verified survey:

| Channel | Title | Members | Posts | Timestamps |
|---|---|---|---|---|
| `Official_Bonk_Inu` | `Telegram: View @Official_Bonk_Inu` | **11 004** (+178 online) | 0 | 0 |
| `pepecoinchannel` | `PePe Coin BSC Chanel 🐸🐸 – Telegram` | **none** | **20** | **20** |
| `durov` | `Pavel Durov – Telegram` | none | 20 | 20 |
| `bonkcoin` | `Telegram: Contact @bonkcoin` | none | 0 | 0 |
| `OriginalFrogInu` | `Telegram: Contact @OriginalFrogInu` | none | 0 | 0 |
| `this_channel_does_not_exist_9z8x7` | `Telegram Messenger` | none | 0 | 0 |

**Consequences for the methodology:**

1. **Size and activity are mutually exclusive per channel.** You get members OR
   post timestamps, not both, from one channel. A size-based comparator and an
   activity-based comparator cannot both be built from the same channel.
2. **`status: 200` never means "the channel exists".** Only the `View` title
   carries a member count. This is why `leapspace/social.py` requires the title
   match and why `socialedge._telegram_size` requires it too.
3. **The Wayback Machine carries the same two shapes.** An archived
   `t.me/s/pepecoinchannel@20230424004827` renders the POST shape with 5
   timestamps. An archived `t.me/s/bonkinu@20220824024323` renders 4 timestamps
   and **no** member count. So an archived page can supply a historical
   *activity* series even when the live page would give you only a size.

### 1.4 Does Telegram expose member growth over time? — **NO, plainly.**

**There is no keyless way to get a Telegram member-count time series.** The
public preview exposes the **current** count only. There is no endpoint, no
query parameter, and no historical view. Verified on 2026-11-03: the page for
`Official_Bonk_Inu` returned **11 004** members on every one of 7 calls across
the session (including 3 consecutive calls 3 s apart at the end, all
**11 004 / 178 online**). The prior session's recorded value was **11 009**
and the one before that **11 013** — a drift of a handful of members across
days, with **no history retrievable**. The `online` figure moved within the
session (174 → 179 → 181 → 184 → 178), which is exactly why it is the more
useful of the two for a liveness signal.

The `?before=<post_id>` parameter pages backwards through **posts**, not through
member counts.

**Three honest ways to obtain a time series anyway:**

| Route | What it gives | Cost | Limitation |
|---|---|---|---|
| **A. Sample it yourself over time** | A true member-count series | One HTTP call per channel per sample | Requires collecting it. This is what `socialedge.record_community_snapshot` exists for. |
| **B. Wayback archived previews** | Historical member counts *only for channels that were captured* | CDX index + a replay fetch per capture | Coverage is spotty (`Official_Bonk_Inu` → **0 captures**; `pepecoinchannel` → 8). The replay endpoint **429s** constantly — it is a batch job with a pacer, not a live path. And the archived page may be the POST shape with no member count at all. |
| **C. Use post-activity instead of size** | A real, keyless, *retrievable* time series: post timestamps | One HTTP call | Bounded to the ~20 most recent posts. It measures *activity*, not *size*. |

**Route C is the only one that yields a historical social series from a single
call today**, and it is why `socialedge.telegram_post_activity()` and
`socialedge.build_activity_series()` exist. Route A is the only route that
yields member *size* history. The methodology below uses both, and is explicit
about which comparator needs which.

**pytrends is the third historical series, and it is the best one.** `pip install
pytrends` (4.9.2) succeeded on this host and **works**: `build_payload(["bonk",
"pepe"], timeframe="now 7-d")` returned 169 hourly rows; `"today 3-m"` returned
93 daily rows; `related_queries()` returned rising and top frames. Google
Trends is the only source here that gives a *retrospective, hourly, multi-week*
attention series with no key. Note the interest index is **normalised 0–100
relative to the other terms in the same request**, so cross-token comparison
requires a single combined request, never two separate ones.

---

## PART 2 — THE NARRATIVE LIFECYCLE

The LeapSpace meme paper's framework is used where applicable:
**niche community vs broad trend** (the paper's performance clause) and the
**five-layer screen**. The lifecycle below is the bridge between them: the
five layers tell you *whether a token is structurally sound*, the lifecycle tells
you *where in its life it is*, and the lead-time test (Part 3) tells you *who
bought before the market got there*.

**The single most important structural point:** in every phase below, the
on-chain footprint is *mechanically earlier* than the social signal, because the
token must exist before anyone can talk about it. Social is a **lagging
confirming** signal in the early phases and a **lagging warning** in the late
ones. The only phase where social LEADS is **narrative escalation**, and that is
exactly why a social-led entry is usually a late entry. The tradable asymmetry
is not "social leads on-chain" — it is that **certain wallets buy in the window
where social is still ahead of the on-chain footprint.**

### Phase 0 — Pre-launch (deployer funded, no liquidity)

| | |
|---|---|
| **(a) On-chain evidence** | Deployer address derived on-chain (`leapspace/deployers.py`); deployer balance > 0; token contract deployed; **no liquidity pool**; no buy transaction possible; RugCheck `creator`, `dev` (Jupiter) match the derived deployer. |
| **(b) Social evidence** | Social links appear in the token's own metadata **before** the pool exists — DexScreener pair `info.socials`, the global profile/boost lists. A Telegram channel with a handful of members. No mention events anywhere. |
| **(c) Leading / lagging** | **ON-CHAIN IS LEADING.** The deployer funding and the contract deployment are the earliest observable facts. Social metadata is *declaration*, not evidence: it says the project CLAIMS a community. |
| **(d) The trap** | A social link in metadata proves only that the project *asserts* the link. It does not prove the community exists, is funded, or is not controlled by the deployer. Confidence tier **T0 (`declared_by_project`)**. A deployer who creates the Telegram channel, then buys, then shows you the channel, is showing you his own marketing. |

### Phase 1 — Launch (liquidity appears, social accounts created)

| | |
|---|---|
| **(a) On-chain evidence** | First pool created (`pairCreatedAt`, Jupiter `firstPool`); LP added (RugCheck `totalLPProviders`, `lpLockedPct`); first buys; `pair_created_at`; the launchpad funnel (`launchpad_origin` via `market_types`, `n_dexes`). |
| **(b) Social evidence** | Telegram/Discord links in metadata (already declared in Phase 0); channel now returns a `View` title and a member count. Possibly the first 1–10 posts. |
| **(c) Leading / lagging** | **ON-CHAIN IS LEADING, narrowly.** Liquidity existing is a harder fact than a channel existing. But social accounts are usually created *before* launch — so the social *accounts* are early and the social *counts* are late. |
| **(d) The trap** | **A community channel can be empty.** A channel created at launch with 3 members and 0 online is a rounding error against a 12,000-member channel. Size and liveness are different things, and neither is engagement. Also: the launchpad funnel trap — a screener that only sees tokens already on a DEX is scanning the surviving 2%, the opposite of the paper's instruction [5]. |

### Phase 2 — Community formation (membership grows, invites appear)

| | |
|---|---|
| **(a) On-chain evidence** | Holder count climbing; distinct holders per snapshot; first organic holders (not the deployer); RugCheck `totalHolders`; top-holder composition shifting (`leapspace/holders.py`). |
| **(b) Social evidence** | **Member count crosses a threshold** — this is the membership comparator. Telegram member count and Discord `approximate_member_count` rising across snapshots. Discord invites (the invite link) appear in metadata. Online/presence counts as the liveness signal. |
| **(c) Leading / lagging** | **TIGHTLY CONTESTED — and this is the phase that matters.** Holder growth and member growth usually run together; whichever you sample more finely appears to lead. A wallet buying inside this window has **no reliable on-chain or social evidence that the community exists yet** — it has to be anticipating. |
| **(d) The trap** | **Member count is gameable.** Members can be bought; the `online` count cannot. A project can show 10,000 members and 30 online. Also: **Discord presence is cached** — live-verified, it did not move at all across 4 samples 14 s apart, so presence is a slow indicator. And a Discord invite's `approximate_member_count` is approximate by Discord's own definition. |

### Phase 3 — Narrative escalation (mentions and follower growth accelerate, multiple platforms)

| | |
|---|---|
| **(a) On-chain evidence** | Volume accelerates; buy/sell ratio > 1; holder growth accelerates; **first major social mention event** — this is the mention comparator. Volume is now a LAGGING confirmation: by the time volume is visibly accelerating, the news is out. |
| **(b) Social evidence** | Post activity accelerates (Telegram post timestamps); member growth accelerates; **platform breadth increases** (broadcast platforms appear alongside the community channel); Google Trends interest spikes; Farcaster/Bluesky/Mastodon accounts appear. |
| **(c) Leading / lagging** | **SOCIAL IS LEADING, but only barely, and only for a few hours.** Attention moves before money. This is the ONLY phase where social leads. |
| **(d) The trap** | **A big social spike can be a bought campaign.** arXiv:1910.07783 documents *ephemeral* astroturfing — a keyword is promoted to look popular and then the activity is REMOVED. Any popularity metric not measured as a two-point time series is gameable by design. And engagement rate is **NON-MONOTONIC** (arXiv:2209.02911): returns are lower when engagement is too low OR too high, because high engagement signals bot activity. Score engagement as a BAND, never as a ramp. |

### Phase 4 — Peak / divergence (on-chain volume peaks, social still rising)

| | |
|---|---|
| **(a) On-chain evidence** | Volume peaks and **stops rising**; the buy/sell ratio inverts; holder growth flattens while the member count keeps climbing; top-10 concentration rises as early sellers exit to late buyers. |
| **(b) Social evidence** | Member count and post activity STILL RISING. Google Trends interest still rising or just off its peak. |
| **(c) Leading / lagging** | **ON-CHAIN IS LEADING — the divergence has opened.** Price/volume peaked; social has not. The community is the last thing to leave. |
| **(d) The trap** | **This is the trap the divergence flag exists for.** The naive reading — "social is up, therefore buy" — is most wrong exactly here. Volume can be bots (Jupiter's `organicScore` and `stats24h.buyOrganicVolume` exist precisely because raw volume is not trustworthy). `socialedge.social_vs_onchain_divergence()` flags `social_slope > 0 AND volume_slope < 0` and calls it what it is: **distribution starting while the community still grows.** |

### Phase 5 — Decay (social falls before price, or price falls first)

| | |
|---|---|
| **(a) On-chain evidence** | Price falls; volume falls; holder count falls (holders leave); RugCheck `risks` populates (mint/freeze authority still live, LP unlocked); `rugged: true`. |
| **(b) Social evidence** | Member count falls or plateaus; **online count collapses first** (people stop showing up before they leave); post activity drops. |
| **(c) Leading / lagging** | **THE ORDER DEPENDS ON WHICH YOU READ.** Social member count falls **LATE** — people stay subscribed long after they stop participating. The **online count** falls early. Price often falls first, with social following days later. |
| **(d) The trap** | **The naive reading inverts here too.** "Members are still up" during decay is a LAGGING indicator of a community that is already gone. And the reverse divergence — **social DOWN, volume UP** — is often the late distribution trap where money flows into a dying token. `social_vs_onchain_divergence()` reports both directions explicitly. |

### Phase 6 — Death

| | |
|---|---|
| **(a) On-chain evidence** | Liquidity near zero; the LP is pulled; the holder set is a handful of addresses; `rugged: true`; the pool disappears from DexScreener. |
| **(b) Social evidence** | The channel still renders 200 with a member count — **the channel outlives the token by months.** Member count is a stale number, not a live signal. |
| **(c) Leading / lagging** | **Social IS THE LAGGING INDICATOR OF DEATH, BY WEEKS.** The count barely moves while the token is dead. |
| **(d) The trap** | **A channel with 10,000 members and a dead token looks exactly like a healthy token to a size-only screener.** This is why member count must be paired with the ONLINE count and with on-chain liquidity. |

### Phase summary — which signal leads

| Phase | On-chain | Social | Edge lives in |
|---|---|---|---|
| 0 Pre-launch | **LEADING** | lagging (declaration only) | the deployer trace |
| 1 Launch | **LEADING** | lagging | the deployer + LP check |
| 2 Community formation | contested | contested | **buying before the member threshold crossing** |
| 3 Narrative escalation | lagging | **LEADING (briefly)** | knowing the window is closing |
| 4 Peak | **LEADING** | lagging | **the divergence flag** |
| 5 Decay | leading | lagging | online count + concentration |
| 6 Death | leading | **lagging by weeks** | liquidity, not members |

---

## PART 3 — THE SOCIAL-EDGE TEST

### 3.1 The definition

For a wallet's **first buy** of a token at `t_buy`, and a comparator event at
`t_event`:

```
lead_time_hours = (t_event - t_buy) / 3600
```

* **lead_time > +6 h → LEADING** (bought before the comparator fired)
* **lead_time < −6 h → LAGGING** (bought after)
* **|lead_time| ≤ 6 h → COINCIDENT** (no information)

The ±6 h window (`COINCIDENT_WINDOW_HOURS_DEFAULT`) is an `ANALYST_CHOICE`.
Without it, a wallet that bought 30 minutes after the event is reported as a
laggard, which overstates the evidence.

**The overall verdict is the MEDIAN of the resolved comparators, not the mean.**
One noisy comparator firing very early must not drag the verdict. Both the
median and the mean are reported.

**A wallet's entry is its EARLIEST buy of that token.** A wallet that bought
early and added later is an early buyer; a wallet that bought late and averaged
down is not.

### 3.2 The three comparators — data, source, and cost

| Comparator | Event = | Needs | Free source | Live-verified? |
|---|---|---|---|---|
| **(i) `membership_threshold`** | First snapshot where combined Telegram+Discord members ≥ threshold (default **500**, `ANALYST_CHOICE`) | A **community-size series**: `[{"ts", "telegram_members", "discord_members"}, …]` | `t.me/s/{u}` + Discord invite API, **sampled repeatedly over time** | YES — endpoint 200; the series must be collected |
| **(ii) `holder_inflection`** | First window whose holder growth rate exceeds **2.0×** the series median (`ANALYST_CHOICE`) | A **holder-count series**: `[{"ts", "holder_count"}, …]` | `leapspace/holders.py` (RugCheck `totalHolders`; EVM via Transfer logs) | YES — the package already keeps `state/holder_series/*.json` |
| **(iii) `first_mention_event`** | First observation ≥ **3.0×** the series median (`ANALYST_CHOICE`) | A **mention/attention series**: `[{"ts", "mentions"}, …]` | **Telegram post timestamps** (`t.me/s/{u}` → `<time datetime>` → hourly buckets) — free and keyless. **Google Trends** via pytrends — free, hourly, retrospective. Reddit RSS — free but 429-prone | YES — `pepecoinchannel` → 20 real timestamps → 337 hourly buckets |

### 3.3 The CONVERSE test — late buyers are NOT evidence of an edge

This is mandatory, not optional. A wallet that bought after the narrative was
established has demonstrated only that it can follow a crowd. Pooling such
wallets with genuine leaders inflates the apparent edge.

**Definition.** The narrative is *established* at the first snapshot where
combined members ≥ `NARRATIVE_ESTABLISHED_MEMBERS_DEFAULT` (**1 000**,
`ANALYST_CHOICE` — deliberately higher than the 500 used by comparator (i),
because "established" means the community was already large and
self-sustaining).

* A wallet whose **first** buy lands after that moment is a **LATE BUYER**.
* Late buyers are reported **separately** (`classify_late_buyers` → `late_buys`
  vs `early_buys`, with `late_buy_fraction`), never silently mixed into a
  leading cohort.

**Edge case, handled explicitly.** If the community was **already above** the
established threshold at the *first* observation, the narrative was established
**before the series starts** — a definite answer, not a gap. Every buy in the
window is then correctly a late buy, and the output says so via
`already_established_before_series: true`.

### 3.4 Honest degradation — the rules the code actually follows

1. A comparator that cannot be resolved yields `status: "unavailable"` (or
   `"not_reached"`, or `"already_above_threshold"`) **with a reason**, and
   `lead_time_hours: None`. It contributes **no number at all** — never a zero.
2. The verdict is computed over the comparators that **did** resolve, and
   `n_comparators_resolved`, `comparator_coverage` and
   `comparator_coverage_of_full_set` are all reported, so a verdict based on
   one comparator is never confused with one based on three.
3. If **no** comparator resolves, the verdict is `UNKNOWN` and
   `lead_time_hours` is `None`. Never a fabricated zero.
4. A membership threshold that was **already passed at the first observation**
   is reported as `already_above_threshold` with `event_ts: None`. Reporting
   the first snapshot as "the crossing" would silently invent a date for an
   event that predates the data — manufacturing exactly the lead time the test
   exists to measure.
5. A missing count is `None`, never `0`. A measured `0` stays `0`. An
   unmeasured platform is **unmeasured**, not zero.
6. The divergence flag reports `status: "unavailable"` with a reason when there
   are fewer than 4 paired observations or no time spread — a zero slope and
   an unknown slope are different claims.

### 3.5 Worked example (synthetic fixture, in the test suite)

A community growing 40 → 1 270 members over 48 h; holder count inflecting at
+18 h; a mention spike at +24 h. A wallet buying at **T0 − 16 h**:

| Comparator | Event | Lead time |
|---|---|---|
| membership threshold (500) | T0 + 24 h | **+40 h** |
| holder inflection | T0 + 18 h | **+34 h** |
| first mention event | T0 + 24 h | **+40 h** |

**Median = +40 h → LEADING.** Mean = +38 h (also reported). Coverage 3/3.
The same wallet buying at T0 + 44 h → **LAGGING**; at T0 + 22 h →
**COINCIDENT**.

---

## PART 4 — DELIVERABLES

### 4.1 `leapspace/socialedge.py`

**Dependency audit (executed):** imports are exactly
`{json, os, re, time, typing, __future__, datetime, .http}` — **stdlib plus
`leapspace/http.py` only**. No third-party package.

| Function | Purpose |
|---|---|
| `build_community_series(snapshots)` | Normalise raw snapshots → `[{"ts", "telegram_members", "discord_members", "telegram_online", "discord_online", "combined_members", "combined_is_lower_bound", "n_platforms_measured", "source"}]`. Accepts several key spellings. Drops untimestamped rows. Missing counts stay `None`; measured zeros stay `0`. |
| `community_series_diagnostics(series)` | Coverage: n snapshots, span, median/max gap, per-platform measured counts, and the max-gap warning ("a series with a large max gap cannot resolve a crossing to better than that gap"). |
| `load_community_series` / `save_community_series` / `record_community_snapshot` | Persist the per-token series to `leapspace/state/social_series/{chain}_{mint}.json` (atomic replace). This is the **collection** side that makes a threshold crossing computable at all. |
| `membership_threshold_event(series, threshold, platform)` | Comparator (i). `platform` ∈ `combined` / `telegram` / `discord` / `online`. Handles `ok`, `not_reached`, `already_above_threshold`, `unavailable`. |
| `holder_inflection_event(holder_series, multiple)` | Comparator (ii). Median-rate baseline, first window above `multiple × baseline`. |
| `first_mention_event(mention_series, multiple)` | Comparator (iii). Median-count baseline, first observation above `multiple × median`. |
| `compute_lead_time(buy_ts, comparators, window)` | The lead-time computation and the LEADING / COINCIDENT / LAGGING / UNKNOWN verdict, with per-comparator evidence. |
| `assess_wallet_edge(wallet_buys, community_series, token_address, symbol, holder_series, mention_series, …)` | End-to-end: filter buys to the token, take the earliest as the entry, build all three comparators, compute the verdict, return the evidence. |
| `narrative_established_ts(series, threshold)` | The "established" moment, including the `already_established_before_series` case. |
| `classify_late_buyers(wallet_buys, community_series, …)` | **The converse test.** Splits buys into `late_buys` / `early_buys` with hours-before/after. |
| `social_vs_onchain_divergence(points, social_key, volume_key)` | The divergence flag. `social_slope > 0 AND volume_slope < 0` → divergent. Also reports the **converse** (social down, volume up) and the reading. |
| `sample_community_size(social_links)` | Live sample of the current community size, in the shape the series writer wants. |
| `telegram_post_activity(url)` | Live post-timestamp extraction from the Telegram preview. Returns `status: "no_posts_in_preview"` for a member-shape channel rather than an empty series that looks like "no activity". |
| `build_activity_series(stamps, bucket_seconds)` | Bucket post timestamps into a per-bucket count series. **Emits empty buckets with a count of 0**, so the median is computed over the whole window — a median over active buckets only would make any modest activity look like a spike. |

**Internal readers `_telegram_size` / `_discord_size`** are implemented here
rather than imported from `leapspace/social.py`, to honour the
"stdlib + `leapspace/http.py`" constraint. The test suite contains a **live
drift guard** asserting the two implementations agree on status, HTTP status
and member count for the same URLs — including the nonexistent-channel trap.

### 4.2 `leapspace/tests/test_socialedge.py` and `demo_socialedge.py`

```
python leapspace/tests/test_socialedge.py          # offline, synthetic fixtures
python leapspace/tests/test_socialedge.py --live   # + live endpoint calls
python leapspace/tests/demo_socialedge.py          # end-to-end walkthrough
```

**105/105 checks pass** with `--live`. **61/61** pass offline.

The offline section uses **SYNTHETIC** fixtures and labels them as such in the
output. The live section asserts on real HTTP statuses.

**Live findings the test confirmed on this run:**
* Telegram `Official_Bonk_Inu` → 200, 11 004 members, 178 online
* Telegram trap `this_channel_does_not_exist_9z8x7` → **200**, `members: None`,
  status `not_a_channel_or_absent`
* Discord `qaQa6M6mN2` → 200, 32 581 members, 1 772 presence, guild "Bonk"
* Discord bogus invite → **not ok**, no member count
* `sample_community_size` → both platforms measured, **43 585 combined**
* `already_above_threshold` fires correctly for a 500-member threshold on a
  43 585-member community, and the comparator then yields **UNKNOWN**, not a
  fabricated lead
* Telegram `pepecoinchannel` → 200, **20 posts, 20 timestamps**, window 336.163 h
* Telegram `Official_Bonk_Inu` → `no_posts_in_preview` (the two-shapes finding)
* The divergence flag with 2 paired points → `status: "unavailable"`,
  `divergent: None` — not a fake slope
* Drift guard: `socialedge` and `leapspace.social` agree on every live reading

**`demo_socialedge.py` runs the whole pipeline end to end** and prints the
verdicts. Live run output:

```
[1] LIVE mention series from Telegram post timestamps
    http_status=200 status=ok posts=20 timestamps=20 window_hours=336.163
    activity series: 337 hourly buckets (LIVE, from the public preview)
[2] LIVE current community size (BONK)
    telegram_members=11004 telegram_online=178
    discord_members=32581 discord_online=1772
    combined=43585 gaps=[]
[4] Comparators
    membership_threshold: status=ok event_ts=... (T0+24h) value=830
    holder_inflection:   status=ok event_ts=... (T0+18h)
    first_mention_event: status=ok event_ts=... (T0+24h)
[5] Wallets, the lead-time test, and the converse test
    wallet                  buy   lead_h       class  late?
    early_reader             2h     22.0     LEADING      -
    just_before             22h      2.0  COINCIDENT      -
    at_the_event            24h      0.0  COINCIDENT      -
    boundary                28h     -4.0  COINCIDENT      -
    late_follower           34h    -10.0     LAGGING   LATE
[6] Social vs on-chain divergence
    status=ok divergent=True social_slope/h=0.008935 volume_slope/h=-6.296296
    reading: SOCIAL UP / VOLUME DOWN - distribution is starting while the
             community still grows. The community is the LAST to leave.
[7] Honest degradation: only ONE comparator available
    overall_class=LEADING lead=22.0h resolved=1/1 coverage_of_full_set=0.333
      holder_inflection      unavailable: comparator was not supplied
      first_mention_event    unavailable: comparator was not supplied
```

Note the live Telegram activity series produced **16 non-empty hourly buckets
with a max of 2 posts per bucket**, so the mention comparator honestly reported
`not_reached` — a quiet channel has no "major mention event". That is the
correct answer, not a failure.

### 4.3 The CLI command

The method is runnable from the package. `socialedge` is the **timing** edge and
is complementary to the existing `edge` command, which is the **statistical**
edge (fluke tests, Bayesian skill, deflated Sharpe) — a wallet can be
statistically consistent and still have bought after every narrative spike, or
vice versa.

```bash
# record a live community-size snapshot (the series must be COLLECTED)
python -m leapspace.cli socialedge --token <MINT> --chain solana --sample

# read a token's live Telegram post-activity series
python -m leapspace.cli socialedge --token <MINT> --chain solana --activity

# run the lead-time test and the converse test
python -m leapspace.cli socialedge --token <MINT> --chain solana \
    --buys buys.json --holders --mentions mentions.json
```

`buys.json` is a list of `{"ts", "symbol", "token_address"}`; `mentions.json` is
a list of `{"ts", "mentions"}`. `--json` emits the full machine-readable
payload.

**Live output of the three modes on BONK (2026-11-03):**

```
$ python -m leapspace.cli socialedge --token DezXAZ8z... --sample
COMMUNITY SNAPSHOT — solana / DezXAZ8z...
  telegram members : 11004   online: 166
  discord  members : 32581   online: 1789
  combined         : 43585   measured on 2 platform(s)
  series now has   : 1 snapshot(s), span 0.0h
  A threshold crossing needs TWO snapshots. Telegram exposes NO
  member-count history, so this series must be COLLECTED over
  time - it cannot be queried.

$ python -m leapspace.cli socialedge --token DezXAZ8z... --activity
POST ACTIVITY — solana / DezXAZ8z...
  telegram       : https://t.me/Official_Bonk_Inu
  http_status    : 200   status: no_posts_in_preview
  posts rendered : 0   timestamps: 0
  note           : This channel's preview renders the member block instead
                   of posts. It has no post timestamps to extract; use
                   community size instead.
  mention event  : status=unavailable  event_ts=None  mention series has 0
                   usable point(s); needs >= 4

$ python -m leapspace.cli socialedge --token DezXAZ8z... --buys buys.json --holders
SOCIAL-EDGE ASSESSMENT — solana / DezXAZ8z...
  first buy       : 2026-11-03T01:40:00+00:00 (1793670000)
  VERDICT         : UNKNOWN
  lead time (h)   : None  (mean None)
  comparators     : 0 of 3 resolved (coverage 0.0)
  PER COMPARATOR:
    membership_threshold   unavailable: series has 1 snapshot(s); a crossing needs >= 2
    holder_inflection      unavailable: not enough intervals to estimate a growth rate
    first_mention_event    unavailable: mention series has 0 usable point(s); needs >= 4
  CONVERSE TEST (late buyers are NOT evidence of an edge):
    unavailable: series has 1 snapshot(s); a crossing needs >= 2
  COMMUNITY SERIES: 1 snapshot(s), span 0.0h
    Fewer than two snapshots: no crossing is computable. Run `socialedge
    --sample` again later.
```

The third output is the honest answer for a brand-new token with one snapshot:
**UNKNOWN, with all three reasons given.** No number is invented.

### 4.4 The reverse-engineering procedure

**To find wallets that bought ahead of the crowd:**

1. **Pick the token.** Use the package's launchpad funnel: a token on a
   launchpad (pumpswap / raydium-launchlab, including RugCheck's
   `market_types`) that has *not* yet migrated. A token already on a major DEX
   is a survivor, and survivors have no early phase left to lead.
2. **Resolve its community links** (`leapspace/social.py`), and **sample the
   community size now** (`socialedge.sample_community_size`). Record it with
   `record_community_snapshot`. **This series does not exist yet** — it must be
   collected. Start it before you need it.
3. **Sample it again on a schedule** (hourly for a launch window). Two points
   make a crossing computable; one point makes nothing computable.
4. **Reconstruct the holders** (`leapspace/holders.py` → RugCheck
   `totalHolders`; EVM via Transfer logs) into a holder-count series, and
   record it with the same timestamps.
5. **Reconstruct the mention series** — Telegram post timestamps via
   `telegram_post_activity` → `build_activity_series`, and/or Google Trends
   via pytrends (one combined request for all tokens you are comparing).
6. **Get the wallets' buy timestamps** — `leapspace/memecoinscan.py`
   reconstructs a wallet's per-token buy/sell **with timestamps** from
   Blockscout (Ethereum), and `leapspace/chains.py` does the Solana equivalent
   from `preTokenBalances`/`postTokenBalances` deltas.
7. **Run the test**: `assess_wallet_edge(buys, community_series,
   token_address=…, holder_series=…, mention_series=…)`.
8. **Run the converse test**: `classify_late_buyers(buys, community_series,
   token_address=…)`. **Discard the late buyers from the leading cohort.**
9. **Check the divergence** before you act on a rising social number:
   `social_vs_onchain_divergence(points)` where each point pairs a community
   size with a volume reading at the same timestamp.
10. **Report the coverage.** A LEADING verdict from 1 of 3 comparators is a
    different claim from a LEADING verdict from 3 of 3.

**To reverse-engineer a specific wallet** (the "why did this wallet know?"
question):

* Resolve its on-chain funding source (the package's insider filter).
* Look for a **Farcaster custody address**: `api.warpcast.com/v2/user-by-username`
  returns `extras.custodyAddress`, `extras.solanaWallets` and `extras.ethWallets`
  with `walletLabels` (`primary` / `warpcast`) — live-verified. A purchase from
  that custody address on-chain is **T3 (cryptographic)** evidence of
  identity, per ICD 203's vocabulary. This is the ONLY free platform where
  social identity is anchored to an on-chain address **by protocol** rather
  than by self-report.
* Check whether the wallet bought before or after the membership crossing, and
  whether it bought the token that the community was already talking about, or
  a token the community had not yet adopted.

### 4.5 What was NOT tested / known limits

* **No end-to-end validation that LEADING wallets actually made money.** The
  lead-time test measures *ordering*, not *profit*. The package has no keyless
  historical price source for these contracts, so realised PnL is not computed
  — that limitation is unchanged and is recorded in `memecoinscan.py`.
* **The comparators' thresholds are untuned.** 500 / 1 000 members, 2.0× and
  3.0× multiples, and the ±6 h window are `ANALYST_CHOICE` placeholders. They
  are named constants at the top of `socialedge.py` and are meant to be
  re-scored against a labelled cohort.
* **No wallet has yet been measured with a real member-count series**, because
  that series has to be collected over time and this package has only just
  started collecting it. The comparator logic is verified against synthetic
  fixtures and against live endpoint behaviour; the *empirical* lead-time
  distribution is **not yet measurable** — and is reported as such rather than
  estimated.
* **The survivorship trap applies to the holder cohort**: a top-holder scan
  describes who KEPT, not who PROFITED.
* **ApeWisdom is gone** (NXDOMAIN), so the Reddit-mention comparator has no
  proxy. Reddit RSS is the remaining Reddit path and it rate-limits hard.
* **Google Trends interest is normalised** 0–100 relative to the other terms
  in the same request — one combined request only.
* **Legal, before shipping**: Discord's Developer Policy clause 20 forbids
  mining/scraping Discord services and its Terms forbid scraping outright;
  Telegram's ToS prohibits scraping and its Content Licensing terms forbid
  harvesting for AI; Reddit's Data API Terms require a separate agreement for
  commercial use; X forbids scraping. **Calling a documented public
  unauthenticated JSON endpoint at a low rate is different from crawling a
  site.** Prefer the former, and read the terms before shipping anything
  commercial.

---

## VERIFICATION SUMMARY (2026-11-03)

| Claim | Status |
|---|---|
| `python leapspace/tests/test_socialedge.py --live` | **105/105 checks pass** |
| `python leapspace/tests/demo_socialedge.py` | End-to-end walkthrough runs clean |
| `python -m leapspace.cli socialedge --sample/--activity/--assess` | All three modes run live and degrade honestly |
| `socialedge.py` dependency audit | **stdlib + `leapspace/http.py` only** (AST-verified) |
| Existing package tests | `check_meme_paper_coverage` (0 MISSING), `check_quant_cli`, `check_narrative_forward_selection` — **all still pass** |
| Telegram size + online, keyless | **HTTP 200**, 11 004 / 178 live |
| Telegram Contact trap | **HTTP 200, no member count** — title check enforced |
| Discord invite counts, keyless | **HTTP 200**, 32 581 / 1 772 live |
| Discord widget API | **HTTP 403** on 4 guild ids — not built on |
| Reddit `.json` | **HTTP 403** on 8 paths |
| Reddit `.rss` | **HTTP 200** then **429** — the one working Reddit path |
| ApeWisdom API | **DNS NXDOMAIN** (socket + Cloudflare DoH Status 3) |
| Google Trends / pytrends 4.9.2 | **Works** — 169 hourly rows, 93 daily rows |
| Nostr relays | **101 + real events** (nos.lol, primal; damus intermittent) |
| Nostr filter shape | **Dict required**; a list is rejected |
| Bluesky searchActors / authorFeed | **HTTP 200**; `searchPosts` **403** |
| Farcaster Warpcast user lookup | **HTTP 200**, follower count + custody address + Solana wallet |
| Wayback CDX / replay | **200** for CDX; replay **200** but frequently **429** |
| Telegram member-count history | **Does not exist.** No keyless endpoint |
| Keyless historical social series | Telegram post timestamps + Google Trends |

*Verified live on 2026-11-03 from this host. Every HTTP status above came from
an actual request. Nothing in this document is estimated or assumed.*
