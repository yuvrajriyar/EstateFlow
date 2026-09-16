SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT zip_code) AS zip_codes,
    MIN(month) AS first_month,
    MAX(month) AS last_month,
    MIN(zhvi_usd) AS minimum_value,
    MAX(zhvi_usd) AS maximum_value
FROM staging.zhvi_zip_month;

SELECT COUNT(*) AS missing_required_values
FROM staging.zhvi_zip_month
WHERE zip_code IS NULL
   OR month IS NULL
   OR zhvi_usd IS NULL;

SELECT COUNT(*) AS invalid_home_values
FROM staging.zhvi_zip_month
WHERE zhvi_usd <= 0;

SELECT COUNT(*) AS duplicate_zip_months
FROM (
    SELECT zip_code, month
    FROM staging.zhvi_zip_month
    GROUP BY zip_code, month
    HAVING COUNT(*) > 1
) AS duplicates;