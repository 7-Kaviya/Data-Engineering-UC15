-- ============================================================
-- UC15 ERP Data Platform — Gold Layer Star Schema (FINAL)
-- PostgreSQL DDL
--
-- All 10 modules are fully standalone, sourced ONLY from the 10
-- separately cleaned files in silver/cleansing/cleaned_datasets/,
-- which trace back to the official datasets/ folder.
--
-- erp_cleaned_data.csv / erp_combined_data.csv are DELIBERATELY
-- excluded: their source was traced to
-- C:/Users/USER/Downloads/erp_combined_data.csv, not datasets/,
-- and its Sales/Asset/Customer sections were confirmed (different
-- row counts, different columns, different ID formats) to NOT be
-- the same data as the official source files. Its provenance is
-- unverified, so it is not used anywhere in this warehouse.
--
-- Only DimDate is shared across facts; every other dimension is
-- local to its own fact table, because no natural key was found
-- to genuinely conform across modules in the official source data
-- (confirmed: Customer, Product/Item, and Supplier IDs all differ
-- format-to-format with zero overlap between modules).
-- ============================================================


-- ============================================================
-- SHARED DIMENSION
-- ============================================================

CREATE TABLE DimDate (
    date_key        INT PRIMARY KEY,        -- format YYYYMMDD
    full_date       DATE NOT NULL,
    year            SMALLINT NOT NULL,
    quarter         SMALLINT NOT NULL,
    month           SMALLINT NOT NULL,
    month_name      VARCHAR(15) NOT NULL,
    day             SMALLINT NOT NULL,
    day_of_week     SMALLINT NOT NULL,       -- 1=Monday .. 7=Sunday
    day_name        VARCHAR(15) NOT NULL,
    is_weekend      BOOLEAN NOT NULL,
    week_of_year    SMALLINT NOT NULL
);

CREATE TABLE DimMonth (
    month_key     SMALLINT PRIMARY KEY,   -- 1-12, no year (seasonal pattern only)
    month_name    VARCHAR(15) NOT NULL
);


-- ============================================================
-- SALES  (source: sales_data_cleaned.csv, 1,000 rows)
-- ============================================================

CREATE TABLE FactSales (
    sales_key              SERIAL PRIMARY KEY,
    transaction_id          VARCHAR(20) NOT NULL UNIQUE,
    date_key                 INT NOT NULL REFERENCES DimDate(date_key),
    customer_id               VARCHAR(20),   -- degenerate: does not match any other module
    gender                     VARCHAR(20),
    age                          SMALLINT,
    product_category               VARCHAR(50),   -- degenerate: no product master exists
    quantity                        INT,
    price_per_unit                    NUMERIC(12,2),
    total_amount                        NUMERIC(14,2),
    daily_percent_change                  NUMERIC(10,6)
);


-- ============================================================
-- CUSTOMER MASTER  (source: customer_master_cleaned.csv, 1,500 rows)
-- Standalone dimension: NOT referenced by FactSales.customer_id
-- (confirmed: different ID formats, zero overlap)
-- ============================================================

CREATE TABLE DimCustomerMaster (
    customer_key         SERIAL PRIMARY KEY,
    customer_id           VARCHAR(20) NOT NULL UNIQUE,
    customer_name           VARCHAR(150),
    email                     VARCHAR(150),   -- parsed from source JSON `contact` field
    phone                       VARCHAR(30),   -- parsed from source JSON `contact` field
    city                          VARCHAR(100),   -- parsed from source JSON `address` field
    state                           VARCHAR(100),   -- parsed from source JSON `address` field
    country                           VARCHAR(100),   -- parsed from source JSON `address` field
    customer_type                       VARCHAR(50),
    registration_date                     DATE,
    credit_limit                            NUMERIC(14,2),
    customer_status                           VARCHAR(30)
);


-- ============================================================
-- ASSET  (source: asset_data_cleaned.csv, 1,245 rows)
-- Standalone dimension: no repeating transactions in this data
-- ============================================================

