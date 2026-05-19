/**
 * DB-backed cohort queries. Returns the same shape as Ahmad's `/api/patients`
 * response so the existing UI keeps working — but reads from Supabase instead
 * of Ahmad's local folder. This is what makes the app deployable to Vercel.
 *
 * Run `node scripts/import-cohort.mjs` once locally to seed Supabase from
 * Ahmad's summary files.
 */

import { prisma } from "@/lib/server/prisma";
import type { AhmadPatientListResponse } from "@/types";

type CohortPatient = AhmadPatientListResponse["patients"][number];

export interface CohortPatientWithName extends CohortPatient {
  firstName: string;
  lastName: string;
  displayName: string;
}

export interface CohortListResult {
  total: number;
  patients: CohortPatientWithName[];
}

function displayName(
  firstName: string,
  lastName: string,
  subjectId: number,
): string {
  if (firstName === "Patient" && lastName === String(subjectId)) {
    return `Patient ${subjectId}`;
  }
  return `${firstName} ${lastName}`;
}

function calculateAge(dateOfBirth: Date): number {
  const today = new Date();
  let age = today.getFullYear() - dateOfBirth.getFullYear();
  const m = today.getMonth() - dateOfBirth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < dateOfBirth.getDate())) age--;
  return age;
}

/**
 * List every shadow Patient in the DB that has an aiHadmId set, grouped by
 * subject_id. Matches the shape Ahmad's `/api/patients` returns.
 */
export async function getCohortFromDB(): Promise<CohortListResult> {
  const rows = await prisma.patient.findMany({
    where: { aiHadmId: { not: null }, aiSubjectId: { not: null } },
    include: {
      aiSummaries: {
        orderBy: { generatedAt: "desc" },
        take: 1,
        select: {
          mortalityRisk: true,
          riskLevel: true,
          generatedAt: true,
        },
      },
    },
    orderBy: { aiSubjectId: "asc" },
  });

  const grouped = new Map<number, CohortPatientWithName>();

  for (const p of rows) {
    if (p.aiSubjectId == null || p.aiHadmId == null) continue;
    const sid = p.aiSubjectId;
    const summary = p.aiSummaries[0];
    const admission = {
      hadm_id: p.aiHadmId,
      risk_level:
        (summary?.riskLevel as "LOW" | "MEDIUM" | "HIGH" | undefined) ??
        "LOW",
      probability: summary?.mortalityRisk ?? 0,
      generated_at:
        summary?.generatedAt.toISOString() ?? p.createdAt.toISOString(),
    };

    if (!grouped.has(sid)) {
      grouped.set(sid, {
        subject_id: sid,
        age: calculateAge(p.dateOfBirth),
        gender: p.gender === "MALE" ? "M" : "F",
        hadm_ids: [p.aiHadmId],
        admissions: [admission],
        firstName: p.firstName,
        lastName: p.lastName,
        displayName: displayName(p.firstName, p.lastName, sid),
      });
    } else {
      const g = grouped.get(sid)!;
      g.hadm_ids.push(p.aiHadmId);
      g.admissions.push(admission);
      // Prefer a real name over the default shadow if we have any with names
      if (p.firstName !== "Patient" && g.firstName === "Patient") {
        g.firstName = p.firstName;
        g.lastName = p.lastName;
        g.displayName = displayName(p.firstName, p.lastName, sid);
      }
    }
  }

  const patients = Array.from(grouped.values());
  return { total: patients.length, patients };
}

export interface PatientOverview {
  subjectId: number;
  firstName: string;
  lastName: string;
  displayName: string;
  age: number;
  gender: "M" | "F";
  admissions: AdmissionRailItem[];
  highestRisk: "LOW" | "MEDIUM" | "HIGH" | null;
  highestProbability: number | null;
  avgProbability: number | null;
  totalAlerts: number;
  criticalAlerts: number;
  firstAdmission: string | null;
  latestAdmission: string | null;
}

