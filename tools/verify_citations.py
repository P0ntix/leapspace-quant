"""FINAL VERIFICATION: re-fetch every URL that will be cited in
SOCIAL_NARRATIVE_STANDARDS.md and record the exact status.

This is the evidence table the document's "verified by fetching" claim
rests on. Any URL that fails here is either fixed or marked UNVERIFIED
in the document.

Run:  python tools/verify_citations.py
"""
from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "reports", "citation_verification.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

try:
    import certifi
    _CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:  # pragma: no cover
    _CTX = ssl.create_default_context()

CITATIONS = [
    # (id, url, purpose)
    ("DS-REF", "https://docs.dexscreener.com/api/reference", "DexScreener endpoint list + rate limits"),
    ("DS-PAIRS", "https://api.dexscreener.com/token-pairs/v1/solana/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", "DexScreener token-pairs live"),
    ("RUG-REPORT", "https://api.rugcheck.xyz/v1/tokens/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263/report", "RugCheck report live"),
    ("JUP-DOCS", "https://docs.jup.ag/", "Jupiter docs"),
    ("JUP-SEARCH", "https://lite-api.jup.ag/tokens/v2/search?query=bonk", "Jupiter token search live"),
    ("CG-DOCS", "https://docs.coingecko.com/reference/coins-id", "CoinGecko coins-id docs (community_data removal)"),
    ("CG-PING", "https://api.coingecko.com/api/v3/ping", "CoinGecko public ping"),
    ("REDDIT-DEV", "https://www.reddit.com/dev/api", "Reddit API reference"),
    ("REDDIT-TERMS", "https://redditinc.com/policies/data-api-terms", "Reddit Data API Terms"),
    ("DISC-DOCS", "https://discord.com/developers/docs", "Discord developer docs"),
    ("DISC-INVITE", "https://discord.com/developers/docs/resources/invite", "Discord Invite resource (with_counts)"),
    ("DISC-INVITE-LIVE", "https://discord.com/api/v9/invites/qaQa6M6mN2?with_counts=true", "Discord public invite live"),
    ("DISC-RATE", "https://discord.com/developers/docs/topics/rate-limits", "Discord rate limits"),
    ("DISC-TERMS", "https://discord.com/terms", "Discord Terms of Service"),
    ("DISC-DEVPOL", "https://discord.com/developers/docs/policies", "Discord Developer Policy"),
    ("TG-BOTS", "https://core.telegram.org/bots/api", "Telegram Bot API"),
    ("TG-MEMBERCOUNT", "https://core.telegram.org/bots/api#getchatmembercount", "Telegram getChatMemberCount"),
    ("TG-LINKS", "https://core.telegram.org/api/links", "Telegram public link previews"),
    ("TG-TOS", "https://telegram.org/tos", "Telegram ToS"),
    ("TG-CONTENTLIC", "https://telegram.org/tos/content-licensing", "Telegram Content Licensing / AI scraping terms"),
    ("TG-PREVIEW-LIVE", "https://t.me/s/Official_Bonk_Inu", "Telegram public channel preview live"),
    ("X-PRICING", "https://docs.x.com/x-api/getting-started/pricing", "X API pay-per-use pricing"),
    ("X-FREECREDITS", "https://docs.x.com/x-api/getting-started/free-credits", "X API free credits"),
    ("X-INTRO", "https://docs.x.com/x-api/introduction", "X API introduction"),
    ("X-TOS", "https://x.com/en/tos", "X Terms of Service"),
    ("X-ROBOTS", "https://x.com/robots.txt", "X robots.txt"),
    ("TT-RESEARCH", "https://developers.tiktok.com/products/research-api/", "TikTok Research API"),
    ("TT-DISPLAY", "https://developers.tiktok.com/doc/display-api-overview", "TikTok Display API"),
    ("YT-DOCS", "https://developers.google.com/youtube/v3/docs", "YouTube Data API"),
    ("YT-QUOTA", "https://developers.google.com/youtube/v3/getting-started", "YouTube quota"),
    ("FC-DOCS", "https://docs.farcaster.xyz/", "Farcaster docs"),
    ("FC-WARPCAST-LIVE", "https://client.warpcast.com/v2/search-casts?limit=5&q=bonk", "Farcaster public client live"),
    ("THREADS-DOCS", "https://developers.facebook.com/docs/threads-api", "Threads API"),
    ("SANT-ACADEMY", "https://academy.santiment.net/metrics/", "Santiment metric index"),
    ("SANT-VOL", "https://academy.santiment.net/metrics/social-volume/", "Santiment Social Volume"),
    ("SANT-UNIQ", "https://academy.santiment.net/metrics/unique-social-volume/", "Santiment Unique Social Volume"),
    ("SANT-DOM", "https://academy.santiment.net/metrics/social-dominance/", "Santiment Social Dominance"),
    ("SANT-SENTRATIO", "https://academy.santiment.net/metrics/sentiment-ratio/", "Santiment Sentiment Ratio"),
    ("SANT-CATVOL", "https://academy.santiment.net/metrics/social-volume-categorized/", "Santiment Categorized Social Volume"),
    ("SANT-COMMUNITY", "https://academy.santiment.net/metrics/community-social-volume/", "Santiment Community Social Volume"),
    ("SANT-PRICING", "https://app.santiment.net/pricing", "Santiment pricing"),
    ("SANT-AVAILMETRICS", "https://api.santiment.net/available_metrics", "Santiment metric catalogue"),
    ("LCR-API", "https://lunarcrush.com/developers/api", "LunarCrush API overview"),
    ("LCR-PRICING", "https://lunarcrush.com/pricing", "LunarCrush pricing"),
    ("NAN-API", "https://www.nansen.ai/api", "Nansen API + pricing"),
    ("NAN-SMART", "https://docs.nansen.ai/api/smart-money", "Nansen Smart Money endpoints"),
    ("ASI-BC", "https://blockchaincenter.net/altcoin-season-index", "Altcoin Season Index (Blockchain Center)"),
    ("ASI-CMC", "https://coinmarketcap.com/charts/altcoin-season-index", "CMC Altcoin Season Index"),
    ("KAITO-MIND", "https://studio.kaito.ai/blog/what-is-mindshare", "Kaito mindshare definition"),
    ("KAITO-DOCS", "https://docs.kaito.ai/", "Kaito docs"),
    ("APEW-API", "https://apewisdom.io/api", "ApeWisdom API docs"),
    ("APEW-LIVE", "https://apewisdom.io/api/v1.0/filter/all-crypto/page/1", "ApeWisdom live"),
    ("VADER-GH", "https://github.com/cjhutto/vaderSentiment", "VADER implementation"),
    ("VADER-PAPER", "https://ojs.aaai.org/index.php/ICWSM/article/view/14550", "VADER ICWSM paper"),
    ("PYTRENDS-PYPI", "https://pypi.org/project/pytrends/", "pytrends"),
    ("PYTRENDS-GH", "https://github.com/GeneralMills/pytrends", "pytrends repo"),
    ("TRENDS-RSS", "https://trends.google.com/trending/rss?geo=US", "Google Trends official RSS"),
    ("TRENDS-HELP", "https://support.google.com/trends/answer/4365533", "Google Trends help"),
    ("GDPR-ART5", "https://eur-lex.europa.eu/eli/reg/2016/679/art_5/oj", "GDPR Art.5"),
    ("GDPR-ART6", "https://eur-lex.europa.eu/eli/reg/2016/679/art_6/oj", "GDPR Art.6"),
    ("GDPR-ART4", "https://eur-lex.europa.eu/eli/reg/2016/679/art_4/oj", "GDPR Art.4"),
    ("CCPA", "https://oag.ca.gov/privacy/ccpa", "CCPA/CPRA"),
    ("ARXIV-ENGAGE", "https://arxiv.org/abs/2209.02911", "Social Media Engagement and Cryptocurrency Performance"),
    ("ARXIV-ASTRO", "https://arxiv.org/abs/1910.07783", "Ephemeral Astroturfing Attacks: Fake Twitter Trends"),
    ("ARXIV-BOTS", "https://arxiv.org/abs/1708.08134", "Bots on information diffusion (Ferrara)"),
    ("ARXIV-MEME-FRAG", "https://arxiv.org/abs/2512.00377", "Measuring Memecoin Fragility"),
    ("ARXIV-MEME-SOL", "https://arxiv.org/abs/2512.11850", "Memecoin Phenomenon: Solana"),
    ("ARXIV-RUG", "https://arxiv.org/abs/2608.20271", "Catching the Rug: Solana ML"),
    ("ARXIV-MULTIMODAL", "https://arxiv.org/abs/2412.04913", "Bridging Culture and Finance: Multimodal Memecoins"),
    ("ARXIV-ASTRO2", "https://arxiv.org/abs/2004.08836", "Trollthrottle - Raising the Cost of Astroturfing"),
    ("ARXIV-MEME-ASTRO", "https://arxiv.org/abs/1011.3768", "Detecting Astroturf Memes in Microblog Streams"),
    ("ARXIV-API", "https://export.arxiv.org/api/query?search_query=all:memecoin&max_results=1", "arXiv API"),
    ("IEEE-MEME-SOCIAL", "https://ieeexplore.ieee.org/document/8919455", "Social Media Analysis in the Era of Memecoin"),
    ("IEEE-MEME-NET", "https://ieeexplore.ieee.org/document/10411759", "Identifying Networked Patterns in Memecoin Twitter Accounts"),
    ("DNI-ADM", "https://www.dni.gov/index.php/ic-legal-reference-book", "ICD 203 Analytic Standards"),
    ("NYT-FTC", "https://www.ftc.gov/business-guidance/blog/2023/01/keep-your-ai-claims-check", "FTC claims check"),
]


def check(url):
    hdrs = {"User-Agent": UA, "Accept": "*/*,text/html,application/json",
            "Accept-Language": "en-US,en;q=0.9"}
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=30, context=_CTX) as r:
            body = r.read(400000)
            return {"status": r.status, "final_url": r.url, "bytes": len(body),
                    "content_type": r.headers.get("Content-Type", "")}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "final_url": url, "error": f"HTTPError {exc.code}"}
    except Exception as exc:  # noqa: BLE001
        return {"status": None, "final_url": url, "error": f"{type(exc).__name__}: {exc}"[:160]}


def main():
    out = []
    ok = 0
    for cid, url, purpose in CITATIONS:
        rec = {"id": cid, "url": url, "purpose": purpose}
        rec.update(check(url))
        st = rec.get("status")
        good = bool(st and st < 400)
        ok += 1 if good else 0
        rec["verified"] = good
        out.append(rec)
        print(f"{str(st):>5} {'OK ' if good else 'FAIL'}  {cid}")
        time.sleep(0.6)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n{ok}/{len(out)} citations resolve with status < 400")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
