CREATE SCHEMA IF NOT EXISTS marts;

CREATE OR REPLACE VIEW marts.latest_zip_market_metrics AS
SELECT
    region_id,
    size_rank,
    zip_code,
    region_type,
    state,
    city,
    metro,
    county_name,
    month,
    zhvi_usd,
    zori_usd,
    annualised_rent_usd,
    gross_rent_to_value_pct,
    previous_year_zhvi_usd,
    previous_year_zori_usd,
    home_value_yoy_pct,
    rent_yoy_pct,
    has_yoy_comparison
FROM marts.zip_month_market_metrics
WHERE month = (
    SELECT MAX(month)
    FROM marts.zip_month_market_metrics
);