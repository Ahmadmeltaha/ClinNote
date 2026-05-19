"use client";

import { useEffect } from "react";
import ErrorState from "@/components/ui/ErrorState";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[dashboard page] error:", error);
  }, [error]);

  return (
    <div className="py-12">
      <ErrorState
        title="Some data couldn't be loaded"
        message={
          error.message ||
          "We couldn't fetch your dashboard stats right now. The AI cohort overview or recent alerts may be temporarily unavailable."
        }
        onRetry={reset}
      />
    </div>
  );
}
