# LeapSpace Quant — the memecoin-trader report

Generated: 2026-11-03T04:37:50+00:00

> This is the memecoin-trader half of the consolidated report. It renders artefacts already on disk. It fetched nothing, priced nothing and estimated nothing.

## WHAT THIS DOES NOT SHOW

- **Not a claim about the population of memecoin traders.** The wallets scanned are survivorship-selected: they are the ones that still hold the token. A verdict here is a verdict on those wallets, not a rate.
- **Not a complete performance record.** A per-wallet block cap means a wallet's early history may never have been priced, so its realised PnL can be incomplete.
- **Not net of costs.** Realised PnL is GROSS of gas, DEX fees and MEV.
- **Not evidence that 31 standards are applied.** 13 of them can actually reject a wallet; 3 have no published standard behind them at all.
- **Not an endorsement of any wallet.** No wallet holds WHITELISTED status in this registry.
- **Not a single consistent whitelist.** The state registry and the copy embedded in the priced-edge file disagree on which wallets they hold.
- **Not a lead-time measurement.** No wallet has been measured against a real member-count series; the series must be collected over time before that is possible.
- **Not a claim that an HTTP 200 means the data arrived.** On this host a blocked host answers HTTP 200 with an HTML block page.

The full enumerated list is in section 9.

## 1. The consistency gate

**Provenance:** `DERIVED-FROM-ARTEFACT` · **Sources:** reports\pepe_priced_edge.json

- **Wallets scored:** 15 (the file declares 15 candidates in total; `partial` = `False`)
- **Verdict distribution:** `FLUKE` 15
- **Realised PnL range:** $-55,762.77 to $146,013.44 across 15 wallet(s) · gross of gas, DEX fees and MEV - none of these are observable from ERC-20 transfers alone
- **Trades:** 236 priced, 779 unpriced, 88 closed

### Per wallet — verdict and the most decisive rejection

| Wallet | Verdict | Most decisive rejected_by test | Binding | Closed bets | Realised PnL |
|---|---|---|---|---|---|
| `0x3f9a8345729eA842708E080e238C92731e5699b8` | **FLUKE** | skill_not_distinguishable | REJECT | 1 | $81,475.35 |
| `0xbf45fB5D20BC3D0954188773e803b4E30E87E0b8` | **FLUKE** | deflated_sharpe | REJECT | 0 | $0.00 |
| `0x262190CCE7b2515FC32Aba9569E8c1cBee031CCC` | **FLUKE** | deflated_sharpe | REJECT | 0 | $0.00 |
| `0x59779b3aa3540F45b3e7255b4B5b25a8764bE686` | **FLUKE** | deflated_sharpe | REJECT | 0 | $0.00 |
| `0x72132bF09a9ee6517F3f1d997b4b3cd2115E5991` | **FLUKE** | deflated_sharpe | REJECT | 0 | $0.00 |
| `0xd4Bb423838a66347f5D6860437Cef53e540B5f13` | **FLUKE** | deflated_sharpe | REJECT | 0 | $-55,762.77 |
| `0x4879675Da42274a69F15f1cF969B2Cc6a455B7f9` | **FLUKE** | deflated_sharpe | REJECT | 0 | $0.96 |
| `0xaDFffc33cdC9970349CBcEa3D73Ec343d6ed116D` | **FLUKE** | largest_win_share | REJECT | 2 | $146,013.44 |
| `0xAf2358e98683265cBd3a48509123d390dDf54534` | **FLUKE** | largest_win_share | REJECT | 1 | $5,470.39 |
| `0xEd0203625D3Ef97f8f52AaaD9EAabacE4418cAF3` | **FLUKE** | largest_win_share | REJECT | 1 | $107,298.83 |
| `0xE8f2C2D63443A0E403ba35c95dAfe513eedBAe12` | **FLUKE** | deflated_sharpe | REJECT | 0 | $0.00 |
| `0xcbC9fAD51b83a50DbDc058704fe1355d7B13068d` | **FLUKE** | deflated_sharpe | REJECT | 0 | $0.00 |
| `0xa5F7f1dCE1D1E4c59A28668c51355CDa047D1459` | **FLUKE** | largest_win_share | REJECT | 3 | $110,286.91 |
| `0x442689F3F26cBcCc2E288DaEa986b9d67346149a` | **FLUKE** | skill_not_distinguishable | REJECT | 3 | $-0.00 |
| `0x80374c1F677FF6ae77bF3617DFB12e215741E213` | **FLUKE** | deflated_sharpe | REJECT | 0 | $0.00 |

> **Survivorship.** SURVIVORSHIP-SELECTED SAMPLE. The wallets in this file are the ones that still hold the token, so the universe contains winners by construction. Wallets that bought and then sold out entirely are absent, and a wallet that was admitted to the scan and later decayed may be missing from the screened universe. A verdict produced on this sample cannot be read as 'the gate found no good traders' - it can only be read as 'these particular wallets failed the gate'.

