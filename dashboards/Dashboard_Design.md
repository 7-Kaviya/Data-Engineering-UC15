# Dashboard Design

**Project:** UC15 - Enterprise Resource Planning Data Platform (ERPDP)  
**Sprint:** 3 (Governance, lineage and analytics)  
**Repository:** Data-Engineering-UC15

---

## 1. Purpose

A management dashboard for ABC Global Enterprises that shows the state of each ERP area on one page and, on a last page, how far the numbers can be trusted. It reads only from the warehouse (`uc15_dw`), so every figure can be traced back through `lineage/Data_Lineage.md`.

**Status:** the data layer is built and tested: the SQL views, the CSV files and the check values below. The Power BI file itself has not been built yet (Power BI Desktop runs only on Windows), so Section 9 says how to build it. Nothing in this document was tested inside Power BI.

---

## 2. How the data reaches Power BI

`sql/11_dashboard_views.sql` creates 11 flat views, one per dashboard area. Each view joins a fact table to its dimensions, so a page needs one table and no relationships. The views contain no customer or employee names, e-mail addresses or phone numbers.

| View (also the CSV file name) | Rows | Used by page |
|---|---|---|
| `vw_dash_sales` | 1,000 | 2 Sales |
| `vw_dash_procurement` | 1,300 | 3 Procurement |
| `vw_dash_receivables` | 45,839 | 4 Receivables |
| `vw_dash_inventory_demand` | 12,000 | 5 Inventory and warehouse |
| `vw_dash_warehouse` | 3,204 | 5 Inventory and warehouse |
| `vw_dash_manufacturing` | 1,000 | 6 Manufacturing and assets |
| `vw_dash_assets` | 1,245 | 6 Manufacturing and assets |
| `vw_dash_customers` | 1,500 | 7 Customers and employees |
| `vw_dash_employees` | 35 | 7 Customers and employees |
| `vw_dash_finance` | 1,000 | 8 Finance |
| `vw_dash_data_checks` | 32 | 9 Data trust |

Two ways to load the data in Power BI Desktop: **Get data > Text/CSV** on the files in `dashboards/data/` (simplest, no database connection needed), or **Get data > PostgreSQL database** on the views. The page 9 table `layer_reconciliation.csv` is also in the data folder.

To refresh after the warehouse is reloaded: run `sh dashboards/export_dashboard_data.sh` from the repository folder, then choose Refresh in Power BI.

---

## 3. Rules for every page

1. **Each page states its period.** The modules do not overlap in time: Receivables 2011 to 2016, Procurement 2023 to 2024, Sales 2023 (one record on 1 January 2024), Warehouse restocks in 2024, Manufacturing one week in March 2023, Finance 2025 to 2027. No page puts two modules on one time axis (Finding 3).
2. **Known problems are shown, not hidden.** Where a page uses data with a documented problem, a text box on the page says so, in one sentence, with the finding number.
3. **Measures, not raw columns.** Every number on a page comes from a named measure (Section 5), so the definition is in one place.
4. **Procurement spend leaves out cancelled orders** unless the page says otherwise (Finding 11).
5. **Plain titles.** A page title says what the page answers, for example "Which suppliers do we spend most with?".

---

## 4. The pages

Every number in the *Check* column was calculated from the views, so a card that shows a different value means a setting is wrong (for example a filter, or a measure that uses the wrong column).

### Page 1. Executive overview

*Answers:* How is each part of the business doing, and can we trust the numbers?

*Text box on the page:* Each card shows its own period, because the modules cover different years.

| Visual | Type | Fields |
|---|---|---|
| One card per area | Card | [Total Revenue], [Spend (excl. cancelled)], [Receivable Amount], [Delay Rate], [Items Below Reorder Point], [Failed Job Rate] |
| Data trust card | Card | [Checks Passed], [Known Issues], [Unexpected] |
| Area labels | Text | Period under each card, from Section 3 rule 1 |

