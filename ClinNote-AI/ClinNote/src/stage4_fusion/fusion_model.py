"""
Stage 4 — Fusion Model (Complete 4-Step Pipeline)

Combines all four fusion steps into a single PyTorch Module:

    Step 1: Feature Projection     (ModalityProjections)
            text (768) → 256, labs (50) → 256, vitals (32) → 256

    Step 2: Modality-Specific      (ModalitySelfAttention × 3)
            S_text   = SelfAttn(text_proj)
            S_lab    = SelfAttn(lab_proj)
            S_vitals = SelfAttn(vitals_proj)

    Step 3: Modality-Shared        (CrossModalAttention)
            S_common = CrossAttn(S_text, S_lab, S_vitals)

    Step 4: Disentanglement + Concatenation
            MI Loss  = vCLUB(S_text, S_common)
                     + vCLUB(S_lab, S_common)
                     + vCLUB(S_vitals, S_common)
            h_final  = concat([S_text, S_lab, S_vitals, S_common])  → 1024-dim

The 1024-dim h_final is passed to the mortality prediction head (Stage 5).
"""

import torch                    # Core tensor library
import torch.nn as nn           # Module base class

from configs.model_config import MODEL_CFG
from src.stage4_fusion.projection import ModalityProjections
from src.stage4_fusion.self_attention import ModalitySelfAttention
from src.stage4_fusion.cross_attention import CrossModalAttention
from src.stage4_fusion.mi_loss import VCLUBMILoss


class FusionModel(nn.Module):
    """
    Complete multimodal fusion model.

    Input:
        text_features   : (batch, 768)
        lab_features    : (batch, 50)
        vitals_features : (batch, 32)

    Output:
        h_final : (batch, 1024)  — concatenated disentangled representation
        mi_loss : scalar tensor   — vCLUB MI loss for regularization

    Parameters
    ----------
    text_dim : int
    lab_dim : int
    vitals_dim : int
    projection_dim : int
    fusion_output_dim : int
    """

    def __init__(
        self,
        text_dim: int = MODEL_CFG.text_dim,
        lab_dim: int = MODEL_CFG.lab_dim,
        vitals_dim: int = MODEL_CFG.vitals_dim,
        projection_dim: int = MODEL_CFG.projection_dim,
        fusion_output_dim: int = MODEL_CFG.fusion_output_dim,
    ) -> None:
        super().__init__()
        self.projection_dim = projection_dim
        self.fusion_output_dim = fusion_output_dim

        # Step 1: Projections
        self.projections = ModalityProjections(text_dim, lab_dim, vitals_dim, projection_dim)

        # Step 2: Modality-specific self-attention (one per modality)
        self.text_self_attn   = ModalitySelfAttention(embed_dim=projection_dim)
        self.lab_self_attn    = ModalitySelfAttention(embed_dim=projection_dim)
        self.vitals_self_attn = ModalitySelfAttention(embed_dim=projection_dim)

        # Step 3: Cross-modal attention
        self.cross_attn = CrossModalAttention(embed_dim=projection_dim)

        # Step 4: MI Loss estimators (one per modality pair)
        self.mi_text_common   = VCLUBMILoss(projection_dim, projection_dim)
        self.mi_lab_common    = VCLUBMILoss(projection_dim, projection_dim)
        self.mi_vitals_common = VCLUBMILoss(projection_dim, projection_dim)

    def forward(
        self,
        text_features: torch.Tensor,
        lab_features: torch.Tensor,
        vitals_features: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Run the complete 4-step fusion pipeline.

        Parameters
        ----------
        text_features : torch.Tensor
            Shape (batch_size, 768).
        lab_features : torch.Tensor
            Shape (batch_size, 50).
        vitals_features : torch.Tensor
            Shape (batch_size, 32).

        Returns
        -------
        tuple[torch.Tensor, torch.Tensor]
            h_final : (batch_size, 1024) — fused representation
            mi_loss : scalar             — total MI loss (sum across 3 modalities)
        """
        # Step 1: Project all modalities to 256-dim
        text_p, lab_p, vitals_p = self.projections(text_features, lab_features, vitals_features)

        # Step 2: Modality-specific self-attention
        s_text   = self.text_self_attn(text_p)
        s_lab    = self.lab_self_attn(lab_p)
        s_vitals = self.vitals_self_attn(vitals_p)

        # Step 3: Cross-modal shared features
        s_common = self.cross_attn(s_text, s_lab, s_vitals)

        # Step 4: Compute MI losses
        mi_loss = (
            self.mi_text_common(s_text, s_common)
            + self.mi_lab_common(s_lab, s_common)
            + self.mi_vitals_common(s_vitals, s_common)
        )

        # Concatenate all representations
        h_final = torch.cat([s_text, s_lab, s_vitals, s_common], dim=-1)  # (batch, 1024)

        return h_final, mi_loss

    def get_representations(
        self,
        text_features: torch.Tensor,
        lab_features: torch.Tensor,
        vitals_features: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        """
        Return intermediate representations for interpretability analysis.

        Parameters
        ----------
        (same as forward)

        Returns
        -------
        dict[str, torch.Tensor]
            Keys: "s_text", "s_lab", "s_vitals", "s_common", "h_final".
        """
        text_p, lab_p, vitals_p = self.projections(text_features, lab_features, vitals_features)
        s_text   = self.text_self_attn(text_p)
        s_lab    = self.lab_self_attn(lab_p)
        s_vitals = self.vitals_self_attn(vitals_p)
        s_common = self.cross_attn(s_text, s_lab, s_vitals)
        h_final  = torch.cat([s_text, s_lab, s_vitals, s_common], dim=-1)
        return {
            "s_text":   s_text,
            "s_lab":    s_lab,
            "s_vitals": s_vitals,
            "s_common": s_common,
            "h_final":  h_final,
        }

    @property
    def n_parameters(self) -> int:
        """Return total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


if __name__ == "__main__":
    # model = FusionModel()
    # print(f"Model parameters: {model.n_parameters:,}")
    # text   = torch.randn(4, 768)
    # labs   = torch.randn(4, 50)
    # vitals = torch.randn(4, 32)
    # h_final, mi_loss = model(text, labs, vitals)
    # print(h_final.shape)   # Expected: (4, 1024)
    # print("MI Loss:", mi_loss.item())
    pass
