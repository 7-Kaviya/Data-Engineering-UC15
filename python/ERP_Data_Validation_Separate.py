import pandas as pd

# Read cleaned datasets
employee = pd.read_csv(r"C:/Users/USER/Data-Enginering-UC15/silver/cleansing/cleaned_datasets/employee_data_cleaned.csv")
finance = pd.read_csv(r"C:/Users/USER/Data-Enginering-UC15/silver/cleansing/cleaned_datasets/finance_data_cleaned.csv")
inventory = pd.read_csv(r"C:/Users/USER/Data-Enginering-UC15/silver/cleansing/cleaned_datasets/inventory_data_cleaned.csv")
manufacturing = pd.read_csv(r"C:/Users/USER/Data-Enginering-UC15/silver/cleansing/cleaned_datasets/manufacturing_data_cleaned.csv")
warehouse = pd.read_csv(r"C:/Users/USER/Data-Enginering-UC15/silver/cleansing/cleaned_datasets/warehouse_data_cleaned.csv")


# ------------------------------------------------
# EMPLOYEE VALIDATION
# ------------------------------------------------

print("\nEMPLOYEE VALIDATION")
print("-------------------")

print("Missing values:", employee.isnull().sum().sum())
print("Duplicate rows:", employee.duplicated().sum())

if "age" in employee.columns:
    print("Invalid age:", ((employee["age"] < 18) | (employee["age"] > 100)).sum())

if "salary" in employee.columns:
    print("Negative salary:", (employee["salary"] < 0).sum())


# ------------------------------------------------
# FINANCE VALIDATION
# ------------------------------------------------

print("\nFINANCE VALIDATION")
print("------------------")

print("Missing values:", finance.isnull().sum().sum())
print("Duplicate rows:", finance.duplicated().sum())

if "transaction_id" in finance.columns:
    print("Invalid transaction ID:",
          (finance["transaction_id"] <= 0).sum())

if "transaction_amount" in finance.columns:
    print("Negative transaction amount:",
          (finance["transaction_amount"] < 0).sum())


# ------------------------------------------------
# INVENTORY VALIDATION
# ------------------------------------------------

print("\nINVENTORY VALIDATION")
print("--------------------")

print("Missing values:", inventory.isnull().sum().sum())
print("Duplicate rows:", inventory.duplicated().sum())

if "price_per_unit" in inventory.columns:
    print("Negative price:",
          (inventory["price_per_unit"] < 0).sum())

monthly_columns = [
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
    "dec_demand"
]

for column in monthly_columns:
    if column in inventory.columns:
        print(
            f"Negative {column}:",
            (inventory[column] < 0).sum()
        )


# ------------------------------------------------
# MANUFACTURING VALIDATION
# ------------------------------------------------

print("\nMANUFACTURING VALIDATION")
print("------------------------")

print("Missing values:", manufacturing.isnull().sum().sum())
print("Duplicate rows:", manufacturing.duplicated().sum())

if "material_used" in manufacturing.columns:
    print("Negative material used:",
          (manufacturing["material_used"] < 0).sum())

if "energy_consumption" in manufacturing.columns:
    print("Negative energy consumption:",
          (manufacturing["energy_consumption"] < 0).sum())

if "processing_time" in manufacturing.columns:
    print("Invalid processing time:",
          (manufacturing["processing_time"] <= 0).sum())


# ------------------------------------------------
# WAREHOUSE VALIDATION
# ------------------------------------------------

print("\nWAREHOUSE VALIDATION")
print("--------------------")

print("Missing values:", warehouse.isnull().sum().sum())
print("Duplicate rows:", warehouse.duplicated().sum())

if "stock_level" in warehouse.columns:
    print("Negative stock:",
          (warehouse["stock_level"] < 0).sum())

if "unit_price" in warehouse.columns:
    print("Negative unit price:",
          (warehouse["unit_price"] < 0).sum())


print("\nVALIDATION COMPLETED")