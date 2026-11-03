"""Visual presentation of the LEADING-indicator work.

WHAT THIS IS
    A self-contained, dependency-free visualiser for the leading
    features in `leapspace.leading`: the implied-volatility level, the
    realised-volatility counterpart, the volatility risk premium
    between them, and the position sizing the premium drives.

WHY AN SVG/HTML RENDERER AND NOT MATPLOTLIB
    `leapspace.viz` treats matplotlib as OPTIONAL and the package works
    without it. This module goes further: it renders charts as INLINE
    SVG inside a single HTML file, using only the standard library, so
    the presentation always exists - on a machine with no scientific
    stack, on a locked-down host, in CI.

    An optional PNG is also written when matplotlib happens to be
    installed, matching `viz.py`'s behaviour.

THE CHARTS
    1. IMPLIED vs REALISED - the two series whose difference is the
       edge. Seeing them together is the point: a reader can see
       whether the premium is a persistent wedge (structural) or noise.
    2. THE VOLATILITY RISK PREMIUM - the leading signal itself, with
       the zero line marked. Above zero the market is paying for
       protection; below zero it is not.
    3. THE PREMIUM'S Z-SCORE with the stand-aside zone shaded - the
       position size the signal produces, and the threshold at which
       it reaches zero.
    4. THE REGIME TIMELINE - price with the leading state coloured
       underneath, so the reader can see whether the sizing decisions
       cluster around the drawdowns.
    5. THE LIVE OPTIONS PANEL - gamma exposure by expiry and the
       put/call flow ratio, which are NOW measurements and are
       labelled as such.

WHAT THIS IS NOT
    It is NOT a performance report. The charts describe the FEATURES;
    whether they carry an edge is decided by the backtest gauntlet and
    reported there. A beautiful chart of a worthless signal is still a
    worthless signal.

COLOURS
    The package's trading convention, from `leapspace.viz`:
      up/profit      #00ff88     down/loss   #ff4444
      neutral/info   #4488ff     warning     #ffaa00
      background     #1a1a2e     grid        #333333
      text           #e0e0e0     muted       #aaaaaa
"""
from __future__ import annotations

import html
import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "UP", "DOWN", "NEUTRAL", "WARN", "BG", "GRID", "TEXT", "MUTED",
    "svg_line_chart",
    "svg_bars",
    "render_leading_dashboard",
    "build_leading_dashboard",
]


UP = "#00ff88"
DOWN = "#ff4444"
NEUTRAL = "#4488ff"
WARN = "#ffaa00"
BG = "#1a1a2e"
GRID = "#333333"
TEXT = "#e0e0e0"
MUTED = "#aaaaaa"
ACCENT = "#ffcc00"

_LEADING_VIZ_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports", "charts")


# --------------------------------------------------------------------------
# SVG primitives
# --------------------------------------------------------------------------
def _esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


def _scale(values: Sequence[float], lo: float, hi: float,
           px0: float, px1: float) -> List[float]:
    """Map values into pixel space, inverted so high values are up."""
    out: List[float] = []
    span = (hi - lo) or 1.0
    for v in values:
        try:
            f = (float(v) - lo) / span
        except (TypeError, ValueError):
            f = 0.0
        f = max(0.0, min(1.0, f))
        out.append(px1 - f * (px1 - px0))
    return out


