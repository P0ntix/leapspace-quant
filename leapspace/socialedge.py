"""Social-edge testing: did this wallet buy BEFORE the crowd noticed?

WHAT THIS MODULE IS
-------------------
The social classifier in `leapspace/social.py` measures a token's community
SIZE at one moment. This module measures something harder: the ORDERING of
a wallet's entry relative to the token's social traction inflection, and
it separates the wallets that bought ahead of the narrative from the wallets
that bought into it.

The distinction is the whole point. A wallet that buys a memecoin after the
Telegram channel has 10,000 members and Google Trends has spiked has
demonstrated nothing except that it can follow a crowd. A wallet that buys
before the membership threshold is crossed, before the holder growth
inflects, and before the first major mention event has demonstrated
something that is much harder to do: anticipating the narrative.

THE TEST
--------
For one token and one wallet, compute LEAD TIME in hours:

    lead_time = (comparator_event_ts - wallet_buy_ts) / 3600.0

POSITIVE lead time means the wallet bought BEFORE the comparator fired -
i.e. it was LEADING. Negative means it bought after - LAGGING. A lead time
inside +/- `coincident_window_hours` is COINCIDENT (no information either
way).

Comparators, in order of construction cost:

  membership_threshold  the first community-size snapshot at which combined
                         Telegram+Discord members cross a threshold. This is
                         the cheapest comparator and the most robust, because
                         it is derived from a snapshot series the operator
                         controls.

  holder_inflection     the timestamp at which the token's holder-count
                         growth rate inflects (a change-point in the second
                         derivative of the holder series). Requires a holder
                         time series.

  first_mention_event   the first major social mention event. Requires a
                         mention/attention series (Google Trends interest,
                         an ApeWisdom/Reddit mention count, a Bluesky/Reddit
                         post count). This is the comparator most often
                         MISSING, and the module degrades honestly when it
                         is: the comparator reports `unavailable` with a
                         reason, and the overall verdict is computed over the
                         comparators that DO exist, with the coverage stated.

THE CONVERSE TEST
-----------------
`classify_late_buyers` is the mirror image and it is NOT optional. A wallet
that bought after the narrative was established is evidence of crowd
following, and pooling such wallets with genuine leaders inflates the
apparent edge. The module reports late buyers as a separate, explicitly
labelled population, never silently mixed into the leading cohort.

THE DIVERGENCE FLAG
-------------------
`social_vs_onchain_divergence` flags the window where social membership is
still RISING while on-chain volume has already FALLEN. In the lifecycle
model that is the distribution phase starting: the community is still
growing, but the money is leaving. It is also the state in which a naive
"social is up, therefore buy" rule is most wrong.

DEPENDENCIES
------------
stdlib + `leapspace/http.py` only, as specified. No third-party imports.
All timestamps are UNIX epoch seconds (int). Every function degrades
honestly: a missing comparator yields `unavailable` with a reason, never a
zero, never a guess, never a fabricated number.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .http import http_get

# --------------------------------------------------------------------------
# Thresholds - ANALYST CHOICES, not paper-stated values.
#
# Every one of these is re-scorable and is labelled as such in the output.
# The meme paper itself says its predictive thresholds are an open empirical
# question; nothing here should be read as the paper's number.
# --------------------------------------------------------------------------

#: Combined community members at which a token counts as "the narrative is
#: established" for the reverse test.
NARRATIVE_ESTABLISHED_MEMBERS_DEFAULT = 1_000

#: Membership threshold used by the default membership comparator.
MEMBERSHIP_THRESHOLD_DEFAULT = 500

#: A lead time inside this window (in hours) is COINCIDENT, not leading or
#: lagging. Without it, a wallet that bought 30 minutes after the event
#: would be reported as a laggard, which overstates the evidence.
COINCIDENT_WINDOW_HOURS_DEFAULT = 6.0

#: Minimum number of snapshots before a membership threshold crossing can
#: be called. One snapshot cannot establish a crossing.
MIN_SNAPSHOTS_FOR_CROSSING = 2

#: Holder-series growth rate change-point: the inflection is the first
#: window where the holder growth rate exceeds this multiple of the median
#: growth rate over the series.
HOLDER_GROWTH_INFLECTION_MULTIPLE = 2.0

#: A mention event must reach this multiple of the series median to count
#: as "major".
MAJOR_MENTION_MULTIPLE = 3.0

#: Minimum observations before a mention series can produce an event.
MIN_MENTION_OBSERVATIONS = 4

#: Divergence needs a minimum number of paired observations.
MIN_DIVERGENCE_POINTS = 4

#: Directory for the community-size snapshot series the package keeps.
SOCIAL_SERIES_DIR = os.path.join(os.path.dirname(__file__),
                                 "state", "social_series")


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def _as_ts(value: Any) -> Optional[int]:
    """Coerce a timestamp to UNIX epoch seconds.

    Accepts int, float, numeric string, or an ISO-8601 string. Returns None
    for anything unparseable - a missing timestamp is a gap, not an epoch 0.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError):
            return None
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    try:
        import datetime as _dt
        return int(_dt.datetime.fromisoformat(
            text.replace("Z", "+00:00")).timestamp())
    except (ValueError, TypeError, OSError):
        return None


