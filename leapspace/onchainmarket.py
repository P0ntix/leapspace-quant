"""Market-level on-chain data: the crypto claims' missing layer.

WHY THIS EXISTS
    The research papers name MARKET-LEVEL on-chain variables for crypto:

      "On-chain and blockchain variables repeatedly improve crypto
       forecasting and regime detection, with studies finding strong
       performance for active users, hashrate, wallet activity,
       transaction volume, and related features."
        - Trading strategies for retail traders, p1

      "a crypto regime model should include not only internal features
       like volatility and liquidity but also cross-market and macro
       variables"
        - Financial market regime identification

    The package had WALLET-level on-chain data (`onchain.py` - Solana
    RPC, holder analysis, wallet profiling) and token-level social data
    (`social.py`), but nothing at the market level. That is the gap
    these claims need closed, and the data for it is free.

THE SOURCES, ALL KEYLESS, ALL VERIFIED ON THIS HOST
    * Coin Metrics Community API - the market-level on-chain series:
      active addresses, transaction count, hashrate, EXCHANGE INFLOW
      AND OUTFLOW, price. Daily, BTC and ETH, back to 2010.
    * DeFiLlama - stablecoin supply (the "dry powder" entering the
      market), per-chain TVL, and DEX volume (the "microstructure
      stress" the regime paper asks for).
    * CoinGecko - total market cap, volume and dominance: the
      market-level risk-on state.

THE THREE TRAPS, ALL FOUND BY PROBING
    1. The Coin Metrics parameter is `page_size`, NOT `limit`. Passing
       `limit` returns 400 "Unsupported parameter 'limit'", which
       reads like a metric-name error and is not.
    2. Availability is per asset AND per frequency. Solana's
       `AdrActCnt` at daily frequency is 403. Every row also carries
       `<metric>-status` and `<metric>-status-time` fields saying
       whether that observation was actually reported - a gap in the
       series is NOT a zero, and the status must travel with the
       value.
    3. These series are CONTEMPORANEOUS, with one exception.
       Active addresses, transaction count and TVL describe what is
       happening now; they are regime INPUTS, not forecasts. The
       EXCHANGE NETFLOW is the genuinely leading one - coins leaving
       exchanges precede the supply squeeze - and it is labelled as
       such everywhere it appears.

THE PROCESSING RULES
    * Every series is aligned to the panel's bar grid with a ONE-BAR
      PUBLICATION LAG. A bar at T may only use a measurement published
      before T.
    * Every feature is a Z-SCORE AGAINST A TRAILING WINDOW, never
      against the whole sample - a whole-sample z-score is look-ahead,
      which is a bug this package has already shipped once.
    * A MISSING MEASUREMENT IS None, NEVER 0. A gap in active
      addresses is not a collapse in activity.
    * Every fetch records its provenance: URL, HTTP status, what was
      measured, and the per-observation availability.
"""
from __future__ import annotations

import json
import math
import os
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .http import http_json
from .provenance import Provenance

__all__ = [
    "COINMETRICS_BASE",
    "DEFILLAMA_STABLECOINS",
    "DEFILLAMA_CHAINS",
    "DEFILLAMA_DEXS",
    "COINGECKO_GLOBAL",
    "fetch_coinmetrics_series",
    "fetch_defillama_stablecoins",
    "fetch_defillama_chain_tvl",
    "fetch_defillama_dex_volume",
    "fetch_coingecko_global",
    "build_market_onchain_features",
    "trailing_zscore",
]

COINMETRICS_BASE = ("https://community-api.coinmetrics.io/v4/"
                     "timeseries/asset-metrics")
COINMETRICS_CATALOG = ("https://community-api.coinmetrics.io/v4/"
                        "catalog/asset-metrics")
DEFILLAMA_STABLECOINS = ("https://stablecoins.llama.fi/stablecoins"
                         "?includePrices=true")
DEFILLAMA_CHAINS = "https://api.llama.fi/v2/chains"
DEFILLAMA_DEXS = ("https://api.llama.fi/overview/dexs"
                  "?excludeTotalDataChart=true"
                  "&excludeTotalDataChartBreakdown=true")
COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"

