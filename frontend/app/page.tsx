"use client";

import { useState } from "react";
import { useAllDetections } from "@/lib/api";
import SiteSelector from "@/components/SiteSelector";
import StatCards from "@/components/StatCards";
import SSTChart from "@/components/SSTChart";
import AlertPanel from "@/components/AlertPanel";
import SpeciesRisk from "@/components/SpeciesRisk";
import ForecastStrip from "@/components/ForecastStrip";

export default function Dashboard() {
  const [selectedSite, setSelectedSite] = useState("mahone_bay");
  const { data: allData, error, isLoading } = useAllDetections();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-400 text-sm">Loading MHW data...</div>
      </div>
    );
  }

  if (error || !allData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-400 text-sm">Backend unavailable. Start FastAPI on port 8000.</div>
      </div>
    );
  }

  const activeAlerts = Object.values(allData).filter((d) => d.mhw_active).length;
  const siteData = allData[selectedSite];

  if (!siteData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-400 text-sm">Site data not found.</div>
      </div>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-white">AquaGuard NS</span>
          <span className="flex items-center gap-1 bg-emerald-900 text-emerald-400 text-xs px-2 py-1 rounded-full font-medium">
            <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse inline-block" />
            LIVE
          </span>
        </div>
        {activeAlerts > 0 && (
          <span className="bg-red-600 text-white text-sm px-3 py-1 rounded-full font-semibold">
            {activeAlerts} Active Alert{activeAlerts > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Site Selection */}
      <div className="mb-6">
        <SiteSelector allData={allData} selectedSite={selectedSite} onSelect={setSelectedSite} />
      </div>

      {/* Stats */}
      <div className="mb-6">
        <StatCards data={siteData} />
      </div>

      {/* Chart + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className="lg:col-span-2">
          <SSTChart data={siteData} />
        </div>
        <div>
          <AlertPanel data={siteData} />
        </div>
      </div>

      {/* Forecast */}
      <div className="mb-6">
        <ForecastStrip forecast={siteData.forecast} />
      </div>

      {/* Species Risk */}
      <SpeciesRisk data={siteData} />
    </main>
  );
}
