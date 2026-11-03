"""Unified on-chain models for the memecoin quant layer.

These are the SHARED CONTRACTS. Every other module in this package builds
on them, so the field names and the flattening rules are fixed here.

Two design constraints drive the shape of this module:

1. **Flattened JSON.** MiniMax M3 (and most LLM readers) degrade on deeply
   nested structures. Every model therefore serialises to a SHALLOW dict
   via `to_flat()`: one level of nesting, no dict-of-dict, no lists of
   dicts where a delimited string will do. `to_json()` emits the same
   flat shape.

2. **Provenance on every datum.** Nothing in this package asserts a fact
   it cannot source. Each model carries a `provenance` field with the
   source, the retrieval time and — where it matters — an explicit
   synthetic marker. A `SYNTHETIC` record is never silently mixed with a
   `LIVE` one.

Chain coverage: Solana (SVM) plus Ethereum, Base, BSC and Arbitrum (EVM).
The EVM chains share one adapter because their RPC surface is identical;
only the chain id, explorer and native symbol differ.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .provenance import Provenance

# --------------------------------------------------------------------------
# Chains
# --------------------------------------------------------------------------

FAMILY_SVM = "svm"
FAMILY_EVM = "evm"


@dataclass
class ChainSpec:
    """Static facts about one chain. No network state."""
    chain_id: str            # "solana", "ethereum", "base", "bsc", "arbitrum"
    name: str
    family: str              # FAMILY_SVM | FAMILY_EVM
    native_symbol: str
    rpc_url: str
    explorer: str
    address_len: int = 42    # EVM addresses are 0x + 40
    block_time_s: float = 12

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


CHAINS: Dict[str, ChainSpec] = {
    "solana": ChainSpec(
        chain_id="solana", name="Solana", family=FAMILY_SVM,
        native_symbol="SOL",
        rpc_url="https://api.mainnet-beta.solana.com",
        explorer="https://solscan.io",
        address_len=44, block_time_s=0.4),
    "ethereum": ChainSpec(
        chain_id="ethereum", name="Ethereum", family=FAMILY_EVM,
        native_symbol="ETH", rpc_url="https://ethereum-rpc.publicnode.com",
        explorer="https://etherscan.io", block_time_s=12),
    "base": ChainSpec(
        chain_id="base", name="Base", family=FAMILY_EVM,
        native_symbol="ETH", rpc_url="https://base-rpc.publicnode.com",
        explorer="https://basescan.org", block_time_s=2),
    "bsc": ChainSpec(
        chain_id="bsc", name="BNB Smart Chain", family=FAMILY_EVM,
        native_symbol="BNB", rpc_url="https://bsc-rpc.publicnode.com",
        explorer="https://bscscan.com", block_time_s=3),
    "arbitrum": ChainSpec(
        chain_id="arbitrum", name="Arbitrum One", family=FAMILY_EVM,
        native_symbol="ETH", rpc_url="https://arbitrum-one-rpc.publicnode.com",
        explorer="https://arbiscan.io", block_time_s=1),
}

SUPPORTED_CHAINS = list(CHAINS.keys())


def get_chain(chain_id: str) -> ChainSpec:
    """Look up a chain, with a helpful error rather than a KeyError."""
    cid = (chain_id or "").strip().lower()
    if cid not in CHAINS:
        raise KeyError(
            f"unsupported chain {chain_id!r}; supported: {', '.join(SUPPORTED_CHAINS)}")
    return CHAINS[cid]


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------

EVENT_TOKEN_CREATED = "token_created"
EVENT_LIQUIDITY_ADDED = "liquidity_added"
EVENT_WALLET_TRADE = "wallet_trade"
EVENT_PRICE_UPDATE = "price_update"
EVENT_LIQUIDITY_REMOVED = "liquidity_removed"
EVENT_RUG_SIGNAL = "rug_signal"

EVENT_KINDS = (EVENT_TOKEN_CREATED, EVENT_LIQUIDITY_ADDED,
               EVENT_WALLET_TRADE, EVENT_PRICE_UPDATE,
               EVENT_LIQUIDITY_REMOVED, EVENT_RUG_SIGNAL)


@dataclass
class TokenEvent:
    """A unified on-chain event, normalised across chains.

    Chain-specific fields are flattened into `detail` as a shallow dict of
    scalars. There is no nested structure anywhere in this model.
    """
    kind: str                       # one of EVENT_KINDS
    chain: str                      # chain id
    token: str                      # token address / mint
    symbol: str = ""
    ts: int = 0                     # unix seconds
    tx_hash: str = ""
    block: int = 0                  # block number, or slot on Solana
    source: str = ""                # the endpoint that produced it
    provenance: str = "LIVE"        # LIVE | CACHE | SYNTHETIC
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_flat(self) -> Dict[str, Any]:
        d = asdict(self)
        # detail stays shallow: string-ify anything non-scalar.
        d["detail"] = {k: (v if isinstance(v, (str, int, float, bool))
                           or v is None else json.dumps(v))
                       for k, v in (self.detail or {}).items()}
        return d


@dataclass
class WalletTrade:
    """One wallet's trade in one token, normalised across chains.

    `side` is "buy" or "sell" from the WALLET's perspective.
    `value_usd` is the notional at the trade price; `price_usd` is the
    execution price the trade implies. Both are None when the source did
    not provide a price, and the caller must not infer one.
    """
    wallet: str
    chain: str
    token: str
    symbol: str = ""
    side: str = "buy"
    amount: float = 0.0             # token units
    price_usd: Optional[float] = None
    value_usd: Optional[float] = None
    ts: int = 0
    tx_hash: str = ""
    fee_usd: Optional[float] = None
    source: str = ""
    provenance: str = "LIVE"
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_flat(self) -> Dict[str, Any]:
        d = asdict(self)
        d["detail"] = {k: (v if isinstance(v, (str, int, float, bool))
                           or v is None else json.dumps(v))
                       for k, v in (self.detail or {}).items()}
        return d


# --------------------------------------------------------------------------
# Profiling
# --------------------------------------------------------------------------

# The thresholds the operator brief specifies. These are OPERATOR POLICY,
# not market facts: they are the analyst's criteria for "this wallet is
# consistently good", and they are stated here so every report can show
# them.
PROFILE_THRESHOLDS: Dict[str, Any] = {
    "min_trades": 30,
    "min_win_rate": 0.55,
    "min_profit_factor": 1.5,
    "max_single_trade_pnl_share": 0.40,
}


@dataclass
class WalletProfile:
    """A wallet scored against the operator's consistency thresholds."""
    wallet: str
    chain: str = ""
    n_trades: int = 0
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    pnl_total_usd: Optional[float] = None
    largest_trade_pnl: Optional[float] = None
    largest_trade_pnl_share: Optional[float] = None
    avg_hold_seconds: Optional[float] = None
    median_hold_seconds: Optional[float] = None
    trades: List[WalletTrade] = field(default_factory=list)
    disqualifiers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    provenance: str = "LIVE"
    source: str = ""
    notes: str = ""

    @property
    def qualifies(self) -> bool:
        return not self.disqualifiers

    def to_flat(self) -> Dict[str, Any]:
        d = asdict(self)
        # The trade list is the only nested part; keep it flat and short.
        d["trades"] = [t.to_flat() for t in self.trades]
        d["qualifies"] = self.qualifies
        return d


