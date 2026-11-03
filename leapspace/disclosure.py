"""
US officials' legally-required financial disclosures — all three branches —
plus market-impact analysis.

Source: the user's request, and the live-verified source spec at
C:\\Users\\HP\\disclosure_spec\\US_OFFICIAL_DISCLOSURE_SOURCES.md
(verification date 2026-10-27, every URL fetched live with its real status).

THE THREE BRANCHES AND THE LAW THAT REQUIRES EACH:

  LEGISLATIVE — Members of Congress.
    House: annual Financial Disclosure Report + Periodic Transaction Reports
           (PTR), STOCK Act. Primary, machine-parseable.
    Senate: eFD (same regime). HARD GEO-BLOCK from this host — HTTP 403 on
            every *.senate.gov path, while www.house.gov returns 200 from the
            same IP. This is a source-availability gap, NOT "no filings exist".

  EXECUTIVE — Presidentially Appointed Officials and other filers.
    OGE Form 278e (annual) and 278-T (periodic transaction report), filed
    under 5 CFR part 2634 with OGE; the White House republishes its own.
    Primary, machine-parseable.

  JUDICIAL — Supreme Court Justices and federal judges.
    AO Form 10 annual financial disclosure (Judicial Conference / AO
    regime, 5 U.S.C. 13101-13111). Primary is JEFS
    (pub.jefs.uscourts.gov) — registration-gated AND TCP-unreachable from
    this host. Secondary mirrors: fixthecourt.com, scotusblog.com. Every
    judicial record from a mirror is labelled [secondary].

MARKET-IMPACT ANALYSIS: the papers in this project cover NASDAQ/equity
regimes, crypto, and meme coins. A disclosure is only actionable if it names
an asset that trades in one of those markets. This module therefore:
  1. parses the disclosed asset description into a ticker candidate,
  2. checks that ticker against real market data, and
  3. measures what the market did AFTER the disclosure date.

The impact measurement is deliberately conservative and reports the sample
size: a disclosure that names one stock cannot establish a market effect, and
the module says so rather than printing a t-statistic over n=1.
"""

from __future__ import annotations

import datetime as _dt
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .http import HttpError, http_get, http_json
from .provenance import Provenance, SourceUnavailable, unavailable

# --------------------------------------------------------------------------
# House glyph cipher
# --------------------------------------------------------------------------
# The House FD/PTR PDFs embed a subset font with a broken ToUnicode map, so
# all-caps LABELS extract as IPA code points. Only the labels are affected;
# asset names, tickers, amounts and dates are plain ASCII.
HOUSE_GLYPH = {
    "ʇ": "E", "ʔ": "R", "ʋ": "I", "ʑ": "O", "ʆ": "D", "ʅ": "C",
    "ʃ": "A", "ʐ": "N", "ʕ": "S", "ʖ": "T", "ʒ": "P", "ʎ": "L",
    "ʈ": "F", "ʏ": "M", "ʗ": "U", "ʉ": "G", "ʊ": "H", "ʄ": "B",
    "ʘ": "V", "ʛ": "Y", "ʚ": "X", "ʓ": "Q",
}


def decode_house_glyphs(text: str) -> str:
    return "".join(HOUSE_GLYPH.get(c, c) for c in text)


# --------------------------------------------------------------------------
# Branch definitions
# --------------------------------------------------------------------------

BRANCHES = {
    "legislative": {
        "title": "Legislative — Members of Congress",
        "law": ("House: annual Financial Disclosure Report and Periodic "
                "Transaction Reports under the STOCK Act (5 U.S.C. 13101-13111 "
                "and House rules). Senate: the same regime via the Senate "
                "eFD system."),
        "sources": [
            {"name": "House Clerk annual FD index (XML)",
             "url": "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.xml",
             "provenance": "primary"},
            {"name": "House Clerk annual FD PDF",
             "url": "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}/{docid}.pdf",
             "provenance": "primary"},
            {"name": "House Clerk PTR PDF",
             "url": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{docid}.pdf",
             "provenance": "primary"},
            {"name": "Senate eFD",
             "url": "https://efdsearch.senate.gov/",
             "provenance": "primary",
             "status": "HTTP 403 geo-block from this host"},
        ],
    },
    "executive": {
        "title": "Executive — Presidentially Appointed Officials (OGE 278e / 278-T)",
        "law": ("OGE Form 278e (annual public financial disclosure) and Form "
                "278-T (periodic transaction report) under 5 CFR part 2634."),
        "sources": [
            {"name": "OGE PAS index REST API",
             "url": "https://extapps2.oge.gov/201/Presiden.nsf/API.xsp/v3/rest",
             "provenance": "primary"},
            {"name": "OGE document PDF",
             "url": "https://extapps2.oge.gov/201/Presiden.nsf/PAS+Index/<UNID>/$FILE/<name>.pdf",
             "provenance": "primary"},
            {"name": "White House public disclosures index",
             "url": "https://www.whitehouse.gov/disclosures/",
             "provenance": "primary"},
        ],
    },
    "judicial": {
        "title": "Judicial — Supreme Court Justices and federal judges",
        "law": ("AO Form 10 annual financial disclosure, filed in JEFS under "
                "the Judicial Conference regime (5 U.S.C. 13101-13111)."),
        "sources": [
            {"name": "JEFS — Federal Judicial Financial Disclosure Reports",
             "url": "https://pub.jefs.uscourts.gov/",
             "provenance": "primary",
             "status": "TCP connect timeout from this host; registration-gated"},
            {"name": "Judicial Conference landing page",
             "url": "https://www.uscourts.gov/administration-policies/judiciary-financial-disclosure-reports",
             "provenance": "primary"},
            {"name": "Fix the Court disclosure mirror",
             "url": "https://fixthecourt.com/2025disclosures/",
             "provenance": "secondary"},
            {"name": "SCOTUSblog disclosure index",
             "url": "https://www.scotusblog.com/financial-disclosures/",
             "provenance": "secondary"},
        ],
    },
}


