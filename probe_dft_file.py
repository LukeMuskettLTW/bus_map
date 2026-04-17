from pathlib import Path

FILE = Path(r"C:\Users\Luke.Muskett\Downloads\03 (2).zip")

data = FILE.read_bytes()

print("File:", FILE)
print("Size:", len(data), "bytes")
print("First 16 bytes:", data[:16])
print("Last 64 bytes:", data[-64:])

print("PK local headers:", data.count(b'PK\x03\x04'))
print("PK central dir headers:", data.count(b'PK\x01\x02'))
print("PK end headers:", data.count(b'PK\x05\x06'))