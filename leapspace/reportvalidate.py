"""Pre-flight report validator — a REAL gate over generated reports.

WHAT THIS IS
    A package-facing wrapper around the vendored ``data_quality_checker``
    skill that validates a *rendered report* before it is published to
    disk. It runs the five vendored checks (price_scale, notation,
    dates, allocations, units) over the Markdown text, plus a set of
    package-specific adapter checks that the upstream skill does not
    implement.

WHAT THIS IS NOT
    It is NOT a claim that a report is correct. A clean result means
    "the checks that exist found nothing" — not "the report is right".
    It is NOT a substitute for the research gauntlet (PBO, deflated
    Sharpe, walk-forward) in ``leapspace/backtest.py``.

WHY AN ADAPTER EXISTS
    The upstream skill targets traditional market-analysis documents
    (GLD/GC, SPY/SPX, VIX, USO/CL). This package's subject matter is
    memecoins on four chains, where the dominant unit error is
    different in kind: a token *quantity* written in raw base units
    (1 token = 1e18 base units) being compared against a *whole-token*
    price. That error class once shipped a +30,833% return.

    The upstream ``price_scale`` check cannot catch it, because
    ``INSTRUMENT_DIGIT_HINTS`` only covers ten traditional tickers and
    the ETF/futures ratio cross-reference only covers four pairs. The
    adapter therefore adds its own base-unit/whole-token scale check
    (see :func:`_check_base_unit_scale`), and it does so WITHOUT
    modifying the vendored source.

VENDOR CONTRACT
    The vendored code under ``leapspace/vendor/data_quality_checker/``
    is used UNMODIFIED. All package-specific behaviour lives here, in
    the adapter. If the upstream check misfires on this package's
    formats, the adapter is what gets fixed.

SEVERITY MODEL
    The upstream skill emits ``ERROR`` for date/weekday mismatches and
    ``WARNING``/``INFO`` for everything else. This module treats
    ``ERROR`` as blocking and everything else as non-blocking, then
    escalates adapter findings that are unit-scale defects to
    ``ERROR`` — those are the ones that change a number.

WHAT "MISSING" MEANS HERE
    ``n/a`` and ``unavailable`` mean MISSING, never zero. This matters
    because a report that renders an unavailable quantity as ``0`` and
    then computes a return from it is arithmetically wrong in a way no
    reader can detect. The adapter flags zero-valued renders whose
    payload source was unavailable.

SOURCES
    Upstream skill: tradermonty/claude-trading-skills, MIT licensed,
    vendored at ``leapspace/vendor/data_quality_checker/``.
    Vendored commit: d8e71ce2f0b069eb5b6fca352857c168c35e6c46
    See the NOTICE file in the vendor directory for the full terms.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from leapspace.adapter_checks import (
    AdapterUnavailable,
    VendorFinding,
    run_vendor_checks,
)

__all__ = [
    "validate_report",
    "format_validation_block",
    "ADAPTER_CHECK_NAMES",
    "VENDOR_CHECK_NAMES",
]


#: The upstream check names, in the order they are run.
VENDOR_CHECK_NAMES = (
    "price_scale",
    "notation",
    "dates",
    "allocations",
    "units",
)

#: The package-specific adapter checks, in the order they are run.
ADAPTER_CHECK_NAMES = (
    "base_unit_scale",
    "missing_not_zero",
    "percent_scale",
)

#: Severities that block a report. Everything else is advisory.
BLOCKING_SEVERITIES = frozenset({"ERROR"})

#: Tokens whose raw base-unit representation uses 18 decimals. This is
#: the ERC-20 default and what the package's own universe uses.
ERC20_DECIMALS = 18

#: Words that mark a quantity as missing rather than zero.
MISSING_TOKENS = ("n/a", "unavailable", "unknown", "not available")

#: A raw base-unit quantity: an integer with at least 16 digits.
#: 1e15 base units = 0.001 tokens, so any quantity at or above this
#: magnitude that is not a price or a percentage is a raw base-unit
#: rendering.
_RAW_BASE_UNIT = re.compile(r"(?<![\d.$])\d{16,}(?![\d.])")

#: A scientific-notation price, which is how this package renders
#: micro-priced memecoins.
_MICRO_PRICE = re.compile(r"\d\.\d+e-\d+", re.IGNORECASE)

#: A percentage rendered as a 0-100 number.
_PERCENT_100 = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%")

#: A fraction rendered as a 0-1 decimal (no percent sign).
_FRACTION_01 = re.compile(r"(?<![\d.$])(0\.\d{2,})(?![\d%])")

#: A fraction IMMEDIATELY followed by a parenthetical containing a
#: percentage — the shape that states ONE quantity twice. This is the
#: only shape the percent-scale check treats as a contradiction, because
#: a bare line-level co-occurrence fires on unrelated numbers (a
#: holding period next to an allocation) and produced 254 false
#: alarms across the shipped reports.
_FRAC_THEN_PAREN_PCT = re.compile(
    r"(?<![\d.$])(0\.\d{2,})(?![\d%])\s*\([^)\n]{0,80}?"
    r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%[^)\n]{0,80}\)"
)


def _is_missing(value: Any) -> bool:
    """True when a value represents MISSING rather than a real zero."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in MISSING_TOKENS
    return False


