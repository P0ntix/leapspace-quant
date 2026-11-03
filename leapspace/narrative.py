"""Narrative specificity: is this token a NICHE community, or a generic trend clone?

The meme-coin paper's clause:

    "One notable nuance is thematic quality. In a large Pump.fun sample,
    tokens tied to niche communities and viral cultural expressions
    outperformed broader-trend tokens [15]. That implies that launch
    selection should include cultural specificity as a filtering feature,
    not just momentum."

    Layer 1: "Ask whether the token is tied to a specific meme, niche
    community, or viral cultural expression rather than a generic trend."

Why this module exists
----------------------
The earlier audit recorded this clause as MISSING with the reason "no free
source labels a token generic, so there's no baseline to compare against".
That reasoning was half right and half wrong. There is no free source
that ASSIGNS a token a "generic" label - but there are free SOURCES OF
COMMUNITY FOOTPRINT, and the baseline can be derived from the screened
COHORT ITSELF rather than from an external label set.

Three things are implemented here:

1. `classify_specificity` - a disclosed, weighted classifier over free
   signals that separate a community footprint from a trend clone.
2. `cohort_baseline` - the baseline the clause needs, derived from the
   median and quartiles of the cohort being screened. A token is judged
   against its PEERS, not against an invented absolute.
3. `test_niche_outperformance` - an EMPIRICAL test of the paper's
   performance claim, because the clause asserts that niche tokens
   OUTPERFORM. A filter that claims a performance relationship should be
   held to it, and the honest answer has to be allowed to be "the sample
   does not support it".

Honesty rules this module never breaks:

* Every weight and every keyword list is an ANALYST CHOICE and is
  returned with every classification, so a reader can re-score it.
* The backward association (h24 price change vs specificity) is labelled
  BACKWARD. It is NOT a forward test.
* The forward test requires two observations separated in time. `save_cohort`
  writes a timestamped snapshot; `verify_cohort` later computes the
  forward return. Until a second observation exists, the forward verdict
  is "not yet measurable", not "no effect".
* Nothing here measures attention, sentiment or community SIZE. It
  measures the PRESENCE of a community footprint, which is a different
  and weaker thing.
"""
from __future__ import annotations

import json
import os
import re
import statistics
from typing import Any, Dict, List, Optional, Sequence

from .provenance import read_json, write_json

COHORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "state", "narrative_cohort.json")

# --------------------------------------------------------------------------
# The taxonomy. Every entry is an ANALYST CHOICE, disclosed and re-scorable.
# --------------------------------------------------------------------------

#: Points added per signal. The weights encode the judgement that a
#: COMMUNITY FOOTPRINT (a community channel, a designed identity) is
#: stronger evidence of niche specificity than a name keyword.
WEIGHTS: Dict[str, float] = {
    "community_tag": 2.0,            # Jupiter's "community" tag
    "multi_platform_socials": 2.0,   # more than one social platform
    "has_community_channel": 2.0,    # telegram or discord present
    "has_header_image": 1.0,         # a designed identity banner
    "has_website": 1.0,              # a dedicated site
    "is_verified": 1.0,              # Jupiter verification
    "launchpad_random_name": -1.0,   # alnum gibberish name -> generic
    "trend_keyword_name": -1.0,      # rides a broad trend -> generic
}

#: Minimum score for a token to be called niche.
NICHE_SCORE_THRESHOLD = 5.0

#: Keywords that indicate the token RIDES a broad trend rather than
#: expressing a specific culture. Disclosed list, analyst-authored.
#:
#: Deliberately EXCLUDED are specific meme names (pepe, doge, shib, bonk,
#: wif, inu, ape, milady) and subculture markers (based, cult, rez). By
#: the paper's own distinction those are NICHE - a specific meme with its
#: own community - not the broad-trend category. Only mass themes and
#: generic launch words belong here.
TREND_KEYWORDS = (
    "moon", "pump", "meme", "coin", "token", "solana", "sol", "btc",
    "bitcoin", "eth", "ethereum", "ai", "elon", "musk", "trump", "biden",
    "new", "baby", "gold", "silver", "money", "rich", "king", "queen",
    "safe", "gem", "chill", "lfg", "gg", "fud", "wgm", "elonmusk",
    "tremp", "maga",
)

#: Social platforms that indicate a COMMUNITY rather than a marketing page.
COMMUNITY_PLATFORMS = ("telegram", "discord", "t.me", "discord.gg",
                        "discord.com")

#: A name that looks launchpad-generated: short, alnum, no vowels or a
#: consonant-only run. Analyst heuristic.
_ALNUM_RE = re.compile(r"^[A-Za-z0-9]{2,6}$")
_VOWELS = set("aeiouAEIOU")