| Check | Expected value |
|---|---|
| Sales revenue (1 Jan 2023 to 1 Jan 2024) | 456,000 |
| Procurement spend excluding cancelled (orders 2023 to 2024) | 735,447,294.22 |
| Receivable amount (documents 2011 to 2016) | 816,262,430 |
| Receivables flagged as delayed | 65.7% |
| Warehouse items below the reorder point | 237 of 3,204 (7.4%) |
| Manufacturing jobs that failed | 12.9% |
| Data quality checks | 21 PASS, 11 KNOWN ISSUE, 0 UNEXPECTED |

### Page 2. Sales

*Answers:* What do we sell, to whom and when?

*Text box on the page:* Sales cover 2023. The customer IDs in this file do not match any other module (Finding 1).

| Visual | Type | Fields |
|---|---|---|
| Revenue, transactions, average order, units | Cards | [Total Revenue], [Sales Transactions], [Avg Order Value], [Units Sold] |
| Revenue by month | Column chart | Axis: `month_name` sorted by `month`; value: [Total Revenue] |
| Revenue by category | Bar chart | Axis: `product_category`; value: [Total Revenue] |
| Revenue by gender | Donut | Legend: `gender`; value: [Total Revenue] |
| Revenue by age group | Column chart | Axis: `age_group`; value: [Total Revenue] |
| Filters | Slicers | `month_name`, `gender`, `product_category` |

| Check | Expected value |
|---|---|
| Total revenue | 456,000 |
| Transactions | 1,000 |
| Average order value | 456.00 |
| Units sold | 2,514 |
| Revenue by category | Electronics 156,905, Clothing 155,580, Beauty 143,515 |
| Revenue by gender | Female 232,840, Male 223,160 |
| Best month | May (53,150) |

### Page 3. Procurement

*Answers:* Which suppliers and items do we spend most on, and how much is lost to cancelled orders?

*Text box on the page:* Spend leaves out cancelled orders, which are 25.1% of the ordered value (Finding 11). Supplier names vary for the same supplier, so suppliers are shown by ID (Finding 4).

| Visual | Type | Fields |
|---|---|---|
| Spend, ordered value, cancelled share, orders | Cards | [Spend (excl. cancelled)], [Ordered Value (all orders)], [Cancelled Cost Share], [Purchase Orders] |
| Spend by supplier | Bar chart | Axis: `supplier_id`; value: [Spend (excl. cancelled)] |
| Orders by status | Donut | Legend: `po_status`; value: [Purchase Orders] |
| Spend by month | Column chart | Axis: `order_month`; value: [Spend (excl. cancelled)] |
| Top items | Table | `item_name`, [Spend (excl. cancelled)], sorted descending, top 10 |

| Check | Expected value |
|---|---|
| Ordered value, all orders | 982,390,348.71 |
| Spend excluding cancelled | 735,447,294.22 |
| Cancelled orders | 330 (25.1% of the ordered value) |
| Purchase orders | 1,300 |
| Orders by status | Delivered 334, Ordered 333, Cancelled 330, Partially Delivered 303 |
| Largest supplier by spend | SUP004 (92,742,537.20) |

### Page 4. Receivables

*Answers:* How much do customers owe, how is it paid, and how late?

*Text box on the page:* Documents are from 2011 to 2016. The delay figures are as given in the source and are not reliable: 30.5% of the documents have dates that are out of order (Finding 9).

| Visual | Type | Fields |
|---|---|---|
| Amount, documents, delay rate, consistent dates | Cards | [Receivable Amount], [Receivable Documents], [Delay Rate], [Consistent Dates Share] |
| Documents by lateness | Column chart | Axis: `overdue_bucket`; value: [Receivable Documents] |
| Amount by payment method | Bar chart | Axis: `payment_method_description`; value: [Receivable Amount] |
| Amount by region | Bar chart | Axis: `region`, top 10; value: [Receivable Amount] |
| Documents by month | Line chart | Axis: `doc_month`; value: [Receivable Documents] |
| Filter | Slicer | `dates_consistent` (lets the reader look at only the consistent documents) |

