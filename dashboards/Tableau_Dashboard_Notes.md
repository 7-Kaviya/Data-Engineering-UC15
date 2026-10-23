# Tableau Dashboards

**File:** `dashboards/Dashboards.twbx`


## 1. What it is

`Dashboards.twbx` is a Tableau packaged workbook, made with Tableau 2025.1.2 on Windows. It has **2 dashboards and 10 sheets**, built on the 12 files exported from the dashboard views (`dashboards/data/`). The data is packaged inside the file, so it opens without a database.

The Business Requirement Document named Power BI as the reporting tool. The dashboards were built in Tableau instead. The same views, CSV files and design also support a Power BI build, and the guide for it is kept in `dashboards/Power_BI_Build_Guide.md`.

## 2. How to open it

1. Download `Dashboards.twbx` from GitHub (open the file, then *Download raw file*), or run `git pull origin main`.
2. Install **Tableau Reader** (free, Windows and Mac, view-only) and open the file. Alternatives: **Tableau Public** (free, can also edit) or Tableau Desktop (a student licence may be available).
3. Use a current version of the program: the file was made in 2025.1.2, and an older version cannot open a newer file.

The workbook holds copies of the CSV data. After the warehouse is reloaded, run `sh dashboards/export_dashboard_data.sh` and refresh the data in Tableau Desktop.

## 3. What each sheet shows

| Sheet | Dashboard | Shows | Chart | Data (view) | Check against the warehouse |
|---|---|---|---|---|---|
| 1 | 1 | Total amount of each product category | Bar | `vw_dash_sales` | Matches: Beauty 143,515, Clothing 155,580, Electronics 156,905 |
| 2 | 1 | Daily demand of each warehouse category | Area | `vw_dash_warehouse` | Plausible; sums the daily demand per category |
| 3 | 1 | Days overdue by region and city | Bar | `vw_dash_receivables` | Uses the delay column that is not reliable (Finding 9) |
| 4 | 1 | Total cost of each item | Bar | `vw_dash_procurement` | **Includes cancelled orders** (see Section 5) |
| 5 | 1 | Revenue of each account type | Pie | `vw_dash_finance` | Finance figures are as given and do not add up (Finding 12) |
| 6 | 2 | Machine availability of each operation type | Treemap | `vw_dash_manufacturing` | Plausible |
| 7 | 2 | Unit demand of each month and category | Heat table | `vw_dash_inventory_demand` | Matches: January Apparel 117,009, Electronics 51,897, Grocery 1,199,093 |
| 8 | 2 | Salary by age group | Pie | `vw_dash_employees` | Plausible |
| 9 | 2 | Credit limit of each city | Map | `vw_dash_customers` | Matches: Pune 60,618,437, Hyderabad 70,749,656, Coimbatore 72,107,813, Jaipur 76,809,409 |
| 10 | 2 | Condition score of each asset type and state | Bar | `vw_dash_assets` | **Adds up the scores** (see Section 5) |

The workbook also holds `vw_dash_data_checks` and `layer_reconciliation` as data sources, but no sheet uses them yet.

## 4. How it relates to the design

`dashboards/Dashboard_Design.md` describes nine pages with measures and numbers to check. The Tableau workbook covers part of it: sales, procurement, receivables, inventory, warehouse, manufacturing, assets, customers, employees and finance each have a chart. It does not yet have the executive overview cards, the data-trust page, or the caveat texts of the design.

## 5. Known limitations and suggested improvements

These make the dashboards agree with the rest of the project. Each is a few minutes in Tableau Desktop.

| # | Sheet | Problem | Fix in Tableau | Effect |
|---|---|---|---|---|
| 1 | 4 | Cost includes cancelled orders, which are 25.1% of the ordered value (Finding 11). The SQL reports leave them out. | Drag `is_cancelled` to *Filters* and keep 0, or use `spend_excl_cancelled` instead of `total_cost`. | Laptop falls from 238,793,042 to 169,832,297; the total falls from 982,390,349 to 735,447,294 |
| 2 | 10 | The condition scores are added up, so the group with more assets looks better. | Right-click the pill, choose *Measure > Average*. | Active 0.86, Degraded 0.61, Obsolete 0.44 (the sums are 18.9, 233.0 and 374.1) |
| 3 | 3 | Days overdue is not reliable (Finding 9), and the chart has very many labels. | Add a subtitle "As given in the source; not reliable (Finding 9)", or filter to the top regions. | Honest reading |
| 4 | 5 | Finance revenue is as given (Finding 12), and dates run to 2027. | Add a subtitle "As given in the source (Finding 12)". | Honest reading |
| 5 | All | The sheets are called "Sheet 1" to "Sheet 10", and the dashboards "Dashboard 1" and "Dashboard 2". | Rename them, for example "Sales by category" and "Sales, supply and finance". | Clearer for a reader |
| 6 | Both dashboards | No text boxes, so the caveats are not on the page. | *Dashboard > Objects > Text*, with the wording of the design document. | Caveats visible |
| 7 | New | The data-trust data sources are not used. | New sheet from `vw_dash_data_checks`: count of `status`, and a table of the checks. | Shows 21 PASS, 11 KNOWN ISSUE, 0 UNEXPECTED |
| 8 | Both dashboards | No exported images in the repository. | *Dashboard > Export Image*, or *File > Print to PDF*; save in `dashboards/screenshots/`. | Anyone can see the result without Tableau |
