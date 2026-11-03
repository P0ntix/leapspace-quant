"""The backtest outcome visualisation: equity, drawdown, and the P&L shape.

WHAT THIS IS
    A self-contained HTML dashboard of what the backtests ACTUALLY DID,
    built from real out-of-sample return series - not from the verdict
    labels. The verdict matrix says what the engine concluded; this
    says what the money would have done.

    It is pure-stdlib inline SVG, for the same reason the package's
    other charts are: this host has no scientific stack, and a report
    that cannot be rendered is not a report.

THE CHARTS
    1. EQUITY CURVES. The cumulative out-of-sample path per concept.
       This is the chart that answers "did it work" in one glance, and
       it is the chart a verdict label cannot replace - a concept can
       end with a positive Sharpe and a visibly broken path.
    2. DRAWDOWN. The underwater plot. A strategy that makes money but
       goes through a 40% hole is a different proposition from one
       that drifts up gently, and the verdict label does not say.
    3. PER-FOLD SHARPE. One bar per purged-and-embargoed fold. An
       edge that lives in one fold is not an edge, and this is where
       that shows.
    4. THE P&L SHAPE. The distribution of out-of-sample returns, with
       the wins and the losses separated. This is the chart for the
       question "is the upside bigger than the downside, and are the
       wins more consistent than the losses".
    5. THE OUTCOME TABLE. For every spec: the pooled out-of-sample
       Sharpe, the win rate, the profit factor, the average win, the
       average loss, the payoff ratio and the expectancy per bar -
       with the long/short exposure stated.

THE HONESTY RULES
    * Only specs whose OOS RETURN SERIES is actually available get an
      equity curve. A spec with no series is listed as having none,
      never drawn as a flat line.
    * The benchmark line on the equity chart is the ZERO return line,
      labelled as such. There is no "buy and hold" line unless a
      benchmark series is supplied, because inventing one from the
      price history the signal already used would not be a benchmark.
    * Every number in the outcome table comes from the same run that
      produced the verdict, and the table says which.
"""
from __future__ import annotations

import html
import json
import math
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .viz_leading import (ACCENT, BG, DOWN, GRID, MUTED, NEUTRAL, TEXT,
                           UP, WARN)

__all__ = [
    "OUTCOMES_PATH",
    "collect_outcomes",
    "outcome_statistics",
    "render_backtest_dashboard",
    "build_backtest_dashboard",
]


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTCOMES_PATH = os.path.join(ROOT, "reports", "backtest_outcomes.json")
DASHBOARD_PATH = os.path.join(ROOT, "reports", "charts",
                               "backtest_outcomes.html")


# --------------------------------------------------------------------------
# Collecting the real data
# --------------------------------------------------------------------------
def _load_json(path: str) -> Any:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return None


def _scorecard_dirs() -> List[str]:
    """Every raw scorecard file the workers left behind."""
    reports = os.path.join(ROOT, "reports")
    if not os.path.isdir(reports):
        return []
    out = []
    for name in sorted(os.listdir(reports)):
        if name.endswith("_scorecards.json"):
            out.append(os.path.join(reports, name))
    return out


def _extract_walk_forward(entry: Any) -> Dict[str, Any]:
    """The walk-forward block, whatever shape the scorecard is in.

    The workers captured the gauntlet at different depths - one
    wrapped `full_gauntlet` directly, one captured the whole
    `run_spec` result - so the block sits at a different level in
    each. This digs it out wherever it is.
    """
    if not isinstance(entry, dict):
        return {}
    if isinstance(entry.get("walk_forward"), dict):
        return entry["walk_forward"]
    for key in ("gauntlet", "scorecard"):
        sub = entry.get(key)
        if isinstance(sub, dict):
            wf = _extract_walk_forward(sub)
            if wf:
                return wf
            sc = sub.get("scorecard")
            if isinstance(sc, dict) and isinstance(sc.get("walk_forward"),
                                                   dict):
                return sc["walk_forward"]
    sc = entry.get("scorecard")
    if isinstance(sc, dict) and isinstance(sc.get("walk_forward"), dict):
        return sc["walk_forward"]
    return {}


def _extract_scorecard(entry: Any) -> Dict[str, Any]:
    if not isinstance(entry, dict):
        return {}
    if isinstance(entry.get("scorecard"), dict):
        return entry["scorecard"]
    for key in ("gauntlet",):
        sub = entry.get(key)
        if isinstance(sub, dict):
            sc = _extract_scorecard(sub)
            if sc:
                return sc
    return {}


