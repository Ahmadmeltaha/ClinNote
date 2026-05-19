import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";
import type { AlertPriority } from "@prisma/client";

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const priorityParam = searchParams.get("priority");
    const resolvedParam = searchParams.get("resolved");
    const patientIdParam = searchParams.get("patientId");

    const validPriorities: AlertPriority[] = ["CRITICAL", "WARNING", "INFO"];
    const priority =
      priorityParam && validPriorities.includes(priorityParam as AlertPriority)
        ? (priorityParam as AlertPriority)
        : undefined;

    const isResolved =
      resolvedParam === "true"
        ? true
        : resolvedParam === "false"
          ? false
          : undefined;

    const alerts = await prisma.alert.findMany({
      where: {
        patient: { attendingDoctorId: session.user.id },
        ...(priority && { priority }),
        ...(isResolved !== undefined && { isResolved }),
        ...(patientIdParam && { patientId: patientIdParam }),
      },
      include: {
        patient: {
          select: { id: true, firstName: true, lastName: true, mrn: true },
        },
      },
      orderBy: { createdAt: "desc" },
    });

    // Sort: CRITICAL > WARNING > INFO, then by createdAt desc
    const rank = { CRITICAL: 0, WARNING: 1, INFO: 2 };
    alerts.sort((a, b) => {
      const r = rank[a.priority] - rank[b.priority];
      if (r !== 0) return r;
      return b.createdAt.getTime() - a.createdAt.getTime();
    });

    return NextResponse.json(alerts);
  } catch (error) {
    console.error("GET /api/alerts error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
