"""
Stage 1 — Data Sources: Patient & Admission Loader

Loads patient demographics and admission records from the pre-extracted CSV:
    data/patients_final.csv  (21 columns, one row per hospital admission)

patients_final schema (key columns):
    subject_id           : int  — unique patient identifier
    hadm_id              : int  — hospital admission identifier
    admittime            : str  — admission datetime
    dischtime            : str  — discharge datetime
    deathtime            : str  — in-hospital death datetime (nullable)
    hospital_expire_flag : int  — 1 if patient died in hospital (mortality label)
    gender               : str  — "M" | "F"
    anchor_age           : int  — patient age (de-identified)
    anchor_year_group    : str  — decade group
    dod                  : str  — date of death (nullable)
"""

import logging
from pathlib import Path

import pandas as pd

from configs.paths import PATIENTS_PATH

logger = logging.getLogger(__name__)


class PatientLoader:
    """
    Loads patient demographics and hospital admission records.

    Also builds a master patient index that links subject_id → hadm_id(s)
    for use by the CohortBuilder.

    Parameters
    ----------
    patients_path : Path, optional
        Path to patients_final.csv. Defaults to PATIENTS_PATH from configs.
    """

    def __init__(self, patients_path: Path = PATIENTS_PATH) -> None:
        self.patients_path = patients_path
        self._df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> pd.DataFrame:
        """
        Load patients_final.csv, clean, and return a DataFrame.

        Steps
        -----
        - Load data/patients_final.csv
        - Drop rows where subject_id or hadm_id is null
        - Convert hospital_expire_flag to int (mortality label 0/1)
        - Convert admittime and dischtime to datetime
        - Compute los_days = (dischtime - admittime).dt.total_seconds() / 86400
        - Print shape, label distribution, and null summary

        Returns
        -------
        pd.DataFrame
            Clean patient/admission DataFrame with los_days column added.
        """
        if self._df is not None:
            return self._df

        logger.info("Loading patients from %s ...", self.patients_path)
        df = pd.read_csv(self.patients_path)

        # Drop rows missing key identifiers
        before = len(df)
        df = df.dropna(subset=["subject_id", "hadm_id"])
        dropped = before - len(df)
        if dropped:
            logger.warning("Dropped %d rows with null subject_id or hadm_id.", dropped)

        # Ensure integer types for IDs
        df["subject_id"] = df["subject_id"].astype(int)
        df["hadm_id"]    = df["hadm_id"].astype(int)

        # Mortality label → integer 0/1
        df["hospital_expire_flag"] = df["hospital_expire_flag"].fillna(0).astype(int)

        # Parse datetime columns
        df["admittime"] = pd.to_datetime(df["admittime"], errors="coerce")
        df["dischtime"] = pd.to_datetime(df["dischtime"], errors="coerce")

        # Length of stay in days
        df["los_days"] = (df["dischtime"] - df["admittime"]).dt.total_seconds() / 86400

        self._df = df

        # ---- Print summary ----
        n0 = (df["hospital_expire_flag"] == 0).sum()
        n1 = (df["hospital_expire_flag"] == 1).sum()
        total = len(df)
        print(f"\n[PatientLoader] Shape: {df.shape}")
        print(f"  hospital_expire_flag=0 (survived): {n0:,}  ({100*n0/total:.1f}%)")
        print(f"  hospital_expire_flag=1 (died):     {n1:,}  ({100*n1/total:.1f}%)")
        null_counts = df.isnull().sum()
        null_counts = null_counts[null_counts > 0]
        if len(null_counts):
            print("  Null counts:")
            for col, cnt in null_counts.items():
                print(f"    {col}: {cnt:,}")
        else:
            print("  No nulls in loaded DataFrame.")

        return df

    def get_cohort_ids(self) -> set[tuple[int, int]]:
        """
        Return a set of (subject_id, hadm_id) tuples from the loaded DataFrame.

        Returns
        -------
        set of (int, int)
        """
        df = self.load()
        return set(zip(df["subject_id"], df["hadm_id"]))

    # ------------------------------------------------------------------
    # Legacy-compatibility methods (kept for skeleton compliance)
    # ------------------------------------------------------------------

    def load_patients(self) -> pd.DataFrame:
        """Return the loaded DataFrame (alias for load())."""
        return self.load()

    def load_admissions(self) -> pd.DataFrame:
        """Return the loaded DataFrame (alias for load())."""
        return self.load()

    def build_patient_index(self) -> pd.DataFrame:
        """Return the loaded DataFrame with los_days already computed."""
        return self.load()

    def get_mortality_labels(self) -> pd.Series:
        """Return hospital_expire_flag series indexed by hadm_id."""
        df = self.load()
        return df.set_index("hadm_id")["hospital_expire_flag"]

    def get_patient_demographics(self, subject_id: int) -> dict:
        """Return demographic dict for a single patient."""
        df = self.load()
        row = df[df["subject_id"] == subject_id].iloc[0]
        return row[["gender", "anchor_age", "anchor_year_group", "dod"]].to_dict()

    def load_from_input(self, patient_input) -> pd.DataFrame:
        sid = (patient_input.subject_id
               or abs(hash(patient_input.admittime)) % 1_000_000)
        hadm_id = (abs(hash(str(sid) + patient_input.admittime))
                   % 10_000_000)
        admit = pd.to_datetime(patient_input.admittime)
        disch = (pd.to_datetime(patient_input.dischtime)
                 if patient_input.dischtime
                 else admit + pd.Timedelta(days=5))
        los = (disch - admit).total_seconds() / 86400
        return pd.DataFrame([{
            "subject_id": sid, "hadm_id": hadm_id,
            "gender": patient_input.gender,
            "anchor_age": patient_input.age,
            "admittime": admit, "dischtime": disch,
            "los_days": los, "hospital_expire_flag": 0,
            "anchor_year_group": "2010-2019",
            "dod": None, "deathtime": None,
        }])


if __name__ == "__main__":
    loader = PatientLoader()
    df = loader.load()
    print(df.head())
    print(f"Cohort IDs sample: {list(loader.get_cohort_ids())[:3]}")
