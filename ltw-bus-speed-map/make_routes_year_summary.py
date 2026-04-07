from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parent
INFILE = ROOT / "data" / "routes_timeseries_full.csv"
OUTFILE = ROOT / "data" / "routes_year_summary.csv"

df = pd.read_csv(INFILE)

# Clean column names
df.columns = [str(c).strip().lower() for c in df.columns]

print("Columns found:")
print(df.columns.tolist())
print()

route_col = "route"
speed_col = "mean_speed"
date_col = "period_clean"   # we know this exists

print("Using columns:")
print(f"Route: {route_col}")
print(f"Date: {date_col}")
print(f"Speed: {speed_col}")
print()

# --- Clean data ---
df[route_col] = df[route_col].astype(str).str.strip().str.upper()
df[speed_col] = pd.to_numeric(df[speed_col], errors="coerce")

# --- Extract year manually ---
def extract_year(value):
    if pd.isna(value):
        return None
    s = str(value)

    # Look for 4-digit year
    match = re.search(r"\b(20\d{2})\b", s)
    if match:
        return int(match.group(1))

    return None

df["year"] = df[date_col].apply(extract_year)

# Drop bad rows
df = df.dropna(subset=[route_col, "year", speed_col]).copy()

# --- Aggregate ---
year_summary = (
    df.groupby([route_col, "year"], as_index=False)[speed_col]
      .mean()
      .rename(columns={
          route_col: "route",
          speed_col: "avg_speed"
      })
      .sort_values(["route", "year"])
)

year_summary.to_csv(OUTFILE, index=False)

print(f"Saved: {OUTFILE}")
print(f"Rows: {len(year_summary)}")
print(year_summary.head(20).to_string(index=False))