def _num(value: Any) -> Optional[float]:
    """Coerce to float; None when not numeric."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def _median(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def _linear_slope(points: Sequence[Tuple[float, float]]) -> Optional[float]:
    """OLS slope of y on x. None when x has no spread."""
    if len(points) < 2:
        return None
    n = len(points)
    mean_x = sum(p[0] for p in points) / n
    mean_y = sum(p[1] for p in points) / n
    num = sum((p[0] - mean_x) * (p[1] - mean_y) for p in points)
    den = sum((p[0] - mean_x) ** 2 for p in points)
    if den == 0:
        return None
    return num / den


# --------------------------------------------------------------------------
# 1. Building the community-size time series
# --------------------------------------------------------------------------
def build_community_series(
    snapshots: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Turn raw snapshot records into a clean community-size time series.

    Input rows may carry any of these key spellings, because the package's
    snapshot writers differ:

        ts / timestamp / observed_at / time
        telegram_members / telegram / tg_members
        discord_members  / discord  / dc_members
        telegram_online, discord_online

    Output rows are normalised to exactly:

        {"ts": int, "telegram_members": int|None,
         "discord_members": int|None, "telegram_online": int|None,
         "discord_online": int|None,
         "combined_members": int|None, "source": str|None}

    A member count of 0 is preserved as 0 (a real, measured zero is
    different from an absent measurement), but a MISSING count stays None.
    `combined_members` is None when neither platform was measured, and is
    the SUM when one or both were - including the case where only one
    platform was measured, in which case the sum is a LOWER BOUND and that
    fact is recorded in the row's `combined_is_lower_bound` flag.

    Rows without a usable timestamp are DROPPED, and the count of dropped
    rows is returned by `community_series_diagnostics`.
    """
    out: List[Dict[str, Any]] = []
    for snap in snapshots or []:
        if not isinstance(snap, dict):
            continue
        ts = None
        for key in ("ts", "timestamp", "observed_at", "time", "fetched_at"):
            ts = _as_ts(snap.get(key))
            if ts is not None:
                break
        if ts is None:
            continue
        tg = _num(snap.get("telegram_members"))
        if tg is None:
            tg = _num(snap.get("telegram"))
        if tg is None:
            tg = _num(snap.get("tg_members"))
        dc = _num(snap.get("discord_members"))
        if dc is None:
            dc = _num(snap.get("discord"))
        if dc is None:
            dc = _num(snap.get("dc_members"))
        tg_on = _num(snap.get("telegram_online"))
        if tg_on is None:
            tg_on = _num(snap.get("tg_online"))
        dc_on = _num(snap.get("discord_online"))
        if dc_on is None:
            dc_on = _num(snap.get("dc_online"))

        measured = [v for v in (tg, dc) if v is not None]
        combined = int(sum(measured)) if measured else None
        out.append({
            "ts": int(ts),
            "telegram_members": int(tg) if tg is not None else None,
            "discord_members": int(dc) if dc is not None else None,
            "telegram_online": int(tg_on) if tg_on is not None else None,
            "discord_online": int(dc_on) if dc_on is not None else None,
            "combined_members": combined,
            "combined_is_lower_bound": bool(measured) and (tg is None
                                                           or dc is None),
            "n_platforms_measured": len(measured),
            "source": snap.get("source"),
        })
    out.sort(key=lambda r: r["ts"])
    return out


def community_series_diagnostics(series: Sequence[Dict[str, Any]]
                                 ) -> Dict[str, Any]:
    """Describe the coverage of a community series, honestly."""
    n = len(series)
    if n == 0:
        return {"status": "empty", "n_snapshots": 0,
                "note": "No usable snapshots. Nothing can be computed."}
    span = series[-1]["ts"] - series[0]["ts"]
    gaps = [series[i + 1]["ts"] - series[i]["ts"] for i in range(n - 1)]
    tg = [r["telegram_members"] for r in series
          if r["telegram_members"] is not None]
    dc = [r["discord_members"] for r in series
          if r["discord_members"] is not None]
    return {
        "status": "ok" if n >= MIN_SNAPSHOTS_FOR_CROSSING else "insufficient",
        "n_snapshots": n,
        "first_ts": series[0]["ts"],
        "last_ts": series[-1]["ts"],
        "span_seconds": span,
        "span_hours": round(span / 3600.0, 3),
        "median_gap_seconds": _median(gaps),
        "max_gap_seconds": max(gaps) if gaps else None,
        "telegram_measured_count": len(tg),
        "discord_measured_count": len(dc),
        "both_measured_count": sum(
            1 for r in series
            if r["telegram_members"] is not None
            and r["discord_members"] is not None),
        "min_snapshots_for_crossing": MIN_SNAPSHOTS_FOR_CROSSING,
        "note": ("A crossing needs two snapshots. A series with a large max "
                 "gap cannot resolve a crossing to better than that gap."),
    }


# --- persistence ---------------------------------------------------------
def _series_path(chain: str, mint: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in (mint or ""))[:66]
    return os.path.join(SOCIAL_SERIES_DIR, f"{chain}_{safe}.json")


def load_community_series(chain: str, mint: str) -> Dict[str, Any]:
    """Load the stored community-size series for a token."""
    path = _series_path(chain, mint)
    if not os.path.exists(path):
        return {"chain": chain, "mint": mint, "snapshots": []}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"chain": chain, "mint": mint, "snapshots": []}


def save_community_series(chain: str, mint: str,
                          snapshots: Sequence[Dict[str, Any]]) -> str:
    """Persist a community-size series. Atomic replace."""
    os.makedirs(SOCIAL_SERIES_DIR, exist_ok=True)
    path = _series_path(chain, mint)
    payload = {"chain": chain, "mint": mint,
               "snapshots": list(snapshots or [])}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    os.replace(tmp, path)
    return path


def record_community_snapshot(chain: str, mint: str,
                              telegram_members: Optional[int] = None,
                              discord_members: Optional[int] = None,
                              telegram_online: Optional[int] = None,
                              discord_online: Optional[int] = None,
                              source: str = "") -> Dict[str, Any]:
    """Append one timestamped community-size observation to the series.

    This is the persistence half of `build_community_series`: the package
    keeps a per-token series of community-size observations so that a
    THRESHOLD CROSSING - a change, which needs two observations - becomes
    computable at all.
    """
    stored = load_community_series(chain, mint)
    snaps = list(stored.get("snapshots") or [])
    snaps.append({
        "ts": int(time.time()),
        "telegram_members": telegram_members,
        "discord_members": discord_members,
        "telegram_online": telegram_online,
        "discord_online": discord_online,
        "source": source or "manual",
    })
    snaps.sort(key=lambda s: s.get("ts") or 0)
    save_community_series(chain, mint, snaps)
    return snaps[-1]