> **Truncation.** HISTORY MAY BE TRUNCATED. Prices are read per trade, and the per-wallet block cap limits how many distinct blocks a single wallet scan prices. Where the cap bites, the most RECENT blocks are priced and the number of blocks skipped is reported rather than hidden, so a wallet's early history can be missing from the PnL.

## 2. Criteria coverage — is each criterion enforced?

**Provenance:** `DERIVED-FROM-ARTEFACT` · **Sources:** leapspace\data\consistency_criteria.json, leapspace\edge.py, leapspace\pbo.py, leapspace\traders.py, leapspace\priced.py

The specification carries **31 criteria** and **8 fluke tests**. Against the four enforcement modules (`edge.py`, `pbo.py`, `traders.py`, `priced.py`):

- **Enforced as a gate** (a comparison that can reject a wallet): **13**
- **Enforced as a disclosure** (a required label attached to every result): 1
- **Computed but not gated:** 16
- **Not implemented at all:** 1
- **Analyst choices (no published standard):** 3 of 31

a criterion whose authority starts with NONE, or names an analyst choice, has NO published standard behind it. It is reported as an operating parameter of this package and is never presented as a published standard.

| Criterion | Threshold | Tag | Authority | Enforced | Where enforced | Gap / note |
|---|---|---|---|---|---|---|
| `min_independent_bets` | 637 | ACADEMIC-OR-PROFESSIONAL-GUILD | National Institute of Standards and Technology (NIST/SEMATECH e-Handbook of Statistical Methods) | **yes (gate)** | edge.py:evaluate_edge; edge.py:n_required_independent_bets | the code compares against 5.0 (`min_independent_bets`), not the published 637. |
| `min_independent_bets_table` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | National Institute of Standards and Technology (NIST/SEMATECH e-Handbook of Statistical Methods) | no | edge.py:n_required_independent_bets; edge.py:nist_sample_size_table; traders.py:required_sample_size | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion a sample-size table is computed and reported; it is not a rejection test on its own |
| `min_observations_for_period_statistic` | 36 | ACADEMIC-OR-PROFESSIONAL-GUILD | CFA Institute (GIPS) | **yes (gate)** | edge.py:evaluate_edge | — |
| `wilson_lower_bound_above_chance` | 0.5 | ACADEMIC-OR-PROFESSIONAL-GUILD | National Institute of Standards and Technology (NIST/SEMATECH e-Handbook of Statistical Methods) | no | edge.py:evaluate_edge; traders.py:wilson_interval | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion the Wilson interval is computed and reported, but no test compares its lower bound to the threshold, so it cannot reject a wallet |
| `bayes_posterior_prob_above_chance` | 0.95 | ACADEMIC-OR-PROFESSIONAL-GUILD | Barber, Bay & Solberg, 'Bayes Rules! An Introduction to Applied Bayesian Modeling' (CRC Press), Chapter 3 'The Beta-Binomial Bayesian Model' | **yes (gate)** | edge.py:binomial_tail_p; edge.py:evaluate_edge | — |
| `deflated_sharpe_ratio` | 0.95 | ACADEMIC-OR-PROFESSIONAL-GUILD | David H. Bailey and Marcos Lopez de Prado (Journal of Portfolio Management, forthcoming 2014; SSRN 2460551) | **yes (gate)** | edge.py:evaluate_edge | — |
| `deflated_sharpe_trial_count` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | David H. Bailey and Marcos Lopez de Prado | **yes (gate)** | edge.py:evaluate_edge; priced.py:realised_pnl_and_edge | — |
| `probability_of_backtest_overfitting` | 0.05 | ACADEMIC-OR-PROFESSIONAL-GUILD | Bailey, Borwein, Lopez de Prado & Zhu (Journal of Computational Finance, 2016; SSRN 2326253) | **yes (gate)** | edge.py:evaluate_edge; pbo.py:probability_of_backtest_overfitting | — |
| `bonferroni_alpha_per_test` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | National Institute of Standards and Technology (NIST/SEMATECH e-Handbook of Statistical Methods) | no | pbo.py:bonferroni_alpha | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion |
| `bh_fdr_procedure` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | Yoav Benjamini and Yosef Hochberg (Tel Aviv University) | no | pbo.py:benjamini_hochberg | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion |
| `multiple_testing_t_statistic_hurdle` | 3 | ACADEMIC-OR-PROFESSIONAL-GUILD | Campbell R. Harvey, Yan Liu, Heqing Zhu (Review of Financial Studies, 2016) | no | pbo.py:harvey_liu_zhu_hurdle; pbo.py:multiple_testing_t_statistic_hurdle | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion |
| `consistency_ratio` | null (no published number) | ANALYTICS-VENDOR-CONVENTION | Principal Financial Group / Marietta Board of Pensions (institutional pension plan reporting convention) | **yes (gate)** | edge.py:evaluate_edge | — |
| `min_periods_with_positive_return` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | CFA Institute (GIPS) | **yes (gate)** | edge.py:evaluate_edge | — |
| `sortino_ratio` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | CFA Institute (Deborah Kidd, CFA, Investment Performance Measurement, H17004, 2012) | no | edge.py:evaluate_edge | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion computed and reported; CFA Institute publishes the definition and no band, so there is nothing to gate on |
| `calmar_ratio` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | Anlan Wang, Ales Kresta, Tomas Tichy - Computational Management Science (Springer), open access | no | edge.py:evaluate_edge | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion computed and reported; no published band exists |
| `max_drawdown` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | CFA Institute (Refresher Reading, Portfolio Performance Evaluation, 2026 curriculum) | no | edge.py:evaluate_edge; traders.py:<module> | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion the drawdown is an input to the Calmar ratio only; traders.py declares a 0.20 ceiling in its registry but the qualification gate never checks it |
| `drawdown_duration` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | CFA Institute (Refresher Reading, Portfolio Performance Evaluation, 2026 curriculum) | no | edge.py:drawdown_duration | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion computed and reported; CFA Institute publishes no band |
| `track_record_length_minimum` | 1825 | ACADEMIC-OR-PROFESSIONAL-GUILD | CFA Institute (GIPS) and U.S. Securities and Exchange Commission | no | traders.py:<module> | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion declared in the traders.py criteria registry and never checked by the qualification gate |
| `chain_coverage_ceiling` | null (no published number) | ANALYTICS-VENDOR-CONVENTION | Nansen | no | edge.py:evaluate_edge | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion reported as a comparability caveat, explicitly not a disqualification |
| `single_trade_pnl_concentration` | null (no published number) | ANALYST-CHOICE-UNSTANDARDISED | **ANALYST CHOICE** — NONE - analyst choice (no citable authority located) | **yes (gate)** | edge.py:evaluate_edge; traders.py:qualify_wallet | — |
| `distinct_tokens_minimum` | null (no published number) | ANALYST-CHOICE-UNSTANDARDISED | **ANALYST CHOICE** — NONE for a trader threshold; the 'breadth = independent bets' concept is from Grinold via CFA Institute's 'Analysis of Active Portfolio Management' refresher reading | **yes (gate)** | edge.py:evaluate_edge; traders.py:qualify_wallet | — |
| `edge_decay_split_half` | null (no published number) | ANALYST-CHOICE-UNSTANDARDISED | **ANALYST CHOICE** — NONE for a numeric threshold; the IS/OOS degradation concept is from Bailey, Borwein, Lopez de Prado & Zhu (PBO paper, Section 3.2) | **yes (gate)** | edge.py:evaluate_edge | — |
| `posterior_split_half_stability` | null (no published number) | ACADEMIC-OR-PROFESSIONAL-GUILD | Barber, Bay & Solberg, 'Bayes Rules!' (CRC Press), Chapters 3-4 | no | edge.py:posterior_split_half_stability | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion |
| `survivorship_retention` | history retained; forward cohort only excludes | ACADEMIC-OR-PROFESSIONAL-GUILD | CFA Institute (GIPS for Firms, 2020) | **yes (gate)** | edge.py:evaluate_edge | — |
| `pre_listing_returns_excluded` | no backfilled history | ACADEMIC-OR-PROFESSIONAL-GUILD | Philippe Jorion and Christopher Schwarz (Review of Financial Studies, 2019); Rajesh K. Aggarwal and Philippe Jorion (Financial Analysts Journal, 2010) | **yes (gate)** | edge.py:evaluate_edge | — |
| `cross_chain_comparability_report` | null (no published number) | ANALYTICS-VENDOR-CONVENTION | Nansen | no | edge.py:evaluate_edge | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion reported as a comparability caveat, explicitly not a disqualification |
| `fee_basis_disclosure` | gross-of-fees preferred; net must be labelled | ACADEMIC-OR-PROFESSIONAL-GUILD | CFA Institute (GIPS for Firms, 2020) | yes (disclosure) | priced.py:realised_pnl_and_edge | DISCLOSED, not gated: the required label is attached to every result, so the criterion is satisfied on every run, but no threshold can reject a wallet on it the fee basis is disclosed on every result: gross of gas, DEX fees and MEV |
| `crypto_vendor_win_rate_band` | 0.6 | ANALYTICS-VENDOR-CONVENTION | GMGN (commercial on-chain analytics platform) | no | edge.py:evaluate_edge | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion vendor context only; never a verdict input |
| `crypto_vendor_composite_weights` | null (no published number) | ANALYTICS-VENDOR-CONVENTION | GMGN (commercial on-chain analytics platform) | no | — | NOT IMPLEMENTED: no recognisable implementation token for this criterion was found in edge.py, pbo.py, traders.py, priced.py vendor context only; never a verdict input |
| `crypto_vendor_pnl_ratio` | 1 | ANALYTICS-VENDOR-CONVENTION | GMGN (commercial on-chain analytics platform) | no | edge.py:evaluate_edge | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion vendor context only; the profit ratio is not computed here, so the band is reported and never applied |
| `vendor_label_not_a_standard` | label is context only; no threshold | ANALYTICS-VENDOR-CONVENTION | Nansen; Birdeye; GMGN | no | edge.py:evaluate_edge | computed or reported in code, but NOT enforced: no gate in the four enforcement modules can reject a wallet on this criterion a vendor label is context, never a standard, and never a verdict input |

