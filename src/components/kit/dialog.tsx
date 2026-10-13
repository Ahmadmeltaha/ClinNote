"use client";
import { type ReactNode, useEffect, useId, useRef } from "react";
import "./kit.css";

const FIELDS = "input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])";
const FOCUSABLE = 'button:not([disabled]), [href], input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * A dialog from the starter kit: labelled and modal. When it opens, focus goes to its first field (its first
 * button when it has no field); Escape, Cancel or a press on the backdrop closes it; Tab stays inside it; and when
 * it closes, focus goes back to whatever opened it. The backdrop is a see-through colour; the dialog is never faded.
 */
export function Dialog({
  open,
  title,
  onClose,
  children,
  actions,
  cancelLabel = "Cancel",
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children?: ReactNode;
  /** The dialog's other buttons (use Button from ./button), shown after Cancel at its foot. */
  actions?: ReactNode;
  /** The words on the Cancel button; null for a dialog with no Cancel (Escape still closes it). */
  cancelLabel?: string | null;
}) {
  const titleId = useId();
  const panel = useRef<HTMLDivElement>(null);
  // The latest onClose, so a parent that re-renders (typing in a field) never re-runs the focus below.
  const close = useRef(onClose);
  close.current = onClose;

  useEffect(() => {
    if (!open) return;
    const opener = document.activeElement as HTMLElement | null;
    const first = panel.current?.querySelector<HTMLElement>(FIELDS) ?? panel.current?.querySelector<HTMLElement>(FOCUSABLE) ?? panel.current;
    first?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        close.current();
        return;
      }
      if (e.key !== "Tab" || !panel.current) return;
      const items = panel.current.querySelectorAll<HTMLElement>(FOCUSABLE);
      if (items.length === 0) return;
      const head = items[0];
      const tail = items[items.length - 1];
      if (e.shiftKey && document.activeElement === head) {
        e.preventDefault();
        tail.focus();
      } else if (!e.shiftKey && document.activeElement === tail) {
        e.preventDefault();
        head.focus();
      }
    };
    // A press outside the panel closes it, read on the document so no handler sits on the static backdrop.
    const onPress = (e: MouseEvent) => {
      if (panel.current && e.target instanceof Node && !panel.current.contains(e.target)) close.current();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onPress);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onPress);
      opener?.focus();
    };
  }, [open]);

  if (!open) return null;
  return (
    <div className="kit-dialog-backdrop">
      <div ref={panel} className="kit-dialog" role="dialog" aria-modal="true" aria-labelledby={titleId} tabIndex={-1}>
        <h2 id={titleId} className="kit-dialog-title">
          {title}
        </h2>
        <div>{children}</div>
        {cancelLabel || actions ? (
          <div className="kit-dialog-actions">
            {cancelLabel ? (
              <button type="button" className="kit-button kit-button-secondary" onClick={onClose}>
                {cancelLabel}
              </button>
            ) : null}
            {actions}
          </div>
        ) : null}
      </div>
    </div>
  );
}
