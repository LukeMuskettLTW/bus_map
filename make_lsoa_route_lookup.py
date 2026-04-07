import csv
import json
from pathlib import Path
from statistics import mean
from math import floor

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

LSOA_PATH = DATA / "lsoa_boundaries.geojson"
ROUTES_PATH = DATA / "bus_routes.geojson"
TIMESERIES_PATH = DATA / "routes_year_summary.csv"
OUT_PATH = DATA / "lsoa_route_change_lookup.csv"

GRID_SIZE = 0.02   # degrees
PAD = 0.002        # small overlap tolerance


def clean_key(value: str) -> str:
    return (
        str(value or "")
        .replace("\ufeff", "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def normalise_route(value: str) -> str:
    return str(value or "").strip().upper()


def safe_float(value):
    if value is None:
        return None
    s = str(value).strip().replace(",", "")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({clean_key(k): v for k, v in row.items()})
        return rows


def detect_route_field(feature):
    props = feature.get("properties", {})
    for key in ["route", "Route", "ROUTE", "route_id", "RouteID", "name", "Name", "line", "Line"]:
        if key in props and props[key] not in (None, ""):
            return key
    return None


def build_route_year_table(rows):
    table = {}
    for row in rows:
        route = normalise_route(row.get("route"))
        year = row.get("year")
        avg_speed = safe_float(row.get("avg_speed"))

        if not route or avg_speed is None:
            continue

        try:
            year = int(float(year))
        except (TypeError, ValueError):
            continue

        table.setdefault(route, {})[year] = avg_speed

    return table


def extract_lines(geometry):
    if not geometry:
        return []

    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])

    if gtype == "LineString":
        return [coords]
    if gtype == "MultiLineString":
        return coords
    return []


def polygon_rings(geometry):
    if not geometry:
        return []

    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])

    if gtype == "Polygon":
        return coords
    if gtype == "MultiPolygon":
        rings = []
        for poly in coords:
            rings.extend(poly)
        return rings
    return []


def looks_like_bng(x, y):
    return abs(x) > 1000 or abs(y) > 1000


_transformer = None
def transform_bng_to_wgs84(x, y):
    global _transformer
    if _transformer is None:
        from pyproj import Transformer
        _transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    return _transformer.transform(x, y)


def transform_coord_if_needed(coord):
    x, y = coord[0], coord[1]
    if looks_like_bng(x, y):
        lng, lat = transform_bng_to_wgs84(x, y)
        return [lng, lat]
    return [x, y]


def transform_geometry_if_needed(geometry):
    if not geometry:
        return geometry

    gtype = geometry.get("type")
    coords = geometry.get("coordinates")

    if gtype == "LineString":
        return {
            "type": gtype,
            "coordinates": [transform_coord_if_needed(pt) for pt in coords]
        }

    if gtype == "MultiLineString":
        return {
            "type": gtype,
            "coordinates": [
                [transform_coord_if_needed(pt) for pt in line]
                for line in coords
            ]
        }

    if gtype == "Polygon":
        return {
            "type": gtype,
            "coordinates": [
                [transform_coord_if_needed(pt) for pt in ring]
                for ring in coords
            ]
        }

    if gtype == "MultiPolygon":
        return {
            "type": gtype,
            "coordinates": [
                [
                    [transform_coord_if_needed(pt) for pt in ring]
                    for ring in poly
                ]
                for poly in coords
            ]
        }

    return geometry


def bounds_from_points(points):
    xs = [pt[0] for pt in points if len(pt) >= 2]
    ys = [pt[1] for pt in points if len(pt) >= 2]
    return (min(xs), min(ys), max(xs), max(ys))


def merge_bounds(bounds_list):
    minx = min(b[0] for b in bounds_list)
    miny = min(b[1] for b in bounds_list)
    maxx = max(b[2] for b in bounds_list)
    maxy = max(b[3] for b in bounds_list)
    return (minx, miny, maxx, maxy)


def feature_bounds_from_geometry(geometry):
    lines = extract_lines(geometry)
    all_bounds = []
    for line in lines:
        if line:
            all_bounds.append(bounds_from_points(line))
    if not all_bounds:
        return None
    return merge_bounds(all_bounds)


def polygon_bounds_from_geometry(geometry):
    rings = polygon_rings(geometry)
    all_pts = []
    for ring in rings:
        all_pts.extend(ring)
    if not all_pts:
        return None
    return bounds_from_points(all_pts)


def bounds_intersect(a, b, pad=0.0):
    return not (
        a[2] < b[0] - pad or
        a[0] > b[2] + pad or
        a[3] < b[1] - pad or
        a[1] > b[3] + pad
    )


def get_lsoa_code(props):
    for key in ["LSOA21CD", "lsoa21cd", "lsoa_code", "code", "LSOA_CODE"]:
        if key in props and props[key]:
            return str(props[key]).strip()
    return ""


