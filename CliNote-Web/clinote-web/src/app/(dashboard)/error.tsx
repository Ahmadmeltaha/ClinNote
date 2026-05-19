"use client";

import { useEffect } from "react";
import ErrorState from "@/components/ui/ErrorState";

export default function DashboardSegmentError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[dashboard] segment error:", error);
  }, [error]);

  return (
    <div className="py-12">
      <ErrorState
        title="This page failed to load"
        message={
          error.message ||
          "An unexpected error occurred. Please try again — if it keeps happening, refresh the page or sign in again."
        }
        onRetry={reset}
      />
    </div>
  );
}
