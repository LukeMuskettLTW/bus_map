import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILE = ROOT / "data" / "cycle_major_schemes.geojson"

with open(FILE, "r", encoding="utf-8") as f:
    gj = json.load(f)

# Historical lookup.
# "historical_label" is what should be shown on the map/popup for a historical timeline.
# "current_label" keeps the modern TfL label where helpful.
LOOKUP = {
    # Older Cycle Superhighways
    "C2":  {"opened_year": 2011, "historical_label": "CS2",  "current_label": "C2",  "label_note": "Current branding C2; originally Cycle Superhighway 2"},
    "C3":  {"opened_year": 2010, "historical_label": "CS3",  "current_label": "C3",  "label_note": "Current branding C3; originally Cycle Superhighway 3"},
    "C5":  {"opened_year": 2017, "historical_label": "CS5",  "current_label": "C5",  "label_note": "Current branding C5; originally Cycle Superhighway 5"},
    "C6":  {"opened_year": 2016, "historical_label": "CS6",  "current_label": "C6",  "label_note": "Current branding C6; originally Cycle Superhighway 6"},
    "C7":  {"opened_year": 2010, "historical_label": "CS7",  "current_label": "C7",  "label_note": "Current branding C7; originally Cycle Superhighway 7"},
    "C8":  {"opened_year": 2010, "historical_label": "CS8",  "current_label": "C8",  "label_note": "Current branding C8; originally Cycle Superhighway 8"},
    "CS2": {"opened_year": 2011, "historical_label": "CS2",  "current_label": "C2",  "label_note": "Cycle Superhighway 2"},
    "CS3": {"opened_year": 2010, "historical_label": "CS3",  "current_label": "C3",  "label_note": "Cycle Superhighway 3"},
    "CS5": {"opened_year": 2017, "historical_label": "CS5",  "current_label": "C5",  "label_note": "Cycle Superhighway 5"},
    "CS6": {"opened_year": 2016, "historical_label": "CS6",  "current_label": "C6",  "label_note": "Cycle Superhighway 6"},
    "CS7": {"opened_year": 2010, "historical_label": "CS7",  "current_label": "C7",  "label_note": "Cycle Superhighway 7"},
    "CS8": {"opened_year": 2010, "historical_label": "CS8",  "current_label": "C8",  "label_note": "Cycle Superhighway 8"},
    "CS11":{"opened_year": 2020, "historical_label": "CS11", "current_label": "CS11","label_note": "Cycle Superhighway 11"},

    # Quietways
    "Q1":  {"opened_year": 2016, "historical_label": "Q1",   "current_label": "Q1",  "label_note": "Quietway 1"},
    "Q2":  {"opened_year": 2017, "historical_label": "Q2",   "current_label": "Q2",  "label_note": "Quietway 2"},
    "Q3":  {"opened_year": 2018, "historical_label": "Q3",   "current_label": "Q3",  "label_note": "Quietway 3"},
    "Q15": {"opened_year": 2021, "historical_label": "Q15",  "current_label": "Q15", "label_note": "Quietway 15"},

    # C1 is not a simple former CS label; use current label but with note
    "C1":  {"opened_year": 2016, "historical_label": "C1",   "current_label": "C1",  "label_note": "Embankment / central east-west cycle route"},
    "C4":  {"opened_year": 2019, "historical_label": "C4",   "current_label": "C4",  "label_note": "Cycleway 4"},
    "C9":  {"opened_year": 2020, "historical_label": "C9",   "current_label": "C9",  "label_note": "Cycleway 9"},
    "C10": {"opened_year": 2020, "historical_label": "C10",  "current_label": "C10", "label_note": "Cycleway 10"},
    "C11": {"opened_year": 2020, "historical_label": "C11",  "current_label": "C11", "label_note": "Cycleway 11"},
    "C12": {"opened_year": 2020, "historical_label": "C12",  "current_label": "C12", "label_note": "Cycleway 12"},
    "C13": {"opened_year": 2020, "historical_label": "C13",  "current_label": "C13", "label_note": "Cycleway 13"},
    "C14": {"opened_year": 2020, "historical_label": "C14",  "current_label": "C14", "label_note": "Cycleway 14"},
    "C15": {"opened_year": 2020, "historical_label": "C15",  "current_label": "C15", "label_note": "Cycleway 15"},
    "C16": {"opened_year": 2020, "historical_label": "C16",  "current_label": "C16", "label_note": "Cycleway 16"},
    "C17": {"opened_year": 2020, "historical_label": "C17",  "current_label": "C17", "label_note": "Cycleway 17"},
    "C18": {"opened_year": 2020, "historical_label": "C18",  "current_label": "C18", "label_note": "Cycleway 18"},
    "C19": {"opened_year": 2020, "historical_label": "C19",  "current_label": "C19", "label_note": "Cycleway 19"},
    "C20": {"opened_year": 2020, "historical_label": "C20",  "current_label": "C20", "label_note": "Cycleway 20"},
    "C21": {"opened_year": 2021, "historical_label": "C21",  "current_label": "C21", "label_note": "Cycleway 21"},
    "C22": {"opened_year": 2021, "historical_label": "C22",  "current_label": "C22", "label_note": "Cycleway 22"},
    "C23": {"opened_year": 2021, "historical_label": "C23",  "current_label": "C23", "label_note": "Cycleway 23"},
    "C24": {"opened_year": 2021, "historical_label": "C24",  "current_label": "C24", "label_note": "Cycleway 24"},
    "C25": {"opened_year": 2021, "historical_label": "C25",  "current_label": "C25", "label_note": "Cycleway 25"},
    "C26": {"opened_year": 2021, "historical_label": "C26",  "current_label": "C26", "label_note": "Cycleway 26"},
    "C27": {"opened_year": 2021, "historical_label": "C27",  "current_label": "C27", "label_note": "Cycleway 27"},
    "C28": {"opened_year": 2021, "historical_label": "C28",  "current_label": "C28", "label_note": "Cycleway 28"},
    "C29": {"opened_year": 2021, "historical_label": "C29",  "current_label": "C29", "label_note": "Cycleway 29"},
    "C30": {"opened_year": 2021, "historical_label": "C30",  "current_label": "C30", "label_note": "Cycleway 30"},
    "C31": {"opened_year": 2022, "historical_label": "C31",  "current_label": "C31", "label_note": "Cycleway 31"},
    "C32": {"opened_year": 2022, "historical_label": "C32",  "current_label": "C32", "label_note": "Cycleway 32"},
    "C33": {"opened_year": 2022, "historical_label": "C33",  "current_label": "C33", "label_note": "Cycleway 33"},
    "C34": {"opened_year": 2022, "historical_label": "C34",  "current_label": "C34", "label_note": "Cycleway 34"},
    "C35": {"opened_year": 2022, "historical_label": "C35",  "current_label": "C35", "label_note": "Cycleway 35"},
    "C38": {"opened_year": 2022, "historical_label": "C38",  "current_label": "C38", "label_note": "Cycleway 38"},
    "C39": {"opened_year": 2022, "historical_label": "C39",  "current_label": "C39", "label_note": "Cycleway 39"},
    "C40": {"opened_year": 2022, "historical_label": "C40",  "current_label": "C40", "label_note": "Cycleway 40"},
    "C41": {"opened_year": 2023, "historical_label": "C41",  "current_label": "C41", "label_note": "Cycleway 41"},
    "C42": {"opened_year": 2023, "historical_label": "C42",  "current_label": "C42", "label_note": "Cycleway 42"},
    "C44": {"opened_year": 2023, "historical_label": "C44",  "current_label": "C44", "label_note": "Cycleway 44"},
    "C48": {"opened_year": 2023, "historical_label": "C48",  "current_label": "C48", "label_note": "Cycleway 48"},
    "C49": {"opened_year": 2023, "historical_label": "C49",  "current_label": "C49", "label_note": "Cycleway 49"},
    "C50": {"opened_year": 2023, "historical_label": "C50",  "current_label": "C50", "label_note": "Cycleway 50"},
    "C51": {"opened_year": 2024, "historical_label": "C51",  "current_label": "C51", "label_note": "Cycleway 51"},
    "C52": {"opened_year": 2024, "historical_label": "C52",  "current_label": "C52", "label_note": "Cycleway 52"},
    "C55": {"opened_year": 2024, "historical_label": "C55",  "current_label": "C55", "label_note": "Cycleway 55"},
    "C56": {"opened_year": 2024, "historical_label": "C56",  "current_label": "C56", "label_note": "Cycleway 56"},
    "C57": {"opened_year": 2024, "historical_label": "C57",  "current_label": "C57", "label_note": "Cycleway 57"},
    "C58": {"opened_year": 2024, "historical_label": "C58",  "current_label": "C58", "label_note": "Cycleway 58"},
    "C60": {"opened_year": 2024, "historical_label": "C60",  "current_label": "C60", "label_note": "Cycleway 60"},
    "C61": {"opened_year": 2024, "historical_label": "C61",  "current_label": "C61", "label_note": "Cycleway 61"},
    "C62": {"opened_year": 2024, "historical_label": "C62",  "current_label": "C62", "label_note": "Cycleway 62"},
    "C66": {"opened_year": 2024, "historical_label": "C66",  "current_label": "C66", "label_note": "Cycleway 66"},
}