def _line_of(text: str, index: int) -> int:
    """1-based line number of a character offset."""
    return text.count("\n", 0, index) + 1


def _check_base_unit_scale(
    text: str, payload: Optional[Dict[str, Any]] = None
) -> List[VendorFinding]:
    """Catch a raw base-unit quantity compared against a whole-token price.

    THE BUG CLASS
        A token amount written in raw base units (e.g.
        ``420000000000000000000`` for 420 tokens at 18 decimals) sits
        next to a whole-token price (e.g. ``$0.0000141``). Multiplying
        the two yields a number ~1e18 too large, which is how a
        +30,833% return shipped once.

    DETECTION
        A 16+ digit integer that is not part of a longer decimal run.
        The vendor's own price_scale check cannot see this because it
        only knows ten traditional tickers.

    FALSE-POSITIVE GUARD
        A 16-digit value that is the fractional tail of a probability
        (``skill p=0.9908419512415418``) is NOT flagged: the integer
        part there is short, so the digits are not a standalone 16+
        digit integer. A standalone 16+ digit integer is flagged
        wherever it appears, because a raw base-unit quantity is wrong
        wherever it is rendered.
    """
    findings: List[VendorFinding] = []
    lines = text.splitlines()

    for match in _RAW_BASE_UNIT.finditer(text):
        raw = match.group(0)
        line_no = _line_of(text, match.start())

        # Skip values that are part of a longer decimal run.
        before = text[max(0, match.start() - 2): match.start()]
        after = text[match.end(): match.end() + 2]
        if before.endswith(".") or after.startswith("."):
            continue

        line_text = lines[line_no - 1] if line_no <= len(lines) else ""
        has_price = bool(re.search(r"\$\s*\d", line_text))
        has_micro_price = bool(_MICRO_PRICE.search(line_text))

        findings.append(
            VendorFinding(
                severity="ERROR",
                category="base_unit_scale",
                message=(
                    f"Raw base-unit quantity {raw} "
                    f"({int(raw) / (10 ** ERC20_DECIMALS):,.6f} tokens at "
                    f"{ERC20_DECIMALS} decimals) appears in the report. "
                    + (
                        "A whole-token price appears on the same line — if "
                        "these two are multiplied, the result is ~1e18 too "
                        "large. Convert the quantity to whole tokens before "
                        "multiplying by price."
                        if has_price or has_micro_price
                        else "Raw base units must be converted to whole "
                        "tokens before they are used in any calculation."
                    )
                ),
                line_number=line_no,
                context=line_text.strip()[:160] or None,
            )
        )
    return findings


def _check_missing_not_zero(
    text: str, payload: Optional[Dict[str, Any]] = None
) -> List[VendorFinding]:
    """Catch a MISSING value rendered as a hard zero.

    ``n/a`` and ``unavailable`` mean the value could not be determined.
    Rendering such a value as ``0`` and then computing a return from it
    is arithmetically wrong: a zero price makes a return undefined, and
    a zero quantity makes a position flat.

    When a payload is supplied, the check looks for keys whose value is
    a missing marker next to a rendered ``0`` for the same key name.
    """
    findings: List[VendorFinding] = []

    if not isinstance(payload, dict):
        return findings

    for key, value in _walk_scalars(payload):
        if not _is_missing(value):
            continue
        key_leaf = str(key).split(".")[-1]
        pattern = re.compile(
            rf"[-*|]?\s*{re.escape(key_leaf)}\s*[:=]?\s*\|?\s*"
            rf"0(?:\.0+)?\b",
            re.IGNORECASE,
        )
        for match in pattern.finditer(text):
            findings.append(
                VendorFinding(
                    severity="ERROR",
                    category="missing_not_zero",
                    message=(
                        f"'{key_leaf}' is unavailable in the payload but is "
                        f"rendered as 0. A missing value must not be rendered "
                        f"as zero — it changes the arithmetic."
                    ),
                    line_number=_line_of(text, match.start()),
                    context=match.group(0).strip()[:160],
                )
            )
    return findings