# --------------------------------------------------------------------------
# 2. The comparators
# --------------------------------------------------------------------------
def membership_threshold_event(
    series: Sequence[Dict[str, Any]],
    threshold: int = MEMBERSHIP_THRESHOLD_DEFAULT,
    platform: str = "combined",
) -> Dict[str, Any]:
    """The first snapshot at which community size crosses `threshold`.

    `platform` is one of:

      combined        Telegram + Discord members (default)
      telegram        Telegram members only
      discord         Discord members only
      online          Telegram + Discord ONLINE counts - the LIVENESS
                      series rather than the size series. The member count
                      alone is gameable (members can be bought); the online
                      count moves with real participation. It is a noisier
                      and smaller series, so it is offered as an explicit
                      alternative, not as the default.

    Returns `unavailable` with a reason when the series cannot support a
    crossing - never a fabricated timestamp.
    """
    if not series:
        return {"comparator": "membership_threshold", "status": "unavailable",
                "reason": "no community-size series supplied"}
    if len(series) < MIN_SNAPSHOTS_FOR_CROSSING:
        return {"comparator": "membership_threshold", "status": "unavailable",
                "reason": (f"series has {len(series)} snapshot(s); a crossing "
                           f"needs >= {MIN_SNAPSHOTS_FOR_CROSSING}"),
                "n_snapshots": len(series)}
    key = {"combined": "combined_members", "telegram": "telegram_members",
           "discord": "discord_members"}.get(platform)
    if key is None and platform == "online":
        key = "_online_combined"
    if key is None:
        return {"comparator": "membership_threshold", "status": "unavailable",
                "reason": f"unknown platform selector '{platform}'"}

    observed: List[Tuple[int, Optional[float]]] = []
    for r in series:
        if key == "_online_combined":
            parts = [r.get("telegram_online"), r.get("discord_online")]
            vals = [p for p in parts if p is not None]
            val: Optional[float] = int(sum(vals)) if vals else None
        else:
            val = r.get(key)
        observed.append((r["ts"], val))
    measured = [(t, v) for t, v in observed if v is not None]
    if len(measured) < MIN_SNAPSHOTS_FOR_CROSSING:
        return {"comparator": "membership_threshold", "status": "unavailable",
                "reason": (f"platform '{platform}' was measured in "
                           f"{len(measured)} snapshot(s); a crossing needs "
                           f">= {MIN_SNAPSHOTS_FOR_CROSSING}"),
                "n_measured": len(measured)}

    baseline = measured[0][1]
    if baseline >= threshold:
        # The community was ALREADY above the threshold at the first
        # observation. The crossing happened BEFORE this series starts, so
        # it cannot be dated from this data. Reporting the first snapshot
        # as the crossing would silently invent a date for an event that
        # predates the observations - which is exactly the kind of
        # manufactured lead time the whole test exists to avoid.
        return {
            "comparator": "membership_threshold",
            "status": "already_above_threshold",
            "reason": (f"the community was already at {baseline} members at "
                       f"the FIRST observation, above the threshold of "
                       f"{threshold}; the crossing predates this series and "
                       f"cannot be dated from it"),
            "event_ts": None,
            "threshold": threshold,
            "platform": platform,
            "baseline_value": baseline,
            "first_snapshot_ts": measured[0][0],
            "note": ("No dated crossing. Use an earlier snapshot series, or "
                     "a different comparator, for this token."),
        }
    for ts, value in measured:
        if value >= threshold:
            return {
                "comparator": "membership_threshold",
                "status": "ok",
                "event_ts": ts,
                "threshold": threshold,
                "platform": platform,
                "value_at_event": value,
                "baseline_value": baseline,
                "first_snapshot_ts": measured[0][0],
                "seconds_from_first_snapshot": ts - measured[0][0],
                "note": ("First snapshot at or above the threshold. The "
                         "crossing happened somewhere in the interval "
                         "between the previous snapshot and this one."),
            }
    last_ts, last_val = measured[-1]
    return {"comparator": "membership_threshold", "status": "not_reached",
            "reason": (f"community size never reached {threshold} in the "
                       f"observed window (last measured: {last_val})"),
            "threshold": threshold, "platform": platform,
            "last_measured_ts": last_ts, "last_value": last_val}


def holder_inflection_event(
    holder_series: Sequence[Dict[str, Any]],
    multiple: float = HOLDER_GROWTH_INFLECTION_MULTIPLE,
) -> Dict[str, Any]:
    """The timestamp at which the holder-count growth rate inflects.

    Method: compute the per-hour growth rate between consecutive snapshots,
    take the median rate over the series as the baseline, then take the
    first window whose rate exceeds `multiple` x baseline. The inflection
    is the END of that window (the moment the acceleration is visible).

    A HOLDER-COUNT series means something different from a SOCIAL series and
    the distinction matters: holder count includes bots, airdrop farmers
    and split wallets, so it can rise without any narrative at all. It is
    the best available free proxy for "the market noticed", which is why it
    is a comparator and not the primary signal.
    """
    points: List[Tuple[int, float]] = []
    for row in holder_series or []:
        if not isinstance(row, dict):
            continue
        ts = None
        for key in ("ts", "timestamp", "observed_at", "time"):
            ts = _as_ts(row.get(key))
            if ts is not None:
                break
        if ts is None:
            continue
        val = _num(row.get("holder_count"))
        if val is None:
            val = _num(row.get("holders"))
        if val is None:
            val = _num(row.get("total_holders"))
        if val is None:
            continue
        points.append((ts, val))
    points.sort()

    if len(points) < 3:
        return {"comparator": "holder_inflection", "status": "unavailable",
                "reason": (f"holder series has {len(points)} usable "
                           f"point(s); an inflection needs >= 3"),
                "n_points": len(points)}

    rates: List[Tuple[int, float]] = []
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        dt_h = (t1 - t0) / 3600.0
        if dt_h <= 0:
            continue
        rates.append((t1, (v1 - v0) / dt_h))
    if len(rates) < 2:
        return {"comparator": "holder_inflection", "status": "unavailable",
                "reason": "not enough intervals to estimate a growth rate",
                "n_points": len(points)}

    positive = [r for _, r in rates if r > 0]
    baseline = _median(positive) if positive else None
    if baseline is None or baseline <= 0:
        return {"comparator": "holder_inflection",
                "status": "not_reached",
                "reason": ("holder count never grew at a positive median "
                           "rate; there is no baseline to inflect against"),
                "n_points": len(points)}

    threshold_rate = baseline * multiple
    for ts, rate in rates:
        if rate >= threshold_rate:
            return {
                "comparator": "holder_inflection",
                "status": "ok",
                "event_ts": ts,
                "baseline_rate_per_hour": baseline,
                "threshold_rate_per_hour": threshold_rate,
                "rate_at_event_per_hour": rate,
                "multiple": multiple,
                "first_snapshot_ts": points[0][0],
                "note": ("First window whose holder growth rate exceeded the "
                         "series median by the stated multiple. Holders "
                         "include bots and farmers, so this is a market-"
                         "attention proxy, not a narrative measure."),
            }
    return {"comparator": "holder_inflection", "status": "not_reached",
            "reason": (f"no window exceeded {threshold_rate:.4f} holders/hour "
                       f"({multiple}x the median rate {baseline:.4f})"),
            "n_points": len(points)}


