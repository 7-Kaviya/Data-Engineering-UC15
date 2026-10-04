"""
ERP DATA VALIDATION — GROUP 2
Validates the cleaned Sales, Customer Master, Asset, Account and
Procurement datasets (the five datasets not covered by
ERP_Data_Validation_Separate.py) and writes a summary report to
../silver/validation/group2_validation_summary.csv

Run from the python/ folder:  python3 ERP_Data_Validation_Group2.py
"""

import json
import pandas as pd

DATA_DIR = "../silver/cleansing/cleaned_datasets"

sales = pd.read_csv(f"{DATA_DIR}/sales_data_cleaned.csv")
customer = pd.read_csv(f"{DATA_DIR}/customer_master_cleaned.csv")
asset = pd.read_csv(f"{DATA_DIR}/asset_data_cleaned.csv")
account = pd.read_csv(f"{DATA_DIR}/account_data_cleaned.csv", low_memory=False)
procurement = pd.read_csv(f"{DATA_DIR}/procurement_all_cleaned.csv")

results = []
TODAY = pd.Timestamp.today().normalize()


def log_check(dataset, check_name, error_count):
    results.append({
        "Dataset": dataset,
        "Validation_Check": check_name,
        "Error_Count": int(error_count),
        "Status": "PASS" if error_count == 0 else "FAIL",
    })
    print(f"  {check_name}: {int(error_count)}")


def to_date(series):
    """Parse a column to dates; unparseable values become NaT."""
    return pd.to_datetime(series, errors="coerce", format="mixed")


def common_checks(name, df, key=None):
    """Checks every dataset gets: missing values, duplicate rows, duplicate key."""
    log_check(name, "Missing values", df.isnull().sum().sum())
    log_check(name, "Duplicate rows", df.duplicated().sum())
    if key:
        log_check(name, f"Duplicate {key}", df[key].duplicated().sum())


# ------------------------------------------------
# SALES
# ------------------------------------------------
print("\nSALES VALIDATION")
common_checks("Sales", sales, "transaction_id")
log_check("Sales", "Quantity <= 0", (sales["quantity"] <= 0).sum())
log_check("Sales", "Negative price_per_unit", (sales["price_per_unit"] < 0).sum())
log_check("Sales", "Negative total_amount", (sales["total_amount"] < 0).sum())
expected = sales["quantity"] * sales["price_per_unit"]
log_check("Sales", "total_amount != quantity x price",
          ((expected - sales["total_amount"]).abs() > 0.01).sum())
log_check("Sales", "Invalid age (<18 or >100)",
          ((sales["age"] < 18) | (sales["age"] > 100)).sum())
log_check("Sales", "Invalid gender value",
          (~sales["gender"].isin(["Male", "Female"])).sum())
sdate = to_date(sales["date"])
log_check("Sales", "Unparseable date", sdate.isna().sum())
log_check("Sales", "Future date", (sdate > TODAY).sum())


# ------------------------------------------------
# CUSTOMER MASTER
# ------------------------------------------------
print("\nCUSTOMER MASTER VALIDATION")
common_checks("Customer", customer, "customer_id")
log_check("Customer", "Negative credit_limit", (customer["credit_limit"] < 0).sum())
rdate = to_date(customer["registration_date"])
log_check("Customer", "Unparseable registration_date", rdate.isna().sum())
log_check("Customer", "Future registration_date", (rdate > TODAY).sum())


def bad_json(value):
    try:
        json.loads(value)
        return False
    except (TypeError, ValueError):
        return True


log_check("Customer", "Unparseable contact JSON", customer["contact"].map(bad_json).sum())
log_check("Customer", "Unparseable address JSON", customer["address"].map(bad_json).sum())


# ------------------------------------------------
# ASSET
# ------------------------------------------------
print("\nASSET VALIDATION")
common_checks("Asset", asset, "asset_id")
log_check("Asset", "Negative usage_hours_per_month", (asset["usage_hours_per_month"] < 0).sum())
log_check("Asset", "Negative failure_count", (asset["failure_count"] < 0).sum())
log_check("Asset", "Negative maintenance_cost_last_year", (asset["maintenance_cost_last_year"] < 0).sum())
log_check("Asset", "condition_score outside 0-1",
          ((asset["condition_score"] < 0) | (asset["condition_score"] > 1)).sum())
log_check("Asset", "Future install_year", (asset["install_year"] > TODAY.year).sum())
log_check("Asset", "Future last_maintenance_year", (asset["last_maintenance_year"] > TODAY.year).sum())
log_check("Asset", "last_maintenance_year before install_year",
          (asset["last_maintenance_year"] < asset["install_year"]).sum())


# ------------------------------------------------
# ACCOUNT (ACCOUNTS RECEIVABLE)
# ------------------------------------------------
print("\nACCOUNT VALIDATION")
common_checks("Account", account, "document_no")
log_check("Account", "Negative amount", (account["amount"] < 0).sum())
doc = to_date(account["doc_date"])
due = to_date(account["net_due_date"])
post = to_date(account["posting_date"])
clear = to_date(account["clearing_date"])
log_check("Account", "Unparseable doc_date", doc.isna().sum())
log_check("Account", "Unparseable net_due_date", due.isna().sum())
log_check("Account", "Unparseable clearing_date", clear.isna().sum())
log_check("Account", "net_due_date before doc_date", (due < doc).sum())
log_check("Account", "clearing_date before doc_date", (clear < doc).sum())
log_check("Account", "Future clearing_date", (clear > TODAY).sum())
log_check("Account", "delayflag not 0/1", (~account["delayflag"].isin([0, 1])).sum())


# ------------------------------------------------
# PROCUREMENT
# ------------------------------------------------
print("\nPROCUREMENT VALIDATION")
common_checks("Procurement", procurement, "purchase_order_id")
log_check("Procurement", "Quantity <= 0", (procurement["quantity"] <= 0).sum())
log_check("Procurement", "Negative unit_cost", (procurement["unit_cost"] < 0).sum())
log_check("Procurement", "Negative total_cost", (procurement["total_cost"] < 0).sum())
expected_cost = procurement["quantity"] * procurement["unit_cost"]
log_check("Procurement", "total_cost != quantity x unit_cost",
          ((expected_cost - procurement["total_cost"]).abs() > 0.01).sum())
odate = to_date(procurement["order_date"])
edate = to_date(procurement["expected_delivery"])
log_check("Procurement", "Unparseable order_date", odate.isna().sum())
log_check("Procurement", "expected_delivery before order_date", (edate < odate).sum())


# ------------------------------------------------
# WRITE SUMMARY REPORT
# ------------------------------------------------
summary = pd.DataFrame(results)
summary.to_csv("../silver/validation/group2_validation_summary.csv", index=False)

print("\nVALIDATION COMPLETED")
print(f"Checks run: {len(summary)}   Failed: {(summary['Status'] == 'FAIL').sum()}")
print("Summary written to ../silver/validation/group2_validation_summary.csv")
print()
failed = summary[summary["Status"] == "FAIL"]
if len(failed):
    print(failed.to_string(index=False))
