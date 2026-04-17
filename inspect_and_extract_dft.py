from pathlib import Path
import zipfile
import json
import shutil

INPUT_CANDIDATES = [
    Path(r"C:\Users\Luke.Muskett\Downloads\03 (2).zip"),
    Path(r"C:\Users\Luke.Muskett\Downloads\03 (1).zip"),
    Path(r"C:\Users\Luke.Muskett\Downloads\03.json"),
    Path(r"C:\Users\Luke.Muskett\Downloads\roadworks_data"),
]

OUT_DIR = Path(r"C:\Users\Luke.Muskett\OneDrive - Transport Focus\Documents\ltw-bus-speed-map\dft_extracted")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read_head(path: Path, n: int = 400) -> bytes:
    with open(path, "rb") as f:
        return f.read(n)


def looks_like_zip(head: bytes) -> bool:
    return head.startswith(b"PK\x03\x04")


def looks_like_json(head: bytes) -> bool:
    stripped = head.lstrip()
    return stripped.startswith(b"{") or stripped.startswith(b"[")


def write_preview(path: Path, head: bytes) -> None:
    preview_path = OUT_DIR / "dft_preview.txt"
    try:
        text = head.decode("utf-8", errors="replace")
    except Exception:
        text = repr(head)
    preview_path.write_text(text, encoding="utf-8")
    print(f"Preview written to: {preview_path}")


def extract_zip(path: Path) -> None:
    print(f"\nDetected ZIP: {path}")
    with zipfile.ZipFile(path, "r") as z:
        names = z.namelist()
        print(f"Files inside ZIP: {len(names)}")
        json_names = [n for n in names if n.lower().endswith(".json")]
        print(f"JSON files inside ZIP: {len(json_names)}")

        extract_count = 0
        for name in json_names:
            z.extract(name, OUT_DIR)
            extract_count += 1

    print(f"Extracted JSON files: {extract_count}")
    if json_names:
        print("First few JSON files:")
        for name in json_names[:10]:
            print(" -", name)


def save_json_like(path: Path, head: bytes) -> None:
    print(f"\nDetected JSON-like file: {path}")
    target = OUT_DIR / f"{path.stem}.json"
    shutil.copy2(path, target)
    print(f"Copied to: {target}")
    write_preview(path, head)

    try:
        with open(path, "r", encoding="utf-8") as f:
            first = f.read(2000)
        print("First characters:")
        print(first[:1000])
    except Exception as e:
        print("Could not print text preview:", e)


def save_unknown(path: Path, head: bytes) -> None:
    print(f"\nUnknown file type: {path}")
    target = OUT_DIR / path.name
    shutil.copy2(path, target)
    print(f"Copied raw file to: {target}")
    write_preview(path, head)


def main():
    found = [p for p in INPUT_CANDIDATES if p.exists()]
    if not found:
        raise FileNotFoundError("None of the expected DfT files were found in Downloads.")

    print("Files found:")
    for p in found:
        print(f" - {p} ({p.stat().st_size} bytes)")

    chosen = max(found, key=lambda p: p.stat().st_size)
    print(f"\nUsing largest candidate: {chosen}")

    head = read_head(chosen)

    if looks_like_zip(head):
        extract_zip(chosen)
    elif looks_like_json(head):
        save_json_like(chosen, head)
    else:
        save_unknown(chosen, head)

    print(f"\nDone. Check this folder next:\n{OUT_DIR}")


if __name__ == "__main__":
    main()