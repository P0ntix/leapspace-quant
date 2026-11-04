"""Market data: prices, funding, open interest, positioning, liquidations.

WHY THIS IS SEPARATE FROM ELFA
    Elfa is an ATTENTION and POSITIONING API. It has no price feed, no
    funding rate and no liquidation feed. The research claims need
    both halves joined:

        attention (Elfa)  x  price (here)  =  a testable feature

    and the join is only honest if the two are on the same grid and
    both are point-in-time. That is what this module's output is for.

WHAT IS HERE, AND WHERE EACH PIECE COMES FROM
    OHLCV            Binance. `data-api.binance.vision` for spot (the
                     public, non-geo-blocked host) and `fapi.binance.com`
                     for the perpetuals. Hourly and daily.
    funding          Binance `fapi/v1/fundingRate` - the realised
                     funding rate with its mark price.
    open interest    Binance `fapi/v1/openInterest` and the
                     `futures/data/openInterestHist` series.
    taker flow       Binance `futures/data/takerlongshortRatio` - the
                     buy/sell VOLUME ratio. This is the closest public
                     proxy to aggressor flow, and it is a genuine
                     LEADING indicator: it shows who is crossing the
                     spread before the price moves.
    positioning      Binance `futures/data/topLongShortAccountRatio`
                     and `globalLongShortAccountRatio` - how many
                     ACCOUNTS are long against how many are short.
                     This is the retail-positioning layer the regime
                     paper asks for.
    liquidations     Binance's WebSocket `!forceOrder@arr`. The REST
                     `allForceOrders` endpoint now returns 404, so
                     the stream is the source.

THE LIQUIDATION STREAM IS A FORWARD-TESTING FEED
    Liquidations are a live event feed. Collecting them over time
    produces the forward-testing sample the requirement asks for: a
    record of forced selling with a timestamp, a symbol and a size,
    against which any exit rule can later be judged.
"""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "FAPI", "SPOT_API", "DATA_API",
    "fetch_klines", "fetch_funding_history", "fetch_open_interest",
    "fetch_open_interest_hist", "fetch_taker_long_short",
    "fetch_long_short_ratios", "list_perp_symbols", "list_spot_symbols",
    "collect_liquidation_stream", "ms_to_iso", "ms_to_date",
]


class _StreamClosed(Exception):
    """The server closed the WebSocket. The capture window is over."""

FAPI = "https://fapi.binance.com"
SPOT_API = "https://api.binance.com"
DATA_API = "https://data-api.binance.vision"

#: The Binance intervals the collector uses.
INTERVAL_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000,
    "4h": 14_400_000, "1d": 86_400_000,
}

MAJORS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
          "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "LTCUSDT"]


def _ctx() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        return ssl.create_default_context()


def ms_to_iso(ms: Optional[int]) -> Optional[str]:
    """A Binance millisecond timestamp to an ISO-8601 UTC string.

    Every Binance timestamp in this module is in MILLISECONDS, and
    feeding one to `time.gmtime` raises `OSError: [Errno 22] Invalid
    argument` because the value is far outside the representable
    range. This helper is the only place the conversion happens, so a
    consumer never has to remember which unit a field is in.
    """
    if ms is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(ms) / 1000))


def ms_to_date(ms: Optional[int]) -> Optional[str]:
    """A Binance millisecond timestamp to a UTC date string."""
    if ms is None:
        return None
    return time.strftime("%Y-%m-%d", time.gmtime(int(ms) / 1000))


def _get_json(url: str, timeout: int = 30) -> Any:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout,
                                context=_ctx()) as r:
        return json.loads(r.read().decode())


# --------------------------------------------------------------------------
# Instruments
# --------------------------------------------------------------------------
def list_perp_symbols() -> List[str]:
    """Every Binance USDT-M PERPETUAL that is actively trading."""
    try:
        info = _get_json(f"{FAPI}/fapi/v1/exchangeInfo")
    except Exception:  # noqa: BLE001
        return list(MAJORS)
    out = []
    for s in info.get("symbols") or []:
        if (s.get("contractType") == "PERPETUAL"
                and s.get("quoteAsset") == "USDT"
                and s.get("status") == "TRADING"):
            out.append(s["symbol"])
    return sorted(out)


