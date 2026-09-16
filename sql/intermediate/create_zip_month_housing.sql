CREATE SCHEMA IF NOT EXISTS intermediate;

CREATE OR REPLACE VIEW intermediate.zip_month_housing AS
SELECT
    zhvi.region_id,
    zhvi.size_rank,
    zhvi.zip_code,
    zhvi.region_type,
    zhvi.state,
    zhvi.city,
    zhvi.metro,
    zhvi.county_name,
    zhvi.month,
    zhvi.zhvi_usd,
    zori.zori_usd
FROM staging.zhvi_zip_month AS zhvi
INNER JOIN staging.zori_zip_month AS zori
    ON zhvi.zip_code = zori.zip_code
    AND zhvi.month = zori.month;