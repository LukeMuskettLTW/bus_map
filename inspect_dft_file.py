from pathlib import Path

p = Path(r"C:\Users\Luke.Muskett\Downloads\03 (3).zip")

print("exists:", p.exists())
if p.exists():
    print("size:", p.stat().st_size)
    with open(p, "rb") as f:
        data = f.read(300)
    print("first bytes:", data)