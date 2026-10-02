# EstateFlow web dashboard

[Open the live dashboard](https://yuvrajriyar.vercel.app/projects/estateflow/dashboard).

The public React/Next.js dashboard is deployed within the portfolio. It uses the
same reviewed August 2026 Zillow source vintage as the PostgreSQL mart and
Power BI report. No account, database or Power BI licence is required.

The five views cover national overview, market exploration, ZIP detail,
experimental forecasts and definitions. Controls include state/metro/city
filters, sortable and searchable market tables, geographic benchmarks,
historical ranges, 80%/95% forecast intervals and CSV exports. Reload resets
filters. The data is a fixed snapshot, not a real-time database connection.

[Web implementation](https://github.com/yuvrajriyar/portfolio-website/tree/main/app/projects/estateflow/dashboard)

[Static data exports](https://github.com/yuvrajriyar/portfolio-website/tree/main/public/data/estateflow)

[Reconciliation exporter](https://github.com/yuvrajriyar/portfolio-website/blob/main/scripts/export-estateflow.py)

The exporter verifies the pinned uncompressed source hashes, ZIP/month grain,
positive values, exact twelve-month growth comparisons, 462,410 matched
observations, 8,421 latest ZIPs and 31,566 forecast rows. Medians are calculated
across individual ZIPs with equal weight, not across group medians. History
and forecasts load as state files on demand. Missing growth remains blank.

Latest national medians reconcile to $386,450 home value, $1,824 monthly rent,
5.62% gross rent-to-value, +0.72% home growth and +2.54% rent growth. These are
ZIP-level medians, not population-weighted national indices. Projections are
experimental Zillow-index estimates, not property-level investment returns.
