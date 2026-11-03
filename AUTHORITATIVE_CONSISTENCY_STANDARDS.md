# Authoritative Consistency Standards — Distinguishing a Consistently Profitable Trader from a One-Shot Winner

**Compiled:** 2026-11-03
**Companion document:** `AUTHORITATIVE_TRADER_STANDARDS.md` (the "evidence-of-profit" research). That document establishes *what must exist before you may say a wallet is profitable*. **This document establishes what must exist before you may say a wallet is *consistently* profitable** — i.e. that the edge is a repeatable property of the trader rather than the residue of one lucky trade, one favourable regime, or the best of many sampled wallets.

**Relationship to the companion document — read this first.** The two files do not overlap and do not conflict:
- `AUTHORITATIVE_TRADER_STANDARDS.md` §2–§5 covers: sample size (NIST), Wilson intervals, the rule of three, Sharpe, Sortino, max drawdown / drawdown duration, GIPS track-record length, GIPS survivorship retention, and the crypto-vendor label definitions (Nansen / GMGN / Birdeye / Arkham).
- **This document** covers: multiple testing & selection bias (Deflated Sharpe Ratio, Probability of Backtest Overfitting, Bonferroni, Benjamini–Hochberg), statistical power for profit and the trades-vs-independent-bets distinction, Bayesian skill estimation, consistency-of-returns metrics, drawdown-adjusted performance (Sortino/Calmar), track-record length mapped onto on-chain wallets, cross-chain and survivorship bias, and the crypto-native "consistently profitable wallet" question.
- Where this document cites a criterion that is **fully specified in the companion document**, it says so and gives only the URL and the delta, rather than restating it. Every URL here was fetched from this host on 2026-11-03.

**How to read this file.** Each criterion below carries seven fields:
(a) metric name · (b) concrete formula or threshold · (c) source organisation · (d) document/page title · (e) working URL · (f) verbatim quote or exact section/equation number · (g) classification tag.

Tags: **REGULATORY** · **EXCHANGE-OR-FIRM-STANDARD** · **ANALYTICS-VENDOR-CONVENTION** · **ACADEMIC-OR-PROFESSIONAL-GUILD**

**A note on how formulas are presented.** Where a formula comes from an academic paper, it is transcribed from the printed equation (for the Bailey–López de Prado papers, the equations were rendered as vector graphics and the mathematical symbols are dropped by text extraction, so the equations below were read off high-DPI page renders of the source PDFs and are marked **[read from page image]**). Where a formula is *this document's own* adaptation of a published formula to on-chain wallet data, it is marked **[ANALYST ADAPTATION]** and the underlying citation is given separately. Nothing here is paraphrased and presented as an author's.

---

## 1. MULTIPLE TESTING / SELECTION BIAS — the best of many sampled wallets

The core problem: if you screen N candidate wallets and rank them by realised PnL, the top wallet's performance contains a selection-bias component that grows with N, even when every wallet in the universe is a coin flip. Any consistency test applied *after* the ranking is applied to an already-inflated statistic.

### 1.1 — Deflated Sharpe Ratio (DSR): the expected maximum Sharpe under a null of no skill

- **Metric name:** Deflated Sharpe Ratio (DSR) — the Probabilistic Sharpe Ratio evaluated against a selection-adjusted rejection threshold
- **Concrete threshold (formula, transcribed from the source PDF):**

  From **Bailey & López de Prado**, *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality*, Journal of Portfolio Management, forthcoming 2014 (working-paper version dated 31 July 2014):

  **Equation (2)** **[read from page image, PDF p. 8]**:
  ```
  DSR = PSR(SR_0) = Z[ ( (SR_hat - SR_0) * sqrt(T - 1) )
                     / sqrt( 1 - gamma_3_hat*SR_hat + ((gamma_4_hat - 1)/4)*SR_hat^2 ) ]
  ```
  where (verbatim, same page) "**SR_0 = sqrt(V[{SR_n}]) ((1 - gamma)Z^-1[1 - 1/N] + gamma Z^-1[1 - 1/N e^-1])**, V[{SR_n}] is the variance across the trials' estimated SR and N is the number of independent trials. We also use information concerning the selected strategy: **SR_hat is its estimated SR, T is the sample length, gamma_3_hat is the skewness of the returns distribution and gamma_4_hat is the kurtosis of the returns distribution for the selected strategy. Z is the cumulative function of the standard Normal distribution.**"

  And the **expected maximum** it corrects against, **Equation (1)** **[read from page image, PDF p. 6]**:
  ```
  E[max{SR_n}] ~= E[{SR_n}] + sqrt(V[{SR_n}]) * ( (1 - gamma)*Z^-1[1 - 1/N] + gamma*Z^-1[1 - 1/(N e)] )
  ```
  where (verbatim) "**gamma (approx. 0.5772) is the Euler-Mascheroni constant, Z is the cumulative function of the standard Normal distribution, and e is Euler's number.**"

  **Decision threshold:** DSR ≥ 0.95 (the paper's own framing: "The investor has recognized that there is only a 90% chance that the true SR associated with this strategy is greater than zero" is treated as a *reject*, and "DSR would have been 0.9505, above the 95% confidence level" as an *accept*). §1.2 supplies the rejection threshold directly.
- **Source organisation:** David H. Bailey (Univ. of California, Davis / LBNL) and Marcos López de Prado (Guggenheim Partners / LBNL)
- **Document / page title:** "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality"
- **URL:** http://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf (author's own copy; the SSRN record is https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 — **SSRN returns HTTP 403 to this host**, so the author's PDF is the verified-working copy; the SSRN abstract number 2460551 is printed on the paper's own first page: "Electronic copy available at: http://ssrn.com/abstract=2460551")
- **Verbatim quote (abstract):** "The Deflated Sharpe Ratio (DSR) corrects for two leading sources of performance inflation: Selection bias under multiple testing and non-Normally distributed returns. In doing so, DSR helps separate legitimate empirical findings from statistical flukes."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 22 pages, text extracted; equations 1 and 2 read from 170–330 DPI page renders because the PDF stores the math as vector graphics)
- **On-chain application:** DSR is directly computable from a wallet's per-day return series. T = number of *return observations*, gamma_3/gamma_4 = skewness/kurtosis of that series, SR_hat = the wallet's per-observation Sharpe. N = **the number of candidate wallets that were screened before this one was selected** — see §1.4 for how to compute N for a wallet-screening pipeline. §1.5 gives the arithmetic.

### 1.2 — Probability of Backtest Overfitting (PBO) and the CSCV procedure

- **Metric name:** Probability of Backtest Overfitting (PBO) — "the probability that the model configuration selected as optimal IS will underperform the median of the N model configurations OOS"
- **Concrete threshold (formula and procedure, transcribed from the source PDF):**
  - PBO is estimated as **φ = ∫_{-∞}^{0} f(λ) dλ** — verbatim: "The PBO defined in Section 2.1 may now be estimated using the CSCV method with **φ = ∫_{-∞}^{0} f(λ)dλ**. This represents the rate at which optimal IS strategies underperform the median of the OOS trials."
  - The per-combination statistic is the **logit λ_c = ln(ω̄_c / (1 − ω̄_c))**, where ω̄_c = r̄_c/n* / (N + 1) is the relative OOS rank of the strategy that was best IS. Verbatim: "f) Define the relative rank of r̄_c,n* by **ω̄_c := r̄_c,n*/(N + 1) ∈ (0,1)**. … g) We define the **logit λ_c = ln(ω̄_c/(1−ω̄_c))**. High logit values imply a consistency between IS and OOS performances, which indicates a low level of backtest overfitting."
  - **Rejection threshold: PBO > 0.05 ⇒ REJECT.** The paper's own words: "In accordance with standard applications of the Neyman-Pearson framework, a customary approach would be to **reject models for which PBO is estimated to be greater than 0.05**."
- **Source organisation:** David H. Bailey, Jonathan M. Borwein, Marcos López de Prado, Qiji Jim Zhu (LBNL; University of Newcastle; Guggenheim Partners; Western Michigan University)
- **Document / page title:** "The Probability of Backtest Overfitting" (revised version, 27 February 2015; published *Journal of Computational Finance*, 2016)
- **URL:** https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf (SSRN record https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253 — **403 from this host**; the DOI landing page https://doi.org/10.21314/jcf.2016.322 was located via search but is not directly fetchable here)
- **Verbatim quote (abstract):** "We propose a general framework to assess the probability of backtest overfitting (PBO). We illustrate this framework with specific generic, model-free and nonparametric implementations in the context of investment simulations, which implementations we call combinatorially symmetric cross-validation (CSCV)."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 34 pages, text extracted)
- **On-chain application:** CSCV is directly implementable over a matrix of candidate wallets × time buckets. Treat each candidate wallet as a "trial"; each row of M is a time bucket; each column is one wallet's return over that bucket. The CSCV algorithm (Algorithm 2.3, verbatim: "Second, we partition M across rows, into an even number S of disjoint submatrices of equal dimensions. Third, we form all combinations C_S of M_s, taken in groups of size S/2…") then produces φ. **A wallet that only looks good because it was the best of a large screened universe will show a high PBO.**

