import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import {
  ArrowLeft,
  User,
  Calendar,
  AlertTriangle,
  Activity,
  TrendingUp,
  ChevronRight,
} from "lucide-react";
import { clsx } from "clsx";
import { getAuthSession } from "@/lib/server/auth";
import { getPatientOverview } from "@/lib/server/cohort";
import { CohortUpdateForm } from "@/components/patient-detail/CohortUpdateForm";

export const dynamic = "force-dynamic";

const RISK_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  HIGH: {
    bg: "bg-red-100 dark:bg-red-900/40",
    text: "text-red-800 dark:text-red-300",
    dot: "bg-red-500",
  },
  MEDIUM: {
    bg: "bg-amber-100 dark:bg-amber-900/40",
    text: "text-amber-800 dark:text-amber-300",
    dot: "bg-amber-500",
  },
  LOW: {
    bg: "bg-emerald-100 dark:bg-emerald-900/40",
    text: "text-emerald-800 dark:text-emerald-300",
    dot: "bg-emerald-500",
  },
};

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default async function PatientOverviewPage({
  params,
  searchParams,
}: {
  params: Promise<{ subjectId: string }>;
  searchParams: Promise<{ action?: string }>;
}) {
  const session = await getAuthSession();
  if (!session?.user) redirect("/login");

  const { subjectId: raw } = await params;
  const { action } = await searchParams;
  const showUpdate = action === "update";
  const subjectId = Number.parseInt(raw, 10);
  if (!Number.isFinite(subjectId)) notFound();

  const overview = await getPatientOverview(subjectId);
  if (!overview) notFound();

  const risk = overview.highestRisk;
  const riskPalette = risk ? RISK_COLORS[risk] : null;
  const latestHadmId = overview.admissions[0]?.hadmId;

  return (
    <div className="space-y-6">
      <Link
        href="/patients"
        className="inline-flex items-center gap-1.5 text-sm text-slate-600 transition-colors hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to patients
      </Link>

      {/* Patient header */}
      <div className="animate-cn-fade-up relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-700 dark:bg-slate-800">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-gradient-to-br from-blue-300/30 to-blue-500/10 blur-3xl dark:from-blue-700/20 dark:to-blue-900/10"
        />

        <div className="relative flex flex-wrap items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 shadow-lg shadow-blue-500/40 ring-4 ring-blue-500/20">
              <User className="h-8 w-8 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
                Patient Overview
              </p>
              <h1 className="mt-1 bg-gradient-to-br from-slate-900 to-slate-600 bg-clip-text text-3xl font-extrabold text-transparent dark:from-slate-50 dark:to-slate-300">
                {overview.displayName}
              </h1>
              <p className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-slate-500 dark:text-slate-400">
                <span className="font-mono">ID {overview.subjectId}</span>
                <span>·</span>
                <span>{overview.age} years</span>
                <span>·</span>
                <span>{overview.gender === "M" ? "Male" : "Female"}</span>
              </p>
            </div>
          </div>
          {risk && riskPalette && (
            <div className="rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 backdrop-blur dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Highest risk recorded
              </p>
              <div className="mt-1 flex items-center gap-2">
                <span
                  className={clsx("h-2.5 w-2.5 rounded-full", riskPalette.dot)}
                />
                <span className={clsx("text-2xl font-bold", riskPalette.text)}>
                  {overview.highestProbability != null
                    ? `${(overview.highestProbability * 100).toFixed(0)}%`
                    : "—"}
                </span>
                <span
                  className={clsx(
                    "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                    riskPalette.bg,
                    riskPalette.text,
                  )}
                >
                  {risk}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <OverviewStat
          accent="blue"
          icon={Activity}
          label="Admissions"
          value={overview.admissions.length.toString()}
          delay={0}
        />
        <OverviewStat
          accent="violet"
          icon={TrendingUp}
          label="Avg mortality"
          value={
            overview.avgProbability != null
              ? `${(overview.avgProbability * 100).toFixed(1)}%`
              : "—"
          }
          delay={80}
        />
        <OverviewStat
          accent="red"
          icon={AlertTriangle}
          label="Critical alerts"
          value={overview.criticalAlerts.toString()}
          sub={`${overview.totalAlerts} total unresolved`}
          delay={160}
        />
        <OverviewStat
          accent="emerald"
          icon={Calendar}
          label="First → Latest"
          value={formatDate(overview.firstAdmission)}
          sub={`→ ${formatDate(overview.latestAdmission)}`}
          delay={240}
        />
      </div>

      {/* Update form — only shown in update mode (Case 2 from dashboard) */}
      {showUpdate && latestHadmId != null && (
        <div
          className="animate-cn-fade-up"
          style={{ animationDelay: "300ms" }}
        >
          <CohortUpdateForm hadmId={latestHadmId} />
        </div>
      )}

      {/* Admissions list */}
      <div>
        <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
          Admissions History
        </h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {showUpdate
            ? "Existing admissions for this patient. Submit the form above to add a new one."
            : "Click any admission to open its full AI analysis dashboard."}
        </p>

        <ul className="mt-4 space-y-3">
          {overview.admissions.map((a, i) => {
            const riskKey = a.riskLevel ?? "LOW";
            const palette = RISK_COLORS[riskKey];
            return (
              <li
                key={a.hadmId}
                className="animate-cn-fade-up"
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <Link
                  href={`/patients/${a.hadmId}`}
                  className="group relative flex items-center gap-4 overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl dark:border-slate-700 dark:bg-slate-800"
                >
                  {/* Risk-colored accent bar */}
                  <div
                    className={clsx(
                      "absolute inset-y-0 left-0 w-1.5 transition-all duration-300 group-hover:w-2",
                      palette.dot,
                    )}
                    aria-hidden="true"
                  />

                  <div
                    className={clsx(
                      "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl",
                      palette.bg,
                    )}
                  >
                    <span
                      className={clsx("text-lg font-bold", palette.text)}
                    >
                      #{i + 1}
                    </span>
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-mono text-sm font-bold text-slate-900 dark:text-slate-100">
                        #{a.hadmId}
                      </p>
                      {a.riskLevel && (
                        <span
                          className={clsx(
                            "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                            palette.bg,
                            palette.text,
                          )}
                        >
                          {a.riskLevel}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                      <Calendar className="h-3 w-3" />
                      {formatDate(a.admissionDate)}
                    </p>
                  </div>

                  {a.probability != null && (
                    <div className="text-right">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Mortality
                      </p>
                      <p
                        className={clsx(
                          "text-xl font-bold tabular-nums",
                          palette.text,
                        )}
                      >
                        {(a.probability * 100).toFixed(0)}%
                      </p>
                    </div>
                  )}

                  <ChevronRight className="h-5 w-5 shrink-0 text-slate-400 transition-transform duration-200 group-hover:translate-x-1 group-hover:text-blue-500" />
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

type StatAccent = "blue" | "violet" | "red" | "emerald";
const STAT_ACCENTS: Record<StatAccent, { bar: string; iconBg: string; iconColor: string }> = {
  blue: {
    bar: "bg-gradient-to-r from-blue-400 to-blue-600",
    iconBg: "bg-blue-100 dark:bg-blue-900/40",
    iconColor: "text-blue-600 dark:text-blue-400",
  },
  violet: {
    bar: "bg-gradient-to-r from-violet-400 to-violet-600",
    iconBg: "bg-violet-100 dark:bg-violet-900/40",
    iconColor: "text-violet-600 dark:text-violet-400",
  },
  red: {
    bar: "bg-gradient-to-r from-red-400 to-red-600",
    iconBg: "bg-red-100 dark:bg-red-900/40",
    iconColor: "text-red-600 dark:text-red-400",
  },
  emerald: {
    bar: "bg-gradient-to-r from-emerald-400 to-emerald-600",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/40",
    iconColor: "text-emerald-600 dark:text-emerald-400",
  },
};

function OverviewStat({
  accent,
  icon: Icon,
  label,
  value,
  sub,
  delay,
}: {
  accent: StatAccent;
  icon: typeof User;
  label: string;
  value: string;
  sub?: string;
  delay: number;
}) {
  const a = STAT_ACCENTS[accent];
  return (
    <div
      className="animate-cn-fade-up-lg group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg dark:border-slate-700 dark:bg-slate-800"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className={clsx("absolute inset-x-0 top-0 h-1", a.bar)} />
      <div className="flex items-start justify-between">
        <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {label}
        </p>
        <div
          className={clsx(
            "inline-flex h-9 w-9 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110",
            a.iconBg,
          )}
        >
          <Icon className={clsx("h-4 w-4", a.iconColor)} />
        </div>
      </div>
      <p className="mt-3 text-2xl font-bold text-slate-900 dark:text-slate-100">
        {value}
      </p>
      {sub && (
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          {sub}
        </p>
      )}
    </div>
  );
}
