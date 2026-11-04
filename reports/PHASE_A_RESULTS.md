# PHASE A RESULTS — the paper's long/short rule and the pairs construction

**Run:** 2026-11-04, 1,036 s for 24 specs (12 real, 12 inverted twins).
**Engine:** one code version, the full gauntlet, costs at **2×** the engine
default, `net_target 0.0` and `long_only False` — so a result cannot be
a beta bet in disguise.
**Raw:** `reports/phase_a_results.json` · `reports/phase_a_run.log` ·
`reports/phase_a_specs.json`

---

## THE HEADLINE

**One concept is FRAGILE with its inverted twin REFUTED. That is genuine
discrimination — the first row in this project where the real rule
survived and its control did not.**

| Spec | Verdict | OOS Sharpe | OOS max DD | Folds profitable | Total trades |
|---|---|---|---|---|---|
| `paper_trend_longshort_us_equity_style` | **FRAGILE** | **+0.77** | **3.4%** | **5 / 5** | 6 |
| `paper_trend_longshort_us_equity_style_CONTROL` | REFUTED | **−0.88** | 20.4% | **0 / 5** | 6 |
| `paper_pairs_meanrev_crypto` | REFUTED | −1.43 | 21.1% | 0 / 5 | 190 |
| `paper_pairs_meanrev_crypto_CONTROL` | **FRAGILE** | **+0.97** | 3.4% | 4 / 5 | 190 |

Every other row is REFUTED.

**The equity row is the paper's own rule, tested for the first time.**
The package's previously SUPPORTED result,
`nasdaq_12m_timeseries_momentum`, was `long_only: true` — which
*contradicts* the paper's direction rule: *"Go long when price is above
its trend proxy; go short or flat when below."* This is the first time
the paper's actual rule has been tested, with both legs live, dollar
neutral, at stressed costs.

Its five walk-forward folds, all positive:
**+0.157, +1.183, +0.344, +1.617, +0.442**
The control's five, all negative:
**−0.218, −1.302, −0.517, −1.738, −0.583**

That is the strongest evidence this project has produced that a
*reading* produced a result rather than the market.

**It is still FRAGILE, and it must stay FRAGILE:**

- **only 6 trades** (the gate requires ≥ 30)
- **t-stat 0.97** (the gate requires ≥ 2.0)
- **PBO 0.6** — high, and PBO is meaningless at 6 trades
- **Monte Carlo: ERROR** — it needs ≥ 20 trades and there are 6
- out-of-sample Sharpe *exceeds* in-sample (retention 312%), which on
  6 trades is a symptom of a small sample, not of skill

---

## THE SECOND FINDING, AND IT CUTS AGAINST THE PAPER

**On crypto, the inverted pairs control BEAT the real one.**

`paper_pairs_meanrev_crypto` scored an out-of-sample Sharpe of
**−1.43** with **0 / 5** profitable folds.
`paper_pairs_meanrev_crypto_CONTROL` scored **+0.97** with **4 / 5**
profitable folds, a 3.4% out-of-sample drawdown and a Monte Carlo
probability of profitability of only 23%.

Trading the spread mean-reversion **the wrong way** was better by 2.4
Sharpe points. The likely mechanism: the pair selection picks the
pairs whose spread is *most stable*, and on the crypto universe the
most stable spreads were the *trending* ones — so the selection
rewarded momentum rather than reversion.

That is a **finding about the implementation, and it is reported as
such**: the pairs construction as built does not deliver the paper's
reversion on crypto. It is not evidence that the paper is wrong about
pairs in general — it is evidence that this pair-selection method
finds the wrong pairs. The fix (a Hurst filter or a genuine
cointegration test, which the stdlib does not provide) is in the
proposal.

---

## EVERY ROW

### The paper's long/short trend rule

