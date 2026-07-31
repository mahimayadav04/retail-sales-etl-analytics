"""
validate.py - Phase 4: Validation Module
==========================================
Retail Sales ETL & Analytics Pipeline

Responsibilities:
    - Load the raw DataFrame from the extract module.
    - Run a series of data quality checks.
    - Print a structured validation report to the console.
    - Save a text-based validation report to logs/validation_report.txt.

Usage:
    python scripts/validate.py

Author  : Retail Sales ETL Project
Phase   : 4 - Validation
"""

import os
import sys
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Reuse the extract module so we do not duplicate loading logic.
# sys.path is updated so Python can find scripts/ when running from the
# project root.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from extract import extract_data  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Where the validation report will be saved
REPORT_PATH: str = os.path.join("logs", "validation_report.txt")

SEP: str = "-" * 55  # Plain ASCII separator for cross-platform safety

# Columns that must exist as text and must not be blank
TEXT_COLUMNS: list = ["Segment", "Country", "Region", "Category"]

# Columns that are expected to have a specific pandas dtype
EXPECTED_DTYPES: dict = {
    "Sales": "float64",
    "Quantity": "int64",
    "Discount": "float64",
    "Profit": "float64",
    "Postal Code": "int64",
}

# Date columns to check (not present in this dataset by default, but the
# function is built to handle them if they appear in future versions)
DATE_COLUMNS: list = []  # e.g. ["Order Date", "Ship Date"]


# ---------------------------------------------------------------------------
# Validation Functions
# ---------------------------------------------------------------------------


def check_missing_values(df: pd.DataFrame) -> pd.Series:
    """Count the number of missing (NaN) values in each column.

    Args:
        df (pd.DataFrame): The DataFrame to inspect.

    Returns:
        pd.Series: A Series mapping column names to their missing-value count.

    Example:
        >>> missing = check_missing_values(df)
    """
    missing: pd.Series = df.isnull().sum()
    return missing


def check_duplicates(df: pd.DataFrame) -> int:
    """Count the number of fully duplicate rows in the DataFrame.

    A duplicate row is one where every column value matches another row
    exactly.

    Args:
        df (pd.DataFrame): The DataFrame to inspect.

    Returns:
        int: The number of duplicate rows found.

    Example:
        >>> dup_count = check_duplicates(df)
    """
    duplicate_count: int = int(df.duplicated().sum())
    return duplicate_count


def check_numeric_values(df: pd.DataFrame) -> dict:
    """Check numeric columns for logically invalid values.

    Rules applied:
        - Sales     < 0  -> invalid (revenue cannot be negative)
        - Quantity  <= 0 -> invalid (must sell at least 1 unit)
        - Discount  < 0  -> invalid (discount cannot be negative)
        - Profit    < 0  -> flagged for awareness only (losses are valid)

    Args:
        df (pd.DataFrame): The DataFrame to inspect.

    Returns:
        dict: Keys are check descriptions; values are row counts that fail.

    Example:
        >>> issues = check_numeric_values(df)
    """
    results: dict = {}

    # Sales should never be negative
    if "Sales" in df.columns:
        results["Sales < 0 (invalid)"] = int((df["Sales"] < 0).sum())

    # Quantity must be at least 1
    if "Quantity" in df.columns:
        results["Quantity <= 0 (invalid)"] = int((df["Quantity"] <= 0).sum())

    # Discount cannot be negative
    if "Discount" in df.columns:
        results["Discount < 0 (invalid)"] = int((df["Discount"] < 0).sum())

    # Profit < 0 is flagged for awareness; losses are business-valid
    if "Profit" in df.columns:
        results["Profit < 0 (loss, report only)"] = int((df["Profit"] < 0).sum())

    return results


def check_dates(df: pd.DataFrame, date_columns: list) -> dict:
    """Attempt to parse each specified date column and count unparseable rows.

    Rows that cannot be coerced to a valid datetime are counted as invalid.
    If a column does not exist in the DataFrame it is skipped.

    Args:
        df (pd.DataFrame): The DataFrame to inspect.
        date_columns (list): Names of columns expected to contain dates.

    Returns:
        dict: Keys are column names; values are counts of invalid date rows.

    Example:
        >>> date_issues = check_dates(df, ["Order Date"])
    """
    results: dict = {}

    for col in date_columns:
        if col not in df.columns:
            # Column not present - note it and move on
            results[col] = "Column not found"
            continue

        # coerce=True turns unparseable values into NaT instead of raising
        parsed = pd.to_datetime(df[col], errors="coerce")
        invalid_count: int = int(parsed.isnull().sum())
        results[col] = invalid_count

    return results


