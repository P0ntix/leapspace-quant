"""
Crypto wallet tracking and transaction analysis.

Source paper: "Meme coin trading strategies" (LeapSpace). Its Layer 4
(Manipulation Check) and Layer 2 (Structural Safety) require looking at
wallet-level behaviour on-chain:

  * "Track wallet clusters, not just unique holders, to detect insider-linked
     control"
  * "common funding sources, repeated synchronized buys, looping transfers
     between related wallets, and abrupt ownership changes around price spikes"
  * "repeated transfers, circular flows, self-trading, and abnormal ownership
     anomalies"

Chain: Solana. Two access paths, in order of preference:
  1. Helius (DAS + Enhanced Transactions) when HELIUS_API_KEY is set —
     richer parsing, higher rate limits, free tier available.
  2. Public Solana RPC (api.mainnet-beta.solana.com) — no key, works for
     getSignaturesForAddress / getTransaction / getTokenAccounts / getBalance.
     Verified live from this host.

Every function returns data plus provenance. When neither path is available
the caller gets a SourceUnavailable, never a fabricated wallet summary.
"""

from __future__ import annotations

import datetime as _dt
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .http import HttpError, http_json, http_post_json
from .provenance import Provenance, SourceUnavailable

PUBLIC_RPC = "https://api.mainnet-beta.solana.com"
HELIUS_RPC = "https://mainnet.helius-rpc.com/?api-key={key}"
HELIUS_API = "https://api-mainnet.helius-rpc.com/v0"


def helius_key() -> Optional[str]:
    return os.environ.get("HELIUS_API_KEY") or None


def _rpc(method: str, params: List[Any], helius: bool = True,
         retries: int = 4) -> Any:
    """JSON-RPC call with 429-aware backoff.

    The public Solana endpoint rate-limits aggressively under a burst, so a
    429 is retried with a growing delay rather than being reported as a
    source failure on the first occurrence.
    """
    key = helius_key()
    url = HELIUS_RPC.format(key=key) if (helius and key) else PUBLIC_RPC
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    last: Optional[Exception] = None
    for attempt in range(retries):
        try:
            body, status = http_post_json(url, payload, timeout=45)
        except HttpError as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
            continue
        if isinstance(body, dict) and body.get("error"):
            err = body["error"]
            msg = str(err)
            # "Too many requests" / 429 style errors are retryable.
            if "429" in msg or "too many" in msg.lower() or "rate limit" in msg.lower():
                last = SourceUnavailable(f"rate limited: {msg}")
                time.sleep(2.0 * (attempt + 1))
                continue
            raise SourceUnavailable(f"Solana RPC {method} error: {msg}")
        return body.get("result")
    raise SourceUnavailable(f"Solana RPC {method} failed after {retries} attempts: {last}")


# --------------------------------------------------------------------------
# Raw accessors
# --------------------------------------------------------------------------


def get_signatures(address: str, limit: int = 50, before: Optional[str] = None
                   ) -> Tuple[List[Dict[str, Any]], Provenance]:
    """Recent transaction signatures for a wallet."""
    params: List[Any] = [address, {"limit": min(limit, 1000)}]
    if before:
        params[1]["before"] = before
    res = _rpc("getSignaturesForAddress", params)
    if res is None:
        raise SourceUnavailable(f"no signatures returned for {address}")
    prov = Provenance(source="solana.rpc.getSignaturesForAddress",
                      url=PUBLIC_RPC,
                      note=f"{len(res)} signatures; "
                           f"{'Helius' if helius_key() else 'public RPC'}")
    return res, prov


def get_transaction(signature: str) -> Tuple[Dict[str, Any], Provenance]:
    """A single parsed transaction."""
    res = _rpc("getTransaction", [signature,
                                  {"maxSupportedTransactionVersion": 0,
                                   "encoding": "jsonParsed"}])
    if res is None:
        raise SourceUnavailable(f"transaction {signature} not found")
    prov = Provenance(source="solana.rpc.getTransaction", url=PUBLIC_RPC,
                      note=f"signature {signature}")
    return res, prov


def get_balance(address: str) -> Tuple[float, Provenance]:
    res = _rpc("getBalance", [address])
    lamports = ((res or {}).get("value") or 0)
    prov = Provenance(source="solana.rpc.getBalance", url=PUBLIC_RPC,
                      note=f"{lamports} lamports")
    return lamports / 1e9, prov