export async function getPatientOverview(
  subjectId: number,
): Promise<PatientOverview | null> {
  const rows = await prisma.patient.findMany({
    where: { aiSubjectId: subjectId, aiHadmId: { not: null } },
    include: {
      aiSummaries: {
        orderBy: { generatedAt: "desc" },
        take: 1,
        select: {
          mortalityRisk: true,
          riskLevel: true,
          generatedAt: true,
        },
      },
      alerts: {
        select: { id: true, priority: true, isResolved: true },
      },
    },
    orderBy: { admissionDate: "desc" },
  });
  if (rows.length === 0) return null;

  const first = rows[0];
  const admissions: AdmissionRailItem[] = rows
    .filter((r) => r.aiHadmId != null)
    .map((r) => ({
      hadmId: r.aiHadmId!,
      admissionDate: r.admissionDate.toISOString(),
      riskLevel: (r.aiSummaries[0]?.riskLevel as "LOW" | "MEDIUM" | "HIGH" | null) ?? null,
      probability: r.aiSummaries[0]?.mortalityRisk ?? null,
      generatedAt:
        r.aiSummaries[0]?.generatedAt.toISOString() ??
        r.admissionDate.toISOString(),
    }));

  const probs = admissions.map((a) => a.probability).filter((p): p is number => p != null);
  const avgProbability = probs.length > 0 ? probs.reduce((a, b) => a + b, 0) / probs.length : null;
  const highestProbability = probs.length > 0 ? Math.max(...probs) : null;
  const RANK = { HIGH: 2, MEDIUM: 1, LOW: 0 } as const;
  let highestRisk: "LOW" | "MEDIUM" | "HIGH" | null = null;
  for (const a of admissions) {
    if (!a.riskLevel) continue;
    if (highestRisk == null || RANK[a.riskLevel] > RANK[highestRisk]) {
      highestRisk = a.riskLevel;
    }
  }

  let totalAlerts = 0;
  let criticalAlerts = 0;
  for (const r of rows) {
    for (const al of r.alerts) {
      if (!al.isResolved) {
        totalAlerts++;
        if (al.priority === "CRITICAL") criticalAlerts++;
      }
    }
  }

  const isDefault =
    first.firstName === "Patient" && first.lastName === String(subjectId);
  const displayName = isDefault
    ? `Patient ${subjectId}`
    : `${first.firstName} ${first.lastName}`;

  const currentYear = new Date().getFullYear();
  const age = currentYear - first.dateOfBirth.getFullYear();

  // Sort by date ascending for first/latest
  const dates = rows
    .map((r) => r.admissionDate.getTime())
    .sort((a, b) => a - b);
  const firstAdmission = dates.length > 0 ? new Date(dates[0]).toISOString() : null;
  const latestAdmission =
    dates.length > 0 ? new Date(dates[dates.length - 1]).toISOString() : null;

  return {
    subjectId,
    firstName: first.firstName,
    lastName: first.lastName,
    displayName,
    age,
    gender: first.gender === "MALE" ? "M" : "F",
    admissions,
    highestRisk,
    highestProbability,
    avgProbability,
    totalAlerts,
    criticalAlerts,
    firstAdmission,
    latestAdmission,
  };
}

export interface AdmissionRailItem {
  hadmId: number;
  admissionDate: string;
  riskLevel: "LOW" | "MEDIUM" | "HIGH" | null;
  probability: number | null;
  generatedAt: string;
}

/** All admissions for a given subject_id, newest first. Used by the patient detail page's sidebar. */
export async function getAdmissionsForSubject(
  subjectId: number,
): Promise<AdmissionRailItem[]> {
  const rows = await prisma.patient.findMany({
    where: { aiSubjectId: subjectId, aiHadmId: { not: null } },
    include: {
      aiSummaries: {
        orderBy: { generatedAt: "desc" },
        take: 1,
        select: {
          mortalityRisk: true,
          riskLevel: true,
          generatedAt: true,
        },
      },
    },
    orderBy: { admissionDate: "desc" },
  });

  return rows
    .filter((r) => r.aiHadmId != null)
    .map((r) => {
      const s = r.aiSummaries[0];
      return {
        hadmId: r.aiHadmId!,
        admissionDate: r.admissionDate.toISOString(),
        riskLevel: (s?.riskLevel as "LOW" | "MEDIUM" | "HIGH" | null) ?? null,
        probability: s?.mortalityRisk ?? null,
        generatedAt:
          s?.generatedAt.toISOString() ?? r.admissionDate.toISOString(),
      };
    });
}

