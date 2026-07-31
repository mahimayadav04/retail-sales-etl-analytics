"""
utils.py - Shared Helper Functions
=====================================
Retail Sales ETL & Analytics Platform  |  Phase 10

Responsibilities:
    - Format numbers, currencies, and percentages consistently.
    - Apply sidebar filters to any DataFrame.
    - Provide safe aggregation helpers used across multiple pages.
"""

from datetime import datetime
import pandas as pd


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_currency(value: float) -> str:
    """Format a number as a USD currency string with K / M suffix.

    Args:
        value (float): Raw numeric value.

    Returns:
        str: Formatted string, e.g. '$1.23M', '$456.7K', '$123'.

    Example:
        >>> fmt_currency(1_234_567)
        '$1.23M'
    """
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.2f}"


def fmt_number(value: float) -> str:
    """Format a plain number with comma thousands separators.

    Args:
        value (float): Raw numeric value.

    Returns:
        str: Formatted string, e.g. '9,977'.
    """
    return f"{value:,.0f}"


def fmt_percent(value: float) -> str:
    """Format a value as a percentage string rounded to two decimals.

    Args:
        value (float): The percentage value (e.g. 23.45 means 23.45 %).

    Returns:
        str: Formatted string, e.g. '23.45%'.
    """
    return f"{value:.2f}%"


# ---------------------------------------------------------------------------
# Filter helper
# ---------------------------------------------------------------------------

def apply_filters(
    df: pd.DataFrame,
    regions: list,
    categories: list,
    segments: list,
    ship_modes: list,
) -> pd.DataFrame:
    """Apply sidebar filter selections to a DataFrame.

    Filters are applied only when the user has selected a non-empty subset.
    An empty list for any filter means 'show all' for that dimension.

    Args:
        df (pd.DataFrame): The full sales DataFrame.
        regions (list): Selected region values.
        categories (list): Selected category values.
        segments (list): Selected segment values.
        ship_modes (list): Selected ship_mode values.

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """
    if regions:
        df = df[df["region"].isin(regions)]
    if categories:
        df = df[df["category"].isin(categories)]
    if segments:
        df = df[df["segment"].isin(segments)]
    if ship_modes:
        df = df[df["ship_mode"].isin(ship_modes)]
    return df


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning a default when denominator is zero.

    Args:
        numerator (float): The top number.
        denominator (float): The bottom number.
        default (float): Value to return when denominator == 0. Default 0.0.

    Returns:
        float: The division result or the default value.
    """
    if denominator == 0:
        return default
    return numerator / denominator


def get_kpis(df: pd.DataFrame) -> dict:
    """Compute the five headline KPIs from a (possibly filtered) DataFrame.

    Args:
        df (pd.DataFrame): Sales DataFrame (full or filtered).

    Returns:
        dict: Keys are KPI names, values are raw floats ready for formatting.
              Keys: total_revenue, total_profit, total_orders,
                    avg_order_value, avg_profit_margin
    """
    return {
        "total_revenue":    df["revenue"].sum(),
        "total_profit":     df["profit"].sum(),
        "total_orders":     len(df),
        "avg_order_value":  safe_divide(df["revenue"].sum(), len(df)),
        "avg_profit_margin": df["profit_margin"].mean() if len(df) else 0.0,
    }


def last_refresh_label() -> str:
    """Return a human-readable 'Last refreshed' timestamp string.

    Returns:
        str: e.g. 'Last refreshed: 2026-07-31 21:43'
    """
    return f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
