"""Small, auditable ZIP-level forecasting experiment.

Forecasts are for Zillow index values, not individual homes or realised income.
No value from after an origin month is used when making that origin's forecast.
"""

from __future__ import annotations

import calendar
import csv
import gzip
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import mean, median
from typing import Iterable, Mapping


HORIZONS = (3, 6, 12)
WINDOW = 24
TREND_DAMPING = 0.85
MAX_MONTHLY_LOG_SLOPE = 0.02
MIN_CALIBRATION_PAIRS = 100
MIN_VALIDATION_IMPROVEMENT = 0.10

ZORI_PATH = Path("data/raw/Zip_zori_uc_sfrcondomfr_sm_month.csv")
ZHVI_PATH = Path(
    "data/raw/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv.gz"
)


@dataclass(frozen=True)
class ZipSeries:
    zip_code: str
    state: str
    city: str
    metro: str
    # Month key is year * 12 + (month - 1); both values must be observed.
    values: Mapping[int, tuple[float, float]]


def month_key(value: date) -> int:
    return value.year * 12 + value.month - 1


def month_end(key: int) -> date:
    year, zero_based_month = divmod(key, 12)
    month = zero_based_month + 1
    return date(year, month, calendar.monthrange(year, month)[1])


def _open_csv(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", newline="", encoding="utf-8-sig")
    return path.open("r", newline="", encoding="utf-8-sig")


def _month_columns(fieldnames: list[str]) -> list[tuple[str, int]]:
    columns = []
    for name in fieldnames:
        try:
            columns.append((name, month_key(date.fromisoformat(name))))
        except ValueError:
            continue
    if not columns:
        raise ValueError("Source file has no ISO-dated monthly columns")
    return columns


def _positive(raw: str | None) -> float | None:
    if not raw:
        return None
    value = float(raw)
    return value if math.isfinite(value) and value > 0 else None


def load_raw_joined(
    zori_path: Path = ZORI_PATH, zhvi_path: Path = ZHVI_PATH
) -> list[ZipSeries]:
    """Join the same observed ZIP-month pairs as the intermediate SQL view.

    Only ZORI's smaller observed series is kept while the ZHVI file streams.
    ZIPs remain five-character strings, including leading zeroes.
    """
    rents: dict[str, tuple[str, str, str, dict[int, float]]] = {}
    with _open_csv(zori_path) as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("Empty ZORI file")
        months = _month_columns(reader.fieldnames)
        for row in reader:
            zip_code = row["RegionName"]
            if len(zip_code) != 5 or not zip_code.isdecimal():
                raise ValueError(f"Invalid ZIP in ZORI: {zip_code!r}")
            if zip_code in rents:
                raise ValueError(f"Duplicate ZIP in ZORI: {zip_code}")
            observed = {
                key: value
                for name, key in months
                if (value := _positive(row[name])) is not None
            }
            rents[zip_code] = (
                row["State"], row["City"], row["Metro"], observed
            )

    result = []
    with _open_csv(zhvi_path) as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("Empty ZHVI file")
        months = _month_columns(reader.fieldnames)
        seen: set[str] = set()
        for row in reader:
            zip_code = row["RegionName"]
            if zip_code not in rents:
                continue
            if zip_code in seen:
                raise ValueError(f"Duplicate ZIP in ZHVI: {zip_code}")
            seen.add(zip_code)
            state, city, metro, monthly_rent = rents[zip_code]
            if row["State"] != state:
                raise ValueError(f"State mismatch for ZIP {zip_code}")
            joined = {
                key: (home_value, monthly_rent[key])
                for name, key in months
                if key in monthly_rent
                if (home_value := _positive(row[name])) is not None
            }
            if joined:
                result.append(ZipSeries(zip_code, state, city, metro, joined))
    return result


def load_database_joined() -> list[ZipSeries]:
    """Read the validated ZIP-month view from the existing local PostgreSQL."""
    import os

    import psycopg
    from dotenv import load_dotenv

    load_dotenv()
    required = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_PORT")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing database settings: {', '.join(missing)}")

    result: list[ZipSeries] = []
    current_zip: str | None = None
    observed: dict[int, tuple[float, float]] = {}
    labels = ("", "", "")
    with psycopg.connect(
        host="localhost",
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    ) as connection:
        with connection.cursor(name="estateflow_forecast_source") as cursor:
            cursor.execute(
                "SELECT zip_code, state, city, metro, month, zhvi_usd, zori_usd "
                "FROM intermediate.zip_month_housing "
                "ORDER BY zip_code, month"
            )
            for zip_code, state, city, metro, month, home, rent in cursor:
                if zip_code != current_zip:
                    if current_zip is not None:
                        result.append(ZipSeries(current_zip, *labels, observed))
                    current_zip = zip_code
                    labels = (state, city or "", metro or "")
                    observed = {}
                key = month_key(month)
                if key in observed:
                    raise ValueError(f"Duplicate ZIP-month: {zip_code}, {month}")
                observed[key] = (float(home), float(rent))
    if current_zip is not None:
        result.append(ZipSeries(current_zip, *labels, observed))
    return result


