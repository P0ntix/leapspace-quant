"""Holder-composition time series, and abrupt ownership change detection.

This is the meme-paper clause "abrupt ownership changes around price spikes".
The screener is stateless per call, so the clause needed infrastructure: a
STORE of timestamped holder-composition snapshots per token, and a detector
that compares consecutive snapshots.

WHY A TIME SERIES IS REQUIRED
-----------------------------
The clause is about a CHANGE, and a change needs two observations. A single
call can tell you a token is concentrated; it cannot tell you that ownership
just shifted. So this module keeps a per-token series:

    state/holder_series/<chain>_<mint>.json
        {"chain":..., "mint":..., "snapshots": [ {...}, {...} ]}

Each snapshot records holder composition AND the price at the same moment,
so a detector can ask "did concentration move at the same time as price?"

HOLDER SOURCES (all free, no API key required)
----------------------------------------------
  Solana : getTokenLargestAccounts -> top-20 token ACCOUNTS, then
           getMultipleAccounts (jsonParsed) to resolve the OWNING WALLET.
           A token account is not a wallet; using token accounts directly
           would compare pools and programs against each other and
           produce nonsense composition.
  EVM    : ERC-20 Transfer logs from eth_getLogs, reconstructed into net
           balances per address. Needs the token's decimals + totalSupply.

KNOWN-EXCLUSION ADDRESSES
--------------------------
DEX pools, token-program vaults and burn addresses are not holders. Leaving
them in inflates apparent concentration. The standard addresses are filtered
out and the FILTERED count is reported alongside the raw one, so the
exclusion is visible rather than silent.

METRIC THRESHOLDS
-----------------
The concentration bands come from the `token-holder-analysis` skill:
top-10% of supply  <30 low / 30-50 moderate / 50-80 high / >80 extreme;
Gini <0.6 very well distributed, 0.6-0.8 typical, 0.8-0.95 common for new
tokens, >0.95 extreme; HHI <1500 competitive, 1500-2500 moderate, >2500
concentrated; Nakamoto >10 / 5-10 / 2-4 / 1.

The DETECTION thresholds (spike size, composition delta) are ANALYST
CHOICES, not paper-stated values, and are labelled as such in the output.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .http import http_post_json
from .provenance import Provenance, SourceUnavailable

LIVE = "LIVE"

SERIES_DIR = os.path.join(os.path.dirname(__file__), "state", "holder_series")

# --- detection thresholds: ANALYST CHOICES, not paper-stated ---------------
# A price spike is "abrupt" at 50% over the window; a composition change is
# "abrupt" at a 10 percentage-point move in top-10 concentration or the
# appearance of a new address in the top 10. These are analyst choices and
# are labelled ANALYST_CHOICE in every output.
SPIKE_PCT_DEFAULT = 50.0
CONCENTRATION_DELTA_PP_DEFAULT = 10.0
MIN_SNAPSHOTS_DEFAULT = 2

# Well-known program / pool / burn addresses that are NOT holders.
# (from the `token-holder-analysis` skill's KNOWN_PROGRAMS list)
KNOWN_NON_HOLDERS_SOLANA = {
    "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",   # Raydium authority
    "GThUX1Atko4tqhN2NaiTazWSeFWMuiUvfFnyJyUghFMJ",   # Orca authority
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",   # Token program
    "11111111111111111111111111111111",               # System program
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "SoLFiHG9TfgtdUXUjWAxi3LtvYuFyDLVhBWxdMZxyCe",   # Burn
}
KNOWN_NON_HOLDERS_EVM = {
    "0x0000000000000000000000000000000000000000",      # mint / burn
    "0x000000000000000000000000000000000000dead",
    "0x0000000000000000000000000000000000000001",
}

TOP_N = 10


# --------------------------------------------------------------- metrics ----
def top_n_percentage(amounts: List[float], total: float, n: int = TOP_N) -> float:
    """Percentage of supply held by the top n addresses."""
    if not amounts or total <= 0:
        return 0.0
    return sum(sorted(amounts, reverse=True)[:n]) / total * 100.0


def gini_coefficient(amounts: List[float]) -> float:
    """Inequality of the holder distribution (0 = equal, 1 = one holder)."""
    if not amounts or all(a == 0 for a in amounts):
        return 0.0
    s = sorted(amounts)
    n = len(s)
    cumsum = sum((i + 1) * a for i, a in enumerate(s))
    total = sum(s)
    return (2 * cumsum) / (n * total) - (n + 1) / n


def hhi(amounts: List[float]) -> float:
    """Herfindahl-Hirschman Index of market shares (0-10000)."""
    total = sum(amounts)
    if total <= 0:
        return 0.0
    return sum((a / total * 100) ** 2 for a in amounts)


def nakamoto_coefficient(amounts: List[float]) -> int:
    """How many holders together control >51% of supply."""
    if not amounts:
        return 0
    total = sum(amounts)
    if total <= 0:
        return 0
    cumulative = 0.0
    for i, a in enumerate(sorted(amounts, reverse=True)):
        cumulative += a
        if cumulative >= total * 0.51:
            return i + 1
    return len(amounts)


def classify_concentration(top10_pct: float, gini: float) -> str:
    """Risk band from the token-holder-analysis skill's thresholds."""
    if top10_pct > 80:
        return "EXTREME"
    if top10_pct > 50:
        return "HIGH"
    if top10_pct > 30:
        return "MODERATE"
    return "LOW"


