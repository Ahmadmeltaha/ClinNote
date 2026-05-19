"""
ClinNote — Model Configuration (Stage 4: Multimodal Data Fusion)

Defines all hyperparameters for the MEDFuse-Inspired Disentangled Transformer:
  - Input feature dimensions from each modality
  - Projection and fusion dimensions
  - Attention head counts and transformer layer depths
  - Training hyperparameters (lr, batch size, epochs)
  - Mortality prediction head settings

Import MODEL_CFG everywhere model architecture or training is configured.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    """
    Complete hyperparameter specification for the ClinNote fusion model.

    Architecture overview:
        text (768) ──┐
        labs  (50) ──┼──[Projection → 256]──[Self-Attn]──[Cross-Attn + MI Loss]──[1024-dim]
        vitals (32)──┘
    """

    # ------------------------------------------------------------------
    # Input feature dimensions (from Stage 3 feature extraction)
    # ------------------------------------------------------------------
    text_dim: int = 768        # ClinicalBERT [CLS] embedding dimension
    lab_dim: int = 50          # Lab feature vector dimension (values + flags + severity)
    vitals_dim: int = 32       # Vitals feature vector dimension (stats × 7 vital signs)

    # ------------------------------------------------------------------
    # Projection layer (Step 1: Feature Projection)
    # All modalities projected to a common dimension before attention
    # ------------------------------------------------------------------
    projection_dim: int = 256  # Target dimension after linear projection

    # ------------------------------------------------------------------
    # Self-attention (Step 2: Modality-Specific Features)
    # Applied independently to each projected modality
    # ------------------------------------------------------------------
    self_attn_heads: int = 4           # Number of attention heads
    self_attn_dropout: float = 0.1     # Dropout within self-attention
    self_attn_layers: int = 2          # Number of stacked self-attention layers

    # ------------------------------------------------------------------
    # Cross-attention (Step 3: Modality-Shared Features)
    # Attends across all three modalities to capture shared information
    # ------------------------------------------------------------------
    cross_attn_heads: int = 4          # Number of cross-attention heads
    cross_attn_dropout: float = 0.1
    cross_attn_layers: int = 2

    # ------------------------------------------------------------------
    # Disentangled transformer (full architecture)
    # ------------------------------------------------------------------
    transformer_layers: int = 6        # Total depth of the disentangled transformer
    ffn_dim: int = 512                 # Feed-forward network hidden dimension (within transformer)
    transformer_dropout: float = 0.1

    # ------------------------------------------------------------------
    # Fusion output (Step 4: Final concatenated representation)
    # h_final = [S_text | S_lab | S_vitals | S_common]
    # = 4 × projection_dim = 4 × 256 = 1024
    # ------------------------------------------------------------------
    fusion_output_dim: int = 1024      # Must equal 4 * projection_dim

    # ------------------------------------------------------------------
    # vCLUB Mutual Information Loss (Step 4: Disentanglement)
    # ------------------------------------------------------------------
    mi_loss_weight: float = 0.1        # Coefficient λ for MI loss in total loss
    club_hidden_dim: int = 128         # Hidden dim of the CLUB MI estimator network

    # ------------------------------------------------------------------
    # Mortality prediction head (Stage 5: Analysis)
    # Binary classification on top of the 1024-dim fused representation
    # ------------------------------------------------------------------
    mortality_hidden_dim: int = 256    # Hidden layer size in classification head
    mortality_dropout: float = 0.3
    mortality_output_dim: int = 1      # Binary: in-hospital mortality (sigmoid)

    # ------------------------------------------------------------------
    # ClinicalBERT (Stage 3: NLP Pipeline)
    # ------------------------------------------------------------------
    clinicalbert_model_name: str = "emilyalsentzer/Bio_ClinicalBERT"
    clinicalbert_max_length: int = 512     # Max token length (BERT hard limit)
    clinicalbert_batch_size: int = 16      # Batch size for encoding
    freeze_bert: bool = True               # Freeze BERT weights during fusion training

    # ------------------------------------------------------------------
    # Training hyperparameters
    # ------------------------------------------------------------------
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    batch_size: int = 32
    num_epochs: int = 50
    warmup_steps: int = 500
    gradient_clip_norm: float = 1.0
    early_stopping_patience: int = 10      # Stop if val loss doesn't improve for N epochs
    scheduler: str = "cosine"             # LR scheduler: "cosine" | "step" | "plateau"

    # ------------------------------------------------------------------
    # Reproducibility
    # ------------------------------------------------------------------
    random_seed: int = 42

    def __post_init__(self) -> None:
        """Validate that derived dimensions are consistent."""
        expected_fusion = 4 * self.projection_dim
        if self.fusion_output_dim != expected_fusion:
            raise ValueError(
                f"fusion_output_dim ({self.fusion_output_dim}) must equal "
                f"4 * projection_dim ({expected_fusion})"
            )


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------
MODEL_CFG = ModelConfig()


if __name__ == "__main__":
    print("=== ClinNote Model Configuration ===")
    print(f"Input dims    : text={MODEL_CFG.text_dim}, labs={MODEL_CFG.lab_dim}, vitals={MODEL_CFG.vitals_dim}")
    print(f"Projection dim: {MODEL_CFG.projection_dim}")
    print(f"Fusion output : {MODEL_CFG.fusion_output_dim}")
    print(f"ClinicalBERT  : {MODEL_CFG.clinicalbert_model_name}")
    print(f"Training      : lr={MODEL_CFG.learning_rate}, bs={MODEL_CFG.batch_size}, epochs={MODEL_CFG.num_epochs}")