def list_spot_symbols() -> List[str]:
    """Every Binance SPOT pair against USDT that is actively trading."""
    try:
        info = _get_json(f"{DATA_API}/api/v3/exchangeInfo")
    except Exception:  # noqa: BLE001
        return list(MAJORS)
    out = []
    for s in info.get("symbols") or []:
        if (s.get("quoteAsset") == "USDT"
                and s.get("status") == "TRADING"):
            out.append(s["symbol"])
    return sorted(out)


# --------------------------------------------------------------------------
# OHLCV
# --------------------------------------------------------------------------
def fetch_klines(symbol: str, interval: str = "1h",
                 start_ms: Optional[int] = None,
                 end_ms: Optional[int] = None,
                 limit: int = 1000,
                 market: str = "perp",
                 max_pages: int = 40) -> List[Dict[str, Any]]:
    """OHLCV bars, oldest first.

    Binance caps a page at 1,000 bars, so a long history is walked
    backwards page by page. `start_ms` bounds the walk.

    A PERPETUAL symbol is not always a SPOT symbol and vice versa -
    1000PEPEUSDT is a perp with no spot pair, and PEPEUSDT is a spot
    pair with no perp. The `market` argument picks the host and the
    fallback tries the other one, and the source is recorded on every
    row so a bar's origin is never in doubt.
    """
    if market == "perp":
        hosts = [(f"{FAPI}/fapi/v1/klines", True), (f"{DATA_API}/api/v3/klines", False)]
    else:
        hosts = [(f"{DATA_API}/api/v3/klines", False), (f"{FAPI}/fapi/v1/klines", True)]
    step = INTERVAL_MS.get(interval, 3_600_000)
    end = end_ms or int(time.time() * 1000)
    rows: List[Dict[str, Any]] = []
    cursor_end = end
    for _ in range(max_pages):
        params: Dict[str, Any] = {"symbol": symbol, "interval": interval,
                                  "limit": limit}
        if start_ms is not None:
            params["startTime"] = start_ms
            params["endTime"] = cursor_end
        got = None
        used = None
        for base, is_perp in hosts:
            url = f"{base}?{urllib.parse.urlencode(params)}"
            try:
                data = _get_json(url)
            except urllib.error.HTTPError:
                continue
            except Exception:  # noqa: BLE001
                continue
            if isinstance(data, list) and data:
                got = data
                used = ("binance_perp" if is_perp else "binance_spot")
                break
        if not got:
            break
        for k in got:
            rows.append({
                "open_time": int(k[0]),
                "open": float(k[1]), "high": float(k[2]),
                "low": float(k[3]), "close": float(k[4]),
                "volume": float(k[5]), "close_time": int(k[6]),
                "quote_volume": float(k[7]),
                "trades": int(k[8]),
                "taker_buy_base": float(k[9]),
                "taker_buy_quote": float(k[10]),
                "symbol": symbol, "interval": interval,
                "source": used,
            })
        if start_ms is None:
            break
        oldest = int(got[0][0])
        if oldest <= start_ms:
            break
        cursor_end = oldest - 1
    rows.sort(key=lambda r: r["open_time"])
    # De-duplicate on open_time - the fallback host can repeat bars.
    seen = set()
    out = []
    for r in rows:
        if r["open_time"] in seen:
            continue
        seen.add(r["open_time"])
        out.append(r)
    return out


# --------------------------------------------------------------------------
# Derivatives
# --------------------------------------------------------------------------
def fetch_funding_history(symbol: str, limit: int = 1000,
                          start_ms: Optional[int] = None,
                          end_ms: Optional[int] = None,
                          max_pages: int = 30) -> List[Dict[str, Any]]:
    """The REALISED funding rate history with its mark price."""
    rows: List[Dict[str, Any]] = []
    cursor = end_ms or int(time.time() * 1000)
    for _ in range(max_pages):
        params: Dict[str, Any] = {"symbol": symbol, "limit": limit}
        if start_ms is not None:
            params["startTime"] = start_ms
            params["endTime"] = cursor
        try:
            data = _get_json(
                f"{FAPI}/fapi/v1/fundingRate?{urllib.parse.urlencode(params)}")
        except Exception:  # noqa: BLE001
            break
        if not isinstance(data, list) or not data:
            break
        for r in data:
            rows.append({
                "funding_time": int(r.get("fundingTime")),
                "funding_rate": float(r.get("fundingRate")),
                "mark_price": float(r.get("markPrice")) if r.get("markPrice")
                else None,
                "symbol": r.get("symbol"),
                "source": "binance/fapi/v1/fundingRate",
            })
        if start_ms is None:
            break
        oldest = int(data[0].get("fundingTime") or 0)
        if oldest <= start_ms:
            break
        cursor = oldest - 1
    rows.sort(key=lambda r: r["funding_time"])
    return rows


