import { type ReactNode, useId } from "react";
import "./kit.css";

/**
 * A card from the starter kit: a panel on the surface colour with a light elevation, an optional heading at the type
 * scale's section size (it names the card for screen readers) and optional actions under its content. Use it to
 * group what belongs together: a form, a summary, one record.
 */
export function Card({ title, children, actions }: { title?: ReactNode; children: ReactNode; actions?: ReactNode }) {
  const headingId = useId();
  return (
    <section className="kit-card" aria-labelledby={title ? headingId : undefined}>
      {title ? (
        <h2 id={headingId} className="kit-card-title">
          {title}
        </h2>
      ) : null}
      <div className="kit-card-body">{children}</div>
      {actions ? <div className="kit-card-actions">{actions}</div> : null}
    </section>
  );
}
