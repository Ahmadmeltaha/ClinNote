"use client";

import Link from "next/link";
import { clsx } from "clsx";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { useState } from "react";
import type { Alert } from "@/types";

interface AlertCardProps {
  alert: Alert & {
    patient?: { id: string; firstName: string; lastName: string; mrn: string };
  };
  /** If provided, shows a Resolve button on unresolved alerts. */
  onResolve?: (id: string) => void | Promise<void>;
  /** Show the patient name (link) above the title. */
  showPatientLink?: boolean;
}

const PRIORITY_STYLES = {
  CRITICAL: {
    border: "border-l-red-500",
    icon: AlertTriangle,
    iconClass: "text-red-600 dark:text-red-400",
    bg: "bg-red-50/50 dark:bg-red-950/20",
  },
  WARNING: {
    border: "border-l-amber-500",
    icon: AlertCircle,
    iconClass: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-50/50 dark:bg-amber-950/20",
  },
  INFO: {
    border: "border-l-blue-500",
    icon: Info,
    iconClass: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-50/50 dark:bg-blue-950/20",
  },
};

function timeAgo(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  return `${day}d ago`;
}

export function AlertCard({ alert, onResolve, showPatientLink }: AlertCardProps) {
  const [busy, setBusy] = useState(false);
  const styles = PRIORITY_STYLES[alert.priority];
  const Icon = styles.icon;

  async function handleResolve() {
    if (!onResolve) return;
    setBusy(true);
    try {
      await onResolve(alert.id);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className={clsx(
        "flex items-start gap-3 rounded-lg border border-slate-200 border-l-4 p-3 transition-colors dark:border-slate-700",
        styles.border,
        styles.bg,
      )}
    >
      <Icon className={clsx("mt-0.5 h-5 w-5 shrink-0", styles.iconClass)} />

      <div className="min-w-0 flex-1">
        {/* Patient link (optional) */}
        {showPatientLink && alert.patient && (
          <div className="mb-1">
            <Link
              href={`/patients/${alert.patient.id}`}
              className="text-xs font-medium text-blue-600 hover:underline dark:text-blue-400"
            >
              {alert.patient.firstName} {alert.patient.lastName} · {alert.patient.mrn}
            </Link>
          </div>
        )}

        <p className="font-semibold text-slate-900 dark:text-slate-100">
          {alert.title}
        </p>
        <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">
          {alert.message}
        </p>

        <div className="mt-2 flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
          <span>{timeAgo(alert.createdAt)}</span>
          {alert.source && (
            <>
              <span className="text-slate-300 dark:text-slate-600">•</span>
              <span>{alert.source}</span>
            </>
          )}
        </div>
      </div>

      {/* Right side: resolve button OR resolved label */}
      <div className="shrink-0">
        {alert.isResolved ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 dark:text-green-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Resolved
            {alert.resolvedAt && (
              <span className="ml-0.5 text-slate-400">
                {timeAgo(alert.resolvedAt)}
              </span>
            )}
          </span>
        ) : (
          onResolve && (
            <button
              type="button"
              onClick={handleResolve}
              disabled={busy}
              className={clsx(
                "inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors",
                busy
                  ? "cursor-not-allowed border-slate-300 bg-slate-100 text-slate-400 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-500"
                  : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700",
              )}
            >
              {busy ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <CheckCircle2 className="h-3 w-3" />
              )}
              Resolve
            </button>
          )
        )}
      </div>
    </div>
  );
}
