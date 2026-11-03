"""The multi-chain memecoin registry.

The package originally screened Solana only. This module makes the chain
set explicit and keeps L1 and L2 TOKEN NETWORKS SEPARATE.

WHY THE SEPARATION MATTERS
--------------------------
Base, Arbitrum, Optimism, Robinhood Chain and the rest settle on Ethereum
and share its EVM execution environment. They are NOT the same token
network: each has its own gas token, its own DEX liquidity, its own
launchpads and its own memecoin market. A screener that treats "EVM" as
one venue misses almost every EVM-chain memecoin, and one that merges
Base into Ethereum attributes Base liquidity to Ethereum.

So every chain carries BOTH:
  layer          L1 | L2 | APPCHAIN  - the settlement architecture
  token_network  the chain's own token economy, never merged with its
                 settlement chain

DATA SOURCES PER CHAIN ARE NOT EQUAL
------------------------------------
A chain being in the registry does NOT mean the package can screen it.
Each entry records, separately: RPC status, DexScreener status, RugCheck
status and Jupiter status. RugCheck and Jupiter are SOLANA-ONLY (verified:
Jupiter returns no result for an Ethereum or Base token address; RugCheck's
path is a Solana mint path). For EVM chains the holder composition comes
from Transfer-log reconstruction instead, which is windowed and says so.

Every figure carries its source and the number of pools sampled, because
free APIs rate-limit and a sampled sum is a LOWER BOUND, not a total.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from .http import http_json
from .provenance import SourceUnavailable

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "data", "chain_registry.json")

#: Symbols that mark a pool as a MEMECOIN candidate. A heuristic, and
#: labelled as one - it is a pre-filter, not a verdict.
MEME_SYMBOL_HINTS = (
    "PEPE", "DOGE", "SHIB", "BONK", "WIF", "FLOKI", "BRETT", "MOG", "POPCAT",
    "PNUT", "TURBO", "SPX", "MOODENG", "TRUMP", "MEME", "CHILL", "PENGU",
    "AI16Z", "ZEREBRO", "GOAT", "NEIRO", "ACT", "FARTCOIN", "MEW", "BOME",
    "POPCAT", "MOTHER", "RETARDIO", "PNUT", "BULLY", "SIGMA", "FWOG",
    "HIGHER", "GIGA", "PNUT", "TOSHI", "USUAL", "MOG", "SNEJ", "MELANIA",
)


def load_registry(path: Optional[str] = None) -> Dict[str, Any]:
    p = path or REGISTRY_PATH
    try:
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        raise SourceUnavailable(f"chain registry unreadable at {p}: {exc}")


def chains(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """All registered chains, in rank order."""
    return list(load_registry(path).get("chains") or [])


def chain(chain_id: str, path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    for c in chains(path):
        if c.get("chain_id") == chain_id:
            return c
    return None


def top_chains(n: int = 10, path: Optional[str] = None) -> List[Dict[str, Any]]:
    """The top n chains, ranked by the BEST available measurement.

    Two volume figures live in the registry and they are NOT the same
    measure, so they are never mixed into one ranking:

      * DefiLlama per-chain DEX `total24h` - a complete single-number
        measurement of the chain's whole DEX volume.
      * GeckoTerminal per-pool `h24` sum - a page-limited sample of the
        top pools. A LOWER BOUND, not a chain total.

    Chains with the DefiLlama measurement rank first, by that value.
    Chains with only the sampled lower bound follow, clearly labelled.
    """
    cs = chains(path)
    measured = [c for c in cs if c.get("dex_volume_source", "")
                and "llama" in str(c.get("dex_volume_source"))]
    sampled = [c for c in cs if c not in measured]
    measured.sort(key=lambda c: -(c.get("dex_volume_24h_usd") or 0))
    sampled.sort(key=lambda c: -(c.get("dex_volume_24h_usd") or 0))
    return (measured + sampled)[:n]


def layer_split(path: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Chains grouped by layer. L1 and L2 are NEVER merged.

    `sidechain-L1` is the landscape survey's label for Polygon: a chain
    with its own validator set and its own token economy, so it groups
    with L1 for the split but keeps its precise label in the record.
    """
    out: Dict[str, List[Dict[str, Any]]] = {"L1": [], "L2": [], "APPCHAIN": []}
    for c in chains(path):
        layer = c.get("layer") or "L1"
        bucket = "L1" if layer.startswith("L1") or layer == "sidechain-L1" \
            else ("L2" if layer.startswith("L2") else "APPCHAIN")
        out.setdefault(bucket, []).append(c)
    return out


