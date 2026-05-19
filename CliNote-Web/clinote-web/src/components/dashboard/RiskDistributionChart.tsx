"use client";

import {
  PieChart,
  Pie,
  Cell,
  Legend,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { PieChart as PieIcon } from "lucide-react";

interface RiskDistributionChartProps {
  low: number;
  medium: number;
  high: number;
  notAnalyzed: number;
}

const COLORS = {
  LOW: "#16a34a",
  MEDIUM: "#f59e0b",
  HIGH: "#dc2626",
  "Not Analyzed": "#94a3b8",
};

export function RiskDistributionChart({
  low,
  medium,
  high,
  notAnalyzed,
}: RiskDistributionChartProps) {
  const total = low + medium + high + notAnalyzed;
  const data = [
    { name: "LOW", value: low, color: COLORS.LOW },
    { name: "MEDIUM", value: medium, color: COLORS.MEDIUM },
    { name: "HIGH", value: high, color: COLORS.HIGH },
    {
      name: "Not Analyzed",
      value: notAnalyzed,
      color: COLORS["Not Analyzed"],
    },
  ].filter((d) => d.value > 0);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
        <PieIcon className="h-4 w-4" />
        Patient Risk Distribution
      </h3>

      {total === 0 ? (
        <p className="py-8 text-center text-sm text-slate-400 dark:text-slate-500">
          No patients yet
        </p>
      ) : (
        <>
          <div className="mt-4 h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {data.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    fontSize: 12,
                    borderRadius: 8,
                    border: "1px solid #cbd5e1",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Stat rows below */}
          <div className="mt-3 space-y-1.5 text-sm">
            {data.map((d) => (
              <div
                key={d.name}
                className="flex items-center justify-between text-slate-700 dark:text-slate-300"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: d.color }}
                  />
                  <span>{d.name}</span>
                </div>
                <div className="text-xs tabular-nums text-slate-500 dark:text-slate-400">
                  {d.value} ({Math.round((d.value / total) * 100)}%)
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
