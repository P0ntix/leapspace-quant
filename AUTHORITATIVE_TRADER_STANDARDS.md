# Authoritative Trader Standards — On-Chain "Successful Trader" Criteria

**Compiled:** 2026-11-03
**Scope:** What the industry actually publishes as the evidence required before anyone may state that a wallet (or a trader) is profitable, and what evidence is *not* standardised at all.

**How to read this file.** Every criterion below carries seven fields:
(a) metric name · (b) concrete threshold · (c) source organisation · (d) document/page title · (e) working URL · (f) verbatim quote or exact section/rule number · (g) classification tag.

Tags: **REGULATORY** · **EXCHANGE-OR-FIRM-STANDARD** · **ANALYTICS-VENDOR-CONVENTION** · **ACADEMIC-OR-PROFESSIONAL-GUILD**

**Verification status is stated per source.** Every URL below was fetched from this host on 2026-11-03 and the quoted text was located in the fetched body. Where a source could not be fetched, it is excluded and the gap is named explicitly in §12.

---

## 1. REGULATORY — Performance advertising and hypothetical performance

The Marketing Rule is the only binding US rule that dictates *what evidence* must exist before a firm may claim performance results. It is a **disclosure-and-substantiation** regime: it never sets a performance *threshold*. It sets the *evidentiary floor*.

### 1.1 — Substantiation floor: every material performance claim must be supportable on demand

- **Metric name:** Substantiation requirement for material statements of fact in performance advertising
- **Concrete threshold:** Zero tolerance — no material statement of fact may be made unless the adviser has a reasonable basis for believing it can substantiate it upon Commission demand. There is no numerical threshold; the obligation is binary.
- **Source organisation:** U.S. Securities and Exchange Commission (SEC)
- **Document / page title:** 17 CFR 275.206(4)-1 — Investment adviser marketing (paragraph (a)(2))
- **URL:** https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1
- **Verbatim quote:** "(2) Include a material statement of fact that the adviser does not have a reasonable basis for believing it will be able to substantiate upon demand by the Commission;"
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (eCFR live text, current as of the 2026-10-29 eCFR issue)

### 1.2 — Net performance must accompany gross performance, with equal prominence

- **Metric name:** Gross-vs-net presentation parity
- **Concrete threshold:** Net performance must be presented with "at least equal prominence" to gross, over "the same time period," and "using the same type of return and methodology"
- **Source organisation:** U.S. Securities and Exchange Commission (SEC)
- **Document / page title:** 17 CFR 275.206(4)-1, paragraph (d)(1)
- **URL:** https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1
- **Verbatim quote:** "(1) Any presentation of gross performance, unless the advertisement also presents net performance: (i) With at least equal prominence to, and in a format designed to facilitate comparison with, the gross performance; and (ii) Calculated over the same time period, and using the same type of return and methodology, as the gross performance."
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes
- **On-chain implication:** A wallet PnL figure quoted gross of gas, priority fees, MEV and slippage is, by this rule's logic, an incomplete presentation. A copy-trade simulator must quote net-of-cost to be publishable.

### 1.3 — Minimum performance periods: one-, five- and ten-year

- **Metric name:** Required performance reporting periods
- **Concrete threshold:** 1-year, 5-year **and** 10-year periods, each with equal prominence, ending no less recently than the most recent calendar year-end; if the portfolio did not exist for a prescribed period, the life of the portfolio is substituted
- **Source organisation:** U.S. Securities and Exchange Commission (SEC)
- **Document / page title:** 17 CFR 275.206(4)-1, paragraph (d)(2)
- **URL:** https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1
- **Verbatim quote:** "(2) Any performance results, of any portfolio or any composite aggregation of related portfolios, in each case other than any private fund, unless the advertisement includes performance results of the same portfolio or composite aggregation for one-, five-, and ten-year periods, each presented with equal prominence and ending on a date that is no less recent than the most recent calendar year-end; except that if the relevant portfolio did not exist for a particular prescribed period, then the life of the portfolio must be substituted for that period."
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes
- **Note:** This is the single most directly relevant rule to the local package: a wallet with 30 trades cannot have a compliant 10-year track record, so the life-of-wallet substitution is the only route. **A wallet PnL claim made to the public is only publishable under a life-substitution if the wallet's entire history is shown.**

### 1.4 — Hypothetical performance: policies, criteria, assumptions, risks

- **Metric name:** Hypothetical performance admissibility conditions
- **Concrete threshold:** Three cumulative conditions — (i) adopted and implemented policies and procedures reasonably designed to ensure the hypothetical performance is relevant to the likely financial situation and objectives of the intended audience; (ii) sufficient information for the audience to understand the criteria used and assumptions made; (iii) sufficient information to understand the risks and limitations
- **Source organisation:** U.S. Securities and Exchange Commission (SEC)
- **Document / page title:** 17 CFR 275.206(4)-1, paragraph (d)(6)
- **URL:** https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1
- **Verbatim quote:** "(6) Any hypothetical performance unless the investment adviser: (i) Adopts and implements policies and procedures reasonably designed to ensure that the hypothetical performance is relevant to the likely financial situation and investment objectives of the intended audience of the advertisement; (ii) Provides sufficient information to enable the intended audience to understand the criteria used and assumptions made in calculating such hypothetical performance; and (iii) Provides (or, if the intended audience is an investor in a private fund, provides, or offers to provide promptly) sufficient information to enable the intended audience to understand the risks and limitations of using such hypothetical performance in making investment decisions"
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes
- **On-chain implication:** **The local package's copy-trade simulator produces hypothetical performance.** Under (d)(6) it may only be published with (i) documented policies, (ii) disclosed criteria and assumptions (the friction model, the thresholds, the chain set), and (iii) disclosed risks and limitations (survivorship bias, empty registries, synthetic rug events). This is the strongest argument for this document existing at all.

### 1.5 — Extracted, related and predecessor performance

- **Metric name:** Related / extracted / predecessor performance conditions
- **Concrete threshold:** Related performance must include all related portfolios unless exclusion is immaterial; extracted performance requires the total portfolio's results to be provided or offered promptly; predecessor performance requires the prior personnel to manage accounts at the advertising adviser and the accounts to be "sufficiently similar"
- **Source organisation:** U.S. Securities and Exchange Commission (SEC)
- **Document / page title:** 17 CFR 275.206(4)-1, paragraphs (d)(4), (d)(5), (d)(7)
- **URL:** https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1
- **Verbatim quote:** "(5) Any extracted performance, unless the advertisement provides, or offers to provide promptly, the performance results of the total portfolio from which the performance was extracted."
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes
- **On-chain implication:** Selecting the 30 best-performing wallets out of a screened universe and publishing their aggregate win rate is "extracted performance" unless the full screened universe's results are also published.

### 1.6 — Books and records: the calculation basis must exist

- **Metric name:** Performance substantiation records (Rule 204-2(a)(16))
- **Concrete threshold:** The adviser must retain "all accounts, books, internal working papers, and any other records or documents that are necessary to form the basis for or demonstrate the calculation of any performance or rate of return." For managed accounts, account statements plus "all worksheets necessary to demonstrate the calculation" suffice.
- **Source organisation:** U.S. Securities and Exchange Commission (SEC)
- **Document / page title:** 17 CFR 275.204-2 — Investment advisers' books and records to be maintained, paragraph (a)(16)
- **URL:** https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.204-2
- **Verbatim quote:** "All accounts, books, internal working papers, and any other records or documents that are necessary to form the basis for or demonstrate the calculation of any performance or rate of return of any or all managed accounts, portfolios (as defined in § 275.206(4)-1(e)(11) of this chapter), or securities recommendations presented in any notice, circular, advertisement (as defined in § 275.206(4)-1(e)(1) of this chapter) …"
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (via the eCFR Title 17 Part 275 XML, title-17 part 275 current as of 2026-10-29)
- **On-chain implication:** The local package's per-trade ledger is the "worksheet." A wallet profile with a win rate but no per-trade export is not substantiable.

### 1.7 — Marketing Rule adopting release and 2022 compliance date

- **Metric name:** Effective / compliance dates of the merged marketing rule
- **Concrete threshold:** Effective 4 May 2021; compliance date **4 November 2022** (18 months). Rule 206(4)-1 replaces former Rules 206(4)-1 and 206(4)-3.
- **Source organisation:** U.S. Securities and Exchange Commission (SEC) — Division of Examinations
- **Document / page title:** "Examinations Focused on the New Investment Adviser Marketing Rule" (Risk Alert, 19 September 2022); adopting release "Investment Adviser Marketing", 86 FR 13024 (5 March 2021), Release No. IA-5653
- **URLs:** https://www.sec.gov/files/exams-risk-alert-marketing-rule-2022.pdf · https://www.federalregister.gov/documents/2021/03/05/2020-28868/investment-adviser-marketing
- **Verbatim quote:** "The compliance date for the Marketing Rule is November 4, 2022 (Compliance Date). As of the Compliance Date, investment advisers may no longer choose to comply with the previous advertising and cash solicitation rules."
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (SEC PDF fetched; FR document fetched via the Federal Register API — effective date 2021-05-04, citation 86 FR 13024)

### 1.8 — The 2022 amendments to 206(4)-1 (and their limits)

- **Metric name:** Scope of the 15 April 2022 amendment to Rule 206(4)-1
- **Concrete threshold:** The 2022 final rule amending 206(4)-1 is **technical only**: it changes the punctuation of paragraph (b)(2)(i) — "removing `,' and adding in its place `;'". It does not change any performance, disclosure or substantiation requirement.
- **Source organisation:** U.S. Securities and Exchange Commission (SEC)
- **Document / page title:** "Technical Amendments to Commission Rules and Forms", Release No. 33-11047; IA-5985; IC-34547, 87 FR 22444 (15 April 2022), effective 15 April 2022
- **URL:** https://www.federalregister.gov/documents/2022/04/15/2022-06972/technical-amendments-to-commission-rules-and-forms
- **Verbatim quote:** "Sec. 275.206(4)-1 [Amended] … 21. In Sec. 275.206(4)-1 amend paragraph (b)(2)(i) by removing `,' and adding in its place `;'."
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (Federal Register full text)
- **Honest correction to a common assumption:** There is **no** 2022 amendment to the Marketing Rule's performance requirements. The eCFR source note for 206(4)-1 reads "[86 FR 13024, Mar. 5, 2021, as amended at 87 FR 22447, Apr. 15, 2022]" — but 87 FR 22447 is the **Interior Department / National Park Service** archaeological-collections rule, and the substantive SEC amendment is the technical amendment above (87 FR 22444, pages 22444–22447). The only SEC rulemaking touching performance disclosure in 2022 is the *proposed* "Investment Adviser Performance-Based Compensation Modernization" (91 FR 63676, 6 October 2026) — a **proposal**, not a standard, and therefore excluded from the criteria below.

### 1.9 — FINRA Rule 2210(d)(1)(F): no projecting performance

