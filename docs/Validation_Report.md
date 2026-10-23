# Validation Report

**Project:** UC15 - Enterprise Resource Planning Data Platform (ERPDP)  
**Sprint:** 3 (Governance, lineage and analytics)  
**Repository:** Data-Engineering-UC15

---

## 1. Summary

This report shows that the data in the warehouse is the same data that came out of the source files, and that the problems we know about are still exactly the problems we documented.

| Check | Result |
|---|---|
| Raw file to cleaned file to warehouse, for the 10 datasets | **9 match exactly, 1 matches after a documented duplicate removal, 0 differ** |
| Warehouse control totals (row count and one total for each of the 15 tables) | **15 of 15 PASS** |
| Data quality checks (32 checks) | **21 PASS, 11 KNOWN ISSUE, 0 UNEXPECTED** |

A **KNOWN ISSUE** is a rule that is broken in exactly the way the Data Quality Report documents. An **UNEXPECTED** result would mean that something changed and has to be investigated. There are none.

---

## 2. What was checked and how

| Level | What it proves | Where it runs |
|---|---|---|
| 1. Layer reconciliation | No rows or amounts were lost or invented between the raw file, the cleaned file and the warehouse. | `python/ERP_Layer_Reconciliation.py`, result in `silver/validation/layer_reconciliation.csv` |
| 2. Warehouse control totals | Each warehouse table holds the expected number of rows and the expected total. | `sql/05_reconciliation_checks.sql`, also run by the Pentaho job `ETL_Load_Warehouse` after every load |
| 3. Data quality checks | Keys are unique and linked, business rules hold, and the known problems have not changed. | `sql/10_data_quality_checks.sql` (the view `vw_data_quality_checks`), result in `silver/validation/data_quality_checks.csv` |

The rule checks of the earlier validation scripts in `silver/validation/` (Sprint 2) work on the cleaned files. The checks here work on the finished warehouse, so they also cover the load.

---

## 3. Layer reconciliation

For each dataset: the number of rows, and the total of one numeric column, at each layer. For Inventory the total is the sum of the 12 monthly demand columns.

| Dataset | Measure | Raw rows | Cleaned rows | Loaded rows | Raw total | Cleaned total | Warehouse total | Result |
|---|---|---|---|---|---|---|---|---|
| Sales | total_amount | 1,000 | 1,000 | 1,000 | 456,000 | 456,000 | 456,000 | PASS |
| Customer Master | credit_limit | 1,500 | 1,500 | 1,500 | 777,900,627.40 | 777,900,627.40 | 777,900,627.40 | PASS |
| Asset | maintenance_cost_last_year | 1,245 | 1,245 | 1,245 | 1,354,770.44 | 1,354,770.44 | 1,354,770.44 | PASS |
| Account | amount | 45,839 | 45,839 | 45,839 | 816,262,430 | 816,262,430 | 816,262,430 | PASS |
| Procurement | total_cost | 1,300 | 1,300 | 1,300 | 982,390,348.71 | 982,390,348.71 | 982,390,348.71 | PASS |
| Employee | salary | 35 | 35 | 35 | 1,520,600 | 1,520,600 | 1,520,600 | PASS |
| Finance | transaction_amount | 1,000 | 1,000 | 1,000 | 2,535,701 | 2,535,701 | 2,535,701 | PASS |
| Inventory | sum of the 12 monthly demand columns | 1,000 | 1,000 | 1,000 | 16,961,896 | 16,961,896 | 16,961,896 | PASS |
| Manufacturing | material_used | 1,000 | 1,000 | 1,000 | 3,026.48 | 3,026.48 | 3,026.48 | PASS |
| Warehouse | stock_level | 6,408 | 3,204 | 3,204 | 1,688,454 | 844,227 | 844,227 | EXPLAINED |

Nine datasets have identical rows and totals at all three layers. **Warehouse** is the only difference: the raw file holds every record twice (6,408 rows), and its raw total is exactly double the cleaned one. Cleaning removes the 3,204 exact duplicates, and from there the cleaned file and the warehouse agree. For Procurement, the loaded rows are the orders in FactProcurement (the supplier table has 10 rows), and for Inventory they are the items in DimItemInventory (the demand table has 12 rows per item, 12,000 in all).

---

## 4. Warehouse control totals

