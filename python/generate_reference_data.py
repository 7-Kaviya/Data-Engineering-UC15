"""
Generate the two reference (lookup) files used by the warehouse:
  DimDate.csv  - one row per calendar day, 2011-01-01 to 2027-12-31
  DimMonth.csv - months 1-12 (used for the monthly demand in Inventory)

These are not taken from a source system; they are calendar data. The Pentaho
transformations 'Load DimDate' and 'Load DimMonth' load them into PostgreSQL.

Run from the python/ folder:  python3 generate_reference_data.py
"""
import os
import pandas as pd

OUT = "../silver/cleansing/reference_data"
os.makedirs(OUT, exist_ok=True)

dates = pd.date_range("2011-01-01", "2027-12-31", freq="D")
dim_date = pd.DataFrame({
    "date_key": dates.strftime("%Y%m%d").astype(int),
    "full_date": dates.strftime("%Y-%m-%d"),
    "year": dates.year,
    "quarter": dates.quarter,
    "month": dates.month,
    "month_name": dates.strftime("%B"),
    "day": dates.day,
    "day_of_week": dates.dayofweek + 1,          # 1 = Monday ... 7 = Sunday
    "day_name": dates.strftime("%A"),
    "is_weekend": dates.dayofweek >= 5,
    "week_of_year": dates.isocalendar().week.astype(int).values,
})
dim_date.to_csv(f"{OUT}/DimDate.csv", index=False)

months = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
pd.DataFrame({"month_key": range(1, 13), "month_name": months}).to_csv(f"{OUT}/DimMonth.csv", index=False)

print(f"DimDate.csv : {len(dim_date)} rows")
print("DimMonth.csv: 12 rows")
