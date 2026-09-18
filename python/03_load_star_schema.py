"""
LOAD STAR SCHEMA
Reads the 10 officially-sourced cleaned datasets (silver/cleansing/cleaned_datasets/)
and loads all 15 Dimension and Fact tables in PostgreSQL.

Run this AFTER 01_create_star_schema.sql has been executed against an
empty database. Safe to re-run: it clears each table before reloading
(so re-running never creates duplicates), but does NOT recreate tables.
"""

import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values

# ----------------------------------------------------------------
# CONNECTION — edit these if your setup differs
# ----------------------------------------------------------------
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="uc15_dw",
    user="postgres",
    password="uc15pass",
)
cur = conn.cursor()
print("Connected to PostgreSQL.")


# ----------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------

def clean(val):
    """Convert pandas NaN/NaT to a real Python None for psycopg2."""
    if pd.isna(val):
        return None
    return val


def date_key(val):
    """Convert a date-like value to the YYYYMMDD integer used as DimDate's key.
    Returns None if the value is missing/unparseable."""
    if pd.isna(val):
        return None
    ts = pd.to_datetime(val, errors="coerce")
    if pd.isna(ts):
        return None
    return int(ts.strftime("%Y%m%d"))


def bulk_insert(table, columns, rows):
    """Insert many rows at once. rows is a list of tuples matching columns."""
    if not rows:
        print(f"  {table}: nothing to insert")
        return
    col_list = ", ".join(columns)
    sql = f"INSERT INTO {table} ({col_list}) VALUES %s"
    execute_values(cur, sql, rows, page_size=1000)
    conn.commit()
    print(f"  {table}: inserted {len(rows)} rows")


def get_key_map(table, key_col, natural_col):
    """After loading a dimension, fetch {natural_key: surrogate_key} for use
    when building fact tables that reference it."""
    cur.execute(f"SELECT {natural_col}, {key_col} FROM {table}")
    return dict(cur.fetchall())


def clear_table(table):
    cur.execute(f"TRUNCATE TABLE {table} CASCADE")
    conn.commit()


DATA_DIR = "../silver/cleansing/cleaned_datasets"


# ==================================================================
# 1. DimDate  (2011-01-01 to 2027-12-31, covers every date in the data)
# ==================================================================
print("\n[1/15] DimDate")
clear_table("DimDate")

