CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.zhvi_zip_month (
    region_id INTEGER NOT NULL,
    size_rank INTEGER,
    zip_code VARCHAR(5) NOT NULL,
    region_type TEXT NOT NULL,
    state CHAR(2) NOT NULL,
    city TEXT,
    metro TEXT,
    county_name TEXT,
    month DATE NOT NULL,
    zhvi_usd NUMERIC(15, 6) NOT NULL,

    PRIMARY KEY (zip_code, month),

    CHECK (zip_code ~ '^[0-9]{5}$'),
    CHECK (zhvi_usd > 0)
);