"""Trader qualification against CITED standards, and a GIPS-consistent
qualified-wallet pool with continuous tracking.

This module exists because "successful trader" needs a defensible answer.
The research in AUTHORITATIVE_TRADER_STANDARDS.md established three things
that change how the package must work:

1. **"30 trades" is not a standard.** No regulator, exchange, professional
   body or academic text publishes a minimum trade count for a win rate to
   be meaningful. What is published is the NIST FORMULA for the minimum
   sample size given the precision you claim. So the trade-count gate is
   COMPUTED from the claim, not hard-coded.

2. **The win-rate and profit-factor BANDS are not standardised.** The
   numbers "55% win rate" and "1.5 profit factor" circulate on vendor and
   blog pages, not in any authority. They are kept, because they are
   operable, but every one is labelled ANALYST_CHOICE with its actual
   provenance stated. The DEFINITIONS (Wilson interval, profit factor,
   Sharpe) are citable and are cited.

3. **GIPS 3.A.9 points the OPPOSITE way to the old pool design.** A
   terminated portfolio "must be included in the historical performance of
   the composite up to the last full measurement period". So a wallet that
   degrades is retired from the FORWARD cohort while its HISTORY STAYS in
   the reported record - never silently dropped, never retroactively
   restated. The old `demote_if_unprofitable` flag deleted the forward
   signal but also lost the record; this module keeps both.

Every criterion below carries: the threshold, the authority tag, and the
URL it came from. Where the authority is "none", that is stated rather
than dressed up.
"""
from __future__ import annotations

from .stats import norm_ppf as _z, poly as _poly

import json
import math
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from .provenance import read_json

POOL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "state", "qualified_pool.json")

# --------------------------------------------------------------------------
# 1. Sample size - the citable formula
# --------------------------------------------------------------------------
#: NIST/SEMATECH e-Handbook 7.2.4.2 "Sample sizes required"
#: https://www.itl.nist.gov/div898/handbook/prc/section2/prc242.htm
#:
#:   N >= [ (z_{1-alpha/2} * sqrt(p0(1-p0)) + z_{1-beta} * sqrt(p1(1-p1)))
#:          / delta ]^2
#:
#: with Fleiss/Levin/Paik continuity correction N = N' + 1/delta.
#: NIST: "taking the value of the proportion defective to be 0.5 leads to
#: the largest possible sample size."
NIST_SAMPLE_SIZE_URL = ("https://www.itl.nist.gov/div898/handbook/prc/"
                        "section2/prc242.htm")
NIST_VALIDITY_URL = ("https://www.itl.nist.gov/div898/handbook/prc/"
                     "section2/prc24.htm")
WILSON_URL = ("https://www.itl.nist.gov/div898/handbook/prc/section2/"
              "prc241.htm")
RULE_OF_THREE_URL = "https://pubmed.ncbi.nlm.nih.gov/6827763/"
SHARPE_URL = ("https://rpc.cfainstitute.org/sites/default/files/-/media/"
              "documents/code/gips/sharpe-ratio-and-the-information-ratio.pdf")
GIPS_URL = ("https://www.gipsstandards.org/wp-content/uploads/2021/03/"
            "2020_gips_standards_firms.pdf")
GMGN_URL = ("https://docs.gmgn.ai/index/insider-traders-snipers-first-70-"
            "buyers")
NANSEN_FIRST_FUNDER_URL = ("https://docs.nansen.ai/api/profiler/"
                           "address-first-funder")
NANSEN_COVERAGE_URL = "https://docs.nansen.ai/api/data-coverage"