### 1.3 — Bonferroni and Benjamini–Hochberg corrections, and how many trials N candidate wallets imply

- **Metric name:** Family-wise error rate (FWER) control (Bonferroni) and false discovery rate (FDR) control (Benjamini–Hochberg), applied to a screen of N candidate wallets
- **Concrete threshold (formulas, transcribed):**

  **Bonferroni** — NIST/SEMATECH e-Handbook §7.4.7.3 verbatim: "Therefore, if simultaneous multiple interval estimates are desired with an overall confidence coefficient 1 − α, one can construct each interval with confidence coefficient **(1 − α/g)**, and the Bonferroni inequality insures that the overall confidence coefficient is at least 1 − α." (g = number of comparisons). The general inequality as printed: "P(⋂_{i=1}^{g} A_i) ≥ 1 − ∑_{i=1}^{g} P[Ā_i]".

  **Benjamini–Hochberg** — *Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing*, J. R. Statist. Soc. B **57**(1), 1995, 289–300, **procedure (1)** transcribed verbatim from the paper: "Consider testing H_1, H_2, …, H_m based on the corresponding p-values P_1, P_2, …, P_m. Let P_(1) ≤ P_(2) ≤ … ≤ P_(m) be the ordered p-values, and denote by H_(i) the null hypothesis corresponding to P_(i). Define the following Bonferroni-type multiple-testing procedure: **let k be the largest i for which P_(i) ≤ (i/m) q\* ; then reject all H_(i), i = 1, 2, …, k.** (1)" — and "**Theorem 1. For independent test statistics and for any configuration of false null hypotheses, the above procedure controls the FDR at q\*.**"

  **How many trials a sample of N candidate wallets implies.** This is the question the task poses, and the answer is: **the trial count is the number of wallets *screened*, not the number that passed.** Concretely:
  - If a screener evaluates **M** candidate wallets and the code selects the top one, then in the DSR/PBO framing **M is the trial count** and N is the number of *independent* trials among them.
  - Bailey & López de Prado, §A.3 of the DSR paper, verbatim: "**It is critical to understand that the N used to compute E[max{SR_n}] corresponds to the number of independent trials. Suppose that we run M trials, where only N trials are independent, N<M. Clearly, using M instead of N will overstate E[max{SR_n}].**" Their Appendix 3 gives the interpolation **Equation (9)**: "Given an estimated average correlation ρ̄̂, we could therefore interpolate between these two extreme outcomes to obtain **N̂ = M·(1 − ρ̄̂)**" (the paper's notation: N̂ as a function of M and the weighted average correlation ρ̄, defined in Equations (7)–(8) as the constant ρ̄ that preserves the quadratic form of the correlation matrix C).
  - **Expected maximum Sharpe under a null of no skill**, computed from Eq. (1) with V = 1 (this document's arithmetic from the paper's formula, γ = 0.5772):

    | N independent trials | E[max SR], V=1 | E[max SR], V=0.5 |
    |---|---|---|
    | 10 | 1.5746 | 1.1134 |
    | 25 | 1.9971 | 1.4122 |
    | 50 | 2.2763 | 1.6096 |
    | 100 | 2.5306 | 1.7894 |
    | 250 | 2.8377 | 2.0065 |
    | 500 | 3.0525 | 2.1585 |
    | 1000 | 3.2551 | 2.3017 |
    | 5000 | 3.6877 | 2.6076 |

    The paper's own worked example corroborates the arithmetic: "if the researcher tries only **N = 10** alternative configurations of an investment strategy, he or she is expected to find a strategy with a Sharpe ratio IS of **1.57**, despite the fact that all strategies are expected to deliver a Sharpe ratio zero OOS" (*Pseudo-Mathematics and Financial Charlatanism*, §2, Proposition 2.1) — matching the N=10 row above.
  - **Practical consequence for a wallet screener:** screening 5,000 candidate wallets and reporting the winner's Sharpe without deflating for N=5,000 means a **null-SR wallet with an observed annualised Sharpe above ~3.69 is the expected outcome**, not evidence of skill.
- **Source organisation:** National Institute of Standards and Technology (NIST) for Bonferroni; Yoav Benjamini & Yosef Hochberg (Tel Aviv University) for FDR; Bailey & López de Prado for the trial-count derivation
- **Document / page titles:** "7.4.7.3. Bonferroni's method" (NIST/SEMATECH e-Handbook of Statistical Methods) · "Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing" (J. R. Statist. Soc. B) · "The Deflated Sharpe Ratio…", Appendix A.3
- **URLs:** https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm · https://www.math.tau.ac.il/~yekutiel/eBayes/bh_1995.pdf (a verbatim reprint of the JRSS-B paper; the publisher's DOI https://doi.org/10.1111/j.2517-6161.1995.tb02031.x returns **HTTP 403** and the JSTOR record https://www.jstor.org/stable/2346101 serves a **JavaScript bot-wall** rather than the article, from this host) · http://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf · http://www.davidhbailey.com/dhbpapers/backtest-pseudo.pdf
- **Verbatim quote (BH, Summary):** "It calls for controlling the expected proportion of falsely rejected hypotheses -the false discovery rate. This error rate is equivalent to the FWER when all hypotheses are true but is smaller otherwise."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD** (NIST and the two journal papers)
- **Fetched:** Yes (all four)
- **Note on BHY:** Harvey, Liu & Zhu (§1.4) use the Benjamini–Hochberg–Yekutieli variant, which controls FDR under *arbitrary* dependence between the test statistics — the correct choice when candidate wallets are correlated (same deployer, same cluster, same token). Their summary table: "Benjamini, Hochberg, and Yekutieli (BHY) | sequential | false discovery rate".

### 1.4 — Harvey–Liu–Zhu: the multiple-testing hurdle a *newly discovered* signal must clear

- **Metric name:** Multiple-testing-adjusted significance threshold for a newly discovered signal
- **Concrete threshold:** **t-statistic > 3.0** for a factor discovered by data mining (as opposed to derived from theory, for which they concede a lower bar is defensible). Their own recommendation, verbatim: "We argue that a newly discovered factor today should have a t-statistic that **exceeds 3.0**." And: "a t-statistic of 2.0 is no longer appropriate—even for factors that are derived from theory."
- **Source organisation:** Campbell R. Harvey (Duke University), Yan Liu (Texas A&M University), Heqing Zhu (University of Oklahoma) — *The Review of Financial Studies* 29(1), 2016
- **Document / page title:** "…and the Cross-Section of Expected Returns"
- **URL:** https://people.duke.edu/~charvey/Research/Published_Papers/P118_and_the_cross.PDF (author's copy) · NBER working-paper record: https://www.nber.org/papers/w20592 (verified 200)
- **Verbatim quote (abstract):** "Our paper introduces a multiple testing framework and provides historical cutoffs from the first empirical tests in 1967 to today. A new factor needs to clear a much higher hurdle, with a **t-statistic greater than 3.0**. We argue that most claimed research findings in financial economics are likely false."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 64 pages, text extracted)
- **On-chain application:** *Analyst adaptation.* For a wallet, the analogous statement is: a wallet selected as the best of a large screened population must clear a materially higher bar than a wallet evaluated in isolation. Translate the wallet's return series into a t-statistic (e.g. the t-stat of the mean per-day return against a null of zero) and apply the multiple-testing-adjusted threshold rather than the naive 1.96.

### 1.5 — The multiple-testing haircut on a Sharpe ratio (Harvey & Liu, "Backtesting")

- **Metric name:** Multiple-testing haircut applied to a reported Sharpe ratio
- **Concrete threshold:** The paper's method is analytical, not a fixed number; the paper explicitly rejects the folklore 50% haircut as a rule of thumb. Verbatim: "The 50% haircut is only a rule of thumb. Our article's goal is to develop an analytical way to determine the haircut's magnitude." And: "We argue that it is a serious mistake to use the usual 50% haircut. Our results show that the multiple testing haircut is **nonlinear**. The highest Sharpe ratios are only moderately penalized, while the marginal Sharpe ratios are heavily penalized."
- **Source organisation:** Campbell R. Harvey and Yan Liu — *The Journal of Portfolio Management* 42(1), Fall 2015
- **Document / page title:** "Backtesting"
- **URL:** https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF
- **Verbatim quote (opening):** "A common practice in evaluating backtests of trading strategies is to discount the reported Sharpe ratios by 50%. There are good economic and statistical reasons for reducing the Sharpe ratios. The discount is a result of data mining."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 17 pages)
- **Implementation note:** use DSR (§1.1) rather than a fixed haircut; it is the analytical version of the same correction and additionally handles non-normality.

### 1.6 — The SEC's own multiple-testing rule, applied to a published wallet leaderboard

