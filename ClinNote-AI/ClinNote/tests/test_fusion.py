"""
Tests: Stage 4 — Multimodal Fusion Model

Tests model config consistency, module imports, and expected tensor shapes.
PyTorch model forward passes are tested once modules are implemented.
"""

import pytest


class TestModelConfig:
    def test_fusion_output_dim_consistency(self):
        from configs.model_config import ModelConfig
        cfg = ModelConfig()
        assert cfg.fusion_output_dim == 4 * cfg.projection_dim

    def test_invalid_fusion_dim_raises(self):
        from configs.model_config import ModelConfig
        with pytest.raises(ValueError):
            ModelConfig(projection_dim=256, fusion_output_dim=999)  # wrong


class TestProjectionLayer:
    def test_module_importable(self):
        from src.stage4_fusion.projection import ProjectionLayer, ModalityProjections
        assert ProjectionLayer is not None
        assert ModalityProjections is not None

    def test_output_shape(self):
        import torch
        from src.stage4_fusion.projection import ProjectionLayer
        layer = ProjectionLayer(input_dim=768, output_dim=256)
        x = torch.randn(4, 768)
        out = layer(x)
        assert out.shape == (4, 256)

    def test_modality_projections_output_shapes(self):
        import torch
        from src.stage4_fusion.projection import ModalityProjections
        proj = ModalityProjections()
        t, l, v = proj(torch.randn(4, 768), torch.randn(4, 50), torch.randn(4, 32))
        assert t.shape == l.shape == v.shape == (4, 256)


class TestFusionModuleImports:
    """Smoke test: all fusion modules must be importable without error."""

    def test_import_self_attention(self):
        from src.stage4_fusion.self_attention import ModalitySelfAttention, SelfAttentionLayer
        assert ModalitySelfAttention is not None

    def test_import_cross_attention(self):
        from src.stage4_fusion.cross_attention import CrossModalAttention
        assert CrossModalAttention is not None

    def test_import_mi_loss(self):
        from src.stage4_fusion.mi_loss import VCLUBMILoss
        assert VCLUBMILoss is not None

    def test_import_fusion_model(self):
        from src.stage4_fusion.fusion_model import FusionModel
        assert FusionModel is not None

    def test_import_disentangled_transformer(self):
        from src.stage4_fusion.disentangled_transformer import DisentangledTransformer, MortalityHead
        assert DisentangledTransformer is not None
        assert MortalityHead is not None


class TestFusionForwardPass:
    """End-to-end forward pass shape and value checks."""

    def test_fusion_model_output_shapes(self):
        import torch
        from src.stage4_fusion.fusion_model import FusionModel
        model = FusionModel()
        h, mi = model(torch.randn(4, 768), torch.randn(4, 50), torch.randn(4, 32))
        assert h.shape == (4, 1024)
        assert mi.ndim == 0  # scalar

    def test_disentangled_transformer_with_labels(self):
        import torch
        from src.stage4_fusion.disentangled_transformer import DisentangledTransformer
        model = DisentangledTransformer()
        labels = torch.randint(0, 2, (4, 1))
        out = model(torch.randn(4, 768), torch.randn(4, 50), torch.randn(4, 32), labels)
        assert out["mortality_prob"].shape == (4, 1)
        assert out["h_final"].shape == (4, 1024)
        assert "total_loss" in out
        assert "task_loss"  in out

    def test_mortality_prob_in_zero_one(self):
        import torch
        from src.stage4_fusion.disentangled_transformer import DisentangledTransformer
        model = DisentangledTransformer()
        out = model(torch.randn(8, 768), torch.randn(8, 50), torch.randn(8, 32))
        probs = out["mortality_prob"]
        assert (probs >= 0).all() and (probs <= 1).all()

    def test_n_parameters_positive(self):
        from src.stage4_fusion.disentangled_transformer import DisentangledTransformer
        model = DisentangledTransformer()
        assert model.n_parameters > 0


class TestMILossConfig:
    def test_mi_loss_weight(self):
        from configs.model_config import MODEL_CFG
        assert 0.0 <= MODEL_CFG.mi_loss_weight <= 1.0

    def test_club_hidden_dim(self):
        from configs.model_config import MODEL_CFG
        assert MODEL_CFG.club_hidden_dim > 0
