"""
charts.py - Plotly Chart Functions
=====================================
Retail Sales ETL & Analytics Platform  |  Phase 10

Responsibilities:
    - One function per chart, each returning a Plotly Figure.
    - All charts share a consistent color palette and layout style.
    - No Streamlit calls inside this module — charts are rendered in app.py.
      This keeps chart logic fully testable and reusable.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Shared style constants
# ---------------------------------------------------------------------------

PALETTE = px.colors.qualitative.Set2          # Consistent colour palette
BG_COLOR = "rgba(0,0,0,0)"                    # Transparent background
FONT_COLOR = "#2c3e50"
FONT_FAMILY = "Inter, Helvetica, Arial, sans-serif"

_LAYOUT = dict(
    plot_bgcolor=BG_COLOR,
    paper_bgcolor=BG_COLOR,
    font=dict(family=FONT_FAMILY, color=FONT_COLOR, size=13),
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="right", x=1),
)


def _apply_layout(fig: go.Figure, title: str) -> go.Figure:
    """Apply the shared layout and title to any Plotly figure."""
    fig.update_layout(title=dict(text=title, font=dict(size=16, color=FONT_COLOR)), **_LAYOUT)
    return fig


# ---------------------------------------------------------------------------
# Revenue trend
# ---------------------------------------------------------------------------

def chart_revenue_by_region(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart: total revenue by region."""
    agg = (
        df.groupby("region", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue")
    )
    fig = px.bar(
        agg,
        x="revenue",
        y="region",
        orientation="h",
        color="region",
        color_discrete_sequence=PALETTE,
        labels={"revenue": "Revenue ($)", "region": "Region"},
        text_auto=".2s",
    )
    fig.update_traces(textposition="outside")
    return _apply_layout(fig, "Revenue by Region")


def chart_revenue_by_category(df: pd.DataFrame) -> go.Figure:
    """Donut chart: revenue split by product category."""
    agg = df.groupby("category", as_index=False)["revenue"].sum()
    fig = px.pie(
        agg,
        names="category",
        values="revenue",
        hole=0.45,
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(textinfo="percent+label", pull=[0.03] * len(agg))
    return _apply_layout(fig, "Revenue by Category")


def chart_revenue_by_segment(df: pd.DataFrame) -> go.Figure:
    """Bar chart: revenue and profit by customer segment."""
    agg = (
        df.groupby("segment", as_index=False)
        .agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
        .sort_values("revenue", ascending=False)
    )
    fig = go.Figure()
    fig.add_bar(name="Revenue", x=agg["segment"], y=agg["revenue"],
                marker_color=PALETTE[0], text=agg["revenue"].apply(lambda v: f"${v:,.0f}"),
                textposition="outside")
    fig.add_bar(name="Profit", x=agg["segment"], y=agg["profit"],
                marker_color=PALETTE[1], text=agg["profit"].apply(lambda v: f"${v:,.0f}"),
                textposition="outside")
    fig.update_layout(barmode="group", xaxis_title="Segment", yaxis_title="Amount ($)")
    return _apply_layout(fig, "Revenue & Profit by Customer Segment")


def chart_top_subcategories(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Horizontal bar chart: top N sub-categories by revenue."""
    agg = (
        df.groupby("sub_category", as_index=False)["revenue"]
        .sum()
        .nlargest(n, "revenue")
        .sort_values("revenue")
    )
    fig = px.bar(
        agg,
        x="revenue",
        y="sub_category",
        orientation="h",
        color="revenue",
        color_continuous_scale="Blues",
        labels={"revenue": "Revenue ($)", "sub_category": "Sub-Category"},
        text_auto=".2s",
    )
    fig.update_traces(textposition="outside")
    fig.update_coloraxes(showscale=False)
    return _apply_layout(fig, f"Top {n} Sub-Categories by Revenue")


# ---------------------------------------------------------------------------
# Sales performance
# ---------------------------------------------------------------------------

def chart_sales_by_state(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart: top 15 states by revenue."""
    agg = (
        df.groupby("state", as_index=False)["revenue"]
        .sum()
        .nlargest(15, "revenue")
        .sort_values("revenue")
    )
    fig = px.bar(
        agg,
        x="revenue",
        y="state",
        orientation="h",
        color="revenue",
        color_continuous_scale="Teal",
        labels={"revenue": "Revenue ($)", "state": "State"},
        text_auto=".2s",
    )
    fig.update_coloraxes(showscale=False)
    return _apply_layout(fig, "Top 15 States by Revenue")


def chart_ship_mode(df: pd.DataFrame) -> go.Figure:
    """Pie chart: order count and revenue by ship mode."""
    agg = (
        df.groupby("ship_mode", as_index=False)
        .agg(orders=("revenue", "count"), revenue=("revenue", "sum"))
    )
    fig = px.pie(
        agg,
        names="ship_mode",
        values="revenue",
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(textinfo="percent+label")
    return _apply_layout(fig, "Revenue by Ship Mode")


# ---------------------------------------------------------------------------
# Product analysis
# ---------------------------------------------------------------------------

def chart_profit_by_category(df: pd.DataFrame) -> go.Figure:
    """Bar chart: profit by category."""
    agg = (
        df.groupby("category", as_index=False)["profit"]
        .sum()
        .sort_values("profit", ascending=False)
    )
    colors = [PALETTE[0] if v >= 0 else "#e74c3c" for v in agg["profit"]]
    fig = go.Figure(go.Bar(
        x=agg["category"],
        y=agg["profit"],
        marker_color=colors,
        text=[f"${v:,.0f}" for v in agg["profit"]],
        textposition="outside",
    ))
    fig.update_layout(xaxis_title="Category", yaxis_title="Profit ($)")
    return _apply_layout(fig, "Profit by Category")


def chart_profit_margin_by_category(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart: average profit margin by category."""
    agg = (
        df.groupby("category", as_index=False)["profit_margin"]
        .mean()
        .sort_values("profit_margin")
    )
    fig = px.bar(
        agg,
        x="profit_margin",
        y="category",
        orientation="h",
        color="profit_margin",
        color_continuous_scale="RdYlGn",
        labels={"profit_margin": "Avg Margin (%)", "category": "Category"},
        text_auto=".1f",
    )
    fig.update_coloraxes(showscale=False)
    return _apply_layout(fig, "Average Profit Margin by Category")


def chart_discount_by_category(df: pd.DataFrame) -> go.Figure:
    """Bar chart: average discount rate by category."""
    agg = (
        df.groupby("category", as_index=False)["discount"]
        .mean()
        .sort_values("discount", ascending=False)
    )
    agg["discount_pct"] = (agg["discount"] * 100).round(2)
    fig = px.bar(
        agg,
        x="category",
        y="discount_pct",
        color="category",
        color_discrete_sequence=PALETTE,
        labels={"discount_pct": "Avg Discount (%)", "category": "Category"},
        text_auto=".1f",
    )
    fig.update_traces(textposition="outside")
    return _apply_layout(fig, "Average Discount Rate by Category")


def chart_top_products_revenue(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Horizontal bar chart: top N sub-categories by revenue."""
    return chart_top_subcategories(df, n)


def chart_bottom_products_profit(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Horizontal bar chart: bottom N sub-categories by profit (loss makers)."""
    agg = (
        df.groupby("sub_category", as_index=False)["profit"]
        .sum()
        .nsmallest(n, "profit")
        .sort_values("profit")
    )
    colors = [PALETTE[0] if v >= 0 else "#e74c3c" for v in agg["profit"]]
    fig = go.Figure(go.Bar(
        x=agg["profit"],
        y=agg["sub_category"],
        orientation="h",
        marker_color=colors,
        text=[f"${v:,.0f}" for v in agg["profit"]],
        textposition="outside",
    ))
    fig.update_layout(xaxis_title="Total Profit ($)", yaxis_title="Sub-Category")
    return _apply_layout(fig, f"Bottom {n} Sub-Categories by Profit")


def chart_category_treemap(df: pd.DataFrame) -> go.Figure:
    """Treemap: revenue distribution across category and sub-category."""
    agg = (
        df.groupby(["category", "sub_category"], as_index=False)["revenue"]
        .sum()
    )
    fig = px.treemap(
        agg,
        path=["category", "sub_category"],
        values="revenue",
        color="revenue",
        color_continuous_scale="Blues",
        labels={"revenue": "Revenue ($)"},
    )
    fig.update_coloraxes(showscale=False)
    return _apply_layout(fig, "Revenue Distribution (Category & Sub-Category)")


# ---------------------------------------------------------------------------
# Customer insights
# ---------------------------------------------------------------------------

def chart_top_cities(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Horizontal bar chart: top N cities by revenue."""
    agg = (
        df.groupby("city", as_index=False)["revenue"]
        .sum()
        .nlargest(n, "revenue")
        .sort_values("revenue")
    )
    fig = px.bar(
        agg,
        x="revenue",
        y="city",
        orientation="h",
        color="revenue",
        color_continuous_scale="Purples",
        labels={"revenue": "Revenue ($)", "city": "City"},
        text_auto=".2s",
    )
    fig.update_coloraxes(showscale=False)
    return _apply_layout(fig, f"Top {n} Cities by Revenue")


def chart_segment_orders(df: pd.DataFrame) -> go.Figure:
    """Donut chart: share of orders by customer segment."""
    agg = df.groupby("segment", as_index=False).size().rename(columns={"size": "orders"})
    fig = px.pie(
        agg,
        names="segment",
        values="orders",
        hole=0.45,
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(textinfo="percent+label")
    return _apply_layout(fig, "Order Share by Customer Segment")


def chart_avg_order_by_segment(df: pd.DataFrame) -> go.Figure:
    """Bar chart: average order value by customer segment."""
    agg = (
        df.groupby("segment", as_index=False)["revenue"]
        .mean()
        .rename(columns={"revenue": "avg_order"})
        .sort_values("avg_order", ascending=False)
    )
    fig = px.bar(
        agg,
        x="segment",
        y="avg_order",
        color="segment",
        color_discrete_sequence=PALETTE,
        labels={"avg_order": "Avg Order Value ($)", "segment": "Segment"},
        text_auto=".2s",
    )
    fig.update_traces(textposition="outside")
    return _apply_layout(fig, "Average Order Value by Segment")


def chart_profit_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter plot: sales vs profit coloured by category."""
    sample = df.sample(min(len(df), 2000), random_state=42)  # cap for performance
    fig = px.scatter(
        sample,
        x="sales",
        y="profit",
        color="category",
        color_discrete_sequence=PALETTE,
        opacity=0.55,
        labels={"sales": "Sales ($)", "profit": "Profit ($)", "category": "Category"},
        hover_data=["sub_category", "region", "discount"],
    )
    return _apply_layout(fig, "Sales vs Profit by Category")


def chart_discount_vs_margin(df: pd.DataFrame) -> go.Figure:
    """Scatter plot: discount vs profit margin to visualise discount erosion."""
    sample = df.sample(min(len(df), 2000), random_state=42)
    
    kwargs = dict(
        x="discount",
        y="profit_margin",
        color="category",
        color_discrete_sequence=PALETTE,
        opacity=0.55,
        labels={
            "discount": "Discount Rate",
            "profit_margin": "Profit Margin (%)",
            "category": "Category",
        },
        hover_data=["sub_category"],
    )

    try:
        import statsmodels.api  # noqa: F401
        fig = px.scatter(sample, trendline="ols", **kwargs)
    except Exception:
        fig = px.scatter(sample, **kwargs)

    return _apply_layout(fig, "Discount Rate vs Profit Margin")
