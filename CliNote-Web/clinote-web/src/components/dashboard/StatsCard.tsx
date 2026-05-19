"use client";

import type { LucideIcon } from "lucide-react";
import { clsx } from "clsx";

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  accentColor?: "blue" | "amber" | "red" | "green";
}

const ACCENT_STYLES = {
  blue: "bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300",
  amber:
    "bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-300",
  red: "bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-300",
  green:
    "bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-300",
};

export function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accentColor = "blue",
}: StatsCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {title}
          </p>
          <p className="mt-1.5 text-3xl font-bold tabular-nums text-slate-900 dark:text-slate-100">
            {value}
          </p>
          {subtitle && (
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {subtitle}
            </p>
          )}
        </div>
        <div
          className={clsx(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
            ACCENT_STYLES[accentColor],
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}