def required_sample_size(p0: float = 0.50, p1: float = 0.55,
                         alpha: float = 0.05, beta: float = 0.20,
                         delta: float = 0.05, one_sided: bool = True,
                         continuity_correction: bool = True) -> Dict[str, Any]:
    """Minimum N to show p1 is better than p0 (NIST 7.2.4.2).

    The defaults answer the question the package actually needs to ask:
    "how many trades before a 55% win rate can be distinguished from a
    coin flip at 95% confidence and 80% power, with a 5 percentage-point
    margin?" The answer is ~617 trades, which is ~21x the 30-trade floor
    the package used to hard-code.
    """
    z_a = _z(1 - alpha) if one_sided else _z(1 - alpha / 2)
    z_b = _z(1 - beta)
    n_prime = ((z_a * math.sqrt(p0 * (1 - p0))
                + z_b * math.sqrt(p1 * (1 - p1))) / delta) ** 2
    n = int(math.ceil(n_prime))
    corrected = None
    if continuity_correction:
        corrected = int(math.ceil(n_prime + 1 / delta))
    return {
        "n_required": corrected if corrected is not None else n,
        "n_without_correction": n,
        "parameters": {"p0": p0, "p1": p1, "alpha": alpha, "beta": beta,
                       "delta": delta, "one_sided": one_sided,
                       "continuity_correction": continuity_correction},
        "source": "NIST/SEMATECH e-Handbook 7.2.4.2",
        "url": NIST_SAMPLE_SIZE_URL,
        "note": ("NIST: 'taking the value of the proportion defective to be "
                 "0.5 leads to the largest possible sample size.' The sample "
                 "size is a function of the CLAIM, not a constant."),
    }


def wilson_interval(wins: int, n: int, confidence: float = 0.95
                     ) -> Dict[str, Any]:
    """Wilson score interval for a win rate (NIST 7.2.4.1).

    The naive Wald interval can produce a negative lower limit; Wilson's
    cannot, which is why NIST recommends it "for virtually all combinations
    of n and p".
    """
    if n <= 0:
        return {"status": "no_sample", "lower": None, "upper": None,
                "source": "NIST 7.2.4.1 (Wilson score interval)",
                "url": WILSON_URL}
    z = _z(1 - (1 - confidence) / 2)
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return {
        "status": "computed",
        "win_rate": p,
        "lower": max(0.0, centre - half),
        "upper": min(1.0, centre + half),
        "confidence": confidence,
        "method": "Wilson score interval",
        "source": "NIST/SEMATECH e-Handbook 7.2.4.1",
        "url": WILSON_URL,
        "note": ("NIST: Wilson 'was recommended by Agresti and Coull for "
                 "virtually all combinations of n and p'. Its lower limit "
                 "cannot be negative, which the naive Wald interval cannot "
                 "guarantee."),
    }


def rule_of_three(n: int) -> Dict[str, Any]:
    """95% upper bound on the rate when zero events were observed.

    Hanley & Lippman-Hand, JAMA 1983. With zero events in n trials the 95%
    upper limit on the event rate is approximately 3/n.
    """
    return {
        "upper_bound": (3.0 / n) if n > 0 else None,
        "n": n,
        "zero_events": True,
        "source": "Hanley & Lippman-Hand, JAMA 1983;249(13):1743-1745",
        "url": RULE_OF_THREE_URL,
        "caveat": ("The reprint PDF was fetched but is a scanned image with "
                   "no text layer, so the '3/n' was taken from the "
                   "publisher-hosted record rather than extracted from the "
                   "PDF."),
    }


def validity_floor(p0: float = 0.50) -> Dict[str, Any]:
    """NIST's validity conditions for the one-proportion test."""
    n_floor = int(math.ceil(5 / min(p0, 1 - p0))) if p0 else 30
    return {
        "min_n_for_normal_approximation": 30,
        "min_n_from_criterion": n_floor,
        "criterion": "min{ N*p0, N*(1-p0) } >= 5",
        "source": "NIST/SEMATECH e-Handbook 7.2.4",
        "url": NIST_VALIDITY_URL,
        "note": ("N > 30 is the VALIDITY FLOOR for the normal approximation, "
                 "not a claim that 30 trades makes a win rate meaningful. The "
                 "research is explicit that no authority publishes '30 "
                 "trades' as a quality standard."),
    }


