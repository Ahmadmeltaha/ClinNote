"use client";

import { AlertTriangle, RotateCcw } from "lucide-react";
import { clsx } from "clsx";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export default function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={clsx(
        "mx-auto flex max-w-lg flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50 p-8 text-center dark:border-red-900 dark:bg-red-950/30",
        className,
      )}
      role="alert"
    >
      <div className="mb-4 rounded-full bg-red-100 p-3 dark:bg-red-900/40">
        <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
      </div>
      <h3 className="text-base font-semibold text-red-900 dark:text-red-200">
        {title}
      </h3>
      <p className="mt-1 max-w-sm text-sm text-red-700 dark:text-red-300">
        {message}
      </p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-5 inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500/30 focus:ring-offset-2 dark:bg-red-500 dark:hover:bg-red-600 dark:focus:ring-offset-slate-900"
        >
          <RotateCcw className="h-4 w-4" />
          Try again
        </button>
      )}
    </div>
  );
}
