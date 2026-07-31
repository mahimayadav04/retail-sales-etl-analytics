-- =============================================================
-- schema.sql
-- Retail Sales ETL & Analytics Pipeline  -  Phase 6
-- =============================================================
-- Purpose : Define the PostgreSQL table that will store the
--           cleaned retail sales data produced by transform.py.
--
-- Table   : sales
-- Dataset : data/processed/retail_sales_cleaned.csv
--
-- Design notes:
--   - Column names match the snake_case headers in the CSV.
--   - A surrogate primary key (id SERIAL) is used because the
--     source data has no single natural key that is guaranteed
--     to be unique across all rows.
--   - Data types are chosen to match the pandas dtypes confirmed
--     during Phase 4 (validation) and Phase 5 (transformation).
--   - The table is dropped first so the script is safe to re-run
--     during development without leaving stale data behind.
-- =============================================================


-- Drop the table if it already exists so re-running this script
-- is safe (e.g. after schema changes during development).
DROP TABLE IF EXISTS sales;


-- Create the sales table
CREATE TABLE sales (

    -- Surrogate primary key - auto-incremented by PostgreSQL
    id              SERIAL          PRIMARY KEY,

    -- Shipping and customer segmentation
    ship_mode       VARCHAR(50),
    segment         VARCHAR(50),

    -- Geography
    country         VARCHAR(100),
    city            VARCHAR(100),
    state           VARCHAR(100),
    postal_code     INTEGER,
    region          VARCHAR(50),

    -- Product classification
    category        VARCHAR(100),
    sub_category    VARCHAR(100),

    -- Financial figures
    sales           NUMERIC(12, 4),
    quantity        INTEGER,
    discount        NUMERIC(6, 4),
    profit          NUMERIC(12, 4),

    -- Derived / calculated columns (added in Phase 5)
    revenue         NUMERIC(12, 4),
    profit_margin   NUMERIC(10, 2)

);
