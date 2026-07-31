"""
database.py - Dashboard Database Layer (CSV Fallback Mode)
============================================================
Retail Sales ETL & Analytics Platform  |  Phase 10

Primary mode  : Reads from PostgreSQL using credentials in .env
Fallback mode : If .env is missing or DB is unreachable, reads the
                cleaned CSV from data/processed/retail_sales_cleaned.csv

This means the dashboard works even without a running PostgreSQL instance.
"""

import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT  = os.path.abspath(os.path.join(_DASHBOARD_DIR, ".."))
_ENV_PATH      = os.path.join(_PROJECT_ROOT, ".env")
_CSV_PATH      = os.path.join(_PROJECT_ROOT, "data", "processed", "retail_sales_cleaned.csv")

load_dotenv(dotenv_path=_ENV_PATH)


# ---------------------------------------------------------------------------
# Determine data source
# ---------------------------------------------------------------------------

def _has_db_config() -> bool:
    """Return True only when all five DB env-vars are present in .env."""
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    return all(os.getenv(v) for v in required)


@st.cache_resource(show_spinner=False)
def _get_engine():
    """Build and return a cached SQLAlchemy engine (PostgreSQL mode only)."""
    from sqlalchemy import create_engine, text
    url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
        f"/{os.getenv('DB_NAME')}"
    )
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading data...", ttl=300)
def load_all_data() -> pd.DataFrame:
    """Load the sales dataset from PostgreSQL (if available) or the CSV fallback.

    Strategy:
        1. If .env exists with all DB variables → try PostgreSQL.
        2. If the DB connection fails → fall back to the cleaned CSV.
        3. If .env is missing → go straight to the cleaned CSV.

    Returns:
        pd.DataFrame: The full sales dataset.
    """
    # ── Try PostgreSQL ───────────────────────────────────────────────────────
    if _has_db_config():
        try:
            from sqlalchemy import text
            engine = _get_engine()
            with engine.connect() as conn:
                df = pd.read_sql(
                    text("SELECT * FROM sales ORDER BY revenue DESC;"),
                    conn,
                )
            st.sidebar.success("Connected to PostgreSQL")
            return df
        except Exception:
            st.sidebar.warning("DB unavailable — using CSV data")

    # ── Fall back to cleaned CSV ─────────────────────────────────────────────
    if os.path.isfile(_CSV_PATH):
        df = pd.read_csv(_CSV_PATH)
        st.sidebar.info("Data source: cleaned CSV")
        return df

    # ── Nothing available ────────────────────────────────────────────────────
    st.error(
        "**No data source found.**\n\n"
        f"Expected the cleaned CSV at:\n`{_CSV_PATH}`\n\n"
        "Run `python scripts/transform.py` first to generate it."
    )
    return pd.DataFrame()


def run_query(sql: str) -> pd.DataFrame:
    """Run a raw SQL query against PostgreSQL (PostgreSQL mode only).

    Not called by the dashboard pages — kept here for advanced use.
    """
    try:
        from sqlalchemy import text
        engine = _get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()
