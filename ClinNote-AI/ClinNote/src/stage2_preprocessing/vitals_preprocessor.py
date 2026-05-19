"""
Stage 2 - Preprocessing: Vital Signs Preprocessor

Cleans and normalizes vital sign measurements from vital_signs.csv
(from VitalsLoader) for use in the vitals feature extraction pipeline (Stage 3).

Preprocessing steps:
  1. Select and rename key columns
  2. Convert charttime to datetime
  3. Drop rows where value is null
  4. Apply hard physiological bounds (drop physically impossible values)
  5. Convert Temperature Fahrenheit -> Celsius
  6. Deduplicate on (subject_id, hadm_id, label, charttime) - keep mean
  7. Flag abnormal values using clinical normal ranges
"""

import logging

import numpy as np
import pandas as pd

from configs.data_config import VITAL_ITEMIDS

logger = logging.getLogger(__name__)

# Hard physiological bounds keyed by label keyword patterns
# Format: (keyword_to_match_in_label, lower_bound, upper_bound)
VITAL_HARD_BOUNDS: dict[str, tuple[float, float]] = {
    "heart_rate":       (0.0, 300.0),
    "systolic_bp":      (0.0, 300.0),
    "diastolic_bp":     (0.0, 200.0),
    "mean_bp":          (0.0, 250.0),
    "respiratory_rate": (0.0, 100.0),
    "spo2":             (0.0, 100.0),
    "temperature_f":    (50.0, 120.0),
    "temperature_c":    (10.0, 45.0),
}

# Keyword patterns used to match label strings to vital categories
LABEL_PATTERNS: list[tuple[str, list[str]]] = [
    ("heart_rate",       ["Heart Rate"]),
    ("systolic_bp",      ["Blood Pressure Systolic", "Arterial Blood Pressure systolic",
                          "Manual Blood Pressure Systolic", "Non Invasive Blood Pressure systolic"]),
    ("diastolic_bp",     ["Blood Pressure Diastolic", "Arterial Blood Pressure diastolic",
                          "Manual Blood Pressure Diastolic", "Non Invasive Blood Pressure diastolic"]),
    ("mean_bp",          ["Blood Pressure Mean", "Arterial Blood Pressure mean",
                          "Non Invasive Blood Pressure mean"]),
    ("respiratory_rate", ["Respiratory Rate"]),
    ("spo2",             ["O2 Saturation", "SpO2", "Sat"]),
    ("temperature_f",    ["Temperature Fahrenheit"]),
    ("temperature_c",    ["Temperature Celsius"]),
]

# Clinical normal ranges for abnormality flagging
NORMAL_RANGES: dict[str, tuple[float, float]] = {
    "heart_rate":       (60.0,  100.0),
    "systolic_bp":      (90.0,  140.0),
    "diastolic_bp":     (60.0,   90.0),
    "mean_bp":          (70.0,  100.0),
    "respiratory_rate": (12.0,   20.0),
    "spo2":             (95.0,  100.0),
    "temperature_c":    (36.0,   38.0),
}


def _map_label_to_category(label: str) -> str | None:
    """Map a raw vital label string to a canonical category key."""
    if not isinstance(label, str):
        return None
    for category, patterns in LABEL_PATTERNS:
        for pattern in patterns:
            if pattern.lower() in label.lower():
                return category
    return None