- **Metric name:** Extracted-performance condition (a performance claim about a *subset* of a larger set must present the whole set)
- **Concrete threshold:** Binary, no numbers. Verbatim: "**Any extracted performance, unless the advertisement provides, or offers to provide promptly, the performance results of the total portfolio from which the performance was extracted.**" Also 17 CFR 275.206(4)-1(d)(6)(ii)–(iii) requires disclosure of "the criteria used and assumptions made" and "the risks and limitations" for any hypothetical performance.
- **Source organisation:** U.S. Securities and Exchange Commission
- **Document / page title:** 17 CFR 275.206(4)-1 — Investment adviser marketing, paragraphs (d)(5) and (d)(6)
- **URL:** https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (verified 200)
- **On-chain application:** publishing "our top 10 memecoin wallets" with aggregate win rate, without publishing the full screened universe's results, is *extracted performance* under (d)(5) and would need the universe's results attached.

---

## 2. STATISTICAL POWER FOR PROFIT — trades are not independent bets

### 2.1 — The governing formula: minimum N for a win rate claim (NIST)

This is the **power** anchor and it is carried forward from the companion document (`AUTHORITATIVE_TRADER_STANDARDS.md` §2.1). It is restated here only because the *independent-bets* correction below changes its input.

- **Metric name:** Minimum sample size to detect a change in a proportion at a stated confidence and power
- **Concrete threshold (formula, verbatim from the NIST page):** `N ≥ [ (z_{1−α}·√(p₀(1−p₀)) + z_{1−β}·√(p₁(1−p₁))) / δ ]²` (one-sided); two-sided uses `z_{1−α/2}`. Plus the Fleiss/Levin/Paik continuity correction `N = N′ + 1/δ`. NIST's own caveat, verbatim: "**Note that taking the value of the proportion defective to be 0.5 leads to the largest possible sample size.**"
- **Source organisation:** National Institute of Standards and Technology (NIST)
- **Document / page title:** "7.2.4.2. Sample sizes required", NIST/SEMATECH e-Handbook of Statistical Methods
- **URL:** https://www.itl.nist.gov/div898/handbook/prc/section2/prc242.htm
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (verified 200)
- **Worked value (this document's arithmetic, from NIST's formula):** p₀ = 0.50 vs p₁ = 0.55, α = 0.05 one-sided, β = 0.20, δ = 0.05 ⇒ **N ≥ 617** (637 with the continuity correction). For p₁ = 0.60 ⇒ 610 (630); p₁ = 0.65 ⇒ 600 (620).
- **Critical point:** N here is the count of **independent** Bernoulli trials, not the count of raw trades. See §2.2.

### 2.2 — Trades vs independent bets: serial correlation and overlapping positions

- **Metric name:** Effective number of independent bets (breadth), and the serial-correlation correction to Sharpe
- **Concrete threshold / formula:**
  - **Lo (2002)**, verbatim: "**I find that the annual Sharpe ratio for a hedge fund can be overstated by as much as 65 percent because of the presence of serial correlation in monthly returns**, and once this serial correlation is properly taken into account, the rankings of hedge funds based on Sharpe ratios can change dramatically." Also: "I show that **monthly Sharpe ratios cannot be annualized by multiplying by √12 except under very special circumstances**, and I derive the correct method of conversion in the general case of stationary returns."
  - **CFA Institute**, on why a longer measurement window is not a free choice: "An investor must consider the length of the time period used in the measurement; **longer time periods tend to result in lower volatility measures**." And on multiperiod returns: Sharpe "believed using multiperiod returns complicates the ratio **because of compounding or potential serial correlation**."
  - **Bailey & López de Prado (AFML)**, the practitioner treatment of *overlapping* bets: the book defines "**Overlapping Outcomes**" (§4.2) and "**Average Uniqueness of a Label**" (§4.4) as the weights that account for the fact that concurrent trades share the same price path, and prescribes "**Purging and embargoing**" (§7.4) to stop overlapping labels leaking across a train/test split. The TOC of the SSRN reprint carries the section headings verbatim: "4.2 Overlapping Outcomes, 59 · 4.3 Number of Concurrent Labels, 60 · 4.4 Average Uniqueness of a Label, 61" and "8 Evaluation — Cross-validation leakage — Purging and embargoing".
  - **Grinold's breadth, restated by CFA Institute:** the fundamental law "separates the expected value added … into the basic elements of the strategy: skill as measured by the information coefficient, structuring of the portfolio as measured by the transfer coefficient, **breadth of the strategy measured by the number of independent decisions per year**, and aggressiveness measured by the benchmark tracking risk." Grinold's own emphasis, quoted in the academic literature: "Grinold (1989) provided a detailed discussion on this subject and **emphasized the importance of counting only independent bets as breadth**."
- **Source organisation:** Andrew W. Lo (MIT / CFA Institute *Financial Analysts Journal*) · CFA Institute · Marcos López de Prado (*Advances in Financial Machine Learning*, Wiley 2018) · Richard Grinold (via Avellaneda, Lee & Ou, *Journal of Portfolio Management*) · CFA Institute (curriculum)
- **Document / page titles:** "The Statistics of Sharpe Ratios", *Financial Analysts Journal* 58(4), July/August 2002 · "The Sharpe Ratio and the Information Ratio" (Deborah Kidd, CFA — *Investment Performance Measurement*, CFA Institute) · *Advances in Financial Machine Learning*, Wiley 2018 (SSRN reprint) · "The Fundamental Law of Active Management: Time Series Dynamics and Cross-Sectional Properties", *Journal of Portfolio Management* 42(4) · "Analysis of Active Portfolio Management" (CFA Institute Refresher Reading, 2026)
- **URLs:** https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios · https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/sharpe-ratio-and-the-information-ratio.pdf · https://www.smallake.kr/wp-content/uploads/2018/07/SSRN-id3104847.pdf (SSRN id 3104847 reprint; the canonical SSRN abstract page is **403 from this host**) · https://math.nyu.edu/inmemoriam/avellaneda/FundamentalLawFT.pdf · https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/analysis-active-portfolio-management
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD** (all five)
- **Fetched:** Yes (all five; the AFML reprint PDF is the full book front-matter + TOC + ch.1 body, 61 pages, so the section *headings and page numbers* are verified from the retrieved body while the chapter 4/7 *body text* is behind the book's "Full version available at" link — flagged accordingly)
- **On-chain implementation [ANALYST ADAPTATION, derived from the above]:** define a wallet's **independent bets** as the maximal set of **non-overlapping** closed trades — i.e. greedily select trades in chronological order, accepting a trade only if its holding interval does not overlap an already-accepted trade's holding interval. Feed the *count of independent bets* (not the raw trade count) into the NIST formula (§2.1) and into the DSR's T (sample length) — and note that for a wallet trading the same token repeatedly, overlapping positions are the norm, not the exception, so raw trade count materially overstates the evidence.

### 2.3 — The minimum independent-bet count, stated as a table

- **Metric name:** Minimum number of independent bets required to distinguish a claimed win rate from chance
- **Concrete threshold:** Computed from the NIST formula with p₀ = 0.50 (chance), one-sided α = 0.05, power 1 − β = 0.80, δ = 0.05. This document's arithmetic:

  | Claimed win rate p₁ | Minimum N (independent bets) | With continuity correction |
  |---|---|---|
  | 0.55 | 617 | 637 |
  | 0.60 | 610 | 630 |
  | 0.65 | 600 | 620 |

  **This is the criterion that actually rejects one-shot winners:** a wallet with 30 raw trades but only 8 non-overlapping independent bets cannot support *any* win-rate claim above chance at these parameters.
- **Source organisation:** NIST (formula) — thresholds computed by this document
- **Document / page title:** NIST/SEMATECH e-Handbook §7.2.4.2
- **URL:** https://www.itl.nist.gov/div898/handbook/prc/section2/prc242.htm
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD** (for the formula); the specific parameterisation (α = 0.05, β = 0.20, δ = 0.05, p₀ = 0.50) is **ANALYST_CHOICE** and is labelled as such in the JSON
- **Fetched:** Yes

### 2.4 — The statistical-power framing Bailey et al. themselves use

- **Metric name:** Minimum backtest length (MinBTL) as a function of the number of trials
- **Concrete threshold (formula, transcribed from the source PDF):** "**Proposition 2.1.** Given a sample of IID random variables, x_n ∼ Z, n = 1, …, N where Z is the CDF of the Standard Normal distribution, the expected maximum of that sample, E[max_N] = E[max{x_n}], can be approximated for a large N as **E[max_N] ≈ (1 − γ)Z⁻¹[1 − 1/N] + γZ⁻¹[1 − 1/(N e)]** (2.4) where **γ ≈ 0.5772156649** … is the Euler-Mascheroni constant, and N >> 1. An upper bound to Eq.(2.4) is **√(2 ln N)**."
- **Source organisation:** Bailey, Borwein, López de Prado, Zhu
- **Document / page title:** "Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance", *Notices of the American Mathematical Society* 61(5), May 2014
- **URL:** http://www.davidhbailey.com/dhbpapers/backtest-pseudo.pdf (author's copy; the AMS URL https://www.ams.org/notices/201405/rnoti-p458.pdf returns **HTTP 403 from this host**)
- **Verbatim quote:** "Proposition 2.1 has important implications. As the researcher tries a growing number of strategy configurations, there will be a **non-null probability of selecting IS a strategy with null expected performance OOS**. Because the hold-out method does not take into account the number of trials attempted before selecting a model, it cannot assess the representativeness of a backtest."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 34 pages)

