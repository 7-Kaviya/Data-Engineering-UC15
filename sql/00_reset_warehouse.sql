-- ============================================================
-- Empties all 15 warehouse tables and restarts the surrogate key counters.
-- Run this before a full reload so the Pentaho transformations
-- (or 03_load_star_schema.py) start from a clean state.
-- CASCADE is needed because fact tables reference the dimensions.
-- ============================================================
TRUNCATE TABLE
    FactSales, FactAccountsReceivable, FactProcurement, FactFinance,
    FactInventoryDemand, FactWarehouseSnapshot, FactManufacturing,
    DimEmployee, DimAsset, DimCustomerMaster, DimSupplier,
    DimItemInventory, DimWarehouseItem, DimMonth, DimDate
RESTART IDENTITY CASCADE;
