"""Download and validate the latest matching Zillow ZIP source vintage."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import shutil
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw"
METADATA = ["RegionID", "SizeRank", "RegionName", "RegionType", "StateName", "State", "City", "Metro", "CountyName"]
SOURCES = {
    "zhvi": "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "zori": "Zip_zori_uc_sfrcondomfr_sm_month.csv",
}


def inspect_source(path: Path) -> dict:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if header[:9] != METADATA or len(header) < 10:
            raise ValueError(f"Unexpected source schema: {path.name}")
        months = [date.fromisoformat(value) for value in header[9:]]
        if months != sorted(set(months)) or months[-1] > date.today():
            raise ValueError(f"Invalid observation dates: {path.name}")
        regions = set()
        observations = latest_count = 0
        for row in reader:
            if len(row) != len(header) or row[2] in regions:
                raise ValueError(f"Invalid row or duplicate ZIP: {path.name}")
            if len(row[2]) != 5 or not row[2].isdigit() or row[3] != "zipcode":
                raise ValueError(f"Invalid ZIP grain: {path.name}")
            regions.add(row[2])
            for value in row[9:]:
                if value:
                    number = float(value)
                    if not math.isfinite(number) or number <= 0:
                        raise ValueError(f"Invalid source value: {path.name}")
                    observations += 1
            latest_count += bool(row[-1])
    if not regions or not latest_count:
        raise ValueError(f"Empty source or latest month: {path.name}")
    return {
        "first_month": months[0].isoformat(),
        "latest_month": months[-1].isoformat(),
        "zip_rows": len(regions),
        "observations": observations,
        "latest_nonmissing_zips": latest_count,
    }


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {"retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "sources": {}}
    with tempfile.TemporaryDirectory(prefix="zillow-", dir=RAW) as directory:
        temporary = Path(directory)
        replacements = []
        for kind, filename in SOURCES.items():
            url = f"https://files.zillowstatic.com/research/public_csvs/{kind}/{filename}"
            downloaded = temporary / filename
            with urlopen(Request(url, headers={"User-Agent": "EstateFlow/1.0"}), timeout=120) as response:
                modified = response.headers.get("Last-Modified")
                with downloaded.open("wb") as output:
                    shutil.copyfileobj(response, output)
            profile = inspect_source(downloaded)
            target = RAW / (filename + ".gz" if kind == "zhvi" else filename)
            if target.exists():
                opener = gzip.open if target.suffix == ".gz" else open
                with opener(target, "rt", encoding="utf-8-sig") as old:
                    previous_month = next(csv.reader(old))[-1]
                if profile["latest_month"] < previous_month:
                    raise ValueError(f"Refusing an older {kind} source vintage")
            with downloaded.open("rb") as source:
                sha256 = hashlib.file_digest(source, "sha256").hexdigest()
            ready = downloaded
            if kind == "zhvi":
                ready = temporary / target.name
                with downloaded.open("rb") as source, ready.open("wb") as output:
                    with gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=0) as compressed:
                        shutil.copyfileobj(source, compressed)
            manifest["sources"][kind] = {
                "url": url, "path": target.relative_to(ROOT).as_posix(),
                "last_modified": modified, "csv_sha256": sha256, **profile,
            }
            replacements.append((ready, target))
            print(f"Validated {kind}: through {profile['latest_month']}, {profile['observations']:,} observations", flush=True)
        months = {item["latest_month"] for item in manifest["sources"].values()}
        if len(months) != 1:
            raise ValueError("ZHVI and ZORI latest months differ; existing files were retained")
        for ready, target in replacements:
            ready.replace(target)
        (RAW / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Latest matched Zillow source vintage saved. Rebuild the pipeline and forecasts before refreshing Power BI.")


if __name__ == "__main__":
    main()
