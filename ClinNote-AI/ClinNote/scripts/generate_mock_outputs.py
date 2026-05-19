"""
Generate realistic mock output files for the ClinNote dashboard.

Writes 5 files to outputs/summaries/:
  - patient_12345_678901.json
  - patient_99999_111111.json
  - patient_list.json
  - cohort_overview.json
  - evaluation_metrics.json

Usage:
    python scripts/generate_mock_outputs.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs.paths import PATHS


def _patient_summary(subject_id, hadm_id, age, gender, admittime,
                     dischtime, los_days, mortality_prob, risk_level,
                     note_text, lab_anomalies, vital_anomalies,
                     vital_trends, alerts):
    return {
        "subject_id": subject_id,
        "hadm_id": hadm_id,
        "generated_at": "2026-01-15T14:22:00",
        "demographics": {
            "age": age,
            "gender": gender,
        },
        "admission_info": {
            "admittime": admittime,
            "dischtime": dischtime,
            "los_days": los_days,
        },
        "mortality_risk": {
            "probability": mortality_prob,
            "risk_level": risk_level,
        },
        "note_summary": note_text,
        "lab_anomalies": lab_anomalies,
        "vital_anomalies": vital_anomalies,
        "vital_trends": vital_trends,
        "alerts": alerts,
    }


# ── Patient 1: 67-year-old male, sepsis, HIGH risk ───────────────────────────
patient_1 = _patient_summary(
    subject_id=12345,
    hadm_id=678901,
    age=67,
    gender="M",
    admittime="2149-03-12T08:14:00",
    dischtime="2149-03-19T11:30:00",
    los_days=7.14,
    mortality_prob=0.42,
    risk_level="HIGH",
    note_text=(
        "67-year-old male with history of CKD stage 3 and type 2 diabetes "
        "presented with fever, hypotension, and altered mental status. "
        "Blood cultures positive for E. coli. Started on broad-spectrum "
        "antibiotics. ICU admission for hemodynamic support. Creatinine "
        "trending up from 2.1 to 3.8 mg/dL over 48 hours. Urine output "
        "decreasing. Nephrology consulted. Prognosis guarded."
    ),
    lab_anomalies=[
        {
            "label": "Creatinine",
            "value": 3.8,
            "unit": "mg/dL",
            "ref_range": "0.6-1.2",
            "flag": "HIGH",
            "severity": "critical",
        },
        {
            "label": "Lactate",
            "value": 4.2,
            "unit": "mmol/L",
            "ref_range": "0.5-2.2",
            "flag": "HIGH",
            "severity": "critical",
        },
        {
            "label": "WBC",
            "value": 18.4,
            "unit": "K/uL",
            "ref_range": "4.5-11.0",
            "flag": "HIGH",
            "severity": "warning",
        },
        {
            "label": "Sodium",
            "value": 129.0,
            "unit": "mEq/L",
            "ref_range": "136-145",
            "flag": "LOW",
            "severity": "warning",
        },
    ],
    vital_anomalies=[
        {
            "label": "Heart Rate",
            "value": 118.0,
            "unit": "bpm",
            "threshold": 100,
            "flag": "HIGH",
            "severity": "warning",
        },
        {
            "label": "SpO2",
            "value": 91.0,
            "unit": "%",
            "threshold": 94,
            "flag": "LOW",
            "severity": "critical",
        },
        {
            "label": "Systolic BP",
            "value": 82.0,
            "unit": "mmHg",
            "threshold": 90,
            "flag": "LOW",
            "severity": "critical",
        },
    ],
    vital_trends={
        "Heart Rate": {"trend": "increasing", "slope": 1.8, "r2": 0.84},
        "MAP": {"trend": "decreasing", "slope": -2.1, "r2": 0.76},
        "Temperature": {"trend": "stable", "slope": 0.02, "r2": 0.12},
    },
    alerts=[
        {
            "type": "mortality_risk",
            "severity": "critical",
            "message": "High mortality risk (42%). Immediate clinical review recommended.",
        },
        {
            "type": "lab_critical",
            "severity": "critical",
            "message": "Creatinine 3.8 mg/dL — severe AKI. Nephrology consult placed.",
        },
        {
            "type": "lab_critical",
            "severity": "critical",
            "message": "Lactate 4.2 mmol/L — septic shock pattern. Resuscitation protocol active.",
        },
        {
            "type": "vital_critical",
            "severity": "critical",
            "message": "SpO2 91% — supplemental oxygen increased. ABG ordered.",
        },
        {
            "type": "vital_critical",
            "severity": "critical",
            "message": "Systolic BP 82 mmHg — vasopressor support initiated.",
        },
    ],
)

# ── Patient 2: 52-year-old female, post-surgical, LOW risk ───────────────────
patient_2 = _patient_summary(
    subject_id=99999,
    hadm_id=111111,
    age=52,
    gender="F",
    admittime="2148-11-04T07:00:00",
    dischtime="2148-11-08T15:45:00",
    los_days=4.36,
    mortality_prob=0.06,
    risk_level="LOW",
    note_text=(
        "52-year-old female admitted for elective laparoscopic "
        "cholecystectomy. Procedure completed without complications. "
        "Post-operative pain managed with IV ketorolac and PO acetaminophen. "
        "Diet advanced on POD1. Ambulating independently on POD2. "
        "Wound inspection: clean, dry, intact. No signs of infection. "
        "Discharged home with instructions. Follow-up in 2 weeks."
    ),
    lab_anomalies=[
        {
            "label": "ALT",
            "value": 62.0,
            "unit": "U/L",
            "ref_range": "7-40",
            "flag": "HIGH",
            "severity": "warning",
        },
        {
            "label": "AST",
            "value": 55.0,
            "unit": "U/L",
            "ref_range": "10-40",
            "flag": "HIGH",
            "severity": "warning",
        },
    ],
    vital_anomalies=[],
    vital_trends={
        "Heart Rate": {"trend": "stable", "slope": -0.3, "r2": 0.08},
        "Systolic BP": {"trend": "stable", "slope": 0.5, "r2": 0.05},
        "Temperature": {"trend": "decreasing", "slope": -0.08, "r2": 0.61},
    },
    alerts=[
        {
            "type": "lab_warning",
            "severity": "warning",
            "message": "ALT/AST mildly elevated — expected post-cholecystectomy. Monitor trend.",
        },
    ],
)

# ── Patient list (overview table) ─────────────────────────────────────────────
patient_list = [
    {
        "subject_id": 12345,
        "hadm_id": 678901,
        "age": 67,
        "gender": "M",
        "admittime": "2149-03-12T08:14:00",
        "los_days": 7.14,
        "risk_level": "HIGH",
        "mortality_probability": 0.42,
        "primary_diagnosis": "Sepsis / AKI",
        "alert_count": 5,
    },
    {
        "subject_id": 99999,
        "hadm_id": 111111,
        "age": 52,
        "gender": "F",
        "admittime": "2148-11-04T07:00:00",
        "los_days": 4.36,
        "risk_level": "LOW",
        "mortality_probability": 0.06,
        "primary_diagnosis": "Elective cholecystectomy",
        "alert_count": 1,
    },
    {
        "subject_id": 10047,
        "hadm_id": 204884,
        "age": 74,
        "gender": "M",
        "admittime": "2150-06-21T13:30:00",
        "los_days": 5.75,
        "risk_level": "MEDIUM",
        "mortality_probability": 0.19,
        "primary_diagnosis": "COPD exacerbation",
        "alert_count": 3,
    },
    {
        "subject_id": 10063,
        "hadm_id": 298685,
        "age": 45,
        "gender": "F",
        "admittime": "2150-09-03T22:15:00",
        "los_days": 3.12,
        "risk_level": "LOW",
        "mortality_probability": 0.04,
        "primary_diagnosis": "Appendectomy",
        "alert_count": 0,
    },
    {
        "subject_id": 10088,
        "hadm_id": 312450,
        "age": 81,
        "gender": "M",
        "admittime": "2151-01-17T05:45:00",
        "los_days": 11.2,
        "risk_level": "HIGH",
        "mortality_probability": 0.58,
        "primary_diagnosis": "Acute MI / cardiogenic shock",
        "alert_count": 7,
    },
]

# ── Cohort overview ───────────────────────────────────────────────────────────
cohort_overview = {
    "generated_at": "2026-01-15T14:22:00",
    "cohort_size": 1258,
    "demographics": {
        "age_mean": 63.4,
        "age_std": 15.8,
        "age_min": 18,
        "age_max": 97,
        "gender_distribution": {"M": 672, "F": 586},
    },
    "admissions": {
        "los_mean_days": 6.9,
        "los_median_days": 4.8,
        "los_std_days": 7.2,
        "los_min_days": 0.5,
        "los_max_days": 61.3,
    },
    "mortality": {
        "in_hospital_deaths": 187,
        "survival": 1071,
        "mortality_rate": 0.1486,
    },
    "risk_distribution": {
        "HIGH": 214,
        "MEDIUM": 389,
        "LOW": 655,
    },
    "data_completeness": {
        "patients_with_notes": 1201,
        "patients_with_labs": 1258,
        "patients_with_vitals": 1147,
        "patients_with_all_modalities": 1089,
    },
}

# ── Evaluation metrics ────────────────────────────────────────────────────────
evaluation_metrics = {
    "generated_at": "2026-01-15T14:22:00",
    "model": "ClinNote Multimodal Fusion (DisentangledTransformer)",
    "dataset_split": {
        "train": 879,
        "validation": 189,
        "test": 190,
    },
    "mortality_prediction": {
        "auroc": 0.8641,
        "auprc": 0.7218,
        "accuracy": 0.8316,
        "sensitivity": 0.7742,
        "specificity": 0.8489,
        "f1_score": 0.7104,
        "brier_score": 0.1082,
        "threshold_used": 0.30,
    },
    "ablation": {
        "text_only":   {"auroc": 0.7821, "auprc": 0.6104},
        "labs_only":   {"auroc": 0.7542, "auprc": 0.5877},
        "vitals_only": {"auroc": 0.7215, "auprc": 0.5461},
        "text_labs":   {"auroc": 0.8293, "auprc": 0.6814},
        "full_fusion": {"auroc": 0.8641, "auprc": 0.7218},
    },
    "anomaly_detection": {
        "lab_anomaly_precision": 0.913,
        "lab_anomaly_recall": 0.887,
        "vital_anomaly_precision": 0.881,
        "vital_anomaly_recall": 0.859,
    },
    "training": {
        "epochs": 50,
        "best_epoch": 43,
        "optimizer": "AdamW",
        "learning_rate": 1e-4,
        "batch_size": 32,
        "early_stopping_patience": 8,
    },
}


def main():
    PATHS.ensure_output_dirs()
    summaries_dir = PATHS.summaries_dir

    files = {
        "patient_12345_678901.json": patient_1,
        "patient_99999_111111.json": patient_2,
        "patient_list.json": patient_list,
        "cohort_overview.json": cohort_overview,
        "evaluation_metrics.json": evaluation_metrics,
    }

    for filename, data in files.items():
        path = summaries_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Wrote {path}")

    print(f"\nAll mock outputs written to: {summaries_dir}")


if __name__ == "__main__":
    main()
