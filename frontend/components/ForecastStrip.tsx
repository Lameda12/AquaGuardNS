"use client";

import type { ForecastDay } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  mhw: "bg-red-900 border-red-500 text-red-200",
  watch: "bg-amber-900 border-amber-500 text-amber-200",
  normal: "bg-slate-800 border-slate-600 text-slate-300",
};

const STATUS_LABEL: Record<string, string> = {
  mhw: "MHW",
  watch: "Watch",
  normal: "Normal",
};

interface Props {
  forecast: ForecastDay[];
}

export default function ForecastStrip({ forecast }: Props) {
  return (
    <div className="bg-slate-900 rounded-xl p-4">
      <h3 className="text-sm text-slate-400 mb-3 uppercase tracking-wide">7-Day Forecast</h3>
      <div className="grid grid-cols-7 gap-2">
        {forecast.map((day) => (
          <div
            key={day.date}
            className={`rounded-lg border p-2 text-center ${STATUS_STYLES[day.status]}`}
          >
            <div className="text-xs font-medium">{day.date.slice(5)}</div>
            <div className="text-sm font-bold mt-1">{day.sst_forecast.toFixed(1)}°</div>
            <div className="text-xs mt-1 opacity-80">{STATUS_LABEL[day.status]}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
