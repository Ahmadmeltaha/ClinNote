import type { ReactNode } from "react";
import "./kit.css";

/**
 * A simple list from the starter kit, for records that need no columns: each item on its own row with a hover state,
 * its main text first and optional actions beside it (they wrap under it on a phone). Name the list with `label`
 * when no heading right above it does.
 */
export function List({ label, children }: { label?: string; children: ReactNode }) {
  return (
    <ul className="kit-list" aria-label={label}>
      {children}
    </ul>
  );
}

export function ListItem({ children, actions }: { children: ReactNode; actions?: ReactNode }) {
  return (
    <li className="kit-list-item">
      <div className="kit-list-item-main">{children}</div>
      {actions ? <div className="kit-list-item-actions">{actions}</div> : null}
    </li>
  );
}