def _name_specificity(name: str, symbol: str) -> Dict[str, Any]:
    """Analyse a token's NAME for generic-launchpad signs."""
    raw = (name or symbol or "").strip()
    out: Dict[str, Any] = {"name": raw}
    is_alnum = bool(_ALNUM_RE.match(raw))
    out["is_short_alnum"] = is_alnum
    out["has_vowel"] = any(ch in _VOWELS for ch in raw) if raw else False
    # A short alnum name with no vowel looks machine-generated.
    out["launchpad_random_name"] = bool(
        is_alnum and len(raw) <= 5 and not out["has_vowel"])
    low = raw.lower()
    hits = sorted({k for k in TREND_KEYWORDS if k in low})
    out["trend_keywords"] = hits
    out["trend_keyword_name"] = bool(hits)
    return out


def classify_specificity(profile: Dict[str, Any],
                         pair: Dict[str, Any]) -> Dict[str, Any]:
    """Score one token's narrative specificity from free sources.

    `profile` is the Jupiter token profile (leapspace.memecoin
    .fetch_token_profile) and `pair` the normalised DexScreener pair.

    Returns the individual signals, the weighted score, the niche verdict
    and the reason - plus the full weight table so a reader can re-score.
    """
    tags = profile.get("tags") or []
    info = pair.get("info") or {}
    socials = info.get("socials") or pair.get("socials") or []
    if isinstance(socials, dict):
        socials = [{"type": k, "url": v} for k, v in socials.items()]
    platforms = sorted({str(s.get("type") or "").lower()
                         for s in socials if isinstance(s, dict)})
    urls = " ".join(str(s.get("url") or "") for s in socials
                    if isinstance(s, dict)).lower()

    signals: Dict[str, Any] = {
        "community_tag": "community" in tags,
        "multi_platform_socials": len(platforms) >= 2,
        "has_community_channel": any(p in platforms for p in COMMUNITY_PLATFORMS)
                                  or any(p in urls for p in COMMUNITY_PLATFORMS),
        "has_header_image": bool(info.get("header")
                                 or pair.get("info_header")),
        "has_website": bool(info.get("websites") or info.get("website")
                             or pair.get("websites")),
        "is_verified": bool(profile.get("is_verified")),
    }
    name_info = _name_specificity(profile.get("name") or "",
                                  profile.get("symbol") or "")
    signals.update({
        "launchpad_random_name": name_info["launchpad_random_name"],
        "trend_keyword_name": name_info["trend_keyword_name"],
    })

    score = sum(WEIGHTS[k] * (1.0 if signals[k] else 0.0) for k in WEIGHTS)
    has_footprint = bool(signals["community_tag"]
                         or signals["has_community_channel"]
                         or signals["multi_platform_socials"])
    is_niche = score >= NICHE_SCORE_THRESHOLD and has_footprint

    reasons: List[str] = []
    if signals["community_tag"]:
        reasons.append("Jupiter tags the token 'community'")
    if signals["has_community_channel"]:
        reasons.append("has a community channel (telegram/discord)")
    if signals["multi_platform_socials"]:
        reasons.append(f"social presence on {len(platforms)} platforms")
    if signals["has_header_image"]:
        reasons.append("has a designed identity header")
    if signals["has_website"]:
        reasons.append("has a dedicated website")
    if signals["launchpad_random_name"]:
        reasons.append("name looks launchpad-generated (generic)")
    if signals["trend_keyword_name"]:
        reasons.append(f"name rides a broad trend ({', '.join(name_info['trend_keywords'])})")
    if not reasons:
        reasons.append("no community footprint signal present")

    return {
        "specificity_score": round(score, 2),
        "is_niche": is_niche,
        "has_community_footprint": has_footprint,
        "signals": signals,
        "reasons": reasons,
        "name_analysis": name_info,
        "social_platforms": platforms,
        "n_social_links": len(socials),
        "weights": dict(WEIGHTS),
        "niche_threshold": NICHE_SCORE_THRESHOLD,
        "trend_keywords": list(TREND_KEYWORDS),
        "disclosure": (
            "The score weights and keyword list are ANALYST CHOICES. This "
            "measures the PRESENCE of a community footprint - it does NOT "
            "measure attention, sentiment, or community size, and it is "
            "NOT a measure of the paper's [15] outperformance, which is "
            "tested separately by backward_association() and "
            "verify_cohort()."),
    }


# --------------------------------------------------------------------------
# The baseline: derived from the cohort being screened
# --------------------------------------------------------------------------


