import { type InputHTMLAttributes, useId } from "react";
import "./kit.css";

/**
 * A form field from the starter kit: its label, the input, an optional help line and an error line. The help and
 * the error are tied to the input for screen readers, and the input is marked invalid while there is an error.
 */
export function Field({
  label,
  help,
  error,
  id,
  ...input
}: InputHTMLAttributes<HTMLInputElement> & { label: string; help?: string; error?: string | null }) {
  const auto = useId();
  const fieldId = id ?? auto;
  const helpId = help ? `${fieldId}-help` : undefined;
  const errorId = error ? `${fieldId}-error` : undefined;
  const describedBy = [helpId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className="kit-field">
      <label htmlFor={fieldId} className="kit-field-label">
        {label}
      </label>
      <input id={fieldId} aria-describedby={describedBy} aria-invalid={error ? true : undefined} {...input} />
      {help ? (
        <p id={helpId} className="kit-field-help">
          {help}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} className="kit-field-error">
          {error}
        </p>
      ) : null}
    </div>
  );
}
