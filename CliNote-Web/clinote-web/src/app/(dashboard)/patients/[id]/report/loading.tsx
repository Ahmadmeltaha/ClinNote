import { Skeleton } from "@/components/ui/Skeleton";

export default function ReportLoading() {
  return (
    <div className="space-y-5">
      {/* Back link */}
      <Skeleton className="h-4 w-32" />

      {/* Report header */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <Skeleton className="h-6 w-72" />
            <Skeleton className="h-3 w-48" />
          </div>
          <Skeleton className="h-7 w-24 rounded-full" />
        </div>
      </div>

      {/* Body grid: content + sidebar */}
      <div className="grid gap-5 lg:grid-cols-3">
        {/* Content */}
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <Skeleton className="h-5 w-32" />
            <div className="mt-4 space-y-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <Skeleton
                  key={i}
                  className={`h-3 ${i % 3 === 0 ? "w-11/12" : i % 3 === 1 ? "w-10/12" : "w-9/12"}`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="mt-3 h-9 w-full rounded-md" />
            <Skeleton className="mt-2 h-9 w-full rounded-md" />
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <Skeleton className="h-4 w-28" />
            <div className="mt-3 space-y-2">
              <Skeleton className="h-3 w-3/4" />
              <Skeleton className="h-3 w-2/3" />
              <Skeleton className="h-3 w-3/5" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
