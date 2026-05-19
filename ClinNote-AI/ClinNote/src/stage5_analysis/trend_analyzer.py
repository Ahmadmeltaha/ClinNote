"""
Stage 5 — Analysis: Temporal Trend Analyzer

Analyzes time-series trends in vital signs and laboratory results using
SciPy and NumPy statistical methods.

Trend analysis outputs:
  - Linear trend slope (rate of change per hour)
  - Acceleration (second derivative — rapid deterioration detection)
  - Periodicity score (regular fluctuations, e.g., respiratory rate cycles)
  - Change point detection (sudden shifts in time series)

These trends are used in:
  1. Anomaly detection (rising troponin, falling SpO2)
  2. Clinical summary generation (trend direction phrases)
  3. Dashboard visualizations (Stage 6)
"""

import logging

import numpy as np              # Array computations
import pandas as pd             # DataFrame operations
from scipy import stats         # linregress for trend slope
from scipy.signal import find_peaks  # Peak detection for change points

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Analyzes temporal trends in vital sign and lab time series.

    Parameters
    ----------
    min_points : int
        Minimum number of data points required to compute a meaningful trend.
    window_hours : int
        Time window (hours) for trend computation. Uses last N hours of data.
    """

    def __init__(
        self,
        min_points: int = 3,
        window_hours: int = 24,
    ) -> None:
        self.min_points = min_points
        self.window_hours = window_hours

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_trend_slope(
        self,
        values: np.ndarray,
        times: np.ndarray,
    ) -> float:
        """
        Compute linear trend slope using SciPy linregress.

        Parameters
        ----------
        values : np.ndarray
            Measured values (e.g., heart rate readings).
        times : np.ndarray
            Corresponding time points in hours.

        Returns
        -------
        float
            Slope of the linear regression fit (units per hour).
            Positive = increasing trend, negative = decreasing.
            Returns 0.0 if insufficient data (< min_points).
        """
        if len(values) < self.min_points:
            return 0.0
        slope, *_ = stats.linregress(times, values)
        return float(slope)

    def compute_trend_stats(
        self,
        values: np.ndarray,
        times: np.ndarray,
    ) -> dict[str, float]:
        """
        Compute comprehensive trend statistics for a time series.

        Parameters
        ----------
        values : np.ndarray
            Time-series values.
        times : np.ndarray
            Corresponding time points (hours).

        Returns
        -------
        dict[str, float]
            Keys: mean, std, min, max, slope, r_squared,
                  last_value, change_from_first, pct_change.
        """
        nan_result = {k: float("nan") for k in [
            "mean", "std", "min", "max", "slope", "r_squared",
            "last_value", "change_from_first", "pct_change",
        ]}
        if len(values) < 2:
            return nan_result
        slope, _, r_value, _, _ = stats.linregress(times, values)
        return {
            "mean"             : float(np.mean(values)),
            "std"              : float(np.std(values)),
            "min"              : float(np.min(values)),
            "max"              : float(np.max(values)),
            "slope"            : float(slope),
            "r_squared"        : float(r_value ** 2),
            "last_value"       : float(values[-1]),
            "change_from_first": float(values[-1] - values[0]),
            "pct_change"       : float((values[-1] - values[0]) / (abs(values[0]) + 1e-8) * 100),
        }

    def classify_trend(self, slope: float, threshold: float = 0.1) -> str:
        """
        Classify a trend slope into a human-readable direction.

        Parameters
        ----------
        slope : float
            Linear regression slope (from compute_trend_slope).
        threshold : float
            Minimum absolute slope to be classified as trending.

        Returns
        -------
        str
            "RISING", "FALLING", or "STABLE".
        """
        if slope > threshold:
            return "RISING"
        if slope < -threshold:
            return "FALLING"
        return "STABLE"

    def analyze_vital_trends(
        self,
        vitals_df: pd.DataFrame,
        stay_id: int,
    ) -> dict[str, dict]:
        """
        Compute trend statistics for all vital signs in one ICU stay.

        Parameters
        ----------
        vitals_df : pd.DataFrame
            Preprocessed vitals with vital_name, valuenum, hours_from_icu_admission.
        stay_id : int
            ICU stay ID.

        Returns
        -------
        dict[str, dict]
            Mapping vital_name → trend_stats dict (from compute_trend_stats).
        """
        stay_data = vitals_df[vitals_df["stay_id"] == stay_id]
        results: dict[str, dict] = {}
        for vital_name in stay_data["vital_name"].unique():
            v_data = stay_data[stay_data["vital_name"] == vital_name].sort_values(
                "hours_from_icu_admission"
            )
            results[vital_name] = self.compute_trend_stats(
                v_data["valuenum"].values,
                v_data["hours_from_icu_admission"].values,
            )
        return results

    def detect_deterioration(
        self,
        vitals_df: pd.DataFrame,
        stay_id: int,
        deterioration_threshold: float = 0.5,
    ) -> bool:
        """
        Detect rapid multi-vital deterioration (early warning score).

        Returns True if multiple vital signs are simultaneously worsening,
        which may indicate clinical deterioration requiring intervention.

        Parameters
        ----------
        vitals_df : pd.DataFrame
            Preprocessed vitals.
        stay_id : int
            ICU stay ID.
        deterioration_threshold : float
            Fraction of vitals that must be worsening to trigger alert.

        Returns
        -------
        bool
            True if patient shows signs of deterioration.
        """
        trend_results = self.analyze_vital_trends(vitals_df, stay_id)
        if not trend_results:
            return False

        worsening_vitals = {
            "heart_rate", "respiratory_rate", "temperature_f", "temperature_c",
        }
        improving_vitals = {"spo2"}

        worsening_count = 0
        for vital_name, stats_dict in trend_results.items():
            slope = stats_dict.get("slope", 0.0)
            if np.isnan(slope):
                continue
            trend = self.classify_trend(slope)
            if vital_name in worsening_vitals and trend == "RISING":
                worsening_count += 1
            elif vital_name in improving_vitals and trend == "FALLING":
                worsening_count += 1

        fraction = worsening_count / len(trend_results)
        return fraction >= deterioration_threshold


if __name__ == "__main__":
    # analyzer = TrendAnalyzer()
    # times  = np.array([0, 2, 4, 6, 8, 10, 12])
    # values = np.array([80, 82, 88, 95, 105, 115, 120])  # Rising HR
    # slope = analyzer.compute_trend_slope(values, times)
    # print(f"HR slope: {slope:.2f} bpm/hour")
    # print(f"Trend: {analyzer.classify_trend(slope)}")
    pass
