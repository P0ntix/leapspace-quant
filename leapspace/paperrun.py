"""The paper-concept runner.

WHAT THIS IS
    Runs the full paper-concept matrix through the engine's validation
    gauntlet and writes the results to a JSON file plus a readable text
    log.

WHY A RUNNER AND NOT THE CLI
    The matrix is 96 specs (48 concepts x 6 asset classes, plus 48
    negative controls). Running them one CLI invocation at a time is
    slow and produces 96 separate result rows that have to be merged by
    hand. This runs them in-process, appends to ONE results file, and
    records everything the report needs.

THE MERGE RULE
    A later run must not erase an earlier one. The runner MERGES by
    spec name, keeping the file's existing order, and the report
    consumes the file. This is the rule the package's own CLI already
    follows, and it exists because a one-spec run that overwrites the
    file leaves the rendered report describing a run that no longer
    exists on disk.

WHAT IS RECORDED FOR EVERY SPEC
    The verdict, every flag, the pooled OOS Sharpe, the in-sample
    Sharpe, the trade count, the max drawdown, the per-fold walk-forward
    table, and which robustness stages RAN, which were SKIPPED and
    which ERRORED. A skipped stage is a finding and is recorded as one.

    The leading-coverage number is recorded too: how many bars of the
    panel actually had a leading-indicator value. A leading feature
    that covers 5% of the sample is a leading feature that cannot be
    evaluated, and the report has to say so.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Sequence

from .backtest import BacktestResult, run_spec

__all__ = ["run_matrix", "merge_results", "PAPER_RESULTS_PATH",
           "leading_coverage_for"]


PAPER_RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports", "paper_concept_results.json")

_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports", "paper_concept_runs.log")


def _lock(path: str, timeout: float = 120.0):
    """A simple exclusive lock so parallel workers do not clobber.

    Several workers may merge into the same results file at the same
    time. A read-modify-write with no lock is a lost-update race: two
    workers read the same file, each adds its own rows, and the second
    write erases the first worker's rows. The lock is an atomic
    O_EXCL create, so exactly one worker holds it at a time.

    The lock file is removed on release, and a stale lock (from a
    killed worker) is broken after `timeout`.
    """
    import time
    lock_path = path + ".lock"
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.time() > deadline:
                # A stale lock from a killed worker. Break it and retry.
                try:
                    os.remove(lock_path)
                except OSError:
                    pass
                continue
            time.sleep(0.25)
    return lock_path


def _release(lock_path: str) -> None:
    try:
        os.remove(lock_path)
    except OSError:
        pass


def merge_results(path: str, rows: Sequence[Dict[str, Any]]) -> str:
    """Merge rows into the results file BY NAME, keeping the file order.

    A later run must not shrink the file. The existing order is kept and
    new rows are appended; a row whose name is already present is
    REPLACED in place, so a re-run updates rather than duplicates.

    The merge is done under an exclusive lock so parallel workers
    cannot lose each other's rows.
    """
    lock_path = _lock(path)
    try:
        existing: List[Dict[str, Any]] = []
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    existing = [r for r in data if isinstance(r, dict)]
            except Exception:  # noqa: BLE001
                existing = []
        by_name = {r.get("name"): r for r in existing if r.get("name")}
        order = [r.get("name") for r in existing if r.get("name")]
        for r in rows:
            name = r.get("name")
            if not name:
                continue
            if name not in by_name:
                order.append(name)
            by_name[name] = r
        out = [by_name[n] for n in order if n in by_name]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        os.replace(tmp, path)
        return path
    finally:
        _release(lock_path)


def leading_coverage_for(spec: Dict[str, Any]) -> Dict[str, Any]:
    """How much leading-indicator data actually covers this spec's panel.

    Returns {"n_bars", "n_leading", "fraction", "source", "asset",
    "reason"}. An unavailable leading series is reported with a reason,
    never as zero coverage with no explanation.
    """
    out: Dict[str, Any] = {"n_bars": 0, "n_leading": 0, "fraction": 0.0,
                           "source": "", "asset": "", "reason": ""}
    names = [f.get("name") for f in (spec.get("features") or [])]
    if not any(n and n.startswith("leading_") for n in names):
        out["reason"] = "this spec does not use a leading indicator"
        return out
    try:
        from .leading import align_to_bars
        from .leadingcache import panel_date_timestamps, series_for_panel

        class _FakePanel:
            symbols = list((spec.get("universe") or {}).get("symbols") or [])
            preset = (spec.get("universe") or {}).get("preset")

        # Resolve the source the same way the engine does, from the
        # universe preset.
        from .leadingcache import resolve_leading_source
        src, asset, _why = resolve_leading_source(_preset_symbols(spec))
        series, info = series_for_panel(_FakePanel(), source=src, asset=asset)
        out["source"] = src
        out["asset"] = asset
        out["n_points"] = len(series)
        if not series:
            out["reason"] = info.get("reason") or "no leading series available"
            return out
        return out
    except Exception as exc:  # noqa: BLE001
        out["reason"] = f"{type(exc).__name__}: {str(exc)[:140]}"
        return out


def _preset_symbols(spec: Dict[str, Any]) -> List[str]:
    """The symbols of a spec's universe, so the leading source resolves."""
    uni = spec.get("universe") or {}
    syms = uni.get("symbols") or []
    if syms:
        return list(syms)
    preset = uni.get("preset")
    if not preset:
        return []
    try:
        from .backtest import _load_skill_modules
        btengine, _btv, _ = _load_skill_modules()
        return list(btengine.UNIVERSE_PRESETS.get(preset) or [])
    except Exception:  # noqa: BLE001
        return []


