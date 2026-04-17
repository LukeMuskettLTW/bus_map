import json
import re
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer

# === FILE PATHS ===
INPUT_DIR = Path("dft_raw")
LSOA_FILE = Path("data/lsoa_boundaries_simplified.geojson")
OUTPUT_FILE = Path("dft_roadworks_lsoa.geojson")

# === COORDINATE TRANSFORM ===
transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

point_re = re.compile(r"POINT\s*\(\s*([0-9\.\-]+)\s+([0-9\.\-]+)\s*\)", re.IGNORECASE)


def extract_json_text(text):
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= start:
        return None
    return text[start:end]


def parse_point(wkt):
    if not wkt:
        return None

    m = point_re.search(wkt)
    if not m:
        return None

    try:
        e = float(m.group(1))
        n = float(m.group(2))
        lon, lat = transformer.transform(e, n)
        return Point(lon, lat)
    except Exception:
        return None


print("Loading LSOAs...")
lsoa = gpd.read_file(LSOA_FILE)
lsoa = lsoa.to_crs("EPSG:4326")
print(f"Loaded {len(lsoa)} LSOAs")

print("Scanning DfT files...")
files = [p for p in INPUT_DIR.rglob("*") if p.is_file()]
print("Files found:", len(files))

points = []
processed = 0
no_json = 0
no_object_data = 0
no_point = 0
errors = 0

for i, f in enumerate(files, start=1):
    if i % 1000 == 0:
        print(
            f"{i}/{len(files)} processed | "
            f"usable points so far: {len(points)} | "
            f"no_point={no_point} errors={errors}"
        )

    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
        json_text = extract_json_text(text)

        if not json_text:
            no_json += 1
            continue

        obj = json.loads(json_text)
        processed += 1

        data = obj.get("object_data")
        if not isinstance(data, dict):
            no_object_data += 1
            continue

        geom = parse_point(data.get("activity_coordinates"))
        if geom is None:
            no_point += 1
            continue

        points.append({
            "geometry": geom,
            "activity_reference_number": data.get("activity_reference_number"),
            "activity": data.get("activity_type"),
            "street": data.get("street_name"),
            "authority": data.get("highway_authority"),
            "start": data.get("start_date"),
            "end": data.get("end_date"),
        })

    except Exception:
        errors += 1

print(f"Total usable points before London filter: {len(points)}")

print("Creating GeoDataFrame...")
gdf = gpd.GeoDataFrame(points, geometry="geometry", crs="EPSG:4326")

print("Running spatial join...")
joined = gpd.sjoin(gdf, lsoa, how="inner", predicate="within")
print(f"Joined rows: {len(joined)}")

print("Aggregating by LSOA...")
counts = joined.groupby("lsoa21cd").size().reset_index(name="roadworks_count")
print(f"LSOAs with at least one DfT roadwork: {len(counts)}")

print("Merging counts back to boundaries...")
lsoa = lsoa.merge(counts, on="lsoa21cd", how="left")
lsoa["roadworks_count"] = lsoa["roadworks_count"].fillna(0).astype(int)

print("Writing output...")
lsoa.to_file(OUTPUT_FILE, driver="GeoJSON")

print("\nDONE")
print("Processed JSON rows:", processed)
print("No JSON:", no_json)
print("No object_data:", no_object_data)
print("No point:", no_point)
print("Joined London rows:", len(joined))
print("LSOAs with roadworks:", len(counts))
print(f"Saved: {OUTPUT_FILE.resolve()}")