# ----------------------------------------------------------- solana source --
#: Minimum seconds between calls to one Solana RPC. Public endpoints
#: rate-limit hard: without a throttle the holder snapshot drew HTTP 429.
_SOL_MIN_INTERVAL = 0.9
_SOL_LAST_CALL: Dict[str, float] = {}


def _sol_rpc(url: str, method: str, params: List[Any],
             attempts: int = 4) -> Any:
    """Solana JSON-RPC with a throttle and backoff on rate limiting.

    Public Solana RPCs answer 429 under a burst. The holder snapshot makes
    several calls per token (largest accounts, then multiple-accounts), so
    without a throttle it reliably trips the limit.
    """
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    last: Optional[Exception] = None
    for attempt in range(attempts):
        gap = time.time() - _SOL_LAST_CALL.get(url, 0.0)
        if gap < _SOL_MIN_INTERVAL:
            time.sleep(_SOL_MIN_INTERVAL - gap)
        _SOL_LAST_CALL[url] = time.time()
        try:
            data, _ = http_post_json(url, body, timeout=30)
        except Exception as exc:  # noqa: BLE001
            last = exc
            if "429" in str(exc) and attempt < attempts - 1:
                time.sleep(2.5 * (attempt + 1))
                continue
            raise SourceUnavailable(f"solana rpc {method}: {exc}") from exc
        if isinstance(data, dict):
            if data.get("error"):
                err = data["error"]
                msg = err.get("message") if isinstance(err, dict) else str(err)
                raise SourceUnavailable(f"solana rpc {method}: {msg}")
            return data.get("result")
        return data
    raise SourceUnavailable(f"solana rpc {method} failed: {last}")


def solana_holder_composition(rpc_url: str, mint: str,
                               top_n: int = TOP_N) -> Dict[str, Any]:
    """Top holders of a Solana mint, resolved to OWNING WALLETS.

    getTokenLargestAccounts returns token ACCOUNTS. A token account is a
    program-owned container, not a person: two token accounts of the same
    wallet are two holders. So each account's owner is resolved with
    getMultipleAccounts before anything is aggregated.
    """
    accounts = _sol_rpc(rpc_url, "getTokenLargestAccounts", [mint])
    if not isinstance(accounts, list) or not accounts:
        raise SourceUnavailable(f"getTokenLargestAccounts returned no accounts "
                                f"for {mint}")
    token_accounts = [a.get("address") for a in accounts if a.get("address")]
    amounts = [float(a.get("uiAmount") or 0) for a in accounts]

    owners: Dict[str, float] = {}
    owner_of: Dict[str, str] = {}
    BATCH = 100
    for i in range(0, len(token_accounts), BATCH):
        batch = token_accounts[i:i + BATCH]
        res = _sol_rpc(rpc_url, "getMultipleAccounts",
                       [batch, {"encoding": "jsonParsed"}])
        for addr, acc in zip(batch, res or []):
            if not acc:
                continue
            try:
                info = acc["account"]["data"]["parsed"]["info"]
            except (KeyError, TypeError):
                continue
            owner = info.get("owner")
            token_amt = (info.get("tokenAmount") or {})
            amt = float(token_amt.get("uiAmountString")
                        or token_amt.get("uiAmount") or 0)
            if not owner or amt <= 0:
                continue
            owners[owner] = owners.get(owner, 0.0) + amt
            owner_of[owner] = owner

    if not owners:
        raise SourceUnavailable(
            f"no owner could be resolved for {mint} on solana - the RPC may "
            f"not support getMultipleAccounts jsonParsed for these accounts")

    supply_res = _sol_rpc(rpc_url, "getTokenSupply", [mint])
    total = 0.0
    try:
        total = float(supply_res["value"]["uiAmountString"])
    except (KeyError, TypeError, ValueError):
        total = sum(owners.values())

    rows = sorted(owners.items(), key=lambda kv: -kv[1])
    top = rows[:top_n]
    total_top = sum(v for _, v in top)
    excluded = [a for a in owners if a in KNOWN_NON_HOLDERS_SOLANA]
    if excluded:
        rows = [(a, v) for a, v in rows if a not in KNOWN_NON_HOLDERS_SOLANA]
        total = max(total - sum(owners[a] for a in excluded), 0.0)

    return {
        "holders": [{"address": a, "amount": v} for a, v in rows[:top_n]],
        "amounts": [v for _, v in rows[:top_n]],
        "total_supply": total,
        "holder_count": len(rows),
        "excluded_program_accounts": len(excluded),
        "source": "solana_rpc:getTokenLargestAccounts+getMultipleAccounts",
    }