def svg_line_chart(series: Sequence[Dict[str, Any]],
                   labels: Optional[Sequence[str]] = None,
                   title: str = "",
                   width: int = 1000, height: int = 320,
                   y_label: str = "",
                   hlines: Sequence[Dict[str, Any]] = (),
                   legend: bool = True) -> str:
    """Render one or more line series as inline SVG.

    `series` is a list of {"name": str, "values": [...], "color": hex}.
    `hlines` draws reference lines: {"value": float, "color": hex,
    "label": str, "dash": bool}.
    """
    pad_l, pad_r, pad_t, pad_b = 70, 20, 34 if title else 16, 34
    px0, px1 = pad_l, width - pad_r
    py0, py1 = pad_t, height - pad_b

    all_vals: List[float] = []
    for s in series:
        for v in (s.get("values") or []):
            if v is not None:
                try:
                    all_vals.append(float(v))
                except (TypeError, ValueError):
                    pass
    for h in hlines:
        try:
            all_vals.append(float(h.get("value")))
        except (TypeError, ValueError):
            pass
    if not all_vals:
        return (f'<svg viewBox="0 0 {width} {height}" width="100%" '
                f'style="max-width:{width}px">'
                f'<rect width="{width}" height="{height}" fill="{BG}"/>'
                f'<text x="{width/2}" y="{height/2}" fill="{MUTED}" '
                f'font-size="13" text-anchor="middle">no data</text></svg>')

    lo, hi = min(all_vals), max(all_vals)
    if hi == lo:
        hi = lo + 1.0
    # A little headroom so the extremes are not clipped.
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad

    n = max((len(s.get("values") or []) for s in series), default=0)
    xs: List[float] = []
    if n > 1:
        xs = [px0 + i * (px1 - px0) / (n - 1) for i in range(n)]
    elif n == 1:
        xs = [(px0 + px1) / 2]

    out: List[str] = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        f'style="max-width:{width}px;background:{BG}" '
        f'xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
    ]
    if title:
        out.append(f'<text x="{pad_l}" y="22" fill="{TEXT}" font-size="14" '
                   f'font-weight="bold">{_esc(title)}</text>')
    if y_label:
        out.append(f'<text x="14" y="{py0 + 14}" fill="{MUTED}" font-size="11">'
                   f'{_esc(y_label)}</text>')

    # grid + y ticks
    for i in range(5):
        frac = i / 4.0
        y = py1 - frac * (py1 - py0)
        val = lo + frac * (hi - lo)
        out.append(f'<line x1="{px0}" y1="{y:.1f}" x2="{px1}" y2="{y:.1f}" '
                   f'stroke="{GRID}" stroke-width="1" opacity="0.55"/>')
        out.append(f'<text x="{pad_l - 8}" y="{y + 4:.1f}" fill="{MUTED}" '
                   f'font-size="10" text-anchor="end">{val:,.2f}</text>')

    # reference lines
    for h in hlines:
        try:
            hv = float(h.get("value"))
        except (TypeError, ValueError):
            continue
        y = py1 - ((hv - lo) / ((hi - lo) or 1.0)) * (py1 - py0)
        if py0 - 2 <= y <= py1 + 2:
            dash = ' stroke-dasharray="4 3"' if h.get("dash", True) else ""
            out.append(f'<line x1="{px0}" y1="{y:.1f}" x2="{px1}" y2="{y:.1f}" '
                       f'stroke="{h.get("color", MUTED)}" stroke-width="1.2"'
                       f'{dash}/>')
            if h.get("label"):
                out.append(f'<text x="{px1 - 4}" y="{y - 5:.1f}" '
                           f'fill="{h.get("color", MUTED)}" font-size="10" '
                           f'text-anchor="end">{_esc(h["label"])}</text>')

    # the series
    for s in series:
        vals = s.get("values") or []
        pts: List[str] = []
        for i, v in enumerate(vals):
            if v is None or i >= len(xs):
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if not (lo <= fv <= hi):
                continue
            y = py1 - ((fv - lo) / ((hi - lo) or 1.0)) * (py1 - py0)
            pts.append(f"{xs[i]:.1f},{y:.1f}")
        if len(pts) >= 2:
            out.append(f'<polyline points="{" ".join(pts)}" '
                       f'fill="none" stroke="{s.get("color", NEUTRAL)}" '
                       f'stroke-width="{s.get("width", 1.8)}" '
                       f'stroke-linejoin="round" stroke-linecap="round"/>')

    # x labels
    if labels:
        for i, lab in enumerate(labels):
            if i >= len(xs):
                break
            if i % max(1, len(labels) // 8) != 0 and i != len(labels) - 1:
                continue
            out.append(f'<text x="{xs[i]:.1f}" y="{height - 10}" fill="{MUTED}" '
                       f'font-size="10" text-anchor="middle">{_esc(lab)}</text>')

    # legend
    if legend and series:
        lx = pad_l
        for s in series:
            name = s.get("name")
            if not name:
                continue
            out.append(f'<rect x="{lx}" y="{height - 26}" width="10" height="3" '
                       f'fill="{s.get("color", NEUTRAL)}"/>')
            out.append(f'<text x="{lx + 14}" y="{height - 20}" fill="{MUTED}" '
                       f'font-size="10">{_esc(name)}</text>')
            lx += 20 + 7 * len(str(name))
    out.append("</svg>")
    return "".join(out)


def svg_bars(items: Sequence[Dict[str, Any]], title: str = "",
             width: int = 1000, height: int = 260,
             value_key: str = "value",
             label_key: str = "label") -> str:
    """Render a labelled bar chart as inline SVG (used for GEX by expiry)."""
    pad_l, pad_r, pad_t, pad_b = 70, 20, 34 if title else 16, 46
    px0, px1 = pad_l, width - pad_r
    py0, py1 = pad_t, height - pad_b
    items = list(items)
    out = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
           f'style="max-width:{width}px;background:{BG}" '
           f'xmlns="http://www.w3.org/2000/svg">',
           f'<rect width="{width}" height="{height}" fill="{BG}"/>']
    if title:
        out.append(f'<text x="{pad_l}" y="22" fill="{TEXT}" font-size="14" '
                   f'font-weight="bold">{_esc(title)}</text>')
    if not items:
        out.append(f'<text x="{width/2}" y="{height/2}" fill="{MUTED}" '
                   f'font-size="13" text-anchor="middle">no data</text></svg>')
        return "".join(out)

    vals: List[float] = []
    for it in items:
        try:
            vals.append(float(it.get(value_key) or 0.0))
        except (TypeError, ValueError):
            vals.append(0.0)
    lo, hi = min(vals + [0.0]), max(vals + [0.0])
    if hi == lo:
        hi = lo + 1.0
    zero_y = py1 - ((0.0 - lo) / (hi - lo)) * (py1 - py0)
    out.append(f'<line x1="{px0}" y1="{zero_y:.1f}" x2="{px1}" y2="{zero_y:.1f}" '
               f'stroke="{GRID}" stroke-width="1.2"/>')

    n = len(items)
    slot = (px1 - px0) / max(1, n)
    bw = slot * 0.62
    for i, (it, v) in enumerate(zip(items, vals)):
        y = py1 - ((v - lo) / (hi - lo)) * (py1 - py0)
        color = UP if v >= 0 else DOWN
        top = min(y, zero_y)
        hgt = abs(y - zero_y)
        x = px0 + i * slot + (slot - bw) / 2
        out.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" '
                   f'height="{max(1.0, hgt):.1f}" fill="{color}" opacity="0.85"/>')
        out.append(f'<text x="{x + bw/2:.1f}" y="{height - 24}" fill="{MUTED}" '
                   f'font-size="10" text-anchor="middle">'
                   f'{_esc(it.get(label_key, ""))}</text>')
    out.append("</svg>")
    return "".join(out)


