"""
Shared Utilities: Evaluation Metrics

Centralizes all metric computations for model evaluation (Stage 5).
Wraps scikit-learn metrics with convenient interfaces and bootstrap CI support.
"""

import logging

import numpy as np
from sklearn import metrics as sk_metrics
from sklearn.utils import resample

logger = logging.getLogger(__name__)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, float]:
    """
    Compute standard binary classification metrics.

    Parameters
    ----------
    y_true : np.ndarray
        Binary ground-truth labels (0 or 1).
    y_prob : np.ndarray
        Predicted probabilities for class 1.
    threshold : float
        Decision threshold for binarizing predictions.

    Returns
    -------
    dict[str, float]
        Keys: auroc, auprc, f1, accuracy, balanced_accuracy,
              sensitivity (recall), specificity, ppv (precision), npv.
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    y_pred = (y_prob >= threshold).astype(int)

    tn, fp, fn, tp = sk_metrics.confusion_matrix(y_true, y_pred).ravel()

    return {
        "auroc":             sk_metrics.roc_auc_score(y_true, y_prob),
        "auprc":             sk_metrics.average_precision_score(y_true, y_prob),
        "f1":                sk_metrics.f1_score(y_true, y_pred),
        "accuracy":          sk_metrics.accuracy_score(y_true, y_pred),
        "balanced_accuracy": sk_metrics.balanced_accuracy_score(y_true, y_pred),
        "sensitivity":       tp / (tp + fn) if (tp + fn) > 0 else 0.0,
        "specificity":       tn / (tn + fp) if (tn + fp) > 0 else 0.0,
        "ppv":               tp / (tp + fp) if (tp + fp) > 0 else 0.0,
        "npv":               tn / (tn + fn) if (tn + fn) > 0 else 0.0,
    }


def bootstrap_confidence_interval(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric_fn,
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    random_state: int = 42,
) -> tuple[float, float]:
    """
    Compute bootstrap confidence interval for a metric.

    Parameters
    ----------
    y_true : np.ndarray
        Ground-truth labels.
    y_prob : np.ndarray
        Predicted probabilities.
    metric_fn : callable
        Function (y_true, y_prob) → float.
    n_iterations : int
        Number of bootstrap samples.
    confidence_level : float
        e.g., 0.95 for 95% CI.
    random_state : int
        Random seed.

    Returns
    -------
    tuple[float, float]
        (lower_bound, upper_bound) of the confidence interval.
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    rng = np.random.RandomState(random_state)
    scores = []
    n = len(y_true)

    for _ in range(n_iterations):
        idx = rng.randint(0, n, n)  # sample with replacement
        if len(np.unique(y_true[idx])) < 2:
            continue  # skip samples with only one class
        scores.append(metric_fn(y_true[idx], y_prob[idx]))

    alpha = (1 - confidence_level) / 2
    lower = float(np.percentile(scores, 100 * alpha))
    upper = float(np.percentile(scores, 100 * (1 - alpha)))
    return lower, upper


def compute_all_metrics_with_ci(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
) -> dict[str, dict]:
    """
    Compute all metrics with bootstrap 95% confidence intervals.

    Returns
    -------
    dict[str, dict]
        Each key maps to {"value": float, "ci_lower": float, "ci_upper": float}.
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    base_metrics = compute_classification_metrics(y_true, y_prob)

    from sklearn.metrics import roc_auc_score, average_precision_score
    metric_fns = {
        "auroc": roc_auc_score,
        "auprc": average_precision_score,
    }

    results = {}
    for key, value in base_metrics.items():
        entry = {"value": value, "ci_lower": None, "ci_upper": None}
        if key in metric_fns:
            lo, hi = bootstrap_confidence_interval(
                y_true, y_prob, metric_fns[key],
                n_bootstrap, confidence_level,
            )
            entry["ci_lower"] = lo
            entry["ci_upper"] = hi
        results[key] = entry

    return results


if __name__ == "__main__":
    y_true = np.array([0, 1, 0, 1, 0, 1, 1, 0, 0, 1])
    y_prob = np.array([0.1, 0.9, 0.3, 0.8, 0.2, 0.7, 0.6, 0.4, 0.1, 0.85])

    print("\n--- compute_classification_metrics ---")
    results = compute_classification_metrics(y_true, y_prob)
    for k, v in results.items():
        print(f"  {k:25s}: {v:.4f}")

    print("\n--- compute_all_metrics_with_ci (n_bootstrap=200) ---")
    full = compute_all_metrics_with_ci(y_true, y_prob, n_bootstrap=200)
    for k, d in full.items():
        ci = (f"  CI=[{d['ci_lower']:.4f}, {d['ci_upper']:.4f}]"
              if d["ci_lower"] is not None else "")
        print(f"  {k:25s}: {d['value']:.4f}{ci}")
