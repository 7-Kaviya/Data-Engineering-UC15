# Data Quality Report

**Project:** UC15 - Enterprise Resource Planning Data Platform (ERPDP)
**Sprint:** 2 (Data Profiling and Data Warehouse)
**Repository:** Data-Engineering-UC15

---

## 1. Summary

This report lists the data quality problems we found in the ERP datasets while doing profiling, cleaning, validation and Star Schema design for Sprint 2. All the numbers below were checked directly on the files in the repository (row counts, column names, ID overlaps) using Python and pandas. The scripts we used are in the `python/` folder.

The main thing we found is that the 10 source datasets do not behave like data from one ERP system. The customer, item and supplier IDs do not match across modules, and the dates of the modules do not line up with each other. Because of this we could not build shared dimensions like one DimCustomer or one DimProduct, so the warehouse is made of 10 standalone modules which share only the date dimension. Validation also showed some real errors in the data, mainly in the Accounts Receivable dates (Finding 9).

---

## 2. Datasets and approach

We worked with 10 datasets in different formats (CSV, JSON, XML, Excel). All of them were cleaned and then loaded into PostgreSQL.

| No. | Dataset | Source format | Rows | Cleaned file |
|---|---|---|---|---|
| 1 | Sales | CSV | 1,000 | sales_data_cleaned.csv |
| 2 | Customer Master | JSON | 1,500 | customer_master_cleaned.csv |
| 3 | Asset | XML | 1,245 | asset_data_cleaned.csv |
| 4 | Account (Accounts Receivable) | Excel | 45,839 | account_data_cleaned.csv |
| 5 | Procurement | CSV | 1,300 | procurement_all_cleaned.csv |
| 6 | Employee | Excel | 35 | employee_data_cleaned.csv |
| 7 | Finance | CSV | 1,000 | finance_data_cleaned.csv |
| 8 | Inventory | JSON | 1,000 | inventory_data_cleaned.csv |
| 9 | Manufacturing | XML | 1,000 | manufacturing_data_cleaned.csv |
| 10 | Warehouse | CSV | 3,204 | warehouse_data_cleaned.csv |

The steps were:

- Profiling with two Jupyter notebooks (one for each group of five datasets).
- Cleaning with `ERP_Data_Cleaning_separate1.py` and `ERP_Data_Cleaning_separate2.py`. These standardise column names, trim text, convert dates and numbers, and remove blank and duplicate rows.
- Validation with `ERP_Data_Validation_Separate.py` (Employee, Finance, Inventory, Manufacturing, Warehouse) and `ERP_Data_Validation_Group2.py` (Sales, Customer, Asset, Account, Procurement). A third script, `ERP_Data_Validation_Combined.py`, works on the combined file explained in Finding 8.

Whenever we found a problem, we checked it again on the actual data before writing it here. For example, to compare two ID columns we took the full set of values from each file and counted how many were common, instead of looking at a few sample rows.

---

## 3. Findings

### Finding 1 - Customer IDs are different in Sales, Customer Master and Account

| Dataset | Customer ID looks like |
|---|---|
| Sales | CUST001 |
| Customer Master | 5001 |
| Account | 5039221069 |

We compared the raw files in `datasets/`, the staged files in `bronze/staging/` and the cleaned files. The IDs were the same in all three places, so the cleaning scripts did not cause this. It is already like this in the source data.

Because of this, a sale or an invoice cannot be linked to a customer in the customer master, and we cannot say which customer made a purchase. We also tried the idea that the IDs follow the row order (CUST001 is the first customer, 5001 is the first row, and so on). We could not confirm it, because the datasets have no common column such as name, age or city to compare, and the row counts are different (1,000 and 1,500). So we did not use it.

In the warehouse, DimCustomerMaster is built only from the customer master file. The `customer_id` in FactSales and the `cust_num` in FactAccountsReceivable are kept as normal columns and not as foreign keys.

### Finding 2 - Item IDs are different across Inventory, Warehouse, Procurement and Sales

| Dataset | Item ID looks like |
|---|---|
| Inventory | ITM_001 |
| Warehouse | ITM10000 |
| Procurement | P109 |
| Sales | no item ID, only a category (Beauty, Clothing, Electronics) |

Inventory and Warehouse look like they should describe the same items, but when we compared the two sets of IDs (1,000 in Inventory and 3,204 in Warehouse) there was no common ID at all.

So one shared product dimension was not possible. Inventory has its own item dimension (DimItemInventory), Warehouse has its own (DimWarehouseItem), and Procurement and Sales keep the item or category as plain text in the fact table.

### Finding 3 - The dates of the modules are in different years