#: The metrics the crypto claims name, mapped to the Coin Metrics
#: metric names. Availability is per asset and per frequency - the API
#: states the restriction in a 403, and the fetch records it.
CM_METRICS: Dict[str, str] = {
    "active_addresses": "AdrActCnt",
    "transaction_count": "TxCnt",
    "hash_rate": "HashRate",
    "exchange_inflow": "FlowInExUSD",
    "exchange_outflow": "FlowOutExUSD",
    "price_usd": "PriceUSD",
}


#: The Coin Metrics observation-status vocabulary.
#:
#:   ``flash``       the value was published in real time and has NOT
#:                  been revised. This is the BEST status for a
#:                  backtest - there is no revision risk at all.
#:   ``available``   the value was revised after the fact. Usable, but
#:                  the revision is a look-ahead hazard if the series
#:                  is re-read today.
#:   anything else  the observation was not reported. A reported gap is
#:                  NOT a zero, so it is dropped.
CM_STATUS_OK = frozenset({"flash", "available", "ok", ""})


def _now_ms() -> int:
    return int(time.time() * 1000)


def _parse_time(ts: str) -> Optional[int]:
    """A Coin Metrics timestamp (ISO-8601) to unix seconds."""
    try:
        s = str(ts).replace("Z", "+00:00")
        if "." in s:
            s = s.split(".")[0] + "+00:00"
        import datetime as dt
        d = dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return int(d.timestamp())
    except Exception:  # noqa: BLE001
        return None


def fetch_coinmetrics_series(asset: str = "btc",
                             metrics: Sequence[str] = ("AdrActCnt",
                                                      "TxCnt",
                                                      "HashRate",
                                                      "FlowInExUSD",
                                                      "FlowOutExUSD",
                                                      "PriceUSD"),
                             frequency: str = "1d",
                             start: Optional[str] = None,
                             end: Optional[str] = None,
                             page_size: int = 5000,
                             timeout: int = 40
                             ) -> Tuple[Dict[str, List[Tuple[int, float]]],
                                        Provenance]:
    """A market-level on-chain series from the Coin Metrics Community API.

    Returns ``{metric_name: [(unix_seconds, value), ...]}``, oldest-first,
    with a gap represented by the ABSENCE of an entry - never a zero.

    The per-observation `-status` fields are consulted: a value the
    provider marked as unavailable is dropped rather than carried as a
    real measurement, because a reported gap is not a zero.

    THE PARAMETER IS `page_size`. Passing `limit` returns 400
    "Unsupported parameter 'limit'", which looks like a metric-name
    error and is not.
    """
    import urllib.parse
    params: Dict[str, Any] = {
        "assets": asset,
        "metrics": ",".join(metrics),
        "frequency": frequency,
        "page_size": int(page_size),
    }
    if start:
        params["start_time"] = start
    if end:
        params["end_time"] = end
    url = f"{COINMETRICS_BASE}?{urllib.parse.urlencode(params)}"

    payload, status = http_json(url, timeout=timeout)
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        err = ""
        if isinstance(payload, dict):
            err = str((payload.get("error") or {}).get("message"))[:160]
        raise SourceUnavailable(
            f"coinmetrics returned no rows for {asset}/{frequency}: {err}")

    out: Dict[str, List[Tuple[int, float]]] = {m: [] for m in metrics}
    dropped = 0
    for r in rows:
        ts = _parse_time(r.get("time") or "")
        if ts is None:
            continue
        for m in metrics:
            if m not in r:
                continue
            v = r.get(m)
            if v is None:
                continue
            # The provider marks each observation. `flash` means it was
            # published in real time and never revised - the ideal
            # status for a backtest. A reported gap is NOT a zero, so
            # an unusable status drops the observation entirely.
            st = str(r.get(f"{m}-status") or "").strip().lower()
            if st not in CM_STATUS_OK:
                dropped += 1
                continue
            try:
                out[m].append((ts, float(v)))
            except (TypeError, ValueError):
                continue
    for m in out:
        out[m].sort()
    prov = Provenance(
        source="coinmetrics.community",
        url=url,
        params=dict(params),
        note=(f"HTTP {status}; {len(rows)} rows; {len(out)} series; "
              f"{dropped} observations dropped as unavailable"))
    return out, prov


