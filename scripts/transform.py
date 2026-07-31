"""
transform.py - Phase 5: Transformation Module
===============================================
Retail Sales ETL & Analytics Pipeline

Responsibilities:
    - Load the validated raw DataFrame from the extract module.
    - Remove duplicate rows.
    - Handle missing values with sensible defaults.
    - Convert date columns to proper datetime objects.
    - Standardize text columns (trim spaces, Title Case).
    - Rename columns to snake_case.
    - Create new calculated columns (revenue, profit_margin, year, month, quarter).
    - Save the cleaned dataset to data/processed/retail_sales_cleaned.csv.
    - Print a transformation summary.

Usage:
    python scripts/transform.py

Author  : Retail Sales ETL Project
Phase   : 5 - Transformation
"""

import os
import sys

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Allow Python to find the scripts/ folder when running from the project root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from extract import extract_data  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Destination path for the cleaned dataset
PROCESSED_DIR: str = os.path.join("data", "processed")
CLEANED_FILE: str = os.path.join(PROCESSED_DIR, "retail_sales_cleaned.csv")

SEP: str = "-" * 55  # Plain ASCII separator line

# Text columns that should be trimmed and converted to Title Case
TEXT_COLUMNS: list = [
    "Ship Mode", "Segment", "Country", "City",
    "State", "Region", "Category", "Sub-Category",
]

# Columns expected to contain date strings (none exist in the raw dataset by
# default, but the function handles them if they appear in future versions)
DATE_COLUMNS: list = []  # e.g. ["Order Date", "Ship Date"]

# Mapping of original column names to snake_case equivalents.
# Only the columns present in this dataset are listed.
COLUMN_RENAME_MAP: dict = {
    "Ship Mode": "ship_mode",
    "Segment": "segment",
    "Country": "country",
    "City": "city",
    "State": "state",
    "Postal Code": "postal_code",
    "Region": "region",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "profit",
}


# ---------------------------------------------------------------------------
# Transformation Functions
# ---------------------------------------------------------------------------


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove fully duplicate rows from the DataFrame.

    A row is considered a duplicate when every column value matches
    another row exactly. Only the first occurrence is kept.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: A new DataFrame with duplicate rows removed.

    Example:
        >>> df_clean = remove_duplicates(df)
    """
    rows_before: int = len(df)

    # Drop duplicates and reset the index so it stays sequential
    df_clean: pd.DataFrame = df.drop_duplicates().reset_index(drop=True)

    rows_removed: int = rows_before - len(df_clean)
    print(f"   [remove_duplicates]  Rows removed : {rows_removed}")

    return df_clean


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Fill or flag missing values using sensible defaults.

    Strategy (instead of simply dropping all rows with NaN):
        - Numeric columns (Sales, Profit, Discount): fill with 0.0
        - Quantity: fill with 1 (minimum logical order quantity).
        - Text / object columns: fill with "Unknown".

    Args:
        df (pd.DataFrame): The input DataFrame (may contain NaN values).

    Returns:
        pd.DataFrame: A DataFrame with missing values handled.

    Example:
        >>> df_filled = clean_missing_values(df)
    """
    df = df.copy()

    # Identify column types and apply appropriate fill strategies
    for col in df.columns:
        if df[col].dtype == "object":
            # Text columns: replace NaN with a placeholder string
            df[col] = df[col].fillna("Unknown")
        elif col in ("Quantity",):
            # Quantity must be at least 1
            df[col] = df[col].fillna(1)
        else:
            # All other numeric columns: default to 0.0
            df[col] = df[col].fillna(0.0)

    missing_after: int = int(df.isnull().sum().sum())
    print(f"   [clean_missing_values]  Missing cells after fill : {missing_after}")

    return df


