"""Charts for the memecoin-trader half of the package.

These are the charts that make the gate's behaviour VISIBLE, which
matters because the gate's most important finding is a collapse that a
table of numbers hides: a wallet's 179 closed trades are ONE
independent bet.

Five charts:
  edge_gate.png         - per wallet: raw closed trades vs independent
                           bets, the verdict, realised PnL
  whitelist.png         - status counts and the promotion/retirement
                           timeline
  price_accuracy.png    - the price-at-block method against the known
                           reference prices
  criteria_coverage.png - which of the 31 cited criteria are enforced
  community_series.png  - the community-size series as it accrues
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence

from .viz import _save, _style

# The house palette (trading-visualization dark theme).
BG = "#1a1a2e"
FG = "#e8e8e8"
MUTED = "#9aa0b4"
GREEN = "#2ecc71"
RED = "#e74c3c"
BLUE = "#3498db"
AMBER = "#f39c12"
PURPLE = "#9b59b6"
GRID = "#2a2a44"

VERDICT_COLOR = {
    "CONSISTENT": GREEN,
    "WEAK": AMBER,
    "FLUKE": RED,
    "INSUFFICIENT": MUTED,
}


def _fig(w: float = 11.0, h: float = 6.0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _style()
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.title.set_color(FG)
    return fig, ax


def _addr(a: str) -> str:
    return (a or "")[:10] + "…" if len(a or "") > 11 else (a or "")


def chart_edge_gate(results: Sequence[Dict[str, Any]], path: str
                    ) -> Optional[str]:
    """The key chart: raw closed trades vs INDEPENDENT BETS, per wallet.

    This is where the gate's finding becomes visible. A wallet with 179
    closed trades may have ONE independent bet, and the statistical
    tests use the smaller number. Plotting both side by side makes the
    collapse impossible to miss.
    """
    rows = [r for r in results if r.get("address")]
    if not rows:
        return None
    import matplotlib.pyplot as plt
    import numpy as np

    rows = sorted(rows, key=lambda r: -(r.get("n_closed") or 0))
    labels = [_addr(r.get("address")) for r in rows]
    raw = [r.get("n_closed") or 0 for r in rows]
    bets = [r.get("n_bets_closed") or 0 for r in rows]
    colors = [VERDICT_COLOR.get(r.get("verdict"), MUTED) for r in rows]
    x = np.arange(len(rows))
    w = 0.38

    fig, ax = _fig(12.5, 6.8)
    b1 = ax.bar(x - w / 2, raw, w, label="raw closed trades",
                color=BLUE, alpha=0.75)
    b2 = ax.bar(x + w / 2, bets, w, label="INDEPENDENT BETS (the "
                "statistical sample)", color=GREEN, alpha=0.9)
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("count   (symlog: 1, 10, 100 …)")
    ax.set_title("The gate's key finding: raw trades collapse to "
                 "independent bets\n"
                 "the statistical tests use the SMALLER number",
                 fontsize=12)
    ax.grid(axis="y", color=GRID, alpha=0.5)
    ax.set_axisbelow(True)
    leg = ax.legend(loc="upper right", fontsize=9, facecolor=BG,
                    edgecolor=GRID)
    for t in leg.get_texts():
        t.set_color(FG)

    # The verdict goes UNDER the rotated address label, so it needs its
    # own row of space rather than sharing the axis line.
    for i, r in enumerate(rows):
        ax.text(i, -0.30, str(r.get("verdict") or "")[:11],
                ha="center", va="top", fontsize=7.5,
                color=VERDICT_COLOR.get(r.get("verdict"), MUTED),
                transform=ax.get_xaxis_transform(), clip_on=False)
        if not (r.get("n_closed") or 0):
            ax.text(i, 1.15, "no closed\ntrades", ha="center", va="bottom",
                    fontsize=7, color=MUTED, rotation=90)

    fig.text(0.01, 0.012,
             "Source: reports/pepe_priced_edge.json  |  prices read from "
             "Uniswap V2 pair reserves at each trade's own block  |  "
             "survivorship-selected sample: these wallets still HOLD the "
             "token",
             fontsize=7.5, color=MUTED)
    # Enough room for the rotated labels AND the verdict row beneath.
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    return _save(fig, path)


def chart_whitelist(wl: Dict[str, Any], path: str) -> Optional[str]:
    """Whitelist status counts and the promotion/retirement timeline."""
    entries = wl.get("entries") or {}
    events = wl.get("events") or []
    if not entries and not events:
        return None
    import matplotlib.pyplot as plt
    import numpy as np

    statuses: Dict[str, int] = {}
    for e in entries.values():
        s = e.get("status") or "UNKNOWN"
        statuses[s] = statuses.get(s, 0) + 1

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(12.5, 5.6),
        gridspec_kw={"width_ratios": [1, 2.2]})
    fig.patch.set_facecolor(BG)
    for ax in (ax1, ax2):
        ax.set_facecolor(BG)
        for s in ax.spines.values():
            s.set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9)
        ax.title.set_color(FG)
        ax.grid(axis="y", color=GRID, alpha=0.5)
        ax.set_axisbelow(True)

    if statuses:
        names = list(statuses)
        vals = [statuses[n] for n in names]
        cols = [VERDICT_COLOR.get(n, MUTED) for n in names]
        ax1.bar(range(len(names)), vals, color=cols, alpha=0.9)
        ax1.set_xticks(range(len(names)))
        ax1.set_xticklabels(names, rotation=30, ha="right", fontsize=8)
        for i, v in enumerate(vals):
            ax1.text(i, v, str(v), ha="center", va="bottom",
                     color=FG, fontsize=9)
    ax1.set_ylabel("wallets")
    ax1.set_title("Registry status", fontsize=11)

    if events:
        acts = [str(e.get("action")) for e in events]
        uniq = sorted(set(acts))
        cmap = {"promote": GREEN, "reject": RED, "retire": AMBER,
                "watch": BLUE}
        for i, e in enumerate(events):
            a = str(e.get("action"))
            ax2.scatter(i, 0, s=70, color=cmap.get(a, MUTED),
                        edgecolors="none", zorder=3)
        ax2.set_yticks([])
        ax2.set_ylim(-1, 1)
        ax2.set_xlabel("evaluation sequence")
        ax2.set_title("Promotion / rejection / retirement timeline",
                      fontsize=11)
        # A legend of the action colours.
        handles = []
        for a in uniq:
            handles.append(plt.Line2D([], [], marker="o", linestyle="",
                                       color=cmap.get(a, MUTED),
                                       label=a))
        leg = ax2.legend(handles=handles, loc="upper left", fontsize=8,
                         facecolor=BG, edgecolor=GRID, ncol=len(uniq))
        for t in leg.get_texts():
            t.set_color(FG)

    fig.text(0.01, 0.015,
             "History is NEVER deleted (CFA Institute GIPS 3.A.9): a "
             "retired wallet leaves the forward cohort but its record "
             "stays.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)


def chart_price_accuracy(path: str) -> Optional[str]:
    """The price-at-block method against the known reference prices.

    The figures are the MEASURED ones. The pool's spot price is not the
    same as the aggregate index price — it is the price the wallet would
    actually have got — and the gap grows when the pool was shallow.
    """
    measured = [
        ("PEPE\n2024-01-01", 1.2370e-06, 1.29e-06),
        ("PEPE\n2025-01-01", 1.8291e-05, 1.984e-05),
        ("PEPE\n2023-06-01", 1.6065e-06, 1.26e-06),
        ("SHIB\n2024-01-01", 9.7679e-06, 9.5e-06),
    ]
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = _fig(11.0, 5.8)
    x = np.arange(len(measured))
    ours = [m[1] for m in measured]
    ref = [m[2] for m in measured]
    ax.bar(x - 0.2, ours, 0.4, label="pool price at the trade's block",
           color=GREEN, alpha=0.9)
    ax.bar(x + 0.2, ref, 0.4, label="reference (index price)",
           color=MUTED, alpha=0.8)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([m[0] for m in measured], fontsize=9)
    ax.set_ylabel("price (USD, log scale)")
    ax.set_title("Historical price at a past block, read from the DEX "
                 "itself\n"
                 "no price API, no rate limit, the true execution price",
                 fontsize=12)
    ax.grid(axis="y", color=GRID, alpha=0.5)
    ax.set_axisbelow(True)
    for i, (m, o, r) in enumerate(measured):
        err = abs(o - r) / r * 100
        ax.text(i, max(o, r) * 1.35, f"{err:.1f}%", ha="center",
                fontsize=9, color=AMBER)
    leg = ax.legend(loc="lower left", fontsize=9, facecolor=BG,
                    edgecolor=GRID)
    for t in leg.get_texts():
        t.set_color(FG)
    fig.text(0.01, 0.015,
             "A pool whose quote side is below the liquidity floor is "
             "REJECTED, never priced — a nearly-empty pool cannot "
             "manufacture a price.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)


def chart_criteria_coverage(rows: Sequence[Dict[str, Any]], path: str
                            ) -> Optional[str]:
    """Which of the cited criteria are actually enforced in code."""
    if not rows:
        return None
    import matplotlib.pyplot as plt
    import numpy as np

    enforced = [r for r in rows if r.get("enforced")]
    missing = [r for r in rows if not r.get("enforced")]
    fig, ax = _fig(11.5, 5.8)
    labels = ([f"enforced ({len(enforced)})"] +
              [f"gap ({len(missing)})"])
    vals = [len(enforced), len(missing)]
    ax.bar([0, 1], vals, color=[GREEN, RED], alpha=0.9, width=0.55)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("criteria")
    ax.set_title("Enforcement of the cited criteria\n"
                 "a criterion that is documented but not enforced is a "
                 "gap, and is shown as one", fontsize=12)
    ax.grid(axis="y", color=GRID, alpha=0.5)
    ax.set_axisbelow(True)
    for i, v in enumerate(vals):
        ax.text(i, v, str(v), ha="center", va="bottom", color=FG,
                fontsize=13)
    if missing:
        ax.text(0.5, -0.22, "still to enforce: " +
                ", ".join(str(m.get("key")) for m in missing[:6]) +
                (" …" if len(missing) > 6 else ""),
                ha="center", va="top", fontsize=7.5, color=AMBER,
                transform=ax.get_xaxis_transform())
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    return _save(fig, path)


def chart_community_series(series_by_token: Dict[str, Any], path: str
                           ) -> Optional[str]:
    """The community-size series as it accrues.

    There is NO keyless source for a historical member count - Telegram's
    public preview shows the current count only - so this series has to
    be COLLECTED. Until it has enough points, the lead-time test has no
    empirical distribution, and this chart is the honest picture of that.
    """
    usable = {k: v for k, v in (series_by_token or {}).items()
              if len(v or []) >= 2}
    if not usable:
        return None
    import matplotlib.pyplot as plt
    import numpy as np
    import time as _t

    fig, ax = _fig(11.5, 5.8)
    for name, snaps in list(usable.items())[:10]:
        ts = [s.get("ts") for s in snaps if s.get("ts")]
        tg = [s.get("telegram_members") for s in snaps if s.get("ts")]
        dc = [s.get("discord_members") for s in snaps if s.get("ts")]
        pairs = [(a, b) for a, b in zip(ts, tg) if a and b is not None]
        if len(pairs) >= 2:
            xs = [a for a, _b in pairs]
            ys = [b for _a, b in pairs]
            ax.plot(xs, ys, marker="o", linewidth=2, label=f"{name} TG")
        pairs = [(a, b) for a, b in zip(ts, dc) if a and b is not None]
        if len(pairs) >= 2:
            xs = [a for a, _b in pairs]
            ys = [b for _a, b in pairs]
            ax.plot(xs, ys, marker="s", linewidth=1.6, linestyle="--",
                    label=f"{name} DC")
    ax.set_ylabel("members")
    ax.set_title("Community-size series, as it is COLLECTED\n"
                 "no keyless source exists for a historical member count",
                 fontsize=12)
    ax.grid(color=GRID, alpha=0.5)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(
        matplotlib.dates.DateFormatter("%m-%d %H:%M")
        if False else plt.FuncFormatter(
            lambda v, _p: _t.strftime("%m-%d %H:%M", _t.localtime(v))))
    leg = ax.legend(loc="upper left", fontsize=8, facecolor=BG,
                    edgecolor=GRID, ncol=2)
    for t in leg.get_texts():
        t.set_color(FG)
    fig.text(0.01, 0.015,
             "A nonexistent Telegram channel still returns HTTP 200 — the "
             "title reads 'Contact @name' instead of 'View @name'. An "
             "unmeasurable platform is recorded as UNMEASURED, never zero.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, path)