### Fluke tests in the specification

| Fluke test | Rejects when | Threshold | Authority |
|---|---|---|---|
| `single_lucky_win_carries_pnl` | max(trade.realised_pnl) / total_realised_pnl > 0.40 (configurable) OR len(distinct tokens) == 1 | 0.4 | **ANALYST CHOICE** — NONE for the numeric threshold; the independence concept is from CFA Institute 'Analysis of Active Portfolio Management' (2026) and Grinold (1989) |
| `win_rate_indistinguishable_from_chance` | wilson_lower_bound_above_chance fails OR bayes_posterior_prob_above_chance < 0.95 OR n_independent_bets < n_required_independent_bets | 0.95 | NIST/SEMATECH e-Handbook; Barber, Bay & Solberg 'Bayes Rules!' |
| `sharpe_inflated_by_selection` | deflated_sharpe_ratio < 0.95 OR probability_of_backtest_overfitting > 0.05 OR the trial count N is unknown | 0.95 | Bailey & Lopez de Prado; Bailey, Borwein, Lopez de Prado & Zhu |
| `edge_decays` | recent half's mean realised PnL per trade is materially worse than the early half's, OR the posterior P(theta>0.5) computed on the early half falls materially below that computed on the full history | 0.5 | **ANALYST CHOICE** — NONE for the numeric threshold; the degradation concept is from the PBO paper |
| `no_independent_bets` | the wallet's trades are all one token, OR the count of non-overlapping independent bets is below the NIST requirement, OR fewer than 36 return observations exist | 36 | NIST; CFA Institute (GIPS and Refresher Reading); GMGN (vendor) |
| `survivorship_selected_universe` | the pool's reported history omits wallets that were admitted and later decayed, OR the screened universe's results are not published alongside the selected wallet's | history retained; universe disclosed | CFA Institute (GIPS); U.S. SEC; FINRA |
| `backfilled_or_pre_listing_performance` | any performance record contains observations before the wallet's first observed on-chain activity, or any vendor-supplied history row is carried forward across a dormant period | no pre-listing performance | Jorion and Schwarz (Review of Financial Studies, 2019); Aggarwal and Jorion (Financial Analysts Journal, 2010) |
| `insufficient_history` | the wallet has no closed trades, or the trades cannot be priced (win count unknown), or the per_day return series is empty | 0 | JAMA (Hanley & Lippman-Hand) |

