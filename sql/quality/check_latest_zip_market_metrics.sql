-- The snapshot should contain every row from the latest mart month.
WITH latest_month AS (
    SELECT MAX(month) AS month
    FROM marts.zip_month_market_metrics
)
SELECT
    (
        SELECT COUNT(*)
        FROM marts.zip_month_market_metrics
        WHERE month = (SELECT month FROM latest_month)
    ) AS expected_rows,
    (
        SELECT COUNT(*)
        FROM marts.latest_zip_market_metrics
    ) AS snapshot_rows;


-- Every snapshot row must come from one common latest month.
SELECT
    COUNT(DISTINCT month) AS distinct_months,
    MIN(month) AS first_month,
    MAX(month) AS last_month
FROM marts.latest_zip_market_metrics;


-- Dashboard-critical fields must not be missing.
SELECT
    COUNT(*) AS missing_required_values
FROM marts.latest_zip_market_metrics
WHERE region_id IS NULL
   OR zip_code IS NULL
   OR state IS NULL
   OR month IS NULL
   OR zhvi_usd IS NULL
   OR zori_usd IS NULL
   OR annualised_rent_usd IS NULL
   OR gross_rent_to_value_pct IS NULL
   OR has_yoy_comparison IS NULL;


-- Values used by the dashboard must be positive.
SELECT
    COUNT(*) AS invalid_metric_values
FROM marts.latest_zip_market_metrics
WHERE zhvi_usd <= 0
   OR zori_usd <= 0
   OR annualised_rent_usd <= 0
   OR gross_rent_to_value_pct <= 0;


-- Each ZIP code should appear exactly once.
SELECT
    COUNT(*) AS duplicate_zip_codes
FROM (
    SELECT zip_code
    FROM marts.latest_zip_market_metrics
    GROUP BY zip_code
    HAVING COUNT(*) > 1
) AS duplicates;


-- The YoY flag must agree with the prior-year fields and calculations.
SELECT
    COUNT(*) AS inconsistent_yoy_flags
FROM marts.latest_zip_market_metrics
WHERE (
    has_yoy_comparison
    AND (
        previous_year_zhvi_usd IS NULL
        OR previous_year_zori_usd IS NULL
        OR home_value_yoy_pct IS NULL
        OR rent_yoy_pct IS NULL
    )
)
OR (
    NOT has_yoy_comparison
    AND (
        previous_year_zhvi_usd IS NOT NULL
        OR previous_year_zori_usd IS NOT NULL
        OR home_value_yoy_pct IS NOT NULL
        OR rent_yoy_pct IS NOT NULL
    )
);

-- Fail the pipeline on failed data checks. Diagnostic queries above remain readable.
DO $quality$
DECLARE
    expected_rows BIGINT;
    snapshot_rows BIGINT;
BEGIN
    SELECT COUNT(*) INTO expected_rows FROM marts.zip_month_market_metrics WHERE month = (SELECT MAX(month) FROM marts.zip_month_market_metrics);
    SELECT COUNT(*) INTO snapshot_rows FROM marts.latest_zip_market_metrics;
    IF expected_rows = 0 OR expected_rows <> snapshot_rows THEN
        RAISE EXCEPTION 'quality gate check_latest_zip_market_metrics: latest snapshot count differs (expected %, got %)', expected_rows, snapshot_rows;
    END IF;
    IF (SELECT COUNT(DISTINCT month) FROM marts.latest_zip_market_metrics) <> 1
       OR (SELECT MIN(month) FROM marts.latest_zip_market_metrics) IS DISTINCT FROM (SELECT MAX(month) FROM marts.zip_month_market_metrics) THEN
        RAISE EXCEPTION 'quality gate check_latest_zip_market_metrics: snapshot is empty, mixed-vintage, or stale';
    END IF;
    IF EXISTS (SELECT 1 FROM marts.latest_zip_market_metrics WHERE region_id IS NULL OR zip_code IS NULL OR state IS NULL OR month IS NULL OR zhvi_usd IS NULL OR zori_usd IS NULL OR annualised_rent_usd IS NULL OR gross_rent_to_value_pct IS NULL OR has_yoy_comparison IS NULL OR zhvi_usd <= 0 OR zori_usd <= 0 OR annualised_rent_usd <= 0 OR gross_rent_to_value_pct <= 0) THEN
        RAISE EXCEPTION 'quality gate check_latest_zip_market_metrics: missing or invalid dashboard fields';
    END IF;
    IF EXISTS (SELECT 1 FROM marts.latest_zip_market_metrics GROUP BY zip_code HAVING COUNT(*) > 1) THEN
        RAISE EXCEPTION 'quality gate check_latest_zip_market_metrics: duplicate ZIP codes';
    END IF;
    IF EXISTS (
        SELECT 1 FROM marts.latest_zip_market_metrics
        WHERE (has_yoy_comparison AND (previous_year_zhvi_usd IS NULL OR previous_year_zori_usd IS NULL OR home_value_yoy_pct IS NULL OR rent_yoy_pct IS NULL))
           OR (NOT has_yoy_comparison AND (previous_year_zhvi_usd IS NOT NULL OR previous_year_zori_usd IS NOT NULL OR home_value_yoy_pct IS NOT NULL OR rent_yoy_pct IS NOT NULL))
           OR (has_yoy_comparison AND (ABS(home_value_yoy_pct - ((zhvi_usd - previous_year_zhvi_usd) / previous_year_zhvi_usd * 100)) > 0.000001 OR ABS(rent_yoy_pct - ((zori_usd - previous_year_zori_usd) / previous_year_zori_usd * 100)) > 0.000001))
    ) THEN RAISE EXCEPTION 'quality gate check_latest_zip_market_metrics: inconsistent year-over-year fields'; END IF;
END
$quality$;
