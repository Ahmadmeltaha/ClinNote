"""
Stage 2 - Preprocessing: Laboratory Results Preprocessor

Cleans and normalizes lab events DataFrame (from LabsLoader) for use
in the lab feature extraction pipeline (Stage 3).

Preprocessing steps:
  1. Drop unused columns (microbiology/merge artifacts)
  2. Parse datetime columns
  3. Drop rows where valuenum or subject_id is null
  4. Remove duplicates on (subject_id, hadm_id, itemid, charttime) - keep most recent storetime
  5. Remove outliers: values more than 5 std deviations from per-label mean
  6. Flag abnormal values using ref_range_lower / ref_range_upper
  7. Compute severity score: normalized distance from reference range midpoint
"""

import logging

import numpy as np
import pandas as pd

from configs.data_config import LAB_ITEMIDS, DATA_CFG

logger = logging.getLogger(__name__)

# Columns to drop if they exist (microbiology merge artifacts + unused fields)
COLS_TO_DROP = [
    "order_provider_id_x", "org_name", "isolate_num", "org_itemid",
    "ab_itemid", "dilution_text", "dilution_comparison", "dilution_value",
    "interpretation", "ab_name", "microevent_id", "micro_specimen_id",
    "quantity", "storedate", "storetime_y", "test_seq", "comments_x",
    "priority", "spec_itemid", "fluid", "order_provider_id_y", "category",
    "spec_type_desc", "test_itemid",
]


