"""Stop-loss, trailing-stop and volatility-normalised exits.

WHY THIS EXISTS
    Ten of the 51 daily-testable, never-built claims are about stops:

      "A stop-loss combined with a momentum signal improves downside
       control without materially degrading momentum returns."
        - Trading strategies for retail traders

      "Crypto trends can reverse sharply; a volatility-normalised stop
       band is more useful than a fixed percentage stop."
      "Avoid a tight trailing stop - mean reversion needs room to
       revert."
      "Do not anchor the stop to the original entry - ratchet the stop
       up as the position moves in your favour."

    The shared engine had NO stop support at all. `friction.py`'s
    `stop_loss_pct` is a fixed percentage on a COPIED position in the
    copy-trading simulator - a different thing entirely. So these
    claims were not skipped for lack of data; they were never
    implemented.

THE MECHANICAL PROBLEM, AND WHAT IT COSTS
    A stop is not a portfolio parameter. It needs the entry price, the
    position state, and the path since the entry - so it belongs in
    the SIGNAL, tracking its own state across bars.

    The engine's execution model is: **the signal at bar i decides the
    trade, which fills at bar i+1's OPEN.** So a stop computed inside
    the signal cannot fill at the stop price. It exits at the next
    bar's open instead.

    That is CONSERVATIVE in the right direction. If a long's stop is
    hit intrabar at bar i, the true fill would be the stop price
    (somewhere between the bar's high and low); the engine's fill is
    the NEXT OPEN, which after a stop-out is usually worse. The same
    holds for a short. So the backtest understates the stop's
    protection rather than flattering it.

    This is disclosed on every result, because a stop test that does
    not disclose its fill assumption is a stop test nobody can
    interpret.

THE CLAIMS THIS IMPLEMENTS
    RET-74, 76  a fixed-band stop on a momentum signal
    RET-87     a 1.0-SD band is a WARNING, not an exit
    RET-89, 90 the band is measured in units of the asset's own
               VOLATILITY, so it widens when volatility rises
    RET-91     a trailing stop that follows the price
    RET-92     the stop is RATCHETED - it never moves back down
    RET-95     1.0 SD warns, 1.5 SD triggers
    RET-77     do NOT use a tight trailing stop - mean reversion
               needs room (the paper's own NEGATIVE claim)
    RET-86     stops help momentum, but too-tight stops hurt

THE POINT OF THE WHOLE FAMILY
    RET-77 and RET-86 are the paper's own NEGATIVE claims. A spec
    that implements the TIGHT stop should LOSE to the spec that
    implements the WIDE one. If the tight stop wins, the paper is
    wrong, and this package says so.

    Which means the mechanism has to be verifiably BOUND: a stop that
    never fires changes nothing and proves nothing. `_stop_path`
    returns diagnostics so a test can assert the stop actually
    triggered - the same lesson as the inverted controls that turned
    out to be no-ops.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "sig_stop_momentum",
    "sig_stop_reversion",
    "stop_path",
    "realised_vol",
]


def realised_vol(closes: Sequence[Optional[float]], i: int,
                 lookback: int) -> Optional[float]:
    """The annualised realised volatility as of bar i, INCLUSIVE.

    Only bars up to and including i are used, so this is causal. The
    result is the standard deviation of the last `lookback` log
    returns, scaled by sqrt(252).
    """
    if i < 1 or lookback < 2:
        return None
    rets: List[float] = []
    for k in range(max(1, i - lookback + 1), i + 1):
        c0, c1 = closes[k - 1], closes[k]
        if c0 is None or c1 is None or c0 <= 0 or c1 <= 0:
            continue
        rets.append(math.log(c1 / c0))
    if len(rets) < 2:
        return None
    m = sum(rets) / len(rets)
    var = sum((r - m) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252.0)


def stop_path(panel, features: Dict[str, Any], feature: str = "momentum",
              entry_threshold: float = 0.0,
              stop_sd: float = 1.5,
              vol_normalised: bool = True,
              vol_lookback: int = 20,
              vol_mode: str = "entry",
              trail: bool = False,
              ratchet: bool = False,
              warning_sd: Optional[float] = None,
              warning_de_risk: float = 0.5,
              max_bars: Optional[int] = None,
              invert_signal: bool = False,
              long_when_gt: bool = True,
              **kw: Any) -> Tuple[Dict[str, List[float]], Dict[str, Any]]:
    """Run the stop logic over the panel.

    Returns ``(signal, diagnostics)``.

    The signal is ``{symbol: [position per bar]}``, where the position
    is -1, 0 or +1 (or a scaled-down position when a warning band
    de-risks it) - the same shape the engine's other signals produce.

    THE DIAGNOSTICS MATTER. A stop that never fires is a no-op, and a
    no-op that looks like a result is exactly the failure this package
    has already shipped three times (inverted controls, the leading
    z-score, the fold table). So the caller can assert that the
    mechanism actually bound.

    `vol_mode` is the subtle one:

      ``"entry"``   the band is computed ONCE, from the volatility at
                    the entry bar, and never changes. This is the
                    simple volatility-normalised stop.

      ``"current"`` the band is recomputed every bar from the CURRENT
                    volatility, so it widens when volatility rises.

    THE RATCHET ONLY BINDS IN "current" MODE, and this is not a
    detail - it is the whole interaction between the two claims:

      A trailing stop whose band is PROPORTIONAL TO THE RUNNING
      EXTREME can never loosen, because the running extreme is
      monotonic in the position's favour. A long's extreme only rises;
      a short's only falls. So in "entry" mode the ratchet is
      mathematically identical to the plain trail, and a test that
      claims otherwise is testing nothing.

      In "current" mode the band WIDENS when volatility rises. A
      volatility spike would then push the stop AWAY from the price -
      loosening it exactly when the market is most dangerous. THE
      RATCHET IS WHAT PREVENTS THAT. It is the stop that only ever
      tightens.

    So the honest statement is: the ratchet is a real control, and it
    only has anything to do in the regime where the band can move.
    """
    vals = features.get(feature) or {}
    n = panel.n
    signal: Dict[str, List[float]] = {}
    diag: Dict[str, Any] = {
        "entries": 0, "stops": 0, "warnings": 0, "time_exits": 0,
        "trail_updates": 0, "trail_rejected": 0,
        "vol_mode": vol_mode, "ratchet": bool(ratchet),
        "per_symbol": {},
    }

    for s in panel.symbols:
        closes = list(panel.close.get(s) or [])
        lows = list(panel.low.get(s) or [])
        highs = list(panel.high.get(s) or [])
        opens = list(panel.open.get(s) or [])
        v = list(vals.get(s) or [])

        row: List[float] = []
        pos = 0.0
        entry_px: Optional[float] = None
        stop_px: Optional[float] = None
        entry_vol: Optional[float] = None
        extreme_px: Optional[float] = None
        bars_held = 0
        warned = False
        s_entries = s_stops = s_warnings = s_time = 0

        for i in range(n):
            x = v[i] if i < len(v) else None
            px_close = closes[i] if i < len(closes) else None
            px_low = lows[i] if i < len(lows) else None
            px_high = highs[i] if i < len(highs) else None

            if pos != 0.0:
                # ---- an open position: check the stop ----
                bars_held += 1
                hit = False

                if stop_px is not None and px_low is not None and \
                        px_high is not None:
                    if pos > 0 and px_low <= stop_px:
                        hit = True
                    elif pos < 0 and px_high >= stop_px:
                        hit = True

                if hit:
                    pos = 0.0
                    s_stops += 1
                    diag["stops"] += 1
                    entry_px = stop_px = entry_vol = extreme_px = None
                    warned = False
                    bars_held = 0
                    row.append(0.0)
                    continue

                # A time stop: the edge decays while we wait.
                if max_bars is not None and bars_held >= int(max_bars):
                    pos = 0.0
                    s_time += 1
                    diag["time_exits"] += 1
                    entry_px = stop_px = entry_vol = extreme_px = None
                    warned = False
                    bars_held = 0
                    row.append(0.0)
                    continue

                # ---- the warning band ----
                # A warning does NOT exit. It de-risks: the position is
                # halved and the stop is pulled in, so the "1.0 SD is a
                # warning, 1.5 SD is the trigger" rule has a real,
                # testable consequence.
                if (warning_sd is not None and not warned and
                        entry_px is not None and entry_vol):
                    dist = abs(entry_px) * entry_vol * warning_sd
                    warned_now = (px_low is not None and pos > 0 and
                                  px_low <= entry_px - dist) or \
                                 (px_high is not None and pos < 0 and
                                  px_high >= entry_px + dist)
                    if warned_now:
                        warned = True
                        s_warnings += 1
                        diag["warnings"] += 1
                        pos = pos * float(warning_de_risk)
                        # Pull the stop in to the warning level.
                        new_stop = (entry_px - dist if pos > 0
                                    else entry_px + dist)
                        if stop_px is None or (ratchet and pos > 0 and
                                               new_stop > stop_px) or \
                                (ratchet and pos < 0 and new_stop < stop_px) \
                                or not ratchet:
                            stop_px = new_stop

                # ---- the trailing / ratchet update ----
                if trail and entry_px is not None:
                    if extreme_px is None:
                        extreme_px = entry_px
                    if pos > 0 and px_high is not None:
                        extreme_px = max(extreme_px, px_high)
                    elif pos < 0 and px_low is not None:
                        extreme_px = min(extreme_px, px_low)

                    # The band. In "entry" mode it is fixed for the
                    # life of the position. In "current" mode it is
                    # recomputed from the CURRENT volatility, so it
                    # WIDENS when volatility rises - and that is the
                    # only regime in which the ratchet has anything
                    # to do.
                    if vol_mode == "current":
                        band_vol = realised_vol(closes, i, vol_lookback)
                    else:
                        band_vol = entry_vol
                    if not band_vol:
                        # No volatility estimate: keep the existing
                        # stop rather than guess a new one.
                        row.append(pos)
                        continue
                    dist = abs(extreme_px) * band_vol * stop_sd
                    new_stop = (extreme_px - dist if pos > 0
                                else extreme_px + dist)
                    # A RATCHETED stop only ever moves TOWARDS the
                    # price: up for a long, down for a short. A plain
                    # trailing stop follows the band wherever it goes
                    # - which, in "current" mode, means a volatility
                    # spike can push it AWAY from the price.
                    if ratchet:
                        tightens = (
                            (pos > 0 and stop_px is not None
                             and new_stop > stop_px) or
                            (pos < 0 and stop_px is not None
                             and new_stop < stop_px))
                        if stop_px is None or tightens:
                            stop_px = new_stop
                            diag["trail_updates"] += 1
                        else:
                            diag["trail_rejected"] += 1
                    else:
                        stop_px = new_stop
                        diag["trail_updates"] += 1

                row.append(pos)
                continue

            # ---- flat: look for an entry ----
            if x is None or px_close is None:
                row.append(0.0)
                continue
            trigger = x > entry_threshold if long_when_gt else x < entry_threshold
            if not trigger:
                row.append(0.0)
                continue

            # The fill happens at the NEXT bar's open - that is the
            # engine's execution model. Using it as the entry price
            # makes the stop exactly right rather than approximately
            # right. It is the FILL, not a prediction of a future
            # price.
            fill = opens[i + 1] if (i + 1 < n and opens[i + 1] is not None) \
                else px_close
            if fill is None or fill <= 0:
                row.append(0.0)
                continue

            entry_vol = realised_vol(closes, i, vol_lookback)
            if vol_normalised:
                if not entry_vol:
                    # Without a volatility estimate the band is
                    # undefined; refuse the entry rather than invent
                    # one.
                    row.append(0.0)
                    continue
                band = abs(fill) * entry_vol * stop_sd
            else:
                band = abs(fill) * stop_sd

            pos = 1.0 if long_when_gt else -1.0
            if invert_signal:
                pos = -pos
            entry_px = fill
            extreme_px = fill
            stop_px = (fill - band) if pos > 0 else (fill + band)
            bars_held = 0
            warned = False
            s_entries += 1
            diag["entries"] += 1
            row.append(pos)

        signal[s] = row
        diag["per_symbol"][s] = {"entries": s_entries, "stops": s_stops,
                                 "warnings": s_warnings,
                                 "time_exits": s_time}

    return signal, diag


def sig_stop_momentum(panel, features: Dict[str, Any], feature: str = "momentum",
                      **kw: Any) -> Dict[str, List[float]]:
    """A stop-loss applied to a momentum-style signal.

    This is the engine's signal signature: it is called ONCE for the
    whole panel, so it can track the position state itself.
    """
    sig, _diag = stop_path(panel, features, feature=feature, **kw)
    return sig


def sig_stop_reversion(panel, features: Dict[str, Any], feature: str = "rsi",
                      **kw: Any) -> Dict[str, List[float]]:
    """A stop-loss applied to a reversion signal.

    The reversion entry is the mirror of the momentum one: enter when
    the feature is LOW, not high.
    """
    kw.setdefault("long_when_gt", False)
    sig, _diag = stop_path(panel, features, feature=feature, **kw)
    return sig