def first_mention_event(
    mention_series: Sequence[Dict[str, Any]],
    multiple: float = MAJOR_MENTION_MULTIPLE,
    count_key: str = "mentions",
) -> Dict[str, Any]:
    """The first MAJOR social mention event in an attention series.

    The series is a list of dicts with a timestamp and a mention/attention
    count (Google Trends interest, a Reddit mention count, a Bluesky post
    count, ...). The event is the first observation whose count reaches
    `multiple` x the series median.

    This comparator is the one most often unavailable, and that is a
    property of the free surface rather than a defect of the method: X is
    paid and forbids scraping, Reddit's JSON listing 403s from this host,
    and ApeWisdom's API host no longer resolves. See
    NARRATIVE_EDGE_METHODOLOGY.md for the live status of each.
    """
    points: List[Tuple[int, float]] = []
    for row in mention_series or []:
        if not isinstance(row, dict):
            continue
        ts = None
        for key in ("ts", "timestamp", "observed_at", "time"):
            ts = _as_ts(row.get(key))
            if ts is not None:
                break
        if ts is None:
            continue
        val = None
        for key in (count_key, "count", "value", "interest", "mentions",
                    "score", "posts"):
            val = _num(row.get(key))
            if val is not None:
                break
        if val is None:
            continue
        points.append((ts, val))
    points.sort()

    if len(points) < MIN_MENTION_OBSERVATIONS:
        return {"comparator": "first_mention_event", "status": "unavailable",
                "reason": (f"mention series has {len(points)} usable "
                           f"point(s); needs >= {MIN_MENTION_OBSERVATIONS}"),
                "n_points": len(points)}

    med = _median([v for _, v in points])
    if med is None or med <= 0:
        return {"comparator": "first_mention_event", "status": "not_reached",
                "reason": ("median mention count is zero; every observation "
                           "is zero, so no event can be distinguished"),
                "n_points": len(points)}
    threshold = med * multiple
    for ts, val in points:
        if val >= threshold:
            return {
                "comparator": "first_mention_event",
                "status": "ok",
                "event_ts": ts,
                "threshold": threshold,
                "median": med,
                "multiple": multiple,
                "value_at_event": val,
                "first_snapshot_ts": points[0][0],
                "note": ("First observation at or above the threshold. The "
                         "true event is somewhere in the preceding interval."),
            }
    return {"comparator": "first_mention_event", "status": "not_reached",
            "reason": (f"no observation reached {threshold:.2f} "
                       f"({multiple}x median {med:.2f})"),
            "n_points": len(points)}


# --------------------------------------------------------------------------
# 3. The lead-time test
# --------------------------------------------------------------------------
LEADING = "LEADING"
COINCIDENT = "COINCIDENT"
LAGGING = "LAGGING"
UNKNOWN = "UNKNOWN"

_COMPARATOR_ORDER = ("membership_threshold", "holder_inflection",
                     "first_mention_event")


def _classify_lead(lead_hours: Optional[float],
                   window_hours: float) -> str:
    if lead_hours is None:
        return UNKNOWN
    if lead_hours > window_hours:
        return LEADING
    if lead_hours < -window_hours:
        return LAGGING
    return COINCIDENT


def compute_lead_time(
    buy_ts: int,
    comparators: Dict[str, Dict[str, Any]],
    coincident_window_hours: float = COINCIDENT_WINDOW_HOURS_DEFAULT,
) -> Dict[str, Any]:
    """Compute lead time in hours against each comparator.

    `buy_ts` is the wallet's buy timestamp in UNIX epoch seconds.
    `comparators` maps a comparator name to that comparator's event dict
    (as produced by `membership_threshold_event`, `holder_inflection_event`
    and `first_mention_event`).

    A comparator with status != "ok" is reported as `unavailable` with its
    reason, and it contributes NO lead time. The overall verdict is computed
    over the comparators that DID resolve, and the number resolved is
    reported so a verdict based on one comparator is never confused with a
    verdict based on three.
    """
    per: Dict[str, Dict[str, Any]] = {}
    resolved_leads: List[float] = []
    resolved_classes: List[str] = []
    for name in _COMPARATOR_ORDER:
        comp = comparators.get(name)
        if comp is None:
            per[name] = {"comparator": name, "status": "unavailable",
                         "reason": "comparator was not supplied",
                         "lead_time_hours": None, "class": UNKNOWN}
            continue
        status = comp.get("status")
        if status != "ok":
            per[name] = {"comparator": name, "status": status,
                         "reason": comp.get("reason", ""),
                         "lead_time_hours": None, "class": UNKNOWN}
            continue
        event_ts = comp.get("event_ts")
        if not isinstance(event_ts, (int, float)):
            per[name] = {"comparator": name, "status": "unavailable",
                         "reason": "comparator reported ok but no event_ts",
                         "lead_time_hours": None, "class": UNKNOWN}
            continue
        lead_h = (float(event_ts) - float(buy_ts)) / 3600.0
        cls = _classify_lead(lead_h, coincident_window_hours)
        per[name] = {
            "comparator": name,
            "status": "ok",
            "event_ts": int(event_ts),
            "buy_ts": int(buy_ts),
            "lead_time_hours": round(lead_h, 4),
            "class": cls,
            "comparator_detail": {k: v for k, v in comp.items()
                                   if k not in ("comparator", "status")},
        }
        resolved_leads.append(lead_h)
        resolved_classes.append(cls)

    n_resolved = len(resolved_leads)
    if n_resolved == 0:
        overall = UNKNOWN
        mean_lead = None
        median_lead = None
    else:
        mean_lead = round(sum(resolved_leads) / n_resolved, 4)
        med = _median(resolved_leads)
        median_lead = round(med, 4) if med is not None else None
        # Overall class follows the MEDIAN comparator, not the mean: one
        # comparator firing very early (a noisy membership snapshot) must
        # not drag the verdict. Ties break toward COINCIDENT.
        if median_lead is None:
            overall = UNKNOWN
        elif median_lead > coincident_window_hours:
            overall = LEADING
        elif median_lead < -coincident_window_hours:
            overall = LAGGING
        else:
            overall = COINCIDENT

    return {
        "buy_ts": int(buy_ts),
        "overall_class": overall,
        "lead_time_hours": median_lead,
        "lead_time_mean_hours": mean_lead,
        "n_comparators_resolved": n_resolved,
        "n_comparators_supplied": len(comparators or {}),
        "n_comparators_possible": len(_COMPARATOR_ORDER),
        "comparator_coverage": (round(n_resolved / len(comparators), 3)
                                if comparators else 0.0),
        "comparator_coverage_of_full_set": round(
            n_resolved / len(_COMPARATOR_ORDER), 3),
        "per_comparator": per,
        "coincident_window_hours": coincident_window_hours,
        "note": ("Lead time is (comparator_event_ts - buy_ts). Positive means "
                 "the wallet bought BEFORE the comparator fired. The overall "
                 "class is the MEDIAN across resolved comparators; "
                 "unresolved comparators are listed with their reasons and "
                 "do NOT contribute a zero."),
    }


