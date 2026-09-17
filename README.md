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
- Data profiling (individual datasets and combined dataset) using Python
- Data cleaning and standardization of all 10 ERP datasets
- Separate validation (Employee, Finance, Inventory, Manufacturing, Warehouse)
- Combined/cross-module validation (duplicate master records, missing finance references, inventory balance, financial mismatches, master-data consistency)
- Data Quality Report findings (ID fragmentation across modules, non-overlapping date ranges, missing manufacturing execution data)
- Star Schema design — in progress
- PostgreSQL Data Warehouse — in progress
- SQL scripts (DDL/DML) — in progress
