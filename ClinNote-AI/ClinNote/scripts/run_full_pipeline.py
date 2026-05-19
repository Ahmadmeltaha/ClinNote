"""
Script: End-to-End ClinNote Pipeline

Runs all 6 stages in sequence. Each stage can be toggled in PIPELINE_CFG.stages.
Cached outputs from previous runs are reused automatically.

Usage:
    python scripts/run_full_pipeline.py [--debug] [--force-rerun]

Options:
    --debug        Process 500 patients for fast development testing
    --force-rerun  Ignore cached files and rerun all stages
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.logger import setup_logger
from src.utils.helpers import set_seed, timer
from configs.paths import PATHS
from configs.pipeline_config import PIPELINE_CFG
from configs.model_config import MODEL_CFG

logger = setup_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClinNote Full Pipeline")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--force-rerun", action="store_true")
    parser.add_argument("--patient_id", type=str, default=None)
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    if args.patient_id:
        from api.pipeline_runner import run_for_patient
        run_for_patient(args.patient_id)
        return

    set_seed(MODEL_CFG.random_seed)
    PATHS.ensure_output_dirs()

    logger.info("=" * 70)
    logger.info("ClinNote AI Pipeline — Full Run")
    logger.info("Debug: %s | Force rerun: %s", args.debug, args.force_rerun)
    logger.info("=" * 70)

    cfg = PIPELINE_CFG.stages

    # Stage 1 + 2: Preprocessing
    if cfg.run_stage1_loading or cfg.run_stage2_preprocessing:
        if args.force_rerun or not PATHS.cohort_file.exists():
            logger.info("--- Stage 1+2: Preprocessing ---")
            import scripts.run_stage2 as run_stage2
            run_stage2.run(args)
        else:
            logger.info("Skipping Stage 1+2 (cohort cache found).")

    # Stage 3: Feature extraction
    if cfg.run_stage3_feature_extraction:
        if args.force_rerun or not PATHS.text_features_file.exists():
            logger.info("--- Stage 3: Feature Extraction ---")
            import scripts.run_feature_extraction as run_feat
            run_feat.run(args)
        else:
            logger.info("Skipping Stage 3 (features cache found).")

    # Stage 4: Fusion training
    if cfg.run_stage4_fusion_training:
        if args.force_rerun or not PATHS.fusion_model_checkpoint.exists():
            logger.info("--- Stage 4: Fusion Training ---")
            import scripts.run_fusion_training as run_fusion
            run_fusion.run(args)
        else:
            logger.info("Skipping Stage 4 (checkpoint found).")

    # Stage 5: Evaluation
    if cfg.run_stage5_analysis:
        logger.info("--- Stage 5: Evaluation ---")
        import scripts.run_evaluation as run_eval
        eval_args = argparse.Namespace(split="test", generate_summaries=False)
        run_eval.run(eval_args)

    logger.info("=" * 70)
    logger.info("Pipeline complete.")


if __name__ == "__main__":
    run(parse_args())
