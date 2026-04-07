from pathlib import Path
import json
import math

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

IN_FILE = DATA / "cycle_routes_official.json"
OUT_FILE = DATA / "cycle_major_schemes.geojson"

# Keep only open Cycleways, and ignore very short fragments.
MIN_LENGTH_KM = 1.0


def line_length_km(coords):
    """Approximate length in km for one LineString coordinate list."""
    total = 0.0
    for i in range(1, len(coords)):
        lon1, lat1 = coords[i - 1]
        lon2, lat2 = coords[i]

        # crude but fine for London filtering
        dx = (lon2 - lon1) * 111.320 * math.cos(math.radians((lat1 + lat2) / 2))
        dy = (lat2 - lat1) * 110.574
        total += math.sqrt(dx * dx + dy * dy)
    return total


def geom_length_km(geometry):
    if not geometry:
        return 0.0

    gtype = geometry.get("type")

    if gtype == "LineString":
        return line_length_km(geometry.get("coordinates", []))

    if gtype == "MultiLineString":
        return sum(line_length_km(line) for line in geometry.get("coordinates", []))

    return 0.0


def opened_year_from_label(label):
    """
    Pragmatic working years.
    Can be refined later route by route.
    """
    label = (label or "").strip().upper()

    if label in {"CS2", "CS3", "CS7", "CS8"}:
        return 2013
    if label in {"CS1", "CS5", "CS6"}:
        return 2016
    if label.startswith("Q"):
        return 2019
    if label.startswith("C"):
        return 2020

    return 2020


def main():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_features = data.get("features", [])
    output_features = []

    kept_labels = {}

    for feature in source_features:
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}

        label = str(props.get("Label", "")).strip()
        route_name = str(props.get("Route_Name", "")).strip()
        programme = str(props.get("Programme", "")).strip()
        status = str(props.get("Status", "")).strip()

        if not label:
            continue

        if status.lower() != "open":
            continue

        if programme.lower() not in {"cycleways", "quietways", "mini-holland", "central london grid"}:
            continue

        length_km = geom_length_km(geom)
        if length_km < MIN_LENGTH_KM:
            continue

        kept_labels[label] = kept_labels.get(label, 0) + 1

        output_features.append({
            "type": "Feature",
            "properties": {
                "name": route_name or label,
                "route_code": label,
                "opened_year": opened_year_from_label(label),
                "status": status,
                "source": "TfL official cycle routes",
                "programme": programme,
                "length_km": round(length_km, 3)
            },
            "geometry": geom
        })

    out_geojson = {
        "type": "FeatureCollection",
        "features": output_features
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out_geojson, f)

    print(f"Source features: {len(source_features)}")
    print(f"Output features: {len(output_features)}")
    print(f"Unique labels kept: {len(kept_labels)}")
    print(f"Saved to: {OUT_FILE}")
    print("Labels kept:", sorted(kept_labels.keys())[:100])


if __name__ == "__main__":
    main()