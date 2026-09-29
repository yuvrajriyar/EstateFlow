# Forecast experiment: ZIP-level Zillow indices

This is a reproducible forecasting experiment, separate from the observed-data Power BI report. It estimates future **ZIP-level ZHVI (home-value index)** and **ZORI (monthly rent index)** values at 3, 6, and 12 months. It does not forecast an individual property's sale price, lease, household income, profit, or investment return. Dates and results below describe the source snapshot ending **2026-07-31**; they will change when the source files change.

## Run and outputs

From the repository root, with the existing pipeline and local PostgreSQL running:

```bash
uv run python src/estateflow/run_forecast.py
```

For a reproducible experiment directly from the two committed Zillow source files, without PostgreSQL:

```bash
uv run python src/estateflow/run_forecast.py --source raw
uv run python -m unittest discover -s tests -v
```

The script writes `data/processed/forecasts/forecast_evaluation.csv` (six metric-horizon evaluations) and `data/processed/forecasts/zip_market_forecasts.csv` (ZIP, as-of month, target month, metric, model, estimate, and empirical 80% and 95% bounds). These generated CSVs are ignored by Git. The database mode reads the validated `intermediate.zip_month_housing` view. The raw mode joins observed ZIP-month pairs directly and is used to verify the project without a live database. This experiment is intentionally **not** called by `run_pipeline.py`.

To replace the separate experimental forecast table in PostgreSQL for Power BI, after reviewing the six evaluation rows:

```bash
uv run python src/estateflow/run_forecast.py --publish-to-db
docker compose exec -T postgres psql -U estateflow_user -d estateflow -v ON_ERROR_STOP=1 -f - < sql/quality/check_zip_market_forecasts.sql
```

The load happens in one transaction: if `COPY`, table checks or row-count reconciliation fails, the previous forecast snapshot remains. The `marts.zip_market_forecast_display` view gives Power BI reader-friendly index and model names. Open the editable Power BI Project, refresh the semantic model, and inspect the **Forecast Experiment** page. Its charts require one ZIP selection; without it, the record table remains browsable. This authored Power BI integration must be visually and functionally verified in Power BI Desktop before treating the report as released.

## What the model does

| Step | Rule |
| --- | --- |
| Eligibility | ZIP has both observed indices for 24 consecutive months ending in the as-of month. Do not fill gaps. |
| Baseline | Carry the latest index forward unchanged. |
| Candidate | Fit a straight line to log(index) over those 24 months; anchor at the latest observation, cap monthly log slope at ±0.02, and damp each future month's slope by `0.85^month`. |
| Model choice | Compare methods on older target months, then require the trend to beat the baseline by at least 10% in median absolute percentage error on a separate validation period. Otherwise use the baseline. |
| Uncertainty | Pool absolute log errors from an earlier calibration period by metric and horizon. Add/subtract their empirical 80th and 95th quantiles on the log scale, then exponentiate. Bounds remain positive. |
| Final check | Evaluate the chosen model on later targets, without using these target values in the code's model-choice or interval-calibration steps. |

For horizon \(h\), the point projection is a *future index level*, not a prediction that every home or advertised rent will follow the ZIP index. The flat benchmark is deliberately strong: a complex model needs to demonstrate added value, not merely produce a changing line.

The four target-month windows, relative to the source's latest month \(T\), are: selection \(T-59\) to \(T-48\), validation \(T-47\) to \(T-36\), calibration \(T-35\) to \(T-24\), and final evaluation \(T-11\) to \(T\). Each prediction at target month \(t\) uses an origin at \(t-h\) and only index values observed by that origin. For the July 2026 snapshot these correspond to August 2021–July 2022, August 2022–July 2023, August 2023–July 2024, and August 2025–July 2026. The latest calibration target precedes the earliest final-evaluation origin, even at 12 months. An individual ZIP is scored only when its target exists and its origin has 24 complete months. Historical ZIP-month test cases overlap and should not be treated as independent samples.

## Results on the July 2026 snapshot

The source join contained **455,832 observed ZIP-month pairs across 8,508 ZIPs**. The latest observed joined month has 8,499 ZIPs, but only **5,236** have the complete recent history required for all six forecast rows: **31,416 forecast rows** (5,236 ZIPs × two indices × three horizons). The remainder are left unforecasted, not silently filled. All values below are retrospective, not proven future accuracy.

| Index | Horizon | Published model | Median absolute % error | Flat baseline error | 80% empirical coverage | 95% empirical coverage |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| ZHVI | 3 months | Flat | 0.67% | 0.67% | 92.6% | 98.6% |
| ZHVI | 6 months | Flat | 1.24% | 1.24% | 92.3% | 98.3% |
| ZHVI | 12 months | Flat | 2.30% | 2.30% | 92.6% | 98.4% |
| ZORI | 3 months | Flat | 1.45% | 1.45% | 78.1% | 92.8% |
| ZORI | 6 months | Flat | 1.85% | 1.85% | 81.5% | 94.5% |
| ZORI | 12 months | Damped log trend | 1.75% | 2.43% | 89.9% | 98.0% |

