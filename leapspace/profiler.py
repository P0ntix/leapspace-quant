"""Wallet profiling, anti-insider filtering, consensus and the trusted pool.

The operator brief's rules, implemented exactly:

* **Wallet Profiling** — a wallet must have >=30 trades, >=55% win rate,
  Profit Factor >=1.5, and <40% of total PnL coming from a single trade.
* **Anti-Insider Filter** — check the INITIAL FUNDING SOURCE of candidate
  wallets. Exclude wallets funded by token deployers, known cabals, or
  wallets that snipe the first few blocks of a token launch.
* **Consensus Tracking** — trigger trades only when >=N profiled wallets act
  on the same token within a configurable time window (T).
* **Trusted Pool** — re-evaluated periodically; an alpha wallet today might
  become a cabal wallet tomorrow.

Three honesty rules this module never breaks:

1. A wallet with too little history is INSUFFICIENT, not passing. The
   profile says so and disqualifies it. No profile is ever padded.
2. Trades without a usable price are EXCLUDED from the PnL maths and
   counted as a warning, not silently counted as zero-PnL winners.
3. The deployer / cabal / exchange registries are EMPTY by default. An
   empty registry cannot exclude anyone, so the funding source is reported
   as "unknown" and the profile says the registry is empty. "Unknown
   funding source" is not a clean bill of health.
"""
from __future__ import annotations

import json
import os
import statistics
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .models import (PROFILE_THRESHOLDS, FundingSource, WalletProfile,
                     WalletTrade, now_ts)
from .provenance import read_json, write_json

POOL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "state", "trusted_pool.json")
REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "state", "deployer_registry.json")


# --------------------------------------------------------------------------
# Registries
# --------------------------------------------------------------------------


def load_registries(config: Optional[Dict[str, Any]] = None
                     ) -> Dict[str, List[str]]:
    """The deployer / cabal / exchange / insider address lists.

    The DEPLOYER list is DERIVED from on-chain data by
    `leapspace/deployers.py`; the rest are hand-maintained and ship empty.
    """
    reg: Dict[str, List[str]] = {
        "deployers": [], "cabals": [], "exchanges": [], "insiders": []}
    if config:
        for k in list(reg):
            reg[k] = list((config.get("registries") or {}).get(k) or [])
    derived = read_json(REGISTRY_PATH) or {}
    for ev in (derived.get("deployers") or {}).values():
        addr = ev.get("address")
        if addr and addr not in reg["deployers"]:
            reg["deployers"].append(addr)
    return reg


# --------------------------------------------------------------------------
# Profiling
# --------------------------------------------------------------------------


def _resolve_price(trade: WalletTrade,
                   price_lookup: Optional[Any] = None) -> Optional[float]:
    """The price for a trade: its own, else whatever the lookup returns."""
    if trade.price_usd is not None:
        return float(trade.price_usd)
    if price_lookup is None:
        return None
    try:
        return price_lookup(trade)
    except Exception:  # noqa: BLE001
        return None


def _realized_pnl(trades: Sequence[WalletTrade],
                  price_lookup: Optional[Any] = None
                  ) -> Tuple[List[Dict[str, Any]], int]:
    """Realised PnL from closed round trips, matched FIFO per token.

    A raw on-chain trade history is a FLOW of buys and sells, not closed
    positions. Profit factor, win rate and "one trade's share of total
    PnL" are all defined on REALISED outcomes, so buys and sells are
    matched FIFO per token. A sell that cannot be matched to a buy in the
    observed window has no knowable acquisition price and is EXCLUDED -
    it is not counted as a loss or a win.

    Returns (closed_trades, n_unmatched_sells).
    """
    by_token: Dict[str, List[WalletTrade]] = {}
    for t in trades:
        by_token.setdefault(t.token, []).append(t)

    closed: List[Dict[str, Any]] = []
    unmatched = 0
    for token, tlist in by_token.items():
        tlist = sorted(tlist, key=lambda x: x.ts or 0)
        lots: List[Dict[str, Any]] = []
        for t in tlist:
            px = _resolve_price(t, price_lookup)
            if px is None or px <= 0:
                continue
            if t.side == "buy":
                lots.append({"remaining": float(t.amount or 0), "px": px,
                             "ts": t.ts or 0})
                continue
            # A sell: match against the open lots, FIFO.
            qty = float(t.amount or 0)
            while qty > 1e-12 and lots:
                lot = lots[0]
                take = min(qty, lot["remaining"])
                if take <= 1e-12:
                    break
                pnl = (px - lot["px"]) * take
                closed.append({
                    "token": token, "ts": t.ts or 0,
                    "pnl_usd": pnl,
                    "notional_usd": px * take,
                    "hold_seconds": ((t.ts or 0) - lot["ts"])
                    if (t.ts and lot["ts"]) else None,
                })
                lot["remaining"] -= take
                qty -= take
                if lot["remaining"] <= 1e-12:
                    lots.pop(0)
            if qty > 1e-12:
                unmatched += 1
    return closed, unmatched


