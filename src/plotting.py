"""Shared matplotlib plotting helpers for mention-analysis notebooks."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
STYLE = "seaborn-v0_8-whitegrid"
DPI = 120
FONT_SIZE = 11

C_BLUE = "#2563eb"
C_GREEN = "#16a34a"
C_RED = "#dc2626"
C_GRAY = "#6b7280"
C_LIGHTBLUE = "#93c5fd"
C_LIGHTRED = "#fca5a5"


def apply_style():
    """Apply the shared matplotlib style."""
    plt.style.use(STYLE)
    plt.rcParams["figure.dpi"] = DPI
    plt.rcParams["font.size"] = FONT_SIZE


# ---------------------------------------------------------------------------
# Calibration plots
# ---------------------------------------------------------------------------

def plot_calibration_curve(
    cal: pd.DataFrame,
    ax: plt.Axes | None = None,
    label: str = "",
    color: str = C_BLUE,
    annotate_n: bool = True,
    marker: str = "o",
) -> plt.Axes:
    """Plot a single calibration curve (actual vs implied).

    cal must have columns: midpoint, actual_yes_pct, n.
    Midpoints in 0-100 scale; actual_yes_pct in 0-1 scale.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))

    x = cal["midpoint"].values / 100
    y = cal["actual_yes_pct"].values

    # Perfect calibration
    ax.plot([0, 1], [0, 1], "--", color=C_GRAY, linewidth=1.5, label="Perfect calibration")
    ax.plot(x, y, f"{marker}-", color=color, linewidth=2.5, markersize=8, label=label)

    if annotate_n:
        for _, row in cal.iterrows():
            if row["n"] > 0:
                ax.annotate(
                    f'n={int(row["n"])}',
                    (row["midpoint"] / 100, row["actual_yes_pct"]),
                    textcoords="offset points",
                    xytext=(0, 12),
                    fontsize=8,
                    color=C_GRAY,
                    ha="center",
                )

    ax.set_xticks(np.arange(0, 1.1, 0.1))
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, linestyle="-", alpha=0.3, color="gray", linewidth=0.5)
    return ax


def plot_multi_horizon_calibration(
    cal_by_time: dict[str, pd.DataFrame],
    intervals: list[str],
    title: str = "",
    bin_size: int = 10,
    annotate_2h: bool = True,
) -> plt.Figure:
    """Plot calibration curves for multiple time horizons on a single axes."""
    n_bins = int(100 / bin_size)
    x_bins = np.arange(n_bins)
    ideal = np.linspace(bin_size / 2, 100 - bin_size / 2, n_bins)

    cmap = plt.get_cmap("viridis_r")
    colors = [cmap(i) for i in np.linspace(0.1, 0.9, len(intervals))]

    figw = 14 if bin_size == 1 else 10
    fig, ax = plt.subplots(figsize=(figw, 6))
    ax.plot(x_bins, ideal, color="black", linestyle="--", linewidth=1.5, label="Perfect Calibration")

    prob_labels = cal_by_time[intervals[0]]["prob_bucket"].values

    for j, interval in enumerate(intervals):
        cal = cal_by_time[interval]
        y = cal["actual_yes_pct"].fillna(np.nan) * 100
        marker = "" if bin_size == 1 else "o"
        lw = 1.2 if bin_size == 1 else 2
        ax.plot(x_bins, y, marker=marker, color=colors[j], linewidth=lw, label=f"{interval} before Close")

        if annotate_2h and interval == "2h" and bin_size != 1:
            for k, val in enumerate(y):
                if not np.isnan(val):
                    n_count = cal.iloc[k]["n"]
                    if n_count > 0:
                        ax.text(x_bins[k], val + 3, f"n={n_count}", ha="center", va="bottom", fontsize=8)

    if bin_size == 1:
        tick_pos = np.arange(0, n_bins, 10)
        ax.set_xticks(tick_pos)
        ax.set_xticklabels([prob_labels[i] for i in tick_pos], rotation=45, ha="right")
    else:
        ax.set_xticks(x_bins)
        ax.set_xticklabels(prob_labels, rotation=45, ha="right")

    ax.set_ylim(-5, 110)
    ax.set_xlabel(f"Market Implied Probability ({bin_size}¢ buckets)")
    ax.set_ylabel("Actual % Resolved 'Yes'")
    ax.set_title(title)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    return fig