# --------------------------------------------------------------------------
# House
# --------------------------------------------------------------------------

HOUSE_FD_INDEX = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.xml"
HOUSE_FD_PDF = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}/{docid}.pdf"
HOUSE_PTR_PDF = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{docid}.pdf"

# FilingType codes resolved by reading the "Filing Type:" line of a sample PDF
# per code (all eight verified live).
HOUSE_FILING_TYPES = {
    "C": "Candidate Report",
    "P": "Periodic Transaction Report",
    "X": "Financial Disclosure Extension Request",
    "W": "Campaign Notice Regarding Financial Disclosure Requirement",
    "D": "Campaign Notice Regarding Financial Disclosure Requirement",
    "A": "Amendment Report",
    "H": "New Filer Report",
    "T": "Terminated Filer Report",
}


@dataclass
class HouseFiling:
    name: str
    prefix: str
    first: str
    last: str
    suffix: str
    filing_type_code: str
    filing_type: str
    state_district: str
    year: int
    filing_date: Optional[_dt.date]
    doc_id: str
    branch: str = "legislative"

    @property
    def is_member(self) -> bool:
        return self.prefix.strip() == "Hon."

    @property
    def is_candidate(self) -> bool:
        return self.prefix.strip() == "Mr."

    def pdf_url(self) -> str:
        # 2xxxxxxx DocIDs live under ptr-pdfs/, everything else under
        # financial-pdfs/. Verified: 20034201 -> 404 on financial-pdfs, 200 on
        # ptr-pdfs.
        sub = "ptr-pdfs" if self.doc_id.startswith("2") else "financial-pdfs"
        return (f"https://disclosures-clerk.house.gov/public_disc/{sub}/"
                f"{self.year}/{self.doc_id}.pdf")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch": self.branch,
            "name": self.name,
            "is_member": self.is_member,
            "is_candidate": self.is_candidate,
            "filing_type": self.filing_type,
            "filing_type_code": self.filing_type_code,
            "state_district": self.state_district,
            "year": self.year,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "doc_id": self.doc_id,
            "pdf_url": self.pdf_url(),
            "provenance": "primary — House Clerk",
        }


def _parse_house_date(text: str) -> Optional[_dt.date]:
    """House FilingDate is M/D/YYYY — not ISO."""
    if not text:
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return _dt.datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    return None


def fetch_house_index(year: int = 2026) -> Tuple[List[HouseFiling], Provenance]:
    url = HOUSE_FD_INDEX.format(year=year)
    status, body, _ = http_get(url, timeout=60)
    prov = Provenance(source="house.fd-index", url=url, note=f"HTTP {status}")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise SourceUnavailable(f"house FD index is not valid XML: {exc}") from exc
    out: List[HouseFiling] = []
    for m in root.findall("Member"):
        def g(tag: str) -> str:
            el = m.find(tag)
            return (el.text or "").strip() if el is not None else ""
        prefix, first, last, suffix = g("Prefix"), g("First"), g("Last"), g("Suffix")
        code = g("FilingType")
        name = " ".join(x for x in (prefix, first, last, suffix) if x).strip()
        out.append(HouseFiling(
            name=name, prefix=prefix, first=first, last=last, suffix=suffix,
            filing_type_code=code,
            filing_type=HOUSE_FILING_TYPES.get(code, f"Unknown ({code})"),
            state_district=g("StateDst"),
            year=int(g("Year") or year),
            filing_date=_parse_house_date(g("FilingDate")),
            doc_id=g("DocID"),
        ))
    if not out:
        raise SourceUnavailable(f"house FD index for {year} contained no members")
    prov.note = f"HTTP {status}; {len(out)} member records"
    return out, prov


def extract_pdf_text(pdf_bytes: bytes) -> Optional[str]:
    """Extract a PDF's text layer with PyMuPDF. None when unavailable.

    Returns None rather than an empty string distinction being lost: callers
    must treat None as "no text layer" (scanned image -> OCR required).
    """
    try:
        import pymupdf  # type: ignore
    except Exception:
        try:
            import fitz as pymupdf  # type: ignore
        except Exception:
            return None
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return None
    try:
        pages = []
        for page in doc:
            pages.append(page.get_text())
        text = "\n".join(pages)
        return text if text.strip() else None
    finally:
        try:
            doc.close()
        except Exception:
            pass


