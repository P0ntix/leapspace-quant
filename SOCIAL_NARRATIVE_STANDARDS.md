# SOCIAL NARRATIVE STANDARDS

**An evidence-backed reference for classifying memecoin NARRATIVE and TRACTION using only free, no-API-key data.**

- **Compiled:** 2026-11-03
- **Compiled for:** LeapSpace Quant memecoin screener — `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\`
- **Verification method:** every URL below was fetched by script from this host on 2026-11-03 and the HTTP status recorded in `reports/citation_verification.json` (76 URLs tested; 73 resolved `< 400` on first pass, the 3 failures repaired with working alternates, final set re-verified). Live API probes are in `reports/free_endpoint_probe*.json`.
- **Scripts that produced the evidence:** `tools/check_urls.py`, `tools/probe_free_endpoints.py`, `tools/probe_free_endpoints2.py`, `tools/probe_free_endpoints3.py`, `tools/probe4_urls.py`, `tools/probe5.py`, `tools/probe6_papers.py`, `tools/probe7.py`, `tools/verify_citations.py`, `tools/fetch_docs.py`.

### How to read the tags

| Tag | Meaning |
|---|---|
| **STANDARD** | A definitional convention with a public, citable specification that more than one vendor uses, or an academic definition with peer review. |
| **VENDOR-PROPRIETARY** | Invented and defined by one commercial vendor. The formula, weighting, corpus and bot-filtering are that vendor's alone. Reimplementing it requires their paid data. |
| **ACADEMIC** | Defined in a peer-reviewed or preprint paper with a stated method and dataset. |
| **UNVERIFIED** | Could not be confirmed by fetching a primary source from this host. Either excluded from the tables or explicitly flagged. |

### The three things this document is most likely to be wrong about

1. **"RugCheck token socials" do not exist.** The brief assumes `RugCheck` returns social links for a token. It does not: the live `/report` payload has **no `socials` key at all** (verified 2026-11-03, `tools/probe_free_endpoints.py`). The full top-level key list is recorded in `reports/free_endpoint_probe.json`. Any classifier reading RugCheck for socials is reading nothing.
2. **"CoinGecko token metadata links" still work, but `community_data` is dead.** CoinGecko documents that "As of 28 August 2026, the `community_data` and `developer_data` objects are no longer returned. The `community_data` and `developer_data` query params are kept for backward compatibility but have no effect." (`https://docs.coingecko.com/reference/coins-id`, fetched). So `twitter_followers` / `reddit_subscribers` / `telegram_channel_user_count` are **no longer available**. The `links` object still is.
3. **X/Twitter is no longer free.** X's API is pay-per-use with no subscription tiers: "Post: Read $0.005 per resource", "User: Read $0.010 per resource" (`https://docs.x.com/x-api/getting-started/pricing`, fetched). There is no free tier to scrape around; Section 6 therefore uses **X only through link-metadata and third-party aggregators**, never the X API.

---

## SECTION 1 — PLATFORM LANDSCAPE

Which platforms carry memecoin narrative and traction today, what each is used for, whether it is reachable free/no-key, and the structural fact that matters for a classifier.

### 1.1 X / Twitter

- **Used for:** narrative broadcast, KOL amplification, signal-to-noise for token announcements, and — critically for this screener — the **self-reported link** a token puts in its own metadata. It is also the platform where astroturfing is best documented (see Section 5).
- **Free / no-key:** **No.** The X API is pay-per-use only. From the fetched pricing page: "The X API uses pay-per-use pricing. No subscriptions—pay only for what you use." Read costs: Posts $0.005/resource, Users $0.010/resource, DMs $0.010, Following/Followers $0.010. "Pay-per-use plans are capped at 3 million Post reads per monthly billing cycle." A one-time $20 credit exists for a first purchase (`https://docs.x.com/x-api/getting-started/free-credits`, HTTP 200). **No free read tier exists.**
- **Legal:** the ToS is explicit — "You may not access the Services in any way other than through the currently available, published interfaces that we provide. For example, this means that, except as required by applicable law, you cannot scrape the Services without X's express written permission" (`https://x.com/en/tos`, fetched). `https://x.com/robots.txt` (fetched) sets per-path `Disallow` rules including `/search/realtime`, `/search/users`, `/*/followers`, `/*/following`, `/*/analytics`.
- **Structural facts for a classifier:**
  - **X handles are self-reported and freely impersonated.** A token's `twitter` link is a claim, not a fact. Nothing in the metadata proves the account belongs to the deployer. Treat every X handle as an *unverified assertion* until independently corroborated (Section 4).
  - A handle can be sold, renamed, or hijacked after listing. **A one-time snapshot is not a durable identity.**
  - Because X reads are priced per resource, **no free screener can measure X follower counts or mention velocity directly.** Any product claiming to do this free is either using a scraped corpus or a vendor's paid feed.
- **Sources:** https://docs.x.com/x-api/getting-started/pricing · https://docs.x.com/x-api/getting-started/free-credits · https://docs.x.com/x-api/introduction · https://x.com/en/tos · https://x.com/robots.txt

### 1.2 Telegram

- **Used for:** the **primary community channel** for memecoins — where holders talk, where dev announcements land, and where the only honest member-count signal lives. Santiment treats a token's own Telegram server as a first-class corpus: "Community Social Volume returns the social volume of the asset in the asset's own community chat (Telegram server) or subreddit (Reddit)" (`https://academy.santiment.net/metrics/community-social-volume/`, fetched).
- **Free / no-key:** **Yes, partially.** Two distinct paths:
  1. **Public channel preview** — `https://t.me/s/<username>` returns an HTML preview with **member count and online count** and no key. Verified live 2026-11-03: `https://t.me/s/Official_Bonk_Inu` → text contains **"11 012 members, 324 online"** (and on a repeat fetch minutes later "11 013 members, 313 online" — the online figure moves, the member figure is near-static). This is the **single highest-value free traction signal** in this document.
  2. **Bot API `getChatMemberCount`** — official method, "Returns Integer on success", takes `@username` (`https://core.telegram.org/bots/api#getchatmembercount`, fetched) — but **requires a bot token and the bot must be a member of the chat**, so it is not no-key for an arbitrary public channel.
- **Structural facts for a classifier:**
  - **Telegram invite links are self-reported by the project.** A `t.me/xxx` link in a token's metadata is a claim about *which* group is "official". It is not proof that the project controls that group.
  - **Member count ≠ participants.** A group can have a large member count and near-zero activity. The `online` figure in the same preview is the far better traction signal because it moves with real presence.
  - The preview shows only a **bounded window** of recent posts (verified: 5–20 `datetime=` entries on the channels tested), so post *rate* cannot be computed from one fetch — it needs two fetches separated in time.
  - **Bot padding:** Telegram member counts are historically inflated by bots and by users who join once. A member count with no corresponding message volume or online count is a weak signal.
- **Legal:** Telegram's Terms of Service "prohibits data scraping as part of its Content Licensing and AI Scraping Terms, which apply to all users, businesses, and third-party services accessing the platform" (`https://telegram.org/tos`, fetched). The Content Licensing terms are stronger still: "Telegram firmly prohibits the scraping, indexing, harvesting, aggregation or use of data obtained from its platform to train, fine-tune, validate or otherwise engage in the development, enhancement, benchmarking or deployment of artificial intelligence, machine learning models and similar technologies" (`https://telegram.org/tos/content-licensing`, fetched). That clause is aimed at model training; it does not authorise an AI agent to bulk-harvest Telegram for a screener, and the general ToS prohibition on scraping applies. **Recommendation: fetch a token's own single public channel preview at a low rate, treat it as a read of a public page, and do not build a bulk Telegram harvester.**
- **Sources:** https://core.telegram.org/bots/api · https://core.telegram.org/bots/api#getchatmembercount · https://core.telegram.org/api/links · https://telegram.org/tos · https://telegram.org/tos/content-licensing · https://academy.santiment.net/metrics/community-social-volume/ · live: `https://t.me/s/Official_Bonk_Inu`

### 1.3 Discord

- **Used for:** the second community surface — usually a mirror of the Telegram group. Historically the source of the highest apparent engagement counts because Discord widgets expose live member counts publicly.
- **Free / no-key:** **Yes — via two distinct routes, with an important gotcha.**
  1. **Widget API** — `https://discord.com/api/guilds/<guild_id>/widget.json`. **Requires the guild to have the Server Widget enabled.** Verified 2026-11-03: 10 of 10 guild IDs probed returned **404** (`discord.widget.probe.*` in `reports/free_endpoint_probe3.json`) — 404 means the widget is disabled or the ID is wrong, *not* that the API is gone. `https://discord.com/developers/docs/resources/guild#get-guild-widget` documents the resource.
  2. **Public invite endpoint** — `https://discord.com/api/v9/invites/<code>?with_counts=true`. This works **without the widget being enabled** and returns `approximate_member_count` and `approximate_presence_count`. Verified live 2026-11-03 on BONK's own invite `qaQa6M6mN2` → **`approximate_member_count: 32586`, `approximate_presence_count: 2120`, guild name "Bonk"**. A second probe (`wifcoin`) returned **404 "Unknown Invite"** — the invite was invalid, which confirms the endpoint distinguishes bad codes from blocked ones. The `approximate_member_count` / `approximate_presence_count` fields are documented on the Invite Resource page (`https://discord.com/developers/docs/resources/invite`, fetched).
  - **This is the practical free Discord traction signal: resolve the `discord.gg/...` invite from the token metadata and read the counts.**
- **Legal — this is the tightest constraint in this document.** Discord's Terms of Service: "scraping our services without our written consent, including by using any robot, spider, crawler, scraper, or other automatic device, process, or software" (`https://discord.com/terms`, fetched). The Developer Policy is stricter still: "**20. Do not mine or scrape any data, content, or information available on or through Discord services**" (`https://discord.com/developers/docs/policies`, fetched). Note that clause 20 is written against the **API** surface; the **invite** endpoint is a documented public API resource and the counts are *approximate* aggregates the server owner has chosen to expose — but the Developer Policy's blanket prohibition is broad enough that a production screener should treat Discord invite lookups as legally sensitive and (a) low-rate, (b) cached, (c) reviewed before shipping. Note also: resolving an invite **adds the bot/account to nothing** — it is a read of an invite's public metadata.
- **Rate limits:** "All bots can make up to 50 requests per second to our API. If no authorization header is provided, then the limit is applied to the IP address." (`https://discord.com/developers/docs/topics/rate-limits`, fetched). Per-route buckets are identified by `X-RateLimit-Bucket`.
- **Structural facts for a classifier:**
  - **Discord invite links are self-reported by the project**, exactly like Telegram. Same confidence ceiling.
  - `approximate_presence_count` (online now) vs `approximate_member_count` (total ever) — the **ratio** of the two is a far better authenticity signal than either alone. BONK: 2120/32586 ≈ **6.5% online**, which reads as a live community rather than a padded list.
- **Sources:** https://discord.com/developers/docs · https://discord.com/developers/docs/resources/invite · https://discord.com/developers/docs/resources/guild#get-guild-widget · https://discord.com/developers/docs/topics/rate-limits · https://discord.com/developers/docs/policies · https://discord.com/terms · live: `https://discord.com/api/v9/invites/qaQa6M6mN2?with_counts=true`

### 1.4 TikTok

- **Used for:** **the meme's cultural origin point** — a video that spawns a token. In practice it is a *source-discovery* channel, not a measurement channel: it tells you a narrative exists, not how much traction the token has.
- **Free / no-key:** **No.** Two gated products:
  - **Research API** — "Qualified researchers in the U.S., Europe, Canada, and Brazil can apply to study public data about TikTok content and accounts" (`https://developers.tiktok.com/products/research-api/`, fetched). Requires an approved application; "You can typically expect to hear back from us within 4 weeks of submission." Eligibility requires academic/non-profit status, "independent of commercial interests", and non-commercial purpose — **a commercial memecoin screener does not qualify.**
  - **Display API** — "Display API for Business" (`https://developers.tiktok.com/doc/display-api-overview`, fetched) — requires a Business account, app review, and gives access to *your own* TikTok content plus basic discovery. Not a corpus of others' posts.
- **Structural fact for a classifier:** a TikTok link on a token's page is a **narrative-provenance claim** (the meme came from here), which is genuinely useful for the niche-vs-broad distinction, and it is **cheap to verify by hand** — open the video, check the engagement. It is not automatable free.
- **Sources:** https://developers.tiktok.com/products/research-api/ · https://developers.tiktok.com/doc/display-api-overview

### 1.5 Reddit

