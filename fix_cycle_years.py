import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILE = ROOT / "data" / "cycle_major_schemes.geojson"

with open(FILE, "r", encoding="utf-8") as f:
    gj = json.load(f)

# Pragmatic year lookup for clearly known historic schemes.
# Expand this over time if you want.
YEAR_MAP = {
    "CS2": 2011,
    "CS3": 2010,
    "CS5": 2017,
    "CS6": 2016,
    "CS7": 2010,
    "CS8": 2010,
    "CS11": 2020,
    "Q1": 2016,
    "C1": 2016,   # broadly former CS3 corridor / Embankment-era network
    "C2": 2011,   # broadly former CS2 corridor
    "C3": 2010,
    "C5": 2017,
    "C6": 2016,
    "C8": 2020,
    "C9": 2020,
    "C10": 2020,
}

def get_code(props):
    return str(
        props.get("route_code")
        or props.get("Label")
        or props.get("label")
        or ""
    ).upper().strip()

updated = 0
unknown = 0

for feat in gj.get("features", []):
    props = feat.get("properties", {}) or {}
    code = get_code(props)

    if code in YEAR_MAP:
        props["opened_year"] = YEAR_MAP[code]
        updated += 1
    else:
        props["opened_year"] = None
        unknown += 1

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(gj, f, indent=2)

print(f"Cycle scheme years updated: {updated}")
print(f"Unknown / unset years: {unknown}")
print("Unknown schemes will now be hidden in year-by-year mode.")