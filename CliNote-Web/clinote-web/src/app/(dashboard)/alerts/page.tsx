import { redirect } from "next/navigation";
import { getAuthSession } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";
import { AlertsList } from "@/components/alerts/AlertsList";
import type { Alert } from "@/types";

export const dynamic = "force-dynamic";

export default async function AlertsPage() {
  const session = await getAuthSession();
  if (!session?.user) redirect("/login");

  // ---------- True counts from the WHOLE alerts table (not capped at 500). ----------
  // Single groupBy keeps it to one DB round trip (Supabase pool limit = 1).
  const grouped = await prisma.alert.groupBy({
    by: ["priority", "isResolved"],
    _count: { _all: true },
  });

  const totalCounts = {
    activeTotal: 0,
    resolvedTotal: 0,
    critical: 0,
    warning: 0,
    info: 0,
  };
  for (const g of grouped) {
    const n = g._count._all;
    if (g.isResolved) {
      totalCounts.resolvedTotal += n;
    } else {
      totalCounts.activeTotal += n;
      if (g.priority === "CRITICAL") totalCounts.critical += n;
      else if (g.priority === "WARNING") totalCounts.warning += n;
      else if (g.priority === "INFO") totalCounts.info += n;
    }
  }

  const alerts = await prisma.alert.findMany({
    orderBy: [{ priority: "asc" }, { createdAt: "desc" }],
    take: 500,
    include: {
      patient: {
        select: {
          id: true,
          firstName: true,
          lastName: true,
          mrn: true,
          aiHadmId: true,
          aiSubjectId: true,
        },
      },
    },
  });

  const serialized = alerts.map(
    (a): Alert & {
      patient: { id: string; firstName: string; lastName: string; mrn: string };
    } => {
      const linkId = a.patient.aiHadmId
        ? String(a.patient.aiHadmId)
        : a.patient.id;
      const isDefault =
        a.patient.firstName === "Patient" &&
        a.patient.aiSubjectId != null &&
        a.patient.lastName === String(a.patient.aiSubjectId);
      const lastName = isDefault
        ? `${a.patient.aiSubjectId}`
        : a.patient.lastName;

      return {
        id: a.id,
        patientId: linkId,
        alertType: a.alertType,
        priority: a.priority,
        title: a.title,
        message: a.message,
        source: a.source ?? undefined,
        isResolved: a.isResolved,
        resolvedAt: a.resolvedAt?.toISOString(),
        resolvedBy: a.resolvedBy ?? undefined,
        createdAt: a.createdAt.toISOString(),
        patient: {
          id: linkId,
          firstName: a.patient.firstName,
          lastName,
          mrn: a.patient.mrn,
        },
      };
    },
  );

  return <AlertsList alerts={serialized} totalCounts={totalCounts} />;
}
