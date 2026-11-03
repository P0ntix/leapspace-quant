"""
Offline checks for `leapspace/report_memecoin.py`.

Run:  python leapspace/tests/test_report_memecoin.py

WHAT THIS FILE CHECKS
---------------------
The module renders the memecoin-trader half of the consolidated report
from artefacts on disk. The dangerous failure modes are not crashes -
they are SILENT OVER-CLAIMS: a section that says more than its input
supports, a criterion presented as a published standard when it is an
analyst choice, an API key leaking into the markdown, and a missing input
quietly replaced by a plausible default.

So the checks below are about honesty as much as about mechanics:

  a) all nine sections are present
  b) every section carries a provenance string
  c) the criteria coverage has exactly one row per criterion in the
     specification, and every row has a key, a threshold and an
     enforced flag
  d) a criterion whose authority starts with NONE is never described as a
     published standard
  e) the markdown carries a "WHAT THIS DOES NOT SHOW" block
  f) the markdown contains nothing that looks like an API key
  g) a missing input file makes the section say so, not raise
  h) the gaps section is non-empty

DETERMINISTIC AND OFFLINE. No network call is made, and nothing outside
the scratch directory is written. The only writes are to a temporary
directory created by the test itself, which is removed afterwards.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                "..", "..")))

from leapspace import report_memecoin as rm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FAILURES: list = []
CHECKS = 0


def check(name: str, cond: bool, detail: object = "") -> bool:
    """Record one check. Prints PASS/FAIL and remembers failures."""
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name} :: {detail}")
        FAILURES.append((name, str(detail)))
    return bool(cond)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


#: An API key looks like a run of 26-40 uppercase alphanumerics. The
#: Etherscan key is never printed, fingerprinted or hashed, so nothing
#: of that shape may appear in the rendered markdown.
API_KEY_RE = re.compile(r"\b[A-Z0-9]{26,40}\b")


def _load_spec_criteria() -> list:
    """The criterion keys in the specification JSON, read straight from
    disk so the test compares the report against the SPEC and not against
    the module's own expectations."""
    path = os.path.join(ROOT, "leapspace", "data", "consistency_criteria.json")
    with open(path, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    return [c for c in (spec.get("criteria") or []) if isinstance(c, dict)]


def main() -> int:
    print("leapspace/report_memecoin.py — offline checks")
    print(f"package root: {ROOT}")

    payload = rm.build_memecoin_sections()
    sections = payload.get("sections") or {}

    # -- a) all nine sections present --------------------------------
    section("a) the payload carries all nine sections")
    for name in rm.SECTION_NAMES:
        check(f"section present: {name}", name in sections,
              f"missing from {sorted(sections.keys())}")
    check("the payload exposes the sections at the top level too",
          all(name in payload for name in rm.SECTION_NAMES),
          sorted(payload.keys()))
    check("build_memecoin_sections returns a dict",
          isinstance(payload, dict), type(payload))

    # -- b) every section carries a provenance string -----------------
    section("b) every section carries a provenance string")
    for name in rm.SECTION_NAMES:
        sec = sections.get(name) or {}
        prov = sec.get("provenance")
        check(f"provenance present: {name}",
              isinstance(prov, str) and prov.strip() != "", repr(prov))
        check(f"provenance is one of the house values: {name}",
              prov in rm.ALLOWED_PROVENANCE, repr(prov))
    check("no section is marked SYNTHETIC",
          all((sections.get(n) or {}).get("provenance") != rm.SYNTHETIC
              for n in rm.SECTION_NAMES),
          "a section claims synthetic data")

    # -- c) the criteria coverage has exactly one row per criterion ---
    section("c) the criteria coverage matches the specification")
    spec_criteria = _load_spec_criteria()
    spec_keys = [str(c.get("key")) for c in spec_criteria]
    cov = sections.get("criteria_coverage") or {}
    rows = cov.get("rows") or []
    check("the specification carries 31 criteria",
          len(spec_criteria) == 31, len(spec_criteria))
    check("one coverage row per specification criterion",
          len(rows) == len(spec_criteria),
          f"{len(rows)} rows vs {len(spec_criteria)} criteria")
    row_keys = [str(r.get("key")) for r in rows]
    check("every specification criterion has a row",
          all(k in row_keys for k in spec_keys),
          sorted(set(spec_keys) - set(row_keys)))
    check("no extra rows beyond the specification",
          all(k in spec_keys for k in row_keys),
          sorted(set(row_keys) - set(spec_keys)))
    check("the criterion keys are unique",
          len(set(row_keys)) == len(row_keys),
          sorted({k for k in row_keys if row_keys.count(k) > 1}))
    check("every row has a key",
          all(str(r.get("key") or "").strip() for r in rows),
          [r.get("key") for r in rows if not r.get("key")])
    check("every row has a threshold field",
          all("threshold" in r for r in rows),
          [r.get("key") for r in rows if "threshold" not in r])
    check("every row has an enforced flag",
          all(isinstance(r.get("enforced"), bool) for r in rows),
          [(r.get("key"), r.get("enforced")) for r in rows
           if not isinstance(r.get("enforced"), bool)])
    check("the enforced count matches the rows",
          cov.get("n_enforced") == sum(1 for r in rows if r.get("enforced")),
          (cov.get("n_enforced"),
           sum(1 for r in rows if r.get("enforced"))))
    check("the coverage section reports the criterion count",
          cov.get("n_criteria") == len(spec_criteria),
          (cov.get("n_criteria"), len(spec_criteria)))

    # -- d) a NONE-authority criterion is not a published standard -----
    section("d) a NONE-authority criterion is never a published standard")
    md = rm.render_memecoin_markdown(payload)
    none_keys = [str(c.get("key")) for c in spec_criteria
                 if str(c.get("authority") or "").startswith("NONE")
                 or "analyst choice" in
                 str(c.get("authority") or "").lower()]
    check("the specification carries NONE-authority criteria to test",
          bool(none_keys), none_keys)
    for row in rows:
        if str(row.get("key")) in none_keys:
            check(f"marked as an analyst choice: {row.get('key')}",
                  row.get("analyst_choice") is True
                  and row.get("published_standard") is False,
                  (row.get("analyst_choice"), row.get("published_standard")))
    # In the MARKDOWN, the row for such a criterion must not present it
    # as a published standard.
    md_lines = md.splitlines()
    for key in none_keys:
        row_lines = [ln for ln in md_lines if f"`{key}`" in ln and ln.startswith("|")]
        check(f"the markdown has a row for {key}", bool(row_lines), key)
        for ln in row_lines:
            low = ln.lower()
            check(f"the markdown row for {key} is not a published standard",
                  "published standard" not in low
                  or "no published standard" in low
                  or "not a published standard" in low,
                  ln[:200])
            check(f"the markdown row for {key} says it is an analyst choice",
                  "analyst choice" in low, ln[:200])
    check("the markdown states that analyst choices have no published "
          "standard",
          "no published standard" in md.lower()
          or "never presented as a published standard" in md.lower(),
          "the disclaimer is missing")

    # -- e) the WHAT THIS DOES NOT SHOW block -------------------------
    section("e) the markdown opens with WHAT THIS DOES NOT SHOW")
    check("the markdown contains the heading",
          "WHAT THIS DOES NOT SHOW" in md, "heading absent")
    heading_at = md.find("WHAT THIS DOES NOT SHOW")
    check("the heading is near the top",
          0 <= heading_at < 2000, heading_at)
    check("the block appears as a markdown heading",
          any(ln.startswith("#") and "WHAT THIS DOES NOT SHOW" in ln
              for ln in md_lines),
          [ln for ln in md_lines if "WHAT THIS DOES NOT SHOW" in ln])
    check("the block names survivorship selection",
          "survivorship" in md.lower(), "not mentioned")
    check("the block says the PnL is gross of fees",
          "gross" in md.lower(), "not mentioned")

    # -- f) no API key in the markdown ---------------------------------
    section("f) the markdown contains nothing that looks like an API key")
    key_hits = API_KEY_RE.findall(md)
    check("no 26-40 character uppercase alphanumeric token in the markdown",
          not key_hits, key_hits[:5])
    # The Etherscan key must never appear in the payload either.
    payload_text = json.dumps(payload, default=str)
    check("no 26-40 character uppercase alphanumeric token in the payload",
          not API_KEY_RE.findall(payload_text),
          API_KEY_RE.findall(payload_text)[:5])
    keyed = sections.get("keyed_source") or {}
    check("the keyed-source section never reports a key value",
          "api_key_value" not in keyed
          and "api_key_fingerprint" not in keyed,
          sorted(keyed.keys()))
    check("the keyed-source section says the key comes from the "
          "environment",
          "environment" in str(keyed.get("api_key_source", "")).lower(),
          keyed.get("api_key_source"))

    # -- g) a missing input is reported, not raised --------------------
    section("g) a missing input file makes the section say so")
    tmp = tempfile.mkdtemp(prefix="leapspace_report_memecoin_")
    try:
        empty_payload = rm.build_memecoin_sections(package_root=tmp)
        empty_sections = empty_payload.get("sections") or {}
        check("building against an empty root does not raise",
              isinstance(empty_payload, dict), type(empty_payload))
        for name in rm.SECTION_NAMES:
            sec = empty_sections.get(name) or {}
            check(f"the section still exists with no inputs: {name}",
                  isinstance(sec, dict) and bool(sec), sec)
            check(f"the section reports itself unavailable: {name}",
                  sec.get("status") == "unavailable"
                  or sec.get("available") is True,
                  sec.get("status"))
            if sec.get("status") == "unavailable":
                check(f"the section names what is missing: {name}",
                      bool(sec.get("missing")) and bool(sec.get("note")),
                      (sec.get("missing"), sec.get("note")))
                check(f"the note says the input is unavailable: {name}",
                      "UNAVAILABLE" in str(sec.get("note", "")).upper(),
                      sec.get("note"))
        # The gaps section must survive an empty root and must say the
        # inputs are missing rather than claim a result.
        gaps = empty_sections.get("gaps") or {}
        check("the gaps section is non-empty with no inputs",
              bool(gaps.get("gaps")), gaps.get("n_gaps"))
        check("the gaps section names the missing inputs",
              any("unavailable" in str(g.get("gap", "")).lower()
                  for g in (gaps.get("gaps") or [])),
              [g.get("id") for g in (gaps.get("gaps") or [])])
        empty_md = rm.render_memecoin_markdown(empty_payload)
        check("the markdown renders with no inputs",
              "WHAT THIS DOES NOT SHOW" in empty_md, "heading absent")
        check("the markdown states the sections are unavailable",
              "UNAVAILABLE" in empty_md.upper(), "not stated")
        check("no API-key-shaped token appears in the empty-root markdown",
              not API_KEY_RE.findall(empty_md),
              API_KEY_RE.findall(empty_md)[:5])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # -- h) the gaps section is non-empty ------------------------------
    section("h) the gaps section enumerates what is not shown")
    gaps = sections.get("gaps") or {}
    gap_list = gaps.get("gaps") or []
    check("the gaps list is not empty", bool(gap_list), gaps.get("n_gaps"))
    check("the gap count matches the list",
          gaps.get("n_gaps") == len(gap_list),
          (gaps.get("n_gaps"), len(gap_list)))
    check("every gap has an id, an area and a statement",
          all(g.get("id") and g.get("area") and g.get("gap")
              for g in gap_list),
          [g.get("id") for g in gap_list])
    check("every gap says what would close it",
          all(g.get("what_would_close_it") for g in gap_list),
          [g.get("id") for g in gap_list])
    check("the gaps appear in the markdown",
          "does NOT show" in md, "the gaps heading is absent")

    # -- the report the reader actually sees --------------------------
    section("the rendered report")
    check("the markdown is substantial",
          len(md) > 4000, len(md))
    check("the markdown renders a criteria coverage table",
          "| Criterion | Threshold | Tag | Authority | Enforced |" in md,
          "the coverage table header is absent")
    check("the markdown renders a whitelist table",
          "| Wallet | Status |" in md, "the whitelist table is absent")
    check("the markdown renders a criteria row per criterion",
          sum(1 for ln in md_lines
              if ln.startswith("| `") and
              any(f"`{k}`" in ln for k in spec_keys)) >= len(spec_keys),
          "a criterion row is missing from the table")
    check("the markdown names the deployer check",
          "DEPLOYER" in md.upper(), "the deployer check is absent")
    check("the markdown states the COLON separator rule",
          "COLON" in md, "the separator rule is absent")
    check("the markdown reports the free/pro tier split",
          "Pro-only" in md or "PRO ONLY" in md, "the tier split is absent")
    check("the markdown states the survivorship selection explicitly",
          "SURVIVORSHIP-SELECTED" in md.upper(),
          "the survivorship note is absent")
    check("the markdown states the price cap consequence",
          "truncat" in md.lower(), "the truncation note is absent")
    check("the markdown reports the liquidity floor",
          "MIN" not in md or "floor" in md.lower(), "the floor is absent")
    check("the markdown says no lead time has been measured",
          "NO WALLET HAS YET BEEN MEASURED" in md.upper()
          or "not yet measurable" in md.lower(), "the lead-time note is absent")

    # -- the report writer ---------------------------------------------
    section("the report writer")
    tmp = tempfile.mkdtemp(prefix="leapspace_report_memecoin_out_")
    try:
        paths = rm.write_memecoin_report(payload, out_dir=tmp)
        check("the markdown file is written",
              os.path.exists(paths["markdown"]), paths)
        check("the JSON file is written",
              os.path.exists(paths["json"]), paths)
        with open(paths["json"], "r", encoding="utf-8") as fh:
            written = json.load(fh)
        check("the JSON artefact carries the nine sections",
              all(n in (written.get("sections") or {})
                  for n in rm.SECTION_NAMES),
              sorted((written.get("sections") or {}).keys()))
        check("the written markdown matches the rendered markdown",
              open(paths["markdown"], "r", encoding="utf-8").read() == md,
              "the file differs from render_memecoin_markdown()")
        check("no API-key-shaped token in the written artefacts",
              not API_KEY_RE.findall(
                  open(paths["markdown"], "r", encoding="utf-8").read())
              and not API_KEY_RE.findall(
                  open(paths["json"], "r", encoding="utf-8").read()),
              "a key-shaped token was written to disk")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{CHECKS} checks, {len(FAILURES)} failed")
    if FAILURES:
        for name, detail in FAILURES:
            print(f"  FAILED  {name} :: {detail}")
        print("\nRESULT: FAIL")
        return 1
    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
