# Zillow ZORI Source Notes

## Dataset selected

* Dataset: Zillow Observed Rent Index, All Homes
* Geography: ZIP Code
* Version: Smoothed
* Unit: Monthly rent in US dollars
* Filename: `Zip_zori_uc_sfrcondomfr_sm_month.csv`
* Source: https://www.zillow.com/research/data/

## What ZORI measures

ZORI estimates the typical observed market-rate rent within a geographic area. It uses listed rents from the middle portion of the rental market and weights them to represent the wider rental housing stock, rather than only the properties currently advertised.

The All Homes dataset covers single-family residences, condominiums and multi-family rental properties.

## Source structure

Each row represents one ZIP code. The first nine columns identify the location, followed by 139 monthly rent columns.

The file is in wide format because each month appears as a separate column. EstateFlow will eventually reshape it into long format, where each row represents one ZIP code during one month.

## Geographic fields

The file contains:

* Zillow RegionID
* ZIP code
* City
* County
* Metropolitan area
* State
* Region type
* Size rank

ZIP codes must be stored as text to preserve leading zeros.

## Date coverage

The file contains monthly rent estimates from January 2015 through July 2026.

## Data-quality concerns

* The dataset includes 8,543 ZIP codes, substantially fewer than the 26,269 ZIP codes in the ZHVI dataset.
* Approximately 61.5% of all possible historical monthly values are missing.
* Rent histories begin at different times for different ZIP codes.
* The median ZIP code has approximately 45 months of available rent data.
* July 2026 data is available for 8,534 of the 8,543 included ZIP codes.
* Rent-based analysis must be limited to ZIP-month combinations where both ZORI and ZHVI values exist.
* ZORI is a modelled index based on observed listings, not a complete record of every lease signed.

## Suitability for EstateFlow

This dataset is suitable for EstateFlow because it provides ZIP-level monthly rent estimates that can be compared with ZIP-level home values.

Its coverage is narrower and less historically complete than ZHVI. EstateFlow must therefore measure coverage, preserve missing values and avoid presenting unavailable rent estimates as zero. The first version can focus on ZIP codes with recent values in both datasets.