def predict_log(
    monthly: Mapping[int, tuple[float, float]],
    metric_index: int,
    origin: int,
    horizon: int,
    method: str,
) -> float | None:
    """24 consecutive observed months; fit only through `origin`."""
    keys = range(origin - WINDOW + 1, origin + 1)
    if any(key not in monthly for key in keys):
        return None
    values = [math.log(monthly[key][metric_index]) for key in keys]
    latest = values[-1]
    if method == "flat":
        return latest
    if method != "damped_log_trend":
        raise ValueError(f"Unknown method: {method}")

    # Ordinary least squares slope over 24 log-index values, anchored at the
    # latest observation. Damping and the pre-declared cap limit extrapolation.
    centre = (WINDOW - 1) / 2
    average = mean(values)
    numerator = sum((i - centre) * (value - average) for i, value in enumerate(values))
    denominator = sum((i - centre) ** 2 for i in range(WINDOW))
    slope = max(-MAX_MONTHLY_LOG_SLOPE, min(MAX_MONTHLY_LOG_SLOPE, numerator / denominator))
    damped_months = sum(TREND_DAMPING**step for step in range(1, horizon + 1))
    return latest + slope * damped_months


def conformal_radius(errors: Iterable[float], coverage: float) -> float:
    """Finite-sample rank of held-out absolute log errors (pooled ZIPs)."""
    ordered = sorted(errors)
    if not ordered or not 0 < coverage < 1:
        raise ValueError("Need errors and a coverage strictly between 0 and 1")
    rank = min(len(ordered), math.ceil((len(ordered) + 1) * coverage))
    return ordered[rank - 1]


def _cases(
    series: list[ZipSeries], metric_index: int, horizon: int,
    target_months: range, method: str,
) -> list[tuple[str, float, float]]:
    cases = []
    for item in series:
        for target in target_months:
            actual = item.values.get(target)
            if actual is None:
                continue
            estimate = predict_log(item.values, metric_index, target - horizon, horizon, method)
            if estimate is not None:
                cases.append((item.zip_code, estimate, math.log(actual[metric_index])))
    return cases