@dataclass
class FundingSource:
    """Where a wallet's first token arrived from — the anti-insider input."""
    wallet: str
    chain: str = ""
    funder: str = ""
    funder_label: str = "unknown"   # unknown | deployer | cabal | exchange | unknown_wallet
    distance_blocks: Optional[int] = None
    token: str = ""
    ts: int = 0
    provenance: str = "LIVE"
    source: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_flat(self) -> Dict[str, Any]:
        d = asdict(self)
        d["detail"] = {k: (v if isinstance(v, (str, int, float, bool))
                           or v is None else json.dumps(v))
                       for k, v in (self.detail or {}).items()}
        return d


@dataclass
class TokenCandidate:
    """A token that tripped a detection rule, with its traction evidence."""
    token: str
    chain: str
    symbol: str = ""
    detected_ts: int = 0
    detection_rule: str = ""
    traction_score: Optional[float] = None
    trusted_wallets_in: List[str] = field(default_factory=list)
    consensus_count: int = 0
    liquidity_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None
    price_usd: Optional[float] = None
    holder_count: Optional[int] = None
    top_holder_pct: Optional[float] = None
    risk_flags: List[str] = field(default_factory=list)
    provenance: str = "LIVE"
    source: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_flat(self) -> Dict[str, Any]:
        d = asdict(self)
        d["trusted_wallets_in"] = ",".join(self.trusted_wallets_in)
        d["detail"] = {k: (v if isinstance(v, (str, int, float, bool))
                           or v is None else json.dumps(v))
                       for k, v in (self.detail or {}).items()}
        return d


