"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Search, Users, ChevronRight, Activity } from "lucide-react";
import { clsx } from "clsx";
import type { CohortPatientWithName } from "@/lib/server/cohort";

type Action = "view" | "update";

interface CohortPatientListProps {
  patients: CohortPatientWithName[];
  action?: Action;
  totalCount: number;
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

function highestRiskOf(
  admissions: CohortPatientWithName["admissions"],
): "LOW" | "MEDIUM" | "HIGH" {
  const rank = { LOW: 0, MEDIUM: 1, HIGH: 2 } as const;
  let best: "LOW" | "MEDIUM" | "HIGH" = "LOW";
  for (const a of admissions) {
    if (rank[a.risk_level] > rank[best]) best = a.risk_level;
  }
  return best;
}

export function CohortPatientList({
  patients,
  action = "view",
  totalCount,
}: CohortPatientListProps) {
  const [query, setQuery] = useState("");

  const trimmed = query.trim().toLowerCase();
  const hasQuery = trimmed.length > 0;

  const filtered = useMemo(() => {
    if (!hasQuery) return [];
    return patients
      .filter((p) => {
        if (String(p.subject_id).includes(trimmed)) return true;
        if (p.displayName.toLowerCase().includes(trimmed)) return true;
        if (p.hadm_ids.some((h) => String(h).includes(trimmed))) return true;
        return false;
      })
      .slice(0, 50);
  }, [patients, trimmed, hasQuery]);

  return (
    <div className="space-y-4">
      {/* Big search input */}
      <div className="relative">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a subject ID or admission ID to search…"
          className="w-full rounded-xl border border-slate-300 bg-white py-3.5 pl-12 pr-4 text-base text-slate-900 placeholder-slate-400 shadow-sm transition-shadow focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
        />
      </div>

      {!hasQuery ? (
        // Empty state — invite the doctor to search
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 py-16 text-center dark:border-slate-700 dark:bg-slate-900/30">
          <div className="rounded-2xl bg-blue-100 p-3 dark:bg-blue-900/40">
            <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            {totalCount.toLocaleString()} patients available
          </h3>
          <p className="max-w-sm text-sm text-slate-500 dark:text-slate-400">
            Start typing in the search box above to find a patient by subject
            ID or admission ID.
          </p>
        </div>
      ) : filtered.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-300 px-5 py-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
          No patients match <span className="font-mono">“{query}”</span>.
        </p>
      ) : (
        <>
          <p className="text-xs text-slate-500 dark:text-slate-500">
            {filtered.length === 50
              ? `Showing the first 50 matches — refine your search to narrow down.`
              : `Showing ${filtered.length} of ${totalCount.toLocaleString()} patients.`}
          </p>
          <ul className="space-y-3">
            {filtered.map((p, i) => {
              const highest = highestRiskOf(p.admissions);
              return (
                <li
                  key={p.subject_id}
                  className="animate-cn-fade-up"
                  style={{ animationDelay: `${Math.min(i * 25, 600)}ms` }}
                >
                  <Link
                    href={
                      action === "update"
                        ? `/patients/by-subject/${p.subject_id}?action=update`
                        : `/patients/by-subject/${p.subject_id}`
                    }
                    className="group relative flex items-center gap-4 overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg dark:border-slate-700 dark:bg-slate-800"
                  >
                    <div
                      className={clsx(
                        "absolute inset-y-0 left-0 w-1.5 transition-all duration-300 group-hover:w-2",
                        RISK_DOT[highest],
                      )}
                      aria-hidden="true"
                    />
                    <div
                      className={clsx(
                        "inline-flex h-11 w-11 items-center justify-center rounded-full text-sm font-bold",
                        p.gender === "M"
                          ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                          : "bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300",
                      )}
                    >
                      {p.gender}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-base font-bold text-slate-900 dark:text-slate-100">
                        {p.displayName}
                      </p>
                      <p className="mt-0.5 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-slate-500 dark:text-slate-400">
                        <span className="font-mono">ID {p.subject_id}</span>
                        <span>·</span>
                        <span>{p.age} yrs</span>
                        <span>·</span>
                        <span className="inline-flex items-center gap-1">
                          <Activity className="h-3 w-3" />
                          {p.admissions.length} admission{p.admissions.length === 1 ? "" : "s"}
                        </span>
                      </p>
                    </div>
                    <div className="hidden text-right sm:block">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Highest risk
                      </p>
                      <p
                        className={clsx(
                          "mt-0.5 text-sm font-bold",
                          RISK_TEXT[highest],
                        )}
                      >
                        {highest}
                      </p>
                    </div>
                    <ChevronRight className="h-5 w-5 shrink-0 text-slate-400 transition-transform duration-200 group-hover:translate-x-1 group-hover:text-blue-500" />
                  </Link>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
}

