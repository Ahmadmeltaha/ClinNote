"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Bell, AlertTriangle, AlertCircle, Info } from "lucide-react";
import { clsx } from "clsx";
import { AlertCard } from "@/components/alerts/AlertCard";
import EmptyState from "@/components/ui/EmptyState";
import type { Alert } from "@/types";

interface AlertsListProps {
  alerts: (Alert & {
    patient: { id: string; firstName: string; lastName: string; mrn: string };
  })[];
  /**
   * True counts computed server-side from the whole alerts table, not just
   * the (capped) `alerts` list above. Used for the header summary + chips so
   * the numbers reflect reality, not just what fits in the page payload.
   */
  totalCounts: {
    activeTotal: number;
    resolvedTotal: number;
    critical: number;
    warning: number;
    info: number;
  };
}

type StatusFilter = "active" | "resolved" | "all";
type PriorityFilter = "ALL" | "CRITICAL" | "WARNING" | "INFO";

const PRIORITY_RANK = { CRITICAL: 0, WARNING: 1, INFO: 2 } as const;

export function AlertsList({ alerts, totalCounts }: AlertsListProps) {
  const router = useRouter();
  const [status, setStatus] = useState<StatusFilter>("active");
  const [priority, setPriority] = useState<PriorityFilter>("ALL");
  const [patientFilter, setPatientFilter] = useState<string>("ALL");

  // Build patient dropdown options from the alerts list
  const patientOptions = useMemo(() => {
    const seen = new Map<
      string,
      { id: string; firstName: string; lastName: string; mrn: string }
    >();
    for (const a of alerts) {
      if (a.patient && !seen.has(a.patient.id)) seen.set(a.patient.id, a.patient);
    }
    return Array.from(seen.values()).sort((a, b) =>
      a.lastName.localeCompare(b.lastName),
    );
  }, [alerts]);

  const filtered = useMemo(() => {
    return alerts
      .filter((a) => {
        if (status === "active" && a.isResolved) return false;
        if (status === "resolved" && !a.isResolved) return false;
        if (priority !== "ALL" && a.priority !== priority) return false;
        if (patientFilter !== "ALL" && a.patientId !== patientFilter) return false;
        return true;
      })
      .sort((a, b) => {
        const r = PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority];
        if (r !== 0) return r;
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      });
  }, [alerts, status, priority, patientFilter]);

  // Stats come from the server-side totalCounts (true counts across the WHOLE
  // alerts table, not just the capped `alerts` slice we render below).
  const stats = totalCounts;

  async function resolve(id: string) {
    const res = await fetch(`/api/alerts/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ isResolved: true }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(`Resolve failed: ${data.error ?? res.status}`);
      return;
    }
    router.refresh();
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            All Alerts
          </h2>
          <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
            {stats.activeTotal} active · {stats.resolvedTotal} resolved
          </p>
        </div>
      </div>

      {/* Stats chips */}
      <div className="flex flex-wrap gap-2">
        <StatChip
          icon={AlertTriangle}
          count={stats.critical}
          label="Critical"
          color="red"
        />
        <StatChip
          icon={AlertCircle}
          count={stats.warning}
          label="Warning"
          color="amber"
        />
        <StatChip icon={Info} count={stats.info} label="Info" color="blue" />
      </div>

      {/* Filter row */}
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 pb-3 dark:border-slate-700">
        {/* Status toggle */}
        <div className="inline-flex rounded-lg border border-slate-300 bg-white p-0.5 text-xs font-medium dark:border-slate-600 dark:bg-slate-800">
          {(["active", "resolved", "all"] as StatusFilter[]).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStatus(s)}
              className={clsx(
                "rounded-md px-3 py-1.5 capitalize transition-colors",
                status === s
                  ? "bg-blue-600 text-white"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700",
              )}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Priority dropdown */}
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value as PriorityFilter)}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        >
          <option value="ALL">All priorities</option>
          <option value="CRITICAL">Critical only</option>
          <option value="WARNING">Warning only</option>
          <option value="INFO">Info only</option>
        </select>

        {/* Patient dropdown */}
        {patientOptions.length > 0 && (
          <select
            value={patientFilter}
            onChange={(e) => setPatientFilter(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          >
            <option value="ALL">All patients</option>
            {patientOptions.map((p) => (
              <option key={p.id} value={p.id}>
                {p.firstName} {p.lastName} ({p.mrn})
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={Bell}
          title={
            status === "active"
              ? "No active alerts"
              : alerts.length === 0
                ? "No alerts yet"
                : "No alerts match your filters"
          }
          description={
            status === "active" && alerts.length > 0
              ? "All alerts have been resolved. Nice work."
              : alerts.length === 0
                ? "Alerts will appear here when AI analysis is run on a patient."
                : undefined
          }
        />
      ) : (
        <div className="space-y-2">
          {filtered.map((a) => (
            <AlertCard
              key={a.id}
              alert={a}
              onResolve={a.isResolved ? undefined : resolve}
              showPatientLink
            />
          ))}
        </div>
      )}
    </div>
  );
}

function StatChip({
  icon: Icon,
  count,
  label,
  color,
}: {
  icon: typeof Bell;
  count: number;
  label: string;
  color: "red" | "amber" | "blue";
}) {
  const colors = {
    red: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
    amber:
      "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
    blue: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
  };
  return (
    <div
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold",
        colors[color],
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      <span className="tabular-nums">{count}</span>
      <span>{label}</span>
    </div>
  );
}
