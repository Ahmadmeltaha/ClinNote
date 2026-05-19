"use client";

import { useEffect } from "react";
import ErrorState from "@/components/ui/ErrorState";

export default function AlertsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[alerts] error:", error);
  }, [error]);

  return (
    <div className="py-12">
      <ErrorState
        title="Couldn't load alerts"
        message={
          error.message ||
          "We couldn't fetch the alerts list right now. Please try again."
        }
        onRetry={reset}
      />
    </div>
  );
}
