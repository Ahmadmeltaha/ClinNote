/**
 * GET / PUT / DELETE /api/reports/[id]
 *
 * Status transitions enforced (M31):
 *   DRAFT            → PENDING_REVIEW       (submit)
 *   DRAFT            → DRAFT                (just edit content/title)
 *   PENDING_REVIEW   → APPROVED             (approve, sets approvedAt)
 *   PENDING_REVIEW   → REJECTED             (reject; reason passed via content prefix)
 *   PENDING_REVIEW   → DRAFT                (withdraw — also allowed)
 *   APPROVED         → (locked, no further edits)
 *   REJECTED         → DRAFT                (re-edit)
 */
import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { z } from "zod";
import { authOptions } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";
import type { ReportStatus } from "@prisma/client";

const updateSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  content: z.string().min(1).max(50_000).optional(),
  status: z
    .enum(["DRAFT", "PENDING_REVIEW", "APPROVED", "REJECTED"])
    .optional(),
  rejectionReason: z.string().max(2000).optional(),
});

const ALLOWED_TRANSITIONS: Record<ReportStatus, ReportStatus[]> = {
  DRAFT: ["DRAFT", "PENDING_REVIEW"],
  PENDING_REVIEW: ["DRAFT", "APPROVED", "REJECTED"],
  APPROVED: [], // locked
  REJECTED: ["DRAFT"],
};

async function loadOwnedReport(id: string, doctorId: string) {
  const report = await prisma.report.findUnique({
    where: { id },
    include: { patient: { select: { attendingDoctorId: true } } },
  });
  if (!report) return { error: 404 as const };
  if (report.patient.attendingDoctorId !== doctorId) return { error: 403 as const };
  return { report };
}

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

    const check = await loadOwnedReport(id, session.user.id);
    if (check.error === 404) {
      return NextResponse.json({ error: "Report not found" }, { status: 404 });
    }
    if (check.error === 403) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const full = await prisma.report.findUnique({
      where: { id },
      include: {
        author: { select: { id: true, name: true, email: true } },
        patient: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            mrn: true,
            dateOfBirth: true,
            gender: true,
          },
        },
      },
    });
    return NextResponse.json(full);
  } catch (error) {
    console.error("GET /api/reports/[id] error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const { id } = await context.params;

    const check = await loadOwnedReport(id, session.user.id);
    if (check.error === 404) {
      return NextResponse.json({ error: "Report not found" }, { status: 404 });
    }
    if (check.error === 403) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
    const current = check.report;

    const body = await request.json();
    const result = updateSchema.safeParse(body);
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

    // Block any edits to APPROVED reports
    if (current.status === "APPROVED") {
      return NextResponse.json(
        { error: "Approved reports are locked and cannot be edited." },
        { status: 409 },
      );
    }

    // Validate status transition if status is changing
    let newStatus: ReportStatus = current.status;
    if (data.status && data.status !== current.status) {
      const allowed = ALLOWED_TRANSITIONS[current.status];
      if (!allowed.includes(data.status)) {
        return NextResponse.json(
          {
            error: `Cannot transition from ${current.status} to ${data.status}.`,
          },
          { status: 409 },
        );
      }
      newStatus = data.status;
    }

    // For REJECTED transitions, prepend rejection reason to content
    let newContent = data.content ?? current.content;
    if (newStatus === "REJECTED" && data.rejectionReason) {
      const reasonNote = `[REJECTED on ${new Date().toISOString()} by ${session.user.name}: ${data.rejectionReason}]\n\n`;
      newContent = reasonNote + newContent;
    }

    const updated = await prisma.report.update({
      where: { id },
      data: {
        ...(data.title !== undefined && { title: data.title }),
        content: newContent,
        status: newStatus,
        ...(newStatus === "APPROVED" && { approvedAt: new Date() }),
      },
      include: {
        author: { select: { id: true, name: true, email: true } },
        patient: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            mrn: true,
          },
        },
      },
    });

    return NextResponse.json(updated);
  } catch (error) {
    console.error("PUT /api/reports/[id] error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function DELETE(
  _request: NextRequest,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const { id } = await context.params;

    const check = await loadOwnedReport(id, session.user.id);
    if (check.error === 404) {
      return NextResponse.json({ error: "Report not found" }, { status: 404 });
    }
    if (check.error === 403) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    await prisma.report.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("DELETE /api/reports/[id] error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
