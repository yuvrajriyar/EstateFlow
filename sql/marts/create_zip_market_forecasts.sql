CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE IF NOT EXISTS marts.zip_market_forecasts (
    zip_code VARCHAR(5) NOT NULL CHECK (zip_code ~ '^[0-9]{5}$'),
    state CHAR(2) NOT NULL,
    city TEXT,
    metro TEXT,
    metric TEXT NOT NULL CHECK (metric IN ('zhvi_usd', 'zori_usd')),
    as_of_month DATE NOT NULL,
    forecast_month DATE NOT NULL,
    horizon_months INTEGER NOT NULL CHECK (horizon_months IN (3, 6, 12)),
    model TEXT NOT NULL CHECK (model IN ('flat', 'damped_log_trend')),
    estimate_usd NUMERIC(16, 2) NOT NULL,
    lower_80_usd NUMERIC(16, 2) NOT NULL,
    upper_80_usd NUMERIC(16, 2) NOT NULL,
    lower_95_usd NUMERIC(16, 2) NOT NULL,
    upper_95_usd NUMERIC(16, 2) NOT NULL,
    PRIMARY KEY (zip_code, as_of_month, horizon_months, metric),
    CHECK (forecast_month > as_of_month),
    CHECK (
        0 < lower_95_usd AND
        lower_95_usd <= lower_80_usd AND
        lower_80_usd <= estimate_usd AND
        estimate_usd <= upper_80_usd AND
        upper_80_usd <= upper_95_usd
    )
);

COMMENT ON TABLE marts.zip_market_forecasts IS
    'Experimental ZIP-level Zillow index projections, separate from observed housing marts.';

CREATE OR REPLACE VIEW marts.zip_market_forecast_display AS
SELECT
    zip_code,
    state,
    city,
    metro,
    CASE metric
        WHEN 'zhvi_usd' THEN 'Home value index'
        ELSE 'Monthly rent index'
    END AS index_name,
    as_of_month,
    forecast_month,
    horizon_months,
    CASE model
        WHEN 'flat' THEN 'Last observed value'
        ELSE 'Damped trend'
    END AS method,
    estimate_usd,
    lower_80_usd,
    upper_80_usd,
    lower_95_usd,
    upper_95_usd
FROM marts.zip_market_forecasts;
