"""
Stage 1 — Data Sources: Cohort Builder

Builds the final patient cohort by intersecting patients who appear in all
four pre-extracted data sources:
  - patients_final.csv  (demographics + mortality label)
  - clinical_notes.csv  (clinical text)
  - labs_final.csv      (laboratory results)
  - vital_signs.csv     (ICU vital sign measurements)

The resulting cohort DataFrame has one row per (subject_id, hadm_id) and
includes the mortality label (hospital_expire_flag) for Stage 5 analysis.

Saves cohort to: outputs/features/cohort.pkl
"""

import logging
import pickle
from pathlib import Path

import pandas as pd

from configs.paths import PATHS, FEATURES_DIR, COHORT_FILE

logger = logging.getLogger(__name__)


class CohortBuilder:
    """
    Constructs the multimodal patient cohort.

    Finds subject_ids that appear in ALL four DataFrames (patients, notes,
    labs, vitals) and returns the filtered patients DataFrame with the
    required columns.

    Parameters
    ----------
    notes_loader   : unused (kept for API compatibility)
    labs_loader    : unused (kept for API compatibility)
    vitals_loader  : unused (kept for API compatibility)
    patient_loader : unused (kept for API compatibility)
    max_patients   : int | None — cap on cohort size for debugging
    """

    def __init__(
        self,
        notes_loader=None,
        labs_loader=None,
        vitals_loader=None,
        patient_loader=None,
        max_patients: int | None = None,
    ) -> None:
        self.max_patients = max_patients
        self._cohort: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        patients_df: pd.DataFrame,
        notes_df: pd.DataFrame,
        labs_df: pd.DataFrame,
        vitals_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Build and return the filtered patient cohort.

        Parameters
        ----------
        patients_df : pd.DataFrame  — output of PatientLoader.load()
        notes_df    : pd.DataFrame  — output of NotesLoader.load()
        labs_df     : pd.DataFrame  — output of LabsLoader.load()
        vitals_df   : pd.DataFrame  — output of VitalsLoader.load()

        Returns
        -------
        pd.DataFrame
            Cohort with columns:
            subject_id, hadm_id, hospital_expire_flag, gender, anchor_age, los_days
        """
        if self._cohort is not None:
            logger.debug("Returning cached cohort.")
            return self._cohort

        logger.info("Building patient cohort ...")

        # Subject IDs present in each modality
        pts_ids    = set(patients_df["subject_id"].unique())
        notes_ids  = set(notes_df["subject_id"].unique())
        labs_ids   = set(labs_df["subject_id"].unique())
        vitals_ids = set(vitals_df["subject_id"].unique())

        print(f"\n[CohortBuilder] Patients with notes:  {len(notes_ids):,}")
        print(f"[CohortBuilder] Patients with labs:   {len(labs_ids):,}")
        print(f"[CohortBuilder] Patients with vitals: {len(vitals_ids):,}")

        # Relaxed filtering: require notes + vitals (core modalities).
        # Labs are optional — missing labs are imputed as zeros by the feature extractor.
        # This increases cohort size significantly since labs is the smallest file.
        core_ids   = pts_ids & notes_ids & vitals_ids
        common_ids = core_ids | (pts_ids & notes_ids & labs_ids & vitals_ids)
        common_ids = core_ids  # notes + vitals is the minimum requirement
        print(f"[CohortBuilder] Patients with notes + vitals (relaxed): {len(common_ids):,}")
        print(f"[CohortBuilder] Of those, also have labs:               {len(common_ids & labs_ids):,}")

        # Filter patients to common subjects
        cohort = patients_df[patients_df["subject_id"].isin(common_ids)].copy()

        # Keep required columns (add defaults for any that might be missing)
        required_cols = ["subject_id", "hadm_id", "hospital_expire_flag",
                         "gender", "anchor_age", "los_days"]
        for col in required_cols:
            if col not in cohort.columns:
                cohort[col] = None

        cohort = cohort[required_cols].reset_index(drop=True)

        # Optional cap for debugging
        if self.max_patients:
            cohort = cohort.head(self.max_patients)
            logger.info("Capped cohort to %d patients.", self.max_patients)

        self._cohort = cohort

        # ---- Print summary ----
        total = len(cohort)
        n0 = (cohort["hospital_expire_flag"] == 0).sum()
        n1 = (cohort["hospital_expire_flag"] == 1).sum()
        print(f"\n[CohortBuilder] Final cohort size: {total:,} admissions")
        print(f"  hospital_expire_flag=0 (survived): {n0:,}  ({100*n0/total:.1f}%)")
        print(f"  hospital_expire_flag=1 (died):     {n1:,}  ({100*n1/total:.1f}%)")
        print(f"  Class balance: {100*n1/total:.1f}% positive (mortality)")

        # Save to disk
        self.save()

        return self._cohort

    def save(self, output_path: Path | None = None) -> None:
        """Persist the cohort DataFrame to disk as a pickle file."""
        if self._cohort is None:
            raise RuntimeError("Call build() before save().")
        import src.stage1_data_loading.cohort_builder as _self_mod
        out = output_path or _self_mod.COHORT_FILE
        out.parent.mkdir(parents=True, exist_ok=True)
        self._cohort.to_pickle(out)
        logger.info("Cohort saved to %s", out)
        print(f"[CohortBuilder] Cohort saved -> {out}")

    @classmethod
    def load_cached(cls, cohort_path: Path = COHORT_FILE) -> pd.DataFrame:
        """Load a previously saved cohort without re-querying source data."""
        if not cohort_path.exists():
            raise FileNotFoundError(
                f"No cached cohort found at {cohort_path}. Run CohortBuilder.build() first."
            )
        return pd.read_pickle(cohort_path)

    def get_stats(self) -> dict:
        """Return summary statistics about the built cohort."""
        if self._cohort is None:
            raise RuntimeError("Call build() first.")
        df = self._cohort
        return {
            "n_admissions":    len(df),
            "n_patients":      df["subject_id"].nunique(),
            "mortality_rate":  df["hospital_expire_flag"].mean(),
            "avg_age":         df["anchor_age"].mean() if "anchor_age" in df.columns else None,
            "avg_los_days":    df["los_days"].mean() if "los_days" in df.columns else None,
        }

    # ------------------------------------------------------------------
    # Private helpers (kept for API compatibility)
    # ------------------------------------------------------------------

    def _get_hadm_ids_with_notes(self) -> set[int]:
        raise NotImplementedError("Pass DataFrames directly to build().")

    def _get_hadm_ids_with_sufficient_labs(self) -> set[int]:
        raise NotImplementedError("Pass DataFrames directly to build().")


if __name__ == "__main__":
    from src.stage1_data_loading.patient_loader import PatientLoader
    from src.stage1_data_loading.notes_loader import NotesLoader
    from src.stage1_data_loading.labs_loader import LabsLoader
    from src.stage1_data_loading.vitals_loader import VitalsLoader

    patients = PatientLoader().load()
    notes    = NotesLoader().load()
    labs     = LabsLoader().load()
    vitals   = VitalsLoader().load()

    builder = CohortBuilder()
    cohort  = builder.build(patients, notes, labs, vitals)
    print(cohort.head())
    print(builder.get_stats())
