"""Structural checks for the forecast page authored as a Power BI Project."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "powerbi/EstateFlow_PowerBI_Analytics/EstateFlow_Dashboard.SemanticModel/definition"
REPORT = ROOT / "powerbi/EstateFlow_PowerBI_Analytics/EstateFlow_Dashboard.Report/definition/pages"
PAGE_ID = "e4fca6582f8d4d0b98f1"


class ForecastPBIRTests(unittest.TestCase):
    def test_forecast_page_has_source_backed_fields_and_fits_canvas(self):
        page = json.loads((REPORT / PAGE_ID / "page.json").read_text())
        pages = json.loads((REPORT / "pages.json").read_text())
        self.assertIn(PAGE_ID, pages["pageOrder"])
        self.assertEqual(page["displayName"], "Forecast Experiment")
        model = (MODEL / "tables/ZIP Forecasts.tmdl").read_text()
        defined = set(re.findall(r"^\s*(?:column|measure) '([^']+)'", model, flags=re.M))
        defined |= set(re.findall(r"^\s*(?:column|measure) ([A-Za-z][A-Za-z0-9 ]*)\s*(?:=|$)", model, flags=re.M))
        self.assertIn("ref table 'ZIP Forecasts'", (MODEL / "model.tmdl").read_text())
        names = set()
        visuals = list((REPORT / PAGE_ID / "visuals").glob("*/visual.json"))
        self.assertGreaterEqual(len(visuals), 9, "forecast page is missing its core chart, card, or table visuals")
        for path in visuals:
            visual = json.loads(path.read_text())
            self.assertEqual(visual["name"], path.parent.name)
            self.assertNotIn(visual["name"], names)
            names.add(visual["name"])
            position = visual["position"]
            self.assertLessEqual(position["x"] + position["width"], page["width"])
            self.assertLessEqual(position["y"] + position["height"], page["height"])
            for projection in visual["visual"].get("query", {}).get("queryState", {}).values():
                for item in projection.get("projections", []):
                    field = item["field"]
                    kind = "Column" if "Column" in field else "Measure"
                    reference = field[kind]
                    self.assertEqual(reference["Expression"]["SourceRef"]["Entity"], "ZIP Forecasts")
                    self.assertIn(reference["Property"], defined)


if __name__ == "__main__":
    unittest.main()
