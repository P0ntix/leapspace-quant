"""Low-level live HTTP helper for the chain-landscape survey.

Reuses `leapspace.http` for the TLS context (certifi bundle - this host's
Windows CA store mis-validates several chains) and the browser User-Agent
headers, but does NOT raise on HTTP error statuses: the survey needs the
EXACT status code for every endpoint, so 403 / 429 / 404 are data points,
not exceptions.
"""
from __future__ import annotations

import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from leapspace.http import DEFAULT_HEADERS, ssl_context  # noqa: E402

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CACHE_DIR = os.path.join(DATA_DIR, "_raw")
os.makedirs(CACHE_DIR, exist_ok=True)


class Result:
    """Outcome of one HTTP probe."""

    __slots__ = ("url", "status", "body", "error", "elapsed_ms", "headers")

    def __init__(self, url: str, status: Optional[int], body: bytes,
                 error: Optional[str], elapsed_ms: float,
                 headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.status = status
        self.body = body
        self.error = error
        self.elapsed_ms = elapsed_ms
        self.headers = headers or {}

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300

    def text(self) -> str:
        if self.body is None:
            return ""
        return self.body.decode("utf-8", "replace")

    def json(self) -> Any:
        try:
            return json.loads(self.text())
        except ValueError:
            return None

    def summary(self) -> str:
        if self.error:
            return f"ERROR {self.error}"
        return f"HTTP {self.status}"


def _decompress(body: bytes, headers: Dict[str, str]) -> bytes:
    enc = (headers.get("Content-Encoding") or headers.get("content-encoding") or "").lower()
    if "gzip" in enc or body[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(body)
        except OSError:
            return body
    return body


def request(url: str, method: str = "GET", payload: Any = None,
            headers: Optional[Dict[str, str]] = None, timeout: int = 30,
            retries: int = 2, retry_429: int = 0,
            backoff_429: float = 12.0) -> Result:
    """One HTTP call, retries transient failures, never raises.

    `retry_429` adds extra attempts specifically for HTTP 429 (CoinGecko's
    free tier throttles hard and needs multi-second waits, not sub-second).
    """
    hdrs = dict(DEFAULT_HEADERS)
    hdrs.update(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    last_err: Optional[str] = None
    last_status: Optional[int] = None
    total = retries + retry_429
    for attempt in range(total + 1):
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
            with urllib.request.urlopen(req, timeout=timeout,
                                        context=ssl_context()) as resp:
                raw = resp.read()
                hd = {k.title(): v for k, v in resp.headers.items()}
                body = _decompress(raw, hd)
                return Result(url, resp.status, body, None,
                              (time.time() - t0) * 1000.0, hd)
        except urllib.error.HTTPError as exc:
            last_status = exc.code
            last_err = f"HTTPError {exc.code} {exc.reason}"
            try:
                body = exc.read()
                hd = {k.title(): v for k, v in (exc.headers or {}).items()}
                body = _decompress(body, hd)
            except Exception:  # noqa: BLE001
                body, hd = b"", {}
            if exc.code == 429 and attempt < total:
                wait = backoff_429 * (attempt + 1)
                time.sleep(wait)
                continue
            if exc.code in (500, 502, 503, 504) and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return Result(url, exc.code, body, last_err,
                          (time.time() - t0) * 1000.0, hd)
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            return Result(url, None, b"", last_err, (time.time() - t0) * 1000.0)
    return Result(url, last_status, b"", last_err, 0.0)


def fetch_json(name: str, url: str, method: str = "GET", payload: Any = None,
               headers: Optional[Dict[str, str]] = None, timeout: int = 30,
               retries: int = 2, save: bool = True, retry_429: int = 0,
               backoff_429: float = 12.0) -> Tuple[Any, Result]:
    """Fetch + parse JSON, and optionally cache the raw response."""
    res = request(url, method=method, payload=payload, headers=headers,
                  timeout=timeout, retries=retries, retry_429=retry_429,
                  backoff_429=backoff_429)
    data = res.json()
    if save:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:80]
        path = os.path.join(CACHE_DIR, f"{safe}.json")
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"url": url, "status": res.status, "error": res.error,
                           "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                      time.gmtime()),
                           "data": data}, fh, default=str)
        except OSError:
            pass
    return data, res


def load_cached(name: str) -> Any:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:80]
    path = os.path.join(CACHE_DIR, f"{safe}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh).get("data")
    except (OSError, ValueError):
        return None
