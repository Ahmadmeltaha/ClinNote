import { FlaskConical, Activity } from "lucide-react";
import { clsx } from "clsx";
import type { EvaluationMetrics } from "@/types";

interface AnomalyDetectionStatsProps {
  data: EvaluationMetrics["anomaly_detection"];
}

export function AnomalyDetectionStats({ data }: AnomalyDetectionStatsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Card
        title="Lab Anomaly Detection"
        icon={FlaskConical}
        precision={data.lab.precision}
        recall={data.lab.recall}
      />
      <Card
        title="Vital Anomaly Detection"
        icon={Activity}
        precision={data.vital.precision}
        recall={data.vital.recall}
      />
    </div>
  );
}

function Card({
  title,
  icon: Icon,
  precision,
  recall,
}: {
  title: string;
  icon: typeof FlaskConical;
  precision: number;
  recall: number;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
        <Icon className="h-4 w-4" />
        {title}
      </h3>
      <div className="mt-4 space-y-3">
        <Bar label="Precision" value={precision} />
        <Bar label="Recall" value={recall} />
      </div>
    </div>
  );
}

function Bar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-slate-700 dark:text-slate-300">
          {label}
        </span>
        <span className="font-mono tabular-nums text-slate-900 dark:text-slate-100">
          {value.toFixed(2)}
        </span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className={clsx(
            "h-full rounded-full transition-all",
            pct >= 90
              ? "bg-green-500"
              : pct >= 75
                ? "bg-blue-500"
                : "bg-amber-500",
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
