"use client";

import type { SiteDetection } from "@/lib/api";

const CATEGORY_LABELS: Record<number, string> = {
  0: "None",
  1: "Cat I",
  2: "Cat II",
  3: "Cat III",
  4: "Cat IV",
};

const CATEGORY_COLORS: Record<number, string> = {
  0: "text-slate-400",
  1: "text-yellow-400",
  2: "text-orange-400",
  3: "text-red-400",
  4: "text-red-600",
};

interface Props {
  data: SiteDetection;
}

function Card({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 flex flex-col gap-1">
      <span className="text-xs text-slate-400 uppercase tracking-wide">{label}</span>
      <span className="text-2xl font-bold text-white">{value}</span>
      {sub && <span className="text-xs text-slate-500">{sub}</span>}
    </div>
  );
}

export default function StatCards({ data }: Props) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <Card
        label="Current SST"
        value={`${data.current_sst.toFixed(1)}°C`}
        sub={`Climatology: ${data.climatology_today.toFixed(1)}°C`}
      />
      <Card
        label="Anomaly"
        value={`+${data.anomaly.toFixed(2)}°C`}
        sub={`Threshold: ${data.threshold_today.toFixed(1)}°C`}
      />
      <Card
        label="Duration"
        value={data.mhw_active ? `${data.mhw_duration_days} days` : "—"}
        sub={data.mhw_active ? "Active MHW" : "No active event"}
      />
      <div className="bg-slate-800 rounded-xl p-4 flex flex-col gap-1">
        <span className="text-xs text-slate-400 uppercase tracking-wide">MHW Category</span>
        <span className={`text-2xl font-bold ${CATEGORY_COLORS[data.mhw_category]}`}>
          {CATEGORY_LABELS[data.mhw_category]}
        </span>
      </div>
    </div>
  );
}
