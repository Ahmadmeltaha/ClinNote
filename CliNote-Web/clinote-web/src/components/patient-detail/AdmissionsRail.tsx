"use client";

import Link from "next/link";
import { Calendar, ChevronRight } from "lucide-react";
import { clsx } from "clsx";
import type { AdmissionRailItem } from "@/lib/server/cohort";

interface AdmissionsRailProps {
  currentHadmId: number;
  admissions: AdmissionRailItem[];
}

const RISK_DOT: Record<string, string> = {
  HIGH: "bg-red-500",
  MEDIUM: "bg-amber-500",
  LOW: "bg-emerald-500",
};

const RISK_TEXT: Record<string, string> = {
  HIGH: "text-red-700 dark:text-red-300",
  MEDIUM: "text-amber-700 dark:text-amber-300",
  LOW: "text-emerald-700 dark:text-emerald-300",
};

function formatShort(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function AdmissionsRail({
  currentHadmId,
  admissions,
}: AdmissionsRailProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
          Admissions
        </p>
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          {admissions.length} total · sorted newest first
        </p>
      </div>

      <ul className="max-h-[calc(100vh-220px)] overflow-y-auto">
        {admissions.map((a, i) => {
          const isCurrent = a.hadmId === currentHadmId;
          const riskKey = a.riskLevel ?? "LOW";
          return (
            <li
              key={a.hadmId}
              className="border-b border-slate-100 last:border-b-0 dark:border-slate-700/60"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              <Link
                href={`/patients/${a.hadmId}`}
                className={clsx(
                  "group relative flex items-center gap-3 px-4 py-3 transition-all duration-200",
                  isCurrent
                    ? "bg-blue-50 dark:bg-blue-950/30"
                    : "hover:bg-slate-50 dark:hover:bg-slate-900/30",
                )}
              >
                {/* Left accent bar for current */}
                {isCurrent && (
                  <span
                    className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-blue-400 to-blue-600"
                    aria-hidden="true"
                  />
                )}

                <span
                  className={clsx(
                    "h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-white dark:ring-slate-800",
                    RISK_DOT[riskKey],
                  )}
                  aria-label={riskKey}
                />

                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p
                      className={clsx(
                        "truncate font-mono text-sm font-semibold",
                        isCurrent
                          ? "text-blue-900 dark:text-blue-200"
                          : "text-slate-900 dark:text-slate-100",
                      )}
                    >
                      #{a.hadmId}
                    </p>
                    {a.probability != null && (
                      <span
                        className={clsx(
                          "shrink-0 text-xs font-semibold tabular-nums",
                          RISK_TEXT[riskKey],
                        )}
                      >
                        {(a.probability * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 flex items-center gap-1 text-[11px] text-slate-500 dark:text-slate-400">
                    <Calendar className="h-3 w-3" />
                    {formatShort(a.admissionDate)}
                    {a.riskLevel && (
                      <>
                        <span className="opacity-50">·</span>
                        <span className={RISK_TEXT[riskKey]}>
                          {a.riskLevel}
                        </span>
                      </>
                    )}
                  </p>
                </div>

                <ChevronRight
                  className={clsx(
                    "h-4 w-4 shrink-0 transition-transform duration-200",
                    isCurrent
                      ? "text-blue-500"
                      : "text-slate-400 group-hover:translate-x-0.5",
                  )}
                />
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