# --------------------------------------------------------------------------
# 2. The criteria registry - each with its actual authority
# --------------------------------------------------------------------------
CRITERIA: Dict[str, Dict[str, Any]] = {
    "min_trades": {
        "label": "Minimum closed trades",
        "threshold": None,      # COMPUTED, see required_sample_size
        "authority": "NIST/SEMATECH e-Handbook 7.2.4.2",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": NIST_SAMPLE_SIZE_URL,
        "note": ("No authority publishes a constant minimum trade count. The "
                 "requirement is COMPUTED from the claim being made."),
    },
    "min_win_rate": {
        "label": "Win rate floor",
        "threshold": 0.55,
        "authority": "NONE - analyst choice",
        "tag": "NOT-STANDARDISED",
        "url": None,
        "note": ("Research finding: 'No regulator, exchange, professional "
                 "body or academic text publishes a win-rate threshold for "
                 "trader quality.' The 55% figure is operable and is kept, "
                 "but it is an analyst choice and must be reported as one. "
                 "Win rate is only meaningful WITH its confidence interval."),
    },
    "min_profit_factor": {
        "label": "Profit factor floor",
        "threshold": 1.5,
        "authority": "NONE - analyst choice (vendor convention)",
        "tag": "ANALYTICS-VENDOR-CONVENTION",
        "url": None,
        "note": ("The DEFINITION (gross profit / gross loss) is uncontested. "
                 "The THRESHOLD is not: 'No regulator, exchange, CFA "
                 "Institute, GIPS or professional body publishes an "
                 "interpretation band.' The frequently repeated '1.5 / 2.0' "
                 "bands appear only on vendor and blog pages."),
    },
    "max_single_trade_pnl_share": {
        "label": "Max share of PnL from one trade",
        "threshold": 0.40,
        "authority": "NONE - analyst choice",
        "tag": "NOT-STANDARDISED",
        "url": None,
        "note": ("Anti-survivorship / anti-lucky-hit guard. Not standardised; "
                 "kept as an analyst choice."),
    },
    "min_distinct_tokens": {
        "label": "Distinct tokens traded",
        "threshold": 10,
        "authority": "NONE - analyst choice",
        "tag": "NOT-STANDARDISED",
        "url": None,
        "note": "Keeps a one-token wonder out of the pool.",
    },
    "max_bot_probability": {
        "label": "Bot probability ceiling",
        "threshold": 0.30,
        "authority": "NONE - analyst choice",
        "tag": "NOT-STANDARDISED",
        "url": None,
        "note": ("Bot-like timing variance. The copy-trading skill's "
                 "operating rule; no authority publishes this number."),
    },
    "max_drawdown": {
        "label": "Maximum drawdown ceiling",
        "threshold": 0.20,
        "authority": "NONE - CFA Institute publishes NO band",
        "tag": "NOT-STANDARDISED",
        "url": None,
        "note": ("CFA Institute lists maximum drawdown as an APPRAISAL RATIO "
                 "and warns it 'must be used with care', but publishes NO "
                 "numerical threshold. The package's 0.20 is an analyst "
                 "choice and cannot be attributed to CFA Institute."),
    },
    "sharpe": {
        "label": "Sharpe ratio",
        "threshold": None,
        "authority": "CFA Institute",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": SHARPE_URL,
        "note": ("CFA Institute: 'The Sharpe ratio is the industry standard "
                 "for measuring risk-adjusted return.' The DEFINITION is "
                 "citable; CFA Institute publishes NO interpretation band."),
    },
    "fee_basis": {
        "label": "Fee basis of the risk measures",
        "threshold": "gross-of-fees, disclosed",
        "authority": "CFA Institute (GIPS) 2.B.7, 4.C.42",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": GIPS_URL,
        "note": ("'The firm should use gross-of-fees returns when "
                 "calculating risk measures.' An on-chain Sharpe computed "
                 "after modelled slippage, gas and MEV is a NET-OF-FEES "
                 "Sharpe and must be labelled as such."),
    },
    "pool_retention": {
        "label": "Retention of a retired wallet's history",
        "threshold": "history retained, forward cohort only excludes",
        "authority": "CFA Institute (GIPS) 3.A.9",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": GIPS_URL,
        "note": ("'Terminated portfolios must be included in the historical "
                 "performance of the composite up to the last full "
                 "measurement period.' A degraded wallet leaves the FORWARD "
                 "cohort; its record stays."),
    },
    "track_record_length": {
        "label": "Track-record length before a performance record is presented",
        "threshold": "5 years",
        "authority": "CFA Institute (GIPS) 1.A.3, 6.A.1(a), 8.C.1(a)",
        "tag": "ACADEMIC-OR-PROFESSIONAL-GUILD",
        "url": GIPS_URL,
        "note": ("The published minimum for presenting a performance record "
                 "as a GIPS composite. A 30-day on-chain track record is "
                 "NOT comparable to a GIPS-compliant 5-year record, and "
                 "must not be presented as if it were."),
    },
    "insider_exclusion": {
        "label": "Exclusion of conflicted wallets",
        "threshold": None,
        "authority": "NONE - constructed from published primitives",
        "tag": "NOT-STANDARDISED",
        "url": GMGN_URL,
        "note": ("No regulator, exchange, professional body, standard-setter "
                 "or analytics vendor publishes a rule for excluding "
                 "deployer-funded, sniper or bundler wallets from a "
                 "copy-trading universe. GMGN publishes the COMPONENT "
                 "definitions (insider, sniper, 'first 70 buyers'); Nansen "
                 "publishes the first-funder METHOD. The COMBINATION is a "
                 "construction and is labelled as one."),
    },
}


