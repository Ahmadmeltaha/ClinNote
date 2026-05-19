/**
 * GET /api/patients/[hadmId] — fetch a single admission dashboard from Ahmad's API.
 *
 * The route param `[id]` is now a hadm_id (numeric string), not a Prisma cuid.
 * This calls Ahmad's `GET /api/patient/{hadm_id}` which can take 1–3 minutes
 * because his code regenerates the LLM summary on every request.
 */
import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/server/auth";
import { getAhmadPatientDashboard } from "@/lib/server/ai-pipeline";

// Allow up to 5 minutes — Ahmad's GET endpoint regenerates Phi-3.5 every call.
export const maxDuration = 300;

export async function GET(
  _request: NextRequest,
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

    const dashboard = await getAhmadPatientDashboard(hadmId);
    return NextResponse.json(dashboard);
  } catch (error) {
    console.error("GET /api/patients/[id] error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
