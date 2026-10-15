-- ============================================================
-- UC15 ERP Data Platform - Data quality checks on the warehouse
--
-- One view that runs every check and gives each a status:
--   PASS          no rows break the rule
--   KNOWN ISSUE   the rule is broken in exactly the way the Data Quality Report documents
--   UNEXPECTED    the result differs from what is documented: investigate
--
-- Check groups:  I = integrity (keys),  R = business rules that should hold,
--                K = known issues recorded in docs/Data_Quality_Report.md
-- 'expected' is the number of rows documented for that check (0 means it must be clean).
-- K08 depends on today's date, so it has no fixed expected number.
-- Run:  SELECT * FROM vw_data_quality_checks;
-- ============================================================
CREATE OR REPLACE VIEW vw_data_quality_checks AS
WITH results AS (
  SELECT 'I01' AS check_id, 'Integrity' AS area, 'Orphan foreign keys (all 14 relationships)' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) FROM factsales x WHERE NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.date_key)) + (SELECT COUNT(*) FROM factaccountsreceivable x WHERE NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.doc_date_key)) + (SELECT COUNT(*) FROM factaccountsreceivable x WHERE x.net_due_date_key IS NOT NULL AND NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.net_due_date_key)) + (SELECT COUNT(*) FROM factaccountsreceivable x WHERE x.clearing_date_key IS NOT NULL AND NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.clearing_date_key)) + (SELECT COUNT(*) FROM factprocurement x WHERE NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.order_date_key)) + (SELECT COUNT(*) FROM factprocurement x WHERE x.expected_delivery_date_key IS NOT NULL AND NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.expected_delivery_date_key)) + (SELECT COUNT(*) FROM factprocurement x WHERE NOT EXISTS (SELECT 1 FROM dimsupplier y WHERE y.supplier_key = x.supplier_key)) + (SELECT COUNT(*) FROM factfinance x WHERE NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.date_key)) + (SELECT COUNT(*) FROM factinventorydemand x WHERE NOT EXISTS (SELECT 1 FROM dimiteminventory y WHERE y.item_key = x.item_key)) + (SELECT COUNT(*) FROM factinventorydemand x WHERE NOT EXISTS (SELECT 1 FROM dimmonth y WHERE y.month_key = x.month_key)) + (SELECT COUNT(*) FROM factwarehousesnapshot x WHERE NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.date_key)) + (SELECT COUNT(*) FROM factwarehousesnapshot x WHERE NOT EXISTS (SELECT 1 FROM dimwarehouseitem y WHERE y.warehouse_item_key = x.warehouse_item_key)) + (SELECT COUNT(*) FROM factmanufacturing x WHERE NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.scheduled_start_date_key)) + (SELECT COUNT(*) FROM factmanufacturing x WHERE x.actual_start_date_key IS NOT NULL AND NOT EXISTS (SELECT 1 FROM dimdate y WHERE y.date_key = x.actual_start_date_key)))::bigint AS violations
  UNION ALL
  SELECT 'I02' AS check_id, 'Integrity' AS area, 'Duplicate transaction_id in FactSales' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT transaction_id) FROM factsales))::bigint AS violations
  UNION ALL
  SELECT 'I03' AS check_id, 'Integrity' AS area, 'Duplicate transaction_id in FactFinance' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT transaction_id) FROM factfinance))::bigint AS violations
  UNION ALL
  SELECT 'I04' AS check_id, 'Integrity' AS area, 'Duplicate job_id in FactManufacturing' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT job_id) FROM factmanufacturing))::bigint AS violations
  UNION ALL
  SELECT 'I05' AS check_id, 'Integrity' AS area, 'Duplicate document_no in FactAccountsReceivable' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT document_no) FROM factaccountsreceivable))::bigint AS violations
  UNION ALL
  SELECT 'I06' AS check_id, 'Integrity' AS area, 'Duplicate purchase_order_id in FactProcurement' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT purchase_order_id) FROM factprocurement))::bigint AS violations
  UNION ALL
  SELECT 'I07' AS check_id, 'Integrity' AS area, 'Duplicate asset_id in DimAsset' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT asset_id) FROM dimasset))::bigint AS violations
  UNION ALL
  SELECT 'I08' AS check_id, 'Integrity' AS area, 'Duplicate customer_id in DimCustomerMaster' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM dimcustomermaster))::bigint AS violations
  UNION ALL
  SELECT 'I09' AS check_id, 'Integrity' AS area, 'Duplicate supplier_id in DimSupplier' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT supplier_id) FROM dimsupplier))::bigint AS violations
  UNION ALL
  SELECT 'I10' AS check_id, 'Integrity' AS area, 'Duplicate item_id in DimItemInventory' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT item_id) FROM dimiteminventory))::bigint AS violations
  UNION ALL
  SELECT 'I11' AS check_id, 'Integrity' AS area, 'Duplicate item_id in DimWarehouseItem' AS check_name, '-' AS finding, 0::bigint AS expected, ((SELECT COUNT(*) - COUNT(DISTINCT item_id) FROM dimwarehouseitem))::bigint AS violations
  UNION ALL
  SELECT 'R01' AS check_id, 'Business rule' AS area, 'Sales: total_amount differs from quantity x price' AS check_name, '-' AS finding, 0::bigint AS expected, (SELECT COUNT(*) FROM factsales WHERE ABS(total_amount - quantity * price_per_unit) >= 0.01)::bigint AS violations
  UNION ALL
  SELECT 'R02' AS check_id, 'Business rule' AS area, 'Procurement: total_cost differs from quantity x unit_cost' AS check_name, '-' AS finding, 0::bigint AS expected, (SELECT COUNT(*) FROM factprocurement WHERE ABS(total_cost - quantity * unit_cost) >= 0.01)::bigint AS violations
  UNION ALL
  SELECT 'R03' AS check_id, 'Business rule' AS area, 'Employee: salary differs from expenditure + savings' AS check_name, '-' AS finding, 0::bigint AS expected, (SELECT COUNT(*) FROM dimemployee WHERE ABS(salary - (expenditure + savings)) >= 0.01)::bigint AS violations
  UNION ALL
  SELECT 'R04' AS check_id, 'Business rule' AS area, 'Manufacturing: empty actual start is not exactly the Failed jobs' AS check_name, 'Finding 6' AS finding, 0::bigint AS expected, (SELECT COUNT(*) FROM factmanufacturing WHERE (actual_start_date_key IS NULL) <> (job_status = 'Failed'))::bigint AS violations
  UNION ALL
  SELECT 'R05' AS check_id, 'Business rule' AS area, 'Zero or negative quantity or amount (Sales, Procurement, Receivables)' AS check_name, '-' AS finding, 0::bigint AS expected, (SELECT (SELECT COUNT(*) FROM factsales WHERE quantity <= 0 OR total_amount <= 0) + (SELECT COUNT(*) FROM factprocurement WHERE quantity <= 0 OR total_cost <= 0) + (SELECT COUNT(*) FROM factaccountsreceivable WHERE amount < 0))::bigint AS violations
  UNION ALL
  SELECT 'R06' AS check_id, 'Business rule' AS area, 'Procurement: expected delivery before the order date' AS check_name, '-' AS finding, 0::bigint AS expected, (SELECT COUNT(*) FROM factprocurement f JOIN dimdate o ON o.date_key = f.order_date_key JOIN dimdate e ON e.date_key = f.expected_delivery_date_key WHERE e.full_date < o.full_date)::bigint AS violations
  UNION ALL
  SELECT 'R07' AS check_id, 'Business rule' AS area, 'Asset condition_score outside 0 to 1' AS check_name, '-' AS finding, 0::bigint AS expected, (SELECT COUNT(*) FROM dimasset WHERE condition_score < 0 OR condition_score > 1)::bigint AS violations
  UNION ALL
  SELECT 'R08' AS check_id, 'Business rule' AS area, 'Warehouse order_fulfillment_rate outside 0 to 1' AS check_name, '-' AS finding, 0::bigint AS expected, (SELECT COUNT(*) FROM factwarehousesnapshot WHERE order_fulfillment_rate < 0 OR order_fulfillment_rate > 1)::bigint AS violations
  UNION ALL
  SELECT 'R09' AS check_id, 'Business rule' AS area, 'Sales age outside 18 to 100' AS check_name, '-' AS finding, 0::bigint AS expected, (SELECT COUNT(*) FROM factsales WHERE age < 18 OR age > 100)::bigint AS violations
  UNION ALL
  SELECT 'R10' AS check_id, 'Business rule' AS area, 'Purchase order status not one of the four allowed values' AS check_name, '-' AS finding, 0::bigint AS expected, (SELECT COUNT(*) FROM factprocurement WHERE po_status NOT IN ('Delivered','Ordered','Cancelled','Partially Delivered'))::bigint AS violations
  UNION ALL
  SELECT 'K01' AS check_id, 'Known issue' AS area, 'Receivables: due date before the document date' AS check_name, 'Finding 9' AS finding, 11269::bigint AS expected, (SELECT COUNT(*) FROM factaccountsreceivable a JOIN dimdate dd ON dd.date_key = a.doc_date_key JOIN dimdate dn ON dn.date_key = a.net_due_date_key JOIN dimdate dc ON dc.date_key = a.clearing_date_key WHERE dn.full_date < dd.full_date)::bigint AS violations
  UNION ALL
  SELECT 'K02' AS check_id, 'Known issue' AS area, 'Receivables: clearing date before the document date' AS check_name, 'Finding 9' AS finding, 12104::bigint AS expected, (SELECT COUNT(*) FROM factaccountsreceivable a JOIN dimdate dd ON dd.date_key = a.doc_date_key JOIN dimdate dn ON dn.date_key = a.net_due_date_key JOIN dimdate dc ON dc.date_key = a.clearing_date_key WHERE dc.full_date < dd.full_date)::bigint AS violations
  UNION ALL
  SELECT 'K03' AS check_id, 'Known issue' AS area, 'Receivables: days_overdue_delay differs from clearing date minus due date' AS check_name, 'Finding 9' AS finding, 16910::bigint AS expected, (SELECT COUNT(*) FROM factaccountsreceivable a JOIN dimdate dd ON dd.date_key = a.doc_date_key JOIN dimdate dn ON dn.date_key = a.net_due_date_key JOIN dimdate dc ON dc.date_key = a.clearing_date_key WHERE a.days_overdue_delay <> (dc.full_date - dn.full_date))::bigint AS violations
  UNION ALL
  SELECT 'K04' AS check_id, 'Known issue' AS area, 'Receivables: delayflag disagrees with days_overdue_delay above 0' AS check_name, 'Finding 9' AS finding, 5797::bigint AS expected, (SELECT COUNT(*) FROM factaccountsreceivable WHERE (days_overdue_delay > 0) <> (delayflag::numeric = 1))::bigint AS violations
  UNION ALL
  SELECT 'K05' AS check_id, 'Known issue' AS area, 'Finance: net_income differs from revenue - expenditure' AS check_name, 'Finding 12' AS finding, 1000::bigint AS expected, (SELECT COUNT(*) FROM factfinance WHERE ABS(net_income - (revenue - expenditure)) >= 0.01)::bigint AS violations
  UNION ALL
  SELECT 'K06' AS check_id, 'Known issue' AS area, 'Finance: gross_profit differs from revenue - expenditure' AS check_name, 'Finding 12' AS finding, 1000::bigint AS expected, (SELECT COUNT(*) FROM factfinance WHERE ABS(gross_profit - (revenue - expenditure)) >= 0.01)::bigint AS violations
  UNION ALL
  SELECT 'K07' AS check_id, 'Known issue' AS area, 'Finance: profit_margin differs from net_income / revenue' AS check_name, 'Finding 12' AS finding, 998::bigint AS expected, (SELECT COUNT(*) FROM factfinance WHERE ABS(profit_margin - net_income / NULLIF(revenue, 0)) >= 0.0005)::bigint AS violations
  UNION ALL
  SELECT 'K08' AS check_id, 'Known issue' AS area, 'Customers registered after today (changes with the date)' AS check_name, 'Finding 10' AS finding, NULL::bigint AS expected, (SELECT COUNT(*) FROM dimcustomermaster WHERE registration_date > CURRENT_DATE)::bigint AS violations
  UNION ALL
  SELECT 'K09' AS check_id, 'Known issue' AS area, 'Sales: empty daily_percent_change' AS check_name, 'Finding 10' AS finding, 1::bigint AS expected, (SELECT COUNT(*) FROM factsales WHERE daily_percent_change IS NULL)::bigint AS violations
  UNION ALL
  SELECT 'K10' AS check_id, 'Known issue' AS area, 'Procurement: orders with status Cancelled' AS check_name, 'Finding 11' AS finding, 330::bigint AS expected, (SELECT COUNT(*) FROM factprocurement WHERE po_status = 'Cancelled')::bigint AS violations
  UNION ALL
  SELECT 'K11' AS check_id, 'Known issue' AS area, 'Procurement: suppliers that appear under more than one name' AS check_name, 'Finding 4' AS finding, 10::bigint AS expected, (SELECT COUNT(*) FROM (SELECT supplier_key FROM factprocurement GROUP BY supplier_key HAVING COUNT(DISTINCT supplier_name) > 1) t)::bigint AS violations
)
SELECT check_id, area, check_name, finding, expected, violations,
       CASE WHEN violations = 0 THEN 'PASS'
            WHEN expected IS NULL THEN 'KNOWN ISSUE'
            WHEN violations = expected THEN 'KNOWN ISSUE'
            ELSE 'UNEXPECTED' END AS status
FROM results
ORDER BY check_id;