# --------------------------------------------------------------- evm source --
def _evm_rpc(url: str, method: str, params: List[Any]) -> Any:
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    data, _ = http_post_json(url, body, timeout=40)
    if isinstance(data, dict):
        if data.get("error"):
            err = data["error"]
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise SourceUnavailable(f"evm rpc {method}: {msg}")
        return data.get("result")
    return data


def _evm_call(url: str, to: str, data: str) -> str:
    return _evm_rpc(url, "eth_call", [{"to": to, "data": data}, "latest"]) or "0x"


def evm_holder_composition(rpc_url: str, token: str, top_n: int = TOP_N,
                           blocks_back: int = 4000,
                           log_span_cap: int = 5000) -> Dict[str, Any]:
    """Reconstruct ERC-20 holders from Transfer logs.

    This is a WINDOWED reconstruction, not a global one: it covers only the
    transfer logs visible in the scanned block range. A token whose early
    transfers predate the window will show an incomplete distribution. The
    scanned range is reported so the reader knows the coverage.
    """
    latest_hex = _evm_rpc(rpc_url, "eth_blockNumber", [])
    latest = int(latest_hex, 16)
    span = min(blocks_back, log_span_cap)
    frm = hex(max(0, latest - span))

    transfer_topic = ("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a1162"
                      "8f55a4df523b3ef")
    request = [{"fromBlock": frm, "toBlock": hex(latest),
                "topics": [transfer_topic], "address": token}]
    try:
        logs = _evm_rpc(rpc_url, "eth_getLogs", request)
    except SourceUnavailable as exc:
        # Free public RPCs cap eth_getLogs. Base's error literally names the
        # range it WILL accept ("retry with the range A-B"), so use it.
        rng = re.search(r"range (\d+)-(\d+)", str(exc))
        if not rng:
            raise
        lo, hi = int(rng.group(1)), int(rng.group(2))
        logs = _evm_rpc(rpc_url, "eth_getLogs",
                        [{"fromBlock": hex(lo), "toBlock": hex(hi),
                          "topics": [transfer_topic], "address": token}])
        frm, span = hex(lo), hi - lo + 1
    if not isinstance(logs, list):
        raise SourceUnavailable("eth_getLogs returned no log array for "
                                f"{token}")

    dec_hex = _evm_call(rpc_url, token, "0x313ce567")
    sup_hex = _evm_call(rpc_url, token, "0x18160ddd")
    try:
        decimals = int(dec_hex, 16)
    except (TypeError, ValueError):
        decimals = 18
    try:
        total_supply = int(sup_hex, 16) / (10 ** decimals)
    except (TypeError, ValueError):
        total_supply = 0.0

    balances: Dict[str, float] = {}
    for lg in logs:
        topics = lg.get("topics") or []
        if len(topics) < 3:
            continue
        frm_a = "0x" + str(topics[1])[-40:].lower()
        to_a = "0x" + str(topics[2])[-40:].lower()
        try:
            value = int(lg.get("data", "0x0"), 16) / (10 ** decimals)
        except (TypeError, ValueError):
            continue
        balances[frm_a] = balances.get(frm_a, 0.0) - value
        balances[to_a] = balances.get(to_a, 0.0) + value

    excluded = [a for a in balances if a in KNOWN_NON_HOLDERS_EVM]
    for a in excluded:
        balances.pop(a, None)
    positive = {a: v for a, v in balances.items() if v > 0e-12}
    rows = sorted(positive.items(), key=lambda kv: -kv[1])

    return {
        "holders": [{"address": a, "amount": v} for a, v in rows[:top_n]],
        "amounts": [v for _, v in rows[:top_n]],
        "total_supply": total_supply,
        "holder_count": len(rows),
        "excluded_program_accounts": len(excluded),
        "coverage": {"from_block": frm, "to_block": hex(latest),
                     "blocks_scanned": span,
                     "logs_seen": len(logs),
                     "note": ("WINDOWED reconstruction: covers only transfers "
                              "inside the scanned block range. Free public "
                              "RPC caps eth_getLogs ranges.")},
        "source": "evm_rpc:eth_getLogs(Transfer)",
    }


