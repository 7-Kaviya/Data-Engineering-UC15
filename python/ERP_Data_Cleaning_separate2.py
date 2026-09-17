import pandas as pd
from pathlib import Path
import json


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

output_file = Path(
    "../silver/cleansing/cleaned_datasets"
)

output_file.mkdir(parents=True, exist_ok=True)


# ============================================================
# INPUT FILES
# ============================================================

sales = pd.read_csv(
    "../datasets/Sales_data.csv"
)

customer = pd.read_json(
    "../datasets/Customer_Master.json"
)

asset = pd.read_xml(
    "../datasets/Asset_data.xml"
)

account = pd.read_excel(
    "../datasets/Account_data.xls"
)

procurement = pd.read_csv(
    "../datasets/procurement_all.csv"
)


# ============================================================
# STANDARDIZE COLUMN NAMES
# ============================================================

def standardize_columns(df):

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    return df


# ============================================================
# CONVERT NESTED JSON VALUES
# ============================================================

def convert_nested_values(df):

    for col in df.columns:

        df[col] = df[col].apply(
            lambda x: json.dumps(x, sort_keys=True)
            if isinstance(x, (dict, list))
            else x
        )

    return df


# ============================================================
# CLEAN DATASET
# ============================================================

def clean_dataset(df):

    rows_before = len(df)

    # --------------------------------------------------------
    # 1. Remove completely blank rows
    # --------------------------------------------------------

    df = df.dropna(how="all").copy()


    # --------------------------------------------------------
    # 2. Handle dictionary/list values
    # --------------------------------------------------------

    df = convert_nested_values(df)


    # --------------------------------------------------------
    # 3. Trim spaces and convert NULL values
    # --------------------------------------------------------

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for col in text_columns:

        df[col] = df[col].apply(
            lambda x: x.strip()
            if isinstance(x, str)
            else x
        )

        df[col] = df[col].replace(
            r"^\s*(NULL|None|none|N/A|n/a|NA|na|-)\s*$",
            pd.NA,
            regex=True
        )


    # --------------------------------------------------------
    # 4. Remove exact duplicate rows
    # --------------------------------------------------------

    duplicates_removed = int(
        df.duplicated().sum()
    )

    df = df.drop_duplicates().copy()


    # --------------------------------------------------------
    # 5. Convert numeric-looking columns
    # --------------------------------------------------------

    for col in df.columns:

        if df[col].dtype == "object":

            converted = pd.to_numeric(
                df[col],
                errors="coerce"
            )

            non_empty = df[col].notna().sum()

            if non_empty > 0:

                numeric_count = converted.notna().sum()

                if numeric_count / non_empty >= 0.90:

                    df[col] = converted


    # --------------------------------------------------------
    # 6. Convert date-looking columns
    # --------------------------------------------------------

    date_keywords = [
        "date",
        "dob",
        "birth",
        "created",
        "updated",
        "start",
        "end",
        "maintenance",
        "purchase"
    ]

    for col in df.columns:

        if any(
            keyword in col
            for keyword in date_keywords
        ):

            if df[col].dtype == "object":

                converted_date = pd.to_datetime(
                    df[col],
                    errors="coerce"
                )

                non_empty = df[col].notna().sum()

                if non_empty > 0:

                    valid_dates = converted_date.notna().sum()

                    if valid_dates / non_empty >= 0.70:

                        df[col] = converted_date


    return (
        df,
        rows_before,
        len(df),
        duplicates_removed
    )


# ============================================================
# DATASETS
# ============================================================

datasets = {

    "sales_data": sales,

    "customer_master": customer,

    "asset_data": asset,

    "account_data": account,

    "procurement_all": procurement

}


# ============================================================
# CLEAN AND SAVE
# ============================================================

log = []


for name, df in datasets.items():

    print(f"Cleaning {name}...")

    # Standardize columns
    df = standardize_columns(df)

    # Clean
    (
        cleaned_df,
        rows_before,
        rows_after,
        duplicates_removed
    ) = clean_dataset(df)


    # Output file
    cleaned_file = (
        output_file /
        f"{name}_cleaned.csv"
    )


    # Save
    cleaned_df.to_csv(
        cleaned_file,
        index=False
    )


    # Log
    log.append({

        "dataset": name,

        "rows_before": rows_before,

        "rows_after": rows_after,

        "duplicates_removed": duplicates_removed,

        "columns": len(cleaned_df.columns)

    })


    print(
        f"Saved: {cleaned_file}"
    )

    print(
        f"Rows before: {rows_before}"
    )

    print(
        f"Rows after : {rows_after}"
    )

    print(
        f"Duplicates : {duplicates_removed}"
    )

    print()


# ============================================================
# CLEANING LOG
# ============================================================

log_df = pd.DataFrame(log)

log_file = (
    output_file /
    "five_datasets_cleaning_log_group2.csv"
)

log_df.to_csv(
    log_file,
    index=False
)


# ============================================================
# COMPLETION MESSAGE
# ============================================================

print("==========================================")
print("DATA CLEANING COMPLETED")
print("==========================================")

print(
    f"Cleaned files: {output_file}"
)

print(
    f"Cleaning log : {log_file}"
)

print()

print(
    log_df.to_string(index=False)
)