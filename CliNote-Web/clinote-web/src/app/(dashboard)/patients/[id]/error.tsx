"use client";

import { useEffect } from "react";
import ErrorState from "@/components/ui/ErrorState";

export default function PatientDetailError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[patient detail] error:", error);
  }, [error]);

  return (
    <div className="py-12">
      <ErrorState
        title="Couldn't load this patient"
        message={
          error.message ||
          "Something went wrong while loading this patient's record. The patient may have been deleted, or there may be a temporary issue with the database."
        }
        onRetry={reset}
      />
    </div>
  );
}
