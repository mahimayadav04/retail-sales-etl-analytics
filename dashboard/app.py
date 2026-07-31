"""
app.py - Main Streamlit Dashboard
=====================================
Retail Sales ETL & Analytics Platform  |  Phase 10

Entry point for the interactive dashboard.
Run with:  streamlit run dashboard/app.py

Pages:
    1. Executive Dashboard  - headline KPIs + top-level charts
    2. Sales Performance    - geographic and segment breakdown
    3. Product Analysis     - category/sub-category deep dive
    4. Customer Insights    - segment, city, and shipping analysis

Architecture:
    - database.py  -> loads data from PostgreSQL (cached)
    - utils.py     -> formatting and filtering helpers
    - components.py-> sidebar, KPI cards, empty-data guards
    - charts.py    -> one Plotly figure per function (no st calls)
    - app.py       -> assembles pages and calls st.plotly_chart()
"""

import os
import sys

import streamlit as st

# ---------------------------------------------------------------------------
# Make sibling modules importable when launched via 'streamlit run dashboard/app.py'
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import load_all_data
from utils import apply_filters, last_refresh_label
from components import render_sidebar, render_kpi_cards, warn_empty
from charts import (
    chart_revenue_by_region,
    chart_revenue_by_category,
    chart_revenue_by_segment,
    chart_top_subcategories,
    chart_sales_by_state,
    chart_ship_mode,
    chart_profit_by_category,
    chart_profit_margin_by_category,
    chart_discount_by_category,
    chart_top_products_revenue,
    chart_bottom_products_profit,
    chart_category_treemap,
    chart_top_cities,
    chart_segment_orders,
    chart_avg_order_by_segment,
    chart_profit_scatter,
    chart_discount_vs_margin,
)


