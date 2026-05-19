/**
 * GET  /api/patients  — list patients from Ahmad's cohort store
 * POST /api/patients  — Case 3: create a brand-new patient via Ahmad's /api/patient/new
 *
 * The web no longer maintains its own patient list — Ahmad's `/api/patients`
 * is the source of truth. Shadow `Patient` rows are created on demand by the
 * detail/submit/create handlers so existing FK relations (Alert / Report /
 * AISummary) keep working.
 */
import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { z } from "zod";
import { authOptions } from "@/lib/server/auth";
import { getAhmadPatients } from "@/lib/server/ai-pipeline";
import {
  AIAnalysisExecutionError,
  createPatientWithAI,
} from "@/lib/server/ai-analysis";

export const maxDuration = 300;

export async function GET() {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const list = await getAhmadPatients();
    return NextResponse.json(list);
  } catch (error) {
    console.error("GET /api/patients error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

const newPatientSchema = z.object({
  firstName: z.string().min(1).max(100),
  lastName: z.string().min(1).max(100),
  age: z.number().int().positive().max(130),
  gender: z.enum(["M", "F"]),
  admittime: z.string().optional(),
  noteText: z.string().max(50_000).optional(),
  vitals: z
    .array(
      z.object({
        name: z.enum([
          "Heart Rate",
          "Systolic Blood Pressure",
          "Diastolic Blood Pressure",
          "Mean Blood Pressure",
          "SpO2",
          "Respiratory Rate",
          "Temperature Fahrenheit",
          "Temperature Celsius",
        ]),
        value: z.number(),
      }),
    )
    .optional(),
});

/**
 * Case 3 — create a new patient. Accepts BOTH:
 *   - multipart/form-data (when a labs_pdf is uploaded)
 *   - application/json (when no PDF)
 */
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const contentType = request.headers.get("content-type") ?? "";

    let parsed: z.infer<typeof newPatientSchema>;
    let labsPdf: Buffer | undefined;

    if (contentType.startsWith("multipart/form-data")) {
      const form = await request.formData();
      const firstName = (form.get("firstName") as string)?.trim() || "";
      const lastName = (form.get("lastName") as string)?.trim() || "";
      const ageRaw = form.get("age");
      const genderRaw = form.get("gender");
      const noteText = (form.get("noteText") as string) || undefined;
      const admittime = (form.get("admittime") as string) || undefined;
      const vitalsRaw = (form.get("vitals") as string) || "[]";
      let vitals: z.infer<typeof newPatientSchema>["vitals"];
      try {
        vitals = JSON.parse(vitalsRaw);
      } catch {
        vitals = [];
      }

      const candidate = {
        firstName,
        lastName,
        age: ageRaw ? Number(ageRaw) : NaN,
        gender: genderRaw as "M" | "F",
        admittime,
        noteText,
        vitals,
      };
      const result = newPatientSchema.safeParse(candidate);
      if (!result.success) {
        return NextResponse.json(
          {
            error: "Validation failed",
            details: result.error.flatten().fieldErrors,
          },
          { status: 400 },
        );
      }
      parsed = result.data;

      const file = form.get("labs_pdf");
      if (file instanceof File && file.size > 0) {
        labsPdf = Buffer.from(await file.arrayBuffer());
      }
    } else {
      const body = await request.json();
      const result = newPatientSchema.safeParse(body);
      if (!result.success) {
        return NextResponse.json(
          {
            error: "Validation failed",
            details: result.error.flatten().fieldErrors,
          },
          { status: 400 },
        );
      }
      parsed = result.data;
    }

    const out = await createPatientWithAI(session.user.id, {
      firstName: parsed.firstName,
      lastName: parsed.lastName,
      age: parsed.age,
      gender: parsed.gender,
      admittime: parsed.admittime,
      noteText: parsed.noteText,
      vitals: parsed.vitals,
      labsPdf,
    });

    return NextResponse.json(
      { hadmId: out.hadmId, patientId: out.patient.id },
      { status: 201 },
    );
  } catch (err) {
    if (err instanceof AIAnalysisExecutionError) {
      return NextResponse.json(
        { error: err.message },
        { status: err.httpStatus },
      );
    }
    console.error("POST /api/patients error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