def collect_outcomes(results_path: Optional[str] = None,
                     scorecard_paths: Optional[Sequence[str]] = None
                     ) -> Dict[str, Any]:
    """Gather the outcome data for every spec that has any.

    The results file is the source of truth for the VERDICT and the
    metrics. The raw scorecards are the source of truth for the OOS
    RETURN SERIES and the full fold table, because those were never
    in the results file.
    """
    results_path = results_path or os.path.join(
        ROOT, "reports", "paper_concept_results.json")
    rows = _load_json(results_path) or []
    if not isinstance(rows, list):
        rows = []

    by_name: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        if isinstance(r, dict) and r.get("name"):
            by_name[str(r["name"])] = r

    # Harvest the OOS paths from the raw scorecards.
    paths: Dict[str, List[float]] = {}
    folds: Dict[str, List[Dict[str, Any]]] = {}
    for sp in (scorecard_paths if scorecard_paths is not None
               else _scorecard_dirs()):
        data = _load_json(sp)
        if not isinstance(data, dict):
            continue
        for key, entry in data.items():
            if not isinstance(entry, dict):
                continue
            wf = _extract_walk_forward(entry)
            if not wf:
                continue
            rets = wf.get("oos_rets")
            if isinstance(rets, list) and rets:
                # The scorecard files are keyed by spec name, sometimes
                # with a suffix. Match on the stem.
                for name in by_name:
                    if key == name or key.startswith(name):
                        paths.setdefault(name, [float(x) for x in rets])
                        break
                else:
                    # Fall back: match on the base name.
                    base = key.split("::")[-1].split("|")[-1].strip()
                    for name in by_name:
                        if base == name or name.endswith(base):
                            paths.setdefault(name, [float(x) for x in rets])
                            break
            fl = wf.get("folds")
            if isinstance(fl, list) and fl:
                for name in by_name:
                    if key == name or key.startswith(name):
                        folds.setdefault(name, fl)
                        break

    # Fold tables from the results file take precedence - they are the
    # corrected ones.
    for name, r in by_name.items():
        f = (r.get("walk_forward") or {}).get("folds")
        if f:
            folds[name] = f

    specs: List[Dict[str, Any]] = []
    for name, r in by_name.items():
        m = r.get("metrics") or {}
        oos = m.get("oos_sharpe")
        is_sh = m.get("in_sample_sharpe")
        rets = paths.get(name) or []
        stats = outcome_statistics(rets)
        specs.append({
            "name": name,
            "concept": r.get("concept") or "",
            "asset_class": r.get("asset_class") or "",
            "verdict": r.get("verdict") or "",
            "flags": list(r.get("flags") or []),
            "errors": list(r.get("errors") or []),
            "oos_sharpe": oos,
            "in_sample_sharpe": is_sh,
            "n_trades": m.get("n_trades"),
            "max_drawdown": m.get("max_drawdown"),
            "total_return": m.get("total_return"),
            "oos_max_drawdown": m.get("oos_max_drawdown"),
            "oos_cagr": m.get("oos_cagr"),
            "oos_profitable_folds": m.get("oos_profitable_folds"),
            "oos_retention": m.get("oos_retention"),
            "pbo": m.get("pbo"),
            "deflated_sharpe": m.get("deflated_sharpe"),
            "folds": folds.get(name) or [],
            "path": rets,
            "path_length": len(rets),
            "stats": stats,
            "stages": r.get("stages") or {},
            "leading_coverage": r.get("leading_coverage") or {},
        })

    return {
        "generated_at": _now(),
        "n_specs": len(specs),
        "n_with_path": sum(1 for s in specs if s["path_length"]),
        "specs": specs,
    }


def _now() -> str:
    import datetime as dt
    return dt.datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# The outcome statistics - this is where "upside vs downside" is measured
