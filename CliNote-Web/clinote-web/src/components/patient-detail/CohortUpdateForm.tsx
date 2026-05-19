"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  Plus,
  Trash2,
  Brain,
  Loader2,
  AlertCircle,
  FileText,
  X,
  Sparkles,
} from "lucide-react";
import { clsx } from "clsx";
import type { AhmadVitalName } from "@/types";

interface CohortUpdateFormProps {
  /** Latest hadm_id for this subject — the one we POST `/update` against. */
  hadmId: number;
  /** Optional close handler. If omitted, no close button is shown (used inline). */
  onClose?: () => void;
}

interface VitalRow {
  name: AhmadVitalName;
  value: string;
}

const VITAL_NAMES: AhmadVitalName[] = [
  "Heart Rate",
  "Systolic Blood Pressure",
  "Diastolic Blood Pressure",
  "Mean Blood Pressure",
  "SpO2",
  "Respiratory Rate",
  "Temperature Fahrenheit",
  "Temperature Celsius",
];

export function CohortUpdateForm({ hadmId, onClose }: CohortUpdateFormProps) {
  const router = useRouter();
  const [noteText, setNoteText] = useState("");
  const [vitals, setVitals] = useState<VitalRow[]>([]);
  const [labsPdf, setLabsPdf] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addVitalRow() {
    setVitals((prev) => [...prev, { name: "Heart Rate", value: "" }]);
  }
  function removeVitalRow(i: number) {
    setVitals((prev) => prev.filter((_, idx) => idx !== i));
  }
  function setVitalRow(i: number, patch: Partial<VitalRow>) {
    setVitals((prev) =>
      prev.map((row, idx) => (idx === i ? { ...row, ...patch } : row)),
    );
  }

  async function submit() {
    setError(null);
    const cleanVitals = vitals
      .map((v) => ({ name: v.name, value: Number.parseFloat(v.value) }))
      .filter((v) => Number.isFinite(v.value));

    const hasAny =
      noteText.trim().length > 0 || cleanVitals.length > 0 || labsPdf != null;
    if (!hasAny) {
      setError("Add at least a note, vitals, or a lab PDF before submitting.");
      return;
    }

    setSubmitting(true);
    try {
      const fd = new FormData();
      if (noteText.trim()) fd.append("note_text", noteText);
      if (cleanVitals.length > 0)
        fd.append("vitals", JSON.stringify(cleanVitals));
      if (labsPdf) fd.append("labs_pdf", labsPdf);

      const res = await fetch(`/api/patients/${hadmId}/submit`, {
        method: "POST",
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.error ?? `Update failed (${res.status})`);
        return;
      }
      // Ahmad mints a new hadm_id after each /update — navigate to the new admission's dashboard.
      const newHadmId = data.newHadmId ?? hadmId;
      router.push(`/patients/${newHadmId}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-amber-200 bg-white p-6 shadow-lg dark:border-amber-800/40 dark:bg-slate-800">
      {/* Top accent bar */}
      <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600" />

      {/* Decorative blob */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-gradient-to-br from-amber-200/40 to-amber-400/20 blur-3xl dark:from-amber-700/20 dark:to-amber-900/10"
      />

      <div className="relative flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg shadow-amber-500/40 ring-4 ring-amber-500/20">
            <Sparkles className="h-5 w-5 text-white" strokeWidth={2.5} />
          </div>
          <div>
            <h3 className="text-lg font-extrabold text-slate-900 dark:text-slate-50">
              Add new clinical data
            </h3>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Provide a note, vitals, or a lab PDF — the AI runs a fresh analysis
              and adds a new admission to this patient.
            </p>
          </div>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-slate-500 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700"
            aria-label="Close update form"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Clinical note */}
      <div className="relative mt-5">
        <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
          Clinical note
        </label>
        <textarea
          value={noteText}
          onChange={(e) => setNoteText(e.target.value)}
          rows={5}
          placeholder="e.g. Patient developed worsening hypoxia overnight. SpO2 dropped to 88%. Started on supplemental oxygen 4L NC…"
          className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 transition-shadow focus:border-amber-500 focus:outline-none focus:ring-4 focus:ring-amber-500/15 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:placeholder-slate-500"
        />
      </div>

      {/* Vitals */}
      <div className="relative mt-5">
        <div className="mb-2 flex items-center justify-between">
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
            Vital signs <span className="font-normal text-slate-500">(add one per reading)</span>
          </label>
          <button
            type="button"
            onClick={addVitalRow}
            className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 transition-colors hover:border-amber-300 hover:bg-amber-50 hover:text-amber-700 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:border-amber-700 dark:hover:bg-amber-950/30 dark:hover:text-amber-300"
          >
            <Plus className="h-3 w-3" />
            Add vital
          </button>
        </div>
        {vitals.length === 0 ? (
          <p className="rounded-md border border-dashed border-slate-300 px-3 py-2 text-xs text-slate-400 dark:border-slate-600 dark:text-slate-500">
            No vitals added. Click <em>Add vital</em> to enter values.
          </p>
        ) : (
          <ul className="space-y-2">
            {vitals.map((v, i) => (
              <li key={i} className="flex items-center gap-2">
                <select
                  value={v.name}
                  onChange={(e) =>
                    setVitalRow(i, { name: e.target.value as AhmadVitalName })
                  }
                  className="flex-1 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 focus:border-amber-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                >
                  {VITAL_NAMES.map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  step="any"
                  value={v.value}
                  onChange={(e) => setVitalRow(i, { value: e.target.value })}
                  placeholder="Value"
                  className="w-32 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 placeholder-slate-400 focus:border-amber-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
                />
                <button
                  type="button"
                  onClick={() => removeVitalRow(i)}
                  className="rounded-md p-1.5 text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
                  aria-label="Remove vital"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* PDF */}
      <div className="relative mt-5">
        <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
          Lab report <span className="font-normal text-slate-500">(PDF, optional)</span>
        </label>
        {labsPdf ? (
          <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm dark:border-amber-800 dark:bg-amber-950/20">
            <FileText className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <span className="min-w-0 flex-1 truncate text-amber-900 dark:text-amber-200">
              {labsPdf.name}
            </span>
            <span className="shrink-0 text-xs text-amber-700/70 dark:text-amber-300/70">
              {(labsPdf.size / 1024).toFixed(0)} KB
            </span>
            <button
              type="button"
              onClick={() => setLabsPdf(null)}
              className="text-amber-700 hover:text-amber-900 dark:text-amber-300 dark:hover:text-amber-100"
              aria-label="Remove PDF"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <label className="flex cursor-pointer items-center justify-center gap-1.5 rounded-md border border-dashed border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:border-amber-400 hover:bg-amber-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-amber-500 dark:hover:bg-amber-950/20">
            <FileText className="h-3.5 w-3.5" />
            Choose PDF
            <input
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => setLabsPdf(e.target.files?.[0] ?? null)}
            />
          </label>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="relative mt-4 flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Submit */}
      <div className="relative mt-6 flex items-center justify-end gap-2">
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            Cancel
          </button>
        )}
        <button
          type="button"
          onClick={submit}
          disabled={submitting}
          className={clsx(
            "group inline-flex items-center gap-2 rounded-xl px-6 py-2.5 text-sm font-bold text-white transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-amber-500/30",
            submitting
              ? "cursor-not-allowed bg-amber-400 dark:bg-amber-500"
              : "bg-gradient-to-br from-amber-500 to-amber-600 shadow-lg shadow-amber-500/40 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-amber-500/50 dark:from-amber-500 dark:to-amber-700",
          )}
        >
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing…
            </>
          ) : (
            <>
              <Brain className="h-4 w-4 transition-transform duration-300 group-hover:rotate-3 group-hover:scale-110" />
              Run AI Analysis
            </>
          )}
        </button>
      </div>
    </div>
  );
}
