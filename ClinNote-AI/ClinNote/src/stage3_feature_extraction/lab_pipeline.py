"""
Stage 3 — Feature Extraction Pipeline B: Laboratory Tests

Transforms preprocessed lab events into a fixed-length 50-dimensional
feature vector per patient admission.

Feature vector layout (50 dimensions):
    For each of the 25 key lab tests:
      [2i]   normalized_value  — (value - range_midpoint) / half_range
      [2i+1] is_abnormal       — 0.0 or 1.0
    = 25 × 2 = 50 dimensions exactly.

    The 25 labs are taken from the first 25 entries of LAB_ITEMIDS.as_list().

Input:  preprocessed labs DataFrame (from LabsPreprocessor)
Output: np.ndarray of shape (n_admissions, 50)
"""

import logging

import numpy as np
import pandas as pd

from configs.model_config import MODEL_CFG
from configs.data_config import LAB_ITEMIDS

logger = logging.getLogger(__name__)

# Expected output dimension
LAB_FEATURE_DIM = MODEL_CFG.lab_dim  # 50

# Use exactly 25 labs → 25 × 2 features = 50 dims
_N_LABS = LAB_FEATURE_DIM // 2  # 25


class LabPipeline:
    """
    Extracts 50-dimensional lab feature vectors from preprocessed lab events.

    For each admission:
      1. Gets the latest value per lab test
      2. Normalizes values using reference range midpoints
      3. Encodes abnormality flags as binary features
      4. Pads missing labs with zeros
      5. Assembles into a fixed-length 50-dim vector

    Parameters
    ----------
    normalize_values : bool
        Whether to normalize lab values by reference range midpoint.
    missing_fill : float
        Value used for labs not measured in this admission. Default 0.0.
    """

    def __init__(
        self,
        normalize_values: bool = True,
        missing_fill: float = 0.0,
    ) -> None:
        self.normalize_values = normalize_values
        self.missing_fill = missing_fill
        self._feature_names: list[str] | None = None

        # Build the ordered list of (itemid, label) pairs we use
        label_map = LAB_ITEMIDS.label_map()  # {itemid: label}
        itemids = LAB_ITEMIDS.as_list()[:_N_LABS]
        self._itemids = itemids
        self._labels = [label_map[iid] for iid in itemids]
        self._ref_ranges = LAB_ITEMIDS.reference_ranges()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_for_admission(
        self,
        labs_df: pd.DataFrame,
        hadm_id: int,
    ) -> np.ndarray:
        """
        Extract the 50-dim lab feature vector for a single admission.

        Parameters
        ----------
        labs_df : pd.DataFrame
            Preprocessed lab events (output of LabsPreprocessor.preprocess()).
        hadm_id : int
            Hospital admission ID.

        Returns
        -------
        np.ndarray
            Float32 array of shape (50,).
        """
        # Filter to this admission and get the latest value per itemid
        adm_labs = labs_df[labs_df["hadm_id"] == hadm_id].copy()

        if adm_labs.empty:
            return np.full(LAB_FEATURE_DIM, self.missing_fill, dtype=np.float32)

        # Keep most recent measurement per itemid
        if "charttime" in adm_labs.columns:
            adm_labs = adm_labs.sort_values("charttime")
        latest = adm_labs.groupby("itemid").last().reset_index()

        vector = self._build_feature_vector(latest)
        assert vector.shape == (LAB_FEATURE_DIM,), (
            f"Expected {LAB_FEATURE_DIM} dims, got {vector.shape}"
        )
        return vector

    def extract_batch(
        self,
        labs_df: pd.DataFrame,
        hadm_ids: list[int],
    ) -> np.ndarray:
        """
        Extract lab feature vectors for a list of admissions.

        Parameters
        ----------
        labs_df : pd.DataFrame
            Preprocessed lab events.
        hadm_ids : list[int]
            List of hospital admission IDs.

        Returns
        -------
        np.ndarray
            Float32 array of shape (len(hadm_ids), 50).
        """
        from tqdm import tqdm
        features = []
        for hadm_id in tqdm(hadm_ids, desc="Lab feature extraction"):
            vec = self.extract_for_admission(labs_df, hadm_id)
            features.append(vec)
        return np.stack(features, axis=0)

    def get_feature_names(self) -> list[str]:
        """
        Return the name for each dimension in the 50-dim feature vector.

        Returns
        -------
        list[str]
            50 names: ["glucose_value", "glucose_abnormal",
                       "creatinine_value", "creatinine_abnormal", ...]
        """
        if self._feature_names is not None:
            return self._feature_names

        names = []
        for label in self._labels:
            names.append(f"{label}_value")
            names.append(f"{label}_abnormal")
        self._feature_names = names
        return self._feature_names

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_feature_vector(self, latest_labs: pd.DataFrame) -> np.ndarray:
        """
        Assemble the 50-dim feature vector from the latest lab values.

        Parameters
        ----------
        latest_labs : pd.DataFrame
            One row per itemid with columns: itemid, valuenum, is_abnormal.

        Returns
        -------
        np.ndarray
            Float32 array of shape (50,).
        """
        features = []
        for itemid, label in zip(self._itemids, self._labels):
            row = latest_labs[latest_labs["itemid"] == itemid]
            if len(row) == 0:
                # Lab not measured: fill both slots with missing_fill
                features.append(self.missing_fill)
                features.append(self.missing_fill)
            else:
                valuenum = float(row["valuenum"].values[0])

                # Abnormality flag
                if "is_abnormal" in row.columns:
                    is_abnormal = float(row["is_abnormal"].values[0])
                else:
                    is_abnormal = 0.0

                # Normalize value
                if self.normalize_values:
                    norm_val = self._normalize_value(valuenum, label,
                                                     self._ref_ranges)
                else:
                    norm_val = valuenum

                features.append(norm_val)
                features.append(is_abnormal)

        # Ensure exactly LAB_FEATURE_DIM values
        features = features[:LAB_FEATURE_DIM]
        features += [self.missing_fill] * (LAB_FEATURE_DIM - len(features))
        return np.array(features, dtype=np.float32)

    def _normalize_value(
        self,
        value: float,
        lab_label: str,
        ref_ranges: dict[str, tuple[float, float]],
    ) -> float:
        """
        Normalize a lab value using the reference range.

        value=0.0  → at reference range midpoint (normal center)
        value=±1.0 → at boundary of reference range
        Values outside [-1, 1] are abnormal.

        Parameters
        ----------
        value : float
        lab_label : str
        ref_ranges : dict

        Returns
        -------
        float
        """
        lo, hi = ref_ranges.get(lab_label, (0.0, 1.0))
        mid = (lo + hi) / 2.0
        half_range = (hi - lo) / 2.0 or 1.0
        return (value - mid) / half_range


if __name__ == "__main__":
    pipeline = LabPipeline()
    names = pipeline.get_feature_names()
    print(f"Feature vector has {len(names)} dimensions")
    print("First 6 names:", names[:6])
