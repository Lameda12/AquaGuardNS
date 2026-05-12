"""Generate synthetic SST fallback data for Mahone Bay."""
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

START = date(2023, 1, 1)
END = date(2026, 5, 12)
OUT = Path(__file__).parent / "mahone_bay_sst_fallback.csv"

MHW_1_START = date(2023, 8, 1)
MHW_1_END = date(2023, 8, 12)
MHW_2_START = date(2026, 5, 6)
MHW_2_END = date(2026, 5, 12)


def seasonal_sst(d: date) -> float:
    day_of_year = d.timetuple().tm_yday
    # sine: min ~2 in Jan (day 15), max ~20 in Aug (day 228)
    phase = 2 * math.pi * (day_of_year - 15) / 365 - math.pi / 2
    base = 11.0 + 9.0 * math.sin(phase)
    noise = random.gauss(0, 0.5)
    return round(base + noise, 2)


rows = []
current = START
while current <= END:
    sst = seasonal_sst(current)
    if MHW_1_START <= current <= MHW_1_END:
        sst = round(sst + 3.0, 2)
    elif MHW_2_START <= current <= MHW_2_END:
        sst = round(sst + 3.2, 2)
    rows.append((current.isoformat(), sst))
    current += timedelta(days=1)

with open(OUT, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "sst_celsius"])
    writer.writerows(rows)

print(f"Written {len(rows)} rows to {OUT}")