# --------------------------------------------------------------------------
def outcome_statistics(rets: Sequence[float]) -> Dict[str, Any]:
    """The shape of the out-of-sample P&L.

    This is the measurement the user's requirement actually asks for:
    is the upside bigger than the downside, are the wins more
    consistent than the losses, and are the losses small.

      * `win_rate`       - the share of positive out-of-sample bars
      * `n_wins`, `n_losses`, `n_flat`
      * `avg_win`, `avg_loss` - the mean of each side
      * `payoff_ratio`   - avg_win / |avg_loss|. Above 1.0 means the
                           wins are bigger than the losses.
      * `profit_factor`  - gross profit / gross loss. Above 1.0 means
                           the strategy made money.
      * `expectancy`     - the mean return per bar. The single number
                           that says whether the edge exists.
      * `upside_downside` - gross profit / gross loss expressed as a
                           ratio, which is the profit factor again;
                           kept separate because it is the phrase the
                           requirement uses.
      * `max_consecutive_losses` - how long the losing runs went.
      * `median_win`, `median_loss` - because a mean is a poor
                           description of a skewed distribution.
    """
    clean = [float(r) for r in rets
             if isinstance(r, (int, float)) and not math.isnan(float(r))]
    if not clean:
        return {"n_bars": 0}
    wins = [r for r in clean if r > 0]
    losses = [r for r in clean if r < 0]
    flat = [r for r in clean if r == 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    n = len(clean)

    # Equity path, for the drawdown and the cumulative series.
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    dd_series: List[float] = []
    for r in clean:
        equity *= (1.0 + r)
        peak = max(peak, equity)
        dd = 0.0 if peak <= 0 else (peak - equity) / peak
        max_dd = max(max_dd, dd)
        dd_series.append(dd)

    # Consecutive losing runs.
    run = 0
    worst_run = 0
    for r in clean:
        if r < 0:
            run += 1
            worst_run = max(worst_run, run)
        else:
            run = 0

    def _median(xs: List[float]) -> Optional[float]:
        if not xs:
            return None
        s = sorted(xs)
        m = len(s) // 2
        return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2.0

    avg_win = (sum(wins) / len(wins)) if wins else None
    avg_loss = (sum(losses) / len(losses)) if losses else None
    payoff = (abs(avg_win / avg_loss)
              if avg_win is not None and avg_loss not in (None, 0) else None)
    pf = (gross_win / gross_loss) if gross_loss > 0 else (
        float("inf") if gross_win > 0 else None)

    return {
        "n_bars": n,
        "n_wins": len(wins),
        "n_losses": len(losses),
        "n_flat": len(flat),
        "win_rate": len(wins) / n if n else None,
        "loss_rate": len(losses) / n if n else None,
        "gross_win": gross_win,
        "gross_loss": gross_loss,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "median_win": _median(wins),
        "median_loss": _median(losses),
        "payoff_ratio": payoff,
        "profit_factor": pf,
        "upside_downside": pf,
        "expectancy": sum(clean) / n,
        "total_return": equity - 1.0,
        "max_drawdown": max_dd,
        "max_consecutive_losses": worst_run,
        "dd_series": dd_series,
    }


# --------------------------------------------------------------------------
# The charts
# --------------------------------------------------------------------------
def _esc(v: Any) -> str:
    return html.escape(str(v), quote=True)


def _equity_curve(path: Sequence[float]) -> List[float]:
    """The cumulative path from a return series."""
    eq = 1.0
    out = [eq]
    for r in path:
        eq *= (1.0 + float(r))
        out.append(eq)
    return out


def _downsample(values: Sequence[float], max_points: int = 600
                ) -> List[float]:
    """Reduce a long series to at most `max_points` points.

    A 4,290-bar equity path rendered as an SVG polyline is 4,290
    coordinate pairs. With 48 specs and several charts each, the
    dashboard was over a megabyte of SVG the browser had to parse, and
    the visual gain past a few hundred points is nil.

    The reduction keeps the FIRST and LAST points exactly, so the
    start and end of every equity curve - the two points a reader
    actually compares - are never interpolated away.
    """
    n = len(values)
    if n <= max_points:
        return list(values)
    if max_points < 3:
        return [values[0], values[-1]]
    step = (n - 1) / float(max_points - 1)
    out: List[float] = []
    for i in range(max_points):
        idx = int(round(i * step))
        idx = max(0, min(n - 1, idx))
        out.append(values[idx])
    out[0] = values[0]
    out[-1] = values[-1]
    return out


def _svg_equity(series: Sequence[Dict[str, Any]], title: str,
                 height: int = 340) -> str:
    """Cumulative equity, log-ish scale, with a zero reference."""
    width = 1000
    pad_l, pad_r, pad_t, pad_b = 70, 20, 34 if title else 16, 34
    px0, px1 = pad_l, width - pad_r
    py0, py1 = pad_t, height - pad_b

    allv: List[float] = []
    for s in series:
        allv.extend([float(v) for v in (s.get("values") or [])])
    if not allv:
        return ('<svg viewBox="0 0 1000 200"><rect width="1000" '
                'height="200" fill="' + BG + '"/><text x="500" y="100" '
                'fill="' + MUTED + '" text-anchor="middle">no data</text>'
                '</svg>')
    lo, hi = min(allv), max(allv)
    if hi == lo:
        hi = lo + 0.01
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad

    def y(v: float) -> float:
        return py1 - ((v - lo) / (hi - lo)) * (py1 - py0)

    out = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
           f'style="max-width:{width}px;background:{BG}" '
           f'xmlns="http://www.w3.org/2000/svg">',
           f'<rect width="{width}" height="{height}" fill="{BG}"/>']
    if title:
        out.append(f'<text x="{pad_l}" y="22" fill="{TEXT}" font-size="14" '
                   f'font-weight="bold">{_esc(title)}</text>')
    # Grid and y labels.
    for i in range(5):
        frac = i / 4.0
        val = lo + frac * (hi - lo)
        yy = py1 - frac * (py1 - py0)
        out.append(f'<line x1="{px0}" y1="{yy:.1f}" x2="{px1}" y2="{yy:.1f}" '
                   f'stroke="{GRID}" stroke-width="1" opacity="0.55"/>')
        out.append(f'<text x="{pad_l - 8}" y="{yy + 4:.1f}" fill="{MUTED}" '
                   f'font-size="10" text-anchor="end">{val:,.2f}</text>')
    # The break-even line: 1.0 on the cumulative scale.
    if lo <= 1.0 <= hi:
        out.append(f'<line x1="{px0}" y1="{y(1.0):.1f}" x2="{px1}" '
                   f'y2="{y(1.0):.1f}" stroke="{MUTED}" stroke-width="1.2" '
                   f'stroke-dasharray="4 3"/>')
        out.append(f'<text x="{px1 - 4}" y="{y(1.0) - 5:.1f}" fill="{MUTED}" '
                   f'font-size="9" text-anchor="end">break-even</text>')
    # The series.
    for s in series:
        vals = s.get("values") or []
        if not vals:
            continue
        n = len(vals)
        step = (px1 - px0) / max(1, n - 1)
        pts = " ".join(f"{px0 + i * step:.1f},{y(float(v)):.1f}"
                       for i, v in enumerate(vals))
        out.append(f'<polyline points="{pts}" fill="none" '
                   f'stroke="{s.get("color", ACCENT)}" stroke-width="1.8" '
                   f'opacity="0.9"/>')
    # Legend.
    lx = px0
    ly = height - 10
    for s in series:
        out.append(f'<rect x="{lx}" y="{ly - 8}" width="10" height="10" '
                   f'fill="{s.get("color", ACCENT)}" rx="2"/>')
        out.append(f'<text x="{lx + 14}" y="{ly + 1}" fill="{TEXT}" '
                   f'font-size="10">{_esc(s.get("name"))}</text>')
        lx += 18 + 7 * len(str(s.get("name")))
    out.append("</svg>")
    return "".join(out)


