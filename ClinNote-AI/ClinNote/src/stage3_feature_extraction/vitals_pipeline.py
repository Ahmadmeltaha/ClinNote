"""
Stage 3 — Feature Extraction Pipeline C: Vital Signs

Transforms preprocessed vital sign time-series into a fixed-length
32-dimensional feature vector per ICU stay.

Feature vector layout (32 dimensions):
    6 vital signs × 5 statistics + 2 trend slopes = 32

    Vital signs used (6):
        heart_rate, systolic_bp, diastolic_bp,
        mean_bp, respiratory_rate, spo2
    (temperature_c excluded to hit exactly 32 dims)

    Statistics per vital (5):
        mean, std, min, max, last_value

    Extra features (2):
        heart_rate_slope  — linear trend slope (units/hour)
        spo2_slope        — linear trend slope (units/hour)

    Total: 6×5 + 2 = 32

Input:  preprocessed vitals DataFrame (from VitalsPreprocessor + TimeAligner)
Output: np.ndarray of shape (n_stays, 32)
"""

import logging

import numpy as np
import pandas as pd
from scipy import stats

from configs.model_config import MODEL_CFG
from configs.data_config import VITAL_ITEMIDS

logger = logging.getLogger(__name__)

# Expected output dimension
VITALS_FEATURE_DIM = MODEL_CFG.vitals_dim  # 32

# 6 vitals × 5 stats = 30, + 2 slopes = 32
STAT_FUNCTIONS = ["mean", "std", "min", "max", "last"]
_VITALS_USED = [
    "heart_rate", "systolic_bp", "diastolic_bp",
    "mean_bp", "respiratory_rate", "spo2",
]
_SLOPE_VITALS = ["heart_rate", "spo2"]