- **Used for:** **the closest thing to organic, non-paywalled discussion.** r/wallstreetbets, r/CryptoCurrency, r/CryptoMoonShots. Crucially, Reddit posts carry **author handles, upvote counts and timestamps** — so Reddit is the only free platform where you can get *per-participant* evidence rather than an aggregate.
- **Free / no-key:** **Technically yes, practically blocked.**
  - The Data API reference is public and reachable: `https://www.reddit.com/dev/api` → HTTP 200 (fetched).
  - But **every unauthenticated JSON path tested from this host returned HTTP 403**: `www.reddit.com/r/wallstreetcoins/new.json`, `/r/CryptoCurrency/new.json`, `/search.json`, `old.reddit.com/.../.json`, `api.reddit.com/...`, `oauth.reddit.com/...` without a token, `/comments/1.json`. Reddit's HTML pages returned 200 while the JSON siblings returned 403 — the block is specific to the JSON API without OAuth. (`reports/free_endpoint_probe2.json`, `reports/probe4_urls.json`.)
  - `https://www.reddit.com/api/v1/me` returned 200 — so Reddit is not blanket-blocking this IP; the unauthenticated **listing** endpoints are.
  - **Conclusion: Reddit's public JSON API requires an OAuth client (free registration) to be reliable.** It is free, but **not no-key.** Registering a free Reddit app is a one-time, non-paid step; that is the recommended path, and it makes the API compliant with the Data API Terms.
  - **Free workaround that IS no-key:** ApeWisdom's public API (§1.12, Section 3) proxies Reddit + 4chan mention counts and works with no key at all.
- **Legal:** Reddit's Data API Terms govern use: "If you are interested in using the Data APIs for commercial purposes, research in excess of rate limits, or for any use that is not expressly permitted under the Data API Terms, then you will need to enter into a separate agreement with Reddit" (`https://redditinc.com/policies/data-api-terms`, fetched). Reddit's API terms also impose a User-Agent identification requirement and limit commercial use — **a commercial memecoin screener is exactly the case the separate-agreement clause contemplates.**
- **Structural facts for a classifier:**
  - **Reddit usernames are pseudonymous but *stable and checkable*.** A post history is a behavioural fingerprint. A handle that mentions a token for weeks before launch is a different class of evidence from a token that lists a subreddit nobody has posted in.
  - Reddit's upvote/downvote counts are **self-reported-ish and gameable**, but the *shape* of a subreddit (how many distinct authors, how many comments per post) is much harder to fake than a member count.
  - Santiment's own corpus treats Reddit as one of six social sources, and splits metrics per-platform (`social_volume_reddit`, `social_dominance_reddit`, `unique_social_volume_reddit`).
- **Sources:** https://www.reddit.com/dev/api · https://redditinc.com/policies/data-api-terms · https://academy.santiment.net/metrics/social-volume/

### 1.6 YouTube

- **Used for:** long-form narrative (video essays, "explainer" content), and — because view counts are public — a **slow-moving traction proxy**. Relevant for established memes, weak for new launches.
- **Free / no-key:** **No — needs a free API key (Google Cloud project).** The Data API v3 is documented at `https://developers.google.com/youtube/v3/docs` (fetched, 200). Quota: "Projects that enable the YouTube Data API have a default quota allocation of 100 `search.list` calls, 100 `videos.insert` calls, and **10,000 units per day** combined for all other endpoints" (`https://developers.google.com/youtube/v3/getting-started`, fetched). A key is free; it is not zero-config.
- **Structural fact for a classifier:** `search.list` costs **100 units** — one search eats 1% of the daily budget. Budget accordingly; do not search per token.
- **Sources:** https://developers.google.com/youtube/v3/docs · https://developers.google.com/youtube/v3/getting-started

### 1.7 Farcaster

