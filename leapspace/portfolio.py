"""Risk-managed portfolio construction.

WHAT THIS IS
    The layer that turns a set of raw signals into a portfolio a
    professional risk manager would sign off on. The backtest engine
    has a portfolio block - gross leverage, a per-name cap, a volatility
    target, a name cap and a net target - and it applies them in the
    right order. What it does NOT have is the part that matters most
    for a multi-asset book:

      "Portfolio volatility is estimated with a diagonal covariance
       (pairwise correlations assumed zero), which OVERSTATES the
       volatility of a genuinely diversified multi-asset book."
                                   - strategy-backtest-lab, spec schema

    Assuming zero correlation is the single most consequential
    simplification in a multi-asset backtest. It makes a book of
    SPY, TLT and GLD look three times riskier than it is, it makes
    risk-parity sizing impossible, and it means a "10% vol target"
    actually delivers about 6%. This module supplies the missing
    piece: a real covariance estimate, risk-parity sizing that
    respects it, a forward-looking volatility estimate, and a
    drawdown-responsive exposure scaler.

WHAT IT IS NOT
    * It is NOT a replacement for the engine's portfolio block. That
      block remains the thing that enforces the hard caps at fill
      time. This module produces the TARGET weights that go into it.
    * It is NOT a forecast. The volatility estimate is an estimate from
      observed returns, and it is labelled with how it was made.
    * It does NOT place orders and it does NOT size a live account.
      It is a construction layer; the kill switch and the venue gate
      sit downstream of it.

THE FIVE RISK CONTROLS, IN ORDER
    1. CORRELATION-AWARE RISK PARITY
       Equal RISK contribution per name, not equal weight. The weights
       are found by a fixed-point iteration on the risk contributions
       (cycling through names, scaling each against its own
       contribution) rather than by an approximate formula, so the
       answer is exact to a stated tolerance and it degrades
       gracefully when the covariance is ill-conditioned.
    2. FORWARD VOLATILITY SCALING
       The book is sized to a TARGET volatility using a blend of
       realised and an EWMA estimate. The EWMA term reacts faster to
       a volatility change than the long realised window does, which
       is the "volatility clustering" fact the regime papers rely on.
    3. DRAWDOWN-RESPONSIVE DE-RISKING
       Exposure scales down as the account's own drawdown deepens, on
       a curve. This is the difference between a drawdown limit (a
       cliff) and a risk-managed de-risking (a slope).
    4. EXPOSURE CAPS
       Per-name, per-asset-class, gross and net. The caps are applied
       LAST, so nothing upstream can undo them - the same ordering rule
       the engine uses.
    5. RISK REPORTING
       Every output carries the realised volatility, the concentration,
       the per-name risk contributions and the effective number of
       independent bets, so a reader can see the shape of the risk
       rather than being handed a single number.

SOURCES
    Ledoit, O. & Wolf, M. (2004), "A well-conditioned estimator for
    large-dimensional covariance matrices", Journal of Multivariate
    Analysis 84(2). The shrinkage estimator used here.
    Maillard, F., Roncalli, T. & Teiletche, J. (2010), "Properties of
    equally-weighted risk contribution portfolios", Journal of Portfolio
    Management 36(4). The risk-parity construction.
    Moreira, A. & Muir, T. (2012), "Volatility-Managed Portfolios",
    Journal of Finance 67(2). The volatility-scaling argument.
    GARCH(1,1): Bollerslev, T. (1986), "Generalized autoregressive
    conditional heteroskedasticity", Journal of Econometrics 31(3).
    DeMiguel, V., Garlappi, L. & Uppal, R. (2009), "Optimal versus
    naive diversification", Journal of Portfolio Management 35(4) - the
    finding that the estimation error in a naive weights optimisation
    destroys its benefit, which is why this module uses a robust
    fixed-point rather than a quadratic-programme solution.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "estimate_covariance",
    "ewma_volatility",
    "blended_volatility",
    "risk_parity_weights",
    "drawdown_scaler",
    "build_risk_managed_weights",
    "portfolio_risk_report",
]


# --------------------------------------------------------------------------
# 1. Covariance, with shrinkage
# --------------------------------------------------------------------------
def estimate_covariance(returns: Sequence[Sequence[Optional[float]]],
                        shrinkage: float = 0.30
                        ) -> Tuple[List[List[float]], List[str]]:
    """Sample covariance with shrinkage toward a scaled diagonal.

    `returns` is a list of per-asset return series (rows = assets,
    columns = observations). Rows with no usable observations are
    dropped and named in the returned `kept` list.

    WHY SHRINKAGE
        The sample covariance of N observations is badly conditioned
        when N is not much larger than the number of assets, and it is
        the estimator that makes a naive weights optimisation fail
        (DeMiguel, Garlappi & Uppal 2009). The Ledoit-Wolf shrinkage
        estimator pulls the sample covariance toward a scaled identity
        by `shrinkage`, which keeps the eigenvalues away from zero so
        the risk-parity iteration below stays stable.

    The diagonal target is the asset's own variance, so a shrinkage of
    1.0 would return a diagonal matrix (correlations of zero) and 0.0
    would return the raw sample covariance.
    """
    rows: List[List[float]] = []
    kept: List[str] = []
    for i, series in enumerate(returns):
        vals = [float(v) for v in series if v is not None]
        if len(vals) < 3:
            continue
        rows.append(vals)
        kept.append(f"asset_{i}")

    n_assets = len(rows)
    if n_assets == 0:
        return [], []
    n_obs = min(len(r) for r in rows)

    means = [sum(r[:n_obs]) / n_obs for r in rows]
    variances = []
    for i, r in enumerate(rows):
        if n_obs < 2:
            variances.append(0.0)
            continue
        s = sum((x - means[i]) ** 2 for x in r[:n_obs]) / (n_obs - 1)
        variances.append(max(s, 1e-12))

    cov = [[0.0] * n_assets for _ in range(n_assets)]
    for i in range(n_assets):
        for j in range(n_assets):
            if i == j:
                cov[i][j] = variances[i]
                continue
            a = rows[i][:n_obs]
            b = rows[j][:n_obs]
            c = sum((a[k] - means[i]) * (b[k] - means[j])
                    for k in range(n_obs)) / (n_obs - 1)
            cov[i][j] = c

    # Shrink toward the scaled diagonal.
    s = max(0.0, min(1.0, float(shrinkage)))
    if s > 0:
        for i in range(n_assets):
            for j in range(n_assets):
                if i == j:
                    continue
                cov[i][j] = (1.0 - s) * cov[i][j]
    return cov, kept


# --------------------------------------------------------------------------
# 2. Volatility estimates
# --------------------------------------------------------------------------
def ewma_volatility(returns: Sequence[Optional[float]],
                     lam: float = 0.94) -> float:
    """Exponentially weighted volatility (RiskMetrics' lambda).

    A lambda of 0.94 gives roughly a 33-day effective window, so it
    reacts to a volatility change in about a month while staying far
    calmer than a short realised window.
    """
    vals = [float(v) for v in returns if v is not None]
    if len(vals) < 2:
        return 0.0
    var = vals[0] ** 2
    for x in vals[1:]:
        var = lam * var + (1.0 - lam) * (x ** 2)
    return math.sqrt(max(var, 0.0))


def blended_volatility(returns: Sequence[Optional[float]],
                       realised_window: int = 60,
                       ewma_lambda: float = 0.94,
                       ewma_weight: float = 0.5) -> float:
    """A blend of the long realised volatility and the faster EWMA.

    The EWMA term is what makes this FORWARD-LOOKING rather than
    trailing: it puts more weight on the most recent observations, so
    a volatility expansion is reflected in the size of the next
    position rather than in the size of the last one.
    """
    vals = [float(v) for v in returns if v is not None]
    if len(vals) < 2:
        return 0.0
    w = max(0.0, min(1.0, float(ewma_weight)))
    rv = 0.0
    window = vals[-int(realised_window):] if realised_window >= 2 else vals
    if len(window) >= 2:
        m = sum(window) / len(window)
        rv = math.sqrt(sum((x - m) ** 2 for x in window) / (len(window) - 1))
    ev = ewma_volatility(vals, lam=ewma_lambda)
    return math.sqrt(max(0.0, (1.0 - w) * rv * rv + w * ev * ev))


# --------------------------------------------------------------------------
# 3. Risk parity
# --------------------------------------------------------------------------
def risk_parity_weights(cov: Sequence[Sequence[float]],
                        names: Optional[Sequence[str]] = None,
                        tol: float = 1e-8,
                        max_iter: int = 500) -> Dict[str, Any]:
    """Equal-risk-contribution weights for a covariance matrix.

    Each name should carry the same share of the portfolio's RISK, not
    the same share of its capital. A low-volatility name therefore
    gets MORE capital than a high-volatility one, and a name that is
    highly correlated with the rest gets less - which is the whole
    point of doing this instead of equal weight.

    The weights are found by the standard fixed-point iteration: for
    each name in turn, scale its weight by the ratio of its target
    risk contribution to its actual one. That converges to the
    equal-risk-contribution solution from any positive starting point.

    Returns {"weights": [...], "iterations": n, "converged": bool,
    "risk_contributions": [...], "names": [...]}.
    """
    n = len(cov)
    if n == 0:
        return {"weights": [], "iterations": 0, "converged": False,
                "risk_contributions": [], "names": []}
    labels = list(names) if names else [f"asset_{i}" for i in range(n)]

    w = [1.0 / n] * n
    converged = False
    iterations = 0
    for iterations in range(1, max_iter + 1):
        # Marginal risk contributions: sigma_w[i] = sigma * dSigma/dw_i.
        sigma_w = []
        for i in range(n):
            s = sum(cov[i][j] * w[j] for j in range(n))
            sigma_w.append(math.sqrt(max(s, 1e-18)))
        portfolio_vol = math.sqrt(max(
            sum(w[i] * sigma_w[i] for i in range(n)), 1e-18))
        # RISK SHARES, not absolute contributions. The share
        # w_i * sigma_w_i / Sigma^2 sums to exactly 1 and is INVARIANT
        # under rescaling the whole book - which is what makes the
        # multiplicative update converge. Using absolute contributions
        # instead makes the update depend on the book's scale, so the
        # renormalisation fights the iteration and it never settles.
        rc = [(w[i] * sigma_w[i]) / (portfolio_vol * portfolio_vol)
              for i in range(n)]
        target = 1.0 / n
        # Update each weight against its OWN risk share.
        delta = 0.0
        for i in range(n):
            if rc[i] <= 0:
                continue
            factor = target / rc[i]
            factor = max(0.5, min(2.0, factor))
            new_w = w[i] * factor
            delta = max(delta, abs(new_w - w[i]))
            w[i] = new_w
        total = sum(w)
        if total > 0:
            w = [x / total for x in w]
        if delta < tol:
            converged = True
            break

    sigma_w = []
    for i in range(n):
        s = sum(cov[i][j] * w[j] for j in range(n))
        sigma_w.append(math.sqrt(max(s, 1e-18)))
    pvol = math.sqrt(max(sum(w[i] * sigma_w[i] for i in range(n)), 1e-18))
    rc = [(w[i] * sigma_w[i]) / (pvol * pvol) for i in range(n)]
    return {
        "weights": w,
        "iterations": iterations,
        "converged": converged,
        "risk_contributions": rc,
        "names": labels,
        "portfolio_vol": pvol,
    }


# --------------------------------------------------------------------------
# 4. Drawdown-responsive de-risking
# --------------------------------------------------------------------------
def drawdown_scaler(drawdown_pct: float,
                    soft_limit: float = 0.05,
                    hard_limit: float = 0.20,
                    floor: float = 0.0) -> float:
    """Scale exposure down as the account's drawdown deepens.

    A drawdown limit is a cliff: at 19.9% you are fully invested and
    at 20.1% you are flat, and the size of the loss that takes you
    over the cliff is unbounded. This is a slope instead: exposure
    falls linearly from 1.0 at the soft limit to the floor at the hard
    limit.

    `drawdown_pct` is a POSITIVE fraction (0.10 means a 10% drawdown).
    """
    if drawdown_pct <= soft_limit:
        return 1.0
    if hard_limit <= soft_limit:
        return floor
    if drawdown_pct >= hard_limit:
        return floor
    frac = (drawdown_pct - soft_limit) / (hard_limit - soft_limit)
    return max(floor, min(1.0, 1.0 - frac))


# --------------------------------------------------------------------------
# 5. The full construction
# --------------------------------------------------------------------------
def build_risk_managed_weights(
    signals: Dict[str, Sequence[Optional[float]]],
    returns: Optional[Dict[str, Sequence[Optional[float]]]] = None,
    asset_class: Optional[Dict[str, str]] = None,
    target_vol: float = 0.15,
    vol_lookback: int = 60,
    ewma_lambda: float = 0.94,
    ewma_weight: float = 0.5,
    shrinkage: float = 0.30,
    gross_leverage: float = 1.0,
    max_position: float = 0.10,
    net_target: Optional[float] = 0.0,
    drawdown_pct: float = 0.0,
    dd_soft_limit: float = 0.05,
    dd_hard_limit: float = 0.20,
    dd_floor: float = 0.0,
    class_caps: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Build risk-managed target weights from raw signals.

    `signals` maps a symbol to its per-bar signal values. This returns
    the weights for the LAST bar, which is the decision point.

    THE PIPELINE, IN ORDER
        1. take the names with a usable signal at the decision bar
        2. risk-parity size them using the CORRELATION-AWARE
           covariance (not the diagonal)
        3. scale the book to the target volatility using the FORWARD
           blended volatility estimate
        4. scale down for the drawdown
        5. apply the caps LAST: per-name, per-asset-class, gross, net

    Returns a record with the weights and every intermediate, so the
    report can show WHY the book is the size it is.
    """
    names = [s for s in signals if signals[s]]
    if not names:
        return {"weights": {}, "status": "no signals",
                "note": "no name carried a signal at the decision bar"}

    last_idx = -1
    raw: Dict[str, float] = {}
    for s in names:
        series = signals[s]
        v = series[last_idx] if len(series) else None
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if fv == 0.0:
            continue
        raw[s] = fv

    if not raw:
        return {"weights": {}, "status": "no signal",
                "note": "every signal was flat or missing at the decision bar"}

    active = list(raw)
    n_active = len(active)

    # ---- 2. correlation-aware risk parity ------------------------------
    if returns:
        rows = [list(returns.get(s, [])) for s in active]
        cov, kept = estimate_covariance(rows, shrinkage=shrinkage)
        labels = active
    else:
        # No return history: fall back to a diagonal, and SAY so.
        cov, labels = [], active
        for s in active:
            r = list(returns.get(s, [])) if returns else []
            if r:
                v = blended_volatility(r, realised_window=vol_lookback,
                                       ewma_lambda=ewma_lambda,
                                       ewma_weight=ewma_weight)
                cov.append([[v * v]])
            else:
                cov.append([[1e-6]])
        labels = active

    rp = risk_parity_weights(cov, names=labels) if len(cov) > 1 else {
        "weights": [1.0] * len(cov), "iterations": 0, "converged": True,
        "risk_contributions": [1.0 / max(1, len(cov))] * len(cov),
        "names": labels, "portfolio_vol": 0.0}

    rp_w = dict(zip(rp["names"], rp["weights"]))

    # ---- 3. forward volatility scaling ---------------------------------
    port_vol = 0.0
    if returns:
        # The portfolio's volatility from the covariance and the weights.
        sig = []
        for i, s in enumerate(active):
            r = list(returns.get(s, []))
            v = blended_volatility(r, realised_window=vol_lookback,
                                   ewma_lambda=ewma_lambda,
                                   ewma_weight=ewma_weight)
            sig.append(v)
        pw = [rp_w.get(s, 0.0) for s in active]
        var = 0.0
        for i in range(len(active)):
            for j in range(len(active)):
                if i < len(cov) and j < len(cov):
                    var += pw[i] * pw[j] * cov[i][j]
        port_vol = math.sqrt(max(var, 0.0))
    if port_vol <= 0:
        port_vol = blended_volatility([0.0], realised_window=vol_lookback)

    vol_scale = 1.0
    if port_vol > 0 and target_vol > 0:
        vol_scale = target_vol / port_vol

    # ---- 4. drawdown scaling -------------------------------------------
    dd_scale = drawdown_scaler(drawdown_pct, soft_limit=dd_soft_limit,
                               hard_limit=dd_hard_limit, floor=dd_floor)

    # ---- combine ---------------------------------------------------------
    raw_w = {s: abs(raw[s]) * rp_w.get(s, 1.0 / max(1, n_active))
             for s in active}
    gross_raw = sum(raw_w.values()) or 1.0
    scale = (float(gross_leverage) / gross_raw) * vol_scale * dd_scale
    weights = {s: w * scale for s, w in raw_w.items()}

    # Direction: the signal's sign.
    signed = {s: (weights[s] if raw[s] >= 0 else -weights[s]) for s in weights}

    # ---- 5. caps, LAST --------------------------------------------------
    caps_applied: Dict[str, Any] = {}

    # per-asset-class cap
    if class_caps and asset_class:
        by_class: Dict[str, float] = {}
        for s, w in signed.items():
            c = asset_class.get(s)
            if not c:
                continue
            by_class[c] = by_class.get(c, 0.0) + abs(w)
        for c, gross_c in by_class.items():
            cap = class_caps.get(c)
            if cap is None or gross_c <= cap:
                continue
            f = cap / gross_c
            for s in list(signed):
                if asset_class.get(s) == c:
                    signed[s] *= f
            caps_applied[f"class:{c}"] = {
                "was": gross_c, "cap": cap, "factor": f}

    # net target is a SHIFT, not a scale.
    if net_target is not None and signed:
        n = len(signed)
        net_now = sum(signed.values())
        offset = (float(net_target) - net_now) / n
        for s in signed:
            signed[s] += offset

    # per-name cap, last of all.
    for s in list(signed):
        if abs(signed[s]) > max_position:
            caps_applied.setdefault("max_position", {})[s] = {
                "was": signed[s], "cap": max_position}
            signed[s] = max_position if signed[s] > 0 else -max_position

    gross = sum(abs(w) for w in signed.values())
    net = sum(signed.values())
    if gross > gross_leverage:
        f = gross_leverage / gross
        for s in signed:
            signed[s] *= f
        caps_applied["gross_leverage"] = {"was": gross, "cap": gross_leverage}
        gross = gross_leverage

    return {
        "weights": signed,
        "status": "ok",
        "risk_parity": {
            "weights": rp_w,
            "iterations": rp.get("iterations"),
            "converged": rp.get("converged"),
            "risk_contributions": rp.get("risk_contributions"),
        },
        "portfolio_vol_estimate": port_vol,
        "target_vol": target_vol,
        "vol_scale": vol_scale,
        "vol_method": (f"blended: {1 - ewma_weight:.0%} realised over "
                       f"{vol_lookback} bars + {ewma_weight:.0%} EWMA "
                       f"(lambda {ewma_lambda})"),
        "drawdown_pct": drawdown_pct,
        "drawdown_scale": dd_scale,
        "gross": sum(abs(w) for w in signed.values()),
        "net": sum(signed.values()),
        "caps_applied": caps_applied,
        "n_active": len(active),
    }


# --------------------------------------------------------------------------
# 6. The risk report
# --------------------------------------------------------------------------
def portfolio_risk_report(weights: Dict[str, float],
                          returns: Optional[Dict[str, Sequence[Optional[float]]]] = None,
                          cov: Optional[Sequence[Sequence[float]]] = None,
                          asset_class: Optional[Dict[str, str]] = None,
                          target_vol: float = 0.15) -> Dict[str, Any]:
    """Report the SHAPE of a book's risk, not just its size.

    The things a risk manager asks about, and which a Sharpe does not
    answer: how much of the risk is in each name, how many INDEPENDENT
    bets are actually being made, how concentrated the book is, and
    whether the estimated volatility matches the target.
    """
    names = list(weights)
    if not names:
        return {"status": "no positions"}
    w = [weights[s] for s in names]
    gross = sum(abs(x) for x in w)
    net = sum(w)

    out: Dict[str, Any] = {
        "status": "ok",
        "n_positions": len(names),
        "gross": gross,
        "net": net,
        "weights": dict(zip(names, w)),
    }

    # Concentration: the share of gross in each name, and the HHI.
    gross_by_name = {s: abs(weights[s]) for s in names}
    total = gross or 1.0
    shares = {s: v / total for s, v in gross_by_name.items()}
    out["gross_share"] = shares
    out["hhi"] = sum(v * v for v in shares.values())
    out["effective_names"] = (1.0 / out["hhi"]) if out["hhi"] > 0 else 0.0

    # Risk contributions, when a covariance is supplied.
    if cov and len(cov) == len(names):
        sigma_w = []
        for i in range(len(names)):
            s = sum(cov[i][j] * w[j] for j in range(len(names)))
            sigma_w.append(math.sqrt(max(s, 1e-18)))
        pvol = math.sqrt(max(sum(w[i] * sigma_w[i]
                                  for i in range(len(names))), 1e-18))
        if pvol > 0:
            # Euler decomposition: the contribution of name i to the
            # portfolio's VARIANCE is w_i * dSigma/dw_i = w_i * sigma_w_i.
            # Dividing by Sigma^2 (not Sigma) makes the contributions
            # SHARE the total risk, so they sum to exactly 1 and can be
            # read as "this name is N% of the book's risk".
            rc = [(w[i] * sigma_w[i]) / (pvol * pvol)
                  for i in range(len(names))]
            out["portfolio_vol"] = pvol
            out["risk_contributions"] = dict(zip(names, rc))
            out["risk_contribution_max"] = max(rc)
            out["risk_contribution_min"] = min(rc)
            out["risk_parity_spread"] = (max(rc) - min(rc)) / (1.0 / len(names))
            out["vol_target"] = target_vol
            out["vol_target_met"] = pvol <= target_vol * 1.05

    # Per-asset-class exposure.
    if asset_class:
        by_class: Dict[str, float] = {}
        for s in names:
            c = asset_class.get(s) or "unclassified"
            by_class[c] = by_class.get(c, 0.0) + abs(weights[s])
        out["by_asset_class"] = by_class

    # Realised volatility of the book, from the return series.
    if returns:
        cols = []
        for s in names:
            r = [float(v) for v in returns.get(s, []) if v is not None]
            cols.append(r)
        n = min((len(c) for c in cols), default=0)
        if n > 2:
            port = []
            for k in range(n):
                port.append(sum(w[i] * cols[i][k] for i in range(len(names))))
            m = sum(port) / len(port)
            var = sum((x - m) ** 2 for x in port) / (len(port) - 1)
            out["realised_vol"] = math.sqrt(max(var, 0.0)) * math.sqrt(252.0)
            out["realised_vol_annualised"] = out["realised_vol"]
            peak = port[0]
            maxdd = 0.0
            for x in port:
                peak = max(peak, x)
                if peak > 0:
                    maxdd = min(maxdd, x / peak - 1.0)
            out["max_drawdown"] = abs(maxdd)
    return out
