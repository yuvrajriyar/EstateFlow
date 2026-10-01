-- Confirm that the mart retains every intermediate record
SELECT
    (SELECT COUNT(*)
     FROM intermediate.zip_month_housing) AS intermediate_rows,
    (SELECT COUNT(*)
     FROM marts.zip_month_market_metrics) AS mart_rows;

-- Required values must not be missing
SELECT
    COUNT(*) AS missing_required_values
FROM marts.zip_month_market_metrics
WHERE zip_code IS NULL
   OR month IS NULL
   OR zhvi_usd IS NULL
   OR zori_usd IS NULL
   OR annualised_rent_usd IS NULL
   OR gross_rent_to_value_pct IS NULL;

-- Calculated values must be positive
SELECT
    COUNT(*) AS invalid_metric_values
FROM marts.zip_month_market_metrics
WHERE annualised_rent_usd <= 0
   OR gross_rent_to_value_pct <= 0;

-- Recalculate the metrics and check for discrepancies
SELECT
    COUNT(*) AS calculation_mismatches
FROM marts.zip_month_market_metrics
WHERE ABS(annualised_rent_usd - (zori_usd * 12)) > 0.000001
   OR ABS(
       gross_rent_to_value_pct
       - ((zori_usd * 12 / zhvi_usd) * 100)
   ) > 0.000001;

-- Each row must still represent one ZIP code in one month
SELECT
    COUNT(*) AS duplicate_zip_months
FROM (
    SELECT
        zip_code,
        month
    FROM marts.zip_month_market_metrics
    GROUP BY
        zip_code,
        month
    HAVING COUNT(*) > 1
) AS duplicates;

-- The availability flag must agree with the YoY fields
SELECT
    COUNT(*) AS inconsistent_yoy_flags
FROM marts.zip_month_market_metrics
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
-- Recalculate YoY metrics and check their accuracy
SELECT
    COUNT(*) AS yoy_calculation_mismatches
FROM marts.zip_month_market_metrics
WHERE has_yoy_comparison
  AND (
      ABS(
          home_value_yoy_pct
          - (
              (zhvi_usd - previous_year_zhvi_usd)
              / previous_year_zhvi_usd
          ) * 100
      ) > 0.000001
      OR
      ABS(
          rent_yoy_pct
          - (
              (zori_usd - previous_year_zori_usd)
              / previous_year_zori_usd
          ) * 100
      ) > 0.000001
  );

-- Fail the pipeline on failed data checks. Diagnostic queries above remain readable.
DO $quality$
DECLARE
    intermediate_rows BIGINT;
    mart_rows BIGINT;
BEGIN
    SELECT COUNT(*) INTO intermediate_rows FROM intermediate.zip_month_housing;
    SELECT COUNT(*) INTO mart_rows FROM marts.zip_month_market_metrics;
    IF mart_rows = 0 OR intermediate_rows <> mart_rows THEN
        RAISE EXCEPTION 'quality gate check_zip_month_market_metrics: row counts differ (intermediate %, mart %)', intermediate_rows, mart_rows;
    END IF;
    IF EXISTS (SELECT 1 FROM marts.zip_month_market_metrics WHERE zip_code IS NULL OR month IS NULL OR zhvi_usd IS NULL OR zori_usd IS NULL OR annualised_rent_usd IS NULL OR gross_rent_to_value_pct IS NULL OR annualised_rent_usd <= 0 OR gross_rent_to_value_pct <= 0) THEN
        RAISE EXCEPTION 'quality gate check_zip_month_market_metrics: missing or invalid market metrics';
    END IF;
    IF EXISTS (SELECT 1 FROM marts.zip_month_market_metrics GROUP BY zip_code, month HAVING COUNT(*) > 1) THEN
        RAISE EXCEPTION 'quality gate check_zip_month_market_metrics: duplicate ZIP-month keys';
    END IF;
    IF EXISTS (
        SELECT 1 FROM marts.zip_month_market_metrics
        WHERE ABS(annualised_rent_usd - zori_usd * 12) > 0.000001
           OR ABS(gross_rent_to_value_pct - (zori_usd * 12 / zhvi_usd * 100)) > 0.000001
    ) THEN RAISE EXCEPTION 'quality gate check_zip_month_market_metrics: calculated metric mismatch'; END IF;
    IF EXISTS (
        SELECT 1 FROM marts.zip_month_market_metrics
        WHERE (has_yoy_comparison AND (previous_year_zhvi_usd IS NULL OR previous_year_zori_usd IS NULL OR home_value_yoy_pct IS NULL OR rent_yoy_pct IS NULL))
           OR (NOT has_yoy_comparison AND (previous_year_zhvi_usd IS NOT NULL OR previous_year_zori_usd IS NOT NULL OR home_value_yoy_pct IS NOT NULL OR rent_yoy_pct IS NOT NULL))
    ) THEN RAISE EXCEPTION 'quality gate check_zip_month_market_metrics: inconsistent year-over-year flags'; END IF;
    IF EXISTS (
        SELECT 1 FROM marts.zip_month_market_metrics WHERE has_yoy_comparison AND (
            ABS(home_value_yoy_pct - ((zhvi_usd - previous_year_zhvi_usd) / previous_year_zhvi_usd * 100)) > 0.000001
            OR ABS(rent_yoy_pct - ((zori_usd - previous_year_zori_usd) / previous_year_zori_usd * 100)) > 0.000001
        )
    ) THEN RAISE EXCEPTION 'quality gate check_zip_month_market_metrics: year-over-year calculation mismatch'; END IF;
END
$quality$;