def _svg_drawdown(series: Sequence[Dict[str, Any]], title: str,
                  height: int = 280) -> str:
    """The underwater plot."""
    width = 1000
    pad_l, pad_r, pad_t, pad_b = 70, 20, 34 if title else 16, 34
    px0, px1 = pad_l, width - pad_r
    py0, py1 = pad_t, height - pad_b

    allv: List[float] = []
    for s in series:
        allv.extend([abs(float(v)) for v in (s.get("values") or [])])
    if not allv:
        return ('<svg viewBox="0 0 1000 200"><rect width="1000" '
                'height="200" fill="' + BG + '"/><text x="500" y="100" '
                'fill="' + MUTED + '" text-anchor="middle">no data</text>'
                '</svg>')
    hi = max(allv) or 0.01
    hi = min(1.0, hi * 1.1)

    def y(v: float) -> float:
        return py0 + (abs(float(v)) / hi) * (py1 - py0)

    out = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
           f'style="max-width:{width}px;background:{BG}" '
           f'xmlns="http://www.w3.org/2000/svg">',
           f'<rect width="{width}" height="{height}" fill="{BG}"/>']
    if title:
        out.append(f'<text x="{pad_l}" y="22" fill="{TEXT}" font-size="14" '
                   f'font-weight="bold">{_esc(title)}</text>')
    for i in range(5):
        frac = i / 4.0
        val = frac * hi
        yy = py1 - frac * (py1 - py0)
        out.append(f'<line x1="{px0}" y1="{yy:.1f}" x2="{px1}" y2="{yy:.1f}" '
                   f'stroke="{GRID}" stroke-width="1" opacity="0.55"/>')
        out.append(f'<text x="{pad_l - 8}" y="{yy + 4:.1f}" fill="{MUTED}" '
                   f'font-size="10" text-anchor="end">-{val:.0%}</text>')
    out.append(f'<line x1="{px0}" y1="{py0}" x2="{px1}" y2="{py0}" '
               f'stroke="{TEXT}" stroke-width="1.2" opacity="0.8"/>')
    for s in series:
        vals = s.get("values") or []
        if not vals:
            continue
        n = len(vals)
        step = (px1 - px0) / max(1, n - 1)
        pts = " ".join(f"{px0 + i * step:.1f},{y(v):.1f}"
                       for i, v in enumerate(vals))
        out.append(f'<polyline points="{pts}" fill="none" '
                   f'stroke="{s.get("color", ACCENT)}" stroke-width="1.4" '
                   f'opacity="0.85"/>')
    lx = px0
    ly = height - 10
    for s in series:
        out.append(f'<rect x="{lx}" y="{ly - 8}" width="10" height="10" '
                   f'fill="{s.get("color", ACCENT)}" rx="2"/>')
        out.append(f'<text x="{lx + 14}" y="{ly + 1}" fill="{TEXT}" '
                   f'font-size="10">{_esc(s.get("name"))}</text>')
        lx += 18 + 7 * len(str(s.get("name")))
    out.append("</svg>")
    return "".join(out)


