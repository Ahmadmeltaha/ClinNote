"""
Shared Utilities: Visualization

Plotting utilities for exploring data and presenting results.
Uses matplotlib and seaborn. All plots are saved to outputs/visualizations/.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt  # Core plotting
import seaborn as sns            # Statistical visualization
import numpy as np

from configs.paths import PATHS

logger = logging.getLogger(__name__)

# Global style
sns.set_theme(style="whitegrid", palette="muted")


def plot_vital_timeseries(
    times: np.ndarray,
    values: np.ndarray,
    vital_name: str,
    normal_range: tuple[float, float] | None = None,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot a vital sign time series with shaded normal range.

    Parameters
    ----------
    times : np.ndarray
        Time points (hours from ICU admission).
    values : np.ndarray
        Vital sign measurements.
    vital_name : str
        Human-readable vital sign name.
    normal_range : tuple[float, float] | None
        (lower, upper) bounds for shading the normal zone.
    save_path : Path | None
        If provided, save the figure here. Otherwise display.

    Returns
    -------
    plt.Figure
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, values, marker="o", linewidth=1.5, markersize=3, label=vital_name)
    if normal_range:
        ax.axhspan(normal_range[0], normal_range[1], alpha=0.15,
                   color="green", label="Normal range")
    ax.set_xlabel("Hours from ICU Admission")
    ax.set_ylabel(vital_name)
    ax.set_title(f"{vital_name} Time Series")
    ax.legend()
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info("Saved vital timeseries plot: %s", save_path)
    return fig


def plot_roc_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    auroc: float,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot ROC curve for mortality prediction.

    Parameters
    ----------
    y_true : np.ndarray
        Binary ground-truth labels.
    y_prob : np.ndarray
        Predicted mortality probabilities.
    auroc : float
        Pre-computed AUROC score (displayed in legend).
    save_path : Path | None

    Returns
    -------
    plt.Figure
    """
    from sklearn.metrics import roc_curve
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(fpr, tpr, linewidth=2, label=f"AUROC = {auroc:.4f}")
    ax.plot([0, 1], [0, 1], "--", color="gray", label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve — In-Hospital Mortality")
    ax.legend()
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info("Saved ROC curve: %s", save_path)
    return fig


def plot_lab_distribution(
    values: np.ndarray,
    lab_name: str,
    ref_range: tuple[float, float] | None = None,
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot the distribution of a lab test value across the cohort.

    Parameters
    ----------
    values : np.ndarray
        Lab values across all admissions in the cohort.
    lab_name : str
    ref_range : tuple[float, float] | None
    save_path : Path | None

    Returns
    -------
    plt.Figure
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(values, kde=True, ax=ax, color="steelblue", stat="density")
    if ref_range:
        ax.axvline(ref_range[0], color="red", linestyle="--", linewidth=1.5,
                   label=f"Ref low ({ref_range[0]})")
        ax.axvline(ref_range[1], color="red", linestyle="--", linewidth=1.5,
                   label=f"Ref high ({ref_range[1]})")
        ax.axvspan(ref_range[0], ref_range[1], alpha=0.10, color="green",
                   label="Reference range")
    ax.set_xlabel(lab_name)
    ax.set_ylabel("Density")
    ax.set_title(f"Distribution of {lab_name}")
    ax.legend()
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info("Saved lab distribution plot: %s", save_path)
    return fig


def plot_attention_heatmap(
    attention_weights: np.ndarray,
    modality_labels: list[str],
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Plot cross-modal attention weights as a heatmap.

    Parameters
    ----------
    attention_weights : np.ndarray
        Shape (n_heads, n_modalities, n_modalities).
    modality_labels : list[str]
        e.g., ["Text", "Labs", "Vitals"].
    save_path : Path | None

    Returns
    -------
    plt.Figure
    """
    # Average attention weights over heads -> (n_modalities, n_modalities)
    avg_weights = attention_weights.mean(axis=0)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        avg_weights,
        annot=True,
        fmt=".2f",
        xticklabels=modality_labels,
        yticklabels=modality_labels,
        cmap="Blues",
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("Cross-Modal Attention Weights (avg over heads)")
    ax.set_xlabel("Key Modality")
    ax.set_ylabel("Query Modality")
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info("Saved attention heatmap: %s", save_path)
    return fig