`sql/05_reconciliation_checks.sql` compares each of the 15 tables with figures calculated straight from the cleaned files, for example the total of FactSales is 456,000.00 and the total of FactProcurement is 982,390,348.71. All 15 tables match. The Pentaho job `ETL_Load_Warehouse` runs the same comparison after loading, writes the result to the audit table `etl_run_log` and stops with a FAILED entry if any table does not match.

---

## 5. Data quality checks

Run them with `SELECT * FROM vw_data_quality_checks;`. *Expected* is the number of rows documented for the check, and 0 means the check must be clean.

| Check | Group | What it tests | Finding | Expected | Found | Status |
|---|---|---|---|---|---|---|
| I01 | Integrity | Orphan foreign keys (all 14 relationships) |  | 0 | 0 | PASS |
| I02 | Integrity | Duplicate transaction_id in FactSales |  | 0 | 0 | PASS |
| I03 | Integrity | Duplicate transaction_id in FactFinance |  | 0 | 0 | PASS |
| I04 | Integrity | Duplicate job_id in FactManufacturing |  | 0 | 0 | PASS |
| I05 | Integrity | Duplicate document_no in FactAccountsReceivable |  | 0 | 0 | PASS |
| I06 | Integrity | Duplicate purchase_order_id in FactProcurement |  | 0 | 0 | PASS |
| I07 | Integrity | Duplicate asset_id in DimAsset |  | 0 | 0 | PASS |
| I08 | Integrity | Duplicate customer_id in DimCustomerMaster |  | 0 | 0 | PASS |
| I09 | Integrity | Duplicate supplier_id in DimSupplier |  | 0 | 0 | PASS |
| I10 | Integrity | Duplicate item_id in DimItemInventory |  | 0 | 0 | PASS |
| I11 | Integrity | Duplicate item_id in DimWarehouseItem |  | 0 | 0 | PASS |
| K01 | Known issue | Receivables: due date before the document date | Finding 9 | 11,269 | 11,269 | KNOWN ISSUE |
| K02 | Known issue | Receivables: clearing date before the document date | Finding 9 | 12,104 | 12,104 | KNOWN ISSUE |
| K03 | Known issue | Receivables: days_overdue_delay differs from clearing date minus due date | Finding 9 | 16,910 | 16,910 | KNOWN ISSUE |
| K04 | Known issue | Receivables: delayflag disagrees with days_overdue_delay above 0 | Finding 9 | 5,797 | 5,797 | KNOWN ISSUE |
| K05 | Known issue | Finance: net_income differs from revenue - expenditure | Finding 12 | 1,000 | 1,000 | KNOWN ISSUE |
| K06 | Known issue | Finance: gross_profit differs from revenue - expenditure | Finding 12 | 1,000 | 1,000 | KNOWN ISSUE |
| K07 | Known issue | Finance: profit_margin differs from net_income / revenue | Finding 12 | 998 | 998 | KNOWN ISSUE |
| K08 | Known issue | Customers registered after today (changes with the date) | Finding 10 | date-dependent | 42 | KNOWN ISSUE |
| K09 | Known issue | Sales: empty daily_percent_change | Finding 10 | 1 | 1 | KNOWN ISSUE |
| K10 | Known issue | Procurement: orders with status Cancelled | Finding 11 | 330 | 330 | KNOWN ISSUE |
| K11 | Known issue | Procurement: suppliers that appear under more than one name | Finding 4 | 10 | 10 | KNOWN ISSUE |
| R01 | Business rule | Sales: total_amount differs from quantity x price |  | 0 | 0 | PASS |
| R02 | Business rule | Procurement: total_cost differs from quantity x unit_cost |  | 0 | 0 | PASS |
| R03 | Business rule | Employee: salary differs from expenditure + savings |  | 0 | 0 | PASS |
| R04 | Business rule | Manufacturing: empty actual start is not exactly the Failed jobs | Finding 6 | 0 | 0 | PASS |
| R05 | Business rule | Zero or negative quantity or amount (Sales, Procurement, Receivables) |  | 0 | 0 | PASS |
| R06 | Business rule | Procurement: expected delivery before the order date |  | 0 | 0 | PASS |
| R07 | Business rule | Asset condition_score outside 0 to 1 |  | 0 | 0 | PASS |
| R08 | Business rule | Warehouse order_fulfillment_rate outside 0 to 1 |  | 0 | 0 | PASS |
| R09 | Business rule | Sales age outside 18 to 100 |  | 0 | 0 | PASS |
| R10 | Business rule | Purchase order status not one of the four allowed values |  | 0 | 0 | PASS |