## 3. The whitelist

**Provenance:** `DERIVED-FROM-ARTEFACT` · **Sources:** leapspace\state\whitelist.json, reports\pepe_priced_edge.json

- **Entries:** 2 · **Events:** 3 · **Rejected candidates retained:** 2
- **By status:** `WHITELISTED` 0, `WATCH` 0, `FLUKE` 1, `RETIRED` 1
- **Candidates examined (the N the Deflated Sharpe is corrected for):** 1
- **Copies:** the state registry holds 2 entr(ies); the copy embedded in the priced-edge file holds 11. the state registry and the copy embedded in the priced-edge file DISAGREE on which wallets they hold. The state registry is the live record and is what is tabulated below; the embedded copy is the snapshot the last gate run wrote. A disagreement means one of them is stale, and neither can be preferred without saying which run produced it.

this is the N the Deflated Sharpe is corrected for: the number of candidate wallets that were screened before this one was chosen. An unknown N is treated as an automatic rejection of the selection-bias test, not as N=1.

| Wallet | Status | Last verdict | Closed trades | Skill p | Deflated Sharpe | Trials scanned |
|---|---|---|---|---|---|---|
| `ethereum:0xbad` | **FLUKE** | FLUKE | 1 | 1.0 |  | 1 |
| `ethereum:0xgood` | **RETIRED** | FLUKE | 80 | 4.290279933524806e-06 | 3.2229774404868294e-13 | 1 |

### Promotions (1)

- `ethereum:0xgood` — edge verdict CONSISTENT: edge survives the fluke tests at 1 trial(s) scanned; 80 closed trades, 80 independent bets, skill p=0.9908419512415418

### Retirements (1)

