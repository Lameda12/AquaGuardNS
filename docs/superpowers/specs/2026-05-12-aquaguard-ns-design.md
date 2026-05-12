# AquaGuard NS — Design Spec
**Date:** 2026-05-12  
**Hackathon:** Hack the Elements 2026 (Water theme, May 22–24, ShiftKey Labs)  
**Team:** Alamedin & Neo  

---

## Overview

Marine Heatwave Early Warning System for Nova Scotia aquaculture farms. Fetches SST data from NOAA ERDDAP, runs the Hobday MHW detection algorithm, and presents real-time heatwave status, forecasts, and species risk assessments on a Next.js dashboard.

---

## Approach

Sequential backend-first build. Backend (data pipeline → MHW detection → API) is fully working before frontend starts. Fallback CSV generated before any backend code so demo works even if NOAA ERDDAP is unreachable.

**Why:** Hackathon risk is ERDDAP unavailability or marineHeatWaves library API mismatch. Backend-first surfaces these immediately. Frontend is useless without real MHW data.

---

## Architecture & Data Flow

```
NOAA ERDDAP (primary)
        │ async httpx, sliced to single lat/lon coord
        ▼
  data_fetcher.py
  ├── cache/{site}_sst.json  (TTL 6h)
  └── data/{site}_fallback.csv (always present)
        │
        ▼
  mhw_detector.py
  ├── Hobday algorithm via marineHeatWaves lib
  ├── ordinal dates via matplotlib.dates.date2num
  └── cache/{site}_mhw.json
        │
        ▼
  main.py (FastAPI, port 8000)
  ├── startup: asyncio.gather → all 4 sites
  ├── GET /api/sites
  ├── GET /api/detect/{site_id}
  ├── GET /api/detect/all
  └── POST /api/refresh/{site_id}
        │ http://localhost:8000
        ▼
  Next.js 14 App Router (port 3000)
  ├── SWR polling, 5-min revalidation
  └── page.tsx → SiteSelector + StatCards + SSTChart + AlertPanel + SpeciesRisk + ForecastStrip
```

**Key invariants:**
- Never block HTTP request on live ERDDAP fetch — serve from cache, refresh async
- Never load full SST grid — ERDDAP query sliced to single coordinate
- ERDDAP error or >10s timeout → fall through to fallback CSV

---

## Backend Modules

### `sites.py`
Pure config. `SITES` dict (4 sites: mahone_bay, bedford_basin, chedabucto_bay, bras_dor) and `SPECIES_THRESHOLDS` dict (salmon, mussel, oyster — stress/critical/lethal temps). Imported by all other modules.

### `data_fetcher.py`
Three functions:
- `fetch_erddap_sst(site_id, days_back=90)` — async httpx GET to `erdMH1sstd1day` dataset, slice at site lat/lon, parse `table.rows`, drop nulls, write `cache/{site_id}_sst.json` with `{"fetched_at": ISO, "data": [{date, sst}]}`
- `load_cached_sst(site_id)` — read cache file, return None if missing or >6h old
- `get_sst(site_id)` — cache → ERDDAP → fallback CSV. Always returns `list[dict]` with `date` + `sst` keys.

### `mhw_detector.py`
- `detect_mhw_for_site(site_id)` — calls `get_sst`, converts dates to ordinal via `matplotlib.dates.date2num`, runs `mhw.detect()` with `pctile=90`, `minDuration=5`, `joinAcrossGaps=True`, `maxGap=2`
- MHW category from anomaly/threshold ratio: 1–2x=CatI, 2–3x=CatII, 3–4x=CatIII, >4x=CatIV
- 7-day forecast: linear slope of last 7 SST points projected forward, each day tagged `mhw`/`watch`/`normal` vs threshold
- Builds and returns full response JSON shape (see Response Shape section)
- Caches result to `cache/{site_id}_mhw.json`

### `main.py`
- FastAPI app, CORS allow `http://localhost:3000`
- Startup event: `asyncio.gather(*[detect_mhw_for_site(s) for s in SITES])`
- All endpoints async; serve from cache when fresh, recompute if stale
- Error responses: `{"error": "message", "detail": "..."}` with appropriate HTTP status
- `loguru` for all logging, no print statements

