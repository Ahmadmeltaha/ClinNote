import { redirect } from "next/navigation";
import {
  PieChart,
  Users,
  AlertTriangle,
  Activity,
  Layers,
  TrendingUp,
} from "lucide-react";
import { getAuthSession } from "@/lib/server/auth";
import { getCohortStatsWithBreakdown } from "@/lib/server/cohort";
import { clsx } from "clsx";

export const dynamic = "force-dynamic";

export default async function StatisticsPage() {
  const session = await getAuthSession();
  if (!session?.user) redirect("/login");

  const { stats, riskCounts, histogram } = await getCohortStatsWithBreakdown();

  const avgPct =
    stats.avgMortalityRisk != null
      ? `${(stats.avgMortalityRisk * 100).toFixed(1)}%`
      : "—";
  const totalRisk = riskCounts.HIGH + riskCounts.MEDIUM + riskCounts.LOW;
  const maxHistogram = Math.max(1, ...histogram);

  return (
    <div className="space-y-8">
      <div className="flex items-start gap-4">
        <div className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400">
          <PieChart className="h-6 w-6" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Statistics
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Cohort-wide numbers across every admission in ClinNote.
          </p>
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="animate-cn-fade-up-lg" style={{ animationDelay: "0ms" }}>
          <StatCard
            accent="blue"
            icon={Users}
            label="Total patients"
            value={stats.totalPatients.toLocaleString()}
            sub={`${stats.totalAdmissions.toLocaleString()} admissions analyzed`}
          />
        </div>
        <div className="animate-cn-fade-up-lg" style={{ animationDelay: "80ms" }}>
          <StatCard
            accent="amber"
            icon={Layers}
            label="High-risk admissions"
            value={stats.highRiskCount.toLocaleString()}
            sub={`${pct(stats.highRiskCount, stats.totalAdmissions)} of admissions`}
          />
        </div>
        <div className="animate-cn-fade-up-lg" style={{ animationDelay: "160ms" }}>
          <StatCard
            accent="violet"
            icon={Activity}
            label="Avg mortality risk"
            value={avgPct}
            sub="Across analyzed admissions"
          />
        </div>
        <div className="animate-cn-fade-up-lg" style={{ animationDelay: "240ms" }}>
          <StatCard
            accent="red"
            icon={AlertTriangle}
            label="Critical alerts"
            value={stats.criticalAlertCount.toLocaleString()}
            sub={`${stats.totalAlerts.toLocaleString()} alerts unresolved`}
          />
        </div>
      </div>

      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Risk distribution */}
        <div
          className="animate-cn-fade-up-lg relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800"
          style={{ animationDelay: "320ms" }}
        >
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-slate-500 dark:text-slate-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-200">
              Admissions by Risk Level
            </h3>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            How {totalRisk.toLocaleString()} admissions distribute across risk
            buckets.
          </p>
          <div className="mt-6 space-y-5">
            <RiskRow
              label="HIGH"
              count={riskCounts.HIGH}
              total={totalRisk}
              barClass="bg-gradient-to-r from-red-400 to-red-600"
              labelClass="text-red-700 dark:text-red-300"
            />
            <RiskRow
              label="MEDIUM"
              count={riskCounts.MEDIUM}
              total={totalRisk}
              barClass="bg-gradient-to-r from-amber-400 to-amber-600"
              labelClass="text-amber-700 dark:text-amber-300"
            />
            <RiskRow
              label="LOW"
              count={riskCounts.LOW}
              total={totalRisk}
              barClass="bg-gradient-to-r from-emerald-400 to-emerald-600"
              labelClass="text-emerald-700 dark:text-emerald-300"
            />
          </div>
        </div>

        {/* Mortality histogram */}
        <div
          className="animate-cn-fade-up-lg relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800"
          style={{ animationDelay: "400ms" }}
        >
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-slate-500 dark:text-slate-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-200">
              Mortality Probability Distribution
            </h3>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Each bar is a 10% mortality bucket. Taller = more admissions.
          </p>
          <div className="mt-6 flex h-44 items-end gap-1.5">
            {histogram.map((count, i) => {
              const heightPct = (count / maxHistogram) * 100;
              const lo = i * 10;
              const hi = (i + 1) * 10;
              const accent =
                lo >= 40
                  ? "from-red-400 to-red-600"
                  : lo >= 20
                    ? "from-amber-400 to-amber-600"
                    : "from-emerald-400 to-emerald-600";
              return (
                <div
                  key={i}
                  className="group flex h-full flex-1 flex-col items-center justify-end gap-1.5"
                >
                  <span className="invisible text-[10px] font-bold tabular-nums text-slate-600 group-hover:visible dark:text-slate-300">
                    {count}
                  </span>
                  <div
                    className={clsx(
                      "w-full rounded-t-md bg-gradient-to-t shadow-sm transition-all duration-500 hover:brightness-110",
                      accent,
                    )}
                    style={{ height: `${heightPct}%`, minHeight: count > 0 ? "4px" : "0" }}
                  />
                  <span className="text-[9px] font-mono text-slate-500 dark:text-slate-500">
                    {lo}-{hi}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function RiskRow({
  label,
  count,
  total,
  barClass,
  labelClass,
}: {
  label: string;
  count: number;
  total: number;
  barClass: string;
  labelClass: string;
}) {
  const pct = total === 0 ? 0 : (count / total) * 100;
  return (
    <div>
      <div className="flex items-center justify-between text-xs font-bold">
        <span className={labelClass}>{label}</span>
        <span className="tabular-nums text-slate-700 dark:text-slate-300">
          {count.toLocaleString()}{" "}
          <span className="font-normal text-slate-500 dark:text-slate-400">
            ({pct.toFixed(0)}%)
          </span>
        </span>
      </div>
      <div className="mt-1.5 h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700/50">
        <div
          className={clsx(
            "h-full rounded-full transition-all duration-700 ease-out",
            barClass,
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function pct(n: number, total: number): string {
  if (total === 0) return "—";
  return `${((n / total) * 100).toFixed(0)}%`;
}

type Accent = "blue" | "amber" | "violet" | "red";
const ACCENTS: Record<
  Accent,
  { bar: string; iconBg: string; iconColor: string; glow: string }
> = {
  blue: {
    bar: "bg-gradient-to-r from-blue-400 to-blue-600",
    iconBg: "bg-blue-100 dark:bg-blue-900/40",
    iconColor: "text-blue-600 dark:text-blue-400",
    glow: "hover:shadow-blue-500/20",
  },
  amber: {
    bar: "bg-gradient-to-r from-amber-400 to-amber-600",
    iconBg: "bg-amber-100 dark:bg-amber-900/40",
    iconColor: "text-amber-600 dark:text-amber-400",
    glow: "hover:shadow-amber-500/20",
  },
  violet: {
    bar: "bg-gradient-to-r from-violet-400 to-violet-600",
    iconBg: "bg-violet-100 dark:bg-violet-900/40",
    iconColor: "text-violet-600 dark:text-violet-400",
    glow: "hover:shadow-violet-500/20",
  },
  red: {
    bar: "bg-gradient-to-r from-red-400 to-red-600",
    iconBg: "bg-red-100 dark:bg-red-900/40",
    iconColor: "text-red-600 dark:text-red-400",
    glow: "hover:shadow-red-500/20",
  },
};

function StatCard({
  accent,
  icon: Icon,
  label,
  value,
  sub,
}: {
  accent: Accent;
  icon: typeof Users;
  label: string;
  value: string;
  sub?: string;
}) {
  const a = ACCENTS[accent];
  return (
    <div
      className={
        "group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl dark:border-slate-700 dark:bg-slate-800 " +
        a.glow
      }
    >
      <div
        className={"absolute inset-x-0 top-0 h-1 " + a.bar}
        aria-hidden="true"
      />
      <div className="flex items-start justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {label}
        </p>
        <div
          className={
            "inline-flex h-9 w-9 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110 " +
            a.iconBg
          }
        >
          <Icon className={"h-4 w-4 " + a.iconColor} />
        </div>
      </div>
      <p className="mt-3 text-3xl font-bold text-slate-900 dark:text-slate-100">
        {value}
      </p>
      {sub && (
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{sub}</p>
      )}
    </div>
  );
}
