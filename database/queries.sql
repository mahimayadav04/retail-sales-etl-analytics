-- =============================================================
-- queries.sql
-- Retail Sales ETL & Analytics Pipeline  -  Phase 9
-- =============================================================
-- Purpose : A collection of 20 KPI SQL queries for business
--           analysis on the PostgreSQL 'sales' table.
--
-- Table   : sales
-- Schema  : See database/schema.sql for column definitions
--
-- How to use:
--   Option A - Run in psql:
--       psql -U postgres -d retail_sales_db -f database/queries.sql
--
--   Option B - Paste individual queries into pgAdmin Query Tool.
--
--   Option C - Connect Power BI directly to PostgreSQL and use
--              these queries as custom dataset sources.
--
-- All queries use standard PostgreSQL syntax.
-- =============================================================


-- =============================================================
-- KPI 1 : Total Revenue
-- Business question: What is the total revenue generated across
-- all sales records?
-- =============================================================
SELECT
    ROUND(SUM(revenue)::NUMERIC, 2) AS total_revenue
FROM sales;


-- =============================================================
-- KPI 2 : Total Profit
-- Business question: What is the overall profit after discounts
-- and costs across all transactions?
-- =============================================================
SELECT
    ROUND(SUM(profit)::NUMERIC, 2) AS total_profit
FROM sales;


-- =============================================================
-- KPI 3 : Total Orders
-- Business question: How many individual sales records exist
-- in the dataset? Each row represents one line item.
-- =============================================================
SELECT
    COUNT(*) AS total_orders
FROM sales;


-- =============================================================
-- KPI 4 : Average Order Value
-- Business question: What is the average revenue generated
-- per sales line item?
-- =============================================================
SELECT
    ROUND(AVG(revenue)::NUMERIC, 2) AS avg_order_value
FROM sales;


-- =============================================================
-- KPI 5 : Top 10 Sub-Categories by Revenue
-- Business question: Which product sub-categories generate the
-- most revenue? Useful for prioritising inventory and marketing.
-- =============================================================
SELECT
    sub_category,
    ROUND(SUM(revenue)::NUMERIC, 2) AS total_revenue,
    COUNT(*)                         AS order_count
FROM sales
GROUP BY sub_category
ORDER BY total_revenue DESC
LIMIT 10;


-- =============================================================
-- KPI 6 : Top 10 Cities by Revenue
-- Business question: Which cities contribute the most to total
-- revenue? Useful for regional sales strategy.
-- =============================================================
SELECT
    city,
    state,
    ROUND(SUM(revenue)::NUMERIC, 2) AS total_revenue,
    COUNT(*)                         AS order_count
FROM sales
GROUP BY city, state
ORDER BY total_revenue DESC
LIMIT 10;


-- =============================================================
-- KPI 7 : Sales by Category
-- Business question: How is revenue distributed across the three
-- main product categories (Furniture, Office Supplies, Technology)?
-- =============================================================
SELECT
    category,
    ROUND(SUM(revenue)::NUMERIC, 2)  AS total_revenue,
    ROUND(SUM(profit)::NUMERIC, 2)   AS total_profit,
    COUNT(*)                          AS order_count
FROM sales
GROUP BY category
ORDER BY total_revenue DESC;


-- =============================================================
-- KPI 8 : Sales by Sub-Category
-- Business question: Granular breakdown of revenue and profit
-- at the sub-category level to identify top/bottom performers.
-- =============================================================
SELECT
    category,
    sub_category,
    ROUND(SUM(revenue)::NUMERIC, 2)  AS total_revenue,
    ROUND(SUM(profit)::NUMERIC, 2)   AS total_profit,
    COUNT(*)                          AS order_count
FROM sales
GROUP BY category, sub_category
ORDER BY total_revenue DESC;


-- =============================================================
-- KPI 9 : Sales by Region
-- Business question: How does performance differ across the
-- four US regions (East, West, South, Central)?
-- =============================================================
SELECT
    region,
    ROUND(SUM(revenue)::NUMERIC, 2)  AS total_revenue,
    ROUND(SUM(profit)::NUMERIC, 2)   AS total_profit,
    COUNT(*)                          AS order_count,
    ROUND(AVG(profit_margin)::NUMERIC, 2) AS avg_profit_margin_pct
FROM sales
GROUP BY region
ORDER BY total_revenue DESC;


-- =============================================================
-- KPI 10 : Monthly Revenue Trend
-- Business question: How does total revenue change month by
-- month? Useful for spotting seasonality.
-- NOTE: This dataset does not contain a date column in the
--       loaded table. When a date column is available, replace
--       the placeholder below with the actual column name.
--       Example: DATE_TRUNC('month', order_date) AS revenue_month
-- =============================================================
-- Placeholder query - runs against current data grouping by segment
-- Replace with date-based grouping once order_date is available.
SELECT
    segment                               AS group_label,
    ROUND(SUM(revenue)::NUMERIC, 2)       AS total_revenue,
    COUNT(*)                              AS order_count
FROM sales
GROUP BY segment
ORDER BY total_revenue DESC;


