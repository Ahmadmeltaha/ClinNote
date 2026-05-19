"""
Stage 4 — Fusion Step 4: vCLUB Mutual Information Loss

Implements the Contrastive Log-ratio Upper Bound (CLUB) estimator for
mutual information (MI), used to disentangle modality-specific features
from shared features.

vCLUB MI Estimator (Chen et al., 2021):
    MI(X; Y) ≤ E[log q(y|x)] - E[log q(y|x')]
    where q(y|x) is a variational approximation learned by a small neural network.

In ClinNote:
    X = S_specific (any of S_text, S_lab, S_vitals — the modality-specific embedding)
    Y = S_common   (the shared embedding from cross-attention)
    Loss = vCLUB(S_specific, S_common)

By minimizing this loss, we ensure S_specific and S_common carry different
information — preventing redundant representations in the final fusion vector.

The total training loss is:
    L_total = L_task + λ * L_MI
where L_task is the mortality prediction cross-entropy, and λ = MODEL_CFG.mi_loss_weight.

Reference: CLUB: A Contrastive Log-ratio Upper Bound of Mutual Information
           Chen et al., ICML 2020. arXiv:2006.12013
"""

import torch                    # Tensor operations
import torch.nn as nn           # Neural network modules
import torch.nn.functional as F # Activation functions

from configs.model_config import MODEL_CFG


class VCLUBMILoss(nn.Module):
    """
    Variational CLUB (vCLUB) upper bound estimator for mutual information.

    Learns a conditional distribution q(y|x) via a small MLP, then computes
    the CLUB upper bound on MI(X; Y).

    Parameters
    ----------
    x_dim : int
        Dimension of the specific embedding (X). Defaults to MODEL_CFG.projection_dim.
    y_dim : int
        Dimension of the shared embedding (Y). Defaults to MODEL_CFG.projection_dim.
    hidden_dim : int
        Hidden dimension of the variational network. Defaults to MODEL_CFG.club_hidden_dim.
    """

    def __init__(
        self,
        x_dim: int = MODEL_CFG.projection_dim,
        y_dim: int = MODEL_CFG.projection_dim,
        hidden_dim: int = MODEL_CFG.club_hidden_dim,
    ) -> None:
        super().__init__()
        self.x_dim = x_dim
        self.y_dim = y_dim

        # Variational network: q(y|x) = N(mu(x), sigma^2(x))
        # Outputs mean and log-variance of the conditional distribution

        self.mu_net = nn.Sequential(
            nn.Linear(x_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, y_dim),
        )
        self.logvar_net = nn.Sequential(
            nn.Linear(x_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, y_dim),
        )

    def get_mu_logvar(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Compute the mean and log-variance of q(y|x).

        Parameters
        ----------
        x : torch.Tensor
            Specific modality embedding of shape (batch_size, x_dim).

        Returns
        -------
        tuple[torch.Tensor, torch.Tensor]
            (mu, logvar), each of shape (batch_size, y_dim).
        """
        return self.mu_net(x), self.logvar_net(x)

    def forward(
        self,
        x: torch.Tensor,
        y: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute the vCLUB upper bound: MI(X; Y) ≤ CLUB(X, Y).

        CLUB formula:
            L_CLUB = E[log q(y_i | x_i)] - E[log q(y_j | x_i)]
            where i and j are different samples in the batch.

        Parameters
        ----------
        x : torch.Tensor
            Specific modality embedding S_specific, shape (batch_size, x_dim).
        y : torch.Tensor
            Shared modality embedding S_common, shape (batch_size, y_dim).

        Returns
        -------
        torch.Tensor
            Scalar CLUB upper bound loss value.
        """
        mu, logvar = self.get_mu_logvar(x)

        # Positive: log q(y_i | x_i)
        positive = -0.5 * (logvar + (y - mu).pow(2) / logvar.exp())
        positive = positive.sum(dim=-1).mean()

        # Negative: log q(y_j | x_i) — shuffle y across batch
        y_neg    = y[torch.randperm(y.size(0), device=y.device)]
        negative = -0.5 * (logvar + (y_neg - mu).pow(2) / logvar.exp())
        negative = negative.sum(dim=-1).mean()

        return positive - negative

    def learning_loss(
        self,
        x: torch.Tensor,
        y: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute the loss used to TRAIN the variational network q(y|x).

        This is a separate NLL loss optimized by the CLUB network parameters.
        It is minimized independently to get a better MI estimator.

        Parameters
        ----------
        x : torch.Tensor
            Specific modality embedding, shape (batch_size, x_dim).
        y : torch.Tensor
            Shared modality embedding, shape (batch_size, y_dim).

        Returns
        -------
        torch.Tensor
            Scalar NLL loss for the variational network.
        """
        mu, logvar = self.get_mu_logvar(x)
        nll = 0.5 * (logvar + (y - mu).pow(2) / logvar.exp())
        return nll.sum(dim=-1).mean()


if __name__ == "__main__":
    # mi_loss_fn = VCLUBMILoss()
    # s_text   = torch.randn(4, 256)   # modality-specific
    # s_common = torch.randn(4, 256)   # shared
    # loss = mi_loss_fn(s_text, s_common)
    # print("MI Loss:", loss.item())
    pass
