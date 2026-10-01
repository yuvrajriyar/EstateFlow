"""Exercise the real pipeline SQL gates against a disposable PostgreSQL database.

Set ESTATEFLOW_TEST_DSN to run. The GitHub Actions workflow provides a temporary
PostgreSQL 17 service; local unit runs skip these integration tests without a DSN.
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

import psycopg
from psycopg import ClientCursor


ROOT = Path(__file__).resolve().parents[1]
DSN = os.getenv("ESTATEFLOW_TEST_DSN")
QUALITY_FILES = (
    "check_zori.sql",
    "check_zhvi.sql",
    "check_zip_month_housing.sql",
    "check_zip_month_market_metrics.sql",
    "check_latest_zip_market_metrics.sql",
)
STAGING_FILES = (
    "create_zori_table.sql",
    "create_zhvi_table.sql",
)
MODEL_FILES = (
    "intermediate/create_zip_month_housing.sql",
    "marts/create_zip_month_market_metrics.sql",
    "marts/create_latest_zip_market_metrics.sql",
)


@unittest.skipUnless(DSN, "PostgreSQL integration service is not configured")
class PipelineQualityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = psycopg.connect(DSN, autocommit=True)
        self._execute("DROP SCHEMA IF EXISTS staging CASCADE")
        self._execute("DROP SCHEMA IF EXISTS intermediate CASCADE")
        self._execute("DROP SCHEMA IF EXISTS marts CASCADE")
        for sql_file in STAGING_FILES:
            self._execute((ROOT / "sql/staging" / sql_file).read_text())
        rows = []
        for zip_code, region_id, city, metro, home_values, rents in (
            ("93730", 1001, "Fresno", "Fresno, CA", (600000, 620000), (2400, 2500)),
            ("01002", 1002, "Amherst", "Springfield, MA", (500000, 510000), (2200, 2250)),
        ):
            for month, home, rent in zip(("2025-08-31", "2026-08-31"), home_values, rents):
                rows.append((region_id, 1, zip_code, "zipcode", "CA" if zip_code == "93730" else "MA", city, metro, None, month, home, rent))
        with self.connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    "INSERT INTO staging.zhvi_zip_month "
                    "(region_id,size_rank,zip_code,region_type,state,city,metro,county_name,month,zhvi_usd) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", row[:10]
                )
                cursor.execute(
                    "INSERT INTO staging.zori_zip_month "
                    "(region_id,size_rank,zip_code,region_type,state,city,metro,county_name,month,zori_usd) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", row[:9] + (row[10],)
                )
        for sql_file in MODEL_FILES:
            self._execute((ROOT / "sql" / sql_file).read_text())

    def tearDown(self) -> None:
        self.connection.close()

    def _execute(self, statement: str) -> None:
        with self.connection.cursor(row_factory=ClientCursor) as cursor:
            cursor.execute(statement)

    def _run_quality(self, filename: str) -> None:
        self._execute((ROOT / "sql/quality" / filename).read_text())

    def test_valid_fixture_passes_every_pipeline_quality_file(self) -> None:
        for filename in QUALITY_FILES:
            with self.subTest(filename=filename):
                self._run_quality(filename)

    def test_invalid_or_empty_layers_stop_their_pipeline_gate(self) -> None:
        invalidations = (
            ("check_zori.sql", "TRUNCATE staging.zori_zip_month"),
            ("check_zhvi.sql", "TRUNCATE staging.zhvi_zip_month"),
            (
                "check_zip_month_housing.sql",
                "TRUNCATE staging.zhvi_zip_month, staging.zori_zip_month",
            ),
            (
                "check_zip_month_market_metrics.sql",
                "TRUNCATE staging.zhvi_zip_month, staging.zori_zip_month",
            ),
            (
                "check_latest_zip_market_metrics.sql",
                "TRUNCATE staging.zhvi_zip_month, staging.zori_zip_month",
            ),
        )
        for filename, invalidate in invalidations:
            with self.subTest(filename=filename):
                self._execute(invalidate)
                with self.assertRaises(psycopg.errors.RaiseException) as failure:
                    self._run_quality(filename)
                self.assertIn("quality gate", str(failure.exception))


if __name__ == "__main__":
    unittest.main()