-- =============================================================
-- KPI 11 : Monthly Profit Trend
-- Business question: How does profit fluctuate month by month?
-- Helps identify loss-making periods.
-- NOTE: Same date column caveat as KPI 10.
-- =============================================================
SELECT
    segment                             AS group_label,
    ROUND(SUM(profit)::NUMERIC, 2)      AS total_profit,
    COUNT(*)                            AS order_count
FROM sales
GROUP BY segment
ORDER BY total_profit DESC;


-- =============================================================
-- KPI 12 : Revenue and Profit by Ship Mode
-- Business question: Which shipping methods are associated with
-- the highest revenue and profit? Also covered in KPI 18.
-- =============================================================
SELECT
    ship_mode,
    ROUND(SUM(revenue)::NUMERIC, 2)  AS total_revenue,
    ROUND(SUM(profit)::NUMERIC, 2)   AS total_profit,
    COUNT(*)                          AS order_count
FROM sales
GROUP BY ship_mode
ORDER BY total_revenue DESC;


-- =============================================================
-- KPI 13 : Average Discount
-- Business question: What is the average discount being offered?
-- High average discounts erode margins.
-- =============================================================
SELECT
    ROUND(AVG(discount)::NUMERIC, 4)         AS avg_discount_rate,
    ROUND((AVG(discount) * 100)::NUMERIC, 2) AS avg_discount_pct
FROM sales;


-- =============================================================
-- KPI 14 : Top 5 Most Profitable Sub-Categories
-- Business question: Which product sub-categories deliver the
-- highest total profit? Focus sales efforts here.
-- =============================================================
SELECT
    sub_category,
    ROUND(SUM(profit)::NUMERIC, 2)        AS total_profit,
    ROUND(AVG(profit_margin)::NUMERIC, 2) AS avg_margin_pct
FROM sales
GROUP BY sub_category
ORDER BY total_profit DESC
LIMIT 5;


-- =============================================================
-- KPI 15 : Bottom 5 Least Profitable Sub-Categories
-- Business question: Which sub-categories are consistently
-- generating losses? These may require pricing or cost review.
-- =============================================================
SELECT
    sub_category,
    ROUND(SUM(profit)::NUMERIC, 2)        AS total_profit,
    ROUND(AVG(profit_margin)::NUMERIC, 2) AS avg_margin_pct
FROM sales
GROUP BY sub_category
ORDER BY total_profit ASC
LIMIT 5;


-- =============================================================
-- KPI 16 : Average Profit Margin
-- Business question: What is the average profit margin across
-- all transactions? Benchmark for financial health.
-- =============================================================
SELECT
    ROUND(AVG(profit_margin)::NUMERIC, 2) AS avg_profit_margin_pct
FROM sales;


-- =============================================================
-- KPI 17 : Revenue by Customer Segment
-- Business question: Which customer segment (Consumer, Corporate,
-- Home Office) contributes the most revenue?
-- =============================================================
SELECT
    segment,
    ROUND(SUM(revenue)::NUMERIC, 2)       AS total_revenue,
    ROUND(SUM(profit)::NUMERIC, 2)        AS total_profit,
    COUNT(*)                               AS order_count,
    ROUND(AVG(profit_margin)::NUMERIC, 2) AS avg_margin_pct
FROM sales
GROUP BY segment
ORDER BY total_revenue DESC;


-- =============================================================
-- KPI 18 : Revenue by Ship Mode
-- Business question: How does shipping method impact revenue
-- and order volume? Useful for logistics planning.
-- =============================================================
SELECT
    ship_mode,
    ROUND(SUM(revenue)::NUMERIC, 2)  AS total_revenue,
    COUNT(*)                          AS order_count,
    ROUND(AVG(revenue)::NUMERIC, 2)  AS avg_order_value
FROM sales
GROUP BY ship_mode
ORDER BY total_revenue DESC;


-- =============================================================
-- KPI 19 : Highest Revenue Region
-- Business question: Which single region generates the most
-- revenue? Quick executive-level insight.
-- =============================================================
SELECT
    region,
    ROUND(SUM(revenue)::NUMERIC, 2) AS total_revenue
FROM sales
GROUP BY region
ORDER BY total_revenue DESC
LIMIT 1;


-- =============================================================
-- KPI 20 : Highest Profit Category
-- Business question: Which product category is the most
-- profitable overall?
-- =============================================================
SELECT
    category,
    ROUND(SUM(profit)::NUMERIC, 2)        AS total_profit,
    ROUND(AVG(profit_margin)::NUMERIC, 2) AS avg_margin_pct
FROM sales
GROUP BY category
ORDER BY total_profit DESC
LIMIT 1;


-- =============================================================
-- BONUS : Full KPI Summary (single-query executive snapshot)
-- Business question: Give me the headline numbers at a glance.
-- =============================================================
SELECT
    COUNT(*)                               AS total_orders,
    ROUND(SUM(revenue)::NUMERIC, 2)        AS total_revenue,
    ROUND(SUM(profit)::NUMERIC, 2)         AS total_profit,
    ROUND(AVG(revenue)::NUMERIC, 2)        AS avg_order_value,
    ROUND(AVG(discount * 100)::NUMERIC, 2) AS avg_discount_pct,
    ROUND(AVG(profit_margin)::NUMERIC, 2)  AS avg_profit_margin_pct
FROM sales;
