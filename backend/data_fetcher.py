"""SST data fetching from NOAA ERDDAP with local JSON cache and CSV fallback."""
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from loguru import logger

from sites import SITES

CACHE_DIR = Path(__file__).parent / "cache"
DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_TTL_HOURS = 6
ERDDAP_BASE = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdMH1sstd1day.json"
ERDDAP_TIMEOUT = 10.0


def _cache_path(site_id: str) -> Path:
    return CACHE_DIR / f"{site_id}_sst.json"


def load_cached_sst(site_id: str) -> list[dict] | None:
    path = _cache_path(site_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
        fetched_at = datetime.fromisoformat(payload["fetched_at"])
        if datetime.now(timezone.utc) - fetched_at > timedelta(hours=CACHE_TTL_HOURS):
            return None
        return payload["data"]
    except Exception as e:
        logger.warning(f"Cache read failed for {site_id}: {e}")
        return None


async def fetch_erddap_sst(site_id: str, days_back: int = 90) -> list[dict]:
    # Fix 3: Validate site_id before SITES lookup
    if site_id not in SITES:
        raise ValueError(f"Unknown site: {site_id!r}")

    # Fix 1: Create cache dir before any HTTP call
    CACHE_DIR.mkdir(exist_ok=True)

    site = SITES[site_id]
    lat, lon = site["lat"], site["lon"]
    end = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days_back)

    url = (
        f"{ERDDAP_BASE}?sst"
        f"[({start.strftime('%Y-%m-%dT%H:%M:%SZ')}):({end.strftime('%Y-%m-%dT%H:%M:%SZ')})]"
        f"[({lat})]"
        f"[({lon})]"
    )
    logger.info(f"Fetching ERDDAP SST for {site_id}")

    async with httpx.AsyncClient(timeout=ERDDAP_TIMEOUT) as client:
        response = await client.get(url)
        response.raise_for_status()
        table = response.json()["table"]
        rows = table["rows"]

    data = []
    for row in rows:
        time_str, _lat, _lon, sst = row
        if sst is None:
            continue
        date_str = time_str[:10]
        data.append({"date": date_str, "sst": float(sst)})

    # Fix 2: Atomic cache write using tmp file + rename
    tmp = _cache_path(site_id).with_suffix(".tmp")
    tmp.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }))
    tmp.rename(_cache_path(site_id))
    logger.info(f"Cached {len(data)} SST records for {site_id}")
    return data


def _load_fallback_csv(site_id: str) -> list[dict]:
    path = DATA_DIR / f"{site_id}_fallback.csv"
    if not path.exists():
        raise FileNotFoundError(f"No fallback CSV for {site_id} at {path}")
    data = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({"date": row["date"], "sst": float(row["sst_celsius"])})
    logger.info(f"Loaded {len(data)} rows from fallback CSV for {site_id}")
    return data


async def get_sst(site_id: str) -> list[dict]:
    cached = load_cached_sst(site_id)
    if cached is not None:
        logger.debug(f"Cache hit for {site_id}")
        return cached

    try:
        return await fetch_erddap_sst(site_id)
    except Exception as e:
        logger.warning(f"ERDDAP fetch failed for {site_id}: {e}. Falling back to CSV.")
        return _load_fallback_csv(site_id)
