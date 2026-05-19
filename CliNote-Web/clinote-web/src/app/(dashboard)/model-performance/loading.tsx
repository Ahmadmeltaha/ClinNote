import { Skeleton } from "@/components/ui/Skeleton";

export default function ModelPerformanceLoading() {
  return (
    <div className="space-y-6">
      {/* Heading */}
      <div>
        <Skeleton className="h-7 w-56" />
        <Skeleton className="mt-2 h-4 w-72" />
      </div>

      {/* AUROC hero card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <Skeleton className="h-4 w-28" />
        <div className="mt-4 flex items-end gap-3">
          <Skeleton className="h-12 w-32" />
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="mt-3 h-3 w-3/4" />
      </div>

      {/* 5 metric cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800"
          >
            <Skeleton className="h-3 w-16" />
            <Skeleton className="mt-2 h-7 w-20" />
          </div>
        ))}
      </div>

      {/* Ablation chart */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="mt-2 h-3 w-72" />
        <Skeleton className="mt-5 h-64 w-full rounded-lg" />
      </div>

      {/* Anomaly stats + Training info */}
      <div className="grid gap-6 lg:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800"
          >
            <Skeleton className="h-4 w-32" />
            <div className="mt-4 space-y-3">
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-5/6" />
              <Skeleton className="h-3 w-4/6" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