def fetch_house_pdf(filing: HouseFiling) -> Tuple[Optional[str], Provenance]:
    url = filing.pdf_url()
    try:
        status, body, _ = http_get(url, timeout=60)
    except HttpError:
        # Fall back to the other directory — a DocID prefix rule miss should
        # not silently drop a filing.
        alt = (HOUSE_PTR_PDF if "financial-pdfs" in url else HOUSE_FD_PDF)
        alt_url = alt.format(year=filing.year, docid=filing.doc_id)
        status, body, _ = http_get(alt_url, timeout=60)
        url = alt_url
    prov = Provenance(source="house.pdf", url=url, note=f"HTTP {status}")
    text = extract_pdf_text(body)
    if text:
        text = decode_house_glyphs(text)
    prov.note += f"; text_layer={'present' if text else 'EMPTY (OCR required)'}"
    return text, prov


# --------------------------------------------------------------------------
# OGE (executive branch)
# --------------------------------------------------------------------------

OGE_INDEX = "https://extapps2.oge.gov/201/Presiden.nsf/API.xsp/v3/rest"
OGE_PAGE_SIZE = 100  # VERIFIED: length is SILENTLY CAPPED at 100.


@dataclass
class OgeFiling:
    name: str
    agency: str
    title: str
    level: str
    doc_date: Optional[_dt.datetime]
    amended: Optional[_dt.datetime]
    doc_label: str
    pdf_url: Optional[str]
    request_only: bool
    branch: str = "executive"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch": self.branch,
            "name": self.name,
            "agency": self.agency,
            "title": self.title,
            "level": self.level,
            "doc_date": self.doc_date.isoformat() if self.doc_date else None,
            "amended": self.amended.isoformat() if self.amended else None,
            "doc_label": self.doc_label,
            "pdf_url": self.pdf_url,
            "request_only": self.request_only,
            "provenance": "primary — OGE",
        }


def _parse_oge_dt(text: str) -> Optional[_dt.datetime]:
    if not text:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return _dt.datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return None


def fetch_oge_index(search: Optional[str] = None, start: int = 0,
                     length: int = OGE_PAGE_SIZE
                     ) -> Tuple[List[OgeFiling], int, Provenance]:
    """Fetch one page of the OGE PAS index.

    `length` is silently capped at 100 by the server — this function refuses
    to request more than one page's worth and the caller must page in steps
    of 100 and assert len(rows) == recordsFiltered.
    """
    length = min(length, OGE_PAGE_SIZE)
    url = (f"{OGE_INDEX}?length={length}&start={start}"
           + (f"&search[value]={search}&search[regex]=false" if search else ""))
    payload, status = http_json(url, timeout=60)
    rows = payload.get("data") or []
    total = payload.get("recordsFiltered") or payload.get("recordsTotal") or 0
    out: List[OgeFiling] = []
    for r in rows:
        typ = r.get("type") or ""
        m = re.search(r"href='([^']+\.pdf)'", typ)
        pdf_url = m.group(1) if m else None
        label = re.sub(r"<[^>]+>", "", typ).strip()
        # "Request this Document" rows have NO publicly fetchable PDF.
        request_only = ("Request this Document" in typ) or (pdf_url is None
                        and "PAS+Index" not in typ)
        out.append(OgeFiling(
            name=r.get("name") or "",
            agency=r.get("agency") or "",
            title=r.get("title") or "",
            level=r.get("level") or "",
            doc_date=_parse_oge_dt(r.get("docDate") or ""),
            amended=_parse_oge_dt(r.get("amended") or ""),
            doc_label=label,
            pdf_url=pdf_url,
            request_only=request_only,
        ))
    prov = Provenance(source="oge.pas-index", url=url,
                      note=f"HTTP {status}; {len(out)} rows of {total}")
    return out, total, prov


def fetch_oge_all(search: Optional[str] = None, max_pages: int = 200
                  ) -> Tuple[List[OgeFiling], List[str], Provenance]:
    """Page the whole OGE index for a name. Returns (filings, gaps, provenance)."""
    rows: List[OgeFiling] = []
    gaps: List[str] = []
    start = 0
    total = None
    last_prov = None
    for _ in range(max_pages):
        page, tot, prov = fetch_oge_index(search=search, start=start)
        last_prov = prov
        total = tot
        rows.extend(page)
        if len(page) < OGE_PAGE_SIZE:
            break
        start += OGE_PAGE_SIZE
        if total and len(rows) >= total:
            break
    if total is not None and len(rows) != total:
        gaps.append(f"OGE pagination incomplete: fetched {len(rows)} of {total} rows")
    if last_prov is None:
        raise SourceUnavailable("OGE index returned no pages")
    return rows, gaps, last_prov


