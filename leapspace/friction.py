"""
Friction-aware meme-coin backtesting: slippage, latency, fees, failed
transactions, rug injection, MEV sandwiches and a finite-bankroll
copy-trading simulator.

WHY THIS EXISTS
---------------
A backtest that fills at the price you saw when you decided is fiction.
On-chain execution is slow, expensive and adversarial:

  * you decide at t, the transaction lands at t + latency, at whatever
    the price is THEN (never the price you saw);
  * the order pays slippage, a priority fee and gas;
  * a fraction of transactions simply fail (mev protection, slippage
    tolerance, congestion) and the gas is burned anyway;
  * other bots sandwich your order and push the fill against you;
  * the token you bought may be rugged at any moment (80-99% instant
    drops, LP pulled, liquidity gone).

This module makes all five explicit, CODE-ENFORCED and AUDITABLE. The
stop-loss and take-profit levels are enforced in the simulator code, not
left to the caller; skipped trades are always recorded with a reason;
the bankroll can never go negative; every random draw comes from an
explicit `random.Random(seed)` so a run is bit-for-bit reproducible.

COMPARABILITY WITH THE BAR-BASED ENGINE
----------------------------------------
The strategy-backtest-lab engine (`btengine.DEFAULT_COSTS`) charges, for
crypto: 10 bps commission + 5 bps half-spread + 5 bps slippage + 30 bps
borrow. This module is a SEPARATE simulator (copy-trading of memecoins,
not a bar-based strategy), but its friction knobs are expressed in the
same units (bps of notional, USD fees) so the numbers can be compared
directly: `Friction(slippage_bps=100)` is a 1% adverse move per side,
which is ~20x the engine's 5 bps crypto slippage -- appropriate for a
thin meme-coin pool.

DETERMINISM CONTRACT
--------------------
Every random number comes from a `random.Random` instance owned by the
object that needs it. The global `random` module is never used. Given
the same seed, the same inputs and the same configuration, this module
produces identical output on every run.

PROVENANCE CONTRACT
-------------------
Price series and trade lists carry `LIVE` (fetched during this run),
`CACHE` (read from a local cache of a real fetch) or `SYNTHETIC`
(generated here). Synthetic data is never presented as market data: the
simulation result states the provenance of the price series AND of the
signal list separately, because a simulation can mix a LIVE price series
with SYNTHETIC signals.

LIVE TRADING NOTE (not simulated here)
--------------------------------------
In live trading, rug risk is screened BEFORE entry: LP lock status and
holder concentration are checked by `leapspace.memecoin.screen_meme_coin`
(top-holder %, top-10 %, liquidity, RugCheck score). This module injects
the corresponding EVENTS into history so a strategy can be tested against
tokens that would have been rugged.
"""

from __future__ import annotations

import bisect
import datetime as _dt
import json
import random
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .models import CopyTrade, Friction, Position, TokenCandidate, WalletTrade
from .provenance import CACHE, LIVE, SYNTHETIC, Provenance, SourceUnavailable

__all__ = [
    "Fill", "FrictionModel", "PriceSeries",
    "RugConfig", "RugEvent", "RugInjector",
    "MEVConfig", "MEVOrder", "MEVEvent", "MEVSimulator",
    "CopyConfig", "TradeRecord", "SimulationResult", "CopyTradeSimulator",
    "run_simulation", "price_at_or_before", "MIN_TRADE_USD",
]

# The smallest trade the simulator will open. Below this the free cash is
# treated as LOCKED (the money is tied up in open positions) and the signal
# is recorded as skipped with a reason, rather than opening a dust trade.
MIN_TRADE_USD = 1.0


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def _f(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def price_at_or_before(series: Sequence[Tuple[int, float]],
                        ts: int) -> Optional[Tuple[int, float]]:
    """The most recent price observable at `ts` (never a future price).

    This is the look-ahead guard: a decision at t with latency L fills at
    the price known at t+L, which is this function applied to t+L.
    """
    if not series:
        return None
    times = [t for t, _ in series]
    i = bisect.bisect_right(times, int(ts)) - 1
    if i < 0:
        return None
    return series[i]


class PriceSeries:
    """A sorted (ts, px) series with O(log n) causal price lookup."""

    def __init__(self, points: Iterable[Tuple[int, float]]):
        pts = sorted((int(t), _f(p)) for t, p in points
                     if p is not None and _f(p) > 0.0)
        self.points: List[Tuple[int, float]] = pts
        self.times: List[int] = [t for t, _ in pts]
        self.prices: List[float] = [p for _, p in pts]

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self):
        return iter(self.points)

    def at_or_before(self, ts: int) -> Optional[Tuple[int, float]]:
        if not self.points:
            return None
        i = bisect.bisect_right(self.times, int(ts)) - 1
        if i < 0:
            return None
        return self.times[i], self.prices[i]

    def last(self) -> Optional[Tuple[int, float]]:
        return self.points[-1] if self.points else None


# --------------------------------------------------------------------------
# 1. FrictionModel
# --------------------------------------------------------------------------

@dataclass
class Fill:
    """The outcome of one simulated order."""
    px: Optional[float] = None          # final execution price (None if failed)
    qty: float = 0.0                    # token units transacted
    slippage_usd: float = 0.0           # cost attributable to slippage
    mev_usd: float = 0.0                # cost attributable to the sandwich
    fees_usd: float = 0.0               # priority fee + gas (burned either way)
    failed: bool = False
    reason: str = ""

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


