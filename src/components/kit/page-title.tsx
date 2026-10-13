import type { ReactNode } from "react";
import "./kit.css";

/**
 * The page's name from the starter kit: its one h1, at the type scale's title size, with an optional line under it
 * and optional actions beside it (they wrap under it on a phone). Use it once, at the top of each page.
 */
export function PageTitle({ children, description, actions }: { children: ReactNode; description?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="kit-page-title">
      <div className="kit-page-title-text">
        <h1 className="kit-page-title-heading">{children}</h1>
        {description ? <p className="kit-page-title-description">{description}</p> : null}
      </div>
      {actions ? <div className="kit-page-title-actions">{actions}</div> : null}
    </div>
  );
}