CREATE TABLE DimAsset (
    asset_key                    SERIAL PRIMARY KEY,
    asset_id                       VARCHAR(20) NOT NULL UNIQUE,
    location                         VARCHAR(100),
    install_year                       SMALLINT,
    last_maintenance_year                SMALLINT,
    usage_hours_per_month                  NUMERIC(10,2),
    failure_count                            SMALLINT,
    condition_score                            NUMERIC(6,4),
    maintenance_cost_last_year                   NUMERIC(12,2),
    asset_type                                     VARCHAR(50),
    operational_state                                VARCHAR(30),
    disposal_decision                                  VARCHAR(30)
);


-- ============================================================
-- ACCOUNTS RECEIVABLE  (source: account_data_cleaned.csv, 45,839 rows)
-- Its own business process, separate from Sales
-- ============================================================

CREATE TABLE FactAccountsReceivable (
    ar_key                       SERIAL PRIMARY KEY,
    document_no                    VARCHAR(20) NOT NULL UNIQUE,
    doc_date_key                     INT NOT NULL REFERENCES DimDate(date_key),
    net_due_date_key                   INT REFERENCES DimDate(date_key),
    clearing_date_key                    INT REFERENCES DimDate(date_key),
    cust_num                               VARCHAR(20),   -- degenerate: does not match DimCustomerMaster
    payment_method_description               VARCHAR(100),
    region                                     VARCHAR(50),
    city                                         VARCHAR(100),
    payment_term                                   VARCHAR(30),
    delayflag                                        VARCHAR(10),
    amount                                             NUMERIC(14,2),
    days_overdue_delay                                   INT,
    no_of_orders_by_customer                               INT
);


-- ============================================================
-- PROCUREMENT  (source: procurement_all_cleaned.csv, 1,300 rows)
-- ============================================================

CREATE TABLE DimSupplier (
    supplier_key     SERIAL PRIMARY KEY,
    supplier_id      VARCHAR(20) NOT NULL UNIQUE
    -- supplier_name deliberately excluded: confirmed NOT stable per
    -- supplier_id (all 10 suppliers show multiple different names
    -- across purchase orders). Kept on the fact table instead.
);

CREATE TABLE FactProcurement (
    procurement_key              SERIAL PRIMARY KEY,
    purchase_order_id              VARCHAR(20) NOT NULL UNIQUE,
    order_date_key                   INT NOT NULL REFERENCES DimDate(date_key),
    expected_delivery_date_key         INT REFERENCES DimDate(date_key),
    supplier_key                         INT NOT NULL REFERENCES DimSupplier(supplier_key),
    supplier_name                          VARCHAR(150),   -- degenerate, varies per PO, see note above
    item_id                                  VARCHAR(20),   -- degenerate: no shared product master
    item_name                                  VARCHAR(150),
    po_status                                    VARCHAR(30),
    quantity                                       INT,
    unit_cost                                        NUMERIC(12,2),
    total_cost                                         NUMERIC(14,2)
);


-- ============================================================
-- FINANCE  (source: finance_data_cleaned.csv, 1,000 rows)
-- ============================================================

CREATE TABLE FactFinance (
    finance_key            SERIAL PRIMARY KEY,
    transaction_id           VARCHAR(20) NOT NULL UNIQUE,
    date_key                   INT NOT NULL REFERENCES DimDate(date_key),
    account_type                 VARCHAR(50),
    transaction_amount             NUMERIC(14,2),
    cash_flow                        NUMERIC(14,2),
    net_income                         NUMERIC(14,2),
    revenue                              NUMERIC(14,2),
    expenditure                            NUMERIC(14,2),
    profit_margin                            NUMERIC(8,4),
    gross_profit                               NUMERIC(14,2),
    transaction_volume                           NUMERIC(14,2),
    accuracy_score                                 NUMERIC(6,4)
);


-- ============================================================
-- INVENTORY  (source: inventory_data_cleaned.csv, 1,000 items)
-- ============================================================

CREATE TABLE DimItemInventory (
    item_key          SERIAL PRIMARY KEY,
    item_id             VARCHAR(20) NOT NULL UNIQUE,
    item_name             VARCHAR(150),
    category                VARCHAR(50),
    price_per_unit            NUMERIC(12,2)
);

