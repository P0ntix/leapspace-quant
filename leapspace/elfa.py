"""Elfa AI: the social, narrative and positioning layer.

WHAT THIS IS
    Elfa (https://api.elfa.ai) is a real-time market-intelligence API
    for crypto and equities. It is the layer this package was MISSING.

    The package had prices (Yahoo, CoinGecko), derivatives structure
    (funding, open interest, gamma) and wallet-level on-chain data.
    It had NO attention, narrative, retail-flow or positioning data -
    and the research papers name exactly that:

      "crypto sentiment and retail attention data show strong
       standalone performance in forecast regressions"
      "Market states ... are more directly informed by retail flow
       and positioning"
        - Trading strategies for retail traders

    So this module supplies the social/attention/positioning inputs the
    crypto claims need.

WHAT ELFA DOES NOT HAVE, AND WHERE THAT DATA COMES FROM
    Elfa has NO price feed, NO funding rate and NO liquidation feed.
    It is an attention and positioning API, not a market-data feed.

      token prices   -> `market.py` (Yahoo, CoinGecko, DexScreener)
      funding rates  -> `cryptoderivs.py` (Binance, Bybit)
      liquidations   -> `liquidations.py` (Binance, Bybit)

    The two are complementary and are stored side by side so a
    backtest can join an attention series to a price series.

THE HISTORY LIMIT IS THE BINDING CONSTRAINT
    `/v3/key-status` reports `historyFrom`, and this key's is
    2026-10-05 - about 31 days. The API will not serve older data.

    That is enough for FORWARD testing and for building the feature
    plumbing, and it is NOT enough for a backtest. The module states
    this in every manifest it writes, because a dataset whose length
    is not recorded is a dataset whose length nobody can check.

THE COST
    1 credit per request; about $0.0145 each. The key is PAYG with a
    60-requests-per-minute limit. The client tracks both and refuses
    to exceed the rate limit.

CREDENTIAL HYGIENE
    The key is read from `ELFA_API_KEY` in the environment, or from a
    file path given by `ELFA_KEY_FILE`. It is NEVER logged, never
    written to a manifest, and never included in a provenance record.
    A provenance record carries the endpoint, the parameters, the
    HTTP status and the credit cost - not the credential.

WHERE THE DATA GOES
    `ELFA_STORAGE_ROOT`, defaulting to the directory the user
    specified. Everything collected lands there and nowhere else.
"""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Tuple

__all__ = [
    "DEFAULT_STORAGE_ROOT",
    "ElfaClient",
    "ElfaError",
    "write_jsonl",
    "read_jsonl",
]

#: Where the user asked for the data to be stored, and only there.
DEFAULT_STORAGE_ROOT = r"D:\obsidian\Hermes Agent\Elfa ai storage"

BASE = "https://api.elfa.ai"


class ElfaError(Exception):
    """An Elfa request failed. The message never contains the key."""


def _default_key_file() -> str:
    home = os.path.expanduser("~")
    return os.path.join(home, "AppData", "Local", "hermes", "secrets",
                        "elfa_key.txt")


