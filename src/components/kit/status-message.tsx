import type { ReactNode } from "react";
import "./kit.css";

/**
 * A short message after an action ("Request saved"), from the starter kit. Place it in the page next to what it is
 * about: it takes its own space in the flow and is never laid over other content. Screen readers announce it.
 * Render nothing when there is no message.
 */
export function StatusMessage({ children }: { children?: ReactNode }) {
  if (!children) return null;
  return (
    <p className="kit-status" role="status" aria-live="polite">
      {children}
    </p>
  );
}
