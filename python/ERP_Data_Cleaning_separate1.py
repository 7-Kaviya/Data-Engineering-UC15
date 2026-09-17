import pandas as pd
from pathlib import Path

finance = pd.read_csv("../datasets/Finance_data.csv")
inventory = pd.read_json("../datasets/Inventory_data.json")
manufacturing = pd.read_xml("../datasets/Manufacturing_data.xml")
employee = pd.read_excel("../datasets/employee_data.xls")
warehouse = pd.read_csv("../datasets/warehouse.csv")

output = Path("../silver/cleansing/cleaned_datasets")
output.mkdir(parents=True, exist_ok=True)

def standardize_columns(df):
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-zA-Z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return df

def clean_text(df):
    df = df.copy()

    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = (
            df[col].astype("string")
            .str.strip()
            .replace({
                "": pd.NA,
                "NULL": pd.NA,
                "null": pd.NA,
                "None": pd.NA,
                "none": pd.NA,
                "N/A": pd.NA,
                "n/a": pd.NA
            })
        )

    return df

def basic_clean(df):
    original = len(df)

    df = standardize_columns(df)
    df = df.dropna(how="all").copy()
    blank_removed = original - len(df)

    df = clean_text(df)

    before_duplicates = len(df)
    df = df.drop_duplicates().copy()
    duplicates_removed = before_duplicates - len(df)

    return df, blank_removed, duplicates_removed

def numeric(df, columns, integers=None):
    integers = set(integers or [])

    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

            if col in integers:
                df[col] = df[col].round().astype("Int64")

    return df

def dates(df, columns, fmt="%Y-%m-%d"):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col], errors="coerce"
            ).dt.strftime(fmt)

    return df


# ============================================================
# 1. EMPLOYEE CLEANING
# ============================================================
employee, e_blank, e_dup = basic_clean(employee)

if "gender" in employee.columns:
    employee["gender"] = employee["gender"].str.title()

employee = numeric(
    employee,
    [
        "age",
        "salary",
        "expenditure",
        "savings",
        "expenditure_percentage",
        "savings_percentage"
    ],
    integers=["age"]
)

employee.to_csv(
    output / "employee_data_cleaned.csv",
    index=False
)


# ============================================================
# 2. FINANCE CLEANING
# ============================================================
finance, f_blank, f_dup = basic_clean(finance)

if "account_type" in finance.columns:
    finance["account_type"] = finance["account_type"].str.title()

finance = dates(finance, ["date"])

finance = numeric(
    finance,
    [
        "transaction_id",
        "transaction_amount",
        "cash_flow",
        "net_income",
        "revenue",
        "expenditure",
        "profit_margin",
        "debt_to_equity_ratio",
        "operating_expenses",
        "gross_profit",
        "transaction_volume",
        "processing_time_seconds",
        "accuracy_score",
        "normalized_transaction_amount"
    ],
    integers=[
        "transaction_id",
        "transaction_volume",
        "processing_time_seconds"
    ]
)

if "transaction_outcome" in finance.columns:
    finance["transaction_outcome"] = pd.to_numeric(
        finance["transaction_outcome"],
        errors="coerce"
    ).astype("Int64")

if "missing_data_indicator" in finance.columns:
    finance["missing_data_indicator"] = (
        finance["missing_data_indicator"]
        .astype("string")
        .str.lower()
        .map({"true": True, "false": False})
        .astype("boolean")
    )

finance.to_csv(
    output / "finance_data_cleaned.csv",
    index=False
)


# ============================================================
# 3. INVENTORY CLEANING
# ============================================================
inventory, i_blank, i_dup = basic_clean(inventory)

if "category" in inventory.columns:
    inventory["category"] = inventory["category"].str.title()

month_columns = [
    "jan_demand",
    "feb_demand",
    "mar_demand",
    "apr_demand",
    "may_demand",
    "jun_demand",
    "jul_demand",
    "aug_demand",
    "sep_demand",
    "oct_demand",
    "nov_demand",
    "dec_demand",
    "total_annual_units"
]

inventory = numeric(
    inventory,
    month_columns,
    integers=month_columns
)

inventory = numeric(
    inventory,
    [
        "price_per_unit",
        "total_sales_value"
    ]
)

inventory.to_csv(
    output / "inventory_data_cleaned.csv",
    index=False
)


# ============================================================
# 4. MANUFACTURING CLEANING
# ============================================================
manufacturing, m_blank, m_dup = basic_clean(manufacturing)

for col in [
    "operation_type",
    "job_status",
    "optimization_category"
]:
    if col in manufacturing.columns:
        manufacturing[col] = manufacturing[col].str.title()

manufacturing = numeric(
    manufacturing,
    [
        "material_used",
        "processing_time",
        "energy_consumption",
        "machine_availability"
    ],
    integers=[
        "processing_time",
        "machine_availability"
    ]
)

manufacturing = dates(
    manufacturing,
    [
        "scheduled_start",
        "scheduled_end",
        "actual_start",
        "actual_end"
    ],
    fmt="%Y-%m-%d %H:%M:%S"
)

manufacturing.to_csv(
    output / "manufacturing_data_cleaned.csv",
    index=False
)


# ============================================================
# 5. WAREHOUSE CLEANING
# ============================================================
warehouse, w_blank, w_dup = basic_clean(warehouse)

if "category" in warehouse.columns:
    warehouse["category"] = (
        warehouse["category"]
        .str.title()
        .replace({"Groceries": "Grocery"})
    )

if "zone" in warehouse.columns:
    warehouse["zone"] = warehouse["zone"].str.upper()

warehouse = dates(
    warehouse,
    ["last_restock_date"]
)

warehouse_numeric = [
    "stock_level",
    "reorder_point",
    "reorder_frequency_days",
    "lead_time_days",
    "daily_demand",
    "demand_std_dev",
    "item_popularity_score",
    "picking_time_seconds",
    "handling_cost_per_unit",
    "unit_price",
    "holding_cost_per_unit_day",
    "stockout_count_last_month",
    "order_fulfillment_rate",
    "total_orders_last_month",
    "turnover_ratio",
    "layout_efficiency_score",
    "forecasted_demand_next_7d",
    "kpi_score"
]

warehouse_integers = [
    "stock_level",
    "reorder_point",
    "reorder_frequency_days",
    "lead_time_days",
    "picking_time_seconds",
    "stockout_count_last_month",
    "total_orders_last_month"
]

warehouse = numeric(
    warehouse,
    warehouse_numeric,
    integers=warehouse_integers
)

warehouse.to_csv(
    output / "warehouse_data_cleaned.csv",
    index=False
)


# ============================================================
# CLEANING LOG
# ============================================================
log = pd.DataFrame([
    ["Employee", e_blank, e_dup, len(employee)],
    ["Finance", f_blank, f_dup, len(finance)],
    ["Inventory", i_blank, i_dup, len(inventory)],
    ["Manufacturing", m_blank, m_dup, len(manufacturing)],
    ["Warehouse", w_blank, w_dup, len(warehouse)]
], columns=[
    "Dataset",
    "Blank_Rows_Removed",
    "Exact_Duplicates_Removed",
    "Final_Rows"
])

log.to_csv(
    output / "five_datasets_cleaning_log_group1.csv",
    index=False
)

print("\nDATA CLEANING COMPLETED")
print("=" * 60)
print(log.to_string(index=False))
print("\nFiles saved in:")
print(output)