def fetch_open_interest(symbol: str) -> Optional[Dict[str, Any]]:
    """The current open interest - a snapshot, not a series."""
    try:
        d = _get_json(f"{FAPI}/fapi/v1/openInterest?symbol={symbol}")
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(d, dict):
        return None
    return {
        "symbol": d.get("symbol"),
        "open_interest": float(d.get("openInterest") or 0),
        "time": int(d.get("time") or 0),
        "source": "binance/fapi/v1/openInterest",
    }


def fetch_open_interest_hist(symbol: str, period: str = "1h",
                              limit: int = 500,
                              max_pages: int = 20
                              ) -> List[Dict[str, Any]]:
    """The open-interest history series."""
    rows: List[Dict[str, Any]] = []
    cursor = int(time.time() * 1000)
    for _ in range(max_pages):
        params = {"symbol": symbol, "period": period, "limit": limit,
                  "endTime": cursor}
        try:
            data = _get_json(
                f"{FAPI}/futures/data/openInterestHist?"
                f"{urllib.parse.urlencode(params)}")
        except Exception:  # noqa: BLE001
            break
        if not isinstance(data, list) or not data:
            break
        for r in data:
            rows.append({
                "symbol": r.get("symbol"),
                "sum_open_interest": float(r.get("sumOpenInterest") or 0),
                "sum_open_interest_value":
                    float(r.get("sumOpenInterestValue") or 0),
                "timestamp": int(r.get("timestamp") or 0),
                "source": "binance/futures/data/openInterestHist",
            })
        oldest = int(data[0].get("timestamp") or 0)
        if oldest <= 0:
            break
        cursor = oldest - 1
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def fetch_taker_long_short(symbol: str, period: str = "1h",
                            limit: int = 500, max_pages: int = 20
                            ) -> List[Dict[str, Any]]:
    """Taker buy/sell VOLUME ratio - the aggressor-flow series.

    This is the closest public proxy to order-flow imbalance, and it
    is a genuine LEADING indicator: it shows who is crossing the
    spread before the price has moved to reflect it.
    """
    rows: List[Dict[str, Any]] = []
    cursor = int(time.time() * 1000)
    for _ in range(max_pages):
        params = {"symbol": symbol, "period": period, "limit": limit,
                  "endTime": cursor}
        try:
            data = _get_json(
                f"{FAPI}/futures/data/takerlongshortRatio?"
                f"{urllib.parse.urlencode(params)}")
        except Exception:  # noqa: BLE001
            break
        if not isinstance(data, list) or not data:
            break
        for r in data:
            rows.append({
                "symbol": symbol,
                "buy_vol": float(r.get("buyVol") or 0),
                "sell_vol": float(r.get("sellVol") or 0),
                "buy_sell_ratio": float(r.get("buySellRatio") or 0),
                "timestamp": int(r.get("timestamp") or 0),
                "source": "binance/futures/data/takerlongshortRatio",
            })
        oldest = int(data[0].get("timestamp") or 0)
        if oldest <= 0:
            break
        cursor = oldest - 1
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def fetch_long_short_ratios(symbol: str, period: str = "1h",
                            limit: int = 500, max_pages: int = 20
                            ) -> List[Dict[str, Any]]:
    """The account long/short ratios: TOP traders and GLOBAL accounts.

    The difference between them is the interesting part - when the top
    traders and the crowd lean the same way, the crowding is total.
    """
    rows: List[Dict[str, Any]] = []
    for kind, path in (("top_accounts", "topLongShortAccountRatio"),
                       ("global_accounts", "globalLongShortAccountRatio")):
        cursor = int(time.time() * 1000)
        for _ in range(max_pages):
            params = {"symbol": symbol, "period": period, "limit": limit,
                      "endTime": cursor}
            try:
                data = _get_json(
                    f"{FAPI}/futures/data/{path}?"
                    f"{urllib.parse.urlencode(params)}")
            except Exception:  # noqa: BLE001
                break
            if not isinstance(data, list) or not data:
                break
            for r in data:
                rows.append({
                    "symbol": symbol, "kind": kind,
                    "long_account": float(r.get("longAccount") or 0),
                    "short_account": float(r.get("shortAccount") or 0),
                    "long_short_ratio": float(r.get("longShortRatio") or 0),
                    "timestamp": int(r.get("timestamp") or 0),
                    "source": f"binance/futures/data/{path}",
                })
            oldest = int(data[0].get("timestamp") or 0)
            if oldest <= 0:
                break
            cursor = oldest - 1
    rows.sort(key=lambda r: r["timestamp"])
    return rows


