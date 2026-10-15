# Data Profiling Report

## 1. Purpose and approach

This report describes what the 10 raw ERP datasets contain before any cleaning. Profiling was the first step of Sprint 2: we needed to know the size, structure and quality of every dataset before deciding how to clean it and how to design the warehouse.

The profiling was done in Python with pandas. Two Jupyter notebooks in the `python/` folder do the standard checks, one for each group of five datasets:

| Notebook | Datasets |
|---|---|
| `Data_profiling_each_dataset1.ipynb` | Finance, Employee, Inventory, Manufacturing, Warehouse |
| `Data_profiling_each_dataset2.ipynb` | Sales, Customer Master, Asset, Account, Procurement |

For every dataset the notebooks show the first rows, the shape, the column names and data types, missing values, duplicate rows, `info()` and `describe()`, the numeric and categorical columns, and value counts. The second notebook also has charts (record counts per dataset and the distribution of categories, asset condition, customer type and amounts).

The figures in this report come from running the same checks on the raw files in `datasets/`, with a few extra ones that the notebooks do not do: whether the key column is unique, the date range of each dataset, and whether the calculated totals are correct. A separate notebook, `Data_Profiling_Combined_data.ipynb`, profiles the combined synthetic file. That file is not part of the warehouse, so it is not covered here (see Finding 8 in the Data Quality Report).

---

## 2. Overview of the 10 datasets

| No. | Dataset | Format | Rows | Columns | Numeric / other columns | Missing cells | Duplicate rows |
|---|---|---|---|---|---|---|---|
| 1 | Sales | CSV | 1,000 | 10 | 6 / 4 | 1 | 0 |
| 2 | Customer Master | JSON | 1,500 | 8 | 2 / 6 | 0 | 0 |
| 3 | Asset | XML | 1,245 | 11 | 6 / 5 | 0 | 0 |
| 4 | Account (Accounts Receivable) | Excel | 45,839 | 29 | 14 / 15 | 0 | 0 |
| 5 | Procurement | CSV | 1,300 | 11 | 3 / 8 | 0 | 0 |
| 6 | Employee | Excel | 35 | 9 | 6 / 3 | 0 | 0 |
| 7 | Finance | CSV | 1,000 | 18 | 15 / 3 | 0 | 0 |
| 8 | Inventory | JSON | 1,000 | 18 | 15 / 3 | 0 | 0 |
| 9 | Manufacturing | XML | 1,000 | 13 | 4 / 9 | 258 | 0 |
| 10 | Warehouse | CSV | 6,408 | 23 | 18 / 5 | 0 | 3,204 |

"Other" columns are text columns, and they include dates that are stored as text.

Only three datasets have a quality problem in their raw form: one missing value in Sales, 258 empty cells in Manufacturing, and 3,204 duplicate rows in Warehouse. Everything else is complete, with no duplicates. The rest of the report goes through each dataset.

---

## 3. Profile of each dataset

### 3.1 Sales

1,000 transactions from 1 January 2023 to 31 December 2023. `Transaction ID` is unique. The raw dates are written as DD-MM-YYYY, which is different from most of the other datasets, so the cleaning script converts them.

- Age runs from 18 to 64 (mean 41.4), quantity from 1 to 4, and the gender split is 510 female and 490 male.
- There are three product categories: Clothing 351, Electronics 342 and Beauty 307.
- `Price per Unit` has only five different values (25, 30, 50, 300 and 500), and `Total Amount` (25 to 2,000, mean 456.00) equals quantity times price in every row.
- Every one of the 1,000 transactions has a different customer ID, so no customer buys twice.
- The only missing value is `Daily Percent Change` for the first record, which has no previous day to compare with.

### 3.2 Customer Master

1,500 customers, with a unique `customer_id`. The columns `contact` and `address` hold JSON text (email and phone, city, state and country), which has to be split into separate columns later.

