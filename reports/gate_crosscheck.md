# GATE CROSS-CHECK — an independent implementation of the consistency gate

**Verdict: the package's gate and an independently written implementation
now agree on every metric that is specified.** This document records what
the cross-check found, what was fixed, and what it proved.

---

## 1. What the cross-check is

`leapspace/reference_gate.py` is a **second, independent implementation** of
the consistency gate, written from the cited rules rather than by porting
`leapspace/edge.py`. It shares no helper module with the package — if the
two implementations agreed because they called the same code, the
comparison would prove nothing.

`leapspace/tests/test_crosscheck_gate.py` runs both on the same inputs and
compares them metric by metric. It **fails loudly** on a mismatch rather
than tolerating it.

The real trades come from `reports/crosscheck_trades.json` (600 KB), which
is cached so the comparison is reproducible offline. It was built from live
Ethereum data by pricing each wallet's transfers at the block of each
trade.

---

## 2. The four defects it found — all four were in the package

### 2.1 The Bayesian skill probability was the wrong quantity

The gate used `binomial_tail_p(w, n)` = `P(X <= w)` for `X ~ Binomial(n, 0.5)`
— the **null-hypothesis significance test** — where the cited criteria mean
the **posterior probability** that the true win rate exceeds 50% under a
Beta(1,1) prior:

```
P(p > 0.5 | w wins in n)  =  sum_{k=0}^{w} C(n+1, k) / 2^(n+1)
```

These are different quantities and the significance test **overstates** skill
probability:

| wins/n | significance test | posterior probability | passes 0.95 |
|---|---|---|---|
| 1/1 | 1.0000 | 0.7500 | no → yes |
| 3/3 | 1.0000 | 0.9375 | yes → **no** |
| 5/10 | 0.6230 | 0.5000 | no → no |
| 55/100 | 0.8644 | 0.8401 | no → no |
| 60/100 | 0.9824 | 0.9770 | yes → yes |

**The starkest symptom: a perfect record read as 100% certain skill.**
`P(X <= n | Bin(n, 0.5)) = 1.0` for every n, so every flawless wallet looked
like proof.

**Direction of the error: the gate was LENIENT** — the wrong way for a test
whose entire job is separating skill from luck.

