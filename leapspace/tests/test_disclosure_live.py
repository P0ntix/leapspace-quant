"""Live end-to-end check of the three-branch disclosure module."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from leapspace.disclosure import (fetch_house_index, fetch_house_pdf, fetch_oge_index,
                                  fetch_oge_pdf, extract_assets_from_text,
                                  analyse_market_impact, build_disclosure_report,
                                  fetch_judicial_filings)
import datetime as dt

print("== HOUSE index ==")
try:
    filings, prov = fetch_house_index(2026)
    print(" ", prov.disclosure())
    print("  total:", len(filings))
    types = {}
    for f in filings:
        types[f.filing_type] = types.get(f.filing_type, 0) + 1
    print("  by type:", types)
    ptr = [f for f in filings if f.filing_type_code == "P"]
    ann = [f for f in filings if f.filing_type_code == "C"]
    print("  sample PTR:", ptr[0].to_dict() if ptr else None)
    print("  sample annual:", ann[0].to_dict() if ann else None)
except Exception as e:
    print("  ERR", type(e).__name__, e)
    ptr, ann = [], []

print("\n== HOUSE PDF text + asset extraction ==")
if ptr:
    try:
        text, p = fetch_house_pdf(ptr[0])
        print(" ", p.disclosure())
        if text:
            print("  first 400 chars:\n   ", text[:400].replace("\n", " | "))
            assets = extract_assets_from_text(text)
            print("  assets extracted:", len(assets))
            for a in assets[:6]:
                print("   ", json.dumps(a.to_dict()))
        else:
            print("  no text layer")
    except Exception as e:
        print("  ERR", type(e).__name__, e)

print("\n== OGE index (search 'Powell') ==")
try:
    rows, total, prov = fetch_oge_index(search="Powell")
    print(" ", prov.disclosure())
    for r in rows[:4]:
        print("  ", json.dumps(r.to_dict())[:260])
    withpdf = [r for r in rows if r.pdf_url]
    if withpdf:
        txt, p = fetch_oge_pdf(withpdf[0])
        print("  PDF:", p.disclosure())
        if txt:
            print("  first 300:\n   ", txt[:300].replace("\n", " | "))
            assets = extract_assets_from_text(txt)
            print("  assets:", len(assets))
            for a in assets[:5]:
                print("   ", json.dumps(a.to_dict()))
except Exception as e:
    print("  ERR", type(e).__name__, e)

print("\n== JUDICIAL ==")
try:
    jf, gaps = fetch_judicial_filings()
    print("  filings:", len(jf))
    for f in jf[:6]:
        print("   ", f.justice[:40], f.year, f.doc_type[:20], f.provenance, f.url[-40:])
    for g in gaps:
        print("  GAP:", json.dumps(g)[:220])
except Exception as e:
    print("  ERR", type(e).__name__, e)

print("\n== FULL REPORT (House + OGE names + judicial) ==")
try:
    rep = build_disclosure_report(house_year=2026,
                                  oge_names=["Powell", "Mullin"],
                                  include_judicial=True)
    print("  branches:", list(rep["branches"].keys()))
    print("  coverage:", rep["coverage"])
    for k, v in rep["branches"].items():
        print(f"   {k}:", json.dumps({kk: vv for kk, vv in v.items()
                                      if kk not in ('sample', 'law')})[:260])
    print("  sources_unavailable:", len(rep["sources_unavailable"]))
    for g in rep["sources_unavailable"]:
        print("   -", g.get("source"), ":", str(g.get("reason"))[:120])
except Exception as e:
    print("  ERR", type(e).__name__, e)
    import traceback
    traceback.print_exc()
