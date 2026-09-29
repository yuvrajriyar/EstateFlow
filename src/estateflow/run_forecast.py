"""Run the separately validated EstateFlow forecasting experiment.

From the repository root:
    uv run python src/estateflow/run_forecast.py
    uv run python src/estateflow/run_forecast.py --source raw

This intentionally does not run as part of the established ETL pipeline.
Review the evaluation before using any projection in Power BI.
"""

import argparse
import csv
import os
from io import StringIO
from pathlib import Path

from forecasting import (
    ZHVI_PATH,
    ZORI_PATH,
    evaluate_and_forecast,
    load_database_joined,
    load_raw_joined,
)


FORECAST_TABLE_SQL = Path("sql/marts/create_zip_market_forecasts.sql")


def publish_to_database(forecasts: list[dict]) -> None:
    """Replace one complete forecast snapshot atomically after validation."""
    import psycopg
    from dotenv import load_dotenv

    load_dotenv()
    required = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_PORT")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing database settings: {', '.join(missing)}")
    if not forecasts:
        raise ValueError("Refusing to publish an empty forecast")
    columns = tuple(forecasts[0])
    content = StringIO()
    writer = csv.DictWriter(content, fieldnames=columns)
    writer.writeheader()
    writer.writerows(forecasts)
    with psycopg.connect(
        host="localhost",
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(FORECAST_TABLE_SQL.read_text(encoding="utf-8"))
            cursor.execute("TRUNCATE TABLE marts.zip_market_forecasts")
            with cursor.copy(
                "COPY marts.zip_market_forecasts ("
                + ", ".join(columns)
                + ") FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
            ) as copy:
                copy.write(content.getvalue())
            cursor.execute("SELECT COUNT(*) FROM marts.zip_market_forecasts")
            if cursor.fetchone()[0] != len(forecasts):
                raise RuntimeError("Forecast database row count did not reconcile")
    print(f"Published {len(forecasts):,} forecast rows to marts.zip_market_forecasts.")


def save_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No records to save to {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("database", "raw"), default="database")
    parser.add_argument("--zori-path", type=Path, default=ZORI_PATH)
    parser.add_argument("--zhvi-path", type=Path, default=ZHVI_PATH)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed/forecasts")
    )
    parser.add_argument(
        "--publish-to-db", action="store_true",
        help="Atomically replace the experimental PostgreSQL forecast table",
    )
    args = parser.parse_args()
    if args.publish_to_db and args.source != "database":
        parser.error("--publish-to-db requires --source database so observed and forecast vintages agree")
    if args.source == "database" and (args.zori_path != ZORI_PATH or args.zhvi_path != ZHVI_PATH):
        parser.error("Source paths are only used with --source raw")

    series = (
        load_database_joined()
        if args.source == "database"
        else load_raw_joined(args.zori_path, args.zhvi_path)
    )
    observations = sum(len(item.values) for item in series)
    print(f"Loaded {observations:,} matched ZIP-month observations across {len(series):,} ZIPs.")
    evaluations, forecasts = evaluate_and_forecast(series)

    for row in evaluations:
        print(
            f"{row['metric']} {row['horizon_months']:2d}m "
            f"model={row['model']:<17} "
            f"test n={row['test_cases']:,} "
            f"median error={row['test_median_absolute_pct_error']:.2f}% "
            f"flat={row['test_flat_median_absolute_pct_error']:.2f}% "
            f"80% coverage={row['test_80_coverage_pct']:.1f}% "
            f"95% coverage={row['test_95_coverage_pct']:.1f}%"
        )
    save_csv(args.output_dir / "forecast_evaluation.csv", evaluations)
    save_csv(args.output_dir / "zip_market_forecasts.csv", forecasts)
    if args.publish_to_db:
        publish_to_database(forecasts)
    print(f"Saved {len(forecasts):,} forecast rows to {args.output_dir}.")
    print("These are experimental Zillow-index projections, not investment advice or property-level income.")


if __name__ == "__main__":
    main()