class FrictionModel:
    """Execution friction, wrapping the shared `models.Friction` contract.

    `sandwich_probability` lives here rather than in `models.Friction`
    because the shared contract has no such field and it must not be
    modified by this module.
    """

    def __init__(self, friction: Optional[Friction] = None,
                 sandwich_probability: float = 1.0):
        self.friction: Friction = friction or Friction()
        self.sandwich_probability = max(0.0, min(1.0, float(sandwich_probability)))

    # -- accessors -------------------------------------------------------
    @property
    def slippage_bps(self) -> float:
        return _f(self.friction.slippage_bps)

    @property
    def mev_penalty_bps(self) -> float:
        return _f(self.friction.mev_penalty_bps)

    @property
    def failed_tx_rate(self) -> float:
        return _f(self.friction.failed_tx_rate)

    @property
    def latency_seconds(self) -> float:
        return _f(self.friction.latency_seconds)

    @property
    def priority_fee_usd(self) -> float:
        return _f(self.friction.priority_fee_usd)

    @property
    def gas_usd(self) -> float:
        return _f(self.friction.gas_usd)

    # -- primitives ------------------------------------------------------
    def apply_slippage(self, px: float, side: str) -> float:
        """Adverse slippage: buys pay up, sells receive less."""
        px = _f(px)
        if px <= 0.0:
            return px
        adj = self.slippage_bps / 10_000.0
        if side == "buy":
            return px * (1.0 + adj)
        if side == "sell":
            return px * (1.0 - adj)
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")

    def apply_mev(self, px: float, side: str, rng: random.Random,
                  qty: Optional[float] = None) -> Tuple[float, float]:
        """Sandwich penalty from a front-running bot.

        `friction.mev_penalty_bps` is the MAXIMUM penalty; the actual
        penalty is sampled uniformly in [0, max] and only bites when the
        trade is sandwiched at all (probability `sandwich_probability`).

        Returns (px_after, penalty_usd). `penalty_usd` is the dollar
        penalty for `qty` tokens; with `qty=None` it is the per-token
        dollar penalty.
        """
        px = _f(px)
        if px <= 0.0 or self.mev_penalty_bps <= 0.0:
            return px, 0.0
        if rng.random() >= self.sandwich_probability:
            return px, 0.0
        bps = rng.uniform(0.0, self.mev_penalty_bps)
        delta = px * bps / 10_000.0
        px_after = px + delta if side == "buy" else max(0.0, px - delta)
        units = 1.0 if qty is None else _f(qty)
        return px_after, delta * units

    def total_cost_usd(self, notional: float,
                       priority_fee: Optional[float] = None,
                       gas: Optional[float] = None) -> float:
        """Modelled friction cost of a trade of `notional` USD.

        = slippage on the notional + priority fee + gas.
        MEV is extra and is priced by `simulate_fill` (it depends on the
        fill price, not on the notional alone).
        """
        notional = _f(notional)
        pri = self.priority_fee_usd if priority_fee is None else _f(priority_fee)
        gas_u = self.gas_usd if gas is None else _f(gas)
        return notional * self.slippage_bps / 10_000.0 + pri + gas_u

    def simulate_fill(self, px: float, side: str, notional: float,
                      rng: random.Random) -> Fill:
        """Simulate one order end to end.

        `px` is the reference (decision-time) price, `notional` the USD
        size of the trade. The fill happens at a worse price; with
        probability `failed_tx_rate` the transaction fails, no units
        change hands and the fees are still burned.

        Money model:
          BUY  -- the USD budget is `notional` (plus fees); the units
                  received are notional / fill price, so slippage and the
                  sandwich show up as FEWER units, not as extra cash.
          SELL -- the units are fixed (notional / reference price) and
                  the proceeds are units * fill price, so slippage and
                  the sandwich show up as LESS cash.
        """
        ref = _f(px)
        notional = _f(notional)
        fees = self.priority_fee_usd + self.gas_usd
        if ref <= 0.0 or notional <= 0.0:
            return Fill(px=ref, qty=0.0, fees_usd=fees, failed=True,
                        reason="invalid order (price or notional <= 0)")
        if rng.random() < self.failed_tx_rate:
            return Fill(px=None, qty=0.0, fees_usd=fees, failed=True,
                        reason=("transaction failed (simulated): priority fee "
                                "and gas burned, no fill"))
        px_slip = self.apply_slippage(ref, side)
        # The MEV sample does not need the quantity; the dollar penalty is
        # computed once the quantity is known.
        px_fill, per_token_mev = self.apply_mev(px_slip, side, rng)
        if side == "buy":
            qty = notional / px_fill
            slippage_usd = qty * (px_slip - ref)
            mev_usd = qty * (px_fill - px_slip)
        else:
            qty = notional / ref
            slippage_usd = qty * (ref - px_slip)
            mev_usd = qty * (px_slip - px_fill)
        if side == "sell" and px_fill <= 0.0:
            qty = 0.0
            slippage_usd = 0.0
            mev_usd = 0.0
        return Fill(px=px_fill, qty=qty, slippage_usd=slippage_usd,
                    mev_usd=mev_usd, fees_usd=fees, failed=False, reason="")

    def latency_shift(self, ts: int,
                      latency_seconds: Optional[float] = None) -> int:
        """Execution timestamp: the decision time moved LATER.

        The fill price must be the price AT this shifted time.
        """
        lat = self.latency_seconds if latency_seconds is None else _f(latency_seconds)
        if lat < 0.0:
            lat = 0.0
        return int(ts) + int(round(lat))


# --------------------------------------------------------------------------
# 2. RugInjector
# --------------------------------------------------------------------------

@dataclass
class RugConfig:
    """How rugs are injected into a historical price series."""
    rug_probability: float = 0.10        # per holding period
    min_drop_pct: float = 80.0           # operator brief: 80-99%
    max_drop_pct: float = 99.0
    liquidity_vanish_probability: float = 0.0
    holding_period_bars: int = 1         # bars in one holding period
    seed: int = 0
    notes: str = ""

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RugEvent:
    """One injected rug / liquidity removal, recorded for audit."""
    ts: int = 0
    index: int = 0
    kind: str = "rug"                    # rug | liquidity_vanish
    token: str = ""                     # which token was rugged
    before_px: float = 0.0
    after_px: float = 0.0
    drop_pct: float = 0.0
    detected_as_rug: bool = True         # liquidity_vanish may go unnoticed
    note: str = ""

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


class RugInjector:
    """Inject random rug pulls (80-99% drops) into a price series.

    Deterministic for a given seed. Every injected event is recorded with
    its timestamp, the price before and after, and the drop percentage.
    A rug is permanent: the whole later price path is scaled down, so a
    position open across the rug is marked at the post-rug price.
    """

    def __init__(self, config: Optional[RugConfig] = None):
        self.config: RugConfig = config or RugConfig()
        self.events: List[RugEvent] = []

    def inject(self, points: Sequence[Tuple[int, float]],
               token: str = "") -> Tuple[List[Tuple[int, float]],
                                        List[RugEvent]]:
        """Return (rugged series, events). The input is not modified."""
        cfg = self.config
        pts = sorted((int(t), _f(p)) for t, p in points)
        times = [t for t, _ in pts]
        prices = [p for _, p in pts]
        rng = random.Random(cfg.seed)
        hp = max(1, int(cfg.holding_period_bars))
        n = len(pts)
        events: List[RugEvent] = []
        lo = max(0.0, min(cfg.min_drop_pct, cfg.max_drop_pct))
        hi = max(lo, max(cfg.min_drop_pct, cfg.max_drop_pct))
        n_periods = (n + hp - 1) // hp
        for p in range(n_periods):
            start = p * hp
            end = min(n, start + hp)
            if end <= start:
                continue
            if rng.random() < cfg.rug_probability:
                idx = rng.randrange(start, end)
                drop = rng.uniform(lo, hi)
                factor = 1.0 - drop / 100.0
                before = prices[idx]
                prices[idx:] = [x * factor for x in prices[idx:]]
                events.append(RugEvent(
                    ts=times[idx], index=idx, kind="rug", token=token,
                    before_px=before,
                    after_px=prices[idx], drop_pct=drop, detected_as_rug=True,
                    note=f"injected rug, holding period {p}"))
            if cfg.liquidity_vanish_probability > 0.0 and \
                    rng.random() < cfg.liquidity_vanish_probability:
                idx = rng.randrange(start, end)
                factor = 1e-4                    # price -> ~0
                before = prices[idx]
                prices[idx:] = [max(x * factor, 1e-12) for x in prices[idx:]]
                events.append(RugEvent(
                    ts=times[idx], index=idx, kind="liquidity_vanish",
                    token=token, before_px=before, after_px=prices[idx],
                    drop_pct=(1.0 - factor) * 100.0, detected_as_rug=False,
                    note=f"injected liquidity removal, holding period {p}"))
        self.events = events
        return list(zip(times, prices)), events