---

## 3. BAYESIAN SKILL ESTIMATION — the probability the win rate beats chance

### 3.1 — Beta–Binomial model with a uniform Beta(1,1) prior

- **Metric name:** Posterior probability that a trader's true win rate exceeds chance (p > 0.5), under a Beta–Binomial model
- **Concrete threshold (formula, transcribed from the source):**
  - **Prior:** π ~ Beta(α, β). The standard weak/uniform choice is **Beta(1,1) ≡ Unif(0,1)** — the source states the equivalence verbatim: "c. **Beta(1,1) or, equivalently, Unif(0,1)**".
  - **Likelihood:** Y | π ~ Bin(n, π), with pmf `f(y|π) = C(n,y) π^y (1−π)^(n−y)`.
  - **Posterior (conjugacy), Equation (3.10):** `π | (Y = y) ~ Beta(α + y, β + n − y)`.
  - **Posterior summaries, Equation (3.11):** `E(π|Y=y) = (α + y)/(α + β + n)`; `Mode(π|Y=y) = (α + y − 1)/(α + β + n − 2)`; `Var(π|Y=y) = (α+y)(β+n−y) / [ (α+β+n)² (α+β+n+1) ]`.
  - **Skill statistic:** `P(θ > 0.5 | y, n)` computed from the posterior Beta(α+y, β+n−y). With the uniform Beta(1,1) prior this becomes Beta(1+y, 1+n−y).
- **Source organisation:** Jackson Barber, Adrienne Bay, Helge Solberg (academic textbook, CRC Press) — hosted as the book's own open web edition
- **Document / page title:** "Bayes Rules! An Introduction to Applied Bayesian Modeling", Chapter 3 "The Beta-Binomial Bayesian Model" (§3.4 "The Beta-Binomial model"; §3.1.2 "Tuning the Beta prior")
- **URL:** https://www.bayesrulesbook.com/chapter-3.html
- **Verbatim quote (§3.4):** "This general model has vast applications, applying to any setting having a parameter of interest π that lives on [0,1] with any tuning of a Beta prior and any data Y which is the number of 'successes' in n fixed, independent trials, each having probability of success π." And: "In this case, we say that the Beta(α, β) model is a **conjugate prior** for the corresponding Bin(n, π) data model."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (HTML chapter, text extracted)
- **Threshold:** `P(θ > 0.5 | y, n) ≥ 0.95` is the natural operational cut, but **it is an ANALYST_CHOICE** — no source publishes a probability threshold for trader skill. What is published is the model.
- **Worked values (this document's arithmetic from the published posterior):** with the uniform Beta(1,1) prior:

  | wins y | n | win rate | posterior | P(θ > 0.5) |
  |---|---|---|---|---|
  | 30 | 50 | 0.60 | Beta(31,21) | 0.9196 |
  | 55 | 100 | 0.55 | Beta(56,46) | 0.8401 |
  | 60 | 100 | 0.60 | Beta(61,41) | 0.9770 |
  | 65 | 100 | 0.65 | Beta(66,36) | 0.9987 |
  | 70 | 100 | 0.70 | Beta(71,31) | ≈1.0000 |
  | 40 | 100 | 0.40 | Beta(41,61) | 0.0230 |

  (A 60% win rate on 30 trades gives only P(θ>0.5) = 0.92 — **it does not clear a 0.95 bar.** A 55% win rate on 100 trades gives 0.84. This is the Bayesian statement of the same fact the NIST formula states in the frequentist idiom.)

### 3.2 — Why a Bayesian posterior beats a raw win rate for the "one-shot winner" question

- **Metric name:** Posterior-vs-point-estimate discipline
- **Concrete threshold:** Report `P(θ > 0.5)` (or the full posterior interval), **not** the point estimate alone. **[ANALYST ADAPTATION]** — no source publishes this as a rule; it follows from the published model (§3.1) and from the requirement that the estimate carry its own uncertainty.
- **Source organisation:** (as §3.1)
- **Document / page title:** (as §3.1)
- **URL:** https://www.bayesrulesbook.com/chapter-3.html
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD** (for the model); **ANALYST_CHOICE** for the reporting rule
- **Fetched:** Yes

### 3.3 — Bayesian consistency as a *sequence* of evidence, not a snapshot

- **Metric name:** Posterior stability / sequential updating
- **Concrete threshold:** **[ANALYST ADAPTATION]** — require the posterior `P(θ > 0.5)` computed on the **first half** of the wallet's history to be materially close to the posterior on the **full** history. A wallet whose posterior collapses when the first half is removed is a fluke, regardless of its headline win rate.
- **Source organisation:** Barber, Bay & Solberg (*Bayes Rules!*) — the source's §4.4 "Sequential analysis: Evolving with data" and §4.5 "Proving data order invariance" establish the sequential-update property that makes split-half posterior comparison meaningful (the posterior is order-invariant, so splitting by time is a legitimate holdout).
- **Document / page title:** "Bayes Rules!…", Chapter 4 "Balance and Sequentiality in Bayesian Analyses"
- **URL:** https://www.bayesrulesbook.com/chapter-3.html (Chapter 4 is at https://www.bayesrulesbook.com/chapter-4.html; the URL above is the verified-fetched one)
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD** (for the model); **ANALYST_CHOICE** for the split-half comparison
- **Fetched:** Partially — Chapter 3 fetched and read; Chapter 4's section titles verified from the Chapter 3 page's table of contents but its body not separately fetched.

---

## 4. CONSISTENCY OF RETURNS — the ratio of positive periods to total periods

### 4.1 — Consistency ratio (the standard published definition)

- **Metric name:** Consistency ratio — the fraction of periods in which the manager produced positive excess returns
- **Concrete threshold (formula, verbatim):** "**Consistency Ratio - A measure of how consistently the manager is able to exhibit positive excess returns. To calculate the consistency ratio, the number of months the manager had positive excess returns is divided by the total number of months. The higher the number, the better.**"
- **Source organisation:** Principal Financial Group / Marietta Board of Pensions (an institutional defined-benefit pension plan's published investment-report glossary)
- **Document / page title:** "Investment Option Performance Results and Statistics", Contract No. 4-52551 — Glossary of Terms, p. 26
- **URL:** https://www.mariettaga.gov/DocumentCenter/View/8820/March-31-2016-Supplemental-Pension-Report
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION** — this is a **pension plan's published reporting convention**, not a regulator, exchange, professional body or academic standard. It is the cleanest published definition located, and it is cited as such. **No authority located publishes a minimum acceptable consistency ratio** — the source says only "The higher the number, the better."
- **Fetched:** Yes (PDF, 28 pages, text extracted)

### 4.2 — Whether a professional body publishes a minimum number of periods

- **Metric name:** Minimum observation count for a presented risk statistic, and the annual-period presentation rule
- **Concrete threshold:** GIPS publishes a **hard observation count**: "**4.C.36** For composites with at least three annual periods of performance, the firm must disclose if the three-year annualized ex post standard deviation of the composite and/or benchmark is not presented **because 36 monthly returns are not available**." So a GIPS-compliant record needs **36 monthly return observations** to carry its headline risk statistic. (Parallel: 6.C.29 for pooled funds.)
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *Global Investment Performance Standards (GIPS®) for Firms*, 2020 edition — provisions 4.C.36, 6.C.29, 4.A.1(b)
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Verbatim quote (4.A.1(b)):** "**b. Composite returns for each annual period.**"
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 146 pages)
- **Honest negative finding:** GIPS's 36-monthly-return rule is a *disclosure* rule about when a statistic can be presented — it is **not** a rule about how many periods a wallet must have to demonstrate consistency. **No professional body, regulator or academic source located publishes a minimum "consistency ratio" or a minimum number of positive periods.** The 36-month figure is the only hard observation count in the sources examined.

### 4.3 — CFA Institute's own statement about appraisal ratios and luck vs skill

- **Metric name:** Appraisal ratios as skill measures (and their stated limitations)
- **Concrete threshold:** No numbers published. What is published, verbatim: "Investment performance appraisal ratios—including the Sortino ratio, upside/downside capture ratios, maximum drawdown, and drawdown duration—**measure investment skill**. Appraisal ratios must be used with care, noting the assumptions of each ratio and affording the appropriateness to the measured investment process, risk tolerance, and investor time horizon. Although appraisal ratios help identify manager skill (**as opposed to luck**), they often are based on investment return data, which are often limited and subject to error."
- **Source organisation:** CFA Institute
- **Document / page title:** "Portfolio Performance Evaluation" — CFA Institute Refresher Reading, 2026 curriculum (Learning Module 1, Portfolio Performance Evaluation)
- **URL:** https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/portfolio-performance-evaluation
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes

### 4.4 — Consistency of *relative* performance: the information ratio as a consistency measure

- **Metric name:** Information ratio — consistency-weighted excess return
- **Concrete threshold (formula):** `IR = (active return) / (tracking error)`. The CFA Institute's framing is that the IR "simultaneously considers both the level of excess return as well as **consistency** in which the excess return was delivered to investors." **No published band.**
- **Source organisation:** CFA Institute
- **Document / page title:** "The Sharpe Ratio and the Information Ratio" (Deborah Kidd, CFA — *Investment Performance Measurement*, CFA Institute / H17004, ©2011)
- **URL:** https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/sharpe-ratio-and-the-information-ratio.pdf
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 4 pages)
- **Note:** this file is the same CFA Institute PDF already cited in the companion document §3.1; the delta here is the IR's *consistency* role, which the companion document does not cover.

