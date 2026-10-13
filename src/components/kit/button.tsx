import type { ButtonHTMLAttributes, ReactNode } from "react";
import "./kit.css";

export type ButtonKind = "primary" | "secondary" | "danger";

/**
 * A button from the starter kit. Primary for the main action, secondary for the others, danger for one that
 * deletes or rejects. Each carries its own readable text colour; long words wrap; it is never wider than its row.
 */
export function Button({ kind = "primary", className = "", type = "button", ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { kind?: ButtonKind }) {
  return <button type={type} className={`kit-button kit-button-${kind} ${className}`.trim()} {...rest} />;
}

/** A row of buttons that wraps onto a second line instead of running past the screen's edge. */
export function ButtonRow({ children }: { children: ReactNode }) {
  return <div className="kit-button-row">{children}</div>;
}
