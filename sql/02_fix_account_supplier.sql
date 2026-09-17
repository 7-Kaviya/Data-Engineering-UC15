-- ============================================================
-- UC15 ERP Data Platform — Schema fix
-- Corrects DimAccount and DimSupplier after discovering account_name,
-- cost_center, and supplier_name are NOT stable per account_id/supplier_id
-- (every one of the 10 accounts and all 10 suppliers show multiple
-- different names/cost-centers across transactions — confirmed finding).
--
-- Run this AFTER 01_create_star_schema.sql and BEFORE loading any data.
-- Safe to run even if FactFinance / FactProcurement already exist empty.
-- ============================================================

-- Drop the fact tables first (they reference the dimensions we're fixing)
DROP TABLE IF EXISTS FactFinance;
DROP TABLE IF EXISTS FactProcurement;
DROP TABLE IF EXISTS DimAccount;
DROP TABLE IF EXISTS DimSupplier;


-- Recreate DimAccount — thin, only the stable natural key
CREATE TABLE DimAccount (
    account_key      SERIAL PRIMARY KEY,
    account_id       VARCHAR(20) NOT NULL UNIQUE
    -- account_name and cost_center removed: confirmed NOT stable per
    -- account_id (all 10 accounts show multiple different names/cost
    -- centers across transactions). Moved to FactFinance as degenerate
    -- attributes below.
);

-- Recreate DimSupplier — thin, only the stable natural key
CREATE TABLE DimSupplier (
    supplier_key     SERIAL PRIMARY KEY,
    supplier_id      VARCHAR(20) NOT NULL UNIQUE
    -- supplier_name removed: confirmed NOT stable per supplier_id
    -- (all 10 suppliers show multiple different names across POs).
    -- Moved to FactProcurement as a degenerate attribute below.
);

-- Recreate FactProcurement with supplier_name added as a degenerate attribute
CREATE TABLE FactProcurement (
    procurement_key            SERIAL PRIMARY KEY,
    purchase_order_id          VARCHAR(20) NOT NULL UNIQUE,
    order_date_key             INT NOT NULL REFERENCES DimDate(date_key),
    expected_delivery_date_key INT REFERENCES DimDate(date_key),
    supplier_key                INT NOT NULL REFERENCES DimSupplier(supplier_key),
    supplier_name                VARCHAR(150),   -- degenerate: varies per PO, see note above
    product_key                   INT NOT NULL REFERENCES DimProduct(product_key),
    po_status                      VARCHAR(30),
    quantity                        INT,
    unit_cost                        NUMERIC(12,2),
    total_cost                        NUMERIC(14,2)
);

-- Recreate FactFinance with account_name and cost_center added as degenerate attributes
CREATE TABLE FactFinance (
    finance_key        SERIAL PRIMARY KEY,
    voucher_id         VARCHAR(20) NOT NULL UNIQUE,
    date_key            INT NOT NULL REFERENCES DimDate(date_key),
    account_key          INT NOT NULL REFERENCES DimAccount(account_key),
    account_name           VARCHAR(150),   -- degenerate: varies per transaction, see note above
    transaction_type         VARCHAR(50),
    reference_id               VARCHAR(20),   -- still not a foreign key, see 01_create_star_schema.sql note
    posting_status               VARCHAR(30),
    cost_center                    VARCHAR(50),   -- degenerate: varies per transaction, see note above
    fiscal_year                      SMALLINT,
    debit_amount                       NUMERIC(14,2),
    credit_amount                        NUMERIC(14,2)
);
