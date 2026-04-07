import geopandas as gpd
from pathlib import Path

ROOT = Path(__file__).resolve().parent

IN_FILE = ROOT / "data" / "London_Boroughs.gpkg"
OUT_FILE = ROOT / "data" / "boroughs.geojson"

# Load geopackage
gdf = gpd.read_file(IN_FILE)

# Check column names (just for awareness)
print(gdf.columns)

# Standardise borough name column
# (this dataset usually uses 'NAME' or 'name')
if 'NAME' in gdf.columns:
    gdf = gdf.rename(columns={'NAME': 'name'})
elif 'Name' in gdf.columns:
    gdf = gdf.rename(columns={'Name': 'name'})

# Keep only what we need
gdf = gdf[['name', 'geometry']]

# Convert to WGS84 (Leaflet requires this)
gdf = gdf.to_crs(epsg=4326)

# Save as GeoJSON
gdf.to_file(OUT_FILE, driver="GeoJSON")

print("Done: boroughs.geojson created")