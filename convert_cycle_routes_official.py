from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

IN_FILE = DATA / "cycle_routes_official.json"
OUT_FILE = DATA / "cycle_routes_official.geojson"


def main():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    features_out = []

    # Handle common ESRI-style structure
    for ftr in data.get("features", []):
        geom = ftr.get("geometry", {})
        props = ftr.get("properties", {})

        # ESRI "paths" → GeoJSON LineString / MultiLineString
        if "paths" in geom:
            paths = geom["paths"]

            if len(paths) == 1:
                geometry = {
                    "type": "LineString",
                    "coordinates": paths[0]
                }
            else:
                geometry = {
                    "type": "MultiLineString",
                    "coordinates": paths
                }

        else:
            continue

        new_feature = {
            "type": "Feature",
            "properties": {
                "name": props.get("name") or props.get("route_name") or "Cycle route",
                "status": props.get("status"),
                "programme": props.get("programme"),
                "opened_year": 2020  # placeholder for now
            },
            "geometry": geometry
        }

        features_out.append(new_feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features_out
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson, f)

    print(f"Converted {len(features_out)} features → {OUT_FILE}")


if __name__ == "__main__":
    main()