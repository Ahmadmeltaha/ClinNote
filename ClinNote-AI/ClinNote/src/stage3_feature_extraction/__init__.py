"""
Stage 3 — Parallel Processing Pipelines (Feature Extraction)

Three independent pipelines extract modality-specific feature vectors:
  A. NLP Pipeline      → 768-dim text embeddings (ClinicalBERT [CLS] token)
  B. Lab Pipeline      → 50-dim lab feature vectors (values + anomaly flags)
  C. Vitals Pipeline   → 32-dim vitals feature vectors (temporal statistics)

All extracted features are persisted via FeatureStore for reuse.

Exports
-------
NLPPipeline, LabPipeline, VitalsPipeline, FeatureStore
"""

from src.stage3_feature_extraction.nlp_pipeline import NLPPipeline
from src.stage3_feature_extraction.lab_pipeline import LabPipeline
from src.stage3_feature_extraction.vitals_pipeline import VitalsPipeline
from src.stage3_feature_extraction.feature_store import FeatureStore

__all__ = ["NLPPipeline", "LabPipeline", "VitalsPipeline", "FeatureStore"]