---

## 5. DRAWDOWN-ADJUSTED PERFORMANCE — Sortino, Calmar, and drawdown duration

### 5.1 — Sortino ratio

- **Metric name:** Sortino ratio — excess return over downside risk relative to a Minimum Accepted Return
- **Concrete threshold (formula, verbatim from the CFA Institute PDF):** "**S = (Mean portfolio return – MAR) / Downside deviation.**" And: "The formula for the Sortino ratio is simple; **it is calculated in the same way as the Sharpe ratio except that the MAR replaces the risk-free rate in the numerator and downside deviation replaces standard deviation in the denominator.**"
- **Source organisation:** CFA Institute
- **Document / page title:** "The Sortino Ratio: Is Downside Risk the Only Risk that Matters?" by Deborah Kidd, CFA — *Investment Performance Measurement* (CFA Institute / H17004), ©2012
- **URL:** https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/the-sortino-ratio.pdf
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 3 pages)
- **How it differs from Sharpe:** the denominator is **downside deviation relative to a user-set MAR**, not total standard deviation, so upside volatility is not penalised. The source's own caveat: "several variations of the downside deviation calculation exist, and **which one an investor uses matters a great deal**."
- **No published band.** Same as the companion document §3.2.

### 5.2 — Calmar ratio

- **Metric name:** Calmar ratio — return per unit of maximum drawdown
- **Concrete threshold (formula, verbatim from the peer-reviewed source):** "**Calmar ratio (CR)** Another alternative is to replace the standard deviation by the maximum drawdown (MAXDD). Such a ratio is called Calmar (California managed accounts reports): **CR(R_p, T) = E(R_p − R_f) / MAXDD(T).**"
- **Source organisation:** Anlan Wang, Aleš Kresta, Tomáš Tichý — *Computational Management Science* (Springer), Vol. 21, article 17 (2024), "Evaluation of strategy portfolios" (open access, peer-reviewed)
- **Document / page title:** "Evaluation of strategy portfolios", §2.2 (performance-measure definitions)
- **URL:** https://link.springer.com/article/10.1007/s10287-023-00497-5
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD** (for the formula as published in a peer-reviewed journal)
- **Fetched:** Yes
- **Attribution and its limits, stated honestly:** the ratio is named for **California Managed Accounts Reports**, the newsletter of Terry W. Young, who introduced it in 1991. The originating article (Young, "Calmar Ratio: A Tool for Portfolio Performance Evaluation", *Investment Analysis and Portfolio Management*, HarperCollins/Toyota, 1991; also published in the trade journal *Futures*) **was not directly fetchable from this host** — the archive.org full-text copy of *Investment Analysis and Portfolio Management* located for this research contains **zero** occurrences of "Calmar", "drawdown" or "Terry W. Young", so the original chapter could not be verified. The 36-month version is documented second-hand: "The Calmar ratio uses a slightly modified Sterling ratio – average annual rate of return for the last 36 months divided by the maximum drawdown for the last 36 months – and calculates it on a monthly basis, instead of the Sterling ratio's yearly basis" (Wikipedia, quoting Young 1991 — https://en.wikipedia.org/wiki/Calmar_ratio, fetched 200). **The "36 months" window is therefore a SECONDARY attribution and is flagged UNVERIFIED against the primary source.** The peer-reviewed formula above (`E(R_p − R_f) / MAXDD(T)`) does not fix the window and is the version this document specifies. A second peer-reviewed corroboration that Calmar and maximum drawdown are used together as standard standalone performance measures: Molyboga & L'Ahelec, "A simulation-based methodology for evaluating hedge fund investments", *Journal of Asset Management* 17, 434–452 (2016), https://link.springer.com/article/10.1057/jam.2016.3 — "Standalone performance measures include annualized return, Sharpe and Calmar ratios, maximum drawdown … and the t-statistic of α …".
- **No published band.**

### 5.3 — Maximum drawdown and drawdown duration

- **Metric name:** Maximum drawdown (MDD) and drawdown duration
- **Concrete threshold:** **CFA Institute publishes no numerical band.** The two are listed as *appraisal ratios* that "measure investment skill" and "must be used with care" (§4.3 above, same source and quote). The definition and the "no direct predictive value" caveat are stated in CFA Institute's own digest of the drawdown literature: "They show that drawdown is calculated by comparing the value of a cumulative return with a previous peak that is the maximum cumulative return. … the historical drawdown period is variable because it depends on the timing of the peak. As a result, **drawdown reflects only factual returns from a past period and has no direct predictive value**, which other metrics, such as volatility, imply."
- **Source organisation:** CFA Institute
- **Document / page title:** "Performance Drawdowns in Asset Management: Extending Drawdown Analysis to Active Returns (Digest Summary)", CFA Institute Journal Review, by Servaas Houben, CFA, 1 January 2018
- **URL:** https://rpc.cfainstitute.org/research/cfa-digest/2018/01/dig-v48-n1-3
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **Maximum drawdown as a predictor of subsequent skill** (a peer-reviewed result worth carrying): "Maximum drawdowns for mutual funds are persistent, **indicative of manager skill**, and predictive of subsequent performance." — *Financial Analysts Journal* (2022), "Maximum Drawdown as Predictor of Mutual Fund Performance and Flows", https://rpc.cfainstitute.org/research/financial-analysts-journal/2022/maximum-drawdown-as-predictor-of-mutual-fund-performance-flows (fetched 200; abstract read).
- **How they differ from Sharpe:** Sharpe penalises upside and downside volatility symmetrically and is scale-free by construction; Sortino replaces the denominator with downside deviation about a MAR; Calmar replaces it with the single worst peak-to-trough loss. A wallet with one enormous drawdown can have a good Sharpe and a poor Calmar — which is exactly the profile of a wallet whose edge is concentrated in a few trades.

---

## 6. TRACK-RECORD LENGTH — how long before a performance claim may be made

### 6.1 — The published institutional minimum (carried forward)

- **Metric name:** Minimum track-record length before a performance record may be presented
- **Concrete threshold:** GIPS: **five years** to claim compliance (1.A.3), building up to **10 years** (4.A.1(a), 6.A.1(a)); a gips advertisement presenting composite returns must present **one-, three- and five-year** annualized returns through the most recent period, plus since-inception if under five years (8.C.1(a)). SEC Marketing Rule 206(4)-1(d)(2): **one-, five- and ten-year** periods, or the **life of the portfolio** if shorter.
- **Source organisation:** CFA Institute (GIPS); U.S. SEC
- **Document / page titles:** *GIPS for Firms*, 2020 — 1.A.3, 4.A.1(a), 6.A.1(a), 8.C.1(a) · 17 CFR 275.206(4)-1(d)(2)
- **URLs:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf · https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1
- **Verbatim quote (1.A.3):** "To initially claim compliance with the GIPS standards, the firm must attain compliance for a minimum of five years or for the period since the firm inception if the firm has been in existence for less than five years."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD** (GIPS) / **REGULATORY** (SEC)
- **Fetched:** Yes (both; both URLs verified 200)
- **Cross-reference:** full treatment in the companion document §1.3 and §4.3; not restated here.

### 6.2 — Mapping "five years" onto an on-chain wallet: the chain-coverage ceiling

- **Metric name:** Maximum attainable track-record length for a wallet, bounded by the chain's index start date
- **Concrete threshold (published table):** Nansen's per-chain earliest available data: **Ethereum 30 Jul 2015 · Tron 25 Jun 2018 · TON 15 Nov 2019 · Solana 17 Mar 2020 · Polygon 30 May 2020 · BNB Chain 29 Aug 2020 · Avalanche 23 Sep 2020 · Arbitrum 29 May 2021 · Optimism 11 Nov 2021 · Sui 12 Apr 2023 · Base 15 Jun 2023 · Linea 06 Jul 2023 · Sonic 01 Dec 2024 · HyperEVM 18 Feb 2025 · Monad 14 May 2025 · Robinhood 30 Apr 2026 · Arc 15 Jul 2026.** Nansen's own summary: "Chains that onboarded before mid-2023 (Ethereum through Linea above) offer **3+ years** of history; newer chains offer proportionally less."
- **Source organisation:** Nansen
- **Document / page title:** "Data Coverage by Chain" (Nansen API docs)
- **URL:** https://docs.nansen.ai/api/data-coverage.md
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes (markdown version, fetched 200)
- **The consequence, stated plainly:** **a five-year track record does not exist on most memecoin chains.** A Base wallet's maximum possible history as of 2026-11-03 is ~3.4 years; a Monad wallet's is ~1.5 years; a Sonic wallet's is ~1.9 years. Any claim of "5-year consistency" on those chains is impossible, not merely unproven. A consistency standard applied across chains must therefore be expressed in **independent bets / return observations**, with the chain's coverage date used to *cap* the maximum achievable, not to demand an unreachable target.
- **Nansen's own look-ahead caveat, verbatim:** "Historical endpoints **avoid look-ahead bias** where point-in-time sources are available, but results are not immutable response snapshots. Results may still be revised for late-arriving or backfilled onchain data, data-quality corrections, historical-price fixes, attribution or label-history updates…"

### 6.3 — The floor for a *per-period* statistic

- **Metric name:** Minimum observation count to present a period-based risk statistic
- **Concrete threshold:** **36 monthly returns** (GIPS 4.C.36 / 6.C.29, quoted in §4.2). **On-chain analogue:** a wallet must have at least 36 **daily return observations** (or the equivalent in daily units) before a period-based statistic is presented at all.
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *GIPS for Firms*, 2020 — 4.C.36
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **Honest note:** the "36 daily observations on-chain" mapping is an **ANALYST ADAPTATION** of a GIPS *disclosure* rule for a *composite* record. The 36 figure is cited; the mapping is this document's.

---

## 7. CROSS-CHAIN AND SURVIVORSHIP BIAS

### 7.1 — The published anti-survivorship rule for performance composites

- **Metric name:** Retention of terminated/degraded constituents in the reported record
- **Concrete threshold:** Verbatim (GIPS 3.A.9): "**Terminated portfolios must be included in the historical performance of the composite up to the last full measurement period that each portfolio was under management and for which the firm has discretion.**" And (3.A.6): "**Any change to a composite definition must not be applied retroactively.**" And (3.A.7): "Composites must include new portfolios on a timely and consistent composite-specific basis after each portfolio comes under management." And (3.A.5): "Composites must include all portfolios … that meet the composite definition. **The firm must not exclude portfolios from composites based solely on legal structure differences.**"
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *GIPS for Firms*, 2020 — provisions 3.A.5, 3.A.6, 3.A.7, 3.A.9
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **Cross-reference:** full treatment in the companion document §7.1. **The delta here is the on-chain consequence:** a wallet pool that drops degraded wallets from its *history* (not just from its forward cohort) reproduces exactly the survivorship bias GIPS forbids. A "top memecoin wallets of 2026" list, presented without the wallets that were in the pool and decayed, is a survivorship-selected sample and **cannot** support a claim about skill.
- **Honest note, carried forward:** the phrase "survivorship bias" appears **zero times** in GIPS 2020; GIPS addresses it structurally through 3.A.2/3.A.5/3.A.9.

### 7.2 — Measured magnitude of the survivorship bias

- **Metric name:** Size of the survivorship bias in a performance database
- **Concrete threshold:** "**The resulting survivorship bias is substantial, averaging more than 5 percent a year.**" And: "60 percent of the funds added to the TASS database between April 1999 and November 2001 are likely to be survivors (i.e., funds that were selected only from funds that were live as of 31 March 1999)."
- **Source organisation:** Rajesh K. Aggarwal and Philippe Jorion — *Financial Analysts Journal* 66(2), March/April 2010 (published by CFA Institute)
- **Document / page title:** "Hidden Survivorship in Hedge Fund Returns"
- **URL:** https://rpc.cfainstitute.org/research/financial-analysts-journal/2010/hidden-survivorship-in-hedge-fund-returns
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (abstract + publisher metadata; full text is behind CFA Institute's member paywall — **only the abstract is verified**)
- **The finding that matters here:** what is normally called *backfill* is in fact *hidden survivorship* — i.e. a fund is included in a database only because it was still alive, and the database then presents its (favourable) early history as if it were contemporaneous.

### 7.3 — Backfill bias: the published remedy

- **Metric name:** Backfill-bias treatment
- **Concrete threshold:** Verbatim: "The most common treatments include either retaining all backfilled returns or truncating a fixed number of returns from each return series. However, we show that **truncation largely preserves backfilled returns** and document that either of these backfill treatments can lead to biased empirical findings, including cross-sectional results. Thus, our findings show that **the best practice for empirical tests is to remove returns prior to the listing date.** Because most databases do not have listing dates, we propose a novel method to infer unavailable listing dates."
- **Source organisation:** Philippe Jorion (UC Irvine) and Christopher Schwarz (UC Irvine) — *The Review of Financial Studies* 32(12), 2019, 5048–5099
- **Document / page title:** "The Fix Is In: Properly Backing out Backfill Bias"
- **URL:** https://ideas.repec.org/a/oup/rfinst/v32y2019i12p5048-5099..html (RePEc record with the publisher abstract; the publisher's full text is subscriber-restricted and the SSRN copy at https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3010469 is **403 from this host**)
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (abstract only — full text paywalled)
- **On-chain application:** a wallet's on-chain history *begins* at its listing. Any performance record assembled from a vendor that backfills (i.e. shows history for a wallet before its first observed activity, or carries forward a label across a dormant period) is carrying backfill bias. **The rule for a wallet is: compute performance only from observed on-chain activity, and exclude any period before the wallet's first observed transaction.** This is the published "remove returns prior to the listing date" rule, transplanted to a listing date that is knowable rather than inferred.

### 7.4 — Cross-chain: the chains do not share a coverage window

- **Metric name:** Cross-chain comparability of a consistency claim
- **Concrete threshold:** See the §6.2 table — earliest indexed data differs by **up to 11 years** across chains (Ethereum 30 Jul 2015 → Arc 15 Jul 2026). Nansen's Smart Money endpoints additionally do **not** cover the same chain set: "Netflow, DEX Trades, and Holdings support these chains: Arbitrum, Arc, Avalanche, Base, BNB Chain, Ethereum, HyperEVM, IOTA EVM, Linea, Mantle, Monad, Optimism, Plasma, Polygon, **Robinhood**, Sei, **Solana**, Sonic."
- **Source organisation:** Nansen
- **Document / page title:** "Smart Money" (Nansen API docs, "Supported Chains" section) · "Data Coverage by Chain"
- **URLs:** https://docs.nansen.ai/api/smart-money · https://docs.nansen.ai/api/data-coverage.md
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes (both)
- **Consequence:** a consistency standard that is *chain-agnostic in the metric* but *chain-specific in attainability* must report the per-chain maximum achievable history alongside the verdict, or the same wallet on two chains produces incomparable verdicts for reasons that have nothing to do with the trader.

### 7.5 — The published anti-selection-bias discipline that applies to choosing a universe

- **Metric name:** Universe-selection disclosure obligation
- **Concrete threshold:** Binary. FINRA Rule 2214 requires an investment analysis tool to explain "how selection works, and discloses selectivity"; the SEC requires that any extracted performance be accompanied by the total portfolio's results (§1.6 above). **There is no published standard that says "you cannot infer skill from a survivorship-selected list of holders" in those words** — but the *structural* requirements above (GIPS 3.A.5/3.A.9; SEC (d)(5); FINRA 2214's selectivity disclosure) are the published provisions that make a survivorship-selected wallet list non-substantiable.
- **Source organisation:** FINRA (rulebook) and SEC (Marketing Rule) — cross-referenced from the companion document §1.5 and §1.11
- **Document / page title:** FINRA Rule 2214 — Requirements for the Use of Investment Analysis Tools; 17 CFR 275.206(4)-1(d)(5)
- **URLs:** https://www.finra.org/rules-guidance/rulebooks/finra-rules/2214 · https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (per the companion document's §11 provenance; the FINRA URL is **403 to direct clients from this host** and was retrieved there via the `r.jina.ai` reader proxy — this document does not re-fetch it and inherits that provenance)

---

## 8. CRYPTO-NATIVE — what the on-chain vendors actually publish

**This section does not duplicate the companion document §5.** It answers a narrower and harder question: *do any of these vendors publish a notion of a **consistently** profitable wallet — as opposed to a wallet with a high total PnL?*

### 8.1 — Nansen: the fields exist, the thresholds do not

- **Metric name:** Nansen Smart Money PnL Leaderboard — per-wallet fields returned
- **Concrete threshold:** The published API schema (fetched from the live OpenAPI document embedded in the page) defines, per wallet: `realized_pnl_usd`, `unrealized_pnl_usd`, `total_pnl_usd`, `avg_trade_roi` ("Average trade ROI as a fraction"), `roi_percent_unrealised`, `win_rate` ("Win rate as a fraction (0-1)"), `n_trades` ("Number of trades"), `n_tokens` ("Number of tokens traded"), `open_trades`, `held_tokens_count`, `top_traded_tokens_info`. The `timeframe` parameter allows **1, 7, 30, 90, 180** days (default 7). The sortable fields include `win_rate` and `n_trades`.
- **Source organisation:** Nansen
- **Document / page title:** "PnL Leaderboard" (Nansen API docs, including the full OpenAPI schema)
- **URL:** https://docs.nansen.ai/api/smart-money/pnl-leaderboard.md
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes (markdown, fetched 200)
- **The decisive negative finding, re-verified for this document:** Nansen publishes the *fields* `win_rate`, `n_trades` and `avg_trade_roi` per wallet and lets the caller **sort** by them, but publishes **no threshold** that constitutes "consistently profitable". The label itself is a black box: "Smart Trader | **Historically profitable traders**; covers all 30D, 90D and 180D Smart Traders" — with no published selection rule. Therefore: **any claim that a Nansen Smart Money wallet is a "consistently profitable trader" is an inference, not a Nansen statement.** The vendor supplies the ingredients (win_rate, n_trades, avg_trade_roi) and the caller must supply the bar.
- **GMGN's own warning about the same cohort, verbatim:** "GMGN has big data on smart money… Especially with the release of the new meme coin, there is a concentrated entry of smart money. The necessary action to check the contract is not less, because **a lot of smart money also has a disorderly situation.**" (https://docs.gmgn.ai/index/track-smart-money, fetched 200.)

### 8.2 — GMGN: the only vendor found that publishes numeric thresholds — in its own tooling guide

- **Metric name:** GMGN's published wallet-quality thresholds
- **Concrete threshold (verbatim from GMGN's own published workflow documentation):**
  - "`winrate` | % of profitable trades (0–1) | **> 0.6 strong, > 0.5 acceptable**"
  - "`pnl` | realized_profit / total_cost multiplier | **> 1.0 = net positive**"
  - "`token_num` | number of distinct tokens traded | high = diversified"
  - A published **composite score** for ranking smart money wallets: "**winrate × 40% · pnl × 40% · token_num (diversity) × 10% · Recency (7d winrate vs 30d winrate improvement) × 10%**"
  - And a published **trade-count window** for the copy-trade estimate: "For the wallet's **last 20–30 completed trades** (round-trip buys + sells)".
- **Source organisation:** GMGN (commercial on-chain analytics platform) — published in GMGN's own `gmgn-skills` documentation repository
- **Document / page title:** "Smart Money Profile — Behavior Analysis Workflow" (GMGN Skills, `docs/workflow-smart-money-profile.md`) and "Wallet Analysis — Full Workflow" (`docs/workflow-wallet-analysis.md`)
- **URLs:** https://raw.githubusercontent.com/GMGNAI/gmgn-skills/HEAD/docs/workflow-smart-money-profile.md · https://raw.githubusercontent.com/GMGNAI/gmgn-skills/HEAD/docs/workflow-wallet-analysis.md (human-readable: https://github.com/GMGNAI/gmgn-skills/blob/main/docs/workflow-smart-money-profile.md)
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION** — plainly and explicitly: these are GMGN's own product-documentation thresholds, not a regulator's, exchange's, professional body's or academic standard.
- **Fetched:** Yes (both, fetched 200)
- **Why this is the single most useful crypto-native row:** it is a **vendor-published, numeric, multi-metric notion of wallet quality that includes both a win-rate band AND a consistency signal (7d winrate vs 30d winrate trend) AND a token-diversity term AND an explicit trade-count window.** It is directly translatable into the criteria JSON, and it is honestly labelled as a vendor convention.
- **Second GMGN threshold (wallet-analysis workflow), verbatim:** "`winrate` — ratio of profitable trades (0–1); **> 0.6 is strong**" and "`pnl` — profit/loss ratio = `realized_profit / total_cost`; **`2.0` = doubled money**".

### 8.3 — Birdeye and Arkham: semantics only / confidence bands

- **Metric name:** Birdeye Smart Money API — cohort definition; Arkham label confidence bands
- **Concrete threshold:**
  - Birdeye, verbatim: "Endpoints that track **high-performing wallets** and their activity so you can follow smart money flows." And: "The Smart Money group focuses on tokens being accumulated, traded, or surfaced by **stronger-performing wallets**." **No numeric threshold, no win-rate band, no trade-count minimum** — the API exposes endpoint semantics only.
  - Arkham, verbatim: "Verified labels **≥98%** … Prediction labels **≥80%** … Prediction labels are explicitly marked as lower-confidence." (These are *attribution-confidence* bands, not performance bands.)
- **Source organisation:** Birdeye (data provider); Arkham (blockchain intelligence)
- **Document / page titles:** "Smart Money API" (Birdeye Data docs) · "How Arkham Labels Wallets" (Arkham API guides)
- **URLs:** https://data.birdeye.so/docs/data-api/smart-money/index · https://arkm.com/llms/guides/how-arkham-labels-wallets.md
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes (both)
- **Honest negative finding:** Birdeye publishes **no** definition of "consistently profitable". Arkham publishes **confidence in attribution**, not skill in trading. Neither helps with the consistency question.

### 8.4 — CryptoQuant and Dune: re-verified as publishing nothing on this question

- **Metric name:** CryptoQuant / Dune "smart money" / consistency definitions
- **Concrete threshold:** **None published.**
- **Source organisation:** CryptoQuant; Dune
- **URLs examined:** https://docs.cryptoquant.com/llms.txt (45,957 chars, retrieved in full) · https://docs.dune.com/llms.txt (35,405 chars, retrieved in full)
- **Verification performed:** a case-insensitive search of both retrieved indexes for "smart money", "smart_money", "sniper", "insider", "win rate", "win_rate", "profit factor", "profitable", "skilled", "consistency" returned **zero** matches in the CryptoQuant index. The Dune index returned matches only for "Decode Smart Contracts" / "decoded data tables" (the phrase "smart contracts"), which are unrelated to smart-money trading.
- **Classification tag:** **NOT-AUTHORITATIVE / NOT LOCATED — EXCLUDED**
- **Fetched:** Yes — this is a **re-verification** for this document, independent of the companion document §5.8, and it confirms the same negative result.
- **Explicitly: no CryptoQuant or Dune definition of a consistently profitable wallet is asserted anywhere in this document.**

### 8.5 — The published "smart money win rate" that does exist in the research literature

- **Metric name:** Realised win rate / persistence of on-chain "smart money" cohorts in published research
- **Concrete threshold:** **None published in a form that can be cited as a threshold.** The Nansen API *exposes* `win_rate` and `n_trades` (§8.1) and GMGN *publishes* bands on them (§8.2), but no peer-reviewed paper establishing a "smart money" win-rate standard was located.
- **Classification tag:** **NOT STANDARDISED** — recorded as a negative finding so that it is not silently assumed to exist.
- **Note:** Nansen's own cohort definition is the only published *definition* of "historically profitable traders" in the crypto-native space, and it is explicitly label-based, not threshold-based: "Smart Trader | Historically profitable traders".

---

## 9. What this document establishes that the companion document does not

| # | Question | Answer | Where |
|---|---|---|---|
| 1 | Is the best-of-many-wallet selection bias accounted for? | **Yes** — DSR with N = number of wallets screened; PBO via CSCV; Bonferroni/BH corrections; HLZ t > 3.0 | §1 |
| 2 | How many *independent* bets are needed? | NIST formula on the **non-overlapping** trade count; Lo's 65%-overstatement finding; Grinold's "count only independent bets as breadth" | §2 |
| 3 | What is the probability the win rate beats chance? | Beta–Binomial with Beta(1,1) prior → P(θ > 0.5) | §3 |
| 4 | Is the return stream consistent? | Consistency ratio (positive periods ÷ total periods); GIPS's 36-observation floor; CFA's appraisal-ratio statement | §4 |
| 5 | Is the return stream drawdown-adjusted? | Sortino (CFA), Calmar (peer-reviewed), MDD + drawdown duration (CFA, no bands) | §5 |
| 6 | Is the track record long enough? | GIPS 5y→10y; SEC 1/5/10y; **chain-coverage ceiling** (Base ~3.4y max as of 2026-11-03) | §6 |
| 7 | Is the universe survivorship-selected? | GIPS 3.A.5/3.A.6/3.A.7/3.A.9; Aggarwal–Jorion (>5%/yr); Jorion–Schwarz (remove pre-listing returns) | §7 |
| 8 | Do crypto vendors define "consistently profitable"? | **Only GMGN publishes numeric bands** (winrate > 0.6 strong / > 0.5 acceptable; pnl > 1.0; 40/40/10/10 composite; 20–30-trade window). Nansen exposes fields but no thresholds. Birdeye/Arkham publish nothing applicable. CryptoQuant/Dune publish nothing. | §8 |

---

## 10. Provenance — what was fetched, what was inferred, what was not done

### 10.1 — Fetched and quoted verbatim from the retrieved body (2026-11-03)

Bailey & López de Prado, "The Deflated Sharpe Ratio" PDF (22 pp; Eq. (1) and Eq. (2) read from 170–330 DPI page renders because the math is vector-graphic) · Bailey, Borwein, López de Prado & Zhu, "The Probability of Backtest Overfitting" PDF (34 pp) · Bailey, Borwein, López de Prado & Zhu, "Pseudo-Mathematics and Financial Charlatanism" PDF (34 pp) · Benjamini & Hochberg (1995) JRSS-B verbatim reprint PDF (13 pp, from math.tau.ac.il) · Harvey, Liu & Zhu, "…and the Cross-Section of Expected Returns" PDF (64 pp, author's Duke copy) · Harvey & Liu, "Backtesting" PDF (17 pp, author's Duke copy) · NIST e-Handbook §7.4.7.3 (Bonferroni), §7.4.7 (multiple comparisons), §7.2.4.2 (sample size), §7.2.4.1 (Wilson), §7.2.4 (validity floors) — all five verified 200 · CFA Institute "The Sharpe Ratio and the Information Ratio" PDF (4 pp) · CFA Institute "The Sortino Ratio" PDF (3 pp) · *GIPS for Firms* 2020 PDF (146 pp) · CFA Institute Refresher Reading "Portfolio Performance Evaluation" (2026) · CFA Institute Refresher Reading "Analysis of Active Portfolio Management" (2026) · CFA Institute RPC "The Statistics of Sharpe Ratios" (FAJ 2002) landing page + abstract · CFA Institute RPC "Hidden Survivorship in Hedge Fund Returns" (FAJ 2010) landing page + abstract · CFA Institute RPC "Performance Drawdowns in Asset Management" (CFA Institute Journal Review 2018) · CFA Institute RPC "Maximum Drawdown as Predictor of Mutual Fund Performance and Flows" (FAJ 2022) landing page + abstract · CFA Institute, *Bayes Rules!* Ch. 3 (Beta-Binomial) HTML · Avellaneda, Lee & Ou, "The Fundamental Law of Active Management" PDF (33 pp) · Wang, Kresta & Tichý, "Evaluation of strategy portfolios" (*Computational Management Science*, Springer, open access) · Molyboga & L'Ahelec, "A simulation-based methodology for evaluating hedge fund investments" (*Journal of Asset Management*, Springer, open access) · Jorion & Schwarz, "The Fix Is In" (RePEc record + abstract) · Marietta Board of Pensions / Principal, "Investment Option Performance Results and Statistics" PDF (28 pp) · Nansen API docs: Smart Money, PnL Leaderboard (incl. full OpenAPI schema), Data Coverage (markdown) · GMGN Tutorial "Track Smart Money" · GMGN Skills: "Smart Money Profile" and "Wallet Analysis" workflows (raw markdown) · Birdeye "Smart Money API" index · Arkham "How Arkham Labels Wallets" · CryptoQuant `llms.txt` (45,957 chars, full) · Dune `llms.txt` (35,405 chars, full) · Lopez de Prado, *Advances in Financial Machine Learning* SSRN reprint PDF (61 pp) · 17 CFR 275.206(4)-1 on eCFR · PubMed record 6827763 (Hanley & Lippman-Hand) · Wikipedia "Calmar ratio" (fetched; **secondary, used only for the 36-month attribution, which is flagged UNVERIFIED**).

### 10.2 — Fetched but NOT fully verifiable from the retrieved body (flagged in place)

- **Calmar's original 36-month window.** The archive.org full-text copy of *Investment Analysis and Portfolio Management* located for this research contains **zero** occurrences of "Calmar", "drawdown" or "Terry W. Young" — the originating chapter could not be verified. The 36-month version is sourced from Wikipedia's quotation of Young (1991) and is marked **UNVERIFIED against the primary source**. The peer-reviewed formula `E(R_p − R_f)/MAXDD(T)` (Springer, open access) carries no fixed window and is what the JSON specifies.
- **Affagharwal & Jorion (FAJ 2010)** and **Lo (2002)** — publisher landing pages and abstracts fetched; full texts are behind CFA Institute's member paywall. Only the abstracts' wording is quoted.
- **Jorion & Schwarz (RFS 2019)** — RePEc abstract fetched; publisher full text subscriber-restricted and the SSRN copy 403s from this host.
- **López de Prado, *AFML*** — the SSRN reprint PDF fetched is the front matter + table of contents + chapter 1 body. The §4.2 / §4.4 / §7.4 **section titles and page numbers** are verified from the retrieved body; the **chapter 4 and 7 body text is not in the retrieved PDF** and is therefore quoted only by title, never by passage.
- **GMGN's `gmgn-skills` repository** is GMGN's own published tooling documentation, not GMGN's product UI documentation; it is cited as GMGN-published vendor material, with that distinction noted.
- **SSRN abstract pages** (2460551, 2326253, 2342389, 3010469, 2547415, 2548397) all return **HTTP 403** to this host. Where a paper's SSRN number matters it is given as the paper's own printed identifier (the DSR PDF's first page literally prints "Electronic copy available at: http://ssrn.com/abstract=2460551"), and the *working* URL given is the author's or a mirror that was actually fetched.
- **JSTOR** (BH 1995 at stable/2346101, Lo 2002 at stable/4480405) returns HTTP 200 but serves a **JavaScript "Client Challenge" bot-wall** (3,036 bytes) instead of the article; and **doi.org** for BH 1995 returns **HTTP 403** to this host. The BH 1995 working URL is the verbatim reprint PDF that *was* fetched. The `https://www.jstor.org/stable/2346101` and `https://doi.org/10.1111/j.2517-6161.1995.tb02031.x` links are given as the canonical publisher records, and are marked as bot-walled here rather than as working fetch targets.
- **GitHub** returned **HTTP 429** (rate limit) only when many URLs were requested in parallel; requested individually, `https://github.com/GMGNAI/gmgn-skills/blob/main/docs/workflow-smart-money-profile.md` returns 200.

### 10.3 — Inferred rather than fetched (each flagged in place)

- **All numeric tables in §1.3 (E[max SR] by N), §2.3 (minimum independent bets by claimed win rate), §3.1 (posterior P(θ > 0.5) by wins and n), and §1.1's DSR cross-check** are **this document's arithmetic** from the published formulas (NIST §7.2.4.2; Bailey–López de Prado Eqs. (1) and (2); the Beta-Binomial posterior of §3.1). The sources do not publish these particular tables. The DSR arithmetic was validated against the source's own worked example (§1.1: reproducing the paper's stated DSR = 0.9505 at N = 46 with skew = −3 and kurtosis = 10, and 0.95 at N = 88 for Normal returns, requires interpreting Eq. (2) on the **per-period** return series with SR and SR₀ on the same per-period scale and SR₀ scaled by 1/√(per-periods-per-year) from the annualised variance V — this document's reconstruction, and it reproduces the paper's printed values to 4 decimal places).
- **§2.2's "greedy non-overlapping trades" definition of independent bets** is an **ANALYST ADAPTATION** built on the published concepts (Lo on serial correlation; AFML on overlapping outcomes and average uniqueness; Grinold on counting only independent bets as breadth). No source publishes this exact procedure for wallets.
- **§3.3's split-half posterior comparison** and **§5.1–5.3's mapping of GIPS's 36-monthly-return rule to 36 daily on-chain observations** are ANALYST ADAPTATIONS, cited to their underlying sources and labelled as such.
- **The decision thresholds that are not published** — DSR ≥ 0.95, PBO ≤ 0.05 (this one **is** published, §1.2), P(θ > 0.5) ≥ 0.95, consistency-ratio bands, Sortino/Calmar bands — are marked **ANALYST_CHOICE** in the JSON except where a source publishes them.

### 10.4 — Explicitly NOT done

- **No URL in this document was constructed from memory.** Every URL was requested from this host on 2026-11-03 and returned 200, or is returned as a **403/404 that is disclosed alongside the working substitute**. A URL that failed is never presented as working.
- **No formula was paraphrased and presented as an author's.** Where the source prints an equation, the equation is transcribed from the printed form (or, for the two Bailey–López de Prado papers, read from a high-DPI render of the printed equation). Where this document adapts a formula, it is marked **[ANALYST ADAPTATION]**.
- **No source is cited for a threshold it does not publish.** Where an authority publishes no threshold — CFA Institute on Sortino/Calmar/MDD bands, NIST on a constant trade count, GIPS on a consistency ratio, Nansen on wallet selection criteria, Birdeye/Arkham/CryptoQuant/Dune on anything — that absence is recorded as a negative finding rather than filled with a plausible number.
- **The companion document's findings were not re-derived or re-litigated.** Where this document cites NIST §7.2.4.2, §7.2.4.1, the rule of three, the Sharpe definition, GIPS 1.A.3/4.A.1/6.A.1/8.C.1, SEC 206(4)-1(d)(2), FINRA 2214, and the Nansen/GMGN/Arkham label definitions, it does so by reference and adds only the delta, to avoid two documents making two slightly different claims about the same source.