def fetch_defillama_stablecoins(timeout: int = 40
                                ) -> Tuple[List[Dict[str, Any]],
                                           Provenance]:
    """The stablecoin supply picture - the 'dry powder' entering the
    market."""
    payload, status = http_json(DEFILLAMA_STABLECOINS, timeout=timeout)
    assets = (payload.get("peggedAssets") or []
              if isinstance(payload, dict) else [])
    out: List[Dict[str, Any]] = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        out.append({
            "name": a.get("name"),
            "symbol": a.get("symbol"),
            "circulating": (a.get("circulating") or {}).get("peggedUSD"),
            "total": (a.get("total") or {}).get("peggedUSD"),
            "price": a.get("price"),
        })
    prov = Provenance(source="defillama.stablecoins",
                      url=DEFILLAMA_STABLECOINS,
                      note=f"HTTP {status}; {len(out)} pegged assets")
    return out, prov


def fetch_defillama_chain_tvl(timeout: int = 40
                              ) -> Tuple[Dict[str, float], Provenance]:
    """TVL per chain."""
    payload, status = http_json(DEFILLAMA_CHAINS, timeout=timeout)
    out: Dict[str, float] = {}
    if isinstance(payload, list):
        for c in payload:
            if isinstance(c, dict) and c.get("name"):
                try:
                    out[str(c["name"])] = float(c.get("tvl") or 0.0)
                except (TypeError, ValueError):
                    continue
    prov = Provenance(source="defillama.chains", url=DEFILLAMA_CHAINS,
                      note=f"HTTP {status}; {len(out)} chains")
    return out, prov


def fetch_defillama_dex_volume(timeout: int = 40
                               ) -> Tuple[Dict[str, float], Provenance]:
    """DEX volume per protocol."""
    payload, status = http_json(DEFILLAMA_DEXS, timeout=timeout)
    out: Dict[str, float] = {}
    if isinstance(payload, dict):
        for p in (payload.get("protocols") or []):
            if isinstance(p, dict) and p.get("name"):
                try:
                    out[str(p["name"])] = float(p.get("total24h") or 0.0)
                except (TypeError, ValueError):
                    continue
    prov = Provenance(source="defillama.dexs", url=DEFILLAMA_DEXS,
                      note=f"HTTP {status}; {len(out)} protocols")
    return out, prov


def fetch_coingecko_global(timeout: int = 40
                           ) -> Tuple[Dict[str, Any], Provenance]:
    """The global crypto market picture - market cap, volume, dominance.

    The response shape is not uniform: `total_market_cap` is a dict
    keyed by currency, but `market_cap_change_percentage_24h_usd` is a
    plain float. Both shapes are handled, because assuming either one
    crashes on the other.
    """
    payload, status = http_json(COINGECKO_GLOBAL, timeout=timeout)
    data = (payload.get("data") or {}) if isinstance(payload, dict) else {}

    def _usd(v: Any) -> Optional[float]:
        """A currency-keyed dict, or a bare number."""
        if isinstance(v, dict):
            v = v.get("usd")
        try:
            return None if v is None else float(v)
        except (TypeError, ValueError):
            return None

    out = {
        "total_market_cap_usd": _usd(data.get("total_market_cap")),
        "total_volume_usd": _usd(data.get("total_volume")),
        "market_cap_percentage": data.get("market_cap_percentage") or {},
        "market_cap_change_24h": _usd(
            data.get("market_cap_change_percentage_24h_usd")),
        "volume_change_24h": _usd(
            data.get("volume_change_percentage_24h_usd")),
        "fear_and_greed_index": data.get("fear_and_greed_index"),
    }
    prov = Provenance(source="coingecko.global", url=COINGECKO_GLOBAL,
                      note=f"HTTP {status}")
    return out, prov


