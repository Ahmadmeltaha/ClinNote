import Link from "next/link";
import { redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { getAuthSession } from "@/lib/server/auth";
import { CohortNewPatientForm } from "@/components/patients/CohortNewPatientForm";

export default async function NewPatientPage() {
  const session = await getAuthSession();
  if (!session?.user) redirect("/login");

  return (
    <div className="mx-auto w-full max-w-3xl">
      <Link
        href="/patients"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-600 transition-colors hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to patients
      </Link>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 sm:p-8">
        <div className="mb-5">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Add New Patient
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Enter the patient&apos;s demographics and any initial clinical data.
            The AI pipeline will generate a mortality risk, anomaly detection,
            and a clinical summary on submit.
          </p>
        </div>

        <CohortNewPatientForm />
      </div>
    </div>
  );
}
