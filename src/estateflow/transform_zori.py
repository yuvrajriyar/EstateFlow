from io import StringIO
import os
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv


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
assert zori_long["StateName"].equals(
    zori_long["State"]
), "State columns do not match"

print(f"Wide shape: {zori_wide.shape}")
print(f"Long shape after removing missing rents: {zori_long.shape}")
print(f"First month: {zori_long['month'].min()}")
print(f"Last month: {zori_long['month'].max()}")
print("All transformation validation checks passed.")

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

target_columns = [
    "region_id",
    "size_rank",
    "zip_code",
    "region_type",
    "state",
    "city",
    "metro",
    "county_name",
    "month",
    "zori_usd",
]

zori_long = zori_long[target_columns]

load_dotenv()

required_variables = [
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_PORT",
]

missing_variables = [
    variable
    for variable in required_variables
    if not os.getenv(variable)
]

if missing_variables:
    raise RuntimeError(
        "Missing environment variables: "
        + ", ".join(missing_variables)
    )

csv_buffer = StringIO()
zori_long.to_csv(
    csv_buffer,
    index=False,
    header=False,
    na_rep="",
)
csv_buffer.seek(0)

with psycopg.connect(
    host="localhost",
    port=os.environ["POSTGRES_PORT"],
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
) as connection:
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE staging.zori_zip_month;")

        with cursor.copy(
            """
            COPY staging.zori_zip_month (
                region_id,
                size_rank,
                zip_code,
                region_type,
                state,
                city,
                metro,
                county_name,
                month,
                zori_usd
            )
            FROM STDIN
            WITH (FORMAT CSV)
            """
        ) as copy:
            copy.write(csv_buffer.getvalue())

        cursor.execute(
            "SELECT COUNT(*) FROM staging.zori_zip_month;"
        )
        database_row_count = cursor.fetchone()[0]

expected_row_count = len(zori_long)

if database_row_count != expected_row_count:
    raise RuntimeError(
        "Row-count reconciliation failed: "
        f"expected {expected_row_count:,}, "
        f"loaded {database_row_count:,}"
    )

print(
    f"Successfully loaded and reconciled "
    f"{database_row_count:,} ZORI records."
)