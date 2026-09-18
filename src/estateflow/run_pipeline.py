import os
import subprocess
import sys
import argparse
from pathlib import Path


from dotenv import load_dotenv


STAGING_SQL_FILES = [
    Path("sql/staging/create_zori_table.sql"),
    Path("sql/staging/create_zhvi_table.sql"),
]

TRANSFORM_SCRIPTS = [
    Path("src/estateflow/transform_zori.py"),
    Path("src/estateflow/transform_zhvi.py"),
]

MODEL_SQL_FILES = [
    Path("sql/intermediate/create_zip_month_housing.sql"),
    Path("sql/marts/create_zip_month_market_metrics.sql"),
]

QUALITY_SQL_FILES = [
    Path("sql/quality/check_zori.sql"),
    Path("sql/quality/check_zhvi.sql"),
    Path("sql/quality/check_zip_month_housing.sql"),
    Path("sql/quality/check_zip_month_market_metrics.sql"),
]


def get_database_settings() -> tuple[str, str]:
    load_dotenv()

    required_variables = [
        "POSTGRES_DB",
        "POSTGRES_USER",
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

    return (
        os.environ["POSTGRES_DB"],
        os.environ["POSTGRES_USER"],
    )


def run_sql_file(
    sql_file: Path,
    database: str,
    user: str,
) -> None:
    print(f"\nRunning SQL file: {sql_file}")

    sql = sql_file.read_text()

    subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            user,
            "-d",
            database,
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            "-",
        ],
        input=sql,
        text=True,
        check=True,
    )


def run_python_script(script: Path) -> None:
    print(f"\nRunning Python script: {script}")

    subprocess.run(
        [sys.executable, str(script)],
        check=True,
    )

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the EstateFlow data pipeline."
    )

    parser.add_argument(
        "--skip-loads",
        action="store_true",
        help=(
            "Skip the ZORI and ZHVI transformations and use "
            "the data already stored in PostgreSQL."
        ),
    )

    return parser.parse_args()
def main() -> None:
    arguments = parse_arguments()
    database, user = get_database_settings()

    print("Starting EstateFlow pipeline.")

    for sql_file in STAGING_SQL_FILES:
        run_sql_file(sql_file, database, user)

    if arguments.skip_loads:
        print("\nSkipping source-data loads.")
    else:
        for transform_script in TRANSFORM_SCRIPTS:
            run_python_script(transform_script)

    for sql_file in MODEL_SQL_FILES:
        run_sql_file(sql_file, database, user)

    for sql_file in QUALITY_SQL_FILES:
        run_sql_file(sql_file, database, user)

    print("\nEstateFlow pipeline completed successfully.")


if __name__ == "__main__":
    main()