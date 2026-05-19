"""
Stage 1 — Data Sources

Loads raw MIMIC-IV and MIMIC-IV-Note tables from disk and exposes them as
clean pandas DataFrames. No preprocessing happens here — only I/O and
basic schema validation.

Exports
-------
NotesLoader, LabsLoader, VitalsLoader, PatientLoader, CohortBuilder
"""

from src.stage1_data_loading.notes_loader import NotesLoader
from src.stage1_data_loading.labs_loader import LabsLoader
from src.stage1_data_loading.vitals_loader import VitalsLoader
from src.stage1_data_loading.patient_loader import PatientLoader
from src.stage1_data_loading.cohort_builder import CohortBuilder

__all__ = [
    "NotesLoader",
    "LabsLoader",
    "VitalsLoader",
    "PatientLoader",
    "CohortBuilder",
]
