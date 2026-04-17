import csv
import re
from pathlib import Path
from datetime import datetime

INPUT = Path("20mph_manual_overrides.csv")
OUTPUT = Path("20mph_manual_overrides_clean.csv")


def clean_header(h):
    return (h or "").replace("\ufeff", "").replace("\xa0", " ").strip().lower()


def normalise_row_keys(row):
    out = {}
    for k, v in row.items():
        ck = clean_header(k)

        if ck in ["road name", "road_name"]:
            ck = "name"
        elif ck in ["borough name", "borough_name"]:
            ck = "borough"
        elif ck in [
            "20mph implementation date",
            "implementation date",
            "date",
            "20mph date",
            "year",
        ]:
            ck = "raw_text"

        out[ck] = v
    return out


def read_csv_flex(path):
    last_error = None
    for enc in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
        try:
            return path.read_text(encoding=enc)
        except Exception as e:
            last_error = e
    raise RuntimeError(f"Could not read CSV with common encodings: {last_error}")


def extract_explicit_year(text):
    if not text:
        return ""

    s = str(text).replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s_lower = s.lower()

    # 1. Any 4-digit year anywhere: use the LAST one
    years4 = re.findall(r"\b(20\d{2})\b", s_lower)
    if years4:
        return years4[-1]

    # 2. Short month-year forms like Mar-20
    m = re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*[-/ ](\d{2})\b",
        s_lower,
        re.I,
    )
    if m:
        yy = int(m.group(2))
        return str(2000 + yy)

    # 3. "By 2019"
    m = re.search(r"\bby\s+(20\d{2})\b", s_lower)
    if m:
        return m.group(1)

    # 4. Try known date formats
    for fmt in [
        "%d %B %Y",
        "%d %b %Y",
        "%B %Y",
        "%b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d-%b-%y",
        "%b-%y",
        "%B-%y",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]:
        try:
            dt = datetime.strptime(s, fmt)
            return str(dt.year)
        except ValueError:
            pass

    return ""


def classify_status_and_year(raw_text, borough, road_name):
    raw = str(raw_text or "").replace("\xa0", " ")
    raw = re.sub(r"\s+", " ", raw).strip()
    raw_lower = raw.lower()
    borough_lower = str(borough or "").strip().lower()
    road_lower = str(road_name or "").strip().lower()

    # Default
    year = extract_explicit_year(raw)
    status = "unresolved"

    # ---------------------------------
    # Greenwich planned / rolling logic
    # ---------------------------------
    if "greenwich" in borough_lower:
        if "rolling (tbc)" in raw_lower or raw_lower == "tbc" or "tbc" in raw_lower:
            return "", "planned_tbc"

        # If Greenwich row has an explicit date, keep it but mark as planned_with_date
        if year:
            return year, "planned_with_date"

    # -------------------------
    # Exact / explicit year rows
    # -------------------------
    if year:
        # If wording suggests future planned but with a date
        if any(x in raw_lower for x in ["planned", "operational via", "comes into force", "into force"]):
            return year, "planned_with_date"

        # Trial/final style wording
        if "trial" in raw_lower and "final" in raw_lower:
            return year, "implemented"

        return year, "implemented"

    # --------------------------------------
    # Harrow phased rollout: implemented set
    # --------------------------------------
    if "harrow" in borough_lower and "phased rollout" in raw_lower:
        # Borough programme appears implemented/phased through 2021-2024
        return "2024", "implemented_phased"

    # ---------------------------------------------------
    # Hounslow area schemes / borough-wide rollout cases
    # ---------------------------------------------------
    if "hounslow" in borough_lower:
        if "borough-wide rollout" in raw_lower:
            inferred = extract_explicit_year(raw)
            if inferred:
                return inferred, "implemented"
            return "2021", "implemented_phased"

        if "area scheme" in raw_lower or "residential road rollout" in raw_lower:
            inferred = extract_explicit_year(raw)
            if inferred:
                return inferred, "implemented"
            return "2021", "implemented_phased"

        if "phased" in raw_lower:
            inferred = extract_explicit_year(raw)
            if inferred:
                return inferred, "implemented_phased"
            return "2021", "implemented_phased"

    # --------------------------------------------------
    # Hillingdon area scheme patterns from your examples
    # --------------------------------------------------
    if "hillingdon" in borough_lower:
        # Exact scheme/date rows already caught by explicit year
        if "phased rollout" in raw_lower:
            # This looks implemented, but year may be unclear.
            # Leave year blank if no explicit year rather than inventing one.
            return "", "implemented_phased_unclear"

    # --------------------------------------------------
    # Generic phased rollout with explicit year range text
    # e.g. 2021–2024 -> year already extracted as 2024 above
    # --------------------------------------------------
    if "phased rollout" in raw_lower:
        if year:
            return year, "implemented_phased"
        return "", "implemented_phased_unclear"

    # ------------------------------------
    # Generic wording for future programmes
    # ------------------------------------
    if any(x in raw_lower for x in ["tbc", "rolling", "planned", "future rollout"]):
        return "", "planned_tbc"

    # ------------------------------------
    # Borough-wide wording
    # ------------------------------------
    if "borough-wide rollout" in raw_lower:
        if year:
            return year, "implemented"
        return "", "implemented_phased_unclear"

    # ------------------------------------
    # Fallback
    # ------------------------------------
    if year:
        return year, "implemented"

    return "", "unresolved"


def main():
    if not INPUT.exists():
        raise RuntimeError(f"Missing input file: {INPUT}")

    raw = read_csv_flex(INPUT)

    sample = raw[:5000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    reader = csv.DictReader(raw.splitlines(), delimiter=delimiter)

    if reader.fieldnames:
        reader.fieldnames = [clean_header(h) for h in reader.fieldnames]

    rows = []
    explicit_years = 0
    inferred_years = 0
    blanks = 0

    for row in reader:
        row = normalise_row_keys(row)

        name = str(row.get("name", "")).strip()
        borough = str(row.get("borough", "")).strip()
        raw_text = str(row.get("raw_text", "")).strip()

        year, status = classify_status_and_year(raw_text, borough, name)

        if year:
            # crude split between explicit and inferred
            if extract_explicit_year(raw_text):
                explicit_years += 1
            else:
                inferred_years += 1
        else:
            blanks += 1

        rows.append({
            "name": name,
            "borough": borough,
            "year": year,
            "status": status,
            "raw_text": raw_text,
        })

    if not rows:
        raise RuntimeError("No rows found in input CSV")

    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "borough", "year", "status", "raw_text"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote: {OUTPUT}")
    print(f"Rows processed: {len(rows)}")
    print(f"Rows with explicit year extracted: {explicit_years}")
    print(f"Rows with inferred year: {inferred_years}")
    print(f"Rows left without year: {blanks}")
    print(f"Detected delimiter: {delimiter!r}")


if __name__ == "__main__":
    main()