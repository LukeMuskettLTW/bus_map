import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILE = ROOT / "data" / "cycle_major_schemes.geojson"

with open(FILE, "r", encoding="utf-8") as f:
    gj = json.load(f)

fallbacks = []

for feat in gj.get("features", []):
    p = feat.get("properties", {}) or {}
    code = str(
        p.get("route_code")
        or p.get("Label")
        or p.get("label")
        or ""
    ).upper().strip()
    opened = p.get("opened_year")

    if opened == 2020:
        name = p.get("name") or p.get("Route_Name") or p.get("route_name") or ""
        fallbacks.append((code, name))

print(f"Fallback entries: {len(fallbacks)}\n")
for code, name in sorted(set(fallbacks)):
    print(f"{code:>6} | {name}")