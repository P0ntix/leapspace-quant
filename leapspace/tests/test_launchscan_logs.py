"""Tests for the log-based launch-window scan.

THE GAP THIS FILE CLOSES
    `leapspace.launchscan.early_buyers` identified the launch window by
    paging Blockscout's token-transfers endpoint BACKWARDS through the
    token's ENTIRE history until it reached the first transfer. For any
    token with thousands of transfers that never terminates in practice:

        PEPE:  read 600 transfers over 12 pages without reaching the
               start of this token's history -> "insufficient_history"
        TURBO: read 750 transfers over 15 pages -> "insufficient_history"

    Both are long-established tokens, so this is not an edge case - it
    is the normal case, and it means `early_buyers` (and therefore
    `screen_early_buyers`, and therefore `edge.screen_universe`) could
    never run on a real token.

THE FIX
    Ask the chain directly for the answer. The launch block is known
    (`token_launch`), and an ERC-20's transfers are `Transfer` LOGS
    emitted by the token contract. `eth_getLogs` over
    [launch_block, launch_block + window] returns exactly the launch
    window's transfers in one or two calls, with no history walk.

    Verified live: PEPE's launch block is 17046105 and the log query
    returns the mint and the first buyers in seconds, where the paging
    approach could not reach the same window after 750 transfers.

WHAT THIS FILE ASSERTS
    The log decoder and the window scan, against SYNTHETIC logs, so the
    suite is offline and deterministic. The live path is exercised by
    the network tests, not here.

Run: python leapspace/tests/test_launchscan_logs.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

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


#: A synthetic ERC-20 Transfer log, in the shape eth_getLogs returns.
def _log(block: int, frm: str, to: str, amount: int, log_index: int = 0):
    def pad(addr: str) -> str:
        return "0x" + addr.lower().replace("0x", "").rjust(64, "0")
    return {
        "address": "0x" + "11" * 20,
        "topics": [
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4"
            "df523b3ef",
            pad(frm),
            pad(to),
        ],
        "data": "0x" + format(amount, "064x"),
        "blockNumber": hex(block),
        "transactionHash": "0x" + "aa" * 32,
        "logIndex": hex(log_index),
        "removed": False,
    }


print("=" * 72)
print("TEST 1 — the log decoder exists and reads the real log shape")
print("=" * 72)

from leapspace import launchscan as LS  # noqa: E402

check(
    "launchscan exposes a log decoder",
    hasattr(LS, "decode_transfer_logs"),
    "there is no log decoder — the launch scan still walks history",
)

check(
    "the decoder is documented",
    bool((LS.decode_transfer_logs.__doc__ or "").strip())
    if hasattr(LS, "decode_transfer_logs") else False,
    "no docstring",
)

if hasattr(LS, "decode_transfer_logs"):
    LOGS = [
        # the mint: 0x0 -> deployer, 1,000,000,000 tokens
        _log(17046105, "0x" + "00" * 20, "0x" + "aa" * 20, 10 ** 27, 100),
        # first buyer: 3 tokens
        _log(17046538, "0x" + "aa" * 20, "0x" + "bb" * 20, 3 * 10 ** 18, 7),
        # a second buy by the same wallet: 1 token
        _log(17046600, "0x" + "aa" * 20, "0x" + "bb" * 20, 1 * 10 ** 18, 9),
        # someone else: 5 tokens
        _log(17047000, "0x" + "aa" * 20, "0x" + "cc" * 20, 5 * 10 ** 18, 11),
    ]

    decoded = LS.decode_transfer_logs(LOGS, decimals=18)

    check(
        "the mint is excluded (it is not a BUY)",
        all(d["to"] != "0x" + "aa" * 20 for d in decoded),
        "the mint was treated as a purchase",
    )
    check(
        "two RECIPIENTS are decoded (the two bb buys aggregate)",
        len(decoded) == 2,
        f"decoded {len(decoded)} transfers: {decoded}",
    )

    bb = [d for d in decoded if d["to"] == "0x" + "bb" * 20]
    check(
        "the two buys by the same wallet are aggregated",
        len(bb) == 1 and bb[0]["n_buys"] == 2,
        f"bb entries: {bb}",
    )
    check(
        "the aggregated amount is the SUM of both buys (3 + 1 = 4 tokens)",
        bb and abs(bb[0]["bought"] - 4.0) < 1e-9,
        f"bought={bb[0]['bought'] if bb else None} (expected 4.0)",
    )
    cc = [d for d in decoded if d["to"] == "0x" + "cc" * 20]
    check(
        "a single buy keeps its amount (5 tokens)",
        cc and abs(cc[0]["bought"] - 5.0) < 1e-9,
        f"bought={cc[0]['bought'] if cc else None} (expected 5.0)",
    )
    check(
        "the first block is the EARLIEST buy",
        bb and bb[0]["first_block"] == 17046538,
        f"first_block={bb[0]['first_block'] if bb else None}",
    )
    check(
        "the last block is the LATEST buy",
        bb and bb[0]["last_block"] == 17046600,
        f"last_block={bb[0]['last_block'] if bb else None}",
    )
    check(
        "the block number is decoded from hex",
        bb and bb[0]["first_block"] == int(hex(17046538), 16),
        "block numbers were not decoded from hex",
    )

print()
print("=" * 72)
print("TEST 2 — the window scan is bounded by the window")
print("=" * 72)

if hasattr(LS, "decode_transfer_logs"):
    LAUNCH = 17046105

    # A buy well outside the window must not appear.
    logs = [
        _log(LAUNCH, "0x" + "00" * 20, "0x" + "aa" * 20, 10 ** 27, 1),
        _log(LAUNCH + 50, "0x" + "aa" * 20, "0x" + "bb" * 20, 10 ** 24, 2),
        _log(LAUNCH + 5000, "0x" + "aa" * 20, "0x" + "dd" * 20, 10 ** 24, 3),
    ]
    scanned = LS.scan_launch_window(
        logs, launch_block=LAUNCH, window_blocks=1000, decimals=18)

    check(
        "the scan reports ok",
        scanned.get("status") == "ok",
        f"status={scanned.get('status')}",
    )
    buyers = scanned.get("buyers") or []
    check(
        "only buyers inside the window are listed",
        all(b["first_block"] <= LAUNCH + 1000 for b in buyers),
        f"buyers={buyers}",
    )
    check(
        "a buyer outside the window is excluded",
        all(b["to"] != "0x" + "dd" * 20 for b in buyers),
        "an out-of-window buyer was included",
    )
    check(
        "the entry lag is computed from the launch block",
        buyers and buyers[0]["entry_lag_blocks"] == 50,
        f"lags={[b.get('entry_lag_blocks') for b in buyers]}",
    )
    check(
        "the entry class is assigned",
        buyers and buyers[0].get("entry_class"),
        "no entry_class assigned",
    )
    check(
        "the scan says it used logs, not a history walk",
        "log" in str(scanned.get("method", "")).lower(),
        f"method={scanned.get('method')!r}",
    )

print()
print("=" * 72)
print("TEST 3 — the scan is honest about an empty window")
print("=" * 72)

if hasattr(LS, "decode_transfer_logs"):
    scanned = LS.scan_launch_window(
        [], launch_block=17046105, window_blocks=1000, decimals=18)
    check(
        "an empty log set returns ok with zero buyers",
        scanned.get("status") == "ok" and not scanned.get("buyers"),
        f"scanned={scanned}",
    )
    check(
        "it does NOT claim insufficient history",
        scanned.get("status") != "insufficient_history",
        "an empty window was reported as insufficient history",
    )

print()
print("=" * 72)
print("TEST 4 — the log path is used by early_buyers, not the history walk")
print("=" * 72)

import inspect  # noqa: E402

src = inspect.getsource(LS.early_buyers)
check(
    "early_buyers prefers the log scan",
    "scan_launch_window" in src or "transfer_logs" in src
    or "fetch_transfer_logs" in src,
    "early_buyers does not use the log scan at all",
)

# The history walk stays as a FALLBACK, so the flag legitimately
# remains in the source. What matters is that the log route is tried
# FIRST and that the fallback is only reached when the log route
# failed. So assert the ORDER, not the absence of the flag.
log_at = src.find("fetch_transfer_logs")
walk_at = src.find("fetch_token_transfers")
check(
    "the log route is tried BEFORE the history walk",
    log_at != -1 and walk_at != -1 and log_at < walk_at,
    f"log route at {log_at}, history walk at {walk_at}",
)
check(
    "the history walk is only reached when the log route failed",
    "if logs.get(\"ok\"):" in src,
    "the fallback is not guarded by the log route's success",
)
check(
    "the fallback path is labelled as such",
    "log route unavailable" in src,
    "the fallback does not say which route produced the result",
)

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
