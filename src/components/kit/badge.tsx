import type { ReactNode } from "react";
import "./kit.css";

/**
 * A badge from the starter kit: a short status or label ("Available", "On loan", "Overdue") on a soft ground with
 * ink text, so every tone reads at full contrast in light and dark. The tone says what kind of state it is.
 */
export function Badge({ tone = "neutral", children }: { tone?: "neutral" | "accent" | "success" | "warning" | "danger"; children: ReactNode }) {
  return <span className={`kit-badge kit-badge-${tone}`}>{children}</span>;
}