# --------------------------------------------------------------------------
# 3. MEVSimulator
# --------------------------------------------------------------------------

@dataclass
class MEVConfig:
    """Sandwich attack parameters.

    `max_penalty_bps` overrides `Friction.mev_penalty_bps` when it is
    greater than zero; 0 means "inherit the friction model's value".
    `sandwich_probability` is the share of orders that get sandwiched.
    """
    max_penalty_bps: float = 0.0
    sandwich_probability: float = 0.35
    seed: int = 0
    notes: str = ""

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MEVOrder:
    """One intended order (what we wanted to trade)."""
    side: str = "buy"
    px: float = 0.0
    notional_usd: float = 0.0
    token: str = ""
    ts: int = 0
    wallet: str = ""

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MEVEvent:
    """The penalty applied to one order."""
    token: str = ""
    side: str = "buy"
    ts: int = 0
    px_before: float = 0.0
    px_after: float = 0.0
    penalty_bps: float = 0.0
    penalty_usd: float = 0.0
    sandwiched: bool = False

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)


class MEVSimulator:
    """Apply a randomised sandwich penalty to a series of intended orders.

    Deterministic for a given seed: the same order list always produces
    the same penalties, in the same order.
    """

    def __init__(self, friction: Optional[FrictionModel] = None,
                 config: Optional[MEVConfig] = None):
        self.config: MEVConfig = config or MEVConfig()
        if friction is not None:
            base = replace(friction.friction)
            if self.config.max_penalty_bps > 0.0:
                base.mev_penalty_bps = self.config.max_penalty_bps
            self.friction = FrictionModel(
                base, sandwich_probability=self.config.sandwich_probability)
        else:
            max_bps = self.config.max_penalty_bps or 50.0
            self.friction = FrictionModel(
                Friction(mev_penalty_bps=max_bps),
                sandwich_probability=self.config.sandwich_probability)
        self.rng = random.Random(self.config.seed)

    @staticmethod
    def _as_order(o: Any) -> MEVOrder:
        if isinstance(o, MEVOrder):
            return o
        if isinstance(o, dict):
            return MEVOrder(side=str(o.get("side", "buy")),
                            px=_f(o.get("px")),
                            notional_usd=_f(o.get("notional_usd")),
                            token=str(o.get("token", "")),
                            ts=int(o.get("ts", 0) or 0),
                            wallet=str(o.get("wallet", "")))
        raise TypeError(f"unsupported order type: {type(o)!r}")

    def apply_to_orders(self, orders: Sequence[Any]) -> List[MEVEvent]:
        """Penalise every intended order; returns one event per order."""
        out: List[MEVEvent] = []
        for raw in orders:
            o = self._as_order(raw)
            before = _f(o.px)
            if before <= 0.0:
                out.append(MEVEvent(token=o.token, side=o.side, ts=o.ts,
                                    px_before=before, px_after=before,
                                    penalty_bps=0.0, penalty_usd=0.0,
                                    sandwiched=False))
                continue
            qty = o.notional_usd / before if before > 0.0 else 0.0
            after, penalty_usd = self.friction.apply_mev(before, o.side,
                                                         self.rng, qty=qty)
            penalty_bps = ((abs(after - before) / before) * 10_000.0
                           if before else 0.0)
            out.append(MEVEvent(token=o.token, side=o.side, ts=o.ts,
                                px_before=before, px_after=after,
                                penalty_bps=penalty_bps, penalty_usd=penalty_usd,
                                sandwiched=penalty_usd > 0.0))
        return out


# --------------------------------------------------------------------------
# 4. Copy-trading simulator
# --------------------------------------------------------------------------

@dataclass
class CopyConfig:
    """Copy-trading rules and sizing."""
    start_usd: float = 10_000.0
    size_pct: float = 0.10               # fraction of equity per trade
    stop_loss_pct: float = 0.35          # enforced in code
    take_profit_pct: float = 1.00        # enforced in code
    max_hold_seconds: Optional[int] = 3600
    max_open_positions: int = 5
    trusted_wallets: Optional[List[str]] = None
    min_consensus: int = 0
    provenance: str = SYNTHETIC
    notes: str = ""

    def to_flat(self) -> Dict[str, Any]:
        d = asdict(self)
        d["trusted_wallets"] = ",".join(self.trusted_wallets or [])
        return d


@dataclass
class TradeRecord:
    """A `CopyTrade` plus the simulation detail the ledger needs."""
    trade: CopyTrade
    intended_action: str = ""            # buy | sell
    pnl_usd: Optional[float] = None
    mev_usd: float = 0.0
    exit_reason: str = ""
    reason: str = ""                     # clamp / failure note
    hold_seconds: Optional[int] = None

    def to_flat(self) -> Dict[str, Any]:
        d = self.trade.to_flat()
        d.update({
            "intended_action": self.intended_action,
            "pnl_usd": self.pnl_usd,
            "mev_usd": self.mev_usd,
            "exit_reason": self.exit_reason,
            "reason": self.reason,
            "hold_seconds": self.hold_seconds,
        })
        return d


@dataclass
class SimulationResult:
    """Everything a simulation produced, in flattener-friendly form."""
    start_usd: float = 0.0
    final_equity_usd: float = 0.0
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    trades: List[TradeRecord] = field(default_factory=list)
    rugs: List[RugEvent] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    provenance: str = SYNTHETIC
    price_provenance: str = SYNTHETIC
    signal_provenance: str = SYNTHETIC
    source: str = ""
    notes: str = ""
    disclosure: str = ""

    def to_flat(self) -> Dict[str, Any]:
        """Shallow, flattener-friendly dict (the package convention)."""
        return {
            "start_usd": self.start_usd,
            "final_equity_usd": self.final_equity_usd,
            "n_equity_points": len(self.equity_curve),
            "equity_curve": " | ".join(
                f"{p['ts']}={p['equity_usd']:.6f}" for p in self.equity_curve),
            "trades": [t.to_flat() for t in self.trades],
            "n_trade_records": len(self.trades),
            "rugs": [r.to_flat() for r in self.rugs],
            "n_rugs": len(self.rugs),
            "stats": self.stats,
            "provenance": self.provenance,
            "price_provenance": self.price_provenance,
            "signal_provenance": self.signal_provenance,
            "source": self.source,
            "notes": self.notes,
            "disclosure": self.disclosure,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_flat(), sort_keys=True, default=str)