- Customer types are Wholesale 411, Retail 378, Individual 362 and Corporate 349.
- 1,393 customers are Active and 107 are Inactive.
- Credit limit runs from 25,944.90 to 998,980 (mean 518,600).
- Registration dates run from 2018-01-01 to 2026-12-26, so some of them are in the future.

### 3.3 Asset

1,245 assets, with a unique `asset_id`, installed between 2000 and 2023, in four locations.

- Asset types are Sensor 424, Transformer 421 and Meter 400.
- Condition score goes from 0.004 to 0.995 (mean 0.50), failure count from 0 to 9 (mean 2.9), and maintenance cost last year from 201 to 1,999 (mean 1,088).
- The operational state is very uneven: Obsolete 842 (68%), Degraded 381 and Active only 22 (under 2%).
- Disposal decisions are Recycle 493, Discard 269, Sell 269 and Retain 214.

### 3.4 Account (Accounts Receivable)

The largest dataset: 45,839 documents with 29 columns. It is a receivables process (document number, payment term, due, posting and clearing dates), and it is separate from the Sales dataset.

- Only 69 different customers appear in the 45,839 documents, so each customer has many documents.
- `Amount` goes from 2 to 5,709,354 with a mean of 17,807. The distribution is very skewed: 99% of the amounts are below 212,706, and 1,644 documents are above 100,000.
- There are 30 regions. The biggest are AA125 (10,219 documents), AA113 (9,712) and AA121 (8,054).
- The most used payment methods are Direct Debits 2 (24,010) and Direct Debits 1 (18,981).
- `Days_Overdue_Delay` goes from -117 to 1,257, and 65.7% of the documents have the delay flag set.

### 3.5 Procurement

1,300 purchase orders, with a unique `purchase_order_id`, placed between 1 January 2023 and 30 December 2024, with 10 suppliers and 15 items.

- Quantity is 10 to 150 (mean 79), unit cost 499.51 to 42,412.90 (mean 9,537), and the total cost equals quantity times unit cost in every row.
- The order status is spread almost equally: Delivered 334, Ordered 333, Cancelled 330 and Partially Delivered 303.
- Cancelled orders still carry a full cost: 246.9 million of the total 982.4 million (25.1%).

### 3.6 Employee

Only 35 rows. There is no employee ID column, only first name and last name.

- 20 men and 15 women, with ages from 25 to 52 (mean 37.6).
- Salary goes from 24,100 to 80,000 (mean 43,446). The other columns are expenditure, savings and their percentages.

### 3.7 Finance

1,000 transactions with a unique `Transaction ID` and 18 columns, mostly numeric (revenue, expenditure, net income, cash flow, profit margin and similar).

- Account types are balanced: Expense 257, Asset 255, Liability 250 and Revenue 238.
- Transaction amount goes from 106 to 4,998 (mean 2,536).
- The dates run from 2025-01-01 to 2027-09-27, which is much later than the other datasets.

### 3.8 Inventory

1,000 items, with a unique `Item_ID`, and one column of demand for each month (January to December).

- Categories are Grocery 402, Apparel 216, Electronics 193, Home & Kitchen 100 and Toys 89.
- Price per unit goes from 2 to 1,000 (mean 57), and the yearly demand of one item from 581 to 59,967 (mean 16,962).

### 3.9 Manufacturing

1,000 production jobs on 5 machines, with a unique `Job_ID`. All the scheduled start and end times are filled in.

- Operations are Lathe 212, Grinding 208, Milling 201, Additive 190 and Drilling 189.
- Job status is Completed 673, Delayed 198 and Failed 129.
- Processing time goes from 20 to 120 (mean 71.4) and energy consumption from 2.0 to 15.0 (mean 8.5).
- 129 jobs have no actual start and no actual end. These are exactly the 129 Failed jobs: every Failed job is empty and no other job is. So the empty cells are expected, because a failed job has no actual run time.
- The jobs are scheduled in a very short period (18 to 25 March 2023).

