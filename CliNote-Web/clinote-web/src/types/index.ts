// ============================================================================
// APP / DATABASE TYPES (our Postgres schema via Prisma)
// ============================================================================

export interface User {
  id: string;
  email: string;
  name: string;
}

export interface Patient {
  id: string;
  mrn: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: "MALE" | "FEMALE";
  admissionDate: string;
  dischargeDate?: string;
  chiefComplaint?: string;
  attendingDoctorId: string;
  attendingDoctor?: User;
  createdAt: string;
}

export interface PatientWithDetails extends Patient {
  problems: Problem[];
  allergies: Allergy[];
  medications: Medication[];
  labResults: LabResult[];
  vitalSigns: VitalSign[];
  clinicalNotes: ClinicalNote[];
  aiSummaries: AISummary[];
  alerts: Alert[];
  reports: Report[];
}

export interface PatientListItem {
  id: string;
  mrn: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: "MALE" | "FEMALE";
  admissionDate: string;
  dischargeDate?: string | null;
  chiefComplaint?: string | null;
  riskLevel?: "LOW" | "MEDIUM" | "HIGH" | null;
  mortalityRisk?: number | null;
  alertCount: number;
  criticalAlertCount: number;
  primaryDiagnosis?: string | null;
}

export interface Problem {
  id: string;
  patientId: string;
  name: string;
  icdCode?: string;
  status: "ACTIVE" | "RESOLVED" | "CHRONIC";
  onsetDate?: string;
}

export interface Allergy {
  id: string;
  patientId: string;
  allergen: string;
  reaction?: string;
  severity: "MILD" | "MODERATE" | "SEVERE";
}

export interface Medication {
  id: string;
  patientId: string;
  name: string;
  dose?: string;
  route?: string;
  frequency?: string;
  startDate: string;
  endDate?: string;
  isActive: boolean;
}

export interface LabResult {
  id: string;
  patientId: string;
  testName: string;
  value: number;
  unit: string;
  refRangeLow?: number;
  refRangeHigh?: number;
  flag: "NORMAL" | "LOW" | "HIGH" | "CRITICAL_LOW" | "CRITICAL_HIGH";
  collectedAt: string;
}

export interface VitalSign {
  id: string;
  patientId: string;
  temperature?: number;
  heartRate?: number;
  bpSystolic?: number;
  bpDiastolic?: number;
  respiratoryRate?: number;
  spO2?: number;
  recordedAt: string;
}

export interface ClinicalNote {
  id: string;
  patientId: string;
  noteType: "ADMISSION" | "PROGRESS" | "DISCHARGE" | "CONSULTATION" | "PROCEDURE";
  content: string;
  author: string;
  noteDate: string;
}

export interface AISummary {
  id: string;
  patientId: string;
  summaryType: "COMPREHENSIVE" | "DISCHARGE" | "BRIEF";
  content: string;
  keyFindings?: string[];
  mortalityRisk?: number;
  riskLevel?: "LOW" | "MEDIUM" | "HIGH";
  confidenceInterval?: { lower: number; upper: number };
  modelUsed?: string;
  generatedAt: string;
}

export interface Alert {
  id: string;
  patientId: string;
  alertType: "LAB_ABNORMAL" | "VITAL_ABNORMAL" | "DRUG_INTERACTION" | "ALLERGY_CONFLICT" | "DISCREPANCY" | "TREND";
  priority: "CRITICAL" | "WARNING" | "INFO";
  title: string;
  message: string;
  source?: string;
  isResolved: boolean;
  resolvedAt?: string;
  resolvedBy?: string;
  createdAt: string;
}

