import { TrendingUp } from "lucide-react";
import type { EvaluationMetrics } from "@/types";

interface MetricsOverviewProps {
  metrics: EvaluationMetrics["mortality_prediction"];
}

const METRIC_DESCRIPTIONS: Record<string, string> = {
  AUPRC: "Area Under Precision-Recall Curve",
  F1: "Harmonic mean of precision and recall",
  Accuracy: "Correct predictions / total",
  Sensitivity: "True positive rate (recall)",
  Specificity: "True negative rate",
};

export function MetricsOverview({ metrics }: MetricsOverviewProps) {
  return (
    <div className="space-y-4">
      {/* Hero AUROC card */}
      <div className="rounded-xl border border-slate-200 bg-gradient-to-br from-blue-50 to-white p-6 shadow-sm dark:border-slate-700 dark:from-blue-950/30 dark:to-slate-800">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              AUROC
            </p>
            <p className="mt-1 text-5xl font-bold tabular-nums text-blue-600 dark:text-blue-400">
              {metrics.auroc.toFixed(3)}
            </p>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              Area Under ROC Curve — overall mortality discrimination
            </p>
          </div>
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/40">
            <TrendingUp className="h-7 w-7 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </div>

      {/* 5 supporting metrics */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <SmallMetric
          label="AUPRC"
          value={metrics.auprc}
          description={METRIC_DESCRIPTIONS.AUPRC}
        />
        <SmallMetric
          label="F1 Score"
          value={metrics.f1_score}
          description={METRIC_DESCRIPTIONS.F1}
        />
        <SmallMetric
          label="Accuracy"
          value={metrics.accuracy}
          description={METRIC_DESCRIPTIONS.Accuracy}
        />
        <SmallMetric
          label="Sensitivity"
          value={metrics.sensitivity}
          description={METRIC_DESCRIPTIONS.Sensitivity}
        />
        <SmallMetric
          label="Specificity"
          value={metrics.specificity}
          description={METRIC_DESCRIPTIONS.Specificity}
        />
      </div>
    </div>
  );
}

function SmallMetric({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
        {label}
      </p>
      <p className="mt-1 text-2xl font-bold tabular-nums text-slate-900 dark:text-slate-100">
        {value.toFixed(3)}
      </p>
      <p className="mt-1 text-[11px] leading-tight text-slate-500 dark:text-slate-400">
        {description}
      </p>
    </div>
  );
}
