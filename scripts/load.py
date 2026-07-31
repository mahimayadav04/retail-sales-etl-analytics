"""
load.py - Phase 7: Load Module
================================
Retail Sales ETL & Analytics Pipeline

Responsibilities:
    - Read database credentials from the .env file.
    - Create a SQLAlchemy engine to connect to PostgreSQL.
    - Verify the database connection.
    - Read the cleaned CSV from data/processed/.
    - Load (insert) the cleaned data into the PostgreSQL 'sales' table.
    - Verify the load by querying the total row count.
    - Display a summary: rows loaded, execution time, success message.

Usage:
    python scripts/load.py

Prerequisites:
    1. PostgreSQL is running.
    2. The target database exists (e.g. CREATE DATABASE retail_sales_db;).
    3. A .env file exists in the project root with the correct credentials.
    4. The cleaned CSV exists at data/processed/retail_sales_cleaned.csv.
       (Run transform.py first if it does not exist.)

Author  : Retail Sales ETL Project
Phase   : 7 - Load
"""

import os
import sys
import time

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Path to the cleaned dataset that will be loaded into the database
CLEANED_CSV_PATH: str = os.path.join("data", "processed", "retail_sales_cleaned.csv")

# PostgreSQL table name where data will be inserted
TABLE_NAME: str = "sales"

SEP: str = "-" * 55  # Plain ASCII separator


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def load_environment() -> dict:
    """Read database credentials from the .env file.

    Loads the .env file located in the project root directory into
    os.environ, then reads each required variable into a dictionary.

    Returns:
        dict: A dictionary with keys:
              db_host, db_port, db_name, db_user, db_password.

    Raises:
        EnvironmentError: If any required variable is missing from .env.

    Example:
        >>> config = load_environment()
    """
    # Look for .env in the project root (one level above scripts/)
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")

    # Load variables from the .env file into os.environ
    load_dotenv(dotenv_path=env_path)

    # Required environment variable names
    required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]

    config: dict = {}
    missing: list = []

    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing.append(var)
        else:
            config[var.lower()] = value

    if missing:
        raise EnvironmentError(
            f"\n[ERROR] Missing environment variables: {missing}\n"
            "Please create a .env file in the project root.\n"
            "Refer to .env.example for the required variables."
        )

    print("[OK] Environment variables loaded successfully.")
    return config


def create_connection(config: dict):
    """Build a SQLAlchemy engine and verify the database connection.

    Uses the credentials from the config dict to construct a PostgreSQL
    connection URL, then creates a SQLAlchemy engine. A lightweight
    connection test is run immediately to confirm the database is reachable.

    Args:
        config (dict): Database credentials as returned by load_environment().

    Returns:
        sqlalchemy.engine.Engine: A connected SQLAlchemy engine.

    Raises:
        OperationalError: If the database cannot be reached (wrong host,
                          port, credentials, or database name).
        SQLAlchemyError: For any other SQLAlchemy-level error.

    Example:
        >>> engine = create_connection(config)
    """
    # Build the PostgreSQL connection URL
    # Format: postgresql+psycopg2://user:password@host:port/dbname
    connection_url: str = (
        f"postgresql+psycopg2://"
        f"{config['db_user']}:{config['db_password']}"
        f"@{config['db_host']}:{config['db_port']}"
        f"/{config['db_name']}"
    )

    # Create the SQLAlchemy engine (lazy - does not connect yet)
    engine = create_engine(connection_url)

    # Test the connection immediately with a trivial query
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    print(
        f"[OK] Database connected successfully.\n"
        f"     Host : {config['db_host']}:{config['db_port']}\n"
        f"     DB   : {config['db_name']}"
    )
    return engine


