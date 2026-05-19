import { redirect } from "next/navigation";
import { getAuthSession } from "@/lib/server/auth";
import { getEvaluationMetrics } from "@/lib/server/ai-pipeline";
import { MetricsOverview } from "@/components/model-performance/MetricsOverview";
import { AblationChart } from "@/components/model-performance/AblationChart";
import { AnomalyDetectionStats } from "@/components/model-performance/AnomalyDetectionStats";
import { TrainingInfo } from "@/components/model-performance/TrainingInfo";
import type { EvaluationMetrics } from "@/types";

export default async function ModelPerformancePage() {
  const session = await getAuthSession();
  if (!session?.user) redirect("/login");

  const metrics = (await getEvaluationMetrics()) as EvaluationMetrics;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          Model Performance
        </h2>
        <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">
          Mortality prediction model evaluation on MIMIC-IV ICU data
        </p>
      </div>

      <MetricsOverview metrics={metrics.mortality_prediction} />
      <AblationChart ablation={metrics.ablation} />
      <AnomalyDetectionStats data={metrics.anomaly_detection} />
      <TrainingInfo training={metrics.training} />
    </div>
  );
}
