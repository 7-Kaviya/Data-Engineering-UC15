-- ============================================================
-- UC15 ERP Data Platform — Enterprise Reporting Queries
-- Sprint 2 deliverable: "Develop SQL queries for enterprise reporting"
--
-- Every query below has been run against the real, loaded warehouse
-- and returns genuine results (not just syntax-checked).
-- ============================================================


-- ============================================================
-- SALES ANALYTICS
-- ============================================================

-- Sales by month (seasonality)
SELECT
    d.month_name,
    d.month,
    COUNT(*) AS transaction_count,
    SUM(s.total_amount) AS total_revenue
FROM factsales s
JOIN dimdate d ON s.date_key = d.date_key
GROUP BY d.month_name, d.month
ORDER BY d.month;

-- Sales by product category
SELECT
    product_category,
    COUNT(*) AS transaction_count,
    SUM(quantity) AS units_sold,
    SUM(total_amount) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_transaction_value
FROM factsales
GROUP BY product_category
ORDER BY total_revenue DESC;

-- Sales by customer demographic (gender/age band)
SELECT
    gender,
    CASE
        WHEN age < 25 THEN 'Under 25'
        WHEN age BETWEEN 25 AND 40 THEN '25-40'
        WHEN age BETWEEN 41 AND 55 THEN '41-55'
        ELSE '56+'
    END AS age_band,
    COUNT(*) AS transaction_count,
    SUM(total_amount) AS total_revenue
FROM factsales
GROUP BY gender, age_band
ORDER BY total_revenue DESC;

-- Top 10 highest-value individual sales transactions
SELECT
    transaction_id,
    customer_id,
    product_category,
    quantity,
    total_amount
FROM factsales
ORDER BY total_amount DESC
LIMIT 10;


-- ============================================================
-- PROCUREMENT ANALYTICS
-- ============================================================

-- Procurement cost by supplier
SELECT
    sup.supplier_id,
    COUNT(*) AS po_count,
    SUM(p.quantity) AS total_units_ordered,
    SUM(p.total_cost) AS total_spend
FROM factprocurement p
JOIN dimsupplier sup ON p.supplier_key = sup.supplier_key
GROUP BY sup.supplier_id
ORDER BY total_spend DESC;

-- Purchase orders by month
SELECT
    d.month_name,
    d.month,
    COUNT(*) AS po_count,
    SUM(p.total_cost) AS total_spend
FROM factprocurement p
JOIN dimdate d ON p.order_date_key = d.date_key
GROUP BY d.month_name, d.month
ORDER BY d.month;

-- Procurement by item (which items cost the most overall)
SELECT
    item_id,
    item_name,
    COUNT(*) AS po_count,
    SUM(quantity) AS total_units,
    SUM(total_cost) AS total_spend
FROM factprocurement
GROUP BY item_id, item_name
ORDER BY total_spend DESC
LIMIT 10;

-- Purchase order status breakdown
SELECT
    po_status,
    COUNT(*) AS po_count,
    SUM(total_cost) AS total_value
FROM factprocurement
GROUP BY po_status
ORDER BY po_count DESC;


-- ============================================================
-- INVENTORY ANALYTICS
-- ============================================================

-- Total annual demand by item category
SELECT
    i.category,
    SUM(f.units_demanded) AS total_annual_demand
FROM factinventorydemand f
JOIN dimiteminventory i ON f.item_key = i.item_key
GROUP BY i.category
ORDER BY total_annual_demand DESC;

-- Seasonal demand pattern (all items combined, by month)
SELECT
    m.month_name,
    m.month_key,
    SUM(f.units_demanded) AS total_demand
FROM factinventorydemand f
JOIN dimmonth m ON f.month_key = m.month_key
GROUP BY m.month_name, m.month_key
ORDER BY m.month_key;

-- Top 10 highest-demand items (annual total)
SELECT
    i.item_id,
    i.item_name,
    i.category,
    SUM(f.units_demanded) AS annual_demand
FROM factinventorydemand f
JOIN dimiteminventory i ON f.item_key = i.item_key
GROUP BY i.item_id, i.item_name, i.category
ORDER BY annual_demand DESC
LIMIT 10;


-- ============================================================
-- WAREHOUSE ANALYTICS
-- ============================================================

-- Stock levels and turnover by category
SELECT
    wi.category,
    SUM(w.stock_level) AS total_stock,
    ROUND(AVG(w.turnover_ratio), 2) AS avg_turnover_ratio,
    ROUND(AVG(w.kpi_score), 4) AS avg_kpi_score
FROM factwarehousesnapshot w
JOIN dimwarehouseitem wi ON w.warehouse_item_key = wi.warehouse_item_key
GROUP BY wi.category
ORDER BY total_stock DESC;

-- Items with stockouts last month (operational risk)
SELECT
    wi.item_id,
    wi.category,
    wi.zone,
    w.stock_level,
    w.stockout_count_last_month,
    w.reorder_point