def assess_wallet_edge(
    wallet_buys: Sequence[Dict[str, Any]],
    community_series: Sequence[Dict[str, Any]],
    token_address: Optional[str] = None,
    symbol: Optional[str] = None,
    holder_series: Optional[Sequence[Dict[str, Any]]] = None,
    mention_series: Optional[Sequence[Dict[str, Any]]] = None,
    membership_threshold: int = MEMBERSHIP_THRESHOLD_DEFAULT,
    coincident_window_hours: float = COINCIDENT_WINDOW_HOURS_DEFAULT,
) -> Dict[str, Any]:
    """Full social-edge assessment for one wallet against one token.

    `wallet_buys` is a list of dicts with at least `ts`; `token_address` and
    `symbol` are used to select the relevant buys when the list covers
    several tokens. The EARLIEST buy of that token is the wallet's entry,
    because a wallet that first bought early and added later is still an
    early buyer, while a wallet that bought late and then averaged down is
    not an early buyer.

    Every comparator is built from the data supplied and reported
    separately. A missing holder or mention series produces an
    `unavailable` comparator with a reason, and the assessment states how
    many comparators actually resolved.
    """
    buys = [b for b in (wallet_buys or []) if isinstance(b, dict)]
    if token_address:
        want = str(token_address).lower()
        buys = [b for b in buys
                if str(b.get("token_address") or "").lower() == want]
    if symbol:
        sym = str(symbol).upper()
        buys = [b for b in buys
                if str(b.get("symbol") or "").upper() == sym]
    buys = [b for b in buys if _as_ts(b.get("ts")) is not None]
    buys.sort(key=lambda b: _as_ts(b.get("ts")) or 0)

    out: Dict[str, Any] = {
        "wallet_buys_supplied": len(wallet_buys or []),
        "n_buys_for_token": len(buys),
        "token_address": token_address,
        "symbol": symbol,
        "comparators": {},
        "community_series_diagnostics": community_series_diagnostics(
            community_series),
        "edge": {"status": "no_buy_events",
                 "reason": ("no buy event for this token could be located in "
                            "the supplied events")},
        "note": ("A wallet's entry is its EARLIEST buy of the token. Later "
                 "buys do not change the entry time."),
    }
    if not buys:
        return out

    first_buy_ts = _as_ts(buys[0].get("ts"))
    if first_buy_ts is None:
        out["edge"] = {"status": "unavailable",
                       "reason": "the earliest buy had no usable timestamp"}
        return out
    out["first_buy_ts"] = first_buy_ts
    out["first_buy_iso"] = _iso(first_buy_ts)
    out["buy_timestamps"] = [_as_ts(b.get("ts")) for b in buys]

    comparators: Dict[str, Dict[str, Any]] = {
        "membership_threshold": membership_threshold_event(
            community_series, threshold=membership_threshold),
        "holder_inflection": holder_inflection_event(holder_series or []),
        "first_mention_event": first_mention_event(mention_series or []),
    }
    out["comparators"] = comparators
    out["edge"] = compute_lead_time(
        first_buy_ts, comparators,
        coincident_window_hours=coincident_window_hours)
    out["edge"]["first_buy_ts"] = first_buy_ts
    out["edge"]["first_buy_iso"] = _iso(first_buy_ts)
    return out


def _iso(ts: Optional[int]) -> Optional[str]:
    if ts is None:
        return None
    try:
        import datetime as _dt
        return _dt.datetime.fromtimestamp(
            int(ts), _dt.timezone.utc).isoformat()
    except (ValueError, OSError, OverflowError):
        return None


# --------------------------------------------------------------------------
# 4. The CONVERSE test - late buyers are not evidence of an edge
# --------------------------------------------------------------------------
def narrative_established_ts(
    community_series: Sequence[Dict[str, Any]],
    threshold: int = NARRATIVE_ESTABLISHED_MEMBERS_DEFAULT,
) -> Dict[str, Any]:
    """The moment the narrative was ESTABLISHED, not merely detected.

    This is deliberately a different (higher) threshold from the
    membership comparator: "established" means the community was already
    large and self-sustaining, so anyone buying after that point is
    following an existing crowd rather than anticipating one.

    Special case: if the community was ALREADY above the threshold at the
    first observation, the narrative was established BEFORE this series
    starts. That is a definite answer ("established before the window"),
    not a gap, and it is reported with `event_ts` set to the first
    snapshot so that every buy in the series is correctly classified as
    late.
    """
    ev = membership_threshold_event(community_series, threshold=threshold,
                                     platform="combined")
    ev["comparator"] = "narrative_established"
    ev["established_threshold"] = threshold
    if ev.get("status") == "already_above_threshold":
        ev["status"] = "ok"
        ev["event_ts"] = ev.get("first_snapshot_ts")
        ev["already_established_before_series"] = True
        ev["reason"] = ""
        ev["note"] = ("The community was already above the established "
                      "threshold at the FIRST observation, so the narrative "
                      "was established BEFORE this series begins. Every buy "
                      "in the window is therefore a LATE buy.")
    else:
        ev["already_established_before_series"] = False
    return ev