class CopyTradeSimulator:
    """Follow a set of wallets with a FINITE bankroll.

    Rules enforced in code:
      * size = size_pct of equity (cash + mark-to-market of open
        positions), decided at the signal's timestamp;
      * the fill happens `latency_seconds` LATER, at the price known at
        that later time -- never at the price seen when deciding;
      * stop-loss, take-profit and a time-stop are checked on every bar;
      * the bankroll never goes negative -- a trade that would take cash
        below zero is clamped, and the clamp is recorded;
      * a trade that cannot be afforded is RECORDED as skipped with a
        reason (e.g. "insufficient free cash (funds locked in open
        positions)"), never silently dropped;
      * every signal produces exactly one ledger record, and the ledger
        is checked for consistency when the run ends.
    """

    def __init__(self, friction: FrictionModel,
                 config: Optional[CopyConfig] = None,
                 candidates: Optional[Dict[str, TokenCandidate]] = None):
        self.friction = friction
        self.config: CopyConfig = config or CopyConfig()
        self.candidates: Dict[str, TokenCandidate] = dict(candidates or {})
        self.rng = random.Random(0)
        self.cash: float = _f(self.config.start_usd)
        self.positions: Dict[str, Position] = {}
        self.trades: List[TradeRecord] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self._meta: Dict[str, Dict[str, Any]] = {}
        self._realised: List[float] = []
        self._series_map: Dict[str, PriceSeries] = {}
        self._default_series: Optional[PriceSeries] = None
        self._timeline: List[int] = []
        self._pending_buys: Set[str] = set()
        self._n_decision_skips: int = 0
        self._n_orders: int = 0

    # -- ledger ----------------------------------------------------------
    def _record(self, trade: CopyTrade, intended: str = "",
                pnl: Optional[float] = None, mev: float = 0.0,
                exit_reason: str = "", reason: str = "",
                hold: Optional[int] = None) -> None:
        self.trades.append(TradeRecord(
            trade=trade, intended_action=intended, pnl_usd=pnl, mev_usd=mev,
            exit_reason=exit_reason, reason=reason, hold_seconds=hold))

    def _skip(self, token: str, wallet: str, reason: str, ts: int,
              chain: str = "", intended: str = "", provenance: str = "",
              extra: str = "", counts_as_decision: bool = True) -> None:
        tr = CopyTrade(token=token, chain=chain, wallet=wallet, action="skip",
                       skipped=True, skip_reason=reason, ts=int(ts),
                       balance_after_usd=self.cash,
                       provenance=provenance or self.config.provenance)
        self._record(tr, intended=intended, reason=extra)
        if counts_as_decision:
            self._n_decision_skips += 1

    # -- state -----------------------------------------------------------
    def _equity(self, px_hint: Optional[float] = None) -> float:
        val = self.cash
        for token, pos in self.positions.items():
            px = self._meta.get(token, {}).get("mark_px")
            if px is None:
                px = pos.last_px if pos.last_px else (px_hint or 0.0)
            val += _f(pos.qty) * _f(px)
        return val

    def _mark(self, token: str, px: float, ts: int) -> None:
        pos = self.positions.get(token)
        if pos is None:
            return
        pos.last_px = px
        pos.last_ts = int(ts)
        pos.unrealised_usd = (px - _f(pos.entry_px)) * _f(pos.qty)
        self._meta.setdefault(token, {})["mark_px"] = px

    # -- decisions -------------------------------------------------------
    def _wallet_allowed(self, sig: WalletTrade) -> Optional[str]:
        """The trusted-wallet / consensus rules, when they are configured."""
        trusted = self.config.trusted_wallets
        if trusted is not None and sig.wallet not in set(trusted):
            return f"wallet not trusted: {sig.wallet}"
        cand = self.candidates.get(sig.token)
        if cand is not None:
            if trusted is None and cand.trusted_wallets_in and \
                    sig.wallet not in set(cand.trusted_wallets_in):
                return (f"wallet not among the token's trusted wallets: "
                        f"{sig.wallet}")
            if self.config.min_consensus > 0 and \
                    int(cand.consensus_count or 0) < self.config.min_consensus:
                return (f"consensus {cand.consensus_count} below required "
                        f"{self.config.min_consensus}")
        if self.config.min_consensus > 0 and cand is None:
            cc = (sig.detail or {}).get("consensus_count")
            if cc is None or int(cc) < self.config.min_consensus:
                return (f"consensus {cc} below required "
                        f"{self.config.min_consensus}")
        return None

    def _trigger_reason(self, pos: Position, ts: int, px: float) -> str:
        """Stop-loss, take-profit and time-stop. Enforced in code."""
        if self.config.stop_loss_pct > 0.0 and pos.stop_px is not None and \
                px <= _f(pos.stop_px):
            return "stop_loss"
        if self.config.take_profit_pct > 0.0 and pos.entry_px and \
                px >= _f(pos.entry_px) * (1.0 + self.config.take_profit_pct):
            return "take_profit"
        if self.config.max_hold_seconds:
            if (int(ts) - int(pos.entry_ts)) >= int(self.config.max_hold_seconds):
                return "time_stop"
        return ""

    # -- price lookup ----------------------------------------------------
    @staticmethod
    def _normalise_series(price_series: Any) -> Tuple[Dict[str, PriceSeries],
                                                       Optional[PriceSeries]]:
        """Accept a single [(ts, px)] series or a {token: [(ts, px)]} map."""
        series_map: Dict[str, PriceSeries] = {}
        default: Optional[PriceSeries] = None
        if isinstance(price_series, dict):
            for tok, pts in price_series.items():
                ps = PriceSeries(pts or [])
                if len(ps):
                    series_map[str(tok)] = ps
        else:
            default = PriceSeries(price_series or [])
        return series_map, default

    def _series_for(self, token: str) -> Optional[PriceSeries]:
        return self._series_map.get(token) or self._default_series

    def _price_for(self, token: str, ts: int) -> Optional[Tuple[int, float]]:
        """The price observable for `token` at `ts` (never a future price)."""
        ps = self._series_for(token)
        return ps.at_or_before(ts) if ps is not None else None

    # -- execution -------------------------------------------------------
    def _execute(self, order: Dict[str, Any]) -> None:
        kind = order["kind"]
        ts = int(order["exec_ts"])
        token = order["token"]
        sig: WalletTrade = order["signal"]
        provenance = sig.provenance or self.config.provenance
        chain = sig.chain or ""

        # The price AT the execution time (shifted later), never the
        # price that was visible when the decision was made.
        px_ref = self._price_for(token, ts)
        if px_ref is None:
            self._skip(token, sig.wallet,
                       "no price available at execution time", ts, chain,
                       kind, provenance, extra=f"exec_ts={ts}",
                       counts_as_decision=False)
            return
        px = px_ref[1]

        if kind == "buy":
            self._pending_buys.discard(token)
            if token in self.positions:
                self._skip(token, sig.wallet, "already holding a position",
                           ts, chain, kind, provenance,
                           counts_as_decision=False)
                return
            notional = _f(order["notional"])
            fees = self.friction.priority_fee_usd + self.friction.gas_usd
            free = self.cash
            clamp_note = ""
            # A buy spends exactly `notional` USD (plus fees); slippage and
            # the sandwich cost UNITS, not extra cash. So the budget that
            # must fit inside the bankroll is notional + fees.
            if notional + fees > free:
                affordable = free - fees
                if affordable < MIN_TRADE_USD:
                    self._skip(token, sig.wallet,
                               "insufficient free cash (funds locked in open positions)",
                               ts, chain, kind, provenance,
                               extra=(f"wanted ${notional:.2f}, free cash "
                                      f"${free:.2f}, fees ${fees:.2f}"),
                               counts_as_decision=False)
                    return
                clamp_note = (f"notional clamped ${notional:.2f} -> "
                              f"${affordable:.2f} to stay inside the bankroll")
                notional = affordable
            fill = self.friction.simulate_fill(px, "buy", notional, self.rng)
            if fill.failed:
                # The gas and the priority fee are burned even though the
                # trade did not happen.
                self.cash = max(0.0, self.cash - fill.fees_usd)
                self._skip(token, sig.wallet, fill.reason, ts, chain, kind,
                           provenance, extra=clamp_note, counts_as_decision=False)
                return
            cash_out = notional + fill.fees_usd
            self.cash = max(0.0, self.cash - cash_out)
            pos = Position(token=token, chain=chain, symbol=sig.symbol,
                            entry_px=fill.px, qty=fill.qty, entry_ts=ts,
                            cost_usd=cash_out, last_px=fill.px, last_ts=ts,
                            stop_px=_f(fill.px) *
                            (1.0 - self.config.stop_loss_pct),
                            unrealised_usd=0.0)
            self.positions[token] = pos
            self._meta[token] = {"entry_bar": order["bar"], "mark_px": fill.px,
                                  "chain": chain, "symbol": sig.symbol,
                                  "exit_pending": False, "signal": sig}
            tr = CopyTrade(token=token, chain=chain, wallet=sig.wallet,
                           action="buy", skipped=False, px=fill.px,
                           qty=fill.qty, notional_usd=notional,
                           fee_usd=fill.fees_usd,
                           slippage_usd=fill.slippage_usd,
                           ts=ts, balance_after_usd=self.cash,
                           provenance=provenance)
            self._record(tr, intended="buy", mev=fill.mev_usd, reason=clamp_note)
            return

        # --- sell / exit ---
        pos = self.positions.get(token)
        if pos is None:
            self._skip(token, sig.wallet, "no open position to sell", ts,
                       chain, kind, provenance, counts_as_decision=False)
            return
        notional = _f(pos.qty) * px
        fill = self.friction.simulate_fill(px, "sell", notional, self.rng)
        if fill.failed:
            self.cash = max(0.0, self.cash - fill.fees_usd)
            if token in self._meta:
                self._meta[token]["exit_pending"] = False   # retried later
            self._skip(token, sig.wallet, fill.reason, ts, chain, kind,
                       provenance, extra=f"exit_reason={order.get('reason', '')}",
                       counts_as_decision=False)
            return
        proceeds = fill.qty * _f(fill.px) - fill.fees_usd
        self.cash = max(0.0, self.cash + proceeds)
        pnl = proceeds - _f(pos.cost_usd)
        hold = ts - int(pos.entry_ts)
        tr = CopyTrade(token=token, chain=chain, wallet=sig.wallet,
                       action="sell", skipped=False, px=fill.px, qty=fill.qty,
                       notional_usd=notional, fee_usd=fill.fees_usd,
                       slippage_usd=fill.slippage_usd, ts=ts,
                       balance_after_usd=self.cash, provenance=provenance)
        self._record(tr, intended="sell", pnl=pnl, mev=fill.mev_usd,
                     exit_reason=order.get("reason", ""), hold=hold)
        self.positions.pop(token, None)
        self._meta.pop(token, None)
        self._realised.append(pnl)

    # -- main loop -------------------------------------------------------
    def run(self, signals: Sequence[WalletTrade],
            price_series: Any,
            seed: Optional[int] = None) -> SimulationResult:
        self.rng = random.Random(seed if seed is not None else 0)
        self._series_map, self._default_series = self._normalise_series(
            price_series)
        # The simulation clock is the union of every series' timestamps,
        # so a multi-token run advances on a single causal timeline.
        stamps = set()
        for ps in list(self._series_map.values()) + \
                ([self._default_series] if self._default_series else []):
            stamps.update(ps.times)
        self._timeline = sorted(stamps)
        self._realised = []
        self.trades = []
        self.equity_curve = []
        self._meta = {}
        self.positions = {}
        self._pending_buys = set()
        self._n_decision_skips = 0
        self._n_orders = 0
        self.cash = _f(self.config.start_usd)

        sigs = sorted(signals, key=lambda s: (int(s.ts), s.wallet, s.token))
        pending: List[Dict[str, Any]] = []
        si = 0

        for i, ts in enumerate(self._timeline):
            # (a) decisions for signals at or before this bar
            while si < len(sigs) and int(sigs[si].ts) <= ts:
                sig = sigs[si]
                si += 1
                self._decide(sig, i, ts, pending)
            # (b) stop / take-profit / time-stop on positions opened earlier
            for token, pos in list(self.positions.items()):
                meta = self._meta.get(token, {})
                if int(meta.get("entry_bar", i)) >= i:
                    continue
                if meta.get("exit_pending"):
                    continue
                px_ref = self._price_for(token, ts)
                if px_ref is None:
                    continue
                reason = self._trigger_reason(pos, ts, px_ref[1])
                if reason:
                    meta["exit_pending"] = True
                    self._n_orders += 1
                    pending.append({"kind": "sell", "token": token,
                                    "exec_ts": self.friction.latency_shift(ts),
                                    "bar": i, "reason": reason,
                                    "signal": meta.get("signal")})
            # (c) execute everything whose execution time has arrived
            if pending:
                ready = [o for o in pending if int(o["exec_ts"]) <= ts]
                pending = [o for o in pending if int(o["exec_ts"]) > ts]
                for o in sorted(ready, key=lambda o: (int(o["exec_ts"]),
                                                       str(o["token"]))):
                    self._execute(o)
            # (d) mark to market and record equity
            for token in list(self.positions):
                px_ref = self._price_for(token, ts)
                if px_ref is not None:
                    self._mark(token, px_ref[1], ts)
            pv = sum(_f(p.qty) * _f(self._meta.get(t, {}).get("mark_px"))
                     for t, p in self.positions.items())
            self.equity_curve.append({
                "ts": int(ts), "cash_usd": round(self.cash, 6),
                "positions_value_usd": round(pv, 6),
                "equity_usd": round(self.cash + pv, 6)})

        # signals beyond the end of the series must still be recorded
        while si < len(sigs):
            sig = sigs[si]
            si += 1
            self._skip(sig.token, sig.wallet,
                       "signal timestamp beyond the end of the price series",
                       int(sig.ts), sig.chain or "", sig.side,
                       sig.provenance or self.config.provenance)

        # orders that could never execute (execution time past the data)
        for o in pending:
            self._skip(o["token"], o["signal"].wallet,
                       "no fill: execution time beyond the end of the price series",
                       int(o["exec_ts"]), o["signal"].chain or "", o["kind"],
                       o["signal"].provenance or self.config.provenance,
                       extra=f"exit_reason={o.get('reason', '')}",
                       counts_as_decision=False)

        expected = self._n_decision_skips + self._n_orders
        if len(self.trades) != expected:
            raise AssertionError(
                f"ledger mismatch: {len(self.trades)} records for "
                f"{expected} expected decisions "
                f"({self._n_decision_skips} skips + {self._n_orders} orders)")

        return self._result()

    def _decide(self, sig: WalletTrade, bar: int, ts: int,
                pending: List[Dict[str, Any]]) -> None:
        """Apply the copy rules to one signal; schedule an order or skip."""
        provenance = sig.provenance or self.config.provenance
        chain = sig.chain or ""
        allowed = self._wallet_allowed(sig)
        if allowed:
            self._skip(sig.token, sig.wallet, allowed, int(sig.ts), chain,
                       sig.side, provenance)
            return
        side = (sig.side or "").lower()
        if side not in ("buy", "sell"):
            self._skip(sig.token, sig.wallet,
                       f"unsupported signal side '{sig.side}'",
                       int(sig.ts), chain, side, provenance)
            return
        if side == "sell":
            if sig.token not in self.positions:
                self._skip(sig.token, sig.wallet, "no open position to sell",
                           int(sig.ts), chain, side, provenance)
                return
            if self._meta.get(sig.token, {}).get("exit_pending"):
                self._skip(sig.token, sig.wallet, "exit already pending",
                           int(sig.ts), chain, side, provenance)
                return
            self._meta[sig.token]["exit_pending"] = True
            self._n_orders += 1
            pending.append({"kind": "sell", "token": sig.token,
                            "exec_ts": self.friction.latency_shift(int(sig.ts)),
                            "bar": bar, "reason": "signal_sell", "signal": sig})
            return
        # buy
        if sig.token in self.positions:
            self._skip(sig.token, sig.wallet, "already holding a position",
                       int(sig.ts), chain, side, provenance)
            return
        if sig.token in self._pending_buys:
            self._skip(sig.token, sig.wallet, "buy already pending",
                       int(sig.ts), chain, side, provenance)
            return
        if len(self.positions) + len(self._pending_buys) >= \
                int(self.config.max_open_positions):
            self._skip(sig.token, sig.wallet,
                       f"max open positions reached "
                       f"({self.config.max_open_positions})",
                       int(sig.ts), chain, side, provenance)
            return
        px_ref = self._price_for(sig.token, int(sig.ts))
        equity = self._equity(px_ref[1] if px_ref else None)
        notional = equity * _f(self.config.size_pct)
        if notional <= 0.0:
            self._skip(sig.token, sig.wallet,
                       "equity is zero, cannot size a trade",
                       int(sig.ts), chain, side, provenance)
            return
        self._n_orders += 1
        self._pending_buys.add(sig.token)
        pending.append({"kind": "buy", "token": sig.token,
                        "exec_ts": self.friction.latency_shift(int(sig.ts)),
                        "bar": bar, "reason": "signal_buy", "signal": sig,
                        "notional": notional})

    # -- result ----------------------------------------------------------
    def _result(self) -> SimulationResult:
        start = _f(self.config.start_usd)
        open_value = 0.0
        for token, pos in self.positions.items():
            px = self._meta.get(token, {}).get("mark_px")
            if px is None:
                px = pos.last_px or 0.0
            open_value += _f(pos.qty) * _f(px)
        final_equity = self.cash + open_value
        curve = list(self.equity_curve)
        if curve:
            last = dict(curve[-1])
            last["equity_usd"] = round(final_equity, 6)
            last["cash_usd"] = round(self.cash, 6)
            last["positions_value_usd"] = round(open_value, 6)
            curve[-1] = last

        peak = -1e18
        max_dd = 0.0
        max_dd_usd = 0.0
        for pt in curve:
            eq = _f(pt["equity_usd"])
            peak = max(peak, eq)
            dd = peak - eq
            if dd > max_dd_usd:
                max_dd_usd = dd
                max_dd = (dd / peak) if peak > 0 else 0.0

        closed = len(self._realised)
        wins = [p for p in self._realised if p > 0]
        losses = [p for p in self._realised if p <= 0]
        gross_profit = sum(wins)
        gross_loss = -sum(losses)
        total_fees = sum(_f(t.trade.fee_usd) for t in self.trades)
        total_slip = sum(_f(t.trade.slippage_usd) for t in self.trades)
        total_mev = sum(_f(t.mev_usd) for t in self.trades)
        n_skipped = sum(1 for t in self.trades if t.trade.skipped)
        stats = {
            "n_trades": len(self.trades) - n_skipped,
            "n_skipped": n_skipped,
            "n_records": len(self.trades),
            "n_closed_positions": closed,
            "n_open_positions": len(self.positions),
            "win_rate": (len(wins) / closed) if closed else None,
            "profit_factor": ((gross_profit / gross_loss)
                              if gross_loss > 0 else None),
            "gross_profit_usd": round(gross_profit, 6),
            "gross_loss_usd": round(gross_loss, 6),
            "realised_pnl_usd": round(sum(self._realised), 6),
            "total_return_usd": round(final_equity - start, 6),
            "total_return_pct": (round((final_equity / start - 1.0) * 100.0, 6)
                                 if start else None),
            "max_drawdown_usd": round(max_dd_usd, 6),
            "max_drawdown_pct": round(max_dd * 100.0, 6),
            "final_cash_usd": round(self.cash, 6),
            "final_equity_usd": round(final_equity, 6),
            "total_fees_usd": round(total_fees, 6),
            "total_slippage_usd": round(total_slip, 6),
            "total_mev_usd": round(total_mev, 6),
        }
        return SimulationResult(
            start_usd=start, final_equity_usd=final_equity, equity_curve=curve,
            trades=self.trades, rugs=[], stats=stats,
            provenance=self.config.provenance,
            price_provenance=self.config.provenance,
            signal_provenance=self.config.provenance,
            source="leapspace.friction.CopyTradeSimulator",
            notes=self.config.notes)