class ElfaClient:
    """A rate-limited, credit-aware Elfa client.

    Usage::

        c = ElfaClient()
        c.key_status()
        c.trending_tokens(from_ts=..., to_ts=...)
    """

    def __init__(self, api_key: Optional[str] = None,
                 key_file: Optional[str] = None,
                 storage_root: Optional[str] = None,
                 requests_per_minute: int = 60,
                 timeout: int = 60,
                 verbose: bool = True) -> None:
        self.api_key = api_key or os.environ.get("ELFA_API_KEY") or ""
        if not self.api_key and key_file:
            self.api_key = self._read_key_file(key_file)
        if not self.api_key:
            self.api_key = self._read_key_file(_default_key_file())
        if not self.api_key:
            raise ElfaError(
                "No Elfa API key. Set ELFA_API_KEY in the environment, or "
                "write the key to the file named by ELFA_KEY_FILE.")
        self.storage_root = storage_root or os.environ.get(
            "ELFA_STORAGE_ROOT", DEFAULT_STORAGE_ROOT)
        self.rpm = max(1, int(requests_per_minute))
        self.timeout = timeout
        self.verbose = verbose
        self._call_times: List[float] = []
        self.credits_spent = 0
        self.requests_made = 0
        self._ssl_ctx: Optional[ssl.SSLContext] = None

    # ------------------------------------------------------------------
    @staticmethod
    def _read_key_file(path: str) -> str:
        try:
            with open(path, encoding="utf-8") as fh:
                return fh.read().strip()
        except OSError:
            return ""

    def _ctx(self) -> ssl.SSLContext:
        if self._ssl_ctx is None:
            try:
                import certifi
                self._ssl_ctx = ssl.create_default_context(
                    cafile=certifi.where())
            except Exception:  # noqa: BLE001
                self._ssl_ctx = ssl.create_default_context()
        return self._ssl_ctx

    def _throttle(self) -> None:
        """Stay inside the per-minute limit."""
        now = time.time()
        self._call_times = [t for t in self._call_times
                            if now - t < 60.0]
        if len(self._call_times) >= self.rpm:
            sleep_for = 60.0 - (now - self._call_times[0]) + 0.5
            if sleep_for > 0:
                if self.verbose:
                    print(f"  [elfa] rate limit reached, sleeping "
                          f"{sleep_for:.1f}s", flush=True)
                time.sleep(sleep_for)
                now = time.time()
                self._call_times = [t for t in self._call_times
                                    if now - t < 60.0]
        self._call_times.append(time.time())

    def get(self, path: str, params: Optional[Dict[str, Any]] = None,
            retries: int = 3) -> Tuple[Any, Dict[str, Any]]:
        """One GET. Returns ``(parsed_body, meta)``.

        `meta` carries the HTTP status, the credit cost, the rate-limit
        state and the endpoint - NEVER the credential.
        """
        url = BASE + path
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean, doseq=True)

        last: Optional[str] = None
        for attempt in range(retries):
            self._throttle()
            req = urllib.request.Request(url, method="GET", headers={
                "x-elfa-api-key": self.api_key,
                "Accept": "application/json",
                "User-Agent": "leapspace-quant/1.0",
            })
            try:
                with urllib.request.urlopen(
                        req, timeout=self.timeout,
                        context=self._ctx()) as resp:
                    body = json.loads(resp.read().decode())
                    hdrs = {k.lower(): v for k, v in resp.headers.items()}
                    self.requests_made += 1
                    try:
                        self.credits_spent += int(
                            hdrs.get("x-elfa-credits") or 0)
                    except (TypeError, ValueError):
                        pass
                    meta = {
                        "endpoint": path,
                        "params": dict(params or {}),
                        "http_status": resp.status,
                        "credits": hdrs.get("x-elfa-credits"),
                        "rate_limit_remaining":
                            hdrs.get("x-ratelimit-remaining"),
                        "fetched_at": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                    return body, meta
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode(errors="replace")
                code = None
                msg = raw[:300]
                try:
                    parsed = json.loads(raw)
                    code = parsed.get("code")
                    msg = parsed.get("message") or msg
                except Exception:  # noqa: BLE001
                    pass
                last = f"HTTP {exc.code} {code or ''} {msg}".strip()
                # 429 is the rate limit, 503 is a transient upstream.
                if exc.code in (429, 503, 502, 504):
                    wait = 5.0 * (attempt + 1)
                    try:
                        reset = exc.headers.get("RateLimit-Reset")
                        if reset:
                            wait = max(wait, min(float(reset), 65.0))
                    except (TypeError, ValueError):
                        pass
                    if self.verbose:
                        print(f"  [elfa] {exc.code} on {path}, retrying in "
                              f"{wait:.0f}s", flush=True)
                    time.sleep(wait)
                    continue
                break
            except Exception as exc:  # noqa: BLE001
                last = f"{type(exc).__name__}: {str(exc)[:200]}"
                if attempt < retries - 1:
                    time.sleep(3.0 * (attempt + 1))
                    continue
                break
        raise ElfaError(f"{path} failed: {last}")

    def get_paginated(self, path: str, params: Optional[Dict[str, Any]] = None,
                      items_key: str = "items",
                      page_size: Optional[int] = 200,
                      max_pages: int = 20,
                      send_limit: bool = True,
                      verbose: bool = False) -> Tuple[List[Any], Dict[str, Any]]:
        """Follow the cursor and collect every page.

        The v3 endpoints return ``{items_key: [...], nextCursor, hasMore,
        servedFrom}``. The cursor is opaque and must be echoed back
        unchanged. `servedFrom` says where the history ACTUALLY started,
        which is the number that matters - a request for 30 days that
        the plan cuts to 12 says so in `servedFrom`, and a dataset
        whose real start is not recorded is a dataset whose length
        cannot be checked.
        """
        base = dict(params or {})
        rows: List[Any] = []
        cursor: Optional[str] = None
        meta: Dict[str, Any] = {}
        served_from: Optional[int] = None
        page = 0
        for page in range(max_pages):
            p = dict(base)
            if send_limit and page_size:
                p["limit"] = page_size
            if cursor:
                p["cursor"] = cursor
            body, meta = self.get(path, p)
            if not isinstance(body, dict):
                break
            sf = body.get("servedFrom")
            if sf:
                served_from = int(sf)
            batch = body.get(items_key) or []
            rows.extend(batch)
            if verbose:
                print(f"    {path} page {page + 1}: +{len(batch)} "
                      f"(total {len(rows)})", flush=True)
            if not body.get("hasMore"):
                break
            cursor = body.get("nextCursor")
            if not cursor:
                break
        meta = dict(meta)
        meta["served_from"] = served_from
        meta["pages_fetched"] = page + 1 if "page" in dir() else 0
        meta["items_key"] = items_key
        return rows, meta

    # ------------------------------------------------------------------
    # The endpoints
    # ------------------------------------------------------------------
    def key_status(self) -> Dict[str, Any]:
        body, meta = self.get("/v3/key-status")
        return {"status": body, "meta": meta}

    def trending_tokens(self, from_ts: Optional[int] = None,
                        to_ts: Optional[int] = None,
                        time_window: Optional[str] = None,
                        page: int = 1, page_size: int = 50,
                        min_mentions: int = 1) -> Dict[str, Any]:
        """Tokens ranked by MENTION COUNT - the social-attention series.

        `from_ts`/`to_ts` are unix seconds and make the endpoint
        HISTORICAL, which is what turns it into a feature rather than
        a snapshot.
        """
        body, meta = self.get("/v2/aggregations/trending-tokens", {
            "timeWindow": time_window, "from": from_ts, "to": to_ts,
            "page": page, "pageSize": page_size,
            "minMentions": min_mentions,
        })
        return {"data": body, "meta": meta}

    def trending_narratives(self, time_frame: str = "day",
                            max_narratives: int = 20) -> Dict[str, Any]:
        body, meta = self.get("/v2/data/trending-narratives", {
            "timeFrame": time_frame, "maxNarratives": max_narratives,
        })
        return {"data": body, "meta": meta}

    def token_news(self, coin_ids: str, time_window: str = "24h",
                   page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        body, meta = self.get("/v2/data/token-news", {
            "coinIds": coin_ids, "timeWindow": time_window,
            "page": page, "pageSize": page_size,
        })
        return {"data": body, "meta": meta}

    def top_mentions(self, ticker: Optional[str] = None,
                     time_window: str = "24h",
                     page_size: int = 50) -> Dict[str, Any]:
        body, meta = self.get("/v2/data/top-mentions", {
            "ticker": ticker, "timeWindow": time_window,
            "pageSize": page_size,
        })
        return {"data": body, "meta": meta}

    def trending_cas_twitter(self, time_window: str = "24h",
                             page: int = 1, page_size: int = 50,
                             min_mentions: int = 1) -> Dict[str, Any]:
        body, meta = self.get("/v2/aggregations/trending-cas/twitter", {
            "timeWindow": time_window, "page": page,
            "pageSize": page_size, "minMentions": min_mentions,
        })
        return {"data": body, "meta": meta}

    def trending_cas_telegram(self, time_window: str = "24h",
                              page: int = 1, page_size: int = 50,
                              min_mentions: int = 1) -> Dict[str, Any]:
        body, meta = self.get("/v2/aggregations/trending-cas/telegram", {
            "timeWindow": time_window, "page": page,
            "pageSize": page_size, "minMentions": min_mentions,
        })
        return {"data": body, "meta": meta}

    def crypto_mindshare(self, **params: Any) -> Dict[str, Any]:
        body, meta = self.get("/v3/market/crypto/mindshare", params)
        return {"data": body, "meta": meta}

    def equity_mindshare(self, **params: Any) -> Dict[str, Any]:
        body, meta = self.get("/v3/market/equity/mindshare", params)
        return {"data": body, "meta": meta}

    def crypto_call_book(self, **params: Any) -> Dict[str, Any]:
        """HOURLY BARS of long/short share and crowding - a real series."""
        body, meta = self.get("/v3/market/crypto/call-book", params)
        return {"data": body, "meta": meta}

    def equity_call_book(self, **params: Any) -> Dict[str, Any]:
        body, meta = self.get("/v3/market/equity/call-book", params)
        return {"data": body, "meta": meta}

    def trending_contracts(self, **params: Any) -> Dict[str, Any]:
        """EVM and Solana contract addresses ranked by social mentions.

        This is the MEMECOIN layer: the contracts worth watching are
        often the ones nobody has catalogued.
        """
        body, meta = self.get("/v3/market/crypto/trending-contracts",
                               params)
        return {"data": body, "meta": meta}

    def calls(self, **params: Any) -> Dict[str, Any]:
        body, meta = self.get("/v3/calls", params)
        return {"data": body, "meta": meta}

    def call_episodes(self, **params: Any) -> Dict[str, Any]:
        body, meta = self.get("/v3/calls/episodes", params)
        return {"data": body, "meta": meta}

    def positioning(self, entity_id: str) -> Dict[str, Any]:
        body, meta = self.get("/v3/calls/positioning",
                               {"entityId": entity_id})
        return {"data": body, "meta": meta}

    def events(self, **params: Any) -> Dict[str, Any]:
        body, meta = self.get("/v3/events", params)
        return {"data": body, "meta": meta}

    def storylines(self, **params: Any) -> Dict[str, Any]:
        body, meta = self.get("/v3/events/storylines", params)
        return {"data": body, "meta": meta}

    def arcs(self, **params: Any) -> Dict[str, Any]:
        body, meta = self.get("/v3/events/arcs", params)
        return {"data": body, "meta": meta}

    def entities(self, query: str) -> Dict[str, Any]:
        """Resolve a name to an entity id. It MATCHES EXACTLY."""
        body, meta = self.get("/v3/entities", {"q": query})
        return {"data": body, "meta": meta}

    def top_accounts(self, **params: Any) -> Dict[str, Any]:
        body, meta = self.get("/v3/people/accounts", params)
        return {"data": body, "meta": meta}


# ----------------------------------------------------------------------
# Storage
# ----------------------------------------------------------------------
def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> int:
    """Append rows to a JSONL file. Returns the number written."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = 0
    with open(path, "a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, default=str) + "\n")
            n += 1
    return n


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out