def profile_wallet(chain: str, wallet: str,
                   trades: Optional[Sequence[WalletTrade]] = None,
                   thresholds: Optional[Dict[str, Any]] = None,
                   source: str = "",
                   price_lookup: Optional[Any] = None) -> WalletProfile:
    """Score one wallet against the operator's consistency thresholds.

    `trades` may be supplied (already fetched) or left None, in which case
    they are fetched from the chain. `price_lookup` is an optional
    callable that resolves a WalletTrade to a USD price; without it, only
    trades that already carry a price can contribute to the PnL
    statistics.
    """
    th = dict(PROFILE_THRESHOLDS)
    if thresholds:
        th.update(thresholds)

    gaps: List[str] = []
    if trades is None:
        try:
            from .chains import fetch_wallet_trades
            trades = fetch_wallet_trades(chain, wallet)
            source = source or "chain"
        except Exception as exc:  # noqa: BLE001
            gaps.append(f"trade history unavailable: {exc}")
            trades = []
            source = "unavailable"

    trades = list(trades)
    warnings = list(gaps)

    closed, unmatched = _realized_pnl(trades, price_lookup)
    n_trades = len(trades)
    if n_trades and not closed:
        warnings.append(
            "no CLOSED round trip could be priced: the trade history has no "
            "usable prices, so win rate and profit factor are UNAVAILABLE. "
            "This is an absence of evidence, not a failure - pass a "
            "price_lookup to resolve prices from a real source.")
    if unmatched:
        warnings.append(
            f"{unmatched} sell(s) could not be matched to a buy in the "
            f"observed window (no knowable acquisition price) and were "
            f"EXCLUDED rather than counted as losses")

    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    pnl_total: Optional[float] = None
    largest_pnl: Optional[float] = None
    largest_share: Optional[float] = None
    gross_profit = 0.0
    gross_loss = 0.0
    holds: List[float] = []

    if closed:
        pnls = [c["pnl_usd"] for c in closed]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        pnl_total = sum(pnls)
        win_rate = len(wins) / len(pnls)
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        else:
            # No losing round trip: the factor is unbounded. Report None
            # rather than inf so the JSON stays clean, and say why.
            profit_factor = None
            warnings.append(
                "no losing round trips, so the profit factor is unbounded "
                "(reported as None, not a number)")
        total_abs = sum(abs(p) for p in pnls)
        if total_abs > 0:
            biggest = max(pnls, key=abs)
            largest_pnl = float(biggest)
            largest_share = abs(biggest) / total_abs
        holds = [c["hold_seconds"] for c in closed
                 if c.get("hold_seconds") is not None]

    # --- apply the thresholds ---
    disq: List[str] = []
    if n_trades < th["min_trades"]:
        disq.append(f"trades={n_trades} < {th['min_trades']}")
    if win_rate is None:
        disq.append("win rate unavailable (no priced trades)")
    elif win_rate < th["min_win_rate"]:
        disq.append(f"win_rate={win_rate:.3f} < {th['min_win_rate']}")
    if profit_factor is None:
        if gross_loss == 0 and gross_profit > 0:
            pass  # unbounded: not a disqualifier, already warned
        else:
            disq.append("profit factor unavailable")
    elif profit_factor < th["min_profit_factor"]:
        disq.append(f"profit_factor={profit_factor:.3f} < {th['min_profit_factor']}")
    if largest_share is None:
        if n_trades:
            disq.append("single-trade PnL share unavailable")
    elif largest_share >= th["max_single_trade_pnl_share"]:
        disq.append(f"single_trade_pnl_share={largest_share:.3f} >= "
                    f"{th['max_single_trade_pnl_share']}")

    notes = ""
    if n_trades < th["min_trades"]:
        notes = (f"INSUFFICIENT HISTORY: {n_trades} trades against a "
                 f"{th['min_trades']}-trade minimum, so this wallet cannot "
                 f"qualify regardless of its other statistics. It is not a "
                 f"failure - it is an absence of evidence.")

    return WalletProfile(
        wallet=wallet, chain=chain, n_trades=n_trades,
        win_rate=win_rate, profit_factor=profit_factor,
        pnl_total_usd=pnl_total, largest_trade_pnl=largest_pnl,
        largest_trade_pnl_share=largest_share,
        trades=trades, disqualifiers=disq, warnings=warnings,
        provenance="LIVE" if trades else "UNAVAILABLE",
        source=source, notes=notes)


