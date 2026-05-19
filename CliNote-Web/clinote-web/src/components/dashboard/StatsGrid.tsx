"use client";

import { Users, AlertTriangle, Activity, Bell } from "lucide-react";
import { StatsCard } from "@/components/dashboard/StatsCard";

interface StatsGridProps {
  totalPatients: number;
  highRiskCount: number;
  avgMortalityRisk: number | null;
  criticalAlertCount: number;
  warningAlertCount: number;
}

function formatPercent(value: number | null): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

export function StatsGrid({
  totalPatients,
  highRiskCount,
  avgMortalityRisk,
  criticalAlertCount,
  warningAlertCount,
}: StatsGridProps) {
  const highRiskPct =
    totalPatients > 0
      ? `${Math.round((highRiskCount / totalPatients) * 100)}% of patients`
      : "—";

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatsCard
        title="Total Patients"
        value={totalPatients}
        icon={Users}
        accentColor="blue"
      />
      <StatsCard
        title="High Risk"
        value={highRiskCount}
        subtitle={highRiskPct}
        icon={AlertTriangle}
        accentColor="red"
      />
      <StatsCard
        title="Avg Mortality Risk"
        value={formatPercent(avgMortalityRisk)}
        subtitle={
          avgMortalityRisk == null ? "No analyses yet" : "Across analyzed patients"
        }
        icon={Activity}
        accentColor="amber"
      />
      <StatsCard
        title="Critical Alerts"
        value={criticalAlertCount}
        subtitle={`${warningAlertCount} warning${warningAlertCount === 1 ? "" : "s"} active`}
        icon={Bell}
        accentColor="red"
      />
    </div>
  );
}