- **Metric name:** Broker-dealer communications content standard — performance projection prohibition
- **Concrete threshold:** Absolute prohibition on communications that "predict or project performance, imply that past performance will recur or make any exaggerated or unwarranted claim, opinion or forecast," with three narrow carve-outs (hypothetical illustration of mathematical principles that does not predict an investment's performance; a compliant Rule 2214 investment analysis tool; a research-report price target with reasonable basis)
- **Source organisation:** Financial Industry Regulatory Authority (FINRA)
- **Document / page title:** FINRA Rule 2210 — Communications with the Public, paragraph (d)(1)(F)
- **URL:** https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210
- **Verbatim quote:** "(F) Communications may not predict or project performance, imply that past performance will recur or make any exaggerated or unwarranted claim, opinion or forecast; provided, however, that this paragraph (d)(1)(F) does not prohibit: (i) A hypothetical illustration of mathematical principles, provided that it does not predict or project the performance of an investment or investment strategy; (ii) An investment analysis tool, or a written report produced by an investment analysis tool, that meets the requirements of Rule 2214; and (iii) A price target contained in a research report on debt or equity securities…"
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes — via the `r.jina.ai` reader proxy. **Direct requests to finra.org return HTTP 403 (Cloudflare) from this host**; the proxy retrieved the page whose "URL Source" line confirms the canonical finra.org address. Treat the finra.org URL as live for a normal browser but as proxy-fetched here.

### 1.10 — FINRA Rule 2210(d)(1)(A)–(B): fair dealing and no misleading statements

- **Metric name:** Fair-and-balanced / no-untrue-statement standards
- **Concrete threshold:** All member communications must be based on fair dealing and good faith, must be fair and balanced, and must not contain an untrue statement of a material fact
- **Source organisation:** Financial Industry Regulatory Authority (FINRA)
- **Document / page title:** FINRA Rule 2210, paragraph (d)(1)(A)–(B)
- **URL:** https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210
- **Verbatim quote:** "(A) All member communications must be based on principles of fair dealing and good faith, must be fair and balanced, and must provide a sound basis for evaluating the facts in regard to any particular security or type of security, industry, or service. … (B) No member may make any false, exaggerated, unwarranted, promissory or misleading statement or claim in any communication."
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (proxy, as in 1.9)

### 1.11 — FINRA Rule 2214: the narrow exception for backtest-style tools

- **Metric name:** Investment analysis tool — disclosure conditions
- **Concrete threshold:** A tool may be provided only if it (1) describes criteria, methodology, limitations and key assumptions; (2) explains that results vary with each use and over time; (3) if applicable, describes the universe of investments considered, how selection works, and discloses selectivity; and (4) displays the mandatory hypothetical-performance legend
- **Source organisation:** Financial Industry Regulatory Authority (FINRA)
- **Document / page title:** FINRA Rule 2214 — Requirements for the Use of Investment Analysis Tools
- **URL:** https://www.finra.org/rules-guidance/rulebooks/finra-rules/2214
- **Verbatim quote:** "(4) displays the following additional disclosure: \"IMPORTANT: The projections or other information generated by [name of investment analysis tool] regarding the likelihood of various investment outcomes are hypothetical in nature, do not reflect actual investment results and are not guarantees of future results.\""
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (proxy)
- **On-chain implication:** This is the closest regulatory analogue to the local package's copy-trade simulator, and it names the exact three things the simulator must disclose: methodology + assumptions, universe + selection criteria, and the hypothetical-performance legend.

### 1.12 — SEC examination focus: what examiners actually check on performance claims

- **Metric name:** Examination review areas (performance advertising)
- **Concrete threshold:** No numeric threshold. The staff reviews: (i) written policies and procedures with "objective and testable means"; (ii) substantiation — where the adviser cannot substantiate, "we will presume that the adviser did not have a reasonable basis for its belief"; (iii) the performance prohibitions (gross without net, no specified time periods, no claim of Commission approval, no subset extraction, hypothetical performance, predecessor performance); (iv) books and records
- **Source organisation:** U.S. Securities and Exchange Commission (SEC), Division of Examinations
- **Document / page title:** "Examinations Focused on the New Investment Adviser Marketing Rule" (Risk Alert, 19 September 2022)
- **URL:** https://www.sec.gov/files/exams-risk-alert-marketing-rule-2022.pdf
- **Verbatim quote:** "if an adviser is unable to substantiate the material claims of fact made in an advertisement when the Commission demands it, we will presume that the adviser did not have a reasonable basis for its belief."
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (SEC PDF)
- **Note:** A Risk Alert is staff guidance, not a rule — it has "no legal force or effect" by its own terms. It is cited because it is the SEC's own statement of what evidence it expects, not as an independent standard.

---

## 2. STATISTICAL SIGNIFICANCE — Minimum sample size before a win rate means anything

**There is no authority that publishes "30 trades" or "100 trades" as the minimum sample for a trader's win rate.** What is published is the *formula* for computing the minimum sample size given the precision you claim, plus validity floors on the underlying test. These are the citable standards.

### 2.1 — Minimum sample size for a proportion (the governing formula)

- **Metric name:** Minimum sample size to detect a change in a proportion at a stated confidence and power
- **Concrete threshold:** `N ≥ [ (z_{1−α/2}·√(p₀(1−p₀)) + z_{1−β}·√(p₁(1−p₁))) / δ ]²` for a two-sided interval; `N ≥ [ (z_{1−α}·√(p₀(1−p₀)) + z_{1−β}·√(p₁(1−p₁))) / δ ]²` for one-sided, where δ is the allowable deviation. Fleiss, Levin & Paik's continuity correction `N = N′ + 1/δ` is also recommended. **Worked example from the source: p₀ = 0.10 → p₁ = 0.20, α = 0.05 one-sided, β = 0.10 ⇒ N ≈ 102, and 112 with the continuity correction.** The source also states: "taking the value of the proportion defective to be 0.5 leads to the largest possible sample size."
- **Source organisation:** National Institute of Standards and Technology (NIST) — NIST/SEMATECH e-Handbook of Statistical Methods
- **Document / page title:** "7.2.4.2. Sample sizes required" (§7.2.4 Does the proportion of defectives meet requirements?)
- **URL:** https://www.itl.nist.gov/div898/handbook/prc/section2/prc242.htm
- **Verbatim quote:** "Thus, the minimum sample size is … For a two-sided interval N ≥ [ ( z_{1−α/2} √p₀(1−p₀) + z_{1−β} √p₁(1−p₁) ) / δ ]² … For a one-sided interval N ≥ [ ( z_{1−α} √p₀(1−p₀) + z_{1−β} √p₁(1−p₁) ) / δ ]² … The mathematical details of this derivation are given on pages 30-34 of Fleiss, Levin, and Paik. … Note that taking the value of the proportion defective to be 0.5 leads to the largest possible sample size." (The page's typeset formula is LaTeX; it is rendered here in plain-text form. The page also carries a machine-readable alt-string of the one-sided formula: `= [z(alpha)*SQRT(p0*(1-p0)) + z(beta)*SQRT(p1*(1-P1))/delta]^2`.)
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD** (NIST is a US federal statistical authority; its handbook is the reference cited by the academic literature below)
- **Fetched:** Yes
- **Applied to the local package:** With p₀ = 0.50 (coin-flip win rate), p₁ = 0.55, one-sided α = 0.05, β = 0.20, δ = 0.05, this formula requires **N ≥ 617 trades** (637 with NIST's continuity correction) to show that a 55% win rate is better than chance. The package's `min_trades: 30` is **~21× smaller** than the sample needed to support its own `min_win_rate: 0.55` claim at those parameters. That gap is a finding, not a stylistic preference.

### 2.2 — Validity floors on the one-proportion test

- **Metric name:** Sample-size validity conditions for the normal approximation to the binomial
- **Concrete threshold:** The normal approximation is "valid for large N, (N > 30)"; and `min{N·p₀, N·(1−p₀)} ≥ 5`. The source's own worked consequences: if p₀ = 0.1, N should be at least 50; if p₀ = 0.01, N should be at least 500.
- **Source organisation:** National Institute of Standards and Technology (NIST) — NIST/SEMATECH e-Handbook of Statistical Methods
- **Document / page title:** "7.2.4. Does the proportion of defectives meet requirements?" (§7.2.4 — hypothesis testing for a proportion)
- **URL:** https://www.itl.nist.gov/div898/handbook/prc/section2/prc24.htm
- **Verbatim quote:** "The test statistic … depends on a normal approximation to the binomial distribution that is valid for large N, (N > 30). … Because the test is approximate, N needs to be large for the test to be valid. One criterion is that N should be chosen so that min{ N_p0 , N(1-p0) } ≥ 5 . For example, if p0 = 0.1, then N should be at least 50 and if p0 = 0.01, then N should be at least 500." (Inline mathematics rendered as plain text; the page's alt-string for the criterion reads `min{ Np 0 , N (1 - p 0 )} ≥ 5`.)
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **Note:** N > 30 is the *validity floor for the test*, not a claim that 30 trades makes a win rate meaningful. It is a validity condition for a normal approximation, nothing more.

### 2.3 — The correct confidence interval for a win rate: Wilson score

- **Metric name:** Confidence interval method for a binomial proportion (win rate)
- **Concrete threshold:** Use the Wilson (1927) score interval — recommended by Brown, Cai & DasGupta (2001) and Agresti & Coull (1998). The handbook states the procedure "is also supported by the research of Agresti and Coull" and "was recommended by Agresti and Coull for virtually all combinations of n and p." Its key property: "the lower limit cannot be negative," which the naive Wald interval `p̂ ± z√(p̂(1−p̂)/n)` cannot guarantee.
- **Source organisation:** National Institute of Standards and Technology (NIST) — NIST/SEMATECH e-Handbook of Statistical Methods
- **Document / page title:** "7.2.4.1. Confidence intervals" (§7.2.4)
- **URL:** https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm
- **Verbatim quote:** "The Wilson method for calculating confidence intervals for proportions (introduced by Wilson (1927), recommended by Brown, Cai and DasGupta (2001) and Agresti and Coull (1998)) is based on inverting the hypothesis test given in Section 7.2.4. … One advantage of this procedure is that its worth does not strongly depend upon the value of n and/or p, and indeed was recommended by Agresti and Coull for virtually all combinations of n and p."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **Underlying academic references (named by NIST, cited not independently fetched):** Brown, Cai & DasGupta (2001), "Interval Estimation for a Binomial Proportion," *Statistical Science* 16(2); Agresti & Coull (1998), "Approximate Is Better than 'Exact' for Interval Estimation of a Proportion," *JASA*. Both are named verbatim in the NIST page.

### 2.4 — "Rule of three" for a zero-numerator sample (Hanley & Lippman-Hand)

- **Metric name:** Upper confidence bound when zero events are observed
- **Concrete threshold:** With zero events in *n* trials, the 95% upper confidence limit on the event rate is approximately **3/n**. (The 3 comes from −ln(0.05) ≈ 3.)
- **Source organisation:** JAMA (American Medical Association) / Hanley J.A. & Lippman-Hand A.
- **Document / page title:** "If Nothing Goes Wrong, Is Everything All Right? Interpreting Zero Numerators," *JAMA* 1983;249(13):1743–1745
- **URL:** https://pubmed.ncbi.nlm.nih.gov/6827763/ (bibliographic record, PMID 6827763); reprint: https://www.jhanley.biostat.mcgill.ca/Reprints/If_Nothing_Goes_1983.pdf
- **Verbatim quote (from the reprint's own text):** "Because a confidence interval may be constructed easily from a zero numerator using the \"rule of three,\" we hope that those fortunate enough to be able to report \"no problems so far\" will quantify the worst or best that a group of future patients can expect."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** **Partially.** The PubMed bibliographic record was fetched and confirms title/authors/journal/volume/pages/DOI/PMID. The McGill reprint PDF was fetched (75,962 bytes) but is a **scanned image with no extractable text layer**, so the quote above is taken from the publisher-hosted search result for that same reprint rather than from text extracted from the PDF itself. **Do not treat the "3/n" as machine-verified from the PDF.** If you need it airtight, obtain the PDF through an institutional subscription.

### 2.5 — What is NOT a statistical standard: "30 trades"

No regulator, exchange, professional body or academic text located in this research publishes a minimum trade count of 30 for a trader's win rate to be meaningful. The NIST source (§2.1) is the citable authority, and it produces a *sample size as a function of the claim*, not a constant. See §10.

---

## 3. RISK-ADJUSTED PERFORMANCE — Authoritative definitions

### 3.1 — Sharpe ratio: the definition and its stated industry status

- **Metric name:** Sharpe ratio (excess return per unit of total risk)
- **Concrete threshold:** `Sharpe = (mean portfolio return − risk-free rate) / standard deviation of returns`. Zero excess return ⇒ Sharpe = 0. The source describes it as "the industry standard for measuring risk-adjusted return" — i.e. CFA Institute assigns it canonical status. No interpretation band is published by CFA Institute.
- **Source organisation:** CFA Institute
- **Document / page title:** "The Sharpe Ratio and the Information Ratio," by Deborah Kidd, CFA — *Investment Performance Measurement* (CFA Institute / H17004), ©2011
- **URL:** https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/sharpe-ratio-and-the-information-ratio.pdf
- **Verbatim quote:** "The Sharpe ratio is the industry standard for measuring risk-adjusted return. Sharpe originally developed this ratio as a single-period forecasting tool and named it the reward-to-variability ratio. … The numerator of the ratio is the expected portfolio return less the risk-free rate, and the denominator is the portfolio's expected volatility or standard deviation of returns"
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 4 pages, text extracted)
- **Caveats the source itself raises (also citable):** the Sharpe ratio "measures only one dimension of risk: the variance"; it "penalizes both [upside and downside deviations] equally"; negative Sharpe ratios "are also uninformative"; and "An investor must consider the length of the time period used in the measurement; longer time periods tend to result in lower volatility measures."

### 3.2 — Sortino ratio: downside deviation, and the MAR dependency

- **Metric name:** Sortino ratio (excess return over downside risk relative to a Minimum Accepted Return)
- **Concrete threshold:** `Sortino = (Mean portfolio return − MAR) / Downside deviation`, where MAR is an investor-defined Minimum Accepted Return (absolute return, index return, risk-free rate, or zero). Same shape as Sharpe with MAR replacing the risk-free rate in the numerator and downside deviation replacing standard deviation in the denominator.
- **Source organisation:** CFA Institute
- **Document / page title:** "The Sortino Ratio: Is Downside Risk the Only Risk that Matters?" by Deborah Kidd, CFA — *Investment Performance Measurement* (CFA Institute / H17004), ©2012
- **URL:** https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/the-sortino-ratio.pdf
- **Verbatim quote:** "The Sortino ratio is a variation of the Sharpe ratio, the most universal measure of return to risk. … The formula for the Sortino ratio is simple; it is calculated in the same way as the Sharpe ratio except that the MAR replaces the risk-free rate in the numerator and downside deviation replaces standard deviation in the denominator. … The calculation for the Sortino ratio is as follows: S = (Mean portfolio return – MAR)/ Downside deviation."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 3 pages, text extracted)
- **Caveat the source raises:** "several variations of the downside deviation calculation exist, and which one an investor uses matters a great deal."

### 3.3 — Maximum drawdown and drawdown duration: recognised appraisal ratios, but no published band

- **Metric name:** Maximum drawdown and drawdown duration (appraisal ratios)
- **Concrete threshold:** **No numerical threshold is published by CFA Institute.** CFA Institute lists both as *appraisal ratios* that "measure investment skill" and warns they "must be used with care, noting the assumptions of each ratio."
- **Source organisation:** CFA Institute
- **Document / page title:** "Portfolio Performance Evaluation" — CFA Institute Refresher Reading (2026 curriculum), Learning Outcome Statements and Summary
- **URL:** https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/portfolio-performance-evaluation
- **Verbatim quote:** "calculate and interpret the Sortino ratio, the appraisal ratio, upside/ downside capture ratios, maximum drawdown, and drawdown duration; … Investment performance appraisal ratios—including the Sortino ratio, upside/downside capture ratios, maximum drawdown, and drawdown duration—measure investment skill. Appraisal ratios must be used with care, noting the assumptions of each ratio and affording the appropriateness to the measured investment process, risk tolerance, and investor time horizon."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **Consequence:** The local package's `kill_switch.max_drawdown_pct: 0.20` and `pool` staleness rule **cannot** be attributed to CFA Institute. There is no CFA Institute number. See §10 and §11.

### 3.4 — The three-year ex-post standard deviation: a presentation requirement with a real threshold

- **Metric name:** Required risk statistic and its look-back window
- **Concrete threshold:** Where monthly returns are available, the firm **must** present the **three-year annualized ex post standard deviation** (using monthly returns) of the composite and the benchmark as of each annual period end. (Provision 4.A.1(j) for composites; 6.A.1(h) for pooled funds.) If the composite has at least three annual periods but 36 monthly returns are unavailable, the firm must disclose that the statistic is not presented (4.C.36). Recommendation 4.B.4: for all periods greater than three years where annualized returns are presented, the corresponding annualized ex post standard deviation should also be presented.
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *Global Investment Performance Standards (GIPS®) for Firms*, 2020 edition — provisions 4.A.1(j), 4.C.36, 4.B.4, 6.A.1(h)
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Verbatim quote:** "For composites for which monthly composite returns are available, the three-year annualized ex post standard deviation (using monthly returns) of the composite and the benchmark as of each annual period end."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 146 pages, text extracted)

### 3.5 — Gross-of-fees is the GIPS convention for risk measures

- **Metric name:** Fee basis for risk measures
- **Concrete threshold:** "The firm should use gross-of-fees returns when calculating risk measures" (2.B.7, recommendation). Required disclosure: if the firm presents additional risk measures it must (a) describe them and (b) disclose the name of the risk-free rate if one is used (4.C.41, 5.C.41); and it must disclose whether gross-of-fees or net-of-fees returns were used to calculate presented risk measures (4.C.42).
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *GIPS for Firms*, 2020 — provisions 2.B.7, 4.C.41, 4.C.42, 5.C.41
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Verbatim quote:** "2.B.7 The firm should use gross-of-fees returns when calculating risk measures." / "4.C.42 The firm must disclose if gross-of-fees or net-of-fees returns are used to calculate presented risk measures."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **On-chain implication:** A Sharpe ratio computed on wallet PnL **after** modelled slippage, gas and MEV is a net-of-fees Sharpe and must be labelled as such. The GIPS convention is to compute risk on gross and report the fee basis.

### 3.6 — Profit factor: definition is universal, thresholds are NOT

- **Metric name:** Profit factor (gross profit ÷ gross loss)
- **Concrete threshold:** The *definition* is consistent across the literature (`gross profit / gross loss`). **No regulator, exchange, CFA Institute, GIPS or professional body publishes an interpretation band.** The frequently repeated bands ("above 1.5 is workable, above 2.0 is strong") appear only on vendor/blog pages.
- **Source organisation:** *(no authoritative publisher located)* — see §10. The definition as used by the local package matches the consensus formula stated by every vendor page checked, including https://www.tradingmetrics.com/en/technical-analysis/trading-metrics/trade-specific-metrics/profit-factor ("Profit factor is gross profit divided by gross loss") — which is **NOT AUTHORITATIVE** and is cited only to show where the number circulates.
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION** (for the thresholds); the definition itself is unremarkable and uncontested
- **Fetched:** Vendor pages exist but are excluded as authority. The local package's `min_profit_factor: 1.5` therefore has **no citable authority** and should be labelled an analyst choice.

### 3.7 — Win rate: definition is universal, thresholds are NOT

- **Metric name:** Win rate (winning trades ÷ total closed trades)
- **Concrete threshold:** No regulator, exchange, professional body or academic text publishes a win-rate threshold for trader quality. Win rate is only meaningful *with* its confidence interval (§2.3) and its cost basis (§1.2). There is **no** "industry standard" win rate.
- **Source organisation:** *(none located)*
- **Classification tag:** **NOT STANDARDISED** — see §10
- **Fetched:** N/A — negative finding, established by exhaustive search of the sources listed in §12

---

## 4. TRADER EVALUATION — Published criteria for qualifying a trader

**Every rubric in this section is a commercial product term, not a professional standard.** A prop firm publishes a challenge to sell a funded account; an exchange publishes copy-trading eligibility to recruit liquidity providers. Neither is a quality attestation on behalf of the market.

### 4.1 — FTMO Challenge trading objectives (2-Step)

- **Metric name:** Prop-firm challenge pass criteria
- **Concrete threshold:** Profit Target = **10%** of Initial Simulated Capital; Maximum Loss = **10%** of Initial Simulated Capital (end-of-day trailing limit, recalculated daily); Maximum Daily Loss = **3%** of Initial Simulated Capital; Minimum Trading Days = **4** (a day on which at least one position is opened, 00:00:00–23:59:59 CE(S)T)
- **Source organisation:** FTMO (commercial proprietary-trading firm)
- **Document / page title:** "FTMO Trading Objectives"
- **URL:** https://www.ftmo.com/en/trading-objectives/
- **Verbatim quote:** "The Profit Target for the FTMO Challenge is calculated as **10%** of the Initial Simulated Capital." / "the **Maximum Loss Amount**, which is **10%** of the Initial Simulated Capital." / "the **Maximum Daily Loss Amount**, which is **3%** of the Initial Simulated Capital." / "The Minimum Trading Days rule requires the trader to achieve at least **4** Trading Days."
- **Classification tag:** **EXCHANGE-OR-FIRM-STANDARD** — **but explicitly COMMERCIAL MARKETING, NOT A STANDARD**
- **Fetched:** Yes
- **Plain statement:** This is FTMO's product specification. It tells you what a *challenge seller* requires. It says nothing about whether the trader who passes is actually good — a challenge pass rate is a commercial KPI. It is not evidence of trader skill, and FTMO is not a regulator.

### 4.2 — Exchange copy-trading eligibility rules: NOT VERIFIED, EXCLUDED

- **Metric name:** Copy-trading lead/master-trader eligibility (ROI, AUM, win-rate floors)
- **Concrete threshold:** **None verified.**
- **Source organisation:** Bybit, OKX, Binance (candidates examined)
- **URLs examined:** https://www.bybit.com/en/help-center/topic-list/copy-trading · https://www.okx.com/en-us/help/copy-trading-introduction · https://www.binance.com/en/support/faq/detail/360038285832
- **Verbatim quote:** *n/a* — the pages returned navigation chrome only ("This article is currently not supported on this site." / "Buy Bitcoin & Crypto | Crypto Exchange, App & Wallet") with no eligibility thresholds in the retrieved body.
- **Classification tag:** **NOT-AUTHORITATIVE / UNVERIFIED — EXCLUDED**
- **Fetched:** Yes, but the substantive criteria were not present in the fetched body. **No numeric copy-trading eligibility threshold is asserted anywhere in this file.** If you need one, it must be read in a real browser session with the region-correct URL.

### 4.3 — Institutional published minimums for a track record

- **Metric name:** Minimum track-record length before a performance record may be presented as a GIPS composite
- **Concrete threshold:** A firm must attain GIPS compliance for a **minimum of five years** (or since inception if shorter) before it may claim compliance (1.A.3). Pooled funds must present **at least five years** of GIPS-compliant performance, then **add one year each year, building up to a minimum of 10 years** (6.A.1(a)). For a gips advertisement presenting composite returns, the required presentations are one-, three- and five-year annualized returns through the most recent period, plus since-inception if under five years (8.C.1(a)).
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *GIPS for Firms*, 2020 — provisions 1.A.3, 6.A.1(a), 8.C.1(a)
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Verbatim quote:** "To initially claim compliance with the GIPS standards, the firm must attain compliance for a minimum of five years or for the period since the firm inception if the firm has been in existence for less than five years." / "At least five years of performance (or for the period since the pooled fund inception date if the pooled fund has been in existence less than five years) that meets the requirements of the GIPS standards. After the firm presents a minimum of five years of GIPS-compliant performance … the firm must present an additional year of performance each year, building up to a minimum of 10 years of GIPS-compliant performance."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **On-chain implication:** This is the closest thing to an institutional "you need at least N years of history" rule in existence — and it is a **presentation** rule for GIPS-compliant composites, not a quality bar on the trader. The closest crypto analogue is §1.3's life-of-portfolio substitution.

---

## 5. CRYPTO-NATIVE "smart money" and "profitable wallet" definitions

**Every definition in this section is a vendor's own product definition.** There is no industry body for on-chain wallet analytics. Each vendor publishes a definition; the definitions are **not** interchangeable and mostly **not** numerical.

### 5.1 — Nansen "Smart Money" / "Smart Trader"

- **Metric name:** Smart Money / Smart Trader wallet cohort
- **Concrete threshold:** **Nansen publishes no numeric threshold (no minimum win rate, no minimum PnL, no minimum trade count).** It publishes *labels with look-back windows*: `Smart Trader` ("Historically profitable traders"), formerly `30D Smart Trader`, `90D Smart Trader`, `180D Smart Trader`; and `Smart HL Perps Trader` ("Profitable Hyperliquid traders"). Since 14 October 2026 the dated labels are deprecated and `Smart Trader` covers all windows. The Smart Money PnL Leaderboard accepts `timeframe` ∈ {1, 7, 30, 90, 180} days (default 7) and returns per-wallet `realized_pnl_usd`, `unrealized_pnl_usd`, `total_pnl_usd`, `avg_trade_roi`, `win_rate`, `n_trades`, `n_tokens`, `open_trades`.
- **Source organisation:** Nansen
- **Document / page title:** "Smart Money" (Nansen API docs); "PnL Leaderboard" (Nansen API docs); changelog "14-10-2026: Smart Trader Covers All Windows; Dated Smart Trader Labels Deprecated"
- **URLs:** https://docs.nansen.ai/api/smart-money · https://docs.nansen.ai/api/smart-money/pnl-leaderboard · https://docs.nansen.ai/api/changelog/14-10-2026-dated-smart-trader-labels-deprecation.md
- **Verbatim quote:** "Smart Money endpoints provide insights into the trading and holding activity of historically profitable traders: Smart Traders on spot markets and Smart HL Perps Traders on Hyperliquid." / label table: "`Smart Trader` | Historically profitable traders; covers all 30D, 90D and 180D Smart Traders" / "`Smart HL Perps Trader` | Profitable Hyperliquid traders" / PnL Leaderboard: "Each entry includes realized and unrealized PnL, win rate, trade counts, and top token positions."
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes
- **Critical honesty note:** Nansen does **not** publish the rule that turns "historically profitable" into a label. The selection criteria are not public. Any claim that "Nansen's Smart Money = wallets with >X% win rate over N trades" is **fabricated**. What *is* published is the label vocabulary, the chain coverage, the leaderboard fields, and the fact that `win_rate` and `n_trades` are returned per wallet — which means **the downstream consumer chooses the threshold**, and Nansen does not validate it.

### 5.2 — Nansen holder-count threshold ($1)

- **Metric name:** Holder-count inclusion threshold for Smart Money / Fund holdings
- **Concrete threshold:** `holders_count` counts a wallet when it holds **more than $1** of the token. Until 27 October 2026 it required **more than $100**.
- **Source organisation:** Nansen
- **Document / page title:** Changelog "27-10-2026: Smart Money and Fund Holdings Count Holders Above $1"
- **URL:** https://docs.nansen.ai/api/changelog/27-10-2026-holder-minimum-1-usd.md
- **Verbatim quote:** "`holders_count` now counts a wallet when it holds more than $1 of the token. It used to require more than $100. … on October 27 the Smart Money holder count for ETH on Ethereum was 311 under the old rule and 581 under the new one."
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes
- **Why it matters here:** This is a **worked example of threshold drift** — the same endpoint's population changed by +87% overnight with no change to the underlying wallets. Any on-chain "smart money" cohort is a moving target defined by a vendor, and a threshold can change under you.

### 5.3 — Nansen first funder (the funding-trace primitive)

- **Metric name:** First funder / funding source
- **Concrete threshold:** "the earliest address to send native gas to the input EVM address … on whichever supported chain the earliest funding happened." Chain is fixed to `all`; the result is point-in-time with no historical look-back.
- **Source organisation:** Nansen
- **Document / page title:** "Address First Funder" (Nansen API docs)
- **URL:** https://docs.nansen.ai/api/profiler/address-first-funder
- **Verbatim quote:** "Returns the **first funder** of a wallet: the earliest address to send native gas to the input EVM address. … **First funder = the first address to send native gas to this wallet**, on whichever supported chain the earliest funding happened. This is the gas-funder / funding source, **not** the USDC (or any stablecoin) source. Usually the same entity (a CEX withdrawal drops both), but not guaranteed."
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes
- **On-chain implication:** This is the strongest published primitive for the local package's anti-insider funding trace, and it is exactly the mechanism `leapspace/deployers.py` approximates on Solana. Nansen also publishes the **related-wallets** endpoint (relationship type + timing) at https://docs.nansen.ai/api/profiler/address-related-wallets — "Returns a current, point-in-time view of related wallets — there is no date-range parameter or historical look-back."

### 5.4 — Nansen chain coverage (how the standards travel across chains)

- **Metric name:** Per-chain historical depth and data freshness
- **Concrete threshold:** Concrete earliest-index dates per chain, e.g. Ethereum 30 Jul 2015; Solana 17 Mar 2020; BNB Chain 29 Aug 2020; Avalanche 23 Sep 2020; Arbitrum 29 May 2021; Optimism 11 Nov 2021; Base 15 Jun 2023; Linea 06 Jul 2023; Sui 12 Apr 2023; Monad 14 May 2025; Sonic 01 Dec 2024; HyperEVM 18 Feb 2025. Smart Money Netflow/DEX Trades/Holdings support 18 chains including arbitrum, avalanche, base, bnb, ethereum, optimism, polygon, solana, sonic.
- **Source organisation:** Nansen
- **Document / page title:** "Data Coverage by Chain" (Nansen API docs)
- **URL:** https://docs.nansen.ai/api/data-coverage
- **Verbatim quote:** "This page is the single source of truth for **how far back Nansen indexes each chain** and **how fresh live data is**. … Historical endpoints avoid look-ahead bias where point-in-time sources are available, but results are not immutable response snapshots. Results may still be revised for late-arriving or backfilled onchain data, data-quality corrections, historical-price fixes, attribution or label-history updates …"
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes
- **Directly usable for the "top 10 memecoin chains" requirement:** the coverage table is the honest instrument for deciding which chains a wallet-history requirement can even be tested on. A wallet on Base (indexed from 15 Jun 2023) has a shorter maximum track record than one on Ethereum (30 Jul 2015) — which directly limits any minimum-history criterion.

### 5.5 — GMGN: insider, sniper, first-70-buyer definitions

- **Metric name:** Insider-trading wallets / Insider Trading Holder Ratio / Snipers / Top 70 buyers
- **Concrete threshold:** (a) Insider Trading wallets = "Wallets that did not buy tokens after trading opened, but hold tokens." (b) Insider Trading Holder Ratio = "The proportion of holdings by insider trading wallets to the total token supply" — **no threshold value published; GMGN says only "the higher the ratio, the more concerning it is."** (c) Snipers = "Buyers who purchased within the first few blocks after trading opened" — **"the first few blocks" is not quantified.** (d) Top 70 Buyer Wallets = "Wallets that were the first 70 to buy tokens after the opening of trading" — 70 is a fixed count. (e) Scammer Wallets = "Wallets that frequently buy rug pull tokens, suspected to be secondary accounts of the token creators involved in rug pull schemes" — **not quantified.**
- **Source organisation:** GMGN (commercial on-chain analytics platform)
- **Document / page title:** "Insider Traders, Snipers, First 70 Buyers" (GMGN Tutorial)
- **URL:** https://docs.gmgn.ai/index/insider-traders-snipers-first-70-buyers
- **Verbatim quote:** "Insider Trading: Wallets that did not buy tokens after trading opened, but hold tokens, may indicate that the token creator's holdings were transferred to multiple wallets to secretly sell off. … Insider Trading Holder Ratio: The proportion of holdings by insider trading wallets to the total token supply, the higher the ratio, the more concerning it is. … **Snipers:** Buyers who purchased within the first few blocks after trading opened. **Scammer Wallets:** Wallets that frequently buy rug pull tokens, suspected to be secondary accounts of the token creators involved in rug pull schemes."
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes
- **GMGN's own disclaimer, which must travel with any use of these labels:** "The holding status of insider traders, snipers, and the first 70 buyers cannot guarantee real-time accuracy and is provided for auxiliary reference only."
- **Note:** GMGN's own "Track Smart Money" page carries no criteria at all: "GMGN has big data on smart money … Especially with the release of the new meme coin, there is a concentrated entry of smart money. The necessary action to check the contract is not less, because a lot of smart money also has a disorderly situation." (https://docs.gmgn.ai/index/track-smart-money) — i.e. **the vendor itself says smart money is frequently not competent.** That is the single most important vendor statement in this file for the local package.

### 5.6 — Birdeye Smart Money API

- **Metric name:** Smart Money cohort (tokens identified via smart money traders)
- **Concrete threshold:** **None published.** Birdeye publishes endpoint semantics only: "Endpoints that track high-performing wallets and their activity so you can follow smart money flows" and "Returns tokens identified via smart money traders, segmented by trader style and risk appetite." Endpoints: `GET /smart-money/v1/token/list` and `POST /defi/v3/token/money-flow` ("Retrieve token money flow metrics across selected time frames, wallet tags, and wallet addresses").
- **Source organisation:** Birdeye
- **Document / page title:** "Smart Money API" (Birdeye Data docs)
- **URL:** https://data.birdeye.so/docs/data-api/smart-money/index
- **Verbatim quote:** "Endpoints that track high-performing wallets and their activity so you can follow smart money flows." / "Returns tokens identified via smart money traders, segmented by trader style and risk appetite."
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes
- **Honest note:** "segmented by trader style and risk appetite" implies a style/risk taxonomy that Birdeye does not publish thresholds for. There is no numeric criterion to cite.

### 5.7 — Arkham: confidence-scored attribution (the one vendor that publishes its confidence bands)

- **Metric name:** Verified label / Entity Prediction confidence thresholds
- **Concrete threshold:** **Verified labels: ≥98% confidence** (blue badge). **Entity Prediction labels: ≥80% confidence** (pink badge), explicitly "lower-confidence" and to be treated as "probabilistic attribution rather than certainty."
- **Source organisation:** Arkham
- **Document / page title:** "How Arkham Labels Wallets" (Arkham API guides, machine-readable at `/llms/guides/how-arkham-labels-wallets.md`)
- **URL:** https://arkm.com/llms/guides/how-arkham-labels-wallets.md (also https://arkm.com/api/docs)
- **Verbatim quote:** "Arkham labels wallets by combining **on-chain behavior** with **public off-chain signals**, running that through our proprietary attribution system (**ULTRA**), and only publishing labels when they meet strict confidence thresholds. … **Verified labels ≥98%** … **Prediction labels ≥80%** … Prediction labels are explicitly marked as lower-confidence."
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes
- **Also published by Arkham (citable, and directly relevant to insider labelling):** the *Tags* vocabulary — "qualitative descriptors that summarize the **type** or **behavior** of an address/entity, whether it is labeled or not" with examples "Fund," "BTC Whale," "OFAC Sanctioned," "Hacker," "Banned by USDT," "High Transacting" — and the standing caveat that "Entity composition can change as new attribution is discovered and additional addresses are linked." (https://arkm.com/llms/guides/addresses-entities-labels.md)
- **Why this is the most useful vendor row in the file:** Arkham is the only vendor located that publishes the **confidence band attached to each attribution**. An insider/COI exclusion rule that says "exclude wallets Arkham tags as insider at ≥98% confidence" is defensible; one that says "exclude wallets I think are insiders" is not.

### 5.8 — CryptoQuant and Dune: smart-money definitions NOT LOCATED

- **Metric name:** CryptoQuant / Dune smart money, sniper, insider definitions
- **Concrete threshold:** **None published in the retrievable documentation.**
- **Source organisation:** CryptoQuant; Dune
- **URLs examined:** https://docs.cryptoquant.com/ · https://docs.cryptoquant.com/llms.txt · https://docs.cryptoquant.com/catalog/catalog.json · https://docs.cryptoquant.com/guides/glossary.md · https://docs.dune.com/ · https://docs.dune.com/llms.txt
- **Verbatim quote:** *n/a* — the CryptoQuant documentation index and full machine-readable catalog (442,844 chars retrieved) contain **zero** occurrences of "sniper", "insider", "smart money", "bundle" or "wash"; the Dune documentation index likewise contains no smart-money endpoint or definition.
- **Classification tag:** **NOT-AUTHORITATIVE / NOT LOCATED — EXCLUDED**
- **Fetched:** Yes, and the absence was verified against the full retrieved text, not inferred. **No CryptoQuant or Dune definition is asserted in this file.**

### 5.9 — Top-10 memecoin chains: the current measurable landscape

- **Metric name:** Chain-scoped memecoin categories, ranked by market capitalisation (free, reproducible, no key)
- **Concrete threshold:** Not a threshold but a *measurement*: chain-scoped memecoin categories observed on CoinGecko's live category list on 2026-11-03 — Solana Meme ($2,759.0M mcap / $414.1M 24h vol), Chinese Meme ($725.1M / $22.8M), Four.meme Ecosystem (BNB Memes) ($691.2M / $23.9M), IP Meme ($708.0M / $88.8M), Cat-Themed ($592.1M / $61.8M), AI Meme ($377.6M / $41.6M), Robinhood Chain Meme ($331.1M / $42.2M), Base Meme ($220.4M / $16.3M), BONK.fun Ecosystem ($137.0M / $9.4M), Bitcoin Meme ($130.3M / $1.1M), TON Meme ($94.1M / $5.5M), Sui Meme ($14.2M / $2.0M), TRON Meme ($6.0M / $0.4M), Desci Meme ($5.9M / $2.5M)
- **Source organisation:** CoinGecko (analytics vendor, free public API)
- **Document / page title:** CoinGecko API — `/coins/categories`
- **URL:** https://api.coingecko.com/api/v3/coins/categories
- **Verbatim quote:** Category list entries include `"name": "Solana Meme"`, `"name": "Base Meme"`, `"name": "Four.meme Ecosystem (BNB Memes)"`, `"name": "TON Meme"`, `"name": "TRON Meme"`, `"name": "Sui Meme"`, `"name": "Bitcoin Meme"`, `"name": "Robinhood Chain Meme"`, `"name": "BONK.fun Ecosystem"`, `"name": "Desci Meme"` with their `market_cap` and `volume_24h` values as listed above.
- **Classification tag:** **ANALYTICS-VENDOR-CONVENTION**
- **Fetched:** Yes (777 categories retrieved)
- **How to use this for the "works across top 10 memecoin chains" requirement:** the chain-scoped memecoin categories identify the chains where memecoin flow actually lives — **Solana, Base, BNB Chain, TON, Sui, TRON, Bitcoin, and Robinhood Chain** are the chain-scoped meme ecosystems visible in CoinGecko's own taxonomy. Cross-referencing with Nansen's coverage table (§5.4), all of Solana/Base/BNB are covered by Nansen's Smart Money endpoints, while **TON, Sui and TRON are not in the Nansen Smart Money chain list** — i.e. a "smart money" definition applied uniformly across the top 10 memecoin chains **does not exist at any vendor**, because the vendors do not cover the same chains. The local package's five chains (solana, ethereum, base, bsc, arbitrum) cover the highest-volume memecoin chains but not TON/Sui/TRON.

---

## 6. INSIDER AND CONFLICT-OF-INTEREST RULES

### 6.1 — Wash trading: the only published legal definition that transfers to on-chain

- **Metric name:** Wash trade / wash sale
- **Concrete threshold:** Two-part test: (a) the transaction "produces a wash result — meaning the purchase and sale of the same instrument at the same price, or a similar price, for accounts with the same beneficial ownership or for accounts with common beneficial ownership"; **and** (b) "that the party(ies) intended to achieve a wash result." Intent "may be inferred from evidence of prearrangement or from evidence that the orders or trade(s) were structured, entered or executed in a manner that the party(ies) knew, or reasonably should have known, would produce a wash result."
- **Source organisation:** Chicago Mercantile Exchange (CME Group), CME/CBOT/NYMEX/COMEX Rule 534, as filed with and approved by the CFTC
- **Document / page title:** "CME Group RA2008-5 Wash Trades Prohibited," Market Regulation Advisory Notice (Rule References: Rule 534), FAQ Q1
- **URL:** https://www.cmegroup.com/rulebook/files/cme-group-Rule-534.pdf
- **Verbatim quote:** "A wash trade is a form of fictitious trade in which a transaction or a series of transactions give the appearance that bona fide purchases and sales have been made, but where the trades have been entered into without the intent to take a bona fide market position or without the intent to execute bona fide transactions subject to market risk or price competition. … A wash trade requires: a) that the transaction or series of transactions produces a wash result — meaning the purchase and sale of the same instrument at the same price, or a similar price, for accounts with the same beneficial ownership or for accounts with common beneficial ownership; and b) that the party(ies) intended to achieve a wash result. Intent may be inferred from evidence of prearrangement or from evidence that the orders or trade(s) were structured, entered or executed in a manner that the party(ies) knew, or reasonably should have known, would produce a wash result."
- **Classification tag:** **EXCHANGE-OR-FIRM-STANDARD** (exchange rule under CFTC oversight)
- **Fetched:** Yes (via the r.jina.ai reader proxy; direct PDF fetch returned HTTP 403 from this host)

### 6.2 — CFTC glossary: fictitious trading

- **Metric name:** Fictitious trading
- **Concrete threshold:** No numeric threshold; a definition. Wash trading is one species.
- **Source organisation:** U.S. Commodity Futures Trading Commission (CFTC)
- **Document / page title:** CFTC "Futures Glossary" — entry "Fictitious Trading"
- **URL:** https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/CFTCGlossary/index.htm
- **Verbatim quote:** "Fictitious Trading — Wash trading, bucketing, cross trading, or other schemes which give the appearance of trading but actually no bona fide, competitive trade has occurred."
- **Classification tag:** **REGULATORY**
- **Fetched:** Yes (direct, HTTP 200)

### 6.3 — Sybil attack: the canonical academic definition

- **Metric name:** Sybil attack (identity multiplicity in a permissionless system)
- **Concrete threshold:** A conceptual definition, not a numeric threshold. Douceur et al. define the threat as a single faulty entity presenting multiple identities so as to control a substantial fraction of a redundant system; the defence requirement is that a Sybil-resistant system must have some external means of verifying identity.
- **Source organisation:** Douceur, J.R. (Microsoft Research) — peer-reviewed academic literature (IEEE Symposium on Security and Privacy 2002), published in *Revised Papers from the First International Workshop on Peer-to-Peer Systems*
- **Document / page title:** "The Sybil Attack" (Douceur et al.)
- **URLs:** https://link.springer.com/chapter/10.1007/3-540-45748-8_24 · public reprint: https://www.freehaven.net/anonbib/cache/sybil.pdf
- **Verbatim quote:** "Large-scale peer-to-peer systems face security threats from faulty or hostile remote computing elements. To resist these threats, many such systems employ redundancy. However, if a single faulty entity can present multiple identities, it can control a substantial fraction of the system, thereby undermining this redundancy."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (reprint PDF text retrieved via the reader proxy; Springer landing page reachable via search)

### 6.4 — Sybil attack, plain-language protocol definition

- **Metric name:** Sybil attack (protocol glossary)
- **Concrete threshold:** Conceptual definition only
- **Source organisation:** Ethereum Foundation (ethereum.org)
- **Document / page title:** Ethereum Glossary — "Sybil attack"
- **URL:** https://ethereum.org/glossary/#sybil-attack
- **Verbatim quote:** "Sybil attacks refer to individual humans tricking a system into thinking they are multiple people to increase their influence."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD** (protocol reference, non-regulatory)
- **Fetched:** Yes
- **Relevance to the local package:** this is the canonical anchor for the package's bundled/clustered wallets (one operator, many addresses). Note the definition is about *identity multiplicity*, not about *insider knowledge* — bundlers and insider wallets are a different exclusion category and need their own rule.

### 6.5 — Published standard for EXCLUDING funded-by-deployer / sniper / bundler wallets from a copy-trade universe

- **Metric name:** Copy-trade universe exclusion criteria for conflicted wallets
- **Concrete threshold:** **None exists.** No regulator, exchange, professional body, standard-setter or analytics vendor located in this research publishes a rule for excluding deployer-funded, sniper or bundler wallets from a copy-trading universe.
- **Source organisation:** *(none located)*
- **URLs searched:** SEC (FR API full-text across 2020–2026 for "206(4)-1", "hypothetical performance", "Investment Adviser Marketing"); FINRA rulebook 2210/2214; GIPS 2020 (Firms + Asset Owners) full text; Nansen API docs; GMGN docs; Birdeye docs; CryptoQuant docs (full catalog); Arkham docs; CME Rule 534; CFTC glossary; CFTC enforcement orders
- **Verbatim quote:** *n/a* — negative finding
- **Classification tag:** **NOT STANDARDISED** — see §10
- **Fetched:** N/A — established by exhaustive retrieval; see §12 for the gaps that remain open.

### 6.6 — What CAN be assembled from published primitives (a constructed rule, honestly labelled)

The closest thing to a defensible on-chain exclusion rule that this research could assemble from **published** components is:

| Component | Published source | Published threshold? |
|---|---|---|
| Funding-source trace (first funder) | Nansen Address First Funder | No threshold; defines the *method* (earliest native-gas sender across chains) |
| Related-wallet / cluster relation | Nansen Address Related Wallets | No threshold; returns relation type + timing |
| Attribution confidence | Arkham Verified vs Prediction labels | **Yes: ≥98% vs ≥80%** |
| Behavioural insider definition | GMGN insider/sniper/first-70 labels | **Yes: 70 buyers; "first few blocks" (unquantified)** |
| Wash-trade / self-dealing | CME Rule 534 | **Yes: wash result + intent** |
| Sybil / bundler identity multiplicity | Douceur et al.; ethereum.org | Conceptual only |
| Deployer identity | *none located* | — |

**This table is an ASSEMBLAGE, not a standard.** Every threshold in it is a vendor's own number and the combination is this document's construction. It must be labelled as such wherever it is used.

---

## 7. DECAY AND POOL HYGIENE — Published guidance on re-evaluation and survivorship bias

### 7.1 — GIPS composite maintenance: terminated portfolios must stay in the record

- **Metric name:** Anti-survivorship-bias rule for performance composites
- **Concrete threshold:** **No retroactive removal.** "Terminated portfolios must be included in the historical performance of the composite up to the last full measurement period that each portfolio was under management and for which the firm has discretion." Also: "All actual, fee-paying, discretionary segregated accounts must be included in at least one composite"; "Composites must include all portfolios, including segregated accounts and pooled funds, that meet the composite definition. The firm must not exclude portfolios from composites based solely on legal structure differences"; "Composites must include new portfolios on a timely and consistent composite-specific basis after each portfolio comes under management"; and "Any change to a composite definition must not be applied retroactively."
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *GIPS for Firms*, 2020 — provisions 3.A.2, 3.A.5, 3.A.6, 3.A.7, 3.A.9
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Verbatim quote:** "3.A.9 Terminated portfolios must be included in the historical performance of the composite up to the last full measurement period that each portfolio was under management and for which the firm has discretion."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (PDF, 146 pages)
- **On-chain implication, stated plainly:** **This is the published precedent for the package's pool-hygiene problem, and it points the opposite way to the package's current design.** The package's `pool.demote_if_unprofitable: true` demotes a wallet that "turns unprofitable" — but GIPS's rule is that a terminated portfolio *stays in the historical performance of the composite*. The GIPS-consistent behaviour is: **a wallet that stops trading or degrades is removed from the FORWARD cohort, and its history remains in the reported record** — never silently dropped, and never retroactively restated.

### 7.2 — Theoretical / model / backtested / hypothetical performance: the disclosure rule

- **Metric name:** Theoretical performance disclosure requirements
- **Concrete threshold:** Four cumulative disclosure requirements whenever theoretical performance is included as supplemental information: (a) disclose "that the results are theoretical, are not based on the performance of actual assets, and if the theoretical performance was derived from the retroactive or prospective application of a model"; (b) disclose "a basic description of the methodology and assumptions used to calculate the theoretical performance sufficient for the prospective client or prospective investor to interpret the theoretical performance, including if it is based on model performance, backtested performance, or hypothetical performance"; (c) disclose whether it reflects deduction of actual or estimated fees and transaction costs; (d) "Clearly label the theoretical performance as supplemental information."
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *GIPS for Firms*, 2020 — provisions 4.C.48 (composite report) and 5.C.44 (money-weighted composite report); the parallel asset-owner provision is 24.C.37
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Verbatim quote:** "4.C.48 When the gips composite report includes theoretical performance as supplemental information, the firm must: a. Disclose that the results are theoretical, are not based on the performance of actual assets, and if the theoretical performance was derived from the retroactive or prospective application of a model. b. Disclose a basic description of the methodology and assumptions used to calculate the theoretical performance sufficient for the prospective client or prospective investor to interpret the theoretical performance, including if it is based on model performance, backtested performance, or hypothetical performance. c. Disclose whether the theoretical performance reflects the deduction of actual or estimated investment management fees, transaction costs, or other fees and charges that an actual client portfolio would have paid or will pay. d. Clearly label the theoretical performance as supplemental information."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes (and the parallel asset-owner provision 24.C.37 was verified in the *GIPS for Asset Owners* PDF at https://www.cfainstitute.org/sites/default/files/-/media/documents/code/gips/2020-gips-standards-asset-owners.pdf)

### 7.3 — GIPS fair representation and full disclosure: the two governing principles

- **Metric name:** Fair representation and full disclosure
- **Concrete threshold:** Principles, not numbers: "The GIPS standards are ethical standards for investment performance presentation to ensure fair representation and full disclosure of investment performance."
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *GIPS for Firms*, 2020 — Introduction, "Overview: Key concepts"
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Verbatim quote:** "The GIPS standards are ethical standards for investment performance presentation to ensure fair representation and full disclosure of investment performance."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **Explicit negative finding:** the phrase "survivorship bias" does **not** appear anywhere in the GIPS 2020 Firms or Asset Owners standards (verified by full-text search of both PDFs: 0 hits in each). **GIPS addresses survivorship bias *structurally* — through 3.A.2/3.A.5/3.A.9 — without using the term.** Anyone citing "GIPS on survivorship bias" must cite those provisions, not the phrase.

### 7.4 — Pool re-evaluation cadence: NOT STANDARDISED

- **Metric name:** Required frequency for re-evaluating a copy-trading wallet pool
- **Concrete threshold:** **None.** No authority publishes a re-evaluation interval for a trader pool. GIPS requires *timely and consistent* inclusion of new portfolios (3.A.7) and annual reporting periods, but sets no re-evaluation cadence and no demotion rule for degraded constituents.
- **Source organisation:** *(none located)*
- **Classification tag:** **NOT STANDARDISED** — see §10
- **Fetched:** N/A — negative finding

### 7.5 — Annual reporting period: the one published cadence that transfers

- **Metric name:** Minimum reporting granularity for a performance record
- **Concrete threshold:** Annual, with each annual period end as the measurement date for the required risk statistic. Additional disclosures (e.g. 4.C.38, a material-error correction) must be included "for a minimum of one year and for as long as it is relevant to interpreting the track record."
- **Source organisation:** CFA Institute (GIPS)
- **Document / page title:** *GIPS for Firms*, 2020 — provisions 4.A.1(j), 4.C.38
- **URL:** https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf
- **Verbatim quote:** "4.C.38 The firm must disclose any change to the gips composite report resulting from the correction of a material error. Following the correction of the gips composite report, this disclosure must be included for a minimum of one year and for as long as it is relevant to interpreting the track record."
- **Classification tag:** **ACADEMIC-OR-PROFESSIONAL-GUILD**
- **Fetched:** Yes
- **Note:** the local package's `pool.stale_days: 30` is a **30-day** staleness window against an annual published cadence. There is no published basis for 30 days; it is an analyst choice.

---

## 8. What is NOT standardised

The following claims about trader performance are commonly made and have **no authoritative standard behind them**. Anyone asserting them as "industry standards" is wrong.

| # | Common claim | Status | What the research actually found |
|---|---|---|---|
| 1 | "A win rate above X% is good" | **NOT STANDARDISED** | No threshold published by any regulator, exchange, professional body or academic text located. Win rate is meaningful only with a confidence interval (§2.3) and a cost basis (§1.2). The package's 0.55 has no citation. |
| 2 | "You need at least 30 trades for a win rate to mean anything" | **NOT STANDARDISED** | No source states this. NIST (§2.1) gives a *formula* producing ≥617 trades for a 55%-vs-50% claim at α=0.05 one-sided, β=0.20, δ=0.05 — ~21× the package's 30. The "30" is folklore. |
| 3 | "A profit factor above 1.5 is good / 2.0 is strong" | **ANALYTICS-VENDOR-CONVENTION ONLY** | These bands appear only on vendor and blog pages (e.g. tradingmetrics.com). No regulator, CFA Institute or GIPS publishes a profit-factor band. |
| 4 | "A Sharpe ratio of X is excellent" | **NOT STANDARDISED as a band** | CFA Institute publishes the definition and calls it "the industry standard for measuring risk-adjusted return" (§3.1) but publishes **no interpretation band**. Sharpe's own interpretation is qualitative and context-dependent. |
| 5 | "A maximum drawdown under 20% is acceptable" | **NOT STANDARDISED** | CFA Institute lists maximum drawdown as an appraisal ratio and warns it "must be used with care" (§3.3). No published number. The package's 0.20 is an analyst choice. |
| 6 | "Sortino > X is good" | **NOT STANDARDISED as a band** | Definition published by CFA Institute (§3.2); no band. |
| 7 | "A trader with ≥N trades and ≥X% win rate is a successful trader" | **NOT STANDARDISED** | No such composite criterion exists anywhere. It is the package's construction. |
| 8 | "Smart money" wallets are demonstrably good traders | **NOT STANDARDISED** | Every vendor defines its own cohort with unpublished selection criteria (§5.1, §5.5, §5.6). **GMGN itself warns:** "a lot of smart money also has a disorderly situation." |
| 9 | "Nansen's Smart Money = wallets with win rate > X" | **FALSE / FABRICATED** | Nansen publishes no selection threshold at all (§5.1). Any such statement is invented. |
| 10 | "Sniper wallets are those that bought within N blocks" | **ANALYTICS-VENDOR-CONVENTION, partly quantified** | GMGN says "within the first few blocks" — **not quantified** (§5.5). Any specific N is the user's choice, not GMGN's. |
| 11 | "Insider Trading Holder Ratio above X% is dangerous" | **ANALYTICS-VENDOR-CONVENTION, unquantified** | GMGN publishes the ratio's definition and says only "the higher the ratio, the more concerning it is" — no threshold (§5.5). |
| 12 | "Wash trading" in on-chain copy trading | **LEGALLY DEFINED for regulated markets; NOT DEFINED for on-chain** | CME Rule 534 gives a two-part legal test (§6.1). No published extension of it to on-chain wallets, and no published on-chain wash-detection threshold. |
| 13 | "Bundler wallets must be excluded from copy-trade pools" | **NOT STANDARDISED** | No published exclusion rule. Bundling is documented in MEV literature and in vendor product features, but no exclusion criterion is published by any authority (§6.5). |
| 14 | "A copy-trade pool should be re-evaluated every N days" | **NOT STANDARDISED** | No cadence published (§7.4). The only published cadence is GIPS's annual reporting period (§7.5). |
| 15 | "Survivorship bias" as a GIPS term | **MISATTRIBUTION** | The phrase appears **zero times** in GIPS 2020 (Firms or Asset Owners). GIPS addresses it structurally via 3.A.2/3.A.5/3.A.9 (§7.3). |
| 16 | "The SEC amended the Marketing Rule's performance requirements in 2022" | **FALSE** | The only 2022 amendment to 206(4)-1 is a punctuation fix to (b)(2)(i) (§1.8). The performance requirements date from the 2021 adopting release (86 FR 13024). |
| 17 | "A wallet with a 10% win rate is break-even" | **NOT STANDARDISED** | Break-even win rate is a function of the reward:risk ratio and the cost model, neither of which is standardised; it is arithmetic on your own assumptions, not a standard. |
| 18 | "Profitable wallet" as a regulated or recognised category | **NOT STANDARDISED** | No regulator, exchange or standard-setter recognises the category. "Profitable" is a computed metric with no published verification protocol for on-chain data. |

---

## 9. What the local package currently assumes

Read from `leapspace/data/operator_config.json` (and mirrored in `leapspace/models.py::PROFILE_THRESHOLDS`). **Every value below is already labelled by the package itself as a POLICY CHOICE, not a market fact** — the file's own `_note` says: "Every number here is a POLICY CHOICE, not a market fact." This table records the current label and states whether this research can now replace it with a citation.

### 9.1 — `thresholds` (wallet-qualification gate; a wallet must clear ALL FOUR)

| Key | Value | Current label in the package | Replaceable with a citation? |
|---|---|---|---|
| `min_trades` | **30** | Operator policy ("taken verbatim from the brief"), inside a block headed "Every number here is a POLICY CHOICE, not a market fact" | **YES — replaced.** The authoritative alternative is NIST §2.1's sample-size formula (a real threshold, computable from α, β, δ and the claimed effect). 30 itself is folklore and is contradicted by the formula. |
| `min_win_rate` | **0.55** | Operator policy (same block) | **NO — cannot be replaced.** No authority publishes a win-rate threshold (§3.7, §8 #1). It becomes defensible only *conditionally*: 0.55 becomes citable only when paired with a stated α/β/δ and a Wilson interval at a computed minimum N. The number itself stays an analyst choice. |
| `min_profit_factor` | **1.5** | Operator policy (same block) | **NO — cannot be replaced.** Only vendor-convention bands exist (§3.6, §8 #3). Keep it, but label it ANALYTICS-VENDOR-CONVENTION and cite the vendor, or drop it and rely on the CI-based criterion. |
| `max_single_trade_pnl_share` | **0.40** | Operator policy (same block) | **NO — cannot be replaced.** No located authority publishes a concentration limit on a single trade's contribution to total PnL. It is a sound analyst heuristic with no upstream standard; keep it and label it as an analyst choice. |

### 9.2 — `consensus`

| Key | Value | Current label | Replaceable? |
|---|---|---|---|
| `min_wallets` | **3** | Operator policy (block note: "Trigger a trade only when >=N profiled wallets act on the same token within the window") | **NO.** No authority publishes a consensus threshold for copy-trading entry. Analyst choice. |
| `window_seconds` | **3600** | Operator policy | **NO.** No published standard. Analyst choice. |
| `profiled_only` | **true** | Operator policy | **NO** (but consistent with §1.2/§1.6: a portfolio that fails the profile should not be counted). |

### 9.3 — `friction` (execution-cost assumptions)

| Key | Value | Current label | Replaceable? |
|---|---|---|---|
| `slippage_bps` | **100.0** (1.00%/side) | Operator policy | **NO.** No standard slippage assumption exists. BUT: GIPS §3.5 requires that the fee/cost basis of a presented risk measure be disclosed, so this number must be *disclosed with any published Sharpe*, not replaced. |
| `priority_fee_usd` | **0.0** | Operator policy | **NO.** Analyst choice (and arguably wrong for Solana). |
| `latency_seconds` | **2.0** | Operator policy | **NO.** Analyst choice. |
| `failed_tx_rate` | **0.05** | Operator policy | **NO.** Analyst choice. |
| `mev_penalty_bps` | **0.0** | Operator policy | **NO.** Analyst choice; see the bundler/MEV gap in §8 #13. |
| `gas_usd` | **0.0** | Operator policy | **NO.** Analyst choice. |

### 9.4 — `kill_switch` (code-enforced)

| Key | Value | Current label | Replaceable? |
|---|---|---|---|
| `max_drawdown_pct` | **0.20** | Operator policy | **NO — cannot be replaced.** CFA Institute publishes maximum drawdown as an appraisal ratio and explicitly declines to publish a band (§3.3, §8 #5). **This 20% must be labelled an analyst choice, never "industry standard."** |
| `drawdown_window_seconds` | **900** | Operator policy | **NO.** Analyst choice. Note the tension with GIPS §7.5: a 15-minute drawdown window is far shorter than GIPS's annual measurement basis. |
| `min_liquidity_usd` | **1000.0** | Operator policy | **NO.** Analyst choice. |
| `max_slippage_bps` | **500.0** | Operator policy | **NO.** Analyst choice. |

### 9.5 — `rug` (stress-test injector)

| Key | Value | Current label | Replaceable? |
|---|---|---|---|
| `rug_probability` | **0.05** | Operator policy; the note says injected rug events are "SYNTHETIC by construction … This is a stress test, not a claim about history." | **NO.** Correctly framed as a stress-test parameter, not a market fact. |
| `min_drop_pct` | **0.80** | Operator policy (same) | **NO.** Stress-test parameter. |
| `max_drop_pct` | **0.99** | Operator policy (same) | **NO.** Stress-test parameter. |
| `liquidity_vanish_probability` | **0.02** | Operator policy (same) | **NO.** Stress-test parameter. |
| `seed` | **42** | Determinism | **NO.** Not a threshold. |

### 9.6 — `copy_trade`

| Key | Value | Current label | Replaceable? |
|---|---|---|---|
| `start_usd` | **1000.0** | Operator policy (finite bankroll) | **NO.** Analyst choice. |
| `position_pct` | **0.10** | Operator policy | **NO.** Analyst choice. |
| `stop_loss_pct` | **0.20** | Operator policy | **NO.** Analyst choice. |
| `take_profit_pct` | **0.50** | Operator policy | **NO.** Analyst choice. |
| `max_concurrent_positions` | **10** | Operator policy | **NO.** Analyst choice. |
| `seed` | **42** | Determinism | **NO.** Not a threshold. |

### 9.7 — `pool` (the re-evaluating trusted pool)

| Key | Value | Current label | Replaceable? |
|---|---|---|---|
| `stale_days` | **30** | Operator policy (note: "a wallet that stops trading, turns unprofitable, or is revealed to be cabal-funded gets demoted, with the reason logged") | **PARTIALLY.** No published staleness cadence (§7.4). **But the *shape* of the rule is citable from GIPS §7.1:** demote from the forward cohort while **retaining the wallet's history in the reported record** (3.A.9). The current wording ("demoted") does not say whether history is retained — GIPS says it must be. |
| `demote_if_unprofitable` | **true** | Operator policy | **PARTIALLY — and this is the one to change.** GIPS 3.A.9 requires terminated portfolios to remain in the composite's historical performance. The package's rule as written risks the survivorship-bias failure GIPS structurally prevents. Recommend: demote from forward cohort, **retain in reported history**, never restate retroactively (3.A.6). |
| `min_trades_for_promotion` | **30** | Operator policy | **YES — replaced.** Same as `thresholds.min_trades`: replace with NIST §2.1's formula applied to the specific claim being made. |

### 9.8 — `registries` and `chains` (not thresholds, but stated as policy)

| Key | Value | Current label | Note |
|---|---|---|---|
| `deployers` / `cabals` / `exchanges` / `insiders` | all `[]` (empty) | "The CABAL, EXCHANGE and INSIDER registries remain hand-maintained and are EMPTY by default — the anti-insider filter can only exclude a wallet it has been told about. With those lists empty the filter reports 'unknown' for every funding source and NO wallet is excluded for insider reasons — which is the honest result, not a clean bill of health." | **This is correct and should not change.** There is no published standard that can populate these lists (§6.5). What *can* be cited: Nansen's first-funder method (§5.3) to derive funding sources on-chain, and Arkham's ≥98%/≥80% confidence bands (§5.7) to set the bar for accepting an *externally supplied* insider label. |
| `chains.targets` | `["solana","ethereum","base","bsc","arbitrum"]` | "The operator brief names these five." | **The brief says top 10; the config says 5.** See §5.9 — the additional chain-scoped memecoin ecosystems are TON, Sui, TRON and Bitcoin, and **no single vendor's Smart Money definition covers all of them.** Expanding the chain list without a per-chain definition source would make the "successful trader" claim *less* uniform, not more. Recommend: either (a) keep 5 chains and state that the criteria are chain-agnostic and applied identically, or (b) extend to 10 and publish the per-chain vendor coverage table (§5.4) alongside it, so the reader knows which definition applies where. |

### 9.9 — Summary of the substitution opportunity

| Local threshold | Currently | Can this research replace it? |
|---|---|---|
| `min_trades` (30) | operator policy | **YES** → NIST §2.1 formula (α, β, δ, effect size) |
| `min_trades_for_promotion` (30) | operator policy | **YES** → NIST §2.1 formula |
| `min_win_rate` (0.55) | operator policy | **CONDITIONALLY** — only as "claimed effect size p₁", with the sample size derived from §2.1 and a Wilson CI per §2.3. The 0.55 itself remains an analyst choice. |
| `min_profit_factor` (1.5) | operator policy | **NO** — label as ANALYTICS-VENDOR-CONVENTION or replace with a CI-based criterion |
| `max_single_trade_pnl_share` (0.40) | operator policy | **NO** — analyst choice, no upstream standard |
| `max_drawdown_pct` (0.20) | operator policy | **NO** — analyst choice; CFA Institute publishes no band |
| `stale_days` (30) | operator policy | **NO** for the number; **YES** for the rule shape (GIPS 3.A.9: retain history) |
| `demote_if_unprofitable` (true) | operator policy | **YES — modify** per GIPS 3.A.9 + 3.A.6 (retain history; no retroactive restatement) |
| `kill_switch` thresholds, `friction`, `copy_trade`, `rug`, `consensus` | operator policy | **NO** — no published standards exist; keep them labelled as policy, and disclose the cost basis with any published risk metric (GIPS 4.C.42) |

---

## 10. Index of criteria with tags and URLs

| # | Criterion | Metric / threshold | Source org | Tag | URL |
|---|---|---|---|---|---|
| 1.1 | Substantiation floor | Reasonable basis to substantiate on demand; binary | SEC | REGULATORY | https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1 |
| 1.2 | Gross-vs-net parity | Net with ≥ equal prominence, same period, same methodology | SEC | REGULATORY | https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1 |
| 1.3 | Required performance periods | 1-, 5- and 10-year, or life of portfolio | SEC | REGULATORY | https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1 |
| 1.4 | Hypothetical performance | 3 cumulative conditions (policies / criteria+assumptions / risks+limits) | SEC | REGULATORY | https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1 |
| 1.5 | Extracted performance | Must provide total-portfolio results | SEC | REGULATORY | https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.206(4)-1 |
| 1.6 | Performance books & records | All worksheets demonstrating the calculation | SEC | REGULATORY | https://www.ecfr.gov/current/title-17/chapter-II/part-275/section-275.204-2 |
| 1.7 | Marketing Rule dates | Effective 4 May 2021; compliance 4 Nov 2022 | SEC | REGULATORY | https://www.sec.gov/files/exams-risk-alert-marketing-rule-2022.pdf |
| 1.8 | 2022 amendment scope | Punctuation-only fix to (b)(2)(i) | SEC | REGULATORY | https://www.federalregister.gov/documents/2022/04/15/2022-06972/technical-amendments-to-commission-rules-and-forms |
| 1.9 | No performance projection | Absolute ban, 3 carve-outs | FINRA | REGULATORY | https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210 |
| 1.10 | Fair dealing / no untrue statement | No untrue material fact | FINRA | REGULATORY | https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210 |
| 1.11 | Investment analysis tool | 4 cumulative conditions + mandatory hypothetical legend | FINRA | REGULATORY | https://www.finra.org/rules-guidance/rulebooks/finra-rules/2214 |
| 1.12 | Exam focus on performance claims | Reasonable-basis presumption | SEC (Exams) | REGULATORY | https://www.sec.gov/files/exams-risk-alert-marketing-rule-2022.pdf |
| 2.1 | Min sample size for a proportion | N ≥ [(z√p₀q₀ + z√p₁q₁)/δ]² ; ex. N≈102, 112 w/ continuity | NIST | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.itl.nist.gov/div898/handbook/prc/section2/prc242.htm |
| 2.2 | Test validity floors | N > 30 ; min{N·p₀, N·(1−p₀)} ≥ 5 | NIST | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.itl.nist.gov/div898/handbook/prc/section2/prc24.htm |
| 2.3 | Win-rate CI method | Wilson score interval | NIST | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm |
| 2.4 | Zero-numerator bound | ≈ 3/n at 95% | JAMA (Hanley & Lippman-Hand 1983) | ACADEMIC-OR-PROFESSIONAL-GUILD | https://pubmed.ncbi.nlm.nih.gov/6827763/ |
| 3.1 | Sharpe ratio definition | (Rp − Rf)/σ ; "industry standard" | CFA Institute | ACADEMIC-OR-PROFESSIONAL-GUILD | https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/sharpe-ratio-and-the-information-ratio.pdf |
| 3.2 | Sortino ratio definition | (Rp − MAR)/downside deviation | CFA Institute | ACADEMIC-OR-PROFESSIONAL-GUILD | https://rpc.cfainstitute.org/sites/default/files/-/media/documents/code/gips/the-sortino-ratio.pdf |
| 3.3 | Max drawdown / duration | Appraisal ratios; **no published band** | CFA Institute | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/portfolio-performance-evaluation |
| 3.4 | 3-yr ex-post std dev | Required when monthly returns available | CFA Institute (GIPS) | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf |
| 3.5 | Fee basis for risk measures | Gross-of-fees preferred; must disclose basis | CFA Institute (GIPS) | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf |
| 3.6 | Profit factor | Definition universal; **bands not standardised** | *(none)* | ANALYTICS-VENDOR-CONVENTION | https://www.tradingmetrics.com/en/technical-analysis/trading-metrics/trade-specific-metrics/profit-factor *(NOT AUTHORITATIVE)* |
| 3.7 | Win rate | **No standard threshold exists** | *(none)* | NOT STANDARDISED | — |
| 4.1 | Prop-firm challenge | 10% target / 10% max loss / 3% daily / 4 days | FTMO | EXCHANGE-OR-FIRM-STANDARD *(commercial marketing, not a standard)* | https://www.ftmo.com/en/trading-objectives/ |
| 4.2 | Copy-trade eligibility | **No threshold verified — excluded** | Bybit/OKX/Binance | NOT-AUTHORITATIVE / UNVERIFIED | https://www.bybit.com/en/help-center/topic-list/copy-trading |
| 4.3 | Institutional minimum track record | 5 yrs to claim; 5→10 yrs build-up | CFA Institute (GIPS) | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf |
| 5.1 | Nansen Smart Money | Labels only; **no numeric selection threshold** | Nansen | ANALYTICS-VENDOR-CONVENTION | https://docs.nansen.ai/api/smart-money |
| 5.2 | Nansen holder threshold | > $1 (was > $100, changed 27 Oct 2026) | Nansen | ANALYTICS-VENDOR-CONVENTION | https://docs.nansen.ai/api/changelog/27-10-2026-holder-minimum-1-usd.md |
| 5.3 | First funder | Earliest native-gas sender, cross-chain | Nansen | ANALYTICS-VENDOR-CONVENTION | https://docs.nansen.ai/api/profiler/address-first-funder |
| 5.4 | Chain coverage & freshness | Per-chain index start dates; look-ahead-bias note | Nansen | ANALYTICS-VENDOR-CONVENTION | https://docs.nansen.ai/api/data-coverage |
| 5.5 | Insider / sniper / first-70 | 70 buyers; "first few blocks" unquantified | GMGN | ANALYTICS-VENDOR-CONVENTION | https://docs.gmgn.ai/index/insider-traders-snipers-first-70-buyers |
| 5.6 | Birdeye Smart Money | Endpoint semantics only; no thresholds | Birdeye | ANALYTICS-VENDOR-CONVENTION | https://data.birdeye.so/docs/data-api/smart-money/index |
| 5.7 | Arkham attribution confidence | Verified ≥98% ; Prediction ≥80% | Arkham | ANALYTICS-VENDOR-CONVENTION | https://arkm.com/llms/guides/how-arkham-labels-wallets.md |
| 5.8 | CryptoQuant / Dune smart money | **Not located — excluded** | CryptoQuant; Dune | NOT-AUTHORITATIVE / NOT LOCATED | https://docs.cryptoquant.com/llms.txt |
| 5.9 | Top-10 memecoin chains | Chain-scoped meme categories, live mcap/vol | CoinGecko | ANALYTICS-VENDOR-CONVENTION | https://api.coingecko.com/api/v3/coins/categories |
| 6.1 | Wash trade | Wash result + intent; two-part test | CME Group | EXCHANGE-OR-FIRM-STANDARD | https://www.cmegroup.com/rulebook/files/cme-group-Rule-534.pdf |
| 6.2 | Fictitious trading | Definition | CFTC | REGULATORY | https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/CFTCGlossary/index.htm |
| 6.3 | Sybil attack | Academic definition | Douceur et al. (IEEE S&P 2002) | ACADEMIC-OR-PROFESSIONAL-GUILD | https://link.springer.com/chapter/10.1007/3-540-45748-8_24 |
| 6.4 | Sybil attack (plain) | Protocol glossary | Ethereum Foundation | ACADEMIC-OR-PROFESSIONAL-GUILD | https://ethereum.org/glossary/#sybil-attack |
| 6.5 | Wallet-exclusion rule for copy-trade | **No published standard** | *(none)* | NOT STANDARDISED | — |
| 6.6 | Assembled exclusion primitives | Per-vendor thresholds (98/80, 70 buyers, wash test) | *(assemblage)* | ANALYTICS-VENDOR-CONVENTION / NOT-A-STANDARD | — |
| 7.1 | Anti-survivorship (terminated portfolios) | Retain in historical performance; no retroactive restatement | CFA Institute (GIPS) 3.A.9 | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf |
| 7.2 | Theoretical performance disclosure | 4 cumulative disclosures | CFA Institute (GIPS) 4.C.48 | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf |
| 7.3 | Fair representation & full disclosure | Governing principles | CFA Institute (GIPS) | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf |
| 7.4 | Pool re-evaluation cadence | **No published cadence** | *(none)* | NOT STANDARDISED | — |
| 7.5 | Reporting granularity | Annual; corrections disclosed ≥1 year | CFA Institute (GIPS) 4.C.38 | ACADEMIC-OR-PROFESSIONAL-GUILD | https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_standards_firms.pdf |

---

## 11. Provenance of this document — what was fetched and what was inferred

**Fetched and quoted verbatim from the retrieved body (2026-11-03):**
17 CFR 275.206(4)-1 (eCFR XML, current 2026-10-29) · 17 CFR 275.204-2 (eCFR Title 17 Part 275 XML) · SEC Risk Alert "Examinations Focused on the New Investment Adviser Marketing Rule" (PDF) · SEC Small Entity Compliance Guide "Investment Adviser Marketing" · FR "Investment Adviser Marketing" 86 FR 13024 (FR API + full text) · FR "Technical Amendments to Commission Rules and Forms" 87 FR 22444 (full text) · FR rulemaking-activity API queries · FINRA Rule 2210 · FINRA Rule 2214 (both via the r.jina.ai reader proxy; direct finra.org returns 403 from this host) · NIST/SEMATECH e-Handbook §7.2.4, §7.2.4.1, §7.2.4.2 (3 pages) · CFA Institute "The Sharpe Ratio and the Information Ratio" (PDF) · CFA Institute "The Sortino Ratio" (PDF) · CFA Institute "Portfolio Performance Evaluation" refresher reading (2026) · GIPS 2020 for Firms (PDF, 146 pp) · GIPS 2020 for Asset Owners (PDF, 84 pp) · Nansen API docs (Smart Money, PnL Leaderboard, First Funder, Related Wallets, Labels, Data Coverage, 2 changelogs) · GMGN Tutorial (Insider/Sniper/First-70, Track Smart Money) · Birdeye Data docs (Smart Money API index + endpoint pages) · Arkham API guides (Labels Wallets, Addresses-Entities-Labels, API Guide, llms.txt) · CryptoQuant docs (llms.txt, catalog.json, glossary, v2 overview — **no smart-money content found**) · Dune docs (llms.txt, data catalog) · CME Group RA2008-5 / Rule 534 (PDF via reader proxy) · CFTC Futures Glossary (direct) · CFTC enforcement orders (Shinhan 2025; COFCO/Chinatex 2022) · Eth glossary · Douceur et al. sybil reprint (via reader proxy) · Springer sybil landing page (via search) · Hanley & Lippman-Hand PubMed record 6827763 · CoinGecko `/coins/categories` (777 categories) · CoinGecko `/coins/markets?category=meme-token` (250 coins) · DexScreener token-boosts API · FTMO "Trading Objectives".

**Fetched but the claim was NOT verifiable from the retrieved body (excluded from the criteria above):**
- Hanley & Lippman-Hand PDF text: the scanned reprint has **no extractable text layer**; the "rule of three" quote in §2.4 is marked PARTIAL and flagged accordingly.
- Bybit / OKX / Binance copy-trading eligibility: pages returned navigation chrome only; **no threshold asserted** (§4.2).
- CryptoQuant and Dune smart-money definitions: full documentation index and catalog searched; **zero matches**; excluded (§5.8).
- `https://www.sec.gov/investment/marketing-rule` and `https://www.sec.gov/rules-regulations/2022/03/investment-adviser-marketing-amendments-performance-disclosures`: **404** on SEC's own site; the working SEC URLs used here are the small-entity compliance guide and the Risk Alert.
- FCA cryptoasset financial-promotions guidance and the FCA Handbook: the Handbook URLs redirect to a JS home page and the guidance URLs 404 or return nav chrome only; **no FCA criterion is asserted anywhere in this file.**

**Inferred rather than fetched (each is flagged in place):**
- The NIST §2.1 arithmetic applied to the local package's own parameters (N = 617 for 55% vs 50% at α=0.05 one-sided, β=0.20, δ=0.05; 637 with NIST's continuity correction) is **this document's computation** from NIST's published formula and NIST's own worked example; NIST does not state 617. The formula was re-derived and validated against NIST's own published worked example (p₀=0.10, p₁=0.20, α=0.05 one-sided, β=0.10, δ=0.10 ⇒ 102; with continuity correction 112), which NIST's page states and which this document reproduces exactly.
- The §5.9 top-10 chain shortlist and the §9 table's "replaceable?" verdicts are **this document's analysis** of the cited sources, not statements made by any source.
- §6.6 is explicitly an **assemblage** built by this document from vendor-published components; it is not a standard.

**Explicitly NOT done:** no URL in this file was constructed from memory. Every URL above is one that was actually requested and returned a 200 (or, where noted, a 403/404 that is disclosed alongside the working substitute). No source is cited for a threshold it does not publish.