def rugcheck_holder_composition(mint: str, top_n: int = TOP_N
                                 ) -> Dict[str, Any]:
    """Holder composition from RugCheck's FULL report (Solana).

    This is the best free Solana holder source: RugCheck resolves each
    token account to its OWNING WALLET and publishes the percentage of
    supply, plus an `insider` flag per holder. The RPC path
    (getTokenLargestAccounts) needs a throttled public endpoint and
    gives no insider flags, so this is the primary and the RPC is the
    fallback.

    `pct` is the holder's share of supply, so composition is computed
    from percentages rather than raw amounts - which also sidesteps the
    decimals mismatch between different sources.
    """
    from .memecoin import fetch_rugcheck
    try:
        report, _ = fetch_rugcheck(mint)
    except Exception as exc:  # noqa: BLE001
        raise SourceUnavailable(f"rugcheck full report {mint}: {exc}")

    rows = []
    for h in (report.get("top_holders") or [])[:top_n]:
        addr = h.get("owner") or h.get("address")
        if not addr:
            continue
        rows.append({"address": addr,
                     "pct": h.get("pct"),
                     "insider": bool(h.get("insider"))})
    if not rows:
        raise SourceUnavailable(f"rugcheck returned no top holders for {mint}")

    total_pct = sum(float(r.get("pct") or 0.0) for r in rows)
    return {
        "holders": rows,
        "amounts": [float(r.get("pct") or 0.0) for r in rows],
        "total_supply": 100.0,
        "holder_count": report.get("total_holders"),
        "insider_count": sum(1 for r in rows if r.get("insider")),
        "top_holders_pct_covered": round(total_pct, 3),
        "excluded_program_accounts": 0,
        "source": "rugcheck.report:topHolders",
    }


# ------------------------------------------------------------- snapshotting --
def _series_path(chain: str, mint: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in mint)[:66]
    return os.path.join(SERIES_DIR, f"{chain}_{safe}.json")


def load_series(chain: str, mint: str) -> Dict[str, Any]:
    path = _series_path(chain, mint)
    if not os.path.exists(path):
        return {"chain": chain, "mint": mint, "snapshots": []}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"chain": chain, "mint": mint, "snapshots": []}


def save_series(chain: str, mint: str, series: Dict[str, Any]) -> str:
    os.makedirs(SERIES_DIR, exist_ok=True)
    path = _series_path(chain, mint)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(series, fh, indent=2)
    os.replace(tmp, path)
    return path


def record_snapshot(chain: str, mint: str, composition: Dict[str, Any],
                    price_usd: Optional[float], price_change_24h: Optional[float],
                    provenance: str = LIVE,
                    source: str = "") -> Dict[str, Any]:
    """Append one timestamped holder-composition snapshot to the series."""
    amounts = [float(a) for a in composition.get("amounts", [])]
    total = float(composition.get("total_supply") or 0.0)
    if not total:
        total = sum(amounts)
    top10 = top_n_percentage(amounts, total, TOP_N)
    g = gini_coefficient(amounts)
    h = hhi(amounts)
    nk = nakamoto_coefficient(amounts)

    snap: Dict[str, Any] = {
        "ts": int(time.time()),
        "price_usd": price_usd,
        "price_change_24h": price_change_24h,
        "total_supply": total,
        "holder_count": composition.get("holder_count"),
        "top_holders": composition.get("holders", [])[:TOP_N],
        "metrics": {
            "top1_pct": top_n_percentage(amounts, total, 1),
            "top5_pct": top_n_percentage(amounts, total, 5),
            "top10_pct": top10,
            "gini": round(g, 4),
            "hhi": round(h, 1),
            "nakamoto": nk,
            "risk_band": classify_concentration(top10, g),
        },
        "provenance": provenance,
        "source": source or composition.get("source", ""),
    }
    if composition.get("coverage"):
        snap["coverage"] = composition["coverage"]

    series = load_series(chain, mint)
    series.setdefault("chain", chain)
    series.setdefault("mint", mint)
    series.setdefault("snapshots", [])
    series["snapshots"].append(snap)
    series["snapshots"].sort(key=lambda s: s.get("ts", 0))
    save_series(chain, mint, series)
    return snap


