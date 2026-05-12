You are building AquaGuard NS — a Marine Heatwave Early Warning System for Nova Scotia aquaculture farms, for the Hack the Elements 2026 hackathon (Water theme). Read CLAUDE.md in full before writing any code. Follow every rule in it exactly.

## What to build

Scaffold the entire project, then implement it working end-to-end.

### Step 1: Scaffold
Create this exact structure:
```
aquaguard-ns/
├── CLAUDE.md
├── README.md
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── SiteSelector.tsx
│   │   ├── SSTChart.tsx
│   │   ├── AlertPanel.tsx
│   │   ├── SpeciesRisk.tsx
│   │   ├── ForecastStrip.tsx
│   │   └── StatCards.tsx
│   ├── lib/
│   │   └── api.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
├── backend/
│   ├── main.py
│   ├── mhw_detector.py
│   ├── data_fetcher.py
│   ├── sites.py
│   ├── requirements.txt
│   └── cache/
│       └── .gitkeep
└── data/
    └── README.md
```

### Step 2: Backend — implement in this order

1. `sites.py` — SITES dict and SPECIES_THRESHOLDS as defined in CLAUDE.md

2. `data_fetcher.py`
   - `fetch_erddap_sst(site_id, days_back=90)` — async, fetches NOAA ERDDAP, parses table.rows, drops nulls, writes to `cache/{site_id}_sst.json` with `{"fetched_at": ISO_timestamp, "data": [{"date": ..., "sst": ...}]}`
   - `load_cached_sst(site_id)` — reads cache, returns None if missing or >6h old
   - `get_sst(site_id)` — tries cache first, then ERDDAP, then falls back to `data/{site_id}_fallback.csv` if it exists

3. `mhw_detector.py`
   - `detect_mhw_for_site(site_id)` — loads SST via data_fetcher, runs marineHeatWaves.detect(), builds the full response JSON shape defined in CLAUDE.md, caches result to `cache/{site_id}_mhw.json`
   - MHW category: anomaly 1-2x threshold = Cat I, 2-3x = Cat II, 3-4x = Cat III, >4x = Cat IV
   - Forecast: linear extrapolation of last 7-day SST slope, projected 7 days forward, tagged vs threshold

4. `main.py` — FastAPI app
   - `GET /api/sites` — returns list of all site IDs and names
   - `GET /api/detect/{site_id}` — returns full MHW detection JSON (from cache if fresh, else recomputes)
   - `GET /api/detect/all` — returns detection for all 4 sites in one response
   - `POST /api/refresh/{site_id}` — forces re-fetch from ERDDAP and recomputes
   - CORS: allow `http://localhost:3000`
   - On startup: run `detect_mhw_for_site` for all sites concurrently using asyncio.gather

### Step 3: Frontend — implement in this order

1. `lib/api.ts` — typed fetch wrappers for all backend endpoints using SWR

2. `components/StatCards.tsx` — 4 metric cards: Current SST, Intensity (anomaly), Duration, MHW Category

3. `components/SSTChart.tsx` — Chart.js line chart with 3 datasets: SST (blue solid), Climatology (gray dashed), 90th pct threshold (amber dashed). Fill red between SST and threshold when SST > threshold. X-axis: dates, Y-axis: °C. Last 90 days.

4. `components/ForecastStrip.tsx` — 7 horizontal day cards. Red bg if MHW forecast, amber if Watch, neutral if Normal.

5. `components/AlertPanel.tsx` — renders active alerts with severity color-coded left border (red=critical, amber=moderate, blue=watch). Data from MHW detection result.

6. `components/SpeciesRisk.tsx` — 3 cards (salmon, mussel, oyster). Each has labeled progress bars for thermal stress %, mortality risk %, disease risk %. Risk % = (current_sst - stress_threshold) / (lethal_threshold - stress_threshold) * 100, clamped 0–100.

7. `components/SiteSelector.tsx` — 4 clickable site cards. Shows site name, current SST, MHW/Watch/Normal badge. Active site highlighted.

8. `app/page.tsx` — assembles all components. Header with logo, live badge, and active alert count. Full layout as seen in the dashboard design.

### Step 4: Static fallback data
Generate a realistic synthetic CSV for `data/mahone_bay_sst_fallback.csv`:
- Dates: 2023-01-01 to 2026-05-12
- SST values: seasonal sine curve (min ~2°C Jan, max ~20°C Aug) + gaussian noise (σ=0.5) + a simulated MHW event in Aug 2023 (+3°C for 12 days) and one in May 2026 (+3.2°C for 7 days ending today)
- Write it as a Python script `data/generate_fallback.py` that outputs the CSV, then run it

### Step 5: Requirements
`backend/requirements.txt`:
```
fastapi
uvicorn[standard]
httpx
numpy
scipy
matplotlib
marineHeatWaves @ git+https://github.com/ecjoliver/marineHeatWaves
loguru
python-dateutil
```

`frontend/package.json` deps: next@14, react, react-dom, typescript, tailwindcss, swr, chart.js, react-chartjs-2, @types/react, @types/node

### Constraints (from CLAUDE.md — non-negotiable)
- No Docker. Everything runs natively on macOS M2.
- Use `uv` for Python, `pnpm` for Node.
- JSON file cache only, no database.
- No paid APIs, no API keys.
- Async everywhere in FastAPI.
- Cache TTL 6h for SST, never block requests on live fetch.
- Low memory — do not load full grids, slice at the coordinate level in ERDDAP queries.

### When done, print:
```
=== AquaGuard NS ready ===
Backend:  cd backend && uv run uvicorn main:app --reload --port 8000
Frontend: cd frontend && pnpm dev
Dashboard: http://localhost:3000
API docs:  http://localhost:8000/docs
```