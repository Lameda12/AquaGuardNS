"""Marine Heatwave detection using Hobday algorithm."""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import marineHeatWaves as mhw
import numpy as np
from loguru import logger

from data_fetcher import get_sst, CACHE_DIR
from sites import SITES

CACHE_TTL_HOURS = 6


def _cache_path(site_id: str) -> Path:
    return CACHE_DIR / f"{site_id}_mhw.json"


def _load_cached_mhw(site_id: str) -> dict | None:
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
        logger.warning(f"MHW cache read failed for {site_id}: {e}")
        return None


def _categorize_mhw(anomaly: float, threshold: float) -> int:
    if threshold <= 0 or anomaly <= 0:
        return 0
    ratio = anomaly / threshold
    if ratio >= 4:
        return 4
    elif ratio >= 3:
        return 3
    elif ratio >= 2:
        return 2
    elif ratio >= 1:
        return 1
    return 0


def _tag_forecast_status(sst_forecast: float, threshold: float) -> str:
    if sst_forecast >= threshold:
        return "mhw"
    elif sst_forecast >= threshold * 0.95:
        return "watch"
    return "normal"


async def detect_mhw_for_site(site_id: str) -> dict:
    cached = _load_cached_mhw(site_id)
    if cached is not None:
        logger.debug(f"MHW cache hit for {site_id}")
        return cached

    logger.info(f"Running MHW detection for {site_id}")
    sst_records = await get_sst(site_id)

    dates_raw = [r["date"] for r in sst_records]
    temps = [r["sst"] for r in sst_records]

    date_objs = [date.fromisoformat(d) for d in dates_raw]
    t = np.array([d.toordinal() for d in date_objs])
    temp = np.array(temps)

    clim_start = date_objs[0].year
    clim_end = min(date_objs[-1].year, 2023)

    mhws, clim = mhw.detect(
        t, temp,
        climatologyPeriod=[clim_start, clim_end],
        pctile=90,
        minDuration=5,
        joinAcrossGaps=True,
        maxGap=2,
    )

    today_idx = -1
    current_sst = float(temp[today_idx])
    climatology_today = float(clim["seas"][today_idx])
    threshold_today = float(clim["thresh"][today_idx])
    anomaly = round(current_sst - climatology_today, 2)

    mhw_active = False
    mhw_duration_days = 0
    if mhws["n_events"] > 0:
        last_end = mhws["date_end"][-1]
        if last_end >= date_objs[-1]:
            mhw_active = True
            mhw_duration_days = int(mhws["duration"][-1])

    mhw_category = _categorize_mhw(max(anomaly, 0), max(threshold_today - climatology_today, 0.1))

    last_7_temps = temp[-7:]
    slope = float(np.polyfit(np.arange(7), last_7_temps, 1)[0])
    forecast = []
    for i in range(1, 8):
        forecast_date = date_objs[-1] + timedelta(days=i)
        sst_forecast = round(float(temp[-1]) + slope * i, 2)
        forecast.append({
            "date": forecast_date.isoformat(),
            "sst_forecast": sst_forecast,
            "status": _tag_forecast_status(sst_forecast, threshold_today),
        })

    result = {
        "site": site_id,
        "current_sst": current_sst,
        "climatology_today": climatology_today,
        "threshold_today": threshold_today,
        "anomaly": anomaly,
        "mhw_active": mhw_active,
        "mhw_duration_days": mhw_duration_days,
        "mhw_category": mhw_category,
        "timeseries": {
            "dates": dates_raw,
            "sst": [round(float(x), 2) for x in temp],
            "climatology": [round(float(x), 2) for x in clim["seas"]],
            "threshold": [round(float(x), 2) for x in clim["thresh"]],
        },
        "forecast": forecast,
    }

    CACHE_DIR.mkdir(exist_ok=True)
    _cache_path(site_id).write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": result,
    }))
    logger.info(f"MHW detection complete for {site_id}, mhw_active={mhw_active}")
    return result