*Verified* against numerical integration of the Beta(w+1, n-w+1) posterior
density (Simpson's rule, 200,000 steps, written from the definition): the
`n+1` form matches to **1.7e-06**; the significance test is off by up to
**0.25**.

**Fixed** by adding `stats.bayesian_skill_probability` and using it in
`edge.evaluate_edge` and `edge.posterior_split_half_stability`.
`binomial_tail_p` keeps its original meaning.

### 2.2 SR0(2) used an asymptotic shortcut instead of the cited formula

`expected_max_sharpe` fell back to `sqrt(2 * ln N)` for `N <= 2`. The
published Bailey & López de Prado form is valid at N = 2:

```
SR0(2) = (1-gamma)*Z^-1(1 - 1/N) + gamma*Z^-1(1 - 1/(N*e))
       = 0.4228*0 + 0.5772*0.9 = 0.5198
```

The package returned **1.1774** — 2.3× too large, which understated the
selection penalty. Now agrees with the reference to **2.7e-09** across
N = 1..1000.

### 2.3 The decay test split the wrong list — and it flipped verdicts

`evaluate_edge` computed the raw closed-trade PnL series, then overwrote the
count with the **bet** count, and the decay test used that bet count as the
index into the **raw** list:

```python
n_closed = bo["n_closed_bets"]        # 4 bets
pnls = [...raw closed trades...]       # 179 entries
half = n_closed // 2                  # 2
early, recent = pnls[:half], pnls[half:]   # 2 and 177 RAW trades
```

Because the raw list is dominated by the early bets' partial sells, the
ratio read **0.9025** (no decay) where the bet split reads **0.0025** (total
collapse). On the fixture built to expose it, the package said
**CONSISTENT** and the reference said **FLUKE**.

The criterion and the rest of the gate work in bets, so the decay test must
too. **Fixed**: the split now uses the bet series.

### 2.4 The three bet counters disagreed with each other

`independent_bets()` counted every bet that **opened**; `bet_outcomes()` and
`time_disjoint_bets()` counted every bet that **closed**. On 2000 random leg
sequences they disagreed on **1335**.

```
legs=[('buy', 2), ('buy', 2)]  independent_bets=1  time_disjoint=0  bet_outcomes=0
```

They now share one definition and one set of rules — a buy while flat opens a
bet, a sell that takes the net to zero or below closes it, and a sell with no
open bet does not reset the net. **0 disagreements in 2000 sequences.**

### 2.5 A field whose name lied

`n_closed_trades` reported the **bet** count while the raw trade count was
computed and then shadowed. Now `n_closed_trades` is the raw closed-trade
count and `n_closed_bets` is the bet count.

---

## 3. What the cross-check now agrees on

### 3.1 The four REAL wallets in `reports/crosscheck_trades.json`

Every row below is a measured value printed by the test, not an estimate.
`reports/crosscheck_trades.json` was built from live Ethereum data by
pricing each wallet's transfers at the block of each trade.

**Wallet 1 — `0x3f9a8345729eA842708E080e238C92731e5699b8`** (381 priced rows, 179 closed trades)

| Metric | Package | Reference | Agreement |
|---|---|---|---|
| Independent (effective) bets | 4 | 4 | **exact** (delta 0.000e+00) |
| Time-disjoint bet count | 4 | 4 | **exact** |
| Raw closed trades | 179 | 179 | **exact** |
| Wins / losses | 1 / 3 | 1 / 3 | **exact** |
| Win rate | 0.25 | 0.25 | **exact** |
| Wilson lower bound | 0.04558726076 | 0.04558726081 | AGREE (delta 5.257e-11) |
| Wilson upper bound | 0.6993581577 | 0.6993581574 | AGREE (delta 2.540e-10) |
| Bayesian skill probability | 0.1875 | 0.1875 | **exact** |
| Deflated Sharpe | 4.030950843e-05 | 4.030950855e-05 | AGREE (delta 1.237e-13) |
| `edge_decay` n_early / n_recent | 2 / 2 | 2 / 2 | **exact** |
| **Verdict** | **FLUKE** | **FLUKE** | **exact** |
| Definitive rejections | `skill_not_distinguishable`, `deflated_sharpe` | same | **exact** |
| Insufficiencies | `min_observations_for_period_statistic`, `insufficient_independent_bets`, `too_few_closed_trades` | same | **exact** |

NIST sample size for a 55%-vs-50% claim: **637** effective bets required;
this wallet has **4**.

**Wallet 2 — `0xaDFffc33cdC9970349CBcEa3D73Ec343d6ed116D`** (90 priced rows, 2 closed)

| Metric | Package | Reference | Agreement |
|---|---|---|---|
| Independent (effective) bets | 0 | 0 | **exact** |
| Time-disjoint bet count | 0 | 0 | **exact** |
| Raw closed trades | 2 | 2 | **exact** |
| **Verdict** | **FLUKE** | **FLUKE** | **exact** |
| Definitive rejections | `deflated_sharpe` | `deflated_sharpe` | **exact** |
| Insufficiencies | `min_observations_for_period_statistic`, `insufficient_independent_bets`, `single_token_only`, `too_few_closed_trades` | same | **exact** |

**Wallet 3 — `0xEd0203625D3Ef97f8f52AaaD9EAabacE4418cAF3`** (264 priced rows, 65 closed)

| Metric | Package | Reference | Agreement |
|---|---|---|---|
| Independent (effective) bets | 0 | 0 | **exact** |
| Time-disjoint bet count | 0 | 0 | **exact** |
| Raw closed trades | 65 | 65 | **exact** |
| **Verdict** | **FLUKE** | **FLUKE** | **exact** |
| Definitive rejections | `deflated_sharpe` | `deflated_sharpe` | **exact** |
| Insufficiencies | `min_observations_for_period_statistic`, `insufficient_independent_bets`, `single_token_only`, `too_few_closed_trades` | same | **exact** |

**Wallet 4 — `0x442689F3F26cBcCc2E288DaEa986b9d67346149a`** (169 priced rows, 22 closed)

| Metric | Package | Reference | Agreement |
|---|---|---|---|
| Independent (effective) bets | 0 | 0 | **exact** |
| Time-disjoint bet count | 0 | 0 | **exact** |
| Raw closed trades | 22 | 22 | **exact** |
| **Verdict** | **FLUKE** | **FLUKE** | **exact** |
| Definitive rejections | `deflated_sharpe` | `deflated_sharpe` | **exact** |
| Insufficiencies | `min_observations_for_period_statistic`, `insufficient_independent_bets`, `too_few_closed_trades` | same | **exact** |

All four real wallets: **same verdict from both implementations.**

### 3.2 The four SYNTHETIC fixtures

These are constructed to probe the gate's decision boundaries. They are
**synthetic by construction** and are not evidence about any real wallet.

| Fixture | Independent bets (pkg/ref) | Win rate (pkg/ref) | Bayesian skill (pkg/ref) | Deflated Sharpe (pkg/ref) | Verdict (pkg/ref) | Agreement |
|---|---|---|---|---|---|---|
| consistent (180 rows) | 60 / 60 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | **CONSISTENT / CONSISTENT** | **exact** |
| one-lucky-win (63 rows) | 21 / 21 | 0.04761904762 / same | 5.483627319e-06 / same | 0 / 0 | **FLUKE / FLUKE** | **exact** |
| coin-flip (90 rows) | 30 / 30 | 0.5 / 0.5 | 0.5 / 0.5 | 0 / 0 | **FLUKE / FLUKE** | **exact** |
| decaying (240 rows) | 80 / 80 | — | — | — | **FLUKE / FLUKE** | **exact** |

Wilson interval bounds agree to <= 2.003e-10 across all four fixtures;
`edge_decay` n_early/n_recent agree exactly in all four.

The `one-lucky-win` fixture is the important one: a wallet with a single
large win among 21 bets has a Bayesian skill probability of **5.5e-06** and
a Deflated Sharpe of **0** — the gate reads it as no skill at all, and both
implementations agree.

### 3.3 The remaining comparison metrics

| Metric | Package | Reference | Agreement |
|---|---|---|---|
| Bayesian skill probability | — | — | **exact** (delta 0.000e+00) on 10 cases, and equal to numerical integration |
| Wilson interval (lower/upper) | — | — | <= 5.3e-10 on 10 cases |
| NIST sample size (55% vs 50%) | 637 | 637 | **exact** |
| SR0(N) for N = 1..1000 | — | — | <= 2.7e-09 |
| Independent (effective) bets | — | — | **exact** |
| Time-disjoint bet count | — | — | **exact** |
| Wins / losses / win rate | — | — | **exact** |
| Deflated Sharpe | — | — | <= 1.2e-13 |
| `edge_decay` n_early / n_recent | — | — | **exact** |
| **Verdict** | — | — | **exact** |
| Definitive rejections | — | — | **exact** |
| Insufficiencies | — | — | **exact** |

The `—` in this table marks the metrics that are asserted on the fixtures
and the 10-case reference tables rather than on the four real wallets; the
measured wallet-by-wallet values are in §3.1 above.

The vendor bands (GMGN win-rate and PnL-ratio thresholds) are reported as
context and **never change a verdict** — verified explicitly (both
implementations return CONSISTENT with and without a vendor label).

---

## 4. Can the gate be trusted for a live-capital decision?

**Yes, as a measurement instrument — with its scope stated precisely.**

- The statistics are now correct by three independent routes (the package,
  the independent reference, and numerical integration of the Beta
  posterior), and the implementation is pinned by tests that fail loudly.
- The gate is **conservative**: an unknown trial count is an automatic
  rejection, the Deflated Sharpe is computed against the number of
  candidates actually screened, survivorship-selected universes and
  backfilled history are rejected outright, and a thin sample cannot
  excuse a fluke.
- The vendor bands cannot influence a verdict.

**What it cannot do:** it cannot manufacture a qualified wallet. On the
population searched so far — PEPE's top-50 holders — **0 of 15 passed**,
and that remains the finding. The gate is the instrument; the *population*
is the open question, and it is documented in `reports/WALLET_SEARCH.md`.

One limit worth stating: the two implementations agree on the metrics they
both specify. Where a rule is ambiguous — for example, whether a bet that is
still open counts — the cross-check forces an explicit choice rather than
leaving it implicit, and those choices are documented in the code.

---

## 5. Reproducing it

```bash
cd C:/Users/HP/AppData/Local/hermes/projects/leapspace-quant
python leapspace/tests/test_crosscheck_gate.py
```

The test prints every comparison side by side and exits non-zero on any
mismatch. The cached real trades are in `reports/crosscheck_trades.json`; to
rebuild them from live data, run `reports/fetch_crosscheck_trades.py`.
