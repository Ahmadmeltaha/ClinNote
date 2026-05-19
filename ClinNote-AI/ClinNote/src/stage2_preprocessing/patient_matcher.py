"""
Stage 2 - Preprocessing: Patient ID Matcher

Ensures consistent patient linkage across all four data sources:
    patients_final.csv  : subject_id + hadm_id (demographics + mortality label)
    clinical_notes.csv  : subject_id + hadm_id
    labs_final.csv      : subject_id + hadm_id
    vital_signs.csv     : subject_id + hadm_id + stay_id

Finds the intersection of subject_ids across all 4 DataFrames,
filters each to matched patients, encodes demographics, and fills nulls.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


class PatientMatcher:
    """
    Validates and aligns patient identifiers across all data sources.

    Parameters
    ----------
    icu_stay_selection : str
        When a patient has multiple ICU stays within one admission,
        which to select:
        - "first"   : earliest intime
        - "longest" : highest los (length of stay)
    """

    KEEP_COLS = [
        "subject_id", "hadm_id", "gender", "anchor_age", "race",
        "marital_status", "insurance", "anchor_year", "anchor_year_group",
        "hospital_expire_flag",
    ]

    def __init__(self, icu_stay_selection: str = "first") -> None:
        if icu_stay_selection not in ("first", "longest"):
            raise ValueError("icu_stay_selection must be 'first' or 'longest'")
        self.icu_stay_selection = icu_stay_selection

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match(
        self,
        patients_df: pd.DataFrame,
        notes_df: pd.DataFrame,
        labs_df: pd.DataFrame,
        vitals_df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, set[int]]:
        """
        Find the intersection of subject_ids across all 4 DataFrames.

        Filters each DataFrame to only matched subject_ids, encodes
        demographics, and fills null values in categorical columns.

        Parameters
        ----------
        patients_df : pd.DataFrame
            Patients DataFrame from PatientLoader.load().
        notes_df : pd.DataFrame
            Notes DataFrame from NotesLoader.load() (or cleaned).
        labs_df : pd.DataFrame
            Labs DataFrame from LabsLoader.load() (or cleaned).
        vitals_df : pd.DataFrame
            Vitals DataFrame from VitalsLoader.load() (or cleaned).

        Returns
        -------
        tuple[pd.DataFrame, set[int]]
            - Filtered and encoded patients DataFrame
            - Set of matched subject_ids
        """
        # Collect subject_id sets from each source
        pts_ids    = set(patients_df["subject_id"].dropna().astype(int).unique())
        notes_ids  = set(notes_df["subject_id"].dropna().astype(int).unique())
        labs_ids   = set(labs_df["subject_id"].dropna().astype(int).unique())
        vitals_ids = set(vitals_df["subject_id"].dropna().astype(int).unique())

        print(f"\n[PatientMatcher] Patients in patients_df: {len(pts_ids):,}")
        print(f"[PatientMatcher] Patients with notes:     {len(notes_ids):,}")
        print(f"[PatientMatcher] Patients with labs:      {len(labs_ids):,}")
        print(f"[PatientMatcher] Patients with vitals:    {len(vitals_ids):,}")

        # Intersection across all 4
        matched_ids = pts_ids & notes_ids & labs_ids & vitals_ids
        print(f"[PatientMatcher] Matched (all 4 sources): {len(matched_ids):,}")

        # Filter patients to matched subjects
        df = patients_df[patients_df["subject_id"].isin(matched_ids)].copy()

        # Keep only the required columns
        keep = [c for c in self.KEEP_COLS if c in df.columns]
        df = df[keep]

        # Encode gender: M -> 0, F -> 1
        if "gender" in df.columns:
            df["gender"] = df["gender"].map({"M": 0, "F": 1})

        # Fill null categorical columns
        if "marital_status" in df.columns:
            df["marital_status"] = df["marital_status"].fillna("UNKNOWN")
        if "insurance" in df.columns:
            df["insurance"] = df["insurance"].fillna("Other")
        if "race" in df.columns:
            df["race"] = df["race"].fillna("UNKNOWN")

        df = df.reset_index(drop=True)

        # Print label distribution
        if "hospital_expire_flag" in df.columns:
            total = len(df)
            n0 = (df["hospital_expire_flag"] == 0).sum()
            n1 = (df["hospital_expire_flag"] == 1).sum()
            print(f"[PatientMatcher] Matched admissions: {total:,}")
            print(f"  Survived (0): {n0:,}  ({100*n0/max(total,1):.1f}%)")
            print(f"  Died     (1): {n1:,}  ({100*n1/max(total,1):.1f}%)")

        logger.info("PatientMatcher: %d matched subject_ids, %d admissions.", len(matched_ids), len(df))
        return df, matched_ids

    def get_unmatched_stats(
        self,
        notes_df: pd.DataFrame,
        labs_df: pd.DataFrame,
        vitals_df: pd.DataFrame,
        icustays_df: pd.DataFrame | None = None,
    ) -> dict:
        """Return statistics on how many patients were excluded per modality."""
        notes_ids  = set(notes_df["subject_id"].dropna().astype(int).unique())
        labs_ids   = set(labs_df["subject_id"].dropna().astype(int).unique())
        vitals_ids = set(vitals_df["subject_id"].dropna().astype(int).unique())
        all_three  = notes_ids & labs_ids & vitals_ids
        return {
            "n_notes_only":       len(notes_ids - labs_ids - vitals_ids),
            "n_labs_only":        len(labs_ids - notes_ids - vitals_ids),
            "n_vitals_only":      len(vitals_ids - notes_ids - labs_ids),
            "n_notes_and_labs":   len(notes_ids & labs_ids),
            "n_notes_and_vitals": len(notes_ids & vitals_ids),
            "n_all_three":        len(all_three),
        }

    # ------------------------------------------------------------------
    # Private helpers (kept for skeleton API compatibility)
    # ------------------------------------------------------------------

    def _select_primary_stay(self, icustays_df: pd.DataFrame) -> pd.DataFrame:
        """For admissions with multiple ICU stays, select one primary stay."""
        if self.icu_stay_selection == "first":
            return icustays_df.sort_values("intime").groupby("hadm_id").first().reset_index()
        else:
            return icustays_df.sort_values("los", ascending=False).groupby("hadm_id").first().reset_index()


if __name__ == "__main__":
    from src.stage1_data_loading.patient_loader import PatientLoader
    from src.stage1_data_loading.notes_loader import NotesLoader
    from src.stage1_data_loading.labs_loader import LabsLoader
    from src.stage1_data_loading.vitals_loader import VitalsLoader

    patients = PatientLoader().load()
    notes    = NotesLoader().load()
    labs     = LabsLoader().load()
    vitals   = VitalsLoader().load()

    matcher = PatientMatcher()
    matched_patients, matched_ids = matcher.match(patients, notes, labs, vitals)
    print(matched_patients.head())
