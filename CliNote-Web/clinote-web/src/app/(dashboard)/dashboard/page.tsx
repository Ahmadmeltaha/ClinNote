import { redirect } from "next/navigation";
import { UserPlus, Eye, RefreshCw } from "lucide-react";
import { getAuthSession } from "@/lib/server/auth";
import { ActionCard } from "@/components/dashboard/ActionCard";

export default async function DashboardPage() {
  const session = await getAuthSession();
  if (!session?.user) redirect("/login");

  const firstName = session.user.name.split(" ")[0];

  return (
    <div className="relative space-y-10">
      {/* Soft gradient backdrop */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-12 left-1/2 -z-10 h-72 w-[120%] -translate-x-1/2 rounded-full bg-gradient-to-r from-emerald-200/40 via-blue-200/40 to-amber-200/40 blur-3xl dark:from-emerald-900/20 dark:via-blue-900/20 dark:to-amber-900/20"
      />

      {/* Hero */}
      <div className="animate-cn-fade-up space-y-2 pt-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
          ClinNote
        </p>
        <h1 className="bg-gradient-to-br from-slate-900 to-slate-600 bg-clip-text text-3xl font-bold text-transparent dark:from-slate-50 dark:to-slate-300 sm:text-4xl">
          Welcome back, Dr. {firstName}
        </h1>
        <p className="max-w-2xl text-sm text-slate-500 dark:text-slate-400 sm:text-base">
          What would you like to do today? Pick one of the three clinical
          workflows below.
        </p>
      </div>

      {/* 3 action cards — staggered fade-up entrance */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="animate-cn-fade-up-lg" style={{ animationDelay: "60ms" }}>
          <ActionCard
            accent="emerald"
            icon={UserPlus}
            title="Add Patient"
            description="Create a brand new admission with demographics, a clinical note, vitals, and an optional lab PDF. The AI runs analysis on submit."
            cta="Start"
            href="/patients/new"
          />
        </div>
        <div className="animate-cn-fade-up-lg" style={{ animationDelay: "120ms" }}>
          <ActionCard
            accent="blue"
            icon={Eye}
            title="View Patient"
            description="Search for an existing patient by subject ID or admission ID and open their AI-generated dashboard."
            cta="Search"
            href="/patients?action=view"
          />
        </div>
        <div className="animate-cn-fade-up-lg" style={{ animationDelay: "180ms" }}>
          <ActionCard
            accent="amber"
            icon={RefreshCw}
            title="Update Patient"
            description="Find a patient, add new clinical data — note, vitals, or labs — and trigger a fresh AI analysis."
            cta="Search"
            href="/patients?action=update"
          />
        </div>
      </div>

      {/* Footer hint */}
      <p
        className="animate-cn-fade text-center text-xs text-slate-400 dark:text-slate-500"
        style={{ animationDelay: "300ms" }}
      >
        Need cohort-wide numbers? Check{" "}
        <a
          href="/statistics"
          className="font-medium text-blue-600 hover:underline dark:text-blue-400"
        >
          Statistics
        </a>{" "}
        in the sidebar.
      </p>
    </div>
  );
}