# --------------------------------------------------------------------------
# 5. run_simulation
# --------------------------------------------------------------------------

def run_simulation(signals: Sequence[WalletTrade],
                   price_series: Sequence[Tuple[int, float]],
                   friction: Optional[Friction] = None,
                   bankroll: Optional[float] = None,
                   rug_config: Optional[RugConfig] = None,
                   mev_config: Optional[MEVConfig] = None,
                   seed: int = 0,
                   config: Optional[CopyConfig] = None,
                   candidates: Optional[Dict[str, TokenCandidate]] = None,
                   price_provenance: str = SYNTHETIC,
                   signal_provenance: Optional[str] = None,
                   source: str = "",
                   notes: str = "") -> SimulationResult:
    """Run one friction-aware copy-trading simulation.

    Pipeline: inject rugs into the price series -> build the friction
    model -> run the copy-trading simulator over the signals -> return
    the equity curve, every trade record (skips included), the injected
    rugs and the aggregate stats.

    `mev_config.max_penalty_bps` overrides `friction.mev_penalty_bps`
    when it is greater than zero; `mev_config.sandwich_probability` is
    the share of fills that get sandwiched.
    """
    friction = friction or Friction()
    sandwich_prob = mev_config.sandwich_probability if mev_config else 1.0
    if mev_config and mev_config.max_penalty_bps > 0.0:
        friction = replace(friction,
                           mev_penalty_bps=mev_config.max_penalty_bps)
    fm = FrictionModel(friction, sandwich_probability=sandwich_prob)

    series: Any = price_series
    rugs: List[RugEvent] = []
    if isinstance(series, dict):
        injected: Dict[str, List[Tuple[int, float]]] = {}
        for n, (tok, pts) in enumerate(sorted(series.items(),
                                               key=lambda kv: str(kv[0]))):
            if rug_config is not None:
                # Each token gets its own deterministic rug stream so the
                # same token always rugs the same way, but different tokens
                # do not rug in lock-step.
                tok_cfg = replace(rug_config, seed=rug_config.seed + n)
                injector = RugInjector(tok_cfg)
                rugged, evs = injector.inject([(int(t), _f(p))
                                               for t, p in pts], token=str(tok))
                injected[tok] = rugged
                rugs.extend(evs)
            else:
                injected[tok] = [(int(t), _f(p)) for t, p in pts]
        series = injected
    else:
        pts = [(int(t), _f(p)) for t, p in price_series]
        if rug_config is not None:
            injector = RugInjector(rug_config)
            series, rugs = injector.inject(pts)
        else:
            series = pts

    cfg = config or CopyConfig()
    if bankroll is not None:
        cfg = replace(cfg, start_usd=_f(bankroll))
    if signal_provenance:
        cfg = replace(cfg, provenance=signal_provenance)

    sim = CopyTradeSimulator(fm, cfg, candidates=candidates)
    result = sim.run(signals, series, seed=seed)
    result.rugs = rugs
    result.price_provenance = price_provenance
    result.signal_provenance = cfg.provenance
    result.provenance = price_provenance
    result.source = source or "leapspace.friction.run_simulation"
    result.notes = notes or cfg.notes
    if price_provenance == SYNTHETIC or cfg.provenance == SYNTHETIC:
        result.disclosure = (
            "SYNTHETIC DATA — the price series and/or the signal list were "
            "generated by leapspace.friction, not fetched from a market "
            "source. This is NOT market data and must never be used to "
            "make trading decisions.")
    else:
        result.disclosure = (f"Live data: price series {price_provenance}, "
                              f"signals {cfg.provenance}.")
    return result


