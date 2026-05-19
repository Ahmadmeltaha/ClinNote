"""
Stage 6 — Clinical Output

Generates and exports structured clinical outputs consumed by:
  - Ahmad Meltaha's web dashboard (JSON API responses)
  - Clinical review documents (PDF reports)
  - Alert/warning systems for abnormal findings

Exports
-------
PatientSummaryBuilder, AlertGenerator, DashboardDataExporter, ReportExporter
"""

from src.stage6_output.patient_summary import PatientSummaryBuilder
from src.stage6_output.alert_generator import AlertGenerator
from src.stage6_output.dashboard_data import DashboardDataExporter
from src.stage6_output.report_exporter import ReportExporter

__all__ = [
    "PatientSummaryBuilder",
    "AlertGenerator",
    "DashboardDataExporter",
    "ReportExporter",
]
