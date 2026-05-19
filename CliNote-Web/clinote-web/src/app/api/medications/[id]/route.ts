import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { z } from "zod";
import { authOptions } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";

const medicationUpdateSchema = z.object({
  name: z.string().min(1).max(200).optional(),
  dose: z.string().max(100).optional().or(z.literal("")),
  route: z.string().max(50).optional().or(z.literal("")),
  frequency: z.string().max(100).optional().or(z.literal("")),
  startDate: z.string().optional().or(z.literal("")),
  endDate: z.string().optional().or(z.literal("")),
  isActive: z.boolean().optional(),
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
    const result = medicationUpdateSchema.safeParse(body);
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

    const updated = await prisma.medication.updateMany({
      where: { id, patient: { attendingDoctorId: session.user.id } },
      data: {
        ...(data.name !== undefined && { name: data.name }),
        ...(data.dose !== undefined && { dose: data.dose || null }),
        ...(data.route !== undefined && { route: data.route || null }),
        ...(data.frequency !== undefined && {
          frequency: data.frequency || null,
        }),
        ...(data.startDate !== undefined &&
          data.startDate && { startDate: new Date(data.startDate) }),
        ...(data.endDate !== undefined && {
          endDate: data.endDate ? new Date(data.endDate) : null,
        }),
        ...(data.isActive !== undefined && { isActive: data.isActive }),
      },
    });

    if (updated.count === 0) {
      return NextResponse.json(
        { error: "Medication not found" },
        { status: 404 },
      );
    }

    const medication = await prisma.medication.findUnique({ where: { id } });
    return NextResponse.json(medication);
  } catch (error) {
    console.error("PUT /api/medications/[id] error:", error);
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

    const deleted = await prisma.medication.deleteMany({
      where: { id, patient: { attendingDoctorId: session.user.id } },
    });

    if (deleted.count === 0) {
      return NextResponse.json(
        { error: "Medication not found" },
        { status: 404 },
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("DELETE /api/medications/[id] error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