# --------------------------------------------------------------------------
# 6. Self-test
# --------------------------------------------------------------------------

def _synthetic_series(seed: int = 7, n: int = 120,
                       start_ts: int = 1_760_000_000, step: int = 300,
                       start_px: float = 0.00002
                       ) -> List[Tuple[int, float]]:
    """A synthetic meme-coin price path. SYNTHETIC by construction."""
    rng = random.Random(seed)
    px = start_px
    out = []
    for i in range(n):
        shock = rng.gauss(0.0, 0.08)
        px = max(1e-9, px * (1.0 + shock))
        out.append((start_ts + i * step, px))
    return out


def _synthetic_signals(series: Sequence[Tuple[int, float]], seed: int = 11,
                       every: int = 7, token: str = "SYNTHETIC-MEME",
                       wallets: Sequence[str] = ("WalletA", "WalletB")
                       ) -> List[WalletTrade]:
    """A synthetic wallet signal list. SYNTHETIC by construction."""
    rng = random.Random(seed)
    out: List[WalletTrade] = []
    for i in range(0, len(series), every):
        ts, px = series[i]
        w = wallets[rng.randrange(len(wallets))]
        side = "sell" if (i // every) % 11 == 10 else "buy"
        out.append(WalletTrade(
            wallet=w, chain="solana", token=token, symbol="SYNTH",
            side=side, amount=100.0 / max(px, 1e-12),
            price_usd=px, value_usd=100.0, ts=int(ts),
            source="leapspace.friction.self_test", provenance=SYNTHETIC,
            detail={"consensus_count": 3}))
    return out


def _synthetic_market(seed: int = 7, n: int = 120,
                       tokens: Sequence[str] = ("SYN-A", "SYN-B", "SYN-C",
                                                "SYN-D"),
                       start_ts: int = 1_760_000_000, step: int = 300
                       ) -> Dict[str, List[Tuple[int, float]]]:
    """Several synthetic meme-coin price paths. SYNTHETIC by construction."""
    out: Dict[str, List[Tuple[int, float]]] = {}
    for k, tok in enumerate(tokens):
        rng = random.Random(seed + k)
        px = 0.00002 * (1.0 + 0.5 * k)
        path = []
        for i in range(n):
            px = max(1e-9, px * (1.0 + rng.gauss(0.0, 0.08)))
            path.append((start_ts + i * step, px))
        out[tok] = path
    return out


def _synthetic_signals_multi(series_by_token: Dict[str, List[Tuple[int, float]]],
                             seed: int = 11, every: int = 5,
                             wallets: Sequence[str] = ("WalletA", "WalletB")
                             ) -> List[WalletTrade]:
    """Synthetic signals across several tokens. SYNTHETIC by construction."""
    rng = random.Random(seed)
    out: List[WalletTrade] = []
    for tok, path in series_by_token.items():
        for i in range(0, len(path), every):
            ts, px = path[i]
            w = wallets[rng.randrange(len(wallets))]
            side = "sell" if (i // every) % 13 == 12 else "buy"
            out.append(WalletTrade(
                wallet=w, chain="solana", token=tok, symbol=tok,
                side=side, amount=100.0 / max(px, 1e-12),
                price_usd=px, value_usd=100.0, ts=int(ts),
                source="leapspace.friction.self_test", provenance=SYNTHETIC,
                detail={"consensus_count": 3}))
    out.sort(key=lambda s: (s.ts, s.token, s.wallet))
    return out


def _live_series(symbol: str = "DOGE-USD", rng_range: str = "3mo",
                  interval: str = "1d"
                  ) -> Tuple[List[Tuple[int, float]], Provenance]:
    """Real prices from leapspace.market (Yahoo chart). LIVE provenance."""
    from . import market
    bars, prov = market.fetch_ohlcv(symbol, rng=rng_range, interval=interval)
    out: List[Tuple[int, float]] = []
    for b in bars:
        try:
            d = _dt.datetime.strptime(str(b["date"]), "%Y-%m-%d").replace(
                tzinfo=_dt.timezone.utc)
        except (KeyError, ValueError):
            continue
        px = b.get("close")
        if px is None:
            continue
        out.append((int(d.timestamp()), float(px)))
    return out, prov


def _print_run(title: str, result: SimulationResult) -> None:
    print("=" * 78)
    print(title)
    print("=" * 78)
    print(f"price provenance : {result.price_provenance}")
    print(f"signal provenance: {result.signal_provenance}")
    if result.disclosure:
        print(f"disclosure       : {result.disclosure}")
    st = result.stats
    print(f"trades={st['n_trades']}  skipped={st['n_skipped']}  "
          f"closed={st['n_closed_positions']}  open={st['n_open_positions']}")
    print(f"win_rate={st['win_rate']}  profit_factor={st['profit_factor']}")
    print(f"total_return={st['total_return_pct']}%  "
          f"max_dd={st['max_drawdown_pct']}%  "
          f"final_equity=${st['final_equity_usd']}")
    print(f"fees=${st['total_fees_usd']}  slippage=${st['total_slippage_usd']}  "
          f"mev=${st['total_mev_usd']}")
    if result.rugs:
        print("injected rugs:")
        for r in result.rugs:
            print(f"  ts={r.ts} token={r.token} kind={r.kind} "
                  f"before={r.before_px:.10g} "
                  f"after={r.after_px:.10g} drop={r.drop_pct:.2f}% "
                  f"detected_as_rug={r.detected_as_rug}")
    print("equity curve (ts, equity_usd):")
    for pt in result.equity_curve:
        print(f"  {pt['ts']}  {pt['equity_usd']:.4f}")
    print("skip log:")
    skipped = [t for t in result.trades if t.trade.skipped]
    if not skipped:
        print("  (no skipped trades)")
    for t in skipped:
        print(f"  ts={t.trade.ts} wallet={t.trade.wallet} token={t.trade.token} "
              f"reason={t.trade.skip_reason}")
    print()


def _self_test() -> int:
    print("leapspace.friction self-test")
    print("All randomness comes from random.Random(seed); the global random "
          "module is never used.")
    print()

    # ---- SYNTHETIC run ------------------------------------------------
    syn_market = _synthetic_market(seed=7, n=120)
    syn_signals = _synthetic_signals_multi(syn_market, seed=11)
    syn_cfg = CopyConfig(start_usd=10_000.0, size_pct=0.60, stop_loss_pct=0.35,
                         take_profit_pct=1.00, max_hold_seconds=1800,
                         max_open_positions=4, provenance=SYNTHETIC)
    syn_friction = Friction(slippage_bps=150.0, priority_fee_usd=0.02,
                            latency_seconds=5.0, failed_tx_rate=0.08,
                            mev_penalty_bps=120.0, gas_usd=0.01)
    syn_rug = RugConfig(rug_probability=0.12, min_drop_pct=80.0,
                        max_drop_pct=99.0, liquidity_vanish_probability=0.04,
                        holding_period_bars=10, seed=99)
    syn_mev = MEVConfig(max_penalty_bps=120.0, sandwich_probability=0.40,
                        seed=5)
    syn = run_simulation(syn_signals, syn_market, friction=syn_friction,
                         bankroll=10_000.0, rug_config=syn_rug,
                         mev_config=syn_mev, seed=42, config=syn_cfg,
                         price_provenance=SYNTHETIC,
                         source="leapspace.friction.self_test (synthetic)")
    _print_run("RUN 1 — SYNTHETIC price series + SYNTHETIC signals", syn)

    # ---- invariants ----------------------------------------------------
    min_cash = min((_f(t.trade.balance_after_usd) for t in syn.trades),
                   default=0.0)
    n_rec = len(syn.trades)
    n_skip = sum(1 for t in syn.trades if t.trade.skipped)
    n_locked = sum(1 for t in syn.trades
                    if "insufficient free cash" in (t.trade.skip_reason or ""))
    print("=" * 78)
    print("INVARIANTS")
    print("=" * 78)
    print(f"bankroll never negative      : {min_cash >= 0.0} "
          f"(min recorded balance ${min_cash:.4f})")
    print(f"every trade recorded         : {n_rec} records "
          f"({n_rec - n_skip} executed, {n_skip} skipped)")
    print(f"funds-locked skips logged    : {n_locked} "
          f"(reason 'insufficient free cash ...')")
    print("ledger self-check passed     : True (AssertionError on mismatch)")
    print()

    # ---- determinism --------------------------------------------------
    syn2 = run_simulation(syn_signals, syn_market, friction=syn_friction,
                          bankroll=10_000.0, rug_config=syn_rug,
                          mev_config=syn_mev, seed=42, config=syn_cfg,
                          price_provenance=SYNTHETIC,
                          source="leapspace.friction.self_test (synthetic)")
    identical = syn.to_json() == syn2.to_json()
    print("=" * 78)
    print("DETERMINISM: two runs with seed=42 -> "
          f"{'IDENTICAL' if identical else 'DIFFERENT'}")
    print("=" * 78)
    if not identical:
        print("!! determinism check FAILED")
        return 1

    # ---- LIVE run -----------------------------------------------------
    print()
    try:
        live_series, live_prov = _live_series()
    except (SourceUnavailable, OSError) as exc:
        print("LIVE RUN — price source unavailable: "
              f"{type(exc).__name__}: {exc}")
        print("No data was substituted for the live series; the synthetic "
              "run above is the only result in this self-test.")
        return 0
    live_market = {"DOGE": live_series}
    live_signals = _synthetic_signals_multi(live_market, seed=21, every=3)
    for s in live_signals:
        s.chain = "solana"
    live_cfg = replace(syn_cfg, max_open_positions=3,
                       max_hold_seconds=3 * 86400, provenance=SYNTHETIC)
    live_rug = RugConfig(rug_probability=0.10, min_drop_pct=80.0,
                         max_drop_pct=99.0, liquidity_vanish_probability=0.03,
                         holding_period_bars=5, seed=123)
    live = run_simulation(live_signals, live_market, friction=syn_friction,
                          bankroll=10_000.0, rug_config=live_rug,
                          mev_config=syn_mev, seed=42, config=live_cfg,
                          price_provenance=live_prov.kind,
                          source=f"{live_prov.source} ({live_prov.url})")
    _print_run(f"RUN 2 — LIVE price series ({live_prov.source}) + "
               "SYNTHETIC signals", live)
    print("NOTE: run 2 uses REAL prices "
          f"({live_prov.source}, {live_prov.kind}); the wallet signals are "
          "SYNTHETIC (generated by this self-test), so its trade list is "
          "labelled SYNTHETIC and must not be read as a live strategy result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
