from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

IN_FILE = DATA / "cycle_routes.geojson"
OUT_FILE = DATA / "cycle_major_schemes.geojson"

# Minimum length (in degrees) to count as a "major" route
# This filters out short/local fragments
MIN_COORDS = 80


def count_coords(geometry):
    """Count total coordinate points in a geometry"""
    if not geometry:
        return 0

    if geometry["type"] == "LineString":
        return len(geometry["coordinates"])

    if geometry["type"] == "MultiLineString":
        return sum(len(line) for line in geometry["coordinates"])

    return 0


def main():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        source = json.load(f)

    source_features = source.get("features", [])
    output_features = []

    for feature in source_features:
        geom = feature.get("geometry")

        coord_count = count_coords(geom)

        # Keep only long routes (major corridors)
        if coord_count < MIN_COORDS:
            continue

        new_feature = {
            "type": "Feature",
            "properties": {
                "name": feature.get("properties", {}).get("name", "Cycle route"),
                "opened_year": 2020,  # placeholder for now
                "status": "open"
            },
            "geometry": geom
        }

        output_features.append(new_feature)

    out_geojson = {
        "type": "FeatureCollection",
        "features": output_features
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out_geojson, f)

    print(f"Source features: {len(source_features)}")
    print(f"Output features: {len(output_features)}")
    print(f"Saved to: {OUT_FILE}")


if __name__ == "__main__":
    main()