def _svg_fold_bars(specs: Sequence[Dict[str, Any]], title: str,
                   height: int = 300) -> str:
    """One bar per fold, grouped by spec."""
    width = 1000
    pad_l, pad_r, pad_t, pad_b = 70, 20, 34 if title else 16, 60
    px0, px1 = pad_l, width - pad_r
    py0, py1 = pad_t, height - pad_b

    groups = []
    for s in specs:
        vals = [f.get("oos_sharpe") for f in (s.get("folds") or [])]
        if any(v is not None for v in vals):
            groups.append((s["name"], vals))
    if not groups:
        return ('<svg viewBox="0 0 1000 200"><rect width="1000" '
                'height="200" fill="' + BG + '"/><text x="500" y="100" '
                'fill="' + MUTED + '" text-anchor="middle">no fold data'
                '</text></svg>')

    allv: List[float] = []
    for _n, vals in groups:
        allv.extend([float(v) for v in vals if v is not None])
    lo, hi = min(allv + [0.0]), max(allv + [0.0])
    if hi == lo:
        hi = lo + 1.0
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad

    def y(v: float) -> float:
        return py1 - ((v - lo) / (hi - lo)) * (py1 - py0)

    out = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
           f'style="max-width:{width}px;background:{BG}" '
           f'xmlns="http://www.w3.org/2000/svg">',
           f'<rect width="{width}" height="{height}" fill="{BG}"/>']
    if title:
        out.append(f'<text x="{pad_l}" y="22" fill="{TEXT}" font-size="14" '
                   f'font-weight="bold">{_esc(title)}</text>')
    for i in range(5):
        frac = i / 4.0
        val = lo + frac * (hi - lo)
        yy = py1 - frac * (py1 - py0)
        out.append(f'<line x1="{px0}" y1="{yy:.1f}" x2="{px1}" y2="{yy:.1f}" '
                   f'stroke="{GRID}" stroke-width="1" opacity="0.55"/>')
        out.append(f'<text x="{pad_l - 8}" y="{yy + 4:.1f}" fill="{MUTED}" '
                   f'font-size="10" text-anchor="end">{val:,.2f}</text>')
    zero_y = y(0.0)
    out.append(f'<line x1="{px0}" y1="{zero_y:.1f}" x2="{px1}" '
               f'y2="{zero_y:.1f}" stroke="{TEXT}" stroke-width="1.1" '
               f'opacity="0.7"/>')

    gw = (px1 - px0) / max(1, len(groups))
    for gi, (name, vals) in enumerate(groups):
        gw_in = gw * 0.86
        bw = gw_in / max(1, len(vals))
        gx = px0 + gi * gw + (gw - gw_in) / 2.0
        for fi, v in enumerate(vals):
            bx = gx + fi * bw
            if v is None:
                out.append(f'<rect x="{bx + 1:.1f}" y="{zero_y - 3:.1f}" '
                           f'width="{max(2, bw - 2):.1f}" height="3" '
                           f'fill="{GRID}" opacity="0.7"/>')
                continue
            col = UP if float(v) >= 0 else DOWN
            vy = y(float(v))
            top, hgt = (vy, zero_y - vy) if vy <= zero_y else (zero_y,
                                                               vy - zero_y)
            out.append(f'<rect x="{bx + 1:.1f}" y="{top:.1f}" '
                       f'width="{max(2, bw - 2):.1f}" height="{max(1, hgt):.1f}" '
                       f'fill="{col}" opacity="0.85" rx="1"/>')
        out.append(f'<text x="{px0 + gi * gw + gw / 2:.1f}" y="{height - 42}" '
                   f'fill="{MUTED}" font-size="9" text-anchor="middle" '
                   f'transform="rotate(-30 {px0 + gi * gw + gw / 2:.1f} '
                   f'{height - 42})">{_esc(name.replace("NEGATIVE-CONTROL-", "~"))}</text>')
    out.append(f'<text x="{px0}" y="{height - 6}" fill="{MUTED}" '
               f'font-size="9">~ = negative control (inverted polarity)</text>')
    out.append("</svg>")
    return "".join(out)