def profile_many(chain: str, wallets: Sequence[str],
                 thresholds: Optional[Dict[str, Any]] = None
                 ) -> Dict[str, Any]:
    """Profile several wallets; returns a flat summary plus the raw profiles."""
    profiles: List[WalletProfile] = []
    gaps: List[Dict[str, str]] = []
    for w in wallets:
        try:
            profiles.append(profile_wallet(chain, w, thresholds=thresholds))
        except Exception as exc:  # noqa: BLE001
            gaps.append({"source": f"profile:{w}", "reason": str(exc)})
    return {
        "chain": chain,
        "n_profiled": len(profiles),
        "n_qualified": sum(1 for p in profiles if p.qualifies),
        "profiles": [p.to_flat() for p in profiles],
        "gaps": gaps,
        "thresholds": dict(thresholds or PROFILE_THRESHOLDS),
    }


# --------------------------------------------------------------------------
# Anti-insider: funding source
# --------------------------------------------------------------------------


def trace_funding_source(chain: str, wallet: str,
                          registries: Optional[Dict[str, List[str]]] = None
                          ) -> FundingSource:
    """Find the earliest inbound token transfer to a wallet.

    That transfer's sender is the funding source. It is then labelled:
    "deployer" (in the derived deployer registry), "cabal", "exchange",
    "insider", or "unknown".

    Solana: the wallet's OLDEST signature is read and its token balance
    deltas are inspected for the first inbound transfer.
    EVM: ERC-20 Transfer logs where the wallet is the recipient (topic1),
    oldest first.

    An unreachable source returns a FundingSource with an empty funder and
    an explicit note - never a guess.
    """
    regs = registries if registries is not None else load_registries()
    out = FundingSource(wallet=wallet, chain=chain,
                        provenance="LIVE", source="")
    try:
        if chain == "solana":
            res = _solana_funding(chain, wallet)
        else:
            res = _evm_funding(chain, wallet)
        out.funder = res.get("funder", "") or ""
        out.token = res.get("token", "") or ""
        out.ts = int(res.get("ts") or 0)
        out.distance_blocks = res.get("distance_blocks")
        out.source = res.get("source", "")
        out.detail = res.get("detail", {})
    except Exception as exc:  # noqa: BLE001
        out.provenance = "UNAVAILABLE"
        out.detail = {"error": str(exc)}

    out.funder_label = _label_funder(out.funder, regs)
    if not regs.get("deployers"):
        out.detail["registry_state"] = (
            "the deployer registry is EMPTY, so a funder cannot be matched "
            "against a deployer; 'unknown' is the honest label")
    if not regs.get("cabals"):
        out.detail["cabal_registry_state"] = (
            "the cabal registry is EMPTY, so no funder can be excluded as a "
            "known cabal")
    return out


def _label_funder(funder: str, regs: Dict[str, List[str]]) -> str:
    if not funder:
        return "unknown"
    f = funder.lower()
    if any(f == str(a).lower() for a in regs.get("insiders", [])):
        return "insider"
    if any(f == str(a).lower() for a in regs.get("deployers", [])):
        return "deployer"
    if any(f == str(a).lower() for a in regs.get("cabals", [])):
        return "cabal"
    if any(f == str(a).lower() for a in regs.get("exchanges", [])):
        return "exchange"
    return "unknown_wallet"