FROM factwarehousesnapshot w
JOIN dimwarehouseitem wi ON w.warehouse_item_key = wi.warehouse_item_key
WHERE w.stockout_count_last_month > 0
ORDER BY w.stockout_count_last_month DESC
LIMIT 20;

-- Warehouse performance by zone
SELECT
    wi.zone,
    COUNT(*) AS item_count,
    ROUND(AVG(w.order_fulfillment_rate), 4) AS avg_fulfillment_rate,
    ROUND(AVG(w.picking_time_seconds), 2) AS avg_picking_time_sec
FROM factwarehousesnapshot w
JOIN dimwarehouseitem wi ON w.warehouse_item_key = wi.warehouse_item_key
GROUP BY wi.zone
ORDER BY avg_fulfillment_rate DESC;


-- ============================================================
-- FINANCE ANALYTICS
-- ============================================================

-- Financial performance by account type
SELECT
    account_type,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_amount,
    ROUND(AVG(profit_margin), 4) AS avg_profit_margin,
    SUM(revenue) AS total_revenue,
    SUM(expenditure) AS total_expenditure
FROM factfinance
GROUP BY account_type
ORDER BY total_amount DESC;

-- Monthly financial trend
SELECT
    d.month_name,
    d.month,
    SUM(f.revenue) AS revenue,
    SUM(f.expenditure) AS expenditure,
    SUM(f.net_income) AS net_income
FROM factfinance f
JOIN dimdate d ON f.date_key = d.date_key
GROUP BY d.month_name, d.month
ORDER BY d.month;

-- Accounts Receivable aging: overdue amounts by region
SELECT
    region,
    COUNT(*) AS document_count,
    SUM(amount) AS total_amount,
    ROUND(AVG(days_overdue_delay), 1) AS avg_days_overdue,
    SUM(CASE WHEN delayflag = 'Y' OR delayflag = 'Yes' THEN 1 ELSE 0 END) AS delayed_count
FROM factaccountsreceivable
GROUP BY region
ORDER BY total_amount DESC;

-- Accounts Receivable: worst 15 overdue documents
SELECT
    document_no,
    cust_num,
    region,
    amount,
    days_overdue_delay,
    payment_term
FROM factaccountsreceivable
WHERE days_overdue_delay > 0
ORDER BY days_overdue_delay DESC
LIMIT 15;


-- ============================================================
-- MANUFACTURING ANALYTICS
-- ============================================================

-- Production performance by machine
SELECT
    machine_id,
    COUNT(*) AS jobs_run,
    ROUND(AVG(processing_time), 2) AS avg_processing_time,
    ROUND(AVG(energy_consumption), 2) AS avg_energy_consumption,
    ROUND(AVG(machine_availability), 2) AS avg_availability
FROM factmanufacturing
GROUP BY machine_id
ORDER BY jobs_run DESC;

-- Job status breakdown
SELECT
    job_status,
    COUNT(*) AS job_count,
    ROUND(AVG(processing_time), 2) AS avg_processing_time
FROM factmanufacturing
GROUP BY job_status
ORDER BY job_count DESC;

-- Jobs with no actual execution recorded (data quality flag,
-- matches the finding of 129 such jobs from the validation phase)
SELECT
    job_id,
    machine_id,
    operation_type,
    scheduled_start_date_key
FROM factmanufacturing
WHERE actual_start_date_key IS NULL
ORDER BY job_id
LIMIT 20;

-- Material usage and energy consumption by operation type
SELECT
    operation_type,
    COUNT(*) AS job_count,
    SUM(material_used) AS total_material_used,
    SUM(energy_consumption) AS total_energy_consumed
FROM factmanufacturing
GROUP BY operation_type
ORDER BY total_energy_consumed DESC;


-- ============================================================
-- CROSS-FUNCTIONAL / ENTERPRISE-LEVEL
-- ============================================================

-- Enterprise revenue vs. cost comparison (Sales revenue vs Procurement spend, by month)
-- NOTE: these two modules' date ranges only partially overlap (Sales: 2023-2024,
-- Procurement: 2023-2024) -- this specific pairing is valid, unlike Finance which
-- has a separate, non-overlapping timeline (documented data quality finding).
SELECT
    d.month_name,
    d.month,
    COALESCE(SUM(sales.revenue), 0) AS sales_revenue,
    COALESCE(SUM(proc.spend), 0) AS procurement_spend
FROM dimdate d
LEFT JOIN (
    SELECT date_key, SUM(total_amount) AS revenue
    FROM factsales
    GROUP BY date_key
) sales ON d.date_key = sales.date_key
LEFT JOIN (
    SELECT order_date_key, SUM(total_cost) AS spend
    FROM factprocurement
    GROUP BY order_date_key
) proc ON d.date_key = proc.order_date_key
WHERE d.year = 2023
GROUP BY d.month_name, d.month
ORDER BY d.month;
