import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from data_fetcher import load_cached_sst, get_sst


def test_load_cached_sst_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("data_fetcher.CACHE_DIR", tmp_path)
    result = load_cached_sst("mahone_bay")
    assert result is None


def test_load_cached_sst_fresh(tmp_path, monkeypatch):
    monkeypatch.setattr("data_fetcher.CACHE_DIR", tmp_path)
    data = [{"date": "2026-05-12", "sst": 12.5}]
    cache_file = tmp_path / "mahone_bay_sst.json"
    cache_file.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }))
    result = load_cached_sst("mahone_bay")
    assert result == data


def test_load_cached_sst_stale(tmp_path, monkeypatch):
    monkeypatch.setattr("data_fetcher.CACHE_DIR", tmp_path)
    cache_file = tmp_path / "mahone_bay_sst.json"
    cache_file.write_text(json.dumps({
        "fetched_at": "2020-01-01T00:00:00+00:00",
        "data": [],
    }))
    result = load_cached_sst("mahone_bay")
    assert result is None


@pytest.mark.asyncio
async def test_get_sst_uses_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("data_fetcher.CACHE_DIR", tmp_path)
    data = [{"date": "2026-05-12", "sst": 12.5}]
    cache_file = tmp_path / "mahone_bay_sst.json"
    cache_file.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }))
    result = await get_sst("mahone_bay")
    assert result == data


@pytest.mark.asyncio
async def test_get_sst_falls_back_to_csv(tmp_path, monkeypatch):
    monkeypatch.setattr("data_fetcher.CACHE_DIR", tmp_path)
    fallback = tmp_path / "mahone_bay_fallback.csv"
    fallback.write_text("date,sst_celsius\n2026-05-12,12.5\n")
    monkeypatch.setattr("data_fetcher.DATA_DIR", tmp_path)

    with patch("data_fetcher.fetch_erddap_sst", side_effect=Exception("ERDDAP down")):
        result = await get_sst("mahone_bay")

    assert len(result) == 1
    assert result[0]["date"] == "2026-05-12"
    assert result[0]["sst"] == 12.5