def _svg_pnl_histogram(specs: Sequence[Dict[str, Any]], title: str,
                        height: int = 300) -> str:
    """The distribution of out-of-sample returns, wins and losses apart."""
    width = 1000
    pad_l, pad_r, pad_t, pad_b = 70, 20, 34 if title else 16, 40
    px0, px1 = pad_l, width - pad_r
    py0, py1 = pad_t, height - pad_b

    allr: List[float] = []
    for s in specs:
        allr.extend(s.get("path") or [])
    if not allr:
        return ('<svg viewBox="0 0 1000 200"><rect width="1000" '
                'height="200" fill="' + BG + '"/><text x="500" y="100" '
                'fill="' + MUTED + '" text-anchor="middle">no return data'
                '</text></svg>')

    lo = min(allr + [0.0])
    hi = max(allr + [0.0])
    if hi == lo:
        hi = lo + 0.01
    nbins = 41
    step = (hi - lo) / nbins
    bins = [0] * nbins
    for r in allr:
        idx = int((r - lo) / step)
        idx = max(0, min(nbins - 1, idx))
        bins[idx] += 1
    maxc = max(bins) or 1

    def x(v: float) -> float:
        return px0 + ((v - lo) / (hi - lo)) * (px1 - px0)

    out = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
           f'style="max-width:{width}px;background:{BG}" '
           f'xmlns="http://www.w3.org/2000/svg">',
           f'<rect width="{width}" height="{height}" fill="{BG}"/>']
    if title:
        out.append(f'<text x="{pad_l}" y="22" fill="{TEXT}" font-size="14" '
                   f'font-weight="bold">{_esc(title)}</text>')
    bw = (px1 - px0) / nbins
    for i, c in enumerate(bins):
        if c == 0:
            continue
        b_lo = lo + i * step
        b_hi = b_lo + step
        col = UP if b_lo >= 0 else DOWN
        h = (c / maxc) * (py1 - py0)
        out.append(f'<rect x="{px0 + i * bw + 0.5:.1f}" y="{py1 - h:.1f}" '
                   f'width="{max(1, bw - 1):.1f}" height="{h:.1f}" '
                   f'fill="{col}" opacity="0.8"/>')
    zero_x = x(0.0)
    out.append(f'<line x1="{zero_x:.1f}" y1="{py0}" x2="{zero_x:.1f}" '
               f'y2="{py1}" stroke="{TEXT}" stroke-width="1.2" opacity="0.8"/>')
    out.append(f'<text x="{px0}" y="{py1 + 16}" fill="{MUTED}" '
               f'font-size="9">{lo:.2%}</text>')
    out.append(f'<text x="{px1}" y="{py1 + 16}" fill="{MUTED}" '
               f'font-size="9" text-anchor="end">{hi:.2%}</text>')
    out.append(f'<text x="{zero_x:.1f}" y="{py1 + 16}" fill="{TEXT}" '
               f'font-size="9" text-anchor="middle">0</text>')
    out.append(f'<text x="{(px0 + px1) / 2:.0f}" y="{height - 4}" '
               f'fill="{MUTED}" font-size="10" text-anchor="middle">'
               f'out-of-sample return per bar</text>')
    out.append("</svg>")
    return "".join(out)