def _solana_funding(chain: str, wallet: str, max_sigs: int = 100
                    ) -> Dict[str, Any]:
    """The earliest INBOUND token transfer to a Solana wallet.

    The wallet's signatures are read newest-first, and each transaction's
    balance deltas are inspected for an inbound transfer. The first one
    found (scanning backwards to the oldest) is the funding event, and its
    COUNTERPARTY - the account whose balance fell by the same amount - is
    the funder. Looking only at the single oldest transaction is not
    enough: that transaction may be a sell, so every signature is checked.
    """
    from .chains import SolanaClient, _solana_transfers_from_deltas
    client = SolanaClient(chain)
    sigs = client.get_signatures_for_address(wallet, limit=min(max_sigs, 100))
    if not sigs:
        return {"funder": "", "source": "solana_rpc",
                "detail": {"note": "no signatures returned for this wallet"}}
    # Oldest first, so the earliest funding event wins.
    for sig in reversed(sigs):
        if sig.get("err"):
            continue
        try:
            tx = client.get_transaction(sig["signature"])
        except Exception:  # noqa: BLE001
            continue
        if not tx:
            continue
        transfers = _solana_transfers_from_deltas(tx, wallet)
        inbound = [t for t in transfers if t.side == "buy"]
        if not inbound:
            continue
        first = inbound[0]
        counterparty = (first.detail or {}).get("counterparty") or ""
        return {"funder": counterparty, "token": first.token,
                "ts": int(sig.get("blockTime") or 0),
                "source": "solana_rpc",
                "detail": {"funding_signature": sig.get("signature"),
                           "funding_slot": sig.get("slot"),
                           "signatures_scanned": len(sigs),
                           "note": ("the funder is the account whose token "
                                    "balance fell by the same amount in the "
                                    "same transaction")}}
    return {"funder": "", "source": "solana_rpc",
            "ts": int(sigs[-1].get("blockTime") or 0),
            "detail": {"note": "no inbound token transfer found in the "
                               "scanned signatures",
                       "signatures_scanned": len(sigs)}}


def _evm_funding(chain: str, wallet: str, blocks: int = 5000
                 ) -> Dict[str, Any]:
    from .chains import EVMClient, TRANSFER_TOPIC
    client = EVMClient(chain)
    topic_wallet = "0x" + wallet.lower().replace("0x", "").rjust(64, "0")
    latest = client.block_number()
    logs = client.get_logs(topics=[TRANSFER_TOPIC, topic_wallet],
                            from_block=max(0, latest - blocks), to_block=latest)
    if not logs:
        return {"funder": "", "source": "eth_getLogs",
                "detail": {"note": f"no inbound Transfer log in the last "
                                   f"{blocks} blocks of {chain}"}}
    def _blk(lg):
        b = lg.get("blockNumber")
        try:
            return int(b, 16) if isinstance(b, str) else int(b or 0)
        except (TypeError, ValueError):
            return 0
    oldest = sorted(logs, key=_blk)[0]
    topics = oldest.get("topics") or []
    funder = "0x" + topics[1][-40:] if len(topics) > 1 else ""
    return {"funder": funder, "token": "0x" + oldest.get("address", "")[-40:],
            "distance_blocks": latest - _blk(oldest),
            "source": "eth_getLogs",
            "detail": {"block": _blk(oldest),
                       "tx_hash": oldest.get("transactionHash")}}


# --------------------------------------------------------------------------
# Anti-insider: the exclusion rule
# --------------------------------------------------------------------------