CREATE TABLE FactInventoryDemand (
    item_key          INT NOT NULL REFERENCES DimItemInventory(item_key),
    month_key           SMALLINT NOT NULL REFERENCES DimMonth(month_key),
    units_demanded         INT,
    PRIMARY KEY (item_key, month_key)
);


-- ============================================================
-- WAREHOUSE  (source: warehouse_data_cleaned.csv, 3,204 rows)
-- item_id here does NOT match DimItemInventory.item_id
-- (confirmed: different format, zero overlap) - kept separate
-- ============================================================

CREATE TABLE DimWarehouseItem (
    warehouse_item_key    SERIAL PRIMARY KEY,
    item_id                 VARCHAR(20) NOT NULL UNIQUE,
    category                  VARCHAR(50),
    storage_location_id        VARCHAR(30),
    zone                          VARCHAR(30)
);

CREATE TABLE FactWarehouseSnapshot (
    snapshot_key              SERIAL PRIMARY KEY,
    date_key                    INT NOT NULL REFERENCES DimDate(date_key),  -- last_restock_date
    warehouse_item_key            INT NOT NULL REFERENCES DimWarehouseItem(warehouse_item_key),
    stock_level                     INT,
    reorder_point                     INT,
    lead_time_days                      SMALLINT,
    daily_demand                          NUMERIC(10,2),
    picking_time_seconds                    NUMERIC(10,2),
    handling_cost_per_unit                    NUMERIC(10,2),
    unit_price                                  NUMERIC(12,2),
    holding_cost_per_unit_day                     NUMERIC(10,4),
    stockout_count_last_month                       SMALLINT,
    order_fulfillment_rate                            NUMERIC(6,4),
    total_orders_last_month                             SMALLINT,
    turnover_ratio                                        NUMERIC(10,4),
    forecasted_demand_next_7d                               NUMERIC(10,2),
    kpi_score                                                 NUMERIC(6,4)
);


-- ============================================================
-- MANUFACTURING  (source: manufacturing_data_cleaned.csv, 1,000 jobs)
-- ============================================================

CREATE TABLE FactManufacturing (
    job_key                     SERIAL PRIMARY KEY,
    job_id                        VARCHAR(20) NOT NULL UNIQUE,
    scheduled_start_date_key        INT NOT NULL REFERENCES DimDate(date_key),
    actual_start_date_key             INT REFERENCES DimDate(date_key),  -- NULLABLE:
        -- 129 of 1,000 jobs have no actual_start/actual_end recorded
    machine_id                          VARCHAR(20),   -- degenerate: only 5 distinct
        -- values, no further descriptive data, not worth a full dimension
    operation_type                        VARCHAR(50),
    job_status                              VARCHAR(30),
    optimization_category                     VARCHAR(50),
    material_used                               NUMERIC(10,2),
    processing_time                               NUMERIC(10,2),
    energy_consumption                              NUMERIC(10,2),
    machine_availability                              NUMERIC(6,2)
);


-- ============================================================
-- EMPLOYEE  (source: employee_data_cleaned.csv, 35 rows)
-- ============================================================

CREATE TABLE DimEmployee (
    employee_key             SERIAL PRIMARY KEY,   -- generated: source has
        -- NO natural key (no employee_id column at all)
    first_name                 VARCHAR(100),
    last_name                    VARCHAR(100),
    gender                         VARCHAR(20),
    age                               SMALLINT,
    salary                              NUMERIC(12,2),
    expenditure                           NUMERIC(12,2),
    savings                                 NUMERIC(12,2),
    expenditure_percentage                    NUMERIC(6,4),
    savings_percentage                          NUMERIC(6,4)
    -- Standalone: no fact table references DimEmployee, nothing else
    -- in the source data carries an employee ID.
);


-- ============================================================
-- INDEXES on natural keys used for lookups during ETL loads
-- ============================================================

CREATE INDEX idx_customer_natural   ON DimCustomerMaster(customer_id);
CREATE INDEX idx_asset_natural      ON DimAsset(asset_id);
CREATE INDEX idx_supplier_natural   ON DimSupplier(supplier_id);
CREATE INDEX idx_item_inv_natural   ON DimItemInventory(item_id);
CREATE INDEX idx_wh_item_natural    ON DimWarehouseItem(item_id);
