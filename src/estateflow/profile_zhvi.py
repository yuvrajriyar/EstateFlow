from pathlib import Path

import pandas as pd


file_path = Path(
    "data/raw/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)

zhvi = pd.read_csv(
    file_path,
    dtype={"RegionName": "string"},
)

metadata_columns = zhvi.columns[:9]
month_columns = zhvi.columns[9:]
monthly_values = zhvi[month_columns]

missing_values = monthly_values.isna().sum().sum()
total_values = monthly_values.size
missing_percentage = missing_values / total_values * 100

duplicate_zips = zhvi["RegionName"].duplicated().sum()
latest_month_count = zhvi[month_columns[-1]].notna().sum()

print(f"Rows: {zhvi.shape[0]}")
print(f"Columns: {zhvi.shape[1]}")
print(f"Metadata columns: {metadata_columns.tolist()}")
print(f"First month: {month_columns[0]}")
print(f"Last month: {month_columns[-1]}")
print(f"Unique ZIP codes: {zhvi['RegionName'].nunique()}")
print(f"ZIP 08701 exists: {'08701' in zhvi['RegionName'].values}")
print(f"Missing monthly values: {missing_values:,}")
print(f"Missing percentage: {missing_percentage:.2f}%")
print(f"Duplicate ZIP codes: {duplicate_zips}")
print(f"ZIP codes with latest-month data: {latest_month_count:,}")