"""
Stage 4 — Fusion Step 3: Cross-Modal Attention (Shared Features)

After modality-specific self-attention produces S_text, S_lab, S_vitals,
cross-modal attention captures information shared across modalities.

The cross-modal attention treats all three modality embeddings as a sequence:
    input_sequence = stack([S_text, S_lab, S_vitals])  # shape: (batch, 3, 256)

A single transformer encoder layer then attends across all three modalities,
allowing each modality to update its representation using information from
the other two.

The output S_common is obtained by mean-pooling or by taking the first token:
    S_common = mean_pool(cross_attn_output)  # shape: (batch, 256)

Purpose: S_common captures findings corroborated by multiple sources
(e.g., elevated creatinine in labs AND mention of renal failure in notes).
The MI Loss (Step 4) then enforces that S_common and S_specific are disentangled.
"""

import torch                    # Tensor operations
import torch.nn as nn           # Module base class

from configs.model_config import MODEL_CFG


class CrossModalAttention(nn.Module):
    """
    Transformer encoder that attends across all three modality embeddings.

    Takes the three modality-specific embeddings (S_text, S_lab, S_vitals)
    and produces a single shared embedding S_common.

    Architecture:
        stack modalities → (batch, 3, 256) →
        [n_layers × TransformerEncoderLayer] →
        mean pool over sequence dim →
        S_common: (batch, 256)

    Parameters
    ----------
    embed_dim : int
        Embedding dimension. Must match projection_dim (256).
    n_heads : int
        Number of cross-attention heads.
    dropout : float
        Attention and FFN dropout rate.
    ffn_dim : int
        Feed-forward hidden dimension.
    n_layers : int
        Number of cross-attention layers.
    pooling : str
        How to aggregate the 3-token sequence to a single vector:
        - "mean" : mean pool over all tokens (recommended)
        - "first": use first token (text-biased)
        - "cls"  : prepend a learnable [CLS] token and use it
    """

    def __init__(
        self,
        embed_dim: int = MODEL_CFG.projection_dim,
        n_heads: int = MODEL_CFG.cross_attn_heads,
        dropout: float = MODEL_CFG.cross_attn_dropout,
        ffn_dim: int = MODEL_CFG.ffn_dim,
        n_layers: int = MODEL_CFG.cross_attn_layers,
        pooling: str = "mean",
    ) -> None:
        super().__init__()
        self.embed_dim = embed_dim
        self.pooling = pooling

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=n_heads,
            dim_feedforward=ffn_dim,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.norm = nn.LayerNorm(embed_dim)
        if pooling == "cls":
            self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))

    def forward(
        self,
        s_text: torch.Tensor,
        s_lab: torch.Tensor,
        s_vitals: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute the shared representation S_common from all three modalities.

        Parameters
        ----------
        s_text : torch.Tensor
            Shape (batch_size, 256) — output of text self-attention.
        s_lab : torch.Tensor
            Shape (batch_size, 256) — output of lab self-attention.
        s_vitals : torch.Tensor
            Shape (batch_size, 256) — output of vitals self-attention.

        Returns
        -------
        torch.Tensor
            S_common of shape (batch_size, 256).
        """
        seq = torch.stack([s_text, s_lab, s_vitals], dim=1)  # (batch, 3, 256)

        if self.pooling == "cls":
            cls = self.cls_token.expand(seq.size(0), -1, -1)
            seq = torch.cat([cls, seq], dim=1)                # (batch, 4, 256)

        out = self.transformer(seq)                            # (batch, seq_len, 256)
        out = self.norm(out)

        if self.pooling == "mean":
            return out.mean(dim=1)
        else:  # "first" or "cls"
            return out[:, 0, :]


if __name__ == "__main__":
    # cross_attn = CrossModalAttention()
    # s_text   = torch.randn(4, 256)
    # s_lab    = torch.randn(4, 256)
    # s_vitals = torch.randn(4, 256)
    # s_common = cross_attn(s_text, s_lab, s_vitals)
    # print(s_common.shape)   # Expected: (4, 256)
    pass
