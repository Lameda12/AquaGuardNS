import pytest
from unittest.mock import AsyncMock, patch
from mhw_detector import detect_mhw_for_site, _categorize_mhw, _tag_forecast_status


def test_categorize_mhw_cat1():
    assert _categorize_mhw(anomaly=1.5, threshold=1.0) == 1


def test_categorize_mhw_cat2():
    assert _categorize_mhw(anomaly=2.5, threshold=1.0) == 2


def test_categorize_mhw_cat3():
    assert _categorize_mhw(anomaly=3.5, threshold=1.0) == 3


def test_categorize_mhw_cat4():
    assert _categorize_mhw(anomaly=4.5, threshold=1.0) == 4


def test_categorize_mhw_no_event():
    assert _categorize_mhw(anomaly=0.5, threshold=1.0) == 0


def test_tag_forecast_status_mhw():
    assert _tag_forecast_status(sst_forecast=19.0, threshold=17.0) == "mhw"


def test_tag_forecast_status_watch():
    assert _tag_forecast_status(sst_forecast=16.5, threshold=17.0) == "watch"


def test_tag_forecast_status_normal():
    assert _tag_forecast_status(sst_forecast=14.0, threshold=17.0) == "normal"


@pytest.mark.asyncio
async def test_detect_mhw_for_site_returns_required_keys():
    from datetime import date, timedelta
    import math

    def make_sst(days=400):
        records = []
        base = date(2022, 1, 1)
        for i in range(days):
            d = base + timedelta(days=i)
            doy = d.timetuple().tm_yday
            sst = 11.0 + 9.0 * math.sin(2 * math.pi * (doy - 15) / 365)
            records.append({"date": d.isoformat(), "sst": round(sst, 2)})
        return records

    with patch("mhw_detector.get_sst", new=AsyncMock(return_value=make_sst())):
        result = await detect_mhw_for_site("mahone_bay")

    required = [
        "site", "current_sst", "climatology_today", "threshold_today",
        "anomaly", "mhw_active", "mhw_duration_days", "mhw_category",
        "timeseries", "forecast",
    ]
    for key in required:
        assert key in result, f"Missing key: {key}"

    assert isinstance(result["timeseries"]["dates"], list)
    assert isinstance(result["forecast"], list)
    assert len(result["forecast"]) == 7