# ------------------------------------------------------------- the detector --
def detect_ownership_shifts(chain: str, mint: str,
                            spike_pct: float = SPIKE_PCT_DEFAULT,
                            concentration_delta_pp: float =
                            CONCENTRATION_DELTA_PP_DEFAULT,
                            min_snapshots: int = MIN_SNAPSHOTS_DEFAULT
                            ) -> Dict[str, Any]:
    """Find windows where composition changed abruptly around a price spike.

    A window is flagged when ALL of these hold:
      * price moved by at least `spike_pct` (either direction)
      * top-10 concentration moved by at least `concentration_delta_pp`
      * OR a NEW address entered the top-10 that was not in the previous
        snapshot's top-10 (a swap of control, not just drift)
    """
    series = load_series(chain, mint)
    snaps = series.get("snapshots") or []
    out: Dict[str, Any] = {
        "chain": chain, "mint": mint,
        "n_snapshots": len(snaps),
        "status": "insufficient_history" if len(snaps) < min_snapshots
                  else "computed",
        "shifts": [],
        "thresholds": {
            "price_spike_pct": spike_pct,
            "concentration_delta_pp": concentration_delta_pp,
            "min_snapshots": min_snapshots,
            "label": "ANALYST_CHOICE - not a paper-stated value",
        },
        "note": ("Ownership change is only detectable between snapshots. "
                 "With fewer than two snapshots there is nothing to compare, "
                 "and that is reported rather than filled in."),
    }
    if len(snaps) < min_snapshots:
        return out

    for prev, cur in zip(snaps, snaps[1:]):
        p0 = prev.get("price_usd")
        p1 = cur.get("price_usd")
        if not p0 or not p1:
            continue
        price_move = (float(p1) / float(p0) - 1.0) * 100.0
        m0 = prev.get("metrics", {})
        m1 = cur.get("metrics", {})
        c0 = float(m0.get("top10_pct") or 0.0)
        c1 = float(m1.get("top10_pct") or 0.0)
        delta_pp = c1 - c0
        prev_addrs = {h.get("address") for h in (prev.get("top_holders") or [])}
        cur_addrs = {h.get("address") for h in (cur.get("top_holders") or [])}
        newcomers = sorted(a for a in cur_addrs - prev_addrs if a)
        left = sorted(a for a in prev_addrs - cur_addrs if a)

        price_spike = abs(price_move) >= spike_pct
        concentration_shift = abs(delta_pp) >= concentration_delta_pp
        control_swap = bool(newcomers)
        if not (price_spike and (concentration_shift or control_swap)):
            continue

        out["shifts"].append({
            "from_ts": prev.get("ts"), "to_ts": cur.get("ts"),
            "window_seconds": int(cur.get("ts", 0) - prev.get("ts", 0)),
            "price_from": p0, "price_to": p1,
            "price_move_pct": round(price_move, 2),
            "top10_from_pct": round(c0, 2), "top10_to_pct": round(c1, 2),
            "concentration_delta_pp": round(delta_pp, 2),
            "gini_from": m0.get("gini"), "gini_to": m1.get("gini"),
            "hhi_from": m0.get("hhi"), "hhi_to": m1.get("hhi"),
            "nakamoto_from": m0.get("nakamoto"),
            "nakamoto_to": m1.get("nakamoto"),
            "new_top10_addresses": newcomers[:5],
            "departed_top10_addresses": left[:5],
            "triggers": [t for t, ok in (("price_spike", price_spike),
                                         ("concentration_shift",
                                          concentration_shift),
                                         ("top10_control_swap", control_swap))
                         if ok],
            "interpretation": ("Ownership shifted around a price move"
                               if control_swap else
                               "Concentration changed around a price move"),
        })
    out["n_shifts"] = len(out["shifts"])
    out["status"] = "computed"
    return out
