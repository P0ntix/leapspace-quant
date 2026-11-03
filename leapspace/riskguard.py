"""
Code-enforced kill switch + anomaly log (operator brief, quadrants 3 and 4).

QUADRANT 4 — UNKNOWN UNKNOWING (black-swan defence)
--------------------------------------------------
The brief asks for a kill switch the LLM CANNOT override: "If the portfolio
drops by X% in Y minutes, or if liquidity vanishes, the bot must halt all
trading immediately", and on an unprecedented market, "HALT, log the exact
market conditions, and convert this 'Unknown Unknowing' into a 'Known
Unknown' for future backtests".

THE CONTRACT
------------
`KillSwitch` is CODE-ENFORCED. Once it has halted, EVERY subsequent call to
`check()` returns `(False, reason)`. No prompt, string, `force=True`, env
var or "operator override" silently clears it. The only way out is
`reset(by=..., reason=...)`, which REQUIRES a named actor and a non-empty
reason and is written to the state log. Enforced STRUCTURALLY: the
authoritative flag is `KillSwitch._halted` (cleared only by `reset()`);
`KillSwitchState.halted = False` is written from exactly one place — inside
`reset()` — and the state is a guarded subclass whose `__setattr__` raises
`PermissionError` on any other attempt to clear it; and the halt is
PERSISTED to JSON, so a restarted process reloads it and does NOT resume
trading. `verify_no_bypass()` re-checks that against this module's own
source (AST-based) at runtime, so the guarantee is testable, not asserted.

QUADRANT 3 — UNKNOWN KNOWLEDGE
-------------------------------
The anomaly log is the other half: when the market does something that was
not anticipated, the exact market conditions are recorded, the bot halts,
and the incident is PROMOTED to a Known Unknown — a stored, replayable
condition snapshot that future backtests can be run against.

Provenance rules follow the rest of this package: every recorded condition
is the value that was observed, never an estimate; the rug-signal thresholds
are OPERATOR POLICY and are published in `RUG_SIGNAL_THRESHOLDS` with their
source, like `alerts.ALERT_THRESHOLDS` and `memecoin.THRESHOLDS`.
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import textwrap
from collections import deque
from dataclasses import asdict
from typing import Any, Deque, Dict, List, Optional, Sequence, Tuple

from .models import Anomaly, KillSwitchState, now_ts, to_json
from .provenance import read_json, write_json

# Defaults: the values in leapspace/data/operator_config.json's `kill_switch`
# block — OPERATOR POLICY, not market facts.
DEFAULT_MAX_DRAWDOWN_PCT = 0.20          # 20% drawdown from the window peak
DEFAULT_DRAWDOWN_WINDOW_SECONDS = 900    # 15 minutes
DEFAULT_MIN_LIQUIDITY_USD = 1_000.0
DEFAULT_MAX_SLIPPAGE_BPS = 500.0

STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
DEFAULT_STATE_PATH = os.path.join(STATE_DIR, "kill_switch.json")
DEFAULT_ANOMALY_PATH = os.path.join(STATE_DIR, "anomaly_log.json")
SEVERITIES = ("low", "medium", "high", "critical")

# Rug-signal thresholds — OPERATOR POLICY, published with their source.
RUG_SIGNAL_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    k: {"value": v, "source": s, "note": n} for k, v, s, n in (
        ("lp_removal_drop_pct", 0.50, "analyst_choice",
         "Liquidity gone when it drops by half or more vs the previous observation."),
        ("lp_removal_floor_usd", 1_000.0, "operator_config",
         "Same floor as kill_switch.min_liquidity_usd: the position cannot be exited."),
        ("liquidity_collapse_usd", 25_000.0, "memecoin.THRESHOLDS.min_liquidity_usd",
         "The meme-coin screen's minimum liquidity floor; exit quality fails below it."),
        ("liquidity_collapse_drop_pct", 0.30, "alerts.ALERT_THRESHOLDS.liquidity_drop_pct",
         "The alert layer's liquidity-decline band."),
        ("concentration_top_holder_pct", 20.0, "alerts.ALERT_THRESHOLDS.top_holder_pct",
         "Largest covered holder at or above this share is a structural reject."),
        ("concentration_jump_pct", 5.0, "analyst_choice",
         "A 5-point jump in the top holder's share between observations."),
        ("holder_collapse_pct", 0.50, "analyst_choice",
         "Holder count down by half or more between observations."),
        ("price_collapse_pct", -0.50, "alerts.ALERT_THRESHOLDS.drawdown_pct_hard",
         "A 50% single-interval collapse, matching the alert layer's hard band."),
    )}

def _t(key: str) -> Any:
    return RUG_SIGNAL_THRESHOLDS[key]["value"]

def _pct(value: Any) -> Optional[float]:
    """Normalise a percentage. Values above 1 are read as PERCENT (20 -> 0.20)."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v / 100.0 if abs(v) > 1.0 else v