def fetch_oge_pdf(filing: OgeFiling) -> Tuple[Optional[str], Provenance]:
    if not filing.pdf_url:
        raise SourceUnavailable(
            f"no public PDF for '{filing.name}' {filing.doc_label} — OGE serves a "
            f"'Request this Document' form instead")
    status, body, _ = http_get(filing.pdf_url, timeout=60)
    prov = Provenance(source="oge.pdf", url=filing.pdf_url, note=f"HTTP {status}")
    text = extract_pdf_text(body)
    prov.note += f"; text_layer={'present' if text else 'EMPTY'}"
    return text, prov


# --------------------------------------------------------------------------
# Judicial branch (JEFS + secondary mirrors)
# --------------------------------------------------------------------------

JEFS_ROOT = "https://pub.jefs.uscourts.gov/"
FIXTHECOURT_INDEX = "https://fixthecourt.com/2025disclosures/"
SCOTUSBLOG_INDEX = "https://www.scotusblog.com/financial-disclosures/"


@dataclass
class JudicialFiling:
    justice: str
    year: Optional[int]
    doc_type: str
    url: str
    provenance: str  # "primary" | "secondary"
    text: Optional[str] = None
    text_note: str = ""
    branch: str = "judicial"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch": self.branch,
            "justice": self.justice,
            "year": self.year,
            "doc_type": self.doc_type,
            "url": self.url,
            "provenance": self.provenance,
            "text_extracted": bool(self.text),
            "text_note": self.text_note,
        }


def fetch_judicial_filings(include_mirrors: bool = True
                            ) -> Tuple[List[JudicialFiling], List[Dict[str, Any]]]:
    """Collect judicial-branch filings.

    The primary (JEFS) is attempted first and, from this host, is a TCP
    timeout. The failure is RECORDED as an unavailability — never as "there
    are no judicial disclosures".
    """
    filings: List[JudicialFiling] = []
    gaps: List[Dict[str, Any]] = []

    # --- primary: JEFS ---
    try:
        status, body, _ = http_get(JEFS_ROOT, timeout=25, retries=1)
        text = body.decode("utf-8", "replace")
        for m in re.finditer(r'href=["\']([^"\']+\.pdf)["\'][^>]*>([^<]{2,80})',
                             text, re.I):
            filings.append(JudicialFiling(
                justice=m.group(2).strip(), year=None, doc_type="Annual",
                url=m.group(1), provenance="primary"))
        gaps.append({"source": "JEFS", "status": f"HTTP {status}",
                     "note": "reachable; PDFs listed from the index page"})
    except HttpError as exc:
        gaps.append(unavailable("jefs_database", JEFS_ROOT, str(exc)))

    if not include_mirrors:
        return filings, gaps

    # --- secondary mirror 1: Fix the Court ---
    try:
        status, body, _ = http_get(FIXTHECOURT_INDEX, timeout=45)
        text = body.decode("utf-8", "replace")
        n = 0
        for m in re.finditer(r'href=["\']([^"\']+\.pdf)["\'][^>]*>([^<]{2,90})',
                             text, re.I):
            label = m.group(2).strip()
            name = label.split("-Annual")[0].split("-Periodic")[0].strip()
            yr = None
            ym = re.search(r"(20\d{2})", label)
            if ym:
                yr = int(ym.group(1))
            dtype = "Periodic Transaction Report" if "Periodic" in label else "Annual"
            filings.append(JudicialFiling(
                justice=name, year=yr, doc_type=dtype, url=m.group(1),
                provenance="secondary"))
            n += 1
        gaps.append({"source": "fixthecourt.com", "status": f"HTTP {status}",
                     "note": f"secondary mirror, {n} PDFs indexed"})
    except HttpError as exc:
        gaps.append(unavailable("fixthecourt_mirror", FIXTHECOURT_INDEX, str(exc)))

    # --- secondary mirror 2: SCOTUSblog ---
    try:
        status, body, _ = http_get(SCOTUSBLOG_INDEX, timeout=45)
        text = body.decode("utf-8", "replace")
        # The anchors are grouped under a heading per justice; take the last
        # heading before each PDF anchor.
        positions = [(m.start(), m.group(0).strip())
                     for m in re.finditer(r"(?:Chief Justice|Justice)[^<\n]{0,60}",
                                          text)]
        n = 0
        for m in re.finditer(r'href=["\'](https://cdn\.sanity\.io/[^"\']+\.pdf)["\']'
                             r'[^>]*>([^<]{2,60})', text, re.I):
            before = text[:m.start()]
            justice = ""
            for pos, name in positions:
                if pos < m.start():
                    justice = name
            yr = None
            ym = re.search(r"(20\d{2})", m.group(2))
            if ym:
                yr = int(ym.group(1))
            filings.append(JudicialFiling(
                justice=justice or "unknown", year=yr, doc_type="Annual",
                url=m.group(1), provenance="secondary"))
            n += 1
        gaps.append({"source": "scotusblog.com", "status": f"HTTP {status}",
                     "note": f"secondary mirror, {n} PDFs indexed"})
    except HttpError as exc:
        gaps.append(unavailable("scotusblog_mirror", SCOTUSBLOG_INDEX, str(exc)))

    return filings, gaps


