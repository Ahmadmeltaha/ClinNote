/**
 * Translation layer between Ahmad Jaber's raw API shape and our internal
 * `PatientResult` contract that every UI component consumes.
 *
 * If Ahmad changes his response shape later, this is the only file that needs
 * to change — UI components keep working unchanged.
 */

import type {
  AhmadAlert,
  AhmadDashboardResponse,
  AhmadLabAbnormal,
  AhmadVitalAlert,
  AhmadVitalEntry,
  AhmadVitalName,
  PatientResult,
} from "@/types";

/**
 * Subset of `VitalSign` fields we need — accepts `null` (Prisma) and `undefined`
 * (serialized internal type) interchangeably so callers can pass either shape.
 */
interface VitalSignInput {
  temperature?: number | null;
  heartRate?: number | null;
  bpSystolic?: number | null;
  bpDiastolic?: number | null;
  respiratoryRate?: number | null;
  spO2?: number | null;
}

export function translateAhmadResponse(
  ahmad: AhmadDashboardResponse,
): PatientResult {
  return {
    subject_id: ahmad.subject_id,
    hadm_id: ahmad.hadm_id,
    generated_at: ahmad.generated_at,
    demographics: ahmad.demographics,
    admission_info: {
      admittime: ahmad.admission.admittime,
      dischtime: ahmad.admission.dischtime,
      los_days: ahmad.admission.los_days,
    },
    mortality_risk: {
      probability: ahmad.predicted_mortality.probability,
      risk_level: ahmad.predicted_mortality.risk_level,
    },
    note_summary: ahmad.clinical_summary,
    note_excerpt: ahmad.note_excerpt,
    diagnoses: ahmad.diagnoses,
    medications: ahmad.medications,
    lab_anomalies: ahmad.lab_summary.top_abnormal.map(translateLab),
    vital_anomalies: ahmad.vital_summary.alerts.map(translateVitalAlert),
    vital_trends: translateTrendOverview(ahmad.vital_summary.trend_overview),
    alerts: ahmad.alerts.map(translateAlert),
    update_diff: ahmad.update_diff,
  };
}

function translateLab(lab: AhmadLabAbnormal): PatientResult["lab_anomalies"][number] {
  return {
    label: lab.name,
    value: lab.value,
    unit: lab.unit,
    ref_range: `${lab.ref_low}-${lab.ref_high}`,
    flag: lab.direction,
    severity: lab.severity > 0.5 ? "critical" : "warning",
  };
}

function translateVitalAlert(
  alert: AhmadVitalAlert,
): PatientResult["vital_anomalies"][number] {
  return {
    label: prettifyVitalName(alert.vital_name),
    value: alert.value,
    unit: lookupVitalUnit(alert.vital_name),
    threshold: 0,
    flag: alert.status,
    severity: deriveVitalSeverity(alert.vital_name, alert.value, alert.status),
  };
}

function translateTrendOverview(
  trends: Record<string, "INCREASING" | "DECREASING" | "STABLE">,
): PatientResult["vital_trends"] {
  const out: PatientResult["vital_trends"] = {};
  for (const [key, ahmadTrend] of Object.entries(trends)) {
    out[key] = {
      trend:
        ahmadTrend === "INCREASING"
          ? "increasing"
          : ahmadTrend === "DECREASING"
            ? "decreasing"
            : "stable",
      slope: 0,
      r2: 0,
    };
  }
  return out;
}

function translateAlert(alert: AhmadAlert): PatientResult["alerts"][number] {
  return {
    type:
      alert.type === "LAB"
        ? "lab_critical"
        : alert.type === "VITAL"
          ? "vital_critical"
          : alert.type === "MORTALITY"
            ? "mortality_risk"
            : "trend_alert",
    severity:
      alert.severity === "CRITICAL" || alert.severity === "HIGH"
        ? "critical"
        : "warning",
    message: alert.message,
  };
}

// ────────────────────────────────────────────────────────────────────────────
// Vital name + unit dictionaries (mirror README_API.md)
// ────────────────────────────────────────────────────────────────────────────

const VITAL_DISPLAY: Record<string, string> = {
  heart_rate: "Heart Rate",
  systolic_bp: "Systolic BP",
  diastolic_bp: "Diastolic BP",
  mean_bp: "Mean BP",
  spo2: "SpO2",
  respiratory_rate: "Respiratory Rate",
  temperature_f: "Temperature (°F)",
  temperature_c: "Temperature (°C)",
};

const VITAL_UNITS: Record<string, string> = {
  heart_rate: "bpm",
  systolic_bp: "mmHg",
  diastolic_bp: "mmHg",
  mean_bp: "mmHg",
  spo2: "%",
  respiratory_rate: "breaths/min",
  temperature_f: "°F",
  temperature_c: "°C",
};

function prettifyVitalName(snake: string): string {
  return (
    VITAL_DISPLAY[snake] ??
    snake.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

function lookupVitalUnit(snake: string): string {
  return VITAL_UNITS[snake] ?? "";
}

function deriveVitalSeverity(
  vitalName: string,
  value: number,
  status: "HIGH" | "LOW",
): "critical" | "warning" {
  switch (vitalName) {
    case "spo2":
      return value < 90 ? "critical" : "warning";
    case "heart_rate":
      return value < 50 || value > 130 ? "critical" : "warning";
    case "systolic_bp":
      return value < 90 || value > 180 ? "critical" : "warning";
    case "respiratory_rate":
      return value < 8 || value > 30 ? "critical" : "warning";
    case "temperature_c":
      return value < 35 || value > 39.5 ? "critical" : "warning";
    case "temperature_f":
      return value < 95 || value > 103 ? "critical" : "warning";
    default:
      return status === "HIGH" || status === "LOW" ? "warning" : "warning";
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Outbound translation: our DB VitalSign rows → Ahmad's vitals JSON shape
// ────────────────────────────────────────────────────────────────────────────

/**
 * Take our latest VitalSign row (assumed to be sorted by `recordedAt` desc) and
 * emit one `AhmadVitalEntry` per non-null field, using the EXACT name strings
 * Ahmad's API requires.
 *
 * Pass an array — we use the first entry (most recent). Returns `[]` if the
 * input is empty or all fields are null.
 */
export function wideVitalsToAhmadArray(
  vitals: VitalSignInput[],
): AhmadVitalEntry[] {
  const latest = vitals[0];
  if (!latest) return [];
  const out: AhmadVitalEntry[] = [];
  pushIfPresent(out, "Heart Rate", latest.heartRate);
  pushIfPresent(out, "Systolic Blood Pressure", latest.bpSystolic);
  pushIfPresent(out, "Diastolic Blood Pressure", latest.bpDiastolic);
  pushIfPresent(out, "Respiratory Rate", latest.respiratoryRate);
  pushIfPresent(out, "SpO2", latest.spO2);
  pushIfPresent(out, "Temperature Celsius", latest.temperature);
  return out;
}

function pushIfPresent(
  out: AhmadVitalEntry[],
  name: AhmadVitalName,
  value: number | null | undefined,
) {
  if (value != null) out.push({ name, value });
}
