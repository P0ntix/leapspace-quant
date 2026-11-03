"""Adapter over the vendored `data_quality_checker` skill.

The vendored skill validates *market analysis documents* — it catches
price-scale slips (a PEPE quoted at $0.014 instead of $1.4e-06),
instrument-notation errors, date/weekday mismatches, allocation totals
that do not add to 100%, and mixed units (bp alongside %).

This module wires that checker into the package so that the reports this
project *generates* are held to the same standard as the documents it
reads. A report that says "PEPE 2024-01-01 was a Tuesday" when it was a
Monday, or that quotes a memecoin price in cents instead of units, is a
data-quality defect in the same class the vendored skill was written to
catch — and this project's whole premise is that bad units are the
difference between a real edge and a fake one.

Design rules obeyed here:
  * The vendored code is used **unmodified**. This module is a thin,
    well-tested adapter around it.
  * Every result carries a provenance string.
  * A missing vendored checkout degrades honestly to an
    ``unavailable`` record — never to a silent "no findings".
  * Findings are advisory (the vendored skill is advisory-mode by
    design), so severities are preserved as-is and the caller decides
    what to escalate.

Vendor: the `data_quality_checker` skill.
Vendored at: leapspace/vendor/data_quality_checker/
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from leapspace.provenance import CACHE, unavailable

__all__ = [
    "AdapterUnavailable",
    "VendorFinding",
    "check_token_activity",
    "run_vendor_checks",
    "vendor_available",
    "VENDOR_REL_PATH",
    "VENDOR_CHECK_NAMES",
]

#: Where the vendored skill lives, relative to the repository root.
VENDOR_REL_PATH = "leapspace/vendor/data_quality_checker"

#: The check names the vendored skill exposes. Kept here so a rename
#: upstream is caught by the test rather than silently disabling checks.
VENDOR_CHECK_NAMES = (
    "price_scale",
    "notation",
    "dates",
    "allocations",
    "units",
)


class AdapterUnavailable(RuntimeError):
    """Raised when the vendored checker cannot be imported."""


@dataclass
class VendorFinding:
    """One finding from the vendored checker, in this package's shape."""

    severity: str
    category: str
    message: str
    line_number: Optional[int] = None
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _vendor_root(package_root: Optional[str] = None) -> Path:
    """Resolve the vendored skill directory.

    ``package_root`` is the repository root (the directory that contains
    ``leapspace/``). When omitted it is derived from this file's
    location, which is the normal in-package case.
    """
    if package_root:
        root = Path(package_root)
    else:
        # .../leapspace/adapter_checks.py -> .../leapspace -> ...
        root = Path(__file__).resolve().parent.parent
    return root / "leapspace" / "vendor" / "data_quality_checker"


def _load_vendor_module(package_root: Optional[str] = None):
    """Import the vendored checker as a standalone module.

    It is loaded by path rather than by package name because the
    vendored tree carries no ``__init__.py`` files (it is a skill
    checkout, not a Python package) and we must not modify it.
    """
    root = _vendor_root(package_root)
    target = root / "scripts" / "check_data_quality.py"
    if not target.is_file():
        raise AdapterUnavailable(
            f"vendored data_quality_checker not found at {target}"
        )

    module_name = "leapspace_vendor_data_quality_checker"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, target)
    if spec is None or spec.loader is None:
        raise AdapterUnavailable(f"cannot load vendored checker at {target}")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so a recursive import does not loop.
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - defensive
        sys.modules.pop(module_name, None)
        raise AdapterUnavailable(
            f"vendored checker failed to import: {exc}"
        ) from exc
    return module


def vendor_available(package_root: Optional[str] = None) -> bool:
    """True when the vendored checker can be imported."""
    try:
        _load_vendor_module(package_root)
    except AdapterUnavailable:
        return False
    return True