class LabsPreprocessor:
    """
    Cleans and normalizes lab events.

    Parameters
    ----------
    missing_strategy : str
        How to handle missing valuenum:
        - "drop"  : remove rows with null valuenum
        - "flag"  : keep rows, add is_missing=True column
    outlier_std_threshold : float
        Values more than this many standard deviations from the mean
        (per label) are flagged as outliers and removed.
    """

    def __init__(
        self,
        missing_strategy: str = "drop",
        outlier_std_threshold: float = 5.0,
    ) -> None:
        if missing_strategy not in ("drop", "flag"):
            raise ValueError(f"missing_strategy must be 'drop' or 'flag', got {missing_strategy!r}")
        self.missing_strategy = missing_strategy
        self.outlier_std_threshold = outlier_std_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def preprocess(self, labs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Run the full preprocessing pipeline on a lab events DataFrame.

        Parameters
        ----------
        labs_df : pd.DataFrame
            Raw lab events from LabsLoader.load() (already has charttime renamed).

        Returns
        -------
        pd.DataFrame
            Cleaned lab events with additional columns:
              - is_abnormal (bool)
              - severity_score (float, 0.0-1.0)
        """
        df = labs_df.copy()
        rows_before = len(df)
        print(f"\n[LabsPreprocessor] Rows before: {rows_before:,}")

        # Step 1: drop unused columns
        drop_existing = [c for c in COLS_TO_DROP if c in df.columns]
        if drop_existing:
            df = df.drop(columns=drop_existing)

        # Step 2: parse datetime columns
        for col in ["charttime", "charttime_y", "chartdate"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        if "storetime" in df.columns:
            df["storetime"] = pd.to_datetime(df["storetime"], errors="coerce")

        # Step 3: drop null subject_id
        df = df.dropna(subset=["subject_id"])
        df["subject_id"] = pd.to_numeric(df["subject_id"], errors="coerce")
        df = df.dropna(subset=["subject_id"])
        df["subject_id"] = df["subject_id"].astype(int)

        # Step 4: drop null valuenum
        df = self._handle_missing(df)

        # Step 5: deduplicate
        df = self._remove_duplicates(df)

        # Step 6: remove outliers per label
        df = self._remove_outliers(df)

        # Step 7: flag abnormal
        df = self._flag_abnormal(df)

        # Step 8: compute severity score
        df = self._compute_severity(df)

        df = df.reset_index(drop=True)
        rows_after = len(df)

        print(f"[LabsPreprocessor] Rows after:  {rows_after:,}")
        print(f"[LabsPreprocessor] Dropped: {rows_before - rows_after:,}")
        if "label" in df.columns:
            print(f"  Unique labels: {df['label'].nunique():,}")
        if "is_abnormal" in df.columns:
            abnormal_rate = df["is_abnormal"].mean() * 100
            print(f"  Abnormal rate: {abnormal_rate:.1f}%")
        if "severity_score" in df.columns:
            avg_sev = df["severity_score"].mean()
            print(f"  Avg severity score: {avg_sev:.4f}")

        logger.info("Labs preprocessing complete: %d rows.", rows_after)
        return df

    def preprocess_for_admission(self, labs_df: pd.DataFrame, hadm_id: int) -> pd.DataFrame:
        """Preprocess lab events for a single admission."""
        return labs_df[labs_df["hadm_id"] == hadm_id].sort_values("charttime")

    def get_latest_per_item(self, labs_df: pd.DataFrame, hadm_id: int) -> pd.DataFrame:
        """Return the most recent lab result per itemid for a given admission."""
        adm_labs = self.preprocess_for_admission(labs_df, hadm_id)
        latest = adm_labs.sort_values("charttime").groupby("itemid").last()
        return latest.reset_index()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate lab events on (subject_id, hadm_id, itemid, charttime).
        Keep the row with the most recent storetime.
        """
        dup_cols = [c for c in ["subject_id", "hadm_id", "itemid", "charttime"] if c in df.columns]
        if not dup_cols:
            return df
        if "storetime" in df.columns:
            df = df.sort_values("storetime", na_position="first")
        df = df.drop_duplicates(subset=dup_cols, keep="last")
        return df

    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle rows with null valuenum based on self.missing_strategy."""
        df["is_missing"] = df["valuenum"].isna()
        if self.missing_strategy == "drop":
            df = df[~df["is_missing"]]
        return df

    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flag and remove values more than outlier_std_threshold std devs from
        the per-label mean.
        """
        group_col = "label" if "label" in df.columns else "itemid"

        # Compute per-group mean and std, then broadcast back via transform
        grp = df.groupby(group_col)["valuenum"]
        mean = grp.transform("mean")
        std  = grp.transform("std").fillna(0)

        # Where std == 0, keep all rows (z-score undefined)
        z = (df["valuenum"] - mean).abs() / std.replace(0, float("inf"))
        df["is_outlier"] = z > self.outlier_std_threshold
        df = df[~df["is_outlier"]].copy()
        return df.reset_index(drop=True)

    def _flag_abnormal(self, df: pd.DataFrame) -> pd.DataFrame:
        """Flag lab values outside their reference ranges."""
        df = df.copy()
        has_lower = df["ref_range_lower"].notna() if "ref_range_lower" in df.columns else pd.Series(False, index=df.index)
        has_upper = df["ref_range_upper"].notna() if "ref_range_upper" in df.columns else pd.Series(False, index=df.index)
        has_ranges = has_lower & has_upper

        df["is_abnormal"] = False
        if has_ranges.any():
            below = df["valuenum"] < df["ref_range_lower"]
            above = df["valuenum"] > df["ref_range_upper"]
            df.loc[has_ranges, "is_abnormal"] = (below | above)[has_ranges]

        return df

    def _compute_severity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute a normalized severity score for each lab value.

        severity = abs(valuenum - midpoint) / half_range, clipped to [0, 1].
        If ref ranges are null, severity_score = 0.0.
        """
        df = df.copy()
        df["severity_score"] = 0.0

        if "ref_range_lower" not in df.columns or "ref_range_upper" not in df.columns:
            return df

        has_ranges = df["ref_range_lower"].notna() & df["ref_range_upper"].notna()
        if not has_ranges.any():
            return df

        midpoint   = (df.loc[has_ranges, "ref_range_lower"] + df.loc[has_ranges, "ref_range_upper"]) / 2
        half_range = (df.loc[has_ranges, "ref_range_upper"] - df.loc[has_ranges, "ref_range_lower"]) / 2

        # Avoid divide-by-zero
        safe_half = half_range.replace(0, np.nan)
        severity = ((df.loc[has_ranges, "valuenum"] - midpoint).abs() / safe_half).clip(0.0, 1.0)
        severity = severity.fillna(0.0)

        df.loc[has_ranges, "severity_score"] = severity
        return df


if __name__ == "__main__":
    preprocessor = LabsPreprocessor()
    from src.stage1_data_loading.labs_loader import LabsLoader
    loader = LabsLoader()
    raw_labs = loader.load()
    clean_labs = preprocessor.preprocess(raw_labs)
    print(clean_labs[["label", "valuenum", "is_abnormal", "severity_score"]].head())