def check_text_columns(df: pd.DataFrame, text_columns: list) -> dict:
    """Check specified text columns for empty or whitespace-only values.

    Args:
        df (pd.DataFrame): The DataFrame to inspect.
        text_columns (list): Names of columns that should contain non-empty text.

    Returns:
        dict: Keys are column names; values are counts of empty/blank rows.

    Example:
        >>> text_issues = check_text_columns(df, ["Region", "Category"])
    """
    results: dict = {}

    for col in text_columns:
        if col not in df.columns:
            results[col] = "Column not found"
            continue

        # Strip whitespace then check for empty strings or NaN
        empty_count: int = int(
            df[col].astype(str).str.strip().isin(["", "nan", "None"]).sum()
        )
        results[col] = empty_count

    return results


def check_data_types(df: pd.DataFrame, expected: dict) -> dict:
    """Verify that key columns carry the expected pandas dtype.

    Args:
        df (pd.DataFrame): The DataFrame to inspect.
        expected (dict): Mapping of column name -> expected dtype string
                         (e.g., {"Sales": "float64"}).

    Returns:
        dict: Keys are column names; values are dicts with "expected",
              "actual", and "match" keys.

    Example:
        >>> dtype_report = check_data_types(df, {"Sales": "float64"})
    """
    results: dict = {}

    for col, expected_dtype in expected.items():
        if col not in df.columns:
            results[col] = {"expected": expected_dtype, "actual": "not found", "match": False}
            continue

        actual_dtype: str = str(df[col].dtype)
        results[col] = {
            "expected": expected_dtype,
            "actual": actual_dtype,
            "match": actual_dtype == expected_dtype,
        }

    return results