def _flat_scalars(d: Any) -> Dict[str, Any]:
    """Flatten a mapping to scalars only; non-scalars become JSON strings."""
    out: Dict[str, Any] = {}
    for k, v in (d or {}).items():
        out[str(k)] = (v if isinstance(v, (str, int, float, bool)) or v is None
                       else json.dumps(v, sort_keys=True, default=str))
    return out

_CLEAR_SENTINEL = object()

class _GuardedKillState(KillSwitchState):
    """`KillSwitchState` whose `halted` flag can only be CLEARED by reset().

    Writing `halted = False` requires the internal clear token, held only
    for the duration of `KillSwitch.reset()`. Any other write — an operator
    script, a prompt handler, a stray assignment — raises `PermissionError`
    instead of silently resuming trading.
    """

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "halted" and value is False:
            if self.__dict__.get("_clear_token") is not _CLEAR_SENTINEL:
                raise PermissionError(
                    "the kill switch cannot be cleared here: `halted = False` "
                    "is writable only inside KillSwitch.reset(by=..., reason=...)")
        object.__setattr__(self, name, value)

    def __init__(self, **kwargs: Any) -> None:
        object.__setattr__(self, "_clear_token", _CLEAR_SENTINEL)
        try:
            super().__init__(**kwargs)
        finally:
            object.__setattr__(self, "_clear_token", None)