def cohort_baseline(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """The baseline the clause needs, taken from the cohort itself.

    No free source labels a token "generic", but a screened cohort has its
    OWN distribution: the tokens that carry fewer community-footprint
    signals than three quarters of their peers are generic RELATIVE TO
    THIS COHORT. That is a real, data-derived baseline rather than an
    invented absolute.
    """
    scores = [float(r.get("specificity_score") or 0.0) for r in rows
              if r.get("specificity_score") is not None]
    if not scores:
        return {"n": 0, "note": "no specificity scores in the cohort"}
    scores.sort()

    def _q(p: float) -> float:
        if len(scores) == 1:
            return scores[0]
        idx = p * (len(scores) - 1)
        lo = int(idx)
        hi = min(lo + 1, len(scores) - 1)
        return scores[lo] + (scores[hi] - scores[lo]) * (idx - lo)

    return {
        "n": len(scores),
        "median": round(statistics.median(scores), 3),
        "q25": round(_q(0.25), 3),
        "q75": round(_q(0.75), 3),
        "min": round(scores[0], 3),
        "max": round(scores[-1], 3),
        "niche_count": sum(1 for r in rows if r.get("is_niche")),
        # The sorted scores are kept so a token can be placed by RANK.
        # Threshold-based quartiles break on discrete scores: with many
        # tokens tied at the 25th percentile, `score < q25` selects
        # NOTHING and the bottom-quartile bucket comes back empty.
        "sorted_scores": scores,
        "note": ("A token in the cohort's bottom QUARTILE BY RANK is "
                 "'generic relative to its peers'. This is a cohort-derived "
                 "baseline, not an external label."),
    }


def _rank_pct(score: float, baseline: Dict[str, Any]) -> Optional[float]:
    """The percentile RANK of a score within the cohort (ties averaged)."""
    scores = baseline.get("sorted_scores") or []
    n = len(scores)
    if not n:
        return None
    s = float(score)
    lower = sum(1 for v in scores if v < s)
    equal = sum(1 for v in scores if v == s)
    # Average rank among the tied group.
    rank = lower + (equal + 1) / 2.0
    return rank / n


def relative_to_cohort(row: Dict[str, Any],
                        baseline: Dict[str, Any]) -> Dict[str, Any]:
    """Place one token in its cohort's distribution, BY RANK."""
    score = float(row.get("specificity_score") or 0.0)
    b = baseline or {}
    if not b.get("n"):
        return {"relative": "unknown", "note": "no cohort baseline"}
    pct = _rank_pct(score, b)
    if pct is None:
        return {"relative": "unknown", "note": "no cohort baseline"}
    if pct >= 0.75:
        rel = "top quartile"
    elif pct >= 0.50:
        rel = "above median"
    elif pct >= 0.25:
        rel = "below median"
    else:
        rel = "bottom quartile"
    return {
        "relative": rel,
        "rank_pct": round(pct, 3),
        "score": score,
        "cohort_median": b.get("median"),
        "cohort_q25": b.get("q25"),
        "cohort_q75": b.get("q75"),
        "is_generic_vs_peers": rel == "bottom quartile",
    }


# --------------------------------------------------------------------------
# The empirical test of the paper's performance claim
# --------------------------------------------------------------------------


def backward_association(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """BACKWARD association between specificity and 24h performance.

    This uses the price change that ALREADY happened, so it shows whether
    niche tokens have been performing better RECENTLY. It is NOT a
    forward test - a token could be niche because it already ran.
    """
    niche = [r for r in rows if r.get("is_niche")
             and r.get("price_change_24h") is not None]
    generic = [r for r in rows if not r.get("is_niche")
               and r.get("price_change_24h") is not None]
    if len(niche) < 3 or len(generic) < 3:
        return {
            "status": "insufficient sample",
            "n_niche": len(niche), "n_generic": len(generic),
            "note": ("Need at least 3 priced tokens in each bucket to say "
                     "anything; the sample is too small to infer from."),
        }

    def med(xs: List[float]) -> float:
        return float(statistics.median(xs))

    n_med = med([float(r["price_change_24h"]) for r in niche])
    g_med = med([float(r["price_change_24h"]) for r in generic])
    diff = n_med - g_med
    return {
        "status": "computed",
        "direction": "BACKWARD (h24 price change, already realised)",
        "n_niche": len(niche),
        "n_generic": len(generic),
        "median_price_change_24h_niche_pct": round(n_med, 2),
        "median_price_change_24h_generic_pct": round(g_med, 2),
        "difference_pct_points": round(diff, 2),
        "supports_claim": bool(diff > 0),
        "note": ("This is a BACKWARD association on a small free sample. It "
                 "is NOT evidence that niche tokens cause outperformance, "
                 "and it is NOT a forward test. Use verify_cohort() for "
                 "that."),
    }


def save_cohort(rows: Sequence[Dict[str, Any]], path: str = COHORT_PATH
                ) -> Dict[str, Any]:
    """Write a timestamped snapshot so a later run can measure FORWARD returns."""
    import time
    blob = read_json(path) or {"snapshots": []}
    snap = {
        "ts": int(time.time()),
        "n": len(rows),
        "rows": [{
            "mint": r.get("mint"), "symbol": r.get("symbol"),
            "is_niche": r.get("is_niche"),
            "specificity_score": r.get("specificity_score"),
            "price_usd": r.get("price_usd"),
            "price_change_24h": r.get("price_change_24h"),
            "liquidity_usd": r.get("liquidity_usd"),
            "pair_address": r.get("pair_address"),
            "dex": r.get("dex"),
        } for r in rows],
    }
    blob.setdefault("snapshots", []).append(snap)
    blob["snapshots"] = blob["snapshots"][-20:]
    write_json(path, blob)
    return {"path": path, "snapshot_ts": snap["ts"], "n": snap["n"],
            "n_snapshots": len(blob["snapshots"])}


def select_base_rows(snaps: Sequence[Dict[str, Any]],
                     now: Optional[int] = None,
                     min_gap_seconds: int = 3600
                     ) -> tuple:
    """Select, per token, the EARLIEST qualifying observation.

    Two rules, and BOTH the forward test and the CLI that re-prices the
    cohort must use them identically - if they drift apart the CLI prices
    one pool and the test compares it against another:

      1. only snapshots at least `min_gap_seconds` old are eligible;
      2. a row is eligible only if it recorded its POOL ADDRESS. A row
         without one cannot be compared safely, because the only price
         available then came from whichever pool had the most liquidity at
         that moment - comparing that against a pinned pool NOW manufactures
         returns.

    Rule 2 is why this is per-token rather than per-snapshot: a token
    first seen before the pool-address fix was saved can still have a
    LATER snapshot that recorded its pool. Selecting the first row ever
    seen (rather than the first row that recorded a pool) silently drops
    every such token - and, in the observed history, dropped every NICHE
    token, emptying the niche bucket and making the forward test
    uninterpretable.

    Returns (earliest, no_pair) where `earliest` maps mint -> base row
    dict and `no_pair` lists the mints whose eligible rows recorded no
    pool address.
    """
    import time
    if now is None:
        now = int(time.time())
    earliest: Dict[str, Dict[str, Any]] = {}
    no_pair: List[str] = []
    for s in snaps:
        ts = int(s.get("ts", 0))
        if now - ts < min_gap_seconds:
            continue
        for row in s.get("rows", []):
            mint = row.get("mint")
            if not mint or not row.get("price_usd"):
                continue
            if not row.get("pair_address"):
                no_pair.append(mint)
                continue
            prev = earliest.get(mint)
            if prev is None or ts < int(prev.get("ts", 0)):
                earliest[mint] = {"price_usd": row.get("price_usd"),
                                  "ts": ts,
                                  "is_niche": row.get("is_niche"),
                                  "symbol": row.get("symbol"),
                                  "specificity_score": row.get(
                                      "specificity_score"),
                                  "pair_address": row.get("pair_address")}
    return earliest, no_pair


def verify_cohort(path: str = COHORT_PATH, min_gap_seconds: int = 3600,
                  current_rows: Optional[Sequence[Dict[str, Any]]] = None
                  ) -> Dict[str, Any]:
    """Measure FORWARD returns between two snapshots and test the claim.

    Compares the most recent earlier snapshot with the current prices.
    Until two snapshots separated by at least `min_gap_seconds` exist, the
    forward verdict is 'not yet measurable' - never 'no effect'.
    """
    import time
    blob = read_json(path) or {"snapshots": []}
    snaps = blob.get("snapshots") or []
    if current_rows is None:
        return {"status": "no current rows supplied"}
    if len(snaps) < 1:
        return {"status": "not yet measurable",
                "note": "no snapshot saved yet - run save_cohort() first"}

    now = int(time.time())
    # Pick the LARGEST qualifying prior snapshot. Each snapshot holds one
    # query's cohort, so the most recent one can hold a single token -
    # picking it would shrink the matched sample for no reason.
    prior = None
    for s in snaps:
        if now - int(s.get("ts", 0)) < min_gap_seconds:
            continue
        if prior is None or len(s.get("rows") or []) > len(prior.get("rows") or []):
            prior = s
    if prior is None:
        latest = snaps[-1]
        return {"status": "not yet measurable",
                "n_snapshots": len(snaps),
                "latest_snapshot_ts": latest.get("ts"),
                "seconds_since_latest": now - int(latest.get("ts", 0)),
                "min_gap_seconds": min_gap_seconds,
                "note": ("A forward test needs two observations separated by "
                         "time. Save another snapshot once the gap has "
                         "elapsed.")}

    # PER-TOKEN BASE. Each snapshot holds one query's cohort, so a single
    # cohort-wide base matches only that cohort - with 2 niche tokens that
    # is too small to infer from. Matching every token against ITS OWN
    # earliest recorded observation widens the sample to the whole history
    # and gives each token its own forward window, which is reported so
    # the reader can see the spread. The selection rule lives in
    # `select_base_rows` so the CLI that re-prices the cohort cannot pick
    # a different base than this function does.
    earliest, no_pair = select_base_rows(snaps, now=now,
                                         min_gap_seconds=min_gap_seconds)

    fwd: List[Dict[str, Any]] = []
    pair_mismatch = 0
    for r in current_rows:
        mint = r.get("mint")
        base = earliest.get(mint)
        p0 = base.get("price_usd") if base else None
        p1 = r.get("price_usd")
        if not p0 or not p1:
            continue
        # Same pool at both ends.
        want = (base.get("pair_address") or "").lower()
        got = (r.get("pair_address") or "").lower()
        if want and got and want != got:
            pair_mismatch += 1
            continue
        try:
            fwd.append({"mint": mint, "symbol": r.get("symbol"),
                        "forward_return_pct": (float(p1) / float(p0) - 1.0) * 100.0,
                        "is_niche": r.get("is_niche"),
                        "window_seconds": now - int(base.get("ts", 0)),
                        "base_price_usd": p0})
        except (TypeError, ValueError, ZeroDivisionError):
            continue
    niche = [f["forward_return_pct"] for f in fwd if f.get("is_niche")]
    generic = [f["forward_return_pct"] for f in fwd if not f.get("is_niche")]
    windows = [f["window_seconds"] for f in fwd]
    out: Dict[str, Any] = {
        "status": "computed",
        "direction": "FORWARD",
        "base": "each token's own earliest recorded price",
        "prior_snapshot_ts": prior.get("ts"),
        "seconds_elapsed": now - int(prior.get("ts", 0)),
        "n_matched": len(fwd),
        "n_niche": len(niche), "n_generic": len(generic),
        "window_seconds_min": min(windows) if windows else None,
        "window_seconds_max": max(windows) if windows else None,
        "median_window_seconds": (int(statistics.median(windows))
                                  if windows else None),
        "skipped_no_pair_address": len(no_pair),
        "skipped_no_pair_address_distinct_tokens": len(set(no_pair)),
        "skipped_pair_mismatch": pair_mismatch,
        "matched": [{"symbol": f.get("symbol"),
                     "niche": f.get("is_niche"),
                     "forward_return_pct": round(f["forward_return_pct"], 2),
                     "window_seconds": f["window_seconds"]}
                    for f in sorted(fwd,
                                    key=lambda x: -x["forward_return_pct"])],
    }
    if len(niche) >= 3 and len(generic) >= 3:
        n_med = float(statistics.median(niche))
        g_med = float(statistics.median(generic))
        out.update({
            "median_forward_return_niche_pct": round(n_med, 2),
            "median_forward_return_generic_pct": round(g_med, 2),
            "difference_pct_points": round(n_med - g_med, 2),
            "supports_claim": bool(n_med > g_med),
            "note": ("FORWARD returns on a small free sample. Each token "
                     "uses its own forward window, so the windows differ "
                     "(see window_seconds). This is evidence about THIS "
                     "sample, not a general law."),
        })
    else:
        out["note"] = ("fewer than 3 matched tokens in one bucket - not "
                        "enough to infer from")
        out["supports_claim"] = None
    if no_pair:
        out["skipped_reason"] = (
            f"{len(no_pair)} snapshot ROW(s) across "
            f"{len(set(no_pair))} distinct token(s) recorded no PAIR "
            f"ADDRESS. Those snapshots predate the same-pool fix, and "
            f"comparing them against a different pool would manufacture "
            f"returns. A token is only EXCLUDED from the measurement if "
            f"no snapshot of it recorded a pool; a token whose later "
            f"snapshot did record one is measured from that snapshot.")
    return out