def get_token_accounts(address: str) -> Tuple[List[Dict[str, Any]], Provenance]:
    """All token accounts (and their mints) owned by a wallet."""
    res = _rpc("getTokenAccountsByOwner", [address,
                                           {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                                           {"encoding": "jsonParsed"}])
    accounts = ((res or {}).get("value") or [])
    prov = Provenance(source="solana.rpc.getTokenAccountsByOwner", url=PUBLIC_RPC,
                      note=f"{len(accounts)} token accounts")
    return accounts, prov


def get_asset_holders(mint: str) -> Tuple[List[Dict[str, Any]], Provenance]:
    """Top token accounts for a mint (owner + balance), via getTokenLargestAccounts.

    Solana RPC caps this at 20 accounts per call; pagination is handled by
    walking the cursor. This is a TOP-HOLDERS view, not the full holder set.
    """
    out: List[Dict[str, Any]] = []
    cursor = None
    for _ in range(20):  # hard cap: 20 pages x 20 = 400 accounts
        params: List[Any] = [mint, {"limit": 20}]
        if cursor:
            params[1]["cursor"] = cursor
        res = _rpc("getTokenLargestAccounts", params)
        if not res:
            break
        for a in res.get("value") or []:
            info = a.get("uiAmount")
            out.append({
                "address": a.get("address"),
                "token_account": a.get("address"),
                "amount_raw": (a.get("uiAmountString") or a.get("amount")),
                "amount": info,
            })
        cursor = ((res.get("context") or {}).get("cursor")) or None
        if not cursor:
            break
    prov = Provenance(source="solana.rpc.getTokenLargestAccounts", url=PUBLIC_RPC,
                      note=f"{len(out)} largest token accounts for mint {mint}")
    return out, prov


# --------------------------------------------------------------------------
# Transaction analysis
# --------------------------------------------------------------------------


@dataclass
class WalletTransaction:
    signature: str
    block_time: Optional[int]
    slot: Optional[int]
    fee_lamports: int
    success: bool
    err: Optional[Any]
    native_transfers: List[Dict[str, Any]] = field(default_factory=list)
    token_transfers: List[Dict[str, Any]] = field(default_factory=list)
    account_keys: List[str] = field(default_factory=list)
    log_messages: List[str] = field(default_factory=list)

    @property
    def timestamp(self) -> Optional[_dt.datetime]:
        if self.block_time is None:
            return None
        return _dt.datetime.fromtimestamp(self.block_time, _dt.timezone.utc)

    def counterparties(self) -> List[str]:
        seen: List[str] = []
        for t in self.native_transfers:
            for k in ("from", "to"):
                if t.get(k) and t[k] not in seen:
                    seen.append(t[k])
        for t in self.token_transfers:
            for k in ("from", "to"):
                if t.get(k) and t[k] not in seen:
                    seen.append(t[k])
        return seen


def _balances_to_transfers(meta: Dict[str, Any],
                            owner_accounts: Sequence[str]
                            ) -> List[Dict[str, Any]]:
    """Derive token transfers from pre/post token balances.

    Public Solana RPC often omits `meta.tokenTransfers` for transactions whose
    moves happen inside invoked programs (DEX swaps, routed transfers). The
    `preTokenBalances` / `postTokenBalances` arrays ARE populated, and their
    deltas ARE the transfers. Deriving them from the deltas is therefore the
    reliable path; `meta.tokenTransfers` is used only as a supplement.
    """
    pre = meta.get("preTokenBalances") or []
    post = meta.get("postTokenBalances") or []
    owner_set = set(owner_accounts or [])

    def _index(entries):
        out = {}
        for e in entries:
            key = (e.get("accountIndex"), e.get("mint"))
            ui = e.get("uiTokenAmount") or {}
            amount = ui.get("uiAmountString")
            if amount is None:
                amount = ui.get("uiAmount")
            try:
                amount = float(amount)
            except (TypeError, ValueError):
                amount = 0.0
            owner = e.get("owner")
            out[key] = (amount, owner)
        return out

    p_idx = _index(pre)
    q_idx = _index(post)
    out: List[Dict[str, Any]] = []
    for key, (q_amt, q_owner) in q_idx.items():
        p_amt = p_idx.get(key, (0.0, None))[0]
        delta = q_amt - p_amt
        if abs(delta) < 1e-12:
            continue
        owner = q_owner or p_idx.get(key, (0.0, None))[1]
        out.append({
            "mint": key[1],
            "from": owner if delta < 0 else None,
            "to": owner if delta > 0 else None,
            "amount": abs(delta),
            "owner": owner,
            "owner_in_account_keys": owner in owner_set if owner else False,
            "source": "balance_delta",
        })
    return out


def _parsed_instruction_transfers(tx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract transfers from `parsed` instructions (System/SPL transfers)."""
    out: List[Dict[str, Any]] = []
    msg = (tx.get("transaction") or {}).get("message") or {}
    for ix in (msg.get("instructions") or []):
        info = ix.get("parsed") or {}
        if not isinstance(info, dict):
            continue
        itype = info.get("type")
        if itype in ("transfer", "transferWithSeed"):
            src = info.get("source")
            dst = info.get("destination")
            lam = (info.get("info") or {}).get("lamports")
            try:
                lam = float(lam)
            except (TypeError, ValueError):
                lam = 0.0
            if src and dst:
                out.append({"from": src, "to": dst, "amount": lam / 1e9,
                            "token": "SOL", "source": "parsed_instruction"})
        elif itype in ("transferChecked", "transferCheckeds") or \
                info.get("program") == "spl-token" and itype in ("transfer", "transferChecked"):
            info2 = info.get("info") or {}
            src = info2.get("source")
            dst = info2.get("destination")
            amt = info2.get("tokenAmount") or {}
            try:
                a = float(amt.get("uiAmountString") or amt.get("uiAmount") or 0.0)
            except (TypeError, ValueError):
                a = 0.0
            if src and dst:
                out.append({"from": src, "to": dst, "amount": a,
                            "token": amt.get("mint"), "source": "parsed_instruction"})
    return out


def parse_transaction(tx: Dict[str, Any]) -> WalletTransaction:
    meta = tx.get("meta") or {}
    inner = ((tx.get("transaction") or {}).get("message") or {})
    keys = inner.get("accountKeys") or []
    resolved = []
    for k in keys:
        if isinstance(k, dict):
            resolved.append(k.get("pubkey"))
        else:
            resolved.append(k)
    resolved = [k for k in resolved if k]

    native = list(meta.get("nativeTransfers") or [])
    token = list(meta.get("tokenTransfers") or [])
    # Supplement with balance deltas and parsed instructions, which public
    # RPC provides even when meta.tokenTransfers is omitted.
    for t in _balances_to_transfers(meta, resolved):
        token.append({"mint": t["mint"], "from": t["from"], "to": t["to"],
                      "tokenAmount": {"uiAmountString": str(t["amount"])},
                      "_derived": True})
    for t in _parsed_instruction_transfers(tx):
        if t.get("token") == "SOL":
            native.append({"from": t["from"], "to": t["to"],
                            "amount": int(t["amount"] * 1e9)})
        else:
            token.append({"mint": t.get("token"), "from": t.get("from"),
                          "to": t.get("to"),
                          "tokenAmount": {"uiAmountString": str(t.get("amount") or 0)},
                          "_derived": True})

    return WalletTransaction(
        signature=tx.get("signature") or "",
        block_time=tx.get("blockTime"),
        slot=tx.get("slot"),
        fee_lamports=int(meta.get("fee") or 0),
        success=meta.get("err") is None,
        err=meta.get("err"),
        native_transfers=native,
        token_transfers=token,
        account_keys=resolved,
        log_messages=(meta.get("logMessages") or []),
    )


@dataclass
class WalletProfile:
    address: str
    n_signatures: int = 0
    n_transactions_fetched: int = 0
    n_failed_transactions: int = 0
    total_fees_lamports: int = 0
    sol_balance: Optional[float] = None
    counterparties: Dict[str, int] = field(default_factory=dict)
    token_mints: Dict[str, int] = field(default_factory=dict)
    native_outflow_lamports: int = 0
    native_inflow_lamports: int = 0
    token_inflows: Dict[str, float] = field(default_factory=dict)
    token_outflows: Dict[str, float] = field(default_factory=dict)
    first_seen: Optional[int] = None
    last_seen: Optional[int] = None
    loops: List[Dict[str, Any]] = field(default_factory=list)
    self_trades: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    provenance: List[Provenance] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "n_signatures": self.n_signatures,
            "n_transactions_fetched": self.n_transactions_fetched,
            "n_failed_transactions": self.n_failed_transactions,
            "total_fees_lamports": self.total_fees_lamports,
            "sol_balance": self.sol_balance,
            "unique_counterparties": len(self.counterparties),
            "top_counterparties": sorted(self.counterparties.items(),
                                         key=lambda kv: -kv[1])[:10],
            "unique_token_mints": len(self.token_mints),
            "native_outflow_sol": self.native_outflow_lamports / 1e9,
            "native_inflow_sol": self.native_inflow_lamports / 1e9,
            "token_inflows": dict(sorted(self.token_inflows.items(),
                                         key=lambda kv: -kv[1])[:15]),
            "token_outflows": dict(sorted(self.token_outflows.items(),
                                          key=lambda kv: -kv[1])[:15]),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "loop_transactions": self.loops,
            "self_trades": self.self_trades,
            "warnings": self.warnings,
            "provenance": [p.disclosure() for p in self.provenance],
        }


def analyse_wallet(address: str, tx_limit: int = 50,
                    fetch_transactions: bool = True) -> WalletProfile:
    """Fetch and analyse a wallet's recent activity.

    Detects, per the meme-coin paper's manipulation layer:
      * repeated transfers to the same counterparty (clustering signal)
      * circular flows (A -> B -> A within the sampled window)
      * self-trades (both sides of a transfer are the same wallet)
      * concentration of token mints traded
    """
    prof = WalletProfile(address=address)
    sigs, prov = get_signatures(address, limit=tx_limit)
    prof.n_signatures = len(sigs)
    prof.provenance.append(prov)
    if sigs:
        prof.first_seen = min((s.get("blockTime") or 0) for s in sigs if s.get("blockTime")) or None
        prof.last_seen = max((s.get("blockTime") or 0) for s in sigs if s.get("blockTime")) or None

    if fetch_transactions:
        seen_edges: List[Tuple[str, str, str]] = []  # (from, to, token)
        for s in sigs:
            sig = s.get("signature")
            if not sig:
                continue
            try:
                tx, tprov = get_transaction(sig)
            except SourceUnavailable:
                prof.n_failed_transactions += 1
                continue
            prof.provenance.append(tprov)
            wt = parse_transaction(tx)
            prof.n_transactions_fetched += 1
            prof.total_fees_lamports += wt.fee_lamports
            if not wt.success:
                prof.n_failed_transactions += 1
                continue
            for t in wt.native_transfers:
                f, to = t.get("from"), t.get("to")
                lam = int(t.get("amount") or 0)
                if f == address:
                    prof.native_outflow_lamports += lam
                if to == address:
                    prof.native_inflow_lamports += lam
                if f and to:
                    other = to if f == address else f
                    prof.counterparties[other] = prof.counterparties.get(other, 0) + 1
                    seen_edges.append((f, to, "SOL"))
            for t in wt.token_transfers:
                f, to = t.get("from"), t.get("to")
                mint = t.get("mint") or "?"
                amt = float(t.get("tokenAmount", {}).get("uiAmountString")
                            or t.get("uiAmount") or 0.0)
                prof.token_mints[mint] = prof.token_mints.get(mint, 0) + 1
                # A balance-delta transfer carries the OWNER, not from/to.
                # When the owner is the tracked wallet, the direction is
                # inferred from the sign of the delta.
                owner = t.get("owner")
                if owner == address and f is None and to is None:
                    # Direction unknown from the delta alone; record the mint
                    # as touched but do NOT invent a counterparty.
                    continue
                if f == address:
                    prof.token_outflows[mint] = prof.token_outflows.get(mint, 0.0) + amt
                if to == address:
                    prof.token_inflows[mint] = prof.token_inflows.get(mint, 0.0) + amt
                if f and to:
                    other = to if f == address else f
                    prof.counterparties[other] = prof.counterparties.get(other, 0) + 1
                    seen_edges.append((f, to, mint))
                    if f == to:
                        prof.self_trades.append({"signature": wt.signature,
                                                "token": mint, "amount": amt})
            # circular flow: a counterparty that also appears as a sender
            # back to this wallet
        # circular-flow detection over the sampled edges
        pair_count: Dict[Tuple[str, str, str], int] = defaultdict(int)
        for f, to, tok in seen_edges:
            pair_count[(f, to, tok)] += 1
        for (f, to, tok), c in list(pair_count.items()):
            if (to, f, tok) in pair_count:
                prof.loops.append({"from": f, "to": to, "token": tok,
                                   "count_a_to_b": c,
                                   "count_b_to_a": pair_count[(to, f, tok)]})
    try:
        bal, bprov = get_balance(address)
        prof.sol_balance = bal
        prof.provenance.append(bprov)
    except SourceUnavailable as exc:
        prof.warnings.append(f"balance unavailable: {exc}")
    return prof


def cluster_wallets(wallets: Sequence[WalletProfile],
                    min_shared: int = 2) -> Dict[str, Any]:
    """Cluster wallets that share funding sources / counterparties.

    The meme-coin paper's Layer 2 says wallet LINKAGE matters more than raw
    holder counts: "Fund-flow similarity and anomalous transaction patterns
    can reveal wallets that appear distinct but behave as a coordinated
    cluster."

    This is a FUNDING-SOURCE GRAPH, not a proof of coordination. The paper
    says exactly this ("wallet clustering ... not directly tested"), so the
    output is a candidate-cluster list for manual review, not a verdict.
    """
    addresses = {w.address for w in wallets}
    shared: Dict[str, set] = {a: set() for a in addresses}
    for w in wallets:
        peers = set(w.counterparties) & addresses
        for p in peers:
            shared[w.address].add(p)
            shared[p].add(w.address)
    clusters: List[List[str]] = []
    seen = set()
    for a in addresses:
        if a in seen:
            continue
        group = {a} | shared[a]
        if len(group) >= 2:
            clusters.append(sorted(group))
            seen |= group
    clusters = [c for c in clusters if len(c) >= 2]
    out = {
        "n_wallets": len(addresses),
        "n_clusters": len(clusters),
        "clusters": clusters,
        "min_shared_counterparties": min_shared,
        "interpretation": ("Candidate clusters share >=1 counterparty within "
                            "the sampled window. This is a FUNDING/TRANSFER "
                            "LINKAGE signal, not proof of coordinated trading "
                            "or insider control — the source paper states "
                            "this link is not directly tested."),
    }
    return out


def concentration_report(mint: str) -> Tuple[Dict[str, Any], List[Provenance]]:
    """Top-holder concentration for a token — the paper's structural-risk layer.

    "if attention is rising while concentration remains extreme, the token may
    be attracting exit liquidity rather than healthy distribution."
    """
    accounts, prov = get_asset_holders(mint)
    if not accounts:
        raise SourceUnavailable(f"no token accounts returned for mint {mint}")
    total = sum(float(a.get("amount") or 0.0) for a in accounts)
    top = sorted(accounts, key=lambda a: -float(a.get("amount") or 0.0))
    shares = []
    for a in top:
        amt = float(a.get("amount") or 0.0)
        shares.append({"token_account": a.get("address"),
                       "amount": amt,
                       "pct_of_top20": (amt / total * 100.0) if total else None})
    top1 = shares[0]["pct_of_top20"] if shares else None
    top10 = sum(s["amount"] for s in shares[:10])
    top10_pct = (top10 / total * 100.0) if total else None
    return {
        "mint": mint,
        "accounts_covered": len(accounts),
        "coverage_note": ("This is the LARGEST-accounts view only (Solana RPC "
                          "caps getTokenLargestAccounts at 20 per page and the "
                          "walk is bounded at 400 accounts). It is NOT the full "
                          "holder set, so percentages are of the covered set, "
                          "not of total supply."),
        "top1_pct_of_covered": top1,
        "top10_pct_of_covered": top10_pct,
        "holders": shares[:20],
        "structural_risk_read": _concentration_read(top1, top10_pct),
    }, [prov]


def _concentration_read(top1: Optional[float],
                        top10: Optional[float]) -> str:
    """Thresholds are ANALYST CHOICES, disclosed as such — the paper does not
    quantify them ("short-horizon predictive thresholds are not directly
    quantified")."""
    if top1 is None:
        return "Concentration could not be computed (no covered accounts)."
    top10_txt = f"{top10:.1f}" if top10 is not None else "n/a"
    if top1 >= 50.0:
        return (f"EXTREME: the single largest covered account holds {top1:.1f}% "
                f"of the covered supply. The paper's Libra case had 92.8% "
                f"creator control and insider-style gains; treat this as a "
                f"structural-risk red flag.")
    if top10 is not None and top10 >= 60.0:
        return (f"HIGH: the top 10 covered accounts hold {top10_txt}% of the "
                f"covered supply — concentration above what healthy "
                f"distribution implies.")
    if top1 >= 20.0:
        return f"MODERATE: the largest covered account holds {top1:.1f}%."
    return (f"LOW by this measure: largest covered account {top1:.1f}%, "
            f"top-10 {top10_txt}%.")
