import pandas as pd
import geopandas as gpd
from pathlib import Path

# === FILE PATHS ===
RAW_FILE = Path(r"C:\Users\Luke.Muskett\OneDrive - Transport Focus\Documents\roadworks\roadworks_raw.csv")
OUTPUT_FILE = Path(r"C:\Users\Luke.Muskett\OneDrive - Transport Focus\Documents\roadworks\roadworks_points.geojson")

LATITUDE_CANDIDATES = ["latitude", "lat", "y", "Latitude"]
LONGITUDE_CANDIDATES = ["longitude", "lon", "lng", "x", "Longitude"]

def find_col(df, candidates):
    for c in candidates:
        for col in df.columns:
            if col.lower() == c.lower():
                return col
    return None

def classify_authority(val):
    if not val:
        return "Unknown"
    val = str(val).lower()

    if "transport for london" in val or "tfl" in val:
        return "TfL"

    # everything else = borough / other
    return "Borough or other"

def main():
    print("Loading raw data...")
    df = pd.read_csv(RAW_FILE)

    lat_col = find_col(df, LATITUDE_CANDIDATES)
    lon_col = find_col(df, LONGITUDE_CANDIDATES)

    if not lat_col or not lon_col:
        raise RuntimeError("Latitude/longitude columns not found")

    df = df.dropna(subset=[lat_col, lon_col]).copy()

    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df = df.dropna(subset=[lat_col, lon_col])

    print(f"Rows with coords: {len(df)}")

    # === CLASSIFY ROAD MANAGER ===
    authority_col = None
    for c in df.columns:
        if "authority" in c.lower():
            authority_col = c
            break

    if authority_col:
        df["road_manager"] = df[authority_col].apply(classify_authority)
    else:
        df["road_manager"] = "Unknown"

    # === CREATE GEO ===
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326"
    )

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    gdf.to_file(OUTPUT_FILE, driver="GeoJSON")

    print(f"Done: {OUTPUT_FILE}")
    print(f"Features: {len(gdf)}")

if __name__ == "__main__":
    main()