def screenable_chains(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Chains the package can actually screen: RPC + DexScreener both work.

    A chain with no working RPC can still be screened for social/market
    data through DexScreener, so the two are reported separately rather
    than as one boolean.
    """
    out = []
    for c in chains(path):
        dex_ok = c.get("dexscreener_status") == "ok"
        rpc_ok = c.get("rpc_status") == 200
        if dex_ok:
            out.append({**c,
                        "can_screen_market": True,
                        "can_read_chain_state": rpc_ok,
                        "holder_source": ("rugcheck" if c.get("family") == "SVM"
                                          else "evm_transfer_logs"),
                        "social_source": "dexscreener"})
    return out


def chain_health(path: Optional[str] = None) -> Dict[str, Any]:
    """A matrix of what works where, by capability rather than by chain."""
    cs = chains(path)
    return {
        "generated_at": int(time.time()),
        "total_chains": len(cs),
        "by_layer": {k: len(v) for k, v in layer_split(path).items()},
        "rpc_working": [c["chain_id"] for c in cs if c.get("rpc_status") == 200],
        "rpc_failing": [{"chain_id": c["chain_id"], "status": c.get("rpc_status"),
                         "note": c.get("measurement_gap", "")}
                        for c in cs if c.get("rpc_status") not in (200, None)],
        "rpc_unprobed": [c["chain_id"] for c in cs if c.get("rpc_status") is None],
        "dexscreener_working": [c["chain_id"] for c in cs
                                if c.get("dexscreener_status") == "ok"],
        "rugcheck_solana_only": [c["chain_id"] for c in cs
                                 if c.get("rugcheck_status") == "ok"],
        "jupiter_solana_only": [c["chain_id"] for c in cs
                                if c.get("jupiter_status") == "ok"],
        "note": ("RugCheck and Jupiter were verified to serve Solana only. "
                 "Jupiter returns no result for an Ethereum or Base token "
                 "address; RugCheck's path is a Solana mint path."),
    }


# --------------------------------------------------------------------------
# Chain-wide memecoin discovery
# --------------------------------------------------------------------------
def _num(v: Any) -> Optional[float]:
    """Coerce a value to float. GeckoTerminal returns NUMBERS AS STRINGS."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _gt_pools(network_id: str, pages: int = 2) -> List[Dict[str, Any]]:
    """Top pools of a GeckoTerminal network, with the token address."""
    out: List[Dict[str, Any]] = []
    for page in range(1, pages + 1):
        url = (f"https://api.geckoterminal.com/api/v2/networks/{network_id}"
               f"/pools?page={page}")
        try:
            data, _ = http_json(url, timeout=30)
        except Exception:  # noqa: BLE001
            break
        rows = (data or {}).get("data") or []
        if not rows:
            break
        for p in rows:
            at = p.get("attributes") or {}
            rel = (p.get("relationships") or {}).get("base_token") or {}
            token_id = ((rel.get("data") or {}).get("id")) or ""
            addr = token_id.split("_", 1)[1] if "_" in token_id else token_id
            vol = (at.get("volume_usd") or {}).get("h24")
            out.append({
                "pool_id": p.get("id"),
                "pool_name": at.get("name") or "",
                "token_address": addr,
                "symbol": (at.get("name") or "").split(" / ")[0].strip(),
                "price_usd": _num(at.get("base_token_price_usd")),
                "liquidity_usd": _num(at.get("reserve_in_usd")),
                "volume_24h_usd": _num(vol) or 0.0,
                "fdv_usd": _num(at.get("fdv_usd")),
                "market_cap_usd": _num(at.get("market_cap_usd")),
                "pool_created_at": at.get("pool_created_at"),
                "price_change_24h": _num(
                    (at.get("price_change_percentage") or {}).get("h24")),
                "source": f"geckoterminal:{network_id}",
            })
        time.sleep(2.0)
    return out


def discover_memecoins(chain_id: str, limit: int = 20, pages: int = 2,
                        meme_only: bool = True) -> Dict[str, Any]:
    """Find memecoin candidates on a chain from the chain's top pools.

    This is a PRE-FILTER on the chain's highest-volume pools. It is not a
    screening verdict: the full five-layer screen (liquidity, one-sidedness,
    price impact, launchpad funnel, RugCheck risk) runs afterwards in
    `memecoin.screen_search`.
    """
    spec = chain(chain_id)
    if not spec:
        return {"chain": chain_id, "status": "unknown_chain",
                "candidates": [],
                "gaps": [{"source": "chain_registry",
                          "reason": f"{chain_id} is not registered"}]}
    gt_id = spec.get("geckoterminal_id")
    if not gt_id:
        return {"chain": chain_id, "status": "no_volume_source",
                "layer": spec.get("layer"),
                "token_network": spec.get("token_network"),
                "candidates": [],
                "gaps": [{"source": "geckoterminal",
                          "reason": spec.get("measurement_gap",
                                             "no geckoterminal id")}]}
    pools = _gt_pools(gt_id, pages=pages)
    pools.sort(key=lambda p: -(p.get("volume_24h_usd") or 0.0))
    cands = []
    for p in pools:
        if meme_only:
            sym = (p.get("symbol") or "").upper()
            if not any(h in sym for h in MEME_SYMBOL_HINTS):
                continue
        if p.get("token_address"):
            cands.append(p)
        if len(cands) >= limit:
            break
    return {
        "chain": chain_id,
        "name": spec.get("name"),
        "layer": spec.get("layer"),
        "token_network": spec.get("token_network"),
        "layer_note": spec.get("layer_note"),
        "status": "ok",
        "pools_examined": len(pools),
        "candidates": cands,
        "candidate_count": len(cands),
        "prefilter": "symbol contains a known memecoin ticker (ANALYST_HEURISTIC)",
        "source": f"https://api.geckoterminal.com/api/v2/networks/{gt_id}/pools",
    }