### 3.10 Warehouse

6,408 rows in the raw file but only 3,204 different items. Every item appears exactly twice, and the two copies are identical, so the file contains each record two times. The cleaning script removes the extra copy (6,408 rows become 3,204).

- Five categories (Pharma, Automotive, Electronics, Groceries and Apparel) and four zones (A to D), each with a similar share of rows. The cleaning script renames "Groceries" to "Grocery" so that it matches the Inventory spelling.
- Stock level goes from 20 to 499 (mean 263).
- The last restock dates are all in 2024.

---

## 4. Observations that apply to several datasets

- **Keys:** the main key is unique in every dataset that has one (Sales, Customer, Asset, Procurement, Finance, Inventory, Manufacturing, Account by its document number, and Warehouse after cleaning). Employee has no key at all. The customer number in Account repeats, as it should: 69 customers have 45,839 documents.
- **ID formats:** customers are `CUST001` in Sales, `5001` in Customer Master and a ten-digit number in Account. Items are `ITM_001` in Inventory, `ITM10000` in Warehouse and `P109` in Procurement. They do not match, which is the reason for the standalone design of the warehouse (Findings 1 and 2 of the Data Quality Report).
- **Category names:** Sales uses Clothing, Electronics and Beauty. Inventory uses Grocery, Apparel, Electronics, Home & Kitchen and Toys. Warehouse uses Pharma, Automotive, Electronics, Groceries and Apparel. Only Electronics appears in all three. In the raw files "Grocery" and "Groceries" are spelled differently, and the cleaning script fixes that by renaming the Warehouse value to "Grocery". After cleaning, Inventory and Warehouse share three categories (Grocery, Apparel and Electronics), while Pharma and Automotive exist only in Warehouse and Home & Kitchen and Toys only in Inventory.
- **Dates:** the modules are in different periods (Account 2011 to 2016, Sales and Procurement 2023 to 2024, Warehouse 2024, Finance 2025 to 2027). Date formats also differ, for example DD-MM-YYYY in Sales.
- **Synthetic look:** several patterns suggest that the data was generated and not taken from one company: only five prices in Sales, one purchase per customer, an equal split of procurement statuses, and 68% of the assets being obsolete. This is the reason we avoid drawing business conclusions from the figures and use them only to test the pipeline.

---

## 5. Raw data compared with cleaned data

The cleaning scripts standardise the column names, trim text, convert dates and numbers, and remove blank rows and exact duplicates. The cleaning logs (`five_datasets_cleaning_log_group1.csv` and `group2.csv`) show how many rows each dataset has before and after:

| Dataset | Raw rows | Cleaned rows | Removed |
|---|---|---|---|
| Sales | 1,000 | 1,000 | 0 |
| Customer Master | 1,500 | 1,500 | 0 |
| Asset | 1,245 | 1,245 | 0 |
| Account | 45,839 | 45,839 | 0 |
| Procurement | 1,300 | 1,300 | 0 |
| Employee | 35 | 35 | 0 |
| Finance | 1,000 | 1,000 | 0 |
| Inventory | 1,000 | 1,000 | 0 |
| Manufacturing | 1,000 | 1,000 | 0 |
| Warehouse | 6,408 | 3,204 | 3,204 duplicates |

Only Warehouse loses rows. The one missing value in Sales and the 258 empty cells in Manufacturing are kept as they are, because they are not errors that can be fixed.

---

## 6. Conclusion

Profiling shows that the 10 datasets are in good shape structurally: they are complete, their keys are unique, and the calculated totals are correct. The real problems are few. Warehouse had every row twice, and this was fixed in cleaning. The remaining differences are between the datasets and not inside them: the IDs, category names and time periods do not match, and this is documented in the Data Quality Report. Profiling also pointed to two things that the later validation confirmed: the Account dates are not always in a logical order, and the cancelled purchase orders (a quarter of the procurement cost) have to be filtered when reporting spend.