# --------------------------------------------------------------------------
# Liquidations - the WebSocket stream
# --------------------------------------------------------------------------
def collect_liquidation_stream(seconds: int = 60,
                               out_path: Optional[str] = None,
                               verbose: bool = True) -> List[Dict[str, Any]]:
    """Collect Binance forced-liquidation orders from the public stream.

    The REST `allForceOrders` endpoint now returns 404, so the
    WebSocket `!forceOrder@arr` stream is the source. It is a raw
    WebSocket, so this uses a minimal RFC-6455 client over a TLS
    socket - no third-party dependency, no install.

    This is a FORWARD-TESTING feed: it records forced selling as it
    happens, with a timestamp, a symbol, a side and a size, which is
    exactly the sample an exit rule needs to be judged against.
    """
    import base64
    import hashlib
    import socket
    import struct

    host = "fstream.binance.com"
    port = 443
    path = "/ws/!forceOrder@arr"
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
           f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
           f"User-Agent: Mozilla/5.0\r\n\r\n")

    rows: List[Dict[str, Any]] = []
    try:
        raw = socket.create_connection((host, port), timeout=30)
        ctx = _ctx()
        sock = ctx.wrap_socket(raw, server_hostname=host)
        sock.sendall(req.encode())
        buf = b""
        deadline = time.time() + seconds
        sock.settimeout(5.0)
        while time.time() < deadline:
            try:
                chunk = sock.recv(65536)
            except socket.timeout:
                continue
            except Exception:  # noqa: BLE001
                break
            if not chunk:
                break
            buf += chunk
            while True:
                # ---- decode a server frame ----
                if len(buf) < 2:
                    break
                b1, b2 = buf[0], buf[1]
                opcode = b1 & 0x0F
                masked = b2 & 0x80
                ln = b2 & 0x7F
                off = 2
                if ln == 126:
                    if len(buf) < 4:
                        break
                    ln = struct.unpack(">H", buf[2:4])[0]
                    off = 4
                elif ln == 127:
                    if len(buf) < 10:
                        break
                    ln = struct.unpack(">Q", buf[2:10])[0]
                    off = 10
                if masked:
                    off += 4
                if len(buf) < off + ln:
                    break
                payload = buf[off:off + ln]
                buf = buf[off + ln:]
                if opcode == 0x8:
                    # The server closed the stream. That is the END of
                    # the capture window, not a failure - Binance
                    # sends a close frame when the connection ages
                    # out. The rows collected so far are still valid.
                    if verbose:
                        print(f"  liquidation stream closed by the server "
                              f"after {len(rows)} orders", flush=True)
                    raise _StreamClosed()
                if opcode not in (0x1, 0x2):
                    continue
                try:
                    msg = json.loads(payload.decode())
                except Exception:  # noqa: BLE001
                    continue
                o = msg.get("o") or {}
                if not o:
                    continue
                rows.append({
                    "symbol": o.get("s"),
                    "side": o.get("S"),
                    "order_type": o.get("o"),
                    "time_in_force": o.get("f"),
                    "original_quantity": float(o.get("q") or 0),
                    "price": float(o.get("p") or 0),
                    "average_price": float(o.get("ap") or 0),
                    "order_status": o.get("X"),
                    "last_fill_quantity": float(o.get("l") or 0),
                    "trade_time": int(o.get("T") or 0),
                    "source": "binance/ws/!forceOrder@arr",
                })
        try:
            sock.close()
        except Exception:  # noqa: BLE001
            pass
    except _StreamClosed:
        pass
    except Exception as exc:  # noqa: BLE001
        if verbose:
            print(f"  liquidation stream failed: "
                  f"{type(exc).__name__}: {str(exc)[:140]}", flush=True)
    if out_path and rows:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, default=str) + "\n")
    return rows