def run_vendor_checks(
    content: str,
    checks: Optional[Sequence[str]] = None,
    as_of: Optional[date] = None,
    filepath: Optional[str] = None,
    package_root: Optional[str] = None,
) -> List[VendorFinding]:
    """Run the vendored checks over ``content``.

    Returns the findings as :class:`VendorFinding` objects so callers do
    not depend on the vendored module's internal classes.

    Raises :class:`AdapterUnavailable` when the vendored checkout is
    missing — the caller decides whether that is fatal.
    """
    module = _load_vendor_module(package_root)

    available = getattr(module, "ALL_CHECKS", {})
    requested = list(checks) if checks else list(VENDOR_CHECK_NAMES)
    unknown = [c for c in requested if c not in available]
    if unknown:
        raise ValueError(
            f"unknown vendor check(s): {unknown}; "
            f"available: {sorted(available)}"
        )

    raw = module.run_checks(
        content, checks=requested, as_of=as_of, filepath=filepath
    )
    return [
        VendorFinding(
            severity=f.severity,
            category=f.category,
            message=f.message,
            line_number=getattr(f, "line_number", None),
            context=getattr(f, "context", None),
        )
        for f in raw
    ]


def check_token_activity(
    content: str,
    report_location: Optional[str] = None,
    tags: Optional[List[str]] = None,
    skip_checks: Optional[List[str]] = None,
    as_of: Optional[date] = None,
    package_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Audit a generated research document for data-quality defects.

    This is the package-facing entry point. It runs the vendored skill's
    five checks over ``content`` and returns a record that is safe to
    embed in a report.

    Parameters
    ----------
    content:
        The document text to audit.
    report_location:
        Where the document came from (a path or URL). Used only for
        labelling; it is never fetched.
    tags:
        Optional labels carried through to the result.
    skip_checks:
        Vendor check names to skip. Defaults to none.
    as_of:
        Reference date for the vendor's date/weekday check.
    package_root:
        Repository root, when not running from inside the package.

    Returns
    -------
    dict
        ``status`` is ``"ok"`` when the audit ran, ``"unavailable"``
        when the vendored checkout is missing. The unavailable record
        names what is missing — it never reports zero findings, because
        "no findings" and "could not check" are different claims.
    """
    skip = set(skip_checks or ())
    requested = [c for c in VENDOR_CHECK_NAMES if c not in skip]

    try:
        findings = run_vendor_checks(
            content,
            checks=requested,
            as_of=as_of,
            filepath=report_location,
            package_root=package_root,
        )
    except AdapterUnavailable as exc:
        return unavailable(
            "vendor:data_quality_checker",
            None,
            f"{exc}. The vendored skill was not found, so NO data-quality "
            f"checks were run. This is not a clean bill of health.",
        )

    by_severity: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_category[f.category] = by_category.get(f.category, 0) + 1

    return {
        "status": "ok",
        "provenance": CACHE,
        "report_location": report_location,
        "tags": list(tags or []),
        "checks_run": requested,
        "checks_skipped": sorted(skip),
        "n_findings": len(findings),
        "by_severity": by_severity,
        "by_category": by_category,
        "findings": [f.to_dict() for f in findings],
        "advisory": True,
        "note": (
            "The vendored data_quality_checker is advisory by design: "
            "findings are warnings for human review, not automatic failures. "
            "A clean result means the five vendored checks found nothing - "
            "it does not certify the document is correct."
        ),
        "vendor": "data_quality_checker (vendored, unmodified)",
    }


def main() -> int:
    """Audit every generated markdown report in ``reports/``.

    Writes ``reports/data_quality.json`` and prints a summary. Exits
    non-zero if any report has ERROR-severity findings.
    """
    import argparse
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Audit generated reports.")
    parser.add_argument(
        "--reports-dir", default=str(root / "reports"),
        help="directory of markdown reports to audit",
    )
    parser.add_argument(
        "--output", default=str(root / "reports" / "data_quality.json"),
        help="where to write the JSON result",
    )
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_dir():
        print(f"no reports directory at {reports_dir}")
        return 2

    targets = sorted(reports_dir.glob("*.md"))
    if not targets:
        print(f"no markdown reports in {reports_dir}")
        return 2

    results = []
    total_errors = 0
    for path in targets:
        text = path.read_text(encoding="utf-8", errors="replace")
        result = check_token_activity(
            text, report_location=str(path), tags=["report"]
        )
        result["file"] = path.name
        results.append(result)
        if result.get("status") == "ok":
            n_err = result.get("by_severity", {}).get("ERROR", 0)
            total_errors += n_err
            print(f"{path.name}: {result['n_findings']} finding(s), "
                  f"{n_err} error(s)")
        else:
            print(f"{path.name}: UNAVAILABLE - {result.get('reason')}")

    payload = {
        "provenance": CACHE,
        "n_reports": len(results),
        "total_errors": total_errors,
        "results": results,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
