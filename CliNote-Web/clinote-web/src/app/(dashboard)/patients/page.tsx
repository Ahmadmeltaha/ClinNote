import Link from "next/link";
import { redirect } from "next/navigation";
import { ArrowLeft, Eye, RefreshCw } from "lucide-react";
import { getAuthSession } from "@/lib/server/auth";
import { getCohortFromDB } from "@/lib/server/cohort";
import { CohortPatientList } from "@/components/patients/CohortPatientList";

type Action = "view" | "update";

export const dynamic = "force-dynamic";

export default async function PatientsPage({
  searchParams,
}: {
  searchParams: Promise<{ action?: string }>;
}) {
  const session = await getAuthSession();
  if (!session?.user) redirect("/login");

  const { action: actionRaw } = await searchParams;
  const action: Action = actionRaw === "update" ? "update" : "view";

  const cohort = await getCohortFromDB();

  const isUpdate = action === "update";

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1.5 text-sm text-slate-600 transition-colors hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to dashboard
      </Link>

      <div className="flex items-start gap-4">
        <div
          className={
            "inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl " +
            (isUpdate
              ? "bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400"
              : "bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400")
          }
        >
          {isUpdate ? (
            <RefreshCw className="h-6 w-6" />
          ) : (
            <Eye className="h-6 w-6" />
          )}
        </div>
        <div className="flex-1">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
            {isUpdate ? "Case 2" : "Case 1"}
          </p>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {isUpdate ? "Update a patient" : "View a patient"}
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {isUpdate
              ? "Search the cohort and pick an admission to add new clinical data."
              : "Search the cohort and pick an admission to open its AI dashboard."}
          </p>
        </div>
      </div>

      {cohort.patients.length === 0 ? (
        <EmptyCohortNotice />
      ) : (
        <CohortPatientList
          patients={cohort.patients}
          action={action}
          totalCount={cohort.total}
        />
      )}
    </div>
  );
}

function EmptyCohortNotice() {
  return (
    <div className="rounded-2xl border border-dashed border-amber-300 bg-amber-50 p-8 text-center dark:border-amber-800 dark:bg-amber-950/30">
      <h3 className="text-base font-semibold text-amber-900 dark:text-amber-200">
        Database is empty
      </h3>
      <p className="mt-1 text-sm text-amber-800 dark:text-amber-300">
        Import the cohort first by running
        <code className="mx-1 rounded bg-amber-100 px-1.5 py-0.5 font-mono text-xs dark:bg-amber-900/60">
          node scripts/import-cohort.mjs
        </code>
        — it pulls all patients from Ahmad&apos;s summary folder into Supabase.
      </p>
    </div>
  );
}