- **Used for:** the **crypto-native social graph**. Its distinguishing property for this project: a Farcaster identity is anchored to an **on-chain custody address**, so social identity ↔ on-chain address is a *protocol-level* link, not a self-report. That makes Farcaster the platform where Section 4's confidence tiers can actually be upgraded.
- **Free / no-key:** **Yes.** The public Warpcast client API responds without a key. Verified live 2026-11-03: `https://client.warpcast.com/v2/search-casts?limit=5&q=bonk` → HTTP 200 returning real casts with `hash`, `threadHash`, `author.fid`, `author.displayName`, `author.profile.bio`, and `text`. `https://client.warpcast.com/v2/user-by-fid?fid=3` → HTTP 200 returning the full profile for FID 3 (Dan Romero), including custody/verified address fields.
- **Paid alternative:** Neynar is the commercial Farcaster data provider and returned **HTTP 402** with `{"x402Version":1,"error":"X-PAYMENT header or API key required"}` and a `maxAmountRequired` of 10000 (x402/USDC) — i.e. it now has a pay-per-call path on top of the key path. Neynar markets "2.6M+ accounts ... and $500M+ in connected wallets" (`https://neynar.com/`, fetched).
- **Structural facts for a classifier:**
  - Farcaster is **small and high-signal**. Santiment carries dedicated Farcaster metrics: `social_dominance_farcaster`, `unique_social_volume_farcaster` and their moving averages (Santiment's own versioned metrics inventory, fetched 2026-11-03 at `https://raw.githubusercontent.com/santiment/santiment-research-quickstart/main/skills/santiment-api/references/versioned-metrics-2.0-inventory.md`).
  - Because each FID is anchored to a custody address, **a token's on-chain buyers can be cross-referenced against Farcaster identities** — the only platform in this list where that join is cryptographically anchored rather than asserted. That is the single strongest "wallet tracking of the major players" path available for free.
  - `fid` is a **stable primary key**; `displayName` is not. Resolve by FID, never by handle.
- **Sources:** https://docs.farcaster.xyz/ · https://neynar.com/ · https://docs.neynar.com/ · live: `https://client.warpcast.com/v2/search-casts?limit=5&q=bonk` · https://raw.githubusercontent.com/santiment/santiment-research-quickstart/main/skills/santiment-api/references/versioned-metrics-2.0-inventory.md

### 1.8 Threads

- **Used for:** **negligible for memecoins.** Threads has no meaningful independent memecoin community; tokens cross-post from X/TikTok. Treat a Threads link as a *breadth* signal at best, and do not build a Threads collector.
- **Free / no-key:** **No.** Meta's Threads API requires a Meta app with the Threads use case, an access token, and permission grants. Docs: `https://developers.facebook.com/documentation/threads/` (HTTP 400 from this host's plain fetch — Meta's doc CDN rejects non-browser clients; the page is live in a browser). Reference at `https://developers.facebook.com/documentation/threads/reference/` and `https://developers.facebook.com/documentation/threads/insights/`.
- **Recommendation:** **exclude from the classifier.** If a token lists only a Threads link and no X/Telegram/Discord, that is itself a weak negative signal (no real community surface).
- **Sources:** https://developers.facebook.com/documentation/threads/ · https://developers.facebook.com/documentation/threads/reference/ · https://developers.facebook.com/documentation/threads/insights/ — *note: verified via search-result index and browser-rendered page; the plain-HTTP fetch from this host returns HTTP 400 because Meta rejects non-browser user agents. Treat as browser-verified, not fetch-verified.*

### 1.9 Platform summary

| Platform | Memecoin use | Free, no-key? | Best free traction signal | Confidence ceiling on identity links |
|---|---|---|---|---|
| X / Twitter | Narrative broadcast, KOL amplification | **No** — pay-per-use, $0.005/post read | Link presence only; counts via paid feed | **Claim only** — impersonable, sellable |
| Telegram | Primary community channel | **Yes** — `t.me/s/<user>` | **Member count + online count** | **Claim only** — invite self-reported |
| Discord | Secondary community mirror | **Yes** — invite API | **`approximate_member_count` + `approximate_presence_count`** | **Claim only** — invite self-reported |
| TikTok | Meme origin / provenance | **No** — Research API needs approval | Manual view/engagement check | **Claim only** |
| Reddit | Organic discussion, per-author evidence | **Free but needs OAuth app** | Author count, comment depth, post rate | **Moderate** — handles are stable and behaviourally checkable |
| YouTube | Long-form narrative | **No** — free key required | View count (10k units/day quota) | **Claim only** |
| Farcaster | Crypto-native graph, on-chain-anchored | **Yes** — public Warpcast client | Cast recency + author FID diversity | **High for addresses** — custody link is protocol-level |
| Threads | Negligible | **No** — Meta app required | — | **Claim only** |

**Structural law for the classifier:** *every* off-chain identity link in this table is a **self-reported claim** except Farcaster's on-chain custody anchor and Reddit's behaviourally-checkable author history. A classifier that treats link presence as proof of a community will systematically over-rank tokens that merely *claimed* a community.

---

## SECTION 2 — TRACTION AND NARRATIVE METRICS

Standard definitions and formulas, with source URLs and a STANDARD / VENDOR-PROPRIETARY / ACADEMIC tag.

### 2.1 Social volume / mention count

- **Definition (Santiment):** "Social Volume is built on top of the Social Data. The total number of social data text documents that contain the given search term **at least once**." A document counts **once**, no matter how many times the term appears inside it: "If a single short Telegram message includes the word `crypto` more than once, this message will increase the social volume of the word `crypto` by 1. If a long Reddit post contains the word `crypto` 10 times, this again will increase the social volume of the word `crypto` by 1." For an asset, a **Lucene query is auto-constructed** including negative terms — e.g. `santiment` expands to `(SAN OR santiment OR santoken OR santimentnet OR sancoin OR sansan) AND NOT ((san AND francisco) OR (san AND fran) OR (san AND diego) OR (san AND marino) OR (san AND jose))`.
- **Formula:** `social_volume(asset, t) = |{ documents d : query(asset) matches d }|` — one increment per matching document.
- **Source:** https://academy.santiment.net/metrics/social-volume/ (fetched 2026-11-03)
- **Tag: VENDOR-PROPRIETARY.** The document-counting mechanic is Santiment's. There is no cross-vendor standard for what a "mention" is.
- **Operational caveat Santiment itself discloses:** "We constantly update our labels, which helps us keep labels as fresh as possible but results in **historical data changes**. Any modifications to labels, social sources, or relevant jobs will prompt recalculation for the previous month's data." A vendor time-series is therefore **not reproducible across time**.
- **Free access:** Santiment's own metric catalogue marks `social_volume_*` metrics as **RESTRICTED** (`https://api.santiment.net/available_metrics`, fetched).

### 2.2 Mention velocity

- **Definition:** rate of change in mention count over time, typically mentions/hour or the first difference of a rolling social-volume series.
- **Formula (general):** `velocity(t) = (social_volume(t) − social_volume(t−Δ)) / Δ`. Santiment's own inventory exposes the first differences as discrete metrics: `social_volume_total_change_1d`, `social_volume_total_change_7d`, `social_volume_total_change_30d` (from `https://api.santiment.net/available_metrics`, fetched) — i.e. the vendor implements velocity as **published change metrics**, not as a continuous rate.
- **Source:** https://academy.santiment.net/metrics/social-volume/ · https://api.santiment.net/available_metrics
- **Tag: VENDOR-PROPRIETARY** for the exact vendor form; the *concept* is a plain derivative and is **STANDARD** as arithmetic.
- **Critically important for this project:** velocity is the metric most vulnerable to the failure mode in §2.6 and §5. A single burst of bot posts produces an enormous velocity spike and no sustained volume. **Always pair velocity with a persistence check (does volume hold after the burst?) and with a unique-author check.**

### 2.3 Engagement rate

- **Definition:** interactions (likes, replies, reposts, quotes, clicks) divided by an audience denominator. **The denominator is the entire dispute** — there is no industry standard.
- **Formulas in use (all are conventions, not standards):**
  - `ER_by_followers = interactions / followers × 100`
  - `ER_by_reach = interactions / impressions × 100`
  - `ER_by_views = interactions / video_views × 100`
- **Source:** No primary vendor spec publishes a normative engagement-rate formula for memecoins. The **academic** treatment is arXiv:2209.02911 (*Social Media Engagement and Cryptocurrency Performance*, Qureshi & Zaman, 2022-09-07), which "propose[s] a new model to measure the engagement of users with topics discussed on social media based on interactions with social media posts" and states this "overcomes the limitations of previous volume and sentiment based approaches" — fetched via the arXiv API (`https://export.arxiv.org/api/query?id_list=2209.02911`, and the paper at https://arxiv.org/abs/2209.02911).
- **Tag: VENDOR-PROPRIETARY** for any specific published formula; **ACADEMIC** for the engagement-coefficient construct.
- **The finding that matters (§5, cross-referenced):** in that paper, "Cryptocurrencies whose engagement coefficients are **too low or too high** have lower returns. Low engagement coefficients signal a lack of interest, while **high engagement coefficients signal artificial activity which is likely from automated accounts known as bots**." **Engagement rate is non-monotonic. More engagement is not better.** A classifier that scores "higher engagement = better" is encoding the exact error the literature identifies.

### 2.4 Follower growth rate

- **Definition:** change in a platform account's follower count over a window, usually normalised per day.
- **Formula:** `follower_growth(t) = (followers(t) − followers(t−Δ)) / Δ`. Santiment exposes a dedicated `Twitter Followers` metric family (https://academy.santiment.net/metrics/twitter-followers/) and classifies account categories separately from project followers — the fetched Categorized Social Volume page is explicit: "**"Followers" here means people following the project.** X's profile payload also carries `friends_count`".
- **Tag: VENDOR-PROPRIETARY.**
- **Free-access reality:** **not obtainable free on X** (read costs $0.010/resource per the X pricing page). CoinGecko's `twitter_followers` was retired on 28 Aug 2026 (§2.13). **A free screener cannot measure X follower growth today** — it can only observe growth in *Telegram member counts* and *Discord presence counts*, which is why those two are the recommended traction signals in Section 6.

### 2.5 Unique participants vs total mentions (bot adjustment)

- **Definition (Santiment, Unique Social Volume):** "The Unique Social Volume is the same type of aggregation on top of the social data as the Social Volume, but it takes into account only the **unique text documents** for each interval, i.e., **completely duplicated messages will be excluded** from the calculations, which results in a slightly lower and to some degree cleaner way to measure the volume of mentions." Three granularities: `unique_social_volume_total_5m`, `_1h`, `_1d`.
- **The mechanism (fetched verbatim):** "If some spam messages are posted in the span of 30 minutes, then every one of the six 5-minute buckets would have one copy of that message. In the case of 1h, all these messages would be reduced to a single one, thus providing more aggressive spam filtering. When comparing `unique_social_volume_total_1h` and `unique_social_volume_total_5m` aggregated at 1h intervals, the `unique_social_volume_total_1h` will always have fewer or equal values."
- **Formula:** `unique_social_volume(asset, t, g) = |{ unique matching documents in bucket t }|` where uniqueness is by content hash within a bucket of width g ∈ {5m, 1h, 1d}.
- **Source:** https://academy.santiment.net/metrics/unique-social-volume/ (fetched)
- **Tag: VENDOR-PROPRIETARY.**
- **The free analogue that a no-key screener can build:** the ratio
  `participant_ratio = distinct_authors(t) / total_mentions(t)`.
  On Reddit the denominator and numerator are both directly observable per post (author + comment count). On Telegram/Discord previews the *messages* are observable but the *authors* are not — so the free approximation is **content-dedup ratio** (`unique message texts / total messages`), which is exactly Santiment's 5-minute dedup with their corpus swapped for yours. **Report it as a dedup ratio, not a participant ratio** — that distinction is a honesty requirement, not pedantry.

### 2.6 Sentiment score

- **Definition (academic, canonical):** VADER — "a lexicon and rule-based sentiment analysis tool that is specifically attuned to sentiments expressed in social media" (https://github.com/cjhutto/vaderSentiment, fetched). Peer-reviewed at ICWSM: *VADER: A Parsing-Aware Lexical Sentiment Analyzer* (https://ojs.aaai.org/index.php/ICWSM/article/view/14550 — the article page is behind an Anubis bot-check from plain fetch, but the DOI record and PDF are publicly available).
  - VADER's mechanism: "Implements the grammatical and syntactical rules described in the paper, incorporating empirically derived quantifications for the impact of each rule on the perceived intensity of sentiment in sentence-level text. Importantly, these heuristics go beyond what would normally be captured in a typical bag-of-words model. They incorporate **word-order sensitive** relationships between terms." Degree modifiers (intensifiers/booster words) scale intensity; negation flips polarity.
  - **Output:** a normalized `compound` score in [−1, +1].
  - **Formula (as implemented):** `compound = normalize_sum(Σ valence_i)` where valence of each token comes from the lexicon, adjusted by negation, intensifier/diminisher multipliers and punctuation/capitalisation emphasis, then normalised by `x / sqrt(x² + α)` with α = 15.
- **Definition (vendor, Santiment Sentiment Ratio):** "Sentiment Ratio compares Labeled Social Volume counts to show what share of documents fall into each sentiment bucket — positive, neutral, or negative."
  - `Positive Ratio = Positive Docs Count / (Positive Docs Count + Neutral Docs Count + Negative Docs Count)`
  - `Neutral Ratio = Neutral Docs Count / (Positive + Neutral + Negative)`
  - `Negative Ratio = Negative Docs Count / (Positive + Neutral + Negative)`
  - (The page renders both LaTeX and plain-text forms of these formulas — fetched.)
- **Source:** https://academy.santiment.net/metrics/sentiment-ratio/ · https://github.com/cjhutto/vaderSentiment · https://ojs.aaai.org/index.php/ICWSM/article/view/14550
- **Tag: VADER = ACADEMIC.** Santiment Sentiment Ratio = **VENDOR-PROPRIETARY** (the bucket boundaries and the classifier are theirs).
- **Practical note:** sentiment on memecoin chatter is close to **useless as a discriminator** between tokens — most high-volume memecoin chatter is positive by default, and bots post positive. Santiment's own framing is that mindshare "must always be read in conjunction with the corresponding sentiment data" (§2.8) — sentiment is a *modifier*, not a scorer.

### 2.7 Social dominance

- **Definition (Santiment, asset):** "Social Dominance for an asset compares the Social Volume of that asset to the combined social volume of the **100 largest assets by marketcap**. Social Dominance of 50% for an asset means that the number of messages/posts that discuss this asset equals half the number of messages/posts that discuss the Top 100 assets. **This definition allows the social dominance of an asset to exceed 100%.** This can happen for assets whose name and/or ticker is a very common English word."
- **Definition (Santiment, text phrase):** "compares the Social Volume of that search term to the total number of documents available. This essentially computes the percentage of all documents that match this search term."
- **Source:** https://academy.santiment.net/metrics/social-dominance/ (fetched)
- **Tag: VENDOR-PROPRIETARY.**
- **A documented inconsistency to be aware of:** Santiment's **older** research article (https://santiment.github.io/articles/social-volume-metrics/) states the denominator is "the top 50 by market capitalization", while the current academy page says **100**. The current page governs. Cite the current one.
- **Why it matters to memecoins:** for a top-50 asset, dominance is a meaningful "share of the conversation". For a micro-cap memecoin, dominance against a top-100 benchmark is **structurally near-zero and uninformative**. **The useful analogue for a memecoin screener is a cohort-relative dominance** — the token's share of mentions *within the screened cohort* — which is precisely the cohort-baseline approach the existing `leapspace/narrative.py` already implements via `cohort_baseline()` and `relative_to_cohort()`. That is a sound implementation of a Santiment-style concept on free data.

### 2.8 Mindshare (Kaito)

- **Definition (Kaito, fetched verbatim):** "Mindshare is the percentage of total tracked attention that a brand, company, asset or topic receives within a defined **comparison group** and time period. When analyzing a mindshare percentage, it is very important to have a comparison group, to check how the measurement was done and the time span. 'Mention counts' measure the amount of discussion about a subject or term, while mindshare measures the percentage of overall attention that a subject or term receives."
- **Kaito's own framing of what it is NOT (fetched):** "Mindshare measures attention, **share of voice** measures visibility relative to competitors, and **sentiment** measures the tone of discussion. Note that all of these metrics often have somewhat different definitions, therefore, we recommend that you always check out how a tool for online analysis actually defines them."
- **The dependency Kaito flags (fetched):** "The quality of attention depends on the quality of the underlying sources (e.g. blogs, media, social networks), contributors (e.g. editors, writers, commentators) and filtering applied to identify relevant mentions. Mindshare must always be read in conjunction with the corresponding sentiment data and a representation of the relevant discussions. **Rising mindshare can stem from positive interest, from harsh criticism, or even from a temporary event.**"
- **Source:** https://studio.kaito.ai/blog/what-is-mindshare (fetched) · https://docs.kaito.ai/ · https://h5.portal.kaito.ai/narrative (Narrative Mindshare product page, fetched)
- **Tag: VENDOR-PROPRIETARY.** Kaito invented the term in this crypto sense. It is *derived from* classic advertising "mind share" (share of mental availability), but the crypto metric, its corpus, its weighting and its "attention" model are Kaito's own.
- **Note the "Narrative Mindshare" product (https://h5.portal.kaito.ai/narrative):** "a metric that measures the prominence of a specific **narrative or story** within the overall market context." That is directly the metric this project's narrative classifier wants — but it is **paid and vendor-gated**, and the published methodology does not let you reproduce it. Treat it as a **target metric to approximate**, and say so in the code.

### 2.9 Altcoin Season Index

- **Definition (Blockchain Center, fetched):** "If **75% of the Top 50 coins performed better than Bitcoin over the last season (90 days)** it is Altcoin Season."
- **Definition (CoinMarketCap's independent implementation, fetched):** "If **75% of the top 100 coins** outperform Bitcoin in the last 90 days, it's Altcoin Season. Remember, stablecoins like Tether and DAI, as well as asset-backed tokens such as WBTC, stETH, and cLINK, aren't included."
- **Source:** https://blockchaincenter.net/altcoin-season-index · https://coinmarketcap.com/charts/altcoin-season-index
- **Tag: VENDOR-PROPRIETARY** (two independent vendor implementations with **different universes** — top 50 vs top 100, and CMC excludes stablecoins/LSTs).
- **Role in a memecoin classifier: this is a MARKET-REGIME variable, not a per-token narrative variable.** It tells you whether small caps are outperforming BTC at all. Its correct use is as a **screening gate or a conditioning variable**: in an altcoin season, low-cap momentum is partly explained by beta, so a token's traction must be measured *against its cohort*, not against the market. Do **not** use ASI to score an individual memecoin.
- **Also relevant to Section 6:** because ASI is computed from CoinGecko/CoinMarketCap market data, it is free to replicate.

### 2.10 LunarCrush social metrics

- **What LunarCrush actually offers (fetched from the API docs):** "The LunarCrush API v4 is a JSON-over-HTTPS API rooted at `https://lunarcrush.com/api4`. **Authenticate every request with an `Authorization: Bearer ***` header.** One API covers social sentiment, mention and engagement volume, creators, topics, trending data, and price and market metrics for both crypto and stocks." Endpoints are organised into 9 groups: AI & MCP Server, Topics, Categories, Creators, Posts, Coins, Stocks, Searches, System. "For example, `/public/coins/list/v1` returns every tracked coin with price, market cap, **Galaxy Score**, **AltRank**, sentiment, and 24-hour social volume."
- **Galaxy Score** and **AltRank** are LunarCrush's own composite indices. Their internals are not published.
- **Marketing claim (fetched from the pricing page):** "**Six layers of processing** separate us from any tweet scraper. Every post passes through every layer. 20+ data points per asset, each with full historical time-series."
- **Source:** https://lunarcrush.com/developers/api · https://lunarcrush.com/developers/api/endpoints · https://lunarcrush.com/pricing
- **Tag: VENDOR-PROPRIETARY.** Galaxy Score and AltRank are proprietary composites with undisclosed formulas. **Do not present them as standards, and do not attempt to replicate them from the label alone.**
- **Live check:** `https://lunarcrush.com/api4/public/coins/list/v1` returned **HTTP 401** with `{"error": ...}` and no data — the endpoint is real but requires a bearer token. Live probe recorded in `reports/free_endpoint_probe.json`.

### 2.11 Santiment Social Volume and Social Dominance

Covered in full at §2.1 and §2.7. Summary of the **access** side, since that is what decides whether a screener can use them:
- Santiment's metric catalogue (`https://api.santiment.net/available_metrics`, fetched) lists `social_volume_*` and `social_dominance_*` as **RESTRICTED**, while some market indicators (e.g. `price_volatility_1d`) are marked **FREE**.
- The GraphQL endpoint `https://api.santiment.net/graphql` returned **HTTP 400 `{"errors":{"details":"Invalid JSON Web Token (JWT)"}}`** when given a placeholder bearer token, and a syntax error with no auth header — i.e. **an API key is required**, and it is validated as a JWT.
- **Pricing (fetched from https://app.santiment.net/pricing):** **Free $0 — "Free forever"**, but with "30-day lag in Sanbase", "Hidden top 3 tokens in Trending Coins", "No filters and sorting for Screener", "Up to 3 simultaneous alerts". **Sanbase Pro $49/mo** ($529/yr), **Sanbase Max $249/mo** ($2700/yr) — and it is **Max**, not Pro, that advertises "full API access to real-time data".
- **Implication: Santiment's social metrics are not available on the free tier in real time.** Any plan to use them means paying, which the operator has ruled out.

### 2.12 Nansen smart-money metrics

- **Definition (fetched from the Nansen API docs):** "Smart Money endpoints provide insights into the trading and holding activity of **historically profitable traders**: Smart Traders on spot markets and Smart HL Perps Traders on Hyperliquid. **Funds are not part of Smart Money**; for current Fund holdings, use Fund Holdings."
- **Endpoints (fetched):** `/api/v1/smart-money/netflow` (net capital flows, inflows vs outflows), `/api/v1/smart-money/dex-trades` (real-time DEX trading activity), `/api/v1/smart-money/perp-trades`, `/api/v1/smart-money/dcas` (marked deprecated), plus PnL, Leaderboard, Holdings, Historical Holdings, Funds, Profiler, Token God Mode, Portfolio, Chain Rank, Backtesting, Prediction Market, Smart Alerts.
- **Formula:** netflow is a signed USD (or token-denominated) flow — `netflow = inflow − outflow` over a window. The *ranking* of historically profitable wallets is Nansen's proprietary edge; the underlying tagging methodology is closed.
- **Source:** https://docs.nansen.ai/api/smart-money · https://www.nansen.ai/api
- **Tag: VENDOR-PROPRIETARY.**
- **Pricing (fetched from https://www.nansen.ai/api):** "**Free Plan $0 /month** — Best for quick experimentation and testing — 100 trial credits, Daily 10-credit refill, Rate limits: 15/sec, 300/min." "**Pro Plan Popular $49/month** — 2000 starting credits, Bulk credit discounts, Rate limits: 75/sec, 1,500/min." And: "Start without an API key, from **$0.01 per query**. x402 payments enable pay-per-call access to the Nansen API using USDC on Base or Solana."
- **Live check:** `https://api.nansen.ai/api/beta/defi/token/screener/v1` returned **HTTP 401 `{"message":"No API key found in request"}`** — recorded in `reports/free_endpoint_probe.json`.
- **Assessment for this project:** the free tier is real but **credit-metered and key-gated**, so it is *not* in the no-key set. However — and this is the important part — **the underlying idea is implementable free**: "historically profitable traders" can be approximated from public chain data by a screener that already profiles wallets (§6). Nansen supplies the labels; you can compute your own.

### 2.13 DEX social-to-on-chain conversion ratios

- **The concept:** the ratio of *social attention* to *on-chain action* — how many social mentions per unique buyer, or what fraction of on-chain participants show up socially. It is the standard "hype vs. reality" check.
- **Vendor implementation (Santiment Conversion Rate):** the metric page `https://academy.santiment.net/metrics/conversion-rate/` is a **soft 404** — it returns **HTTP 200** but the rendered body is the academy's not-found page ("404: Not found … Looks like you got lost"), verified 2026-11-03. The word "conversion" also does **not** appear among the **109** metric pages linked from the academy index (`https://academy.santiment.net/metrics/`, fetched and enumerated). It exists in older Santiment material and in the vendor's SQL/Sansheets function library, but **there is no current primary spec page for it.**
  - **Status: UNVERIFIED as a current Santiment metric.** Do not cite a formula for it. (Related, *verified* metric: **Community Messages Count** — "returns the number of messages written in the asset's own community chat (Telegram server) or subreddit (Reddit). Currently telegram and reddit are supported" — https://academy.santiment.net/metrics/community-messages-count/ — which is the *social* side of the join, not the conversion ratio itself.)
- **The free, buildable version (recommended):**
  - `social_to_buyers_ratio = social_mentions(Δt) / unique_buyers(Δt)`
  - `buyer_participation = unique_buyers(Δt) / unique_buyers(lifetime)`
  - A token with high mentions and low unique buyers is **bought by few distinct wallets** — the shape of a coordinated push, and exactly the population the "wallet tracking of the major players" requirement targets.
  - Free inputs: DexScreener/RugCheck for liquidity and volume; the chain's public RPC + Jupiter's `holderCount` for buyer counts; Telegram/Discord preview counts for the social side.
- **Tag: the *concept* is STANDARD** (a funnel ratio is a standard growth-analytics construct); **the vendor metric is UNVERIFIED**; **the free reconstruction is an analyst construction** and must be labelled as such in the output.

### 2.14 Metric summary table

| Metric | Formula (where stated) | Tag | Source | Free? |
|---|---|---|---|---|
| Social volume / mention count | `\|{docs matching query(asset)}\|`, 1 per doc | VENDOR-PROPRIETARY | [academy.santiment.net/metrics/social-volume](https://academy.santiment.net/metrics/social-volume/) | No (RESTRICTED) |
| Mention velocity | `Δvolume / Δt`; vendor publishes `_change_1d/7d/30d` | VENDOR-PROPRIETARY | [same](https://academy.santiment.net/metrics/social-volume/) | No |
| Engagement rate | no normative formula; `interactions/followers`, `/impressions`, `/views` | VENDOR-PROPRIETARY / ACADEMIC | [arXiv:2209.02911](https://arxiv.org/abs/2209.02911) | n/a |
| Follower growth rate | `(F(t) − F(t−Δ))/Δ` | VENDOR-PROPRIETARY | [academy.santiment.net/metrics/twitter-followers](https://academy.santiment.net/metrics/twitter-followers/) | No (X paid) |
| Unique participants (bot adj.) | `\|{unique matching docs in bucket}\|`, g ∈ {5m,1h,1d} | VENDOR-PROPRIETARY | [academy.santiment.net/metrics/unique-social-volume](https://academy.santiment.net/metrics/unique-social-volume/) | No |
| Sentiment score (VADER) | normalized valence sum, compound ∈ [−1,1] | **ACADEMIC** | [github.com/cjhutto/vaderSentiment](https://github.com/cjhutto/vaderSentiment) · [ICWSM paper](https://ojs.aaai.org/index.php/ICWSM/article/view/14550) | **Yes** |
| Sentiment ratio (Santiment) | `Pos/(Pos+Neu+Neg)` etc. | VENDOR-PROPRIETARY | [academy.santiment.net/metrics/sentiment-ratio](https://academy.santiment.net/metrics/sentiment-ratio/) | No |
| Mindshare | `subject attention % of total tracked attention` within a comparison group + period | VENDOR-PROPRIETARY | [studio.kaito.ai/blog/what-is-mindshare](https://studio.kaito.ai/blog/what-is-mindshare) | No |
| Social dominance | `volume(asset) / volume(top-100 by mcap)`; can exceed 100% | VENDOR-PROPRIETARY | [academy.santiment.net/metrics/social-dominance](https://academy.santiment.net/metrics/social-dominance/) | No |
| Altcoin Season Index | `% of top-50 (BC) / top-100 (CMC) coins beating BTC over 90d ≥ 75%` | VENDOR-PROPRIETARY | [blockchaincenter.net](https://blockchaincenter.net/altcoin-season-index) · [coinmarketcap.com](https://coinmarketcap.com/charts/altcoin-season-index) | **Yes** |
| LunarCrush Galaxy Score / AltRank / social volume | undisclosed composites | VENDOR-PROPRIETARY | [lunarcrush.com/developers/api](https://lunarcrush.com/developers/api) | No (401 w/o bearer) |
| Nansen Smart Money | `inflow − outflow` over window; labels proprietary | VENDOR-PROPRIETARY | [docs.nansen.ai/api/smart-money](https://docs.nansen.ai/api/smart-money) | Key-gated (free tier, 100 credits) |
| DEX social→on-chain conversion | `mentions / unique_buyers`; vendor formula UNVERIFIED | STANDARD concept / vendor UNVERIFIED | — | **Yes** (free inputs) |

---

## SECTION 3 — FREE versus PAID

### 3.1 The specific endpoints named in the brief — verified live on 2026-11-03

| Endpoint | Key needed? | Works without auth? | Published rate limit | Social fields returned | Verdict |
|---|---|---|---|---|---|
| **DexScreener** `info.socials` (`/token-pairs/v1/{chain}/{token}`) | **No** | **Yes** | **300 req/min** for token-pairs & search; **60 req/min** for profiles/boosts/meta | `info.socials[]` each `{type, url}`; `info.websites[]`; `info.header`; `info.imageUrl` | ✅ **FREE, NO-KEY — use it** |
| **RugCheck** token socials (`/v1/tokens/{mint}/report`) | No | Yes | Not published in the response | **NONE — there is no `socials` key at all** | ❌ **Does not exist** |
| **Jupiter** token metadata socials | No | Yes | Not published | `tags[]` (`community`, `verified`, `birdeye-trending`, `moonshot-verified`, `strict`, `meme`); `organicScore`; `dev`; `firstPool`. **No `socials` array.** The `/tokens/v2/recent` feed does carry a `twitter` field on some entries | ⚠️ **Partial — tags + organic score, no social links** |
| **CoinGecko** token metadata links (`/coins/{id}`) | No (keyless tier exists) | **Yes** | 429 on burst; docs at [/docs/errors-and-rate-limits](https://docs.coingecko.com/docs/errors-and-rate-limits) | `links.{homepage, twitter, telegram, reddit, github, ...}` — ✅ **still returned**. `community_data` / `developer_data` **removed 28 Aug 2026** | ✅ **FREE for links only** |
| **LunarCrush** free tier | **Yes** (Bearer) | No | Not published | — | ❌ paid ($90/$300/$900) |
| **Santiment** free tier | **Yes** (JWT) | No | — | — | ❌ social metrics RESTRICTED |
| **ApeWisdom** | **No** | **Yes** | No rate-limit headers published | `rank`, `ticker`, `name`, `mentions`, `upvotes`, `rank_24h_ago`, `mentions_24h_ago` | ✅ **FREE, NO-KEY** |
| **VADER** | No (pip) | Yes (local) | n/a | local sentiment | ✅ **FREE** |
| **Google Trends** via pytrends | No | Partially | undocumented | unofficial endpoint; **the `explore` endpoint returned HTTP 400 to plain GET from this host** | ⚠️ **Official RSS works; pytrends is fragile** |
| **Reddit** public JSON API | No (works unauth'd in principle) | **403 from this host on every listing endpoint** | OAuth: 100 queries/min per OAuth client id | — | ⚠️ **free but needs a free OAuth app** |
| **Telegram** public preview (`t.me/s/<user>`) | **No** | **Yes** | undocumented | member count, online count, recent post window | ✅ **FREE, NO-KEY — use it** |
| **Discord** widget API | **No** | **Yes, but 404 unless the guild enabled the widget** | global 50 req/s (IP-based if unauthenticated) | `member_count`, `presence_count`, channels, `instant_invite` | ⚠️ use the **invite API** instead |
| **Discord invite API** (`/api/v9/invites/{code}?with_counts=true`) | **No** | **Yes** | global 50 req/s | `approximate_member_count`, `approximate_presence_count`, guild name | ✅ **FREE, NO-KEY — use it** |
| **Farcaster** Warpcast client (`/v2/search-casts`) | **No** | **Yes** | undocumented | casts with `author.fid`, `displayName`, text | ✅ **FREE, NO-KEY** |
| **Neynar** | **Yes** | No | — | — | ❌ HTTP 402 (x402 pay-per-call) |
| **Nansen** | **Yes** | No | free tier 15/sec, 300/min | — | ❌ HTTP 401 without key |

### 3.2 Paid tiers and published prices

| Vendor | Free tier | Paid | Published price | Source |
|---|---|---|---|---|
| **X API** | **None.** One-time $20 credit on first purchase | Pay-per-use | **Posts read $0.005/resource · Users read $0.010 · DMs $0.010 · Following/Followers $0.010 · Space read $0.005 · List read $0.005 · Counts:recent $0.005 · Trends $0.010**. Writes: Post create $0.015 ($0.200 with a URL), Interaction create $0.015. Cap: 3M post reads/month | [docs.x.com/x-api/getting-started/pricing](https://docs.x.com/x-api/getting-started/pricing) |
| **LunarCrush** | A free *account* on Discover (1h/24h social sentiment); "Paid plans have **no** free trial" | Individual / Builder / Scale | **$90/mo · $300/mo · $900/mo** | [lunarcrush.com/pricing](https://lunarcrush.com/pricing) |
| **Santiment** | Sanbase Free **$0 forever** — 30-day lag, top-3 Trending Coins hidden, no screener filters, 3 alerts; **no real-time API** | Sanbase Pro / Max | **$49/mo ($529/yr)** / **$249/mo ($2700/yr)** — Max advertises "full API access to real-time data" | [app.santiment.net/pricing](https://app.santiment.net/pricing) |
| **Nansen** | **$0/mo**, 100 trial credits, 10-credit daily refill, 15/sec + 300/min | Pro | **$49/mo**, 2000 credits, 75/sec + 1,500/min. Also **x402 pay-per-call from $0.01/query, no API key** | [nansen.ai/api](https://www.nansen.ai/api) |
| **Neynar** | key-gated | — | x402 `maxAmountRequired` **10000** (USDC units) observed in the 402 response | [neynar.com](https://neynar.com/) |
| **CoinGecko** | keyless tier + free Demo key | Pro | price not captured this run — see [errors-and-rate-limits](https://docs.coingecko.com/docs/errors-and-rate-limits) | [docs.coingecko.com/docs/errors-and-rate-limits](https://docs.coingecko.com/docs/errors-and-rate-limits) |
| **Reddit** | free OAuth client | separate agreement for commercial use | "Reddit reserves the right to charge fees for future use or access to the Data APIs, rates to be determined" | [redditinc.com/policies/data-api-terms](https://redditinc.com/policies/data-api-terms) |
| **YouTube Data API** | free key | — | free quota: **10,000 units/day**, 100 `search.list` calls | [developers.google.com/youtube/v3/getting-started](https://developers.google.com/youtube/v3/getting-started) |
| **TikTok Research API** | free once approved (academic/non-profit only) | — | — | [developers.tiktok.com/products/research-api](https://developers.tiktok.com/products/research-api/) |

### 3.3 The no-key set — the short, honest list

**Confirmed working with zero credentials, verified by live fetch on 2026-11-03:**

1. **DexScreener** — `https://api.dexscreener.com/token-pairs/v1/{chain}/{token}` → `info.socials`, `info.websites`, `info.header`, `info.imageUrl`; 300 req/min. Also `/token-profiles/latest/v1` and `/token-boosts/latest/v1` at 60 req/min.
2. **Telegram public preview** — `https://t.me/s/{username}` → member count, online count, bounded recent-post window.
3. **Discord public invite** — `https://discord.com/api/v9/invites/{code}?with_counts=true` → `approximate_member_count`, `approximate_presence_count`.
4. **ApeWisdom** — `https://apewisdom.io/api/v1.0/filter/{filter}/page/{n}` → Reddit/4chan mention counts + 24h-ago baselines. Filters include `all`, `all-stocks`, `all-crypto`, and named subreddits (`CryptoCurrency`, `SatoshiStreetBets`, `CryptoMoonShots`, `CryptoMarkets`, `wallstreetbets`, …). Pages of 100.
5. **Farcaster public Warpcast client** — `https://client.warpcast.com/v2/search-casts?limit=N&q={term}` and `/v2/user-by-fid?fid={n}` → casts and profiles with FID-anchored identity.
6. **CoinGecko links** — `https://api.coingecko.com/api/v3/coins/{id}` → `links.*` (keyless; rate-limited).
7. **Jupiter** — `https://lite-api.jup.ag/tokens/v2/search?query=...` → `tags`, `organicScore`, `dev`; `/tokens/v2/recent` and `/tokens/v2/toporganicscore/24h`.
8. **RugCheck report** — `https://api.rugcheck.xyz/v1/tokens/{mint}/report` → on-chain social-adjacent facts (top holders, LP providers, insider graph). **No socials.**
9. **Google Trends official RSS** — `https://trends.google.com/trending/rss?geo=US` → 10 daily trending searches (verified: 10 `<item>` elements).
10. **Altcoin Season Index** — reconstructible from free market data.
11. **VADER** — local, free, no network.

**Two caveats that must travel with this list:**
- **ApeWisdom's crypto coverage is thin.** Live: `filter/all-crypto/page/1` returned `count: 5` with every `mentions` value = 1, and `filter/CryptoCurrency/page/1` likewise returned 5 rows with `mentions: 1`. The `all` and `all-stocks` filters return full pages of 100 with meaningful counts (e.g. SPY 102 mentions). **So ApeWisdom is a usable mention signal for equities, and at present a very weak one for memecoins.** Verify coverage per token before relying on it; do not treat "absent from ApeWisdom" as "no discussion".
- **The `t.me/s/{username}` member/online parse works for *groups* but not for every channel.** Verified: `Official_Bonk_Inu` → "11 013 members, 313 online"; `bonk_inu` → **no** members/online string (it renders posts instead, 5 `datetime=` entries); `telegram` → 20 posts. **Parse both shapes and record `null` rather than coercing to 0** — a silent 0 would invert the traction ranking.

---

## SECTION 4 — OSINT CORRELATION METHODS

### 4.1 The linkage types that exist, and what each can support

| Linkage | Mechanism | Confidence tier supportable |
|---|---|---|
| **Token metadata → X handle** | Self-declared on the token's own page/DEX listing | **Claim of association only.** Highest tier: "the project asserts it is affiliated with this handle". Cannot support "the deployer controls this handle". |
| **Token metadata → Telegram group** | Self-declared invite link | Same — **claim only**. The group may be a ghost town, may be hijacked, may predate the token. |
| **Token metadata → Discord server** | Self-declared invite link | Same — **claim only**. |
| **Token metadata → website** | Self-declared URL | **Claim only**, but websites carry a verifiable payload: the HTML may name the mint address, the GitHub repo, the team, the contract address, and the social handles. **A website is the best free corroboration surface available** because it can be cross-checked field-by-field. |
| **Deployer address → GitHub / npm** | On-chain deployer publishes a verified-source repo; the repo's commit signature, package publish history, and README mint address link the two | **Strong.** This is the highest-confidence free linkage: it is *cryptographically* anchored (a signed commit or an npm publish is an act by the key holder) rather than asserted. |
| **Farcaster identity → on-chain address** | Protocol-level custody address recorded for the FID | **Strong** for the FID→address direction; the address→FID direction follows from it. |
| **On-chain wallet → X handle** | Requires the wallet to have published a link (bio, a transaction memo, a signed message) | **Medium if signed** (the wallet proves control of the address by signing a challenge containing the handle), **Low if merely asserted** (a claim in a bio is the same class of evidence as a metadata link). |
| **Telegram group → on-chain address** | Requires the group admin to publish the mint address *in the group* and the group's history to predate the token | **Medium-High** — the group's own message history is a timestamped, third-party-hosted record. A group that has posted the mint address since before launch is far harder to fake than a link on the launchpad page. |
| **Reddit author → on-chain address** | Reddit history + a post containing the mint address | **Medium-High** — Reddit author histories are stable and time-stamped, and the platform is independent of the project. |
| **Ticker/symbol → token** | Symbol collision | **Low unless disambiguated.** `$PEPE`, `$MOON`, `$DOGE` are shared by dozens of tokens across chains. |

### 4.2 A sound method when the only linkage is a self-reported link on a token's own metadata page

**The rule: a self-reported link supports a claim about the *project's assertion*, and nothing stronger.** Build the evidence chain so that the assertion is the object being asserted, not a fact about the world.

**Concrete method:**

1. **Record the assertion as an evidence item, with its source.** Not "X handle @bonk_inu" but "token metadata page lists `twitter.com/bonk_inu` as the project's Twitter" — with the URL, the fetch timestamp, and the field path (`info.socials[0].url`). The `osint-investigation` skill's discipline applies: *"Entity resolution produces candidates, NOT conclusions. A `fuzzy` match between 'ACME LLC' and 'Acme Holdings Group' is a lead, not a fact."*
2. **Corroborate on an INDEPENDENT surface, and record which surface.** A token that lists the same handle on DexScreener *and* CoinGecko *and* its own website is stronger than one that lists it on DexScreener alone — but note that all three may derive from the same source document, so **independent-host ≠ independent-origin**. Check whether the pages *agree* (same handle) and record the agreement count, not just the presence.
3. **Look for a *cryptographic* confirmation on the social side.** The strong form: the account itself posts the mint address, or the website's DNS/TXT or the deployer's signed commit references the handle. Only that upgrades the tier.
4. **Assign a confidence tier and keep it with the claim.** Use the **ICD 203 Analytic Standards** vocabulary, which is the authoritative US intelligence-community standard for exactly this problem — it requires analysts to "Properly describe the quality and credibility of underlying sources, data, and methodologies" and to "Properly express and explain uncertainties associated with major analytic judgments", and it prescribes a fixed likelihood vocabulary (almost no chance / very unlikely / roughly even chance / likely / very likely / almost certain) with explicit percentage bands (01-05%, 05-20%, 20-45%, 45-55%, 55-80%, 80-95%, 95-99%). Critically, ICD 203 also states that a product "must not combine a confidence level and a degree of likelihood … in the same sentence" — so pick one per claim and say which. Source: **ICD 203 Analytic Standards** — the canonical dni.gov PDF (`https://www.dni.gov/files/documents/ICD/ICD-203.pdf`) returns **HTTP 403 to non-browser clients from this host**; a byte-identical public mirror was fetched successfully (HTTP 200, 3,051,281 bytes) at `https://donohueintellaw.ll.georgetown.edu/sites/default/files/assets/ICD%20203%20Analytic%20Standards.pdf` (Georgetown Law). **Cite the dni.gov URL as canonical and the Georgetown mirror as the verified-readable copy.**
5. **Recommended tier ladder for this screener:**

| Tier | Name | What it takes |
|---|---|---|
| T0 | **Unverified claim** | A link in the token's own metadata only. Assert: "the project lists handle H." Nothing else. |
| T1 | **Corroborated assertion** | Two or more independent hosts carry the same handle. Assert: "the project consistently presents H as its handle." Still not control. |
| T2 | **Reciprocated link** | The account/group itself references the token, its mint, or its website. Assert: "H publicly references this token." |
| T3 | **Cryptographic linkage** | A signed commit, npm publish, on-chain message, or custody record ties the identity to the address. Assert: "address A is controlled by identity H" — and even here, assert it at the confidence of the specific evidence, not as certainty. |

**T0 is where almost every memecoin sits today, and that is the honest answer.** The screener should not launder T0 into "the community exists".

### 4.3 Legal and ethical constraints

**Platform terms (fetched verbatim):**

- **X —** "You may not access the Services in any way other than through the currently available, published interfaces that we provide. For example, this means that, except as required by applicable law, you cannot scrape the Services without X's express written permission, try to work around any technical limitations we impose, or otherwise attempt to disrupt the operation of the Services." (`https://x.com/en/tos`)
- **Discord (Terms) —** "scraping our services without our written consent, including by using any robot, spider, crawler, scraper, or other automatic device, process, or software; selling, licensing, or otherwise commercializing content or data obtained from our services". (`https://discord.com/terms`)
- **Discord (Developer Policy, clause 20) —** "Do not mine or scrape any data, content, or information available on or through Discord services." (`https://discord.com/developers/docs/policies`, fetched 2026-11-03 at HTTP 200; the URL redirects to `https://support-dev.discord.com/hc/en-us/articles/8563934450327-Discord-Developer-Policy`, which returns HTTP 403 to plain non-browser fetches **intermittently** — the clause text was captured and is quoted verbatim here. **Cite the developer-policy URL; fetch it with a browser UA or from a browser if it 403s.**)
- **Telegram —** ToS: "Telegram additionally prohibits data scraping as part of its Content Licensing and AI Scraping Terms, which apply to all users, businesses, and third-party services accessing the platform." (`https://telegram.org/tos`)
- **Telegram (Content Licensing) —** "Telegram firmly prohibits the scraping, indexing, harvesting, aggregation or use of data obtained from its platform to train, fine-tune, validate or otherwise engage in the development, enhancement, benchmarking or deployment of artificial intelligence, machine learning models and similar technologies." (`https://telegram.org/tos/content-licensing`)
- **Reddit (Data API Terms) —** "If you are interested in using the Data APIs for commercial purposes, research in excess of rate limits, or for any use that is not expressly permitted under the Data API Terms, then you will need to enter into a separate agreement with Reddit." (`https://redditinc.com/policies/data-api-terms`)

**Data-protection law:**

- **GDPR Art. 4 (definition of personal data):** data is personal if it relates to an identified or identifiable natural person (`https://eur-lex.europa.eu/eli/reg/2016/679/art_4/oj`).
- **GDPR Art. 5 (principles):** lawfulness/fairness/transparency; purpose limitation; data minimisation; accuracy; storage limitation; integrity/confidentiality (`https://eur-lex.europa.eu/eli/reg/2016/679/art_5/oj`).
- **GDPR Art. 6 (lawful bases):** consent, contract, legal obligation, vital interests, public interest, and **legitimate interests** (`https://eur-lex.europa.eu/eli/reg/2016/679/art_6/oj`).
- **ePrivacy Directive Art. 5(3):** storing/accessing information on terminal equipment requires consent after clear information, subject to exceptions (`https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32002L0058`, HTTP 202).
- **CCPA/CPRA (California):** "personal information" categories and consumer rights including the right to delete (`https://oag.ca.gov/privacy/ccpa`).

**Practical legal guidance for this project:**

1. **A public X/Telegram/Reddit *handle* is not itself personal data** — a handle is not a natural person. But **linking a handle to a natural person's wallet, and then to their transaction history, can create personal data** about that person. The moment the screener says "this wallet is probably the deployer, who is a named person", the analysis is processing personal data and the Art. 6 basis and Art. 5 minimisation obligations attach.
2. **Art. 5 purpose limitation** is the binding constraint: a screener built to *classify token narrative* may not silently accumulate a permanent dossier on individuals. **Collect the aggregate (member count, presence count, mention counts) and keep the identity mapping ephemeral.**
3. **Art. 5 data minimisation** argues for collecting **counts, not content**, wherever the count answers the question. This is also better engineering: a count is stable, a text corpus is a liability.
4. **Scraping vs. using a documented public endpoint.** The ToS clauses above prohibit *scraping*. Calling a **documented, public, unauthenticated JSON endpoint** (Discord's invite resource) at a respectful rate is materially different from crawling a site. **This is the single most important legal distinction in this document for the free/no-key build**: prefer documented public endpoints (DexScreener, Discord invite, Telegram preview, ApeWisdom, Warpcast client) over crawling HTML you were not invited to crawl.
5. **Do not build a bulk X harvester.** X forbids it, it is priced per read, and `robots.txt` disallows the search paths you would need. There is no version of "free X social data" that is lawful and reliable.
6. **Commercial use is the specific trigger for the paid tiers.** Reddit's terms, X's pricing, Nansen's key requirement and Santiment's tiering all key on *commercial* use. The operator's cost constraint is therefore aligned with the terms of service, not in tension with them.

### 4.4 On-chain ↔ off-chain correlation methods that work with free data

- **Deployer → repo:** derive the deployer address on-chain (already implemented in `leapspace/deployers.py`), then check whether a **verified-source** repository or an npm package publishes that address in its README, `package.json`, or deployment config. A **signed commit** by the same key that deployed is T3-grade.
- **Deployer → verified source on the explorer:** Etherscan/Solscan "Contract Source Code Verified" + constructor args often contain the deployer's own address and the mint. Free, no key for the read endpoints.
- **Farcaster FID → custody address:** free via the Warpcast client. Then: does any of that FID's casts mention the token? Does its custody address hold the token? That is a *protocol-anchored* social→on-chain link, and it is the answer to "wallet tracking of the major players that would move the market".
- **Smart-money approximation:** rank wallets by realised PnL on comparable tokens (free: DexScreener/price history + on-chain swaps), then look for *overlap* between the top wallets holding the candidate token and the wallets historically buying early. This reproduces Nansen's *concept* without their labels.
- **Telegram group → mint address:** scrape the group's own message history for the mint; check the **first** mention date against the token's launch date. A group mentioning the mint *before* launch is strong evidence of authenticity (the group pre-existed the token); a group whose only mention is the launch announcement is weak.

---

## SECTION 5 — SIGNAL RELIABILITY

### 5.1 What has evidence behind it

**Bots inflate social volume and the inflation is measurable.**
- Ferrara, *Measuring social spam and the effect of bots on information diffusion in social media* (arXiv:1708.08134, 2017-08-27, fetched via the arXiv API): "Bots have been playing a crucial role in online platform ecosystems, as efficient and automatic tools to generate content and diffuse information to the social media human population… we will first investigate some differences between diffusion dynamics of content generated by bots, as opposed to humans."
- **Consequence for the screener:** raw mention count and raw engagement are bot-contaminated, and the contamination is *systematic* — it favours tokens whose promoters buy bots. Use a dedup/unique-author ratio (§2.5) and prefer **online/presence** counts (§6) over member totals.

**Astroturfing is real, industrialised, and targets the exact mechanism memecoin screener uses.**
- *Ephemeral Astroturfing Attacks: The Case of Fake Twitter Trends* (arXiv:1910.07783v4, 2019-10-17, fetched): "We uncover a previously unknown, ongoing astroturfing attack on the popularity mechanisms of social media platforms: ephemeral astroturfing attacks. In this attack, a chosen keyword or topic is artificially promoted by coordinated and inauthentic activity to appear popular, and, crucially, **this activity is removed as part of the attack**. We observe such attacks on Twitter trends and find that these attacks are not only successful but also pervasive. We detected **over 19,000 unique fake trends promoted by over 108,000 accounts**."
- **This is the most important single finding for this document.** The attack is designed to defeat *exactly* the metric a memecoin screener uses (popularity of a term), and it is **self-cleaning** — a naive scrape at time T sees the inflated signal, and a scrape at T+1 sees nothing. **Implication: any social-popularity metric that is not measured as a time series, with persistence, is gameable by design.**
- *Trollthrottle — Raising the Cost of Astroturfing* (arXiv:2004.08836v1): "Astroturfing, i.e., the fabrication of public discourse by private or state-controlled sponsors via the creation of fake online accounts, has become incredibly widespread in recent years. It gives a disproportionally strong voice to wealthy and technology-savvy actors."
- *Detecting and Tracking the Spread of Astroturf Memes in Microblog Streams* (arXiv:1011.3768v1) — the original framework, noting that "microblogs have become crucial grounds on which public relations, marketing, and political battles are fought."
- **Consequence:** require **persistence** — a signal that survives across two snapshots separated in time is much harder to manufacture than a spike.

**Engagement rate fails as a predictor, and fails in a specific, documented, non-monotonic way.**
- Qureshi & Zaman, *Social Media Engagement and Cryptocurrency Performance* (arXiv:2209.02911v1, 2022-09-07, fetched): "We find that the future returns of the cryptocurrencies are dependent on the engagement coefficients. **Cryptocurrencies whose engagement coefficients are too low or too high have lower returns.** Low engagement coefficients signal a lack of interest, while **high engagement coefficients signal artificial activity which is likely from automated accounts known as bots**. We measure the amount of bot posts for the cryptocurrencies and find that generally, **cryptocurrencies with more bot posts have lower future returns**." The paper's engagement model was designed to "overcome the limitations of previous volume and sentiment based approaches".
- **Consequence for the screener:** score engagement on a **band, not a ramp**. Both "almost nobody engages" and "everyone engages" are bearish signals; only a middle band is constructive. And **correlate engagement with an independent bot indicator** — in this project that indicator is free and free-of-charge: the *online/presence* count from Discord and Telegram versus the member total, and the ratio of distinct participants to mentions.

**Social metrics are not reproducible even from the vendor.**
- Santiment's own disclosure (fetched on the Social Volume, Social Dominance and Unique Social Volume pages): "We constantly update our labels… which helps us keep labels as fresh as possible but results in **historical data changes**. Any modifications to labels, social sources, or relevant jobs will prompt recalculation for the previous month's data."
- **Consequence:** a vendor time-series can change retroactively. Any backtest built on a vendor's social history is **not reproducible** — the vendor's own history will differ from what you recorded. This is an independent reason to build the screener on *counts you fetch yourself*.

**Memecoin social activity is structurally distinct from token fundamentals — which is why the niche/broad distinction is real and worth measuring.**
- *Measuring Memecoin Fragility* (arXiv:2512.00377v2, 2025-11-29, fetched): "Memecoins, emerging from internet culture and community-driven narratives, have rapidly evolved into a unique class of crypto assets. Unlike technology-driven cryptocurrencies, their market dynamics are primarily shaped by **viral social media diffusion, celebrity influence, and speculative capital inflows**." It proposes the Memecoin Ecosystem Fragility Framework (ME2F) with a Volatility Dynamics Score capturing "persistent and extreme price swings together with spillover".
- *Catching the Rug: Early Prediction of Fraudulent Memecoins on Solana via Machine Learning* (arXiv:2608.20271v1, 2026-08-20, fetched): "Solana memecoin rug pulls are predominantly driven by **liquidity manipulation and social dynamics**." (Dataset: 6.4M records.)
- *Bridging Culture and Finance: A Multimodal Analysis of Memecoins in the Web3 Ecosystem* (arXiv:2412.04913v3, 2024-12-06, fetched): introduces "the **Coin-Meme dataset**, an open-source collection of visual, textual, community, and financial data from the Pump.fun platform on the Solana blockchain" — i.e. the academic community treats *cultural* and *financial* features as separate modalities that must be joined. This directly supports the project's "narrative classifier" as a first-class, separable concern.
- *The Memecoin Phenomenon: An In-Depth Study of Solana's Blockchain Trends* (arXiv:2512.11850v3, 2025-12-04, fetched): "Pump$.$fun accounted for up to **71.1%** of all tokens minted on Solana and contributed **40-67.4%** of total DEX transactions. Despite this activity, **fewer than 2% of tokens successfully transitioned to major decentralized exchanges**." — **This independently corroborates the "fewer than 2%" funnel figure in the LeapSpace paper**, from a separate source.
- *Identifying Networked Patterns in Memecoin Twitter Accounts Using Exponential Random Graph Modeling* (IEEE, https://ieeexplore.ieee.org/document/10411759, HTTP 202 = fetched through IEEE's bot-check interstitial): "We built a following-follower and mention-reply network by crawling more than 100 official memecoin Twitter accounts… using statistical tests to detect a [community structure]". Note the method: **network structure, not aggregate counts**, is what identifies a real memecoin community.

### 5.2 What is folklore, or only weakly supported

| Claim | Status | Why |
|---|---|---|
| "A large Telegram member count means a real community" | **FOLKLORE / misleading** | Member counts are self-reported by the group and historically inflated by bots and one-time joiners. The free *online* figure in the same preview is the counter-measure; there is no primary study showing member count predicts memecoin returns. |
| "More engagement = stronger token" | **REFUTED** | arXiv:2209.02911 — engagement is non-monotonic; too-high engagement signals bot activity and predicts *lower* returns. |
| "Social sentiment predicts memecoin price" | **WEAKLY SUPPORTED at best** | The academic work that survives treats sentiment as one weak input next to engagement and bot share; Santiment itself frames sentiment as a *modifier* of attention. No fetched primary source establishes sentiment as a standalone price predictor for memecoins. |
| "Reddit mentions are organic" | **UNSUPPORTED** | Reddit is *more* gameable than it looks: coordinated posting is well documented, and there is no fetched source establishing that Reddit mention counts for memecoins are organic. Treat Reddit as better-sourced than Telegram, not as clean. |
| "Santiment's Social Volume is the industry standard mention count" | **FALSE** | It is one vendor's definition, explicitly labelled RESTRICTED in their own catalogue. Santiment's older article and current academy even disagree on the social-dominance denominator (top-50 vs top-100). |
| "Mindshare is a standard metric" | **FALSE** | Kaito's own blog says the opposite: "all of these metrics often have somewhat different definitions, therefore, we recommend that you always check out how a tool for online analysis actually defines them." |
| "Google Trends shows memecoin search interest for free" | **FALSE as stated** | There is no official free Trends API. `pytrends` self-describes as an "**Unofficial** API for Google Trends… Only good until Google changes their backend again :-P". The unofficial `explore` endpoint returned HTTP 400 to a plain GET from this host. **The official RSS works** (`trends.google.com/trending/rss?geo=US`) but gives only today's top searches — no per-token series. |
| "Kaito, LunarCrush and Santiment all agree on a token's social score" | **FALSE** | They measure different corpora with different filters. Cross-vendor agreement is not a validation; it is three unrelated estimates. |
| "Engagement rate is comparable across tokens" | **FALSE** | The denominator (followers vs impressions vs views) differs between every vendor and every platform, and X's own follower counts exclude other bots and the accounts you follow. Never compare engagement rates across tokens without normalising to a stated denominator — or better, do not compare them at all. |
| "Discord/Telegram invite links prove a project has a community" | **FALSE (T0 only)** | The invite is self-reported. See §4.2. |

### 5.3 The reliability rules that follow

1. **Prefer liveness to size.** `online` (Telegram), `presence_count` (Discord) >> `members`.
2. **Prefer ratios to absolutes.** presence/members, unique-authors/mentions, buyers/mentions.
3. **Require persistence.** A signal must survive two snapshots separated in time. Astroturfing is self-cleaning (§5.1), so a single spike proves nothing.
4. **Score engagement as a band, not a ramp** (arXiv:2209.02911).
5. **Never let one platform carry the verdict.** The five available free surfaces are Telegram, Discord, ApeWisdom (Reddit/4chan), Farcaster, and metadata. A token that is loud on one and absent on the others is the astroturfing signature.
6. **Record `null`, not `0`.** A missing parse (e.g. a Telegram channel that shows posts but no member count) is missing data, not zero traction.
7. **Label every metric STANDARD / VENDOR / ACADEMIC in the output.** A screener that cannot say which metrics are its own inventions will eventually present an invention as a standard.

---

## SECTION 6 — A RECOMMENDED FREE SIGNAL SET

Constraint: **FREE, NO-API-KEY data only.** Each signal below was probed live from this host on 2026-11-03 unless marked otherwise. Signals are ordered by value to the classifier, and each carries its platform and its failure mode.

### Tier 1 — the traction signals that no paid tier improves on

**S1. Discord `approximate_presence_count` (online members) and `approximate_member_count`**
- **Source:** `https://discord.com/api/v9/invites/{code}?with_counts=true` — from the `discord` link in DexScreener's `info.socials`.
- **Rationale:** Discord's invite endpoint returns a **live** count and a **total** count with no key and no widget requirement. The presence/total ratio distinguishes a living server from a padded one. BONK measured **2,120 / 32,586 ≈ 6.5%**.
- **Why it beats paid data:** LunarCrush and Santiment aggregate *public posts*; they cannot see a Discord server's live presence at all. This is a signal they structurally cannot replicate.
- **Failure mode:** the invite may point at a different server than the token's real community (T0 — self-reported). Also `approximate_` means Discord's own estimate.
- **Legal note:** Developer Policy clause 20 (§4.3). Read at low rate, cache the result, and do not mass-scrape.

**S2. Telegram `members` and `online` from the public channel preview**
- **Source:** `https://t.me/s/{username}` — from the `telegram` link in DexScreener's `info.socials`.
- **Rationale:** the same live-vs-total structure as S1, on the platform memecoins actually use. Verified: `Official_Bonk_Inu` → "11 013 members, 313 online" → **~2.8% online**. A large member count with ~0 online is a dead community; the online figure is the discriminator.
- **Failure mode:** bot-inflated membership; parse shape varies by channel (§3.3) — record `null` when absent. Legal: Telegram ToS prohibits scraping (§4.3) — read single public channel previews, do not build a bulk harvester.

**S3. Telegram group message recency + cadence (two-point time series)**
- **Source:** the same `t.me/s/{username}` preview, but count `datetime=` entries and compare across two fetches ≥1h apart.
- **Rationale:** distinguishes a community that is *producing* content from one that merely *exists*. Directly addresses astroturfing: real posts persist, injected ones do not.
- **Failure mode:** the preview window is bounded (5–20 posts observed), so cadence is coarse — enough to detect "zero new posts in 24h", not enough to measure posting rate precisely.

**S4. Token metadata social footprint (DexScreener `info.socials` + `info.websites` + `info.header`)**
- **Source:** `https://api.dexscreener.com/token-pairs/v1/{chain}/{token}` — 300 req/min, no key.
- **Rationale:** it is the *only* free source that yields the project's own declared community channels in one call, and it is the input to S1/S2/S3. Also yields `info.header` (a designed identity banner) and `info.websites` — a website is the best free corroboration surface (§4.2) because it can be cross-checked field-by-field against the mint address.
- **Failure mode:** every link is a self-reported assertion (T0). Treat presence as "asserted", never as "verified".
- **Implementation note:** the live API returns `{type, url}` objects, while the published docs example shows `{platform, handle}` — **the docs and the API disagree.** Code against the live shape and tolerate both.

**S5. Jupiter `tags` and `organicScore`**
- **Source:** `https://lite-api.jup.ag/tokens/v2/search?query=...` — no key.
- **Rationale:** Jupiter's tags (`community`, `verified`, `birdeye-trending`, `moonshot-verified`, `meme`, `strict`) are a **vendor curation label applied to the same token metadata** — they encode whether the project has demonstrated a community, and `organicScore` (BONK measured **82.29**) is Jupiter's own ranking of organic attention. Free, and cheap.
- **Failure mode:** `organicScore` is a **vendor-proprietary composite with an undisclosed formula** — do not present it as a standard, and do not treat it as independent of S4 (it is derived from the same underlying data plus Jupiter's own judgement).
- **Use it as:** a *prior* on which tokens are worth deeper per-token social fetching, not as a classifier input on its own.

### Tier 2 — corroboration and cohort-relative signals

**S6. ApeWisdom Reddit/4chan mention counts and 24h deltas**
- **Source:** `https://apewisdom.io/api/v1.0/filter/{filter}/page/{n}` — no key; filters include `all-crypto`, `CryptoCurrency`, `CryptoMoonShots`, `CryptoMarkets`, `SatoshiStreetBets`.
- **Rationale:** the only free source of **per-subreddit mention counts with a 24h-ago baseline** (`mentions` and `mentions_24h_ago`) — which gives you mention velocity (§2.2) and a persistence check (§5.3) from a source independent of the project's own channels.
- **Failure mode:** **crypto coverage is currently very thin** (live: `all-crypto` returned 5 rows with `mentions: 1`; `CryptoCurrency` likewise). Use it as a *negative* screen (is there any independent Reddit footprint?) and record coverage per token. Absence is not evidence of absence.

**S7. Farcaster public Warpcast client — casts, FIDs, and custody**
- **Source:** `https://client.warpcast.com/v2/search-casts?limit=N&q={symbol}` and `https://client.warpcast.com/v2/user-by-fid?fid={n}` — no key.
- **Rationale:** the **only platform where off-chain identity is anchored to an on-chain address by protocol**, not by self-report. This is the highest-confidence available linkage and directly serves "wallet tracking of the major players": resolve a candidate buyer's FID → custody address → verify the on-chain purchase independently. It also gives a clean read on *which narratives are being discussed by identifiable accounts*, with stable FIDs as primary keys.
- **Failure mode:** small audience (a strength for precision, a weakness for coverage); the client API is undocumented and may change; Neynar's paid API is the stable path.

**S8. On-chain traction to pair against social traction**
- **Source:** DexScreener pair data (liquidity, volume, buys/sells, `pairCreatedAt`), RugCheck report (`topHolders`, `totalHolders`, `totalLPProviders`, `graphInsidersDetected`, `knownAccounts`), Jupiter (`holderCount`, `firstPool`).
- **Rationale:** social signals without on-chain signals cannot distinguish a community from a crowd. The pair `(social size, on-chain participation)` is the classifier: e.g. `mentions per unique buyer` (the free reconstruction of the unverified vendor "conversion rate", §2.13).
- **Failure mode:** none of this is social data — but it is the **control variable** that makes the social data meaningful, and it is entirely free.

**S9. Google Trends daily RSS — market-regime conditioning only**
- **Source:** `https://trends.google.com/trending/rss?geo=US` — official, no key, verified 10 `<item>` elements.
- **Rationale:** a free, *official*, machine-readable read of what the general public is searching for. Use as a **regime gate** (broad cultural attention is up) and to identify **broad-trend** narratives — which is exactly the `narrative.py` taxonomy distinction between niche-specific and broad-trend tokens.
- **Failure mode:** it is **not per-token** and does not give a historical series. Do not attempt per-token Trends without pytrends, and treat pytrends as fragile (self-described "unofficial", `explore` returned HTTP 400 here).

### Tier 3 — local computation (no network, no key)

**S10. VADER sentiment on any text you can lawfully obtain**
- **Source:** `https://github.com/cjhutto/vaderSentiment` (pip `vaderSentiment`), method per [ICWSM paper](https://ojs.aaai.org/index.php/ICWSM/article/view/14550).
- **Rationale:** free, offline, deterministic, academic, and the only sentiment method with a peer-reviewed definition. Apply it to text you already fetched via an allowed route — **not** as a reason to scrape.
- **Failure mode:** sentiment is a *modifier*, not a scorer (§2.6). And on memecoin chatter it is near-constant positive.

**S11. DexScreener `token-boosts` — the paid-promotion tell**
- **Source:** `https://api.dexscreener.com/token-boosts/latest/v1` — 60 req/min, no key. Returns boosted tokens with `description` and `amount`/`totalAmount` fields.
- **Rationale:** **a token that is paying for boosts has bought attention.** This is a direct, free, no-key read on the "paid promotion" failure mode (§5). A boosted token's social metrics are *not* organic, and the boost list tells you which.
- **Failure mode:** boosts are visible only while active; a token can boost for a week and then stop.

### Explicitly EXCLUDED, with reasons

| Excluded | Why |
|---|---|
| **X API anything** | Pay-per-use only ($0.005/post read), ToS forbids scraping, robots.txt disallows the search paths. No free lawful path exists. |
| **TikTok Research API** | Requires an approved academic/non-profit application; a commercial screener is ineligible. |
| **Threads API** | Requires a Meta app + token; and Threads has no meaningful memecoin community to measure. |
| **YouTube Data API** | Needs a free key; `search.list` costs 100 of the 10,000 daily units — poor value for memecoin narrative. Use manual checks on the rare token where a YouTube link is decisive. |
| **LunarCrush / Santiment / Nansen / Kaito / Neynar APIs** | All key-gated; Santiment's social metrics are RESTRICTED even on the free tier; LunarCrush's cheapest paid plan is $90/mo. |
| **Reddit JSON API without OAuth** | 403 on every listing endpoint tested from this host. Register a free OAuth app (still free, but no longer no-key) or use ApeWisdom. |
| **pytrends for per-token series** | Unofficial, self-described as fragile, `explore` returned HTTP 400 here. Use the official RSS for regime only. |
| **Santiment "Conversion Rate"** | No current primary spec page (404 on the academy metric page; "conversion" absent from the 109-page academy metric index). Use the free reconstruction in §2.13 instead. |
| **Trusting `info.socials` presence as community proof** | T0 self-report. Every link needs the §4.2 tier ladder. |
| **Any single-platform verdict** | Five free surfaces exist; astroturfing concentrates on one. Cross-platform agreement is the signal. |

### The recommended classifier input vector (all free, all no-key)

```
per_token = {
  # narrative / specificity (self-reported -> assert only)
  asserted_social_links:   [telegram, discord, twitter, website, ...]   # DexScreener info.socials + info.websites
  link_hosts:              count of distinct hosts asserting the token
  website_present:         bool
  header_image_present:    bool                                        # DexScreener info.header
  jupiter_tags:            [community, verified, birdeye-trending, ...] # Jupiter /tokens/v2/search
  jupiter_organic_score:   float

  # traction - LIVE counts
  tg_members:              int | None                                  # t.me/s/<user>  (null, never 0)
  tg_online:               int | None
  tg_online_ratio:         float | None
  tg_new_posts_1h:         int | None                                  # two-point diff
  dc_members:              int | None                                  # Discord invite with_counts
  dc_presence:             int | None
  dc_presence_ratio:       float | None

  # traction - independent surfaces
  ape_mentions:            int | None                                  # ApeWisdom
  ape_mentions_24h_ago:    int | None
  fc_casts:                int | None                                  # Warpcast client
  fc_distinct_authors:     int | None

  # on-chain controls
  holders:                 int | None                                  # RugCheck totalHolders
  top_holder_concentration: float | None
  insiders_detected:       int | None                                  # RugCheck graphInsidersDetected
  lp_providers:            int | None
  liquidity_usd:           float | None
  volume_24h:              float | None
  unique_buyers_24h:       int | None

  # derived (label every one as an analyst construction)
  presence_ratio:          mean(dc_presence_ratio, tg_online_ratio)
  social_to_buyers_ratio:  mentions / unique_buyers_24h
  cross_platform_confirm:  number of surfaces with a non-null live count
  boost_paid:              bool                                        # DexScreener token-boosts
  bot_suspicion:           f(mentions vs participants, presence vs members)
}
```

**Scoring rules that follow directly from Sections 4–5:**
1. **`cross_platform_confirm` is the single strongest cheap signal.** A token with live counts on Telegram *and* Discord *and* a Reddit/4chan footprint is very unlikely to be an astroturfing artifact; a token with a huge member count on one channel and zeros elsewhere is the signature of a bought community.
2. **Use `presence_ratio` (live/total), not raw members.** A high member count with a low presence ratio is a padded community.
3. **Never score a link's presence as a community.** Score it as an *assertion*; score the *live counts* as traction.
4. **Report `null` distinctly from `0`.** Every field above is `int | None` for a reason.
5. **Report the free signal set as a set of raw observations with an explicit confidence tier per field**, so a later run can re-score with different weights — the discipline `leapspace/narrative.py` already applies to its specificity score (`WEIGHTS` returned with every classification, "so a reader can re-score it"). **Extend that to the traction layer.**
6. **Label each metric inline as STANDARD / VENDOR-PROPRIETARY / ACADEMIC / ANALYST-CONSTRUCTION.** Anything you invent must say so.

---

## APPENDIX A — Verification record

**Final audit of the delivered file:** `tools/audit_document_urls.py` extracts **every** URL from `SOCIAL_NARRATIVE_STANDARDS.md` and fetches it. Result on 2026-11-03 → `reports/document_url_audit.json`:

```
  CITATION       75/75 resolve < 400
  TEMPLATE       12/12 resolve after substitution
  EXPECTED-GATED 10/10 returned the documented status
  TOTAL          97/97
  HARD FAILURES (citations that do not resolve): none
```

The three classes are separated deliberately: a **CITATION** is a URL the reader opens and must return `< 400`; a **TEMPLATE** is a URL with a placeholder (`{code}`, `<username>`, `limit=N`) that is proved real by substituting a known-good value; an **EXPECTED-GATED** URL is one the document cites *because* it fails (a 401/403/400 probe that proves an API key is required). Counting them in one bucket would either hide real breakage or flag deliberate evidence. Two URLs are additionally classified `CITATION-INTERMITTENT` because their upstream blocks non-browser clients inconsistently — Discord's developer policy (403 or 200) and the canonical dni.gov ICD 203 PDF (403, or a connection failure) — and both have a verified-readable alternative cited alongside them.

**Citations:** 76 URLs tested by `tools/verify_citations.py` on 2026-11-03 → `reports/citation_verification.json`. 73 resolved `< 400` on the first pass; 3 failed and were repaired:

| Failed URL | Reason | Replacement (verified) |
|---|---|---|
| `https://developers.facebook.com/docs/threads-api` | HTTP 404 (Meta moved its docs) | `https://developers.facebook.com/documentation/threads/` — **browser-verified only**; plain fetch returns HTTP 400 because Meta rejects non-browser user agents |
| `https://www.dni.gov/index.php/ic-legal-reference-book` | HTTP 403 to this host | Canonical PDF `https://www.dni.gov/files/documents/ICD/ICD-203.pdf` is also 403 to non-browser clients; **verified-readable mirror**: `https://donohueintellaw.ll.georgetown.edu/sites/default/files/assets/ICD%20203%20Analytic%20Standards.pdf` (HTTP 200, 3,051,281 bytes) |
| `https://www.ftc.gov/business-guidance/blog/2023/01/keep-your-ai-claims-check` | HTTP 404 | Replaced with the eCFR primary source: `https://www.ecfr.gov/current/title-16/chapter-I/subchapter-B/part-255` (HTTP 200) — 16 CFR Part 255, Guides Concerning Use of Endorsements and Testimonials in Advertising |

**Live API probes:** `reports/free_endpoint_probe.json` (round 1), `free_endpoint_probe2.json`, `free_endpoint_probe3.json`, `probe4_urls.json`, `probe5.json`, `probe6_papers.json`, `probe7.json`.
**Doc fetches:** `reports/doc_fetches.json` + extracted page text in `reports/doctext/`.
**Rate limits confirmed by parsing the vendors' own pages:** DexScreener 300/min (pairs, search, token-pairs) and 60/min (profiles, boosts, meta); Discord global 50 req/s; X per-resource per-call pricing; YouTube 10,000 units/day; Nansen free tier 15/sec + 300/min; CoinGecko 429 behaviour.

**Verified by fetching** (primary source retrieved and parsed): every metric definition and formula in Section 2 (Santiment Social Volume, Unique Social Volume, Social Dominance, Sentiment Ratio, Categorized Social Volume, Community Social Volume, Community Messages Count; Kaito mindshare; Blockchain Center and CMC Altcoin Season Index; LunarCrush API overview and pricing; Nansen Smart Money endpoints and pricing; CoinGecko coins-id and errors-and-rate-limits; DexScreener API reference; Discord invite/rate-limit/developer-policy pages; Telegram Bot API and both ToS pages; X pricing, free-credits and ToS; Reddit dev API and Data API Terms; ApeWisdom API doc; Google Trends RSS; pytrends PyPI; VADER repo; GDPR Arts. 4/5/6 and ePrivacy Art. 5; CCPA; eCFR 16 CFR 255).
**Verified via the arXiv API** (metadata + full abstract retrieved): arXiv:2209.02911, 1910.07783, 1708.08134, 2512.00377, 2512.11850, 2608.20271, 2412.04913, 2004.08836, 1011.3768.
**Browser-verified, not fetch-verified:** the Meta Threads API documentation pages.
**Inferred from search-result snippets only:** the exact CoinGecko free-tier numeric call cap (CoinGecko's live page publishes error codes and tiering but the specific per-minute figure was not captured in a fetched page — treat the number as unconfirmed); whether ApeWisdom publishes any rate limit (no rate-limit headers were returned; no published figure found — treat as unpublished).
**UNVERIFIED and excluded from the tables:** Santiment "Conversion Rate" formula (no current spec page); the Reddit per-client numeric rate limit (Reddit's own help centre returned HTTP 403 to this host — **the number commonly quoted, 100 queries/minute per OAuth client id, is therefore NOT asserted here**); a per-token Google Trends series (no official API).

## APPENDIX B — Compact index

| Signal | Definition (one line) | Source | Free / paid | Free-API reachable (no key) |
|---|---|---|---|---|
| DexScreener `info.socials` | Project's self-declared social links per token | https://docs.dexscreener.com/api/reference · https://api.dexscreener.com/token-pairs/v1/{chain}/{token} | Free | **Yes** (300/min) |
| DexScreener `info.websites` / `info.header` | Project's declared site + identity banner | same | Free | **Yes** |
| DexScreener `token-boosts` | Tokens currently paying for promotion | https://api.dexscreener.com/token-boosts/latest/v1 | Free | **Yes** (60/min) |
| RugCheck report | On-chain risk facts; **no socials field** | https://api.rugcheck.xyz/v1/tokens/{mint}/report | Free | **Yes** |
| Jupiter tags / organicScore | Vendor curation labels + proprietary organic-attention score | https://lite-api.jup.ag/tokens/v2/search?query=… | Free | **Yes** |
| Telegram channel preview members | Self-reported subscriber count | https://t.me/s/{username} | Free | **Yes** |
| Telegram channel preview online | Live concurrent viewers — liveness signal | https://t.me/s/{username} | Free | **Yes** |
| Telegram message recency (2-point) | New posts between two fetches ≥1h apart | https://t.me/s/{username} | Free | **Yes** |
| Telegram `getChatMemberCount` | Official member count for a chat the bot is in | https://core.telegram.org/bots/api#getchatmembercount | Free w/ bot token | No |
| Discord `approximate_member_count` | Approximate total guild members via invite | https://discord.com/api/v9/invites/{code}?with_counts=true | Free | **Yes** (50/s) |
| Discord `approximate_presence_count` | Approximate currently-online members — liveness | same | Free | **Yes** (50/s) |
| Discord widget `member_count` / `presence_count` | Same, but requires the Server Widget enabled (404 otherwise) | https://discord.com/developers/docs/resources/guild#get-guild-widget | Free | Partly (404 if disabled) |
| ApeWisdom mentions | Reddit/4chan mention count + rank per ticker | https://apewisdom.io/api/v1.0/filter/{filter}/page/{n} | Free | **Yes** |
| ApeWisdom `mentions_24h_ago` | 24h-ago baseline → mention velocity | same | Free | **Yes** |
| Farcaster search-casts | Public casts with FID-anchored authors | https://client.warpcast.com/v2/search-casts?limit=N&q=… | Free | **Yes** |
| Farcaster user-by-fid | Profile incl. custody/verified addresses | https://client.warpcast.com/v2/user-by-fid?fid={n} | Free | **Yes** |
| CoinGecko `links` | Project's declared homepage/twitter/telegram/reddit/github | https://api.coingecko.com/api/v3/coins/{id} | Free (keyless tier) | **Yes** (429 on burst) |
| CoinGecko `community_data` | Follower/subscriber counts — **retired 28 Aug 2026** | https://docs.coingecko.com/reference/coins-id | Retired | **No** |
| Google Trends daily RSS | Today's top searches, any topic | https://trends.google.com/trending/rss?geo=US | Free | **Yes** |
| Altcoin Season Index | % of top-50/100 coins beating BTC over 90d; ≥75% = season | https://blockchaincenter.net/altcoin-season-index · https://coinmarketcap.com/charts/altcoin-season-index | Free | **Yes** (recomputable) |
| VADER sentiment | Rule-based lexicon sentiment, compound ∈ [−1,1] | https://github.com/cjhutto/vaderSentiment · https://ojs.aaai.org/index.php/ICWSM/article/view/14550 | Free | **Yes** (local) |
| Social volume (Santiment) | Documents containing the term, 1 per document | https://academy.santiment.net/metrics/social-volume/ | Paid (RESTRICTED) | **No** |
| Unique social volume (Santiment) | Matching documents after content dedup per 5m/1h/1d | https://academy.santiment.net/metrics/unique-social-volume/ | Paid (RESTRICTED) | **No** |
| Social dominance (Santiment) | Asset volume ÷ top-100-by-mcap volume | https://academy.santiment.net/metrics/social-dominance/ | Paid (RESTRICTED) | **No** |
| Sentiment ratio (Santiment) | Pos/Neu/Neg doc shares | https://academy.santiment.net/metrics/sentiment-ratio/ | Paid | **No** |
| Mindshare (Kaito) | % of total tracked attention within a comparison group + period | https://studio.kaito.ai/blog/what-is-mindshare | Paid | **No** |
| Narrative Mindshare (Kaito) | Prominence of a narrative/story in market context | https://h5.portal.kaito.ai/narrative | Paid | **No** |
| Galaxy Score / AltRank (LunarCrush) | Proprietary composite social/market indices | https://lunarcrush.com/developers/api | Paid $90/$300/$900 | **No** (401 w/o bearer) |
| LunarCrush social volume / sentiment | Mention volume + sentiment per asset | https://lunarcrush.com/developers/api/endpoints | Paid | **No** |
| Nansen Smart Money netflow | Inflow − outflow by historically profitable traders | https://docs.nansen.ai/api/smart-money | Free tier (100 credits) / $49 Pro | **No** (401 w/o key) |
| X API post read | X post resource | https://docs.x.com/x-api/getting-started/pricing | **$0.005/resource, no free tier** | **No** |
| X API user read | X user resource | same | $0.010/resource | **No** |
| YouTube Data API | Quota-metered data API | https://developers.google.com/youtube/v3/getting-started | Free key, 10k units/day | **No** (key required) |
| Reddit Data API | Reddit listing/search endpoints | https://www.reddit.com/dev/api | Free OAuth app | **No** (403 unauth'd) |
| TikTok Research API | Approved-researcher public data | https://developers.tiktok.com/products/research-api/ | Free if approved (academic) | **No** |
| Threads API | Meta Threads posts/profiles/insights | https://developers.facebook.com/documentation/threads/ | Free w/ Meta app | **No** |
| Neynar | Farcaster data at scale | https://neynar.com/ | x402 pay-per-call / key | **No** (402) |
| DEX social→on-chain conversion | mentions ÷ unique buyers | vendor formula UNVERIFIED; free reconstruction §2.13 | Free | **Yes** (from free inputs) |
| Engagement coefficient | Interactions-with-posts engagement; **non-monotonic** vs returns | https://arxiv.org/abs/2209.02911 | Free (paper) | **Yes** (paper) |
| Mentions-to-unique-participants ratio | Bot-adjustment ratio | https://academy.santiment.net/metrics/unique-social-volume/ (vendor) / §2.5 (free reconstruction) | Free inputs | **Yes** |
| Cross-platform confirmation count | # of surfaces with a non-null live count | analyst construction, §6 | Free | **Yes** |
| Presence ratio (live ÷ total) | Discord presence/members, Telegram online/members | analyst construction, §6 | Free | **Yes** |
| Bot suspicion score | From mentions-vs-participants + presence-vs-members | analyst construction, §6 | Free | **Yes** |
| Boost-paid flag | Token is currently paying for promotion | https://api.dexscreener.com/token-boosts/latest/v1 | Free | **Yes** |
| Identity-link confidence tier | T0 unverified claim → T3 cryptographic | ICD 203 (https://www.dni.gov/files/documents/ICD/ICD-203.pdf; mirror https://donohueintellaw.ll.georgetown.edu/sites/default/files/assets/ICD%20203%20Analytic%20Standards.pdf) | Free | **Yes** (methodology) |
