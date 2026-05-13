"use client";

import type { SiteDetection } from "@/lib/api";

const THRESHOLDS = {
  "Atlantic Salmon": { stress: 16.0, critical: 18.0, lethal: 23.0 },
  "Blue Mussel":     { stress: 20.0, critical: 24.0, lethal: 27.0 },
  "Eastern Oyster":  { stress: 28.0, critical: 32.0, lethal: 35.0 },
} as const;

type Species = keyof typeof THRESHOLDS;

function clamp(val: number, min: number, max: number) {
  return Math.max(min, Math.min(max, val));
}

function riskPct(sst: number, low: number, high: number): number {
  return clamp(((sst - low) / (high - low)) * 100, 0, 100);
}

function ProgressBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs text-slate-400 mb-1">
        <span>{label}</span>
        <span>{pct.toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

interface Props {
  data: SiteDetection;
}

export default function SpeciesRisk({ data }: Props) {
  const sst = data.current_sst;

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <h3 className="text-sm text-slate-400 mb-3 uppercase tracking-wide">Species Risk</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {(Object.keys(THRESHOLDS) as Species[]).map((species) => {
          const t = THRESHOLDS[species];
          const thermal = riskPct(sst, t.stress, t.lethal);
          const mortality = riskPct(sst, t.critical, t.lethal);
          const disease = riskPct(sst, t.stress, t.critical);

          return (
            <div key={species} className="bg-slate-900 rounded-lg p-3">
              <div className="text-sm font-semibold text-white mb-3">{species}</div>
              <ProgressBar label="Thermal Stress" pct={thermal} color="bg-yellow-500" />
              <ProgressBar label="Mortality Risk" pct={mortality} color="bg-red-500" />
              <ProgressBar label="Disease Risk" pct={disease} color="bg-orange-500" />
            </div>
          );
        })}
      </div>
    </div>
  );
}