The 12-month ZHVI trend achieved only a small earlier validation improvement and did not pass the 10% material-gain rule. In the final retrospective period its median error was 2.33%, versus 2.30% for the flat benchmark. The 12-month ZORI candidate did pass the rule and outperformed the benchmark in the final retrospective period. A developer inspected these historical outcomes while refining this experiment, so the final period is **not** a pristine external, prospective validation set. Treat the comparison as exploratory and rerun on future source vintages.

### September 2026 source-vintage check

On 28 September, we downloaded the ZIP ZHVI and ZORI files that Zillow last modified on 16 September. Both now end at **2026-08-31**. Run the uncommitted, newer files without replacing the repository's July snapshot:

```bash
uv run python src/estateflow/run_forecast.py --source raw \
  --zori-path /path/to/new/Zip_zori_uc_sfrcondomfr_sm_month.csv \
  --zhvi-path /path/to/new/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv \
  --output-dir data/processed/forecast_new_vintage
```

The new join has **462,410 observed ZIP-month pairs across 8,424 ZIPs** and produces **31,566 projections for 5,261 eligible ZIPs**. Model choice is unchanged. In the new file's *retrospective* evaluation, median errors are 0.65%, 1.18% and 2.24% for 3-, 6- and 12-month ZHVI, and 1.46%, 1.86% and 1.74% for ZORI. The 12-month ZORI flat baseline has 2.41% median error. These are **re-estimates on a revised historical series**, not prospective validation of July projections: the July 3-month forecast targets October 2026, the 6-month forecast January 2027, and the 12-month forecast July 2027.

Historical values also moved. Among **7,799 ZIPs** with joined July values in both vintages, every July value differed at the stored precision; the median absolute revision was **1.064% for ZHVI** and **2.051% for ZORI**. The original joined July set had 8,499 ZIPs; the newer vintage has 7,865 for July and 8,421 for August. This change in coverage and values means the next analysis should retain source-vintage metadata and assess prospective errors only when the target months arrive. The newer files and outputs were kept outside the Git-tracked source snapshot for this check.

For example, ZIP **01002 (Amherst, MA)** had a July 2026 observed ZORI index of about **$2,430 per month**. The experiment's July 2027 ZORI point estimate is **$2,487**, with a pooled empirical 80% band of **$2,373–$2,607** and a 95% band of **$2,302–$2,687**. This illustrates how to read a forecast row; it is not a rent quote for a particular home. The point estimate × 12, approximately **$29,845**, is only an annualised gross-rent *run rate at that future monthly level*.

## How to read the intervals and income question

The bands are **empirical prediction intervals** for the future *index level*, not confidence intervals for a population mean. “80%” and “95%” refer to the calibration quantiles; check the realised coverage above instead of assuming a guarantee. Coverage differs from labels because ZIPs, months, and vintage revisions are dependent and market conditions shift. These pooled bands do not reflect each ZIP's own risk and can be poorly calibrated for unusual or thinly observed markets.

Monthly ZORI × 12 can be shown as an **annualised gross-rent run rate**. It is not a forecast of the next 12 months of collected rent and **not net income**. Estimating property income would additionally require units, actual contract rent, occupancy, expenses, taxes, financing, and property-level assumptions. Do not relabel ZORI or annualised gross rent as income in the dashboard.

## Limitations and next release gate

- Zillow's historical index series can be revised. Backtesting today's full revised file is not a true vintage-by-vintage simulation of what an analyst knew at each past date.
- The first-pass model uses only index history, not interest rates, local supply, seasonality, policy, or economic drivers. The 24-month complete-history rule makes availability non-representative of all US ZIP codes.
- Tests pool repeated ZIP-month forecast errors. Empirical quantiles have **no distribution-free coverage guarantee** here; unusual ZIPs and a new regime may behave differently.
- A 12-month target is evaluated using later realised observations; a displayed future estimate remains hypothetical until those observations exist.
- Before releasing the authored Power BI page: validate output against a database run, test on a new Zillow release, confirm the imported table and filter behaviour in Power BI Desktop, and audit the interval labels and tooltips with a reader unfamiliar with housing data. The observed pages remain separate from the experimental page.

## References

- [Zillow Research data and methodologies](https://www.zillow.com/research/data/), for the source indices and revision considerations.
- [Forecasting: Principles and Practice, time-series cross-validation](https://otexts.com/fpp3/tscv.html), for rolling-origin evaluation.
- [Forecasting: Principles and Practice, prediction intervals](https://otexts.com/fpp3/prediction-intervals.html), for distinguishing point forecasts from uncertainty bands.