| Check | Expected value |
|---|---|
| Receivable amount | 816,262,430 |
| Documents | 45,839 |
| Delay rate | 65.7% |
| Documents with consistent dates | 69.5% |
| Documents by lateness | On time or early 21,540, 1-30 days late 23,477, 31-90 days late 686, 91-180 days late 120, Over 180 days late 16 |
| Largest payment method | Direct Debits 2: 408,301,396 (50.0% of the amount) |

### Page 5. Inventory and warehouse

*Answers:* What is in demand, and where is stock at risk?

*Text box on the page:* Demand has 12 months and no year. Warehouse figures are a snapshot with restocks in 2024.

| Visual | Type | Fields |
|---|---|---|
| Demand, items below reorder point, fulfilment, turnover, stock value | Cards | [Units Demanded], [Items Below Reorder Point], [Avg Fulfilment Rate], [Avg Turnover Ratio], [Stock Value] |
| Demand by month | Column chart | Axis: `month_name` sorted by `month_number`; value: [Units Demanded] |
| Demand by category | Bar chart | Axis: `category`; value: [Units Demanded] |
| Stockouts by zone | Column chart | Axis: `zone`; value: [Stockouts Last Month] |
| Items below the reorder point | Stacked bar | Axis: `category`; legend: `zone`; value: [Items Below Reorder Point] |
| Stock against reorder point | Table | `item_id`, `category`, `stock_level`, `reorder_point`, `days_of_stock`, filtered to `below_reorder_point` = 1 |

| Check | Expected value |
|---|---|
| Units demanded, all months | 16,961,896 |
| Peak month | March (1,421,239) |
| Lowest month | August (1,403,721) |
| Demand by category | Grocery 14,328,734, Apparel 1,404,956, Electronics 624,622, Toys 306,774, Home & Kitchen 296,810 |
| Items below the reorder point | 237 of 3,204 (7.4%) |
| Average fulfilment rate | 85.0% |
| Average turnover ratio | 8.1 |
| Stockouts last month by zone | D 3,812, A 3,682, B 3,626, C 3,626 |
| Stock value | 89,566,189.04 |

### Page 6. Manufacturing and assets

*Answers:* Which machines and operations cause problems, and what is the state of the equipment?

*Text box on the page:* Manufacturing covers one week in March 2023, so there is no long-term trend. Failed jobs have no actual start date (Finding 6).

| Visual | Type | Fields |
|---|---|---|
| Jobs, completed rate, failed rate, low-efficiency share | Cards | [Jobs], [Completed Job Rate], [Failed Job Rate], [Low Efficiency Share] |
| Jobs by machine and status | Stacked column | Axis: `machine_id`; legend: `job_status`; value: [Jobs] |
| Failed rate by machine | Bar chart | Axis: `machine_id`; value: [Failed Job Rate] |
| Average energy by operation | Bar chart | Axis: `operation_type`; value: [Avg Energy per Job] |
| Efficiency bands | Donut | Legend: `optimization_category`; value: [Jobs] |
| Assets: state by type | Stacked column | Axis: `asset_type`; legend: `operational_state`; value: count of `asset_id` |
| Maintenance cost by location | Bar chart | Axis: `location`; value: [Maintenance Cost] |
| Planned disposal | Donut | Legend: `disposal_decision`; value: count of `asset_id` |
| Cards | Cards | [Obsolete Asset Share], [Avg Condition Score] |

| Check | Expected value |
|---|---|
| Jobs by status | Completed 673, Delayed 198, Failed 129 |
| Failed rate / completed rate | 12.9% / 67.3% |
| Highest and lowest failed rate by machine | M04 17.6%, M02 10.0% |
| Average energy per job by operation | Drilling 8.86, Additive 8.55, Grinding 8.49, Lathe 8.48, Milling 8.25 |
| Jobs in the Low Efficiency band | 65.0% |
| Assets | 1,245 |
| Obsolete assets | 67.6% |
| Average condition score | 0.50 |
| Planned disposal | Recycle 493, Discard 269, Sell 269, Retain 214 |
| Maintenance cost, total | 1,354,770.44 |

