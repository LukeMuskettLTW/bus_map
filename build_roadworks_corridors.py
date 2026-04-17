import pandas as pd
import geopandas as gpd
from pathlib import Path

# === FILE PATHS ===
RAW_FILE = Path(r"C:\Users\Luke.Muskett\OneDrive - Transport Focus\Documents\roadworks\roadworks_raw.csv")
OUTPUT_FILE = Path(r"C:\Users\Luke.Muskett\OneDrive - Transport Focus\Documents\roadworks\roadworks_corridors.geojson")

# === SETTINGS ===
LATITUDE_CANDIDATES = ["latitude", "lat", "y", "Latitude", "LATITUDE"]
LONGITUDE_CANDIDATES = ["longitude", "lon", "lng", "x", "Longitude", "LONGITUDE"]

# corridor width in metres either side of point
BUFFER_METRES = 60

# optional London-ish filter to remove bad coordinates
MIN_LAT, MAX_LAT = 51.25, 51.75
MIN_LON, MAX_LON = -0.55, 0.35


def find_first_existing(columns, candidates):
    lower_map = {str(col).lower(): col for col in columns}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def pick_first_column(df, candidates, fallback_name):
    col = find_first_existing(df.columns, candidates)
    if col is None:
        df[fallback_name] = ""
        return fallback_name
    return col


def main():
    print("Loading roadworks CSV...")

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Missing raw roadworks file: {RAW_FILE}\n"
            "Put roadworks_raw.csv into your Documents\\roadworks folder."
        )

    df = pd.read_csv(RAW_FILE)
    print(f"Raw rows loaded: {len(df)}")
    print("CSV columns:", list(df.columns))

    lat_col = find_first_existing(df.columns, LATITUDE_CANDIDATES)
    lon_col = find_first_existing(df.columns, LONGITUDE_CANDIDATES)

    if lat_col is None or lon_col is None:
        raise RuntimeError(
            "Could not find latitude/longitude columns in roadworks_raw.csv.\n"
            f"Found columns: {list(df.columns)}"
        )

    print(f"Using latitude column: {lat_col}")
    print(f"Using longitude column: {lon_col}")

    # Optional useful columns if present
    street_col = pick_first_column(
        df,
        ["street_name", "street", "road", "road_name", "StreetName", "Street", "RoadName"],
        "street_name"
    )
    start_col = pick_first_column(
        df,
        ["start_date", "works_start", "start", "StartDate"],
        "start_date"
    )
    end_col = pick_first_column(
        df,
        ["end_date", "works_end", "end", "EndDate"],
        "end_date"
    )
    id_col = pick_first_column(
        df,
        ["id", "works_id", "activity_id", "reference", "Reference"],
        "id"
    )

    df = df.dropna(subset=[lat_col, lon_col]).copy()
    print(f"Rows with coordinates: {len(df)}")

    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df = df.dropna(subset=[lat_col, lon_col]).copy()

    # London-ish bounding box
    df = df[
        (df[lat_col] >= MIN_LAT) & (df[lat_col] <= MAX_LAT) &
        (df[lon_col] >= MIN_LON) & (df[lon_col] <= MAX_LON)
    ].copy()

    print(f"Rows after London bounding-box filter: {len(df)}")

    if df.empty:
        raise RuntimeError("No usable roadworks points remain after coordinate filtering.")

    print("Converting points to GeoDataFrame...")
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326"
    )

    # Project to British National Grid so buffer uses metres
    print("Projecting to British National Grid for buffering...")
    gdf_bng = gdf.to_crs("EPSG:27700")

    print(f"Creating {BUFFER_METRES}m buffered corridors...")
    gdf_bng["geometry"] = gdf_bng.geometry.buffer(BUFFER_METRES)

    # Back to WGS84 for web map use
    corridors = gdf_bng.to_crs("EPSG:4326")

    # Keep a clean subset of columns
    keep_cols = [id_col, street_col, start_col, end_col, lat_col, lon_col, "geometry"]
    keep_cols = [c for c in keep_cols if c in corridors.columns]

    corridors = corridors[keep_cols].copy()

    # Normalise output field names a bit
    rename_map = {}
    if id_col in corridors.columns:
        rename_map[id_col] = "roadworks_id"
    if street_col in corridors.columns:
        rename_map[street_col] = "street_name"
    if start_col in corridors.columns:
        rename_map[start_col] = "start_date"
    if end_col in corridors.columns:
        rename_map[end_col] = "end_date"
    if lat_col in corridors.columns:
        rename_map[lat_col] = "latitude"
    if lon_col in corridors.columns:
        rename_map[lon_col] = "longitude"

    corridors = corridors.rename(columns=rename_map)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("Writing buffered roadworks GeoJSON...")
    corridors.to_file(OUTPUT_FILE, driver="GeoJSON")

    print(f"Done: {OUTPUT_FILE}")
    print(f"Buffered corridor features written: {len(corridors)}")


if __name__ == "__main__":
    main()