def fetch_judicial_text(filing: JudicialFiling) -> Tuple[Optional[str], str]:
    """Fetch a judicial PDF's text. Returns (text, note).

    NOTE: some SCOTUS periodic-transaction PDFs are image-only with an EMPTY
    text layer (verified: 4 characters across a 5-page, 628 KB PDF). Those
    need OCR; this function reports that explicitly rather than returning "".
    """
    try:
        status, body, _ = http_get(filing.url, timeout=90)
    except HttpError as exc:
        return None, f"fetch failed: {exc}"
    text = extract_pdf_text(body)
    if text is None:
        return None, (f"HTTP {status}; EMPTY TEXT LAYER — image-only PDF, "
                      f"OCR required to read")
    return text, f"HTTP {status}; {len(text)} chars extracted"


# --------------------------------------------------------------------------
# Asset extraction — turning a disclosure into a tradeable ticker
# --------------------------------------------------------------------------

# Observed House asset types: [ST] stock, [OP] option, [AB] partnership/other,
# [RP] real property, [OL] other, [MF] mutual fund, [PE] pension,
# [BA] bank account, [IH] insurance/annuity, [DC] defined contribution.
ASSET_TYPE_CODES = {
    "ST": "stock", "OP": "option", "AB": "partnership/other",
    "RP": "real property", "OL": "other", "MF": "mutual fund",
    "PE": "pension", "BA": "bank account", "IH": "insurance/annuity",
    "DC": "defined contribution",
}

# Securities that must NEVER be treated as a tradeable signal: the STOCK
# Act carve-outs and the OGE noise-filter exemptions.
EXEMPT_SECURITIES = ("mutual fund", "money market", "government bond",
                     "broad index etf in blind trust", "blind trust",
                     "pension", "401(k)", "ira", "thrift savings")


@dataclass
class DisclosedAsset:
    description: str
    ticker: Optional[str]
    asset_type: Optional[str]
    value_band: Optional[str]
    value_low: Optional[float]
    value_high: Optional[float]
    income_type: Optional[str]
    owner_code: Optional[str]
    is_exempt: bool
    raw_line: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "ticker": self.ticker,
            "asset_type": self.asset_type,
            "value_band": self.value_band,
            "value_low": self.value_low,
            "value_high": self.value_high,
            "income_type": self.income_type,
            "owner_code": self.owner_code,
            "is_exempt": self.is_exempt,
        }


