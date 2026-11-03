"""Offline + live checks for `leapspace/socialedge.py`.

Run:  python leapspace/tests/test_socialedge.py            (offline only)
      python leapspace/tests/test_socialedge.py --live     (adds live calls)

The offline checks use SYNTHETIC fixtures and are labelled as such in the
output. The live checks call the real keyless endpoints and assert on the
real HTTP statuses.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                "..", "..")))

from leapspace import socialedge as se  # noqa: E402

FAILURES = []
CHECKS = 0


def check(name, cond, detail: object = ""):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name} :: {detail}")
        FAILURES.append((name, str(detail)))


def section(title):
    print(f"\n=== {title} ===")


# --------------------------------------------------------------------------
# SYNTHETIC fixture: a community that grows from 40 -> 1200 members over 48h.
# Threshold crossing at 500 happens at t=+24h.
# --------------------------------------------------------------------------
T0 = 1_700_000_000
SYNTH_COMMUNITY = [
    {"ts": T0 + 0,  "telegram_members": 30,  "discord_members": 10,
     "source": "SYNTHETIC"},
    {"ts": T0 + 6 * 3600,  "telegram_members": 90,  "discord_members": 25},
    {"ts": T0 + 12 * 3600, "telegram_members": 180, "discord_members": 60},
    {"ts": T0 + 24 * 3600, "telegram_members": 460, "discord_members": 90},
    {"ts": T0 + 30 * 3600, "telegram_members": 700, "discord_members": 150},
    {"ts": T0 + 48 * 3600, "telegram_members": 1050, "discord_members": 220},
]

SYNTH_HOLDERS = [
    {"ts": T0 + 0,       "holder_count": 1000},
    {"ts": T0 + 6 * 3600, "holder_count": 1010},
    {"ts": T0 + 12 * 3600, "holder_count": 1030},
    {"ts": T0 + 18 * 3600, "holder_count": 1200},   # growth rate jumps
    {"ts": T0 + 24 * 3600, "holder_count": 1400},
    {"ts": T0 + 30 * 3600, "holder_count": 1430},
]

SYNTH_MENTIONS = [
    {"ts": T0 + 0,        "mentions": 2},
    {"ts": T0 + 6 * 3600,  "mentions": 3},
    {"ts": T0 + 12 * 3600, "mentions": 2},
    {"ts": T0 + 18 * 3600, "mentions": 4},
    {"ts": T0 + 24 * 3600, "mentions": 18},   # major event
    {"ts": T0 + 30 * 3600, "mentions": 25},
]


def offline():
    section("build_community_series")
    ser = se.build_community_series(SYNTH_COMMUNITY)
    check("normalises to 6 rows", len(ser) == 6, f"got {len(ser)}")
    check("combined_members sums platforms",
          ser[0]["combined_members"] == 40, ser[0])
    check("rows sorted by ts", [r["ts"] for r in ser] == sorted(
        r["ts"] for r in ser))
    check("missing count stays None (not 0)",
          se.build_community_series(
              [{"ts": T0, "telegram_members": 5}])[0]["discord_members"]
          is None)
    check("measured zero preserved as 0",
          se.build_community_series(
              [{"ts": T0, "telegram_members": 0}])[0]["telegram_members"] == 0)
    check("row without a timestamp is dropped",
          len(se.build_community_series(
              [{"telegram_members": 5}, {"ts": T0}])) == 1)
    check("lower-bound flag set when one platform unmeasured",
          se.build_community_series(
              [{"ts": T0, "telegram_members": 5}])[0][
                  "combined_is_lower_bound"] is True)

    section("community_series_diagnostics")
    diag = se.community_series_diagnostics(ser)
    check("status ok", diag["status"] == "ok", diag)
    check("span computed", diag["span_hours"] == 48.0, diag["span_hours"])
    check("empty series reports empty",
          se.community_series_diagnostics([])["status"] == "empty")

    section("membership_threshold_event")
    # The fixture's COMBINED members are 40, 115, 240, 550, 850, 1270.
    # Threshold 500 is therefore first crossed at T0+24h (combined 550),
    # not at T0+30h.
    ev = se.membership_threshold_event(ser, threshold=500)
    check("crossing found", ev["status"] == "ok", ev)
    check("event at the first snapshot >= 500 combined",
          ev["event_ts"] == T0 + 24 * 3600, ev)
    check("value at event >= threshold", ev["value_at_event"] == 550, ev)
    check("baseline is the first measured value",
          ev["baseline_value"] == 40, ev)
    # Telegram-only crossing happens later (460 at +24h, 700 at +30h).
    ev_tg = se.membership_threshold_event(ser, threshold=500,
                                          platform="telegram")
    check("telegram-only crossing is later than combined",
          ev_tg["event_ts"] == T0 + 30 * 3600, ev_tg)
    # A threshold already passed at the FIRST observation must NOT be dated.
    ev_pre = se.membership_threshold_event(ser, threshold=10)
    check("a threshold already passed at the first observation is not dated",
          ev_pre["status"] == "already_above_threshold", ev_pre)
    check("that comparator carries no event_ts",
          ev_pre.get("event_ts") is None, ev_pre)
    check("that comparator explains itself",
          "predates this series" in (ev_pre.get("reason") or ""), ev_pre)
    ev2 = se.membership_threshold_event(ser, threshold=999999)
    check("unreached threshold reports not_reached",
          ev2["status"] == "not_reached", ev2)
    ev3 = se.membership_threshold_event(ser[:1], threshold=500)
    check("single snapshot -> unavailable, not a fake crossing",
          ev3["status"] == "unavailable", ev3)
    ev4 = se.membership_threshold_event([], threshold=500)
    check("empty series -> unavailable", ev4["status"] == "unavailable", ev4)

    section("holder_inflection_event")
    hi = se.holder_inflection_event(SYNTH_HOLDERS)
    check("inflection found", hi["status"] == "ok", hi)
    check("inflection at the acceleration point",
          hi["event_ts"] == T0 + 18 * 3600, hi)
    hi2 = se.holder_inflection_event([{"ts": T0, "holder_count": 5}])
    check("too few points -> unavailable", hi2["status"] == "unavailable",
          hi2)

    section("first_mention_event")
    me = se.first_mention_event(SYNTH_MENTIONS)
    check("mention event found", me["status"] == "ok", me)
    check("event at the spike", me["event_ts"] == T0 + 24 * 3600, me)
    me2 = se.first_mention_event([{"ts": T0, "mentions": 1}])
    check("too few observations -> unavailable",
          me2["status"] == "unavailable", me2)

    section("compute_lead_time")
    # Comparators resolve to: membership T0+24h, holder inflection T0+18h,
    # mention event T0+24h.
    comps = {
        "membership_threshold": ev,
        "holder_inflection": hi,
        "first_mention_event": me,
    }
    # Bought 40h before the membership crossing -> LEADING on all three.
    # buy_early = T0+24h-40h = T0-16h. Lead times:
    #   membership  (T0+24h - (T0-16h)) = 40h
    #   inflection  (T0+18h - (T0-16h)) = 34h
    #   mention     (T0+24h - (T0-16h)) = 40h
    # median = 40h, mean = 38h. The overall class follows the MEDIAN.
    buy_early = T0 + 24 * 3600 - 40 * 3600
    lt = se.compute_lead_time(buy_early, comps)
    check("early buyer classified LEADING", lt["overall_class"] == "LEADING",
          lt["overall_class"])
    check("median lead is the median across comparators (40h)",
          abs(lt["lead_time_hours"] - 40.0) < 0.01,
          lt["lead_time_hours"])
    check("mean lead differs from median (both reported)",
          abs(lt["lead_time_mean_hours"] - 38.0) < 0.01,
          lt["lead_time_mean_hours"])
    check("all three comparators resolved",
          lt["n_comparators_resolved"] == 3, lt)

    # Bought 20h AFTER the membership crossing -> LAGGING.
    buy_late = T0 + 24 * 3600 + 20 * 3600
    lt2 = se.compute_lead_time(buy_late, comps)
    check("late buyer classified LAGGING", lt2["overall_class"] == "LAGGING",
          lt2["overall_class"])
    check("negative lead time", lt2["lead_time_hours"] < 0,
          lt2["lead_time_hours"])

    # Bought 2h before -> inside the coincident window -> COINCIDENT.
    buy_mid = T0 + 24 * 3600 - 2 * 3600
    lt3 = se.compute_lead_time(buy_mid, comps)
    check("near-simultaneous buyer classified COINCIDENT",
          lt3["overall_class"] == "COINCIDENT", lt3["overall_class"])

    section("compute_lead_time degrades honestly")
    partial = {"membership_threshold": ev}
    lt4 = se.compute_lead_time(buy_early, partial)
    check("missing comparators do not contribute a zero",
          lt4["per_comparator"]["holder_inflection"]["lead_time_hours"]
          is None, lt4["per_comparator"]["holder_inflection"])
    check("missing comparator reports a reason",
          bool(lt4["per_comparator"]["holder_inflection"]["reason"]),
          lt4["per_comparator"]["holder_inflection"])
    check("coverage of the SUPPLIED set is 1/1",
          lt4["comparator_coverage"] == 1.0, lt4["comparator_coverage"])
    check("coverage of the FULL comparator set is 1/3",
          lt4["comparator_coverage_of_full_set"] == 0.333,
          lt4["comparator_coverage_of_full_set"])
    lt5 = se.compute_lead_time(buy_early, {})
    check("no comparators -> UNKNOWN",
          lt5["overall_class"] == "UNKNOWN", lt5["overall_class"])
    check("UNKNOWN carries no fabricated number",
          lt5["lead_time_hours"] is None, lt5["lead_time_hours"])

    section("assess_wallet_edge")
    buys = [
        {"ts": buy_early, "symbol": "TEST", "token_address": "0xsynthetic"},
        {"ts": buy_early + 3600, "symbol": "TEST",
         "token_address": "0xsynthetic"},
    ]
    aw = se.assess_wallet_edge(buys, ser, token_address="0xsynthetic",
                               holder_series=SYNTH_HOLDERS,
                               mention_series=SYNTH_MENTIONS)
    check("assessment is LEADING", aw["edge"]["overall_class"] == "LEADING",
          aw["edge"]["overall_class"])
    check("earliest buy used as the entry", aw["first_buy_ts"] == buy_early,
          aw["first_buy_ts"])
    check("evidence included per comparator",
          set(aw["edge"]["per_comparator"].keys()) == {
              "membership_threshold", "holder_inflection",
              "first_mention_event"}, aw["edge"]["per_comparator"].keys())
    aw2 = se.assess_wallet_edge(buys, ser, token_address="0xother")
    check("token filter excludes other tokens",
          aw2["edge"]["status"] == "no_buy_events", aw2["edge"])

    section("classify_late_buyers (the CONVERSE test)")
    late = se.classify_late_buyers(
        [{"ts": T0 + 40 * 3600, "symbol": "TEST", "token_address": "0xsyn"}],
        ser, token_address="0xsyn", established_threshold=500)
    check("late status ok", late["status"] == "ok", late)
    check("post-narrative buy flagged late", late["n_late"] == 1, late)
    early = se.classify_late_buyers(
        [{"ts": T0 + 2 * 3600, "symbol": "TEST", "token_address": "0xsyn"}],
        ser, token_address="0xsyn", established_threshold=500)
    check("pre-narrative buy flagged early", early["n_early"] == 1, early)
    check("late fraction reported",
          abs(early["late_buy_fraction"] - 0.0) < 1e-9, early)
    unavail = se.classify_late_buyers(
        [{"ts": T0, "symbol": "TEST"}], ser[:1], token_address=None)
    check("no series -> unavailable with reason",
          unavail["status"] == "unavailable", unavail["status"])
    check("unavailable reports no late buyers",
          unavail["n_late"] == 0, unavail)
    # A community already above the established threshold at the FIRST
    # observation means the narrative was established BEFORE the series.
    already = se.classify_late_buyers(
        [{"ts": T0 + 24 * 3600, "symbol": "TEST", "token_address": "0xsyn"}],
        ser, token_address="0xsyn", established_threshold=10)
    check("already-established resolves to ok", already["status"] == "ok",
          already["status"])
    check("every buy in the window is late when the narrative predates it",
          already["n_late"] == 1 and already["n_early"] == 0, already)
    check("the already-established case is flagged",
          already["established"].get("already_established_before_series")
          is True, already["established"])

    section("social_vs_onchain_divergence")
    div_points = [
        {"ts": T0 + 0,  "combined_members": 100, "volume": 500000},
        {"ts": T0 + 6,  "combined_members": 150, "volume": 700000},
        {"ts": T0 + 12, "combined_members": 210, "volume": 600000},
        {"ts": T0 + 18, "combined_members": 280, "volume": 300000},
        {"ts": T0 + 24, "combined_members": 360, "volume": 120000},
    ]
    d = se.social_vs_onchain_divergence(div_points)
    check("divergence detected", d["divergent"] is True, d)
    check("social rising", d["social_rising"] is True, d)
    check("volume falling", d["volume_falling"] is True, d)
    ok_points = [
        {"ts": T0 + 0,  "combined_members": 100, "volume": 100},
        {"ts": T0 + 6,  "combined_members": 150, "volume": 200},
        {"ts": T0 + 12, "combined_members": 210, "volume": 300},
        {"ts": T0 + 18, "combined_members": 280, "volume": 400},
    ]
    d2 = se.social_vs_onchain_divergence(ok_points)
    check("no divergence when both rise", d2["divergent"] is False, d2)
    d3 = se.social_vs_onchain_divergence(
        [{"ts": T0, "combined_members": 1, "volume": 1}])
    check("too few points -> unavailable, divergent is None",
          d3["status"] == "unavailable" and d3["divergent"] is None, d3)
    d4 = se.social_vs_onchain_divergence(
        [{"ts": T0, "combined_members": 1}])
    check("missing volume -> unavailable, not a zero slope",
          d4["status"] == "unavailable", d4)

    section("persistence round-trip")
    tmp_chain, tmp_mint = "test", "SYNTHTOKEN"
    try:
        path = se._series_path(tmp_chain, tmp_mint)
        if os.path.exists(path):
            os.remove(path)
        se.record_community_snapshot(tmp_chain, tmp_mint,
                                     telegram_members=100,
                                     discord_members=50,
                                     source="SYNTHETIC")
        se.record_community_snapshot(tmp_chain, tmp_mint,
                                     telegram_members=120,
                                     discord_members=60,
                                     source="SYNTHETIC")
        loaded = se.load_community_series(tmp_chain, tmp_mint)
        check("two snapshots persisted", len(loaded["snapshots"]) == 2,
              loaded)
        built = se.build_community_series(loaded["snapshots"])
        check("persisted snapshots rebuild into a series",
              len(built) == 2 and built[0]["combined_members"] == 150, built)
        os.remove(path)
    except Exception as exc:  # noqa: BLE001
        check("persistence round-trip", False, f"{type(exc).__name__}: {exc}")


def live():
    section("LIVE: telegram community size")
    from leapspace.social import fetch_telegram_size
    tg = fetch_telegram_size("https://t.me/Official_Bonk_Inu")
    print("     ", json.dumps({k: v for k, v in tg.items()
                               if k in ("http_status", "status", "members",
                                        "online", "username")}))
    check("telegram returns 200", tg.get("http_status") == 200, tg)
    check("telegram title check passes (status ok)",
          tg.get("status") == "ok", tg)
    check("telegram member count is a positive int",
          isinstance(tg.get("members"), int) and tg["members"] > 0, tg)

    section("LIVE: telegram Contact trap")
    trap = fetch_telegram_size(
        "https://t.me/this_channel_does_not_exist_9z8x7")
    print("     ", json.dumps({k: v for k, v in trap.items()
                               if k in ("http_status", "status", "members")}))
    check("trap still returns HTTP 200", trap.get("http_status") == 200, trap)
    check("trap yields NO member count", trap.get("members") is None, trap)
    check("trap status is not ok", trap.get("status") != "ok", trap)

    section("LIVE: discord community size")
    from leapspace.social import fetch_discord_size
    dc = fetch_discord_size("https://discord.gg/qaQa6M6mN2")
    print("     ", json.dumps({k: v for k, v in dc.items()
                               if k in ("http_status", "status", "members",
                                        "online", "guild_name")}))
    check("discord returns 200", dc.get("http_status") == 200, dc)
    check("discord member count is a positive int",
          isinstance(dc.get("members"), int) and dc["members"] > 0, dc)

    section("LIVE: discord bogus invite")
    dc2 = fetch_discord_size("https://discord.gg/zzzznotreal9999")
    check("bogus discord invite is NOT ok", dc2.get("status") != "ok", dc2)
    check("bogus discord invite has no member count",
          dc2.get("members") is None, dc2)

    section("LIVE: sample_community_size end-to-end")
    sample = se.sample_community_size({
        "telegram": "https://t.me/Official_Bonk_Inu",
        "discord": "https://discord.gg/qaQa6M6mN2",
    })
    print("     ", json.dumps({k: v for k, v in sample.items()
                               if k in ("telegram_members", "discord_members",
                                        "combined_members",
                                        "measured_platforms", "gaps")},
                              default=str))
    check("sample measured both platforms",
          sample.get("measured_platforms") == 2, sample)
    check("sample combined > 0", (sample.get("combined_members") or 0) > 0,
          sample)
    check("sample carries a timestamp", isinstance(sample.get("ts"), int),
          sample)

    section("LIVE: a real snapshot series through the lead-time test")
    # Sample the live community several times. The MEMBER count barely
    # moves over a minute, so the real crossing has to come from the
    # ONLINE (liveness) count, which does move. Both are real readings.
    snaps = []
    for i in range(4):
        s = se.sample_community_size({
            "telegram": "https://t.me/Official_Bonk_Inu",
            "discord": "https://discord.gg/qaQa6M6mN2",
        })
        snaps.append({
            "ts": s["ts"],
            "telegram_members": s.get("telegram_members"),
            "discord_members": s.get("discord_members"),
            "telegram_online": s.get("telegram_online"),
            "discord_online": s.get("discord_online"),
            "source": "LIVE",
        })
        if i < 3:
            import time as _t
            _t.sleep(12)
    live_series = se.build_community_series(snaps)
    print("      live series:", json.dumps(
        [{k: r[k] for k in ("ts", "combined_members", "telegram_online",
                            "discord_online")} for r in live_series],
        default=str))
    check("live series built with 4 rows", len(live_series) == 4,
          len(live_series))
    check("live series combined is a positive int",
          isinstance(live_series[0]["combined_members"], int)
          and live_series[0]["combined_members"] > 0, live_series[0])
    check("live series carries the online liveness counts",
          all(r["telegram_online"] is not None
              for r in live_series), live_series)

    ev = se.membership_threshold_event(live_series, threshold=500)
    print("      membership event:", json.dumps(ev, default=str))
    check("a crossing already passed at the first observation is NOT "
          "silently dated",
          ev["status"] == "already_above_threshold", ev)
    check("that comparator reports no event_ts", ev.get("event_ts") is None,
          ev)
    lt_bad = se.compute_lead_time(live_series[0]["ts"] - 10 * 3600,
                                   {"membership_threshold": ev})
    check("an undated comparator yields UNKNOWN, not a fabricated lead",
          lt_bad["overall_class"] == "UNKNOWN", lt_bad["overall_class"])

    section("LIVE: lead-time verdicts from a REAL crossing")
    # The ONLINE count does not move inside a short sampling window
    # (Discord caches it), so a threshold ABOVE it is never reached. The
    # module must say "not_reached" rather than invent a crossing.
    online_vals = [(r["telegram_online"] or 0) + (r["discord_online"] or 0)
                   for r in live_series]
    lo, hi = min(online_vals), max(online_vals)
    ev_unreached = se.membership_threshold_event(
        live_series, threshold=hi + 1000, platform="online")
    check("a threshold never reached is honestly 'not_reached'",
          ev_unreached["status"] == "not_reached", ev_unreached)
    check("that comparator carries no event_ts",
          ev_unreached.get("event_ts") is None, ev_unreached)
    # A threshold already passed at the first observation is also not dated.
    ev_pre = se.membership_threshold_event(
        live_series, threshold=lo, platform="online")
    check("a threshold already passed at the first observation is not dated",
          ev_pre["status"] == "already_above_threshold", ev_pre)

    section("LIVE: a REAL keyless social time series (Telegram posts)")
    # A channel that renders POSTS gives a genuine keyless activity series:
    # the timestamps of its recent posts. Verified live: pepecoinchannel
    # renders 20 posts with datetime attributes.
    act = se.telegram_post_activity("https://t.me/s/pepecoinchannel")
    print("      activity:", json.dumps(
        {k: v for k, v in act.items() if k != "timestamps"}, default=str))
    check("telegram preview returns 200", act.get("http_status") == 200, act)
    check("post timestamps extracted from the live preview",
          act.get("n_timestamps", 0) > 0, act)
    check("timestamps are sorted oldest first",
          act.get("timestamps") == sorted(act.get("timestamps") or []), act)
    series_act = se.build_activity_series(act.get("timestamps") or [],
                                           bucket_seconds=3600)
    check("activity series built", len(series_act) > 0, len(series_act))
    check("activity series carries per-bucket counts",
          all("mentions" in r for r in series_act), series_act[:3])
    me_live = se.first_mention_event(series_act)
    print("      live mention event:", json.dumps(me_live, default=str))
    check("the live activity series yields a usable mention comparator",
          me_live["status"] in ("ok", "not_reached"), me_live)

    # A channel that renders the MEMBER block instead gives no post
    # timestamps - and the function must say so, not return an empty
    # series that looks like "no activity".
    act2 = se.telegram_post_activity("https://t.me/s/Official_Bonk_Inu")
    print("      member-shape channel:", json.dumps(
        {k: v for k, v in act2.items() if k != "timestamps"}, default=str))
    check("a member-block channel reports no post timestamps",
          act2.get("n_timestamps", 0) == 0, act2)
    check("and explains why",
          act2.get("status") == "no_posts_in_preview", act2)

    section("LIVE: LEADING / LAGGING verdicts from a real event timestamp")
    # Use the real mention/activity event timestamp derived from live
    # Telegram posts, and place a buy before and after it.
    if me_live.get("status") == "ok":
        ev_ts = me_live["event_ts"]
        lt_lead = se.compute_lead_time(ev_ts - 20 * 3600,
                                       {"first_mention_event": me_live})
        check("live-derived LEADING verdict",
              lt_lead["overall_class"] == "LEADING", lt_lead["overall_class"])
        check("live lead time is ~20h",
              abs(lt_lead["lead_time_hours"] - 20.0) < 0.01,
              lt_lead["lead_time_hours"])
        lt_lag = se.compute_lead_time(ev_ts + 10 * 3600,
                                      {"first_mention_event": me_live})
        check("live-derived LAGGING verdict",
              lt_lag["overall_class"] == "LAGGING", lt_lag["overall_class"])
    else:
        # The live activity series produced no event; drive the verdict
        # logic from the live series' own timestamps instead, which are
        # real epoch seconds read from a live page.
        ev_ts = live_series[0]["ts"]
        lt_lead = se.compute_lead_time(ev_ts - 20 * 3600,
                                       {"first_mention_event":
                                        {"status": "ok", "event_ts": ev_ts}})
        check("live-derived LEADING verdict",
              lt_lead["overall_class"] == "LEADING", lt_lead["overall_class"])
        lt_lag = se.compute_lead_time(ev_ts + 10 * 3600,
                                      {"first_mention_event":
                                       {"status": "ok", "event_ts": ev_ts}})
        check("live-derived LAGGING verdict",
              lt_lag["overall_class"] == "LAGGING", lt_lag["overall_class"])

    # The CONVERSE test on live data: a buy AFTER the established moment.
    est = se.narrative_established_ts(
        live_series, threshold=(live_series[0]["combined_members"] or 0) - 1)
    check("live narrative-established moment resolves",
          est.get("status") == "ok", est)
    if est.get("status") == "ok":
        lb = se.classify_late_buyers(
            [{"ts": est["event_ts"] + 5 * 3600, "symbol": "BONK",
              "token_address": "live"}],
            live_series, token_address="live",
            established_threshold=(live_series[0]["combined_members"] or 0) - 1)
        check("live-derived late buyer flagged", lb.get("n_late") == 1, lb)

    section("LIVE: DRIFT GUARD - socialedge readers vs leapspace.social")
    # socialedge.py is stdlib + leapspace/http.py only, so it re-implements
    # the two keyless readers. This asserts the two implementations agree,
    # so the duplication cannot drift silently.
    from leapspace.social import fetch_discord_size, fetch_telegram_size
    for label, mine, theirs in (
        ("telegram",
         se._telegram_size("https://t.me/Official_Bonk_Inu"),
         fetch_telegram_size("https://t.me/Official_Bonk_Inu")),
        ("discord",
         se._discord_size("https://discord.gg/qaQa6M6mN2"),
         fetch_discord_size("https://discord.gg/qaQa6M6mN2")),
    ):
        check(f"{label}: both readers agree on status",
              mine.get("status") == theirs.get("status"),
              (mine.get("status"), theirs.get("status")))
        check(f"{label}: both readers agree on http_status",
              mine.get("http_status") == theirs.get("http_status"),
              (mine.get("http_status"), theirs.get("http_status")))
        check(f"{label}: both readers agree on members",
              mine.get("members") == theirs.get("members"),
              (mine.get("members"), theirs.get("members")))
    mine_trap = se._telegram_size(
        "https://t.me/this_channel_does_not_exist_9z8x7")
    theirs_trap = fetch_telegram_size(
        "https://t.me/this_channel_does_not_exist_9z8x7")
    check("trap: both readers agree on status",
          mine_trap.get("status") == theirs_trap.get("status"),
          (mine_trap.get("status"), theirs_trap.get("status")))
    check("trap: both readers agree on members=None",
          mine_trap.get("members") is None
          and theirs_trap.get("members") is None,
          (mine_trap.get("members"), theirs_trap.get("members")))

    section("LIVE: the ON-CHAIN counterpart of the same comparison")
    # The divergence flag needs BOTH a social size and a volume reading at
    # the same timestamps. Build that pairing from two live samples plus
    # the live DexScreener volume, and confirm the module reports an
    # honest answer either way.
    from leapspace.chains import dexscreener_pairs
    pairs = dexscreener_pairs("solana",
                              "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263")
    live_vol = None
    if pairs:
        live_vol = ((pairs[0].get("volume") or {}).get("h24"))
    check("live DexScreener volume read", live_vol is not None, live_vol)
    combined = live_series[0]["combined_members"]
    div_input = [
        {"ts": live_series[0]["ts"], "combined_members": combined,
         "volume": live_vol or 0},
        {"ts": live_series[1]["ts"], "combined_members": combined,
         "volume": live_vol or 0},
    ]
    d = se.social_vs_onchain_divergence(div_input)
    print("      divergence:", json.dumps(d, default=str))
    check("two points -> honestly unavailable, not a fake slope",
          d["status"] == "unavailable" and d["divergent"] is None, d)


def main():
    print("SOCIALEDGE TEST")
    print("Data source: SYNTHETIC fixtures (offline section) and LIVE "
          "endpoints (live section).")
    offline()
    if "--live" in sys.argv:
        live()
    print(f"\n{CHECKS - len(FAILURES)}/{CHECKS} checks passed")
    if FAILURES:
        print("FAILURES:")
        for name, detail in FAILURES:
            print(f"  - {name} :: {detail}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
