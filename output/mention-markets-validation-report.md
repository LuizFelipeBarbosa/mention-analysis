# Mention-market validation report

**Date:** 2026-10-02
**Scope:** the repository copies and published versions of [Political Mention Market Calibration](https://lfpmb.com/articles/political-mention-market-calibration) and [Cross-Category Calibration Analysis](https://lfpmb.com/articles/cross-category-calibration-analysis), both original Jupyter notebooks, the broad T7 snapshot, and the refreshed Trump audit at `/Volumes/T7/mention-markets/longshot-audit/2026-10-02-validation`. The prior `/2026-09-04` audit is retained for comparison.

## Verdict

The essays need revision before they are used as current research or as evidence for a deployable trading strategy.

The independent Trump check gives a mixed result:

- **Low side:** supported, but smaller than in the first audit. In the refreshed audit, contracts at a 2-hour VWAP of 25–35% resolved YES **24.51%** of the time against a mean implied probability of **29.94%**, a **−5.43 percentage-point** error. A speech-level cluster bootstrap gives a 95% interval of **−9.78 to −1.07 pp**.
- **High side:** not established in the refreshed audit. Contracts at 70%+ resolved YES **81.07%** against a mean implied probability of **81.13%**, a **−0.06 pp** error. The cluster-bootstrap interval is **−4.18 to +3.53 pp**, so it includes calibration and both directions of error.
- **Snapshot sensitivity:** the older broad T7 snapshot still shows a much larger high-side gap: 70%+ contracts were 91.86% YES against 83.65% mean implied probability (**+8.20 pp**, 1,719 contracts, 232 events). That difference is why the published “70% or above happens much more than 70%” statement should be labeled historical and snapshot-sensitive rather than a persistent current fact.

The defensible conclusion is: **Trump mention markets show a reproducible low-probability overestimation around 30% in the newest audit; the favorite-side effect is positive in the older snapshot but does not replicate reliably in the newest one.**

## Evidence and denominators

The audit separates two data layers so that historical essay numbers are not silently mixed with newer observations.

| Evidence layer | Coverage | Key counts | Use |
|---|---|---:|---|
| Broad loader over `/Volumes/T7/mention-markets` | Raw metadata through 2026-08-08; valid VWAP rows through 2026-07-05 | 38,450 raw markets; 36,214 resolved; 20,979 valid 2-hour VWAP rows; 143 raw series values | Reconcile cross-category claims and the repository pipeline |
| Trump audit `/longshot-audit/2026-10-02-validation` | Collection finished 2026-10-02; trade tape through 2026-10-01 22:51:26 UTC | 9,334 market rows; 8,926 resolved non-DNQ rows; 5,012,511 trade rows; 14,433 decision rows; 152 events | Primary current Trump calibration check |

The count in a report must identify its grain. The project contains raw markets, resolved markets, markets with trades, valid-VWAP contracts, trade rows, and duplicated trade positions. These are different denominators.

## Claim-by-claim findings

| Claim in the essays | Status | What the audit found | Required fix |
|---|---|---|---|
| Political universe = 7,320; Trump = 3,401 | **Historical / stale** | These values match the original political notebook's executed snapshot. The current broad valid-2-hour universe has 10,271 Politicians rows; the canonical broad Trump subset has 6,352 valid 2-hour rows across 260 events. | Put the snapshot date and file manifest beside every headline count. Recompute from a canonical universe. |
| Cross-category universe = 18,948 from 35,837 raw and 33,587 resolved | **Historical / stale** | The original notebook output is reproducible as a historical result. The current broad loader has 38,450 raw rows, 36,214 resolved rows, and 20,979 rows with a valid 2-hour VWAP. | Publish raw, resolved, traded, and valid-VWAP counts separately. |
| Trump is the exact series `KXTRUMPMENTION` | **Incorrect filter** | Current broad metadata stores Trump contracts under `KXTRUMPMENTION` (4,812 rows), `A` (1,267), and `B` (460). Exact-series filtering misses the latter 1,727 rows; the canonical ticker-prefix universe has 6,745 raw rows. | Select by a maintained ticker-prefix/universe map and print a series audit every run. |
| Around 30% is overestimated | **Supported with caveat** | Refreshed audit, 2-hour 25–35% band: 461 contracts, 124 events, mean p 29.94%, YES 24.51%, error −5.43 pp, bootstrap −9.78 to −1.07 pp. | Keep the 25–35% definition, report mean p rather than the bucket midpoint, and cluster uncertainty by event. |
| 70%+ happens much more than 70% | **Not established in newest audit** | Refreshed audit, 2-hour 70%+ band: 803 contracts, 131 events, mean p 81.13%, YES 81.07%, error −0.06 pp, bootstrap −4.18 to +3.53 pp. The older broad snapshot is +8.20 pp. | Reword as “observed in the older snapshot; not replicated in the refreshed audit” until a frozen holdout confirms it. |
| Overall MAD = 5.35 pp; recent eight weeks = 3.26 pp | **Metric interpretation error** | The political notebook computes cumulative weekly MAD snapshots and then averages selected snapshots. That is not a single contract-level overall MAD, and “recent eight weeks” is not a cohort whose contracts all closed in the last eight weeks. | Call it mean cumulative weekly MAD, or replace it with cohort-by-close-week calibration. |
| Median settlement lag = 71 minutes | **Timestamp and denominator issue** | The old metric is `close_time - last_trade_time`, with negative values excluded from the displayed positive-lag denominator. The refreshed audit contains a separate `settlement_ts`; its nonnegative `settlement_ts - close_time` median is 30.2 minutes, with 17.4% over one hour and 8.5% over four hours. | Use `close_time` for trading cessation, `settlement_ts` for payout timing, and show missing/negative cases. See Kalshi's [market API definition](https://docs.kalshi.com/api-reference/market/get-market) and [timeline and payout guidance](https://help.kalshi.com/en/articles/13823825-timeline-and-payout). |
| Every category improves monotonically toward the final horizon | **Unsupported generalization** | Horizon samples have different denominators. The refreshed Trump table is not monotone: the 25–35% error is −5.43 pp at 2h, −4.98 pp at 6h, and −6.49 pp at 12h; 70%+ is −0.06 pp at 2h, −1.55 pp at 6h, and −3.08 pp at 12h. | Report n, event counts, and uncertainty for every horizon and test a pre-specified trend on comparable contracts. |
| +5.0¢ YES and +14.1¢ NO are pooled per-trade results | **Incorrect aggregation** | The original subgroup/category summaries average group-level PnL means while displaying summed trade counts. That is not total PnL divided by total eligible contracts. | Aggregate total net PnL and total eligible contracts at the contract/trade grain; report equal-group means separately. |
| Positive fee-adjusted backtests imply a tradeable edge | **Not established** | Current broad in-sample accounting is positive (YES >70: +5.13¢/contract over 7,313; NO <50: +12.42¢ over 10,158), but it assumes retrospective VWAP fills. In the newer Trump 2-hour split, fixed YES >70 is −2.38¢/trade in train and +2.81¢ in test; NO <40 is +3.34¢ and +2.33¢. | Freeze thresholds before evaluation, use chronological event splits, and model fills, available size, spread, slippage, and event-level drawdowns. |
| Learning, liquidity, and asymmetric information explain the pattern | **Hypotheses only** | Calibration results establish association, not mechanism or causality. | Reword causal prose as hypotheses and add liquidity, participation, event type, and time controls before testing mechanisms. |

## Corrected broad cross-category profile

This table uses the current broad loader, canonicalizes Trump by ticker prefix, requires a valid 2-hour VWAP, and computes MAD from each bucket's mean implied probability rather than its fixed midpoint.

| Category | Valid 2h contracts | YES rate | Directional accuracy | Corrected MAD |
|---|---:|---:|---:|---:|
| Earnings | 2,118 | 57.37% | 88.48% | 12.17 pp |
| Entertainment | 1,228 | 32.33% | 92.59% | 16.50 pp |
| Finance | 559 | 39.00% | 86.58% | 11.58 pp |
| Media/News | 757 | 40.82% | 83.49% | 10.78 pp |
| Other | 663 | 41.03% | 86.58% | 12.78 pp |
| Politicians | 10,271 | 44.05% | 82.84% | 8.60 pp |
| Sports | 5,383 | 52.03% | 87.29% | 11.95 pp |

The old article's category values are therefore not a current release. The current map leaves 663 valid 2-hour rows in `Other`; the leading unmapped series include `KXSTARMERMENTION`, `KXBILATERALMENTION`, and `KXJOHNSONMENTION`. Those rows should be explicitly mapped or reported as unmapped rather than silently treated as a meaningful category.

## Interpretation

The refreshed Trump audit gives a narrower result than the essays state. Low-probability YES contracts are still overestimated around 30% at the 2-hour horizon. That is consistent with a low-side long-shot bias, although the gap is smaller than in the first audit. The corresponding favorite-side statement is not confirmed: the 70%+ result is effectively calibrated at 2 hours and the event-cluster interval includes zero. The older broad snapshot's +8.2 pp high-side estimate is useful historical evidence, but the snapshot difference means it should not be presented as a persistent live effect.

## Methodology and visual audit

The notebook code now aligns the statistic and the chart with the question being asked:

- **VWAP definition.** Each horizon is a cumulative volume-weighted average of all trades at or before `last_trade_time - horizon`; it is not a trailing-window VWAP over the preceding horizon. It is a historical trading-stop benchmark. It is not a price before Trump spoke, not a settlement-time VWAP, and not proof that a trader could fill that size at that price. If a trailing-window VWAP is intended, the SQL needs both lower and upper time bounds and the whole analysis must be recomputed.
- **Calibration x-axis.** The x-coordinate is the mean observed implied probability within each bucket. Fixed bucket midpoints remain labels only. The calibration charts use a numeric 0–100% x-axis and a true 45-degree reference line; the prior categorical bucket-index graphics could make the spacing look uniform even when the observed prices were not centered in the buckets.
- **MAD chart.** Horizon labels run from longer lookback to shorter lookback without reversing the axis. The title and x-axis explicitly say “final recorded trade,” so the chart is not mistaken for time before speech or settlement.
- **VWAP traces.** The spaghetti chart is retained as a diagnostic of per-contract paths. It is not a time-aligned event trajectory: contracts have unequal available horizons and different event timing. Numeric calibration tables and bucket plots carry the inferential result.
- **Time-over-time chart.** Weekly curves use cumulative, trade-position-weighted observations from both sides of trades. They are descriptive snapshots with repeated and correlated positions, not independent contract-level measurements.
- **Strategy charts.** Category heatmaps remain exploratory. Pooled summary tables now compute total net PnL divided by total eligible contracts, while the Trump audit uses event-clustered uncertainty and a chronological split.

## Method issues and repairs

### 1. Snapshot drift

The essays describe a January 2025–March 2026 analysis, while the current broad T7 files and the October Trump audit contain later data and different market coverage. Re-running code against a changed drive cannot validate an old headline without the original manifest.

**Repair:** save a manifest containing file paths, hashes, schema, API cutoff, timezone, and code version. Store the manifest beside every report.

### 2. Universe and join logic

The `series` field is not stable enough to identify the Trump universe in the current files. `A` and `B` are valid Trump rows, and the newer audit's explicit universe is `KXTRUMPMENTION` plus `KXTRUMPMENTIONB`.

**Repair:** identify the universe by canonical ticker prefix, join `event_ticker`, and maintain a versioned series-to-category mapping. Print unmapped values and counts.

### 3. Calibration reference probability

The original `calibration_buckets` function compared each bucket's observed rate with a fixed midpoint. If observations cluster near one edge of a bucket, midpoint error is not calibration error.

**Repair implemented:** `src/metrics.py` now records `mean_implied_pct` and `compute_mad` uses it by default; `midpoint` remains available for chart labels and backward-compatible plotting.

### 4. Correlated observations

Twenty contracts from one speech are not twenty independent tests. The essays mostly count contracts and trades, which overstates inferential precision.

**Repair:** use `event_ticker` as the resampling unit. The consolidated notebook reports event counts and event-cluster bootstrap intervals for the key bands.

### 5. Timestamp semantics

The loader's `last_trade_time` anchor is appropriate for a question framed as “N hours before trading stopped.” It should not be called a settlement timestamp. The newer audit provides `settlement_ts`, allowing trading cessation and payout timing to be analyzed separately.

**Repair:** name timestamps by their operational meaning, report both lags, and do not use payout lag to infer price information timing.

### 6. In-sample strategy evaluation

The original threshold tables use the same data to observe the calibration pattern and to score the strategy. Retrospective VWAP is also not a guaranteed fill.

**Repair:** pre-specify the primary horizon and thresholds, split by event date, evaluate once on a later holdout, and add an executable fill model. Report total PnL, total wagered, net return, per-contract PnL, fills, and event-level worst loss.

### 7. Pooled PnL aggregation

A mean of subgroup means gives every subgroup equal weight, even when their contract counts differ. Pairing that mean with a summed contract count produces a mislabeled “per-trade” statistic.

**Repair:** sum net PnL and divide by the sum of eligible contracts. Keep macro-average and micro-average metrics under separate names.

### 8. Horizon comparisons

The horizon columns do not have a common contract set. Markets without an early trade have null VWAPs, so later horizons can be selected samples. A visual decline in MAD is not enough to claim monotonic information arrival.

**Repair:** report horizon-specific coverage, use paired contracts for within-market comparisons, and test trend differences with event-aware uncertainty.

## Changes made in this repository

- `src/data_loading.py` now expands parquet files explicitly and ignores macOS `._*.parquet` sidecars, preventing invalid-file failures on T7.
- `src/metrics.py` now preserves bucket midpoints for display while calculating MAD from the within-bucket mean implied probability.
- `src/plotting.py` now uses within-bucket mean probabilities on numeric calibration axes, labels the final-trade VWAP anchor, preserves the intended horizon order, and documents the diagnostic limits of trace plots.
- `scripts/refresh_trump_audit.py` refreshes a new timestamped Trump snapshot from Kalshi's public market/trade endpoints, records API cutoffs and hashes, and writes no orders.
- The two original notebooks now use ticker-prefix categorization, within-bucket mean probabilities, corrected chart axes/labels, trade-weighted pooled strategy summaries, and explicit methodological limitations; they still link to the consolidated audit as the canonical current result.
- The earlier Trump-focused notebook and correction note are explicitly labeled historical comparisons and no longer present their broad-snapshot favorite-side result as current evidence.
- `output/mention-markets-validation-consolidated.ipynb` is an executed, top-to-bottom notebook containing provenance, data-quality checks, Trump calibration, event-cluster bootstrap, recency and horizon sensitivity, cross-category recalculation, strategy audit, and the claim ledger.
- `output/mention-markets-validation-consolidated.md` is the rendered Markdown companion.
- `README.md` links the consolidated artifacts and explains that the original notebooks are historical snapshots.

## Reproducibility and limitations

The consolidated notebook requires the T7 drive at `/Volumes/T7/mention-markets`. It is intentionally explicit about two source snapshots. The broad loader is useful for reconciling the essays but is not a replacement for the original historical manifest. The newer Trump audit has spot-checked settlement results and a trade-error file with no recorded errors, but its decision rows are still a curated research table with event-anchor and VWAP construction choices that should be independently reviewed before live deployment.

The fee calculation follows the project formula and the [Kalshi fee schedule](https://kalshi.com/docs/kalshi-fee-schedule.pdf). Fees, VWAP benchmarks, and resolved outcomes do not establish executable returns. A live claim requires a frozen holdout and a fill-level simulation.

## Artifacts

- [Executed Jupyter notebook](mention-markets-validation-consolidated.ipynb)
- [Rendered Markdown notebook](mention-markets-validation-consolidated.md)
- [Historical Trump-focused notebook](trump-longshot-bias-validation.ipynb)
- [Historical Trump-focused correction note](trump-longshot-bias-correction-report.md)
