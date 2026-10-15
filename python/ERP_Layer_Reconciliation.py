"""
ERP LAYER RECONCILIATION  (raw file > cleaned file > warehouse)

For each of the 10 datasets this compares three things at every layer:
  rows          the number of records
  control total the sum of one numeric column (for Inventory, the 12 monthly demand columns)
and says whether the layers agree. A difference is accepted only when it has a known reason
(for example exact duplicate rows removed by cleaning); anything else is reported as DIFFERENT.

Run from the python/ folder (the warehouse must be loaded):   python3 ERP_Layer_Reconciliation.py
Writes ../silver/validation/layer_reconciliation.csv
Password: environment variable UC15_DB_PASSWORD (default uc15pass).
"""
import os
import re
import warnings

import pandas as pd
import psycopg2

warnings.filterwarnings("ignore")
DATASETS = "../datasets"
CLEAN = "../silver/cleansing/cleaned_datasets"

DB = dict(host=os.getenv("PGHOST", "localhost"), port=int(os.getenv("PGPORT", "5432")), dbname=os.getenv("PGDATABASE", "uc15_dw"),
          user=os.getenv("PGUSER", "postgres"), password=os.getenv("UC15_DB_PASSWORD", "uc15pass"))

norm = lambda s: re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def read_raw(name):
    p = f"{DATASETS}/{name}"
    if name.endswith(".csv"): return pd.read_csv(p)
    if name.endswith(".json"): return pd.read_json(p)
    if name.endswith(".xml"): return pd.read_xml(p)
    return pd.read_excel(p)


def raw_column(raw_df, cleaned_name):
    lookup = {norm(c): c for c in raw_df.columns}
    return lookup[cleaned_name]


MONTHS = [f"{m}_demand" for m in ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")]
# dataset, raw file, cleaned file, measure (cleaned column name, or "MONTHS"), warehouse table for the row count, warehouse table.column for the total
PLAN = [
    ("Sales", "Sales_data.csv", "sales_data_cleaned.csv", "total_amount", "factsales", ("factsales", "total_amount")),
    ("Customer Master", "Customer_Master.json", "customer_master_cleaned.csv", "credit_limit", "dimcustomermaster", ("dimcustomermaster", "credit_limit")),
    ("Asset", "Asset_data.xml", "asset_data_cleaned.csv", "maintenance_cost_last_year", "dimasset", ("dimasset", "maintenance_cost_last_year")),
    ("Account", "Account_data.xls", "account_data_cleaned.csv", "amount", "factaccountsreceivable", ("factaccountsreceivable", "amount")),
    ("Procurement", "procurement_all.csv", "procurement_all_cleaned.csv", "total_cost", "factprocurement", ("factprocurement", "total_cost")),
    ("Employee", "employee_data.xls", "employee_data_cleaned.csv", "salary", "dimemployee", ("dimemployee", "salary")),
    ("Finance", "Finance_data.csv", "finance_data_cleaned.csv", "transaction_amount", "factfinance", ("factfinance", "transaction_amount")),
    ("Inventory", "Inventory_data.json", "inventory_data_cleaned.csv", "MONTHS", "dimiteminventory", ("factinventorydemand", "units_demanded")),
    ("Manufacturing", "Manufacturing_data.xml", "manufacturing_data_cleaned.csv", "material_used", "factmanufacturing", ("factmanufacturing", "material_used")),
    ("Warehouse", "warehouse.csv", "warehouse_data_cleaned.csv", "stock_level", "dimwarehouseitem", ("factwarehousesnapshot", "stock_level")),
]


def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    out = []
    for name, raw_file, clean_file, measure, row_table, (tot_table, tot_col) in PLAN:
        raw = read_raw(raw_file)
        cleaned = pd.read_csv(f"{CLEAN}/{clean_file}", low_memory=False)
        if measure == "MONTHS":
            raw_total = float(sum(raw[raw_column(raw, m)].sum() for m in MONTHS))
            clean_total = float(cleaned[MONTHS].sum().sum())
            label = "sum of the 12 monthly demand columns"
        else:
            raw_total = float(raw[raw_column(raw, measure)].sum())
            clean_total = float(cleaned[measure].sum())
            label = measure
        cur.execute(f"SELECT COUNT(*) FROM {row_table}")
        loaded_rows = cur.fetchone()[0]
        cur.execute(f"SELECT COALESCE(SUM({tot_col}), 0) FROM {tot_table}")
        wh_total = float(cur.fetchone()[0])

        raw_rows, clean_rows = len(raw), len(cleaned)
        cleaned_ok = clean_rows == loaded_rows and abs(clean_total - wh_total) < 0.05
        if raw_rows == clean_rows and abs(raw_total - clean_total) < 0.05:
            raw_ok, note = True, "Raw and cleaned agree."
        elif len(raw.drop_duplicates()) == clean_rows and abs(raw_total - clean_total) > 0.05:
            raw_ok, note = True, f"Explained: the raw file holds {raw_rows - clean_rows:,} exact duplicate rows, removed by cleaning."
        else:
            raw_ok, note = False, "Raw and cleaned differ and the difference is not explained."
        if not cleaned_ok:
            note = "Cleaned file and warehouse differ. " + note
        status = "PASS" if (cleaned_ok and raw_ok and "Explained" not in note) else "EXPLAINED" if (cleaned_ok and raw_ok) else "DIFFERENT"
        out.append(dict(dataset=name, measure=label, raw_rows=raw_rows, cleaned_rows=clean_rows, loaded_rows=loaded_rows,
                        raw_total=round(raw_total, 2), cleaned_total=round(clean_total, 2), warehouse_total=round(wh_total, 2), status=status, note=note))
    conn.close()
    res = pd.DataFrame(out)
    res.to_csv("../silver/validation/layer_reconciliation.csv", index=False)
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 20)
    print(res[["dataset", "raw_rows", "cleaned_rows", "loaded_rows", "raw_total", "cleaned_total", "warehouse_total", "status"]].to_string(index=False))
    print()
    for r in res.itertuples():
        if r.status != "PASS":
            print(f"{r.dataset}: {r.note}")
    print(f"\n{(res.status == 'PASS').sum()} PASS, {(res.status == 'EXPLAINED').sum()} EXPLAINED, {(res.status == 'DIFFERENT').sum()} DIFFERENT")
    print("Written ../silver/validation/layer_reconciliation.csv")


if __name__ == "__main__":
    main()