### Page 7. Customers and employees

*Answers:* Who are our customers and how are they spread?

*Text box on the page:* 42 customers have a registration date in the future (Finding 10). Customer IDs do not match Sales or Receivables (Finding 1).

| Visual | Type | Fields |
|---|---|---|
| Customers, active share, credit limit | Cards | [Customers], [Active Customer Share], [Credit Limit Total] |
| Customers by state | Bar chart | Axis: `state`; value: [Customers] |
| Customers by type | Donut | Legend: `customer_type`; value: [Customers] |
| Registrations by year | Column chart | Axis: `registration_year`; value: [Customers] |
| Employees | Cards | count of `employee_number`, [Avg Salary] |
| Salary by age group | Column chart | Axis: `age_group`; value: average of `salary` |

| Check | Expected value |
|---|---|
| Customers | 1,500 |
| Active customers | 92.9% |
| Credit limit, total | 777,900,627.40 |
| Largest state | Tamil Nadu (379 customers) |
| Customers by type | Wholesale 411, Retail 378, Individual 362, Corporate 349 |
| Employees / average salary | 35 / 43,446 |

### Page 8. Finance (as given)

*Answers:* What do the finance records show, and what must a reader be careful about?

*Text box on the page:* The finance measures are shown as given. They do not follow the usual accounting formulas (Finding 12), so do not subtract one from another. Dates run to September 2027, and about 347 of the 1,000 transactions are dated after today.

| Visual | Type | Fields |
|---|---|---|
| Revenue, expenditure, transaction amount (as given) | Cards | [Finance Revenue (as given)], [Finance Expenditure (as given)], [Finance Amount (as given)] |
| Transactions by account type | Column chart | Axis: `account_type`; value: count of `transaction_id` |
| Amount by month | Line chart | Axis: `transaction_month`; value: [Finance Amount (as given)] |

| Check | Expected value |
|---|---|
| Transactions | 1,000 |
| Revenue, as given | 2,610,989 |
| Expenditure, as given | 2,026,188 |
| Transaction amount, as given | 2,535,701 |
| Transactions by account type | Expense 257, Asset 255, Liability 250, Revenue 238 |

### Page 9. Data trust

*Answers:* Can we rely on these numbers, and what is known to be wrong?

*Text box on the page:* Known issues are problems in the source data that we documented and did not change.

| Visual | Type | Fields |
|---|---|---|
| Check results | Cards | [Checks Passed], [Known Issues], [Unexpected] |
| All 32 checks | Table | `vw_dash_data_checks`: `check_id`, `check_name`, `finding`, `expected`, `violations`, `status`; colour `status` |
| Raw to warehouse | Table | `layer_reconciliation.csv`: `dataset`, `raw_rows`, `cleaned_rows`, `loaded_rows`, `status` |

| Check | Expected value |
|---|---|
| Checks | 21 PASS, 11 KNOWN ISSUE, 0 UNEXPECTED |
| Datasets reconciled from raw file to warehouse | 9 PASS, 1 EXPLAINED (Warehouse: 3,204 duplicate rows removed), 0 DIFFERENT |

---

## 5. Measures

Create these in Power BI Desktop with *Modeling > New measure*. The table names are the CSV file names.

