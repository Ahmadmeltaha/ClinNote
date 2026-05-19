"use client";

import { useEffect } from "react";
import ErrorState from "@/components/ui/ErrorState";

export default function ModelPerformanceError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[model-performance] error:", error);
  }, [error]);

  return (
    <div className="py-12">
      <ErrorState
        title="Couldn't load model metrics"
        message={
          error.message ||
          "We couldn't fetch the evaluation metrics. The AI server may be unreachable, or its summaries directory may be empty."
        }
        onRetry={reset}
      />
    </div>
  );
}