def criteria_table() -> List[Dict[str, Any]]:
    """Flat, printable view of every criterion with its authority."""
    out = []
    for name, c in CRITERIA.items():
        out.append({
            "criterion": name,
            "label": c.get("label"),
            "threshold": c.get("threshold"),
            "authority": c.get("authority"),
            "tag": c.get("tag"),
            "url": c.get("url"),
        })
    return out


# --------------------------------------------------------------------------
# 3. Wallet qualification
# --------------------------------------------------------------------------
def qualify_wallet(profile: Dict[str, Any],
                   criteria: Optional[Dict[str, Any]] = None
                   ) -> Dict[str, Any]:
    """Judge a wallet profile against the criteria, with the authority of
    each gate attached to its result.

    `profile` is the profiler's output: trade count, win rate, profit
    factor, max single-trade share, distinct tokens, bot probability,
    drawdown, Sharpe.
    """
    crit = criteria or {}
    n_trades = int(profile.get("n_trades") or 0)
    n_wins_raw = profile.get("n_wins")
    wins = int(n_wins_raw) if n_wins_raw is not None else None
    wr = profile.get("win_rate")
    # Derive the win rate ONLY when a win count actually exists. If the
    # win count is unknown, the win rate is unknown too - deriving 0/N
    # would turn "could not be priced" into "lost every trade".
    if wr is None and wins is not None and n_trades:
        wr = wins / n_trades

    # --- the citable gate: sample size computed from the claim -----------
    claim = crit.get("min_win_rate", 0.55)
    nss = required_sample_size(p0=0.50, p1=float(claim))
    sample_ok = n_trades >= nss["n_required"]
    floor = validity_floor(0.50)

    checks: List[Dict[str, Any]] = []

    def add(name: str, value: Any, ok: bool, detail: str = "") -> None:
        c = CRITERIA.get(name, {})
        checks.append({
            "criterion": name,
            "value": value,
            "pass": bool(ok),
            "threshold": crit.get(name, c.get("threshold")),
            "authority": c.get("authority"),
            "tag": c.get("tag"),
            "url": c.get("url"),
            "detail": detail,
        })

    add("min_trades", n_trades, sample_ok,
        f"NIST formula needs N>={nss['n_required']} to support a "
        f"{claim:.0%} win rate vs a 50% coin flip "
        f"(alpha=0.05 one-sided, beta=0.20, delta=0.05)")

    pf = profile.get("profit_factor")
    add("min_profit_factor", pf,
        pf is not None and pf >= crit.get("min_profit_factor", 1.5),
        "threshold has no citable authority - analyst choice")

    add("min_win_rate", wr,
        wr is not None and wr >= claim,
        "threshold has no citable authority - analyst choice")

    single = profile.get("max_single_trade_pnl_share")
    add("max_single_trade_pnl_share", single,
        single is not None
        and single <= crit.get("max_single_trade_pnl_share", 0.40),
        "anti-lucky-hit guard - analyst choice")

    distinct = profile.get("n_tokens")
    add("min_distinct_tokens", distinct,
        distinct is not None
        and distinct >= crit.get("min_distinct_tokens", 10),
        "analyst choice")

    bot = profile.get("bot_probability")
    add("max_bot_probability", bot,
        bot is not None and bot <= crit.get("max_bot_probability", 0.30),
        "analyst choice")

    passed = all(c["pass"] for c in checks)
    # A Wilson interval is only meaningful when the win COUNT is known. If
    # the trades could not be priced the win rate is UNKNOWN, and an
    # interval computed from a fabricated zero would be a false precision.
    if wr is None:
        wi: Dict[str, Any] = {
            "status": "not computed - the win rate is UNKNOWN, not zero",
            "reason": ("The profiler could not price this wallet's trades, "
                       "so there is no win count to build an interval "
                       "from. A zero here would be a fabricated performance "
                       "record."),
            "lower": None, "upper": None,
            "source": "NIST 7.2.4.1 (Wilson score interval)",
            "url": WILSON_URL,
        }
    else:
        wi = wilson_interval(wins, n_trades)
    out: Dict[str, Any] = {
        "qualified": passed,
        "checks": checks,
        "n_trades": n_trades,
        "win_rate": wr,
        "wilson_interval": wi,
        "sample_size_requirement": nss,
        "validity_floor": floor,
        "evaluated_at": int(time.time()),
        "interpretation": (
            "QUALIFIED against the stated criteria" if passed else
            "NOT QUALIFIED against the stated criteria"),
        "important": (
            "Passing these gates does NOT mean the wallet is a successful "
            "trader. These thresholds are mostly analyst choices - see each "
            "check's 'authority'. What IS citable here is the sample-size "
            "requirement, the confidence interval and the fee-basis label."),
    }
    if n_trades == 0:
        out["interpretation"] = ("INSUFFICIENT HISTORY: no closed trades. "
                                 "A wallet below the trade-count threshold "
                                 "has a SAMPLE, not a profile.")
        out["qualified"] = False
    elif wins == 0:
        out["zero_numerator"] = rule_of_three(n_trades)
    return out


