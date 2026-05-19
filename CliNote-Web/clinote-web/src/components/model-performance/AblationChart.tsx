"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  LabelList,
  ResponsiveContainer,
} from "recharts";
import { Layers } from "lucide-react";

interface AblationChartProps {
  ablation: Record<string, number>;
}

const ORDER = ["text_only", "labs_only", "vitals_only", "full_fusion"] as const;
const LABELS: Record<string, string> = {
  text_only: "Text Only",
  labs_only: "Labs Only",
  vitals_only: "Vitals Only",
  full_fusion: "Full Fusion",
};

export function AblationChart({ ablation }: AblationChartProps) {
  const data = ORDER.filter((k) => k in ablation).map((k) => ({
    modality: LABELS[k],
    auroc: ablation[k],
    isFull: k === "full_fusion",
  }));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
        <Layers className="h-4 w-4" />
        Multimodal Fusion vs Single-Modality Performance
      </h3>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
        Combining clinical notes, lab results, and vital signs improves
        prediction accuracy over any single data source.
      </p>

      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 20, right: 20, left: -10, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              className="stroke-slate-200 dark:stroke-slate-700"
            />
            <XAxis
              dataKey="modality"
              tick={{ fontSize: 12 }}
              className="fill-slate-500 dark:fill-slate-400"
            />
            <YAxis
              domain={[0.5, 1]}
              tick={{ fontSize: 11 }}
              tickFormatter={(v: number) => v.toFixed(2)}
              className="fill-slate-500 dark:fill-slate-400"
            />
            <Tooltip
              contentStyle={{
                fontSize: 12,
                borderRadius: 8,
                border: "1px solid #cbd5e1",
              }}
              formatter={(v: unknown) => [
                typeof v === "number" ? v.toFixed(4) : String(v),
                "AUROC",
              ]}
            />
            <Bar dataKey="auroc" radius={[6, 6, 0, 0]}>
              {data.map((d, i) => (
                <Cell
                  key={i}
                  fill={d.isFull ? "#2563eb" : "#94a3b8"}
                />
              ))}
              <LabelList
                dataKey="auroc"
                position="top"
                formatter={(v: unknown) =>
                  typeof v === "number" ? v.toFixed(3) : String(v)
                }
                style={{ fontSize: 11, fontWeight: 600 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
