"""
Stdlib HTTP layer with a browser User-Agent, retries, gzip handling and an
optional on-disk cache.

Deliberately stdlib-only: this machine has ~3.7 GB free on C: and adding
requests/httpx would be a pointless dependency. The backtest engine in the
strategy-backtest-lab skill already proved this shape works from this host
(Yahoo's chart API rejects a default urllib UA with HTTP 429; a browser UA
gets through).
"""

from __future__ import annotations

import gzip
import hashlib
import re
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

from .provenance import CACHE, LIVE, Provenance, SourceUnavailable

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "application/json,text/plain,*/*",
    "Accept-Encoding": "gzip",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}

# This host's Windows CA store mis-validates some chains (valid Let's Encrypt
# certs read as expired), so prefer certifi's bundle when it is importable.
try:  # pragma: no cover - environment dependent
    import certifi  # type: ignore

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:  # pragma: no cover
    _SSL_CTX = ssl.create_default_context()


def ssl_context() -> ssl.SSLContext:
    return _SSL_CTX


class HttpError(SourceUnavailable):
    pass


def _decompress(body: bytes, headers: Dict[str, str]) -> bytes:
    enc = (headers.get("Content-Encoding") or headers.get("content-encoding") or "").lower()
    if "gzip" in enc or body[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(body)
        except OSError:
            return body
    return body


def http_get(url: str, headers: Optional[Dict[str, str]] = None,
             timeout: int = 30, retries: int = 3,
             backoff: float = 1.5) -> Tuple[int, bytes, Dict[str, str]]:
    """GET with retries. Raises HttpError (a SourceUnavailable) on failure."""
    hdrs = dict(DEFAULT_HEADERS)
    hdrs.update(headers or {})
    last: Optional[Exception] = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                raw = resp.read()
                hdict = {k.title(): v for k, v in resp.headers.items()}
                return resp.status, _decompress(raw, hdict), hdict
        except urllib.error.HTTPError as exc:
            last = exc
            # 4xx (except 429) will not fix itself on retry.
            if exc.code not in (429, 500, 502, 503, 504):
                break
        except Exception as exc:  # noqa: BLE001
            last = exc
        if attempt < retries - 1:
            time.sleep(backoff * (attempt + 1))
    raise HttpError(f"GET failed after {retries} attempt(s): "
                    f"{redact(url)} -> "
                    f"{type(last).__name__}: {redact(str(last))}")


def http_json(url: str, headers: Optional[Dict[str, str]] = None,
              timeout: int = 30, retries: int = 3) -> Tuple[Any, int]:
    status, body, _ = http_get(url, headers=headers, timeout=timeout, retries=retries)
    try:
        return json.loads(body.decode("utf-8", "replace")), status
    except ValueError as exc:
        raise HttpError(f"Non-JSON response from {url} (HTTP {status}): {exc}") from exc


def http_post_json(url: str, payload: Any,
                   headers: Optional[Dict[str, str]] = None,
                   timeout: int = 30, retries: int = 3) -> Tuple[Any, int]:
    hdrs = dict(DEFAULT_HEADERS)
    hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    data = json.dumps(payload).encode("utf-8")
    last: Optional[Exception] = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                raw = resp.read()
                hdict = {k.title(): v for k, v in resp.headers.items()}
                body = _decompress(raw, hdict)
                return json.loads(body.decode("utf-8", "replace")), resp.status
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in (429, 500, 502, 503, 504):
                break
        except Exception as exc:  # noqa: BLE001
            last = exc
        if attempt < retries - 1:
            time.sleep(1.5 * (attempt + 1))
    raise HttpError(f"POST failed after {retries} attempt(s): "
                    f"{redact(url)} -> "
                    f"{type(last).__name__}: {redact(str(last))}")


def _cache_key(url: str) -> str:
    """A filesystem-safe cache key for a URL.

    The URL may contain a credential in its query string (Etherscan puts
    `apikey` there), so the on-disk name is a HASH of the URL, never the
    URL itself. The full URL stays in the in-memory index only.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return digest

class CachedFetcher:
    """Fetch-with-cache helper.

    The cache stores the response AND its provenance, so a later cache hit is
    reported as CACHE with the ORIGINAL fetch time — never as fresh live data.
    """

    def __init__(self, cache_dir: str, max_age_seconds: Optional[float] = None):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.max_age_seconds = max_age_seconds

    def _key(self, name: str, params: Optional[Dict[str, Any]] = None) -> str:
        import hashlib
        raw = name + "|" + json.dumps(params or {}, sort_keys=True, default=str)
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:60]
        return os.path.join(self.cache_dir, f"{safe}.{h}.json")

    def get_json(self, name: str, url: str,
                 params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None,
                 max_age_seconds: Optional[float] = None,
                 refresh: bool = False,
                 timeout: int = 30,
                 source: str = "http") -> Tuple[Any, Provenance]:
        key = self._key(name, params)
        age_limit = max_age_seconds if max_age_seconds is not None else self.max_age_seconds
        if not refresh and os.path.exists(key):
            try:
                with open(key, "r", encoding="utf-8") as fh:
                    blob = json.load(fh)
                prov = Provenance(**blob["provenance"])
                fresh = age_limit is None or (time.time() - prov.fetched_at_epoch) <= age_limit
                if fresh:
                    prov.kind = CACHE
                    prov.note = (prov.note + " " if prov.note else "") + \
                        "Served from local cache; upstream not re-contacted."
                    return blob["payload"], prov
            except (OSError, ValueError, KeyError, TypeError):
                pass
        payload, status = http_json(url, headers=headers, timeout=timeout)
        prov = Provenance(source=source, kind=LIVE, url=url,
                          params=dict(params or {}),
                          note=f"HTTP {status}")
        try:
            with open(key, "w", encoding="utf-8") as fh:
                json.dump({"payload": payload, "provenance": {
                    "source": prov.source, "kind": LIVE, "url": prov.url,
                    "fetched_at": prov.fetched_at,
                    "fetched_at_epoch": prov.fetched_at_epoch,
                    "note": prov.note, "params": prov.params}}, fh)
        except OSError:
            pass
        return payload, prov


# --------------------------------------------------------------------------
# Secrets
# --------------------------------------------------------------------------
# Credentials live in the process environment, or in a gitignored
# `.secrets.env` beside the package. They are NEVER literals in source,
# and NEVER reach a report, chart, log or summary.
#
# The git repository's toplevel is C:\Users\HP, so a `git add .` from
# there would stage anything under AppData. Both the repository root and
# the project directory carry a .gitignore that excludes `.secrets.env`,
# `*.env`, `*.key` and `*.pem`.

_SECRET_NAMES = ("ETHERSCAN_API_KEY", "ETHERSCAN_KEY", "MORALIS_API_KEY",
                 "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "BINANCE_API_KEY")


def _load_secret_file() -> None:
    """Populate os.environ from a `.secrets.env` beside the package.

    Existing environment variables WIN: an explicitly exported variable
    is a deliberate override and must not be clobbered by a file.
    """
    path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), ".secrets.env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                name = name.strip()
                value = value.strip().strip('"').strip("'")
                if not name or not value:
                    continue
                os.environ.setdefault(name, value)
    except OSError:
        pass


_load_secret_file()


def get_secret(name: str) -> Optional[str]:
    """A credential, or None. The value is returned to the caller only;
    it is never logged."""
    return os.environ.get(name) or None


#: Matches anything that looks like an API key or a long opaque token.
_SECRET_PATTERN = re.compile(
    r"(?i)\b(?:apikey|api[_-]?key|apikey=)"
    r"[\s:=]*[A-Za-z0-9_\-]{16,}")


def redact(text: str) -> str:
    """Strip credential-shaped strings out of text before it is written
    to an artefact. This is the single chokepoint for report output."""
    if not text:
        return text
    out = _SECRET_PATTERN.sub("[REDACTED]", text)
    for name in _SECRET_NAMES:
        val = os.environ.get(name)
        if val and len(val) >= 8:
            out = out.replace(val, "[REDACTED]")
    return out
