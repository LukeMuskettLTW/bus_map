from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
IN_FILE = ROOT / "data" / "route_bus_speeds.xlsx"
OUT_FILE = ROOT / "data" / "routes_clean.csv"

# Read the first sheet, skipping the title block
df = pd.read_excel(IN_FILE, sheet_name=0, skiprows=24)

# Drop completely empty columns
df = df.dropna(axis=1, how="all")

# Find the route column: first column with lots of non-null values that is not a date-like column
route_col = None
for c in df.columns:
    series = df[c]
    non_null = series.dropna()
    if len(non_null) < 20:
        continue
    # Try numeric conversion: routes can be numeric or text like N8, SL6, B13
    sample = non_null.astype(str).str.strip().head(50)
    # Exclude obvious date/header columns
    if "mean" in str(c).lower() or "speed" in str(c).lower():
        continue
    route_col = c
    break

if route_col is None:
    raise RuntimeError("Could not find a usable route column.")

# Find the latest usable speed column by working right-to-left
candidate_cols = [c for c in df.columns if c != route_col]
speed_col = None
for c in reversed(candidate_cols):
    series = pd.to_numeric(df[c], errors="coerce")
    if series.notna().sum() > 20:
        speed_col = c
        break

if speed_col is None:
    raise RuntimeError("Could not find a usable speed column.")

print("Using route column:", route_col)
print("Using speed column:", speed_col)

df = df[[route_col, speed_col]].copy()
df.columns = ["Route", "Speed"]

# Clean
df["Route"] = df["Route"].astype(str).str.strip()
df["Speed"] = pd.to_numeric(df["Speed"], errors="coerce")

# Keep real rows only
df = df[df["Speed"].notna()]
df = df[df["Route"] != ""]
df = df[df["Route"].str.lower() != "nan"]
df = df[~df["Route"].str.contains("route", case=False, na=False)]

# Remove duplicate route rows, keep the first
df = df.drop_duplicates(subset=["Route"]).sort_values("Route")

df.to_csv(OUT_FILE, index=False)

print("Done:", OUT_FILE)
print(df.head(20))
print(f"Rows saved: {len(df)}")