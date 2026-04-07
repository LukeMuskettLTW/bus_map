from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
IN_FILE = ROOT / "data" / "routes_timeseries_full.csv"
OUT_FILE = ROOT / "data" / "route_changes_summary.csv"

MIN_POINTS_PER_ROUTE = 8
MIN_BASE_SPEED_FOR_PCT = 5.0
MAX_REASONABLE_PCT = 200.0
ALLOW_ZERO_LATEST_SPEED = False

PERIOD_RE = re.compile(r"P(\d{2})/(\d{4})", re.IGNORECASE)
SHEET_RE = re.compile(r"^(\d{4})-(\d{2,4})$")


def parse_period_date(period_label: str, source_sheet: str) -> pd.Timestamp:
    """
    Build a synthetic date for sorting/comparison.
    TfL periods are treated as 4-week steps from 1 April of the sheet year.
    """
    label = str(period_label).strip()
    m = PERIOD_RE.search(label)
    if m:
        period_num = int(m.group(1))
        fiscal_year = int(m.group(2))
        base = pd.Timestamp(year=fiscal_year, month=4, day=1)
        return base + pd.Timedelta(days=28 * (period_num - 1))

    sheet_match = SHEET_RE.match(str(source_sheet).strip())
    if sheet_match:
        fiscal_year = int(sheet_match.group(1))
        return pd.Timestamp(year=fiscal_year, month=4, day=1)

    return pd.NaT


def nearest_row(group: pd.DataFrame, target_date: pd.Timestamp) -> pd.Series:
    g = group.copy()
    g["date_diff"] = (g["period_date"] - target_date).abs()
    return g.sort_values(["date_diff", "period_date"]).iloc[0]


def safe_pct_change(latest_speed: float, base_speed: float):
    if pd.isna(latest_speed) or pd.isna(base_speed):
        return pd.NA
    if base_speed <= 0 or base_speed < MIN_BASE_SPEED_FOR_PCT:
        return pd.NA
    pct = ((latest_speed - base_speed) / base_speed) * 100.0
    if abs(pct) > MAX_REASONABLE_PCT:
        return pd.NA
    return pct


def safe_abs_change(latest_speed: float, base_speed: float):
    if pd.isna(latest_speed) or pd.isna(base_speed):
        return pd.NA
    return latest_speed - base_speed


df = pd.read_csv(IN_FILE)
df.columns = [str(c).strip() for c in df.columns]

required = {"route", "period_label", "mean_speed", "source_sheet"}
missing = required - set(df.columns)
if missing:
    raise RuntimeError(f"Missing expected columns: {sorted(missing)}")

df["route"] = df["route"].astype(str).str.strip()
df["mean_speed"] = pd.to_numeric(df["mean_speed"], errors="coerce")

df = df.dropna(subset=["route", "mean_speed"]).copy()
df = df[df["route"] != ""]
df = df[df["route"].str.lower() != "nan"]

df["period_date"] = df.apply(
    lambda r: parse_period_date(r["period_label"], r["source_sheet"]),
    axis=1
)
df = df.dropna(subset=["period_date"]).copy()

# Deduplicate to one mean speed per route / period
df = (
    df.groupby(["route", "period_date", "period_label", "source_sheet"], as_index=False)["mean_speed"]
    .mean()
    .sort_values(["route", "period_date"])
    .reset_index(drop=True)
)

rows = []

