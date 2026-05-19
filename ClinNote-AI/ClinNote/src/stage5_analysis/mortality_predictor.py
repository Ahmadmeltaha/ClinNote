"""
Stage 5 — Analysis: In-Hospital Mortality Predictor

Wraps the trained DisentangledTransformer for inference and evaluation.
Computes AUROC, AUPRC, F1, accuracy, and balanced accuracy on the test set.

The mortality prediction head is a binary classifier trained on:
    Input : 1024-dim fused representation (h_final from FusionModel)
    Output: P(in-hospital mortality) ∈ [0, 1]
    Label : hospital_expire_flag from MIMIC-IV admissions.csv.gz

Evaluation is done on the held-out test split from PIPELINE_CFG.split.
"""

import logging
from pathlib import Path

import numpy as np              # Array ops
import torch                    # Model inference
from sklearn import metrics     # AUROC, AUPRC, F1, accuracy

from configs.paths import PATHS
from configs.pipeline_config import PIPELINE_CFG

logger = logging.getLogger(__name__)


class MortalityPredictor:
    """
    Loads a trained DisentangledTransformer and runs mortality prediction.

    Parameters
    ----------
    model_checkpoint : Path
        Path to the saved model checkpoint (.pt file).
    device : str
        "cuda" or "cpu".
    threshold : float
        Decision threshold for binary predictions. Defaults to 0.5.
    """

    def __init__(
        self,
        model_checkpoint: Path = PATHS.fusion_model_checkpoint,
        device: str | None = None,
        threshold: float = PIPELINE_CFG.evaluation.decision_threshold,
    ) -> None:
        self.model_checkpoint = Path(model_checkpoint)
        self.threshold = threshold
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """
        Load the trained DisentangledTransformer from checkpoint.

        Raises
        ------
        FileNotFoundError
            If the checkpoint does not exist.
        """
        from src.stage4_fusion.disentangled_transformer import DisentangledTransformer
        if not self.model_checkpoint.exists():
            raise FileNotFoundError(f"Checkpoint not found: {self.model_checkpoint}")
        self._model = DisentangledTransformer()
        state = torch.load(self.model_checkpoint, map_location=self.device, weights_only=False)
        self._model.load_state_dict(state["model_state_dict"])
        self._model.to(self.device)
        self._model.eval()
        logger.info("Loaded model from %s", self.model_checkpoint)

    def predict_proba(
        self,
        text_features: np.ndarray,
        lab_features: np.ndarray,
        vitals_features: np.ndarray,
    ) -> np.ndarray:
        """
        Predict mortality probabilities for a batch of patients.

        Parameters
        ----------
        text_features : np.ndarray
            Shape (n, 768).
        lab_features : np.ndarray
            Shape (n, 50).
        vitals_features : np.ndarray
            Shape (n, 32).

        Returns
        -------
        np.ndarray
            Float32 array of shape (n,) — predicted mortality probabilities.
        """
        if self._model is None:
            self.load_model()
        t = torch.tensor(text_features,   dtype=torch.float32).to(self.device)
        l = torch.tensor(lab_features,    dtype=torch.float32).to(self.device)
        v = torch.tensor(vitals_features, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            out = self._model(t, l, v)
        return out["mortality_prob"].cpu().numpy().squeeze()

    def predict(
        self,
        text_features: np.ndarray,
        lab_features: np.ndarray,
        vitals_features: np.ndarray,
    ) -> np.ndarray:
        """
        Predict binary mortality labels using self.threshold.

        Returns
        -------
        np.ndarray
            Int array of shape (n,) with values 0 or 1.
        """
        return (self.predict_proba(text_features, lab_features, vitals_features) >= self.threshold).astype(int)

    def evaluate(
        self,
        text_features: np.ndarray,
        lab_features: np.ndarray,
        vitals_features: np.ndarray,
        labels: np.ndarray,
    ) -> dict[str, float]:
        """
        Compute all evaluation metrics on a labeled dataset.

        Parameters
        ----------
        text_features : np.ndarray
            Shape (n, 768).
        lab_features : np.ndarray
            Shape (n, 50).
        vitals_features : np.ndarray
            Shape (n, 32).
        labels : np.ndarray
            Binary ground-truth labels of shape (n,).

        Returns
        -------
        dict[str, float]
            Keys: auroc, auprc, f1, accuracy, balanced_accuracy,
                  sensitivity, specificity, ppv, npv.
        """
        proba = self.predict_proba(text_features, lab_features, vitals_features)
        preds = (proba >= self.threshold).astype(int)
        result: dict[str, float] = {
            "accuracy"         : float(metrics.accuracy_score(labels, preds)),
            "balanced_accuracy": float(metrics.balanced_accuracy_score(labels, preds)),
            "f1"               : float(metrics.f1_score(labels, preds, zero_division=0)),
        }
        if len(np.unique(labels)) >= 2:
            result["auroc"] = float(metrics.roc_auc_score(labels, proba))
            result["auprc"] = float(metrics.average_precision_score(labels, proba))
            tn, fp, fn, tp = metrics.confusion_matrix(labels, preds, labels=[0,1]).ravel()
            result["sensitivity"] = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            result["specificity"] = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
            result["ppv"]         = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            result["npv"]         = float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0
        else:
            result.update({"auroc": 0.0, "auprc": 0.0, "sensitivity": 0.0,
                           "specificity": 0.0, "ppv": 0.0, "npv": 0.0})
        return result


if __name__ == "__main__":
    # predictor = MortalityPredictor()
    # predictor.load_model()
    # metrics = predictor.evaluate(text_feats, lab_feats, vitals_feats, labels)
    # print(metrics)
    pass
