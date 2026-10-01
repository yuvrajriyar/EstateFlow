# Current verified data snapshot

The published Zillow source files run through **31 August 2026**. They were retrieved on **1 October 2026 at 20:28 UTC** and were last modified by Zillow on **16 September 2026**. Source URLs, observation dates, and CSV hashes are recorded in [source_manifest.json](../data/raw/source_manifest.json).

The full pipeline completed successfully on the author's local PostgreSQL database on 1 October 2026. All required-value, positive-value, duplicate-grain, reconciliation, metric-calculation, and year-over-year checks reported zero failures. The forecast step then published its separate experimental table.

| Dataset or output | Records | ZIP coverage |
| --- | ---: | ---: |
| ZHVI staging observations | 6,482,537 | 26,268 |
| ZORI staging observations | 463,419 | 8,459 |
| Matched historical ZIP-month mart | 462,410 | 8,424 |
| Latest matched snapshot, 2026-08-31 | 8,421 | 8,421 |
| Experimental forecasts | 31,566 | 5,261 eligible ZIPs |

Forecast coverage is smaller because each eligible ZIP needs a complete recent history for both indices and all three horizons. Six forecast rows are published per eligible ZIP.

## Retrospective forecast evaluation

These results were reported by the verified August database run. Median errors compare predicted and observed index levels in chronological historical holdouts. Interval coverage is empirical and differs from the nominal 80% and 95% labels.

| Index | Horizon | Selected model | Test cases | Median error | Flat baseline error | 80% interval coverage | 95% interval coverage |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ZHVI | 3 months | Flat | 58,805 | 0.65% | 0.65% | 92.2% | 98.5% |
| ZHVI | 6 months | Flat | 57,048 | 1.18% | 1.18% | 92.8% | 98.5% |
| ZHVI | 12 months | Flat | 53,111 | 2.24% | 2.24% | 92.6% | 98.4% |
| ZORI | 3 months | Flat | 58,805 | 1.46% | 1.46% | 77.8% | 92.7% |
| ZORI | 6 months | Flat | 57,048 | 1.86% | 1.86% | 81.4% | 94.3% |
| ZORI | 12 months | Damped log trend | 53,111 | 1.74% | 2.41% | 88.6% | 97.6% |

These are exploratory retrospective results on revised Zillow indices, not prospective validation or property-level income forecasts. See [forecast-methodology.md](forecast-methodology.md) for model selection, calibration, and limitations.

## Power BI acceptance

On 1 October 2026, the author refreshed the five-page report in Power BI Desktop. Screenshots confirmed populated Overview, Market Explorer, ZIP Detail, Forecast Experiment, and Reader's Guide pages. The forecast page was checked with ZIP 01002, showing both charts and all six horizon/index rows; ZIP Detail was checked with San Francisco ZIP 94112. The author confirmed that navigation, Clear filters, and reopening through `Open EstateFlow.cmd` worked, restoring Overview and cleared filters.

The dashboard previews now show the August 2026 snapshot. These are screenshots of the locally verified report, not a publicly hosted interactive report. Power BI Service publication and public access have not yet been verified.
