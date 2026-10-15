-- ============================================================
-- UC15 ERP Data Platform - Dashboard views
--
-- One flat view per dashboard area. Each joins a fact table to its dimensions, so Power BI
-- (or any tool) can read one table per page and needs no relationships to be set up.
--
-- Rules followed in every view:
--   * flags are stored as 0/1 whole numbers (works the same in a database connection and in CSV files)
--   * names, e-mail addresses and phone numbers of customers and employees are NOT included
--   * the data is shown as it is in the warehouse; known problems are marked with a flag or described
--     in dashboards/Dashboard_Design.md, never corrected (see docs/Data_Quality_Report.md)
-- Needs sql/10_data_quality_checks.sql to have been run first (vw_dash_data_checks reads vw_data_quality_checks).
-- Safe to run more than once.
-- ============================================================

-- SALES (2023, one record on 2024-01-01)
CREATE OR REPLACE VIEW vw_dash_sales AS
SELECT f.transaction_id, d.full_date AS sale_date, d.year, d.quarter, d.month, d.month_name, d.day_name,
       d.is_weekend::int AS is_weekend, f.customer_id, f.gender, f.age,
       CASE WHEN f.age < 25 THEN '18-24' WHEN f.age < 35 THEN '25-34' WHEN f.age < 45 THEN '35-44' WHEN f.age < 55 THEN '45-54' ELSE '55+' END AS age_group,
       f.product_category, f.quantity, f.price_per_unit, f.total_amount, f.daily_percent_change
FROM factsales f
JOIN dimdate d ON d.date_key = f.date_key;

-- PROCUREMENT (orders from 2023-01-01 to 2024-12-30). Cancelled orders are flagged: spend reports should leave them out (Finding 11)
CREATE OR REPLACE VIEW vw_dash_procurement AS
SELECT f.purchase_order_id, o.full_date AS order_date, date_trunc('month', o.full_date)::date AS order_month,
       o.year AS order_year, e.full_date AS expected_delivery_date, (e.full_date - o.full_date) AS planned_lead_days,
       s.supplier_id, f.supplier_name, f.item_id, f.item_name, f.po_status,
       (f.po_status = 'Cancelled')::int AS is_cancelled, f.quantity, f.unit_cost, f.total_cost,
       CASE WHEN f.po_status = 'Cancelled' THEN 0 ELSE f.total_cost END AS spend_excl_cancelled
FROM factprocurement f
JOIN dimsupplier s ON s.supplier_key = f.supplier_key
JOIN dimdate o ON o.date_key = f.order_date_key
LEFT JOIN dimdate e ON e.date_key = f.expected_delivery_date_key;

-- ACCOUNTS RECEIVABLE (documents from 2011 to 2016). Dates and delay columns do not agree with each other (Finding 9):
-- dates_consistent = 1 only when neither the due date nor the clearing date is earlier than the document date
CREATE OR REPLACE VIEW vw_dash_receivables AS
SELECT f.document_no, dd.full_date AS doc_date, dd.year AS doc_year, date_trunc('month', dd.full_date)::date AS doc_month,
       dn.full_date AS net_due_date, dc.full_date AS clearing_date, f.cust_num, f.payment_method_description, f.region, f.city, f.payment_term,
       f.delayflag::numeric::int AS delayflag, f.amount, f.days_overdue_delay,
       CASE WHEN f.days_overdue_delay <= 0 THEN '1 On time or early' WHEN f.days_overdue_delay <= 30 THEN '2 1-30 days late' WHEN f.days_overdue_delay <= 90 THEN '3 31-90 days late'
            WHEN f.days_overdue_delay <= 180 THEN '4 91-180 days late' ELSE '5 Over 180 days late' END AS overdue_bucket,
       (dn.full_date >= dd.full_date AND dc.full_date >= dd.full_date)::int AS dates_consistent
FROM factaccountsreceivable f
JOIN dimdate dd ON dd.date_key = f.doc_date_key
JOIN dimdate dn ON dn.date_key = f.net_due_date_key
JOIN dimdate dc ON dc.date_key = f.clearing_date_key;

-- INVENTORY DEMAND (12 months per item; the source has no year)
CREATE OR REPLACE VIEW vw_dash_inventory_demand AS
SELECT i.item_id, i.item_name, i.category, i.price_per_unit, m.month_key AS month_number, m.month_name,
       f.units_demanded, f.units_demanded * i.price_per_unit AS demand_value