def convert_date_columns(df: pd.DataFrame, date_columns: list) -> pd.DataFrame:
    """Convert specified columns from string format to pandas datetime.

    Unparseable values are coerced to NaT (Not a Time) rather than raising
    an error, so the rest of the column is still usable.

    Args:
        df (pd.DataFrame): The input DataFrame.
        date_columns (list): Column names to convert.

    Returns:
        pd.DataFrame: DataFrame with the specified columns as datetime64.

    Example:
        >>> df = convert_date_columns(df, ["Order Date"])
    """
    df = df.copy()

    for col in date_columns:
        if col not in df.columns:
            print(f"   [convert_date_columns]  Column '{col}' not found - skipped.")
            continue

        # errors='coerce' turns bad values into NaT instead of crashing
        df[col] = pd.to_datetime(df[col], errors="coerce")
        invalid_count: int = int(df[col].isnull().sum())
        print(f"   [convert_date_columns]  '{col}' converted | invalid dates : {invalid_count}")

    if not date_columns:
        print("   [convert_date_columns]  No date columns configured - skipped.")

    return df


def standardize_columns(df: pd.DataFrame, text_columns: list) -> pd.DataFrame:
    """Trim whitespace and apply Title Case to specified text columns.

    This makes category values consistent, e.g. "office supplies " becomes
    "Office Supplies".

    Args:
        df (pd.DataFrame): The input DataFrame.
        text_columns (list): Column names to standardize.

    Returns:
        pd.DataFrame: DataFrame with cleaned text columns.

    Example:
        >>> df = standardize_columns(df, ["Category", "Region"])
    """
    df = df.copy()

    for col in text_columns:
        if col not in df.columns:
            continue

        # Strip leading/trailing whitespace, then convert to Title Case
        df[col] = df[col].astype(str).str.strip().str.title()

    print(f"   [standardize_columns]  Standardized {len(text_columns)} text column(s).")

    return df


