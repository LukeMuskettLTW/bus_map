from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
IN_FILE = ROOT / "data" / "route_bus_speeds.xlsx"
OUT_FILE = ROOT / "data" / "routes_timeseries_full.csv"

# Open workbook and list all sheets
xls = pd.ExcelFile(IN_FILE)
sheets = xls.sheet_names

records = []

for sheet in sheets:
    print(f"Processing sheet: {sheet}")

    try:
        # Skip the title / notes block at the top
        df = pd.read_excel(IN_FILE, sheet_name=sheet, skiprows=24)
    except Exception as e:
        print(f"  Skipping sheet {sheet} (read error): {e}")
        continue

    # Remove completely empty columns
    df = df.dropna(axis=1, how="all")

    if df.empty or len(df.columns) < 2:
        print(f"  Skipping sheet {sheet} (no usable columns)")
        continue

    # Find the route column: first non-speed column with lots of values
    route_col = None
    for c in df.columns:
        c_str = str(c).strip().lower()

        if "mean" in c_str or "speed" in c_str:
            continue

        non_null = df[c].dropna()
        if len(non_null) > 50:
            route_col = c
            break

    if route_col is None:
        print(f"  Skipping sheet {sheet} (could not identify route column)")
        continue

    df = df.rename(columns={route_col: "Route"})

    # Find usable speed columns: numeric columns with lots of values
    speed_cols = []
    for c in df.columns:
        if c == "Route":
            continue

        series = pd.to_numeric(df[c], errors="coerce")
        if series.notna().sum() > 50:
            speed_cols.append(c)

    if not speed_cols:
        print(f"  Skipping sheet {sheet} (no usable speed columns)")
        continue

    # Extract long-format records
    for _, row in df.iterrows():
        route = row["Route"]

        # Handle odd cases where pandas gives a Series
        if isinstance(route, pd.Series):
            route = route.iloc[0]

        if pd.isna(route):
            continue

        route = str(route).strip()

        # Skip junk rows
        if route == "" or route.lower() in ["nan", "route"]:
            continue

        # Skip obvious non-route rows
        if "period commencing" in route.lower():
            continue
        if "mean obs speed" in route.lower():
            continue

        for col in speed_cols:
            speed = pd.to_numeric(row[col], errors="coerce")
            if pd.isna(speed):
                continue

            period = str(col).strip()

            records.append({
                "Route": route,
                "Period": period,
                "Speed": float(speed),
                "SourceSheet": sheet
            })

out_df = pd.DataFrame(records)

if out_df.empty:
    raise RuntimeError("No route time-series rows were extracted from any sheet.")

# Remove duplicates just in case
out_df = out_df.drop_duplicates(subset=["Route", "Period", "SourceSheet"])

# Convert Period to datetime where possible
out_df["Period"] = pd.to_datetime(out_df["Period"], errors="coerce")

# Drop rows where period could not be parsed
out_df = out_df.dropna(subset=["Period"])

# Final sort
out_df = out_df.sort_values(["Route", "Period", "SourceSheet"])

# Save
out_df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")

print("\nDone:", OUT_FILE)
print(f"Rows: {len(out_df)}")
print(f"Routes: {out_df['Route'].nunique()}")
print(f"Periods: {out_df['Period'].nunique()}")
print(f"Sheets used: {out_df['SourceSheet'].nunique()}")

print("\nFirst 20 rows:")
print(out_df.head(20).to_string(index=False))

print("\nSheets found:")
print(sheets)