GENERIC_CODES_TO_EXCLUDE = {"C", "Q", ""}

def get_code(props):
    return str(
        props.get("route_code")
        or props.get("Label")
        or props.get("label")
        or ""
    ).upper().strip()

updated = 0
excluded = 0
unknown = []

new_features = []

for feat in gj.get("features", []):
    props = feat.get("properties", {}) or {}
    code = get_code(props)

    # Drop vague generic records entirely
    if code in GENERIC_CODES_TO_EXCLUDE:
        excluded += 1
        continue

    if code in LOOKUP:
        item = LOOKUP[code]
        props["opened_year"] = item["opened_year"]
        props["historical_label"] = item["historical_label"]
        props["current_label"] = item["current_label"]
        props["label_note"] = item["label_note"]
        updated += 1
    else:
        # Keep route, but mark as unknown rather than inventing history
        props["opened_year"] = None
        props["historical_label"] = code if code else "Unknown"
        props["current_label"] = code if code else "Unknown"
        props["label_note"] = "Opening year not yet assigned"
        unknown.append((code, props.get("name") or props.get("Route_Name") or ""))

    feat["properties"] = props
    new_features.append(feat)

gj["features"] = new_features

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(gj, f, indent=2)

print(f"Updated with historical labels: {updated}")
print(f"Excluded generic records: {excluded}")
print(f"Still unknown: {len(unknown)}")

if unknown:
    print("\nUnknown codes still needing review:")
    for code, name in sorted(set(unknown)):
        print(f"{code:>6} | {name}")