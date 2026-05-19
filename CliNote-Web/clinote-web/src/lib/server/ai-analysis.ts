/**
 * Orchestration for Ahmad's 3 AI cases:
 *   - Case 1 (View existing):     `runAnalysisForHadmId(hadmId, doctorId)`
 *   - Case 2 (Update existing):   `runAnalysisForHadmId(hadmId, doctorId, { ...inputs })`
 *   - Case 3 (Create new patient): `createPatientWithAI(doctorId, { age, gender, ... })`
 *
 * The web's source of truth for the patient list is now Ahmad's `/api/patients`
 * (his MIMIC cohort + everything submitted through Case 3). On first touch of
 * a patient by hadm_id, we lazy-create a "shadow" `Patient` row in our DB so
 * existing FK relations (AISummary / Alert / Report → Patient.id) keep working.
 */

import { prisma } from "@/lib/server/prisma";
import {
  AIPipelineError,
  getAhmadPatientDashboard,
  submitNewPatient,
  updatePatient,
} from "@/lib/server/ai-pipeline";
import {
  translateAhmadResponse,
  wideVitalsToAhmadArray,
} from "@/lib/server/ai-adapter";
import type {
  AhmadDashboardResponse,
  AhmadVitalEntry,
  PatientResult,
} from "@/types";
import type {
  Patient,
  AlertType,
  AlertPriority,
} from "@prisma/client";

export class AIAnalysisOwnershipError extends Error {
  constructor(public httpStatus: 401 | 403 | 404) {
    super(`AI analysis ownership error: ${httpStatus}`);
    this.name = "AIAnalysisOwnershipError";
  }
}

export class AIAnalysisExecutionError extends Error {
  constructor(
    message: string,
    public httpStatus: 502 | 504,
  ) {
    super(message);
    this.name = "AIAnalysisExecutionError";
  }
}

export interface AnalysisInputs {
  noteText?: string;
  vitals?: AhmadVitalEntry[];
  labsPdf?: Buffer;
}

// ────────────────────────────────────────────────────────────────────────────
// Case 1 + Case 2 — existing hadm_id
// ────────────────────────────────────────────────────────────────────────────

/**
 * Either view (Case 1) or update (Case 2) an existing admission.
 * If `inputs` contains any new data, we POST /update; else we GET the dashboard.
 *
 * On update, Ahmad's pipeline produces a NEW hadm_id for the merged admission —
 * we return it as `newHadmId` so the UI can redirect there.
 */
export async function runAnalysisForHadmId(
  hadmId: number,
  doctorId: string,
  inputs: AnalysisInputs = {},
) {
  const hasNewData = !!(
    inputs.noteText ||
    (inputs.vitals && inputs.vitals.length > 0) ||
    inputs.labsPdf
  );

  let ahmad: AhmadDashboardResponse;
  try {
    if (hasNewData) {
      ahmad = await updatePatient(hadmId, inputs);
    } else {
      ahmad = await getAhmadPatientDashboard(hadmId);
    }
  } catch (err) {
    if (err instanceof AIPipelineError) {
      throw new AIAnalysisExecutionError(
        `AI pipeline error: ${err.message}`,
        err.status === 504 ? 504 : 502,
      );
    }
    throw new AIAnalysisExecutionError("Failed to call AI pipeline", 502);
  }

  const result = translateAhmadResponse(ahmad);
  const patient = await ensureShadowPatient(ahmad, doctorId);

  // Only persist when there was actually a new analysis. Case 1 (pure view) is
  // idempotent — re-persisting on every page load would duplicate alerts.
  if (hasNewData) {
    await syncAIDerivedRecords(patient.id, result);
    await syncReport(patient.id, doctorId, patient, result);
    await persistResult(patient.id, result);
  }

  return {
    patient,
    fullResult: result,
    updateDiff: result.update_diff,
    newHadmId: ahmad.hadm_id,
  };
}

// ────────────────────────────────────────────────────────────────────────────
// Case 3 — new patient
// ────────────────────────────────────────────────────────────────────────────

export interface NewPatientInputs {
  firstName?: string;
  lastName?: string;
  age: number;
  gender: "M" | "F";
  admittime?: string;
  noteText?: string;
  vitals?: AhmadVitalEntry[];
  labsPdf?: Buffer;
}

