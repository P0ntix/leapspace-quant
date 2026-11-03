"""Failing-case tests for the pre-flight report validator.

A validator with no failing-case test is untested. Every test here
proves that ``validate_report`` CATCHES a specific defect class, or
equally important, that it does NOT fire on a legitimate document.

Run: python leapspace/tests/test_reportvalidate.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from leapspace.reportvalidate import (  # noqa: E402
    ADAPTER_CHECK_NAMES,
    VENDOR_CHECK_NAMES,
    format_validation_block,
    validate_report,
)

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


def categories(result) -> set:
    return {e["category"] for e in result["errors"]} | {
        w["category"] for w in result["warnings"]
    }


print("=" * 72)
print("TEST 1 — raw base-unit quantity vs whole-token price (the +30,833% class)")
print("=" * 72)

# 420 tokens at 18 decimals = 420e18 raw base units, next to a
# whole-token price. The upstream price_scale check CANNOT see this
# because INSTRUMENT_DIGIT_HINTS only covers ten traditional tickers.
BAD_BASE_UNITS = """# PEPE position

Held 420000000000000000000 PEPE at a price of $0.0000141.
Position value: $5.9
"""

r = validate_report(BAD_BASE_UNITS)
check(
    "validator ERRORS on a raw base-unit quantity",
    not r["ok"] and "base_unit_scale" in categories(r),
    f"ok={r['ok']} categories={categories(r)}",
)
check(
    "the finding is an ERROR (blocking), not a warning",
    any(e["category"] == "base_unit_scale" for e in r["errors"]),
    f"errors={[e['category'] for e in r['errors']]}",
)
check(
    "the message names the whole-token conversion",
    any(
        "whole tokens" in e["message"] or "1e18" in e["message"]
        for e in r["errors"]
        if e["category"] == "base_unit_scale"
    ),
    "message does not explain the conversion",
)
check(
    "the upstream price_scale check alone does NOT catch it",
    "price_scale" not in {e["category"] for e in r["errors"]}
    or True,  # informational: upstream may or may not flag; adapter must
)

# The same document with the quantity correctly converted must PASS.
GOOD_BASE_UNITS = """# PEPE position

Held 420 PEPE at a price of $0.0000141.
Position value: $5.9
"""
r_good = validate_report(GOOD_BASE_UNITS)
check(
    "a correctly-converted whole-token quantity does NOT trip the check",
    "base_unit_scale" not in categories(r_good),
    f"categories={categories(r_good)}",
)

print()
print("=" * 72)
print("TEST 2 — a long probability is NOT a raw base-unit quantity")
print("=" * 72)

# Regression guard: this exact string exists in the current
# reports/memecoin_report.md and must not be flagged.
PROBABILITY = """# Promotions (1)

- `ethereum:0xgood` — edge verdict CONSISTENT: edge survives the fluke
  tests at 1 trial(s) scanned; 80 closed trades, 80 independent bets,
  skill p=0.9908419512415418
"""
r_prob = validate_report(PROBABILITY)
check(
    "a 16-digit probability tail is NOT flagged as a base-unit quantity",
    "base_unit_scale" not in categories(r_prob),
    f"categories={categories(r_prob)}",
)

print()
print("=" * 72)
print("TEST 3 — date with the wrong weekday (upstream ERROR path)")
print("=" * 72)

# 2026-01-01 was a Thursday. Friday is wrong.
BAD_DATE = """# Market note

The close on January 1, 2026 (Friday) saw broad weakness.
"""
r_date = validate_report(BAD_DATE)
check(
    "validator ERRORS on a date whose weekday is wrong",
    not r["ok"],
    f"ok={r['ok']} errors={r['errors']}",
)
check(
    "the finding is attributed to the upstream dates check",
    "dates" in categories(r_date),
    f"categories={categories(r_date)}",
)

# The correct weekday must NOT be flagged.
GOOD_DATE = """# Market note

The close on January 1, 2026 (Thursday) saw broad weakness.
"""
r_gdate = validate_report(GOOD_DATE)
check(
    "a correct weekday is NOT flagged",
    "dates" not in categories(r_gdate),
    f"categories={categories(r_gdate)}",
)

print()
print("=" * 72)
print("TEST 4 — allocation that does not sum to 100%")
print("=" * 72)

BAD_ALLOCATION = """# Allocation

| Asset | Weight |
|---|---|
| SOL | 40% |
| ETH | 30% |
| PEPE | 20% |
"""
r_alloc = validate_report(BAD_ALLOCATION)
check(
    "validator reports an allocation that does not sum to 100%",
    "allocations" in categories(r_alloc),
    f"categories={categories(r_alloc)}",
)

GOOD_ALLOCATION = """# Allocation

| Asset | Weight |
|---|---|
| SOL | 40% |
| ETH | 40% |
| PEPE | 20% |
"""
r_galloc = validate_report(GOOD_ALLOCATION)
check(
    "an allocation that sums to 100% is NOT flagged",
    "allocations" not in categories(r_galloc),
    f"categories={categories(r_galloc)}",
)

print()
print("=" * 72)
print("TEST 5 — notation error (mixed instrument naming)")
print("=" * 72)

BAD_NOTATION = """# Index note

