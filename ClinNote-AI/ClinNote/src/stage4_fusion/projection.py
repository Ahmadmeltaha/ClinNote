"""
Stage 4 — Fusion Step 1: Feature Projection Layers

Projects each modality's feature vector to a common 256-dimensional space
before applying attention mechanisms.

Three separate linear projection layers (one per modality):
  text   : Linear(768 → 256)  + LayerNorm + Dropout
  labs   : Linear(50  → 256)  + LayerNorm + Dropout
  vitals : Linear(32  → 256)  + LayerNorm + Dropout

After projection, all three modalities share the same embedding space,
enabling cross-modal attention in Step 3.
"""

import torch                    # PyTorch tensor operations
import torch.nn as nn           # Neural network modules


from configs.model_config import MODEL_CFG


class ProjectionLayer(nn.Module):
    """
    Linear projection + LayerNorm + Dropout for a single modality.

    Parameters
    ----------
    input_dim : int
        Input feature dimension (768 for text, 50 for labs, 32 for vitals).
    output_dim : int
        Projected dimension. Defaults to MODEL_CFG.projection_dim (256).
    dropout : float
        Dropout probability after LayerNorm.
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int = MODEL_CFG.projection_dim,
        dropout: float = MODEL_CFG.self_attn_dropout,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim

        self.linear     = nn.Linear(input_dim, output_dim)
        self.layer_norm = nn.LayerNorm(output_dim)
        self.dropout    = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Project input tensor from input_dim to output_dim.

        Parameters
        ----------
        x : torch.Tensor
            Input tensor of shape (batch_size, input_dim).

        Returns
        -------
        torch.Tensor
            Projected tensor of shape (batch_size, output_dim).
        """
        x = self.linear(x)
        x = self.layer_norm(x)
        x = self.dropout(x)
        return x


class ModalityProjections(nn.Module):
    """
    Container for all three modality projection layers.

    Projects:
      text   (batch, 768) → (batch, 256)
      labs   (batch, 50)  → (batch, 256)
      vitals (batch, 32)  → (batch, 256)

    Parameters
    ----------
    text_dim : int
        Text input dimension. Defaults to MODEL_CFG.text_dim.
    lab_dim : int
        Lab input dimension. Defaults to MODEL_CFG.lab_dim.
    vitals_dim : int
        Vitals input dimension. Defaults to MODEL_CFG.vitals_dim.
    projection_dim : int
        Common output dimension. Defaults to MODEL_CFG.projection_dim.
    dropout : float
        Dropout rate for each projection layer.
    """

    def __init__(
        self,
        text_dim: int = MODEL_CFG.text_dim,
        lab_dim: int = MODEL_CFG.lab_dim,
        vitals_dim: int = MODEL_CFG.vitals_dim,
        projection_dim: int = MODEL_CFG.projection_dim,
        dropout: float = MODEL_CFG.self_attn_dropout,
    ) -> None:
        super().__init__()

        self.text_proj   = ProjectionLayer(text_dim,   projection_dim, dropout)
        self.lab_proj    = ProjectionLayer(lab_dim,    projection_dim, dropout)
        self.vitals_proj = ProjectionLayer(vitals_dim, projection_dim, dropout)

    def forward(
        self,
        text_features: torch.Tensor,
        lab_features: torch.Tensor,
        vitals_features: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Project all three modalities to the common embedding space.

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
        tuple[torch.Tensor, torch.Tensor, torch.Tensor]
            (text_proj, lab_proj, vitals_proj), each shape (batch_size, 256).
        """
        return (
            self.text_proj(text_features),
            self.lab_proj(lab_features),
            self.vitals_proj(vitals_features),
        )


if __name__ == "__main__":
    # proj = ModalityProjections()
    # text = torch.randn(4, 768)    # batch of 4
    # labs = torch.randn(4, 50)
    # vitals = torch.randn(4, 32)
    # t_p, l_p, v_p = proj(text, labs, vitals)
    # print(t_p.shape, l_p.shape, v_p.shape)  # Expected: (4, 256) × 3
    pass
