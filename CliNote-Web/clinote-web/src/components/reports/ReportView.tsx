"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Pencil,
  Send,
  CheckCircle2,
  XCircle,
  Printer,
  Sparkles,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { clsx } from "clsx";
import Modal from "@/components/ui/Modal";
import { ReportEditor } from "@/components/reports/ReportEditor";
import type { Report } from "@/types";

interface ReportViewProps {
  report: Report;
  patient: {
    id: string;
    firstName: string;
    lastName: string;
    mrn: string;
  };
  authorName: string;
}

const STATUS_STYLES = {
  DRAFT:
    "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300",
  PENDING_REVIEW:
    "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  APPROVED:
    "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
  REJECTED: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
};

const STATUS_LABELS = {
  DRAFT: "Draft",
  PENDING_REVIEW: "Pending Review",
  APPROVED: "Approved",
  REJECTED: "Rejected",
};

function formatDateTime(iso?: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Detects "[REJECTED on … by …: reason]" prefix in content and extracts.
 *  Uses [\s\S] instead of . with /s flag so it works on older TS targets. */
function extractRejection(content: string): {
  reason: string | null;
  cleanContent: string;
} {
  const match = content.match(
    /^\[REJECTED on [\s\S]+? by [\s\S]+?: ([\s\S]+?)\]\n\n/,
  );
  if (!match) return { reason: null, cleanContent: content };
  return {
    reason: match[1],
    cleanContent: content.slice(match[0].length),
  };
}

export function ReportView({ report, patient, authorName }: ReportViewProps) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [busy, setBusy] = useState<null | "submit" | "approve" | "reject" | "edit">(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  const isApproved = report.status === "APPROVED";
  const { reason: rejectionReasonFromContent, cleanContent } = extractRejection(
    report.content,
  );

  async function transition(
    nextStatus: Report["status"],
    extra?: { rejectionReason?: string },
  ) {
    setError(null);
    setBusy(
      nextStatus === "PENDING_REVIEW"
        ? "submit"
        : nextStatus === "APPROVED"
          ? "approve"
          : nextStatus === "REJECTED"
            ? "reject"
            : "edit",
    );
    try {
      const res = await fetch(`/api/reports/${report.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus, ...extra }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error ?? `Action failed (${res.status})`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
    } finally {
      setBusy(null);
    }
  }

  async function submitForReview() {
    await transition("PENDING_REVIEW");
  }
  async function approve() {
    if (!confirm("Approve this report? It will be locked and read-only.")) return;
    await transition("APPROVED");
  }
  async function reject() {
    if (!rejectReason.trim()) return;
    await transition("REJECTED", { rejectionReason: rejectReason.trim() });
    setRejectModalOpen(false);
    setRejectReason("");
  }
  async function reEdit() {
    await transition("DRAFT");
    setEditing(true);
  }

  if (editing) {
    return (
      <div className="space-y-3">
        <Link
          href={`/patients/${patient.id}`}
          className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to patient
        </Link>
        <ReportEditor
          report={report}
          onClose={() => setEditing(false)}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl space-y-4">
      <Link
        href={`/patients/${patient.id}`}
        className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to {patient.firstName} {patient.lastName}
      </Link>

      {/* Top bar with status, action buttons */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                {report.title}
              </h1>
              <span
                className={clsx(
                  "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
                  STATUS_STYLES[report.status],
                )}
              >
                {STATUS_LABELS[report.status]}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              <Link
                href={`/patients/${patient.id}`}
                className="font-medium text-blue-600 hover:underline dark:text-blue-400"
              >
                {patient.firstName} {patient.lastName}
              </Link>
              {" · "}
              MRN {patient.mrn}
              {" · "}
              by {authorName}
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-2">
            {report.originalAI && (
              <button
                type="button"
                onClick={() => setShowOriginal(true)}
                className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
              >
                <Sparkles className="h-3 w-3" />
                View Original AI Text
              </button>
            )}
            {report.status === "DRAFT" && (
              <>
                <button
                  type="button"
                  onClick={() => setEditing(true)}
                  className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
                >
                  <Pencil className="h-3 w-3" />
                  Edit
                </button>
                <button
                  type="button"
                  onClick={submitForReview}
                  disabled={busy !== null}
                  className={clsx(
                    "inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium text-white",
                    busy === "submit"
                      ? "cursor-not-allowed bg-blue-400"
                      : "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600",
                  )}
                >
                  {busy === "submit" ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Send className="h-3 w-3" />
                  )}
                  Submit for Review
                </button>
              </>
            )}
            {report.status === "PENDING_REVIEW" && (
              <>
                <button
                  type="button"
                  onClick={() => setRejectModalOpen(true)}
                  disabled={busy !== null}
                  className="inline-flex items-center gap-1 rounded-md border border-red-300 bg-white px-2.5 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 dark:border-red-800 dark:bg-slate-800 dark:text-red-400 dark:hover:bg-red-950/30"
                >
                  <XCircle className="h-3 w-3" />
                  Reject
                </button>
                <button
                  type="button"
                  onClick={approve}
                  disabled={busy !== null}
                  className={clsx(
                    "inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium text-white",
                    busy === "approve"
                      ? "cursor-not-allowed bg-green-400"
                      : "bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600",
                  )}
                >
                  {busy === "approve" ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-3 w-3" />
                  )}
                  Approve
                </button>
              </>
            )}
            {report.status === "APPROVED" && (
              <button
                type="button"
                onClick={() => window.print()}
                className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
              >
                <Printer className="h-3 w-3" />
                Print
              </button>
            )}
            {report.status === "REJECTED" && (
              <button
                type="button"
                onClick={reEdit}
                disabled={busy !== null}
                className={clsx(
                  "inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium text-white",
                  busy === "edit"
                    ? "cursor-not-allowed bg-blue-400"
                    : "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600",
                )}
              >
                {busy === "edit" ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Pencil className="h-3 w-3" />
                )}
                Edit & Resubmit
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* APPROVED prominent banner */}
        {isApproved && report.approvedAt && (
          <div className="mt-3 flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            Approved on {formatDateTime(report.approvedAt)} — locked, read-only
          </div>
        )}

        {/* Rejection reason banner */}
        {report.status === "REJECTED" && rejectionReasonFromContent && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-semibold">Rejected</p>
              <p className="mt-0.5 text-xs">{rejectionReasonFromContent}</p>
            </div>
          </div>
        )}
      </div>

      {/* Status timeline */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          History
        </h3>
        <ul className="mt-2 space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
          <li>
            <span className="font-medium">Created</span> on{" "}
            {formatDateTime(report.createdAt)}
          </li>
          {report.status !== "DRAFT" && (
            <li>
              <span className="font-medium">Last updated</span> on{" "}
              {formatDateTime(report.updatedAt)}
            </li>
          )}
          {report.approvedAt && (
            <li className="text-green-700 dark:text-green-400">
              <span className="font-medium">Approved</span> on{" "}
              {formatDateTime(report.approvedAt)}
            </li>
          )}
        </ul>
      </div>

      {/* Body */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-800 dark:text-slate-200">
          {cleanContent}
        </pre>
      </div>

      {/* Reject modal */}
      <Modal
        isOpen={rejectModalOpen}
        onClose={() => {
          setRejectModalOpen(false);
          setRejectReason("");
        }}
        title="Reject Report"
      >
        <div className="space-y-3">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Provide a reason for rejection. This will be visible on the report.
          </p>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={4}
            placeholder="e.g. Missing imaging review, unclear medication reconciliation, etc."
            className="w-full rounded-lg border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                setRejectModalOpen(false);
                setRejectReason("");
              }}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={reject}
              disabled={!rejectReason.trim() || busy !== null}
              className={clsx(
                "inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium text-white",
                !rejectReason.trim() || busy !== null
                  ? "cursor-not-allowed bg-red-400"
                  : "bg-red-600 hover:bg-red-700",
              )}
            >
              {busy === "reject" ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <XCircle className="h-3 w-3" />
              )}
              Reject Report
            </button>
          </div>
        </div>
      </Modal>

      {/* Original AI text modal */}
      <Modal
        isOpen={showOriginal}
        onClose={() => setShowOriginal(false)}
        title="Original AI-Generated Text"
      >
        <pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-700 dark:text-slate-300">
          {report.originalAI ?? "No original AI text saved."}
        </pre>
      </Modal>
    </div>
  );
}
