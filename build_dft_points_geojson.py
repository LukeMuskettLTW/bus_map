import json
import re
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point


# =========================
# FILE PATHS
# =========================
ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "dft_raw"
LSOA_FILE = ROOT / "data" / "lsoa_boundaries_simplified.geojson"
OUTPUT_FILE = ROOT / "data" / "dft_roadworks_points.geojson"

# =========================
# COORDINATE TRANSFORM
# DfT activity_coordinates are EPSG:27700 (British National Grid)
# Convert to EPSG:4326 for web mapping
# =========================
TRANSFORMER = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

POINT_RE = re.compile(
    r"POINT\s*\(\s*([0-9\.\-]+)\s+([0-9\.\-]+)\s*\)",
    re.IGNORECASE,
)


def extract_json_text(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= start:
        return None
    return text[start:end]


def parse_point(wkt: str | None) -> Point | None:
    if not wkt:
        return None

    match = POINT_RE.search(wkt)
    if not match:
        return None

    try:
        easting = float(match.group(1))
        northing = float(match.group(2))
        lon, lat = TRANSFORMER.transform(easting, northing)
        return Point(lon, lat)
    except Exception:
        return None


def safe_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def safe_date_only(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value).split("T")[0]


def extract_year(value: Any) -> int | None:
    date_text = safe_date_only(value)
    if not date_text:
        return None
    try:
        return pd.to_datetime(date_text, errors="raise").year
    except Exception:
        return None


def load_lsoa() -> gpd.GeoDataFrame:
    print("Loading London LSOA boundaries...")
    if not LSOA_FILE.exists():
        raise FileNotFoundError(f"Missing LSOA file: {LSOA_FILE}")

    lsoa = gpd.read_file(LSOA_FILE).to_crs("EPSG:4326")

    required = {"lsoa21cd", "lsoa21nm", "geometry"}
    missing = required.difference(lsoa.columns)
    if missing:
        raise RuntimeError(f"LSOA file is missing required columns: {sorted(missing)}")

    print(f"Loaded {len(lsoa)} LSOAs")
    return lsoa[["lsoa21cd", "lsoa21nm", "geometry"]].copy()


def build_rows(files: list[Path]) -> tuple[list[dict], dict[str, int]]:
    rows: list[dict] = []

    stats = {
        "processed_json": 0,
        "no_json": 0,
        "no_object_data": 0,
        "no_point": 0,
        "errors": 0,
    }

    total = len(files)

    for i, file_path in enumerate(files, start=1):
        if i % 1000 == 0 or i == total:
            print(
                f"{i}/{total} processed | usable points so far: {len(rows)} | "
                f"no_json={stats['no_json']} "
                f"no_object_data={stats['no_object_data']} "
                f"no_point={stats['no_point']} "
                f"errors={stats['errors']}"
            )

        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            json_text = extract_json_text(text)

            if not json_text:
                stats["no_json"] += 1
                continue

            obj = json.loads(json_text)
            stats["processed_json"] += 1

            data = obj.get("object_data")
            if not isinstance(data, dict):
                stats["no_object_data"] += 1
                continue

            geom = parse_point(data.get("activity_coordinates"))
            if geom is None:
                stats["no_point"] += 1
                continue

            start_value = data.get("start_date")
            end_value = data.get("end_date")

            rows.append(
                {
                    "geometry": geom,
                    "activity_reference_number": safe_str(data.get("activity_reference_number")),
                    "usrn": safe_str(data.get("usrn")),
                    "street_name": safe_str(data.get("street_name")),
                    "area_name": safe_str(data.get("area_name")),
                    "town": safe_str(data.get("town")),
                    "road_category": safe_str(data.get("road_category")),
                    "activity_name": safe_str(data.get("activity_name")),
                    "activity_type": safe_str(data.get("activity_type")),
                    "activity_type_details": safe_str(data.get("activity_type_details")),
                    "start": safe_str(start_value),
                    "end": safe_str(end_value),
                    "start_date_only": safe_date_only(start_value),
                    "end_date_only": safe_date_only(end_value),
                    "start_year": extract_year(start_value),
                    "end_year": extract_year(end_value),
                    "activity_location_type": safe_str(data.get("activity_location_type")),
                    "activity_location_description": safe_str(data.get("activity_location_description")),
                    "traffic_management_required": safe_str(data.get("traffic_management_required")),
                    "traffic_management_type": safe_str(data.get("traffic_management_type")),
                    "collaborative_working": safe_str(data.get("collaborative_working")),
                    "cancelled": safe_str(data.get("cancelled")),
                    "highway_authority_swa_code": safe_str(data.get("highway_authority_swa_code")),
                    "highway_authority": safe_str(data.get("highway_authority")),
                    "event_reference": safe_str(obj.get("event_reference")),
                    "event_type": safe_str(obj.get("event_type")),
                    "event_time": safe_str(obj.get("event_time")),
                    "object_type": safe_str(obj.get("object_type")),
                    "object_reference": safe_str(obj.get("object_reference")),
                    "version": safe_str(obj.get("version")),
                    "source_file": file_path.name,
                }
            )

        except Exception:
            stats["errors"] += 1

    return rows, stats


def deduplicate_points(df: pd.DataFrame) -> pd.DataFrame:
    print("Deduplicating points...")

    df = df.copy()

    has_ref = df["activity_reference_number"].notna() & (df["activity_reference_number"] != "")
    with_ref = df.loc[has_ref].copy()
    without_ref = df.loc[~has_ref].copy()

    before = len(df)

    if not with_ref.empty:
        with_ref = with_ref.drop_duplicates(subset=["activity_reference_number"])

    if not without_ref.empty:
        fallback_cols = [
            "street_name",
            "area_name",
            "town",
            "activity_type",
            "activity_type_details",
            "start_date_only",
            "end_date_only",
            "highway_authority",
            "lsoa21cd",
            "geometry",
        ]
        existing = [c for c in fallback_cols if c in without_ref.columns]
        without_ref = without_ref.drop_duplicates(subset=existing)

    out = pd.concat([with_ref, without_ref], ignore_index=True)

    print(f"Deduplicated rows: {before} -> {len(out)}")
    return out


def main() -> None:
    lsoa = load_lsoa()

    print("Scanning DfT raw files...")
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Missing input folder: {INPUT_DIR}")

    files = [p for p in INPUT_DIR.rglob("*") if p.is_file()]
    print(f"Files found: {len(files)}")

    rows, stats = build_rows(files)

    print(f"Total usable points before London clip: {len(rows)}")
    if not rows:
        raise RuntimeError("No usable DfT points found.")

    print("Creating GeoDataFrame...")
    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")

    print("Spatially clipping points to London LSOAs with predicate='within'...")
    joined = gpd.sjoin(gdf, lsoa, how="inner", predicate="within")
    print(f"Joined London rows: {len(joined)}")

    if joined.empty:
        raise RuntimeError("No DfT points fell within the London LSOAs.")

    keep_cols = [
        "geometry",
        "activity_reference_number",
        "usrn",
        "street_name",
        "area_name",
        "town",
        "road_category",
        "activity_name",
        "activity_type",
        "activity_type_details",
        "start",
        "end",
        "start_date_only",
        "end_date_only",
        "start_year",
        "end_year",
        "activity_location_type",
        "activity_location_description",
        "traffic_management_required",
        "traffic_management_type",
        "collaborative_working",
        "cancelled",
        "highway_authority_swa_code",
        "highway_authority",
        "event_reference",
        "event_type",
        "event_time",
        "object_type",
        "object_reference",
        "version",
        "source_file",
        "lsoa21cd",
        "lsoa21nm",
    ]
    existing_cols = [c for c in keep_cols if c in joined.columns]
    out = joined[existing_cols].copy()

    out = deduplicate_points(out)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("Writing London-only DfT points GeoJSON...")
    gpd.GeoDataFrame(out, geometry="geometry", crs="EPSG:4326").to_file(
        OUTPUT_FILE,
        driver="GeoJSON",
    )

    area_counts = (
        out["area_name"]
        .fillna("Unknown")
        .value_counts()
        .sort_values(ascending=False)
    )

    town_counts = (
        out["town"]
        .fillna("Unknown")
        .value_counts()
        .sort_values(ascending=False)
    )

    print("\nDONE")
    print(f"Processed JSON rows: {stats['processed_json']}")
    print(f"No JSON: {stats['no_json']}")
    print(f"No object_data: {stats['no_object_data']}")
    print(f"No point: {stats['no_point']}")
    print(f"Errors: {stats['errors']}")
    print(f"London-clipped points written: {len(out)}")
    print(f"Saved: {OUTPUT_FILE.resolve()}")

    print("\nTop 20 area_name values in output:")
    print(area_counts.head(20).to_string())

    print("\nTop 20 town values in output:")
    print(town_counts.head(20).to_string())

    sample_cols = [c for c in ["street_name", "area_name", "town", "start_date_only", "end_date_only", "lsoa21nm"] if c in out.columns]
    if sample_cols:
        print("\nSample of output rows:")
        print(out[sample_cols].head(15).to_string(index=False))


if __name__ == "__main__":
    main()