def _parse_band(text: str) -> Tuple[Optional[float], Optional[float]]:
    """Parse a VALUE BAND into (low, high).

    Only a string that is ENTIRELY a band is accepted:
      '$1,000,001 - $5,000,000'  -> (1000001, 5000000)
      'Over $5,000,000'           -> (5000001, None)
      '$500,001 -'                -> (500001, None)   [split across PDF lines]
    A line like 'QQQ - 4.105 shares sold @ $601.68/share' is NOT a band and
    must not be parsed as one, or a share price would be read as an asset
    value.
    """
    if not text:
        return None, None
    s = text.strip()
    m = re.fullmatch(r"Over\s*\$([0-9][0-9,]*)", s, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", "")) + 1.0, None
    m = re.fullmatch(r"\$([0-9][0-9,]*)\s*-\s*(?:\$([0-9][0-9,]*))?", s)
    if m:
        lo = float(m.group(1).replace(",", ""))
        hi = float(m.group(2).replace(",", "")) if m.group(2) else None
        return lo, hi
    return None, None


_TICKER_RE = re.compile(r"\(([A-Z][A-Z0-9.\-]{0,5})\)\s*$")
# A ticker that appears before a type code: '(AMZN) [ST]'.
_TICKER_INLINE_RE = re.compile(r"^\(([A-Z][A-Z0-9.\-]{0,5})\)\s*(?=\[|$)")
# A ticker alone on its line: '(AMZN)'.
_TICKER_ONLY_RE = re.compile(r"^\(([A-Z][A-Z0-9.\-]{0,5})\)\s*$")
# Words that look like tickers in parentheses but are not securities.
_NOT_TICKERS = {"US", "USA", "USD", "LLC", "LP", "LTD", "INC", "PC", "II",
                "III", "IV", "PLC", "CORP", "CO", "NA", "DC", "JT", "SP", "TR",
                "ETF", "IRA", "IRS", "FE", "NE", "MA", "CA", "NY"}


def _is_band_line(text: str) -> bool:
    s = text.strip()
    if not s or "$" not in s:
        return False
    if re.fullmatch(r"Over\s*\$[0-9,]+", s, re.IGNORECASE):
        return True
    if re.fullmatch(r"\$[0-9,]*\s*-\s*\$?[0-9,]*", s):
        return True
    return False


def classify_oge_document(text: str) -> str:
    """Classify an OGE PDF's text into a document kind.

    Only the 278e (annual public financial disclosure) and 278-T (periodic
    transaction report) forms carry an asset/transaction table. An Ethics
    Agreement, Ethics Agreement Compliance, Conflict of Interest Waiver,
    Certificate of Divestiture or Nomination Questionnaire does not, and
    scanning one for tickers produces false positives.
    """
    if not text:
        return "none"
    head = text[:4000]
    if "Periodic Transaction Report" in head or "OGE Form 278-T" in head:
        return "oge_278t"
    if "Public Financial Disclosure Report" in head or "OGE Form 278e" in head:
        return "oge_278e"
    for marker in ("Ethics Agreement", "Conflict of Interest Waiver",
                   "Certificate of Divestiture", "Nomination",
                   "Ethics Agreement Compliance", "Public Financial Disclosure Report"):
        if marker in head:
            return "oge_other"
    return "oge_other"


def classify_house_document(text: str) -> str:
    """Classify a House PDF into house_fd / house_ptr / house_other."""
    if not text:
        return "none"
    head = text[:3000]
    if "PERIODIC TRANSACTION REPORT" in head:
        return "house_ptr"
    if "FINANCIAL DISCLOSURE REPORT" in head or "FINANCIAL DISCLOSURE" in head:
        return "house_fd"
    return "house_other"


def extract_assets_from_text(text: str, doc_kind: str = "auto"
                             ) -> List[DisclosedAsset]:
    """Pull disclosed assets out of an extracted filing text.

    `doc_kind` gates which document shapes are asset-bearing:
      "auto"      — accept house_fd / house_ptr / oge_278e / oge_278t
      "oge_278e"  — annual public financial disclosure (asset table)
      "oge_278t"  — periodic transaction report (transaction table)
      "house_fd"  — House annual financial disclosure (asset table)
      "house_ptr" — House periodic transaction report (transaction table)
      "none"      — return nothing

    A document that is NOT an asset-bearing form (an OGE Ethics Agreement, a
    nomination questionnaire, a House campaign notice) contains no asset
    table, and scanning it produces false tickers out of abbreviations like
    "(USAO)". Gate on the form, then scan.

    Layout handling, learned from the real PDFs:
      * House PTR rows put the DESCRIPTION on one line and the
        `(TICKER) [TYPE]` on the next:
            Amazon.com, Inc. - Common Stock
            (AMZN) [ST]
      * House annual FD rows put them on one line:
            Alphabet Inc. - Class A (GOOGL) [ST]
      * OGE 278e rows put DESCRIPTION on one line and EIF/VALUE/INCOME on
        following lines.

    A line is only treated as an asset when it carries a recognised type code
    or a parenthesised ticker. Free text is never guessed into a ticker.
    """
    out: List[DisclosedAsset] = []
    if not text:
        return out
    if doc_kind == "none":
        return out
    if doc_kind == "auto":
        head = text[:6000]
        # House documents carry their own masthead; check for it FIRST,
        # because the House PTR title ("PERIODIC TRANSACTION REPORT") is the
        # same phrase the OGE 278-T uses.
        if "Clerk of the House of Representatives" in head:
            doc_kind = classify_house_document(text)
        elif ("OGE Form 278" in head or "U.S. Office of Government Ethics" in head
              or "5 C.F.R. part 2634" in head):
            doc_kind = classify_oge_document(text)
        else:
            doc_kind = classify_house_document(text)
    if doc_kind not in ("oge_278e", "oge_278t", "house_fd", "house_ptr"):
        return out
    lines = [ln.strip() for ln in text.splitlines()]
    n = len(lines)
    consumed: set = set()

    for i, line in enumerate(lines):
        if not line or len(line) > 300:
            continue
        code_m = re.search(r"\[([A-Z]{2})\]", line)
        # The ticker may be at the end of the line ('... Stock (AMZN)'), at the
        # start before a type code ('(AMZN) [ST]'), or on its own line
        # ('(AMZN)').
        tick_m = (_TICKER_RE.search(line) or _TICKER_INLINE_RE.search(line)
                  or _TICKER_ONLY_RE.fullmatch(line.strip()))

        ticker = None
        asset_type = None
        desc = line
        if code_m:
            code = code_m.group(1)
            if code in ASSET_TYPE_CODES:
                asset_type = ASSET_TYPE_CODES[code]
                desc = line[:code_m.start()].strip()
            else:
                code_m = None
        if not tick_m and desc:
            # The type code may have been stripped off the end, leaving the
            # ticker at the end of what remains.
            tick_m = _TICKER_RE.search(desc)
        if tick_m:
            cand = tick_m.group(1)
            if cand not in _NOT_TICKERS and not cand.isdigit():
                ticker = cand
                desc = desc[:tick_m.start()].strip()
                desc = re.sub(r"\s*\([A-Z][A-Z0-9.\-]{0,5}\)\s*$", "", desc).strip()

        # A line that is ONLY the ticker (plus its type code): the description
        # is the previous non-empty line.
        if ticker and not desc:
            for j in range(i - 1, max(-1, i - 4), -1):
                cand = lines[j]
                if not cand or j in consumed:
                    continue
                if _TICKER_RE.search(cand) or re.search(r"\[[A-Z]{2}\]", cand):
                    continue
                desc = cand
                consumed.add(j)
                break
        if not ticker and not asset_type:
            continue
        if not desc:
            desc = ticker or "(unnamed)"

        low = desc.lower()
        is_exempt = any(k in low for k in EXEMPT_SECURITIES)

        # The value band is a nearby line that is ENTIRELY a band.
        band = None
        for j in (i + 1, i + 2, i + 3, i - 1):
            if 0 <= j < n and j not in consumed and _is_band_line(lines[j]):
                band = lines[j]
                consumed.add(j)
                break
        lo, hi = _parse_band(band or "")
        # A band split across two PDF lines: '$500,001 -' then '$1,000,000'.
        if band and hi is None and band.rstrip().endswith("-"):
            for j in range(i + 1, min(n, i + 6)):
                if re.fullmatch(r"\$[0-9][0-9,]*", lines[j].strip()):
                    hi = float(lines[j].strip().replace("$", "").replace(",", ""))
                    break
        out.append(DisclosedAsset(
            description=desc, ticker=ticker, asset_type=asset_type,
            value_band=band, value_low=lo, value_high=hi,
            income_type=None, owner_code=None, is_exempt=is_exempt,
            raw_line=line))
    return out


# --------------------------------------------------------------------------
# Market impact analysis
# --------------------------------------------------------------------------

IMPACT_WINDOWS = (1, 5, 20)  # trading days after the disclosure date


@dataclass
class ImpactObservation:
    ticker: str
    disclosure_date: _dt.date
    asset_value_low: Optional[float]
    windows: Dict[str, Optional[float]] = field(default_factory=dict)
    benchmark_windows: Dict[str, Optional[float]] = field(default_factory=dict)
    excess: Dict[str, Optional[float]] = field(default_factory=dict)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "disclosure_date": self.disclosure_date.isoformat(),
            "asset_value_low": self.asset_value_low,
            "returns_by_window": self.windows,
            "benchmark_returns_by_window": self.benchmark_windows,
            "excess_returns_by_window": self.excess,
            "note": self.note,
        }