- `ethereum:0xgood` — retired: no longer qualifying - rejected by: skill_not_distinguishable, deflated_sharpe

### Rejections (2)

- `ethereum:0xbad` — rejected by: largest_win_share, deflated_sharpe (also insufficient: min_observations_for_period_statistic, insufficient_independent_bets, single_token_only, too_few_closed_trades)
- `ethereum:0xgood` — rejected by: skill_not_distinguishable, deflated_sharpe

> a retired or rejected wallet leaves the forward cohort and its history is RETAINED (CFA Institute GIPS 3.A.9), so the scan's selection bias stays visible instead of being edited away.

## 4. The historical price method

**Provenance:** `DERIVED-FROM-ARTEFACT` · **Sources:** leapspace\priceatblock.py, reports\pepe_priced_edge.json, README.md, reports\probe_pool_vs_llama.json

Uniswap V2 pair reserves read at each trade's own block, via a keyless archive RPC. The package asks the V2 factory, AT that block, which pair existed for (token, USDC), then reads that pair's getReserves() at the same block and takes reserve(quote) / reserve(token) with decimals applied. A token whose deep pair is quoted in WETH is priced in WETH and multiplied by the WETH/USD price read from the deep WETH/USDC pair at the same block. No price API is required for the pool route.

- **Liquidity floor:** a stable-quote pair must hold at least `10_000.0` quote units and a WETH-quote pair at least `30.0` WETH; below that the pair is REJECTED (`insufficient_liquidity`) and the price is reported as unavailable. a pair whose quote side holds less than the floor is REJECTED and the price is reported as unavailable rather than as a number, so a nearly-empty pool cannot manufacture a price
- **Per-wallet block cap:** `40` distinct blocks per wallet scan. the cap limits how many DISTINCT blocks one wallet scan prices. When it bites, the most RECENT blocks are priced - those are the trades that decide whether the wallet has a live edge - and the number of blocks NOT priced is reported rather than hidden. A wallet's EARLY history can therefore be missing from its realised PnL, and its PnL can be incomplete without the PnL itself being wrong.
- **Fee basis:** the realised PnL is GROSS of gas, DEX fees and MEV. None of those are observable from ERC-20 transfers alone, so a net figure would need per-swap gas and fee logs. Every PnL number in this report is on that gross basis.

### Measured against DefiLlama's historical index

| Token | Date | Pool price | Reference index | Error |
|---|---|---|---|---|
| PEPE | 2024-01-01 | $1.2370e-06 | $1.2900e-06 | 4.1% |
| PEPE | 2025-01-01 | $1.8291e-05 | $1.9840e-05 | 7.8% |
| PEPE | 2023-06-01 | $1.6065e-06 | $1.2600e-06 | 27.5%— the pool was new and shallow |
| SHIB | 2024-01-01 | $9.7679e-06 | n/a | n/a— no reference figure or error percentage is recorded for this row, so none is stated here |

the pool-derived price is compared against DefiLlama's historical index price. The percentage errors above are the measured ones recorded in the package README's verification table; the third row is large because the pool was new and shallow, which is exactly the case the liquidity floor targets.

**Provenance of these figures:** 4 of 4 rows were found verbatim in the package README's verification table on disk. A row that was not found there is reported as not found rather than asserted.

An independent on-disk probe (`reports\probe_pool_vs_llama.json`) compared the pool-derived price with the reference at 7 fixed blocks: the largest absolute error was 1.0% and the median was 0.1%.

## 5. The new-meme path — the launch-window scan

**Provenance:** `DERIVED-FROM-ARTEFACT` · **Sources:** reports\launch_scan.json

- **Token:** `0x93025BB139fa2756A6130De833df9D07bBD2E3b1` (ethereum)
- **Launch:** block 26327462, deployer `0x2F0F35765563Ba038BA80ffB80d76Eb6106B946A`
- **Window:** 1000 blocks
- **Buyers inside the window:** 2 (candidates scanned: 2)
- **DEPLOYER FOUND IN THE WINDOW:** **YES**

> THE DEPLOYER WAS FOUND INSIDE THE LAUNCH WINDOW - the deployer address appears among the wallets that bought within the window. That is a positive insider-detection result: the deployer took its own token.

| Buyer | Deployer? | Entry lag (blocks) | Entry class | Edge verdict | Skill p | Independent bets |
|---|---|---|---|---|---|---|
| `0x2F0F35765563Ba038BA80ffB80d76Eb6106B946A` | **YES** | 0 | sniper (<10 blocks) | **FLUKE** | 0.5 | 1 |
| `0x211D2FfE82fe134571F031850703041752EFCE49` | no | 20 | very early (<100 blocks) | **FLUKE** | 0.5 | 1 |

> Only buyers INSIDE the window are listed. A wallet that bought after it is not an early buyer and is not here.

## 6. Social edge — the narrative cohort

