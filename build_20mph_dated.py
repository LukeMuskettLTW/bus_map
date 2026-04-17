from pathlib import Path
import re
import csv
import geopandas as gpd

ROOT = Path(__file__).resolve().parent

ROADS_IN = ROOT / "20mph_osm_cleaned.geojson"
BOROUGHS_IN = ROOT / "data" / "boroughs.geojson"
OVERRIDES_IN = ROOT / "20mph_manual_overrides.csv"
ROADS_OUT = ROOT / "20mph_osm_dated.geojson"

# Only these statuses count as live on the map
LIVE_STATUSES = {"implemented", "implemented_phased"}

# Borough fallback years where still useful
BOROUGH_YEAR = {
    "islington": 2013,
    "camden": 2013,
    "city of london": 2014,
    "southwark": 2015,
    "hackney": 2015,
    "lambeth": 2015,
    "tower hamlets": 2016,
    "lewisham": 2016,
    "hammersmith and fulham": 2016,
    "wandsworth": 2017,
    "croydon": 2017,
    "newham": 2024,
    "richmond upon thames": 2024,
    "richmond": 2024,
    "ealing": 2024,
}

# Specific road overrides / TfL phase logic
NAMED_YEAR_OVERRIDES = {
    # Central / Vision Zero phase 1
    "victoria embankment": 2020,
    "millbank": 2020,
    "tower hill": 2020,
    "borough high street": 2020,
    "blackfriars road": 2020,
    "great dover street": 2020,

    # 2022 TfL phase 2 initial
    "a1": 2022,
    "a10": 2022,
    "a41": 2022,
    "a503": 2022,

    # 2023 wider TfL expansion / arterial rollout
    "cromwell road": 2023,
    "brompton road": 2023,
    "warwick road": 2023,
    "holland road": 2023,
    "redcliffe gardens": 2023,
    "pembroke road": 2023,
    "eltham road": 2023,
    "lee high road": 2023,
    "lewisham way": 2023,
    "old kent road": 2023,
    "new cross road": 2023,
    "clapham road": 2023,
    "kennington park road": 2023,
    "catford road": 2023,
    "stanstead road": 2023,
    "dulwich common": 2023,
    "woolwich common": 2023,
    "peckham high street": 2023,
    "camberwell church street": 2023,
    "crystal palace parade": 2023,
    "west wickham high street": 2023,
    "barking road": 2023,
    "broadway": 2023,
    "bourne road": 2023,
    "north cray road": 2023,
    "ealing road": 2023,

    # 2026 phase 3
    "a23": 2026,
    "thornton road": 2026,
    "a24": 2026,
    "stonecot hill": 2026,
    "upper tooting road": 2026,
    "balham high road": 2026,
    "a214": 2026,
    "trinity road": 2026,
    "a312": 2026,
    "roehampton lane": 2026,
}

def normalise(text: str) -> str:
    s = str(text or "").lower().strip()
    s = s.replace("&", "and")
    s = s.replace("’", "'").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def find_borough_name_column(gdf: gpd.GeoDataFrame) -> str:
    candidates = [
        "name", "NAME",
        "borough", "BOROUGH",
        "lad23nm", "LAD23NM",
        "gss_name", "GSS_NAME",
    ]
    for col in candidates:
        if col in gdf.columns:
            return col
    raise RuntimeError(
        f"Could not find a borough name column in boroughs.geojson. "
        f"Columns found: {list(gdf.columns)}"
    )

