import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { z } from "zod";
import { authOptions } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";

const problemUpdateSchema = z.object({
  name: z.string().min(1).max(200).optional(),
  icdCode: z.string().max(20).optional().or(z.literal("")),
  status: z.enum(["ACTIVE", "RESOLVED", "CHRONIC"]).optional(),
  onsetDate: z.string().optional().or(z.literal("")),
});

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

    const body = await request.json();
    const result = problemUpdateSchema.safeParse(body);
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

    // Atomic ownership check: updateMany with a nested `where` on the
    // parent patient returns count=0 if no row matches (either wrong id
    // or the patient doesn't belong to this doctor).
    const updated = await prisma.problem.updateMany({
      where: { id, patient: { attendingDoctorId: session.user.id } },
      data: {
        ...(data.name !== undefined && { name: data.name }),
        ...(data.icdCode !== undefined && {
          icdCode: data.icdCode || null,
        }),
        ...(data.status !== undefined && { status: data.status }),
        ...(data.onsetDate !== undefined && {
          onsetDate: data.onsetDate ? new Date(data.onsetDate) : null,
        }),
      },
    });

    if (updated.count === 0) {
      return NextResponse.json(
        { error: "Problem not found" },
        { status: 404 },
      );
    }

    const problem = await prisma.problem.findUnique({ where: { id } });
    return NextResponse.json(problem);
  } catch (error) {
    console.error("PUT /api/problems/[id] error:", error);
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

    const deleted = await prisma.problem.deleteMany({
      where: { id, patient: { attendingDoctorId: session.user.id } },
    });

    if (deleted.count === 0) {
      return NextResponse.json(
        { error: "Problem not found" },
        { status: 404 },
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("DELETE /api/problems/[id] error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
