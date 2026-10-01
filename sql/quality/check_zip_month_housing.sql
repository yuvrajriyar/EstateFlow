-- Summary of the combined housing dataset
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT zip_code) AS zip_codes,
    MIN(month) AS first_month,
    MAX(month) AS last_month,
    MIN(zhvi_usd) AS minimum_home_value,
    MAX(zhvi_usd) AS maximum_home_value,
    MIN(zori_usd) AS minimum_rent,
    MAX(zori_usd) AS maximum_rent
FROM intermediate.zip_month_housing;

-- Required values must never be missing
SELECT
    COUNT(*) AS missing_required_values
FROM intermediate.zip_month_housing
WHERE zip_code IS NULL
   OR month IS NULL
   OR zhvi_usd IS NULL
   OR zori_usd IS NULL;

-- Home values and rents must be positive
SELECT
    COUNT(*) AS invalid_values
FROM intermediate.zip_month_housing
WHERE zhvi_usd <= 0
   OR zori_usd <= 0;

-- Each ZIP-month combination must occur only once
SELECT
    COUNT(*) AS duplicate_zip_months
FROM (
    SELECT
        zip_code,
        month
    FROM intermediate.zip_month_housing
    GROUP BY
        zip_code,
        month
    HAVING COUNT(*) > 1
) AS duplicates;

-- Fail the pipeline on failed data checks. Diagnostic queries above remain readable.
DO $quality$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM intermediate.zip_month_housing) THEN
        RAISE EXCEPTION 'quality gate check_zip_month_housing: joined model is empty';
    END IF;
    IF EXISTS (SELECT 1 FROM intermediate.zip_month_housing WHERE zip_code IS NULL OR month IS NULL OR zhvi_usd IS NULL OR zori_usd IS NULL OR zhvi_usd <= 0 OR zori_usd <= 0) THEN
        RAISE EXCEPTION 'quality gate check_zip_month_housing: missing or invalid joined values';
    END IF;
    IF EXISTS (SELECT 1 FROM intermediate.zip_month_housing GROUP BY zip_code, month HAVING COUNT(*) > 1) THEN
        RAISE EXCEPTION 'quality gate check_zip_month_housing: duplicate ZIP-month keys';
    END IF;
END
$quality$;
