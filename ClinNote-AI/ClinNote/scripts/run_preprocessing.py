"""
Script: Run Full Preprocessing Pipeline (Stages 1–2)

Loads all raw MIMIC-IV data, builds the patient cohort, and runs all
preprocessing steps. Outputs: cohort.pkl, cleaned DataFrames cached to disk.

Usage:
    python scripts/run_preprocessing.py [--debug] [--max-patients N]

Options:
    --debug         Run on a small subset (500 patients) for fast testing
    --max-patients  Override the number of patients to process
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.logger import setup_logger
from src.utils.helpers import set_seed, timer
from configs.paths import PATHS
from configs.pipeline_config import PIPELINE_CFG

logger = setup_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClinNote Preprocessing Pipeline")
    parser.add_argument("--debug", action="store_true", help="Use debug subset (500 patients)")
    parser.add_argument("--max-patients", type=int, default=None)
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    """Run the full preprocessing pipeline."""
    set_seed(42)
    max_patients = 500 if args.debug else args.max_patients

    logger.info("=" * 60)
    logger.info("ClinNote Preprocessing Pipeline")
    logger.info("Debug mode: %s | Max patients: %s", args.debug, max_patients)
    logger.info("=" * 60)

    PATHS.ensure_output_dirs()
    PATHS.validate_raw_data()

    # Stage 1: Build cohort
    # TODO:
    #   from src.stage1_data_loading.cohort_builder import CohortBuilder
    #   with timer("Stage 1: Cohort building"):
    #       builder = CohortBuilder(max_patients=max_patients)
    #       cohort = builder.build()
    #       builder.save()
    #       logger.info("Cohort built: %d admissions", len(cohort))

    # Stage 2: Preprocessing
    # TODO:
    #   from src.stage1_data_loading import NotesLoader, LabsLoader, VitalsLoader
    #   from src.stage2_preprocessing import TextCleaner, LabsPreprocessor, VitalsPreprocessor, TimeAligner
    #
    #   with timer("Stage 2: Text cleaning"):
    #       notes = NotesLoader().load()
    #       cleaner = TextCleaner()
    #       notes = cleaner.clean_dataframe(notes)
    #
    #   with timer("Stage 2: Lab preprocessing"):
    #       labs = LabsLoader().load_labevents()
    #       labs = LabsPreprocessor().preprocess(labs)
    #
    #   with timer("Stage 2: Vitals preprocessing"):
    #       vitals = VitalsLoader().load_vitals()
    #       vitals = VitalsPreprocessor().preprocess(vitals)

    logger.info("Preprocessing pipeline complete.")
    raise NotImplementedError("run_preprocessing.py: implement the pipeline body.")


if __name__ == "__main__":
    args = parse_args()
    run(args)
