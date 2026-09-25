# EstateFlow Power BI Dashboard Blueprint

## Dashboard purpose

EstateFlow helps users compare United States housing markets by combining
monthly home-value and rent data at the ZIP-code level.

The dashboard should help answer:

1. What does the current housing market look like?
2. Which ZIP codes have the strongest rent-to-value ratios?
3. Where are home values and rents growing fastest?
4. How has an individual ZIP code changed over time?
5. How do selected markets compare?

---

## Data sources

### Historical market mart

PostgreSQL view:

`marts.zip_month_market_metrics`

Grain:

One row per ZIP code per month.

Purpose:

- Historical trend charts
- Year-over-year analysis
- ZIP-code history
- Market comparisons over time

### Latest market snapshot

PostgreSQL view:

`marts.latest_zip_market_metrics`

Grain:

One row per ZIP code for the latest common month.

Purpose:

- KPI cards
- Current market rankings
- Maps
- Latest market comparison tables

---

## Page 1: National Market Overview

### Purpose

Provide an executive summary of the latest available housing market.

### Filters

- State
- Metro
- County
- City
- ZIP code
- Has YoY comparison

### KPI cards

- ZIP codes covered
- Median home value
- Median monthly rent
- Median gross rent-to-value percentage
- Median home-value YoY growth
- Median rent YoY growth
- Latest data month

### Visuals

1. United States ZIP-code market map
   - Location: ZIP code
   - Colour: gross rent-to-value percentage
   - Tooltip: city, state, home value, rent, and YoY growth

2. Top 10 rent-to-value markets
   - Horizontal bar chart
   - Exclude missing values
   - Show ZIP code, city, and state

3. Home-value YoY growth distribution
   - Column chart using growth bands

4. Rent YoY growth distribution
   - Column chart using growth bands

5. Latest market table
   - ZIP code
   - City
   - State
   - Home value
   - Monthly rent
   - Gross rent-to-value percentage
   - Home-value YoY percentage
   - Rent YoY percentage

---

## Page 2: Market Explorer

### Purpose

Allow users to compare affordability, rent levels, growth, and potential
rental-market yield across ZIP codes.

### Filters

- State
- Metro
- County
- City
- Minimum home value
- Maximum home value
- Has YoY comparison

### Visuals

1. Home value versus monthly rent
   - Scatter plot
   - X-axis: home value
   - Y-axis: monthly rent
   - Colour: state
   - Tooltip: ZIP, city, rent-to-value percentage, and YoY growth

2. Home-value growth versus rent growth
   - Scatter plot
   - X-axis: home-value YoY percentage
   - Y-axis: rent YoY percentage
   - Only include rows with YoY comparisons

3. Top and bottom market rankings
   - Rent-to-value percentage
   - Home-value growth
   - Rent growth

4. Detailed comparison table
   - Conditional formatting for growth and rent-to-value metrics

---

## Page 3: ZIP Market Detail

### Purpose

Show the historical performance of one selected ZIP code.

### Required selection

- One ZIP code

### KPI cards

- Current home value
- Current monthly rent
- Current rent-to-value percentage
- Home-value YoY growth
- Rent YoY growth

### Visuals

1. Home-value trend
   - Month on X-axis
   - ZHVI on Y-axis

2. Monthly-rent trend
   - Month on X-axis
   - ZORI on Y-axis

3. Rent-to-value trend
   - Month on X-axis
   - Gross rent-to-value percentage on Y-axis

4. Market information
   - ZIP code
   - City
   - State
   - Metro
   - County

---

## Metric definitions

### Annualised rent

Monthly ZORI multiplied by 12.

This is a simple annualised estimate and not observed annual rental income.

### Gross rent-to-value percentage

Annualised rent divided by ZHVI, multiplied by 100.

This is a screening metric. It is not net rental yield, cap rate, or profit
because it excludes vacancies, taxes, insurance, maintenance, financing,
management costs, and transaction costs.

### Home-value YoY growth

Percentage change in ZHVI compared with the same ZIP code and calendar month
one year earlier.

### Rent YoY growth

Percentage change in ZORI compared with the same ZIP code and calendar month
one year earlier.

### Missing YoY comparison

A YoY comparison is unavailable when the same ZIP code does not have both
home-value and rent observations for the matching month one year earlier.

---

## Visual design

- Dark navy background
- Off-white primary text
- Muted grey secondary text
- Gold accent for selected markets
- Green for positive growth
- Red for negative growth
- Minimal borders
- Consistent currency and percentage formatting
- Clear notes explaining metric limitations