export async function createPatientWithAI(
  doctorId: string,
  args: NewPatientInputs,
) {
  let ahmad: AhmadDashboardResponse;
  try {
    ahmad = await submitNewPatient(args);
  } catch (err) {
    if (err instanceof AIPipelineError) {
      throw new AIAnalysisExecutionError(
        `AI pipeline error: ${err.message}`,
        502,
      );
    }
    throw new AIAnalysisExecutionError("Failed to create patient", 502);
  }

  const result = translateAhmadResponse(ahmad);
  const patient = await ensureShadowPatient(ahmad, doctorId, {
    firstName: args.firstName,
    lastName: args.lastName,
  });
  await syncAIDerivedRecords(patient.id, result);
  await syncReport(patient.id, doctorId, patient, result);
  await persistResult(patient.id, result);

  return {
    patient,
    hadmId: ahmad.hadm_id,
    fullResult: result,
  };
}

// ────────────────────────────────────────────────────────────────────────────
// Case 1 implicit persistence — make View Report work for cohort patients
// ────────────────────────────────────────────────────────────────────────────

/**
 * Called by the patient detail server component the FIRST time anyone opens
 * a cohort admission. Lazy-creates the shadow Patient + one AISummary + one
 * DRAFT Report from the disk-saved Ahmad data, so the View Report link works
 * without forcing the doctor to click Re-analyze first.
 *
 * Idempotent — if an AISummary already exists for this patient, we just
 * return it (no duplicates).
 */
export async function ensureCohortPersistence(
  ahmad: AhmadDashboardResponse,
  doctorId: string,
): Promise<{ patient: Patient; aiSummary: { content: string } | null }> {
  const patient = await ensureShadowPatient(ahmad, doctorId);

  const existing = await prisma.aISummary.findFirst({
    where: { patientId: patient.id },
    orderBy: { generatedAt: "desc" },
    select: { content: true },
  });
  if (existing) return { patient, aiSummary: existing };

  const result = translateAhmadResponse(ahmad);
  await syncAIDerivedRecords(patient.id, result);
  await syncReport(patient.id, doctorId, patient, result);
  const persisted = await persistResult(patient.id, result);
  return {
    patient,
    aiSummary: { content: persisted.aiSummary.content },
  };
}

// ────────────────────────────────────────────────────────────────────────────
// Shadow patient — lazy-create on first touch
// ────────────────────────────────────────────────────────────────────────────

/**
 * Look up the local `Patient` row for a given Ahmad admission, or create one
 * if it doesn't exist. We need this so AISummary / Alert / Report rows can
 * keep their FK relation to Patient.
 *
 * Demographics are derived from Ahmad's response:
 *   - dateOfBirth: approximated as Jan 1 of (currentYear - age)
 *   - firstName/lastName: "Patient {subject_id}" (cohort patients are anonymous)
 *   - mrn: "MIMIC-{hadm_id}" (unique per admission)
 */
async function ensureShadowPatient(
  ahmad: AhmadDashboardResponse,
  doctorId: string,
  overrides: { firstName?: string; lastName?: string } = {},
): Promise<Patient> {
  const hadmId = ahmad.hadm_id;
  const subjectId = ahmad.subject_id;

  const existing = await prisma.patient.findUnique({
    where: { aiHadmId: hadmId },
  });
  if (existing) {
    // If caller provided a real name and the row was a default shadow, upgrade it.
    if (
      overrides.firstName &&
      overrides.lastName &&
      (existing.firstName === "Patient" || existing.lastName === String(subjectId))
    ) {
      return await prisma.patient.update({
        where: { id: existing.id },
        data: {
          firstName: overrides.firstName,
          lastName: overrides.lastName,
        },
      });
    }
    return existing;
  }

  const currentYear = new Date().getFullYear();
  const yearOfBirth = currentYear - (ahmad.demographics.age ?? 0);

  let admissionDate = new Date(ahmad.admission.admittime);
  if (Number.isNaN(admissionDate.getTime())) admissionDate = new Date();

  return await prisma.patient.create({
    data: {
      mrn: `MIMIC-${hadmId}`,
      firstName: overrides.firstName ?? "Patient",
      lastName: overrides.lastName ?? String(subjectId),
      dateOfBirth: new Date(yearOfBirth, 0, 1),
      gender: ahmad.demographics.gender === "M" ? "MALE" : "FEMALE",
      admissionDate,
      attendingDoctorId: doctorId,
      aiHadmId: hadmId,
      aiSubjectId: subjectId,
    },
  });
}

