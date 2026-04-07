import pandas as pd
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
IN_FILE = ROOT / "data" / "tfl_bus_speeds.xlsx"
OUT_FILE = ROOT / "data" / "bus_speeds.csv"

LONDON_BOROUGHS = {
    "barking and dagenham",
    "barnet",
    "bexley",
    "brent",
    "bromley",
    "camden",
    "croydon",
    "ealing",
    "enfield",
    "greenwich",
    "hackney",
    "hammersmith and fulham",
    "haringey",
    "harrow",
    "havering",
    "hillingdon",
    "hounslow",
    "islington",
    "kensington and chelsea",
    "kingston upon thames",
    "lambeth",
    "lewisham",
    "merton",
    "newham",
    "redbridge",
    "richmond upon thames",
    "southwark",
    "sutton",
    "tower hamlets",
    "waltham forest",
    "wandsworth",
    "westminster",
}

NAME_FIXES = {
    "city of westminster": "westminster",
    "westminster city": "westminster",
    "royal borough of kensington and chelsea": "kensington and chelsea",
    "kensington & chelsea": "kensington and chelsea",
    "royal borough of kingston upon thames": "kingston upon thames",
    "royal borough of greenwich": "greenwich",
    "hammersmith & fulham": "hammersmith and fulham",
    "richmond upon thames london borough": "richmond upon thames",
}

def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

def normalise_name(name):
    name = clean_text(name).lower()
    name = re.sub(r"\s+", " ", name)
    return NAME_FIXES.get(name, name)

def score_sheet(df):
    score = 0
    cols = [str(c).strip().lower() for c in df.columns]

    for c in cols:
        if "borough" in c:
            score += 4
        if "speed" in c:
            score += 4
        if "mph" in c:
            score += 2
        if "average" in c:
            score += 1

    sample_text = " ".join(cols)
    if "borough" in sample_text and ("speed" in sample_text or "mph" in sample_text):
        score += 5

    return score

def choose_columns(df):
    cols = list(df.columns)

    borough_col = None
    speed_col = None

    for c in cols:
        lc = str(c).strip().lower()
        if borough_col is None and "borough" in lc:
            borough_col = c
        if speed_col is None and ("speed" in lc or "mph" in lc):
            speed_col = c

    if borough_col is None:
        for c in cols:
            lc = str(c).strip().lower()
            if "local authority" in lc or "area" == lc:
                borough_col = c
                break

    return borough_col, speed_col

if not IN_FILE.exists():
    raise FileNotFoundError(f"Missing input file: {IN_FILE}")

excel = pd.ExcelFile(IN_FILE)
best_sheet = None
best_df = None
best_score = -1

for sheet in excel.sheet_names:
    try:
        df = pd.read_excel(IN_FILE, sheet_name=sheet)
        df.columns = [clean_text(c) for c in df.columns]
        s = score_sheet(df)
        print(f"Sheet: {sheet} | score: {s} | columns: {list(df.columns)}")
        if s > best_score:
            best_score = s
            best_sheet = sheet
            best_df = df
    except Exception as e:
        print(f"Skipping sheet {sheet}: {e}")

if best_df is None:
    raise RuntimeError("Could not read any sheet from the workbook.")

print(f"\nUsing sheet: {best_sheet}")

borough_col, speed_col = choose_columns(best_df)

if borough_col is None or speed_col is None:
    raise RuntimeError(
        f"Could not identify borough/speed columns in sheet '{best_sheet}'. "
        f"Columns found: {list(best_df.columns)}"
    )

print(f"Borough column: {borough_col}")
print(f"Speed column: {speed_col}")

out_rows = []

for _, row in best_df.iterrows():
    borough_raw = clean_text(row[borough_col])
    speed_raw = row[speed_col]

    borough = normalise_name(borough_raw)

    if borough not in LONDON_BOROUGHS:
        continue

    speed = pd.to_numeric(speed_raw, errors="coerce")
    if pd.isna(speed):
        continue

    out_rows.append({
        "Borough": borough.title().replace("And", "and"),
        "AverageSpeed": round(float(speed), 2)
    })

out_df = pd.DataFrame(out_rows).drop_duplicates(subset=["Borough"]).sort_values("Borough")

if out_df.empty:
    raise RuntimeError("No London borough speed rows were found.")

out_df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")

print(f"\nWrote {len(out_df)} rows to: {OUT_FILE}")
print(out_df.to_string(index=False))