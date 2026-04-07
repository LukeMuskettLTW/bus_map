from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parent
file_path = ROOT / "data" / "route_bus_speeds.xlsx"

xls = pd.ExcelFile(file_path)

all_data = []

def find_header_row(df):
    for i in range(0, 40):
        row = df.iloc[i].astype(str).str.lower()
        if row.str.contains("route").any() and row.str.contains("mean").any():
            return i
    return None

def extract_periods(df, header_row):
    for offset in [1, 2, 3]:
        if header_row - offset < 0:
            continue
        row = df.iloc[header_row - offset].astype(str)
        if row.str.contains("P01").any():
            return row
    return None

for sheet in xls.sheet_names:
    try:
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)

        header_row = find_header_row(df)

        if header_row is None:
            print(f"Skipping sheet (no header found): {sheet}")
            continue

        periods_row = extract_periods(df, header_row)

        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].copy()
        df = df.rename(columns=lambda x: str(x).strip())

        route_col = [c for c in df.columns if "route" in c.lower()]
        if not route_col:
            print(f"No route column in {sheet}")
            continue
        route_col = route_col[0]

        df = df[df[route_col].notna()]
        df = df[df[route_col].astype(str).str.strip() != ""]

        speed_cols = []
        period_labels = []

        for i, col in enumerate(df.columns):
            if "mean" in str(col).lower():
                speed_cols.append(col)
                if periods_row is not None:
                    period_labels.append(periods_row.iloc[i])
                else:
                    period_labels.append(col)

        if not speed_cols:
            print(f"No speed columns in {sheet}")
            continue

        df_long = df.melt(
            id_vars=[route_col],
            value_vars=speed_cols,
            var_name="period",
            value_name="mean_speed"
        )

        df_long["period_label"] = period_labels * len(df)
        df_long["route"] = df_long[route_col].astype(str).str.strip()
        df_long["source_sheet"] = sheet

        df_long = df_long[["route", "period_label", "mean_speed", "source_sheet"]]
        df_long = df_long.dropna(subset=["mean_speed"])

        all_data.append(df_long)
        print(f"Processed sheet: {sheet} ({len(df_long)} rows)")

    except Exception as e:
        print(f"Error in sheet {sheet}: {e}")

df_all = pd.concat(all_data, ignore_index=True)

def clean_period(p):
    if isinstance(p, str):
        match = re.search(r'\d{2}/\d{2}/\d{2,4}', p)
        if match:
            return match.group()
    return p

df_all["period_clean"] = df_all["period_label"].apply(clean_period)

output_path = ROOT / "data" / "routes_timeseries_full.csv"
df_all.to_csv(output_path, index=False)

print("\nSaved to:", output_path)
print("Total rows:", len(df_all))
print("Routes:", df_all["route"].nunique())
print("Sheets used:", df_all["source_sheet"].nunique())