for route, group in df.groupby("route"):
    group = group.sort_values("period_date").reset_index(drop=True)
    points = len(group)

    if points < 2:
        continue

    first = group.iloc[0]
    latest = group.iloc[-1]

    latest_speed = float(latest["mean_speed"])

    include_in_map = True
    if points < MIN_POINTS_PER_ROUTE:
        include_in_map = False
    if not ALLOW_ZERO_LATEST_SPEED and latest_speed <= 0:
        include_in_map = False

    row = {
        "route": str(route),
        "points": points,
        "first_period_label": first["period_label"],
        "first_source_sheet": first["source_sheet"],
        "first_date": first["period_date"],
        "first_speed": float(first["mean_speed"]),
        "latest_period_label": latest["period_label"],
        "latest_source_sheet": latest["source_sheet"],
        "latest_date": latest["period_date"],
        "latest_speed": latest_speed,
    }

    # Full period
    row["prev_speed_full"] = row["first_speed"]
    row["abs_change_full"] = safe_abs_change(row["latest_speed"], row["prev_speed_full"])
    row["pct_change_full"] = safe_pct_change(row["latest_speed"], row["prev_speed_full"])

    # Rolling comparisons
    for years, label in [(1, "1yr"), (5, "5yr"), (10, "10yr")]:
        target = row["latest_date"] - pd.DateOffset(years=years)
        try:
            base = nearest_row(group, target)
            base_speed = float(base["mean_speed"])

            row[f"base_period_label_{label}"] = base["period_label"]
            row[f"base_source_sheet_{label}"] = base["source_sheet"]
            row[f"base_date_{label}"] = base["period_date"]
            row[f"prev_speed_{label}"] = base_speed
            row[f"abs_change_{label}"] = safe_abs_change(row["latest_speed"], base_speed)
            row[f"pct_change_{label}"] = safe_pct_change(row["latest_speed"], base_speed)
        except Exception:
            row[f"base_period_label_{label}"] = pd.NA
            row[f"base_source_sheet_{label}"] = pd.NA
            row[f"base_date_{label}"] = pd.NaT
            row[f"prev_speed_{label}"] = pd.NA
            row[f"abs_change_{label}"] = pd.NA
            row[f"pct_change_{label}"] = pd.NA

    flags = []

    if points < MIN_POINTS_PER_ROUTE:
        flags.append("too_few_points")
    if latest_speed <= 0:
        flags.append("latest_speed_zero_or_negative")
    if row["first_speed"] < MIN_BASE_SPEED_FOR_PCT:
        flags.append("full_base_speed_low")

    for label in ["1yr", "5yr", "10yr"]:
        prev_speed = row.get(f"prev_speed_{label}", pd.NA)
        if pd.notna(prev_speed) and prev_speed < MIN_BASE_SPEED_FOR_PCT:
            flags.append(f"base_speed_{label}_low")

    row["include_in_map"] = include_in_map
    row["flags"] = ";".join(flags)

    rows.append(row)

final = pd.DataFrame(rows)

if final.empty:
    raise RuntimeError("No output rows were produced.")

final = final.sort_values(["include_in_map", "pct_change_full"], ascending=[False, False])
final.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")

report_df = final[final["include_in_map"] == True].copy()

print("\n=== Largest improvements (overall %) ===")
print(
    report_df.sort_values("pct_change_full", ascending=False)[
        ["route", "first_source_sheet", "latest_source_sheet", "prev_speed_full", "latest_speed", "abs_change_full", "pct_change_full"]
    ].head(15).to_string(index=False)
)

print("\n=== Largest declines (overall %) ===")
print(
    report_df.sort_values("pct_change_full", ascending=True)[
        ["route", "first_source_sheet", "latest_source_sheet", "prev_speed_full", "latest_speed", "abs_change_full", "pct_change_full"]
    ].head(15).to_string(index=False)
)

print("\n=== Largest improvements (1 year %) ===")
print(
    report_df.sort_values("pct_change_1yr", ascending=False)[
        ["route", "base_source_sheet_1yr", "latest_source_sheet", "prev_speed_1yr", "latest_speed", "abs_change_1yr", "pct_change_1yr"]
    ].head(15).to_string(index=False)
)

print("\n=== Largest declines (1 year %) ===")
print(
    report_df.sort_values("pct_change_1yr", ascending=True)[
        ["route", "base_source_sheet_1yr", "latest_source_sheet", "prev_speed_1yr", "latest_speed", "abs_change_1yr", "pct_change_1yr"]
    ].head(15).to_string(index=False)
)

print(f"\nSaved to: {OUT_FILE}")
print(f"Routes analysed: {final['route'].nunique()}")
print(f"Routes included in map/reporting: {report_df['route'].nunique()}")