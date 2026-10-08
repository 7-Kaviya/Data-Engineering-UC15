-- ============================================================
-- UC15 ERP Data Platform - Warehouse reconciliation
-- Compares the data loaded into PostgreSQL with control totals
-- calculated directly from the cleaned Silver CSV files
-- (silver/cleansing/cleaned_datasets and reference_data).
--
-- For every table it checks the row count and one numeric total.
-- All 15 rows should show PASS. Run it after any reload.
-- ============================================================
WITH expected (table_name, exp_rows, exp_total) AS (
    VALUES
    ('dimdate',                6209,  0.00),
    ('dimmonth',               12,    0.00),
    ('dimsupplier',            10,    0.00),
    ('dimwarehouseitem',       3204,  0.00),
    ('dimiteminventory',       1000,  57358.00),
    ('dimcustomermaster',      1500,  777900627.40),
    ('dimasset',               1245,  1354770.44),
    ('dimemployee',            35,    1520600.00),
    ('factsales',              1000,  456000.00),
    ('factfinance',            1000,  2535701.00),
    ('factmanufacturing',      1000,  3026.48),
    ('factaccountsreceivable', 45839, 816262430.00),
    ('factprocurement',        1300,  982390348.71),
    ('factinventorydemand',    12000, 16961896.00),
    ('factwarehousesnapshot',  3204,  844227.00)
),
actual (table_name, act_rows, act_total) AS (
    SELECT 'dimdate',                COUNT(*), 0::numeric FROM dimdate
    UNION ALL SELECT 'dimmonth',     COUNT(*), 0::numeric FROM dimmonth
    UNION ALL SELECT 'dimsupplier',  COUNT(*), 0::numeric FROM dimsupplier
    UNION ALL SELECT 'dimwarehouseitem', COUNT(*), 0::numeric FROM dimwarehouseitem
    UNION ALL SELECT 'dimiteminventory',  COUNT(*), ROUND(SUM(price_per_unit)::numeric, 2) FROM dimiteminventory
    UNION ALL SELECT 'dimcustomermaster', COUNT(*), ROUND(SUM(credit_limit)::numeric, 2) FROM dimcustomermaster
    UNION ALL SELECT 'dimasset',          COUNT(*), ROUND(SUM(maintenance_cost_last_year)::numeric, 2) FROM dimasset
    UNION ALL SELECT 'dimemployee',       COUNT(*), ROUND(SUM(salary)::numeric, 2) FROM dimemployee
    UNION ALL SELECT 'factsales',         COUNT(*), ROUND(SUM(total_amount)::numeric, 2) FROM factsales
    UNION ALL SELECT 'factfinance',       COUNT(*), ROUND(SUM(transaction_amount)::numeric, 2) FROM factfinance
    UNION ALL SELECT 'factmanufacturing', COUNT(*), ROUND(SUM(material_used)::numeric, 2) FROM factmanufacturing
    UNION ALL SELECT 'factaccountsreceivable', COUNT(*), ROUND(SUM(amount)::numeric, 2) FROM factaccountsreceivable
    UNION ALL SELECT 'factprocurement',   COUNT(*), ROUND(SUM(total_cost)::numeric, 2) FROM factprocurement
    UNION ALL SELECT 'factinventorydemand', COUNT(*), ROUND(SUM(units_demanded)::numeric, 2) FROM factinventorydemand
    UNION ALL SELECT 'factwarehousesnapshot', COUNT(*), ROUND(SUM(stock_level)::numeric, 2) FROM factwarehousesnapshot
)
SELECT e.table_name,
       e.exp_rows,
       a.act_rows,
       e.exp_total,
       a.act_total,
       CASE WHEN e.exp_rows = a.act_rows
             AND ABS(e.exp_total - COALESCE(a.act_total, 0)) < 0.05
            THEN 'PASS' ELSE 'FAIL' END AS status
FROM expected e
JOIN actual a ON a.table_name = e.table_name
ORDER BY (e.table_name LIKE 'fact%'), e.table_name;
