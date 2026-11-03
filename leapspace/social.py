"""Multi-platform social signals and traction measurement.

This is the FIX to the narrative classifier. The previous version read only
Jupiter's `community` tag and DexScreener's `info.socials`, so it never saw
Telegram-group culture vs TikTok marketing, and it measured no traction at
all. This module reads EVERY platform the free sources expose and separates
NARRATIVE (what the project says it is) from TRACTION (what the market
actually did).

SOURCES, AND WHAT EACH ONE IS EVIDENCE OF
-----------------------------------------
The osint-investigation skill's rule applies: every claim must trace to a
record, and confidence travels with the claim. So each signal carries a
`confidence` tier, because these sources are NOT equally reliable:

  declared_by_project   A social link or description the PROJECT declares
                        about itself. Evidence that the project CLAIMS a
                        community. NOT evidence the community exists, and
                        NOT evidence of who controls the account.
  third_party_observed On-chain or market data observed by a third party
                        (holder counts, volume, buy/sell split).
  vendor_assigned      A vendor's own computed score (Jupiter's organic
                        score, RugCheck's risk score). Reproducing the
                        vendor's methodology is not possible, so these are
                        reported as the vendor's opinion, never as fact.

PLATFORM TAXONOMY
-----------------
  community_platforms  telegram, discord - a channel the project runs for
                        its members. The strongest free proxy for a real
                        community, and the one the paper's "niche community"
                        clause is really about.
  broadcast_platforms  x/twitter, tiktok, instagram, youtube, facebook,
                        reddit, threads, medium, substack, bluesky, farcaster
                        - reach, not membership. A project can broadcast to
                        100k people and have zero members.
  site                 a website.

A token with 1 broadcast platform and no community channel is a marketing
page. A token with 2+ community platforms has members. That distinction -
membership vs reach - is the thing the old classifier could not see.

TRACTION
--------
Traction is measured from data a third party observed: holder count and its
change, buy/sell imbalance, ORGANIC volume (volume excluding suspected
bot activity, as Jupiter computes it), liquidity, transaction counts, LP
lock, and the project's age. An account of followers is not traction; an
account of holders, volume and organic flow is.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .http import http_get, http_json
from .provenance import CACHE, LIVE, Provenance, SourceUnavailable

# --------------------------------------------------------------------------
# Platform taxonomy
# --------------------------------------------------------------------------
COMMUNITY_PLATFORMS = ("telegram", "discord", "t.me", "discord.gg",
                        "discord.com", "telegram.me")
BROADCAST_PLATFORMS = ("twitter", "x.com", "tiktok", "instagram", "youtube",
                       "facebook", "reddit", "threads", "medium", "substack",
                       "bluesky", "bsky", "farcaster", "warpcast", "weibo",
                       "mastodon", "linkedin")

#: Social link type -> normalised platform name.
_PLATFORM_ALIASES = {
    "twitter": "x", "x": "x", "tiktok": "tiktok", "instagram": "instagram",
    "youtube": "youtube", "facebook": "facebook", "reddit": "reddit",
    "threads": "threads", "medium": "medium", "substack": "substack",
    "discord": "discord", "telegram": "telegram", "t.me": "telegram",
    "discord.gg": "discord", "discord.com": "discord", "telegram.me":
    "telegram", "bluesky": "bluesky", "farcaster": "farcaster",
    "warpcast": "farcaster", "linkedin": "linkedin", "mastodon": "mastodon",
    "weibo": "weibo", "linktree": "linktree", "linktr.ee": "linktree",
}


def _normalise_platform(raw_type: str, url: str) -> str:
    """Map a social link to a platform name, falling back to the URL host."""
    t = (raw_type or "").strip().lower()
    if t in _PLATFORM_ALIASES:
        return _PLATFORM_ALIASES[t]
    u = (url or "").lower()
    for key, name in _PLATFORM_ALIASES.items():
        if key in u:
            return name
    for key, name in (("x.com", "x"), ("twitter.com", "x"),
                      ("youtu.be", "youtube"), ("t.me", "telegram")):
        if key in u:
            return name
    return t or "unknown"


def _class_of(platform: str) -> str:
    if platform in ("telegram", "discord"):
        return "community"
    if platform in ("x", "tiktok", "instagram", "youtube", "facebook",
                    "reddit", "threads", "medium", "substack", "bluesky",
                    "farcaster", "weibo", "mastodon", "linkedin"):
        return "broadcast"
    if platform in ("site", "linktree"):
        return "site"
    return "other"


# --------------------------------------------------------------------------
# Narrative text analysis
# --------------------------------------------------------------------------
#: Words in a project's own description that signal a COMMUNITY with a
#: specific culture rather than a generic launch. Analyst-authored list.
COMMUNITY_TEXT_MARKERS = (
    "community", "cult", "army", "lore", "canon", "believers", "holders",
    "fam", "crew", "squad", "brigade", "troops", "mission", "movement",
    "rebel", "chad", "based", "degen", "anon", "anon", "meme", "memecoin",
    "club", "squad", "guild", "order", "brotherhood", "frens", "pixel",
    "reddit", "discord", "telegram", "memes", "copypasta", "irony",
    "satire", "shitpost", "internet", "viral", "crossover", "collab",
    "narrative", "season", "episode", "arc", "lorebook", "fandom",
)

#: Words in a description that signal a GENERIC financial launch.
GENERIC_TEXT_MARKERS = (
    "utility", "ecosystem", "defi", "protocol", "staking", "yield", "apy",
    "governance", "tokenomics", "roadmap", "partnership", "launchpad",
    "airdrop", "presale", "ido", "ieo", "liquidity", "marketplace",
    "exchange", "platform", "revolution", "future of", "next generation",
    "gamefi", "nft", "metaverse", "ai-powered", "web3", "blockchain",
)

#: Capitalised / rare tokens in a description that look like NAMED entities
#: (a person, a place, a specific in-joke). A proper-noun proxy.
_PROPER_NOUN = re.compile(r"\b([A-Z][a-z]{2,}[A-Za-z]*)\b")
_STOP_CAPS = {
    "The", "This", "That", "Our", "Your", "Their", "Token", "Coin",
    "Community", "Protocol", "Network", "Official", "Join", "Welcome",
    "About", "What", "Why", "How", "Get", "Now", "New", "All", "For",
    "With", "From", "Into", "Only", "Just", "Your", "Every", "One",
}


def analyse_description(text: str) -> Dict[str, Any]:
    """Classify a project's own description for community vs generic framing.

    The description is the richest free NARRATIVE field available: it is
    written by the project about itself. It is therefore evidence of the
    project's CLAIM, not of anything beyond it.
    """
    t = (text or "").strip()
    low = t.lower()
    community_hits = sorted({m for m in COMMUNITY_TEXT_MARKERS if m in low})
    generic_hits = sorted({m for m in GENERIC_TEXT_MARKERS if m in low})
    props = sorted({m for m in _PROPER_NOUN.findall(t)
                    if m not in _STOP_CAPS})
    return {
        "has_description": bool(t),
        "description_chars": len(t),
        "community_markers": community_hits,
        "generic_markers": generic_hits,
        "named_entities": props[:8],
        "named_entity_count": len(props),
        # More community markers than generic ones => community-framed.
        "community_framed": bool(community_hits)
                            and len(community_hits) >= len(generic_hits),
        "generic_framed": bool(generic_hits)
                          and len(generic_hits) > len(community_hits),
        "confidence": "declared_by_project",
    }


# --------------------------------------------------------------------------
# Source readers
# --------------------------------------------------------------------------
def _dexscreener_pair_socials(chain: str, token: str) -> Dict[str, Any]:
    """Social links carried on the DexScreener PAIR record."""
    from .chains import dexscreener_pairs
    try:
        pairs = dexscreener_pairs(chain, token)
    except Exception as exc:  # noqa: BLE001
        raise SourceUnavailable(f"dexscreener pairs {chain}/{token}: {exc}")
    if not pairs:
        raise SourceUnavailable(f"dexscreener has no pair for "
                                f"{chain}/{token}")
    p = pairs[0]
    info = p.get("info") or {}
    socials = info.get("socials") or []
    if isinstance(socials, dict):
        socials = [{"type": k, "url": v} for k, v in socials.items()]
    sites = info.get("websites") or []
    if isinstance(sites, str):
        sites = [{"url": sites}]
    return {
        "socials": socials,
        "websites": sites,
        "header": info.get("header"),
        "open_graph": info.get("openGraph"),
        "image": info.get("imageUrl"),
        "pair": p,
    }


#: DexScreener's PER-TOKEN profile endpoint does not exist. The rich
#: social+description records live in two GLOBAL lists, each holding the
#: 30 most recent (or most boosted) tokens. Their COVERAGE IS LIMITED and
#: that limitation is reported, not hidden: a token outside those lists
#: simply has no written description.
_DEXSCR_GLOBAL_LISTS = (
    ("https://api.dexscreener.com/token-profiles/latest/v1",
     "dexscreener_token_profiles_latest"),
    ("https://api.dexscreener.com/token-boosts/top/v1",
     "dexscreener_token_boosts_top"),
)


def _dexscreener_profile_links(chain: str, token: str) -> Dict[str, Any]:
    """Social links + description for a token, from DexScreener's global lists.

    COVERAGE LIMIT: the per-token endpoint `/token-profiles/v1/{chain}/{token}`
    does NOT exist (verified: HTTP error). The records that carry the extra
    platforms (tiktok, instagram) and the project's written DESCRIPTION live
    in two GLOBAL lists of 30 tokens each. A token in neither list gets no
    description - which is reported in `coverage`.
    """
    want = (token or "").lower()
    merged: Dict[str, Any] = {"links": [], "description": None,
                              "header": None, "icon": None,
                              "open_graph": None, "url": None}
    seen: set = set()
    lists_hit: List[str] = []
    for url, name in _DEXSCR_GLOBAL_LISTS:
        try:
            data, _ = http_json(url, timeout=25)
        except Exception:  # noqa: BLE001
            continue
        for row in (data if isinstance(data, list) else []):
            if not isinstance(row, dict):
                continue
            if str(row.get("tokenAddress") or "").lower() != want:
                continue
            lists_hit.append(name)
            for link in (row.get("links") or []):
                if isinstance(link, dict):
                    seen.add(json.dumps(link, sort_keys=True))
                    merged["links"].append(link)
            if row.get("description") and not merged["description"]:
                merged["description"] = row.get("description")
            for k, src in (("header", "header"), ("icon", "icon"),
                           ("open_graph", "openGraph"), ("url", "url")):
                if row.get(src) and not merged.get(k):
                    merged[k] = row.get(src)
    if not lists_hit:
        raise SourceUnavailable(
            f"token is not in DexScreener's global profile/boost lists - it "
            f"has no written description there (those lists hold 30 tokens "
            f"each). Pair-record links are still used.")
    merged["coverage"] = {
        "lists_hit": lists_hit,
        "note": ("Description and extra platforms come from DexScreener's "
                 "GLOBAL 30-token lists; coverage is partial by design."),
    }
    return merged


def _jupiter_profile(mint: str) -> Dict[str, Any]:
    """Jupiter token record: tags, organic score, stats, audit (Solana).

    The RAW v2 record is read directly rather than through
    `memecoin.fetch_token_profile`, because that wrapper renames the stats
    keys and drops `dev` (the deployer address), which the insider checks
    need.
    """
    url = f"https://lite-api.jup.ag/tokens/v2/search?query={mint}"
    data, _ = http_json(url, timeout=30)
    rows = data if isinstance(data, list) else []
    if not rows:
        raise SourceUnavailable(f"jupiter returned no token for {mint}")
    return rows[0]


def _rugcheck_summary(mint: str) -> Dict[str, Any]:
    """RugCheck FULL report: top holders with owners, insider flags, risks.

    The `/report` endpoint is used, not `/report/summary`: only the full
    report carries `topHolders` with the OWNING WALLET, the holder's pct
    and an `insider` flag, plus `totalHolders`, `graphInsidersDetected` and
    `insiderNetworks`.
    """
    from .memecoin import fetch_rugcheck
    try:
        report, _ = fetch_rugcheck(mint)
    except Exception as exc:  # noqa: BLE001
        raise SourceUnavailable(f"rugcheck report {mint}: {exc}")
    return report



# --------------------------------------------------------------------------
# Community SIZE - the strongest free evidence for the "niche community"
# clause, and obtainable with no API key.
#
# A project publishes its own community links, so these reads are
# `declared_by_project` in confidence. But the COUNTS are hosted and
# computed by a third party, so the metric is recorded as an observed
# public metric with that split stated.
#
# VALIDITY TRAP (live-verified): a NONEXISTENT Telegram channel still
# returns HTTP 200. Its title reads "Telegram: Contact @name"; a real
# channel reads "Telegram: View @name". Only the latter carries a member
# count, so the title check is what stops a zero-member channel from
# being reported as a community with members.
# --------------------------------------------------------------------------
_TG_MEMBER_RE = re.compile(
    r"([\d\s,\u00a0\u202f\.]+?)\s*members", re.I)
_TG_ONLINE_RE = re.compile(
    r"([\d\s,\u00a0\u202f\.]+?)\s*online", re.I)
_TG_VIEW_RE = re.compile(r"<title>\s*Telegram:\s*View\s*@", re.I)


def _telegram_username(url: str) -> Optional[str]:
    """Extract a public channel username from a t.me link."""
    u = (url or "").strip()
    m = re.search(r"(?:t\.me|telegram\.me)/(?:s/)?@?([A-Za-z0-9_]{4,})",
                  u)
    if not m:
        return None
    name = m.group(1)
    # /joinchat/<hash> and /+<hash> are private invites, not channels.
    if u.lower().find("/joinchat/") >= 0 or "/+" in u:
        return None
    return name


def _discord_invite_code(url: str) -> Optional[str]:
    """Extract a Discord invite code from a discord.gg / discord.com link."""
    u = (url or "").strip()
    m = re.search(r"discord\.gg/([A-Za-z0-9]+)", u)
    if not m:
        m = re.search(r"discord\.com/invite/([A-Za-z0-9]+)", u)
    return m.group(1) if m else None


def _clean_count(s: str) -> Optional[int]:
    """'11 009' -> 11009. Handles spaces, nbsp, narrow-nbsp and commas."""
    t = re.sub(r"[\s\u00a0\u202f,]", "", s or "")
    t = t.rstrip(".")
    try:
        return int(t)
    except (TypeError, ValueError):
        return None


def fetch_telegram_size(url: str) -> Dict[str, Any]:
    """Member and online counts from a Telegram channel's public preview."""
    user = _telegram_username(url)
    out: Dict[str, Any] = {"source": "telegram_public_preview",
                            "url": url, "username": user}
    if not user:
        out["status"] = "no_public_channel_in_link"
        return out
    try:
        st, body, _ = http_get(f"https://t.me/s/{user}", timeout=25)
        html = body.decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        out["status"] = "unavailable"
        out["error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
        return out
    out["http_status"] = st
    if st != 200:
        out["status"] = "unavailable"
        return out
    if not _TG_VIEW_RE.search(html):
        # "Contact @x" means this is a personal profile or a channel that
        # does not exist. Either way there is NO member count.
        out["status"] = "not_a_channel_or_absent"
        out["members"] = None
        out["online"] = None
        return out
    m = _TG_MEMBER_RE.search(html)
    o = _TG_ONLINE_RE.search(html)
    members = _clean_count(m.group(1)) if m else None
    online = _clean_count(o.group(1)) if o else None
    if members is None:
        out["status"] = "no_member_count_in_page"
        out["members"] = None
        out["online"] = online
        return out
    out["status"] = "ok"
    out["members"] = members
    out["online"] = online
    out["confidence"] = ("declared_by_project (the link) + observed public "
                         "metric (the count, hosted by Telegram)")
    return out


def fetch_discord_size(url: str) -> Dict[str, Any]:
    """Member and presence counts from a Discord invite."""
    code = _discord_invite_code(url)
    out: Dict[str, Any] = {"source": "discord_invite_api", "url": url,
                            "invite_code": code}
    if not code:
        out["status"] = "no_invite_code_in_link"
        return out
    api = (f"https://discord.com/api/v9/invites/{code}"
           f"?with_counts=true")
    try:
        data, st = http_json(api, timeout=25)
    except Exception as exc:  # noqa: BLE001
        out["status"] = "unavailable"
        out["error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
        return out
    if not isinstance(data, dict):
        out["status"] = "unavailable"
        out["http_status"] = st
        return out
    out["http_status"] = st
    members = data.get("approximate_member_count")
    presence = data.get("approximate_presence_count")
    out["members"] = int(members) if isinstance(members, (int, float)) else None
    out["online"] = (int(presence)
                     if isinstance(presence, (int, float)) else None)
    out["guild_name"] = (data.get("guild") or {}).get("name")
    out["status"] = "ok" if out["members"] is not None else "no_counts"
    out["confidence"] = ("declared_by_project (the link) + observed public "
                         "metric (the count, hosted by Discord)")
    return out


# --------------------------------------------------------------------------
# The composite profile
# --------------------------------------------------------------------------
def fetch_social_profile(chain: str, token: str,
                          jupiter: bool = False,
                          rugcheck: bool = False) -> Dict[str, Any]:
    """Collect every free social + traction signal available for a token.

    `jupiter` and `rugcheck` are Solana-only sources; on other chains they
    are skipped and the omission is recorded rather than hidden.
    """
    out: Dict[str, Any] = {
        "chain": chain, "token": token,
        "sources": [], "gaps": [],
        "platforms": [], "social_links": [],
        "narrative": {}, "traction": {},
        "provenance": LIVE,
    }

    # --- pair-level links ---------------------------------------------------
    pair_info: Dict[str, Any] = {}
    try:
        pair_info = _dexscreener_pair_socials(chain, token)
        out["sources"].append({"source": "dexscreener_pairs",
                               "url": f"https://api.dexscreener.com/"
                                      f"token-pairs/v1/{chain}/{token}",
                               "status": "ok"})
    except SourceUnavailable as exc:
        out["gaps"].append({"source": "dexscreener_pairs", "reason": str(exc)})

    # --- token-profile links + description ----------------------------------
    profile_info: Dict[str, Any] = {}
    try:
        profile_info = _dexscreener_profile_links(chain, token)
        out["sources"].append({"source": "dexscreener_token_profile",
                               "url": f"https://api.dexscreener.com/"
                                      f"token-profiles/v1/{chain}/{token}",
                               "status": "ok"})
    except SourceUnavailable as exc:
        out["gaps"].append({"source": "dexscreener_token_profile",
                            "reason": str(exc)})

    # --- collect every link from both records --------------------------------
    links: List[Dict[str, Any]] = []
    for s in (pair_info.get("socials") or []):
        if isinstance(s, dict):
            links.append({"type": s.get("type"), "url": s.get("url"),
                          "from": "pair"})
    for s in (profile_info.get("links") or []):
        if isinstance(s, dict):
            links.append({"type": s.get("type"), "url": s.get("url"),
                          "from": "token_profile"})
    for s in (pair_info.get("websites") or []):
        if isinstance(s, dict):
            links.append({"type": "website", "url": s.get("url"),
                          "from": "pair"})

    norm: Dict[str, str] = {}
    for s in links:
        plat = _normalise_platform(str(s.get("type") or ""),
                                   str(s.get("url") or ""))
        if plat == "unknown":
            continue
        norm.setdefault(plat, str(s.get("url") or ""))
    out["social_links"] = [{"platform": k, "url": v,
                             "class": _class_of(k)} for k, v in norm.items()]
    out["platforms"] = sorted(norm)
    community = [p for p in norm if _class_of(p) == "community"]
    broadcast = [p for p in norm if _class_of(p) == "broadcast"]
    sites = [p for p in norm if _class_of(p) == "site"]
    out["platform_classes"] = {"community": sorted(community),
                               "broadcast": sorted(broadcast),
                               "site": sorted(sites)}

    # --- narrative from the project's own description -------------------------
    desc = profile_info.get("description") or ""
    out["narrative"] = analyse_description(desc)
    out["narrative"]["description_source"] = (
        "dexscreener_token_profile" if desc else "")
    out["narrative"]["has_header_image"] = bool(
        pair_info.get("header") or profile_info.get("header"))
    out["narrative"]["has_open_graph"] = bool(
        pair_info.get("open_graph") or profile_info.get("open_graph"))

    # --- traction from the pair record --------------------------------------
    pair = pair_info.get("pair") or {}
    liq = pair.get("liquidity") or {}
    txns = pair.get("txns") or {}
    vol = pair.get("volume") or {}
    pc = pair.get("priceChange") or {}
    t24 = txns.get("h24") or {}
    traction: Dict[str, Any] = {
        "price_usd": pair.get("priceUsd"),
        "price_change_24h": pc.get("h24"),
        "liquidity_usd": liq.get("usd"),
        "volume_24h_usd": vol.get("h24"),
        "market_cap": pair.get("marketCap"),
        "fdv": pair.get("fdv"),
        "buys_24h": t24.get("buys"),
        "sells_24h": t24.get("sells"),
        "txns_24h": t24.get("buys", 0) + t24.get("sells", 0) if t24 else None,
        "pair_created_at": pair.get("pairCreatedAt"),
        "confidence": "third_party_observed",
    }
    b, s = traction.get("buys_24h"), traction.get("sells_24h")
    traction["buy_sell_ratio_24h"] = (round(b / s, 3)
                                       if b is not None and s else None)

    # --- Solana-only enrichment ---------------------------------------------
    jup: Dict[str, Any] = {}
    if jupiter:
        try:
            jup = _jupiter_profile(token)
            out["sources"].append({"source": "jupiter_tokens_v2",
                                   "url": "https://lite-api.jup.ag/tokens/v2/"
                                          f"search?query={token}",
                                   "status": "ok"})
        except Exception as exc:  # noqa: BLE001
            out["gaps"].append({"source": "jupiter_tokens_v2",
                                "reason": str(exc)})
    else:
        out["gaps"].append({"source": "jupiter_tokens_v2",
                            "reason": "Solana-only source; not applicable to "
                                      f"chain '{chain}'"})

    if jup:
        stats = jup.get("stats24h") or {}
        stats1h = jup.get("stats1h") or {}
        audit = jup.get("audit") or {}
        traction.update({
            "holder_count": jup.get("holderCount"),
            "holder_change_1h": stats1h.get("holderChange"),
            "holder_change_24h": stats.get("holderChange"),
            "volume_change_24h": stats.get("volumeChange"),
            "buy_volume_24h": stats.get("buyVolume"),
            "sell_volume_24h": stats.get("sellVolume"),
            "buy_organic_volume_24h": stats.get("buyOrganicVolume"),
            "sell_organic_volume_24h": stats.get("sellOrganicVolume"),
            "organic_score": jup.get("organicScore"),
            "organic_score_label": jup.get("organicScoreLabel"),
            "top_holders_pct": audit.get("topHoldersPercentage"),
            "dev_balance_pct": audit.get("devBalancePercentage"),
            "mint_authority_disabled": audit.get("mintAuthorityDisabled"),
            "freeze_authority_disabled": audit.get("freezeAuthorityDisabled"),
            "jupiter_tags": jup.get("tags") or [],
            "is_verified": jup.get("isVerified"),
            "deployer": jup.get("dev"),
            "created_at": jup.get("createdAt"),
        })
        ov = ((traction.get("buy_organic_volume_24h") or 0)
              + (traction.get("sell_organic_volume_24h") or 0))
        tv = ((traction.get("buy_volume_24h") or 0)
              + (traction.get("sell_volume_24h") or 0))
        traction["organic_volume_share_24h"] = (round(ov / tv, 3)
                                                 if tv > 0 else None)
        traction["organic_score_confidence"] = "vendor_assigned"

    if rugcheck:
        try:
            rc = _rugcheck_summary(token)
            out["sources"].append({"source": "rugcheck_report",
                                   "url": f"https://api.rugcheck.xyz/v1/"
                                          f"tokens/{token}/report",
                                   "status": "ok"})
            th = rc.get("top_holders") or []
            traction.update({
                "rugcheck_score": rc.get("score"),
                "rugcheck_score_normalised": rc.get("score_normalised"),
                "rugcheck_risk_level": rc.get("score_normalised"),
                "rugcheck_total_holders": rc.get("total_holders"),
                "rugcheck_insider_count": (
                    rc.get("insider_holder_count")
                    or sum(1 for r in th if r.get("insider"))),
                "rugcheck_graph_insiders": rc.get("graph_insiders_detected"),
                "rugcheck_creator": rc.get("creator"),
                "rugcheck_creator_balance": rc.get("creator_balance"),
                "rugcheck_rugged": rc.get("rugged"),
                "rugcheck_lp_providers": rc.get("total_lp_providers"),
                "rugcheck_markets": len(rc.get("markets") or []),
                "rugcheck_risks": [r.get("name") for r in (rc.get("risks") or [])
                                   if isinstance(r, dict)],
                "rugcheck_top_holders": [
                    {"owner": r.get("owner"), "pct": r.get("pct"),
                     "insider": r.get("insider")} for r in th[:10]],
            })
            # lpLockedPct lives on the /report/summary endpoint, not the
            # full report, so it is a second (free) call.
            try:
                summ, _ = http_json(
                    f"https://api.rugcheck.xyz/v1/tokens/{token}/report/summary",
                    timeout=30)
                traction["lp_locked_pct"] = (summ or {}).get("lpLockedPct")
            except Exception:  # noqa: BLE001
                traction["lp_locked_pct"] = None
        except Exception as exc:  # noqa: BLE001
            out["gaps"].append({"source": "rugcheck_summary",
                                "reason": str(exc)})
    else:
        out["gaps"].append({"source": "rugcheck_summary",
                            "reason": "Solana-only source; not applicable to "
                                      f"chain '{chain}'"})

    if traction.get("created_at"):
        try:
            import datetime as _dt
            born = _dt.datetime.fromisoformat(
                str(traction["created_at"]).replace("Z", "+00:00"))
            traction["age_days"] = round(
                (time.time() - born.timestamp()) / 86400.0, 2)
        except Exception:  # noqa: BLE001
            traction["age_days"] = None

    # --- community SIZE: the counts behind the links ----------------------
    community_size: Dict[str, Any] = {"sources": {}, "errors": []}
    for plat, purl in norm.items():
        if plat == "telegram":
            res = fetch_telegram_size(purl)
        elif plat == "discord":
            res = fetch_discord_size(purl)
        else:
            continue
        community_size["sources"][plat] = res
        if res.get("status") != "ok":
            community_size["errors"].append(
                {"platform": plat, "status": res.get("status"),
                 "reason": res.get("error", "")})
    tg = (community_size["sources"].get("telegram") or {})
    dc = (community_size["sources"].get("discord") or {})
    tg_members = tg.get("members")
    dc_members = dc.get("members")
    combined = (tg_members or 0) + (dc_members or 0)
    community_size["telegram_members"] = tg_members
    community_size["telegram_online"] = tg.get("online")
    community_size["discord_members"] = dc_members
    community_size["discord_online"] = dc.get("online")
    community_size["discord_guild_name"] = dc.get("guild_name")
    community_size["combined_members"] = combined if combined else None
    community_size["measured_platforms"] = sum(
        1 for x in (tg_members, dc_members) if x is not None)
    community_size["note"] = (
        "Counts are live reads of public pages, no API key. A channel with "
        "a link but no public member count is reported as unmeasured, not "
        "as zero.")
    out["community_size"] = community_size

    out["traction"] = traction
    traction["community_members"] = combined if combined else None
    traction["community_online"] = ((tg.get("online") or 0)
                                     + (dc.get("online") or 0)) or None
    out["narrative"]["n_community_platforms"] = len(community)
    out["narrative"]["n_broadcast_platforms"] = len(broadcast)
    out["narrative"]["platform_breadth"] = len(norm)
    out["narrative"]["has_multi_platform"] = len(norm) >= 2
    out["narrative"]["has_community_channel"] = bool(community)
    out["narrative"]["has_broadcast_only"] = bool(broadcast) and not community
    out["narrative"]["community_channel_ratio"] = (
        round(len(community) / len(norm), 3) if norm else None)
    return out


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------
#: NARRATIVE weights. ANALYST CHOICES - disclosed and re-scorable.
NARRATIVE_WEIGHTS: Dict[str, float] = {
    "has_community_channel": 2.0,      # membership, not reach
    "community_has_members": 2.0,      # the count exists -> a real community
    "large_community": 1.5,            # >= 1000 members (ANALYST_CHOICE)
    "community_measured_on_both": 0.5, # Telegram AND Discord both measured
    "multi_community_channels": 1.0,   # 2+ community platforms
    "community_framed_description": 2.0,
    "named_entities": 1.0,             # specific in-joke / person / place
    "has_multi_platform": 1.0,
    "has_broadcast_platform": 0.5,
    "has_website": 0.5,
    "has_header_image": 0.5,
    "jupiter_community_tag": 2.0,
    "generic_framed_description": -1.5,
    "has_broadcast_only": -1.0,
    "launchpad_random_name": -1.0,
    "trend_keyword_name": -1.0,
}

#: TRACTION weights. ANALYST CHOICES - disclosed and re-scorable.
TRACTION_WEIGHTS: Dict[str, float] = {
    "has_community_members": 2.0,      # community SIZE is traction
    "has_organic_score": 1.5,
    "organic_score_high": 1.0,
    "holder_growth_24h": 1.0,
    "buy_pressure_24h": 0.5,
    "has_liquidity": 0.5,
    "lp_locked": 0.5,
    "young_token": 0.5,
}


def score_narrative(profile: Dict[str, Any],
                    name_info: Optional[Dict[str, Any]] = None
                    ) -> Dict[str, Any]:
    """Turn a social profile into a narrative score + niche verdict."""
    nar = profile.get("narrative") or {}
    tr = profile.get("traction") or {}
    jtags = [str(t).lower() for t in (tr.get("jupiter_tags") or [])]

    cs = profile.get("community_size") or {}
    members = cs.get("combined_members")
    signals: Dict[str, Any] = {
        "has_community_channel": bool(nar.get("has_community_channel")),
        "community_has_members": bool(members),
        "large_community": bool(members and members >= 1000),
        "community_measured_on_both": (
            int(cs.get("measured_platforms") or 0) >= 2),
        "multi_community_channels":
            int(nar.get("n_community_platforms") or 0) >= 2,
        "community_framed_description": bool(nar.get("community_framed")),
        "named_entities": int(nar.get("named_entity_count") or 0) >= 1,
        "has_multi_platform": bool(nar.get("has_multi_platform")),
        "has_broadcast_platform":
            int(nar.get("n_broadcast_platforms") or 0) >= 1,
        "has_website": bool(nar.get("narrative_website")) or bool(
            (profile.get("platform_classes") or {}).get("site")),
        "has_header_image": bool((profile.get("narrative") or {})
                                 .get("has_header_image")),
        "jupiter_community_tag": "community" in jtags,
        "generic_framed_description": bool(nar.get("generic_framed")),
        "has_broadcast_only": bool(nar.get("has_broadcast_only")),
    }
    if name_info:
        signals["launchpad_random_name"] = bool(
            name_info.get("launchpad_random_name"))
        signals["trend_keyword_name"] = bool(name_info.get("trend_keyword_name"))

    score = 0.0
    for k, w in NARRATIVE_WEIGHTS.items():
        if k in signals:
            score += w * (1.0 if signals[k] else 0.0)
    has_footprint = bool(signals["has_community_channel"]
                         or signals["community_framed_description"]
                         or signals["jupiter_community_tag"])
    is_niche = score >= 5.0 and has_footprint

    reasons: List[str] = []
    if signals["has_community_channel"]:
        reasons.append(
            "community channel(s): "
            + ", ".join((profile.get("platform_classes") or {})
                        .get("community") or []))
    cs = profile.get("community_size") or {}
    if cs.get("telegram_members"):
        reasons.append(f"Telegram: {cs['telegram_members']} members")
    if cs.get("discord_members"):
        reasons.append(f"Discord: {cs['discord_members']} members")
    if signals["large_community"]:
        reasons.append("community has >=1000 members (ANALYST_CHOICE "
                       "threshold)")
    if signals["multi_community_channels"]:
        reasons.append("more than one community platform")
    if signals["community_framed_description"]:
        reasons.append("own description is community-framed")
    if signals["named_entities"]:
        ents = ", ".join((nar.get("named_entities") or [])[:4])
        reasons.append(f"named entities in description: {ents}")
    if signals["has_multi_platform"]:
        reasons.append(f"present on {nar.get('platform_breadth')} platforms")
    if signals["has_broadcast_only"]:
        reasons.append("broadcast only - reach without membership")
    if signals["generic_framed_description"]:
        reasons.append("own description is generic-financial framing")
    if signals["jupiter_community_tag"]:
        reasons.append("Jupiter tags the token 'community'")

    return {
        "narrative_score": round(score, 2),
        "is_niche": is_niche,
        "signals": signals,
        "reasons": reasons,
        "platforms": profile.get("platforms") or [],
        "weights": NARRATIVE_WEIGHTS,
        "threshold": 5.0,
        "threshold_label": "ANALYST_CHOICE - not a paper-stated value",
        "confidence": "declared_by_project for links/description; "
                      "third_party_observed for on-chain metrics",
    }


def score_traction(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Turn observed market behaviour into a traction score."""
    tr = profile.get("traction") or {}
    hv = tr.get("holder_change_24h")
    b = tr.get("buys_24h")
    s = tr.get("sells_24h")
    oscore = tr.get("organic_score")
    age = tr.get("age_days")
    lp = tr.get("lp_locked_pct")

    cs = profile.get("community_size") or {}
    signals: Dict[str, Any] = {
        "has_community_members": bool(cs.get("combined_members")),
        "has_organic_score": oscore is not None,
        "organic_score_high": bool(
            str(tr.get("organic_score_label") or "").lower() == "high"),
        "holder_growth_24h": bool(hv is not None and hv > 0),
        "buy_pressure_24h": bool(b and s and b > s),
        "has_liquidity": bool((tr.get("liquidity_usd") or 0) > 0),
        "lp_locked": bool(lp is not None and float(lp) > 0),
        "young_token": bool(age is not None and age < 30),
    }
    score = 0.0
    for k, w in TRACTION_WEIGHTS.items():
        if signals.get(k):
            score += w
    return {
        "traction_score": round(score, 2),
        "signals": signals,
        "weights": TRACTION_WEIGHTS,
        "observed": {
            "holder_count": tr.get("holder_count"),
            "holder_change_24h": hv,
            "organic_score": oscore,
            "organic_score_label": tr.get("organic_score_label"),
            "buy_sell_ratio_24h": tr.get("buy_sell_ratio_24h"),
            "organic_volume_share_24h": tr.get("organic_volume_share_24h"),
            "liquidity_usd": tr.get("liquidity_usd"),
            "volume_24h_usd": tr.get("volume_24h_usd"),
            "age_days": age,
            "lp_locked_pct": lp,
            "rugcheck_risk_level": tr.get("rugcheck_risk_level"),
        },
        "threshold_label": "ANALYST_CHOICE - not a paper-stated value",
        "confidence": "third_party_observed, except organic_score and "
                      "rugcheck_risk_level which are vendor_assigned",
    }
