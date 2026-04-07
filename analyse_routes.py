from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
IN_FILE = ROOT / "data" / "routes_timeseries.csv"

df = pd.read_csv(IN_FILE)

# Ensure sorted
df["Period"] = pd.to_datetime(df["Period"])
df = df.sort_values(["Route", "Period"])

# Latest speed
latest = df.groupby("Route").last().reset_index()
latest = latest.rename(columns={"Speed": "LatestSpeed", "Period": "LatestPeriod"})

# First speed
first = df.groupby("Route").first().reset_index()
first = first.rename(columns={"Speed": "FirstSpeed", "Period": "FirstPeriod"})

# Merge
summary = latest.merge(first, on="Route")

# Absolute change
summary["Change"] = summary["LatestSpeed"] - summary["FirstSpeed"]

# Percentage change
summary["PctChange"] = (summary["Change"] / summary["FirstSpeed"]) * 100

# Clean weird values (e.g. divide by zero)
summary = summary.replace([float("inf"), -float("inf")], pd.NA)

# Save
summary.to_csv(ROOT / "data" / "routes_summary.csv", index=False)

# ---------- OUTPUTS ----------

print("\n=== Biggest percentage decline ===")
print(summary.sort_values("PctChange").head(15).to_string(index=False))

print("\n=== Biggest percentage improvement ===")
print(summary.sort_values("PctChange", ascending=False).head(15).to_string(index=False))

print("\n=== Slowest routes (latest) ===")
print(summary.sort_values("LatestSpeed").head(15).to_string(index=False))

print("\n=== Fastest routes (latest) ===")
print(summary.sort_values("LatestSpeed", ascending=False).head(15).to_string(index=False))