def _state_kwargs(st: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a persisted KillSwitchState payload into constructor kwargs."""
    return {"halted": bool(st.get("halted")), "reason": st.get("reason") or "",
            "trigger": st.get("trigger") or "",
            "triggered_at": int(st.get("triggered_at") or 0),
            "peak_equity_usd": st.get("peak_equity_usd"),
            "equity_usd": st.get("equity_usd"), "drawdown_pct": st.get("drawdown_pct"),
            "reset_by": st.get("reset_by") or "", "reset_reason": st.get("reset_reason") or "",
            "reset_at": int(st.get("reset_at") or 0),
            "state_log": list(st.get("state_log") or [])}

def _anomaly_from_dict(r: Dict[str, Any]) -> Anomaly:
    """Rebuild an Anomaly from its persisted dict."""
    return Anomaly(kind=r.get("kind") or "unknown", chain=r.get("chain") or "",
                   token=r.get("token") or "", symbol=r.get("symbol") or "",
                   ts=int(r.get("ts") or 0), severity=r.get("severity") or "medium",
                   description=r.get("description") or "",
                   market_state=r.get("market_state") or {},
                   action_taken=r.get("action_taken") or "",
                   promoted_to_known_unknown=bool(r.get("promoted_to_known_unknown")),
                   lesson=r.get("lesson") or "", provenance=r.get("provenance") or "LIVE")

class KillSwitch:
    """CODE-ENFORCED trading halt. The LLM cannot override this.

    `check()` returns `(allowed, reason)`. `allowed` is False whenever the
    switch is halted, for ANY reason, until `reset(by=..., reason=...)` is
    called with an actor and a non-empty reason. The drawdown rule is
    measured against the PEAK equity inside a ROLLING window of
    `drawdown_window_seconds` — "drops by X% in Y minutes".
    """

    def __init__(self, cfg: Optional[Dict[str, Any]] = None, *,
                 max_drawdown_pct: Optional[float] = None,
                 drawdown_window_seconds: Optional[int] = None,
                 min_liquidity_usd: Optional[float] = None,
                 max_slippage_bps: Optional[float] = None,
                 token_rules: Optional[Dict[str, Dict[str, Any]]] = None,
                 state_path: Optional[str] = None) -> None:
        conf = dict(cfg or {})

        def pick(arg: Any, key: str, default: Any) -> Any:
            return arg if arg is not None else conf.get(key, default)

        self.max_drawdown_pct = _pct(pick(max_drawdown_pct, "max_drawdown_pct",
                                          DEFAULT_MAX_DRAWDOWN_PCT))
        self.drawdown_window_seconds = int(
            pick(drawdown_window_seconds, "drawdown_window_seconds",
                 DEFAULT_DRAWDOWN_WINDOW_SECONDS))
        self.min_liquidity_usd = float(
            pick(min_liquidity_usd, "min_liquidity_usd", DEFAULT_MIN_LIQUIDITY_USD))
        self.max_slippage_bps = float(
            pick(max_slippage_bps, "max_slippage_bps", DEFAULT_MAX_SLIPPAGE_BPS))
        self.token_rules: Dict[str, Dict[str, Any]] = dict(
            token_rules or conf.get("token_rules") or {})
        self.state_path = state_path or conf.get("state_path") or DEFAULT_STATE_PATH
        self.state = _GuardedKillState()
        self._halted = False
        self._window: Deque[Tuple[int, float]] = deque()

    # -- internals ---------------------------------------------------------
    def _rules_for(self, token: Optional[str]) -> Dict[str, Optional[float]]:
        rules = {"max_drawdown_pct": self.max_drawdown_pct,
                 "min_liquidity_usd": self.min_liquidity_usd,
                 "max_slippage_bps": self.max_slippage_bps}
        if token:
            over = self.token_rules.get(token) or {}
            for k in rules:
                if over.get(k) is not None:
                    rules[k] = (_pct(over[k]) if k == "max_drawdown_pct" else float(over[k]))
        return rules

    def _push(self, ts: int, equity: float) -> Optional[float]:
        """Append an equity sample, drop expired ones, return the peak."""
        self._window.append((int(ts), float(equity)))
        cutoff = int(ts) - int(self.drawdown_window_seconds)
        while self._window and self._window[0][0] < cutoff:
            self._window.popleft()
        return max((e for _, e in self._window), default=None)

    def _log(self, line: str) -> None:
        self.state.state_log.append(line)

    def _halt_message(self) -> str:
        return (f"HALTED ({self.state.trigger or 'unknown trigger'}): "
                f"{self.state.reason or 'no reason recorded'} "
                f"[triggered_at={self.state.triggered_at}; "
                f"clearing requires reset(by=..., reason=...)]")

    def _trip(self, reason: str, trigger: str, ts: int) -> Tuple[bool, str]:
        self.halt(reason=reason, trigger=trigger, ts=ts)
        return False, reason

    # -- public API --------------------------------------------------------
    def check(self, equity_usd: Optional[float], ts: int,
              liquidity_usd: Optional[float] = None, token: Optional[str] = None,
              slippage_bps: Optional[float] = None) -> Tuple[bool, str]:
        """May we trade right now? Returns `(allowed, reason)`. `reason` is
        empty when allowed; when blocked it names the rule and the numbers."""
        # THE GATE. Everything below this line is unreachable while halted.
        if self._halted or self.state.halted:
            return False, self._halt_message()

        ts = int(ts)
        rules = self._rules_for(token)
        why = f" for {token}" if token else ""

        if equity_usd is not None:
            equity = float(equity_usd)
            peak = self._push(ts, equity)
            if peak and peak > 0:
                dd = (peak - equity) / peak
                self.state.peak_equity_usd = peak
                self.state.equity_usd = equity
                self.state.drawdown_pct = dd
                limit = rules["max_drawdown_pct"]
                if limit is not None and dd > limit:
                    return self._trip(f"drawdown {dd:.2%} from the window peak "
                                      f"${peak:,.2f} to ${equity:,.2f} exceeds "
                                      f"the {limit:.2%} limit{why}",
                                      "max_drawdown_pct", ts)

        floor = rules["min_liquidity_usd"]
        if liquidity_usd is not None and floor is not None \
                and float(liquidity_usd) < floor:
            return self._trip(f"liquidity ${float(liquidity_usd):,.2f} is below "
                              f"the ${floor:,.2f} floor{why}",
                              "min_liquidity_usd", ts)

        cap = rules["max_slippage_bps"]
        if slippage_bps is not None and cap is not None \
                and float(slippage_bps) > cap:
            return self._trip(f"observed slippage {float(slippage_bps):,.1f}bps "
                              f"exceeds the {cap:,.1f}bps cap{why}",
                              "max_slippage_bps", ts)
        return True, ""

    def halt(self, reason: str, trigger: str,
             ts: Optional[int] = None) -> KillSwitchState:
        """Halt trading. Idempotent; the FIRST reason is the one kept."""
        ts = int(ts if ts is not None else now_ts())
        first = not self._halted
        self._halted = True
        self.state.halted = True
        if first:
            self.state.reason = reason
            self.state.trigger = trigger
            self.state.triggered_at = ts
            self._log(f"{ts} HALT trigger={trigger} reason={reason}")
        else:
            self._log(f"{ts} HALT (already halted) trigger={trigger} reason={reason}")
        return self.state

    def reset(self, by: str, reason: str, ts: Optional[int] = None,
              equity_usd: Optional[float] = None) -> KillSwitchState:
        """Clear the halt. REQUIRES an actor and a non-empty reason.

        No default, no fallback, no "reset everything" shortcut. The clear is
        logged with actor and reason, and the drawdown window is re-baselined.
        """
        if not isinstance(by, str) or not by.strip():
            raise ValueError("reset() requires an actor (`by`); a halt cannot "
                             "be cleared anonymously or by a model")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reset() requires a non-empty reason; a halt "
                             "cannot be cleared silently")
        ts = int(ts if ts is not None else now_ts())
        was_halted = self._halted
        self._halted = False
        object.__setattr__(self.state, "_clear_token", _CLEAR_SENTINEL)
        try:
            self.state.halted = False
        finally:
            object.__setattr__(self.state, "_clear_token", None)
        self.state.reset_by = by.strip()
        self.state.reset_reason = reason.strip()
        self.state.reset_at = ts
        self._log(f"{ts} RESET by={by.strip()} reason={reason.strip()}"
                  + ("" if was_halted else " (switch was not halted)"))
        # Re-baseline the drawdown window from the reset point.
        self._window.clear()
        if equity_usd is not None:
            self._push(ts, float(equity_usd))
            self.state.equity_usd = float(equity_usd)
            self.state.peak_equity_usd = float(equity_usd)
            self.state.drawdown_pct = 0.0
        return self.state

    # -- persistence -------------------------------------------------------
    def to_flat(self) -> Dict[str, Any]:
        flat = self.state.to_flat()
        flat.update({"max_drawdown_pct": self.max_drawdown_pct,
                     "drawdown_window_seconds": self.drawdown_window_seconds,
                     "min_liquidity_usd": self.min_liquidity_usd,
                     "max_slippage_bps": self.max_slippage_bps,
                     "state_path": self.state_path,
                     "state_log_entries": len(self.state.state_log)})
        return flat

    def save(self, path: Optional[str] = None) -> str:
        """Persist the halt so a restarted process does NOT resume trading."""
        path = path or self.state_path
        write_json(path, {"schema": 1, "saved_at": now_ts(), "config": {
            "max_drawdown_pct": self.max_drawdown_pct,
            "drawdown_window_seconds": self.drawdown_window_seconds,
            "min_liquidity_usd": self.min_liquidity_usd,
            "max_slippage_bps": self.max_slippage_bps,
            "token_rules": self.token_rules},
            "state": asdict(self.state),
            "window": [[ts, eq] for ts, eq in self._window]})
        return path

    def load(self, path: Optional[str] = None) -> bool:
        """Reload a persisted halt. True when a state file was read.

        A MISSING file is a clean start. A CORRUPT file fails CLOSED: we
        cannot prove trading was allowed, so we do not assume it was.
        """
        path = path or self.state_path
        blob = read_json(path, None)
        if blob is None:
            if os.path.exists(path):
                self.halt(f"persisted state at {path} is unreadable — failing "
                          "closed rather than assuming trading was allowed",
                          "state_unreadable")
                self._log(f"{now_ts()} LOAD failed-closed (unreadable state file)")
                return False
            return False
        self.state = _GuardedKillState(**_state_kwargs(blob.get("state") or {}))
        self._halted = bool(self.state.halted)
        self._window.clear()
        for ts, eq in (blob.get("window") or []):
            try:
                self._window.append((int(ts), float(eq)))
            except (TypeError, ValueError):
                continue
        self._log(f"{now_ts()} LOAD halted={self._halted} from {path}")
        return True

    # -- structural self-check --------------------------------------------
    def verify_no_bypass(self) -> Dict[str, Any]:
        """Prove the 'cannot be overridden' claim against this module's source.

        AST-based, not a text grep, so a docstring that merely MENTIONS
        `halted = False` cannot pass or fail the audit: every write of
        `halted = False` must live in `reset()`, `_halted` may only be
        cleared in `reset()`/`__init__`, and no method may expose a
        `force`-style bypass parameter.
        """
        violations: List[str] = []
        writes: List[str] = []
        private_writes: List[str] = []
        tree = ast.parse(textwrap.dedent(inspect.getsource(KillSwitch)))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for sub in ast.walk(node):
                tg = ([*sub.targets] if isinstance(sub, ast.Assign)
                      else [sub.target] if isinstance(sub, ast.AnnAssign) else [])
                for tgt in tg:
                    if not isinstance(tgt, ast.Attribute):
                        continue
                    if not isinstance(sub.value, ast.Constant) or sub.value.value is not False:
                        continue
                    where = f"{node.name}: {ast.unparse(sub)}"
                    if tgt.attr == "halted":
                        writes.append(where)
                        if node.name != "reset":
                            violations.append(f"`halted = False` outside reset() -> {where}")
                    elif tgt.attr == "_halted":
                        private_writes.append(where)
                        if node.name not in ("reset", "__init__"):
                            violations.append(f"`_halted = False` outside reset() -> {where}")
        if len(writes) != 1:
            violations.append(f"expected exactly 1 `halted = False` write, found {len(writes)}")
        for nm in ("check", "halt", "reset"):
            bad = [x for x in inspect.signature(getattr(KillSwitch, nm)).parameters
                   if x.lower() in ("force", "override", "bypass")]
            if bad:
                violations.append(f"{nm}() exposes a bypass parameter: {bad}")
        return {"ok": not violations, "writes": writes,
                "private_flag_writes": private_writes, "violations": violations}

def state_json(ks: KillSwitch) -> str:
    """Flat JSON of the switch state, for the flattener."""
    return to_json(ks.state)

class AnomalyLog:
    """Record unprecedented market conditions and promote them to Known Unknowns.

    An anomaly stores the EXACT market conditions observed (a flat dict of
    scalars) so the incident can be replayed; promotion adds a lesson and
    makes it a Known Unknown for future backtests.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or DEFAULT_ANOMALY_PATH
        self.anomalies: List[Anomaly] = []
        self.known_unknowns: List[Dict[str, Any]] = []

    # -- persistence -------------------------------------------------------
    def load(self, path: Optional[str] = None) -> bool:
        path = path or self.path
        blob = read_json(path, None)
        if not blob:
            return False
        self.anomalies = [_anomaly_from_dict(r) for r in (blob.get("anomalies") or [])]
        self.known_unknowns = list(blob.get("known_unknowns") or [])
        return True

    def save(self, path: Optional[str] = None) -> str:
        path = path or self.path
        write_json(path, {"schema": 1, "saved_at": now_ts(),
                          "anomalies": [asdict(a) for a in self.anomalies],
                          "known_unknowns": self.known_unknowns})
        return path

    # -- recording ---------------------------------------------------------
    def record(self, kind: str, description: str, market_state: Dict[str, Any],
               severity: str = "medium", action_taken: str = "", chain: str = "",
               token: str = "", symbol: str = "",
               ts: Optional[int] = None) -> Anomaly:
        """Log one anomaly with the exact market conditions that produced it."""
        sev = (severity or "medium").lower()
        anom = Anomaly(kind=kind or "unknown", chain=chain or "", token=token or "",
                       symbol=symbol or "", ts=int(ts if ts is not None else now_ts()),
                       severity=sev if sev in SEVERITIES else "medium",
                       description=description or "",
                       market_state=_flat_scalars(market_state),
                       action_taken=action_taken or "",
                       promoted_to_known_unknown=False, lesson="", provenance="LIVE")
        self.anomalies.append(anom)
        return anom

    def promote_to_known_unknown(self, anomaly: Anomaly,
                                 lesson: str) -> Dict[str, Any]:
        """Convert an Unknown Unknowing into a replayable Known Unknown."""
        if not isinstance(anomaly, Anomaly):
            raise TypeError("promote_to_known_unknown expects an Anomaly")
        if not isinstance(lesson, str) or not lesson.strip():
            raise ValueError("a Known Unknown must carry a lesson")
        anomaly.promoted_to_known_unknown = True
        anomaly.lesson = lesson.strip()
        ku = {"kind": anomaly.kind, "lesson": anomaly.lesson, "ts": anomaly.ts,
              "severity": anomaly.severity, "description": anomaly.description,
              "action_taken": anomaly.action_taken, "chain": anomaly.chain,
              "token": anomaly.token, "symbol": anomaly.symbol,
              "market_state": dict(anomaly.market_state or {}),
              "provenance": anomaly.provenance}
        self.known_unknowns.append(ku)
        return ku

    # -- replay ------------------------------------------------------------
    @staticmethod
    def _series(price_series: Any) -> List[Tuple[int, float]]:
        out: List[Tuple[int, float]] = []
        if not price_series:
            return out
        if isinstance(price_series, dict):
            items = list(price_series.values())[0] if price_series else []
        else:
            items = price_series
        for i, row in enumerate(items):
            if isinstance(row, dict):
                px = row.get("px", row.get("price", row.get("close")))
                ts = row.get("ts", row.get("date", i))
            elif isinstance(row, (list, tuple)) and len(row) >= 2:
                ts, px = row[0], row[1]
            else:
                ts, px = i, row
            try:
                out.append((int(ts), float(px)))
            except (TypeError, ValueError):
                continue
        out.sort(key=lambda kv: kv[0])
        return out

    def replay_known_unknowns(self, price_series: Any) -> List[Dict[str, Any]]:
        """Scan a price series for the recorded conditions.

        One flat record per Known Unknown: conditions derivable from a price
        series report where they WOULD have fired; the rest are reported
        `not_assessable` rather than quietly ignored.
        """
        series = self._series(price_series)
        results: List[Dict[str, Any]] = []
        for ku in self.known_unknowns:
            state = ku.get("market_state") or {}
            matches: List[Dict[str, Any]] = []
            assessed: List[str] = []
            not_assessable: List[str] = []

            dd_cond = state.get("drawdown_pct")
            if isinstance(dd_cond, (int, float)):
                assessed.append("drawdown_pct")
                peak = None
                for ts, px in series:
                    peak = px if peak is None else max(peak, px)
                    if peak and peak > 0 and (peak - px) / peak >= abs(float(dd_cond)):
                        matches.append({"ts": ts, "px": px, "drawdown_pct": (peak - px) / peak})
            chg_cond = state.get("price_change_pct")
            if isinstance(chg_cond, (int, float)):
                assessed.append("price_change_pct")
                win = max(1, int(state.get("change_window_bars") or 1))
                for i in range(win, len(series)):
                    ts, px = series[i]
                    base = series[i - win][1]
                    if base and px / base - 1.0 <= float(chg_cond):
                        matches.append({"ts": ts, "px": px, "price_change_pct": px / base - 1.0})
            for k in ("liquidity_usd", "holder_count", "top_holder_pct",
                      "slippage_bps", "volume_usd"):
                if k in state:
                    not_assessable.append(k)

            status = ("not_assessable_from_price_series" if not assessed else
                      "would_have_fired" if matches else "did_not_fire")
            results.append({
                "kind": ku.get("kind") or "", "lesson": ku.get("lesson") or "",
                "status": status, "n_matches": len(matches),
                "first_match_ts": matches[0]["ts"] if matches else None,
                "first_match_px": matches[0]["px"] if matches else None,
                "matches": matches[:20],
                "conditions_assessed": ",".join(assessed),
                "conditions_not_assessable": ",".join(not_assessable),
                "series_points": len(series)})
        return results

    def to_flat(self) -> Dict[str, Any]:
        return {"anomalies": [a.to_flat() for a in self.anomalies],
                "known_unknowns": list(self.known_unknowns),
                "n_anomalies": len(self.anomalies),
                "n_known_unknowns": len(self.known_unknowns), "path": self.path}

def _get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)

