"""Run with: python -m unittest discover -s tests -v"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "estateflow"))

from forecasting import (  # noqa: E402
    ZipSeries,
    conformal_radius,
    evaluate_and_forecast,
    month_end,
    month_key,
    predict_log,
)


class ForecastingTests(unittest.TestCase):
    def test_month_end_handles_leap_year_and_leading_zero_zip(self):
        self.assertEqual(month_end(month_key(month_end(2024 * 12 + 1))), month_end(2024 * 12 + 1))
        self.assertEqual(month_end(2024 * 12 + 1).isoformat(), "2024-02-29")

    def test_no_future_leakage(self):
        values = {key: (100 * math.exp(key * 0.005), 1000.0) for key in range(50)}
        before = predict_log(values, 0, origin=30, horizon=6, method="damped_log_trend")
        values[31] = (10**10, 1.0)
        values[36] = (10**10, 1.0)
        self.assertEqual(before, predict_log(values, 0, 30, 6, "damped_log_trend"))

    def test_gap_is_not_silently_interpolated(self):
        values = {key: (100.0, 1000.0) for key in range(24)}
        values.pop(12)
        self.assertIsNone(predict_log(values, 0, 23, 3, "flat"))

    def test_intervals_are_nested_and_positive(self):
        records = []
        for zip_number in range(120):
            values = {
                key: (
                    200_000 * math.exp((0.002 + zip_number / 200_000) * key),
                    1_500 * math.exp((0.001 + zip_number / 300_000) * key),
                )
                for key in range(100)
            }
            records.append(ZipSeries(f"{zip_number:05d}", "CA", "Test", "Test", values))
        evaluation, forecast = evaluate_and_forecast(records)
        self.assertEqual(len(evaluation), 6)
        self.assertEqual(len(forecast), 120 * 2 * 3)
        self.assertTrue(all(0 < row["lower_95_usd"] <= row["lower_80_usd"]
                            <= row["estimate_usd"] <= row["upper_80_usd"]
                            <= row["upper_95_usd"] for row in forecast))
        self.assertIn("00000", {row["zip_code"] for row in forecast})

    def test_trend_is_rejected_if_recent_holdout_favours_flat(self):
        records = []
        for zip_number in range(120):
            values = {
                key: (200_000 * math.exp(0.005 * (key if key < 52 else 46)),
                      1_500 * math.exp(0.005 * (key if key < 52 else 46)))
                for key in range(100)
            }
            records.append(ZipSeries(f"{zip_number:05d}", "CA", "Test", "Test", values))
        evaluation, forecast = evaluate_and_forecast(records)
        result = next(row for row in evaluation if row["metric"] == "zhvi_usd"
                      and row["horizon_months"] == 12)
        self.assertEqual(result["selection_model"], "damped_log_trend")
        self.assertEqual(result["model"], "flat")
        self.assertEqual(result["decision"], "candidate_rejected_on_validation")
        self.assertTrue(all(row["model"] == "flat" for row in forecast
                            if row["metric"] == "zhvi_usd" and row["horizon_months"] == 12))

    def test_conformal_rank(self):
        self.assertEqual(conformal_radius([1, 2, 3, 4, 5, 6, 7, 8, 9], 0.8), 8)
        self.assertEqual(conformal_radius([1, 2, 3, 4, 5, 6, 7, 8, 9], 0.95), 9)


if __name__ == "__main__":
    unittest.main()
