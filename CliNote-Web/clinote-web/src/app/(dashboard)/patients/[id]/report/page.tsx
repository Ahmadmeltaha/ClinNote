import { notFound, redirect } from "next/navigation";
import { getAuthSession } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";
import { ReportView } from "@/components/reports/ReportView";
import type { Report } from "@/types";

/**
 * `[id]` is a hadm_id (numeric string) in the new Option A flow. Reports live
 * on the shadow `Patient` row we lazy-created when the doctor first analyzed
 * this admission. If no shadow row exists → no analysis has been run yet.
 */
export default async function PatientReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await getAuthSession();
  if (!session?.user) redirect("/login");

  const { id } = await params;
  const hadmId = Number.parseInt(id, 10);
  if (!Number.isFinite(hadmId)) notFound();

  const patient = await prisma.patient.findUnique({
    where: { aiHadmId: hadmId },
    select: {
      id: true,
      firstName: true,
      lastName: true,
      mrn: true,
      aiHadmId: true,
      aiSubjectId: true,
    },
  });

  // Patient not yet analyzed by anyone — there's no shadow row, no report.
  if (!patient) {
    return <NoReportYet hadmId={hadmId} />;
  }

  let report = await prisma.report.findFirst({
    where: { patientId: patient.id },
    include: { author: { select: { name: true } } },
    orderBy: { createdAt: "desc" },
  });

  if (!report) {
    const summary = await prisma.aISummary.findFirst({
      where: { patientId: patient.id },
      orderBy: { generatedAt: "desc" },
    });
    if (!summary) {
      return <NoReportYet hadmId={hadmId} />;
    }

    const today = new Date().toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
    report = await prisma.report.create({
      data: {
        patientId: patient.id,
        authorId: session.user.id,
        title: `Clinical Report — ${patient.firstName} ${patient.lastName} — ${today}`,
        content: summary.content,
        originalAI: summary.content,
        status: "DRAFT",
      },
      include: { author: { select: { name: true } } },
    });
  }

  const serialized: Report = {
    id: report.id,
    patientId: String(hadmId),
    authorId: report.authorId,
    title: report.title,
    content: report.content,
    originalAI: report.originalAI ?? undefined,
    status: report.status,
    approvedAt: report.approvedAt?.toISOString(),
    createdAt: report.createdAt.toISOString(),
    updatedAt: report.updatedAt.toISOString(),
  };

  return (
    <ReportView
      report={serialized}
      patient={{
        id: String(hadmId),
        firstName: patient.firstName,
        lastName: patient.lastName,
        mrn: patient.mrn,
      }}
      authorName={report.author.name}
    />
  );
}

function NoReportYet({ hadmId }: { hadmId: number }) {
  return (
    <div className="mx-auto max-w-2xl rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center dark:border-slate-600 dark:bg-slate-800">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
        No report yet
      </h2>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        Run AI analysis on this admission first — a draft report will be
        generated automatically.
      </p>
      <a
        href={`/patients/${hadmId}`}
        className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        Go to patient
      </a>
    </div>
  );
}