# --------------------------------------------------------------------------
# 4. The qualified pool - GIPS-consistent retention
# --------------------------------------------------------------------------
def load_pool(path: Optional[str] = None) -> Dict[str, Any]:
    p = path or POOL_PATH
    blob = read_json(p) or {}
    blob.setdefault("wallets", {})
    blob.setdefault("events", [])
    return blob


def save_pool(pool: Dict[str, Any], path: Optional[str] = None) -> str:
    p = path or POOL_PATH
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(pool, fh, indent=2)
    os.replace(tmp, p)
    return p


def record_evaluation(address: str, chain: str, verdict: Dict[str, Any],
                       pool: Optional[Dict[str, Any]] = None,
                       path: Optional[str] = None) -> Dict[str, Any]:
    """Record one evaluation and update the wallet's forward eligibility.

    The history is APPENDED and never rewritten. A wallet that fails a
    later evaluation is retired from the forward cohort but its earlier
    record stays in the pool and in the reported history - GIPS 3.A.9.
    """
    pool = pool if pool is not None else load_pool(path)
    key = f"{chain}:{address}"
    w = pool["wallets"].setdefault(key, {
        "address": address, "chain": chain,
        "promoted_at": None, "promoted_reason": None,
        "retired_at": None, "retired_reason": None,
        "status": "candidate", "forward_eligible": False,
        "history": [],
    })
    entry = {
        "ts": verdict.get("evaluated_at") or int(time.time()),
        "qualified": bool(verdict.get("qualified")),
        "n_trades": verdict.get("n_trades"),
        "win_rate": verdict.get("win_rate"),
        "wilson": verdict.get("wilson_interval", {}).get("lower"),
        "interpretation": verdict.get("interpretation"),
    }
    w["history"].append(entry)
    w["last_evaluated_at"] = entry["ts"]
    w["last_verdict"] = verdict

    if verdict.get("qualified"):
        if w["status"] != "active":
            w["status"] = "active"
            w["promoted_at"] = entry["ts"]
            w["promoted_reason"] = (
                f"qualified at {entry['ts']} "
                f"({verdict.get('n_trades')} trades, "
                f"win rate {verdict.get('win_rate')})")
            pool["events"].append({
                "ts": entry["ts"], "action": "promote", "key": key,
                "reason": w["promoted_reason"]})
        w["forward_eligible"] = True
    else:
        if w["status"] == "active":
            w["status"] = "retired"
            w["retired_at"] = entry["ts"]
            w["retired_reason"] = (
                f"no longer qualifying at {entry['ts']} "
                f"({verdict.get('interpretation')})")
            pool["events"].append({
                "ts": entry["ts"], "action": "retire", "key": key,
                "reason": w["retired_reason"]})
        w["forward_eligible"] = False

    save_pool(pool, path)
    return {"wallet": w, "event": pool["events"][-1] if pool["events"] else None}