Check K08 counts customers whose registration date is later than today. It was 42 on 15 October 2026 and 47 on 4 October, and it falls as the calendar moves forward, so it has no fixed expected number.

**What the passing checks tell us.** No foreign key points at a missing row, no business ID is repeated, sales and procurement totals equal quantity times price in every row, an employee's salary equals expenditure plus savings in every row, and the manufacturing jobs without an actual start are exactly the Failed jobs.

**What the known issues tell us.** They are the problems in the source data that the Data Quality Report describes, now measured on the finished warehouse:

- Receivables dates and delay columns do not agree with each other (K01 to K04, Finding 9).
- The finance measures do not follow the usual accounting relationships (K05 to K07, Finding 12).
- Suppliers appear under several names (K11, Finding 4), one sales value is empty and some customers have future registration dates (K08 and K09, Finding 10).
- A quarter of the purchase orders are cancelled and still carry a cost (K10, Finding 11).

None of these were changed, because correcting them would mean inventing values. They stay in the warehouse and the reports that use them carry the caveats given in the Data Quality Report.

---

## 6. The Bronze copy (for information)

The Sprint 1 staging copy in `bronze/staging/` is not an input to the cleaning, so it is outside the reconciliation above. Two of its files do not match the Silver input: `employees.tsv` has 70 rows (each of the 35 employees twice), and `procurement.tsv` has 2,000 rows from a different procurement file. See Sections 8 and 9 of `lineage/Data_Lineage.md`.

---

## 7. Can the cleaning be repeated? (reproducibility)

The end-to-end job runs the cleaning scripts again, so we tested whether running them again gives the files that are in the repository. We ran both cleaning scripts on a clean copy of the repository and compared all 10 cleaned files with the committed ones.

| Result | Files |
|---|---|
| Identical, byte for byte | 9 of 10 (Account, Asset, Customer Master, Employee, Inventory, Manufacturing, Procurement, Sales, Warehouse) |
| Same rows, columns and values; 22 numbers differ only in the 16th or 17th digit | Finance (a floating-point formatting difference of the software, not a data change) |

The test found one real problem, which is now fixed. The second cleaning script only converted a column to a date when its type was `object`. In the newest version of pandas (3.0), text columns have a new type called `str`, so the conversion was silently skipped and the 1,000 Sales dates stayed as `24-11-2023`, which the Pentaho load cannot read. The fix is two lines in `python/ERP_Data_Cleaning_separate2.py`: a column is now treated as text when it is `object` or `str`. After the fix, the Sales dates are identical to the committed file, and all 1,000 equal the raw dates read as day-month-year, including the 414 where the day is 12 or less and day and month could be confused.

---

## 8. How to run the checks again

**All in one run:** open `pentaho/jobs/ETL_End_To_End.kjb` in Spoon and click Run. It cleans and validates the raw files, loads the warehouse, runs the layer reconciliation and the data quality gate, and stops with a FAILED entry in `etl_run_log` if any step fails. Or run the parts one by one:

1. Load the warehouse with the Pentaho job `ETL_Load_Warehouse` (it reconciles by itself and writes `etl_run_log`).
2. In pgAdmin on `uc15_dw`, run `sql/10_data_quality_checks.sql` once to create the view, then `SELECT * FROM vw_data_quality_checks;`. Every row must be PASS or KNOWN ISSUE.
3. In Terminal, from the `python/` folder: `python3 ERP_Layer_Reconciliation.py`. The last line must read `0 DIFFERENT`.

If the source data changes on purpose, update the control totals in `sql/05_reconciliation_checks.sql` and the *expected* numbers in `sql/10_data_quality_checks.sql`, and update the Data Quality Report.

---

## 9. Conclusion and limits

The warehouse holds exactly what the source files contain, apart from the duplicate rows removed on purpose, and the known problems of the source data are stable and documented. These checks show that the pipeline preserves the data. They do not show that the source data is correct: for example, they cannot tell which of the finance measures is right.

The checks cover the 15 warehouse tables. The REST API demo and the audit table are separate, and the Tableau dashboards are not covered by these checks. They read exported copies of the dashboard views, whose totals equal the warehouse control totals, and the figures of three sheets were compared with the warehouse by hand (see `dashboards/Tableau_Dashboard_Notes.md`).
