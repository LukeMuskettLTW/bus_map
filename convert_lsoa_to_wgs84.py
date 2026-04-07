import json
from pathlib import Path
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

IN_PATH = DATA / "lsoa_boundaries.geojson"
OUT_PATH = DATA / "lsoa_boundaries_wgs84.geojson"

transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

def looks_like_bng(x, y):
    return abs(x) > 1000 or abs(y) > 1000

def convert_coord(coord):
    x, y = coord[0], coord[1]
    if looks_like_bng(x, y):
        lon, lat = transformer.transform(x, y)
        return [lon, lat]
    return [x, y]

def convert_coords(coords):
    if not coords:
        return coords

    if isinstance(coords[0], (int, float)):
        return convert_coord(coords)

    return [convert_coords(c) for c in coords]

with IN_PATH.open("r", encoding="utf-8") as f:
    geojson = json.load(f)

for feature in geojson.get("features", []):
    geom = feature.get("geometry")
    if geom and "coordinates" in geom:
        geom["coordinates"] = convert_coords(geom["coordinates"])

with OUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(geojson, f)

print(f"Saved converted file to: {OUT_PATH}")