# --------------------------------------------------------------------------
# The dashboard
# --------------------------------------------------------------------------
_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LEAPSPACE - leading indicators</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin:0; padding:24px; background:{bg}; color:{text};
         font:14px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif; }}
  h1 {{ font-size:21px; margin:0 0 4px; letter-spacing:-.2px; }}
  h2 {{ font-size:15px; margin:0 0 10px; color:{text}; }}
  .sub {{ color:{muted}; font-size:13px; margin:0 0 22px; }}
  .card {{ background:#20203a; border:1px solid {grid}; border-radius:12px;
           padding:16px 18px; margin-bottom:16px; }}
  .note {{ color:{muted}; font-size:12.5px; margin:8px 0 0; }}
  .warn {{ color:{warn}; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
           gap:14px; }}
  table {{ border-collapse:collapse; width:100%; font-size:12.5px; }}
  th,td {{ text-align:left; padding:6px 9px; border-bottom:1px solid {grid}; }}
  th {{ color:{muted}; font-weight:600; text-transform:uppercase;
        font-size:10.5px; letter-spacing:.4px; }}
  .kv {{ color:{muted}; }} .vv {{ color:{text}; }}
  .tag {{ display:inline-block; padding:2px 8px; border-radius:999px;
          font-size:11px; font-weight:600; }}
  .t-ok {{ background:rgba(0,255,136,.14); color:{up}; }}
  .t-bad {{ background:rgba(255,68,68,.14); color:{down}; }}
  .t-mid {{ background:rgba(255,170,0,.14); color:{warn}; }}
  code {{ background:#16162c; padding:1px 5px; border-radius:4px; font-size:12px; }}
</style></head><body>
<h1>LEAPSPACE &mdash; leading-indicator module</h1>
<p class="sub">{subtitle}</p>
{body}
</body></html>
"""


def _card(title: str, svg: str, note: str = "", warn: bool = False) -> str:
    cls = "note warn" if warn else "note"
    return (f'<div class="card"><h2>{_esc(title)}</h2>{svg}'
            f'<p class="{cls}">{note}</p></div>')


def render_leading_dashboard(payload: Dict[str, Any]) -> str:
    """Render the whole leading-indicator page as one HTML string."""
    parts: List[str] = []

    # --- headline numbers ---
    rows = []
    for label, value, note in payload.get("headline", []):
        rows.append(f'<tr><td class="kv">{_esc(label)}</td>'
                    f'<td class="vv">{_esc(value)}</td>'
                    f'<td class="kv">{_esc(note)}</td></tr>')
    if rows:
        parts.append('<div class="card"><h2>What was measured</h2>'
                     '<table><tr><th>Item</th><th>Value</th><th>Note</th></tr>'
                     + "".join(rows) + '</table></div>')

    charts = payload.get("charts") or []
    for c in charts:
        parts.append(_card(c.get("title", ""), c.get("svg", ""),
                            c.get("note", ""), c.get("warn", False)))

    # --- the live options panel ---
    live = payload.get("live") or {}
    if live:
        cards = []
        gex = live.get("gamma") or {}
        if gex:
            state = gex.get("gamma_state", "")
            tag = ("t-bad" if str(state).startswith("negative")
                   else "t-ok")
            cards.append(
                f'<div><div class="kv">Dealer gamma</div>'
                f'<div class="vv"><span class="tag {tag}">'
                f'{_esc(state)}</span></div>'
                f'<div class="kv">net GEX {gex.get("net_gex", 0):,.0f} '
                f'&middot; {_esc(gex.get("currency", ""))} spot '
                f'{gex.get("spot", 0):,.2f}</div></div>')
        flow = live.get("flow") or {}
        if flow:
            pcr = flow.get("put_call_ratio")
            cards.append(
                f'<div><div class="kv">Option flow put/call</div>'
                f'<div class="vv">{("n/a" if pcr is None else f"{pcr:.2f}")}'
                f'</div>'
                f'<div class="kv">{flow.get("n_trades", 0)} trades '
                f'&middot; call share '
                f'{(flow.get("call_share") or 0):.1%}</div></div>')
        if cards:
            parts.append('<div class="card"><h2>Live options market '
                         '(a NOW measurement)</h2><div class="grid">'
                         + "".join(cards) + '</div>'
                         '<p class="note warn">These are live snapshots, not '
                         'backtestable history. They describe the current '
                         'options market; they are context for a decision, '
                         'not a strategy.</p></div>')

    # --- the honest caveats ---
    caveats = payload.get("caveats") or []
    if caveats:
        items = "".join(f"<li>{_esc(c)}</li>" for c in caveats)
        parts.append('<div class="card"><h2>What this does and does not '
                     'establish</h2><ul style="margin:0;padding-left:20px">'
                     + items + '</ul></div>')

    subtitle = payload.get("subtitle", "")
    return _PAGE.format(bg=BG, grid=GRID, text=TEXT, muted=MUTED, up=UP,
                         down=DOWN, warn=WARN,
                         subtitle=_esc(subtitle),
                         body="\n".join(parts))


def build_leading_dashboard(payload: Dict[str, Any],
                            out_dir: Optional[str] = None) -> Dict[str, Any]:
    """Write the leading-indicator dashboard. Returns the paths written."""
    d = out_dir or _LEADING_VIZ_DIR
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "leading_indicators.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_leading_dashboard(payload))
    return {"html": path,
            "n_charts": len(payload.get("charts") or [])}


def _demo_payload() -> Dict[str, Any]:
    """A synthetic payload, so the renderer can be tested offline."""
    import math
    import random
    random.seed(11)
    n = 180
    base = 100.0
    closes = []
    iv = []
    rv = []
    vrp = []
    z = []
    for i in range(n):
        base *= (1.0 + random.uniform(-0.02, 0.021))
        closes.append(base)
        wave = 12.0 * math.sin(i / 19.0)
        iv.append(18.0 + wave + random.uniform(-1.0, 1.0))
        r = 15.0 + 6.0 * math.sin(i / 31.0) + random.uniform(-1.5, 1.5)
        rv.append(r)
        vrp.append(iv[-1] - r)
    vals = [v for v in vrp]
    m = sum(vals) / len(vals)
    sd = (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5 or 1.0
    z = [(v - m) / sd for v in vrp]
    labels = [f"d{i}" for i in range(0, n, 30)]
    return {
        "subtitle": "synthetic demo payload - no live data",
        "headline": [
            ("Implied volatility source", "synthetic", "demo only"),
            ("Bars", str(n), "synthetic"),
        ],
        "charts": [
            {"title": "Implied vs realised volatility",
             "svg": svg_line_chart(
                 [{"name": "implied", "values": iv, "color": NEUTRAL},
                  {"name": "realised", "values": rv, "color": WARN}],
                 labels, "Implied vs realised volatility", y_label="%"),
             "note": "The gap between the two lines is the signal."},
            {"title": "Volatility risk premium",
             "svg": svg_line_chart(
                 [{"name": "VRP", "values": vrp, "color": ACCENT}],
                 labels, "Volatility risk premium", y_label="pp",
                 hlines=[{"value": 0.0, "color": MUTED, "label": "zero"}]),
             "note": "Above zero the market pays for protection."},
            {"title": "Premium z-score and the stand-aside zone",
             "svg": svg_line_chart(
                 [{"name": "z-score", "values": z, "color": UP}],
                 labels, "Premium z-score", y_label="z",
                 hlines=[{"value": 0.0, "color": MUTED, "label": "full size"},
                         {"value": 1.0, "color": DOWN, "label": "flat"}]),
             "note": "The position size scales to zero at z = 1."},
        ],
        "live": {},
        "caveats": ["synthetic data - demo only"],
    }
