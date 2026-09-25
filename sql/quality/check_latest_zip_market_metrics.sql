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