class VitalsPreprocessor:
    """
    Cleans and normalizes vital sign measurements.

    Parameters
    ----------
    drop_warned : bool
        If True, drop rows where warning=1 (nurse flagged as unusual).
    resample_freq : str
        Pandas offset alias for resampling. None to skip resampling.
    fill_limit_hours : int
        Maximum consecutive hours to forward-fill missing vitals.
    """

    def __init__(
        self,
        drop_warned: bool = True,
        resample_freq: str | None = "1h",
        fill_limit_hours: int = 4,
    ) -> None:
        self.drop_warned = drop_warned
        self.resample_freq = resample_freq
        self.fill_limit_hours = fill_limit_hours

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def preprocess(self, vitals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Run the full preprocessing pipeline on a vital signs DataFrame.

        Parameters
        ----------
        vitals_df : pd.DataFrame
            Raw vital signs DataFrame from VitalsLoader.load().

        Returns
        -------
        pd.DataFrame
            Cleaned vital signs DataFrame with columns:
              subject_id, hadm_id, label, value, charttime, is_abnormal.
        """
        df = vitals_df.copy()
        rows_before = len(df)
        print(f"\n[VitalsPreprocessor] Rows before: {rows_before:,}")

        # Step 1: keep only needed columns
        keep = [c for c in ["subject_id", "hadm_id", "stay_id", "label", "valuenum", "charttime", "warning"]
                if c in df.columns]
        df = df[keep]

        # Step 2: rename valuenum -> value
        if "valuenum" in df.columns:
            df = df.rename(columns={"valuenum": "value"})

        # Step 3: parse charttime
        df["charttime"] = pd.to_datetime(df["charttime"], errors="coerce")

        # Step 4: drop warned rows
        df = self._drop_warned(df)

        # Step 5: drop null value rows
        df = self._remove_null_values(df)

        # Step 6: add vital category column for bounds filtering
        df["_category"] = df["label"].apply(_map_label_to_category)

        # Step 7: apply hard physiological bounds
        df = self._apply_hard_bounds(df)

        # Step 8: convert Fahrenheit -> Celsius
        df = self._normalize_temperature_units(df)

        # Step 9: deduplicate
        df = self._remove_duplicates(df)

        # Step 10: flag abnormal values
        df = self._flag_abnormal(df)

        # Drop internal category column
        if "_category" in df.columns:
            df = df.drop(columns=["_category"])

        df = df.reset_index(drop=True)
        rows_after = len(df)

        print(f"[VitalsPreprocessor] Rows after:  {rows_after:,}")
        print(f"[VitalsPreprocessor] Dropped: {rows_before - rows_after:,}")
        if "label" in df.columns:
            print("  Top 15 label distribution:")
            top15 = df["label"].value_counts().head(15)
            for lbl, cnt in top15.items():
                print(f"    {lbl}: {cnt:,}")
        if "is_abnormal" in df.columns:
            abnormal_rate = df["is_abnormal"].mean() * 100
            print(f"  Abnormal rate: {abnormal_rate:.1f}%")

        logger.info("Vitals preprocessing complete: %d rows.", rows_after)
        return df

    def resample_for_stay(self, vitals_df: pd.DataFrame, stay_id: int) -> pd.DataFrame:
        """Resample vital signs for a single ICU stay to regular intervals."""
        stay_vitals = vitals_df[vitals_df["stay_id"] == stay_id]
        pivoted = stay_vitals.pivot_table(
            index="charttime", columns="label", values="value", aggfunc="mean"
        )
        if self.resample_freq:
            pivoted = pivoted.resample(self.resample_freq).mean()
            pivoted = pivoted.ffill(limit=self.fill_limit_hours)
        return pivoted

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _drop_warned(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows flagged by nurses as unusual (warning=1)."""
        if self.drop_warned and "warning" in df.columns:
            df = df[df["warning"] != 1]
        # Drop the warning column after filtering
        if "warning" in df.columns:
            df = df.drop(columns=["warning"])
        return df

    def _remove_null_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop rows with null value."""
        return df.dropna(subset=["value"])

    def _map_vital_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map itemid -> human-readable vital_name using VITAL_ITEMIDS.label_map()."""
        label_map = VITAL_ITEMIDS.label_map()
        df["vital_name"] = df["itemid"].map(label_map)
        df = df.dropna(subset=["vital_name"])
        return df

    def _apply_hard_bounds(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows where value is outside physiological hard bounds."""
        valid_mask = pd.Series(True, index=df.index)

        for category, (lo, hi) in VITAL_HARD_BOUNDS.items():
            cat_mask = df["_category"] == category
            if cat_mask.any():
                in_bounds = (df["value"] >= lo) & (df["value"] <= hi)
                # Only invalidate rows that belong to this category AND are out of bounds
                valid_mask = valid_mask & (~cat_mask | in_bounds)

        return df[valid_mask]

    def _normalize_temperature_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Temperature Fahrenheit rows to Celsius."""
        mask = df["label"].str.contains("Fahrenheit", case=False, na=False)
        df = df.copy()
        df.loc[mask, "value"] = (df.loc[mask, "value"] - 32) * 5 / 9
        df.loc[mask, "label"] = "Temperature Celsius"
        df.loc[mask, "_category"] = "temperature_c"
        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate (subject_id, hadm_id, label, charttime) rows — keep mean."""
        group_cols = [c for c in ["subject_id", "hadm_id", "label", "charttime"] if c in df.columns]
        # For non-numeric columns keep first; for value keep mean
        agg_dict = {"value": "mean"}
        for col in df.columns:
            if col not in group_cols and col != "value":
                agg_dict[col] = "first"
        df = df.groupby(group_cols, as_index=False).agg(agg_dict)
        return df

    def _flag_abnormal(self, df: pd.DataFrame) -> pd.DataFrame:
        """Flag vital values outside clinical normal ranges."""
        df = df.copy()
        df["is_abnormal"] = False

        for category, (lo, hi) in NORMAL_RANGES.items():
            cat_mask = df["_category"] == category
            if cat_mask.any():
                abnormal = (df["value"] < lo) | (df["value"] > hi)
                df.loc[cat_mask & abnormal, "is_abnormal"] = True

        return df


if __name__ == "__main__":
    preprocessor = VitalsPreprocessor()
    from src.stage1_data_loading.vitals_loader import VitalsLoader
    loader = VitalsLoader()
    raw_vitals = loader.load()
    clean_vitals = preprocessor.preprocess(raw_vitals)
    print(clean_vitals.head())
