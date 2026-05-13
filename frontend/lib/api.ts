"use client";

import useSWR from "swr";

const BASE = "http://localhost:8000";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export interface SiteInfo {
  id: string;
  name: string;
}

export interface ForecastDay {
  date: string;
  sst_forecast: number;
  status: "mhw" | "watch" | "normal";
}

export interface Timeseries {
  dates: string[];
  sst: number[];
  climatology: number[];
  threshold: number[];
}

export interface SiteDetection {
  site: string;
  current_sst: number;
  climatology_today: number;
  threshold_today: number;
  anomaly: number;
  mhw_active: boolean;
  mhw_duration_days: number;
  mhw_category: number;
  timeseries: Timeseries;
  forecast: ForecastDay[];
}

export function useSites() {
  return useSWR<SiteInfo[]>(`${BASE}/api/sites`, fetcher, { refreshInterval: 300_000 });
}

export function useSiteDetection(siteId: string) {
  return useSWR<SiteDetection>(`${BASE}/api/detect/${siteId}`, fetcher, { refreshInterval: 300_000 });
}

export function useAllDetections() {
  return useSWR<Record<string, SiteDetection>>(`${BASE}/api/detect/all`, fetcher, { refreshInterval: 300_000 });
}

export async function refreshSite(siteId: string): Promise<void> {
  await fetch(`${BASE}/api/refresh/${siteId}`, { method: "POST" });
}
