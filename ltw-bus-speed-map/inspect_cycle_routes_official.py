from pathlib import Path
import json
from pprint import pprint

ROOT = Path(__file__).resolve().parent
IN_FILE = ROOT / "data" / "cycle_routes_official.json"

with open(IN_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print("TOP-LEVEL TYPE:", type(data).__name__)

if isinstance(data, dict):
    print("\nTOP-LEVEL KEYS:")
    print(list(data.keys())[:50])

    for key, value in data.items():
        print(f"\nKEY: {key}")
        print("TYPE:", type(value).__name__)

        if isinstance(value, list):
            print("LIST LENGTH:", len(value))
            if value:
                print("FIRST ITEM TYPE:", type(value[0]).__name__)
                print("FIRST ITEM:")
                pprint(value[0])

        elif isinstance(value, dict):
            print("DICT KEYS:", list(value.keys())[:50])

elif isinstance(data, list):
    print("LIST LENGTH:", len(data))
    if data:
        print("\nFIRST ITEM TYPE:", type(data[0]).__name__)
        print("FIRST ITEM:")
        pprint(data[0])