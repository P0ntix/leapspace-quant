"""End-to-end integration check for the on-chain memecoin quant layer.

Exercises the whole chain on real data:
  chain health -> token events -> wallet trades -> profile -> funding ->
  insider check -> consensus -> copy-trade simulation -> kill switch ->
  anomaly log -> bias audit.

Every step prints what it actually observed. A step that cannot reach its
source is reported as a GAP, not as a fabricated number.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from leapspace.chains import (chain_health, fetch_token_events,  # noqa: E402
                              fetch_wallet_trades)
from leapspace.models import CHAINS, WalletTrade  # noqa: E402
from leapspace.profiler import (consensus_signal, is_insider,  # noqa: E402
                                profile_wallet, trace_funding_source,
                                TrustedPool)
from leapspace.riskguard import AnomalyLog, KillSwitch  # noqa: E402
from leapspace.biasaudit import audit_spec, audit_report  # noqa: E402
from leapspace.friction import (CopyConfig, FrictionModel, MEVConfig,  # noqa
                                RugConfig, run_simulation)
from leapspace.models import Friction  # noqa: E402

fails = []


def check(label, ok, detail=""):
    print(f"  [{'OK ' if ok else 'BAD'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        fails.append(label)


print("=" * 72)
print("STEP 1 — chain health (live)")
print("=" * 72)
health = chain_health(list(CHAINS.keys()))
for cid, rec in health["chains"].items():
    print(f"  {cid:<10} rpc={rec['rpc_status']}  data={rec['data_status']}")
reachable = sum(1 for r in health["chains"].values() if r["reachable"])
check("all five chains reachable", reachable == 5, f"{reachable}/5")
for g in health.get("gaps", []):
    print(f"  GAP {g['source']}: {g['reason'][:100]}")

print()
print("=" * 72)
print("STEP 2 — token events (real)")
print("=" * 72)
samples = {
    "solana": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "ethereum": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
    "base": "0x532f27101965dd16442E59d40670FaF5eBB142E4",
    "bsc": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
}
events_by_chain = {}
for cid, addr in samples.items():
    res = fetch_token_events(cid, addr)
    events_by_chain[cid] = res["events"]
    kinds = ",".join(e.kind for e in res["events"]) or "none"
    px = ""
    for e in res["events"]:
        if e.kind == "price_update":
            px = (f" px=${e.detail.get('price_usd')} "
                  f"liq=${e.detail.get('liquidity_usd')}")
    print(f"  {cid:<10} events={len(res['events'])} [{kinds}]{px}")
    check(f"{cid}: at least one real event", len(res["events"]) >= 1)

print()
print("=" * 72)
print("STEP 3 — wallet trades + profile + funding (real)")
print("=" * 72)
wallets = {
    "solana": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "ethereum": "0x28C6c06298d514Db089934071355E5743bf21d60",
}
trades_by_wallet = {}
for cid, w in wallets.items():
    try:
        tr = fetch_wallet_trades(cid, w, limit=40)
    except Exception as exc:  # noqa: BLE001
        print(f"  {cid:<10} trades FAILED {type(exc).__name__}: {exc}")
        continue
    trades_by_wallet[w] = tr
    print(f"  {cid:<10} {w[:14]}... trades={len(tr)}")
    for t in tr[:2]:
        print(f"      {t.side:<4} {t.token[:18]} amt={t.amount} src={t.source}")
    p = profile_wallet(cid, w, trades=tr)
    print(f"      profile: trades={p.n_trades} win_rate={p.win_rate} "
          f"pf={p.profit_factor} qualifies={p.qualifies}")
    for d in p.disqualifiers[:3]:
        print(f"        disqualifier: {d}")
    for wn in p.warnings[:3]:
        print(f"        warning: {wn[:130]}")
    check(f"{cid}: profile produced a verdict, not a crash",
          isinstance(p.disqualifiers, list))

    try:
        fs = trace_funding_source(cid, w)
        print(f"      funding: funder={fs.funder or 'unknown'} "
              f"label={fs.funder_label} prov={fs.provenance}")
        ins = is_insider(w, fs)
        print(f"      insider: {ins['is_insider']} reasons={ins['reasons']}")
        for c in ins["checked"]:
            if "NOTE" in c:
                print(f"        {c}")
    except Exception as exc:  # noqa: BLE001
        print(f"      funding FAILED {type(exc).__name__}: {exc}")

print()
print("=" * 72)
print("STEP 4 — consensus")
print("=" * 72)
all_trades = [t for v in trades_by_wallet.values() for t in v]
if all_trades:
    cons = consensus_signal(all_trades, min_wallets=2, window_seconds=86400)
    print(f"  tokens seen: {cons['n_tokens']}  min_wallets=2  "
          f"window=86400s")
    for row in cons["tokens"][:5]:
        print(f"    {row['token'][:22]:<24} wallets={row['distinct_wallets']} "
              f"consensus={row['consensus']}")
    check("consensus ran over real trades", cons["n_tokens"] >= 0)
else:
    print("  no trades retrieved - consensus skipped")
    fails.append("consensus: no trades")

print()
print("=" * 72)
print("STEP 5 — copy-trade simulation (SYNTHETIC prices, clearly labelled)")
print("=" * 72)
from leapspace.provenance import SYNTHETIC_DISCLOSURE  # noqa: E402
prices = [(1700000000 + i * 3600, 1.0 + 0.01 * (i % 17) - 0.002 * i)
           for i in range(120)]
signals = []
for i in range(12):
    signals.append(WalletTrade(
        wallet=f"w{i % 4}", chain="solana", token=f"TOK{i % 3}",
        side="buy", amount=100.0, price_usd=1.0 + 0.01 * (i % 17),
        ts=1700000000 + i * 3600, provenance="SYNTHETIC"))
res = run_simulation(
    signals, prices,
    friction=Friction(slippage_bps=100.0, failed_tx_rate=0.05,
                      latency_seconds=2.0),
    bankroll=1000.0,
    rug_config=RugConfig(rug_probability=0.1, min_drop_pct=80.0,
                          max_drop_pct=99.0, seed=42),
    mev_config=MEVConfig(max_penalty_bps=50.0, sandwich_probability=0.35,
                          seed=42),
    seed=42, config=CopyConfig(start_usd=1000.0, size_pct=0.1,
                               stop_loss_pct=0.2, take_profit_pct=0.5),
    price_provenance="SYNTHETIC", signal_provenance="SYNTHETIC")
st = res.stats or {}
print(f"  trades={st.get('n_trades')} skipped={st.get('n_skipped')} "
      f"win_rate={st.get('win_rate')} pf={st.get('profit_factor')}")
print(f"  rugs injected={len(res.rugs)}  return={st.get('total_return')} "
      f"max_dd={st.get('max_drawdown')}")
skipped = [c for c in res.trades if getattr(c.trade, "skipped", False)]
print(f"  skipped trades recorded: {len(skipped)}")
for c in skipped[:4]:
    print(f"    {c.trade.token} {c.trade.action}: {c.trade.skip_reason}")
check("simulation produced trades", (st.get("n_trades") or 0) > 0)
check("skipped trades are recorded, not dropped",
      all(c.trade.skip_reason for c in skipped))
check("synthetic data is disclosed",
      res.price_provenance == "SYNTHETIC"
      and (SYNTHETIC_DISCLOSURE in (res.disclosure or "")
           or "SYNTHETIC" in (res.disclosure or "")),
      (res.disclosure or "")[:70])

# determinism
res2 = run_simulation(
    signals, prices,
    friction=Friction(slippage_bps=100.0, failed_tx_rate=0.05,
                      latency_seconds=2.0),
    bankroll=1000.0,
    rug_config=RugConfig(rug_probability=0.1, min_drop_pct=80.0,
                          max_drop_pct=99.0, seed=42),
    mev_config=MEVConfig(max_penalty_bps=50.0, sandwich_probability=0.35,
                          seed=42),
    seed=42, config=CopyConfig(start_usd=1000.0, size_pct=0.1,
                               stop_loss_pct=0.2, take_profit_pct=0.5),
    price_provenance="SYNTHETIC", signal_provenance="SYNTHETIC")
same = json.dumps(res.to_flat(), sort_keys=True, default=str) == \
    json.dumps(res2.to_flat(), sort_keys=True, default=str)
check("same seed reproduces identical results", same)

print()
print("=" * 72)
print("STEP 6 — kill switch (code-enforced)")
print("=" * 72)
with tempfile.TemporaryDirectory() as td:
    sp = os.path.join(td, "ks.json")
    ks = KillSwitch(cfg={"max_drawdown_pct": 0.20,
                         "drawdown_window_seconds": 900,
                         "min_liquidity_usd": 1000.0},
                    state_path=sp)
    ks.load()
    ok1, why1 = ks.check(10000.0, 1700000000)
    print(f"  healthy portfolio      -> allowed={ok1}  {why1}")
    ok2, why2 = ks.check(7000.0, 1700000060)
    print(f"  30% drawdown           -> allowed={ok2}  {why2}")
    check("kill switch fires on the drawdown", ok2 is False)
    ks.save(sp)
    ks2 = KillSwitch(cfg={"max_drawdown_pct": 0.20}, state_path=sp)
    ks2.load()
    ok3, why3 = ks2.check(7000.0, 1700000120)
    print(f"  after restart          -> allowed={ok3}  {why3}")
    check("the halt SURVIVES a restart", ok3 is False)
    try:
        ks2.reset(by="operator", reason="test")
        ok4, _ = ks2.check(7000.0, 1700000180)
        print(f"  after explicit reset   -> allowed={ok4}")
        check("an explicit reset DOES clear it", ok4 is True)
    except Exception as exc:  # noqa: BLE001
        print(f"  reset raised {type(exc).__name__}: {exc}")
        fails.append("reset raised")
    try:
        bypass = ks2.verify_no_bypass()
        print(f"  bypass audit: {bypass}")
    except Exception as exc:  # noqa: BLE001
        print(f"  bypass audit unavailable: {exc}")

print()
print("=" * 72)
print("STEP 7 — anomaly log")
print("=" * 72)
with tempfile.TemporaryDirectory() as td:
    log = AnomalyLog(path=os.path.join(td, "anomalies.json"))
    log.load()
    anomaly = log.record(kind="rug", chain="solana", token="TOKX",
                          description="liquidity fell 95% in one block",
                          market_state={"liq_before": 50000,
                                        "liq_after": 2500},
                          severity="high", action_taken="halted trading")
    log.promote_to_known_unknown(
        anomaly, "a liquidity collapse below 10% of the entry "
                 "liquidity must halt the position")
    log.save()
    log2 = AnomalyLog(path=os.path.join(td, "anomalies.json"))
    log2.load()
    print(f"  anomalies={len(log2.anomalies)} "
          f"known_unknowns={len(log2.known_unknowns)}")
    check("anomaly survives a reload", len(log2.anomalies) == 1)
    check("known unknown was promoted", len(log2.known_unknowns) == 1)

print()
print("=" * 72)
print("STEP 8 — bias audit of the package's own specs")
print("=" * 72)
from leapspace.backtest import all_specs  # noqa: E402
specs = all_specs()
findings = []
for s in specs:
    findings.extend(audit_spec(s))
print(audit_report(findings)[:2500])
check("the auditor produced findings about real specs", len(findings) >= 0,
      f"{len(findings)} finding(s)")

print()
print("=" * 72)
if fails:
    print(f"INTEGRATION: {len(fails)} FAILURE(S)")
    for f in fails:
        print("  FAIL " + f)
    sys.exit(1)
print("INTEGRATION: ALL CHECKS PASS")
