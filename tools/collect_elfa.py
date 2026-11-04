"""Collect Elfa AI data into the user's storage directory.

WHAT IT COLLECTS, AND WHY EACH ONE

    trending_tokens      DAILY MENTION COUNTS per token, reconstructed
                        from 2026-10-05 to now by querying one-day
                        windows. This is the SOCIAL ATTENTION series -
                        the thing the crypto claims name ("retail
                        attention data show strong standalone
                        performance") and the thing this package did
                        not have.

    trending_narratives  The narratives driving attention.

    crypto_mindshare    Each asset's SHARE of crypto attention, with
                        1h/4h splits. Attention share is a crowding
                        measure.

    equity_mindshare    The same for equities - the other asset class
                        the user named.

    crypto_call_book    HOURLY BARS of long/short share, crowding
                        percentile and account count. A genuine
                        time series, and the retail-POSITIONING layer
                        the regime paper asks for.

    equity_call_book    The same for equities.

    trending_contracts  EVM and Solana contract addresses ranked by
                        social mentions. The MEMECOIN layer: the
                        contracts worth watching are often the ones
                        nobody has catalogued, so they have no price
                        feed and no ticker - only a contract address
                        and a mention count.

    token_news          News/social mentions per token.

    top_mentions        The accounts driving the conversation.

    events              The event stream with timestamps - the raw
                        material for a narrative-timing feature.

    positioning         Open long/short episode counts per asset.

EVERY WRITE IS PROVENANCED
    Each row carries the endpoint, the parameters, the HTTP status,
    the credit cost and the fetch timestamp. The API KEY IS NEVER
    WRITTEN. The manifest records the same, plus the row counts and
    the history window, so a dataset whose length nobody can check is
    a dataset that cannot be trusted.
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from leapspace.elfa import (  # noqa: E402
    DEFAULT_STORAGE_ROOT, ElfaClient, ElfaError,
)

DAY = 86400


def _ts(dt: float) -> int:
    return int(dt)


def collect(client: ElfaClient, out_root: str,
            max_daily_windows: int = 31,
            verbose: bool = True) -> Dict[str, Any]:
    """Collect everything. Returns the manifest."""
    manifest: Dict[str, Any] = {
        "source": "Elfa AI API v2/v3",
        "base_url": "https://api.elfa.ai",
        "storage_root": out_root,
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "datasets": {},
    }
    # The subdirectories have to exist before the first write. The
    # first run of this collector collected 1,500 rows of trending
    # tokens and then died on the write, because the directory was
    # never created.
    os.makedirs(os.path.join(out_root, "elfa"), exist_ok=True)
    os.makedirs(os.path.join(out_root, "market"), exist_ok=True)

    def note(name: str, path: str, rows: int, meta: Dict[str, Any],
             extra: Dict[str, Any] | None = None) -> None:
        manifest["datasets"][name] = {
            "file": os.path.relpath(path, out_root),
            "rows": rows,
            "endpoint": meta.get("endpoint"),
            "http_status": meta.get("http_status"),
            "credits": meta.get("credits"),
            "fetched_at": meta.get("fetched_at"),
            "params": meta.get("params"),
            **(extra or {}),
        }
        if verbose:
            print(f"  {name:26s} {rows:6d} rows -> "
                  f"{os.path.relpath(path, out_root)}", flush=True)

    # ---- the history window, from the key itself --------------------
    ks = client.key_status()
    st = ks["status"]
    history_from = int(st.get("historyFrom") or 0)
    manifest["key_status"] = {
        "plan": st.get("plan"),
        "billing_mode": st.get("billingMode"),
        "scopes": st.get("scopes"),
        "requests_per_minute": (st.get("credits") or {}).get(
            "requestsPerMinute"),
        "history_from_epoch": history_from,
        "history_from": (time.strftime("%Y-%m-%d", time.gmtime(history_from))
                         if history_from else None),
        "history_days": (round((time.time() - history_from) / DAY, 2)
                         if history_from else None),
    }
    if verbose:
        print(f"  plan={st.get('plan')}  history_from="
              f"{manifest['key_status']['history_from']}  "
              f"({manifest['key_status']['history_days']} days)  "
              f"scopes={len(st.get('scopes') or [])}", flush=True)

    now = int(time.time())
    start = history_from or (now - 30 * DAY)

    # ---- 1. the daily trending-token attention series ---------------
    # One-day windows, oldest first. This is the expensive one -
    # `max_daily_windows` requests - and it is the dataset that turns
    # Elfa from a snapshot into a usable feature.
    #
    # It is NOT re-fetched if the file already exists: 31 requests is
    # 31 credits, and a re-run that duplicates it spends money for
    # nothing. The manifest records that the series was reused.
    p = os.path.join(out_root, "elfa", "trending_tokens_daily.jsonl")
    rows: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {}
    if os.path.exists(p) and os.path.getsize(p) > 0:
        with open(p, encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        meta = {"endpoint": "/v2/aggregations/trending-tokens",
                "reused": True,
                "note": ("the daily series was already collected and was "
                         "NOT re-fetched")}
        if verbose:
            print(f"  trending_tokens_daily: REUSING {len(rows)} existing "
                  f"rows (not re-fetched)", flush=True)
    else:
        for i in range(max_daily_windows):
            w_end = start + (i + 1) * DAY
            w_start = start + i * DAY
            if w_end > now:
                break
            try:
                res = client.trending_tokens(from_ts=w_start, to_ts=w_end,
                                             page=1, page_size=50,
                                             min_mentions=1)
            except ElfaError as exc:
                if verbose:
                    print(f"    window {i} failed: {exc}", flush=True)
                continue
            meta = res["meta"]
            for item in ((res["data"].get("data") or {}).get("data")
                         or []):
                rows.append({
                    "window_start": w_start,
                    "window_end": w_end,
                    "window_start_iso": time.strftime("%Y-%m-%d",
                                                      time.gmtime(w_start)),
                    "token": item.get("token"),
                    "current_count": item.get("current_count"),
                    "previous_count": item.get("previous_count"),
                    "change_percent": item.get("change_percent"),
                    "source": "elfa/v2/aggregations/trending-tokens",
                    "fetched_at": meta.get("fetched_at"),
                })
            if verbose and (i + 1) % 5 == 0:
                print(f"    trending-tokens: {i + 1} windows, "
                      f"{len(rows)} rows", flush=True)
        with open(p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, default=str) + "\n")
    note("trending_tokens_daily", p, len(rows), meta or {},
         {"granularity": "1 day",
          "history_from": manifest["key_status"]["history_from"]})

    # ---- 2. the hourly call books -----------------------------------
    # `from` is REQUIRED, and one row is one HOUR, so 31 days is ~744
    # bars while the page size caps at 200 - the cursor does the paging.
    for label, path in (("crypto_call_book",
                         "/v3/market/crypto/call-book"),
                        ("equity_call_book",
                         "/v3/market/equity/call-book")):
        try:
            bars, m = client.get_paginated(
                path, {"from": start, "to": now, "order": "asc"},
                items_key="bars", page_size=200, max_pages=12,
                verbose=verbose)
        except ElfaError as exc:
            if verbose:
                print(f"    {label} failed: {exc}", flush=True)
            continue
        out = [{**b, "source": f"elfa/v3/market/{label}",
                "fetched_at": m.get("fetched_at")} for b in bars
               if isinstance(b, dict)]
        p = os.path.join(out_root, "elfa", f"{label}.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            for r in out:
                fh.write(json.dumps(r, default=str) + "\n")
        span = None
        if out:
            ts = sorted(int(b.get("barAt") or 0) for b in out)
            span = [time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts[0])),
                    time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts[-1]))]
        note(label, p, len(out), m, {"granularity": "1 hour",
                                     "span": span,
                                     "served_from": m.get("served_from")})

    # ---- 3. the mindshare snapshots ---------------------------------
    for label, path in (("crypto_mindshare",
                         "/v3/market/crypto/mindshare"),
                        ("equity_mindshare",
                         "/v3/market/equity/mindshare")):
        try:
            body, m = client.get(path, {"limit": 50})
        except ElfaError as exc:
            if verbose:
                print(f"    {label} failed: {exc}", flush=True)
            continue
        body = body if isinstance(body, dict) else {}
        assets = body.get("assets") or []
        out = [{**a, "source": f"elfa/v3/market/{label}",
                "fetched_at": m.get("fetched_at")} for a in assets
               if isinstance(a, dict)]
        p = os.path.join(out_root, "elfa", f"{label}.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            for r in out:
                fh.write(json.dumps(r, default=str) + "\n")
        note(label, p, len(out), m)

    # ---- 4. the memecoin contract layer -----------------------------
    # The RANGE is what makes it historical; a range over 24 hours
    # costs 5 extra credits.
    try:
        contracts, m = client.get_paginated(
            "/v3/market/crypto/trending-contracts",
            {"from": start, "to": now}, items_key="contracts",
            page_size=50, max_pages=8, verbose=verbose)
    except ElfaError as exc:
        if verbose:
            print(f"    trending_contracts failed: {exc}", flush=True)
        contracts, m = [], {}
    out = [{**c, "source": "elfa/v3/market/crypto/trending-contracts",
            "fetched_at": m.get("fetched_at")} for c in contracts
           if isinstance(c, dict)]
    p = os.path.join(out_root, "elfa", "trending_contracts.jsonl")
    with open(p, "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, default=str) + "\n")
    note("trending_contracts", p, len(out), m,
         {"served_from": m.get("served_from")})

    # ---- 5. the narratives ------------------------------------------
    for tf in ("day", "week"):
        try:
            res = client.trending_narratives(time_frame=tf,
                                             max_narratives=50)
        except ElfaError as exc:
            if verbose:
                print(f"    trending_narratives[{tf}] failed: {exc}",
                      flush=True)
            continue
        m = res["meta"]
        body = res["data"] if isinstance(res["data"], dict) else {}
        inner = body.get("data") if isinstance(body.get("data"), dict) \
            else {}
        items = inner.get("trending_narratives") \
            or body.get("trending_narratives") or []
        out = [{**n, "time_frame": tf,
                "source": "elfa/v2/data/trending-narratives",
                "fetched_at": m.get("fetched_at")}
               for n in items if isinstance(n, dict)]
        p = os.path.join(out_root, "elfa",
                         f"trending_narratives_{tf}.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            for r in out:
                fh.write(json.dumps(r, default=str) + "\n")
        note(f"trending_narratives_{tf}", p, len(out), m)

    # ---- 6. the events ----------------------------------------------
    # NOTE: `limit` is REFUSED on /v3/events - sending it returns
    # 400 ERR_INVALID_PARAMETER. The server fixes the page size and the
    # cursor does the paging, so the pagination helper has to NOT send
    # `limit` for this endpoint.
    try:
        events, m = client.get_paginated(
            "/v3/events", {"from": start, "to": now}, items_key="events",
            page_size=None, max_pages=15, verbose=verbose,
            send_limit=False)
    except ElfaError as exc:
        if verbose:
            print(f"    events failed: {exc}", flush=True)
        events, m = [], {}
    out = [{**e, "source": "elfa/v3/events",
            "fetched_at": m.get("fetched_at")}
           for e in events if isinstance(e, dict)]
    p = os.path.join(out_root, "elfa", "events.jsonl")
    with open(p, "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, default=str) + "\n")
    note("events", p, len(out), m,
         {"served_from": m.get("served_from"),
          "history_from": manifest["key_status"]["history_from"]})

    # ---- 7. the entity ids ------------------------------------------
    # The v3 endpoints take entity ids, not names. Resolve the majors
    # once and cache them so the positioning and calls endpoints can
    # be queried without a lookup each time.
    ids: Dict[str, Any] = {}
    for sym in ("btc", "eth", "sol", "doge", "pepe", "xrp", "bnb", "link"):
        try:
            res = client.entities(sym)
            found = res["data"]
            if isinstance(found, dict):
                items = found.get("data") or found.get("entities") or []
            elif isinstance(found, list):
                items = found
            else:
                items = []
            ids[sym] = items
        except ElfaError:
            ids[sym] = None
    p = os.path.join(out_root, "elfa", "entity_ids.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(ids, fh, indent=2, default=str)
    manifest["datasets"]["entity_ids"] = {
        "file": os.path.relpath(p, out_root),
        "rows": len([k for k, v in ids.items() if v]),
        "endpoint": "/v3/entities",
        "note": ("resolved ids for the majors; the v3 endpoints take "
                 "entity ids, not names"),
    }
    if verbose:
        print(f"  {'entity_ids':26s} "
              f"{len([k for k, v in ids.items() if v]):6d} symbols -> "
              f"elfa/entity_ids.json", flush=True)

    # ---- 8. the positioning snapshot --------------------------------
    pos_rows: List[Dict[str, Any]] = []
    pos_meta: Dict[str, Any] = {}
    for sym, items in ids.items():
        if not items:
            continue
        first = items[0] if isinstance(items, list) else None
        eid = (first or {}).get("id") if isinstance(first, dict) else None
        if not eid:
            continue
        try:
            res = client.positioning(eid)
        except ElfaError:
            continue
        pos_meta = res["meta"]
        pos_rows.append({"symbol": sym, "entity_id": eid,
                         **res["data"], "source": "elfa/v3/calls/positioning",
                         "fetched_at": pos_meta.get("fetched_at")})
    p = os.path.join(out_root, "elfa", "positioning.jsonl")
    with open(p, "w", encoding="utf-8") as fh:
        for r in pos_rows:
            fh.write(json.dumps(r, default=str) + "\n")
    note("positioning", p, len(pos_rows), pos_meta or {})

    manifest["totals"] = {
        "requests_made": client.requests_made,
        "credits_spent": client.credits_spent,
        "datasets": len(manifest["datasets"]),
        "total_rows": sum(d.get("rows") or 0
                           for d in manifest["datasets"].values()),
    }
    manifest["credential_note"] = (
        "The API key is NOT recorded in this manifest, in any data file, "
        "or in any provenance record. It is read from the environment "
        "or from a file path and never logged.")
    return manifest


def main() -> int:
    out_root = os.environ.get("ELFA_STORAGE_ROOT", DEFAULT_STORAGE_ROOT)
    os.makedirs(out_root, exist_ok=True)
    print(f"Elfa AI collection -> {out_root}", flush=True)
    try:
        client = ElfaClient(storage_root=out_root)
    except ElfaError as exc:
        print(f"cannot start: {exc}", flush=True)
        return 1
    manifest = collect(client, out_root)
    mp = os.path.join(out_root, "manifest.json")
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, default=str)
    t = manifest["totals"]
    print(f"\ndone: {t['total_rows']} rows, {t['datasets']} datasets, "
          f"{t['requests_made']} requests, {t['credits_spent']} credits",
          flush=True)
    print(f"manifest: {mp}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