| Dataset | Date range |
|---|---|
| Account | 2011 to 2016 |
| Sales | 2023 to 2024 |
| Procurement | 2023 to 2024 |
| Warehouse (last restock) | 2024 |
| Manufacturing | 18 to 25 March 2023 only |
| Finance | 2025 to 2027 |

In one real company all these modules would have records in the same years. Here Account ends in 2016 and Finance starts in 2025, so there is almost no overlap. This is one of the reasons we think the datasets come from different sources.

The effect is that comparing modules for the same period (for example sales against finance by month) is not meaningful for most pairs. The date dimension DimDate covers 2011 to 2027 so that every fact table can still use it.

### Finding 4 - Supplier names change for the same supplier ID

In `procurement_all_cleaned.csv` all 10 suppliers have more than one `supplier_name` across their purchase orders. We checked this by counting the distinct names for each `supplier_id`. Since all 10 are affected, it is not a few typing mistakes.

A dimension table needs one stable name for each supplier, so DimSupplier only has `supplier_id`, and the `supplier_name` is stored in FactProcurement for each order.

The same thing happens with `account_name` and `cost_center` in the finance part of the combined file (Finding 8). The final warehouse does not use those columns, so no change was needed there.

### Finding 5 - Finance cannot be linked to Sales or Procurement

The Finance dataset (`finance_data_cleaned.csv`) has only a transaction ID, a date, an account type and the amounts. It has no reference to a sale or a purchase order.

Also, the Finance `transaction_id` and the Sales `transaction_id` both run from 1 to 1,000, but they are different things. If someone joins them, the result will be wrong, so the two columns should never be joined.

In the combined file, which does have a `reference_id` column in its finance part, only 240 of 1,500 sales (16%) and 249 of 1,300 purchase orders (19%) have a matching reference. The reconciliation between sales, procurement and finance asked for in the project brief is therefore not possible with this data, except for a small part of it.

### Finding 6 - 129 manufacturing jobs have no actual start and end

In `manufacturing_data_cleaned.csv`, 129 of the 1,000 jobs have no `actual_start` and no `actual_end`, while the scheduled times are present for all of them. The validation script reported 258 missing values, which is 129 rows with 2 columns each.

About 13% of the jobs therefore cannot be used to compare actual and scheduled time. We did not delete or fill these rows. In FactManufacturing the column `actual_start_date_key` is allowed to be NULL for them.

### Finding 7 - Employee has no ID column

`employee_data_cleaned.csv` (35 rows) has only first name and last name, there is no employee ID. This does not affect anything else because no other dataset refers to an employee. DimEmployee uses a generated key.

### Finding 8 - The combined dataset is not the same as the official datasets

The repository also has a combined file, `silver/cleansing/erp_cleaned_data.csv` (6,600 rows, 53 columns). It contains five sections: Sales (1,500 rows), Customer (1,200), Asset (1,100), Procurement (1,300) and Finance (1,500).

At first it looked useful for the Star Schema, because inside this file the Sales and Customer sections share customer IDs (all 859 sales customers are present in the customer section) and the Sales and Procurement sections share product IDs (15 out of 15). The 10 official datasets do not have this.

Then we checked where the file comes from. The cleaning script reads `C:/Users/USER/Downloads/erp_combined_data.csv`, and the Pentaho transformation behind it reads the Sales, Asset, Customer and Accounts files from the same Downloads folder (`Sales_Transactions (1).csv`, `Asset_Management.xml`, `Customer_Master.json`, `Accounts.xls`), not from the `datasets/` folder. We compared them and they are different data. For example `datasets/Sales_data.csv` has 1,000 rows and 10 columns with no `product_id`, but the Sales section of the combined file has 1,500 rows and 12 columns including `product_id`, `sales_channel`, `payment_method` and `sales_region`. Only the Procurement section matched the official file (all 1,300 purchase order IDs are the same).

We asked the team member who prepared the combined file. She said the original datasets could not be combined because some columns had the same name but different data types, so she used a separate set of synthetic datasets that combine properly.

So the combined file is a different, synthetic dataset. We did not load it into the warehouse, because the warehouse should represent the actual 10 datasets. We use it only for cross-module validation (see Section 5). The file and its notebook stay in the repository.

### Finding 9 - Dates in the Account (Accounts Receivable) data are not logical

| Check | Rows affected | Share of 45,839 |
|---|---|---|
| `net_due_date` is earlier than `doc_date` | 11,269 | 24.6% |
| `clearing_date` is earlier than `doc_date` | 12,104 | 26.4% |

For example, document 91225055958 has `doc_date` 2015-12-05 but `clearing_date` 2015-10-09, which means the payment was cleared before the document was created.

