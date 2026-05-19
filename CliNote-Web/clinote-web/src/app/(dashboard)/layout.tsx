import { redirect } from "next/navigation";
import { getAuthSession } from "@/lib/server/auth";
import { prisma } from "@/lib/server/prisma";
import { MainLayout } from "@/components/layout/MainLayout";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getAuthSession();

  if (!session?.user) {
    redirect("/login");
  }

  // Critical-priority unresolved alerts across the cohort — used for the
  // sidebar badge. Reads from Supabase (the importer seeded all of Ahmad's
  // cohort alerts into our DB).
  let alertCount = 0;
  try {
    alertCount = await prisma.alert.count({
      where: { isResolved: false, priority: "CRITICAL" },
    });
  } catch {
    alertCount = 0;
  }

  return (
    <MainLayout userName={session.user.name} alertCount={alertCount}>
      {children}
    </MainLayout>
  );
}