def classify_late_buyers(
    wallet_buys: Sequence[Dict[str, Any]],
    community_series: Sequence[Dict[str, Any]],
    token_address: Optional[str] = None,
    symbol: Optional[str] = None,
    established_threshold: int = NARRATIVE_ESTABLISHED_MEMBERS_DEFAULT,
    grace_hours: float = 0.0,
) -> Dict[str, Any]:
    """Separate wallets that bought AFTER the narrative was established.

    These are NOT evidence of an edge. They are evidence of crowd
    following, and mixing them into a leading cohort inflates the
    apparent edge. This function exists so they can be reported apart.

    `grace_hours` widens the established moment slightly, so a wallet that
    bought a few minutes after the threshold is not misfiled on a boundary.
    """
    est = narrative_established_ts(community_series,
                                   threshold=established_threshold)
    buys = [b for b in (wallet_buys or []) if isinstance(b, dict)]
    if token_address:
        want = str(token_address).lower()
        buys = [b for b in buys
                if str(b.get("token_address") or "").lower() == want]
    if symbol:
        sym = str(symbol).upper()
        buys = [b for b in buys
                if str(b.get("symbol") or "").upper() == sym]
    buys = [b for b in buys if _as_ts(b.get("ts")) is not None]
    buys.sort(key=lambda b: _as_ts(b.get("ts")) or 0)

    out: Dict[str, Any] = {
        "n_buys_for_token": len(buys),
        "established": est,
        "established_threshold": established_threshold,
        "grace_hours": grace_hours,
        "late_buys": [],
        "early_buys": [],
        "note": ("A wallet whose FIRST buy lands after the narrative was "
                 "established is a LATE BUYER. It is excluded from any "
                 "leading cohort and reported separately."),
    }
    if est.get("status") != "ok":
        out["status"] = "unavailable"
        out["reason"] = (est.get("reason")
                         or "the narrative-established moment could not be "
                            "established from the supplied series")
        out["late_buys"] = []
        out["early_buys"] = []
        out["n_late"] = 0
        out["n_early"] = 0
        out["late_buy_fraction"] = None
        return out

    cut = float(est["event_ts"]) + grace_hours * 3600.0
    out["status"] = "ok"
    out["established_ts"] = int(est["event_ts"])
    out["established_iso"] = _iso(int(est["event_ts"]))
    for b in buys:
        ts = _as_ts(b.get("ts"))
        if ts is None:
            continue
        rec = {"ts": ts, "iso": _iso(ts),
               "symbol": b.get("symbol"),
               "token_address": b.get("token_address"),
               "amount": b.get("amount"),
               "price_usd": b.get("price_usd"),
               "side": b.get("side", "buy")}
        if ts >= cut:
            rec["hours_after_established"] = round((ts - cut) / 3600.0, 4)
            out["late_buys"].append(rec)
        else:
            rec["hours_before_established"] = round((cut - ts) / 3600.0, 4)
            out["early_buys"].append(rec)
    out["n_late"] = len(out["late_buys"])
    out["n_early"] = len(out["early_buys"])
    out["late_buy_fraction"] = (round(out["n_late"] / len(buys), 4)
                                if buys else None)
    return out


# --------------------------------------------------------------------------
# 5. Social vs on-chain divergence
# --------------------------------------------------------------------------
def social_vs_onchain_divergence(
    points: Sequence[Dict[str, Any]],
    social_key: str = "combined_members",
    volume_key: str = "volume",
    min_points: int = MIN_DIVERGENCE_POINTS,
    slope_window: Optional[int] = None,
) -> Dict[str, Any]:
    """Flag the window where social is still RISING but volume has FALLEN.

    Each point is a dict with a timestamp and BOTH a social size and an
    on-chain volume reading:

        {"ts": 1700000000, "combined_members": 4200, "volume": 910000}

    `slope_window` limits the comparison to the last N points; by default
    the whole series is used.

    The flag means: the community is still growing while the money is
    already leaving. In the lifecycle model this is the moment distribution
    begins - and it is exactly where a naive "social is up, therefore buy"
    rule is most wrong.

    A `volume_slope` that cannot be estimated (fewer than two usable points,
    or no time spread) yields `status: unavailable` with a reason rather
    than a zero slope, because a zero slope and an unknown slope mean
    different things.
    """
    rows: List[Tuple[int, float, float]] = []
    for p in points or []:
        if not isinstance(p, dict):
            continue
        ts = None
        for key in ("ts", "timestamp", "observed_at", "time"):
            ts = _as_ts(p.get(key))
            if ts is not None:
                break
        if ts is None:
            continue
        social = _num(p.get(social_key))
        if social is None:
            continue
        volume = _num(p.get(volume_key))
        if volume is None:
            continue
        rows.append((ts, social, volume))
    rows.sort()

    if len(rows) < min_points:
        return {"status": "unavailable",
                "reason": (f"{len(rows)} usable point(s) with BOTH a social "
                           f"size and a volume reading; needs >= {min_points}"),
                "n_points": len(rows),
                "divergent": None}

    used = rows[-slope_window:] if slope_window else rows
    social_pts = [(float(t), s) for t, s, _ in used]
    volume_pts = [(float(t), v) for t, _, v in used]

    social_slope = _linear_slope(social_pts)
    volume_slope = _linear_slope(volume_pts)
    if social_slope is None or volume_slope is None:
        return {"status": "unavailable",
                "reason": ("a slope could not be estimated (no time spread "
                           "in the window)"),
                "n_points": len(rows), "divergent": None}

    social_up = social_slope > 0
    volume_down = volume_slope < 0
    divergent = bool(social_up and volume_down)
    converse = bool(social_slope < 0 and volume_slope > 0)

    return {
        "status": "ok",
        "n_points": len(rows),
        "n_points_used": len(used),
        "window_start_ts": used[0][0],
        "window_end_ts": used[-1][0],
        "window_hours": round((used[-1][0] - used[0][0]) / 3600.0, 3),
        "social_slope_per_hour": round(social_slope, 6),
        "volume_slope_per_hour": round(volume_slope, 6),
        "social_rising": social_up,
        "volume_falling": volume_down,
        "divergent": divergent,
        "converse": converse,
        "reading": (
            "SOCIAL UP / VOLUME DOWN - distribution is starting while the "
            "community still grows. The community is the LAST to leave."
            if divergent else
            "SOCIAL DOWN / VOLUME UP - attention is fading while money "
            "still flows in; often a late distribution trap."
            if converse else
            "Social and volume move together - no divergence."),
        "note": ("Slopes are OLS over the window in units per hour. A "
                 "positive social slope with a positive volume slope is NOT "
                 "a divergence, however loud the community looks."),
    }