/**
 * Aggregated counts for the Statistics page. Runs queries SEQUENTIALLY (not
 * Promise.all) because Supabase's pgbouncer pool is configured with
 * connection_limit=1 — parallel queries time out fetching connections.
 */
export async function getCohortStats(): Promise<{
  totalPatients: number;
  totalAdmissions: number;
  highRiskCount: number;
  avgMortalityRisk: number | null;
  criticalAlertCount: number;
  totalAlerts: number;
}> {
  const admissions = await prisma.aISummary.findMany({
    select: {
      patientId: true,
      riskLevel: true,
      mortalityRisk: true,
    },
  });

  const totalAlerts = await prisma.alert.count({
    where: { isResolved: false },
  });

  const criticalCount = await prisma.alert.count({
    where: { isResolved: false, priority: "CRITICAL" },
  });

  const uniquePatients = new Set(admissions.map((a) => a.patientId)).size;
  const totalAdmissions = admissions.length;
  const highRisk = admissions.filter((a) => a.riskLevel === "HIGH").length;

  let probSum = 0;
  let probCount = 0;
  for (const a of admissions) {
    if (typeof a.mortalityRisk === "number") {
      probSum += a.mortalityRisk;
      probCount++;
    }
  }
  const avg = probCount > 0 ? probSum / probCount : null;

  return {
    totalPatients: uniquePatients,
    totalAdmissions,
    highRiskCount: highRisk,
    avgMortalityRisk: avg,
    criticalAlertCount: criticalCount,
    totalAlerts,
  };
}

/**
 * Used by the Statistics page to also compute the histogram + risk breakdown
 * without re-querying. Returns from a single findMany so the connection pool
 * doesn't get hammered.
 */
export async function getCohortStatsWithBreakdown(): Promise<{
  stats: Awaited<ReturnType<typeof getCohortStats>>;
  riskCounts: { HIGH: number; MEDIUM: number; LOW: number };
  histogram: number[];
}> {
  const admissions = await prisma.aISummary.findMany({
    select: {
      patientId: true,
      riskLevel: true,
      mortalityRisk: true,
    },
  });

  const totalAlerts = await prisma.alert.count({
    where: { isResolved: false },
  });

  const criticalCount = await prisma.alert.count({
    where: { isResolved: false, priority: "CRITICAL" },
  });

  const uniquePatients = new Set(admissions.map((a) => a.patientId)).size;
  const totalAdmissions = admissions.length;

  const riskCounts = { HIGH: 0, MEDIUM: 0, LOW: 0 };
  let probSum = 0;
  let probCount = 0;
  const histogram = new Array(10).fill(0) as number[];

  for (const a of admissions) {
    if (a.riskLevel === "HIGH") riskCounts.HIGH++;
    else if (a.riskLevel === "MEDIUM") riskCounts.MEDIUM++;
    else if (a.riskLevel === "LOW") riskCounts.LOW++;

    if (typeof a.mortalityRisk === "number") {
      probSum += a.mortalityRisk;
      probCount++;
      const idx = Math.min(
        9,
        Math.max(0, Math.floor(a.mortalityRisk * 10)),
      );
      histogram[idx]++;
    }
  }

  return {
    stats: {
      totalPatients: uniquePatients,
      totalAdmissions,
      highRiskCount: riskCounts.HIGH,
      avgMortalityRisk: probCount > 0 ? probSum / probCount : null,
      criticalAlertCount: criticalCount,
      totalAlerts,
    },
    riskCounts,
    histogram,
  };
}
