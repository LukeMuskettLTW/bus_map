from pathlib import Path
import zipfile

ZIP_PATH = Path(r"C:\Users\Luke.Muskett\Downloads\03.zip")  # change if needed
OUT_DIR = Path(r"C:\Users\Luke.Muskett\OneDrive - Transport Focus\Documents\roadworks\unzipped_03")

def main():
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"ZIP not found: {ZIP_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        print(f"ZIP: {ZIP_PATH}")
        print(f"Files inside: {len(zf.namelist())}")
        print("-" * 60)
        for name in zf.namelist()[:500]:
            print(name)
        print("-" * 60)
        zf.extractall(OUT_DIR)

    print(f"Extracted to: {OUT_DIR}")

if __name__ == "__main__":
    main()