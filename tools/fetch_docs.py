"""Bulk-fetch documentation pages and print the text that matters.

Every citation in SOCIAL_NARRATIVE_STANDARDS.md must come from a page we
actually fetched, so this records the fetch + the relevant excerpt.

Run:  python tools/fetch_docs.py
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

import requests
import certifi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "reports", "doc_fetches.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# (key, url, [regex-ish keyword groups to keep])
PAGES = [
    ("x_api_pricing", "https://docs.x.com/x-api/getting-started/pricing",
     ["pay-per-use", "free credit", "$0.005", "Owned Reads", "cap"]),
    ("x_api_free_credits", "https://docs.x.com/x-api/fundamentals/free-credits",
     ["free credit", "$20", "one-time"]),
    ("x_api_intro", "https://docs.x.com/x-api/introduction", ["pay-per-use", "tier"]),
    ("x_robots", "https://x.com/robots.txt", ["Disallow", "User-agent"]),
    ("x_tos", "https://x.com/en/tos", ["scrap", "crawl", "automated", "robot"]),
    ("telegram_tos", "https://telegram.org/tos", ["scrap", "crawl", "automated"]),
    ("discord_terms", "https://discord.com/terms", ["scrap", "crawl", "automated",
                                                    "robot"]),
    ("reddit_data_api_terms", "https://redditinc.com/policies/data-api-terms",
     ["rate limit", "User-Agent", "commercial", "scrap", "authenticat"]),
    ("discord_widget", "https://discord.com/developers/docs/resources/guild#get-guild-widget",
     ["widget", "invite", "member"]),
    ("discord_rate_limits", "https://discord.com/developers/docs/topics/rate-limits",
     ["50", "route", "bucket"]),
    ("telegram_bots_api", "https://core.telegram.org/bots/api",
     ["getChatMemberCount", "getChat", "getMe"]),
    ("reddit_dev_api", "https://www.reddit.com/dev/api",
     ["rate limit", "OAuth", "100 requests", "60 requests"]),
    ("coingecko_rate_limits", "https://docs.coingecko.com/reference/overview",
     ["rate limit", "calls per minute", "Demo", "free"]),
    ("coingecko_community_data", "https://docs.coingecko.com/reference/coins-id",
     ["community_data", "twitter_followers", "subreddit_subscribers",
      "telegram_channel_user_count"]),
    ("dexscreener_docs", "https://docs.dexscreener.com/api/reference",
     ["socials", "info", "300", "rate", "token-pairs"]),
    ("dexscreener_rate", "https://docs.dexscreener.com/api/rate-limits",
     ["rate", "60", "300"]),
    ("lunarcrush_endpoints", "https://lunarcrush.com/developers/api/endpoints",
     ["Galaxy Score", "Alt Rank", "social_volume", "sentiment", "Access"]),
    ("lunarcrush_pricing", "https://lunarcrush.com/pricing", ["Free", "$", "Plan",
                                                            "credits"]),
    ("santiment_pricing", "https://app.santiment.net/pricing", ["Free", "$", "Plan"]),
    ("santiment_social_volume", "https://academy.santiment.net/metrics/social-volume/",
     ["Definition", "Social Volume", "Unique Social Volume", "documents"]),
    ("santiment_social_dominance",
     "https://academy.santiment.net/metrics/social-dominance/",
     ["Definition", "Social Dominance", "top 100", "%"]),
    ("santiment_unique_social_volume",
     "https://academy.santiment.net/metrics/unique-social-volume/",
     ["unique", "authors", "bot"]),
    ("nansen_smart_money", "https://docs.nansen.ai/smart-money/overview",
     ["smart money", "tag", "wallet"]),
    ("nansen_api_pricing", "https://www.nansen.ai/pricing", ["$", "Free", "plan"]),
    ("altcoin_season_index", "https://blockchaincenter.net/altcoin-season-index",
     ["index", "outperform", "Bitcoin", "80%"]),
    ("cmc_altcoin_season", "https://coinmarketcap.com/charts/altcoin-season-index",
     ["index", "outperform"]),
    ("kaito_mindshare", "https://studio.kaito.ai/blog/what-is-mindshare",
     ["mindshare", "attention", "definition"]),
    ("kaito_docs", "https://docs.kaito.ai/", ["mindshare", "API"]),
    ("farcaster_docs", "https://docs.farcaster.xyz/", ["hub", "Neynar", "API"]),
    ("neynar_pricing", "https://www.neynar.com/pricing", ["Free", "$", "credits"]),
    ("tiktok_research_api", "https://developers.tiktok.com/products/research-api/",
     ["approved", "researcher", "application", "free"]),
    ("youtube_quota", "https://developers.google.com/youtube/v3/getting-started",
     ["10,000", "quota", "units"]),
    ("threads_api", "https://developers.facebook.com/docs/threads-api",
     ["Threads", "Instagram", "access"]),
    ("pytrends_readme", "https://raw.githubusercontent.com/GeneralMills/pytrends/master/README.md",
     ["unofficial", "API", "Google Trends"]),
    ("vader_readme", "https://raw.githubusercontent.com/cjhutto/vaderSentiment/master/README.rst",
     ["heuristic", "sentiment", "compound"]),
    ("gdpr_article_5", "https://gdpr-info.eu/art-5-gdpr/",
     ["data minimisation", "purpose limitation", "accuracy"]),
    ("gdpr_article_6", "https://gdpr-info.eu/art-6-gdpr/",
     ["lawful basis", "consent"]),
    ("eprivacy_art_5", "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32002L0058",
     ["terminal equipment", "storage", "information society services"]),
    ("hiq_linkedin", "https://supreme.justia.com/cases/federal/appellate-courts/ca9/17-16783/17-16783-2021-04-15.html",
     ["publicly accessible", "scrape", "CFAA"]),
    ("twitter_automation_rule", "https://help.x.com/en/rules-and-policies/x-automation",
     ["automation", "scraping", "access"]),
    ("reddit_api_policy", "https://support.reddithelp.com/hc/en-us/articles/14945211791892-Reddit-API-Access",
     ["rate limit", "OAuth", "free"]),
]


def strip_html(t: str) -> str:
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t)


def fetch(key, url, keywords):
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "*/*"})
    s.verify = certifi.where()
    rec = {"key": key, "url": url}
    try:
        r = s.get(url, timeout=30)
        rec["status"] = r.status_code
        rec["final_url"] = r.url
        raw = r.text
        if raw.lstrip().startswith(("{", "[")):
            rec["is_json"] = True
            rec["excerpt"] = raw[:1500]
        else:
            txt = strip_html(raw)
            rec["text_len"] = len(txt)
            rec["head"] = txt[:700]
            hits = []
            for kw in keywords:
                for m in re.finditer(re.escape(kw), txt, re.I):
                    a = max(0, m.start() - 260)
                    hits.append(f"[{kw}] ...{txt[a:m.start() + 420]}...")
                    break
            rec["keyword_excerpts"] = hits[:8]
            rec["full_text_file"] = f"doc_{key}.txt"
            with open(os.path.join(HERE, "..", "reports", "doctext", rec["full_text_file"]),
                      "w", encoding="utf-8") as fh:
                fh.write(txt)
    except Exception as exc:  # noqa: BLE001
        rec["status"] = None
        rec["error"] = f"{type(exc).__name__}: {exc}"[:200]
    print(f"{str(rec.get('status')):>5}  {key}")
    return rec


def main():
    os.makedirs(os.path.join(HERE, "..", "reports", "doctext"), exist_ok=True)
    out = []
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for key, url, kws in PAGES:
        if only and only not in key:
            continue
        out.append(fetch(key, url, kws))
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