def load_manual_overrides():
    overrides = {}
    all_rows = 0
    used_rows = 0

    if not OVERRIDES_IN.exists():
        print("No manual overrides CSV found. Continuing without it.")
        return overrides

    # Be tolerant on encoding
    raw_text = None
    for enc in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
        try:
            raw_text = OVERRIDES_IN.read_text(encoding=enc)
            break
        except Exception:
            continue

    if raw_text is None:
        raise RuntimeError("Could not read manual overrides CSV")

    sample = raw_text[:5000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    reader = csv.DictReader(raw_text.splitlines(), delimiter=delimiter)
    if reader.fieldnames:
        reader.fieldnames = [
            (h or "").replace("\ufeff", "").replace("\xa0", " ").strip().lower()
            for h in reader.fieldnames
        ]

    required = {"name", "borough", "year"}
    missing = required.difference(reader.fieldnames or [])
    if missing:
        raise RuntimeError(
            f"Overrides CSV is missing required columns: {sorted(missing)}"
        )

    for row in reader:
        all_rows += 1
        row = {
            (k or "").strip().lower(): (v or "").strip()
            for k, v in row.items()
        }

        name = row.get("name", "")
        borough = row.get("borough", "")
        year_raw = row.get("year", "")
        status = row.get("status", "").strip().lower()

        # Only live statuses go onto the map if status exists
        if status and status not in LIVE_STATUSES:
            continue

        if not name or not borough or not year_raw:
            continue

        year_match = re.search(r"(20\d{2})", year_raw)
        if not year_match:
            continue

        year = int(year_match.group(1))
        key = (normalise(name), normalise(borough))
        overrides[key] = (year, status or "manual_override")
        used_rows += 1

    print(f"Loaded {used_rows} live manual overrides from {all_rows} CSV rows")
    return overrides

def main():
    if not ROADS_IN.exists():
        raise RuntimeError(f"Missing roads file: {ROADS_IN}")
    if not BOROUGHS_IN.exists():
        raise RuntimeError(f"Missing boroughs file: {BOROUGHS_IN}")

    print("Loading 20mph roads...")
    roads = gpd.read_file(ROADS_IN)

    print("Loading borough boundaries...")
    boroughs = gpd.read_file(BOROUGHS_IN)
    borough_col = find_borough_name_column(boroughs)

    print("Loading manual overrides...")
    manual_overrides = load_manual_overrides()

    print("Projecting data...")
    roads_proj = roads.to_crs(27700)
    boroughs_proj = boroughs.to_crs(27700)

    print("Matching roads to boroughs...")
    centroids = roads_proj.copy()
    centroids["geometry"] = roads_proj.geometry.centroid

    joined = gpd.sjoin(
        centroids[["geometry"]],
        boroughs_proj[[borough_col, "geometry"]],
        how="left",
        predicate="within",
    )

    roads_proj["borough_name"] = joined[borough_col].values

    introduced_year = []
    introduced_source = []
    introduced_status = []

    count_manual = 0
    count_named = 0
    count_borough = 0
    count_unknown = 0

    for _, row in roads_proj.iterrows():
        road_name = row.get("name") or row.get("ref") or ""
        borough_name = row.get("borough_name") or ""

        road_key = normalise(road_name)
        borough_key = normalise(borough_name)

        # 1. Manual override (only live statuses were loaded)
        manual_key = (road_key, borough_key)
        if manual_key in manual_overrides:
            year, status = manual_overrides[manual_key]
            introduced_year.append(year)
            introduced_source.append("manual_override")
            introduced_status.append(status)
            count_manual += 1
            continue

        # 2. Named specific roads / TfL roads
        if road_key in NAMED_YEAR_OVERRIDES:
            introduced_year.append(NAMED_YEAR_OVERRIDES[road_key])
            introduced_source.append("named_override")
            introduced_status.append("implemented")
            count_named += 1
            continue

        # 3. Borough fallback
        if borough_key in BOROUGH_YEAR:
            introduced_year.append(BOROUGH_YEAR[borough_key])
            introduced_source.append("borough_rollout")
            introduced_status.append("implemented")
            count_borough += 1
            continue

        # 4. Unknown
        introduced_year.append(None)
        introduced_source.append("unknown")
        introduced_status.append("unknown")
        count_unknown += 1

    roads_proj["introduced_year"] = introduced_year
    roads_proj["introduced_source"] = introduced_source
    roads_proj["introduced_status"] = introduced_status

    print("Simplifying geometry slightly...")
    roads_proj["geometry"] = roads_proj.geometry.simplify(4)

    keep_cols = [
        c for c in [
            "name",
            "ref",
            "highway",
            "maxspeed",
            "borough_name",
            "introduced_year",
            "introduced_source",
            "introduced_status",
            "geometry",
        ]
        if c in roads_proj.columns
    ]

    roads_out = roads_proj[keep_cols].to_crs(4326)

    print("Writing output...")
    roads_out.to_file(ROADS_OUT, driver="GeoJSON")

    print("DONE")
    print(f"Manual: {count_manual}")
    print(f"Named: {count_named}")
    print(f"Borough: {count_borough}")
    print(f"Unknown: {count_unknown}")
    print(f"Saved: {ROADS_OUT}")

if __name__ == "__main__":
    main()