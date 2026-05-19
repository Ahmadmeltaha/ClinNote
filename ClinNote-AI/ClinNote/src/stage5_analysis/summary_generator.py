"""
Stage 5 — Analysis: Clinical Summary Generator

Generates structured clinical summaries for each patient combining:
  - Key findings from the discharge note (extracted via ClinicalBERT attention)
  - Abnormal lab values with severity flags
  - Vital sign trends and abnormalities
  - Predicted mortality risk

Output format (dict → JSON for web dashboard):
    {
        "patient_id": "subject_id_hadm_id",
        "admission_date": "...",
        "discharge_date": "...",
        "predicted_mortality_risk": 0.12,
        "risk_level": "LOW",
        "key_diagnoses": ["Sepsis", "Acute kidney injury"],
        "abnormal_labs": [
            {"name": "Creatinine", "value": 3.2, "unit": "mg/dL", "severity": "HIGH"}
        ],
        "vital_alerts": [
            {"name": "Heart Rate", "value": 135, "status": "HIGH"}
        ],
        "summary_text": "...",
        "generated_at": "2026-03-24T..."
    }
"""

import logging
import re
from datetime import datetime

import pandas as pd              # Data access for labs and vitals

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """
    Generates structured clinical summaries for a patient admission.

    Parameters
    ----------
    include_text_excerpts : bool
        Whether to include excerpts from the clinical note.
    max_diagnoses : int
        Maximum number of diagnoses to include.
    max_abnormal_labs : int
        Maximum number of abnormal lab findings to report.
    """

    def __init__(
        self,
        include_text_excerpts: bool = True,
        max_diagnoses: int = 5,
        max_abnormal_labs: int = 10,
    ) -> None:
        self.include_text_excerpts = include_text_excerpts
        self.max_diagnoses = max_diagnoses
        self.max_abnormal_labs = max_abnormal_labs

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        subject_id: int,
        hadm_id: int,
        note_text: str,
        lab_features_df: pd.DataFrame,
        vitals_features_df: pd.DataFrame,
        mortality_prob: float,
        admittime: datetime | None = None,
        dischtime: datetime | None = None,
    ) -> dict:
        """
        Generate a complete structured clinical summary for one admission.

        Parameters
        ----------
        subject_id : int
            MIMIC-IV subject_id.
        hadm_id : int
            Hospital admission ID.
        note_text : str
            Cleaned discharge note text.
        lab_features_df : pd.DataFrame
            Latest lab values with abnormality flags.
        vitals_features_df : pd.DataFrame
            Vital sign summary statistics.
        mortality_prob : float
            Predicted in-hospital mortality probability from Stage 4.
        admittime : datetime | None
        dischtime : datetime | None

        Returns
        -------
        dict
            Structured clinical summary (JSON-serializable).
        """
        abnormal_labs = self._extract_abnormal_labs(lab_features_df)
        vital_alerts  = self._extract_vital_alerts(vitals_features_df)
        diagnoses     = self._extract_diagnoses_from_note(note_text)
        risk_level    = self._classify_risk(mortality_prob)
        summary_text  = self._build_summary_text(
            diagnoses, abnormal_labs, vital_alerts, mortality_prob
        )
        return {
            "patient_id"               : f"{subject_id}_{hadm_id}",
            "subject_id"               : subject_id,
            "hadm_id"                  : hadm_id,
            "admission_date"           : admittime.isoformat() if admittime else None,
            "discharge_date"           : dischtime.isoformat() if dischtime else None,
            "predicted_mortality_risk" : round(float(mortality_prob), 4),
            "risk_level"               : risk_level,
            "key_diagnoses"            : diagnoses[: self.max_diagnoses],
            "abnormal_labs"            : abnormal_labs[: self.max_abnormal_labs],
            "vital_alerts"             : vital_alerts,
            "summary_text"             : summary_text,
            "generated_at"             : datetime.utcnow().isoformat(),
        }

    def generate_batch(
        self,
        cohort_df: pd.DataFrame,
        notes_dict: dict[int, str],
        lab_df: pd.DataFrame,
        vitals_df: pd.DataFrame,
        mortality_probs: dict[int, float],
    ) -> list[dict]:
        """
        Generate summaries for all admissions in the cohort.

        Parameters
        ----------
        cohort_df : pd.DataFrame
            Cohort with subject_id, hadm_id, admittime, dischtime.
        notes_dict : dict[int, str]
            Mapping hadm_id → cleaned note text.
        lab_df : pd.DataFrame
            Preprocessed labs.
        vitals_df : pd.DataFrame
            Preprocessed vitals.
        mortality_probs : dict[int, float]
            Mapping hadm_id → predicted mortality probability.

        Returns
        -------
        list[dict]
            List of structured clinical summaries.
        """
        summaries = []
        for _, row in cohort_df.iterrows():
            hadm_id = int(row["hadm_id"])
            subject_id = int(row["subject_id"])
            note_text = notes_dict.get(hadm_id, "")
            adm_labs = lab_df[lab_df["hadm_id"] == hadm_id] if "hadm_id" in lab_df.columns else pd.DataFrame()
            adm_vitals = vitals_df[vitals_df["hadm_id"] == hadm_id] if "hadm_id" in vitals_df.columns else pd.DataFrame()
            mortality_prob = mortality_probs.get(hadm_id, 0.0)
            admittime = row.get("admittime") if "admittime" in row.index else None
            dischtime = row.get("dischtime") if "dischtime" in row.index else None
            try:
                summary = self.generate(
                    subject_id=subject_id,
                    hadm_id=hadm_id,
                    note_text=note_text,
                    lab_features_df=adm_labs,
                    vitals_features_df=adm_vitals,
                    mortality_prob=mortality_prob,
                    admittime=admittime,
                    dischtime=dischtime,
                )
                summaries.append(summary)
            except Exception as exc:
                logger.warning("Failed to generate summary for hadm_id=%s: %s", hadm_id, exc)
        return summaries

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_abnormal_labs(self, lab_features_df: pd.DataFrame) -> list[dict]:
        """Extract abnormal lab findings sorted by severity."""
        if lab_features_df.empty or "is_abnormal" not in lab_features_df.columns:
            return []
        abnormal = lab_features_df[lab_features_df["is_abnormal"] == True]
        if abnormal.empty:
            return []
        if "severity_score" in abnormal.columns:
            abnormal = abnormal.sort_values("severity_score", ascending=False)
        results = []
        for _, row in abnormal.iterrows():
            results.append({
                "name"    : row.get("label", "Unknown"),
                "value"   : row.get("valuenum", None),
                "unit"    : row.get("valueuom", ""),
                "severity": row.get("severity_score", None),
                "direction": (
                    "HIGH"
                    if row.get("valuenum", 0) > row.get("ref_range_upper", float("inf"))
                    else "LOW"
                ),
            })
        return results

    def _extract_vital_alerts(self, vitals_features_df: pd.DataFrame) -> list[dict]:
        """Extract vital sign measurements outside normal ranges."""
        from configs.data_config import VITAL_ITEMIDS
        if vitals_features_df.empty:
            return []
        normal_ranges = VITAL_ITEMIDS.normal_ranges()
        alerts = []
        if "vital_name" in vitals_features_df.columns and "valuenum" in vitals_features_df.columns:
            for vital_name, (lo, hi) in normal_ranges.items():
                v_data = vitals_features_df[vitals_features_df["vital_name"] == vital_name]
                if v_data.empty:
                    continue
                last_val = float(v_data["valuenum"].iloc[-1])
                if last_val < lo or last_val > hi:
                    alerts.append({
                        "name"  : vital_name,
                        "value" : last_val,
                        "status": "HIGH" if last_val > hi else "LOW",
                    })
        return alerts

    def _extract_diagnoses_from_note(self, note_text: str) -> list[str]:
        """
        Extract diagnoses from the discharge note using regex patterns.

        Looks for common sections: "Discharge Diagnoses:", "Final Diagnoses:".
        """
        if not note_text:
            return []
        patterns = [
            r"(?:Discharge Diagnoses?|Final Diagnoses?|Primary Diagnoses?|Diagnosis)[:\s]*\n((?:.+\n?)+?)(?:\n\n|\Z)",
            r"(?:DISCHARGE DIAGNOSES?|FINAL DIAGNOSES?|PRIMARY DIAGNOSES?|DIAGNOSIS)[:\s]*\n((?:.+\n?)+?)(?:\n\n|\Z)",
        ]
        diagnoses = []
        for pattern in patterns:
            match = re.search(pattern, note_text, re.IGNORECASE)
            if match:
                block = match.group(1)
                for line in block.strip().splitlines():
                    line = re.sub(r"^\s*[\d\.\-\*]+\s*", "", line).strip()
                    if line and len(line) > 3:
                        diagnoses.append(line)
                if diagnoses:
                    break
        return diagnoses

    def _classify_risk(self, mortality_prob: float) -> str:
        """
        Classify mortality risk into a human-readable level.

        Returns "LOW" (<0.10), "MEDIUM" (0.10–0.30), "HIGH" (>0.30).
        """
        if mortality_prob < 0.10:
            return "LOW"
        if mortality_prob < 0.30:
            return "MEDIUM"
        return "HIGH"

    def _build_summary_text(
        self,
        diagnoses: list[str],
        abnormal_labs: list[dict],
        vital_alerts: list[dict],
        mortality_prob: float,
    ) -> str:
        """Build a concise natural-language summary paragraph."""
        risk_level = self._classify_risk(mortality_prob)
        parts = []

        if diagnoses:
            diag_str = ", ".join(diagnoses[: self.max_diagnoses])
            parts.append(f"Key diagnoses include: {diag_str}.")

        if abnormal_labs:
            top_labs = abnormal_labs[: 3]
            lab_phrases = []
            for lab in top_labs:
                name = lab.get("name", "Unknown")
                value = lab.get("value")
                unit = lab.get("unit", "")
                direction = lab.get("direction", "")
                val_str = f"{value:.2f} {unit}".strip() if value is not None else "N/A"
                lab_phrases.append(f"{name} {val_str} ({direction})")
            parts.append(f"Notable lab findings: {'; '.join(lab_phrases)}.")

        if vital_alerts:
            alert_phrases = [
                f"{a['name']} {a['value']:.1f} ({a['status']})"
                for a in vital_alerts[:3]
            ]
            parts.append(f"Vital sign alerts: {'; '.join(alert_phrases)}.")

        risk_sentence = (
            f"Predicted in-hospital mortality risk is {mortality_prob * 100:.1f}% ({risk_level})."
        )
        parts.append(risk_sentence)

        return " ".join(parts)


if __name__ == "__main__":
    # generator = SummaryGenerator()
    # summary = generator.generate(
    #     subject_id=12345,
    #     hadm_id=678901,
    #     note_text="Patient presented with...",
    #     lab_features_df=lab_df,
    #     vitals_features_df=vitals_df,
    #     mortality_prob=0.15,
    # )
    # import json; print(json.dumps(summary, indent=2))
    pass
