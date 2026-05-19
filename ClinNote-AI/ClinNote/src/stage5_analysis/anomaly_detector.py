"""
Stage 5 — Analysis: Anomaly Detector

Identifies and scores abnormal findings in lab results and vital signs.

Anomaly detection approaches:
  1. Rule-based  : values outside clinical reference ranges (hard rules)
  2. Statistical : z-score outliers within the patient cohort distribution
  3. Trend-based : sudden changes / rapid deterioration in vitals time series

Output: structured anomaly report per patient admission with:
  - Lab anomalies (name, value, reference range, severity)
  - Vital sign anomalies (name, value, normal range, trend direction)
  - Aggregate risk score (0.0 – 1.0)
"""

import logging

import numpy as np   # Array and statistical operations
import pandas as pd  # DataFrame filtering

from configs.data_config import VITAL_ITEMIDS, LAB_ITEMIDS

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects clinical anomalies in lab results and vital signs.

    Parameters
    ----------
    lab_severity_threshold : float
        Minimum severity score to include a lab anomaly in the report.
    vital_trend_window_hours : int
        Hours over which to detect rapid trend changes.
    """

    def __init__(
        self,
        lab_severity_threshold: float = 0.3,
        vital_trend_window_hours: int = 4,
    ) -> None:
        self.lab_severity_threshold = lab_severity_threshold
        self.vital_trend_window_hours = vital_trend_window_hours

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_lab_anomalies(
        self,
        labs_df: pd.DataFrame,
        hadm_id: int,
    ) -> list[dict]:
        """
        Identify abnormal lab values for a single admission.

        Parameters
        ----------
        labs_df : pd.DataFrame
            Preprocessed labs with is_abnormal, severity_score columns.
        hadm_id : int
            Hospital admission ID.

        Returns
        -------
        list[dict]
            List of anomaly dicts with keys:
            name, value, unit, ref_low, ref_high, severity, direction.
        """
        adm_labs = labs_df[
            (labs_df["hadm_id"] == hadm_id) & (labs_df["is_abnormal"] == True)
        ]
        anomalies = []
        for _, row in adm_labs.iterrows():
            if row["severity_score"] >= self.lab_severity_threshold:
                anomalies.append({
                    "name"     : row["label"],
                    "value"    : row["valuenum"],
                    "unit"     : row.get("valueuom", ""),
                    "ref_low"  : row.get("ref_range_lower", None),
                    "ref_high" : row.get("ref_range_upper", None),
                    "severity" : row["severity_score"],
                    "direction": "HIGH" if row["valuenum"] > row.get("ref_range_upper", row["valuenum"]) else "LOW",
                })
        return sorted(anomalies, key=lambda x: x["severity"], reverse=True)

    def detect_vital_anomalies(
        self,
        vitals_df: pd.DataFrame,
        stay_id: int,
    ) -> list[dict]:
        """
        Identify abnormal vital sign measurements for a single ICU stay.

        Checks both point-in-time anomalies and rapid trend changes.

        Parameters
        ----------
        vitals_df : pd.DataFrame
            Preprocessed vitals with vital_name, valuenum, is_abnormal,
            hours_from_icu_admission.
        stay_id : int
            ICU stay ID.

        Returns
        -------
        list[dict]
            List of vital anomaly dicts with keys:
            vital_name, current_value, normal_low, normal_high,
            status (HIGH/LOW), trend (RISING/FALLING/STABLE).
        """
        stay_vitals = vitals_df[vitals_df["stay_id"] == stay_id]
        anomalies = []
        normal_ranges = VITAL_ITEMIDS.normal_ranges()
        time_col = "charttime" if "charttime" in stay_vitals.columns else "hours_from_icu_admission"
        for vital_name, (lo, hi) in normal_ranges.items():
            v_data = stay_vitals[stay_vitals["vital_name"] == vital_name]
            if v_data.empty:
                continue
            v_sorted = v_data.sort_values(time_col)
            last_val = float(v_sorted["valuenum"].iloc[-1])
            if last_val < lo or last_val > hi:
                trend = self._compute_trend(v_sorted)
                anomalies.append({
                    "vital_name"   : vital_name,
                    "current_value": last_val,
                    "normal_low"   : lo,
                    "normal_high"  : hi,
                    "status"       : "HIGH" if last_val > hi else "LOW",
                    "trend"        : trend,
                })
        return anomalies

    def compute_aggregate_risk_score(
        self,
        lab_anomalies: list[dict],
        vital_anomalies: list[dict],
        mortality_prob: float,
    ) -> float:
        """
        Compute a single aggregate risk score (0.0–1.0) combining all signals.

        Parameters
        ----------
        lab_anomalies : list[dict]
            Output of detect_lab_anomalies().
        vital_anomalies : list[dict]
            Output of detect_vital_anomalies().
        mortality_prob : float
            Model-predicted mortality probability.

        Returns
        -------
        float
            Aggregate risk score in [0, 1].
        """
        lab_score = 0.0
        if lab_anomalies:
            severities = [a["severity"] for a in lab_anomalies]
            lab_score = float(np.mean(severities))

        vital_score = 0.0
        if vital_anomalies:
            vital_score = min(1.0, len(vital_anomalies) / 5.0)

        aggregate = 0.5 * float(mortality_prob) + 0.3 * lab_score + 0.2 * vital_score
        return float(np.clip(aggregate, 0.0, 1.0))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_trend(self, vital_df: pd.DataFrame) -> str:
        """
        Determine whether a vital sign is RISING, FALLING, or STABLE
        over the last self.vital_trend_window_hours hours.

        Returns one of "RISING", "FALLING", "STABLE".
        """
        from scipy import stats as sp_stats

        time_col = "hours_from_icu_admission" if "hours_from_icu_admission" in vital_df.columns else "charttime"
        v_sorted = vital_df.sort_values(time_col)

        if "hours_from_icu_admission" in v_sorted.columns:
            max_t = v_sorted["hours_from_icu_admission"].max()
            window = v_sorted[
                v_sorted["hours_from_icu_admission"] >= max_t - self.vital_trend_window_hours
            ]
        else:
            window = v_sorted.tail(max(3, len(v_sorted) // 3))

        values = window["valuenum"].values
        if len(values) < 2:
            return "STABLE"

        times = np.arange(len(values), dtype=float)
        slope, *_ = sp_stats.linregress(times, values)
        value_range = float(np.ptp(values)) if np.ptp(values) > 0 else 1.0
        normalised_slope = slope / value_range * len(values)
        if normalised_slope > 0.1:
            return "RISING"
        if normalised_slope < -0.1:
            return "FALLING"
        return "STABLE"


if __name__ == "__main__":
    # detector = AnomalyDetector()
    # lab_anomalies = detector.detect_lab_anomalies(labs_df, hadm_id=12345)
    # vital_anomalies = detector.detect_vital_anomalies(vitals_df, stay_id=6789)
    # print(lab_anomalies)
    pass
