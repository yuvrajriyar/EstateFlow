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

-- Fail the pipeline on failed data checks. Diagnostic queries above remain readable.
DO $quality$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM staging.zori_zip_month) THEN
        RAISE EXCEPTION 'quality gate check_zori: staging table is empty';
    END IF;
    IF EXISTS (SELECT 1 FROM staging.zori_zip_month WHERE zip_code IS NULL OR month IS NULL OR zori_usd IS NULL OR zori_usd <= 0) THEN
        RAISE EXCEPTION 'quality gate check_zori: missing or non-positive ZIP-month rent values';
    END IF;
    IF EXISTS (SELECT 1 FROM staging.zori_zip_month GROUP BY zip_code, month HAVING COUNT(*) > 1) THEN
        RAISE EXCEPTION 'quality gate check_zori: duplicate ZIP-month keys';
    END IF;
END
$quality$;