def analyse_market_impact(disclosure_date: _dt.date, tickers: Sequence[str],
                          bars_by_symbol: Dict[str, List[Dict[str, Any]]],
                          benchmark: str = "SPY",
                          value_by_ticker: Optional[Dict[str, float]] = None
                          ) -> Tuple[List[ImpactObservation], List[str]]:
    """Measure what the market did after a disclosure date.

    Returns (observations, caveats). The caveats are the point: a single
    disclosure on a single stock is an anecdote, not a market effect, and the
    module must say so.
    """
    obs: List[ImpactObservation] = []
    caveats: List[str] = []
    bench = bars_by_symbol.get(benchmark) or []
    bench_by_date = {b["date"]: b for b in bench}

    for ticker in tickers:
        bars = bars_by_symbol.get(ticker) or []
        if not bars:
            caveats.append(f"{ticker}: no market data — impact not measurable")
            continue
        dates = [b["date"] for b in bars]
        try:
            start = dates.index(disclosure_date.isoformat())
        except ValueError:
            later = [i for i, d in enumerate(dates) if d > disclosure_date.isoformat()]
            if not later:
                caveats.append(f"{ticker}: no bars after {disclosure_date} — "
                               f"impact not measurable")
                continue
            start = later[0]
        o = ImpactObservation(
            ticker=ticker, disclosure_date=disclosure_date,
            asset_value_low=(value_by_ticker or {}).get(ticker))
        for w in IMPACT_WINDOWS:
            j = start + w
            if j >= len(bars):
                o.windows[f"{w}d"] = None
                o.benchmark_windows[f"{w}d"] = None
                o.excess[f"{w}d"] = None
                continue
            c0 = bars[start].get("close")
            c1 = bars[j].get("close")
            r = (c1 / c0 - 1.0) if (c0 and c1) else None
            o.windows[f"{w}d"] = r
            b0 = bench_by_date.get(bars[start]["date"], {}).get("close")
            b1 = bench_by_date.get(bars[j]["date"], {}).get("close") if bench_by_date else None
            br = (b1 / b0 - 1.0) if (b0 and b1) else None
            o.benchmark_windows[f"{w}d"] = br
            o.excess[f"{w}d"] = (r - br) if (r is not None and br is not None) else None
        o.note = ("Return measured from the FIRST bar on or after the disclosure "
                  "date. Execution on the disclosure date itself is not "
                  "assumed — the filing may have been published after close.")
        obs.append(o)
    caveats.append(
        f"Sample size: {len(obs)} single-name observation(s). A single "
        f"disclosure is an anecdote, not a demonstrated market effect. No "
        f"statistical inference is drawn from n={len(obs)}.")
    caveats.append(
        "No control for concurrent news. A move after a disclosure cannot be "
        "attributed to the disclosure without an event study; the excess "
        "return versus the benchmark is a descriptive difference, not a "
        "causal estimate.")
    return obs, caveats


# --------------------------------------------------------------------------
# Top-level report
# --------------------------------------------------------------------------