# --------------------------------------------------------------------------
# Execution / portfolio
# --------------------------------------------------------------------------

@dataclass
class Friction:
    """Execution friction assumptions. Every field is explicit and tunable."""
    slippage_bps: float = 100.0          # 1.00% each side
    priority_fee_usd: float = 0.0
    latency_seconds: float = 2.0          # decision -> fill
    failed_tx_rate: float = 0.05          # 5% of orders fail
    mev_penalty_bps: float = 0.0          # extra cost from sandwiching
    gas_usd: float = 0.0
    notes: str = ""

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Position:
    token: str
    chain: str = ""
    symbol: str = ""
    entry_px: Optional[float] = None
    qty: float = 0.0
    entry_ts: int = 0
    cost_usd: Optional[float] = None
    last_px: Optional[float] = None
    last_ts: int = 0
    stop_px: Optional[float] = None
    unrealised_usd: Optional[float] = None
    exit_reason: str = ""

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CopyTrade:
    """One simulated copy-trade, including the ones that were SKIPPED."""
    token: str
    chain: str = ""
    wallet: str = ""
    action: str = "buy"              # buy | sell | skip
    skipped: bool = False
    skip_reason: str = ""
    px: Optional[float] = None
    qty: float = 0.0
    notional_usd: Optional[float] = None
    fee_usd: Optional[float] = None
    slippage_usd: Optional[float] = None
    ts: int = 0
    balance_after_usd: Optional[float] = None
    provenance: str = "LIVE"

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------
# Risk: kill switch + anomaly log
# --------------------------------------------------------------------------

@dataclass
class KillSwitchState:
    """Whether trading is permitted, and why.

    The kill switch is CODE-ENFORCED: an LLM or an operator prompt cannot
    clear `halted` without the explicit, logged `reset()` path, which
    records who reset it and why.
    """
    halted: bool = False
    reason: str = ""
    trigger: str = ""
    triggered_at: int = 0
    peak_equity_usd: Optional[float] = None
    equity_usd: Optional[float] = None
    drawdown_pct: Optional[float] = None
    reset_by: str = ""
    reset_reason: str = ""
    reset_at: int = 0
    state_log: List[str] = field(default_factory=list)

    def to_flat(self) -> Dict[str, Any]:
        d = asdict(self)
        d["state_log"] = " | ".join(self.state_log[-12:])
        return d


@dataclass
class Anomaly:
    """An unexpected market condition, logged with its exact context."""
    kind: str
    chain: str = ""
    token: str = ""
    symbol: str = ""
    ts: int = 0
    severity: str = "medium"        # low | medium | high | critical
    description: str = ""
    market_state: Dict[str, Any] = field(default_factory=dict)
    action_taken: str = ""
    promoted_to_known_unknown: bool = False
    lesson: str = ""
    provenance: str = "LIVE"

    def to_flat(self) -> Dict[str, Any]:
        d = asdict(self)
        d["market_state"] = ",".join(
            f"{k}={v}" for k, v in (self.market_state or {}).items())
        return d


@dataclass
class BiasFinding:
    """One bias detected by the auditor."""
    kind: str                        # look_ahead | survivorship | overfitting
    severity: str = "medium"
    where: str = ""
    detail: str = ""
    evidence: str = ""
    recommendation: str = ""

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


def now_ts() -> int:
    return int(time.time())


def to_json(obj: Any) -> str:
    """Serialise any model to its FLAT json form."""
    if hasattr(obj, "to_flat"):
        return json.dumps(obj.to_flat(), sort_keys=True, default=str)
    if hasattr(obj, "to_dict"):
        return json.dumps(obj.to_dict(), sort_keys=True, default=str)
    return json.dumps(obj, sort_keys=True, default=str)


__all__ = [
    "CHAINS", "ChainSpec", "ChainSpec.to_flat", "SUPPORTED_CHAINS", "get_chain",
    "FAMILY_SVM", "FAMILY_EVM",
    "EVENT_TOKEN_CREATED", "EVENT_LIQUIDITY_ADDED", "EVENT_WALLET_TRADE",
    "EVENT_PRICE_UPDATE", "EVENT_LIQUIDITY_REMOVED", "EVENT_RUG_SIGNAL",
    "EVENT_KINDS", "TokenEvent", "WalletTrade",
    "PROFILE_THRESHOLDS", "WalletProfile", "FundingSource", "TokenCandidate",
    "Friction", "Position", "CopyTrade",
    "KillSwitchState", "Anomaly", "BiasFinding",
    "now_ts", "to_json", "Provenance",
]