---

## API Response Shape

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
    "dates": ["2026-02-11", "..."],
    "sst": [12.1, "..."],
    "climatology": [11.8, "..."],
    "threshold": [13.9, "..."]
  },
  "forecast": [
    {"date": "2026-05-13", "sst_forecast": 18.1, "status": "mhw"}
  ]
}
```

---

## Frontend Components

All components use `"use client"`. No SSR for dashboard data. SWR handles all fetching.

| Component | Purpose |
|---|---|
| `lib/api.ts` | Typed SWR hooks for all 4 endpoints, base URL `http://localhost:8000` |
| `SiteSelector` | 4 clickable cards — site name, current SST, MHW/Watch/Normal badge. Active highlighted. |
| `StatCards` | 4 metric cards: Current SST, Anomaly (°C above threshold), Duration (days), MHW Category |
| `SSTChart` | Chart.js line — SST blue solid, Climatology gray dashed, Threshold amber dashed. Red fill when SST > threshold. Last 90 days. |
| `ForecastStrip` | 7 horizontal day cards. Red=MHW, Amber=Watch, Neutral=Normal |
| `AlertPanel` | Active alerts with color-coded left border (red=critical, amber=moderate, blue=watch) |
| `SpeciesRisk` | 3 cards (salmon/mussel/oyster). Progress bars: thermal stress %, mortality risk %, disease risk %. Formula: `(sst - stress) / (lethal - stress) * 100`, clamped 0–100 |
| `app/page.tsx` | Orchestrates all components. Header: logo + LIVE badge + active alert count. Holds `selectedSite` state (default `mahone_bay`). |

**Styling:** Tailwind only. Dark dashboard aesthetic.

---

## Data & Fallback

**`data/generate_fallback.py`** — run once, outputs `mahone_bay_sst_fallback.csv`:
- Dates: 2023-01-01 → 2026-05-12
- Seasonal sine curve: min ~2°C Jan, max ~20°C Aug
- Gaussian noise σ=0.5
- Simulated MHW events: Aug 2023 (+3°C, 12 days), May 2026 (+3.2°C, 7 days ending today)
- Format: `date,sst_celsius`

**Cache layout:**
```
backend/cache/
├── {site_id}_sst.json    # {"fetched_at": ISO, "data": [{date, sst}]}
├── {site_id}_mhw.json    # full detection result
└── .gitkeep
```

TTL: 6h for both SST and MHW caches. `POST /api/refresh/{site}` forces re-fetch.

---

## Tooling & Dev Setup

**Backend (uv):**
```bash
uv add fastapi uvicorn[standard] httpx numpy scipy matplotlib loguru python-dateutil
uv add git+https://github.com/ecjoliver/marineHeatWaves
```

**Frontend (pnpm):**
```bash
pnpm create next-app@14 frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"
pnpm add swr chart.js react-chartjs-2
```

No Docker. No database. No API keys. Native macOS M2.

---

## Implementation Order

1. Scaffold all dirs + `.gitkeep`
2. `data/generate_fallback.py` → run it → CSV exists
3. `sites.py`
4. `data_fetcher.py`
5. `mhw_detector.py`
6. `main.py`
7. Verify `GET /api/detect/mahone_bay` returns valid JSON
8. Frontend scaffold via pnpm create next-app
9. `lib/api.ts`
10. Components: `StatCards` → `SSTChart` → `ForecastStrip` → `AlertPanel` → `SpeciesRisk` → `SiteSelector`
11. `app/page.tsx` — assemble all components
12. End-to-end smoke test

---

## Constraints (Non-Negotiable)

- No Docker
- No database — JSON file cache only
- No paid APIs, no API keys
- `uv` for Python, `pnpm` for Node
- Async everywhere in FastAPI
- Cache TTL 6h, never block requests on live fetch
- Low memory — slice ERDDAP at coordinate level, never load full grid
