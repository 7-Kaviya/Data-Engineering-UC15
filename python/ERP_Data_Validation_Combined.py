"""
ERP DATA VALIDATION
"""

import pandas as pd
import numpy as np


df = pd.read_csv(r"C:/Users/USER/Data-Enginering-UC15/silver/cleansing/erp_cleaned_data.csv")

# Convert relevant fields
date_columns = [
    "sale_date", "purchase_date", "last_maintenance_date",
    "registration_date", "order_date", "expected_delivery",
    "transaction_date"
]

for col in date_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

numeric_columns = [
    "quantity", "unit_price", "discount_percent", "total_amount",
    "purchase_cost", "useful_life_years", "condition_score",
    "credit_limit", "unit_cost", "total_cost",
    "debit_amount", "credit_amount"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Separate ERP sections
sales = df[df["sale_id"].notna()].copy()
customers = df[df["customer_name"].notna()].copy()
assets = df[df["asset_id"].notna()].copy()
purchase_orders = df[df["purchase_order_id"].notna()].copy()
finance = df[df["voucher_id"].notna()].copy()

# DUPLICATE MASTER RECORD VALIDATION

duplicate_results = []

master_keys = {
    "Customer": ("customer_id", customers),
    "Asset": ("asset_id", assets),
    "Purchase Order": ("purchase_order_id", purchase_orders),
}

for master_name, (key, data) in master_keys.items():
    if key in data.columns:
        dup = data[data[key].duplicated(keep=False)].copy()
        dup.insert(0, "Master_Type", master_name)
        duplicate_results.append(dup)

if duplicate_results:
    duplicate_records = pd.concat(duplicate_results, ignore_index=True)
else:
    duplicate_records = pd.DataFrame()

duplicate_records.to_csv("duplicate_records.csv", index=False)

# MISSING TRANSACTION VALIDATION

missing_sales = pd.DataFrame()
missing_pos = pd.DataFrame()

if "reference_id" in finance.columns:

    finance_refs = set(finance["reference_id"].dropna().astype(str))

    sales_ids = set(sales["sale_id"].dropna().astype(str))
    po_ids = set(purchase_orders["purchase_order_id"].dropna().astype(str))

    missing_sales_ids = sorted(sales_ids - finance_refs)
    missing_po_ids = sorted(po_ids - finance_refs)

    missing_sales = pd.DataFrame({
        "Missing_Sales_ID": missing_sales_ids
    })

    missing_pos = pd.DataFrame({
        "Missing_PO_ID": missing_po_ids
    })

missing_transactions = pd.concat(
    [
        missing_sales.assign(Transaction_Type="Sales"),
        missing_pos.assign(Transaction_Type="Purchase Order")
    ],
    ignore_index=True
)

missing_transactions.to_csv("missing_transactions.csv", index=False)

# INVENTORY VALIDATION

purchased = (
    purchase_orders
    .groupby("item_id")["quantity"]
    .sum()
    .rename("Purchased_Quantity")
)

sold = (
    sales
    .groupby("product_id")["quantity"]
    .sum()
    .rename("Sold_Quantity")
)

inventory = pd.concat([purchased, sold], axis=1).fillna(0)

inventory["Calculated_Balance"] = (
    inventory["Purchased_Quantity"] -
    inventory["Sold_Quantity"]
)

inventory["Validation_Status"] = np.where(
    inventory["Calculated_Balance"] < 0,
    "ERROR - Negative Inventory",
    "VALID"
)

inventory = inventory.reset_index()
inventory.rename(columns={"index": "Product_ID"}, inplace=True)

inventory.to_csv("inventory_validation.csv", index=False)

# FINANCIAL VALIDATION

financial_errors = []

# Sales amount calculation
if all(
    col in sales.columns
    for col in ["quantity", "unit_price", "discount_percent", "total_amount"]
):
    sales["Expected_Amount"] = (
        sales["quantity"]
        * sales["unit_price"]
        * (1 - sales["discount_percent"] / 100)
    )

    sales["Amount_Difference"] = (
        sales["Expected_Amount"] - sales["total_amount"]
    )

    sales_errors = sales[
        sales["Amount_Difference"].abs() > 0.01
    ].copy()

    if not sales_errors.empty:
        sales_errors["Validation_Type"] = "Sales Amount Mismatch"
        financial_errors.append(sales_errors)

# Purchase order amount calculation
if all(
    col in purchase_orders.columns
    for col in ["quantity", "unit_cost", "total_cost"]
):
    purchase_orders["Expected_Cost"] = (
        purchase_orders["quantity"] *
        purchase_orders["unit_cost"]
    )

    purchase_orders["Cost_Difference"] = (
        purchase_orders["Expected_Cost"] -
        purchase_orders["total_cost"]
    )

    po_errors = purchase_orders[
        purchase_orders["Cost_Difference"].abs() > 0.01
    ].copy()

    if not po_errors.empty:
        po_errors["Validation_Type"] = "Purchase Order Cost Mismatch"
        financial_errors.append(po_errors)

if financial_errors:
    financial_validation = pd.concat(
        financial_errors, ignore_index=True, sort=False
    )
else:
    financial_validation = pd.DataFrame()

financial_validation.to_csv("financial_validation.csv", index=False)

# MASTER DATA VALIDATION

master_errors = []

# Supplier ID associated with multiple supplier names
if "supplier_id" in purchase_orders.columns and "supplier_name" in purchase_orders.columns:

    supplier_name_count = (
        purchase_orders
        .groupby("supplier_id")["supplier_name"]
        .nunique()
    )

    bad_supplier_ids = supplier_name_count[
        supplier_name_count > 1
    ].index

    supplier_errors = purchase_orders[
        purchase_orders["supplier_id"].isin(bad_supplier_ids)
    ].copy()

    if not supplier_errors.empty:
        supplier_errors["Validation_Type"] = "Supplier ID / Name Inconsistency"
        master_errors.append(supplier_errors)

# Future maintenance dates
if "last_maintenance_date" in assets.columns:

    today = pd.Timestamp.today().normalize()

    future_maintenance = assets[
        assets["last_maintenance_date"] > today
    ].copy()

    if not future_maintenance.empty:
        future_maintenance["Validation_Type"] = "Future Maintenance Date"
        master_errors.append(future_maintenance)

if master_errors:
    master_data_validation = pd.concat(
        master_errors, ignore_index=True, sort=False
    )
else:
    master_data_validation = pd.DataFrame()

master_data_validation.to_csv(
    "master_data_validation.csv", index=False
)

# VALIDATION SUMMARY

summary = pd.DataFrame({
    "Validation": [
        "Duplicate master records",
        "Missing sales finance references",
        "Missing PO finance references",
        "Negative inventory records",
        "Sales financial errors",
        "PO financial errors",
        "Master-data errors"
    ],
    "Error_Count": [
        len(duplicate_records),
        len(missing_sales),
        len(missing_pos),
        int((inventory["Calculated_Balance"] < 0).sum()),
        len(sales_errors) if "sales_errors" in locals() else 0,
        len(po_errors) if "po_errors" in locals() else 0,
        len(master_data_validation)
    ]
})

summary["Status"] = np.where(
    summary["Error_Count"] == 0,
    "PASS",
    "FAIL"
)

summary.to_csv("validation_summary.csv", index=False)

print("=" * 60)
print("ERP DATA VALIDATION COMPLETED")
print("=" * 60)
print(summary.to_string(index=False))
