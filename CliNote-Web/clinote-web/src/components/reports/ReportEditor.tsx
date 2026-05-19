"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Save, X, GitCompareArrows, Check } from "lucide-react";
import { clsx } from "clsx";
import type { Report } from "@/types";

interface ReportEditorProps {
  report: Report;
  onClose: () => void;
}

const AUTOSAVE_DEBOUNCE_MS = 1500;

export function ReportEditor({ report, onClose }: ReportEditorProps) {
  const router = useRouter();
  const [title, setTitle] = useState(report.title);
  const [content, setContent] = useState(report.content);
  const [showCompare, setShowCompare] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(
    new Date(report.updatedAt),
  );
  const [savingState, setSavingState] = useState<"idle" | "saving" | "saved">(
    "idle",
  );
  const [error, setError] = useState<string | null>(null);

  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const dirty = useRef(false);

  // Autosave: debounce 1.5s after the last change
  useEffect(() => {
    if (!dirty.current) return;
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      void save({ silent: true });
    }, AUTOSAVE_DEBOUNCE_MS);
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [title, content]);

  async function save({ silent }: { silent: boolean }) {
    setError(null);
    setSavingState("saving");
    try {
      const res = await fetch(`/api/reports/${report.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error ?? `Save failed (${res.status})`);
        setSavingState("idle");
        return false;
      }
      dirty.current = false;
      setSavedAt(new Date());
      setSavingState("saved");
      if (!silent) {
        setTimeout(() => setSavingState("idle"), 1200);
      } else {
        setTimeout(() => setSavingState("idle"), 1500);
      }
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
      setSavingState("idle");
      return false;
    }
  }

  async function saveAndClose() {
    const ok = await save({ silent: false });
    if (ok) {
      router.refresh();
      onClose();
    }
  }

  function cancel() {
    if (
      dirty.current &&
      !confirm("Discard unsaved changes?")
    )
      return;
    onClose();
  }

  function onTitleChange(v: string) {
    dirty.current = true;
    setTitle(v);
  }
  function onContentChange(v: string) {
    dirty.current = true;
    setContent(v);
  }

  return (
    <div className="space-y-4">
      {/* Title bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
          Editing
        </span>
        <div className="ml-auto flex items-center gap-2">
          <SaveStatus state={savingState} savedAt={savedAt} />
          {report.originalAI && (
            <button
              type="button"
              onClick={() => setShowCompare((v) => !v)}
              className={clsx(
                "inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors",
                showCompare
                  ? "border-blue-600 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-950/40 dark:text-blue-300"
                  : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600",
              )}
            >
              <GitCompareArrows className="h-3 w-3" />
              {showCompare ? "Hide compare" : "Compare with AI"}
            </button>
          )}
          <button
            type="button"
            onClick={cancel}
            className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
          >
            <X className="h-3 w-3" />
            Cancel
          </button>
          <button
            type="button"
            onClick={saveAndClose}
            disabled={savingState === "saving"}
            className={clsx(
              "inline-flex items-center gap-1 rounded-md px-3 py-1 text-xs font-medium text-white transition-colors",
              savingState === "saving"
                ? "cursor-not-allowed bg-blue-400"
                : "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600",
            )}
          >
            <Save className="h-3 w-3" />
            Save & Close
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Title input */}
      <input
        type="text"
        value={title}
        onChange={(e) => onTitleChange(e.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-lg font-semibold text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
      />

      {/* Editor — split view if comparing, single textarea otherwise */}
      {showCompare && report.originalAI ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <ComparePane
            heading="Your edited report"
            value={content}
            onChange={onContentChange}
            editable
          />
          <ComparePane
            heading="Original AI text"
            value={report.originalAI}
            editable={false}
          />
        </div>
      ) : (
        <textarea
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
          rows={24}
          className="w-full rounded-xl border border-slate-200 bg-white p-4 font-mono text-sm leading-relaxed text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        />
      )}
    </div>
  );
}

function ComparePane({
  heading,
  value,
  onChange,
  editable,
}: {
  heading: string;
  value: string;
  onChange?: (v: string) => void;
  editable: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <div className="border-b border-slate-200 px-4 py-2 dark:border-slate-700">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {heading}
        </p>
      </div>
      {editable ? (
        <textarea
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          rows={20}
          className="w-full rounded-b-xl bg-white p-4 font-mono text-sm leading-relaxed text-slate-800 focus:outline-none dark:bg-slate-800 dark:text-slate-200"
        />
      ) : (
        <pre className="max-h-[480px] overflow-auto whitespace-pre-wrap rounded-b-xl p-4 font-mono text-sm leading-relaxed text-slate-700 dark:text-slate-300">
          {value}
        </pre>
      )}
    </div>
  );
}

function SaveStatus({
  state,
  savedAt,
}: {
  state: "idle" | "saving" | "saved";
  savedAt: Date | null;
}) {
  if (state === "saving") {
    return (
      <span className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
        <Loader2 className="h-3 w-3 animate-spin" />
        Saving…
      </span>
    );
  }
  if (state === "saved") {
    return (
      <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
        <Check className="h-3 w-3" />
        Saved
      </span>
    );
  }
  if (savedAt) {
    return (
      <span className="text-xs text-slate-400 dark:text-slate-500">
        Last saved {savedAt.toLocaleTimeString()}
      </span>
    );
  }
  return null;
}
