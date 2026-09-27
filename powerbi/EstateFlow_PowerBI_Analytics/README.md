# EstateFlow Power BI report

This folder contains the editable Power BI Project (PBIP) for EstateFlow. It is a source-controlled report and semantic model, not a published Power BI Service link.

## Pages

1. **National Housing Market**: state, metro, and city slicers; latest-month headline measures; national home-value and rent history; year-over-year change and coverage; and a sortable ZIP-level market table.
2. **Market Explorer**: compare state-level value growth with gross rent-to-value, review rent momentum, and compare metro-level measures.
3. **How to Read the Dashboard**: plain-language metric definitions, a recommended way to read the report, and a reminder that gross rent-to-value is a screening measure rather than a net investment return.

## Open and refresh

1. Start the EstateFlow PostgreSQL service and run the pipeline from the repository root. See the main [README](../../README.md#run-the-pipeline).
2. Open `EstateFlow_Dashboard.pbip` in Power BI Desktop.
3. On first refresh, configure the PostgreSQL connector for `localhost:5432`, database `estateflow`, using the credentials in your local `.env` file.
4. Refresh the model to load the current marts.

The PBIP model references `marts.zip_month_market_metrics` and `marts.latest_zip_market_metrics`. The PostgreSQL password is not stored in the report; Power BI prompts for local credentials. Generated `.pbi/cache.abf` data and machine-specific settings are excluded from version control.

## Data recency

The screenshots in `../../docs/images/` show the July 2026 Zillow data snapshot. Refresh the local model before relying on the figures for current analysis.