```
-- Sales
Total Revenue = SUM ( vw_dash_sales[total_amount] )
Sales Transactions = COUNTROWS ( vw_dash_sales )
Avg Order Value = DIVIDE ( [Total Revenue], [Sales Transactions] )
Units Sold = SUM ( vw_dash_sales[quantity] )

-- Procurement
Spend (excl. cancelled) = SUM ( vw_dash_procurement[spend_excl_cancelled] )
Ordered Value (all orders) = SUM ( vw_dash_procurement[total_cost] )
Purchase Orders = COUNTROWS ( vw_dash_procurement )
Cancelled Cost Share = DIVIDE ( CALCULATE ( SUM ( vw_dash_procurement[total_cost] ), vw_dash_procurement[is_cancelled] = 1 ), [Ordered Value (all orders)] )

-- Receivables
Receivable Amount = SUM ( vw_dash_receivables[amount] )
Receivable Documents = COUNTROWS ( vw_dash_receivables )
Delay Rate = DIVIDE ( CALCULATE ( COUNTROWS ( vw_dash_receivables ), vw_dash_receivables[delayflag] = 1 ), [Receivable Documents] )
Consistent Dates Share = DIVIDE ( CALCULATE ( COUNTROWS ( vw_dash_receivables ), vw_dash_receivables[dates_consistent] = 1 ), [Receivable Documents] )

-- Inventory and warehouse
Units Demanded = SUM ( vw_dash_inventory_demand[units_demanded] )
Items Below Reorder Point = CALCULATE ( COUNTROWS ( vw_dash_warehouse ), vw_dash_warehouse[below_reorder_point] = 1 )
Avg Fulfilment Rate = AVERAGE ( vw_dash_warehouse[order_fulfillment_rate] )
Avg Turnover Ratio = AVERAGE ( vw_dash_warehouse[turnover_ratio] )
Stock Value = SUM ( vw_dash_warehouse[stock_value] )
Stockouts Last Month = SUM ( vw_dash_warehouse[stockout_count_last_month] )

-- Manufacturing and assets
Jobs = COUNTROWS ( vw_dash_manufacturing )
Failed Job Rate = DIVIDE ( SUM ( vw_dash_manufacturing[is_failed] ), [Jobs] )
Completed Job Rate = DIVIDE ( SUM ( vw_dash_manufacturing[is_completed] ), [Jobs] )
Avg Energy per Job = AVERAGE ( vw_dash_manufacturing[energy_consumption] )
Low Efficiency Share = DIVIDE ( CALCULATE ( [Jobs], vw_dash_manufacturing[optimization_category] = "Low Efficiency" ), [Jobs] )
Obsolete Asset Share = DIVIDE ( CALCULATE ( COUNTROWS ( vw_dash_assets ), vw_dash_assets[operational_state] = "Obsolete" ), COUNTROWS ( vw_dash_assets ) )
Maintenance Cost = SUM ( vw_dash_assets[maintenance_cost_last_year] )
Avg Condition Score = AVERAGE ( vw_dash_assets[condition_score] )

-- Customers and employees
Customers = COUNTROWS ( vw_dash_customers )
Active Customer Share = DIVIDE ( CALCULATE ( [Customers], vw_dash_customers[customer_status] = "Active" ), [Customers] )
Credit Limit Total = SUM ( vw_dash_customers[credit_limit] )
Avg Salary = AVERAGE ( vw_dash_employees[salary] )

-- Finance (as given)
Finance Revenue (as given) = SUM ( vw_dash_finance[revenue] )
Finance Expenditure (as given) = SUM ( vw_dash_finance[expenditure] )
Finance Amount (as given) = SUM ( vw_dash_finance[transaction_amount] )

-- Data trust
Checks Passed = CALCULATE ( COUNTROWS ( vw_dash_data_checks ), vw_dash_data_checks[status] = "PASS" )
Known Issues = CALCULATE ( COUNTROWS ( vw_dash_data_checks ), vw_dash_data_checks[status] = "KNOWN ISSUE" )
Unexpected = CALCULATE ( COUNTROWS ( vw_dash_data_checks ), vw_dash_data_checks[status] = "UNEXPECTED" )
```

For the month axes, sort `month_name` by `month` (Sales) or by `month_number` (Inventory): select the column, then *Column tools > Sort by column*.

---

## 6. What the data shows