# ---------------------------------------------------------------------------
# Page configuration (must be the first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Retail Sales Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Light custom CSS — tighten spacing and style metric cards
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Remove default top padding */
    .block-container { padding-top: 1.5rem; }

    /* Style metric cards */
    [data-testid="stMetric"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 0.75rem 1rem;
    }
    [data-testid="stMetricLabel"] { font-size: 0.82rem; color: #6c757d; }
    [data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: 700; color: #2c3e50; }

    /* Divider colour */
    hr { border-color: #dee2e6; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Load data once  (cached by database.py - re-fetches only on Refresh)
# ---------------------------------------------------------------------------
with st.spinner("Loading data from PostgreSQL..."):
    df_all = load_all_data()

if df_all.empty:
    st.error(
        "**No data found.** Make sure the ETL pipeline has run successfully "
        "and the 'sales' table exists in PostgreSQL."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar: navigation + filters
# ---------------------------------------------------------------------------
sidebar = render_sidebar(df_all)
page: str = sidebar["page"]

# Apply sidebar filters to produce the working DataFrame for the active page
df = apply_filters(
    df_all,
    regions=sidebar["regions"],
    categories=sidebar["categories"],
    segments=sidebar["segments"],
    ship_modes=sidebar["ship_modes"],
)


# ===========================================================================
# PAGE 1 — Executive Dashboard
# ===========================================================================

def page_executive():
    """Render the Executive Dashboard page."""
    st.title("Executive Dashboard")
    st.caption(last_refresh_label())

    if warn_empty(df):
        return

    # -- KPI cards -----------------------------------------------------------
    st.subheader("Key Performance Indicators")
    render_kpi_cards(df)

    st.divider()

    # -- Row 1: Revenue by Region | Revenue by Category ----------------------
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(chart_revenue_by_region(df), use_container_width=True)
    with col_b:
        st.plotly_chart(chart_revenue_by_category(df), use_container_width=True)

    # -- Row 2: Revenue by Segment | Top Sub-Categories ----------------------
    col_c, col_d = st.columns(2)
    with col_c:
        st.plotly_chart(chart_revenue_by_segment(df), use_container_width=True)
    with col_d:
        st.plotly_chart(chart_top_subcategories(df, n=10), use_container_width=True)

    # -- Data summary expander -----------------------------------------------
    with st.expander("Raw Data Preview"):
        st.dataframe(
            df[["ship_mode", "segment", "region", "category",
                "sub_category", "sales", "quantity", "discount",
                "profit", "profit_margin"]].head(200),
            use_container_width=True,
        )


# ===========================================================================
# PAGE 2 — Sales Performance
# ===========================================================================

def page_sales_performance():
    """Render the Sales Performance page."""
    st.title("Sales Performance")
    st.caption(last_refresh_label())

    if warn_empty(df):
        return

    # -- KPI cards -----------------------------------------------------------
    st.subheader("Performance Summary")
    render_kpi_cards(df)

    st.divider()

    # -- Row 1: Top States | Ship Mode ---------------------------------------
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.plotly_chart(chart_sales_by_state(df), use_container_width=True)
    with col_b:
        st.plotly_chart(chart_ship_mode(df), use_container_width=True)

    # -- Row 2: Segment breakdown | Sales vs Profit --------------------------
    col_c, col_d = st.columns(2)
    with col_c:
        st.plotly_chart(chart_revenue_by_segment(df), use_container_width=True)
    with col_d:
        st.plotly_chart(chart_profit_scatter(df), use_container_width=True)

    # -- Discount vs Margin full width ---------------------------------------
    st.plotly_chart(chart_discount_vs_margin(df), use_container_width=True)

    # -- Sortable data table -------------------------------------------------
    st.subheader("Detailed Sales Table")
    display_cols = [
        "ship_mode", "segment", "city", "state", "region",
        "category", "sub_category", "sales", "quantity",
        "discount", "profit", "profit_margin",
    ]
    st.dataframe(
        df[display_cols]
        .sort_values("sales", ascending=False)
        .reset_index(drop=True),
        use_container_width=True,
    )


# ===========================================================================
# PAGE 3 — Product Analysis
# ===========================================================================

def page_product_analysis():
    """Render the Product Analysis page."""
    st.title("Product Analysis")
    st.caption(last_refresh_label())

    if warn_empty(df):
        return

    # -- KPI cards -----------------------------------------------------------
    st.subheader("Product KPIs")
    render_kpi_cards(df)

    st.divider()

    # -- Treemap: full width --------------------------------------------------
    st.plotly_chart(chart_category_treemap(df), use_container_width=True)

    # -- Row 1: Top products | Bottom products --------------------------------
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(chart_top_products_revenue(df, n=10), use_container_width=True)
    with col_b:
        st.plotly_chart(chart_bottom_products_profit(df, n=10), use_container_width=True)

    # -- Row 2: Profit by category | Margin by category ----------------------
    col_c, col_d = st.columns(2)
    with col_c:
        st.plotly_chart(chart_profit_by_category(df), use_container_width=True)
    with col_d:
        st.plotly_chart(chart_profit_margin_by_category(df), use_container_width=True)

    # -- Average discount by category full width -----------------------------
    st.plotly_chart(chart_discount_by_category(df), use_container_width=True)

    # -- Category breakdown table --------------------------------------------
    with st.expander("Category Summary Table"):
        cat_summary = (
            df.groupby(["category", "sub_category"], as_index=False)
            .agg(
                orders=("revenue", "count"),
                total_revenue=("revenue", "sum"),
                total_profit=("profit", "sum"),
                avg_margin=("profit_margin", "mean"),
                avg_discount=("discount", "mean"),
            )
            .sort_values("total_revenue", ascending=False)
        )
        cat_summary["total_revenue"] = cat_summary["total_revenue"].round(2)
        cat_summary["total_profit"] = cat_summary["total_profit"].round(2)
        cat_summary["avg_margin"] = cat_summary["avg_margin"].round(2)
        cat_summary["avg_discount"] = (cat_summary["avg_discount"] * 100).round(2)
        st.dataframe(cat_summary, use_container_width=True)


# ===========================================================================
# PAGE 4 — Customer Insights
# ===========================================================================

def page_customer_insights():
    """Render the Customer Insights page."""
    st.title("Customer Insights")
    st.caption(last_refresh_label())

    if warn_empty(df):
        return

    # -- KPI cards -----------------------------------------------------------
    st.subheader("Customer KPIs")
    render_kpi_cards(df)

    st.divider()

    # -- Row 1: Top cities | Segment order share -----------------------------
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.plotly_chart(chart_top_cities(df, n=10), use_container_width=True)
    with col_b:
        st.plotly_chart(chart_segment_orders(df), use_container_width=True)

    # -- Row 2: Avg order by segment | Revenue by ship mode ------------------
    col_c, col_d = st.columns(2)
    with col_c:
        st.plotly_chart(chart_avg_order_by_segment(df), use_container_width=True)
    with col_d:
        st.plotly_chart(chart_ship_mode(df), use_container_width=True)

    # -- Revenue by segment full width ---------------------------------------
    st.plotly_chart(chart_revenue_by_segment(df), use_container_width=True)

    # -- Customer contribution table -----------------------------------------
    with st.expander("Revenue by Region & Segment"):
        region_seg = (
            df.groupby(["region", "segment"], as_index=False)
            .agg(
                orders=("revenue", "count"),
                total_revenue=("revenue", "sum"),
                total_profit=("profit", "sum"),
            )
            .sort_values("total_revenue", ascending=False)
        )
        region_seg["total_revenue"] = region_seg["total_revenue"].round(2)
        region_seg["total_profit"] = region_seg["total_profit"].round(2)
        st.dataframe(region_seg, use_container_width=True)


# ===========================================================================
# Page router
# ===========================================================================

PAGE_MAP = {
    "Executive Dashboard": page_executive,
    "Sales Performance": page_sales_performance,
    "Product Analysis": page_product_analysis,
    "Customer Insights": page_customer_insights,
}

# Call the function for the page the user selected in the sidebar
PAGE_MAP[page]()
