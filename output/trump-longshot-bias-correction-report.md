# Trump mention-market calibration correction report (2026-09-04 comparison snapshot)

> This focused report is retained as a historical comparison. The refreshed October 2 audit supersedes its “current” wording. Use the [consolidated validation report](mention-markets-validation-report.md) and [executed consolidated notebook](mention-markets-validation-consolidated.ipynb) for the latest T7 evidence.

## Verdict

This historical broad-snapshot comparison supports both sides of the essay's descriptive claim after correcting the market-universe filter: Trump mention contracts priced around 30% resolve YES below their prices, and contracts priced at 70% or more resolve YES above their prices. The refreshed October 2 audit does not replicate the high-side result, so the older positive estimate is snapshot-sensitive rather than a current conclusion.

The essays should still be revised before being treated as current research. Their headline counts and settlement-lag figures are historical, the current snapshot stores Trump contracts under three different `series` values, and the threshold backtests are in-sample VWAP benchmarks rather than executable trading results. The edge also attenuates in newer observations.

## Historical broad-snapshot evidence

The analysis uses 141 market files and 141 trade files from `/Volumes/T7/mention-markets`. The raw market metadata contains 38,450 rows, 36,214 resolved rows, and 143 raw series values. The latest raw market metadata ends on August 8, 2026; resolved Trump contracts with a valid 2-hour VWAP extend through July 5, 2026.

Trump contracts must be selected by ticker prefix (`KXTRUMPMENTION...`). The current metadata stores them as:

| Metadata series | Raw rows | Resolved rows |
|---|---:|---:|
| `KXTRUMPMENTION` | 4,814 | 4,814 |
| `A` | 1,267 | 1,267 |
| `B` | 460 | 460 |
| **Total** | **6,745** | **6,541** |

After requiring a valid 2-hour VWAP, 6,352 contracts across 260 events remain.

| 2-hour price band | Contracts | Events | Mean implied YES | Actual YES | Error (actual − implied) |
|---|---:|---:|---:|---:|---:|
| 25–35% (“around 30%”) | 676 | 196 | 29.71% | 17.01% | **−12.70 pp** |
| 70–80% | 600 | 195 | 75.18% | 86.00% | **+10.82 pp** |
| 70%+ | 1,719 | 232 | 83.65% | 91.86% | **+8.20 pp** |

A speech-level cluster bootstrap gives 95% intervals of −16.29 to −8.97 pp for the 30% band, +7.20 to +14.31 pp for the 70–80% band, and +6.20 to +10.11 pp for the 70%+ band.

The pattern is smaller in the newer data and should be treated as snapshot-sensitive evidence. In the most recent 90 days, the 25–35% band is −7.87 pp and the 70%+ band is +3.25 pp. Those recent bands are much thinner than the full history, so they should be described as attenuated evidence rather than a guaranteed live edge.

## What the historical comparison supports

- Low-price YES contracts are overestimated in the broad snapshot.
- Anchoring VWAP windows to `last_trade_time` is appropriate for a trading-stop question; `close_time` should not be described as settlement time without a separate `settlement_ts`.
- Late-horizon differences are useful sensitivity evidence but can reflect liquidity and sample selection.
- The fee-adjusted threshold benchmark is an in-sample accounting check, not a current trading recommendation.

## What needs correction

1. **Historical counts are presented as current.** The political essay reports 7,320 political contracts and 3,401 Trump contracts. The canonical current Trump sample has 6,352 valid 2-hour observations, and the broader current valid 2-hour universe has 20,979 rows. The old figures should be labeled with their snapshot date.
2. **Exact-series filtering drops Trump markets.** Filtering only `series == "KXTRUMPMENTION"` misses 1,805 Trump rows stored as `A` and `B`. Use ticker-prefix selection or a maintained canonical mapping.
3. **Bucket midpoints are used as implied probabilities.** `calibration_buckets` compares outcomes with fixed midpoints (for example, 25% for the 20–30% bucket). Report the mean price inside each bucket for the calibration error; retain the midpoint only as a display label.
4. **Uncertainty is overstated when contracts are treated as independent.** A single speech can create dozens of correlated contracts. Use event-cluster bootstrap intervals or event-level aggregation for inference.
5. **The backtests are in-sample.** The same observations define the calibration pattern and the strategy returns. Add a chronological train/test split and report the untouched test period separately.
6. **VWAP is a benchmark, not a fill model.** The current strategy code assumes one-contract fills at a retrospective VWAP and does not model available size, queue position, slippage, or event-level drawdown.
7. **The category map is stale.** The current snapshot has 2,342 valid rows classified as `Other`, including new political series. The cross-category article should rebuild its category mapping before updating counts or comparisons.
8. **Settlement-lag figures have changed.** Across the current all-market VWAP population, the positive-lag median is 58.0 minutes, 49.3% exceed one hour, and 21.2% exceed four hours, compared with 71 minutes, 53.2%, and 22.6% in the essay.
9. **The 10-minute result needs an execution caveat.** The larger late-horizon gap may reflect late liquidity, market-selection effects, and prices that are difficult to fill at scale. It is useful calibration evidence, not automatic tradable alpha.

## Recommended update path

- Freeze and record the T7 snapshot date and the exact file manifest.
- Canonicalize market identity by ticker prefix and join `event_ticker` before analysis.
- Report 10-cent calibration tables using within-bin mean implied probability and Wilson or bootstrap intervals.
- Use event-cluster bootstrap as the default uncertainty method.
- Pre-register the primary horizon (2 hours is reasonable), then use 6h/1h/30m/10m as sensitivity checks.
- Split by close date, estimate any threshold rule only on the training period, and evaluate it once on the later test period.
- Add fill-size, slippage, and event-level PnL simulations before making a trading recommendation.
- Rebuild the series-to-category map and separately report unmapped series instead of silently aggregating them.

## Reproducible artifact

The executed notebook contains the loader, data-quality checks, calibration tables, event-cluster bootstrap, recency and horizon sensitivity, fee-adjusted benchmark, essay validation table, and correction steps:

- [Markdown notebook](trump-longshot-bias-validation.md)
- [Executed Jupyter notebook](trump-longshot-bias-validation.ipynb)
