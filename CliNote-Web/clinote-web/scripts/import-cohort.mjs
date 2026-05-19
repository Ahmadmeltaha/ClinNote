/**
 * One-shot importer: reads every `patient_*.json` from Ahmad's outputs/summaries
 * folder and creates the corresponding rows in our Supabase DB:
 *   - Patient (shadow row, MRN = "MIMIC-{hadm_id}")
 *   - AISummary (clinical_summary content, mortality risk, key findings)
 *   - Alert (one per item in `alerts` array)
 *   - Report (DRAFT, ready for the doctor to review)
 *
 * Idempotent — skips any Patient row already imported.
 *
 * Usage:
 *   AI_OUTPUTS_DIR is read from .env.local (defaults to D:\CliNote\ClinNote-AI\ClinNote\outputs)
 *   node scripts/import-cohort.mjs
 */

import { PrismaClient } from "@prisma/client";
import fs from "node:fs/promises";
import path from "node:path";

const AI_OUTPUTS_DIR =
  process.env.AI_OUTPUTS_DIR ??
  "D:\\CliNote\\ClinNote-AI\\ClinNote\\outputs";
const SUMMARIES_DIR = path.join(AI_OUTPUTS_DIR, "summaries");

const prisma = new PrismaClient();

function mapAlertType(category) {
  if (category === "LAB") return "LAB_ABNORMAL";
  if (category === "VITAL") return "VITAL_ABNORMAL";
  if (category === "MORTALITY") return "DISCREPANCY";
  return "DISCREPANCY";
}

function mapAlertPriority(priority) {
  if (priority === "CRITICAL" || priority === "HIGH") return "CRITICAL";
  if (priority === "MEDIUM" || priority === "WARNING") return "WARNING";
  return "INFO";
}

async function main() {
  const doctor = await prisma.user.findFirst();
  if (!doctor) {
    console.error(
      "ERROR: No doctor account found in DB. Register an account through the web first.",
    );
    process.exit(1);
  }
  console.log(`Importing as doctor: ${doctor.name} (${doctor.email})`);

  let files;
  try {
    files = await fs.readdir(SUMMARIES_DIR);
  } catch (e) {
    console.error(`ERROR: Can't read ${SUMMARIES_DIR}: ${e.message}`);
    process.exit(1);
  }

  const summaryFiles = files.filter(
    (f) =>
      f.startsWith("patient_") &&
      f.endsWith(".json") &&
      !f.includes("_report"),
  );
  console.log(`Found ${summaryFiles.length} summary files\n`);

  let imported = 0;
  let skipped = 0;
  let errors = 0;

  for (let i = 0; i < summaryFiles.length; i++) {
    const file = summaryFiles[i];
    try {
      const raw = await fs.readFile(path.join(SUMMARIES_DIR, file), "utf8");
      const cleaned = raw.replace(/:\s*NaN/g, ": null");
      const ahmad = JSON.parse(cleaned);

      const hadmId = ahmad.hadm_id;
      const subjectId = ahmad.subject_id;
      if (!hadmId || !subjectId) {
        skipped++;
        continue;
      }

      const exists = await prisma.patient.findUnique({
        where: { aiHadmId: hadmId },
        select: { id: true },
      });
      if (exists) {
        skipped++;
        continue;
      }

      const currentYear = new Date().getFullYear();
      const age = ahmad.demographics?.age ?? 50;
      const yearOfBirth = currentYear - age;

      let admissionDate = new Date(ahmad.admission?.admittime ?? Date.now());
      if (Number.isNaN(admissionDate.getTime())) admissionDate = new Date();

      const generatedAt = new Date(ahmad.generated_at ?? Date.now());

      const patient = await prisma.patient.create({
        data: {
          mrn: `MIMIC-${hadmId}`,
          firstName: "Patient",
          lastName: String(subjectId),
          dateOfBirth: new Date(yearOfBirth, 0, 1),
          gender: ahmad.demographics?.gender === "M" ? "MALE" : "FEMALE",
          admissionDate,
          attendingDoctorId: doctor.id,
          aiHadmId: hadmId,
          aiSubjectId: subjectId,
        },
      });

      const mortality = ahmad.predicted_mortality ?? {};
      const summaryText = ahmad.clinical_summary ?? "";
      const labAnomalies = ahmad.lab_summary?.top_abnormal ?? [];
      const vitalAlerts = ahmad.vital_summary?.alerts ?? [];

      const keyFindings = [
        ...labAnomalies.map(
          (l) =>
            `Lab: ${l.name} ${l.value} ${l.unit || ""} (${l.direction})`,
        ),
        ...vitalAlerts.map(
          (v) => `Vital: ${v.vital_name} ${v.current_value ?? v.value} (${v.status})`,
        ),
      ];

      await prisma.aISummary.create({
        data: {
          patientId: patient.id,
          summaryType: "COMPREHENSIVE",
          content: summaryText,
          keyFindings,
          mortalityRisk: mortality.probability ?? null,
          riskLevel: mortality.risk_level ?? null,
          modelUsed: `imported|hadm_id=${hadmId}`,
          generatedAt,
        },
      });

      const alerts = ahmad.alerts ?? [];
      if (alerts.length > 0) {
        await prisma.alert.createMany({
          data: alerts.map((a) => ({
            patientId: patient.id,
            alertType: mapAlertType(a.category),
            priority: mapAlertPriority(a.priority),
            title: (a.title ?? a.message ?? "Alert").slice(0, 200),
            message: a.message ?? "",
            source: "AI",
            sourceData: a,
            createdAt: generatedAt,
          })),
        });
      }

      const today = new Date().toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
      await prisma.report.create({
        data: {
          patientId: patient.id,
          authorId: doctor.id,
          title: `Clinical Report — Patient ${subjectId} — ${today}`,
          content: summaryText,
          originalAI: summaryText,
          status: "DRAFT",
        },
      });

      imported++;
      if (imported % 25 === 0) {
        process.stdout.write(`  imported ${imported}/${summaryFiles.length}...\n`);
      }
    } catch (err) {
      errors++;
      if (errors <= 5) {
        console.error(`  ! ${file}: ${err.message}`);
      }
    }
  }

  console.log(
    `\nDone.  imported=${imported}  skipped=${skipped} (already in DB)  errors=${errors}`,
  );
  await prisma.$disconnect();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
