/**
 * POST /api/patients/[hadmId]/submit
 *
 * Route param `[id]` is a hadm_id (numeric string).
 *
 * Body shapes:
 *   - empty               → Case 1 refresh (re-fetch Ahmad's dashboard, no persistence)
 *   - multipart/form-data → Case 2 update (note_text, vitals JSON, labs_pdf file)
 *
 * Returns the translated `PatientResult` plus `newHadmId` (Ahmad's pipeline
 * mints a new hadm_id after each /update — the UI should redirect there).
 */
import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/server/auth";
import {
  runAnalysisForHadmId,
  AIAnalysisOwnershipError,
  AIAnalysisExecutionError,
  type AnalysisInputs,
} from "@/lib/server/ai-analysis";
import type { AhmadVitalEntry } from "@/types";

export const maxDuration = 300;

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await context.params;
    const hadmId = Number.parseInt(id, 10);
    if (!Number.isFinite(hadmId)) {
      return NextResponse.json(
        { error: "Invalid hadm_id" },
        { status: 400 },
      );
    }

    const inputs: AnalysisInputs = {};
    const contentType = request.headers.get("content-type") ?? "";

    if (contentType.startsWith("multipart/form-data")) {
      const form = await request.formData();

      const noteText = form.get("note_text");
      if (typeof noteText === "string" && noteText.trim().length > 0) {
        inputs.noteText = noteText;
      }

      const vitalsRaw = form.get("vitals");
      if (typeof vitalsRaw === "string" && vitalsRaw.trim().length > 0) {
        try {
          const parsed = JSON.parse(vitalsRaw);
          if (Array.isArray(parsed) && parsed.length > 0) {
            inputs.vitals = parsed as AhmadVitalEntry[];
          }
        } catch {
          /* ignore — bad vitals JSON */
        }
      }

      const file = form.get("labs_pdf");
      if (file instanceof File && file.size > 0) {
        inputs.labsPdf = Buffer.from(await file.arrayBuffer());
      }
    }

    const out = await runAnalysisForHadmId(hadmId, session.user.id, inputs);

    return NextResponse.json({
      newHadmId: out.newHadmId,
      patientId: out.patient.id,
      fullResult: out.fullResult,
      updateDiff: out.updateDiff,
    });
  } catch (err) {
    if (err instanceof AIAnalysisOwnershipError) {
      return NextResponse.json(
        { error: err.httpStatus === 404 ? "Patient not found" : "Forbidden" },
        { status: err.httpStatus },
      );
    }
    if (err instanceof AIAnalysisExecutionError) {
      return NextResponse.json(
        { error: err.message },
        { status: err.httpStatus },
      );
    }
    console.error("POST /api/patients/[id]/submit error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
