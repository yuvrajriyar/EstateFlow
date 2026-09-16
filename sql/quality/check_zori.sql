SELECT COUNT(*) AS missing_required_values
FROM staging.zori_zip_month
WHERE zip_code IS NULL
   OR month IS NULL
   OR zori_usd IS NULL;

SELECT COUNT(*) AS invalid_rents
FROM staging.zori_zip_month
WHERE zori_usd <= 0;

SELECT COUNT(*) AS duplicate_zip_months
FROM (
    SELECT zip_code, month
    FROM staging.zori_zip_month
    GROUP BY zip_code, month
    HAVING COUNT(*) > 1
) AS duplicates;