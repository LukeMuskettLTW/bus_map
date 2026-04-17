import gzip
from pathlib import Path

INPUT = Path(r"C:\Users\Luke.Muskett\Downloads\03 (2).zip")
OUTPUT = Path(r"C:\Users\Luke.Muskett\OneDrive - Transport Focus\Documents\ltw-bus-speed-map\dft_decoded.json")

print("Reading:", INPUT)

with open(INPUT, "rb") as f:
    data = f.read()

# Try gzip decode
try:
    decoded = gzip.decompress(data)
    print("GZIP detected and decompressed ✔")
except Exception as e:
    print("Not gzip, writing raw bytes instead")
    decoded = data

# Save output
with open(OUTPUT, "wb") as f:
    f.write(decoded)

print("Saved to:", OUTPUT)