"use client";

import type { SiteDetection } from "@/lib/api";

interface Alert {
  severity: "critical" | "moderate" | "watch";
  title: string;
  message: string;
}

function buildAlerts(data: SiteDetection): Alert[] {
  const alerts: Alert[] = [];
  if (!data.mhw_active) return alerts;

  if (data.mhw_category >= 3) {
    alerts.push({
      severity: "critical",
      title: `Cat ${data.mhw_category} Marine Heatwave Active`,
      message: `SST ${data.current_sst.toFixed(1)}°C — ${data.anomaly.toFixed(1)}°C above climatology for ${data.mhw_duration_days} days.`,
    });
  } else if (data.mhw_category === 2) {
    alerts.push({
      severity: "moderate",
      title: "Cat II Marine Heatwave Active",
      message: `SST ${data.current_sst.toFixed(1)}°C — ${data.anomaly.toFixed(1)}°C above threshold for ${data.mhw_duration_days} days.`,
    });
  } else {
    alerts.push({
      severity: "watch",
      title: "Marine Heatwave Watch",
      message: `SST ${data.current_sst.toFixed(1)}°C approaching threshold. Monitor closely.`,
    });
  }

  const watchDays = data.forecast.filter((d) => d.status !== "normal").length;
  if (watchDays > 3) {
    alerts.push({
      severity: "watch",
      title: "Extended Elevated SST Forecast",
      message: `${watchDays} of next 7 days forecast above threshold.`,
    });
  }

  return alerts;
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: "border-red-500 bg-red-950",
  moderate: "border-amber-500 bg-amber-950",
  watch: "border-blue-500 bg-blue-950",
};

interface Props {
  data: SiteDetection;
}

export default function AlertPanel({ data }: Props) {
  const alerts = buildAlerts(data);

  if (alerts.length === 0) {
    return (
      <div className="bg-slate-800 rounded-xl p-4">
        <h3 className="text-sm text-slate-400 mb-3 uppercase tracking-wide">Alerts</h3>
        <p className="text-slate-500 text-sm">No active alerts</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <h3 className="text-sm text-slate-400 mb-3 uppercase tracking-wide">Alerts ({alerts.length})</h3>
      <div className="flex flex-col gap-2">
        {alerts.map((alert, i) => (
          <div key={i} className={`border-l-4 rounded-r-lg p-3 ${SEVERITY_STYLES[alert.severity]}`}>
            <div className="font-semibold text-sm text-white">{alert.title}</div>
            <div className="text-xs text-slate-300 mt-1">{alert.message}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
