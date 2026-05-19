"""
Stage 2 - Preprocessing: Time Aligner

Aligns all clinical events (notes, labs, vitals) to a common admission
timeline. Uses hospital admission time (admittime from patients_final.csv)
as the reference point (t=0).

All timestamps are converted to:
    hours_from_admission = (event_charttime - hadm_admittime) / timedelta(hours=1)

This normalization:
  - Makes event timing patient-comparable (removes absolute date differences)
  - Allows windowing: "events in the first 48 hours of admission"
  - Removes pre-admission events (negative hours) which represent outpatient data
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


class TimeAligner:
    """
    Converts absolute datetimes to relative hours-from-admission for all events.

    Parameters
    ----------
    reference : str
        Reference timestamp to align to:
        - "admittime"  : hospital admission time (for notes and labs)
        - "icu_intime" : ICU stay start time (for vital signs)
    clip_negative : bool
        If True, remove events that occurred before the reference time
        (negative hours_from_admission). These are pre-admission events.
    """

    def __init__(
        self,
        reference: str = "admittime",
        clip_negative: bool = True,
    ) -> None:
        if reference not in ("admittime", "icu_intime"):
            raise ValueError("reference must be 'admittime' or 'icu_intime'")
        self.reference = reference
        self.clip_negative = clip_negative

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def align(
        self,
        df: pd.DataFrame,
        patients_df: pd.DataFrame,
        time_col: str = "charttime",
        reference: str = "admittime",
        max_hours: float | None = None,
    ) -> pd.DataFrame:
        """
        Generic alignment method for any events DataFrame.

        Joins df with patients_df on subject_id + hadm_id to get the
        reference timestamp, then computes hours_from_admission.

        Parameters
        ----------
        df : pd.DataFrame
            Events DataFrame (notes, labs, or vitals) with charttime and hadm_id.
        patients_df : pd.DataFrame
            Patients DataFrame with hadm_id and admittime (from PatientLoader).
        time_col : str
            Column in df containing the event timestamp. Default "charttime".
        reference : str
            Reference column in patients_df. Default "admittime".
        max_hours : float | None
            If set, keep only events within first max_hours of admission.

        Returns
        -------
        pd.DataFrame
            df with hours_from_admission column added; pre-admission rows dropped.
        """
        rows_before = len(df)
        print(f"\n[TimeAligner] Rows before alignment: {rows_before:,}")

        df = df.copy()

        # Ensure reference column exists in patients_df
        if reference not in patients_df.columns:
            raise ValueError(f"Reference column '{reference}' not found in patients_df.")

        # Determine join keys
        join_keys = []
        if "hadm_id" in df.columns and "hadm_id" in patients_df.columns:
            join_keys = ["hadm_id"]
        if "subject_id" in df.columns and "subject_id" in patients_df.columns:
            join_keys = ["subject_id", "hadm_id"] if "hadm_id" in join_keys else ["subject_id"]

        ref_cols = list(set(join_keys + [reference]))
        ref_df = patients_df[ref_cols].drop_duplicates(subset=join_keys).copy()

        # Coerce join key dtypes to int64 on both sides to avoid object/int mismatch
        for key in join_keys:
            df[key] = pd.to_numeric(df[key], errors="coerce")
            ref_df[key] = pd.to_numeric(ref_df[key], errors="coerce")
        df = df.dropna(subset=join_keys)
        ref_df = ref_df.dropna(subset=join_keys)
        for key in join_keys:
            df[key] = df[key].astype("int64")
            ref_df[key] = ref_df[key].astype("int64")

        # Parse reference time
        ref_df[reference] = pd.to_datetime(ref_df[reference], errors="coerce")

        # Ensure event time is datetime
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

        # Merge
        merged = df.merge(ref_df, on=join_keys, how="left")

        # Compute hours_from_admission
        merged["hours_from_admission"] = (
            merged[time_col] - merged[reference]
        ).dt.total_seconds() / 3600

        # Drop the reference column (don't keep admittime in output)
        if reference in merged.columns:
            merged = merged.drop(columns=[reference])

        # Drop rows where hours_from_admission is null or negative
        before_clip = len(merged)
        merged = merged.dropna(subset=["hours_from_admission"])
        if self.clip_negative:
            merged = merged[merged["hours_from_admission"] >= 0]

        # Optional window filter
        if max_hours is not None:
            merged = merged[merged["hours_from_admission"] <= max_hours]

        merged = merged.reset_index(drop=True)
        rows_after = len(merged)

        print(f"[TimeAligner] Rows after alignment: {rows_after:,}")
        print(f"[TimeAligner] Dropped (pre-admission / null): {rows_before - rows_after:,}")
        hfa = merged["hours_from_admission"]
        print(f"  hours_from_admission: min={hfa.min():.1f}  max={hfa.max():.1f}  mean={hfa.mean():.1f}")

        return merged

    def align_labs(
        self,
        labs_df: pd.DataFrame,
        admissions_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Add hours_from_admission column to lab events."""
        merged = labs_df.merge(
            admissions_df[["hadm_id", "admittime"]].drop_duplicates("hadm_id"),
            on="hadm_id",
            how="left",
        )
        merged["admittime"] = pd.to_datetime(merged["admittime"], errors="coerce")
        merged["charttime"] = pd.to_datetime(merged["charttime"], errors="coerce")
        merged["hours_from_admission"] = (
            merged["charttime"] - merged["admittime"]
        ).dt.total_seconds() / 3600
        if self.clip_negative:
            merged = merged[merged["hours_from_admission"] >= 0]
        return merged.drop(columns=["admittime"])

    def align_vitals(
        self,
        vitals_df: pd.DataFrame,
        icustays_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Add hours_from_icu_admission column to vital sign events."""
        merged = vitals_df.merge(
            icustays_df[["stay_id", "intime"]].drop_duplicates("stay_id"),
            on="stay_id",
            how="left",
        )
        merged["intime"] = pd.to_datetime(merged["intime"], errors="coerce")
        merged["charttime"] = pd.to_datetime(merged["charttime"], errors="coerce")
        merged["hours_from_icu_admission"] = (
            merged["charttime"] - merged["intime"]
        ).dt.total_seconds() / 3600
        if self.clip_negative:
            merged = merged[merged["hours_from_icu_admission"] >= 0]
        return merged.drop(columns=["intime"])

    def align_notes(
        self,
        notes_df: pd.DataFrame,
        admissions_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Add hours_from_admission to clinical notes."""
        return self.align_labs(notes_df, admissions_df)

    def filter_window(
        self,
        df: pd.DataFrame,
        time_col: str,
        max_hours: float,
    ) -> pd.DataFrame:
        """Keep only events within the first max_hours of admission."""
        return df[df[time_col] <= max_hours]


if __name__ == "__main__":
    aligner = TimeAligner(reference="admittime")
    print("TimeAligner ready. Use aligner.align(df, patients_df) to align events.")
