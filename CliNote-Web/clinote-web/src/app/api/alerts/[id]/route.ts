import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { z } from "zod";
import { authOptions } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";

const updateSchema = z.object({
  isResolved: z.boolean(),
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
    const { isResolved } = result.data;

    const updated = await prisma.alert.updateMany({
      where: { id, patient: { attendingDoctorId: session.user.id } },
      data: {
        isResolved,
        resolvedAt: isResolved ? new Date() : null,
        resolvedBy: isResolved ? session.user.name : null,
      },
    });

    if (updated.count === 0) {
      return NextResponse.json({ error: "Alert not found" }, { status: 404 });
    }

    const alert = await prisma.alert.findUnique({ where: { id } });
    return NextResponse.json(alert);
  } catch (error) {
    console.error("PUT /api/alerts/[id] error:", error);
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

    const deleted = await prisma.alert.deleteMany({
      where: { id, patient: { attendingDoctorId: session.user.id } },
    });

    if (deleted.count === 0) {
      return NextResponse.json({ error: "Alert not found" }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("DELETE /api/alerts/[id] error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