def build_disclosure_report(house_year: int = 2026,
                            oge_names: Optional[Sequence[str]] = None,
                            include_judicial: bool = True,
                            fetch_pdfs_for: Optional[Sequence[str]] = None
                            ) -> Dict[str, Any]:
    """Assemble the three-branch disclosure report.

    Every branch that cannot be reached is reported in `sources_unavailable`
    with its real reason. Nothing is reported as "no disclosures exist".
    """
    report: Dict[str, Any] = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "branches": {},
        "sources_unavailable": [],
        "provenance": [],
    }

    # --- LEGISLATIVE / HOUSE ---
    try:
        filings, prov = fetch_house_index(house_year)
        report["branches"]["legislative_house"] = {
            "title": BRANCHES["legislative"]["title"],
            "law": BRANCHES["legislative"]["law"],
            "filings_indexed": len(filings),
            "by_type": _count_by(f.filing_type for f in filings),
            "members": sum(1 for f in filings if f.is_member),
            "candidates": sum(1 for f in filings if f.is_candidate),
            "sample": [f.to_dict() for f in filings[:5]],
            "provenance": prov.disclosure(),
        }
        report["provenance"].append(prov.disclosure())
    except SourceUnavailable as exc:
        report["sources_unavailable"].append(
            unavailable("house_fd_index", HOUSE_FD_INDEX.format(year=house_year), str(exc)))

    # --- LEGISLATIVE / SENATE ---
    report["sources_unavailable"].append({
        "source": "senate_efd",
        "url": "https://efdsearch.senate.gov/",
        "reason": ("HTTP 403 from this host on every *.senate.gov path "
                   "(Akamai geo-block on the egress IP; www.house.gov returns "
                   "200 from the same IP). This is a SOURCE AVAILABILITY gap "
                   "— it is NOT evidence that Senate filings do not exist."),
        "at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "disclosure": ("SENATE SOURCE UNAVAILABLE — no Senate data was "
                       "substituted or estimated."),
    })

    # --- EXECUTIVE / OGE ---
    try:
        names = list(oge_names or [])
        if names:
            all_rows: List[OgeFiling] = []
            provs: List[Provenance] = []
            for n in names:
                rows, _tot, p = fetch_oge_index(search=n)
                all_rows.extend(rows)
                provs.append(p)
            prov = provs[0]
        else:
            all_rows, gaps, prov = fetch_oge_all()
            report["sources_unavailable"].extend(
                [{"source": "oge_pagination", "reason": g,
                  "at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                  "disclosure": "OGE index pagination incomplete."}
                 for g in gaps])
        report["branches"]["executive_oge"] = {
            "title": BRANCHES["executive"]["title"],
            "law": BRANCHES["executive"]["law"],
            "filings_indexed": len(all_rows),
            "with_public_pdf": sum(1 for r in all_rows if r.pdf_url),
            "request_form_only": sum(1 for r in all_rows if r.request_only),
            "by_agency": _count_by(r.agency for r in all_rows).most_common(10),
            "sample": [r.to_dict() for r in all_rows[:5]],
            "provenance": prov.disclosure(),
        }
        report["provenance"].append(prov.disclosure())
    except SourceUnavailable as exc:
        report["sources_unavailable"].append(
            unavailable("oge_pas_index", OGE_INDEX, str(exc)))

    # --- JUDICIAL ---
    if include_judicial:
        filings, gaps = fetch_judicial_filings()
        report["branches"]["judicial"] = {
            "title": BRANCHES["judicial"]["title"],
            "law": BRANCHES["judicial"]["law"],
            "filings_indexed": len(filings),
            "primary_filings": sum(1 for f in filings if f.provenance == "primary"),
            "secondary_filings": sum(1 for f in filings if f.provenance == "secondary"),
            "sample": [f.to_dict() for f in filings[:8]],
            "provenance_note": ("Judicial records from mirrors are labelled "
                                "[secondary]. The primary is JEFS, which is "
                                "registration-gated and TCP-unreachable from "
                                "this host."),
            "scotus_disclosure_page": (
                "NOT FOUND on the live site. Verified by live fetch: 11 "
                "candidate paths return HTTP 404; the live sitemap's 365 "
                "hrefs contain no disclosure link; the on-site search "
                "returns no disclosure page. SETTLED by a complete Wayback "
                "CDX scan: the domain was partitioned by leading path "
                "character (40 partitions), the three that hit the row cap "
                "were subdivided by second character (121,743 further "
                "unique URLs), and 'reportable' appears in ZERO archived "
                "supremecourt.gov URLs. Prefix queries for reportable*, "
                "financial* and disclos* each return 0 rows. The only "
                "archived disclosure URL is the historical "
                "/publicinfo/disclosures/financialdisclosure.aspx (302, "
                "2021-10-05). The one uncovered subtree is /docket*, the "
                "court-filing PDF range, excluded as docket noise."),
        }
        report["sources_unavailable"].extend(gaps)

    report["coverage"] = {
        "legislative_house": "legislative_house" in report["branches"],
        "legislative_senate": False,
        "executive_oge": "executive_oge" in report["branches"],
        "judicial": "judicial" in report["branches"],
    }
    report["disclosure"] = (
        "Coverage is INCOMPLETE by design on this host: the Senate branch is "
        "IP-geo-blocked and the primary judicial database (JEFS) is "
        "registration-gated and TCP-unreachable. The report states this "
        "rather than presenting a partial view as a complete one.")
    return report


def _count_by(items: Iterable[Any]) -> Any:
    from collections import Counter
    return Counter(items)