def get_lsoa_name(props):
    for key in ["LSOA21NM", "lsoa21nm", "lsoa_name", "name", "NAME"]:
        if key in props and props[key]:
            return str(props[key]).strip()
    return ""


def grid_keys_for_bounds(bounds, grid_size=GRID_SIZE):
    minx, miny, maxx, maxy = bounds
    gx0 = floor(minx / grid_size)
    gx1 = floor(maxx / grid_size)
    gy0 = floor(miny / grid_size)
    gy1 = floor(maxy / grid_size)
    for gx in range(gx0, gx1 + 1):
        for gy in range(gy0, gy1 + 1):
            yield (gx, gy)


def main():
    print("Loading files...")
    lsoa_geojson = load_json(LSOA_PATH)
    routes_geojson = load_json(ROUTES_PATH)
    timeseries_rows = load_csv(TIMESERIES_PATH)

    route_year_table = build_route_year_table(timeseries_rows)
    available_years = sorted({year for years in route_year_table.values() for year in years})
    print(f"Years found: {available_years}")

    sample_geom = None
    for feat in lsoa_geojson.get("features", []):
        geom = feat.get("geometry")
        if geom and geom.get("coordinates"):
            sample_geom = geom
            break

    if sample_geom:
        first_pt = None
        gtype = sample_geom.get("type")
        coords = sample_geom.get("coordinates")
        if gtype == "Polygon":
            first_pt = coords[0][0]
        elif gtype == "MultiPolygon":
            first_pt = coords[0][0][0]

        if first_pt:
            if looks_like_bng(first_pt[0], first_pt[1]):
                print("Detected LSOA boundaries in British National Grid. Will convert to lat/long in-script.")
            else:
                print("Detected LSOA boundaries already in lat/long.")

    route_features = []
    route_grid = {}

    for idx, feature in enumerate(routes_geojson.get("features", []), start=1):
        route_field = detect_route_field(feature)
        if not route_field:
            continue

        route_name = normalise_route(feature["properties"].get(route_field))
        if not route_name:
            continue

        geometry = transform_geometry_if_needed(feature.get("geometry"))
        b = feature_bounds_from_geometry(geometry)
        if not b:
            continue

        route_obj = {"route": route_name, "bounds": b}
        route_features.append(route_obj)

        for key in grid_keys_for_bounds(b):
            route_grid.setdefault(key, []).append(route_obj)

        if idx % 250 == 0:
            print(f"Indexed route features: {idx}")

    print(f"Route features loaded: {len(route_features)}")
    print(f"Spatial grid cells used: {len(route_grid)}")

    output_rows = []
    lsoa_count = 0

    features = lsoa_geojson.get("features", [])
    total_features = len(features)

    for i, feature in enumerate(features, start=1):
        props = feature.get("properties", {})
        lsoa_code = get_lsoa_code(props)
        lsoa_name = get_lsoa_name(props)

        if not lsoa_code:
            continue

        geometry = transform_geometry_if_needed(feature.get("geometry"))
        lsoa_b = polygon_bounds_from_geometry(geometry)
        if not lsoa_b:
            continue

        candidate_routes = []
        seen = set()

        for key in grid_keys_for_bounds(lsoa_b):
            for route_obj in route_grid.get(key, []):
                rid = id(route_obj)
                if rid not in seen:
                    seen.add(rid)
                    candidate_routes.append(route_obj)

        touching_routes = []
        for route_obj in candidate_routes:
            if bounds_intersect(lsoa_b, route_obj["bounds"], pad=PAD):
                touching_routes.append(route_obj["route"])

        touching_routes = sorted(set(touching_routes))

        if not touching_routes:
            if i % 500 == 0 or i == total_features:
                print(f"Processed {i}/{total_features} LSOAs...")
            continue

        lsoa_count += 1

        for year in available_years:
            speeds = []
            contributing_routes = []

            for route in touching_routes:
                speed = route_year_table.get(route, {}).get(year)
                if speed is not None:
                    speeds.append(speed)
                    contributing_routes.append(route)

            if not speeds:
                continue

            output_rows.append({
                "lsoa_code": lsoa_code,
                "lsoa_name": lsoa_name,
                "year": year,
                "avg_speed": round(mean(speeds), 6),
                "route_count": len(contributing_routes),
                "routes": "|".join(contributing_routes),
            })

        if i % 500 == 0 or i == total_features:
            print(f"Processed {i}/{total_features} LSOAs... matched so far: {lsoa_count}")

    print(f"LSOAs with matched routes: {lsoa_count}")
    print(f"Rows to write: {len(output_rows)}")

    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["lsoa_code", "lsoa_name", "year", "avg_speed", "route_count", "routes"]
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()