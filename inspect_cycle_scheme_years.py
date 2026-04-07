import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
FILE = ROOT / "data" / "cycle_major_schemes.geojson"

with open(FILE, "r", encoding="utf-8") as f:
    gj = json.load(f)

features = gj.get("features", [])
print(f"Features: {len(features)}\n")

years = []
rows = []

for feat in features:
    p = feat.get("properties", {}) or {}
    name = p.get("name") or p.get("Route_Name") or p.get("route_name") or "Unnamed"
    code = p.get("route_code") or p.get("Label") or p.get("label") or ""
    opened = p.get("opened_year") or p.get("OpenedYear") or p.get("year_opened") or p.get("open_year") or p.get("year")
    rows.append((str(code), str(name), opened))
    years.append(opened)

print("Year counts:")
for year, count in sorted(Counter(years).items(), key=lambda x: (str(x[0]))):
    print(f"{year}: {count}")

print("\nFirst 50 schemes:")
for code, name, opened in rows[:50]:
    print(f"{code:>6} | {opened!s:>6} | {name}")