We first thought this could be a day/month mix-up while reading the dates. To check, we read the columns again with a fixed `YYYY-MM-DD` format. All values are in that format with no parsing failures, and the counts stayed the same. So the problem is in the data itself. `posting_date` is equal to `doc_date` in every row.

Because of this, `days_overdue_delay` and `delayflag` are not reliable for these rows, and the overdue/aging queries in `sql/04_enterprise_reporting_queries.sql` should be read with this in mind. We kept the rows in the warehouse as they are, because correcting the dates would mean making up values. The problem is documented here instead.

### Finding 10 - Smaller issues in Customer and Sales

- 47 customers have a `registration_date` later than the day we ran the check. The dates in `customer_master_cleaned.csv` go from 2018-01-01 to 2026-12-26. This number depends on the date of the run and will become smaller with time.
- Sales transaction 522 has no `daily_percent_change`. It is the first record (2023-01-01), so there is no previous day to calculate the change from. This is expected.

---

## 4. Effect on the Star Schema

Findings 1, 2 and 8 mean that we could not create dimensions shared between modules. The Star Schema therefore has 15 tables: 10 modules which are standalone, plus DimDate which is shared by the fact tables and DimMonth which is used for the monthly demand in Inventory. The tables are created by `sql/01_create_star_schema.sql` and loaded by `python/03_load_star_schema.py`. After loading, the row counts in PostgreSQL match the cleaned files.

---

## 5. Validation results

**Individual datasets - Group 1** (`ERP_Data_Validation_Separate.py`): 32 checks on Employee, Finance, Inventory, Manufacturing and Warehouse (missing values, duplicate rows, negative values, invalid IDs and ages). All passed except one.

| Dataset | Check | Errors | Status |
|---|---|---|---|
| Manufacturing | Missing values | 258 | FAIL (Finding 6) |

**Individual datasets - Group 2** (`ERP_Data_Validation_Group2.py`): 49 checks on Sales, Customer, Asset, Account and Procurement. These include duplicate rows and keys, missing values, negative amounts, total = quantity x price, date parsing and date order. 45 passed and 4 failed.

| Dataset | Check | Errors | Status |
|---|---|---|---|
| Sales | Missing values | 1 | FAIL (Finding 10) |
| Customer | Future registration_date | 47 | FAIL (Finding 10) |
| Account | net_due_date before doc_date | 11,269 | FAIL (Finding 9) |
| Account | clearing_date before doc_date | 12,104 | FAIL (Finding 9) |

**Combined file** (`ERP_Data_Validation_Combined.py`): this script works only on the combined synthetic file, so it does not describe the data in the warehouse. It is used for the cross-module checks that need linked IDs.

| Validation | Errors | Status |
|---|---|---|
| Duplicate master records | 0 | PASS |
| Missing sales finance references | 1,260 | FAIL |
| Missing PO finance references | 1,051 | FAIL |
| Negative inventory records | 0 | PASS |
| Sales financial errors | 0 | PASS |
| PO financial errors | 0 | PASS |
| Master data errors | 1,352 | FAIL |

The master data errors are mostly the supplier name problem (Finding 4), plus some asset maintenance dates which are in the future.

The output files in `silver/validation/` belong to the scripts as follows:

| File | Produced by |
|---|---|
| separate_validation_summary.csv | ERP_Data_Validation_Separate.py |
| group2_validation_summary.csv | ERP_Data_Validation_Group2.py |
| validation_summary.csv, duplicate_records.csv, financial_validation.csv, inventory_validation.csv, master_data_validation.csv, missing_transactions.csv | ERP_Data_Validation_Combined.py |

---

## 6. Recommendations and limitations

1. Do not try to force a link between the different customer, item and supplier IDs. There is nothing in the data that can confirm such a link, so any mapping would be a guess.
2. Treat the Accounts Receivable aging results as indicative only, until the reason for the inconsistent `doc_date`, `net_due_date` and `clearing_date` values (Finding 9) is clarified.
3. Keep `erp_cleaned_data.csv` out of the warehouse. If the team later decides to use it, the Star Schema must be changed, since its keys do not belong to the official datasets.
4. The `sql/` folder still has 11 older files with a `.sql` extension that actually contain CSV data and not SQL. They should be removed or renamed.
5. For Sprint 3 (source-to-target mapping and lineage) the findings in Section 3 can be reused directly.

---

## 7. Conclusion

The 10 datasets are clean enough to be loaded into PostgreSQL and all of them are validated, but they cannot be integrated as one ERP system: the keys do not match and the periods do not overlap. We handled this by building standalone modules and documenting each limitation, and not by inventing links or values. The remaining open points are the Accounts Receivable dates and the 129 manufacturing jobs without actual times, both of which would need to be clarified with the data provider.
