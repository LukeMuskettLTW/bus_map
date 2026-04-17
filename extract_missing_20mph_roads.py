import json
import csv
from collections import defaultdict
from pathlib import Path

INPUT = Path("20mph_osm_dated.geojson")
OUTPUT = Path("missing_20mph_roads.csv")

def is_20mph(value):
    s = str(value or "").strip().lower()
    return s in {"20", "20 mph", "20mph"}

def main():
    print("Loading geojson...")
    data = json.loads(INPUT.read_text(encoding="utf-8"))

    roads = defaultdict(lambda: {
        "name": None,
        "borough_name": None,
        "segments": 0
    })

    for f in data["features"]:
        props = f.get("properties", {})

        # only roads that are currently tagged 20mph
        if not is_20mph(props.get("maxspeed")):
            continue

        # only roads WITHOUT an assigned introduction year
        year = props.get("introduced_year")
        if year not in (None, "", 0):
            continue

        name = (props.get("name") or props.get("ref") or "").strip()
        borough = (props.get("borough_name") or "").strip()

        if not name:
            continue

        key = (name, borough)

        roads[key]["name"] = name
        roads[key]["borough_name"] = borough
        roads[key]["segments"] += 1

    print(f"Found {len(roads)} roads missing dates")

    rows = sorted(
        roads.values(),
        key=lambda x: (-x["segments"], x["borough_name"], x["name"])
    )

    print("Writing CSV...")
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "borough_name", "segments"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print("DONE")

if __name__ == "__main__":
    main()