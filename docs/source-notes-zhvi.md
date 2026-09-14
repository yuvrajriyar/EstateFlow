# Zillow ZHVI Source Notes

## Dataset selected

* Dataset: Zillow Home Value Index, All Homes
* Geography: ZIP Code
* Version: Smoothed and seasonally adjusted
* Unit: US dollars
* Filename: `Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`
* Source: https://www.zillow.com/research/data/

## What ZHVI measures

ZHVI is Zillow’s estimate of the typical home value within a geographic market. It covers homes in the middle portion of the market and includes single-family residences, condominiums and co-ops. It is a modelled market estimate, not an individual property valuation, sale-price average or future forecast.

## Source structure

Each row represents one ZIP code. The first nine columns identify the location. The remaining 319 columns contain monthly home values.

The file is in wide format because every month has a separate column. EstateFlow will eventually reshape it into long format, where each row represents one ZIP code during one month.

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

ZIP codes must be stored as text because ZIP codes beginning with zero can lose that zero when treated as numbers.

## Date coverage

The file contains monthly values from January 2000 through July 2026.

## Data-quality concerns

* Approximately 23% of the possible monthly values are missing.
* Coverage may vary between ZIP codes and time periods.
* Spreadsheet software may incorrectly convert ZIP codes into numbers and remove leading zeros.
* ZHVI is a modelled estimate rather than a record of actual property sales.
* The raw CSV is approximately 123 MB, so it cannot be committed normally to GitHub.
* The dataset may be revised when Zillow updates its methodology or source data.

## Suitability for EstateFlow

This dataset appears suitable as EstateFlow’s first source because it provides monthly historical home-value estimates at the ZIP-code level. It supports the proposed ZIP × month analytical grain after being reshaped from wide to long format.

Its suitability is provisional. We still need to evaluate missing-value coverage, confirm Zillow’s usage terms and determine whether compatible ZIP-level rent and economic data are available.