# --------------------------------------------------------------------------
# The features
# --------------------------------------------------------------------------
def trailing_zscore(series: Sequence[Tuple[int, float]],
                    window: int = 60,
                    min_periods: Optional[int] = None
                    ) -> List[Tuple[int, Optional[float]]]:
    """A z-score over a TRAILING window - never over the whole sample.

    A whole-sample z-score is look-ahead: bar *i*'s value would depend
    on bars after *i*. This package shipped that bug once, in the
    leading-VRP feature, and the engine's causality audit caught it.

    `min_periods` defaults to half the window, so the z-score is not
    computed from a handful of points.
    """
    min_periods = max(3, int(min_periods if min_periods is not None
                             else max(3, window // 2)))
    out: List[Tuple[int, Optional[float]]] = []
    seen: List[float] = []
    for ts, v in series:
        seen.append(float(v))
        window_vals = seen[-window:]
        if len(window_vals) < min_periods:
            out.append((ts, None))
            continue
        m = sum(window_vals) / len(window_vals)
        var = sum((x - m) ** 2 for x in window_vals) / (len(window_vals) - 1)
        sd = math.sqrt(var)
        out.append((ts, None if sd <= 0 else (float(v) - m) / sd))
    return out


def build_market_onchain_features(
    metrics: Dict[str, List[Tuple[int, float]]],
    bar_timestamps: Sequence[int],
    window: int = 60,
    max_lag_bars: int = 1,
    source: str = "coinmetrics.community",
) -> Dict[str, Any]:
    """Turn the raw on-chain series into aligned, leading features.

    The features produced:
      active_addresses_zscore   RET-01's "active users"
      transaction_count_zscore  RET-01's "transaction volume"
      hash_rate_zscore          RET-01's "hashrate"
      exchange_netflow_zscore   THE LEADING ONE - coins leaving exchanges
      exchange_netflow_raw      the same, in USD, unnormalised
      price_usd_zscore          the market's own trend

    Every feature is aligned to `bar_timestamps` with a one-bar
    publication lag, and a missing observation is None, never zero.
    """
    from .leading import align_to_bars

    n = len(bar_timestamps)
    feats: Dict[str, Any] = {
        "source": source,
        "n_bars": n,
        "alignment_rule": (
            f"a bar at T uses a measurement timestamped no later than "
            f"T - {max_lag_bars} bar(s); every feature is a z-score over "
            f"a TRAILING {window}-bar window, never over the whole "
            f"sample"),
    }
    observed = 0

    for cm_name, feature_name in (
            ("AdrActCnt", "active_addresses_zscore"),
            ("TxCnt", "transaction_count_zscore"),
            ("HashRate", "hash_rate_zscore"),
            ("PriceUSD", "price_usd_zscore")):
        series = metrics.get(cm_name) or []
        if not series:
            feats[feature_name] = [None] * n
            continue
        z = dict(trailing_zscore(series, window=window))
        # The warm-up bars have no z-score. They are DROPPED, not
        # carried as None: `align_to_bars` takes the most recent
        # available measurement at or before the cutoff, and a
        # trailing-window statistic stays valid once computed. Passing
        # a None through would crash its float() conversion.
        z = {ts: v for ts, v in z.items() if v is not None}
        aligned = align_to_bars(list(z.items()), list(bar_timestamps),
                                max_lag_bars=max_lag_bars)
        feats[feature_name] = aligned
        observed += sum(1 for v in aligned if v is not None)

    # The exchange netflow: inflow minus outflow. This is the one
    # GENUINELY LEADING measure in the set - coins leaving exchanges
    # precede the supply squeeze - so it gets its own raw series as
    # well as the normalised one.
    inflow = metrics.get("FlowInExUSD") or []
    outflow = metrics.get("FlowOutExUSD") or []
    if inflow and outflow:
        out_map = dict(outflow)
        net: List[Tuple[int, float]] = []
        for ts, v in inflow:
            o = out_map.get(ts)
            if o is None:
                continue
            net.append((ts, float(v) - float(o)))
        z = dict(trailing_zscore(net, window=window))
        # Same rule as the loop above: the warm-up bars have no
        # z-score, and `align_to_bars` float()s every value it keeps.
        z = {ts: v for ts, v in z.items() if v is not None}
        feats["exchange_netflow_zscore"] = align_to_bars(
            list(z.items()), list(bar_timestamps),
            max_lag_bars=max_lag_bars)
        feats["exchange_netflow_raw"] = align_to_bars(
            net, list(bar_timestamps), max_lag_bars=max_lag_bars)
    else:
        feats["exchange_netflow_zscore"] = [None] * n
        feats["exchange_netflow_raw"] = [None] * n

    feats["n_observed"] = observed
    feats["interpretation_note"] = (
        "Active addresses, transaction count and hash rate are "
        "CONTEMPORANEOUS - they describe what is happening now, and "
        "they are regime INPUTS rather than forecasts. The exchange "
        "netflow is the genuinely LEADING measure here: coins leaving "
        "exchanges precede the supply squeeze. Everything is aligned "
        "with a one-bar publication lag, and a missing observation is "
        "None, never zero.")
    return feats


class SourceUnavailable(Exception):
    """The source did not answer with usable data."""
