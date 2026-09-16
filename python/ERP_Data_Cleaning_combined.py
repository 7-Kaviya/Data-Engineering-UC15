"""
ERP DATA CLEANING
"""

import pandas as pd
import re

CLEANING_LOG = "data_cleaning_log.csv"

# Read source data
df = pd.read_csv(r"C:/Users/USER/Downloads/erp_combined_data.csv")

original_rows = len(df)

# Standardize column names
df.columns = (
    df.columns
      .str.strip()
      .str.lower()
      .str.replace(" ", "_", regex=False)
)

# Remove completely blank rows
df = df.dropna(how="all")

# Remove exact duplicate rows
duplicate_rows_removed = df.duplicated().sum()
df = df.drop_duplicates()

# Clean text fields
text_columns = df.select_dtypes(include=["object", "string"]).columns

for col in text_columns:
    df[col] = (
        df[col]
        .astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    )

# Standardize date fields
date_columns = [
    "sale_date",
    "purchase_date",
    "last_maintenance_date",
    "registration_date",
    "order_date",
    "expected_delivery",
    "transaction_date"
]

for col in date_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

# Standardize numeric fields
numeric_columns = [
    "quantity",
    "unit_price",
    "discount_percent",
    "total_amount",
    "purchase_cost",
    "useful_life_years",
    "condition_score",
    "credit_limit",
    "unit_cost",
    "total_cost",
    "debit_amount",
    "credit_amount",
    "fiscal_year"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Standardize phone numbers
if "phone" in df.columns:
    df["phone"] = df["phone"].apply(
        lambda x: re.sub(r"\D", "", str(x)) if pd.notna(x) else pd.NA
    )

# Standardize selected categorical fields
category_columns = [
    "sales_channel",
    "payment_method",
    "sales_region",
    "asset_status",
    "customer_type",
    "customer_status",
    "po_status",
    "transaction_type",
    "posting_status"
]

for col in category_columns:
    if col in df.columns:
        df[col] = df[col].astype("string").str.strip().str.title()

# Save cleaned data
df.to_csv("C:/Users/USER/Downloads/erp_cleaned_data.csv", index=False)

# Cleaning summary
log = pd.DataFrame({
    "Metric": [
        "Original rows",
        "Rows after blank-row removal and duplicate removal",
        "Blank rows removed",
        "Exact duplicate rows removed",
        "Final columns"
    ],
    "Value": [
        original_rows,
        len(df),
        original_rows - len(df) - duplicate_rows_removed,
        duplicate_rows_removed,
        len(df.columns)
    ]
})


print("DATA CLEANING COMPLETED")
print(log.to_string(index=False))
