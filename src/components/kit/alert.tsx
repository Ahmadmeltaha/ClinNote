import type { ReactNode } from "react";
import "./kit.css";

export type AlertKind = "info" | "success" | "warning" | "danger";

/**
 * A message box from the starter kit: info, success, warning or danger. The text is always the theme's ink on a
 * soft ground, so it reads in light and dark; the kind's own colour is only the border. A warning or danger is
 * announced at once, the others politely.
 */
export function Alert({ kind = "info", title, children }: { kind?: AlertKind; title: string; children?: ReactNode }) {
  const urgent = kind === "warning" || kind === "danger";
  return (
    <div className={`kit-alert kit-alert-${kind}`} role={urgent ? "alert" : "status"}>
      <p className="kit-alert-title">{title}</p>
      {children ? <div>{children}</div> : null}
    </div>
  );
}
