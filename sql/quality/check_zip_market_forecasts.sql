-- Readable diagnostics after `run_forecast.py --publish-to-db`.
SELECT
    COUNT(*) AS forecast_rows,
    COUNT(DISTINCT zip_code) AS eligible_zip_codes,
    COUNT(DISTINCT as_of_month) AS source_vintages,
    MIN(as_of_month) AS as_of_month,
    MIN(forecast_month) AS first_forecast_month,
    MAX(forecast_month) AS last_forecast_month
FROM marts.zip_market_forecasts;

SELECT
    metric,
    horizon_months,
    COUNT(*) AS zip_codes,
    COUNT(DISTINCT model) AS model_count,
    COUNT(*) FILTER (WHERE NOT (
        lower_95_usd <= lower_80_usd AND
        lower_80_usd <= estimate_usd AND
        estimate_usd <= upper_80_usd AND
        upper_80_usd <= upper_95_usd
    )) AS invalid_bounds
FROM marts.zip_market_forecasts
GROUP BY metric, horizon_months
ORDER BY metric, horizon_months;

SELECT COUNT(*) AS display_rows FROM marts.zip_market_forecast_display;
