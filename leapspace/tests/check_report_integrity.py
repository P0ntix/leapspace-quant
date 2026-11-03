"""Final integrity check: the report must agree with the results file.

Three artefacts have to tell the same story:
  reports/backtest_results.json      <- what the engine actually produced
  reports/full_gauntlet_results.json  <- the stricter full-gauntlet verdicts
  reports/leapspace_report.md         <- what the reader sees

A stale background job can rewrite the results file after the report was
rendered, so the report is checked against the file, not assumed fresh.

It ALSO runs the pre-flight validator (leapspace/reportvalidate.py) as a
HARD GATE over every markdown report currently in reports/. If a shipped
report trips the validator, that is a FINDING and is reported here — the
check is NOT weakened to make the reports pass.
"""
import json
import os
import re
import sys

ROOT = r"C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant"
R = os.path.join(ROOT, "reports")

sys.path.insert(0, ROOT)


def load(name):
    with open(os.path.join(R, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


results = load("backtest_results.json")
full = {r["name"]: r for r in (load("full_gauntlet_results.json")
                                .get("results") or [])}
md = open(os.path.join(R, "leapspace_report.md"), "r", encoding="utf-8").read()

print(f"results rows        : {len(results)}")
print(f"full-gauntlet rows  : {len(full)}")

# 1. Every result carries the intake gate.
missing_gate = [r["name"] for r in results
                if not (r.get("intake_gate") or {}).get("available")]
print(f"rows missing the gate: {missing_gate or 'none'}")

# 2. Every result appears in the report with the right verdict.
print("\n=== report vs results ===")
bad = []
for r in results:
    name = r["name"]
    expected = full.get(name, {}).get("verdict", r["verdict"])
    m = re.search(r"^\| `?" + re.escape(name) + r"`? \|(.*)$", md, re.M)
    if not m:
        bad.append((name, "NOT IN REPORT"))
        continue
    row = m.group(1)
    if f"**{expected}**" not in row:
        bad.append((name, f"verdict mismatch: report row has {row.strip()[:90]}"))
    else:
        print(f"  OK  {name:<52} {expected}")
for n, why in bad:
    print(f"  BAD {n:<52} {why}")

# 3. The intake-gate table must list all 13.
gate_section = md.split("### Intake gate")[-1].split("###")[0] if "### Intake gate" in md else ""
missing_tbl = [r["name"] for r in results if r["name"] not in gate_section]
print(f"\nrows missing from the gate table: {missing_tbl or 'none'}")

# 4. The source-reliability section must be present and must claim no
#    spec depends on a defective section.
sr = "## 4. Source reliability of the papers themselves" in md
print(f"source-reliability section present: {sr}")
if sr:
    sec = md.split("## 4. Source reliability")[1].split("## 5.")[0]
    print(f"  states the cross-check passed: "
          f"{'no spec depends on a defective' in sec.lower() or 'None' in sec}")

# 5. Report freshness vs the results file.
mtime_md = os.path.getmtime(os.path.join(R, "leapspace_report.md"))
mtime_js = os.path.getmtime(os.path.join(R, "backtest_results.json"))
print(f"\nreport newer than results file: {mtime_md >= mtime_js} "
      f"(delta {mtime_md - mtime_js:+.0f}s)")

# 6. Pre-flight validator as a HARD GATE over every shipped report.
#    Errors block. Warnings are reported but do not block.
print("\n=== pre-flight validator (hard gate over reports/*.md) ===")
validator_errors = []
validator_unavailable = []
try:
    from leapspace.reportvalidate import validate_report

    md_files = sorted(
        f for f in os.listdir(R)
        if f.endswith(".md") and os.path.isfile(os.path.join(R, f))
    )
    print(f"reports scanned: {len(md_files)}")
    for fname in md_files:
        path = os.path.join(R, fname)
        text = open(path, "r", encoding="utf-8", errors="replace").read()
        payload = None
        json_path = os.path.join(R, fname[:-3] + ".json")
        if os.path.isfile(json_path):
            try:
                payload = load(fname[:-3] + ".json")
            except Exception:
                payload = None
        result = validate_report(text, payload, filepath=path)
        n_err = len(result["errors"])
        n_warn = len(result["warnings"])
        status = "OK " if n_err == 0 else "ERR"
        print(f"  [{status}] {fname:<44} errors={n_err} warnings={n_warn}")
        if result.get("vendor_status") != "ok":
            validator_unavailable.append(fname)
        for e in result["errors"]:
            validator_errors.append((fname, e))
            print(f"        ERROR {e['category']}: {e['message'][:150]}")
except ImportError as exc:
    print(f"  validator not importable: {exc}")
    validator_unavailable.append("(validator missing)")

print(f"\nvalidator errors across shipped reports: {len(validator_errors)}")
print(f"reports where the validator could not run: "
      f"{validator_unavailable or 'none'}")

ok = (not missing_gate and not bad and not missing_tbl and sr
      and mtime_md >= mtime_js
      and not validator_errors and not validator_unavailable)
print(f"\nINTEGRITY: {'OK' if ok else 'PROBLEMS FOUND'}")
sys.exit(0 if ok else 1)