**Provenance:** `DERIVED-FROM-ARTEFACT` · **Sources:** leapspace\state\narrative_cohort.json, leapspace\state\social_series\ethereum_0x240D6FAF8c3B1A7394e371792A3bf9D28DD65515.json, leapspace\state\social_series\ethereum_0xA35923162C49cF95e6BF26623385eb431ad920D3.json, leapspace\state\social_series\ethereum_0xC4441c2BE5d8fA8126822B9929CA0b81Ea0DE38E.json, leapspace\state\social_series\ethereum_0xb131f4A55907B10d1F0A50d8ab8FA09EC342cd74.json, leapspace\state\social_series\solana_DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263.json, leapspace\state\holder_series\solana_DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263.json

- **Cohort:** 20 stored snapshot(s), 36 distinct mint(s), largest snapshot 6 rows
- **Narrative specificity split:** 9 niche / 27 generic (distinct mints across all stored snapshots, counted from the is_niche flag each row carries)
- **Community-size series stored:** 6 (6 with member counts that do not move across their snapshots)

| Series | Chain | Snapshots | Span (s) | Telegram | Discord | Holders | Counts move? |
|---|---|---|---|---|---|---|---|
| `leapspace\state\social_series\ethereum_0x240D6FAF8c3B1A7394e371792A3bf9D28DD65515.json` | ethereum | 4 | 424 | 2013 |  |  | no |
| `leapspace\state\social_series\ethereum_0xA35923162C49cF95e6BF26623385eb431ad920D3.json` | ethereum | 4 | 423 |  | 236 |  | no |
| `leapspace\state\social_series\ethereum_0xC4441c2BE5d8fA8126822B9929CA0b81Ea0DE38E.json` | ethereum | 4 | 424 | 16803 | 20021 |  | no |
| `leapspace\state\social_series\ethereum_0xb131f4A55907B10d1F0A50d8ab8FA09EC342cd74.json` | ethereum | 4 | 424 |  | 132347 |  | no |
| `leapspace\state\social_series\solana_DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263.json` | solana | 7 | 6699 | 11004 | 32581 |  | no |
| `leapspace\state\holder_series\solana_DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263.json` | solana | 3 | 0 |  |  | 2101361 | no |

### Measured lead times

**NO WALLET HAS YET BEEN MEASURED AGAINST A REAL MEMBER-COUNT SERIES. No artefact on disk records a lead time between a wallet's buy and a community-size event.**

A member-count series only becomes a SERIES over time: the endpoints expose the CURRENT count, so the series has to be sampled repeatedly, and a lead time needs at least two observations that bracket the wallet's purchase. The stored series cover minutes, not days, and their member counts do not move, so no threshold crossing can be located inside them. Until the series has been collected over a real interval, the honest answer is NOT YET MEASURABLE - not 'no effect' and not a lead time computed from a flat line.

the specificity score is a weighted classifier over free signals that separate a community footprint from a trend clone. Its weights and keyword list are analyst choices and are re-scorable; it measures the PRESENCE of a community footprint, not attention, sentiment or community size.

## 7. The keyed source — the Etherscan adapter

**Provenance:** `DERIVED-FROM-ARTEFACT` · **Sources:** leapspace\etherscan.py, leapspace\priced.py

### Free tier

| Action | Note |
|---|---|
| `account.tokentx` | OK - ERC-20 transfers (1,000 per page) |
| `account.txlist` | OK - transactions |
| `account.tokenbalance` | OK - one address's ERC-20 balance |
| `account.balancemulti` | OK - up to 20 addresses' ERC-20 balances |
| `account.balance` | OK - native balance |
| `contract.getsourcecode` | OK - verified source, compiler, proxy |

### Pro-only

| Action | Note |
|---|---|
| `token.tokenholderlist` | PRO ONLY - returns NOTOK |
| `token.tokeninfo` | PRO ONLY - returns NOTOK |

