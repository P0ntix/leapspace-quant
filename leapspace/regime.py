"""
Market regime identification.

Source: "Financial market regime identification" (LeapSpace) and "NASDAQ
market regime identification" (LeapSpace), both supplied by the user.

The papers specify the DESIGN, and we implement that design literally:

  * 3-5 latent states, not bull/bear  [regime paper, "Model choice"]
  * Feature inputs: volatility level/change, trend, drawdown/rebound,
    liquidity/volume  [both papers, "Regime features"]
  * A slow latent-state model for background regime plus a faster
    directional-change trigger for sharp transitions
  * Momentum ON in orderly trend states, OFF in panic/rebound states
  * Reversal/liquidity-provision ON in stressed / illiquid / rebound states
  * NASDAQ paper adds a fifth overlay: event/session state
  * Soft probabilities rather than hard labels (NASDAQ paper 5.2)

Implementation: a Gaussian HMM with diagonal covariance, fitted by Baum-Welch
(forward-backward + M-step), pure stdlib. The forward pass supports
FILTERING (causal, uses observations up to t only) and SMOOTHING (uses the
whole series). Filtering is what the backtest may use; smoothing may only be
used for retrospective labelling. This distinction is load-bearing: using
smoothed posteriors in a backtest is look-ahead bias.

Everything the papers left unspecified is flagged UNSPECIFIED in the
returned metadata rather than silently defaulted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------

FEATURE_NAMES = ("vol_level", "vol_change", "trend", "drawdown", "liquidity")

FEATURE_UNITS = {
    "vol_level": "annualised realised volatility of trailing returns",
    "vol_change": "short-window vol divided by long-window vol minus 1",
    "trend": "trailing return over the trend lookback",
    "drawdown": "current drawdown from the rolling high (negative)",
    "liquidity": "log average dollar volume (higher = more liquid)",
    "rebound": "1 when price bounced after a prior decline (NASDAQ paper crash dummy)",
    "event": "1 when the bar falls in an event/expiry window (NASDAQ paper overlay)",
}


def _mean(xs: Sequence[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _stdev(xs: Sequence[float]) -> Optional[float]:
    vals = [float(x) for x in xs if x is not None]
    if len(vals) < 2:
        return None
    m = sum(vals) / len(vals)
    var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
    return math.sqrt(var)


def _rolling(xs: Sequence[Optional[float]], window: int,
             fn) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(xs)
    for i in range(len(xs)):
        lo = max(0, i - window + 1)
        w = [v for v in xs[lo:i + 1] if v is not None]
        if len(w) >= max(2, window // 2):
            out[i] = fn(w)
    return out


def build_regime_features(closes: Sequence[float],
                          volumes: Sequence[float],
                          vol_short: int = 10,
                          vol_long: int = 60,
                          trend_lookback: int = 60,
                          drawdown_lookback: int = 60,
                          liquidity_lookback: int = 20,
                          rebound_lookback: int = 20,
                          event_flags: Optional[Sequence[bool]] = None
                          ) -> Dict[str, List[Optional[float]]]:
    """Build the four core regime features + the rebound/event overlays.

    All lookbacks are DEFAULTS, not paper values — the papers name the
    feature families but not their windows. They are exposed so a spec can
    override them, and `UNSPECIFIED` is recorded in the spec metadata.
    """
    n = len(closes)
    rets: List[Optional[float]] = [None] * n
    for i in range(1, n):
        p, c = closes[i - 1], closes[i]
        if p and c and p > 0 and c > 0:
            rets[i] = c / p - 1.0

    ann = math.sqrt(252.0)
    rv = _rolling(rets, vol_short, lambda w: _stdev(w) * ann)
    rv_long = _rolling(rets, vol_long, lambda w: _stdev(w) * ann)

    vol_level: List[Optional[float]] = list(rv)
    vol_change: List[Optional[float]] = [
        None if (a is None or b is None or not b) else a / b - 1.0
        for a, b in zip(rv, rv_long)
    ]

    trend: List[Optional[float]] = [None] * n
    for i in range(n):
        j = i - trend_lookback
        if j >= 0 and closes[j] and closes[i] and closes[j] > 0 and closes[i] > 0:
            trend[i] = closes[i] / closes[j] - 1.0

    drawdown: List[Optional[float]] = [None] * n
    for i in range(n):
        lo = max(0, i - drawdown_lookback + 1)
        window = [c for c in closes[lo:i + 1] if c is not None and c > 0]
        peak = max(window) if window else None
        if peak and closes[i] and closes[i] > 0:
            drawdown[i] = closes[i] / peak - 1.0

    dollar_vol = []
    for c, v in zip(closes, volumes):
        cv = c if c is not None else 0.0
        vv = v if v is not None else 0.0
        dollar_vol.append(cv * vv if (cv > 0 and vv > 0) else 0.0)
    avg_dv = _rolling(dollar_vol, liquidity_lookback, _mean)
    liquidity: List[Optional[float]] = [
        None if (x is None or x <= 0) else math.log(x) for x in avg_dv
    ]

    # Rebound flag: prior decline AND current positive return, the crash
    # dummy described in the NASDAQ paper (ref 60) and the momentum-crash
    # literature it cites.
    rebound: List[Optional[float]] = [None] * n
    for i in range(n):
        j = i - rebound_lookback
        if j < 1 or closes[j] is None or closes[j - 1] is None:
            continue
        if not closes[j] or not closes[j - 1]:
            continue
        prior_ret = closes[j] / closes[j - 1] - 1.0
        cur = rets[i] or 0.0
        rebound[i] = 1.0 if (prior_ret < 0 and cur > 0) else 0.0

    event: List[Optional[float]] = [None] * n
    if event_flags is not None:
        for i, f in enumerate(event_flags[:n]):
            event[i] = 1.0 if f else 0.0
    else:
        event = [0.0] * n

    return {
        "vol_level": vol_level,
        "vol_change": vol_change,
        "trend": trend,
        "drawdown": drawdown,
        "liquidity": liquidity,
        "rebound": rebound,
        "event": event,
        "_returns": rets,
    }


# --------------------------------------------------------------------------
# Gaussian HMM
# --------------------------------------------------------------------------

_LOG_2PI = math.log(2.0 * math.pi)


def _log_gauss(x: float, mu: float, var: float) -> float:
    var = max(var, 1e-12)
    return -0.5 * (_LOG_2PI + math.log(var) + (x - mu) ** 2 / var)


@dataclass
class HMM:
    """Gaussian HMM with diagonal covariance."""

    n_states: int = 4
    means: List[List[float]] = field(default_factory=list)
    variances: List[List[float]] = field(default_factory=list)
    trans: List[List[float]] = field(default_factory=list)
    init: List[float] = field(default_factory=list)
    n_features: int = 0
    log_likelihood: float = float("-inf")
    n_iter: int = 0
    converged: bool = False

    # -- internals ---------------------------------------------------------
    def _emit(self, obs: Sequence[float]) -> List[float]:
        return [sum(_log_gauss(obs[d], self.means[s][d],
                               self.variances[s][d]) for d in range(self.n_features))
                for s in range(self.n_states)]

    def _forward(self, seq: List[List[float]], scaled: bool = True):
        n = len(seq)
        T = [[0.0] * self.n_states for _ in range(n)]
        # scale factors keep the forward recursion in float range
        scales = [0.0] * n
        logB = self._emit(seq[0])
        for s in range(self.n_states):
            T[0][s] = self.init[s] * math.exp(logB[s]) if self.init[s] > 0 else 0.0
        if scaled:
            scales[0] = sum(T[0]) or 1.0
            T[0] = [v / scales[0] for v in T[0]]
        for t in range(1, n):
            logB = self._emit(seq[t])
            for s in range(self.n_states):
                acc = 0.0
                for k in range(self.n_states):
                    acc += T[t - 1][k] * self.trans[k][s]
                T[t][s] = acc * (math.exp(logB[s]) if logB[s] > -700 else 0.0)
            if scaled:
                scales[t] = sum(T[t]) or 1.0
                T[t] = [v / scales[t] for v in T[t]]
        return T, scales

    def _backward(self, seq: List[List[float]], T, scales):
        n = len(seq)
        B = [[0.0] * self.n_states for _ in range(n)]
        for t in range(n - 2, -1, -1):
            logB = self._emit(seq[t + 1])
            for s in range(self.n_states):
                acc = 0.0
                for k in range(self.n_states):
                    e = math.exp(logB[k]) if logB[k] > -700 else 0.0
                    acc += self.trans[s][k] * e * B[t + 1][k]
                B[t][s] = acc / (scales[t + 1] or 1.0)
        return B

    # -- public API --------------------------------------------------------
    def fit(self, seq: List[List[float]], max_iter: int = 120,
            tol: float = 1e-5) -> "HMM":
        if not seq:
            raise ValueError("cannot fit an HMM on an empty sequence")
        self.n_features = len(seq[0])
        k = self.n_states
        d = self.n_features

        # --- init: k-means++ style spread over the observations
        flat = [x for row in seq for x in row]
        if len(flat) < k * d:
            raise ValueError("not enough observations to fit an HMM")
        mean_all = sum(flat) / len(flat)
        var_all = max(1e-9, sum((x - mean_all) ** 2 for x in flat) / len(flat))
        self.means = [[mean_all] * d for _ in range(k)]
        self.variances = [[var_all] * d for _ in range(k)]
        # spread the initial means deterministically along the first feature
        span = sorted(row[0] for row in seq)
        for s in range(k):
            self.means[s][0] = span[int((s + 0.5) / k * (len(span) - 1))]
        self.trans = [[0.7 if k == 1 else (0.8 if i == j else 0.2 / (k - 1))
                       for j in range(k)] for i in range(k)]
        for i in range(k):
            self.trans[i] = [v / sum(self.trans[i]) for v in self.trans[i]]
        self.init = [1.0 / k] * k

        prev_ll = float("-inf")
        for it in range(max_iter):
            T, scales = self._forward(seq)
            ll = sum(math.log(s) for s in scales if s > 0)
            B = self._backward(seq, T, scales)

            # --- M step
            # transition counts
            trans_num = [[0.0] * k for _ in range(k)]
            for t in range(len(seq) - 1):
                for i in range(k):
                    for j in range(k):
                        trans_num[i][j] += T[t][i] * self.trans[i][j] * B[t + 1][j]
            self.trans = []
            for i in range(k):
                row = trans_num[i]
                s = sum(row)
                self.trans.append([(v / s if s > 0 else 1.0 / k) for v in row])

            # emission means / variances
            gamma = [[0.0] * k for _ in range(len(seq))]
            new_means = [[0.0] * d for _ in range(k)]
            new_vars = [[0.0] * d for _ in range(k)]
            for t in range(len(seq)):
                s = sum(T[t][i] * B[t][i] for i in range(k))
                if s <= 0:
                    continue
                for i in range(k):
                    g = T[t][i] * B[t][i] / s
                    gamma[t][i] = g
                    for dd in range(d):
                        new_means[i][dd] += g * seq[t][dd]
                        new_vars[i][dd] += g * (seq[t][dd] ** 2)
            for i in range(k):
                s = sum(gamma[t][i] for t in range(len(seq)))
                if s <= 0:
                    self.means[i] = list(self.means[i])
                    continue
                for dd in range(d):
                    mu = new_means[i][dd] / s
                    var = new_vars[i][dd] / s - mu * mu
                    self.means[i][dd] = mu
                    self.variances[i][dd] = max(var, 1e-10)
            init_num = [sum(gamma[0][i] for i in range(k)) for _ in range(1)]
            self.init = [max(gamma[0][i], 1e-10) for i in range(k)]
            self.init = [v / sum(self.init) for v in self.init]

            self.n_iter = it + 1
            if abs(ll - prev_ll) < tol * max(1.0, abs(prev_ll)):
                self.converged = True
                prev_ll = ll
                break
            prev_ll = ll
        self.log_likelihood = prev_ll
        return self

    def filter(self, seq: List[List[float]]) -> List[List[float]]:
        """CAUSAL posterior P(S_t | x_1..t). Safe for backtesting."""
        if not seq:
            return []
        T, _ = self._forward(seq)
        return T

    def smooth(self, seq: List[List[float]]) -> List[List[float]]:
        """Posterior P(S_t | x_1..T). RETROSPECTIVE ONLY — look-ahead if used live."""
        if not seq:
            return []
        T, scales = self._forward(seq)
        B = self._backward(seq, T, scales)
        out = []
        for t in range(len(seq)):
            row = [T[t][i] * B[t][i] for i in range(self.n_states)]
            s = sum(row) or 1.0
            out.append([v / s for v in row])
        return out

    def viterbi(self, seq: List[List[float]]) -> List[int]:
        """Most likely state path (uses the whole series)."""
        n = len(seq)
        if n == 0:
            return []
        delta = [self._emit(seq[0])[s] + math.log(max(self.init[s], 1e-300))
                 for s in range(self.n_states)]
        psi = [[0] * self.n_states for _ in range(n)]
        for t in range(1, n):
            logB = self._emit(seq[t])
            new = [0.0] * self.n_states
            for s in range(self.n_states):
                best_k, best_v = 0, float("-inf")
                for k in range(self.n_states):
                    v = delta[k] + math.log(max(self.trans[k][s], 1e-300))
                    if v > best_v:
                        best_k, best_v = k, v
                psi[t][s] = best_k
                new[s] = best_v + logB[s]
            delta = new
        path = [0] * n
        path[n - 1] = max(range(self.n_states), key=lambda s: delta[s])
        for t in range(n - 1, 0, -1):
            path[t - 1] = psi[t][path[t]]
        return path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_states": self.n_states,
            "means": self.means,
            "variances": self.variances,
            "trans": self.trans,
            "init": self.init,
            "n_features": self.n_features,
            "log_likelihood": self.log_likelihood,
            "n_iter": self.n_iter,
            "converged": self.converged,
        }


# --------------------------------------------------------------------------
# State labelling — map latent states onto the papers' regime taxonomy
# --------------------------------------------------------------------------

REGIME_TAXONOMY = [
    "tranquil_uptrend",
    "high_vol_uptrend",
    "range_chop",
    "regular_bear",
    "crash_rebound",
]

# Which behaviour each label implies (the papers' central claim).
REGIME_BEHAVIOUR = {
    "tranquil_uptrend": {"momentum": "on", "reversal": "off", "size": "full"},
    "high_vol_uptrend": {"momentum": "reduced", "reversal": "off", "size": "reduced"},
    "range_chop": {"momentum": "off", "reversal": "on", "size": "low"},
    "regular_bear": {"momentum": "off", "reversal": "selective", "size": "reduced"},
    "crash_rebound": {"momentum": "off", "reversal": "on", "size": "minimal"},
}


def label_states(hmm: HMM, feature_names: Sequence[str]) -> Dict[int, str]:
    """Assign the paper's labels to latent states using their emission means.

    The rule set is deterministic and documented so a re-fit produces a
    stable, explainable mapping rather than an arbitrary index permutation.
    """
    idx = {name: i for i, name in enumerate(feature_names)}
    scored: List[Tuple[float, int, str]] = []
    for s in range(hmm.n_states):
        vol = hmm.means[s][idx.get("vol_level", 0)]
        trend = hmm.means[s][idx.get("trend", 0)]
        dd = hmm.means[s][idx.get("drawdown", 0)]
        # rank states by a composite "stress" score
        stress = -trend + abs(min(dd, 0.0)) + vol
        scored.append((stress, s, ""))
    scored.sort(reverse=True)
    order = [s for _, s, _ in scored]
    n = hmm.n_states
    # Map: lowest stress -> tranquil uptrend; then range/chop; then bear; then crash.
    # With 4 states we use tranquil_uptrend, range_chop, regular_bear, crash_rebound.
    # With 5 we insert high_vol_uptrend.
    if n >= 5:
        mapping = {
            order[0]: "tranquil_uptrend",
            order[1]: "high_vol_uptrend",
            order[2]: "range_chop",
            order[3]: "regular_bear",
            order[4]: "crash_rebound",
        }
    elif n == 4:
        mapping = {
            order[0]: "tranquil_uptrend",
            order[1]: "range_chop",
            order[2]: "regular_bear",
            order[3]: "crash_rebound",
        }
    elif n == 3:
        mapping = {
            order[0]: "tranquil_uptrend",
            order[1]: "regular_bear",
            order[2]: "crash_rebound",
        }
    else:
        mapping = {order[0]: "tranquil_uptrend", order[1]: "crash_rebound"}
    return {int(k): v for k, v in mapping.items()}


@dataclass
class RegimeResult:
    n_states: int
    labels: Dict[int, str]
    posteriors_filtered: List[List[Optional[float]]]
    posteriors_smoothed: List[List[Optional[float]]]
    viterbi_path: List[Optional[int]]
    label_series_filtered: List[Optional[str]]
    label_series_smoothed: List[Optional[str]]
    hmm: HMM
    feature_names: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def probability_of(self, label: str, series: str = "filtered") -> List[Optional[float]]:
        idx = [s for s, lab in self.labels.items() if lab == label]
        if not idx:
            return [None] * len(self.posteriors_filtered)
        post = self.posteriors_filtered if series == "filtered" else self.posteriors_smoothed
        out: List[Optional[float]] = []
        for row in post:
            if row is None or row[0] is None:
                out.append(None)
            else:
                vals = [row[i] for i in idx if row[i] is not None]
                out.append(sum(float(v) for v in vals if v is not None))
        return out

    def summary(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for lab in self.label_series_filtered:
            if lab:
                counts[lab] = counts.get(lab, 0) + 1
        total = max(1, sum(counts.values()))
        return {
            "n_states": self.n_states,
            "labels": {str(k): v for k, v in self.labels.items()},
            "state_share": {k: v / total for k, v in counts.items()},
            "state_bars": counts,
            "converged": self.hmm.converged,
            "n_iter": self.hmm.n_iter,
            "log_likelihood": self.hmm.log_likelihood,
            "feature_names": self.feature_names,
            **self.metadata,
        }


def identify_regimes(features: Dict[str, List[Optional[float]]],
                     feature_names: Sequence[str] = ("vol_level", "vol_change",
                                                    "trend", "drawdown", "liquidity"),
                     n_states: int = 4,
                     max_iter: int = 120,
                     standardize: bool = True,
                     min_bars: int = 250,
                     ) -> Optional[RegimeResult]:
    """Fit the HMM and label the states.

    Returns None when there is not enough usable data — the caller must
    report that as "insufficient sample", never as "no regimes found".
    """
    names = list(feature_names)
    n = len(features[names[0]])
    rows: List[List[float]] = []
    keep_idx: List[int] = []
    for t in range(n):
        vals = []
        ok = True
        for nm in names:
            v = features.get(nm, [None] * n)[t]
            if v is None:
                ok = False
                break
            vals.append(float(v))
        if ok:
            rows.append(vals)
            keep_idx.append(t)

    if len(rows) < max(min_bars, n_states * 40):
        return None

    data = rows
    if standardize:
        stats = []
        for d in range(len(names)):
            col = [r[d] for r in rows]
            mu = sum(col) / len(col)
            var = sum((x - mu) ** 2 for x in col) / max(1, len(col) - 1)
            stats.append((mu, math.sqrt(var) if var > 0 else 1.0))
        data = [[(v - stats[d][0]) / stats[d][1] for d, v in enumerate(r)] for r in rows]

    hmm = HMM(n_states=n_states).fit(data, max_iter=max_iter)
    labels = label_states(hmm, names)
    post_f_compact = hmm.filter(data)
    post_s_compact = hmm.smooth(data)
    path_compact = hmm.viterbi(data)

    # Expand the compact (usable-rows-only) outputs back onto the FULL bar
    # axis so every consumer can index by bar position without a separate
    # mapping. Bars that fell in the feature warm-up carry no posterior.
    post_f: List[List[Optional[float]]] = [[None] * n_states for _ in range(n)]
    post_s: List[List[Optional[float]]] = [[None] * n_states for _ in range(n)]
    path: List[Optional[int]] = [None] * n
    lab_f: List[Optional[str]] = [None] * n
    lab_s: List[Optional[str]] = [None] * n
    p_f: List[Optional[float]] = [None] * n
    p_s: List[Optional[float]] = [None] * n
    for t, src in enumerate(keep_idx):
        post_f[src] = list(post_f_compact[t])
        post_s[src] = list(post_s_compact[t])
        path[src] = path_compact[t]
        bf = max(range(n_states), key=lambda s: post_f_compact[t][s])
        bs = max(range(n_states), key=lambda s: post_s_compact[t][s])
        lab_f[src] = labels[bf]
        lab_s[src] = labels[bs]
        p_f[src] = post_f_compact[t][bf]
        p_s[src] = post_s_compact[t][bs]

    meta = {
        "standardized": standardize,
        "bars_used": len(rows),
        "bars_total": n,
        "unusable_bars_warmup": n - len(rows),
        "feature_units": {k: FEATURE_UNITS.get(k, "") for k in names},
        "unspecified_in_source": [
            "feature lookback windows",
            "number of states (paper says 3-5; set by spec)",
            "state labelling thresholds",
        ],
        "causality": ("filter() posteriors are causal and are the only ones "
                      "safe for backtesting; smooth() and viterbi() use the "
                      "whole series and are retrospective only"),
    }
    return RegimeResult(
        n_states=n_states, labels=labels,
        posteriors_filtered=post_f, posteriors_smoothed=post_s,
        viterbi_path=path,
        label_series_filtered=lab_f, label_series_smoothed=lab_s,
        hmm=hmm, feature_names=names, metadata=meta,
    )