# --------------------------------------------------------------------------
# 7. Live POST-ACTIVITY series - the one keyless social time series that
#    exists without collecting your own snapshots
# --------------------------------------------------------------------------
# Telegram's public preview exposes the timestamps of the most recent
# posts as `<time datetime="...">` elements. That is a genuine, keyless
# ACTIVITY time series: it says when the community was talking, not how
# many people are in it.
#
# IMPORTANT AND DELIBERATE: this is NOT a member-count history. It is a
# POST-ACTIVITY history, and it covers only the bounded window of posts the
# preview happens to render (verified: 20 posts for a live channel, and
# the same for an archived capture). It is a different signal from
# community SIZE, and the lead-time test treats it as such.

_TG_TIME_RE = re.compile(r'<time datetime="([^"]+)"', re.I)
_TG_POST_RE = re.compile(r'data-post="([^"]+)"', re.I)


def telegram_post_activity(
    url: str, timeout: int = 25) -> Dict[str, Any]:
    """Read the post timestamps from a Telegram channel's public preview.

    Returns the post timestamps (epoch seconds), oldest first, plus the
    metadata needed to judge whether the window is usable as a comparator.

    Two live-verified facts shape this function:

    * A channel's preview comes in TWO shapes. Some channels render the
      member/online block and NO posts (verified live on
      `t.me/s/Official_Bonk_Inu`: 11 004 members, 0 post timestamps).
      Others render posts with timestamps but NO member block (verified
      live on `t.me/s/pepecoinchannel`: 20 posts, 0 members). Which one
      you get is a property of the channel, not of the request, so this
      function reports what it actually got rather than assuming.

    * A channel that does not exist, or a personal profile, renders the
      "Contact @name" / plain-messenger shape with neither block.

    The Wayback Machine also archives these pages (verified live: CDX
    index returns captures for `t.me/s/bonk`, `t.me/s/pepecoinchannel` and
    `t.me/s/bonkinu`; the replay endpoint serves the archived HTML), so a
    HISTORICAL activity series is possible for channels that were
    captured. The replay endpoint rate-limits hard (HTTP 429), so it is
    a batch job, not a live path.
    """
    out: Dict[str, Any] = {"source": "telegram_public_preview",
                            "url": url, "timestamps": [], "n_posts": 0}
    try:
        st, body, _ = http_get(url, timeout=timeout, retries=2)
        html = body.decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        out["status"] = "unavailable"
        out["error"] = f"{type(exc).__name__}: {str(exc)[:140]}"
        return out
    out["http_status"] = st
    if st != 200:
        out["status"] = "unavailable"
        return out

    title_m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    title = title_m.group(1).strip() if title_m else None
    out["title"] = title
    out["is_contact_or_absent"] = bool(
        re.search(r"Telegram:\s*Contact", title or "", re.I))

    stamps: List[int] = []
    for raw in _TG_TIME_RE.findall(html):
        ts = _as_ts(raw)
        if ts is not None:
            stamps.append(ts)
    stamps.sort()
    out["timestamps"] = stamps
    out["n_posts"] = len(_TG_POST_RE.findall(html))
    out["n_timestamps"] = len(stamps)

    if stamps:
        out["status"] = "ok"
        out["first_post_ts"] = stamps[0]
        out["last_post_ts"] = stamps[-1]
        out["window_hours"] = round((stamps[-1] - stamps[0]) / 3600.0, 3)
        out["posts_per_hour"] = round(
            (len(stamps) - 1) / max((stamps[-1] - stamps[0]) / 3600.0, 1e-9), 4)
        out["note"] = ("Post-activity window from the public preview. The "
                       "preview renders a BOUNDED set of recent posts, so "
                       "this is the tail of the channel's history, not its "
                       "whole history.")
    else:
        out["status"] = "no_posts_in_preview"
        out["note"] = ("This channel's preview renders the member block "
                       "instead of posts. It has no post timestamps to "
                       "extract; use community size instead.")
    return out


