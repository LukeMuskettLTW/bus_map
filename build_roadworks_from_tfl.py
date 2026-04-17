import requests
import json
from pathlib import Path
from datetime import datetime

OUT = Path("data/roadworks.geojson")

# You can change this date dynamically later if you want
START = "2013-01-01"
END = "2025-12-31"

URL = f"https://api.tfl.gov.uk/Road/all/Street/Disruption?startDate={START}&endDate={END}"

def parse_dt(x):
    try:
        return datetime.fromisoformat(x.replace("Z", ""))
    except:
        return None

def main():
    print("Fetching TfL roadworks...")
    r = requests.get(URL)
    r.raise_for_status()
    data = r.json()

    features = []

    for item in data:

        start = parse_dt(item.get("startDateTime"))
        end = parse_dt(item.get("endDateTime"))

        if not start or not end:
            continue

        duration_days = (end - start).days

        lat = item.get("startLat")
        lon = item.get("startLon")

        if lat is None or lon is None:
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "street": item.get("streetName"),
                "location": item.get("location"),
                "category": item.get("category"),
                "subcategory": item.get("subCategory"),
                "severity": item.get("severity"),
                "closure": item.get("closure"),
                "comments": item.get("comments"),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "duration_days": duration_days
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(geojson, indent=2))

    print(f"DONE: {OUT}")
    print(f"Features: {len(features)}")

if __name__ == "__main__":
    main()