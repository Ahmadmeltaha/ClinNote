"""
Stage 6 — Clinical Output: Alert Generator

Generates clinical alerts and warnings based on:
  - Lab anomalies with HIGH severity scores
  - Vital signs outside critical thresholds (not just normal range)
  - Rapid deterioration patterns detected by TrendAnalyzer
  - High predicted mortality probability (> 0.30)

Alerts have three priority levels:
  - CRITICAL : immediate clinical attention required
  - WARNING  : close monitoring recommended
  - INFO     : notable finding, no immediate action required

These alerts are embedded in the patient summary and displayed prominently
in Ahmad Meltaha's web dashboard.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Critical thresholds — stricter than normal range
CRITICAL_VITAL_THRESHOLDS: dict[str, tuple[float, float]] = {
    "heart_rate":       (40.0, 150.0),   # HR < 40 or > 150
    "systolic_bp":      (80.0, 180.0),   # SBP < 80 or > 180
    "respiratory_rate": (8.0, 35.0),     # RR < 8 or > 35
    "spo2":             (88.0, 100.0),   # SpO2 < 88%
    "temperature_c":    (35.0, 40.5),    # Temp < 35 or > 40.5
}

CRITICAL_LAB_SEVERITY_THRESHOLD = 0.7   # severity_score > 0.7 → CRITICAL


@dataclass
class ClinicalAlert:
    """Represents a single clinical alert."""
    priority: str                          # "CRITICAL" | "WARNING" | "INFO"
    category: str                          # "LAB" | "VITAL" | "MORTALITY" | "TREND"
    title: str                             # Short alert title
    message: str                           # Detailed alert message
    value: float | None = None             # Measured value (if applicable)
    threshold: float | None = None         # Threshold that was violated
    generated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "priority"    : self.priority,
            "category"    : self.category,
            "title"       : self.title,
            "message"     : self.message,
            "value"       : self.value,
            "threshold"   : self.threshold,
            "generated_at": self.generated_at,
        }


class AlertGenerator:
    """
    Generates clinical alerts from anomaly detection outputs.

    Parameters
    ----------
    mortality_warning_threshold : float
        Mortality probability above which a WARNING alert is generated.
    mortality_critical_threshold : float
        Mortality probability above which a CRITICAL alert is generated.
    """

    def __init__(
        self,
        mortality_warning_threshold: float = 0.25,
        mortality_critical_threshold: float = 0.40,
    ) -> None:
        self.mortality_warning_threshold = mortality_warning_threshold
        self.mortality_critical_threshold = mortality_critical_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_all_alerts(
        self,
        lab_anomalies: list[dict],
        vital_anomalies: list[dict],
        mortality_prob: float,
        deterioration_detected: bool = False,
    ) -> list[ClinicalAlert]:
        """
        Generate all alerts for a patient.

        Parameters
        ----------
        lab_anomalies : list[dict]
            From AnomalyDetector.detect_lab_anomalies().
        vital_anomalies : list[dict]
            From AnomalyDetector.detect_vital_anomalies().
        mortality_prob : float
            Predicted mortality probability.
        deterioration_detected : bool
            True if TrendAnalyzer flagged rapid deterioration.

        Returns
        -------
        list[ClinicalAlert]
            Alerts sorted by priority (CRITICAL first).
        """
        alerts: list[ClinicalAlert] = []
        alerts.extend(self._generate_lab_alerts(lab_anomalies))
        alerts.extend(self._generate_vital_alerts(vital_anomalies))
        alerts.extend(self._generate_mortality_alert(mortality_prob))
        if deterioration_detected:
            alerts.append(self._generate_deterioration_alert())
        priority_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        return sorted(alerts, key=lambda a: priority_order[a.priority])

    def to_dict_list(self, alerts: list[ClinicalAlert]) -> list[dict]:
        """Convert a list of ClinicalAlert objects to JSON-serializable dicts."""
        return [alert.to_dict() for alert in alerts]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_lab_alerts(self, lab_anomalies: list[dict]) -> list[ClinicalAlert]:
        """Generate alerts for critical lab anomalies."""
        alerts = []
        for lab in lab_anomalies:
            severity = lab.get("severity", 0.0)
            name     = lab.get("name", "Unknown")
            value    = lab.get("value")
            direction = lab.get("direction", "")
            if severity >= CRITICAL_LAB_SEVERITY_THRESHOLD:
                priority = "CRITICAL"
                msg = f"{name} is critically {direction.lower()} at {value} (severity {severity:.2f})."
            else:
                priority = "WARNING"
                msg = f"{name} is {direction.lower()} at {value} — monitor closely."
            alerts.append(ClinicalAlert(
                priority=priority, category="LAB",
                title=f"{name} {direction}",
                message=msg, value=value, threshold=severity,
            ))
        return alerts

    def _generate_vital_alerts(self, vital_anomalies: list[dict]) -> list[ClinicalAlert]:
        """Generate alerts for vital signs outside critical thresholds."""
        alerts = []
        for vital in vital_anomalies:
            name  = vital.get("vital_name", "Unknown")
            value = vital.get("current_value")
            status = vital.get("status", "")
            trend  = vital.get("trend", "STABLE")
            lo, hi = CRITICAL_VITAL_THRESHOLDS.get(name, (None, None))
            is_critical = False
            if value is not None and lo is not None:
                is_critical = value < lo or value > hi
            priority = "CRITICAL" if is_critical else "WARNING"
            trend_str = f" and {trend.lower()}" if trend != "STABLE" else ""
            alerts.append(ClinicalAlert(
                priority=priority, category="VITAL",
                title=f"{name} {status}",
                message=f"{name} is {status.lower()} at {value}{trend_str}.",
                value=value,
            ))
        return alerts

    def _generate_mortality_alert(self, mortality_prob: float) -> list[ClinicalAlert]:
        """Generate a mortality risk alert if above threshold."""
        if mortality_prob >= self.mortality_critical_threshold:
            return [ClinicalAlert(
                priority="CRITICAL", category="MORTALITY",
                title="High Mortality Risk",
                message=f"Predicted in-hospital mortality is {mortality_prob*100:.1f}% — immediate review recommended.",
                value=mortality_prob,
                threshold=self.mortality_critical_threshold,
            )]
        elif mortality_prob >= self.mortality_warning_threshold:
            return [ClinicalAlert(
                priority="WARNING", category="MORTALITY",
                title="Elevated Mortality Risk",
                message=f"Predicted in-hospital mortality is {mortality_prob*100:.1f}% — close monitoring advised.",
                value=mortality_prob,
                threshold=self.mortality_warning_threshold,
            )]
        return []

    def _generate_deterioration_alert(self) -> ClinicalAlert:
        """Generate a CRITICAL alert when rapid deterioration is detected."""
        return ClinicalAlert(
            priority="CRITICAL", category="TREND",
            title="Rapid Clinical Deterioration Detected",
            message="Multiple vital signs are worsening simultaneously. Immediate clinical assessment required.",
        )


if __name__ == "__main__":
    # generator = AlertGenerator()
    # alerts = generator.generate_all_alerts(lab_anomalies, vital_anomalies, mortality_prob=0.35)
    # for alert in alerts:
    #     print(f"[{alert.priority}] {alert.title}: {alert.message}")
    pass