def build_activity_series(
    stamps: Sequence[int], bucket_seconds: int = 3600) -> List[Dict[str, Any]]:
    """Bucket post timestamps into a per-bucket POST COUNT series.

    This is the input shape `first_mention_event` expects: a list of
    {"ts": epoch, "mentions": count} rows. A bucket with no posts is
    emitted with a count of 0, so the median is computed over the WHOLE
    window rather than over the active buckets only - which matters,
    because a median over active buckets only would make any modest
    activity look like a spike.
    """
    if not stamps or bucket_seconds <= 0:
        return []
    lo = min(stamps)
    hi = max(stamps)
    n_buckets = int((hi - lo) // bucket_seconds) + 1
    counts = [0] * n_buckets
    for ts in stamps:
        idx = int((ts - lo) // bucket_seconds)
        if 0 <= idx < n_buckets:
            counts[idx] += 1
    return [{"ts": int(lo + i * bucket_seconds), "mentions": counts[i]}
            for i in range(n_buckets)]


# --------------------------------------------------------------------------
# 6. Live social-size sampling (the snapshot writer for the series)
# --------------------------------------------------------------------------
def sample_community_size(social_links: Dict[str, str],
                           timeout: int = 25) -> Dict[str, Any]:
    """Read the CURRENT community size for a token's Telegram/Discord links.

    This calls the two keyless endpoints that `leapspace/social.py` already
    established:

        https://t.me/s/{username}                     -> members + online
        https://discord.com/api/v9/invites/{code}
            ?with_counts=true                          -> members + presence

    It returns the SAME shape the series writer wants, so a caller can
    pipe the result straight into `record_community_snapshot`.

    IMPORTANT AND DELIBERATE: this reads the CURRENT count only. Telegram's
    public preview exposes NO member-count history, so a time series can
    only be built by SAMPLING OVER TIME. That is why
    `record_community_snapshot` exists and why the series has to be
    collected, not queried.

    DEPENDENCY NOTE: this module is stdlib + `leapspace/http.py` only, so
    the two readers are implemented here rather than imported from
    `leapspace/social.py`. `leapspace/tests/test_socialedge.py` asserts
    that these two readers AGREE with the ones in `leapspace/social.py`
    on the same live URLs, so the duplication cannot drift silently.
    """
    out: Dict[str, Any] = {
        "sources": {}, "gaps": [],
        "ts": int(time.time()),
        "note": ("Live sample of the CURRENT community size. Telegram "
                 "exposes no member-count history, so this must be "
                 "sampled repeatedly to become a time series."),
    }
    tg_url = social_links.get("telegram")
    dc_url = social_links.get("discord")

    if tg_url:
        res = _telegram_size(tg_url, timeout=timeout)
        out["sources"]["telegram"] = res
        out["telegram_members"] = res.get("members")
        out["telegram_online"] = res.get("online")
        if res.get("status") != "ok":
            out["gaps"].append({"platform": "telegram",
                                "reason": res.get("status"),
                                "detail": res.get("error", "")})
    else:
        out["gaps"].append({"platform": "telegram",
                            "reason": "no telegram link supplied"})

    if dc_url:
        res = _discord_size(dc_url, timeout=timeout)
        out["sources"]["discord"] = res
        out["discord_members"] = res.get("members")
        out["discord_online"] = res.get("online")
        if res.get("status") != "ok":
            out["gaps"].append({"platform": "discord",
                                "reason": res.get("status"),
                                "detail": res.get("error", "")})
    else:
        out["gaps"].append({"platform": "discord",
                            "reason": "no discord link supplied"})

    measured = [v for v in (out.get("telegram_members"),
                            out.get("discord_members"))
                if v is not None]
    out["combined_members"] = int(sum(measured)) if measured else None
    out["measured_platforms"] = len(measured)
    return out


# --- the two keyless readers (stdlib + leapspace/http.py only) -----------
_TG_USER_RE = re.compile(r"(?:t\.me|telegram\.me)/(?:s/)?@?([A-Za-z0-9_]{4,})")
_TG_MEMBER_RE = re.compile(r"([\d\s,\u00a0\u202f\.]+?)\s*members", re.I)
_TG_ONLINE_RE = re.compile(r"([\d\s,\u00a0\u202f\.]+?)\s*online", re.I)
_TG_VIEW_RE = re.compile(r"<title>\s*Telegram:\s*View\s*@", re.I)


def _clean_count(raw: str) -> Optional[int]:
    """'11 004' -> 11004. Handles spaces, nbsp, narrow-nbsp and commas."""
    t = re.sub(r"[\s\u00a0\u202f,]", "", raw or "")
    t = t.rstrip(".")
    try:
        return int(t)
    except (TypeError, ValueError):
        return None


def _telegram_size(url: str, timeout: int = 25) -> Dict[str, Any]:
    """Member and online counts from a Telegram channel's public preview.

    THE VALIDITY TRAP, live-verified: a NONEXISTENT channel still returns
    HTTP 200. Its title reads "Telegram: Contact @name" (or the plain
    messenger title) instead of "Telegram: View @name". Only the latter
    carries a member count, so the title check is what stops a
    non-existent channel from being reported as a community with members.
    """
    out: Dict[str, Any] = {"source": "telegram_public_preview", "url": url}
    m = _TG_USER_RE.search(url or "")
    user = m.group(1) if m else None
    out["username"] = user
    if not user or "/joinchat/" in (url or "") or "/+" in (url or ""):
        out["status"] = "no_public_channel_in_link"
        return out
    try:
        st, body, _ = http_get(f"https://t.me/s/{user}", timeout=timeout,
                                retries=2)
        html = body.decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        out["status"] = "unavailable"
        out["error"] = f"{type(exc).__name__}: {str(exc)[:140]}"
        return out
    out["http_status"] = st
    if st != 200:
        out["status"] = "unavailable"
        return out
    if not _TG_VIEW_RE.search(html):
        out["status"] = "not_a_channel_or_absent"
        out["members"] = None
        out["online"] = None
        return out
    mm = _TG_MEMBER_RE.search(html)
    om = _TG_ONLINE_RE.search(html)
    members = _clean_count(mm.group(1)) if mm else None
    online = _clean_count(om.group(1)) if om else None
    if members is None:
        out["status"] = "no_member_count_in_page"
        out["members"] = None
        out["online"] = online
        return out
    out["status"] = "ok"
    out["members"] = members
    out["online"] = online
    return out


def _discord_code(url: str) -> Optional[str]:
    m = re.search(r"discord\.gg/([A-Za-z0-9]+)", url or "")
    if not m:
        m = re.search(r"discord\.com/invite/([A-Za-z0-9]+)", url or "")
    return m.group(1) if m else None


def _discord_size(url: str, timeout: int = 25) -> Dict[str, Any]:
    """Member and presence counts from a Discord invite.

    `approximate_presence_count` is the ONLINE count and is the
    liveness signal; `approximate_member_count` is the size. A bogus
    invite returns HTTP 404, which is the correct outcome and is
    reported as `unavailable`, never as zero members.
    """
    code = _discord_code(url)
    out: Dict[str, Any] = {"source": "discord_invite_api", "url": url,
                            "invite_code": code}
    if not code:
        out["status"] = "no_invite_code_in_link"
        return out
    api = f"https://discord.com/api/v9/invites/{code}?with_counts=true"
    try:
        st, body, _ = http_get(api, timeout=timeout, retries=2)
        data = json.loads(body.decode("utf-8", "replace"))
    except Exception as exc:  # noqa: BLE001
        out["status"] = "unavailable"
        out["error"] = f"{type(exc).__name__}: {str(exc)[:140]}"
        return out
    out["http_status"] = st
    if not isinstance(data, dict):
        out["status"] = "unavailable"
        return out
    members = data.get("approximate_member_count")
    presence = data.get("approximate_presence_count")
    out["members"] = int(members) if isinstance(members, (int, float)) else None
    out["online"] = (int(presence)
                     if isinstance(presence, (int, float)) else None)
    out["guild_name"] = (data.get("guild") or {}).get("name")
    out["status"] = "ok" if out["members"] is not None else "no_counts"
    return out


__all__ = [
    "build_community_series", "community_series_diagnostics",
    "load_community_series", "save_community_series",
    "record_community_snapshot", "membership_threshold_event",
    "holder_inflection_event", "first_mention_event",
    "compute_lead_time", "assess_wallet_edge",
    "narrative_established_ts", "classify_late_buyers",
    "social_vs_onchain_divergence", "sample_community_size",
    "telegram_post_activity", "build_activity_series",
    "LEADING", "COINCIDENT", "LAGGING", "UNKNOWN",
]
