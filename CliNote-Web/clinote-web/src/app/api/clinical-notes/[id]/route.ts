import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { z } from "zod";
import { authOptions } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";

const noteUpdateSchema = z.object({
  noteType: z
    .enum(["ADMISSION", "PROGRESS", "DISCHARGE", "CONSULTATION", "PROCEDURE"])
    .optional(),
  content: z.string().min(5).max(10_000).optional(),
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
    const result = noteUpdateSchema.safeParse(body);
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

    const updated = await prisma.clinicalNote.updateMany({
      where: { id, patient: { attendingDoctorId: session.user.id } },
      data: {
        ...(data.noteType !== undefined && { noteType: data.noteType }),
        ...(data.content !== undefined && { content: data.content }),
      },
    });

    if (updated.count === 0) {
      return NextResponse.json({ error: "Note not found" }, { status: 404 });
    }

    const note = await prisma.clinicalNote.findUnique({ where: { id } });
    return NextResponse.json(note);
  } catch (error) {
    console.error("PUT /api/clinical-notes/[id] error:", error);
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

    const deleted = await prisma.clinicalNote.deleteMany({
      where: { id, patient: { attendingDoctorId: session.user.id } },
    });

    if (deleted.count === 0) {
      return NextResponse.json({ error: "Note not found" }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("DELETE /api/clinical-notes/[id] error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
