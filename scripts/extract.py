"""
extract.py - Phase 3: Extract Module
=====================================
Retail Sales ETL & Analytics Pipeline

Responsibilities:
    - Check whether the raw dataset file exists on disk.
    - Load the CSV file into a pandas DataFrame.
    - Display a structured summary of the dataset.
    - Return the DataFrame for downstream use in later phases.

Usage:
    python scripts/extract.py

Author  : Retail Sales ETL Project
Phase   : 3 - Extract
"""

import os
import sys

import pandas as pd
from pandas.errors import ParserError


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Path to the raw dataset relative to the project root.
# All scripts are run from the project root, so this path is stable.
RAW_DATA_PATH: str = os.path.join("data", "raw", "retail_sales.csv")


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def check_file_exists(file_path: str) -> None:
    """Check whether the given file exists on disk.

    Args:
        file_path (str): Relative or absolute path to the file.

    Raises:
        FileNotFoundError: If the file does not exist at the given path.

    Example:
        >>> check_file_exists("data/raw/retail_sales.csv")
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"\n[ERROR] Dataset not found at: '{file_path}'\n"
            "Please make sure 'retail_sales.csv' is placed inside 'data/raw/'."
        )


def load_dataset(file_path: str) -> pd.DataFrame:
    """Load a CSV file from disk into a pandas DataFrame.

    Args:
        file_path (str): Path to the CSV file to load.

    Returns:
        pd.DataFrame: The loaded dataset as a DataFrame.

    Raises:
        ParserError: If the CSV file is malformed or cannot be parsed.
        Exception:   For any other unexpected error during file reading.

    Example:
        >>> df = load_dataset("data/raw/retail_sales.csv")
    """
    # Read the CSV file into a DataFrame
    df: pd.DataFrame = pd.read_csv(file_path)

    print("\n[OK] Dataset loaded successfully.\n")
    return df


def display_dataset_summary(df: pd.DataFrame) -> None:
    """Print a structured summary of the DataFrame to the console.

    The summary includes:
        - Total number of rows and columns
        - Column names
        - Data type of each column
        - Count of missing (NaN) values per column
        - First five records of the dataset

    Args:
        df (pd.DataFrame): The DataFrame to summarise.

    Returns:
        None

    Example:
        >>> display_dataset_summary(df)
    """
    # Use a plain ASCII separator line for cross-platform compatibility
    separator: str = "-" * 55

    # -- Basic shape ---------------------------------------------------------
    print(separator)
    print("  DATASET SUMMARY")
    print(separator)

    print(f"\n  Rows    : {df.shape[0]:,}")
    print(f"  Columns : {df.shape[1]}")

    # -- Column names --------------------------------------------------------
    print(f"\n{separator}")
    print("  COLUMN NAMES")
    print(separator)
    for col in df.columns:
        print(f"   - {col}")

    # -- Data types ----------------------------------------------------------
    print(f"\n{separator}")
    print("  DATA TYPES")
    print(separator)
    for col, dtype in df.dtypes.items():
        print(f"   {col:<20} {dtype}")

    # -- Missing values ------------------------------------------------------
    print(f"\n{separator}")
    print("  MISSING VALUES PER COLUMN")
    print(separator)
    missing_counts = df.isnull().sum()
    has_missing = False
    for col, count in missing_counts.items():
        if count > 0:
            has_missing = True
        print(f"   {col:<20} {count}")
    if not has_missing:
        print("\n   [OK] No missing values found in any column.")

    # -- First five rows -----------------------------------------------------
    print(f"\n{separator}")
    print("  FIRST FIVE RECORDS")
    print(separator)
    print(df.head())
    print()


def extract_data(file_path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Orchestrate the full extraction process.

    This is the main extraction function that:
        1. Verifies the file exists.
        2. Loads it into a DataFrame.
        3. Prints a summary of the data.
        4. Returns the DataFrame for use in later pipeline stages.

    Args:
        file_path (str): Path to the CSV file. Defaults to RAW_DATA_PATH.

    Returns:
        pd.DataFrame: The extracted dataset as a DataFrame.

    Raises:
        FileNotFoundError: If the file is missing.
        ParserError: If the file cannot be parsed as CSV.
        Exception: For any other unexpected error.
    """
    # Step 1 - Confirm the file is present before attempting to read it
    check_file_exists(file_path)

    # Step 2 - Load the CSV into a DataFrame
    df: pd.DataFrame = load_dataset(file_path)

    # Step 3 - Print summary information for inspection
    display_dataset_summary(df)

    # Step 4 - Return the DataFrame so later phases can use it
    return df


def main() -> None:
    """Entry point when extract.py is run directly from the command line.

    Calls extract_data() and handles all expected exceptions gracefully,
    printing a clear message and exiting with a non-zero code on failure.

    Returns:
        None
    """
    try:
        df: pd.DataFrame = extract_data()
        print("[OK] Extraction complete. DataFrame is ready for the next phase.\n")

    except FileNotFoundError as e:
        # File is missing - guide the user to fix it
        print(e)
        sys.exit(1)

    except ParserError as e:
        # CSV is malformed or corrupted
        print(
            f"\n[ERROR] Failed to parse the CSV file.\n"
            f"Details: {e}\n"
            "Please verify that 'retail_sales.csv' is a valid CSV file."
        )
        sys.exit(1)

    except Exception as e:
        # Catch-all for any other unexpected problems
        print(
            f"\n[ERROR] An unexpected error occurred during extraction.\n"
            f"Details: {e}"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Script Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
