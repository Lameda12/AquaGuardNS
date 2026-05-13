"""AquaGuard NS — FastAPI application."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from mhw_detector import detect_mhw_for_site, _load_cached_mhw
from sites import SITES


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Warming up MHW cache for all sites...")
    results = await asyncio.gather(
        *[detect_mhw_for_site(site_id) for site_id in SITES],
        return_exceptions=True,
    )
    for site_id, result in zip(SITES.keys(), results):
        if isinstance(result, Exception):
            logger.warning(f"Warmup failed for {site_id}: {result}")
        else:
            logger.info(f"Warmup OK for {site_id}")
    logger.info("Startup warmup complete.")
    yield


app = FastAPI(title="AquaGuard NS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/sites")
async def list_sites():
    return [{"id": site_id, "name": info["name"]} for site_id, info in SITES.items()]


@app.get("/api/detect/all")
async def detect_all():
    results = await asyncio.gather(
        *[detect_mhw_for_site(site_id) for site_id in SITES],
        return_exceptions=True,
    )
    return {
        site_id: (result if not isinstance(result, Exception) else {"error": str(result)})
        for site_id, result in zip(SITES.keys(), results)
    }


@app.get("/api/detect/{site_id}")
async def detect_site(site_id: str):
    if site_id not in SITES:
        raise HTTPException(status_code=404, detail=f"Unknown site: {site_id}")
    try:
        return await detect_mhw_for_site(site_id)
    except Exception as e:
        logger.error(f"Detection failed for {site_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "detection_failed", "detail": str(e)})


@app.post("/api/refresh/{site_id}")
async def refresh_site(site_id: str):
    if site_id not in SITES:
        raise HTTPException(status_code=404, detail=f"Unknown site: {site_id}")
    # Delete cached files to force re-fetch
    from data_fetcher import CACHE_DIR
    sst_cache = CACHE_DIR / f"{site_id}_sst.json"
    mhw_cache = CACHE_DIR / f"{site_id}_mhw.json"
    if sst_cache.exists():
        sst_cache.unlink()
    if mhw_cache.exists():
        mhw_cache.unlink()
    try:
        result = await detect_mhw_for_site(site_id)
        return {"status": "refreshed", "data": result}
    except Exception as e:
        logger.error(f"Refresh failed for {site_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "refresh_failed", "detail": str(e)})