dates = pd.date_range(start="2011-01-01", end="2027-12-31", freq="D")
rows = []
for d in dates:
    rows.append((
        int(d.strftime("%Y%m%d")),
        d.date(),
        d.year,
        int((d.month - 1) // 3 + 1),
        d.month,
        d.strftime("%B"),
        d.day,
        d.dayofweek + 1,
        d.strftime("%A"),
        d.dayofweek >= 5,
        int(d.isocalendar()[1]),
    ))

bulk_insert(
    "DimDate",
    ["date_key", "full_date", "year", "quarter", "month", "month_name",
     "day", "day_of_week", "day_name", "is_weekend", "week_of_year"],
    rows,
)


# ==================================================================
# 2. DimMonth  (1-12, no year — used for the Inventory seasonal demand fact)
# ==================================================================
print("\n[2/15] DimMonth")
clear_table("DimMonth")

month_names = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
rows = [(i + 1, name) for i, name in enumerate(month_names)]
bulk_insert("DimMonth", ["month_key", "month_name"], rows)


# ==================================================================
# 3. FactSales  (source: sales_data_cleaned.csv)
# ==================================================================
print("\n[3/15] FactSales")
clear_table("FactSales")

sales = pd.read_csv(f"{DATA_DIR}/sales_data_cleaned.csv")
rows = []
for _, r in sales.iterrows():
    rows.append((
        clean(r.get("transaction_id")),
        date_key(r.get("date")),
        clean(r.get("customer_id")),
        clean(r.get("gender")),
        clean(r.get("age")),
        clean(r.get("product_category")),
        clean(r.get("quantity")),
        clean(r.get("price_per_unit")),
        clean(r.get("total_amount")),
        clean(r.get("daily_percent_change")),
    ))

bulk_insert(
    "FactSales",
    ["transaction_id", "date_key", "customer_id", "gender", "age",
     "product_category", "quantity", "price_per_unit", "total_amount",
     "daily_percent_change"],
    rows,
)


# ==================================================================
# 4. DimCustomerMaster  (source: customer_master_cleaned.csv)
# contact/address are JSON strings -> parse into flat columns
# ==================================================================
print("\n[4/15] DimCustomerMaster")
clear_table("DimCustomerMaster")

import json

custs = pd.read_csv(f"{DATA_DIR}/customer_master_cleaned.csv")
rows = []
for _, r in custs.iterrows():
    try:
        contact = json.loads(r["contact"]) if pd.notna(r.get("contact")) else {}
    except (json.JSONDecodeError, TypeError):
        contact = {}
    try:
        address = json.loads(r["address"]) if pd.notna(r.get("address")) else {}
    except (json.JSONDecodeError, TypeError):
        address = {}

    rows.append((
        clean(r.get("customer_id")),
        clean(r.get("customer_name")),
        contact.get("email"),
        contact.get("phone"),
        address.get("city"),
        address.get("state"),
        address.get("country"),
        clean(r.get("customer_type")),
        clean(r.get("registration_date")),
        clean(r.get("credit_limit")),
        clean(r.get("customer_status")),
    ))

bulk_insert(
    "DimCustomerMaster",
    ["customer_id", "customer_name", "email", "phone", "city", "state",
     "country", "customer_type", "registration_date", "credit_limit",
     "customer_status"],
    rows,
)


# ==================================================================
# 5. DimAsset  (source: asset_data_cleaned.csv)
# ==================================================================
print("\n[5/15] DimAsset")
clear_table("DimAsset")

assets = pd.read_csv(f"{DATA_DIR}/asset_data_cleaned.csv")
rows = []
for _, r in assets.iterrows():
    rows.append((
        clean(r.get("asset_id")),
        clean(r.get("location")),
        clean(r.get("install_year")),
        clean(r.get("last_maintenance_year")),
        clean(r.get("usage_hours_per_month")),
        clean(r.get("failure_count")),
        clean(r.get("condition_score")),
        clean(r.get("maintenance_cost_last_year")),
        clean(r.get("asset_type")),
        clean(r.get("operational_state")),
        clean(r.get("disposal_decision")),
    ))

bulk_insert(
    "DimAsset",
    ["asset_id", "location", "install_year", "last_maintenance_year",
     "usage_hours_per_month", "failure_count", "condition_score",
     "maintenance_cost_last_year", "asset_type", "operational_state",
     "disposal_decision"],
    rows,
)


# ==================================================================
# 6. FactAccountsReceivable  (source: account_data_cleaned.csv, 45,839 rows)
# ==================================================================
print("\n[6/15] FactAccountsReceivable")
clear_table("FactAccountsReceivable")

acct = pd.read_csv(f"{DATA_DIR}/account_data_cleaned.csv", low_memory=False)
rows = []
for _, r in acct.iterrows():
    doc_dk = date_key(r.get("doc_date"))
    if doc_dk is None:
        continue  # doc_date_key is NOT NULL — skip any row missing it
    rows.append((
        clean(r.get("document_no")),
        doc_dk,
        date_key(r.get("net_due_date")),
        date_key(r.get("clearing_date")),
        clean(r.get("cust_num")),
        clean(r.get("payment_method_description")),
        clean(r.get("region")),
        clean(r.get("city")),
        clean(r.get("payment_term")),
        clean(r.get("delayflag")),
        clean(r.get("amount")),
        clean(r.get("days_overdue_delay")),
        clean(r.get("no_of_orders_by_customer")),
    ))

bulk_insert(
    "FactAccountsReceivable",
    ["document_no", "doc_date_key", "net_due_date_key", "clearing_date_key",
     "cust_num", "payment_method_description", "region", "city",
     "payment_term", "delayflag", "amount", "days_overdue_delay",
     "no_of_orders_by_customer"],
    rows,
)


# ==================================================================
# 7 & 8. DimSupplier + FactProcurement  (source: procurement_all_cleaned.csv)
# ==================================================================
print("\n[7/15] DimSupplier")
clear_table("FactProcurement")  # clear fact first (references DimSupplier)
clear_table("DimSupplier")

po = pd.read_csv(f"{DATA_DIR}/procurement_all_cleaned.csv")

supplier_ids = sorted(po["supplier_id"].dropna().unique())
bulk_insert("DimSupplier", ["supplier_id"], [(s,) for s in supplier_ids])
supplier_map = get_key_map("DimSupplier", "supplier_key", "supplier_id")

print("\n[8/15] FactProcurement")
rows = []
for _, r in po.iterrows():
    rows.append((
        clean(r.get("purchase_order_id")),
        date_key(r.get("order_date")),
        date_key(r.get("expected_delivery")),
        supplier_map.get(r.get("supplier_id")),
        clean(r.get("supplier_name")),
        clean(r.get("item_id")),
        clean(r.get("item_name")),
        clean(r.get("po_status")),
        clean(r.get("quantity")),
        clean(r.get("unit_cost")),
        clean(r.get("total_cost")),
    ))

bulk_insert(
    "FactProcurement",
    ["purchase_order_id", "order_date_key", "expected_delivery_date_key",
     "supplier_key", "supplier_name", "item_id", "item_name", "po_status",
     "quantity", "unit_cost", "total_cost"],
    rows,
)


# ==================================================================
# 9. FactFinance  (source: finance_data_cleaned.csv)
# ==================================================================
print("\n[9/15] FactFinance")
clear_table("FactFinance")

fin = pd.read_csv(f"{DATA_DIR}/finance_data_cleaned.csv")
rows = []
for _, r in fin.iterrows():
    rows.append((
        clean(r.get("transaction_id")),
        date_key(r.get("date")),
        clean(r.get("account_type")),
        clean(r.get("transaction_amount")),
        clean(r.get("cash_flow")),
        clean(r.get("net_income")),
        clean(r.get("revenue")),
        clean(r.get("expenditure")),
        clean(r.get("profit_margin")),
        clean(r.get("gross_profit")),
        clean(r.get("transaction_volume")),
        clean(r.get("accuracy_score")),
    ))

bulk_insert(
    "FactFinance",
    ["transaction_id", "date_key", "account_type", "transaction_amount",
     "cash_flow", "net_income", "revenue", "expenditure", "profit_margin",
     "gross_profit", "transaction_volume", "accuracy_score"],
    rows,
)


# ==================================================================
# 10 & 11. DimItemInventory + FactInventoryDemand (unpivoted from
# jan_demand..dec_demand)  (source: inventory_data_cleaned.csv)
# ==================================================================
print("\n[10/15] DimItemInventory")
clear_table("FactInventoryDemand")
clear_table("DimItemInventory")

inv = pd.read_csv(f"{DATA_DIR}/inventory_data_cleaned.csv")
rows = []
for _, r in inv.iterrows():
    rows.append((
        clean(r.get("item_id")),
        clean(r.get("item_name")),
        clean(r.get("category")),
        clean(r.get("price_per_unit")),
    ))

bulk_insert("DimItemInventory", ["item_id", "item_name", "category", "price_per_unit"], rows)
item_map = get_key_map("DimItemInventory", "item_key", "item_id")

print("\n[11/15] FactInventoryDemand")
month_cols = ["jan_demand", "feb_demand", "mar_demand", "apr_demand",
              "may_demand", "jun_demand", "jul_demand", "aug_demand",
              "sep_demand", "oct_demand", "nov_demand", "dec_demand"]

rows = []
for _, r in inv.iterrows():
    ik = item_map.get(r.get("item_id"))
    for month_num, col in enumerate(month_cols, start=1):
        rows.append((ik, month_num, clean(r.get(col))))

bulk_insert("FactInventoryDemand", ["item_key", "month_key", "units_demanded"], rows)


# ==================================================================
# 12 & 13. DimWarehouseItem + FactWarehouseSnapshot
# (source: warehouse_data_cleaned.csv)
# ==================================================================
print("\n[12/15] DimWarehouseItem")
clear_table("FactWarehouseSnapshot")
clear_table("DimWarehouseItem")

wh = pd.read_csv(f"{DATA_DIR}/warehouse_data_cleaned.csv")
rows = []
for _, r in wh.iterrows():
    rows.append((
        clean(r.get("item_id")),
        clean(r.get("category")),
        clean(r.get("storage_location_id")),
        clean(r.get("zone")),
    ))

bulk_insert("DimWarehouseItem", ["item_id", "category", "storage_location_id", "zone"], rows)
wh_item_map = get_key_map("DimWarehouseItem", "warehouse_item_key", "item_id")

print("\n[13/15] FactWarehouseSnapshot")
rows = []
for _, r in wh.iterrows():
    rows.append((
        date_key(r.get("last_restock_date")),
        wh_item_map.get(r.get("item_id")),
        clean(r.get("stock_level")),
        clean(r.get("reorder_point")),
        clean(r.get("lead_time_days")),
        clean(r.get("daily_demand")),
        clean(r.get("picking_time_seconds")),
        clean(r.get("handling_cost_per_unit")),
        clean(r.get("unit_price")),
        clean(r.get("holding_cost_per_unit_day")),
        clean(r.get("stockout_count_last_month")),
        clean(r.get("order_fulfillment_rate")),
        clean(r.get("total_orders_last_month")),
        clean(r.get("turnover_ratio")),
        clean(r.get("forecasted_demand_next_7d")),
        clean(r.get("kpi_score")),
    ))

bulk_insert(
    "FactWarehouseSnapshot",
    ["date_key", "warehouse_item_key", "stock_level", "reorder_point",
     "lead_time_days", "daily_demand", "picking_time_seconds",
     "handling_cost_per_unit", "unit_price", "holding_cost_per_unit_day",
     "stockout_count_last_month", "order_fulfillment_rate",
     "total_orders_last_month", "turnover_ratio",
     "forecasted_demand_next_7d", "kpi_score"],
    rows,
)


# ==================================================================
# 14. FactManufacturing  (source: manufacturing_data_cleaned.csv)
# ==================================================================
print("\n[14/15] FactManufacturing")
clear_table("FactManufacturing")

mfg = pd.read_csv(f"{DATA_DIR}/manufacturing_data_cleaned.csv")
rows = []
for _, r in mfg.iterrows():
    rows.append((
        clean(r.get("job_id")),
        date_key(r.get("scheduled_start")),
        date_key(r.get("actual_start")),  # None if missing — column is nullable
        clean(r.get("machine_id")),
        clean(r.get("operation_type")),
        clean(r.get("job_status")),
        clean(r.get("optimization_category")),
        clean(r.get("material_used")),
        clean(r.get("processing_time")),
        clean(r.get("energy_consumption")),
        clean(r.get("machine_availability")),
    ))

bulk_insert(
    "FactManufacturing",
    ["job_id", "scheduled_start_date_key", "actual_start_date_key",
     "machine_id", "operation_type", "job_status", "optimization_category",
     "material_used", "processing_time", "energy_consumption",
     "machine_availability"],
    rows,
)


# ==================================================================
# 15. DimEmployee  (source: employee_data_cleaned.csv, no natural key)
# ==================================================================
print("\n[15/15] DimEmployee")
clear_table("DimEmployee")

emp = pd.read_csv(f"{DATA_DIR}/employee_data_cleaned.csv")
rows = []
for _, r in emp.iterrows():
    rows.append((
        clean(r.get("first_name")),
        clean(r.get("last_name")),
        clean(r.get("gender")),
        clean(r.get("age")),
        clean(r.get("salary")),
        clean(r.get("expenditure")),
        clean(r.get("savings")),
        clean(r.get("expenditure_percentage")),
        clean(r.get("savings_percentage")),
    ))

bulk_insert(
    "DimEmployee",
    ["first_name", "last_name", "gender", "age", "salary", "expenditure",
     "savings", "expenditure_percentage", "savings_percentage"],
    rows,
)


print("\n" + "=" * 60)
print("LOAD COMPLETE")
print("=" * 60)
cur.close()
conn.close()
