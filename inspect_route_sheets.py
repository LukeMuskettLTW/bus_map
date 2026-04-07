from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
IN_FILE = ROOT / "data" / "route_bus_speeds.xlsx"

xls = pd.ExcelFile(IN_FILE)
sheets = xls.sheet_names

skip_options = [20, 22, 24, 26, 28, 30]

for sheet in sheets:
    print("\n" + "=" * 80)
    print(f"SHEET: {sheet}")
    print("=" * 80)

    for skip in skip_options:
        try:
            df = pd.read_excel(IN_FILE, sheet_name=sheet, skiprows=skip)
            df = df.dropna(axis=1, how="all")

            print(f"\n--- skiprows={skip} ---")
            print(f"shape: {df.shape}")
            print("columns:")
            print([str(c) for c in df.columns[:12]])

            # show first few non-empty rows
            preview = df.head(5)
            with pd.option_context("display.max_columns", 12, "display.width", 200):
                print(preview)

        except Exception as e:
            print(f"\n--- skiprows={skip} ---")
            print(f"ERROR: {e}")