def evaluate_and_forecast(series: list[ZipSeries]) -> tuple[list[dict], list[dict]]:
    if not series:
        raise ValueError("No joined observations to forecast")
    latest = max(key for item in series for key in item.values)
    evaluations: list[dict] = []
    forecasts: list[dict] = []
    for metric_index, metric in enumerate(("zhvi_usd", "zori_usd")):
        for horizon in HORIZONS:
            # Separate chronological periods for model selection, safety
            # validation, interval calibration, and untouched final testing.
            # Latest calibration target predates the earliest test origin.
            selection_targets = range(latest - 59, latest - 47)
            validation_targets = range(latest - 47, latest - 35)
            calibration_targets = range(latest - 35, latest - 23)
            test_targets = range(latest - 11, latest + 1)
            candidate = {
                method: _cases(series, metric_index, horizon, selection_targets, method)
                for method in ("flat", "damped_log_trend")
            }
            paired = len(candidate["flat"])
            if paired < MIN_CALIBRATION_PAIRS or paired != len(candidate["damped_log_trend"]):
                raise ValueError(f"Insufficient paired selection cases for {metric}, {horizon}m")
            flat_error = mean(abs(pred - actual) for _, pred, actual in candidate["flat"])
            trend_error = mean(abs(pred - actual) for _, pred, actual in candidate["damped_log_trend"])
            # A one-percent improvement threshold guards against a trivial win.
            selected = "damped_log_trend" if trend_error < 0.99 * flat_error else "flat"
            selected_validation = _cases(series, metric_index, horizon, validation_targets, selected)
            validation_flat = _cases(series, metric_index, horizon, validation_targets, "flat")
            if len(selected_validation) < MIN_CALIBRATION_PAIRS or len(selected_validation) != len(validation_flat):
                raise ValueError(f"Insufficient paired validation cases for {metric}, {horizon}m")
            selected_validation_mape = median(
                abs(math.expm1(pred - actual)) * 100 for _, pred, actual in selected_validation
            )
            validation_flat_mape = median(
                abs(math.expm1(pred - actual)) * 100 for _, pred, actual in validation_flat
            )
            # Require a material validation gain, rather than accepting a
            # marginal win. The last 12 targets are not an input to this rule.
            rejected = (
                selected != "flat"
                and selected_validation_mape
                >= (1 - MIN_VALIDATION_IMPROVEMENT) * validation_flat_mape
            )
            chosen = "flat" if rejected else selected
            calibration = _cases(series, metric_index, horizon, calibration_targets, chosen)
            if len(calibration) < MIN_CALIBRATION_PAIRS:
                raise ValueError(f"Insufficient calibration cases for {metric}, {horizon}m")
            q80 = conformal_radius((abs(p - a) for _, p, a in calibration), 0.80)
            q95 = conformal_radius((abs(p - a) for _, p, a in calibration), 0.95)
            test = _cases(series, metric_index, horizon, test_targets, chosen)
            baseline = _cases(series, metric_index, horizon, test_targets, "flat")
            if len(test) < MIN_CALIBRATION_PAIRS or len(test) != len(baseline):
                raise ValueError(f"Insufficient paired test cases for {metric}, {horizon}m")
            test_mape = median(abs(math.expm1(pred - actual)) * 100 for _, pred, actual in test)
            baseline_mape = median(abs(math.expm1(pred - actual)) * 100 for _, pred, actual in baseline)
            evaluations.append({
                "as_of_month": month_end(latest).isoformat(),
                "metric": metric,
                "horizon_months": horizon,
                "selection_model": selected,
                "model": chosen,
                "decision": "candidate_rejected_on_validation" if rejected else "selection_accepted",
                "selection_cases": paired,
                "validation_cases": len(selected_validation),
                "validation_candidate_median_absolute_pct_error": selected_validation_mape,
                "validation_flat_median_absolute_pct_error": validation_flat_mape,
                "calibration_cases": len(calibration),
                "test_cases": len(test),
                "test_zips": len({zip_code for zip_code, _, _ in test}),
                "selection_flat_mean_abs_log_error": flat_error,
                "selection_trend_mean_abs_log_error": trend_error,
                "test_median_absolute_pct_error": test_mape,
                "test_flat_median_absolute_pct_error": baseline_mape,
                "test_80_coverage_pct": 100 * mean(
                    abs(pred - actual) <= q80 for _, pred, actual in test
                ),
                "test_95_coverage_pct": 100 * mean(
                    abs(pred - actual) <= q95 for _, pred, actual in test
                ),
                "q80_log": q80,
                "q95_log": q95,
            })
            for item in series:
                if latest not in item.values:
                    continue
                estimate = predict_log(item.values, metric_index, latest, horizon, chosen)
                if estimate is None:
                    continue
                forecasts.append({
                    "zip_code": item.zip_code,
                    "state": item.state,
                    "city": item.city,
                    "metro": item.metro,
                    "metric": metric,
                    "as_of_month": month_end(latest).isoformat(),
                    "forecast_month": month_end(latest + horizon).isoformat(),
                    "horizon_months": horizon,
                    "model": chosen,
                    "estimate_usd": round(math.exp(estimate), 2),
                    "lower_80_usd": round(math.exp(estimate - q80), 2),
                    "upper_80_usd": round(math.exp(estimate + q80), 2),
                    "lower_95_usd": round(math.exp(estimate - q95), 2),
                    "upper_95_usd": round(math.exp(estimate + q95), 2),
                })
    return evaluations, forecasts
