import { Cpu } from "lucide-react";
import type { EvaluationMetrics } from "@/types";

interface TrainingInfoProps {
  training: EvaluationMetrics["training"];
}

export function TrainingInfo({ training }: TrainingInfoProps) {
  const items = [
    { label: "Epochs", value: training.epochs.toString() },
    { label: "Best Epoch", value: training.best_epoch.toString() },
    { label: "Optimizer", value: training.optimizer },
    { label: "Learning Rate", value: training.learning_rate.toExponential(1) },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/30">
      <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
        <Cpu className="h-3.5 w-3.5" />
        Training Details
      </h3>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {items.map((item) => (
          <div key={item.label}>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              {item.label}
            </p>
            <p className="mt-0.5 font-mono text-sm tabular-nums text-slate-700 dark:text-slate-200">
              {item.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
