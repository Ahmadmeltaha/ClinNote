import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { z } from "zod";
import { authOptions } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";

const problemSchema = z.object({
  name: z.string().min(1, "Name is required").max(200),
  icdCode: z.string().max(20).optional().or(z.literal("")),
  status: z.enum(["ACTIVE", "RESOLVED", "CHRONIC"]).default("ACTIVE"),
  onsetDate: z.string().optional().or(z.literal("")),
});

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const { id: patientId } = await context.params;

    // Verify ownership
    const patient = await prisma.patient.findUnique({
      where: { id: patientId },
      select: { attendingDoctorId: true },
    });
    if (!patient) {
      return NextResponse.json({ error: "Patient not found" }, { status: 404 });
    }
    if (patient.attendingDoctorId !== session.user.id) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const body = await request.json();
    const result = problemSchema.safeParse(body);
    if (!result.success) {
      return NextResponse.json(
        {
          error: "Validation failed",
          details: result.error.flatten().fieldErrors,
        },
        { status: 400 },
      );
    }
    const data = result.data;

    const problem = await prisma.problem.create({
      data: {
        patientId,
        name: data.name,
        icdCode: data.icdCode || null,
        status: data.status,
        onsetDate: data.onsetDate ? new Date(data.onsetDate) : null,
      },
    });

    return NextResponse.json(problem, { status: 201 });
  } catch (error) {
    console.error("POST /api/patients/[id]/problems error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