def plot_faceted_calibration(
    group_df: pd.DataFrame,
    group_name: str,
    total_contracts: int,
    accuracy: float,
    intervals: list[str],
) -> plt.Figure:
    """Create a 3-row faceted calibration chart (1¢, 5¢, 10¢ buckets)."""
    from src.metrics import calibration_buckets  # avoid circular import

    fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharey=True)
    bin_sizes = [1, 5, 10]

    for i, bs in enumerate(bin_sizes):
        ax = axes[i]
        n_bins = int(100 / bs)
        x_bins = np.arange(n_bins)
        ideal = np.linspace(bs / 2, 100 - bs / 2, n_bins)

        cmap = plt.get_cmap("viridis_r")
        colors = [cmap(v) for v in np.linspace(0.1, 0.9, len(intervals))]

        ax.plot(x_bins, ideal, color="black", linestyle="--", linewidth=1.5, label="Perfect Calibration")

        for j, interval in enumerate(intervals):
            col = f"vwap_{interval}"
            cal = calibration_buckets(group_df, col, bin_size=bs)
            y = cal["actual_yes_pct"].fillna(np.nan) * 100
            marker = "" if bs == 1 else "o"
            lw = 1.2 if bs == 1 else 2
            ax.plot(x_bins, y, marker=marker, color=colors[j], linewidth=lw, label=f"{interval} before Close")

            if interval == "2h" and bs != 1:
                for k, val in enumerate(y):
                    if not np.isnan(val):
                        n_count = cal.iloc[k]["n"]
                        if n_count > 0:
                            ax.text(x_bins[k], val + 3, f"n={n_count}", ha="center", va="bottom", fontsize=8)

        prob_labels = cal["prob_bucket"].values
        if bs == 1:
            tick_pos = np.arange(0, n_bins, 10)
            ax.set_xticks(tick_pos)
            ax.set_xticklabels([prob_labels[p] for p in tick_pos], rotation=45, ha="right")
        else:
            ax.set_xticks(x_bins)
            ax.set_xticklabels(prob_labels, rotation=45, ha="right")

        ax.set_ylim(-5, 110)
        ax.set_title(f"{bs}¢ Buckets", fontsize=12)
        ax.set_ylabel("Actual % Resolved 'Yes'", fontsize=10)
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.3)

    fig.suptitle(
        f"{group_name}\nTotal Markets: {total_contracts} | Overall Accuracy: {accuracy * 100:.1f}%",
        fontsize=12, fontweight="bold", y=0.95,
    )
    plt.tight_layout(rect=[0, 0, 0.86, 0.96])
    return fig


def plot_mad_summary(
    mad_over_time: dict[str, list[float]],
    intervals: list[str],
    colors: dict[str, str] | None = None,
) -> plt.Figure:
    """Plot MAD over time for multiple groups."""
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(intervals))

    for group, mads in mad_over_time.items():
        c = colors.get(group, "black") if colors else "black"
        ax.plot(x, mads, marker="o", linewidth=2, color=c, label=group)

    ax.set_xticks(x)
    ax.set_xticklabels(intervals)
    ax.set_ylabel("Mean Absolute Deviation (%)")
    ax.set_xlabel("Time Before Market Close")
    ax.set_title("Calibration Bias Reduction Near Close (Mean Absolute Deviation)")
    ax.invert_xaxis()
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    return fig


def plot_vwap_traces(
    df: pd.DataFrame,
    title: str = "VWAP Traces",
    intervals: list[str] | None = None,
) -> plt.Figure:
    """Spaghetti plot of per-contract VWAP traces, colored by outcome."""
    if intervals is None:
        intervals = ["7d", "3d", "1d", "6h", "2h", "1h", "30m", "10m"]
    vwap_cols = [f"vwap_{i}" for i in intervals]
    x = np.arange(len(intervals))

    fig, ax = plt.subplots(figsize=(10, 6))

    yes_data = df[df["actual_yes"]]
    no_data = df[~df["actual_yes"]]

    if not yes_data.empty:
        ax.plot(x, yes_data[vwap_cols].T, color="#2ca02c", alpha=0.05, linewidth=1)
        ax.plot([], [], color="#2ca02c", label="Resolved Yes")
    if not no_data.empty:
        ax.plot(x, no_data[vwap_cols].T, color="#d62728", alpha=0.05, linewidth=1)
        ax.plot([], [], color="#d62728", label="Resolved No")

    ax.set_xticks(x)
    ax.set_xticklabels(intervals)
    ax.set_ylabel("VWAP (Cents)")
    ax.set_xlabel("Time Before Market Close")
    ax.set_ylim(-5, 105)
    ax.set_title(title)

    leg = ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    for line in leg.get_lines():
        line.set_linewidth(3)
        line.set_alpha(1.0)

    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    return fig


