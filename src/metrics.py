"""Calibration, MAD, and profitability metrics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Fee calculation
# ---------------------------------------------------------------------------

def kalshi_fee(price_cents: float) -> int:
    """Kalshi taker fee per contract in cents.

    fee = ceil(0.07 * p * (100 - p) / 100)
    """
    return math.ceil(0.07 * price_cents * (100.0 - price_cents) / 100.0)


# ---------------------------------------------------------------------------
# Calibration helpers
# ---------------------------------------------------------------------------

def calibration_buckets(
    df: pd.DataFrame,
    prob_col: str,
    actual_col: str = "actual_yes",
    bin_size: int = 10,
) -> pd.DataFrame:
    """Bin implied probabilities and compute actual YES rate per bucket.

    Parameters
    ----------
    df : DataFrame with at least ``prob_col`` (0-100 cents) and ``actual_col`` (bool).
    prob_col : column name containing the VWAP in cents.
    actual_col : column with boolean resolved-YES indicator.
    bin_size : bucket width in cents (1, 5, or 10).

    Returns
    -------
    DataFrame with columns: prob_bucket, midpoint, n, actual_yes_pct.
    """
    n_bins = int(100 / bin_size)
    bins = np.linspace(0, 100, n_bins + 1)
    midpoints = np.linspace(bin_size / 2, 100 - bin_size / 2, n_bins)
    labels = [f"{int(b)}-{int(b + bin_size)}%" for b in bins[:-1]]

    tmp = df.copy()
    tmp["_bucket"] = pd.cut(tmp[prob_col], bins=bins, labels=labels, include_lowest=True)

    cal = (
        tmp.groupby("_bucket", observed=False)
        .agg(n=(prob_col, "count"), actual_yes_count=(actual_col, "sum"))
        .reset_index()
    )
    cal.rename(columns={"_bucket": "prob_bucket"}, inplace=True)
    cal["midpoint"] = midpoints
    cal["actual_yes_pct"] = np.where(cal["n"] > 0, cal["actual_yes_count"] / cal["n"], np.nan)
    return cal


def compute_mad(cal: pd.DataFrame, min_n: int = 5) -> float:
    """Mean Absolute Deviation from perfect calibration.

    Uses only buckets with n >= min_n.
    """
    valid = cal[cal["n"] >= min_n].copy()
    if valid.empty:
        return np.nan
    valid["abs_err"] = np.abs(valid["actual_yes_pct"] * 100 - valid["midpoint"])
    return float(valid["abs_err"].mean())


def multi_horizon_calibration(
    df: pd.DataFrame,
    intervals: list[str],
    bin_size: int = 10,
    min_n: int = 5,
) -> tuple[dict[str, pd.DataFrame], list[float]]:
    """Compute calibration buckets and MAD for multiple VWAP horizons.

    Parameters
    ----------
    df : DataFrame with ``vwap_{interval}`` columns and ``actual_yes`` bool.
    intervals : list of interval labels, e.g. ["1d", "6h", "2h", ...].
    bin_size : bucket width in cents.
    min_n : minimum bucket count to include in MAD.

    Returns
    -------
    (dict mapping interval → calibration DataFrame, list of MAD values).
    """
    cal_by_time: dict[str, pd.DataFrame] = {}
    mad_values: list[float] = []
    for interval in intervals:
        col = f"vwap_{interval}"
        cal = calibration_buckets(df, col, bin_size=bin_size)
        cal_by_time[interval] = cal
        mad_values.append(compute_mad(cal, min_n=min_n))
    return cal_by_time, mad_values


# ---------------------------------------------------------------------------
# Profitability helpers
# ---------------------------------------------------------------------------

def strategy_profits(
    df: pd.DataFrame,
    price_col: str = "vwap_2h",
    actual_col: str = "actual_yes",
    thresholds: list[int] | None = None,
    side: str = "yes",
) -> pd.DataFrame:
    """Compute trade counts and profit per trade for threshold strategies.

    Parameters
    ----------
    side : "yes" or "no"
        - "yes": buy YES when price > threshold (bet the word IS mentioned)
        - "no":  buy NO when price < threshold (bet the word is NOT mentioned)
    """
    if thresholds is None:
        if side == "no":
            thresholds = [0, 10, 20, 30, 40]
        else:
            thresholds = [60, 70, 80, 90, 100]

    rows = []
    for t in thresholds:
        if side == "no":
            eligible = df[df[price_col] < t].copy()
        else:
            eligible = df[df[price_col] > t].copy()

        if eligible.empty:
            rows.append({
                "threshold": t, "trades": 0,
                "gross_pnl_per_trade": 0.0, "net_pnl_per_trade": 0.0,
                "gross_return": 0.0, "net_return": 0.0, "hit_rate": 0.0,
            })
            continue

        prices = eligible[price_col].values
        won = eligible[actual_col].values.astype(float)

        if side == "no":
            # Buy NO at (100 - price) cents; win if outcome is NO (won == 0)
            entry_prices = 100.0 - prices
            payouts = (1.0 - won) * 100.0
        else:
            # Buy YES at price cents; win if outcome is YES (won == 1)
            entry_prices = prices.copy()
            payouts = won * 100.0

        fees = np.array([kalshi_fee(p) for p in entry_prices])
        cost = entry_prices + fees
        gross_cost = entry_prices.sum()
        total_cost = cost.sum()
        total_payout = payouts.sum()

        gross_return = (total_payout - gross_cost) / gross_cost if gross_cost > 0 else 0.0
        net_return = (total_payout - total_cost) / total_cost if total_cost > 0 else 0.0

        n = len(eligible)
        gross_pnl = (total_payout - gross_cost) / n
        net_pnl = (total_payout - total_cost) / n
        hit_rate = (payouts > 0).mean()

        rows.append({
            "threshold": t,
            "trades": n,
            "gross_pnl_per_trade": gross_pnl,
            "net_pnl_per_trade": net_pnl,
            "gross_return": gross_return,
            "net_return": net_return,
            "hit_rate": hit_rate,
        })

    return pd.DataFrame(rows)


def extremes_strategy(
    df: pd.DataFrame,
    price_col: str = "vwap_2h",
    actual_col: str = "actual_yes",
    high: int = 70,
    low: int = 30,
) -> dict:
    """Buy YES when price > high, buy NO when price < low."""
    results = {"trades": 0, "total_cost": 0.0, "total_payout": 0.0}

    for _, row in df.iterrows():
        price = row[price_col]
        won = row[actual_col]
        fee = kalshi_fee(price)

        if price > high:
            results["trades"] += 1
            results["total_cost"] += price + fee
            results["total_payout"] += 100.0 if won else 0.0
        elif price < low:
            results["trades"] += 1
            results["total_cost"] += (100.0 - price) + fee
            results["total_payout"] += 100.0 if not won else 0.0

    tc = results["total_cost"]
    results["net_return"] = (results["total_payout"] - tc) / tc if tc > 0 else 0.0
    return results


# ---------------------------------------------------------------------------
# Calibration over time
# ---------------------------------------------------------------------------

def calibration_deviation_over_time(
    df: pd.DataFrame,
    min_cumulative: int = 500,
) -> pd.DataFrame:
    """Compute cumulative MAD at weekly intervals.

    Parameters
    ----------
    df : DataFrame with columns ``created_time``, ``price``, ``won``.
    min_cumulative : skip weeks with fewer cumulative observations.

    Returns
    -------
    DataFrame with columns ``date`` and ``mean_absolute_deviation``.
    """
    df = df.copy()
    df["created_time"] = pd.to_datetime(df["created_time"], utc=True)

    if df.empty:
        return pd.DataFrame(columns=["date", "mean_absolute_deviation"])

    min_date = df["created_time"].min()
    max_date = df["created_time"].max()
    week_dates = pd.date_range(start=min_date, end=max_date, freq="W")

    dates, deviations = [], []
    for end_date in week_dates:
        cumulative = df[df["created_time"] <= end_date]
        agg = (
            cumulative.groupby("price")
            .agg(total=("won", "count"), wins=("won", "sum"))
            .reset_index()
        )
        if agg["total"].sum() < min_cumulative:
            continue

        prices = agg["price"].values.astype(float)
        win_rates = 100.0 * agg["wins"].values / agg["total"].values
        mean_dev = float(np.mean(np.abs(win_rates - prices)))

        dates.append(end_date)
        deviations.append(mean_dev)

    return pd.DataFrame({"date": dates, "mean_absolute_deviation": deviations})


# ---------------------------------------------------------------------------
# Aliases for backward compatibility
# ---------------------------------------------------------------------------

def compute_vwaps(df: pd.DataFrame, intervals: list[str] | None = None) -> pd.DataFrame:
    """Alias / stub: VWAPs are computed in data_loading SQL. Returns df unchanged."""
    return df


def compute_calibration(
    df: pd.DataFrame,
    prob_col: str,
    actual_col: str = "actual_yes",
    bin_size: int = 10,
) -> pd.DataFrame:
    """Alias for calibration_buckets."""
    return calibration_buckets(df, prob_col, actual_col=actual_col, bin_size=bin_size)
