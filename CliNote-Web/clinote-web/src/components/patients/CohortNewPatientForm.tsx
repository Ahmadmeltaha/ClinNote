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
} from "lucide-react";
import { clsx } from "clsx";
import type { AhmadVitalName } from "@/types";

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

export function CohortNewPatientForm() {
  const router = useRouter();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState<"M" | "F">("M");
  const [admittime, setAdmittime] = useState("");
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

    if (!firstName.trim() || !lastName.trim()) {
      setError("Enter the patient's first and last name.");
      return;
    }
    const ageNum = Number.parseInt(age, 10);
    if (!Number.isFinite(ageNum) || ageNum <= 0 || ageNum > 130) {
      setError("Enter a valid age (1–130).");
      return;
    }

    const cleanVitals = vitals
      .map((v) => ({ name: v.name, value: Number.parseFloat(v.value) }))
      .filter((v) => Number.isFinite(v.value));

    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("firstName", firstName.trim());
      fd.append("lastName", lastName.trim());
      fd.append("age", String(ageNum));
      fd.append("gender", gender);
      // Send naive UTC (no trailing Z) — Ahmad's pipeline crashes with mixed tz.
      const admittimeOut =
        admittime || new Date().toISOString().slice(0, 19);
      fd.append("admittime", admittimeOut);
      if (noteText.trim()) fd.append("noteText", noteText);
      if (cleanVitals.length > 0)
        fd.append("vitals", JSON.stringify(cleanVitals));
      if (labsPdf) fd.append("labs_pdf", labsPdf);

      const res = await fetch("/api/patients", {
        method: "POST",
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.error ?? `Create failed (${res.status})`);
        return;
      }
      router.push(`/patients/${data.hadmId}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500";
  const labelClass =
    "mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300";

  return (
    <div className="space-y-5">
      {/* Name */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>
            First name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="e.g. John"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>
            Last name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="e.g. Doe"
            className={inputClass}
          />
        </div>
      </div>

      {/* Demographics */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <label className={labelClass}>
            Age <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            min={1}
            max={130}
            value={age}
            onChange={(e) => setAge(e.target.value)}
            placeholder="e.g. 67"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>
            Gender <span className="text-red-500">*</span>
          </label>
          <select
            value={gender}
            onChange={(e) => setGender(e.target.value as "M" | "F")}
            className={inputClass}
          >
            <option value="M">Male</option>
            <option value="F">Female</option>
          </select>
        </div>
        <div>
          <label className={labelClass}>Admission time</label>
          <input
            type="datetime-local"
            value={admittime}
            onChange={(e) => setAdmittime(e.target.value)}
            className={inputClass}
          />
        </div>
      </div>

      {/* Clinical note */}
      <div>
        <label className={labelClass}>
          Clinical note (initial assessment, history, exam findings…)
        </label>
        <textarea
          value={noteText}
          onChange={(e) => setNoteText(e.target.value)}
          rows={6}
          placeholder="e.g. 67-year-old male with history of CKD stage 3 and hypertension presented with fever (T 38.4°C), tachycardia (HR 118), and altered mental status. Blood cultures positive for E. coli, consistent with urosepsis…"
          className={inputClass}
        />
      </div>

      {/* Vitals */}
      <div>
        <div className="mb-2 flex items-center justify-between">
          <label className={labelClass + " mb-0"}>
            Vital signs (add one per reading)
          </label>
          <button
            type="button"
            onClick={addVitalRow}
            className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
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
                  className="flex-1 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
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
                  className="w-32 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
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
      <div>
        <label className={labelClass}>Lab report (PDF, optional)</label>
        {labsPdf ? (
          <div className="flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm dark:border-blue-900 dark:bg-blue-950/30">
            <FileText className="h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400" />
            <span className="min-w-0 flex-1 truncate text-blue-900 dark:text-blue-200">
              {labsPdf.name}
            </span>
            <span className="shrink-0 text-xs text-blue-700/70 dark:text-blue-300/70">
              {(labsPdf.size / 1024).toFixed(0)} KB
            </span>
            <button
              type="button"
              onClick={() => setLabsPdf(null)}
              className="text-blue-700 hover:text-blue-900 dark:text-blue-300 dark:hover:text-blue-100"
              aria-label="Remove PDF"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <label className="flex cursor-pointer items-center justify-center gap-1.5 rounded-md border border-dashed border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:border-blue-400 hover:bg-blue-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-blue-500 dark:hover:bg-blue-950/30">
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
        <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Submit */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={submit}
          disabled={submitting}
          className={clsx(
            "inline-flex items-center gap-2 rounded-lg px-6 py-2.5 text-sm font-semibold text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:ring-offset-2 dark:focus:ring-offset-slate-800",
            submitting
              ? "cursor-not-allowed bg-blue-400 dark:bg-blue-500"
              : "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600",
          )}
        >
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Creating patient and running AI…
            </>
          ) : (
            <>
              <Brain className="h-4 w-4" />
              Create patient and analyze
            </>
          )}
        </button>
      </div>
    </div>
  );
}
