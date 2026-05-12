# AquaGuard NS — Claude Code Instructions

## Project
Marine Heatwave Early Warning System for Nova Scotia Aquaculture.
Hackathon: Hack the Elements 2026 (May 22–24, ShiftKey Labs).
Team: Alamedin & Neo.

## Stack
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.11+)
- **MHW Detection**: ecjoliver/marineHeatWaves (pip install from GitHub)
- **Data**: NOAA ERDDAP SST API + DFO Maritimes buoy data (no API keys needed)
- **Machine**: MacBook M2, 8GB RAM — keep everything lightweight, no Docker

## Repo Structure
```
aquaguard-ns/
├── CLAUDE.md
├── README.md
├── frontend/          # Next.js app
│   ├── app/
│   ├── components/
│   └── package.json
├── backend/           # FastAPI
│   ├── main.py
│   ├── mhw_detector.py
│   ├── data_fetcher.py
│   ├── requirements.txt
│   └── cache/         # local JSON cache for SST data
└── data/              # static fallback CSVs
```

## Rules

### General
- Never use Docker. Run everything natively.
- Use `uv` for Python package management (not pip/conda).
- Use `pnpm` for Node packages.
- No paid APIs, no API keys required anywhere.
- Keep memory footprint low — cache aggressively, don't load full datasets into RAM.

### Python / Backend
- Python 3.11+, strict type hints throughout.
- Use `uv run` for all Python execution.
- FastAPI with async endpoints only.
- Cache all ERDDAP/DFO responses as JSON in `backend/cache/` with timestamp.
  Cache TTL: 6 hours for SST data. Never re-fetch if cache is fresh.
- MHW detection runs on the cached data — never block an HTTP request on a fresh fetch.
- The marineHeatWaves library uses `ordinal` time format (days since epoch).
  Convert dates with: `matplotlib.dates.date2num(datetime_obj)` or manually.
- All endpoints return `application/json`. No server-side rendering from FastAPI.
- Error responses: `{"error": "message", "detail": "..."}` with appropriate HTTP status.
- Use `loguru` for logging, not print statements.

### Next.js / Frontend
- App Router only. No Pages Router.
- All data fetching from the FastAPI backend at `http://localhost:8000`.
- Use `SWR` for client-side data fetching with 5-min revalidation.
- Tailwind only for styling — no extra CSS frameworks.
- Chart.js via `react-chartjs-2` for all charts.
- Keep components in `frontend/components/`, pages in `frontend/app/`.
- No SSR for dashboard data — use client components with `"use client"`.

### Data Sources

**NOAA ERDDAP (primary SST)**
Base URL: `https://coastwatch.pfeg.noaa.gov/erddap/griddap/`
Dataset: `erdMH1sstd1day` (MODIS Aqua, 1-day composite, 0.01°)
Example fetch for Mahone Bay (44.5°N, -64.3°W), last 90 days:
```
https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdMH1sstd1day.json?sst[(2026-02-11T12:00:00Z):(2026-05-11T12:00:00Z)][(44.5)][-64.3]
```
Parse `table.rows` array, column order: `[time, latitude, longitude, sst]`.
SST is in Celsius. NaN fill value is `null` — drop nulls before running MHW detection.

**DFO Maritimes Buoy (secondary / validation)**
Base URL: `https://www.meds-sdmm.dfo-mpo.gc.ca/isdm-gdsi/waves/msc/data-donnees/`
Station IDs for NS: `44150` (Mahone Bay area), `44137` (Chedabucto).
Fallback: use static CSVs in `data/` if DFO is unreachable.

**Fallback static data**
`data/mahone_bay_sst_2023_2026.csv` — pre-downloaded, always present.
Format: `date,sst_celsius` (ISO date, float).
Use this if ERDDAP returns an error or times out (>10s).

### MHW Detection (Hobday Algorithm)
Install: `uv add git+https://github.com/ecjoliver/marineHeatWaves`

```python
import marineHeatWaves as mhw
import numpy as np
from datetime import date
import matplotlib.dates as mdates

def detect_mhw(dates: list[date], temps: list[float]) -> dict:
    t = np.array([mdates.date2num(d) for d in dates])
    temp = np.array(temps)
    clim_start = dates[0].year
    clim_end = min(dates[-1].year, 2023)  # use historical period for climatology
    mhws, clim = mhw.detect(
        t, temp,
        climatologyPeriod=[clim_start, clim_end],
        pctile=90,
        minDuration=5,
        joinAcrossGaps=True,
        maxGap=2
    )
    return {"events": mhws, "climatology": clim}
```

Return shape expected by frontend:
```json
{
  "site": "mahone_bay",
  "current_sst": 18.4,
  "climatology_today": 15.2,
  "threshold_today": 17.1,
  "anomaly": 3.2,
  "mhw_active": true,
  "mhw_duration_days": 7,
  "mhw_category": 2,
  "timeseries": {
    "dates": ["2026-02-11", ...],
    "sst": [12.1, ...],
    "climatology": [11.8, ...],
    "threshold": [13.9, ...]
  },
  "forecast": [
    {"date": "2026-05-13", "sst_forecast": 18.1, "status": "mhw"}
  ]
}
```

### Sites Config
```python
SITES = {
    "mahone_bay":     {"lat": 44.50, "lon": -64.30, "name": "Mahone Bay",     "species": "Atlantic Salmon"},
    "bedford_basin":  {"lat": 44.72, "lon": -63.63, "name": "Bedford Basin",  "species": "Blue Mussel"},
    "chedabucto_bay": {"lat": 45.40, "lon": -61.10, "name": "Chedabucto Bay", "species": "Eastern Oyster"},
    "bras_dor":       {"lat": 45.83, "lon": -60.90, "name": "Bras d'Or Lake", "species": "Blue Mussel"},
}
```

### Forecast (simple)
No ML model — use linear extrapolation from the last 7 days of SST trend + seasonal climatology.
Tag each forecast day as `"mhw"`, `"watch"`, or `"normal"` vs the 90th pct threshold.

### Species Risk Thresholds
```python
SPECIES_THRESHOLDS = {
    "Atlantic Salmon": {"stress": 16.0, "critical": 18.0, "lethal": 23.0},
    "Blue Mussel":     {"stress": 20.0, "critical": 24.0, "lethal": 27.0},
    "Eastern Oyster":  {"stress": 28.0, "critical": 32.0, "lethal": 35.0},
}
```

## Dev Commands
```bash
# Backend
cd backend && uv run uvicorn main:app --reload --port 8000

# Frontend
cd frontend && pnpm dev

# Prefetch + cache all site data
cd backend && uv run python data_fetcher.py --prefetch-all

# Run MHW detection on cached data
cd backend && uv run python mhw_detector.py --site mahone_bay
```

## What NOT to Do
- No Docker, no docker-compose
- No PostgreSQL or any database — JSON file cache only
- No authentication, no user accounts
- No paid APIs (OpenAI, Mapbox, etc.)
- No heavy ML models — M2 with 8GB RAM can't afford it during a demo
- Don't load the entire 90-day SST grid into memory — slice at request time
- Don't run MHW detection synchronously on every API request — cache results too

## Priority Order (Hackathon)
1. Backend `/api/detect/{site}` returns valid MHW data (real or fallback CSV)
2. Frontend chart renders SST + climatology + threshold correctly
3. Alert system reflects live MHW status
4. Species risk panel
5. Forecast panel
6. Polish / animations last