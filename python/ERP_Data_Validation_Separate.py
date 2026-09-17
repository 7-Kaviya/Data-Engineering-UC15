import pandas as pd

# Read cleaned datasets
employee = pd.read_csv("../silver/cleansing/cleaned_datasets/employee_data_cleaned.csv")
finance = pd.read_csv("../silver/cleansing/cleaned_datasets/finance_data_cleaned.csv")
inventory = pd.read_csv("../silver/cleansing/cleaned_datasets/inventory_data_cleaned.csv")
manufacturing = pd.read_csv("../silver/cleansing/cleaned_datasets/manufacturing_data_cleaned.csv")
warehouse = pd.read_csv("../silver/cleansing/cleaned_datasets/warehouse_data_cleaned.csv")

# Collects every check as a dict; turned into the summary CSV at the end
results = []

def log_check(dataset, check_name, error_count):
    results.append({
        "Dataset": dataset,
        "Validation_Check": check_name,
        "Error_Count": int(error_count),
        "Status": "PASS" if error_count == 0 else "FAIL"
    })


# ------------------------------------------------
# EMPLOYEE VALIDATION
# ------------------------------------------------

print("\nEMPLOYEE VALIDATION")
print("-------------------")

missing = employee.isnull().sum().sum()
print("Missing values:", missing)
log_check("Employee", "Missing values", missing)

dupes = employee.duplicated().sum()
print("Duplicate rows:", dupes)
log_check("Employee", "Duplicate rows", dupes)

if "age" in employee.columns:
    invalid_age = ((employee["age"] < 18) | (employee["age"] > 100)).sum()
    print("Invalid age:", invalid_age)
    log_check("Employee", "Invalid age", invalid_age)

if "salary" in employee.columns:
    neg_salary = (employee["salary"] < 0).sum()
    print("Negative salary:", neg_salary)
    log_check("Employee", "Negative salary", neg_salary)


# ------------------------------------------------
# FINANCE VALIDATION
# ------------------------------------------------

print("\nFINANCE VALIDATION")
print("------------------")

missing = finance.isnull().sum().sum()
print("Missing values:", missing)
log_check("Finance", "Missing values", missing)

dupes = finance.duplicated().sum()
print("Duplicate rows:", dupes)
log_check("Finance", "Duplicate rows", dupes)

if "transaction_id" in finance.columns:
    invalid_id = (finance["transaction_id"] <= 0).sum()
    print("Invalid transaction ID:", invalid_id)
    log_check("Finance", "Invalid transaction ID", invalid_id)

if "transaction_amount" in finance.columns:
    neg_amount = (finance["transaction_amount"] < 0).sum()
    print("Negative transaction amount:", neg_amount)
    log_check("Finance", "Negative transaction amount", neg_amount)


# ------------------------------------------------
# INVENTORY VALIDATION
# ------------------------------------------------

print("\nINVENTORY VALIDATION")
print("--------------------")

missing = inventory.isnull().sum().sum()
print("Missing values:", missing)
log_check("Inventory", "Missing values", missing)

dupes = inventory.duplicated().sum()
print("Duplicate rows:", dupes)
log_check("Inventory", "Duplicate rows", dupes)

if "price_per_unit" in inventory.columns:
    neg_price = (inventory["price_per_unit"] < 0).sum()
    print("Negative price:", neg_price)
    log_check("Inventory", "Negative price", neg_price)

monthly_columns = [
    "jan_demand", "feb_demand", "mar_demand", "apr_demand",
    "may_demand", "jun_demand", "jul_demand", "aug_demand",
    "sep_demand", "oct_demand", "nov_demand", "dec_demand"
]

for column in monthly_columns:
    if column in inventory.columns:
        neg_demand = (inventory[column] < 0).sum()
        print(f"Negative {column}:", neg_demand)
        log_check("Inventory", f"Negative {column}", neg_demand)


# ------------------------------------------------
# MANUFACTURING VALIDATION
# ------------------------------------------------

print("\nMANUFACTURING VALIDATION")
print("------------------------")

missing = manufacturing.isnull().sum().sum()
print("Missing values:", missing)
log_check("Manufacturing", "Missing values", missing)

dupes = manufacturing.duplicated().sum()
print("Duplicate rows:", dupes)
log_check("Manufacturing", "Duplicate rows", dupes)

if "material_used" in manufacturing.columns:
    neg_material = (manufacturing["material_used"] < 0).sum()
    print("Negative material used:", neg_material)
    log_check("Manufacturing", "Negative material used", neg_material)

if "energy_consumption" in manufacturing.columns:
    neg_energy = (manufacturing["energy_consumption"] < 0).sum()
    print("Negative energy consumption:", neg_energy)
    log_check("Manufacturing", "Negative energy consumption", neg_energy)

if "processing_time" in manufacturing.columns:
    invalid_time = (manufacturing["processing_time"] <= 0).sum()
    print("Invalid processing time:", invalid_time)
    log_check("Manufacturing", "Invalid processing time", invalid_time)


# ------------------------------------------------
# WAREHOUSE VALIDATION
# ------------------------------------------------

print("\nWAREHOUSE VALIDATION")
print("--------------------")

missing = warehouse.isnull().sum().sum()
print("Missing values:", missing)
log_check("Warehouse", "Missing values", missing)

dupes = warehouse.duplicated().sum()
print("Duplicate rows:", dupes)
log_check("Warehouse", "Duplicate rows", dupes)

if "stock_level" in warehouse.columns:
    neg_stock = (warehouse["stock_level"] < 0).sum()
    print("Negative stock:", neg_stock)
    log_check("Warehouse", "Negative stock", neg_stock)

if "unit_price" in warehouse.columns:
    neg_price = (warehouse["unit_price"] < 0).sum()
    print("Negative unit price:", neg_price)
    log_check("Warehouse", "Negative unit price", neg_price)


# ------------------------------------------------
# WRITE SUMMARY REPORT
# ------------------------------------------------

summary = pd.DataFrame(results)
summary.to_csv("../silver/validation/separate_validation_summary.csv", index=False)

print("\nVALIDATION COMPLETED")
print(f"Summary written to ../silver/validation/separate_validation_summary.csv ({len(summary)} checks)")
