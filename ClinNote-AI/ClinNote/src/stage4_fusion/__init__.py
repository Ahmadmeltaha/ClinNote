"""
Stage 4 — Multimodal Data Fusion (MEDFuse-Inspired Disentangled Transformer)

Implements the 4-step fusion process:
  Step 1: Feature Projection     — project each modality to 256-dim
  Step 2: Self-Attention         — modality-specific features (S_text, S_lab, S_vitals)
  Step 3: Cross-Attention        — modality-shared features (S_common)
  Step 4: MI Loss + Concatenation — disentangle specific/shared; fuse to 1024-dim

Reference: Lyu et al. (2023), "A Multimodal Transformer: Fusing Clinical Notes
With Structured EHR Data for Interpretable In-Hospital Mortality Prediction"
Extended to 3 modalities with MI-based disentanglement.

Exports
-------
ProjectionLayer, ModalitySelfAttention, CrossModalAttention,
VCLUBMILoss, FusionModel, DisentangledTransformer
"""

from src.stage4_fusion.projection import ProjectionLayer
from src.stage4_fusion.self_attention import ModalitySelfAttention
from src.stage4_fusion.cross_attention import CrossModalAttention
from src.stage4_fusion.mi_loss import VCLUBMILoss
from src.stage4_fusion.fusion_model import FusionModel
from src.stage4_fusion.disentangled_transformer import DisentangledTransformer

__all__ = [
    "ProjectionLayer",
    "ModalitySelfAttention",
    "CrossModalAttention",
    "VCLUBMILoss",
    "FusionModel",
    "DisentangledTransformer",
]
