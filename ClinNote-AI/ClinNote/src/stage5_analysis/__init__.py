"""
Stage 5 — Analysis & Generation

Uses the 1024-dim fused representation (from Stage 4) for:
  - In-hospital mortality prediction (evaluation / validation)
  - Clinical summary generation (template-based + LLM-assisted)
  - Anomaly detection in labs and vital signs
  - Temporal trend analysis (SciPy + NumPy)

Exports
-------
MortalityPredictor, SummaryGenerator, AnomalyDetector, TrendAnalyzer
"""

from src.stage5_analysis.mortality_predictor import MortalityPredictor
from src.stage5_analysis.summary_generator import SummaryGenerator
from src.stage5_analysis.anomaly_detector import AnomalyDetector
from src.stage5_analysis.trend_analyzer import TrendAnalyzer

__all__ = ["MortalityPredictor", "SummaryGenerator", "AnomalyDetector", "TrendAnalyzer"]
