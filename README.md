# UC15 – Enterprise Resource Planning Data Platform

## Project Overview

This project implements an Enterprise Resource Planning Data Platform (ERPDP) for ABC Global Enterprises Ltd.

The platform is designed to integrate enterprise data from multiple ERP modules, process and standardize the data, store datasets in PostgreSQL, and support enterprise operations, business analytics, financial reporting, and executive dashboards.

## ERP Modules

- Finance
- Procurement
- Sales
- Inventory Management
- Manufacturing
- Human Resources
- Warehouse Management
- Asset Management
- Accounts Payable & Receivable
- Vendor Master Data
- Customer Master Data

## Technology Stack

- Pentaho Data Integration (Spoon)
- PostgreSQL
- Python / Pandas
- Git & GitHub
- Power BI
- Markdown / MS Word

## Sprint Roadmap

### Sprint 0 – Project Initiation & Architecture

Activities:
- ERP business process study
- Stakeholder identification
- BRD preparation
- ERP source identification
- Project scope
- High-level architecture
- GitHub repository
- Product Backlog
- Project Charter

### Sprint 1 – Data Discovery & Ingestion

Activities:
- ERP source analysis
- Data Dictionary
- CSV ingestion
- Excel ingestion
- JSON ingestion
- XML ingestion
- SQL ingestion
- PostgreSQL staging
- Logging
- Exception handling

### Sprint 2 – Data Profiling & DB / Data Warehouse

Activities:
- Data profiling with Python (two notebooks, one for each group of five datasets)
- Data cleaning and standardisation of all 10 ERP datasets
- Validation of all 10 datasets (`ERP_Data_Validation_Separate.py` and `ERP_Data_Validation_Group2.py`)
- Data Quality Report (`docs/Data_Quality_Report.md`)
- Star Schema design: 15 tables (8 dimensions, 7 facts), `DimDate` is the only dimension shared between modules
- PostgreSQL Data Warehouse `uc15_dw`, created by `sql/01_create_star_schema.sql`
- Warehouse load with Pentaho (one transformation per table) and an equivalent Python loader
- Reporting queries (`sql/04_enterprise_reporting_queries.sql`) and a reconciliation check (`sql/05_reconciliation_checks.sql`)

Note on the datasets: the warehouse is built only from the 10 cleaned files in `silver/cleansing/cleaned_datasets/`. The combined file `erp_cleaned_data.csv` is a separate synthetic dataset and is not loaded (see Finding 8 in the Data Quality Report).

## How to rebuild the warehouse

**1. Database.** Create an empty PostgreSQL database named `uc15_dw`, then run `sql/01_create_star_schema.sql` in it.

**2. Pentaho setup (one time).** The transformations were built and tested with Pentaho Data Integration 11.0 (Spoon). Each transformation has a connection called `UC15 Warehouse` (localhost, port 5432, database `uc15_dw`, user `postgres`). The password is not stored in the files. Add this line to `~/.kettle/kettle.properties` (on Windows `C:\Users\<you>\.kettle\kettle.properties`) and restart Spoon:

```
UC15_DB_PASSWORD=your_postgres_password
```

If your user or port is different, edit the connection in Spoon.

**3. Reference files.** `silver/cleansing/reference_data/DimDate.csv` and `DimMonth.csv` are already in the repository. They can be regenerated with `python/generate_reference_data.py`.

**4. Run the transformations from `pentaho/transformations/`, in this order** (dimensions first, because the facts look up their keys):

| Step | Transformations |
|---|---|
| 1. Dimensions | Load DimMonth, Load DimDate, Load DimEmployee, Load DimAsset, Load DimSupplier, Load DimCustomerMaster, Load DimItemInventory, Load DimWarehouseItem |
| 2. Facts | Load FactSales, Load FactFinance, Load FactManufacturing, Load FactAccountsReceivable, Load FactProcurement, Load FactWarehouseSnapshot, Load FactInventoryDemand |

To reload everything from scratch, run `sql/00_reset_warehouse.sql` first. PostgreSQL does not let Pentaho truncate a dimension that a fact table points to, so the reset script empties all 15 tables together.

**5. Check the result.** Run `sql/05_reconciliation_checks.sql`. It compares the row count and a numeric total of every table with figures calculated from the cleaned CSV files, and all 15 rows should show PASS.

**Alternative:** `python/03_load_star_schema.py` loads the same 15 tables without Pentaho (edit the connection details at the top of the script).

The files named `... data ingestion.ktr` in `pentaho/transformations/` belong to Sprint 1. They load the raw files into a separate `Staging` database and are not part of this warehouse load.

Still to do in Sprint 3: a Pentaho job that runs the transformations in order, source-to-target mapping, lineage, glossary and the Power BI dashboards.
