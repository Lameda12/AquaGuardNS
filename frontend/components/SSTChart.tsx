"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { SiteDetection } from "@/lib/api";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

interface Props {
  data: SiteDetection;
}

export default function SSTChart({ data }: Props) {
  const { dates, sst, climatology, threshold } = data.timeseries;

  const chartData = {
    labels: dates.map((d) => d.slice(5)),
    datasets: [
      {
        label: "SST",
        data: sst,
        borderColor: "#3b82f6",
        backgroundColor: "rgba(239,68,68,0.15)",
        fill: "+1",
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      },
      {
        label: "Threshold (90th pct)",
        data: threshold,
        borderColor: "#f59e0b",
        borderDash: [6, 3],
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 1.5,
        fill: false,
      },
      {
        label: "Climatology",
        data: climatology,
        borderColor: "#64748b",
        borderDash: [3, 3],
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 1.5,
        fill: false,
      },
    ],
  };

  const options = {
    responsive: true,
    interaction: { mode: "index" as const, intersect: false },
    plugins: {
      legend: { labels: { color: "#94a3b8", font: { size: 11 } } },
      tooltip: { backgroundColor: "#1e293b", titleColor: "#f1f5f9", bodyColor: "#94a3b8" },
    },
    scales: {
      x: {
        ticks: { color: "#64748b", maxTicksLimit: 12, font: { size: 10 } },
        grid: { color: "#1e293b" },
      },
      y: {
        ticks: { color: "#64748b", callback: (v: unknown) => `${v}°C` },
        grid: { color: "#1e293b" },
        title: { display: true, text: "°C", color: "#64748b" },
      },
    },
  };

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <h3 className="text-sm text-slate-400 mb-3 uppercase tracking-wide">SST — Historical</h3>
      <Line data={chartData} options={options} />
    </div>
  );
}
