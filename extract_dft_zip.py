import zipfile
from pathlib import Path

# === CHANGE ONLY THIS IF NEEDED ===
ZIP_PATH = Path(r"C:\Users\Luke.Muskett\Downloads\03 (2).zip")

# === OUTPUT FOLDER ===
OUT_DIR = Path(r"C:\Users\Luke.Muskett\OneDrive - Transport Focus\Documents\ltw-bus-speed-map\dft_extracted")

OUT_DIR.mkdir(parents=True, exist_ok=True)

print("Opening ZIP:", ZIP_PATH)

if not ZIP_PATH.exists():
    raise FileNotFoundError(f"ZIP file not found: {ZIP_PATH}")

with zipfile.ZipFile(ZIP_PATH, "r") as z:
    names = z.namelist()
    print("Files inside ZIP:", len(names))

    json_count = 0

    for name in names:
        if name.lower().endswith(".json"):
            z.extract(name, OUT_DIR)
            json_count += 1

    print("Extracted JSON files:", json_count)
    print("Output folder:", OUT_DIR)