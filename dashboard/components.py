"""
components.py - UI Components
================================
Retail Sales ETL & Analytics Platform  |  Phase 10

Responsibilities:
    - Render the sidebar (navigation, filters, refresh button).
    - Render KPI metric cards using st.metric.
    - Provide a reusable 'empty data' warning widget.
"""

import pandas as pd
import streamlit as st

from utils import fmt_currency, fmt_number, fmt_percent, get_kpis, last_refresh_label
from database import load_all_data


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar(df: pd.DataFrame) -> dict:
    """Render the sidebar navigation, filters, and refresh button.

    Builds multi-select filter widgets from the unique values available
    in the loaded DataFrame. Returns the user's current filter selections
    so the active page can apply them to its data.

    Args:
        df (pd.DataFrame): The full (unfiltered) sales DataFrame.

    Returns:
        dict: Contains keys: page, regions, categories, segments, ship_modes.
              'page' is the currently selected page name (str).
              All filter keys are lists of selected values.
    """
    with st.sidebar:
        # -- Branding --------------------------------------------------------
        st.markdown("## Retail Sales")
        st.markdown("### ETL & Analytics Platform")
        st.divider()

        # -- Navigation ------------------------------------------------------
        st.markdown("**Navigate**")
        page = st.radio(
            label="Page",
            options=[
                "Executive Dashboard",
                "Sales Performance",
                "Product Analysis",
                "Customer Insights",
            ],
            label_visibility="collapsed",
        )
        st.divider()

        # -- Filters ---------------------------------------------------------
        st.markdown("**Filters**")

        regions = st.multiselect(
            "Region",
            options=sorted(df["region"].dropna().unique().tolist()),
            default=[],
            placeholder="All regions",
        )

        categories = st.multiselect(
            "Category",
            options=sorted(df["category"].dropna().unique().tolist()),
            default=[],
            placeholder="All categories",
        )

        segments = st.multiselect(
            "Segment",
            options=sorted(df["segment"].dropna().unique().tolist()),
            default=[],
            placeholder="All segments",
        )

        ship_modes = st.multiselect(
            "Ship Mode",
            options=sorted(df["ship_mode"].dropna().unique().tolist()),
            default=[],
            placeholder="All ship modes",
        )

        st.divider()

        # -- Refresh button --------------------------------------------------
        if st.button("Refresh Data", use_container_width=True):
            # Clear all cached data so the next query hits the database fresh
            st.cache_data.clear()
            st.rerun()

        st.caption(last_refresh_label())

    return {
        "page": page,
        "regions": regions,
        "categories": categories,
        "segments": segments,
        "ship_modes": ship_modes,
    }


# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

def render_kpi_cards(df: pd.DataFrame) -> None:
    """Render the five headline KPI metric cards in a single row.

    Uses st.metric for the standard Streamlit card style. Each card
    shows the KPI name and its formatted value.

    Args:
        df (pd.DataFrame): The filtered sales DataFrame.

    Returns:
        None
    """
    kpis = get_kpis(df)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Revenue",
            value=fmt_currency(kpis["total_revenue"]),
        )
    with col2:
        st.metric(
            label="Total Profit",
            value=fmt_currency(kpis["total_profit"]),
        )
    with col3:
        st.metric(
            label="Total Orders",
            value=fmt_number(kpis["total_orders"]),
        )
    with col4:
        st.metric(
            label="Avg Order Value",
            value=fmt_currency(kpis["avg_order_value"]),
        )
    with col5:
        st.metric(
            label="Avg Profit Margin",
            value=fmt_percent(kpis["avg_profit_margin"]),
        )


# ---------------------------------------------------------------------------
# Reusable empty-data warning
# ---------------------------------------------------------------------------

def warn_empty(df: pd.DataFrame, label: str = "data") -> bool:
    """Display a warning and return True when the DataFrame is empty.

    Use this guard at the top of every chart section to avoid rendering
    empty Plotly figures.

    Args:
        df (pd.DataFrame): The DataFrame to check.
        label (str): Human-readable name for the data (shown in warning).

    Returns:
        bool: True if df is empty, False otherwise.

    Example:
        >>> if warn_empty(df): return
    """
    if df.empty:
        st.warning(f"No {label} found for the current filter selection.")
        return True
    return False
