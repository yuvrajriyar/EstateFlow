# EstateFlow Power BI report

This folder contains the editable Power BI Project (PBIP) for EstateFlow. It is a source-controlled report and semantic model, not a published Power BI Service link.

## Pages

1. **National Housing Market**: state, metro, and city slicers; latest-month headline measures; national home-value and rent history; year-over-year change and coverage; and a sortable ZIP-level market table.
2. **Market Explorer**: compare state-level value growth with gross rent-to-value, review rent momentum, and compare metro-level measures.
3. **ZIP Detail**: selected ZIP history, growth measures, and state benchmarks.
4. **Forecast Experiment**: separately labelled Zillow index projections at 3, 6 and 12 months, with empirical 80% chart bounds and 80%/95% record bounds. Select one ZIP for the two charts.
5. **How to Read the Dashboard**: plain-language metric definitions, a recommended way to read the report, and a reminder that gross rent-to-value is a screening measure rather than a net investment return.

## Open and refresh

1. From the repository root, run `docker compose up -d`, then `uv sync` and `uv run python src/estateflow/run_pipeline.py`. See the main [README](../../README.md#run-the-pipeline).
2. Open `EstateFlow_Dashboard.pbip` in Power BI Desktop.
3. On first refresh, configure the PostgreSQL connector for `localhost:5432`, database `estateflow`, using the credentials in your local `.env` file.
4. Refresh the model to load the current marts.

For the forecast page, review `data/processed/forecasts/forecast_evaluation.csv`, then run `uv run python src/estateflow/run_forecast.py --publish-to-db` from the repository root. This creates `marts.zip_market_forecasts` and `marts.zip_market_forecast_display`. Run the forecast quality query, refresh Power BI, choose one ZIP, and verify that both charts and the six forecast rows match the exported CSV. Keep the observed pages separate from the projections.

The PBIP model references `marts.zip_month_market_metrics`, `marts.latest_zip_market_metrics`, and the separately published `marts.zip_market_forecast_display`. The PostgreSQL password is not stored in the report; Power BI prompts for local credentials. Generated `.pbi/cache.abf` data and machine-specific settings are excluded from version control.

## Data recency

The screenshots in `../../docs/images/` are historical July 2026 previews. The checked-in source now runs through August 2026. Rebuild the database and refresh Power BI before relying on displayed values.