def generate_validation_report(
    df: pd.DataFrame,
    missing: pd.Series,
    duplicates: int,
    numeric_issues: dict,
    date_issues: dict,
    text_issues: dict,
    dtype_report: dict,
) -> str:
    """Build the full validation report as a formatted string.

    This function assembles all individual check results into a single
    readable report that can be printed to the console and saved to a file.

    Args:
        df (pd.DataFrame): The original DataFrame (used for record count).
        missing (pd.Series): Output of check_missing_values().
        duplicates (int): Output of check_duplicates().
        numeric_issues (dict): Output of check_numeric_values().
        date_issues (dict): Output of check_dates().
        text_issues (dict): Output of check_text_columns().
        dtype_report (dict): Output of check_data_types().

    Returns:
        str: The complete validation report as a plain-text string.
    """
    lines: list = []

    # -- Header --------------------------------------------------------------
    lines.append(SEP)
    lines.append("  VALIDATION REPORT")
    lines.append(f"  Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(SEP)

    # -- Record count --------------------------------------------------------
    lines.append(f"\n  Total Records : {len(df):,}")
    lines.append(f"  Total Columns : {df.shape[1]}")

    # -- Missing values ------------------------------------------------------
    lines.append(f"\n{SEP}")
    lines.append("  MISSING VALUES PER COLUMN")
    lines.append(SEP)
    total_missing = missing.sum()
    for col, count in missing.items():
        status = "[OK]" if count == 0 else "[WARN]"
        lines.append(f"   {status}  {col:<22} {count}")
    lines.append(f"\n   Total missing cells : {total_missing}")

    # -- Duplicates ----------------------------------------------------------
    lines.append(f"\n{SEP}")
    lines.append("  DUPLICATE ROWS")
    lines.append(SEP)
    dup_status = "[OK]" if duplicates == 0 else "[WARN]"
    lines.append(f"   {dup_status}  Duplicate rows found : {duplicates}")

    # -- Numeric checks ------------------------------------------------------
    lines.append(f"\n{SEP}")
    lines.append("  INVALID NUMERIC VALUES")
    lines.append(SEP)
    for check, count in numeric_issues.items():
        status = "[OK]" if count == 0 else "[WARN]"
        lines.append(f"   {status}  {check:<38} {count}")

    # -- Date checks ---------------------------------------------------------
    lines.append(f"\n{SEP}")
    lines.append("  INVALID DATE VALUES")
    lines.append(SEP)
    if date_issues:
        for col, count in date_issues.items():
            if isinstance(count, int):
                status = "[OK]" if count == 0 else "[WARN]"
                lines.append(f"   {status}  {col:<22} {count} invalid date(s)")
            else:
                lines.append(f"   [INFO]  {col:<22} {count}")
    else:
        lines.append("   [INFO]  No date columns configured for this dataset.")

    # -- Text column checks --------------------------------------------------
    lines.append(f"\n{SEP}")
    lines.append("  EMPTY TEXT COLUMN VALUES")
    lines.append(SEP)
    for col, count in text_issues.items():
        if isinstance(count, int):
            status = "[OK]" if count == 0 else "[WARN]"
            lines.append(f"   {status}  {col:<22} {count} empty value(s)")
        else:
            lines.append(f"   [INFO]  {col:<22} {count}")

    # -- Data type checks ----------------------------------------------------
    lines.append(f"\n{SEP}")
    lines.append("  DATA TYPE VERIFICATION")
    lines.append(SEP)
    for col, info in dtype_report.items():
        match_tag = "[OK]" if info["match"] else "[WARN]"
        lines.append(
            f"   {match_tag}  {col:<20} expected={info['expected']:<10} actual={info['actual']}"
        )

    # -- Overall status ------------------------------------------------------
    lines.append(f"\n{SEP}")
    lines.append("  OVERALL VALIDATION STATUS")
    lines.append(SEP)

    # Determine pass/fail based on hard errors (not profit losses)
    hard_errors = (
        total_missing > 0
        or duplicates > 0
        or numeric_issues.get("Sales < 0 (invalid)", 0) > 0
        or numeric_issues.get("Quantity <= 0 (invalid)", 0) > 0
        or numeric_issues.get("Discount < 0 (invalid)", 0) > 0
        or any(v for v in text_issues.values() if isinstance(v, int) and v > 0)
    )

    if hard_errors:
        lines.append("   [WARN]  Dataset has quality issues. Review before transformation.")
    else:
        lines.append("   [OK]   Dataset passed all critical validation checks.")

    lines.append(SEP)
    lines.append("")

    return "\n".join(lines)


def validate_data(df: pd.DataFrame) -> str:
    """Run all validation checks and return the assembled report string.

    This is the main orchestration function for Phase 4. It calls every
    individual check function, prints the report to the console, and
    returns the report text so it can be saved to disk.

    Args:
        df (pd.DataFrame): The raw DataFrame returned by extract_data().

    Returns:
        str: The full validation report as a plain-text string.
    """
    print("\n[INFO] Running data validation checks...\n")

    # -- Run each check ------------------------------------------------------
    missing = check_missing_values(df)
    duplicates = check_duplicates(df)
    numeric_issues = check_numeric_values(df)
    date_issues = check_dates(df, DATE_COLUMNS)
    text_issues = check_text_columns(df, TEXT_COLUMNS)
    dtype_report = check_data_types(df, EXPECTED_DTYPES)

    # -- Build the report string ---------------------------------------------
    report: str = generate_validation_report(
        df, missing, duplicates, numeric_issues,
        date_issues, text_issues, dtype_report,
    )

    # -- Print to console ----------------------------------------------------
    print(report)

    return report


def save_report(report: str, report_path: str = REPORT_PATH) -> None:
    """Save the validation report text to a file on disk.

    Creates the logs/ directory if it does not already exist.

    Args:
        report (str): The full report text to save.
        report_path (str): Destination file path. Defaults to REPORT_PATH.

    Returns:
        None

    Example:
        >>> save_report(report_text)
    """
    # Ensure the logs directory exists before writing
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] Validation report saved to: {report_path}\n")


def main() -> None:
    """Entry point when validate.py is run directly from the command line.

    Loads the raw dataset via the extract module, runs all validation checks,
    prints the report, and saves it to logs/validation_report.txt.

    Returns:
        None
    """
    try:
        # Step 1 - Load the dataset using the existing extract module
        print("[INFO] Loading dataset via extract module...")
        df: pd.DataFrame = extract_data()

        # Step 2 - Run all validation checks and get the report string
        report: str = validate_data(df)

        # Step 3 - Persist the report to disk
        save_report(report)

        print("[OK] Validation complete.\n")

    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    except Exception as e:
        print(
            f"\n[ERROR] An unexpected error occurred during validation.\n"
            f"Details: {e}"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Script Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
