"""
Stage 6 — Clinical Output: Patient Summary Builder

Assembles the final structured patient summary by aggregating outputs from
Stage 5 (anomaly detection, trend analysis, summary generation) into a
single JSON-serializable dict that is stored and served to the web dashboard.

Schema (JSON):
{
  "patient_id"         : "12345_678901",
  "subject_id"         : 12345,
  "hadm_id"            : 678901,
  "demographics"       : { "age": 67, "gender": "M" },
  "admission"          : { "admittime": "...", "dischtime": "...", "los_days": 5.2 },
  "diagnoses"          : ["Sepsis", "AKI"],
  "medications"        : ["Vancomycin", "Norepinephrine"],
  "predicted_mortality": { "probability": 0.18, "risk_level": "MEDIUM" },
  "lab_summary"        : { "n_abnormal": 4, "top_abnormal": [...] },
  "vital_summary"      : { "alerts": [...], "trend_overview": {...} },
  "clinical_summary"   : "Patient admitted with sepsis ...",
  "generated_at"       : "2026-03-24T12:00:00"
}
"""

import logging
from datetime import datetime

import pandas as pd  # Data access

logger = logging.getLogger(__name__)


class PatientSummaryBuilder:
    """
    Builds the complete structured patient summary for one admission.

    Parameters
    ----------
    include_medications : bool
        Whether to extract medications from the discharge note.
    include_diagnoses : bool
        Whether to extract ICD diagnoses.
    """

    def __init__(
        self,
        include_medications: bool = True,
        include_diagnoses: bool = True,
    ) -> None:
        self.include_medications = include_medications
        self.include_diagnoses = include_diagnoses

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        subject_id: int,
        hadm_id: int,
        demographics: dict,
        admission_info: dict,
        note_text: str,
        lab_anomalies: list[dict],
        vital_anomalies: list[dict],
        vital_trends: dict,
        mortality_result: dict,
        diagnoses_df: pd.DataFrame | None = None,
        prescriptions_df: pd.DataFrame | None = None,
    ) -> dict:
        """
        Build the complete patient summary dict.

        Parameters
        ----------
        subject_id : int
        hadm_id : int
        demographics : dict
            {"age": int, "gender": str}
        admission_info : dict
            {"admittime": str, "dischtime": str, "los_days": float}
        note_text : str
            Cleaned discharge note.
        lab_anomalies : list[dict]
            Output of AnomalyDetector.detect_lab_anomalies().
        vital_anomalies : list[dict]
            Output of AnomalyDetector.detect_vital_anomalies().
        vital_trends : dict
            Output of TrendAnalyzer.analyze_vital_trends().
        mortality_result : dict
            {"probability": float, "risk_level": str}
        diagnoses_df : pd.DataFrame | None
            Rows from diagnoses_icd for this admission.
        prescriptions_df : pd.DataFrame | None
            Rows from prescriptions for this admission.

        Returns
        -------
        dict
            Complete JSON-serializable patient summary.
        """
        diagnoses   = self._extract_diagnoses(diagnoses_df)   if (self.include_diagnoses   and diagnoses_df   is not None) else []
        medications = self._extract_medications(prescriptions_df) if (self.include_medications and prescriptions_df is not None) else []
        summary_text = self._build_summary_text(
            demographics, admission_info, diagnoses, lab_anomalies, vital_anomalies, mortality_result
        )
        return {
            "patient_id"          : f"{subject_id}_{hadm_id}",
            "subject_id"          : subject_id,
            "hadm_id"             : hadm_id,
            "demographics"        : demographics,
            "admission"           : admission_info,
            "diagnoses"           : diagnoses,
            "medications"         : medications,
            "predicted_mortality" : mortality_result,
            "lab_summary"         : {
                "n_abnormal"  : len(lab_anomalies),
                "top_abnormal": lab_anomalies[:10],
            },
            "vital_summary"       : {
                "alerts"        : vital_anomalies,
                "trend_overview": vital_trends,
            },
            "clinical_summary"    : summary_text,
            "note_excerpt"        : note_text[:500] if note_text else "",
            "generated_at"        : datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_diagnoses(self, diagnoses_df: pd.DataFrame) -> list[str]:
        """Extract ICD diagnosis descriptions for this admission."""
        if diagnoses_df.empty:
            return []
        col = "long_title" if "long_title" in diagnoses_df.columns else (
              "icd_code"   if "icd_code"   in diagnoses_df.columns else None)
        if col is None:
            return []
        return diagnoses_df[col].dropna().astype(str).tolist()

    def _extract_medications(self, prescriptions_df: pd.DataFrame) -> list[str]:
        """Extract unique medication names from the prescriptions table."""
        if prescriptions_df.empty:
            return []
        col = "drug" if "drug" in prescriptions_df.columns else None
        if col is None:
            return []
        return sorted(prescriptions_df[col].dropna().astype(str).unique().tolist())

    def _build_summary_text(
        self,
        demographics: dict,
        admission_info: dict,
        diagnoses: list[str],
        lab_anomalies: list[dict],
        vital_anomalies: list[dict],
        mortality_result: dict,
    ) -> str:
        """Assemble a plain-English clinical summary paragraph."""
        parts = []
        age    = demographics.get("age", "unknown")
        gender = demographics.get("gender", "unknown")
        los    = admission_info.get("los_days")
        los_str = f"{los:.1f} days" if los is not None else "unknown duration"
        parts.append(f"{age}-year-old {gender} patient admitted for {los_str}.")

        if diagnoses:
            parts.append(f"Diagnoses: {', '.join(diagnoses[:3])}.")

        if lab_anomalies:
            top = lab_anomalies[0]
            parts.append(
                f"Most critical lab: {top['name']} {top['value']} ({top['direction']}, severity {top['severity']:.2f})."
            )

        if vital_anomalies:
            alerts = [f"{v['vital_name']} {v['status']}" for v in vital_anomalies[:2]]
            parts.append(f"Vital alerts: {', '.join(alerts)}.")

        prob     = mortality_result.get("probability", 0.0)
        risk_lvl = mortality_result.get("risk_level", "UNKNOWN")
        parts.append(f"Predicted in-hospital mortality: {prob*100:.1f}% ({risk_lvl}).")
        return " ".join(parts)


if __name__ == "__main__":
    # builder = PatientSummaryBuilder()
    # summary = builder.build(...)
    # import json; print(json.dumps(summary, indent=2, default=str))
    pass