def _drop(now: Any, prev: Any) -> Optional[float]:
    """Fractional fall from `prev` to `now`, or None if not computable."""
    if now is None or not prev:
        return None
    try:
        return 1.0 - float(now) / float(prev)
    except (TypeError, ValueError, ZeroDivisionError):
        return None

def rug_signal_details(token_state: Any) -> List[Dict[str, Any]]:
    """Structured rug signals for one token's live state.

    `token_state` is a mapping (or a `TokenCandidate`) carrying any of:
    liquidity_usd(_prev), holders(_prev), top_holder_pct(_prev),
    price_change_pct, lp_removed, lp_burned.
    """
    out: List[Dict[str, Any]] = []
    liq = _get(token_state, "liquidity_usd")
    liq_prev = _get(token_state, "liquidity_usd_prev")
    holders = _get(token_state, "holders", _get(token_state, "holder_count"))
    holders_prev = _get(token_state, "holders_prev")
    top = _get(token_state, "top_holder_pct")
    top_prev = _get(token_state, "top_holder_pct_prev")
    chg = _get(token_state, "price_change_pct")
    explicit_lp = bool(_get(token_state, "lp_removed") or
                       _get(token_state, "lp_burned") or
                       (_get(token_state, "lp_usd_removed") or 0) > 0)
    drop_pct = _drop(liq, liq_prev)
    hdrop = _drop(holders, holders_prev)

    def add(flag: str, sev: str, ev: str, thr: str) -> None:
        out.append({"flag": flag, "severity": sev, "evidence": ev, "threshold": thr})

    if explicit_lp or (drop_pct is not None and drop_pct >= _t("lp_removal_drop_pct")) \
            or (liq is not None and float(liq) < _t("lp_removal_floor_usd")):
        add("lp_removal", "critical",
            f"lp_removed={explicit_lp} liquidity={liq} prev_liquidity={liq_prev} drop={drop_pct}",
            f"explicit LP removal, or liquidity drop >= {_t('lp_removal_drop_pct'):.0%}, "
            f"or liquidity < ${_t('lp_removal_floor_usd'):,.0f}")

    if liq is not None and (float(liq) < _t("liquidity_collapse_usd") or
                            (drop_pct is not None and
                             drop_pct >= _t("liquidity_collapse_drop_pct"))):
        add("liquidity_collapse", "critical",
            f"liquidity=${float(liq):,.2f} prev=${liq_prev} drop={drop_pct}",
            f"liquidity < ${_t('liquidity_collapse_usd'):,.0f} or "
            f"drop >= {_t('liquidity_collapse_drop_pct'):.0%}")

    if top is not None:
        top_f = float(top)
        jump = None
        if top_prev is not None:
            try:
                jump = top_f - float(top_prev)
            except (TypeError, ValueError):
                jump = None
        if top_f >= _t("concentration_top_holder_pct") or \
                (jump is not None and jump >= _t("concentration_jump_pct")):
            add("concentration_spike", "high",
                f"top_holder_pct={top_f:.2f}% prev={top_prev} jump={jump}",
                f"top holder >= {_t('concentration_top_holder_pct'):.0f}% or a jump "
                f">= {_t('concentration_jump_pct'):.0f} points")

    if hdrop is not None and hdrop >= _t("holder_collapse_pct"):
        add("holder_collapse", "high",
            f"holders={holders} prev={holders_prev} drop={hdrop:.2f}",
            f"holder count drop >= {_t('holder_collapse_pct'):.0%}")

    if chg is not None and float(chg) <= _t("price_collapse_pct"):
        add("price_collapse", "critical", f"price_change_pct={float(chg):.2%}",
            f"price change <= {_t('price_collapse_pct'):.0%}")
    return out

