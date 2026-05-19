"""
Script: Run Feature Extraction (Stage 3)

Runs all three feature extraction pipelines in sequence:
  A. NLP Pipeline     -> text_embeddings.h5     (n, 768)
  B. Lab Pipeline     -> lab_features.h5         (n, 50)
  C. Vitals Pipeline  -> vitals_features.h5      (n, 32)

Requires: cohort.pkl from run_stage1.py and preprocessed CSVs from run_stage2.py

Usage:
    python scripts/run_feature_extraction.py [--debug] [--text-only | --labs-only | --vitals-only]
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.logger import setup_logger
from src.utils.helpers import set_seed, timer
from configs.paths import PATHS

logger = setup_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClinNote Feature Extraction")
    parser.add_argument("--debug", action="store_true",
                        help="Process only first 50 admissions")
    parser.add_argument("--text-only", action="store_true")
    parser.add_argument("--labs-only", action="store_true")
    parser.add_argument("--vitals-only", action="store_true")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    set_seed(42)
    PATHS.ensure_output_dirs()

    run_all = not (args.text_only or args.labs_only or args.vitals_only)

    print("=" * 65)
    print("  ClinNote — Stage 3: Feature Extraction")
    print("=" * 65)

    # ------------------------------------------------------------------ #
    # Load cohort and preprocessed data                                    #
    # ------------------------------------------------------------------ #
    print("\n[Loading cohort and preprocessed data...]")

    from src.stage1_data_loading.cohort_builder import CohortBuilder
    cohort = CohortBuilder.load_cached()
    print(f"  Cohort: {cohort.shape}  admissions")

    notes_df = pd.read_csv(PATHS.output_root / "preprocessed_notes.csv")
    labs_df = pd.read_csv(PATHS.output_root / "preprocessed_labs.csv")
    vitals_df = pd.read_csv(PATHS.output_root / "preprocessed_vitals.csv")

    # Parse datetimes
    for col in ["charttime", "storetime"]:
        if col in notes_df.columns:
            notes_df[col] = pd.to_datetime(notes_df[col], errors="coerce")
        if col in labs_df.columns:
            labs_df[col] = pd.to_datetime(labs_df[col], errors="coerce")

    hadm_ids = cohort["hadm_id"].tolist()
    if args.debug:
        hadm_ids = hadm_ids[:50]
        print(f"  [debug] Capped to {len(hadm_ids)} admissions")

    print(f"  Processing {len(hadm_ids)} admissions")

    from src.stage3_feature_extraction.feature_store import FeatureStore
    store = FeatureStore()

    # ------------------------------------------------------------------ #
    # A. NLP Pipeline — ClinicalBERT text embeddings (n, 768)             #
    # ------------------------------------------------------------------ #
    if run_all or args.text_only:
        print("\n" + "-" * 50)
        print("Step A — NLP Pipeline (ClinicalBERT -> 768-dim)")
        print("-" * 50)
        with timer("NLP Pipeline"):
            from src.stage3_feature_extraction.nlp_pipeline import NLPPipeline
            nlp = NLPPipeline()
            nlp.load_model()

            # For each hadm_id, get the most recent cleaned note text
            texts = []
            valid_hadm_ids = []
            for hid in hadm_ids:
                note_rows = notes_df[notes_df["hadm_id"] == hid]
                if note_rows.empty:
                    text = ""
                else:
                    text_col = "text_cleaned" if "text_cleaned" in note_rows.columns \
                               else "text"
                    text = str(note_rows.sort_values("charttime")[text_col].iloc[-1])
                texts.append(text)
                valid_hadm_ids.append(hid)

            embeddings = nlp.encode(texts)
            hadm_ids_arr = np.array(valid_hadm_ids, dtype=np.int64)
            store.save_text_embeddings(embeddings, hadm_ids_arr)

        print(f"  Text embeddings shape: {embeddings.shape}")
        assert embeddings.shape == (len(valid_hadm_ids), 768), \
            f"Expected ({len(valid_hadm_ids)}, 768), got {embeddings.shape}"
        print("  [OK] Shape validated.")

    # ------------------------------------------------------------------ #
    # B. Lab Pipeline — normalized lab features (n, 50)                   #
    # ------------------------------------------------------------------ #
    if run_all or args.labs_only:
        print("\n" + "-" * 50)
        print("Step B — Lab Pipeline (normalize + anomaly -> 50-dim)")
        print("-" * 50)
        with timer("Lab Pipeline"):
            from src.stage3_feature_extraction.lab_pipeline import LabPipeline
            lab_pipe = LabPipeline()
            lab_features = lab_pipe.extract_batch(labs_df, hadm_ids)
            hadm_ids_arr = np.array(hadm_ids, dtype=np.int64)
            store.save_lab_features(lab_features, hadm_ids_arr)

        print(f"  Lab features shape: {lab_features.shape}")
        assert lab_features.shape == (len(hadm_ids), 50), \
            f"Expected ({len(hadm_ids)}, 50), got {lab_features.shape}"
        print("  [OK] Shape validated.")

    # ------------------------------------------------------------------ #
    # C. Vitals Pipeline — temporal stats (n, 32)                         #
    # ------------------------------------------------------------------ #
    if run_all or args.vitals_only:
        print("\n" + "-" * 50)
        print("Step C — Vitals Pipeline (stats + trends -> 32-dim)")
        print("-" * 50)
        with timer("Vitals Pipeline"):
            from src.stage3_feature_extraction.vitals_pipeline import VitalsPipeline

            # Get stay_ids from vitals for the cohort hadm_ids
            stay_ids = []
            for hid in hadm_ids:
                vrows = vitals_df[vitals_df["hadm_id"] == hid]
                if not vrows.empty and "stay_id" in vrows.columns:
                    sid = int(vrows["stay_id"].iloc[0])
                else:
                    sid = 0
                stay_ids.append(sid)

            vitals_pipe = VitalsPipeline(icu_hours_window=48)
            vitals_features = vitals_pipe.extract_batch(vitals_df, stay_ids)
            stay_ids_arr = np.array(stay_ids, dtype=np.int64)
            store.save_vitals_features(vitals_features, stay_ids_arr)

        print(f"  Vitals features shape: {vitals_features.shape}")
        assert vitals_features.shape == (len(hadm_ids), 32), \
            f"Expected ({len(hadm_ids)}, 32), got {vitals_features.shape}"
        print("  [OK] Shape validated.")

    # ------------------------------------------------------------------ #
    # Summary                                                              #
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 65)
    print("  Stage 3 Summary")
    print("=" * 65)
    store.print_summary()
    print()
    if store.all_features_exist():
        print("  Stage 3 Complete — all 3 feature files saved.")
    else:
        print("  Stage 3 Partial — some feature files missing (check flags).")
    print("=" * 65)


if __name__ == "__main__":
    run(parse_args())