| Asset class | Real | OOS SR | Control | OOS SR | Trades |
|---|---|---|---|---|---|
| US equity style | **FRAGILE** | **+0.77** | REFUTED | −0.88 | 6 |
| Crypto | REFUTED | −0.02 | REFUTED | −0.41 | 10 |
| FX majors | REFUTED | −0.19 | REFUTED | +0.10 | 8 |
| Commodities | REFUTED | −0.08 | REFUTED | +0.03 | 13 |
| Futures broad | REFUTED | −0.06 | REFUTED | +0.04 | 15 |
| Rates & credit | REFUTED | +0.06 | REFUTED | +0.05 | 12 |

### The paper's pairs construction

| Asset class | Real | OOS SR | Control | OOS SR | Trades |
|---|---|---|---|---|---|
| US equity style | REFUTED | −0.31 | REFUTED | +0.06 | 321 |
| Crypto | REFUTED | −1.43 | **FRAGILE** | **+0.97** | 190 |
| FX majors | REFUTED | −0.25 | REFUTED | +0.03 | 502 |
| Commodities | REFUTED | −0.17 | REFUTED | +0.10 | 647 |
| Futures broad | REFUTED | +0.18 | REFUTED | −0.24 | 880 |
| Rates & credit | REFUTED | +0.21 | REFUTED | −0.23 | 491 |

---

## THE METHODOLOGICAL FINDING THAT MATTERS MOST

**The trade-count gate is structurally hostile to low-turnover rules.**

A 12-month time-series momentum on five ETFs generates **6 trades in
15 years**. The gate requires **≥ 30**. So the gate will refuse a
12-month momentum on daily bars essentially every time, on a criterion
that has nothing to do with whether the signal works.

Look at the trade counts across the whole run: the trend rule produced
6, 8, 10, 12, 13, 15. The pairs rule produced 190, 321, 491, 502,
647, 880. The gate is calibrated for the second class and structurally
rejects the first.

This is **not** a reason to lower the gate. A gate that refuses a
6-trade result is doing its job — a 6-trade result cannot be
distinguished from luck, and the FRAGILE verdict is correct. But it
means the FRAGILE verdict on the equity trend row is **not** evidence
that the paper's rule fails; it is evidence that the rule needs either
(a) a longer history, (b) a shorter window so it trades more, or (c)
more names so the book has more independent positions.

**The most likely path to a SUPPORTED verdict for the paper's own
rule** is a universe with more independent names — so the same
12-month signal produces more independent trades — and the same gate,
unchanged.

The other trade counts are also worth reading: the equity trend rule
generated 6 trades but **30 out-of-sample trades**. The in-sample
window held most of the positions, and the out-of-sample window
re-traded them. The 5/5 profitable folds come from that re-trading.
So the 30 OOS trades are not 30 independent bets either — they are the
same few positions, re-entered.

---

## WHAT WAS NOT TESTED

The stage ledger records it on every row:

> `replication: SKIPPED — the gauntlet only runs cross-market replication
> when alternative universes are supplied, and the matrix runner supplies
> none, so NO spec in this matrix was tested for whether it transfers to
> a different market.`

**Every single row in the 120-row matrix — the original 96 and these 24
— has an untested replication stage.** The paper's rule was tested on
six markets, which is breadth, not replication: it was tested on the
*same* universe in each. Whether it transfers to a *different* universe
is untested everywhere.

That is the largest single validation gap in the project, and it is
Phase E of the proposal.

---

## WHAT THIS CHANGES IN THE PROPOSAL

1. **The trade-count gate needs a documented turnover-aware form** for
   low-frequency rule classes — not a lower number, but a rule that
   asks the right question. A 12-month momentum cannot produce 30
   independent trades in 15 years, and the gate should say *"6 trades
   is too few to distinguish from luck"* (which it does) without
   implying the rule class is untestable.

2. **More names, not more windows, is the fix.** The paper's rule needs
   independent bets, and independence comes from breadth.

3. **The pairs pair-selection is wrong for crypto.** The stability
   criterion finds trending spreads. A Hurst filter or a real
   cointegration test is needed, and the stdlib has neither.

4. **The replication stage must be wired.** It is the one stage that
   says whether a surviving concept is an edge or a market curiosity.