FROM factinventorydemand f
JOIN dimiteminventory i ON i.item_key = f.item_key
JOIN dimmonth m ON m.month_key = f.month_key;

-- WAREHOUSE STOCK (one row per item; last restock in 2024)
CREATE OR REPLACE VIEW vw_dash_warehouse AS
SELECT w.item_id, w.category, w.zone, w.storage_location_id, d.full_date AS last_restock_date,
       f.stock_level, f.reorder_point, (f.stock_level < f.reorder_point)::int AS below_reorder_point, (f.stock_level - f.reorder_point) AS stock_above_reorder,
       f.lead_time_days, f.daily_demand, ROUND(f.stock_level / NULLIF(f.daily_demand, 0), 1) AS days_of_stock,
       f.stockout_count_last_month, f.total_orders_last_month, f.order_fulfillment_rate, f.turnover_ratio, f.forecasted_demand_next_7d,
       f.unit_price, f.stock_level * f.unit_price AS stock_value, f.picking_time_seconds, f.handling_cost_per_unit, f.holding_cost_per_unit_day, f.kpi_score
FROM factwarehousesnapshot f
JOIN dimwarehouseitem w ON w.warehouse_item_key = f.warehouse_item_key
JOIN dimdate d ON d.date_key = f.date_key;

-- MANUFACTURING (jobs scheduled 2023-03-18 to 2023-03-25: one week, so no long-term trend). Failed jobs have no actual start (Finding 6)
CREATE OR REPLACE VIEW vw_dash_manufacturing AS
SELECT f.job_id, s.full_date AS scheduled_start_date, a.full_date AS actual_start_date, (a.full_date - s.full_date) AS start_delay_days,
       f.machine_id, f.operation_type, f.job_status, (f.job_status = 'Failed')::int AS is_failed, (f.job_status = 'Completed')::int AS is_completed,
       f.optimization_category, f.material_used, f.processing_time, f.energy_consumption, f.machine_availability
FROM factmanufacturing f
JOIN dimdate s ON s.date_key = f.scheduled_start_date_key
LEFT JOIN dimdate a ON a.date_key = f.actual_start_date_key;

-- ASSETS
CREATE OR REPLACE VIEW vw_dash_assets AS
SELECT asset_id, location, asset_type, operational_state, disposal_decision, install_year, last_maintenance_year,
       usage_hours_per_month, failure_count, condition_score, maintenance_cost_last_year
FROM dimasset;

-- CUSTOMERS (no name, e-mail or phone)
CREATE OR REPLACE VIEW vw_dash_customers AS
SELECT customer_id, city, state, country, customer_type, customer_status, registration_date,
       EXTRACT(YEAR FROM registration_date)::int AS registration_year, (registration_date > CURRENT_DATE)::int AS registered_in_future, credit_limit
FROM dimcustomermaster;

-- EMPLOYEES (no names)
CREATE OR REPLACE VIEW vw_dash_employees AS
SELECT employee_key AS employee_number, gender, age,
       CASE WHEN age < 30 THEN 'Under 30' WHEN age < 40 THEN '30-39' WHEN age < 50 THEN '40-49' ELSE '50+' END AS age_group,
       salary, expenditure, savings, expenditure_percentage, savings_percentage
FROM dimemployee;

-- FINANCE (dates run from 2025 into 2027). The measures do not follow the usual accounting formulas (Finding 12): show them as given
CREATE OR REPLACE VIEW vw_dash_finance AS
SELECT f.transaction_id, d.full_date AS transaction_date, d.year, date_trunc('month', d.full_date)::date AS transaction_month, f.account_type,
       f.transaction_amount, f.cash_flow, f.net_income, f.revenue, f.expenditure, f.gross_profit, f.profit_margin, f.transaction_volume, f.accuracy_score
FROM factfinance f
JOIN dimdate d ON d.date_key = f.date_key;

-- DATA TRUST (the data quality checks of sql/10_data_quality_checks.sql)
CREATE OR REPLACE VIEW vw_dash_data_checks AS
SELECT check_id, area, check_name, finding, expected, violations, status FROM vw_data_quality_checks;
