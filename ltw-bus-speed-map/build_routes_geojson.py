import requests
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_FILE = ROOT / "data" / "bus_routes.geojson"

BASE = "https://api.tfl.gov.uk"

print("Fetching list of bus routes...")

routes = requests.get(f"{BASE}/Line/Mode/bus").json()

features = []
count = 0

for r in routes:
    route_id = r["id"]

    try:
        url = f"{BASE}/Line/{route_id}/Route/Sequence/all"
        data = requests.get(url).json()

        for seq in data:
            for stop in seq.get("stopPointSequences", []):
                coords = []

                for s in stop.get("stopPoint", []):
                    lat = s.get("lat")
                    lon = s.get("lon")
                    if lat and lon:
                        coords.append([lon, lat])

                if len(coords) > 1:
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "route": route_id
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coords
                        }
                    })
                    count += 1

    except Exception as e:
        print("Skipping route:", route_id)

geojson = {
    "type": "FeatureCollection",
    "features": features
}

with open(OUT_FILE, "w") as f:
    json.dump(geojson, f)

print("Done:", OUT_FILE)
print("Routes:", count)