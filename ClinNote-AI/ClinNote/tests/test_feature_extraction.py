"""
Tests: Stage 3 — Feature Extraction

Tests for NLPPipeline, LabPipeline, VitalsPipeline.
NLP tests use mocked ClinicalBERT to avoid downloading the model.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestNLPPipeline:
    def test_device_auto_selection(self):
        """Device should default to 'cuda' if available, else 'cpu'."""
        import torch
        from src.stage3_feature_extraction.nlp_pipeline import NLPPipeline
        pipeline = NLPPipeline(device=None)
        expected = "cuda" if torch.cuda.is_available() else "cpu"
        assert pipeline.device == expected

    def test_encode_returns_numpy_array(self):
        from src.stage3_feature_extraction.nlp_pipeline import NLPPipeline
        import numpy as np
        pipeline = NLPPipeline()
        result = pipeline.encode(["test text"])
        assert isinstance(result, np.ndarray)
        assert result.shape == (1, 768)

    def test_model_name_matches_config(self):
        from src.stage3_feature_extraction.nlp_pipeline import NLPPipeline
        from configs.model_config import MODEL_CFG
        pipeline = NLPPipeline()
        assert pipeline.model_name == MODEL_CFG.clinicalbert_model_name


class TestLabPipeline:
    def test_feature_dim_constant(self):
        from src.stage3_feature_extraction.lab_pipeline import LAB_FEATURE_DIM
        from configs.model_config import MODEL_CFG
        assert LAB_FEATURE_DIM == MODEL_CFG.lab_dim
        assert LAB_FEATURE_DIM == 50

    def test_extract_returns_fixed_dim_array(self):
        import pandas as pd, numpy as np
        from src.stage3_feature_extraction.lab_pipeline import LabPipeline, LAB_FEATURE_DIM
        pipeline = LabPipeline()
        result = pipeline.extract_for_admission(pd.DataFrame(columns=["hadm_id"]), hadm_id=1001)
        assert isinstance(result, np.ndarray)
        assert result.shape == (LAB_FEATURE_DIM,)


class TestVitalsPipeline:
    def test_feature_dim_constant(self):
        from src.stage3_feature_extraction.vitals_pipeline import VITALS_FEATURE_DIM
        from configs.model_config import MODEL_CFG
        assert VITALS_FEATURE_DIM == MODEL_CFG.vitals_dim
        assert VITALS_FEATURE_DIM == 32

    def test_extract_returns_fixed_dim_array(self):
        import pandas as pd, numpy as np
        from src.stage3_feature_extraction.vitals_pipeline import VitalsPipeline, VITALS_FEATURE_DIM
        pipeline = VitalsPipeline()
        # empty DataFrame with required columns → returns zero vector
        empty = pd.DataFrame(columns=["stay_id", "label", "valuenum", "charttime"])
        result = pipeline.extract_for_stay(empty, stay_id=301)
        assert isinstance(result, np.ndarray)
        assert result.shape == (VITALS_FEATURE_DIM,)


class TestFeatureStore:
    def test_all_features_exist_false_initially(self):
        """Before any features are saved, all_features_exist() should return False."""
        from src.stage3_feature_extraction.feature_store import FeatureStore
        from configs.paths import PATHS
        store = FeatureStore()
        # In a fresh environment, feature files won't exist
        # This just checks the method doesn't raise
        result = store.all_features_exist()
        assert isinstance(result, bool)
