"""
run_pipeline.py - Phase 8: Pipeline Runner
============================================
Retail Sales ETL & Analytics Pipeline

Responsibilities:
    - Orchestrate the full ETL pipeline in the correct order:
        Step 1: Extract   -> extract.py
        Step 2: Validate  -> validate.py
        Step 3: Transform -> transform.py
        Step 4: Load      -> load.py
    - Display progress for each step.
    - Stop and report clearly if any step fails.
    - Write a persistent log entry to logs/pipeline.log after every run.
    - Display a final summary: status, execution time, rows loaded.

Usage:
    python scripts/run_pipeline.py

Prerequisites:
    1. PostgreSQL is running.
    2. A .env file exists in the project root with correct credentials.
    3. data/raw/retail_sales.csv is present.

Author  : Retail Sales ETL Project
Phase   : 8 - Pipeline Runner
"""

import logging
import os
import sys
import time
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Add scripts/ directory to sys.path so sibling modules can be imported
# regardless of where the user runs the script from.
# ---------------------------------------------------------------------------
SCRIPTS_DIR: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

# Import the core functions from each phase module.
# We import only the functions that the pipeline needs to call;
# the modules handle their own internal logic.
from extract import extract_data                            # Phase 3
from validate import validate_data, save_report            # Phase 4
from transform import transform_data, save_cleaned_dataset # Phase 5
from load import (                                          # Phase 7
    load_environment,
    create_connection,
    read_clean_dataset,
    load_dataframe,
    verify_load,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Absolute path to the logs directory (relative to project root)
PROJECT_ROOT: str = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
LOG_DIR: str = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE: str = os.path.join(LOG_DIR, "pipeline.log")

SEP: str = "-" * 45   # Short separator for pipeline display
SEP_WIDE: str = "=" * 45


# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------

def configure_logging() -> logging.Logger:
    """Set up the Python logging module to write to logs/pipeline.log.

    Appends to the log file on every run (does not overwrite).
    Each log line includes the timestamp, log level, and message.
    Creates the logs/ directory if it does not already exist.

    Returns:
        logging.Logger: The configured logger instance.

    Example:
        >>> logger = configure_logging()
    """
    # Ensure the logs directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Get (or create) a logger named after this module
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if the function is called more than once
    if not logger.handlers:
        # File handler - appends to pipeline.log (mode='a')
        file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # Log format: timestamp | level | message
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# ---------------------------------------------------------------------------
# Pipeline Step Functions
# ---------------------------------------------------------------------------


def run_extract() -> pd.DataFrame:
    """Execute Phase 3: Extract the raw dataset.

    Calls extract_data() from extract.py, which checks the file exists,
    loads the CSV, prints a dataset summary, and returns the DataFrame.

    Returns:
        pd.DataFrame: The raw dataset as a DataFrame.

    Raises:
        Exception: Any exception raised inside extract_data().

    Example:
        >>> df_raw = run_extract()
    """
    # extract_data() already prints its own summary - we just call it
    df: pd.DataFrame = extract_data()
    return df


def run_validation(df: pd.DataFrame) -> None:
    """Execute Phase 4: Validate the raw dataset.

    Calls validate_data() to run all quality checks and prints the report,
    then saves the report to logs/validation_report.txt.

    Args:
        df (pd.DataFrame): The raw DataFrame returned by run_extract().

    Returns:
        None

    Raises:
        Exception: Any exception raised inside validate_data() or save_report().

    Example:
        >>> run_validation(df_raw)
    """
    report: str = validate_data(df)
    save_report(report)


def run_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """Execute Phase 5: Clean and enrich the dataset.

    Calls transform_data() to apply all transformation steps, then saves
    the result to data/processed/retail_sales_cleaned.csv.

    Args:
        df (pd.DataFrame): The raw DataFrame returned by run_extract().

    Returns:
        pd.DataFrame: The fully cleaned and enriched DataFrame.

    Raises:
        Exception: Any exception raised inside transform_data() or
                   save_cleaned_dataset().

    Example:
        >>> df_clean = run_transformation(df_raw)
    """
    df_clean: pd.DataFrame = transform_data(df)
    save_cleaned_dataset(df_clean)
    return df_clean


def run_load() -> int:
    """Execute Phase 7: Load the cleaned dataset into PostgreSQL.

    Reads credentials from .env, connects to PostgreSQL, reads the
    cleaned CSV from disk, inserts it into the 'sales' table, and
    verifies the row count.

    Returns:
        int: The total number of rows confirmed in the database.

    Raises:
        Exception: Any exception raised by the load module functions.

    Example:
        >>> rows = run_load()
    """
    config: dict = load_environment()
    engine = create_connection(config)
    df: pd.DataFrame = read_clean_dataset()
    load_dataframe(df, engine)
    row_count: int = verify_load(engine)
    return row_count


# ---------------------------------------------------------------------------
# Main Pipeline Orchestrator
# ---------------------------------------------------------------------------


def run_pipeline() -> None:
    """Orchestrate the full ETL pipeline from extract through load.

    Executes each step in order. If any step raises an exception,
    the pipeline stops immediately, logs the failure, and exits.

    The function tracks overall start/end time and logs a summary
    entry to logs/pipeline.log after every run (pass or fail).

    Returns:
        None
    """
    logger = configure_logging()
    pipeline_start: float = time.time()
    pipeline_date: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Pipeline header ──────────────────────────────────────────────────────
    print(SEP_WIDE)
    print("   Retail Sales ETL Pipeline")
    print(SEP_WIDE)
    print(f"   Started : {pipeline_date}")
    print(SEP_WIDE)

    logger.info("=" * 50)
    logger.info("PIPELINE STARTED")
    logger.info(f"Start time : {pipeline_date}")

    rows_loaded: int = 0

    # ── Step 1: Extract ──────────────────────────────────────────────────────
    step_start: float = time.time()
    print("\n  Step 1 of 4 : Extract")
    print(SEP)

    try:
        df_raw: pd.DataFrame = run_extract()
    except Exception as e:
        _handle_step_failure("Extract", e, logger, pipeline_start)
        return

    step_elapsed: float = round(time.time() - step_start, 2)
    print(f"\n  [OK] Extract completed in {step_elapsed}s")
    logger.info(f"Step 1 - Extract    : COMPLETED ({step_elapsed}s)")

    # ── Step 2: Validate ─────────────────────────────────────────────────────
    step_start = time.time()
    print(f"\n{SEP}")
    print("  Step 2 of 4 : Validate")
    print(SEP)

    try:
        run_validation(df_raw)
    except Exception as e:
        _handle_step_failure("Validate", e, logger, pipeline_start)
        return

    step_elapsed = round(time.time() - step_start, 2)
    print(f"\n  [OK] Validation completed in {step_elapsed}s")
    logger.info(f"Step 2 - Validate   : COMPLETED ({step_elapsed}s)")

    # ── Step 3: Transform ────────────────────────────────────────────────────
    step_start = time.time()
    print(f"\n{SEP}")
    print("  Step 3 of 4 : Transform")
    print(SEP)

    try:
        df_clean: pd.DataFrame = run_transformation(df_raw)
    except Exception as e:
        _handle_step_failure("Transform", e, logger, pipeline_start)
        return

    step_elapsed = round(time.time() - step_start, 2)
    print(f"\n  [OK] Transformation completed in {step_elapsed}s")
    logger.info(f"Step 3 - Transform  : COMPLETED ({step_elapsed}s)")

    # ── Step 4: Load ─────────────────────────────────────────────────────────
    step_start = time.time()
    print(f"\n{SEP}")
    print("  Step 4 of 4 : Load")
    print(SEP)

    try:
        rows_loaded = run_load()
    except Exception as e:
        _handle_step_failure("Load", e, logger, pipeline_start)
        return

    step_elapsed = round(time.time() - step_start, 2)
    print(f"\n  [OK] Load completed in {step_elapsed}s")
    logger.info(f"Step 4 - Load       : COMPLETED ({step_elapsed}s)")

    # ── Final summary ────────────────────────────────────────────────────────
    total_elapsed: float = round(time.time() - pipeline_start, 2)
    end_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{SEP_WIDE}")
    print("   Pipeline Completed Successfully")
    print(SEP_WIDE)
    print(f"   Rows Loaded    : {rows_loaded:,}")
    print(f"   Execution Time : {total_elapsed} seconds")
    print(f"   Log File       : logs/pipeline.log")
    print(SEP_WIDE)

    logger.info(f"End time   : {end_time}")
    logger.info(f"Rows loaded: {rows_loaded:,}")
    logger.info(f"Total time : {total_elapsed}s")
    logger.info("STATUS     : SUCCESS")
    logger.info("=" * 50)


def _handle_step_failure(
    step_name: str,
    error: Exception,
    logger: logging.Logger,
    pipeline_start: float,
) -> None:
    """Print and log a step failure, then stop the pipeline.

    This is a private helper function called when any pipeline step raises
    an unhandled exception. It prints a clear error to the console, writes
    a FAILED entry to the log file, and exits the process.

    Args:
        step_name (str): Name of the step that failed (e.g. "Extract").
        error (Exception): The exception that was raised.
        logger (logging.Logger): The configured pipeline logger.
        pipeline_start (float): Timestamp when the pipeline started (time.time()).

    Returns:
        None
    """
    elapsed: float = round(time.time() - pipeline_start, 2)
    end_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n  [FAIL] Step '{step_name}' failed.")
    print(f"  Error  : {error}")
    print(f"\n{SEP_WIDE}")
    print("  Pipeline FAILED - see logs/pipeline.log for details.")
    print(SEP_WIDE)

    logger.error(f"Step '{step_name}' FAILED : {error}")
    logger.info(f"End time   : {end_time}")
    logger.info(f"Total time : {elapsed}s")
    logger.info("STATUS     : FAILED")
    logger.info("=" * 50)

    sys.exit(1)


# ---------------------------------------------------------------------------
# Script Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point when run_pipeline.py is run from the command line.

    Returns:
        None
    """
    run_pipeline()


if __name__ == "__main__":
    main()
