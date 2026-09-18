CREATE SCHEMA IF NOT EXISTS marts;

CREATE OR REPLACE VIEW marts.zip_month_market_metrics AS
SELECT
    current_data.region_id,
    current_data.size_rank,
    current_data.zip_code,
    current_data.region_type,
    current_data.state,
    current_data.city,
    current_data.metro,
    current_data.county_name,
    current_data.month,
    current_data.zhvi_usd,
    current_data.zori_usd,

    current_data.zori_usd * 12
        AS annualised_rent_usd,

    (current_data.zori_usd * 12 / current_data.zhvi_usd) * 100
        AS gross_rent_to_value_pct,

    previous_data.zhvi_usd
        AS previous_year_zhvi_usd,

    previous_data.zori_usd
        AS previous_year_zori_usd,

    (
        (current_data.zhvi_usd - previous_data.zhvi_usd)
        / previous_data.zhvi_usd
    ) * 100 AS home_value_yoy_pct,

    (
        (current_data.zori_usd - previous_data.zori_usd)
        / previous_data.zori_usd
    ) * 100 AS rent_yoy_pct,

    previous_data.zip_code IS NOT NULL
        AS has_yoy_comparison

FROM intermediate.zip_month_housing AS current_data

LEFT JOIN intermediate.zip_month_housing AS previous_data
    ON current_data.zip_code = previous_data.zip_code
    AND previous_data.month = (
        DATE_TRUNC('month', current_data.month)
        - INTERVAL '1 year'
        + INTERVAL '1 month'
        - INTERVAL '1 day'
    )::date;