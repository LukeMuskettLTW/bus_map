import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent

BOROUGHS = ROOT / "data" / "boroughs.geojson"
SPEEDS = ROOT / "data" / "bus_speeds.csv"
OUT = ROOT / "map" / "borough_speeds.geojson"

speed_lookup = {}

with open(SPEEDS, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        borough = (row.get("Borough") or "").strip().lower()
        speed_raw = (row.get("AverageSpeed") or "").strip()

        if not borough:
            continue

        if speed_raw == "":
            speed = None
        else:
            speed = float(speed_raw)

        speed_lookup[borough] = speed

with open(BOROUGHS, encoding="utf-8") as f:
    geo = json.load(f)

for feature in geo["features"]:
    name = feature["properties"]["name"].strip().lower()
    speed = speed_lookup.get(name)
    feature["properties"]["bus_speed"] = speed

OUT.parent.mkdir(exist_ok=True)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(geo, f)

print("Done: borough_speeds.geojson created")