CREATE SCHEMA IF NOT EXISTS marts;

CREATE OR REPLACE VIEW marts.zip_month_market_metrics AS
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
    zori_usd * 12 AS annualised_rent_usd,
    (zori_usd * 12 / zhvi_usd) * 100
        AS gross_rent_to_value_pct
FROM intermediate.zip_month_housing;
