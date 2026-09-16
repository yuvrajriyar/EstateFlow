from pathlib import Path

import pandas as pd


file_path = Path("data/raw/Zip_zori_uc_sfrcondomfr_sm_month.csv")

zori_wide = pd.read_csv(
    file_path,
    dtype={"RegionName": "string"},
)

metadata_columns = zori_wide.columns[:9].tolist()
month_columns = zori_wide.columns[9:].tolist()

zori_long = zori_wide.melt(
    id_vars=metadata_columns,
    value_vars=month_columns,
    var_name="month",
    value_name="rent",
)
zori_long = zori_long.dropna(subset=["rent"]).reset_index(drop=True)

zori_long["month"] = pd.to_datetime(zori_long["month"])
assert zori_long["rent"].notna().all(), "Missing rent values remain"
assert (zori_long["rent"] > 0).all(), "Non-positive rent value found"
assert not zori_long.duplicated(
    subset=["RegionName", "month"]
).any(), "Duplicate ZIP-month found"
assert zori_long["RegionName"].str.fullmatch(
    r"\d{5}"
).all(), "Invalid ZIP code found"
print(f"Wide shape: {zori_wide.shape}")
print(f"Long shape after removing missing rents: {zori_long.shape}")
print(f"Missing rents remaining: {zori_long['rent'].isna().sum()}")
print(f"Month data type: {zori_long['month'].dtype}")
print(f"First month: {zori_long['month'].min()}")
print(f"Last month: {zori_long['month'].max()}")
print(zori_long[["RegionName", "month", "rent"]].head(10))
print("All validation checks passed.")

assert zori_long["StateName"].equals(
    zori_long["State"]
), "State columns do not match"

zori_long = zori_long.drop(columns=["StateName"])

zori_long = zori_long.rename(
    columns={
        "RegionID": "region_id",
        "SizeRank": "size_rank",
        "RegionName": "zip_code",
        "RegionType": "region_type",
        "State": "state",
        "City": "city",
        "Metro": "metro",
        "CountyName": "county_name",
        "rent": "zori_usd",
    }
)
print(f"Final columns: {zori_long.columns.tolist()}")

output_path = Path("data/processed/zori_zip_month.csv")
zori_long.to_csv(output_path, index=False)

print(f"Saved {len(zori_long):,} rows to {output_path}")