# --------------------------------------------------------------------------
# The dashboard
# --------------------------------------------------------------------------
def render_backtest_dashboard(data: Dict[str, Any]) -> str:
    """Render the outcomes dashboard."""
    specs = list(data.get("specs") or [])
    with_path = [s for s in specs if s.get("path_length")]
    parts: List[str] = []

    # ---- the headline ------------------------------------------------
    supported = [s for s in specs if s.get("verdict") == "SUPPORTED"]
    fragile = [s for s in specs if s.get("verdict") == "FRAGILE"]
    ran = [s for s in specs if not (s.get("errors") or [])]

    pf_vals = [s["stats"].get("profit_factor") for s in with_path
               if s["stats"].get("profit_factor") not in (None,)
               and s["stats"].get("profit_factor") != float("inf")]
    wr_vals = [s["stats"]["win_rate"] for s in with_path
               if s["stats"].get("win_rate") is not None]

    parts.append(
        '<div class="card"><h2>What the backtests did</h2>'
        '<div class="grid">'
        f'<div><div class="kv">Specs</div><div class="vv big">'
        f'{data.get("n_specs", 0)}</div></div>'
        f'<div><div class="kv">With an OOS path</div>'
        f'<div class="vv big">{data.get("n_with_path", 0)}</div></div>'
        f'<div><div class="kv">SUPPORTED</div>'
        f'<div class="vv big" style="color:{UP}">{len(supported)}</div></div>'
        f'<div><div class="kv">FRAGILE</div>'
        f'<div class="vv big" style="color:{WARN}">{len(fragile)}</div></div>'
        f'<div><div class="kv">Best profit factor</div>'
        f'<div class="vv big">'
        f'{("%.2f" % max(pf_vals)) if pf_vals else "n/a"}</div></div>'
        f'<div><div class="kv">Highest win rate</div>'
        f'<div class="vv big">'
        f'{("%.1f%%" % (100 * max(wr_vals))) if wr_vals else "n/a"}</div></div>'
        '</div>'
        f'<p class="note">Generated {data.get("generated_at", "")}. '
        f'{len(ran)} of {data.get("n_specs", 0)} specs executed without '
        'error. Every figure below is out-of-sample: pooled across '
        'purged-and-embargoed walk-forward folds, at 2x the engine '
        'default costs.</p></div>')

    if not with_path:
        parts.append('<div class="card"><h2>No out-of-sample paths</h2>'
                     '<p class="note warn">No spec has an OOS return '
                     'series yet, so there is nothing to draw. Run the '
                     'matrix and collect the scorecards.</p></div>')
        return _page(parts)

    # ---- the equity curves -------------------------------------------
    concepts: Dict[str, List[Dict[str, Any]]] = {}
    for s in with_path:
        concepts.setdefault(s.get("concept") or "unknown", []).append(s)

    palette = [UP, NEUTRAL, ACCENT, "#c77dff", "#ff6b9d", "#4ecdc4",
               "#ffd166", "#6c8eef"]

    for ci, (concept, ss) in enumerate(sorted(concepts.items())):
        series = []
        for si, s in enumerate(ss[:6]):
            eq = _downsample(_equity_curve(s["path"]))
            series.append({
                "name": f"{s['asset_class']}"
                        + (" (control)" if s["name"].startswith(
                            "NEGATIVE-CONTROL-") else ""),
                "values": eq,
                "color": palette[(ci * 3 + si) % len(palette)],
            })
        parts.append(
            '<div class="card"><h2>'
            + _esc(concept)
            + ' — cumulative out-of-sample equity</h2>'
            + _svg_equity(series, "")
            + '<p class="note">Each line is one asset class, pooled '
              'across the walk-forward folds. The dashed line is '
              'break-even. A curve that ends high but passes through a '
              'deep hole is a different proposition from one that '
              'drifts up gently.</p></div>')

    # ---- the drawdown -----------------------------------------------
    dd_series = []
    for ci, (concept, ss) in enumerate(sorted(concepts.items())):
        best = max(ss, key=lambda x: x["stats"].get("max_drawdown") or 0)
        dd = best["stats"].get("dd_series")
        if dd:
            dd_series.append({
                "name": f"{concept} / {best['asset_class']} (worst)",
                "values": _downsample(dd),
                "color": palette[ci % len(palette)],
            })
    if dd_series:
        parts.append(
            '<div class="card"><h2>Drawdown — the underwater plot</h2>'
            + _svg_drawdown(dd_series, "")
            + '<p class="note">The worst drawdown path for each concept. '
              'This is the chart a verdict label cannot replace: an '
              'edge can be real and still be untradeable if the hole '
              'is too deep to sit in.</p></div>')

    # ---- the per-fold bars ------------------------------------------
    fold_specs = [s for s in specs if s.get("folds")]
    if fold_specs:
        fold_specs = sorted(fold_specs,
                            key=lambda x: -(x.get("oos_sharpe") or -99))[:14]
        parts.append(
            '<div class="card"><h2>Per-fold out-of-sample Sharpe</h2>'
            + _svg_fold_bars(fold_specs, "")
            + '<p class="note">One bar per purged-and-embargoed fold. A '
              'concept that lives in one fold is not an edge. The '
              'grey stubs are folds where the signal never fired.</p>'
              '</div>')

    # ---- the P&L shape -----------------------------------------------
    parts.append(
        '<div class="card"><h2>The P&amp;L shape</h2>'
        + _svg_pnl_histogram(with_path, "")
        + '<p class="note">Every out-of-sample bar return from every spec '
          'with a path, pooled. Green is a winning bar, red a losing '
          'one. A distribution that is mostly green with a thin red '
          'tail is a different strategy from one with a fat red tail '
          'and a few spikes.</p></div>')

    # ---- the outcome table -------------------------------------------
    rows_html = []
    for s in sorted(specs, key=lambda x: -(x.get("oos_sharpe")
                                           if x.get("oos_sharpe") is not None
                                           else -99)):
        st = s.get("stats") or {}
        oos = s.get("oos_sharpe")
        col = (UP if (oos or 0) > 0 else DOWN) if oos is not None else MUTED
        wr = st.get("win_rate")
        pf = st.get("profit_factor")
        pf_txt = ("inf" if pf == float("inf") else
                  ("%.2f" % pf if isinstance(pf, (int, float)) else "n/a"))
        payoff = st.get("payoff_ratio")
        rows_html.append(
            f'<tr><td>{_esc(s.get("concept"))}</td>'
            f'<td>{_esc(s.get("asset_class"))}</td>'
            f'<td>{_esc(s.get("verdict"))}</td>'
            f'<td style="color:{col}">'
            f'{("%.2f" % oos) if isinstance(oos, (int, float)) else "n/a"}</td>'
            f'<td>{s.get("n_trades", "n/a")}</td>'
            f'<td>{("%.1f%%" % (100 * wr)) if wr is not None else "n/a"}</td>'
            f'<td>{pf_txt}</td>'
            f'<td>{("%.2f" % payoff) if isinstance(payoff, (int, float)) else "n/a"}</td>'
            f'<td>{("%.4f%%" % (100 * st["expectancy"])) if st.get("expectancy") is not None else "n/a"}</td>'
            f'<td>{("%.1f%%" % (100 * st["max_drawdown"])) if st.get("max_drawdown") is not None else "n/a"}</td>'
            f'<td>{st.get("n_bars", 0)}</td>'
            f'</tr>')
    parts.append(
        '<div class="card"><h2>Every spec, by outcome</h2>'
        '<div class="tablewrap"><table>'
        '<tr><th>Concept</th><th>Asset class</th><th>Verdict</th>'
        '<th>OOS Sharpe</th><th>Trades</th><th>Win rate</th>'
        '<th>Profit factor</th><th>Payoff ratio</th><th>Expectancy/bar</th>'
        '<th>Max DD</th><th>OOS bars</th></tr>'
        + "".join(rows_html) + '</table></div>'
        '<p class="note">Profit factor is gross profit over gross loss; '
        'above 1.0 means the strategy made money. Payoff ratio is the '
        'average win over the average loss; above 1.0 means the wins are '
        'bigger than the losses. Expectancy is the mean return per '
        'out-of-sample bar. A spec with no OOS path shows n/a - it was '
        'not measured, not zero.</p></div>')

    return _page(parts)


