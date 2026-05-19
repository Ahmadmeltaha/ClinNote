"use client";

import Link from "next/link";
import { useState } from "react";
import {
  ArrowLeft,
  Brain,
  Calendar,
  Clock,
  AlertTriangle,
  FileText,
  Activity,
  Beaker,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { clsx } from "clsx";
import { MortalityGauge } from "@/components/patient-detail/MortalityGauge";
import { Reveal } from "@/components/ui/Reveal";
import type { PatientResult } from "@/types";

interface CohortPatientDashboardProps {
  hadmId: number;
  result: PatientResult;
  displayName?: string;
  mrn?: string;
}

const RISK_PALETTE: Record<string, string> = {
  HIGH: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  MEDIUM:
    "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  LOW: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
};

const ALERT_PALETTE: Record<string, string> = {
  critical:
    "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200",
  warning:
    "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200",
};

export function CohortPatientDashboard({
  hadmId,
  result,
  displayName,
  mrn,
}: CohortPatientDashboardProps) {
  const heading = displayName ?? `Patient ${result.subject_id}`;
  const subId = `Subject ${result.subject_id}`;

  const losDays =
    result.admission_info.los_days != null &&
    Number.isFinite(result.admission_info.los_days)
      ? result.admission_info.los_days.toFixed(1)
      : "—";

  return (
    <div className="space-y-6">
      <Link
        href="/patients"
        className="inline-flex items-center gap-1.5 text-sm text-slate-600 transition-colors hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to patients
      </Link>

      {/* Header card */}
      <div className="animate-cn-fade-up rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {heading}
            </h1>
            <p className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-xs text-slate-500 dark:text-slate-400">
              {mrn && <span>{mrn}</span>}
              <span>{subId}</span>
              <span>Admission {hadmId}</span>
            </p>
          </div>
          <span
            className={clsx(
              "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider",
              RISK_PALETTE[result.mortality_risk.risk_level] ??
                RISK_PALETTE.LOW,
            )}
          >
            {result.mortality_risk.risk_level} ·{" "}
            {(result.mortality_risk.probability * 100).toFixed(1)}%
          </span>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-4">
          <Stat
            label="Age"
            value={result.demographics.age ?? "—"}
          />
          <Stat
            label="Gender"
            value={result.demographics.gender ?? "—"}
          />
          <Stat
            icon={<Calendar className="h-3.5 w-3.5" />}
            label="Admitted"
            value={formatDate(result.admission_info.admittime)}
          />
          <Stat
            icon={<Clock className="h-3.5 w-3.5" />}
            label="Length of stay"
            value={`${losDays} days`}
          />
        </div>
      </div>

      {/* AI Panel */}
      <div
        className="animate-cn-fade-up rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800"
        style={{ animationDelay: "80ms" }}
      >
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            <Brain className="h-4 w-4" />
            AI Analysis
          </h3>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Generated {formatDate(result.generated_at)}
          </p>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-[260px_1fr]">
          <div className="flex justify-center lg:justify-start">
            <MortalityGauge
              probability={result.mortality_risk.probability}
              riskLevel={result.mortality_risk.risk_level}
            />
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Clinical Summary
            </h4>
            <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
              {result.note_summary}
            </p>
            {result.note_excerpt && (
              <details className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                <summary className="cursor-pointer font-medium">
                  Note excerpt
                </summary>
                <p className="mt-1 max-h-32 overflow-auto rounded-md border border-slate-200 bg-slate-50 p-2 dark:border-slate-700 dark:bg-slate-900/40">
                  {result.note_excerpt}
                </p>
              </details>
            )}
          </div>
        </div>
      </div>

      {/* Alerts */}
      {result.alerts.length > 0 && (
        <Reveal>
          <section>
            <SectionLabel
              icon={<AlertTriangle className="h-3.5 w-3.5" />}
              title={`Critical Alerts (${result.alerts.length})`}
            />
            <ul className="space-y-2">
              {result.alerts.map((a, i) => (
                <li
                  key={`${a.type}-${i}`}
                  className={clsx(
                    "animate-cn-fade-up flex items-start gap-3 rounded-lg border px-4 py-3 transition-transform duration-200 hover:-translate-y-0.5",
                    ALERT_PALETTE[a.severity] ?? ALERT_PALETTE.warning,
                  )}
                  style={{ animationDelay: `${i * 30}ms` }}
                >
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs font-semibold uppercase tracking-wider">
                      {a.severity} · {a.type.replace(/_/g, " ")}
                    </p>
                    <p className="mt-0.5 text-sm">{a.message}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </Reveal>
      )}

      {/* Lab abnormalities */}
      {result.lab_anomalies.length > 0 && (
        <Reveal delay={60}>
        <section>
          <SectionLabel
            icon={<Beaker className="h-3.5 w-3.5" />}
            title={`Lab Abnormalities (${result.lab_anomalies.length})`}
          />
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-600 dark:bg-slate-900/40 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-2 text-left">Test</th>
                  <th className="px-4 py-2 text-right">Value</th>
                  <th className="px-4 py-2 text-left">Unit</th>
                  <th className="px-4 py-2 text-left">Range</th>
                  <th className="px-4 py-2 text-left">Flag</th>
                  <th className="px-4 py-2 text-left">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60">
                {result.lab_anomalies.map((l, i) => (
                  <tr key={i}>
                    <td className="px-4 py-2 font-medium text-slate-900 dark:text-slate-100">
                      {l.label}
                    </td>
                    <td className="px-4 py-2 text-right font-mono text-slate-700 dark:text-slate-300">
                      {l.value}
                    </td>
                    <td className="px-4 py-2 text-slate-500 dark:text-slate-400">
                      {l.unit}
                    </td>
                    <td className="px-4 py-2 text-slate-500 dark:text-slate-400">
                      {l.ref_range}
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={clsx(
                          "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold",
                          l.flag === "HIGH"
                            ? "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
                            : "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
                        )}
                      >
                        {l.flag === "HIGH" ? "↑" : "↓"} {l.flag}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={clsx(
                          "rounded-full px-2 py-0.5 text-xs font-semibold uppercase",
                          l.severity === "critical"
                            ? "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
                            : "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
                        )}
                      >
                        {l.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        </Reveal>
      )}

      {/* Vital alerts */}
      {result.vital_anomalies.length > 0 && (
        <Reveal delay={120}>
        <section>
          <SectionLabel
            icon={<Activity className="h-3.5 w-3.5" />}
            title={`Vital Sign Alerts (${result.vital_anomalies.length})`}
          />
          <div className="grid gap-3 sm:grid-cols-2">
            {result.vital_anomalies.map((v, i) => {
              const trend =
                result.vital_trends?.[v.label.toLowerCase().replace(/ /g, "_")];
              return (
                <div
                  key={i}
                  className={clsx(
                    "animate-cn-fade-up rounded-lg border px-4 py-3 transition-transform duration-200 hover:-translate-y-0.5",
                    ALERT_PALETTE[v.severity] ?? ALERT_PALETTE.warning,
                  )}
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold">{v.label}</p>
                    {trend && <TrendIcon trend={trend.trend} />}
                  </div>
                  <p className="mt-1 text-xs">
                    <span className="font-mono text-base font-semibold">
                      {v.value}
                    </span>{" "}
                    {v.unit} ·{" "}
                    <span className="font-semibold">
                      {v.flag === "HIGH" ? "↑ HIGH" : "↓ LOW"}
                    </span>
                  </p>
                </div>
              );
            })}
          </div>
        </section>
        </Reveal>
      )}

      {/* View report — full-width primary action */}
      <Reveal delay={180}>
        <Link
          href={`/patients/${hadmId}/report`}
          className="group relative flex items-center justify-between overflow-hidden rounded-2xl border border-blue-300 bg-gradient-to-br from-blue-600 to-blue-700 px-6 py-5 shadow-lg shadow-blue-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-blue-500/40 dark:border-blue-700 dark:from-blue-500 dark:to-blue-700"
        >
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-12 -top-12 h-40 w-40 rounded-full bg-white/10 blur-2xl transition-transform duration-500 group-hover:scale-125"
          />
          <div className="relative flex items-center gap-3">
            <div className="rounded-xl bg-white/20 p-2.5 backdrop-blur-sm transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3">
              <FileText className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-base font-bold text-white">
                View clinical report
              </p>
              <p className="text-xs text-blue-100/90">
                AI-generated draft, ready for review and approval
              </p>
            </div>
          </div>
          <div className="relative flex items-center gap-1 text-sm font-semibold text-white">
            Open
            <span className="inline-block transition-transform duration-300 group-hover:translate-x-1">
              →
            </span>
          </div>
        </Link>
      </Reveal>
    </div>
  );
}

function Stat({
  icon,
  label,
  value,
}: {
  icon?: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div>
      <p className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
        {icon}
        {label}
      </p>
      <p className="mt-1 text-base font-semibold text-slate-900 dark:text-slate-100">
        {value}
      </p>
    </div>
  );
}

function SectionLabel({
  icon,
  title,
}: {
  icon: React.ReactNode;
  title: string;
}) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
      {icon}
      {title}
    </div>
  );
}

function TrendIcon({ trend }: { trend: string }) {
  if (trend === "increasing") {
    return <TrendingUp className="h-4 w-4" aria-label="increasing" />;
  }
  if (trend === "decreasing") {
    return <TrendingDown className="h-4 w-4" aria-label="decreasing" />;
  }
  return <Minus className="h-4 w-4" aria-label="stable" />;
}

function formatDate(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