def pool_report(pool: Optional[Dict[str, Any]] = None,
                path: Optional[str] = None) -> Dict[str, Any]:
    """The pool, reported with retired wallets' history retained.

    The FORWARD cohort is the active set. The REPORTED record includes
    every wallet ever admitted and its full evaluation history, because
    GIPS 3.A.9 requires terminated portfolios to stay in the historical
    performance of the composite.
    """
    pool = pool if pool is not None else load_pool(path)
    wallets = pool.get("wallets") or {}
    active = {k: w for k, w in wallets.items() if w.get("forward_eligible")}
    retired = {k: w for k, w in wallets.items()
               if not w.get("forward_eligible") and w.get("promoted_at")}
    never = {k: w for k, w in wallets.items() if not w.get("promoted_at")}
    return {
        "forward_cohort": sorted(active),
        "forward_cohort_size": len(active),
        "retired_with_history_retained": sorted(retired),
        "never_qualified": sorted(never),
        "events": pool.get("events") or [],
        "retention_rule": CRITERIA["pool_retention"],
        "note": ("Retired wallets are excluded from the FORWARD cohort and "
                 "RETAINED in the reported history. This follows CFA "
                 "Institute GIPS 3.A.9: 'Terminated portfolios must be "
                 "included in the historical performance of the composite "
                 "up to the last full measurement period.'"),
        "source": GIPS_URL,
    }


# --------------------------------------------------------------------------
# 5. Tracking qualified wallets
# --------------------------------------------------------------------------
def track_wallets(chain: str = "solana", limit: int = 25,
                  pool: Optional[Dict[str, Any]] = None,
                  path: Optional[str] = None) -> Dict[str, Any]:
    """Poll the forward cohort for new activity and update their records.

    This is POLLING, not streaming: free public RPC has no websocket on
    this host, so the interval is explicit and the cost is stated rather
    than implied.
    """
    from .chains import fetch_wallet_trades
    pool = pool if pool is not None else load_pool(path)
    active = [w for w in (pool.get("wallets") or {}).values()
              if w.get("forward_eligible")]
    out: List[Dict[str, Any]] = []
    gaps: List[Dict[str, Any]] = []
    for w in active[:limit]:
        addr = w.get("address")
        try:
            trades = fetch_wallet_trades(chain, addr, limit=25)
            out.append({"address": addr, "chain": chain,
                        "n_trades_seen": len(trades),
                        "newest_ts": max([t.ts for t in trades], default=None)
                        if trades else None,
                        "tokens": sorted({t.token for t in trades
                                          if getattr(t, "token", None)})[:8]})
        except Exception as exc:  # noqa: BLE001
            gaps.append({"address": addr,
                         "reason": f"{type(exc).__name__}: {str(exc)[:150]}"})
    return {
        "chain": chain,
        "mode": "polling (no free websocket on this host)",
        "n_tracked": len(out),
        "wallets": out,
        "gaps": gaps,
        "note": ("Polling means a trade between two polls is not seen until "
                 "the next poll. This is a known limitation, not a claim of "
                 "real-time coverage."),
    }
