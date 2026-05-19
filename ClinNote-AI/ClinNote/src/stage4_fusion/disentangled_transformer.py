"""
Stage 4 — Disentangled Transformer (Full Architecture)

The DisentangledTransformer is the top-level model that wraps:
  1. FusionModel (4-step feature fusion → 1024-dim h_final)
  2. MortalityHead (1024-dim → binary mortality prediction)

This is the primary nn.Module used for training (scripts/run_fusion_training.py)
and inference (Stage 5 analysis).

Training produces two losses:
  L_task = BCELoss(mortality_pred, label)         — task loss
  L_mi   = vCLUB(S_specific, S_common) × 3       — MI regularization
  L_total = L_task + λ * L_mi                     — total loss (λ = MODEL_CFG.mi_loss_weight)

The CLUB variational network has its own optimizer updated separately from
the main model (two-optimizer training scheme — see run_fusion_training.py).
"""

import torch                    # Core tensor library
import torch.nn as nn           # Module base class

from configs.model_config import MODEL_CFG
from src.stage4_fusion.fusion_model import FusionModel


class MortalityHead(nn.Module):
    """
    Binary classification head for in-hospital mortality prediction.

    Takes the 1024-dim fused representation h_final and produces
    a probability of in-hospital mortality.

    Architecture:
        Linear(1024, 256) → GELU → Dropout → Linear(256, 1) → Sigmoid

    Parameters
    ----------
    input_dim : int
        Input dimension. Defaults to MODEL_CFG.fusion_output_dim (1024).
    hidden_dim : int
        Hidden layer dimension. Defaults to MODEL_CFG.mortality_hidden_dim.
    dropout : float
        Dropout rate.
    """

    def __init__(
        self,
        input_dim: int = MODEL_CFG.fusion_output_dim,
        hidden_dim: int = MODEL_CFG.mortality_hidden_dim,
        dropout: float = MODEL_CFG.mortality_dropout,
    ) -> None:
        super().__init__()

        self.head = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, h_final: torch.Tensor) -> torch.Tensor:
        """
        Parameters
        ----------
        h_final : torch.Tensor
            Fused representation, shape (batch_size, 1024).

        Returns
        -------
        torch.Tensor
            Mortality probability, shape (batch_size, 1).
        """
        return self.head(h_final)


class DisentangledTransformer(nn.Module):
    """
    Full ClinNote model: fusion + mortality prediction.

    Wraps FusionModel and MortalityHead. Used for end-to-end training.

    Parameters
    ----------
    mi_loss_weight : float
        λ coefficient for the MI loss term.
    """

    def __init__(
        self,
        mi_loss_weight: float = MODEL_CFG.mi_loss_weight,
    ) -> None:
        super().__init__()
        self.mi_loss_weight = mi_loss_weight

        self.fusion          = FusionModel()
        self.mortality_head  = MortalityHead()
        self.task_loss_fn    = nn.BCELoss()

    def forward(
        self,
        text_features: torch.Tensor,
        lab_features: torch.Tensor,
        vitals_features: torch.Tensor,
        labels: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        """
        Forward pass through the full model.

        Parameters
        ----------
        text_features : torch.Tensor
            Shape (batch_size, 768).
        lab_features : torch.Tensor
            Shape (batch_size, 50).
        vitals_features : torch.Tensor
            Shape (batch_size, 32).
        labels : torch.Tensor | None
            Binary mortality labels of shape (batch_size, 1).
            If provided, computes the total loss.

        Returns
        -------
        dict[str, torch.Tensor]
            Keys:
              "mortality_prob" : (batch, 1)     — predicted mortality probability
              "h_final"        : (batch, 1024)  — fused representation
              "mi_loss"        : scalar          — MI regularization loss
              "task_loss"      : scalar          — BCE task loss (only if labels provided)
              "total_loss"     : scalar          — L_task + λ * L_mi (only if labels provided)
        """
        h_final, mi_loss = self.fusion(text_features, lab_features, vitals_features)
        mortality_prob   = self.mortality_head(h_final)

        result = {
            "mortality_prob": mortality_prob,
            "h_final":        h_final,
            "mi_loss":        mi_loss,
        }

        if labels is not None:
            task_loss  = self.task_loss_fn(mortality_prob, labels.float())
            total_loss = task_loss + self.mi_loss_weight * mi_loss
            result["task_loss"]  = task_loss
            result["total_loss"] = total_loss

        return result

    def predict(
        self,
        text_features: torch.Tensor,
        lab_features: torch.Tensor,
        vitals_features: torch.Tensor,
        threshold: float = 0.5,
    ) -> torch.Tensor:
        """
        Predict binary mortality labels (0 or 1) at inference time.

        Parameters
        ----------
        (same as forward, without labels)
        threshold : float
            Decision threshold for binary classification.

        Returns
        -------
        torch.Tensor
            Binary predictions of shape (batch_size, 1).
        """
        with torch.no_grad():
            output = self.forward(text_features, lab_features, vitals_features)
            return (output["mortality_prob"] >= threshold).float()

    @property
    def n_parameters(self) -> int:
        """Return total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


if __name__ == "__main__":
    # model = DisentangledTransformer()
    # print(f"Total parameters: {model.n_parameters:,}")
    # text   = torch.randn(4, 768)
    # labs   = torch.randn(4, 50)
    # vitals = torch.randn(4, 32)
    # labels = torch.randint(0, 2, (4, 1))
    # output = model(text, labs, vitals, labels)
    # print("Mortality probs:", output["mortality_prob"].squeeze())
    # print("Total loss:", output["total_loss"].item())
    pass
