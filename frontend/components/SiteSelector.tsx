"use client";

import type { SiteDetection } from "@/lib/api";

const BADGE_STYLES: Record<string, string> = {
  mhw: "bg-red-500 text-white",
  watch: "bg-amber-500 text-white",
  normal: "bg-emerald-600 text-white",
};

function siteStatus(data: SiteDetection): "mhw" | "watch" | "normal" {
  if (data.mhw_active) return "mhw";
  if (data.forecast.some((d) => d.status !== "normal")) return "watch";
  return "normal";
}

function formatSiteName(siteId: string): string {
  return siteId.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

interface Props {
  allData: Record<string, SiteDetection>;
  selectedSite: string;
  onSelect: (siteId: string) => void;
}

export default function SiteSelector({ allData, selectedSite, onSelect }: Props) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {Object.entries(allData).map(([siteId, data]) => {
        const status = siteStatus(data);
        const isActive = siteId === selectedSite;
        return (
          <button
            key={siteId}
            onClick={() => onSelect(siteId)}
            className={`rounded-xl p-4 text-left transition-all border ${
              isActive
                ? "border-blue-500 bg-blue-900/30"
                : "border-slate-700 bg-slate-800 hover:border-slate-500"
            }`}
          >
            <div className="flex justify-between items-start mb-2">
              <span className="text-sm font-semibold text-white">{formatSiteName(siteId)}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${BADGE_STYLES[status]}`}>
                {status.toUpperCase()}
              </span>
            </div>
            <div className="text-2xl font-bold text-white">{data.current_sst.toFixed(1)}°C</div>
          </button>
        );
      })}
    </div>
  );
}
