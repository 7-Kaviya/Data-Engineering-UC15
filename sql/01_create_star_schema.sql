-- ============================================================
-- UC15 ERP Data Platform — Gold Layer Star Schema
-- PostgreSQL DDL
--
-- Two zones, sharing only DimDate:
--   LINKED ZONE      : Sales, Customer, Asset, Procurement, Finance
--                       (sourced from silver/cleansing/erp_cleaned_data.csv —
--                        verified conformed keys for Customer and Product)
--   STANDALONE ZONE  : Inventory, Warehouse, Manufacturing, Employee
--                       (sourced from the 10 separately cleaned files —
--                        no shared keys with each other or the linked zone)
--
-- Run this once against a fresh PostgreSQL database to create every table.
-- Run 02_load scripts afterwards to populate them.
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


-- ============================================================
-- LINKED ZONE — DIMENSIONS
-- (Sales / Customer / Asset / Procurement / Finance)
-- ============================================================

CREATE TABLE DimCustomer (
    customer_key        SERIAL PRIMARY KEY,
    customer_id         VARCHAR(20) NOT NULL UNIQUE,   -- natural key
    customer_name       VARCHAR(150),
    email               VARCHAR(150),
    phone               VARCHAR(30),
    city                VARCHAR(100),
    state               VARCHAR(100),
    country             VARCHAR(100),
    customer_type       VARCHAR(50),
    registration_date   DATE,
    credit_limit        NUMERIC(14,2),
    customer_status     VARCHAR(30)
);

CREATE TABLE DimProduct (
    product_key      SERIAL PRIMARY KEY,
    product_id       VARCHAR(20) NOT NULL UNIQUE,      -- natural key
    product_name     VARCHAR(150) NOT NULL
);

CREATE TABLE DimSupplier (
    supplier_key     SERIAL PRIMARY KEY,
    supplier_id      VARCHAR(20) NOT NULL UNIQUE,      -- natural key
    supplier_name    VARCHAR(150)
    -- NOTE: source data shows every supplier_id associated with multiple
    -- supplier_name values (confirmed data-quality finding). This column
    -- currently holds whichever name the load script picks; see the
    -- Data Quality Report for the full finding before treating this as
    -- a single canonical name.
);

CREATE TABLE DimAccount (
    account_key      SERIAL PRIMARY KEY,
    account_id       VARCHAR(20) NOT NULL UNIQUE,      -- natural key
    account_name     VARCHAR(150),
    cost_center      VARCHAR(50)
);

CREATE TABLE DimAsset (
    asset_key                SERIAL PRIMARY KEY,
    asset_id                 VARCHAR(20) NOT NULL UNIQUE,   -- natural key
    asset_name               VARCHAR(150),
    asset_type               VARCHAR(50),
    location                 VARCHAR(100),
    purchase_date            DATE,
    purchase_cost            NUMERIC(14,2),
    useful_life_years        SMALLINT,
    last_maintenance_date    DATE,
    condition_score          NUMERIC(6,4),
    asset_status              VARCHAR(30)
    -- NOTE: standalone dimension, not currently paired with a fact table —
    -- no repeating asset transactions exist in this dataset.
);


-- ============================================================
-- LINKED ZONE — FACTS
-- ============================================================

CREATE TABLE FactSales (
    sales_key            SERIAL PRIMARY KEY,
    sale_id              VARCHAR(20) NOT NULL UNIQUE,   -- degenerate dimension (original source ID)
    date_key             INT NOT NULL REFERENCES DimDate(date_key),
    customer_key         INT REFERENCES DimCustomer(customer_key),  -- NULLABLE:
        -- only 859 of 1,500 sales rows have a matching customer_id
        -- (confirmed data-quality finding); rows without a match keep
        -- customer_key NULL rather than a fabricated link.
    product_key          INT NOT NULL REFERENCES DimProduct(product_key),
    sales_channel         VARCHAR(50),
    payment_method        VARCHAR(50),
    sales_region           VARCHAR(50),
    quantity              INT,
    unit_price             NUMERIC(12,2),
    discount_percent       NUMERIC(5,2),
    total_amount           NUMERIC(14,2)
);

CREATE TABLE FactProcurement (
    procurement_key            SERIAL PRIMARY KEY,
    purchase_order_id          VARCHAR(20) NOT NULL UNIQUE,  -- degenerate dimension
    order_date_key             INT NOT NULL REFERENCES DimDate(date_key),
    expected_delivery_date_key INT REFERENCES DimDate(date_key),
    supplier_key               INT NOT NULL REFERENCES DimSupplier(supplier_key),
    product_key                INT NOT NULL REFERENCES DimProduct(product_key),
    po_status                  VARCHAR(30),
    quantity                   INT,
    unit_cost                  NUMERIC(12,2),
    total_cost                 NUMERIC(14,2)
);

CREATE TABLE FactFinance (
    finance_key       SERIAL PRIMARY KEY,
    voucher_id        VARCHAR(20) NOT NULL UNIQUE,   -- degenerate dimension
    date_key          INT NOT NULL REFERENCES DimDate(date_key),
    account_key       INT NOT NULL REFERENCES DimAccount(account_key),
    transaction_type  VARCHAR(50),
    reference_id      VARCHAR(20),   -- NOT a foreign key: only 16-19% of
        -- reference_id values actually match a sale_id/purchase_order_id
        -- (confirmed data-quality finding). Kept as a plain attribute.
    posting_status    VARCHAR(30),
    fiscal_year       SMALLINT,
    debit_amount      NUMERIC(14,2),
    credit_amount     NUMERIC(14,2)
);