def detect_rug_signals(token_state: Any) -> List[str]:
    """Risk flags for one token's live state, shaped to drop straight into
    `models.TokenCandidate.risk_flags`."""
    return [d["flag"] for d in rug_signal_details(token_state)]

# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------
def _selftest() -> int:
    import shutil
    import tempfile

    ok = True
    results: List[Tuple[str, bool, str]] = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        ok = ok and bool(cond)
        results.append((label, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="leapspace_riskguard_")
    try:
        path = os.path.join(tmp, "kill_switch.json")
        cfg = {"max_drawdown_pct": 0.20, "drawdown_window_seconds": 900,
               "min_liquidity_usd": 1_000.0, "max_slippage_bps": 500.0}
        ks = KillSwitch(cfg=cfg, state_path=path)

        # 1. Normal operation permits trading.
        allowed, reason = ks.check(100_000.0, 1_000)
        check("trading allowed at t=1000", allowed, reason)
        allowed, reason = ks.check(95_000.0, 1_100)      # -5% from peak
        check("trading allowed at -5%", allowed, reason)

        # 2. The switch FIRES on a 20% drawdown inside the window.
        allowed, reason = ks.check(75_000.0, 1_200)      # -25% from peak
        check("trading blocked on -25% drawdown", not allowed, reason)
        check("state.halted is True", ks.state.halted)
        check("trigger recorded", ks.state.trigger == "max_drawdown_pct", ks.state.trigger)

        # 3. Once halted, EVERY subsequent check is blocked.
        for eq, ts in ((75_000.0, 1_300), (200_000.0, 1_400), (1.0, 1_500)):
            allowed, reason = ks.check(eq, ts, liquidity_usd=1_000_000.0)
            check(f"blocked at equity={eq}", not allowed, reason[:70])

        # 4. There is NO bypass: state.halted = False is refused.
        try:
            ks.state.halted = False
            check("direct state write refused", False, "it was ALLOWED")
        except PermissionError as exc:
            check("direct state write refused", True, str(exc)[:90])
        check("authoritative flag still halted", ks._halted and ks.state.halted)
        for bad in ({"by": "", "reason": "because"}, {"by": "me", "reason": ""}):
            try:
                ks.reset(**bad)
                check(f"reset({bad}) refused", False, "it was ALLOWED")
            except ValueError as exc:
                check(f"reset({bad}) refused", True, str(exc)[:70])

        # 5. The halt SURVIVES a process restart (persist + reload).
        ks.save()
        ks2 = KillSwitch(state_path=path)
        check("state file reloaded", ks2.load())
        check("reloaded switch is HALTED", ks2.state.halted and ks2._halted)
        allowed, reason = ks2.check(500_000.0, 9_999, liquidity_usd=10_000_000.0)
        check("restarted bot does NOT resume trading", not allowed, reason[:90])

        # 6. Only an explicit reset(by, reason) clears it.
        ks2.reset(by="operator:risk-desk", reason="post-incident review signed off")
        allowed, reason = ks2.check(500_000.0, 10_000)
        check("trading allowed after explicit reset", allowed, reason)
        check("reset actor recorded", ks2.state.reset_by == "operator:risk-desk")
        check("reset reason recorded", bool(ks2.state.reset_reason))
        check("reset in the state log",
              any("RESET by=operator:risk-desk" in ln for ln in ks2.state.state_log))

        # 7. Structural verification of the 'cannot be overridden' claim.
        v = ks2.verify_no_bypass()
        check("verify_no_bypass() clean", v["ok"], str(v["violations"]))
        check("one `halted = False` write, inside reset()",
              len(v["writes"]) == 1, str(v["writes"]))

        # 8. Liquidity and slippage rules also fire.
        loose = dict(cfg, max_drawdown_pct=0.5)
        allowed, reason = KillSwitch(cfg=loose).check(100_000.0, 2_000, liquidity_usd=500.0)
        check("liquidity floor blocks trading", not allowed, reason[:80])
        allowed, reason = KillSwitch(cfg=loose).check(
            100_000.0, 2_000, liquidity_usd=50_000.0, slippage_bps=900.0)
        check("slippage cap blocks trading", not allowed, reason[:80])

        # 9. Anomaly log: record, promote, replay.
        log = AnomalyLog(path=os.path.join(tmp, "anomalies.json"))
        anom = log.record(
            kind="liquidity_vanished",
            description="DEX pool emptied within one block; price printed "
                        "-92% against a stale quote",
            market_state={"liquidity_usd": 0.0, "drawdown_pct": -0.92,
                          "price_change_pct": -0.92, "change_window_bars": 1,
                          "holder_count": 41, "top_holder_pct": 61.5},
            severity="critical",
            action_taken="HALT — all trading stopped, positions frozen")
        check("anomaly recorded", anom.ts > 0 and anom.severity == "critical")
        check("market conditions captured exactly",
              anom.market_state.get("liquidity_usd") == 0.0
              and anom.market_state.get("top_holder_pct") == 61.5)
        ku = log.promote_to_known_unknown(
            anom, lesson="A pool that empties in one block is a rug, not a "
                         "sell-off: never quote an exit price from a dead pool.")
        check("promoted to Known Unknown", ku["lesson"].startswith("A pool"))
        check("Known Unknown keeps the condition snapshot",
              ku["market_state"].get("drawdown_pct") == -0.92)
        # A synthetic price series: 100 -> 8 in two steps (a -92% collapse).
        replay = log.replay_known_unknowns([(1_000, 100.0), (2_000, 8.0)])
        check("replay reports the anomaly would have fired",
              replay and replay[0]["status"] == "would_have_fired",
              replay[0]["status"] if replay else "no replay")
        check("replay flags conditions a price series cannot assess",
              "liquidity_usd" in replay[0]["conditions_not_assessable"])
        log.save()
        log2 = AnomalyLog(path=os.path.join(tmp, "anomalies.json"))
        log2.load()
        check("anomaly log survives a restart",
              len(log2.anomalies) == 1 and len(log2.known_unknowns) == 1)

        # 10. Rug signals.
        flags = detect_rug_signals({"liquidity_usd": 400.0,
                                    "liquidity_usd_prev": 90_000.0,
                                    "holders": 20, "holders_prev": 900,
                                    "top_holder_pct": 71.0,
                                    "top_holder_pct_prev": 12.0,
                                    "price_change_pct": -0.93})
        for want in ("lp_removal", "liquidity_collapse", "concentration_spike",
                     "holder_collapse", "price_collapse"):
            check(f"{want} flagged", want in flags, str(flags))
        clean = detect_rug_signals({"liquidity_usd": 250_000.0,
                                    "liquidity_usd_prev": 260_000.0,
                                    "holders": 5_000, "holders_prev": 4_900,
                                    "top_holder_pct": 8.0, "top_holder_pct_prev": 8.1,
                                    "price_change_pct": 0.02})
        check("a healthy token produces no flags", clean == [], str(clean))

        print("=" * 72)
        print("RISKGUARD SELF-TEST — code-enforced kill switch + anomaly log")
        print("=" * 72)
        for label, cond, detail in results:
            print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
        print("\n" + "=" * 72)
        print("RESULT: " + ("ALL CHECKS PASSED" if ok else "FAILURES PRESENT"))
        print("=" * 72)
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    raise SystemExit(_selftest())
