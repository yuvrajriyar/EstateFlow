CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.zori_zip_month (
    region_id INTEGER NOT NULL,
    size_rank INTEGER,
    zip_code VARCHAR(5) NOT NULL,
    region_type TEXT NOT NULL,
    state CHAR(2) NOT NULL,
    city TEXT,
    metro TEXT,
    county_name TEXT,
    month DATE NOT NULL,
    zori_usd NUMERIC(12, 6) NOT NULL,

    PRIMARY KEY (zip_code, month),

    CHECK (zip_code ~ '^[0-9]{5}$'),
    CHECK (zori_usd > 0)
);