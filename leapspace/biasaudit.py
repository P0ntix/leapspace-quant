"""
Bias auditor — look-ahead, survivorship and overfitting (operator brief,
quadrant 3: UNKNOWN KNOWLEDGE).

The operator brief asks, of any strategy this package analyses:

    "Look-Ahead Bias: is the backtest accidentally using future price data?"
    "Survivorship Bias: is the backtest only looking at tokens that reached
     millions in market cap, ignoring the 95% that failed immediately?"
    "Overfitting: are the rules too specific to past data (e.g. 'buy at
     exactly $42,102 MC')?"
    "Periodically re-evaluate the 'Trusted Wallet Pool' — an alpha wallet
     today might become a 'cabal' wallet tomorrow."

This module answers those questions about SPECS and about stored backtest
RESULTS. Three things make it honest rather than decorative:

1. **It audits the real artifacts.** `audit_spec()` reads an actual spec
   dict; `audit_backtest_results()` reads `reports/backtest_results.json`.
   The findings are about THIS package's own specs, including the
   unflattering ones.

2. **It can return CLEAN.** A spec with causal features, a survivorship-
   safe universe and round parameters produces no findings. The auditor
   is not rigged to fail everything — the self-test proves it catches a
   deliberately look-ahead-biased spec AND passes a clean one.

3. **Look-ahead is checked structurally, not just by keyword.** The engine
   (`strategy-backtest-lab`) enforces `features[t]` uses only data at
   indices <= t, and `btvalidate.causality_audit()` re-computes features on
   a truncated panel to prove it. This module checks the parts that audit
   CANNOT reach: the spec's own parameters, and the regime path in
   `leapspace/backtest.py`, where the HMM is fitted on the whole panel
   (in-sample classification — disclosed, but a real limit on the
   out-of-sample claim).

THE THREE KINDS

look_ahead    the strategy can see data it could not have seen at decision
              time (a negative lookback, a forward/shift field, a signal
              reading a field that does not exist at t, in-sample parameter
              fitting).

survivorship  the universe is chosen with hindsight — today's survivors.
              A universe built from assets that are still trading in 2026
              IS a survivorship-biased universe, even when every asset in
              it is an index ETF.

overfitting  the rules are too specific to the sample they were fitted on:
              thresholds with many significant digits, hard-coded token
              addresses, non-round lookbacks, or many variants tried
              against one outcome.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .models import BiasFinding, to_json

# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------
# A parameter name that implies the value is taken from the FUTURE.
FORWARD_PARAM_NAMES = ("shift", "forward", "future", "lead", "ahead",
                       "next_bar", "next_day", "t_plus", "future_", "_future")

# Feature/signal names that would be leaks if a spec ever asked for them.
KNOWN_LEAKY_NAMES = ("future_return", "forward_return", "next_return",
                     "future_price", "forward_price", "t1_return",
                     "next_bar_return", "lead_return")

# A hard-coded token address: 0x + 40 hex (EVM) or a long base58 mint.
RE_EVM_ADDRESS = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
RE_BASE58_MINT = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

# Non-round lookbacks: 20, 30, 60, 252 are conventional; 47 or 63 is not.
CONVENTIONAL_LOOKBACKS = {5, 10, 14, 20, 21, 30, 40, 50, 60, 63, 90, 100, 120, 126, 180, 200, 252}

# --------------------------------------------------------------------------
# The engine's universe presets, and what they actually contain.
#
# Copied from the engine's `UNIVERSE_PRESETS` (btengine.py) because the
# auditor must know WHICH assets a preset holds to judge survivorship.
# The engine is the authority; these are the four presets this package's
# 13 specs use.
# --------------------------------------------------------------------------
PRESET_MEMBERS: Dict[str, List[str]] = {
    "us_equity_broad": ["SPY", "VTI", "IVV", "RSP"],
    "us_equity_style": ["SPY", "IWM", "MDY", "RSP", "QQQ", "DIA"],
    "us_equity_sector": ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP",
                         "XLRE", "XLU", "XLV", "XLY"],
    "crypto": ["BTC-USD", "ETH-USD", "LTC-USD", "BCH-USD", "XRP-USD",
               "SOL-USD", "ADA-USD", "DOGE-USD", "AVAX-USD", "LINK-USD"],
}

# Presets whose membership is a set of SURVIVORS chosen with hindsight.
#
# The two cases are NOT the same severity, and the auditor does not treat
# them as if they were:
#
#   * `crypto` is the severe case. Its ten members are individual tokens
#     that CAN die: every coin that launched in the same window and failed
#     is absent by construction, so a strategy measured on this basket is
#     measured on the survivors only.
#   * The ETF presets are wrappers that track an index; the wrapper itself
#     does not fail, and the index provider reconstitutes its membership.
#     The exposure is real but weaker — the SET of funds was still chosen
#     with hindsight, and funds that were closed or merged are excluded.
#
# The severity reflects that difference.
SURVIVORSHIP_PRONE_PRESETS: Dict[str, Dict[str, str]] = {
    "crypto": {
        "severity": "high",
        "text": ("The 10 members are individual tokens that CAN fail. They "
                 "are the coins that are large and liquid TODAY; every token "
                 "that launched in the same window and failed is absent by "
                 "construction, so a strategy measured on this basket is "
                 "measured on the survivors only."),
    },
    "us_equity_broad": {
        "severity": "low",
        "text": ("Four index-tracking ETFs. The wrappers do not die and the "
                 "index provider reconstitutes their membership, so the "
                 "exposure is weaker than for individual assets — but the "
                 "SET of funds was still chosen with hindsight, and funds "
                 "that were closed or merged are excluded."),
    },
    "us_equity_style": {
        "severity": "low",
        "text": ("Six index-tracking ETFs chosen with hindsight about which "
                 "style funds survived and carried a full history. The "
                 "wrappers do not die; the SET selection does exclude funds "
                 "that no longer exist."),
    },
    "us_equity_sector": {
        "severity": "low",
        "text": ("Eleven SPDR sector ETFs. The wrappers do not die, but the "
                 "SET is today's surviving sector funds, and two of them "
                 "(XLC, XLRE) only start in 2018/2015, so the panel is "
                 "shorter and unbalanced at the start."),
    },
}

def _significant_digits(x: float) -> int:
    """Number of significant digits in a float, ignoring trailing zeros."""
    if x == 0:
        return 1
    s = f"{x:.12g}".replace("-", "").replace(".", "").lstrip("0")
    return len(s.rstrip("0")) or 1

def _walk_params(obj: Any, path: str = "") -> Iterable[Tuple[str, Any]]:
    """Yield (dotted_path, value) for every scalar in a nested structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_params(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _walk_params(v, f"{path}[{i}]")
    else:
        yield path, obj

def _strings(obj: Any) -> Iterable[str]:
    """Yield every string in a nested structure."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _strings(v)
    elif isinstance(obj, str):
        yield obj

# --------------------------------------------------------------------------
# LOOK-AHEAD
# --------------------------------------------------------------------------
def _audit_look_ahead(spec: Dict[str, Any], name: str) -> List[BiasFinding]:
    out: List[BiasFinding] = []
    features = spec.get("features") or []
    signal = spec.get("signal") or {}
    sig_params = signal.get("params") or {}

    # 1. A feature with a negative lookback reads BEFORE the series starts.
    for feat in features:
        fname = feat.get("name") or "?"
        params = feat.get("params") or {}
        for key in ("lookback", "window", "lookahead", "lag"):
            v = params.get(key)
            if isinstance(v, (int, float)) and v < 0:
                out.append(BiasFinding(
                    kind="look_ahead", severity="high",
                    where=f"{name}: features[{fname}].params.{key}",
                    detail=(f"'{key}' is {v} — a negative window reaches "
                            f"BACKWARDS from the decision bar, so the feature "
                            f"reads data that does not exist yet at t."),
                    evidence=f"features[].name={fname} params.{key}={v}",
                    recommendation=("Use a positive lookback; if the intent was "
                                    "to skip the most recent bars use `skip`, "
                                    "which the engine applies inside the "
                                    "window rather than before it.")))

        # 2. A forward-looking parameter name.
        for ppath, pval in _walk_params(params, f"features[{fname}].params"):
            leaf = ppath.split(".")[-1].lower()
            if any(tok in leaf for tok in FORWARD_PARAM_NAMES):
                sev = "high" if isinstance(pval, (int, float)) and pval < 0 \
                    else "medium"
                out.append(BiasFinding(
                    kind="look_ahead", severity=sev,
                    where=f"{name}: {ppath}",
                    detail=(f"parameter '{leaf}' implies a value taken from a "
                            f"FUTURE bar; the engine's causality contract "
                            f"requires features[t] to use only indices <= t."),
                    evidence=f"{ppath}={pval!r}",
                    recommendation=("Shift the reference back so the value is "
                                    "computable at t, and re-run the engine's "
                                    "causality audit.")))

        # 3. A feature that is a known leak by name.
        lname = fname.lower()
        if any(bad in lname for bad in KNOWN_LEAKY_NAMES):
            out.append(BiasFinding(
                kind="look_ahead", severity="high",
                where=f"{name}: features[{fname}]",
                detail=(f"feature '{fname}' is a forward-looking construct; "
                        f"a backtest using it is measuring the future."),
                evidence=f"features[].name={fname}",
                recommendation="Replace with a causal transform of past bars."))

    # 4. The signal references a feature the spec does not define.
    referenced = sig_params.get("feature")
    defined = {f.get("name") for f in features if isinstance(f, dict)}
    if referenced and defined and referenced not in defined:
        out.append(BiasFinding(
            kind="look_ahead", severity="medium",
            where=f"{name}: signal.params.feature",
            detail=(f"the signal reads feature '{referenced}', which this "
                    f"spec does not define. An undefined feature is either "
                    f"resolved from elsewhere (an undeclared, unauditable "
                    f"input) or defaults to something not derivable at t."),
            evidence=(f"signal.feature={referenced} "
                      f"defined_features={sorted(x for x in defined if x)}"),
            recommendation="Declare every feature the signal consumes."))

    # 5. A signal type that is not a time-series decision.
    sig_type = str(signal.get("type") or "")
    if any(bad in sig_type.lower() for bad in
           ("forward", "future", "next", "lead", "oracle")):
        out.append(BiasFinding(
            kind="look_ahead", severity="high",
            where=f"{name}: signal.type",
            detail=(f"signal type '{sig_type}' is not a decision-time rule."),
            evidence=f"signal.type={sig_type}",
            recommendation="Use a causal signal type."))

    # 6. Forward-looking parameter names inside the signal params.
    for ppath, pval in _walk_params(sig_params, "signal.params"):
        leaf = ppath.split(".")[-1].lower()
        if any(tok in leaf for tok in FORWARD_PARAM_NAMES):
            out.append(BiasFinding(
                kind="look_ahead", severity="medium",
                where=f"{name}: {ppath}",
                detail=(f"signal parameter '{leaf}' implies a forward-looking "
                        f"input."),
                evidence=f"{ppath}={pval!r}",
                recommendation="Re-derive the value from data available at t."))

    # 7. The regime path: the HMM is fitted on the WHOLE panel, so the
    #    regime CLASSIFICATION is in-sample even though the posterior is
    #    a causal filter. This is disclosed in backtest.py; the auditor
    #    reports it because it bounds the out-of-sample claim.
    if sig_type in ("regime_switch", "regime_switch_cross_sectional"):
        out.append(BiasFinding(
            kind="look_ahead", severity="medium",
            where=f"{name}: signal.type={sig_type}",
            detail=("the regime HMM's parameters (means, variances, transition "
                    "matrix) are fitted on the WHOLE panel, so the regime "
                    "BOUNDARY is in-sample. The posterior itself is a causal "
                    "FILTER (leapspace/regime.py uses filter(), not smooth()), "
                    "so no bar sees its own future — but the walk-forward "
                    "re-simulates the same fitted regime, so the OOS numbers "
                    "carry the in-sample boundary."),
            evidence=("leapspace/backtest.py:sig_regime_switch -> "
                      "identify_regimes() -> HMM.fit(data) on the full "
                      "series; leapspace/regime.py:filter() is causal, "
                      "smooth() is not used"),
            recommendation=("Refit the HMM inside each walk-forward fold "
                            "before trusting the OOS Sharpe, or state the "
                            "in-sample classification as a stated limit on "
                            "the result.")))
    return out

# --------------------------------------------------------------------------
# SURVIVORSHIP
# --------------------------------------------------------------------------
def _audit_survivorship(spec: Dict[str, Any], name: str,
                         universe: Optional[Sequence[str]]) -> List[BiasFinding]:
    out: List[BiasFinding] = []
    uni = spec.get("universe") or {}
    if not isinstance(uni, dict):
        uni = {}
    preset = uni.get("preset")
    symbols = list(universe) if universe else list(uni.get("symbols") or [])
    # A point-in-time universe is constructed ON THE DATE, so it includes the
    # assets that later failed. That is the one construction that is not
    # survivorship-biased, and the spec must say so.
    point_in_time = bool(uni.get("point_in_time"))
    as_of = uni.get("as_of")

    if preset and preset in SURVIVORSHIP_PRONE_PRESETS:
        meta = SURVIVORSHIP_PRONE_PRESETS[preset]
        members = PRESET_MEMBERS.get(preset, [])
        out.append(BiasFinding(
            kind="survivorship", severity=meta["severity"],
            where=f"{name}: universe.preset={preset}",
            detail=("the universe is a PRESET chosen with hindsight: "
                    + meta["text"]),
            evidence=(f"preset={preset} members={','.join(members)} "
                      f"n_members={len(members)}"),
            recommendation=("Rebuild the universe point-in-time: include "
                            "assets that existed and later failed, or state "
                            "the survivorship limit on every number computed "
                            "on this universe.")))

    if symbols and not point_in_time:
        out.append(BiasFinding(
            kind="survivorship", severity="medium",
            where=f"{name}: universe.symbols",
            detail=(f"an explicit {len(symbols)}-symbol list is used and the "
                    f"spec does not declare it point-in-time. A hand-written "
                    f"list is chosen with hindsight; the survivorship-safe "
                    f"construction is one built ON THE DATE, which includes "
                    f"the assets that later failed."),
            evidence=(f"symbols={','.join(symbols[:12])}"
                      + (" ..." if len(symbols) > 12 else "")
                      + f" point_in_time={point_in_time}"
                      + (f" as_of={as_of}" if as_of else "")),
            recommendation=("Declare the universe point-in-time with "
                            "`universe.point_in_time` and `universe.as_of`, "
                            "and state the inclusion rule.")))

    # A universe assembled from "assets that reached millions in market cap"
    # is the classic survivorship trap; look for the wording.
    blob = json.dumps(spec, default=str).lower()
    if re.search(r"(only|just).{0,30}(million|1m|mcap|market cap)", blob):
        out.append(BiasFinding(
            kind="survivorship", severity="high",
            where=f"{name}: universe description",
            detail=("the spec selects assets by a SUCCESS threshold (market "
                    "cap / 'millions'), which selects the survivors by "
                    "construction and drops the failures."),
            evidence="spec text matches a success-threshold universe phrase",
            recommendation=("Select the universe by a POINT-IN-TIME rule "
                            "(listed, liquid at t) rather than by outcome.")))
    return out

# --------------------------------------------------------------------------
# OVERFITTING
# --------------------------------------------------------------------------
def specificity_score(spec: Dict[str, Any]) -> Dict[str, Any]:
    """How specific-to-sample this spec's rules are. Higher = more suspicious.

    The score is a transparent count of suspicious markers, not a mystery
    number: each marker found is listed with its location.
    """
    markers: List[str] = []
    name = spec.get("name") or "?"
    params = (spec.get("signal") or {}).get("params") or {}

    # (a) thresholds with many significant digits.
    for ppath, pval in _walk_params(params, "signal.params"):
        if isinstance(pval, float) and not float(pval).is_integer():
            if _significant_digits(pval) >= 4:
                markers.append(f"{ppath}={pval!r} has "
                               f"{_significant_digits(pval)} significant digits")

    # (b) hard-coded token addresses anywhere in the spec.
    for s in _strings(spec):
        for m in RE_EVM_ADDRESS.findall(s):
            markers.append(f"hard-coded EVM address {m}")
        for m in RE_BASE58_MINT.findall(s):
            # A base58 mint is mixed-case and contains digits. English prose
            # and kebab/snake identifiers do not, so those are not flagged.
            if not (any(c.isdigit() for c in m) and any(c.isupper() for c in m)
                    and any(c.islower() for c in m)):
                continue
            if m.upper() in {x.upper() for x in PRESET_MEMBERS.get("crypto", [])}:
                continue
            markers.append(f"hard-coded base58 mint/address {m[:12]}...")

    # (c) non-round lookbacks.
    for feat in spec.get("features") or []:
        fname = feat.get("name") or "?"
        for key in ("lookback", "window"):
            v = (feat.get("params") or {}).get(key)
            if isinstance(v, int) and v > 0 and v not in CONVENTIONAL_LOOKBACKS:
                markers.append(f"features[{fname}].params.{key}={v} is not a "
                               f"conventional window")

    # (d) a hard-coded price or market-cap level in the signal.
    for ppath, pval in _walk_params(params, "signal.params"):
        if not isinstance(pval, (int, float)) or isinstance(pval, bool):
            continue
        leaf = ppath.split(".")[-1].lower()
        if any(tok in leaf for tok in ("lookback", "window", "skip", "bars",
                                      "period", "n_states", "states", "count",
                                      "embargo", "purge", "len", "size")):
            continue
        if float(pval) > 100.0:
            markers.append(f"{ppath}={pval!r} is an absolute price/size "
                           f"level rather than a rate or a ratio")

    # (e) a very large number of variants tried against one outcome.
    variants = ((spec.get("intake") or {}).get("variants_tried"))
    if isinstance(variants, int) and variants >= 5:
        markers.append(f"variants_tried={variants} — many parameterisations "
                       f"were tried against this outcome")

    return {"score": len(markers), "max": 5, "markers": markers, "spec": name}

def _audit_overfitting(spec: Dict[str, Any], name: str) -> List[BiasFinding]:
    res = specificity_score(spec)
    markers = res["markers"]
    if not markers:
        return []
    sev = "high" if res["score"] >= 3 else ("medium" if res["score"] == 2 else "low")
    return [BiasFinding(
        kind="overfitting", severity=sev,
        where=f"{name}: rules",
        detail=(f"{res['score']} marker(s) of over-specific rules. A rule "
                f"that is only true on the sample it was fitted on is not an "
                f"edge."),
        evidence="; ".join(markers),
        recommendation=("Round the thresholds to conventional values, justify "
                        "each against a reason rather than a result, and "
                        "report the number of variants tried so the "
                        "deflated-Sharpe penalty can be applied honestly."))]

# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def audit_spec(spec: Dict[str, Any], price_series: Optional[Any] = None,
               universe: Optional[Sequence[str]] = None) -> List[BiasFinding]:
    """Audit one strategy spec for look-ahead, survivorship and overfitting.

    `price_series` is optional and used only to check whether the spec's
    stated period is consistent with the data it would be run on (a short
    series cannot support a long lookback). `universe` optionally overrides
    the spec's own universe for the survivorship check.
    """
    if not isinstance(spec, dict):
        raise TypeError("audit_spec expects a spec dict")
    name = str(spec.get("name") or "unnamed_spec")
    findings: List[BiasFinding] = []
    findings.extend(_audit_look_ahead(spec, name))
    findings.extend(_audit_survivorship(spec, name, universe))
    findings.extend(_audit_overfitting(spec, name))

    # Warm-up check: the longest lookback must fit inside the data.
    max_lb = 0
    for feat in spec.get("features") or []:
        v = (feat.get("params") or {}).get("lookback")
        if isinstance(v, int) and v > 0:
            max_lb = max(max_lb, v)
    if max_lb and price_series is not None:
        try:
            n = len(price_series)
        except TypeError:
            n = 0
        if n and n < max_lb * 2:
            findings.append(BiasFinding(
                kind="look_ahead", severity="low",
                where=f"{name}: period vs data",
                detail=(f"the longest lookback is {max_lb} bars but the price "
                        f"series has only {n} points; the feature would be "
                        f"empty for most of the sample."),
                evidence=f"lookback={max_lb} n_points={n}",
                recommendation="Extend the sample or shorten the lookback."))

    # The period end being None means "to the present", which is itself a
    # survivorship exposure: the universe was seen from the future.
    period = spec.get("period") or {}
    if period.get("end") in (None, "", "now", "present"):
        findings.append(BiasFinding(
            kind="survivorship", severity="low",
            where=f"{name}: period.end",
            detail=("the sample runs to the present day, so the universe was "
                    "necessarily chosen knowing which assets survived to "
                    "now."),
            evidence=(f"period.start={period.get('start')} "
                      f"period.end={period.get('end')!r}"),
            recommendation=("Note the survivorship exposure wherever a "
                            "to-present result is quoted.")))
    return findings

def audit_report(findings: Sequence[BiasFinding]) -> str:
    """A flat, readable summary of the findings."""
    if not findings:
        return ("BIAS AUDIT — clean: no look-ahead, survivorship or "
                "overfitting findings.\n"
                "This means the checks did not fire, not that the strategy "
                "is proven to be free of bias.")
    order = {"high": 0, "medium": 1, "low": 2}
    findings = sorted(findings, key=lambda f: (order.get(f.severity, 3), f.kind, f.where))
    lines = ["=" * 72, f"BIAS AUDIT — {len(findings)} finding(s)", "=" * 72]
    counts: Dict[str, int] = {}
    for f in findings:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    lines.append("  by kind: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    sev_counts: Dict[str, int] = {}
    for f in findings:
        sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
    lines.append("  by severity: " + ", ".join(
        f"{k}={v}" for k, v in sorted(sev_counts.items(), key=lambda kv: order.get(kv[0], 3))))
    lines.append("")
    for i, f in enumerate(findings, 1):
        lines.append(f"[{i}] {f.kind.upper()} ({f.severity}) — {f.where}")
        lines.append(f"    what:     {f.detail}")
        lines.append(f"    evidence: {f.evidence}")
        lines.append(f"    fix:      {f.recommendation}")
        lines.append("")
    return "\n".join(lines)

def _load_package_specs() -> List[Dict[str, Any]]:
    """The package's own specs, so results can be mapped back to their universe."""
    try:
        from .backtest import all_specs
        return list(all_specs())
    except Exception:  # noqa: BLE001
        return []

def audit_backtest_results(results: Any,
                           specs: Optional[Sequence[Dict[str, Any]]] = None
                           ) -> List[BiasFinding]:
    """Audit the STORED backtest results for hidden bias.

    The honest headline for this package: all 13 specs run on PRESET
    universes (us_equity_broad, us_equity_style, us_equity_sector, crypto).
    A universe built from assets that are still trading today IS a
    survivorship-biased universe, and that is reported explicitly rather
    than assumed away.

    `specs` may be supplied to map a result row back to its spec; when it
    is omitted the package's own specs are loaded.
    """
    if isinstance(results, dict):
        rows = results.get("results") or []
    else:
        rows = list(results or [])
    if specs is None:
        specs = _load_package_specs()

    findings: List[BiasFinding] = []
    spec_by_name = {str(s.get("name")): s for s in (specs or [])}

    # -- 1. Which universes were used, and are they survivors? -----------
    preset_counts: Dict[str, int] = {}
    preset_rows: Dict[str, List[str]] = {}
    for row in rows:
        name = str(row.get("name") or "?")
        spec = spec_by_name.get(name)
        uni = (spec or {}).get("universe") or {}
        preset = uni.get("preset") if isinstance(uni, dict) else None
        if preset:
            preset_counts[preset] = preset_counts.get(preset, 0) + 1
            preset_rows.setdefault(preset, []).append(name)

    if preset_counts:
        total = sum(preset_counts.values())
        detail = ", ".join(f"{k}={v}" for k, v in sorted(preset_counts.items()))
        findings.append(BiasFinding(
            kind="survivorship", severity="high",
            where="backtest_results.json: universe selection",
            detail=(f"{total} of {len(rows)} spec results ran on PRESET "
                    f"universes ({detail}). Every preset is a list of assets "
                    f"assembled with knowledge of which assets exist and are "
                    f"liquid NOW, so a universe built from surviving assets "
                    f"IS a survivorship-biased universe. This is a real "
                    f"limitation of these results and it is not corrected by "
                    f"the walk-forward, the cost stress or the Monte Carlo."),
            evidence=("; ".join(f"{p}: {', '.join(preset_rows.get(p, []))}"
                                for p in sorted(preset_rows))),
            recommendation=("State the survivorship exposure on every "
                            "verdict, and re-run the crypto specs on a "
                            "point-in-time universe that includes tokens "
                            "which launched and failed in the same window.")))

    for preset, names in sorted(preset_rows.items()):
        if preset in SURVIVORSHIP_PRONE_PRESETS:
            meta = SURVIVORSHIP_PRONE_PRESETS[preset]
            findings.append(BiasFinding(
                kind="survivorship", severity=meta["severity"],
                where=f"backtest_results.json: preset '{preset}'",
                detail=(meta["text"] + f" {len(names)} result(s) depend on it: "
                        + ", ".join(names)),
                evidence=f"members={','.join(PRESET_MEMBERS.get(preset, []))}",
                recommendation=("Do not read these results as an estimate of "
                                "the strategy's live performance.")))

    # -- 2. How many variants were tried against each outcome? -----------
    variants: List[Tuple[str, int]] = []
    for row in rows:
        name = str(row.get("name") or "?")
        v = (row.get("intake_gate") or {}).get("variants_tried")
        if v is None:
            v = ((spec_by_name.get(name) or {}).get("intake") or {}).get("variants_tried")
        if isinstance(v, int):
            variants.append((name, v))
    if variants:
        max_v = max(v for _, v in variants)
        if max_v >= 2:
            offenders = [n for n, v in variants if v >= 2]
            findings.append(BiasFinding(
                kind="overfitting", severity="medium",
                where="backtest_results.json: variants_tried",
                detail=(f"{len(offenders)} spec(s) had more than one "
                        f"parameterisation tried against the same outcome "
                        f"(max variants_tried={max_v}). The deflated-Sharpe "
                        f"penalty scales with the number of trials, so the "
                        f"honest number of trials for the whole research "
                        f"PROGRAMME is larger than any single spec's count: "
                        f"{len(rows)} specs were run over {len(preset_counts)} "
                        f"universes against the same market data."),
                evidence="; ".join(f"{n}: variants_tried={v}"
                                   for n, v in variants if v >= 2),
                recommendation=("Report the family-wise trial count, not just "
                                "the per-spec count, whenever a spec is "
                                "promoted from a set of variants.")))

    # -- 3. A verdict carried on a quick run is not a full-gauntlet verdict.
    quick_rows = [str(r.get("name")) for r in rows if (r.get("skipped_stages") or [])]
    if quick_rows:
        findings.append(BiasFinding(
            kind="overfitting", severity="medium",
            where="backtest_results.json: skipped validation stages",
            detail=(f"{len(quick_rows)} of {len(rows)} stored results skipped "
                    f"at least one validation stage (Monte Carlo, the "
                    f"parameter sweep, cross-market replication). A quick run "
                    f"can be MORE favourable than the full gauntlet — this "
                    f"package's own record shows one SUPPORTED verdict "
                    f"downgraded to FRAGILE once Monte Carlo ran. Reading a "
                    f"quick verdict as a final one is a form of selective "
                    f"reporting."),
            evidence="skipped on: " + ", ".join(quick_rows),
            recommendation=("Compare verdicts only within the same "
                            "validation level, and prefer the stored "
                            "full-gauntlet file where one exists.")))

    # -- 4. Survivorship in the SUPPORTED rows specifically ---------------
    supported = [str(r.get("name")) for r in rows
                 if str(r.get("verdict") or "").upper() == "SUPPORTED"]
    if supported and preset_counts:
        findings.append(BiasFinding(
            kind="survivorship", severity="high",
            where="backtest_results.json: SUPPORTED verdicts",
            detail=(f"{len(supported)} spec(s) are marked SUPPORTED "
                    f"({', '.join(supported)}). Every one of them was "
                    f"measured on a survivor universe, so the SUPPORTED "
                    f"verdict means 'this edge survives costs, walk-forward "
                    f"and (where run) Monte Carlo ON TODAY'S SURVIVORS'. It "
                    f"does not mean the edge is unbiased, and the report "
                    f"should not let it read that way."),
            evidence=f"supported={', '.join(supported)}",
            recommendation=("Attach the survivorship caveat to the SUPPORTED "
                            "rows in the consolidated report.")))
    return findings

# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------
def _selftest() -> int:
    import shutil
    import tempfile

    ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))

    print("=" * 72)
    print("BIASAUDIT SELF-TEST — look-ahead / survivorship / overfitting")
    print("=" * 72)

    # ------------------------------------------------------------------
    # 1. A DELIBERATELY look-ahead-biased spec MUST be caught.
    # ------------------------------------------------------------------
    print("\n1. A deliberately look-ahead-biased spec IS caught")
    leaky = {
        "name": "deliberately_leaky_spec",
        "universe": {"preset": "crypto"},
        "period": {"start": "2021-01-01", "end": None, "interval": "1d"},
        "features": [
            {"name": "sma_gap", "params": {"lookback": 20}},
            {"name": "future_return", "params": {"lookback": -5}},
            {"name": "lead_signal", "params": {"shift": -1}},
        ],
        "signal": {"type": "time_series_threshold",
                   "params": {"feature": "sma_gap", "threshold": 0.0,
                              "future_feature": "future_return"}},
    }
    findings = audit_spec(leaky)
    kinds = [f.kind for f in findings]
    where = " | ".join(f.where for f in findings)
    check("look-ahead findings raised", "look_ahead" in kinds, str(kinds))
    check("negative lookback caught",
          any("lookback" in f.where and "future_return" in f.where
              for f in findings), where[:150])
    check("forward-looking feature name caught", any("future_return" in f.where for f in findings))
    check("shift parameter caught", any("shift" in f.where for f in findings))
    check("survivorship flagged for the crypto preset",
          any(f.kind == "survivorship" for f in findings))
    print(f"  -> {len(findings)} finding(s); report head:")
    for line in audit_report(findings).splitlines()[:10]:
        print("     " + line)

    # ------------------------------------------------------------------
    # 2. A CLEAN spec must produce NO findings (the auditor is not rigged).
    # ------------------------------------------------------------------
    print("\n2. A clean spec produces NO findings (the auditor is not rigged)")
    clean = {
        "name": "clean_causal_spec",
        # A POINT-IN-TIME universe: built on the date, so it contains the
        # assets that later failed. That is the survivorship-safe case, and
        # the auditor accepts it because the spec declares it.
        "universe": {"symbols": ["AAPL", "IBM", "XYZ_FAILED_CO", "ABC_DELISTED"],
                     "point_in_time": True, "as_of": "2010-01-01"},
        "period": {"start": "2010-01-01", "end": "2020-12-31", "interval": "1d"},
        "features": [{"name": "sma_gap", "params": {"lookback": 20}}],
        "signal": {"type": "time_series_threshold",
                   "params": {"feature": "sma_gap", "threshold": 0.0}},
        "intake": {"variants_tried": 1},
    }
    clean_findings = audit_spec(clean)
    check("clean spec -> zero findings", len(clean_findings) == 0,
          "; ".join(f.where for f in clean_findings))
    print("  -> report:")
    for line in audit_report(clean_findings).splitlines():
        print("     " + line)

    print("\n2b. A clean spec on a SURVIVOR preset is NOT clean")
    preset_clean = dict(clean, universe={"preset": "us_equity_broad"})
    preset_findings = audit_spec(preset_clean)
    check("preset universe still raises survivorship",
          any(f.kind == "survivorship" for f in preset_findings),
          "; ".join(f.where for f in preset_findings))

    # ------------------------------------------------------------------
    # 3. An over-fitted spec is caught.
    # ------------------------------------------------------------------
    print("\n3. An over-fitted spec IS caught")
    fitted = {
        "name": "overfitted_spec",
        "universe": {"preset": "crypto"},
        "period": {"start": "2021-01-01", "end": None, "interval": "1d"},
        "features": [{"name": "momentum", "params": {"lookback": 47}}],
        "signal": {"type": "time_series_threshold",
                   "params": {"feature": "momentum", "threshold": 42102.5}},
        "intake": {"variants_tried": 9},
    }
    of_findings = audit_spec(fitted)
    check("overfitting finding raised",
          any(f.kind == "overfitting" for f in of_findings),
          "; ".join(f.evidence for f in of_findings))
    check("many-significant-digit threshold flagged",
          any("significant digits" in f.evidence for f in of_findings))
    check("non-round lookback flagged",
          any("not a conventional window" in f.evidence for f in of_findings))
    check("hard-coded level flagged",
          any("absolute price/size level" in f.evidence for f in of_findings))

    # ------------------------------------------------------------------
    # 4. Audit the REAL specs of this package.
    # ------------------------------------------------------------------
    print("\n4. The REAL specs of this package")
    real_specs = _load_package_specs()
    real_findings: List[BiasFinding] = []
    for s in real_specs:
        real_findings.extend(audit_spec(s))
    by_kind: Dict[str, int] = {}
    for f in real_findings:
        by_kind[f.kind] = by_kind.get(f.kind, 0) + 1
    print(f"  {len(real_specs)} real specs -> {len(real_findings)} finding(s) {by_kind}")
    for f in real_findings:
        print(f"    [{f.severity:<6}] {f.kind:<13} {f.where}")

    # ------------------------------------------------------------------
    # 5. Audit the REAL stored backtest results.
    # ------------------------------------------------------------------
    print("\n5. The REAL stored backtest results")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_path = os.path.join(here, "reports", "backtest_results.json")
    tmpdir = tempfile.mkdtemp(prefix="leapspace_biasaudit_")
    try:
        with open(results_path, "r", encoding="utf-8") as fh:
            results = json.load(fh)
        res_findings = audit_backtest_results(results, specs=real_specs)
        print(f"  {len(results)} stored results -> {len(res_findings)} finding(s)")
        for f in res_findings:
            print(f"    [{f.severity:<6}] {f.kind:<13} {f.where}")
        check("survivorship finding raised on the stored results",
              any(f.kind == "survivorship" for f in res_findings))
        check("the survivorship finding names every preset",
              all(any(p in f.evidence for f in res_findings)
                  for p in ("crypto", "us_equity_broad")))
        check("quick-run verdicts are flagged", any("skipped" in f.where for f in res_findings))
        check("the SUPPORTED-verdict caveat is raised",
              any("SUPPORTED verdicts" in f.where for f in res_findings))
        print("\n  -> report:")
        for line in audit_report(res_findings).splitlines():
            print("     " + line)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 6. Flat output.
    # ------------------------------------------------------------------
    print("\n6. Flat, flattener-friendly output")
    js = to_json(real_findings[0]) if real_findings else to_json(clean)
    check("to_json() emits a flat dict", js.startswith("{") and '"kind"' in js, js[:80])

    print("\n" + "=" * 72)
    print("RESULT: " + ("ALL CHECKS PASSED" if ok else "FAILURES PRESENT"))
    print("=" * 72)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(_selftest())