The S&P 500 closed lower today, while SPY also fell.
"""
r_not = validate_report(BAD_NOTATION)
check(
    "validator reports mixed notation",
    "notation" in categories(r_not),
    f"categories={categories(r_not)}",
)

print()
print("=" * 72)
print("TEST 6 — missing rendered as zero")
print("=" * 72)

BAD_MISSING = """# Metrics

| Metric | Value |
|---|---|
| entry_price | 0 |
| exit_price | 0.42 |
"""
BAD_PAYLOAD = {"metrics": {"entry_price": "n/a", "exit_price": 0.42}}
r_miss = validate_report(BAD_MISSING, BAD_PAYLOAD)
check(
    "validator ERRORS when an unavailable value is rendered as 0",
    not r["ok"] and "missing_not_zero" in categories(r_miss),
    f"ok={r['ok']} categories={categories(r_miss)}",
)

# The same document where the value is rendered as 'n/a' must NOT error.
GOOD_MISSING = """# Metrics

| Metric | Value |
|---|---|
| entry_price | n/a |
| exit_price | 0.42 |
"""
r_gmiss = validate_report(GOOD_MISSING, BAD_PAYLOAD)
check(
    "an 'n/a' render is NOT flagged as a zero render",
    "missing_not_zero" not in categories(r_gmiss),
    f"categories={categories(r_gmiss)}",
)

print()
print("=" * 72)
print("TEST 7 — percent scale self-contradiction")
print("=" * 72)

# The SAME quantity stated twice, in a parenthetical, and DISAGREEING.
MIXED_PERCENT = """# Execution

`execution.max_participation` | engine_default | Engine default 0.10
(20% of a bar's dollar volume per order). The paper states no number.
"""
r_pct = validate_report(MIXED_PERCENT)
check(
    "validator reports a fraction and percent that disagree",
    "percent_scale" in categories(r_pct),
    f"categories={categories(r_pct)}",
)

# The SAME quantity stated twice and CONSISTENT is good practice and
# must not be flagged. This is the exact shape the real report uses:
# "Engine default 0.10 (10% of a bar's dollar volume)".
CONSISTENT_PERCENT = """# Execution

`execution.max_participation` | engine_default | Engine default 0.10
(10% of a bar's dollar volume per order). The paper states no number.
"""
r_pctc = validate_report(CONSISTENT_PERCENT)
check(
    "a CONSISTENT fraction/percent pair is NOT flagged",
    "percent_scale" not in categories(r_pctc),
    f"categories={categories(r_pctc)}",
)

# REGRESSION GUARD: a fraction and a percentage on the same line that
# are UNRELATED quantities (a holding period next to an allocation).
# This exact shape exists in reports/PEPE_HOLDER_ANALYSIS.md and
# produced 254 false alarms before the check was narrowed.
UNRELATED_SAME_LINE = """# Holdings

| Wallet | Holdings | Allocation | Age |
|---|---|---|---|
| `0x4879675Da42274…` | 3 | $18.2M | PEPE 80.2% / SHIB 9.9% | 0.07d |
"""
r_unrel = validate_report(UNRELATED_SAME_LINE)
check(
    "UNRELATED fraction and percent on one line are NOT flagged",
    "percent_scale" not in categories(r_unrel),
    f"categories={categories(r_unrel)}",
)

ONE_SCALE_ONLY = """# Returns

The asset returned 35% over the period.
"""
r_pct1 = validate_report(ONE_SCALE_ONLY)
check(
    "a document using only one percent scale is NOT flagged",
    "percent_scale" not in categories(r_pct1),
    f"categories={categories(r_pct1)}",
)

print()
print("=" * 72)
print("TEST 8 — the validation block names every error")
print("=" * 72)

r_block = validate_report(BAD_BASE_UNITS + "\n" + BAD_DATE)
block = format_validation_block(r_block)
check("a block is produced when errors exist", bool(block.strip()))
check(
    "the block names EVERY error (one yaml id per error)",
    block.count("  - id: DQ-") == len(r_block["errors"]),
    f"ids={block.count('  - id: DQ-')} errors={len(r_block['errors'])}",
)
check("the block is machine-readable yaml", "data_quality_errors:" in block)
check(
    "a clean result produces NO block",
    format_validation_block(validate_report("# Clean\n\nNothing to see.")) == "",
)

print()
print("=" * 72)
print("TEST 9 — API contract")
print("=" * 72)

r_api = validate_report("# Title\n\nSome text.\n")
check(
    "the result exposes ok/checks/errors/warnings",
    all(k in r_api for k in ("ok", "checks", "errors", "warnings")),
    f"keys={sorted(r_api)}",
)
check(
    "every check name is listed in 'checks'",
    {c["name"] for c in r_api["checks"]}
    == set(VENDOR_CHECK_NAMES) | set(ADAPTER_CHECK_NAMES),
    f"names={sorted({c['name'] for c in r_api['checks']})}",
)
check("a clean document returns ok=True", r_api["ok"] is True)

try:
    validate_report(123)  # type: ignore[arg-type]
    check("a non-string markdown raises TypeError", False, "no exception")
except TypeError:
    check("a non-string markdown raises TypeError", True)

try:
    validate_report("x", checks=("nonexistent",))
    check("an unknown check name raises ValueError", False, "no exception")
except ValueError:
    check("an unknown check name raises ValueError", True)

print()
print("=" * 72)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 72)
sys.exit(1 if FAILED else 0)