def plot_calibration_deviation_over_time(
    df_cal: pd.DataFrame,
    title: str = "Calibration Accuracy Over Time",
    color: str = C_BLUE,
    show_trend: bool = False,
) -> plt.Figure:
    """Area chart of calibration deviation over time."""
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(df_cal["date"], df_cal["mean_absolute_deviation"], color=color, linewidth=2.5)
    ax.fill_between(df_cal["date"], df_cal["mean_absolute_deviation"], alpha=0.15, color=color)

    if show_trend and len(df_cal) > 3:
        z = np.polyfit(range(len(df_cal)), df_cal["mean_absolute_deviation"], 2)
        p = np.poly1d(z)
        ax.plot(df_cal["date"], p(range(len(df_cal))), "--", color=C_RED, linewidth=1.5, label="Trend (quadratic)")

    ax.axhline(y=2, color=C_GRAY, linestyle="--", alpha=0.5, label="2% threshold")
    ax.axhline(y=0, color=C_GREEN, linestyle="--", alpha=0.5, label="Perfect Calibration")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Mean Absolute Deviation (%)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, linestyle="-", alpha=0.3, color="gray", linewidth=0.5)
    fig.autofmt_xdate()
    plt.tight_layout()
    return fig


def plot_strategy_comparison(
    strategies: pd.DataFrame,
    title: str = "Strategy Backtest Results",
) -> plt.Figure:
    """Side-by-side bar chart of gross vs net per-trade returns and total profit."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    strat_colors = [C_BLUE, C_GREEN, "#8b5cf6", "#ff7f0e"]
    n_strats = len(strategies)
    colors = strat_colors[:n_strats]
    labels = [f">{t}%" for t in strategies["threshold"].values]

    x = np.arange(n_strats)
    w = 0.35

    # Left: per-trade returns
    axes[0].bar(x - w / 2, strategies["gross_return"] * 100, w, color=colors, alpha=0.5, label="Gross")
    bars2 = axes[0].bar(x + w / 2, strategies["net_return"] * 100, w, color=colors, label="Net of fees")
    axes[0].set_ylabel("Avg Profit Per Trade (¢)")
    axes[0].set_title("Per-Trade Returns (Gross vs Net)", fontweight="bold")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels)
    for bar, val in zip(bars2, strategies["net_return"] * 100):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                     f"{val:.1f}¢", ha="center", fontsize=9, fontweight="bold")
    axes[0].legend()

    # Right: total net profit
    net_total = strategies["trades"] * strategies["net_return"]
    bars3 = axes[1].bar(labels, net_total, color=colors, width=0.5)
    axes[1].set_ylabel("Total Estimated Profit ($)")
    axes[1].set_title("Total Net Profit (Trades × Net Profit)", fontweight="bold")
    for bar, val in zip(bars3, net_total):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     f"${val:.0f}", ha="center", fontsize=10, fontweight="bold")

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    return fig


def plot_profit_heatmap(
    df_sub: pd.DataFrame,
    subgroup_col: str = "subgroup",
    thresholds: list[int] | None = None,
) -> plt.Figure:
    """Color-coded heatmap of profit per trade by subgroup × threshold."""
    if thresholds is None:
        thresholds = [60, 70, 80, 90]

    profit_cols = [f"gt{t}_profit" for t in thresholds]
    labels_x = [f">{t}%" for t in thresholds]
    names = df_sub[subgroup_col].values

    heatmap_data = df_sub[profit_cols].values * 100

    fig, ax = plt.subplots(figsize=(10, max(3, len(names) * 0.8)))
    im = ax.imshow(heatmap_data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=15)

    ax.set_xticks(range(len(labels_x)))
    ax.set_xticklabels(labels_x, fontsize=11)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=11)

    for i in range(len(names)):
        for j in range(len(labels_x)):
            val = heatmap_data[i, j]
            tc = "white" if val > 10 or val < 3 else "black"
            ax.text(j, i, f"{val:.1f}¢", ha="center", va="center", fontsize=12, fontweight="bold", color=tc)

    ax.set_title("Avg Profit Per Trade (¢) by Subgroup × Threshold", fontsize=14, fontweight="bold")
    ax.set_xlabel("Entry Threshold", fontsize=12)
    fig.colorbar(im, ax=ax, label="Profit (¢/trade)", shrink=0.8)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Aliases for backward compatibility
# ---------------------------------------------------------------------------

def setup_style():
    """Alias for apply_style."""
    apply_style()