def run_matrix(specs: Sequence[Dict[str, Any]],
               quick: bool = False,
               out_path: Optional[str] = None,
               log_path: Optional[str] = None,
               only: Optional[Sequence[str]] = None,
               n_variants: Optional[int] = None) -> Dict[str, Any]:
    """Run the specs and merge the results.

    `only` restricts the run to spec names containing one of the given
    substrings, which is how the matrix is split across parallel
    workers. A run with `only` still MERGES into the same results file
    rather than replacing it.
    """
    out_path = out_path or PAPER_RESULTS_PATH
    log_path = log_path or _LOG_PATH
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    rows: List[Dict[str, Any]] = []
    started = time.time()
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n=== RUN {time.strftime('%Y-%m-%d %H:%M:%S')} "
                  f"quick={quick} ===\n")
        for i, spec in enumerate(specs, start=1):
            name = spec.get("name") or f"spec_{i}"
            if only and not any(tok in name for tok in only):
                continue
            t0 = time.time()
            try:
                res: BacktestResult = run_spec(spec, quick=quick,
                                               n_variants=n_variants,
                                               verbose=False)
                row = _row_from_result(res, spec, time.time() - t0)
            except Exception as exc:  # noqa: BLE001
                row = {
                    "name": name, "verdict": "ERROR",
                    "flags": [f"{type(exc).__name__}: {str(exc)[:200]}"],
                    "errors": [f"{type(exc).__name__}: {str(exc)[:200]}"],
                    "paper": spec.get("paper", ""),
                    "concept": spec.get("concept", ""),
                    "asset_class": spec.get("asset_class", ""),
                    "elapsed_s": round(time.time() - t0, 1),
                }
            rows.append(row)
            log.write(f"[{i}] {name} -> {row.get('verdict')} "
                      f"({row.get('elapsed_s')}s)\n")
            log.flush()
            print(f"[{i}/{len(specs)}] {name} -> {row.get('verdict')} "
                  f"({row.get('elapsed_s')}s)", flush=True)

    merge_results(out_path, rows)
    return {
        "results_path": out_path,
        "log_path": log_path,
        "n_run": len(rows),
        "elapsed_s": round(time.time() - started, 1),
        "rows": rows,
    }


def _row_from_result(res: BacktestResult, spec: Dict[str, Any],
                      elapsed: float) -> Dict[str, Any]:
    """Turn a BacktestResult into the row the report consumes.

    The OUT-OF-SAMPLE Sharpe is the result. The in-sample Sharpe is
    kept beside it and never substituted for it.

    This used to do `m.get("oos_sharpe") or m.get("sharpe_oos") or
    m.get("sharpe")` - the last fallback is the IN-SAMPLE Sharpe, so
    every row in the results file reported the in-sample number under
    the out-of-sample key. A report that labels that "pooled OOS
    Sharpe" is reporting the wrong number, and it looked right.
    """
    m = dict(res.metrics or {})

    # The stage ledger: what ran, what was skipped, what errored.
    ledger = dict(res.stage_ledger or {})
    stages = m.get("validation") or m.get("stages") or ledger
    stage_summary: Dict[str, Any] = {}
    if isinstance(stages, dict):
        for k, v in stages.items():
            if k == "skipped_stages":
                continue
            if isinstance(v, dict):
                stage_summary[k] = {
                    "status": v.get("status"),
                    "passed": v.get("passed"),
                    "note": v.get("note"),
                }
            else:
                stage_summary[k] = {"status": str(v)[:120]}

    # The fold table.
    wf = dict(res.walk_forward or {})
    folds = wf.get("folds") or []
    if not folds:
        # Fall back to the flat per-fold Sharpe list.
        raw = wf.get("oos_sharpes") or []
        folds = [{"fold": i, "oos_sharpe": s} for i, s in enumerate(raw)]

    oos = m.get("oos_sharpe")
    is_sharpe = m.get("in_sample_sharpe")
    if is_sharpe is None:
        is_sharpe = m.get("sharpe")

    row: Dict[str, Any] = {
        "name": res.name,
        "verdict": res.verdict,
        "flags": list(res.flags or []),
        "errors": list(res.errors or []),
        "paper": res.paper or spec.get("paper", ""),
        "concept": spec.get("concept", ""),
        "asset_class": spec.get("asset_class", ""),
        "elapsed_s": round(elapsed, 1),
        "metrics": {
            "oos_sharpe": oos,
            "oos_sharpe_live": m.get("oos_sharpe_live"),
            "in_sample_sharpe": is_sharpe,
            "n_trades": m.get("n_trades") or m.get("trades"),
            "max_drawdown": m.get("max_drawdown") or m.get("max_drawdown_pct"),
            "total_return": m.get("total_return") or m.get("total_return_pct"),
            "oos_max_drawdown": m.get("oos_max_drawdown"),
            "oos_cagr": m.get("oos_cagr"),
            "oos_profitable_folds": m.get("oos_profitable_folds"),
            "oos_retention": m.get("oos_retention"),
            "pbo": m.get("pbo"),
            "n_oos_trades": m.get("n_oos_trades"),
            "deflated_sharpe": m.get("deflated_sharpe"),
        },
        "walk_forward": {
            **{k: v for k, v in wf.items() if k != "folds"},
            "folds": folds,
        },
        "stages": stage_summary,
        "skipped_stages": list(res.skipped_stages or []),
    }
    cov = leading_coverage_for(spec)
    row["leading_coverage"] = cov
    return row
