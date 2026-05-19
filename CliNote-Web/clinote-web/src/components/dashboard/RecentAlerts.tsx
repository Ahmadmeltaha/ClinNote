"use client";

import Link from "next/link";
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import { clsx } from "clsx";
import type { Alert } from "@/types";

interface RecentAlertsProps {
  alerts: (Alert & {
    patient: { id: string; firstName: string; lastName: string; mrn: string };
  })[];
}

function timeAgo(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

const PRIORITY = {
  CRITICAL: {
    icon: AlertTriangle,
    color: "text-red-600 dark:text-red-400",
    border: "border-l-red-500",
  },
  WARNING: {
    icon: AlertCircle,
    color: "text-amber-600 dark:text-amber-400",
    border: "border-l-amber-500",
  },
  INFO: {
    icon: Bell,
    color: "text-blue-600 dark:text-blue-400",
    border: "border-l-blue-500",
  },
};

export function RecentAlerts({ alerts }: RecentAlertsProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
        <Bell className="h-4 w-4" />
        Recent Critical Alerts
      </h3>

      {alerts.length === 0 ? (
        <div className="py-8 text-center">
          <div className="mx-auto inline-flex h-10 w-10 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/40">
            <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
          </div>
          <p className="mt-2 text-sm font-medium text-slate-700 dark:text-slate-300">
            No active alerts
          </p>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            All patients are stable.
          </p>
        </div>
      ) : (
        <>
          <ul className="mt-4 space-y-2">
            {alerts.map((a) => {
              const p = PRIORITY[a.priority];
              const Icon = p.icon;
              return (
                <li
                  key={a.id}
                  className={clsx(
                    "rounded-lg border-l-4 border-y border-r border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-900/30",
                    p.border,
                  )}
                >
                  <div className="flex items-start gap-2">
                    <Icon className={clsx("mt-0.5 h-4 w-4 shrink-0", p.color)} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                        {a.title}
                      </p>
                      <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                        <Link
                          href={`/patients/${a.patient.id}`}
                          className="font-medium text-blue-600 hover:underline dark:text-blue-400"
                        >
                          {a.patient.firstName} {a.patient.lastName}
                        </Link>
                        <span className="text-slate-300 dark:text-slate-600">
                          •
                        </span>
                        <span>{timeAgo(a.createdAt)}</span>
                      </div>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>

          <Link
            href="/alerts"
            className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            View all alerts
            <ArrowRight className="h-3 w-3" />
          </Link>
        </>
      )}
    </div>
  );
}
