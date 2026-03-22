# Changelog & Known Issues

## 2026-03-21 — Data Integrity Fixes

### Fix: VWAP Anchor Changed from `close_time` to `last_trade_time`

**Problem:** All VWAP horizons (7d, 3d, 1d, 6h, 2h, 1h, 30m, 10m) were computed relative to `close_time`, which is when Kalshi **settles and pays out** the market — not when trading actually stops.

The median gap between the last trade and `close_time` is **60 minutes**, but can be hours (75th percentile: 258 min). This meant:
- `vwap_2h` was "VWAP up to 2h before settlement," not "2h before the event"
- For markets with large settlement gaps, all VWAP horizons collapsed to the same value because all trades occurred well before any horizon cutoff
- The horizon labels in the analysis were misleading

**Fix:** VWAPs are now anchored to `MAX(created_time)` per ticker — the timestamp of the last recorded trade. This is the best available proxy for when the event ended and trading ceased.

**Impact:** VWAP horizons now correctly differentiate. Before the fix, `vwap_2h == vwap_10m` for nearly all markets. After the fix, only 17.7% of markets show this equality (cases where all trading genuinely happened >2h before the last trade).

**Commits:** `a2c7728`, `eec33df`

---

### Issue: 13,000 Resolved Markets Have Zero Trades

**Observation:** Of 33,587 resolved mention markets in the dataset, only 20,587 have any trade records. The remaining **13,000 markets are excluded** from all analysis because the INNER JOIN between markets and trades drops them.

**Breakdown:**
- **12,459** are from `KXMVEMENTION` — a series where market metadata was collected but trade data was not
- **269** are `KXTRUMPMENTION` markets with no trades (likely very low liquidity, never traded)
- **202** are `KXEARNINGSMENTION` with the same issue
- The remaining ~70 are scattered across other series

**Impact:** The analysis covers 18,948 markets (after VWAP computation), not the full 33,587. This is a data collection gap, not an analytical error. Markets with zero trades have no price information to analyze.

**Status:** Documented. Could be partially addressed by running trade collection for `KXMVEMENTION` if that data still exists on Kalshi's API.

---

### Fix: SQL Bug in Series Filter

**Problem:** `load_mention_markets()` had a `series_clause` that referenced `m.series` inside a CTE where the `m` alias didn't exist, causing the series filter to silently fail.

**Fix:** Changed to bare `series` reference within the CTE scope.

**Commit:** `a2c7728`

---

### Note: Trade Timestamps are Microseconds

**Observation:** Trade `created_time` values loaded via DuckDB's `.values.astype('int64')` produce **16-digit microsecond** integers, while `pd.Timestamp.value` produces **19-digit nanosecond** integers. Code that mixes these (e.g., comparing trade arrays against market timestamps) will silently produce wrong results — window masks return zero matches because everything is off by 1000x.

**Impact:** This was caught and fixed in the `mention-mispricing-system` repo's snapshot builder. The `mention-analysis` repo avoids this issue by doing all time arithmetic in SQL (DuckDB handles units internally).

**Lesson:** Always verify timestamp units when mixing pandas Timestamp arithmetic with numpy int64 arrays.

---

## Data Coverage Summary

| Metric | Count |
|---|---|
| Total MENTION series | 141 |
| Total trades | 7,601,636 |
| Total markets (all statuses) | 35,837 |
| Resolved markets | 33,587 |
| Resolved markets with trades | 20,587 |
| Markets in analysis (after VWAP) | 18,948 |
| Date range | Jan 2025 — Mar 2026 |