def rename_columns(df: pd.DataFrame, rename_map: dict) -> pd.DataFrame:
    """Rename DataFrame columns using a provided mapping dictionary.

    Only columns present in the DataFrame are renamed; missing keys in the
    map are silently ignored.

    Args:
        df (pd.DataFrame): The input DataFrame.
        rename_map (dict): Mapping from original column name to new name.

    Returns:
        pd.DataFrame: DataFrame with columns renamed to snake_case.

    Example:
        >>> df = rename_columns(df, {"Ship Mode": "ship_mode"})
    """
    # Only include keys that actually exist in the DataFrame
    safe_map: dict = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=safe_map)

    print(f"   [rename_columns]  Renamed {len(safe_map)} column(s) to snake_case.")

    return df


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create new calculated columns to enrich the dataset.

    New columns added:
        - revenue       : same as sales (explicit alias for clarity in reports)
        - profit_margin : (profit / sales) * 100, rounded to 2 decimal places.
                          Rows where sales == 0 get a margin of 0.0 to avoid
                          division-by-zero errors.
        - year          : calendar year extracted from order_date (if present).
        - month         : calendar month (1-12) extracted from order_date.
        - quarter       : fiscal quarter (1-4) extracted from order_date.

    Args:
        df (pd.DataFrame): The transformed DataFrame (columns already renamed
                           to snake_case before this function is called).

    Returns:
        pd.DataFrame: DataFrame with additional feature columns appended.

    Example:
        >>> df = create_features(df)
    """
    df = df.copy()
    new_cols: list = []

    # -- revenue -------------------------------------------------------------
    # revenue is semantically identical to sales; the alias makes downstream
    # SQL queries and BI reports more self-documenting.
    if "sales" in df.columns:
        df["revenue"] = df["sales"]
        new_cols.append("revenue")

    # -- profit_margin -------------------------------------------------------
    if "profit" in df.columns and "sales" in df.columns:
        # Use numpy.where to safely handle rows where sales == 0
        df["profit_margin"] = np.where(
            df["sales"] != 0,
            ((df["profit"] / df["sales"]) * 100).round(2),
            0.0,
        )
        new_cols.append("profit_margin")

    # -- year, month, quarter ------------------------------------------------
    # These are only created if an order_date column exists (datetime type)
    if "order_date" in df.columns and pd.api.types.is_datetime64_any_dtype(df["order_date"]):
        df["year"] = df["order_date"].dt.year
        df["month"] = df["order_date"].dt.month
        df["quarter"] = df["order_date"].dt.quarter
        new_cols.extend(["year", "month", "quarter"])
    else:
        print("   [create_features]  'order_date' not found - year/month/quarter skipped.")

    print(f"   [create_features]  New columns created : {new_cols}")

    return df


def save_cleaned_dataset(df: pd.DataFrame, file_path: str = CLEANED_FILE) -> None:
    """Save the cleaned DataFrame to a CSV file in data/processed/.

    Creates the destination directory if it does not already exist.

    Args:
        df (pd.DataFrame): The fully transformed DataFrame to save.
        file_path (str): Destination file path. Defaults to CLEANED_FILE.

    Returns:
        None

    Example:
        >>> save_cleaned_dataset(df)
    """
    # Create the processed/ directory if it does not exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write to CSV without the pandas integer index column
    df.to_csv(file_path, index=False, encoding="utf-8")

    print(f"\n[OK] Cleaned dataset saved to: {file_path}")


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Orchestrate all transformation steps in the correct order.

    This function calls every individual transformation step, tracks row
    counts before and after, and prints a final summary.

    Args:
        df (pd.DataFrame): The raw DataFrame returned by extract_data().

    Returns:
        pd.DataFrame: The fully cleaned and enriched DataFrame.
    """
    original_rows: int = len(df)
    original_cols: int = df.shape[1]

    print(f"\n{SEP}")
    print("  TRANSFORMATION STEPS")
    print(SEP)

    # Step 1 - Remove duplicates
    df = remove_duplicates(df)

    # Step 2 - Handle missing values with sensible defaults
    df = clean_missing_values(df)

    # Step 3 - Convert date columns to datetime
    df = convert_date_columns(df, DATE_COLUMNS)

    # Step 4 - Standardize text columns (trim + Title Case)
    df = standardize_columns(df, TEXT_COLUMNS)

    # Step 5 - Rename columns to snake_case
    df = rename_columns(df, COLUMN_RENAME_MAP)

    # Step 6 - Create calculated feature columns
    df = create_features(df)

    # -- Transformation summary ----------------------------------------------
    final_rows: int = len(df)
    final_cols: int = df.shape[1]
    rows_removed: int = original_rows - final_rows
    cols_created: int = final_cols - original_cols

    print(f"\n{SEP}")
    print("  TRANSFORMATION SUMMARY")
    print(SEP)
    print(f"   Original Rows    : {original_rows:,}")
    print(f"   Final Rows       : {final_rows:,}")
    print(f"   Rows Removed     : {rows_removed:,}")
    print(f"   Original Columns : {original_cols}")
    print(f"   Final Columns    : {final_cols}")
    print(f"   Columns Created  : {cols_created}")
    print(SEP)

    return df


def main() -> None:
    """Entry point when transform.py is run directly from the command line.

    Loads the raw dataset, runs all transformation steps, saves the cleaned
    CSV, and exits successfully.

    Returns:
        None
    """
    try:
        # Step 1 - Load dataset using the existing extract module
        print("[INFO] Loading dataset via extract module...")
        df: pd.DataFrame = extract_data()

        # Step 2 - Run all transformation steps
        df_clean: pd.DataFrame = transform_data(df)

        # Step 3 - Persist the cleaned dataset to disk
        save_cleaned_dataset(df_clean)

        print("[OK] Transformation complete.\n")

    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    except Exception as e:
        print(
            f"\n[ERROR] An unexpected error occurred during transformation.\n"
            f"Details: {e}"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Script Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