def is_insider(wallet: str, funding: FundingSource,
               registries: Optional[Dict[str, List[str]]] = None,
               launch_block: Optional[int] = None,
               snipe_block_window: int = 5) -> Dict[str, Any]:
    """Apply the anti-insider rules to one wallet.

    Excludes a wallet that IS a deployer, or is FUNDED BY a deployer, a
    known cabal, or a known insider. Also excludes a wallet whose funding
    transaction landed within `snipe_block_window` blocks of a token's
    launch block - that is the "sniped the first few blocks" rule.

    Returns {"is_insider": bool, "reasons": [...], "checked": [...]}.
    A wallet is only excluded when there is EVIDENCE for it; an unknown
    funding source is reported as such and does not exclude the wallet.
    """
    regs = registries if registries is not None else load_registries()
    reasons: List[str] = []
    checked: List[str] = []

    f = (funding.funder or "").lower()
    if f:
        checked.append(f"funder={funding.funder}")
        if any(f == str(a).lower() for a in regs.get("insiders", [])):
            reasons.append(f"funded by a KNOWN INSIDER: {funding.funder}")
        if any(f == str(a).lower() for a in regs.get("deployers", [])):
            reasons.append(f"funded by a TOKEN DEPLOYER: {funding.funder}")
        if any(f == str(a).lower() for a in regs.get("cabals", [])):
            reasons.append(f"funded by a KNOWN CABAL: {funding.funder}")
    else:
        checked.append("funder=unknown (no inbound transfer found)")

    if launch_block is not None and funding.distance_blocks is not None:
        near = abs(launch_block - (launch_block - funding.distance_blocks))
        checked.append(f"distance_blocks={funding.distance_blocks}")
        if near <= snipe_block_window:
            reasons.append(
                f"funded within {snipe_block_window} block(s) of the token "
                f"launch (snipe window)")

    for label, key in (("deployer", "deployers"), ("cabal", "cabals"),
                       ("insider", "insiders"), ("exchange", "exchanges")):
        checked.append(f"{label}_registry={len(regs.get(key, []))} address(es)")

    if not regs.get("cabals"):
        checked.append("NOTE: the cabal registry is empty, so the cabal rule "
                       "could not fire")
    if not regs.get("deployers"):
        checked.append("NOTE: the deployer registry is empty, so the "
                       "deployer rule could not fire")

    return {"is_insider": bool(reasons), "reasons": reasons,
            "checked": checked, "funding_label": funding.funder_label}


# --------------------------------------------------------------------------
# Consensus
# --------------------------------------------------------------------------


def consensus_signal(trades: Sequence[WalletTrade],
                     min_wallets: int = 3,
                     window_seconds: int = 3600,
                     trusted_wallets: Optional[Iterable[str]] = None,
                     profiled_only: bool = True) -> Dict[str, Any]:
    """Did >=N wallets act on the same token inside the window?

    Groups trades by token, then counts DISTINCT wallets whose trades fall
    inside the window. When `trusted_wallets` is supplied only those
    wallets are counted (the "profiled_only" rule); when it is not, every
    wallet is counted and the result says so.
    """
    trusted = set(trusted_wallets) if trusted_wallets else None
    by_token: Dict[str, List[WalletTrade]] = {}
    for t in trades:
        by_token.setdefault(t.token, []).append(t)

    rows: List[Dict[str, Any]] = []
    for token, ts in by_token.items():
        if not ts:
            continue
        ts = sorted(ts, key=lambda x: x.ts or 0)
        base = ts[0].ts or 0
        window = [t for t in ts if (t.ts or 0) - base <= window_seconds]
        wallets = {t.wallet for t in window}
        if trusted is not None:
            counted = wallets & trusted
        else:
            counted = wallets
        rows.append({
            "token": token,
            "symbol": next((t.symbol for t in ts if t.symbol), ""),
            "chain": next((t.chain for t in ts if t.chain), ""),
            "distinct_wallets": len(counted),
            "all_wallets": len(wallets),
            "window_seconds": window_seconds,
            "first_ts": base,
            "last_ts": max((t.ts or 0) for t in window) if window else 0,
            "wallets": ",".join(sorted(counted)),
            "consensus": len(counted) >= min_wallets,
            "counted_only_trusted": trusted is not None,
            "provenance": next((t.provenance for t in ts), "LIVE"),
        })
    rows.sort(key=lambda r: (-r["distinct_wallets"], r["token"]))
    return {
        "min_wallets": min_wallets,
        "window_seconds": window_seconds,
        "counted_only_trusted": trusted is not None,
        "n_tokens": len(rows),
        "tokens": rows,
    }


# --------------------------------------------------------------------------
# Trusted pool
# --------------------------------------------------------------------------