export interface Report {
  id: string;
  patientId: string;
  authorId: string;
  author?: User;
  title: string;
  content: string;
  originalAI?: string;
  status: "DRAFT" | "PENDING_REVIEW" | "APPROVED" | "REJECTED";
  approvedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface DashboardStats {
  totalPatients: number;
  riskDistribution: { low: number; medium: number; high: number };
  avgMortalityRisk: number;
  totalCriticalAlerts: number;
  totalWarnings: number;
  recentAlerts: Alert[];
}

// ============================================================================
// AI PIPELINE TYPES (HTTP calls to http://localhost:5000 — Ahmad Jaber's API)
// ============================================================================

/** GET /api/health response. */
export interface HealthResponse {
  status: "ok";
  version: string;
  llm_loaded?: boolean;
  summaries_dir?: string;
}

/** Exact strings Ahmad's API expects in the multipart `vitals` JSON. */
export type AhmadVitalName =
  | "Heart Rate"
  | "Systolic Blood Pressure"
  | "Diastolic Blood Pressure"
  | "Mean Blood Pressure"
  | "SpO2"
  | "Respiratory Rate"
  | "Temperature Fahrenheit"
  | "Temperature Celsius";

export interface AhmadVitalEntry {
  name: AhmadVitalName;
  value: number;
}

/** Raw GET /api/patient/{hadm_id} response shape. */
export interface AhmadDashboardResponse {
  patient_id: string;
  subject_id: number;
  hadm_id: number;
  demographics: { age: number; gender: "M" | "F" };
  admission: { admittime: string; dischtime: string; los_days: number };
  diagnoses: string[];
  medications: string[];
  predicted_mortality: {
    probability: number;
    risk_level: "LOW" | "MEDIUM" | "HIGH";
  };
  lab_summary: {
    n_abnormal: number;
    top_abnormal: AhmadLabAbnormal[];
  };
  vital_summary: {
    alerts: AhmadVitalAlert[];
    trend_overview: Record<string, "INCREASING" | "DECREASING" | "STABLE">;
  };
  alerts: AhmadAlert[];
  clinical_summary: string;
  note_excerpt: string;
  generated_at: string;
  /** Present only on POST /api/patient/{hadm_id}/update responses. */
  update_diff?: AhmadUpdateDiff;
}

export interface AhmadLabAbnormal {
  name: string;
  value: number;
  unit: string;
  ref_low: number;
  ref_high: number;
  severity: number;
  direction: "HIGH" | "LOW";
}

export interface AhmadVitalAlert {
  vital_name: string;
  value: number;
  status: "HIGH" | "LOW";
  trend: "INCREASING" | "DECREASING" | "STABLE";
}

export interface AhmadAlert {
  type: "LAB" | "VITAL" | "MORTALITY";
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  message: string;
}

export interface AhmadUpdateDiff {
  old_probability: number;
  new_probability: number;
  risk_changed: boolean;
  old_risk: "LOW" | "MEDIUM" | "HIGH";
  new_risk: "LOW" | "MEDIUM" | "HIGH";
}

export interface AhmadPatientListResponse {
  total: number;
  patients: {
    subject_id: number;
    age: number;
    gender: "M" | "F";
    hadm_ids: number[];
    admissions: {
      hadm_id: number;
      risk_level: "LOW" | "MEDIUM" | "HIGH";
      probability: number;
      generated_at: string;
    }[];
  }[];
}

export interface AhmadParsedPdf {
  parse_success: boolean;
  n_extracted: number;
  labs: {
    name: string;
    value: number;
    unit: string;
    ref_low: number;
    ref_high: number;
  }[];
}

/**
 * Internal contract consumed by every UI component.
 * Translated from `AhmadDashboardResponse` via `ai-adapter.ts` so UI stays stable
 * even when Ahmad's API shape changes.
 */
export interface PatientResult {
  subject_id: number;
  hadm_id: number;
  generated_at: string;
  demographics: { age: number; gender: "M" | "F" };
  admission_info: {
    admittime: string;
    dischtime: string;
    los_days: number;
  };
  mortality_risk: {
    probability: number; // 0 to 1
    risk_level: "LOW" | "MEDIUM" | "HIGH";
  };
  note_summary: string;
  note_excerpt?: string;
  diagnoses?: string[];
  medications?: string[];
  lab_anomalies: {
    label: string;
    value: number;
    unit: string;
    ref_range: string;
    flag: "HIGH" | "LOW";
    severity: "critical" | "warning";
  }[];
  vital_anomalies: {
    label: string;
    value: number;
    unit: string;
    threshold: number;
    flag: "HIGH" | "LOW";
    severity: "critical" | "warning";
  }[];
  vital_trends: Record<
    string,
    {
      trend: "increasing" | "decreasing" | "stable";
      slope: number;
      r2: number;
    }
  >;
  alerts: {
    type: "mortality_risk" | "lab_critical" | "vital_critical" | "trend_alert";
    severity: "critical" | "warning";
    message: string;
  }[];
  update_diff?: AhmadUpdateDiff;
}

/** evaluation_metrics.json — for the Model Performance page. */
export interface EvaluationMetrics {
  mortality_prediction: {
    auroc: number;
    auprc: number;
    accuracy: number;
    sensitivity: number;
    specificity: number;
    f1_score: number;
  };
  ablation: Record<string, number>; // text_only, labs_only, vitals_only, full_fusion
  anomaly_detection: {
    lab: { precision: number; recall: number };
    vital: { precision: number; recall: number };
  };
  training: {
    epochs: number;
    best_epoch: number;
    optimizer: string;
    learning_rate: number;
  };
}

/** cohort_overview.json — aggregate stats for dashboard stats row. */
export interface CohortOverview {
  cohort_size: number;
  demographics: {
    age_mean: number;
    age_std: number;
    gender_distribution: Record<string, number>;
  };
  mortality: {
    in_hospital_deaths: number;
    survival: number;
    mortality_rate: number;
  };
  risk_distribution: { HIGH: number; MEDIUM: number; LOW: number };
  data_completeness: Record<string, number>;
}