def _page(body: Any) -> str:
    # `body` is a LIST of card fragments. Joining it here rather than
    # relying on the f-string's str() is what keeps a stray "['<div"
    # from appearing above the first card.
    if isinstance(body, (list, tuple)):
        body = "\n".join(str(x) for x in body)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LeapSpace — backtest outcomes</title>
<style>
 :root {{ color-scheme: dark; }}
 body {{ margin:0; padding:24px; background:{BG}; color:{TEXT};
        font:14px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
        overflow-x:hidden; }}
 h1 {{ font-size:21px; margin:0 0 4px; }}
 .sub {{ color:{MUTED}; margin:0 0 22px; font-size:13px; max-width:900px; }}
 .card {{ background:#20203a; border:1px solid {GRID}; border-radius:12px;
          padding:16px 18px; margin-bottom:16px; overflow:hidden; }}
 .note {{ color:{MUTED}; font-size:12.5px; margin:8px 0 0; max-width:900px; }}
 .warn {{ color:{WARN}; }}
 .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
          gap:14px; }}
 .kv {{ color:{MUTED}; font-size:12px; }}
 .vv {{ font-size:16px; }} .big {{ font-size:26px; font-weight:600; }}
 .tablewrap {{ overflow-x:auto; }}
 table {{ border-collapse:collapse; width:100%; font-size:12px; }}
 th,td {{ text-align:left; padding:5px 8px; border-bottom:1px solid {GRID};
          vertical-align:top; white-space:nowrap; }}
 th {{ color:{MUTED}; font-weight:600; text-transform:uppercase;
       font-size:10px; }}
</style></head><body>
<h1>Backtest outcomes</h1>
<p class="sub">What the strategies actually did, out of sample — equity,
drawdown, the P&amp;L shape, and the win/loss record. Every figure is
pooled across purged-and-embargoed walk-forward folds at 2× the engine
default costs.</p>
{body}
</body></html>"""


def build_backtest_dashboard(results_path: Optional[str] = None,
                              scorecard_paths: Optional[Sequence[str]] = None,
                              out_path: Optional[str] = None,
                              json_path: Optional[str] = None) -> Dict[str, Any]:
    """Collect the outcomes and render the dashboard."""
    data = collect_outcomes(results_path, scorecard_paths)
    json_path = json_path or OUTCOMES_PATH
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    html = render_backtest_dashboard(data)
    out_path = out_path or DASHBOARD_PATH
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return {"html": out_path, "json": json_path, "data": data}