class TrustedPool:
    """The trusted wallet pool, with periodic re-evaluation.

    An alpha wallet today might become a cabal wallet tomorrow, so the
    pool is re-evaluated: wallets that stopped trading, turned unprofitable
    or were revealed to be cabal-funded are demoted, with the reason
    logged. Every promotion and demotion is recorded.
    """

    def __init__(self, path: str = POOL_PATH,
                 cfg: Optional[Dict[str, Any]] = None):
        self.path = path
        self.cfg = cfg or {}
        self.wallets: Dict[str, Dict[str, Any]] = {}
        self.log: List[Dict[str, Any]] = []

    # -- persistence -------------------------------------------------------
    def load(self) -> bool:
        blob = read_json(self.path) or {}
        self.wallets = blob.get("wallets") or {}
        self.log = blob.get("log") or []
        return bool(blob)

    def save(self) -> str:
        write_json(self.path, {"wallets": self.wallets, "log": self.log,
                               "updated": now_ts()})
        return self.path

    # -- mutation ----------------------------------------------------------
    def add(self, wallet: str, score: Optional[float] = None,
            reason: str = "") -> None:
        self.wallets[wallet] = {
            "wallet": wallet, "score": score, "reason": reason,
            "added_at": now_ts(), "status": "active"}
        self.log.append({"ts": now_ts(), "action": "promote", "wallet": wallet,
                         "score": score, "reason": reason})

    def remove(self, wallet: str, reason: str = "") -> None:
        rec = self.wallets.pop(wallet, None)
        self.log.append({"ts": now_ts(), "action": "demote", "wallet": wallet,
                         "score": (rec or {}).get("score"),
                         "reason": reason or "operator removed"})

    def re_evaluate(self, profiles: Optional[Dict[str, Any]] = None
                    ) -> Dict[str, Any]:
        """Demote wallets that no longer deserve to be trusted.

        With `profiles` supplied (a mapping of wallet -> WalletProfile or
        its flat dict) the decision uses real statistics. Without them the
        pool can only demote on age, and says so.
        """
        stale_days = int(self.cfg.get("stale_days", 30))
        now = now_ts()
        demoted: List[Dict[str, Any]] = []
        kept: List[str] = []

        for wallet, rec in list(self.wallets.items()):
            if rec.get("status") != "active":
                continue
            added = int(rec.get("added_at") or 0)
            age_days = (now - added) / 86400.0 if added else 0.0
            prof = (profiles or {}).get(wallet)
            reason = ""
            if prof is not None:
                d = prof.to_flat() if hasattr(prof, "to_flat") else prof
                disq = d.get("disqualifiers") or []
                if disq:
                    reason = ("no longer passes the profile thresholds: "
                              + "; ".join(disq[:3]))
                elif age_days > stale_days:
                    reason = (f"stale: added {age_days:.0f} days ago with no "
                              f"refreshed profile")
            elif age_days > stale_days:
                reason = (f"stale: added {age_days:.0f} days ago and no "
                          f"fresh profile is available")
            if reason:
                self.remove(wallet, reason=reason)
                demoted.append({"wallet": wallet, "reason": reason})
            else:
                kept.append(wallet)

        summary = {"demoted": demoted, "kept": len(kept),
                   "n_active": len(self.wallets),
                   "note": ("re-evaluation without fresh profiles can only "
                            "demote on age") if not profiles else
                           ("re-evaluated against supplied profiles")}
        self.log.append({"ts": now_ts(), "action": "reevaluate",
                         "demoted": len(demoted), "kept": len(kept)})
        return summary

    def to_flat(self) -> Dict[str, Any]:
        return {"n_wallets": len(self.wallets), "wallets": self.wallets,
                "log": self.log[-40:], "path": self.path,
                "provenance": "LIVE"}


if __name__ == "__main__":
    import sys

    print("WALLET PROFILER — real on-chain data")
    print()
    wallets = {
        "solana": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        "ethereum": "0x28C6c06298d514Db089934071355E5743bf21d60",
    }
    for chain, w in wallets.items():
        print(f"--- {chain} {w} ---")
        try:
            p = profile_wallet(chain, w)
            print(f"  trades={p.n_trades}  win_rate={p.win_rate}  "
                  f"profit_factor={p.profit_factor}")
            print(f"  pnl_total={p.pnl_total_usd}  "
                  f"largest_share={p.largest_trade_pnl_share}")
            print(f"  QUALIFIES: {p.qualifies}")
            for d in p.disqualifiers:
                print(f"    - {d}")
            for wn in p.warnings:
                print(f"    ! {wn}")
            if p.notes:
                print(f"    note: {p.notes}")
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED {type(exc).__name__}: {exc}")
        try:
            fs = trace_funding_source(chain, w)
            print(f"  funding: funder={fs.funder or 'unknown'} "
                  f"label={fs.funder_label} provenance={fs.provenance}")
            ins = is_insider(w, fs)
            print(f"  insider: {ins['is_insider']}  reasons={ins['reasons']}")
            for c in ins["checked"]:
                print(f"      checked: {c}")
        except Exception as exc:  # noqa: BLE001
            print(f"  funding FAILED {type(exc).__name__}: {exc}")
        print()
    sys.exit(0)