def _check_percent_scale(
    text: str, payload: Optional[Dict[str, Any]] = None
) -> List[VendorFinding]:
    """Catch a percentage that contradicts itself across the two scales.

    This package's payload carries some percentages as fractions (0.35)
    and some as percent numbers (35). Both forms are legitimate, and
    the report deliberately renders the canonical value and its percent
    equivalent together — e.g. "Engine default 0.10 (10% of a bar's
    dollar volume per order)". That is GOOD practice and is NOT
    flagged.

    What IS a defect is when the two forms of ONE quantity disagree:
    "Engine default 0.10 (20% of a bar's dollar volume)" states two
    different values for the same number, and a reader who picks the
    wrong one makes a 2x error.

    WHY THE MATCH IS DELIBERATELY NARROW
        A report line routinely carries several unrelated numbers — a
        table row can hold a holding period ("0.07d") next to an
        allocation ("80.2%"). Treating "a fraction and a percentage
        appear on the same line" as a defect produced 254 false alarms
        across the shipped reports. The check therefore fires ONLY when
        a fraction is IMMEDIATELY followed by a parenthetical that
        contains a percentage, which is the shape that actually states
        one quantity twice. That is the pattern that would mislead a
        reader, and it is the pattern the real defect takes.

    The check fires only when the two disagree numerically (fraction x
    100 must equal the percentage, within 0.05). A consistent pair is
    never flagged.
    """
    findings: List[VendorFinding] = []

    for match in _FRAC_THEN_PAREN_PCT.finditer(text):
        frac = float(match.group(1))
        pct = float(match.group(2))
        if abs(frac * 100.0 - pct) <= 0.05:
            continue
        line_no = _line_of(text, match.start())
        findings.append(
            VendorFinding(
                severity="WARNING",
                category="percent_scale",
                message=(
                    f"The same quantity is given twice and the two values "
                    f"disagree: {frac:g} as a fraction and {pct:g}% as a "
                    f"percentage ({frac:g} x 100 = {frac * 100:g}%). A "
                    f"reader who takes one of them makes a "
                    f"{max(pct / (frac * 100.0), (frac * 100.0) / pct):.1f}x "
                    f"error. State one value."
                ),
                line_number=line_no,
                context=match.group(0).strip()[:160],
            )
        )
    return findings


def _walk_scalars(
    obj: Any, prefix: str = "", _depth: int = 0
) -> List[Tuple[str, Any]]:
    """Yield ``(dotted_key, value)`` for every scalar in a nested dict."""
    if _depth > 8:
        return []
    out: List[Tuple[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.extend(_walk_scalars(v, key, _depth + 1))
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:200]):
            out.extend(_walk_scalars(v, f"{prefix}[{i}]", _depth + 1))
    else:
        out.append((prefix, obj))
    return out


def _validate_payload(
    text: str, payload: Optional[Dict[str, Any]]
) -> List[VendorFinding]:
    """Adapter checks that need the JSON payload rather than the text."""
    findings: List[VendorFinding] = []
    if not isinstance(payload, dict):
        return findings

    for key, value in _walk_scalars(payload):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        if "pct" not in key.lower() and "percent" not in key.lower():
            continue
        if 0 < value <= 1:
            findings.append(
                VendorFinding(
                    severity="INFO",
                    category="percent_scale",
                    message=(
                        f"Payload key '{key}' carries a 0-1 fraction "
                        f"({value}). Document it as a fraction explicitly so "
                        f"it is not read as a percentage."
                    ),
                    line_number=None,
                    context=key,
                )
            )
    return findings


