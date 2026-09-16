import os
from io import StringIO
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv


SOURCE_FILE = Path(
    "data/raw/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)

CHUNK_SIZE = 500

DATABASE_COLUMNS = [
    "region_id",
    "size_rank",
    "zip_code",
    "region_type",
    "state",
    "city",
    "metro",
    "county_name",
    "month",
    "zhvi_usd",
]

COPY_SQL = """
COPY staging.zhvi_zip_month (
    region_id,
    size_rank,
    zip_code,
    region_type,
    state,
    city,
    metro,
    county_name,
    month,
    zhvi_usd
)
FROM STDIN
WITH (FORMAT CSV)
"""


def transform_chunk(zhvi_chunk: pd.DataFrame) -> pd.DataFrame:
    metadata_columns = zhvi_chunk.columns[:9].tolist()
    month_columns = zhvi_chunk.columns[9:].tolist()

    zhvi_long = zhvi_chunk.melt(
        id_vars=metadata_columns,
        value_vars=month_columns,
        var_name="month",
        value_name="home_value",
    )

    zhvi_long = zhvi_long.dropna(
        subset=["home_value"]
    ).reset_index(drop=True)

    zhvi_long["month"] = pd.to_datetime(
        zhvi_long["month"]
    ).dt.date

    assert zhvi_long["home_value"].notna().all(), (
        "Missing home values remain"
    )
    assert (zhvi_long["home_value"] > 0).all(), (
        "Non-positive home value found"
    )
    assert not zhvi_long.duplicated(
        subset=["RegionName", "month"]
    ).any(), "Duplicate ZIP-month found"
    assert zhvi_long["RegionName"].str.fullmatch(
        r"\d{5}"
    ).all(), "Invalid ZIP code found"
    assert zhvi_long["StateName"].equals(
        zhvi_long["State"]
    ), "State columns do not match"

    zhvi_long = zhvi_long.drop(columns=["StateName"])

    zhvi_long = zhvi_long.rename(
        columns={
            "RegionID": "region_id",
            "SizeRank": "size_rank",
            "RegionName": "zip_code",
            "RegionType": "region_type",
            "State": "state",
            "City": "city",
            "Metro": "metro",
            "CountyName": "county_name",
            "home_value": "zhvi_usd",
        }
    )

    return zhvi_long[DATABASE_COLUMNS]


def connect_to_database() -> psycopg.Connection:
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
            f"Missing environment variables: {missing_variables}"
        )

    return psycopg.connect(
        host="localhost",
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def main() -> None:
    chunk_reader = pd.read_csv(
        SOURCE_FILE,
        dtype={"RegionName": "string"},
        chunksize=CHUNK_SIZE,
    )

    total_loaded = 0

    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE TABLE staging.zhvi_zip_month"
            )

        for chunk_number, zhvi_chunk in enumerate(
            chunk_reader,
            start=1,
        ):
            zhvi_long = transform_chunk(zhvi_chunk)

            csv_buffer = StringIO()
            zhvi_long.to_csv(
                csv_buffer,
                index=False,
                header=False,
                na_rep="",
            )
            csv_buffer.seek(0)

            with connection.cursor() as cursor:
                with cursor.copy(COPY_SQL) as copy:
                    copy.write(csv_buffer.getvalue())

            total_loaded += len(zhvi_long)

            print(
                f"Chunk {chunk_number}: "
                f"loaded {len(zhvi_long):,} rows "
                f"({total_loaded:,} total)"
            )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) "
                "FROM staging.zhvi_zip_month"
            )
            database_rows = cursor.fetchone()[0]

        if database_rows != total_loaded:
            raise RuntimeError(
                "Reconciliation failed: "
                f"Python loaded {total_loaded:,} rows, "
                f"but PostgreSQL contains {database_rows:,}"
            )

    print(
        f"Successfully loaded and reconciled "
        f"{total_loaded:,} ZHVI records."
    )


if __name__ == "__main__":
    main()