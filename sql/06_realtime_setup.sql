-- ============================================================
-- UC15 ERP Data Platform - Real-time ingestion (small extension)
--
-- Adds two tables next to the 15 warehouse tables. The 15 tables are
-- not touched, so the reconciliation check (05) still passes.
--
--   sales_event_queue    landing table: every incoming event is stored here first
--   FactSalesRealtime    sales loaded one event at a time, as they arrive
--   vw_sales_batch_and_realtime   batch + real-time sales in one view
--
-- Safe to run more than once.
-- ============================================================

CREATE TABLE IF NOT EXISTS sales_event_queue (
    id            BIGSERIAL PRIMARY KEY,
    payload       JSONB NOT NULL,                       -- the raw event
    received_at   TIMESTAMP NOT NULL DEFAULT localtimestamp,
    processed_at  TIMESTAMP,
    status        VARCHAR(10) NOT NULL DEFAULT 'NEW',   -- NEW, LOADED or REJECTED
    error         TEXT                                   -- reason, when REJECTED
);

CREATE INDEX IF NOT EXISTS idx_queue_new ON sales_event_queue (id) WHERE status = 'NEW';

CREATE TABLE IF NOT EXISTS FactSalesRealtime (
    rt_sales_key      SERIAL PRIMARY KEY,
    event_id          VARCHAR(40) NOT NULL UNIQUE,      -- makes the load safe to repeat
    date_key          INT NOT NULL REFERENCES DimDate(date_key),
    customer_id       VARCHAR(20),
    gender            VARCHAR(20),
    age               SMALLINT,
    product_category  VARCHAR(50),
    quantity          INT,
    price_per_unit    NUMERIC(12,2),
    total_amount      NUMERIC(14,2),
    event_time        TIMESTAMP NOT NULL,               -- when the sale happened
    ingested_at       TIMESTAMP NOT NULL                -- when the warehouse stored it
);

CREATE OR REPLACE VIEW vw_sales_batch_and_realtime AS
SELECT 'batch'::text AS source, transaction_id::text AS sale_id, date_key,
       product_category, quantity, price_per_unit, total_amount
FROM factsales
UNION ALL
SELECT 'realtime'::text, event_id::text, date_key,
       product_category, quantity, price_per_unit, total_amount
FROM factsalesrealtime;
