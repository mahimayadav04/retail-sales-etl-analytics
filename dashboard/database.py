"""
database.py - Dashboard Database Layer (CSV & On-the-fly Transformation Fallback)
===================================================================================
Retail Sales ETL & Analytics Platform  |  Phase 10

Primary mode  : Reads from PostgreSQL using credentials in .env
Fallback 1    : Reads the cleaned CSV from data/processed/retail_sales_cleaned.csv
Fallback 2    : Automatically runs the extraction & transformation on data/raw/retail_sales.csv
"""

import os
import sys
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

# Ensure scripts directory is in sys.path for fallback transformations
_SCRIPTS_DIR = os.path.join(_PROJECT_ROOT, "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

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
    """Load the sales dataset from PostgreSQL, cleaned CSV, or on-the-fly ETL.

    Strategy:
        1. If .env exists with DB variables → try PostgreSQL.
        2. Else if data/processed/retail_sales_cleaned.csv exists → read CSV.
        3. Else → run transformation module on data/raw/retail_sales.csv on the fly.

    Returns:
        pd.DataFrame: The full sales dataset.
    """
    # ── 1. Try PostgreSQL ───────────────────────────────────────────────────
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

    # ── 2. Fall back to cleaned CSV ─────────────────────────────────────────
    if os.path.isfile(_CSV_PATH):
        df = pd.read_csv(_CSV_PATH)
        st.sidebar.info("Data source: cleaned CSV")
        return df

    # ── 3. On-the-fly transformation fallback ───────────────────────────────
    try:
        from extract import extract_data
        from transform import transform_data, save_cleaned_dataset

        df_raw = extract_data()
        df_clean = transform_data(df_raw)
        save_cleaned_dataset(df_clean)
        st.sidebar.info("Data source: Cleaned on-the-fly")
        return df_clean
    except Exception as e:
        st.error(f"**Data transformation failed:** `{e}`")

    # ── 4. Nothing available ────────────────────────────────────────────────
    st.error(
        "**No data source found.**\n\n"
        f"Expected raw CSV or cleaned CSV in data/ directory.\n\n"
        "Please ensure `data/raw/retail_sales.csv` exists in the repository."
    )
    return pd.DataFrame()


def run_query(sql: str) -> pd.DataFrame:
    """Run a raw SQL query against PostgreSQL (PostgreSQL mode only)."""
    try:
        from sqlalchemy import text
        engine = _get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()
