// One-shot script — clears aiHadmId/aiSubjectId on patients whose AI-side
// state was wiped. Run once after deleting the corresponding files in
// ClinNote-AI/outputs/patient_data/<subject_id>/ so the next analyze does
// a fresh /api/patient/new instead of a doomed /update.
//
// Usage:
//   node scripts/reset-ai-link.mjs           # clears all patients
//   node scripts/reset-ai-link.mjs 430093    # clears only patients linked to that AI subject_id

import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();
const targetSubjectId = process.argv[2] ? parseInt(process.argv[2], 10) : null;

const where = targetSubjectId !== null ? { aiSubjectId: targetSubjectId } : {};

const result = await prisma.patient.updateMany({
  where,
  data: { aiHadmId: null, aiSubjectId: null },
});

console.log(`Reset AI link on ${result.count} patient(s).`);
await prisma.$disconnect();