def validate_report(
    markdown_text: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    checks: Optional[Sequence[str]] = None,
    as_of: Optional[Any] = None,
    filepath: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate a rendered report against the vendored + adapter checks.

    Parameters
    ----------
    markdown_text:
        The rendered Markdown to validate.
    payload:
        Optional JSON payload the Markdown was rendered from. When
        given, the adapter checks that need structured data (missing
        vs zero, percent scale) run as well.
    checks:
        Optional subset of vendor check names to run. Defaults to all.
    as_of:
        Reference date for the upstream date/weekday check.
    filepath:
        Path of the document, used by the upstream check to infer a year
        when the content carries none.

    Returns
    -------
    dict
        ``ok`` is True when no BLOCKING finding was produced.
        ``checks`` lists every check that ran, with its finding count.
        ``errors`` and ``warnings`` hold the blocking and non-blocking
        findings respectively, each a dict with severity, category,
        message, line_number and context.

        When the vendored checkout is missing this returns ``ok=False``
        with a single ERROR finding explaining that no checks ran. It
        never reports a clean bill of health for a check that did not
        run — "no findings" and "could not check" are different claims.
    """
    if not isinstance(markdown_text, str):
        raise TypeError(
            f"markdown_text must be str, got {type(markdown_text).__name__}"
        )

    requested = list(checks) if checks else list(VENDOR_CHECK_NAMES)
    unknown = [c for c in requested if c not in VENDOR_CHECK_NAMES]
    if unknown:
        raise ValueError(
            f"unknown vendor check(s): {unknown}; "
            f"available: {sorted(VENDOR_CHECK_NAMES)}"
        )

    findings: List[VendorFinding] = []
    vendor_status = "ok"

    try:
        findings.extend(
            run_vendor_checks(
                markdown_text,
                checks=requested,
                as_of=as_of,
                filepath=filepath,
            )
        )
    except AdapterUnavailable as exc:
        vendor_status = "unavailable"
        findings.append(
            VendorFinding(
                severity="ERROR",
                category="vendor_unavailable",
                message=(
                    f"{exc}. The vendored data_quality_checker was not "
                    f"found, so NO vendor checks were run. This is not a "
                    f"clean bill of health."
                ),
                line_number=None,
                context=None,
            )
        )

    # Adapter checks run regardless of the vendor's availability — they
    # are package code, not vendored code.
    findings.extend(_check_base_unit_scale(markdown_text, payload))
    findings.extend(_check_missing_not_zero(markdown_text, payload))
    findings.extend(_check_percent_scale(markdown_text, payload))
    findings.extend(_validate_payload(markdown_text, payload))

    errors = [f for f in findings if f.severity in BLOCKING_SEVERITIES]
    warnings = [f for f in findings if f.severity not in BLOCKING_SEVERITIES]

    per_check: Dict[str, int] = {}
    for f in findings:
        per_check[f.category] = per_check.get(f.category, 0) + 1

    return {
        "ok": not errors,
        "checks": [
            {"name": name, "n_findings": per_check.get(name, 0)}
            for name in list(requested) + list(ADAPTER_CHECK_NAMES)
        ],
        "errors": [f.to_dict() for f in errors],
        "warnings": [f.to_dict() for f in warnings],
        "n_findings": len(findings),
        "vendor_status": vendor_status,
    }


def format_validation_block(result: Dict[str, Any]) -> str:
    """Render a machine-readable validation warning block for a report.

    The block names EVERY error. It is emitted into the report itself so
    a reader who never opens the JSON cannot miss that the document
    failed pre-flight validation.

    Returns an empty string when the result is clean.
    """
    errors = result.get("errors") or []
    if not errors:
        return ""

    lines = [
        "---",
        "",
        "## :rotating_light: PRE-FLIGHT VALIDATION FAILURES",
        "",
        f"**{len(errors)} error(s)** were found by the report validator "
        f"before this document was written. Every error is listed below. "
        f"The report was still written — this block is the record of "
        f"known defects in the numbers above.",
        "",
        "```yaml",
        "data_quality_errors:",
    ]
    for i, e in enumerate(errors, start=1):
        lines.append(f"  - id: DQ-{i:03d}")
        lines.append(f"    severity: {e.get('severity')}")
        lines.append(f"    category: {e.get('category')}")
        msg = str(e.get("message", "")).replace('"', "'")
        lines.append(f'    message: "{msg}"')
        if e.get("line_number"):
            lines.append(f"    line: {e['line_number']}")
        if e.get("context"):
            ctx = str(e["context"]).replace('"', "'")[:160]
            lines.append(f'    context: "{ctx}"')
    lines.append("```")
    lines.append("")
    lines.append(
        "Do not act on the affected figures until each error above is "
        "resolved."
    )
    lines.append("")
    return "\n".join(lines)
