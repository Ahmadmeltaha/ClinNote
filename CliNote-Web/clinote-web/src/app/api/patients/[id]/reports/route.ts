import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { z } from "zod";
import { authOptions } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";

const createReportSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(1).max(50_000),
  originalAI: z.string().optional(),
});

export async function GET(
  _request: NextRequest,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const { id: patientId } = await context.params;

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

    const reports = await prisma.report.findMany({
      where: { patientId },
      include: {
        author: { select: { id: true, name: true, email: true } },
      },
      orderBy: { createdAt: "desc" },
    });
    return NextResponse.json(reports);
  } catch (error) {
    console.error("GET /api/patients/[id]/reports error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

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
    const result = createReportSchema.safeParse(body);
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

    const report = await prisma.report.create({
      data: {
        patientId,
        authorId: session.user.id,
        title: data.title,
        content: data.content,
        originalAI: data.originalAI ?? null,
        status: "DRAFT",
      },
    });
    return NextResponse.json(report, { status: 201 });
  } catch (error) {
    console.error("POST /api/patients/[id]/reports error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
