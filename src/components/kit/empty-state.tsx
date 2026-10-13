import type { ReactNode } from "react";
import "./kit.css";

/**
 * What a list or table shows when it has no records, from the starter kit: a short title, one line saying what will
 * appear here, and an optional action (a Button to add the first one). Show it in place of the empty list.
 */
export function EmptyState({ title, children, action }: { title: ReactNode; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="kit-empty">
      <p className="kit-empty-title">{title}</p>
      {children ? <p className="kit-empty-text">{children}</p> : null}
      {action ? <div className="kit-empty-action">{action}</div> : null}
    </div>
  );
}
