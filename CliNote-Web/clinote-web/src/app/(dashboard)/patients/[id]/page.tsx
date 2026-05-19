import { notFound, redirect } from "next/navigation";
import { getAuthSession } from "@/lib/server/auth";
import {
  getDashboardFromDisk,
  getAhmadPatientDashboard,
  AIPipelineError,
} from "@/lib/server/ai-pipeline";
import { translateAhmadResponse } from "@/lib/server/ai-adapter";
import { ensureCohortPersistence } from "@/lib/server/ai-analysis";
import { getAdmissionsForSubject } from "@/lib/server/cohort";
import { CohortPatientDashboard } from "@/components/patient-detail/CohortPatientDashboard";
import { AdmissionsRail } from "@/components/patient-detail/AdmissionsRail";

export const dynamic = "force-dynamic";

export default async function PatientDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await getAuthSession();
  if (!session?.user) redirect("/login");

  const { id } = await params;
  const hadmId = Number.parseInt(id, 10);
  if (!Number.isFinite(hadmId)) notFound();

  // Disk-first (fast). Falls back to Ahmad's HTTP endpoint (slow, regenerates LLM).
  let ahmad = await getDashboardFromDisk(hadmId);
  if (!ahmad) {
    try {
      ahmad = await getAhmadPatientDashboard(hadmId);
    } catch (err) {
      if (err instanceof AIPipelineError && err.status === 404) notFound();
      throw err;
    }
  }

  // Lazy-persist shadow Patient + AISummary + DRAFT Report on first view so
  // View Report works without forcing the doctor to click Re-analyze.
  // Idempotent on subsequent views (returns existing AISummary).
  const { patient, aiSummary } = await ensureCohortPersistence(
    ahmad,
    session.user.id,
  );

  const result = translateAhmadResponse(ahmad);

  // If our DB has a richer (LLM-generated) summary from a prior Case 2/3 run,
  // swap it in. The disk JSON's summary is the simple template — DB has the
  // Phi-3.5 output when we ran analysis through our app.
  if (aiSummary?.content && aiSummary.content.length > 80) {
    result.note_summary = aiSummary.content;
  }

  // Pick the display name: real names if the doctor entered them on Case 3,
  // otherwise the anonymous "Patient {subject_id}" fallback.
  const isDefault =
    patient.firstName === "Patient" &&
    patient.lastName === String(result.subject_id);
  const displayName = isDefault
    ? `Patient ${result.subject_id}`
    : `${patient.firstName} ${patient.lastName}`;

  // All admissions for the same subject — used by the left rail so the doctor
  // can navigate between admissions for the same patient with one click.
  const admissions = await getAdmissionsForSubject(result.subject_id);

  return (
    <div className="grid gap-6 lg:grid-cols-12">
      <main className="lg:col-span-9">
        <CohortPatientDashboard
          hadmId={hadmId}
          result={result}
          displayName={displayName}
          mrn={patient.mrn}
        />
      </main>
      <aside className="lg:col-span-3 lg:sticky lg:top-6 lg:self-start lg:order-last">
        <AdmissionsRail currentHadmId={hadmId} admissions={admissions} />
      </aside>
    </div>
  );
}