-- ============================================================
-- STANDALONE ZONE — INVENTORY
-- ============================================================

CREATE TABLE DimMonth (
    month_key     SMALLINT PRIMARY KEY,   -- 1-12
    month_name    VARCHAR(15) NOT NULL
);

CREATE TABLE DimItemInventory (
    item_key          SERIAL PRIMARY KEY,
    item_id           VARCHAR(20) NOT NULL UNIQUE,   -- natural key (ITM_### format)
    item_name         VARCHAR(150),
    category          VARCHAR(50),
    price_per_unit    NUMERIC(12,2)
);

CREATE TABLE FactInventoryDemand (
    item_key          INT NOT NULL REFERENCES DimItemInventory(item_key),
    month_key         SMALLINT NOT NULL REFERENCES DimMonth(month_key),
    units_demanded    INT,
    PRIMARY KEY (item_key, month_key)
);


-- ============================================================
-- STANDALONE ZONE — WAREHOUSE
-- ============================================================

CREATE TABLE DimWarehouseItem (
    warehouse_item_key    SERIAL PRIMARY KEY,
    item_id               VARCHAR(20) NOT NULL UNIQUE,   -- natural key (ITM##### format,
        -- NOTE: does NOT match DimItemInventory.item_id — confirmed
        -- zero overlap, kept as a separate dimension deliberately.
    category               VARCHAR(50),
    storage_location_id    VARCHAR(30),
    zone                    VARCHAR(30)
);

CREATE TABLE FactWarehouseSnapshot (
    snapshot_key              SERIAL PRIMARY KEY,
    date_key                  INT NOT NULL REFERENCES DimDate(date_key),  -- last_restock_date
    warehouse_item_key        INT NOT NULL REFERENCES DimWarehouseItem(warehouse_item_key),
    stock_level                INT,
    reorder_point               INT,
    lead_time_days              SMALLINT,
    daily_demand                 NUMERIC(10,2),
    picking_time_seconds         NUMERIC(10,2),
    handling_cost_per_unit        NUMERIC(10,2),
    unit_price                     NUMERIC(12,2),
    holding_cost_per_unit_day       NUMERIC(10,4),
    stockout_count_last_month        SMALLINT,
    order_fulfillment_rate             NUMERIC(6,4),
    total_orders_last_month              SMALLINT,
    turnover_ratio                         NUMERIC(10,4),
    forecasted_demand_next_7d                NUMERIC(10,2),
    kpi_score                                  NUMERIC(6,4)
);


-- ============================================================
-- STANDALONE ZONE — MANUFACTURING
-- ============================================================

CREATE TABLE FactManufacturing (
    job_key                     SERIAL PRIMARY KEY,
    job_id                      VARCHAR(20) NOT NULL UNIQUE,   -- degenerate dimension
    scheduled_start_date_key    INT NOT NULL REFERENCES DimDate(date_key),
    actual_start_date_key       INT REFERENCES DimDate(date_key),  -- NULLABLE:
        -- 129 of 1,000 jobs have no actual_start/actual_end recorded
        -- (confirmed data-quality finding).
    machine_id                  VARCHAR(20),   -- degenerate attribute; only 5
        -- distinct machines with no further descriptive data, not worth
        -- a full dimension table
    operation_type               VARCHAR(50),
    job_status                    VARCHAR(30),
    optimization_category           VARCHAR(50),
    material_used                     NUMERIC(10,2),
    processing_time                     NUMERIC(10,2),
    energy_consumption                    NUMERIC(10,2),
    machine_availability                    NUMERIC(6,2)
);


-- ============================================================
-- STANDALONE ZONE — EMPLOYEE
-- ============================================================

CREATE TABLE DimEmployee (
    employee_key             SERIAL PRIMARY KEY,   -- generated: source data has
        -- NO natural key (no employee_id column at all, confirmed finding)
    first_name               VARCHAR(100),
    last_name                VARCHAR(100),
    gender                    VARCHAR(20),
    age                        SMALLINT,
    salary                       NUMERIC(12,2),
    expenditure                    NUMERIC(12,2),
    savings                          NUMERIC(12,2),
    expenditure_percentage             NUMERIC(6,4),
    savings_percentage                   NUMERIC(6,4)
    -- NOTE: no fact table references DimEmployee — nothing else in the
    -- source data carries an employee ID. Standalone reference table only.
);


-- ============================================================
-- INDEXES on natural keys used for lookups during ETL loads
-- (surrogate keys above already get a PK index automatically)
-- ============================================================

CREATE INDEX idx_customer_natural   ON DimCustomer(customer_id);
CREATE INDEX idx_product_natural    ON DimProduct(product_id);
CREATE INDEX idx_supplier_natural   ON DimSupplier(supplier_id);
CREATE INDEX idx_account_natural    ON DimAccount(account_id);
CREATE INDEX idx_asset_natural      ON DimAsset(asset_id);
CREATE INDEX idx_item_inv_natural   ON DimItemInventory(item_id);
CREATE INDEX idx_wh_item_natural    ON DimWarehouseItem(item_id);
