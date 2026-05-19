"""
Stage 4 — Fusion Step 2: Modality-Specific Self-Attention

Applies multi-head self-attention independently to each projected modality.
This captures modality-specific patterns before cross-modal interaction.

Output:
    S_text   = SelfAttn(text_proj)    — shape (batch, 256)
    S_lab    = SelfAttn(lab_proj)     — shape (batch, 256)
    S_vitals = SelfAttn(vitals_proj)  — shape (batch, 256)

Each head learns different aspects of the same modality:
  - Text heads might focus on symptoms, diagnoses, medications
  - Lab heads might capture metabolic vs hematologic patterns
  - Vitals heads might capture trend direction vs absolute level

NOTE: Since each modality produces a single 256-dim vector (not a sequence),
we use a "sequence of 1" approach — the vector is treated as a 1-token sequence.
This allows standard transformer self-attention to be applied consistently.
Alternatively, a simple feed-forward residual block may be used.
"""

import torch                    # Tensor operations
import torch.nn as nn           # Module base class

from configs.model_config import MODEL_CFG


class ModalitySelfAttention(nn.Module):
    """
    Multi-head self-attention block for a single modality.

    Applied to the projected feature vector (shape: batch × dim).
    The vector is unsqueezed to a sequence of length 1 for transformer compatibility.

    Architecture:
        input (batch, dim) →
        unsqueeze → (batch, 1, dim) →
        MultiHeadAttention(dim, n_heads) →
        squeeze → (batch, dim) →
        residual + LayerNorm →
        FFN(dim → ffn_dim → dim) →
        residual + LayerNorm →
        output (batch, dim)

    Parameters
    ----------
    embed_dim : int
        Input (and output) embedding dimension. Defaults to MODEL_CFG.projection_dim.
    n_heads : int
        Number of attention heads. Defaults to MODEL_CFG.self_attn_heads.
    dropout : float
        Attention dropout probability.
    ffn_dim : int
        Hidden dimension of the feed-forward sublayer.
    n_layers : int
        Number of stacked self-attention layers.
    """

    def __init__(
        self,
        embed_dim: int = MODEL_CFG.projection_dim,
        n_heads: int = MODEL_CFG.self_attn_heads,
        dropout: float = MODEL_CFG.self_attn_dropout,
        ffn_dim: int = MODEL_CFG.ffn_dim,
        n_layers: int = MODEL_CFG.self_attn_layers,
    ) -> None:
        super().__init__()
        self.embed_dim = embed_dim
        self.n_heads = n_heads
        self.n_layers = n_layers

        self.layers = nn.ModuleList([
            SelfAttentionLayer(embed_dim, n_heads, dropout, ffn_dim)
            for _ in range(n_layers)
        ])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Apply stacked self-attention to a modality embedding.

        Parameters
        ----------
        x : torch.Tensor
            Shape (batch_size, embed_dim).

        Returns
        -------
        torch.Tensor
            Shape (batch_size, embed_dim) — modality-specific refined embedding.
        """
        x = x.unsqueeze(1)       # (batch, 1, embed_dim)
        for layer in self.layers:
            x = layer(x)
        return x.squeeze(1)      # (batch, embed_dim)


class SelfAttentionLayer(nn.Module):
    """
    Single self-attention transformer layer with pre-norm architecture.

    Parameters
    ----------
    embed_dim : int
    n_heads : int
    dropout : float
    ffn_dim : int
    """

    def __init__(
        self,
        embed_dim: int,
        n_heads: int,
        dropout: float,
        ffn_dim: int,
    ) -> None:
        super().__init__()

        self.self_attn = nn.MultiheadAttention(
            embed_dim, n_heads, dropout=dropout, batch_first=True
        )
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.ffn   = nn.Sequential(
            nn.Linear(embed_dim, ffn_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ffn_dim, embed_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Parameters
        ----------
        x : torch.Tensor
            Shape (batch_size, seq_len, embed_dim).

        Returns
        -------
        torch.Tensor
            Same shape as input.
        """
        # Pre-norm self-attention sublayer
        residual = x
        x, _ = self.self_attn(self.norm1(x), self.norm1(x), self.norm1(x))
        x = x + residual
        # Pre-norm FFN sublayer
        residual = x
        x = self.ffn(self.norm2(x)) + residual
        return x


if __name__ == "__main__":
    # attn = ModalitySelfAttention()
    # x = torch.randn(4, 256)   # batch=4, dim=256
    # out = attn(x)
    # print(out.shape)           # Expected: (4, 256)
    pass
