"""
Script: Evaluate the Full Pipeline (Stage 5)

Loads the trained model and test-set features, computes all metrics,
and generates clinical summaries for the test cohort.

Usage:
    python scripts/run_evaluation.py [--split test|val|all] [--generate-summaries]
"""

import argparse
import json
import logging
import pickle
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.logger import setup_logger
from src.stage3_feature_extraction.feature_store import FeatureStore
from src.stage5_analysis.mortality_predictor import MortalityPredictor
from configs.paths import PATHS
from configs.model_config import MODEL_CFG

logger = setup_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClinNote Pipeline Evaluation")
    parser.add_argument("--split", choices=["test", "val", "all"], default="test")
    parser.add_argument("--generate-summaries", action="store_true")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    # ------------------------------------------------------------------
    # 1. Load features + labels
    # ------------------------------------------------------------------
    store = FeatureStore()
    if not store.all_features_exist():
        logger.error("Feature files missing — run scripts/run_feature_extraction.py first.")
        sys.exit(1)

    text_feats,   hadm_ids = store.load_text_embeddings()
    lab_feats,    _        = store.load_lab_features()
    vitals_feats, _        = store.load_vitals_features()

    with open(PATHS.cohort_file, "rb") as f:
        cohort = pickle.load(f)

    label_map = dict(zip(cohort["hadm_id"].values, cohort["hospital_expire_flag"].values))
    labels = np.array([label_map.get(int(h), 0) for h in hadm_ids], dtype=np.float32)

    logger.info("Loaded %d patients — positives: %d (%.1f%%)",
                len(labels), int(labels.sum()), 100 * labels.mean())

    # ------------------------------------------------------------------
    # 2. Recreate same train/val/test split as training
    # ------------------------------------------------------------------
    n = len(labels)
    idx = np.arange(n)
    strat = labels if labels.sum() >= 2 and (labels == 0).sum() >= 2 else None
    idx_train, idx_tmp = train_test_split(idx, test_size=0.30,
                                          random_state=MODEL_CFG.random_seed, stratify=strat)
    strat_tmp = labels[idx_tmp] if strat is not None else None
    idx_val, idx_test = train_test_split(idx_tmp, test_size=0.50,
                                          random_state=MODEL_CFG.random_seed, stratify=strat_tmp)

    split_map = {"train": idx_train, "val": idx_val, "test": idx_test,
                 "all": idx}
    eval_idx = split_map[args.split]
    logger.info("Evaluating on split='%s'  (%d patients)", args.split, len(eval_idx))

    # ------------------------------------------------------------------
    # 3. Load model + evaluate
    # ------------------------------------------------------------------
    predictor = MortalityPredictor()
    predictor.load_model()

    eval_metrics = predictor.evaluate(
        text_feats[eval_idx],
        lab_feats[eval_idx],
        vitals_feats[eval_idx],
        labels[eval_idx],
    )

    print("\n=== Evaluation Results ===")
    print(f"  Split    : {args.split}  ({len(eval_idx)} patients)")
    print(f"  Positives: {int(labels[eval_idx].sum())}  "
          f"({100*labels[eval_idx].mean():.1f}%)")
    print()
    for k, v in eval_metrics.items():
        logger.info("  %-25s: %.4f", k, v)
        print(f"  {k:<25} {v:.4f}")

    # ------------------------------------------------------------------
    # 4. Save metrics JSON
    # ------------------------------------------------------------------
    PATHS.ensure_output_dirs()
    out_path = PATHS.output_root / "evaluation_metrics.json"
    eval_metrics["split"]    = args.split
    eval_metrics["n_patients"] = int(len(eval_idx))
    eval_metrics["n_positive"] = int(labels[eval_idx].sum())
    with open(out_path, "w") as f:
        json.dump(eval_metrics, f, indent=2)
    logger.info("Metrics saved to %s", out_path)
    print(f"\n  Saved to: {out_path}")


if __name__ == "__main__":
    run(parse_args())