These are the useful things the warehouse lets us say, each one visible on a page above. The datasets are synthetic, so they describe the data we have and not a real company.

1. **Sales are spread fairly evenly over three categories.** Electronics (156,905) and Clothing (155,580) lead, Beauty is last (143,515). Female customers account for 51.1% of revenue. May is the best month (53,150).
2. **A quarter of what was ordered was cancelled.** 330 of 1,300 purchase orders are cancelled and carry 25.1% of the ordered value (246,943,054). Leaving them out, spend is 735,447,294, and the largest supplier is SUP004.
3. **Two thirds of receivables are flagged as delayed, but the delay data is weak.** 65.7% of the documents are flagged, yet 30.5% have dates that contradict each other, so lateness is indicative only. Half of the amount (50.0%) is paid by Direct Debits 2.
4. **Demand is dominated by Grocery and hardly changes through the year.** Grocery is 84.5% of the units demanded. The busiest month (March) is only 1.2% above the quietest (August), so there is almost no seasonality to plan for.
5. **237 warehouse items (7.4%) are below their reorder point.** Zone D had the most stockouts last month (3,812). The average order fulfilment rate is 85.0%.
6. **Two machines fail more often than the rest.** M04 fails 17.6% of its jobs and M03 fails 15.6%, against 10.0% to 10.9% for the other three. 12.9% of all jobs failed, and 65.0% are in the Low Efficiency band.
7. **Most of the asset base is obsolete.** 67.6% of the 1,245 assets are Obsolete, and Recycle is the most common planned disposal (493 assets, 39.6%).
8. **Customers are spread over nine states, with Tamil Nadu the largest.** Tamil Nadu has 379 customers (25.3%), the four southern states together have 49.9%, and 92.9% of customers are active.
9. **The data can be traced and checked.** All ten datasets reconcile from raw file to warehouse (one after removing duplicates), and the 32 data quality checks give 21 PASS and 11 known issues, with none unexpected.

---

## 7. Limits

- The modules cannot be combined on one time axis or by customer, item or supplier, because the periods and IDs do not match (Findings 1 to 3). Each page therefore stands alone.
- The receivables delay figures and the finance measures are shown as given and are not reliable (Findings 9 and 12).
- The check values were calculated from the views on the loaded warehouse. The one value that changes with the date is the number of future-dated records (customer registrations and finance transactions).

---

## 8. Files

| File | What it is |
|---|---|
| `sql/11_dashboard_views.sql` | Creates the 11 views |
| `dashboards/export_dashboard_data.sh` | Exports the views to CSV |
| `dashboards/data/*.csv` | The exported data (about 7.6 MB) |
| `dashboards/Dashboard_Design.md` | This document |

---

## 9. How to build it

**Power BI Desktop (Windows).**

A step-by-step version, with checks and fixes for common problems, is in `dashboards/Power_BI_Build_Guide.md`. A script that adds all 36 measures at once is in `dashboards/measures_dax_query.txt`, and a colour theme is in `dashboards/UC15_theme.json`.

1. Copy the repository folder to the Windows computer (or clone it from GitHub). The CSV files are in `dashboards/data/`.
2. *Get data > Text/CSV*, load all 12 files (the 11 views and `layer_reconciliation.csv`). Check that dates have the type Date and the flags are whole numbers.
3. Create the measures from Section 5.
4. Build the nine pages from Section 4, one at a time, and compare each card with its check value. If time is short, build pages 1 to 6 and page 9 first.
5. Save the file as `dashboards/UC15_ERP_Dashboard.pbix` and export each page with *File > Export > Export to PDF* for the report and the presentation.

**Power BI in the browser (work or school account).** As far as I know, a CSV uploaded in the browser becomes its own dataset, and a report can use only one dataset. You would build one report per area with the same measures and pin the visuals to one dashboard. This route is more limited than Desktop.

**If neither route is possible.** The same views can feed a self-contained web page that opens in any browser. It would not be Power BI, so check with your professor whether that is acceptable.
