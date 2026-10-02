# mention-analysis

Calibration analysis and trading strategy evaluation for Kalshi mention markets — binary prediction contracts that settle based on whether a specific topic, person, or phrase is mentioned during a scheduled event.

## Validated consolidated audit

The original notebooks are retained as historical snapshots. The current executed audit consolidates their logic, validates the essay claims against both T7 snapshots, corrects bucket and aggregation issues, and reports the newer Trump-specific evidence:

- **[Consolidated validation notebook](output/mention-markets-validation-consolidated.ipynb)** — executable source and outputs.
- **[Consolidated Markdown notebook](output/mention-markets-validation-consolidated.md)** — reviewable rendered version.
- **[Validation report](output/mention-markets-validation-report.md)** — claim ledger, severity-ranked issues, and repair plan.

The public-data refresh helper is [scripts/refresh_trump_audit.py](scripts/refresh_trump_audit.py). It writes a new timestamped T7 snapshot, records API cutoffs and hashes, reconciles the existing tape, and never places orders.

## Notebooks

| Notebook | Focus |
|----------|-------|
| **[political-mention-markets.ipynb](political-mention-markets.ipynb)** | Deep dive into political speech mention contracts. Covers calibration curves, subgroup analysis (Trump, press briefings, Mamdani/NYC, niche), fee-adjusted strategy backtests, and cross-subgroup profitability comparison. |
| **[general-mention-markets.ipynb](general-mention-markets.ipynb)** | Cross-category comparison of all mention markets: Sports, Politicians, Entertainment, Earnings, Finance, and Media/News. Compares calibration quality, MAD, and strategy profitability across categories. |

## Data

Data lives on an external drive and is symlinked into the repo:

```
data -> /Volumes/T7/mention-markets
├── trades/    # Per-series parquet files (141 series, ~7.6M trades)
└── markets/   # Per-series parquet files (market metadata + outcomes)
```

The counts above describe the historical essay snapshot. Current counts are snapshot-dependent; the consolidated validation artifacts record the exact T7/API cutoff and denominators for each run.

**Trade columns:** `trade_id`, `ticker`, `series`, `created_time` (UTC), `yes_price` (int cents 1–99), `no_price`, `count`, `taker_side`

**Market columns:** `ticker`, `event_ticker`, `market_type`, `title`, `status`, `result`, `close_time`, `volume`, `open_interest`, etc.

## Shared Helpers (`src/`)

| Module | Purpose |
|--------|---------|
| `data_loading.py` | DuckDB-based data loading with VWAP computation at 8 time horizons |
| `mention_filters.py` | Category mapping (ticker prefix/series → category) and political subgroup assignment |
| `metrics.py` | Calibration buckets, MAD, strategy profitability, Kalshi fee calculation |
| `plotting.py` | Matplotlib chart helpers (calibration curves, heatmaps, VWAP traces, etc.) |

## Articles

| Article | Description |
|---------|-------------|
| **[Cross-Category Calibration Analysis](articles/cross-category-calibration-analysis.md)** | Full write-up of the general mention markets analysis: dataset overview, settlement lag problem, calibration by category, MAD convergence, and strategy profitability with 16 figures. |
| **[Political Mention Market Calibration](articles/political-mention-market-calibration.md)** | Deep dive into political speech mentions: subgroup calibration at multiple bucket granularities, longshot bias, VWAP trajectories, and YES vs NO strategy backtests with 22 figures. |

## Key Methodology

- **Cumulative pre-cutoff VWAP snapshots** at 7d, 3d, 1d, 6h, 2h, 1h, 30m, 10m before the final recorded trade
- **Calibration curves**: actual YES rate vs within-bucket mean implied probability in 1/5/10-cent buckets
- **MAD** (Mean Absolute Deviation) from within-bucket mean implied probability; event-cluster uncertainty is required for inference
- **Strategy profitability**: buy YES when price > threshold; gross and net-of-fees returns
- **Kalshi fee**: `ceil(0.07 × p × (100 − p) / 100)` cents per contract

## Setup

```bash
pip3.12 install --break-system-packages duckdb pandas matplotlib numpy pyarrow tabulate
```

Ensure the T7 drive is mounted at `/Volumes/T7/mention-markets`, then:

```bash
ln -sf /Volumes/T7/mention-markets data
```

## References

- Becker, J. (2026). *The Microstructure of Wealth Transfer in Prediction Markets.* https://jbecker.dev/research/prediction-market-microstructure
- Le, N. A. (2026). *Decomposing Crowd Wisdom: Domain-Specific Calibration Dynamics in Prediction Markets.* https://arxiv.org/abs/2602.19520
