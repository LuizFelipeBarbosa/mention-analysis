"""Load mention-market data from parquet files via DuckDB."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

DATA_ROOT = Path(__file__).parent.parent / "data"
TRADES_GLOB = str(DATA_ROOT / "trades" / "*.parquet")
MARKETS_GLOB = str(DATA_ROOT / "markets" / "*.parquet")

# ---------------------------------------------------------------------------
# VWAP intervals used throughout the analysis
# ---------------------------------------------------------------------------
VWAP_INTERVALS = ["7d", "3d", "1d", "6h", "2h", "1h", "30m", "10m"]

_INTERVAL_SQL = {
    "7d": "INTERVAL 7 DAY",
    "3d": "INTERVAL 3 DAY",
    "1d": "INTERVAL 1 DAY",
    "6h": "INTERVAL 6 HOUR",
    "2h": "INTERVAL 2 HOUR",
    "1h": "INTERVAL 1 HOUR",
    "30m": "INTERVAL 30 MINUTE",
    "10m": "INTERVAL 10 MINUTE",
}

# Column expressions that handle both old (yes_price int cents, count int)
# and new (yes_price_dollars float 0-1, count_fp float) schemas.
_YES_PRICE_EXPR = "COALESCE(t.yes_price_dollars * 100.0, t.yes_price)"
_COUNT_EXPR = "COALESCE(t.count_fp, t.count)"


def _vwap_columns(anchor: str = "lt.last_trade_time") -> str:
    """Build the VWAP SELECT expressions for every interval.

    Parameters
    ----------
    anchor : str
        SQL expression for the time anchor. Defaults to ``lt.last_trade_time``
        (the per-ticker last trade timestamp), which is the correct anchor for
        measuring "N hours before trading stopped."  Previously this was
        ``m.close_time`` (settlement time), which could be hours after the last
        trade and caused all VWAP horizons to collapse to the same value.
    """
    parts = []
    for label, interval in _INTERVAL_SQL.items():
        parts.append(
            f"SUM(CASE WHEN t.created_time <= {anchor} - {interval} "
            f"THEN {_YES_PRICE_EXPR} * {_COUNT_EXPR} ELSE 0 END) / "
            f"NULLIF(SUM(CASE WHEN t.created_time <= {anchor} - {interval} "
            f"THEN {_COUNT_EXPR} ELSE 0 END), 0) AS vwap_{label}"
        )
    return ",\n        ".join(parts)


def load_mention_markets(
    trades_glob: str = TRADES_GLOB,
    markets_glob: str = MARKETS_GLOB,
    series_filter: list[str] | None = None,
) -> pd.DataFrame:
    """Load resolved mention markets with VWAP snapshots at each horizon.

    Parameters
    ----------
    trades_glob : str
        Glob pattern for trade parquet files.
    markets_glob : str
        Glob pattern for market parquet files.
    series_filter : list[str] | None
        If provided, restrict to these series names (matched against
        the ``series`` column in the trades table).

    Returns
    -------
    pd.DataFrame with columns: ticker, title, result, series,
        close_time, last_trade_time, vwap_7d … vwap_10m, total_volume.

        ``last_trade_time`` is the timestamp of the final recorded trade for
        each market.  All VWAP horizons are anchored to this timestamp rather
        than ``close_time`` (settlement time), so ``vwap_2h`` truly means
        "the VWAP of trades that occurred more than 2 hours before the last
        trade."
    """
    con = duckdb.connect()

    series_clause = ""
    if series_filter:
        quoted = ", ".join(f"'{s}'" for s in series_filter)
        # Note: no table alias here — we're inside the market_base CTE
        series_clause = f"AND series IN ({quoted})"

    sql = f"""
    WITH market_base AS (
        SELECT
            ticker,
            title,
            result,
            close_time,
            series
        FROM '{markets_glob}'
        WHERE result IN ('yes', 'no')
          {series_clause}
    ),
    -- Compute the last trade timestamp per ticker.
    -- We anchor all VWAP windows to this rather than close_time (settlement),
    -- because close_time can be 60+ minutes after the final trade, causing
    -- all short-horizon VWAPs to collapse to the same value.
    last_trade AS (
        SELECT
            t.ticker,
            MAX(t.created_time) AS last_trade_time
        FROM read_parquet('{trades_glob}', union_by_name=true) t
        INNER JOIN market_base m ON t.ticker = m.ticker
        WHERE ({_YES_PRICE_EXPR}) IS NOT NULL
          AND ({_COUNT_EXPR}) IS NOT NULL
          AND ({_COUNT_EXPR}) > 0
        GROUP BY t.ticker
    ),
    vwaps AS (
        SELECT
            t.ticker,
            {_vwap_columns("lt.last_trade_time")},
            SUM({_COUNT_EXPR}) AS total_volume
        FROM read_parquet('{trades_glob}', union_by_name=true) t
        INNER JOIN market_base m ON t.ticker = m.ticker
        INNER JOIN last_trade lt ON t.ticker = lt.ticker
        WHERE ({_YES_PRICE_EXPR}) IS NOT NULL
          AND ({_COUNT_EXPR}) IS NOT NULL
          AND ({_COUNT_EXPR}) > 0
        GROUP BY t.ticker
    )
    SELECT
        m.ticker,
        m.title,
        m.result,
        m.series,
        m.close_time,
        lt.last_trade_time,
        v.vwap_7d,
        v.vwap_3d,
        v.vwap_1d,
        v.vwap_6h,
        v.vwap_2h,
        v.vwap_1h,
        v.vwap_30m,
        v.vwap_10m,
        v.total_volume
    FROM market_base m
    INNER JOIN last_trade lt ON m.ticker = lt.ticker
    INNER JOIN vwaps v ON m.ticker = v.ticker
    """
    df = con.execute(sql).df()

    # Remove duplicate ticker column from the join
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    return df


def load_trade_positions(
    trades_glob: str = TRADES_GLOB,
    markets_glob: str = MARKETS_GLOB,
    series_filter: list[str] | None = None,
) -> pd.DataFrame:
    """Load both sides of every trade for calibration-over-time analysis.

    Returns columns: created_time, series, price, won.
    price is in cents (1-99).
    """
    con = duckdb.connect()

    series_clause = ""
    if series_filter:
        quoted = ", ".join(f"'{s}'" for s in series_filter)
        series_clause = f"AND m.series IN ({quoted})"

    sql = f"""
    WITH resolved_markets AS (
        SELECT
            ticker,
            result,
            series
        FROM '{markets_glob}'
        WHERE result IN ('yes', 'no')
          {series_clause}
    ),
    raw_trades AS (
        SELECT
            ticker,
            created_time,
            taker_side,
            {_YES_PRICE_EXPR} AS _yp,
            (100.0 - {_YES_PRICE_EXPR}) AS _np,
            {_COUNT_EXPR} AS _cnt
        FROM read_parquet('{trades_glob}', union_by_name=true) t
        WHERE {_YES_PRICE_EXPR} IS NOT NULL
          AND {_COUNT_EXPR} IS NOT NULL
          AND {_COUNT_EXPR} > 0
    ),
    trade_positions AS (
        -- Taker side
        SELECT
            t.created_time,
            m.series,
            CASE WHEN t.taker_side = 'yes' THEN t._yp
                 ELSE t._np END AS price,
            CASE WHEN t.taker_side = m.result THEN true
                 ELSE false END AS won
        FROM raw_trades t
        INNER JOIN resolved_markets m ON t.ticker = m.ticker

        UNION ALL

        -- Counter-party side
        SELECT
            t.created_time,
            m.series,
            CASE WHEN t.taker_side = 'yes' THEN t._np
                 ELSE t._yp END AS price,
            CASE WHEN t.taker_side != m.result THEN true
                 ELSE false END AS won
        FROM raw_trades t
        INNER JOIN resolved_markets m ON t.ticker = m.ticker
    )
    SELECT created_time, series, price, won
    FROM trade_positions
    WHERE price >= 1 AND price <= 99
    ORDER BY created_time
    """
    return con.execute(sql).df()


# ---------------------------------------------------------------------------
# Legacy aliases expected by some notebooks
# ---------------------------------------------------------------------------

def load_trades(trades_glob: str = TRADES_GLOB) -> pd.DataFrame:
    """Load raw trades from parquet. Returns yes_price in cents."""
    con = duckdb.connect()
    sql = f"""
    SELECT
        trade_id,
        ticker,
        series,
        created_time,
        COALESCE(yes_price_dollars * 100.0, yes_price) AS yes_price,
        COALESCE(no_price_dollars * 100.0, no_price) AS no_price,
        COALESCE(count_fp, count) AS count,
        taker_side
    FROM read_parquet('{trades_glob}', union_by_name=true)
    WHERE COALESCE(yes_price_dollars, yes_price / 100.0) IS NOT NULL
      AND COALESCE(count_fp, count) IS NOT NULL
      AND COALESCE(count_fp, count) > 0
    """
    return con.execute(sql).df()


def load_markets(markets_glob: str = MARKETS_GLOB) -> pd.DataFrame:
    """Load raw markets from parquet."""
    con = duckdb.connect()
    return con.execute(f"SELECT * FROM '{markets_glob}'").df()


def load_mention_data(
    trades_glob: str = TRADES_GLOB,
    markets_glob: str = MARKETS_GLOB,
) -> pd.DataFrame:
    """Convenience alias for load_mention_markets."""
    return load_mention_markets(trades_glob=trades_glob, markets_glob=markets_glob)