def read_clean_dataset(file_path: str = CLEANED_CSV_PATH) -> pd.DataFrame:
    """Read the cleaned CSV file into a pandas DataFrame.

    Args:
        file_path (str): Path to the cleaned CSV. Defaults to CLEANED_CSV_PATH.

    Returns:
        pd.DataFrame: The cleaned dataset ready for database insertion.

    Raises:
        FileNotFoundError: If the cleaned CSV does not exist.
        Exception: For any other unexpected error while reading.

    Example:
        >>> df = read_clean_dataset()
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"\n[ERROR] Cleaned dataset not found at: '{file_path}'\n"
            "Please run 'python scripts/transform.py' first to generate it."
        )

    df: pd.DataFrame = pd.read_csv(file_path)

    print(f"[OK] Cleaned dataset loaded : {len(df):,} rows, {df.shape[1]} columns.")
    return df


def load_dataframe(df: pd.DataFrame, engine, table_name: str = TABLE_NAME) -> None:
    """Insert the DataFrame into the PostgreSQL table.

    Uses pandas to_sql() with if_exists='replace', which:
        - Drops the existing table if it already exists.
        - Creates a new table matching the DataFrame's schema.
        - Inserts all rows in one operation.

    Args:
        df (pd.DataFrame): The cleaned DataFrame to load.
        engine: A connected SQLAlchemy engine.
        table_name (str): Target PostgreSQL table name. Defaults to TABLE_NAME.

    Returns:
        None

    Raises:
        SQLAlchemyError: If the insert operation fails.

    Example:
        >>> load_dataframe(df, engine)
    """
    print(f"\n[INFO] Loading {len(df):,} rows into table '{table_name}'...")

    # if_exists='replace' : drops and recreates the table on each run.
    # index=False         : do not write the pandas row index as a column.
    # method='multi'      : inserts multiple rows per SQL statement (faster).
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="replace",
        index=False,
        method="multi",
    )

    print(f"[OK] Data inserted into table '{table_name}' successfully.")


def verify_load(engine, table_name: str = TABLE_NAME) -> int:
    """Run SELECT COUNT(*) on the target table to confirm row count.

    Args:
        engine: A connected SQLAlchemy engine.
        table_name (str): The table to count. Defaults to TABLE_NAME.

    Returns:
        int: The total number of rows currently in the table.

    Example:
        >>> count = verify_load(engine)
    """
    # text() wraps a raw SQL string so SQLAlchemy handles it safely
    query = text(f"SELECT COUNT(*) FROM {table_name};")

    with engine.connect() as conn:
        result = conn.execute(query)
        row_count: int = result.scalar()  # .scalar() returns the single value

    print(f"\n[OK] Verification query: SELECT COUNT(*) FROM {table_name}")
    print(f"     Total records in database : {row_count:,}")

    return row_count


def main() -> None:
    """Entry point when load.py is run directly from the command line.

    Orchestrates the full load process:
        1. Load environment variables from .env.
        2. Connect to PostgreSQL.
        3. Read the cleaned CSV.
        4. Insert data into the database.
        5. Verify the row count.
        6. Print a summary.

    Returns:
        None
    """
    # Track total execution time
    start_time: float = time.time()

    print(SEP)
    print("  LOAD MODULE - Phase 7")
    print(SEP)

    try:
        # Step 1 - Load credentials from .env
        config: dict = load_environment()

        # Step 2 - Connect to PostgreSQL
        engine = create_connection(config)

        # Step 3 - Read the cleaned dataset
        df: pd.DataFrame = read_clean_dataset()

        # Step 4 - Load the DataFrame into the database
        load_dataframe(df, engine)

        # Step 5 - Verify the row count
        row_count: int = verify_load(engine)

        # Step 6 - Print final summary
        elapsed: float = round(time.time() - start_time, 2)

        print(f"\n{SEP}")
        print("  LOAD SUMMARY")
        print(SEP)
        print(f"   Rows Loaded     : {row_count:,}")
        print(f"   Table           : {TABLE_NAME}")
        print(f"   Execution Time  : {elapsed} seconds")
        print(f"   Status          : SUCCESS")
        print(SEP)

    except EnvironmentError as e:
        # .env missing or incomplete
        print(e)
        sys.exit(1)

    except OperationalError as e:
        # Database is unreachable or credentials are wrong
        print(
            "\n[ERROR] Could not connect to the database.\n"
            "Check that PostgreSQL is running and that your .env credentials are correct.\n"
            f"Details: {e}"
        )
        sys.exit(1)

    except FileNotFoundError as e:
        # Cleaned CSV does not exist
        print(e)
        sys.exit(1)

    except PermissionError as e:
        # File or database permission denied
        print(
            f"\n[ERROR] Permission denied.\n"
            f"Details: {e}"
        )
        sys.exit(1)

    except SQLAlchemyError as e:
        # Any other SQLAlchemy / database error
        print(
            f"\n[ERROR] A database error occurred.\n"
            f"Details: {e}"
        )
        sys.exit(1)

    except Exception as e:
        # Catch-all for any other unexpected error
        print(
            f"\n[ERROR] An unexpected error occurred.\n"
            f"Details: {e}"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Script Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
