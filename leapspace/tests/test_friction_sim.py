"""Regression tests for the copy-trade simulator's OFFLINE path.

WHY THIS FILE EXISTS
    The simulator is the ONLY path to a simulated P&L in this package,
    and it is the only way to test capital movement without risking
    money. It was broken in three ways that a green test suite did not
    catch, because nothing exercised the COMMAND:

      1. `cmd_simulate` called `.get()` on a `RugEvent` dataclass ->
         AttributeError, crash on any run that injected a rug.
      2. `cmd_simulate` read `stats['total_return']` and
         `stats['max_drawdown']`, but the keys are `total_return_pct`
         and `max_drawdown_pct` -> the report said "n/a" for numbers
         that existed.
      3. `cmd_simulate` called `.get()` on a `TradeRecord` dataclass
         -> AttributeError listing skipped trades.

    Plus: `--json` printed config warnings to STDOUT, so the JSON
    stream was not parseable. A machine-readable output that is not
    machine-readable is a defect.

WHAT THIS FILE IS NOT
    It is NOT a test of the trading logic. The friction model, the rug
    injection and the cost model are exercised elsewhere. This file
    asserts that the COMMAND runs, reports, and emits valid JSON —
    i.e. that the test environment itself works.

Run: python leapspace/tests/test_friction_sim.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PASSED = 0
FAILED = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {label}")
    else:
        FAILED += 1
        print(f"  [FAIL] {label}" + (f"\n         {detail}" if detail else ""))


def _write_fixtures(tmp: str):
    """A tiny deterministic price series and a wallet that buys then sells."""
    prices = [[1700000000 + i * 3600, 1.0 + i * 0.01] for i in range(50)]
    signals = [
        {
            "wallet": "W1", "chain": "solana", "token": "TOK",
            "side": "buy", "amount": 1000.0, "price_usd": 1.0,
            "ts": 1700000000,
        },
        {
            "wallet": "W1", "chain": "solana", "token": "TOK",
            "side": "sell", "amount": 1000.0, "price_usd": 1.2,
            "ts": 1700007200,
        },
    ]
    p_path = os.path.join(tmp, "prices.json")
    s_path = os.path.join(tmp, "signals.json")
    with open(p_path, "w", encoding="utf-8") as fh:
        json.dump(prices, fh)
    with open(s_path, "w", encoding="utf-8") as fh:
        json.dump(signals, fh)
    return p_path, s_path


def _run(args):
    return subprocess.run(
        [sys.executable, "-m", "leapspace.cli"] + args,
        capture_output=True, text=True, timeout=300, cwd=ROOT,
    )


print("=" * 72)
print("TEST 1 — the simulator COMMAND runs without crashing")
print("=" * 72)

with tempfile.TemporaryDirectory() as tmp:
    p_path, s_path = _write_fixtures(tmp)
    r = _run(["simulate", "--prices", p_path, "--signals", s_path,
              "--bankroll", "5000"])

    check(
        "exits 0 (no AttributeError, no crash)",
        r.returncode == 0,
        f"exit={r.returncode}\nstderr tail:\n{r.stderr[-1200:]}",
    )
    check(
        "prints the COPY-TRADE SIMULATION header",
        "COPY-TRADE SIMULATION" in r.stdout,
        r.stdout[:300],
    )
    check(
        "reports the SYNTHETIC provenance of the fixtures",
        "SYNTHETIC" in r.stdout,
        "no provenance line found",
    )
    check(
        "carries the synthetic-data disclosure",
        "SYNTHETIC DATA" in r.stdout,
        "the disclosure block is missing — a synthetic run must say so",
    )

print()
print("=" * 72)
print("TEST 2 — the reported numbers are REAL, not 'n/a'")
print("=" * 72)

with tempfile.TemporaryDirectory() as tmp:
    p_path, s_path = _write_fixtures(tmp)
    r = _run(["simulate", "--prices", p_path, "--signals", s_path,
              "--bankroll", "5000"])

    out = r.stdout
    check(
        "reports a non-'n/a' return",
        "return=n/a" not in out,
        "the return is reported as n/a — wrong stats key",
    )
    check(
        "reports a non-'n/a' max drawdown",
        "max_dd=n/a" not in out,
        "the drawdown is reported as n/a — wrong stats key",
    )
    check(
        "lists the injected rug events without crashing",
        "INJECTED RUG EVENTS" in out,
        "no rug section — the RugEvent .get() crash path was not reached",
    )
    check(
        "lists the skipped trades without crashing",
        "SKIPPED TRADES" in out,
        "no skipped section — the TradeRecord .get() crash path was "
        "not reached",
    )

print()
print("=" * 72)
print("TEST 3 — --json emits VALID JSON on stdout")
print("=" * 72)

with tempfile.TemporaryDirectory() as tmp:
    p_path, s_path = _write_fixtures(tmp)
    r = _run(["simulate", "--prices", p_path, "--signals", s_path,
              "--bankroll", "5000", "--json"])

    check("exits 0", r.returncode == 0, f"exit={r.returncode}")
    try:
        payload = json.loads(r.stdout)
        valid = True
    except Exception as exc:  # noqa: BLE001
        payload = {}
        valid = False
        detail = f"{exc}\nstdout head: {r.stdout[:300]!r}"
    check(
        "stdout parses as JSON (config warnings must not pollute it)",
        valid,
        locals().get("detail", ""),
    )

    if valid and payload:
        stats = payload.get("stats") or {}
        trades = payload.get("trades") or []
        check(
            "carries total_return_pct",
            isinstance(stats.get("total_return_pct"), (int, float)),
            f"stats keys: {sorted(stats)}",
        )
        check(
            "carries max_drawdown_pct",
            isinstance(stats.get("max_drawdown_pct"), (int, float)),
            f"stats keys: {sorted(stats)}",
        )
        check(
            "records the trade, so capital movement was TRACKED",
            stats.get("n_trades", 0) >= 1,
            f"n_trades={stats.get('n_trades')}",
        )
        check(
            "marks the prices as SYNTHETIC",
            payload.get("price_provenance") == "SYNTHETIC",
            f"price_provenance={payload.get('price_provenance')!r}",
        )
        check(
            "marks the signals as SYNTHETIC",
            payload.get("signal_provenance") == "SYNTHETIC",
            f"signal_provenance={payload.get('signal_provenance')!r}",
        )
        check(
            "records the skipped trade rather than dropping it",
            any(t.get("skipped") for t in trades),
            "no skipped trade recorded",
        )
        check(
            "carries a per-trade slippage figure",
            any(
                t.get("slippage_usd")
                for t in trades
                if not t.get("skipped")
            ),
            "no trade carries a slippage figure",
        )

print()
print("=" * 72)
print("TEST 4 — the simulation is DETERMINISTIC under a fixed seed")
print("=" * 72)

with tempfile.TemporaryDirectory() as tmp:
    p_path, s_path = _write_fixtures(tmp)
    a = _run(["simulate", "--prices", p_path, "--signals", s_path,
              "--bankroll", "5000", "--seed", "7", "--json"])
    b = _run(["simulate", "--prices", p_path, "--signals", s_path,
              "--bankroll", "5000", "--seed", "7", "--json"])

    try:
        ja, jb = json.loads(a.stdout), json.loads(b.stdout)
        same = (ja.get("stats") == jb.get("stats"))
    except Exception:  # noqa: BLE001
        same = False
    check(
        "the same seed produces the same result",
        same,
        "the simulator is not reproducible under a fixed seed",
    )

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