- **Error convention:** Etherscan signals failure in the JSON BODY, not the HTTP status. A bad key, a bad parameter and a rate limit all return HTTP 200 with {"status":"0","message":"NOTOK"}. Every response must therefore be checked for status == "1"; an HTTP 200 is never proof of data.
- **URL separator rule:** the DefiLlama historical-price endpoint separates chain from token with a COLON: https://coins.llama.fi/prices/historical/{unix_ts}/{chain}:{token}. The comma form returns {"coins": {}} and looks like a dead endpoint - it is not.
- **Key handling:** the key is read from the environment at call time. It is never a literal in source, never written into any artefact, report, chart or log, and no fingerprint or hash of it is produced. This section reports only WHETHER one is configured, never its value.
- **Key configured in this environment:** yes (presence only — the value is never read, printed, hashed or written to any artefact; presence was read through the package's own accessor, which returns a boolean)
- **Holder list:** Etherscan's own tokenholderlist action is Pro-only and returns NOTOK on the free tier, so it is not used. Holder balances are read with the free-tier balance actions, or reconstructed by netting the token's transfer tape.

## 8. The free-data catalogue

**Provenance:** `DERIVED-FROM-ARTEFACT` · **Sources:** data\free_data_sources.json

- **Sources live-probed:** 156
- **Verified OK:** 67 (recomputed from the file: 67)
- **Need a key:** 30 (recomputed: 30)
- **Usable as a fallback:** 51
- **Catalogue generated:** 2026-11-03T02:09:34.907081+00:00

**Live status counts:** `conn_fail` 2, `dns_fail` 3, `error` 3, `http_400` 1, `http_401` 10, `http_402` 3, `http_403` 8, `http_404` 56, `http_429` 1, `http_503` 1, `http_525` 1, `ok` 67

### Host-level traps that change how results must be read

- **URL filter:** The host sits behind a Sangfor NGAF URL filter. Blocked hosts are answered with HTTP 200 + an HTML block page, so a status code alone is not proof of data. See tools/freeprobe/validate.py.
- **TLS:** api.coingecko.com fails the TLS handshake (WinError 10054) from this host; pro-api.coingecko.com and www.coingecko.com answer normally.
- **path:** All reddit.com .json paths return HTTP 403; .rss works.
- **CA bundle:** certifi's CA bundle is required - the Windows CA store mis-validates some chains (valid Let's Encrypt certs read as expired). leapspace/http.py already builds the context with certifi.where().
- **widget:** The widget endpoint only returns data for guilds that have the widget enabled.
- **HTTP 200 + NOTOK — `Etherscan API V2 tokenholderlist`:** Live probe with NO key returned HTTP 200 whose body was {status:'0', message:'NOTOK', result:'Missing/Invalid API Key'}. Etherscan signals failure in the JSON body, not the HTTP status - the caller must check body['status']. A placeholder key produced the same NOTOK payload. Chains 56/8453/10/100 answered 'Free API access is not supported for this chain'; chains 534352/324/81457/25/31 answered 'Missing or unsupported chainid'.
- **docs page at a JSON path — `ApeWisdom v1.0 JSON API`:** Live probe returned HTTP 200 application/json with {count:640, pages:7, current_page:1, results:[{rank, ticker, name, mentions, upvotes, rank_24h_ago, mentions_24h_ago}]}. CRITICAL PATH NOTE: the commonly quoted '/api/' and '/api/top-tokens/' return the DOCS HTML page with HTTP 200 - a silent false positive. The working path is '/api/v1.0/filter/{filter}' (filters: all, all-stocks, crypto). The 'crypto' filter probed empty (count:0), so use 'all'.
- **403 on .json — `Reddit public JSON`:** CONFIRMED BLOCKED from this host: HTTP 403 with a 189,908-byte Cloudflare/Reddit block page ('You've been blocked by network security'). The same 403 came back for old.reddit.com, oauth.reddit.com, api.reddit.com, www.reddit.com/search.json and a deep-link comments .json. ALL .json paths are blocked.
- **.rss works — `Reddit public RSS (WORKS where .json is blocked)`:** THE WORKING REDDIT PATH. Live probe returned HTTP 200 with an Atom feed (12,878 bytes, title 'newest submissions : CryptoCurrency'). NOTE /r/wallstreetcoins/top.rss returned HTTP 404 with feed title 'WallStreetCoins: banned' - the subreddit is banned, and RSS reports that as 404 rather than 403.
- **TLS handshake failure — `CoinGecko public API (api.coingecko.com)`:** IMPORTANT HOST FACT: api.coingecko.com is UNREACHABLE from this host. Four separate live probes all failed with ConnectionResetError (WinError 10054) during the TLS handshake, and the raw TLS handshake to the resolved Cloudflare IPs (104.20.41.132, 172.66.172.219) fails the same way. Plain HTTP does not help - it 302s to the local URL filter at 192.168.8.1/urlfilter and returns a 'Sangfor NGAF' block page WITH HTTP 200 (a false positive). pro-api.coingecko.com answers normally (HTTP 401 'API Key Missing') and www.coingecko.com answers (HTTP 404 on API paths), so the block is hostname-specific. Do not treat any 200 from this host as CoinGecko data.

> a status code alone is not proof of data on this host. A blocked host can answer HTTP 200 with an HTML block page, a JSON endpoint can answer HTTP 200 with an API-level error, and a docs page can answer HTTP 200 at a path that is supposed to return JSON. Every count below is therefore reported with the shape of the response, not just its status.

## 9. Gaps — what this report does NOT show

**Provenance:** `DERIVED-FROM-ARTEFACT` · **Sources:** no source file

**16 enumerated gap(s).**

1. **consistency gate — survivorship-selected-sample.** The wallets scored are the ones that still hold the token. Wallets that bought and sold out entirely are absent, so the sample cannot show what fraction of the universe is skilled. _To close it: a scan over a published, non-survivorship-selected wallet universe with the admission rule recorded_
2. **consistency gate / price method — price-cap-truncates-history.** The per-wallet block cap means a wallet's early history may not be priced at all, so its realised PnL can be incomplete. The blocks skipped are reported, but the un-priced history is gone. _To close it: an uncapped per-wallet price pass, or a per-wallet record of which blocks were skipped and why_
3. **consistency gate — gross-of-fees-pnl.** Realised PnL is GROSS of gas, DEX fees and MEV. None of those are observable from ERC-20 transfers alone, so every PnL figure overstates what a wallet kept. _To close it: per-swap gas and fee logs, joined to the transfer tape_
4. **criteria coverage — criteria-not-implemented.** These criteria in the specification have no implementation token in the four enforcement modules: crypto_vendor_composite_weights. _To close it: an implementation in edge.py, pbo.py, traders.py or priced.py_
5. **criteria coverage — criteria-computed-not-gated.** These criteria are computed or reported but CANNOT reject a wallet, so their presence in the code is not evidence that the standard is applied: min_independent_bets_table, wilson_lower_bound_above_chance, bonferroni_alpha_per_test, bh_fdr_procedure, multiple_testing_t_statistic_hurdle, sortino_ratio, calmar_ratio, max_drawdown, drawdown_duration, track_record_length_minimum, chain_coverage_ceiling, posterior_split_half_stability, cross_chain_comparability_report, crypto_vendor_win_rate_band, crypto_vendor_pnl_ratio, vendor_label_not_a_standard. _To close it: a gate that compares the quantity against the threshold_
6. **criteria coverage — analyst-choice-thresholds.** 3 of the 31 criteria have NO published standard behind them. Their thresholds are this package's operating choices. _To close it: a published source, or the explicit acceptance that the number is an analyst choice_
7. **criteria coverage — enforced-value-differs-from-published.** For these criteria the gate compares against a different number from the one the specification publishes: min_independent_bets. The published threshold is in the table; the value the code actually applies is named beside it. _To close it: aligning the gate's threshold with the published one, or recording the substitution as an analyst choice_
8. **whitelist — no-whitelisted-wallet.** No wallet holds WHITELISTED status. The forward cohort is empty, so this package has not identified a consistently profitable memecoin trader. _To close it: a wallet that passes every hard gate with a non-trivial sample_
9. **whitelist — whitelist-copies-disagree.** The state whitelist registry and the whitelist embedded in the priced-edge result file hold different sets of wallets, so one of them is stale. The report cannot say which without knowing which run produced each. _To close it: re-running the gate so both copies are written by the same run, or recording the run identifier in each_
10. **price method — price-accuracy-not-uniform.** The measured error against the reference index ranges from a few percent to roughly a quarter on a young, shallow pool. The price is the price of the pool the wallet traded, which is not always the price of the token. _To close it: a depth-weighted reference price, or the liquidity depth at each trade's block reported beside the price_
11. **launch scan — one-launch-window-only.** The scan covers ONE token over ONE window of 1000 blocks, with 2 buyer(s) inside it. That is a case study, not a rate. _To close it: the same scan run over a large, published set of launches_
12. **launch scan — launch-window-buyers-only.** Only buyers INSIDE the window are listed. A wallet that bought after the window is not an early buyer and is not in this file, so the file cannot be read as the set of buyers of the token. _To close it: the full buyer set with entry lags, or an explicit statement of the screened universe_
13. **social edge — no-lead-time-measured.** No wallet has been measured against a real member-count series, so no lead time is reported. The series must be collected over time before a lead time can mean anything. _To close it: a member-count series spanning days around a wallet's purchase_
14. **social edge — specificity-classifier-is-a-heuristic.** The narrative specificity score is a weighted classifier over free signals whose weights and keyword list are analyst choices. It measures the presence of a community footprint; it does not measure attention, sentiment or size, and it is not a forward test of the paper's outperformance claim. _To close it: two cohort snapshots separated in time and a forward-return test on them_
15. **keyed source — pro-only-actions-unavailable.** The Etherscan holder-list and token-info actions are Pro-only, so on the free tier the holder set is reconstructed from the transfer tape rather than read from the vendor. _To close it: a Pro subscription, or a full transfer tape for the token_
16. **free-data catalogue — http-200-is-not-data.** On this host a blocked host can answer HTTP 200 with an HTML block page, and a JSON endpoint can answer HTTP 200 with an API-level error. Counts of 'working' sources are therefore counts of well-shaped responses, not of reachable data. _To close it: response-shape validation on every probe, which the catalogue partly does but not for every host_

---

*Produced by an automated research system from artefacts on disk. Not investment advice. A CONSISTENT verdict would mean the hypothesis survived the gates that ran — nothing more.*