// ────────────────────────────────────────────────────────────────────────────
// AI-derived clinical records (Problems + Medications)
// ────────────────────────────────────────────────────────────────────────────

async function syncAIDerivedRecords(patientId: string, result: PatientResult) {
  const diagnoses = result.diagnoses ?? [];
  const medications = result.medications ?? [];

  await prisma.problem.deleteMany({ where: { patientId } });
  await prisma.medication.deleteMany({ where: { patientId } });

  if (diagnoses.length > 0) {
    await prisma.problem.createMany({
      data: diagnoses.map((name) => ({
        patientId,
        name,
        status: "ACTIVE" as const,
      })),
    });
  }

  if (medications.length > 0) {
    await prisma.medication.createMany({
      data: medications.map((name) => ({
        patientId,
        name,
        isActive: true,
      })),
    });
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Report — fresh DRAFT per analysis
// ────────────────────────────────────────────────────────────────────────────

async function syncReport(
  patientId: string,
  doctorId: string,
  patient: Patient,
  result: PatientResult,
) {
  const today = new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  await prisma.report.create({
    data: {
      patientId,
      authorId: doctorId,
      title: `Clinical Report — ${patient.firstName} ${patient.lastName} — ${today}`,
      content: result.note_summary,
      originalAI: result.note_summary,
      status: "DRAFT",
    },
  });
}

// ────────────────────────────────────────────────────────────────────────────
// Persistence — AISummary + Alerts
// ────────────────────────────────────────────────────────────────────────────

async function persistResult(patientId: string, result: PatientResult) {
  const keyFindings: string[] = [
    ...(result.diagnoses ?? []).map((d) => `Dx: ${d}`),
    ...(result.medications ?? []).map((m) => `Rx: ${m}`),
    ...result.lab_anomalies.map(
      (l) => `Lab: ${l.label} ${l.value} ${l.unit} (${l.flag}, ${l.severity})`,
    ),
    ...result.vital_anomalies.map(
      (v) => `Vital: ${v.label} ${v.value} ${v.unit} (${v.flag}, ${v.severity})`,
    ),
  ];

  const aiSummary = await prisma.aISummary.create({
    data: {
      patientId,
      summaryType: "COMPREHENSIVE",
      content: result.note_summary,
      keyFindings,
      mortalityRisk: result.mortality_risk.probability,
      riskLevel: result.mortality_risk.risk_level,
      modelUsed: `clinote-ai|hadm_id=${result.hadm_id}|subject_id=${result.subject_id}`,
      generatedAt: new Date(result.generated_at),
    },
  });

  await prisma.alert.updateMany({
    where: { patientId, source: "AI", isResolved: false },
    data: {
      isResolved: true,
      resolvedAt: new Date(),
      resolvedBy: "system (re-analysis)",
    },
  });

  // Bulk insert all alerts in ONE query. Was Promise.all over individual creates,
  // which fired N parallel inserts and exhausted Supabase's connection_limit=1
  // pool. createMany is one round-trip and much faster.
  if (result.alerts.length > 0) {
    await prisma.alert.createMany({
      data: result.alerts.map((a) => ({
        patientId,
        alertType: mapAlertType(a.type),
        priority: mapAlertPriority(a.severity),
        title: a.message.slice(0, 60) + (a.message.length > 60 ? "…" : ""),
        message: a.message,
        source: "AI",
        sourceData: a as unknown as object,
      })),
    });
  }

  return { aiSummary, alerts: [] };
}

function mapAlertType(t: PatientResult["alerts"][number]["type"]): AlertType {
  switch (t) {
    case "lab_critical":
      return "LAB_ABNORMAL";
    case "vital_critical":
      return "VITAL_ABNORMAL";
    case "trend_alert":
      return "TREND";
    case "mortality_risk":
      return "DISCREPANCY";
  }
}

function mapAlertPriority(s: "critical" | "warning"): AlertPriority {
  return s === "critical" ? "CRITICAL" : "WARNING";
}
