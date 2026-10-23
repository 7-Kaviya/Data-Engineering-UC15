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
- Tableau (dashboards)
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
- Data profiling
- Data cleaning and standardisation
- Data validation
- Data Profiling Report
- Data Quality Report
- Star Schema design
- PostgreSQL Data Warehouse
- Pentaho transformations
- SQL scripts and reporting queries

### Sprint 3 – Governance, Lineage & Analytics

Activities:
- Pentaho job to load the warehouse with an audit log
- End-to-end Pentaho job from raw files to a reconciled warehouse
- Source-to-target mapping
- Metadata repository and business glossary
- Data lineage document and diagram
- Enterprise-wide reconciliation and Validation Report
- Data quality checks
- Real-time ingestion from a REST API
- Dashboard views, data exports, dashboard design and Tableau dashboards

## Repository Structure

| Folder | Contents |
|---|---|
| `datasets/` | Raw source files |
| `bronze/` | Sprint 1 staging copies and ingestion documents |
| `silver/` | Cleaned files (`silver/cleansing/`) and validation results (`silver/validation/`) |
| `gold/` | Empty on purpose: the Gold layer is the PostgreSQL database `uc15_dw` |
| `pentaho/` | 26 transformations (11 ingestion, 15 load) and 2 jobs |
| `python/` | Cleaning, validation, profiling, loading and reconciliation scripts |
| `sql/` | Numbered SQL scripts: schema, reporting, reconciliation, audit, metadata, checks, dashboard views |
| `metadata/` | Source-to-target mapping, metadata repository, business glossary |
| `lineage/` | Data lineage document and diagram |
| `docs/` | Project documents, Data Profiling Report, Data Quality Report, Validation Report |
| `dashboards/` | Tableau dashboards, dashboard design, export script and the exported data |
| `realtime_rest_demo/` | Real-time ingestion from a REST API |
| `tests/` | Empty: the checks are in `sql/10_data_quality_checks.sql` and `python/ERP_Layer_Reconciliation.py` |

## How to Run

1. Install PostgreSQL, Pentaho Data Integration 11 and Python 3 with these libraries: `pip3 install pandas numpy lxml xlrd openpyxl psycopg2-binary`.
2. Create the database `uc15_dw` and run these scripts in this order: `sql/01_create_star_schema.sql`, `sql/08_etl_audit_setup.sql`, `sql/09_metadata_comments.sql`, `sql/10_data_quality_checks.sql`, `sql/11_dashboard_views.sql`.
3. Create the file `~/.kettle/kettle.properties` with one line, `UC15_DB_PASSWORD=` followed by your PostgreSQL password. Do not commit this file. Restart Spoon after creating it.
4. Start Spoon from a Terminal window, open `pentaho/jobs/ETL_End_To_End.kjb` and run it. It cleans and validates the raw files, loads the warehouse, reconciles it and checks the data quality.
5. Check the result: `SELECT * FROM vw_data_quality_checks;` should show only PASS and KNOWN ISSUE.