class VitalsPipeline:
    """
    Extracts 32-dimensional temporal feature vectors from vital sign time-series.

    For each ICU stay, computes summary statistics (mean, std, min, max,
    last value) for each vital sign over the first icu_hours_window hours,
    plus linear trend slopes for heart_rate and spo2.

    Parameters
    ----------
    icu_hours_window : int
        Hours from ICU admission to include. Defaults to 48.
    compute_trend_slope : bool
        Whether to include linear trend slopes. Default True.
    missing_fill : float
        Value for vital signs not measured in this stay. Default 0.0.
    """

    def __init__(
        self,
        icu_hours_window: int = 48,
        compute_trend_slope: bool = True,
        missing_fill: float = 0.0,
    ) -> None:
        self.icu_hours_window = icu_hours_window
        self.compute_trend_slope = compute_trend_slope
        self.missing_fill = missing_fill
        self._feature_names: list[str] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_for_stay(
        self,
        vitals_df: pd.DataFrame,
        stay_id: int,
    ) -> np.ndarray:
        """
        Extract the 32-dim vitals feature vector for a single ICU stay.

        Parameters
        ----------
        vitals_df : pd.DataFrame
            Preprocessed vital signs with columns:
            stay_id, label, valuenum, hours_from_admission (or charttime).
        stay_id : int
            ICU stay ID.

        Returns
        -------
        np.ndarray
            Float32 array of shape (32,).
        """
        # Filter to this stay
        stay_data = vitals_df[vitals_df["stay_id"] == stay_id].copy()

        # Apply time window if hours_from_admission is available
        if "hours_from_admission" in stay_data.columns:
            stay_data = stay_data[
                stay_data["hours_from_admission"] <= self.icu_hours_window
            ]

        vector = self._compute_statistics(stay_data)
        assert vector.shape == (VITALS_FEATURE_DIM,), (
            f"Expected {VITALS_FEATURE_DIM}, got {vector.shape}"
        )
        return vector

    def extract_batch(
        self,
        vitals_df: pd.DataFrame,
        stay_ids: list[int],
    ) -> np.ndarray:
        """
        Extract vitals feature vectors for a list of ICU stays.

        Returns
        -------
        np.ndarray
            Float32 array of shape (len(stay_ids), 32).
        """
        from tqdm import tqdm
        features = []
        for stay_id in tqdm(stay_ids, desc="Vitals feature extraction"):
            vec = self.extract_for_stay(vitals_df, stay_id)
            features.append(vec)
        return np.stack(features, axis=0)

    def get_feature_names(self) -> list[str]:
        """
        Return the name for each of the 32 dimensions.

        Returns
        -------
        list[str]
            e.g. ["heart_rate_mean", "heart_rate_std", ...,
                  "spo2_last", "heart_rate_slope", "spo2_slope"]
        """
        if self._feature_names is not None:
            return self._feature_names

        names = []
        for vital in _VITALS_USED:
            for stat in STAT_FUNCTIONS:
                names.append(f"{vital}_{stat}")
        for vital in _SLOPE_VITALS:
            names.append(f"{vital}_slope")

        self._feature_names = names
        return self._feature_names

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_statistics(self, stay_data: pd.DataFrame) -> np.ndarray:
        """
        Compute temporal statistics for each vital sign in a single stay.

        Parameters
        ----------
        stay_data : pd.DataFrame
            Vital measurements for one stay within the time window.
            Columns include: label, valuenum, hours_from_admission.

        Returns
        -------
        np.ndarray
            Float32 array of shape (VITALS_FEATURE_DIM,).
        """
        # Determine which column holds the vital name
        name_col = "vital_name" if "vital_name" in stay_data.columns else "label"

        # Determine which column holds the numeric value
        val_col = "valuenum" if "valuenum" in stay_data.columns else "value"

        # Build label→vital_name lookup from VITAL_ITEMIDS
        label_map = VITAL_ITEMIDS.label_map()  # {itemid: vital_key}

        features = []

        # 6 vitals × 5 stats = 30
        for vital in _VITALS_USED:
            # Match by vital_name column OR by label column containing the key
            mask = stay_data[name_col].str.lower().str.contains(
                vital.replace("_", " "), na=False
            )
            # Also try exact match on mapped vital_name
            if "itemid" in stay_data.columns:
                itemid_mask = stay_data["itemid"].map(label_map) == vital
                mask = mask | itemid_mask

            values = pd.to_numeric(
                stay_data[mask][val_col], errors="coerce"
            ).dropna()

            if len(values) == 0:
                features.extend([self.missing_fill] * len(STAT_FUNCTIONS))
            else:
                features.append(float(values.mean()))
                std = float(values.std()) if len(values) > 1 else 0.0
                features.append(std)
                features.append(float(values.min()))
                features.append(float(values.max()))
                features.append(float(values.iloc[-1]))

        # 2 trend slopes
        for vital in _SLOPE_VITALS:
            mask = stay_data[name_col].str.lower().str.contains(
                vital.replace("_", " "), na=False
            )
            vital_rows = stay_data[mask].copy()
            vital_rows["_num"] = pd.to_numeric(vital_rows[val_col],
                                               errors="coerce")
            vital_rows = vital_rows.dropna(subset=["_num"])
            if (
                self.compute_trend_slope
                and len(vital_rows) >= 3
                and "hours_from_admission" in vital_rows.columns
            ):
                slope = self._compute_trend_slope(
                    vital_rows["_num"].values,
                    vital_rows["hours_from_admission"].values,
                )
            else:
                slope = 0.0
            features.append(slope)

        # Trim or pad to exactly VITALS_FEATURE_DIM
        features = features[:VITALS_FEATURE_DIM]
        features += [self.missing_fill] * (VITALS_FEATURE_DIM - len(features))
        return np.array(features, dtype=np.float32)

    def _compute_trend_slope(
        self,
        values: np.ndarray,
        times: np.ndarray,
    ) -> float:
        """
        Compute the linear trend slope of a vital sign time series.

        Uses scipy.stats.linregress to fit a line to (time, value) pairs.

        Returns
        -------
        float
            Slope in units per hour. Returns 0.0 if insufficient data.
        """
        if len(values) < 3:
            return 0.0
        slope, _, _, _, _ = stats.linregress(times, values)
        return float(slope)


if __name__ == "__main__":
    pipeline = VitalsPipeline(icu_hours_window=48)
    print(f"Vitals feature dim: {VITALS_FEATURE_DIM}")
    names = pipeline.get_feature_names()
    print(f"Feature names ({len(names)}):", names)
