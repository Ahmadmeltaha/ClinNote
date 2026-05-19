"""
ClinNote - Stage 2 Runner

Loads Stage 1 outputs then runs all 5 Stage 2 preprocessors in order:
  1. TextCleaner       -> clean clinical notes
  2. VitalsPreprocessor -> clean vital signs
  3. LabsPreprocessor   -> clean lab results
  4. PatientMatcher     -> match patients across all 4 sources
  5. TimeAligner        -> align events to admission time

Saves preprocessed outputs to outputs/:
  outputs/preprocessed_notes.csv
  outputs/preprocessed_vitals.csv
  outputs/preprocessed_labs.csv
  outputs/preprocessed_patients.csv

Usage:
    cd ClinNote/
    python scripts/run_stage2.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from configs.paths import PATHS, OUTPUTS_DIR

# Stage 1 loaders
from src.stage1_data_loading.patient_loader import PatientLoader
from src.stage1_data_loading.notes_loader   import NotesLoader
from src.stage1_data_loading.labs_loader    import LabsLoader
from src.stage1_data_loading.vitals_loader  import VitalsLoader

# Stage 2 preprocessors
from src.stage2_preprocessing.text_cleaner        import TextCleaner
from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
from src.stage2_preprocessing.labs_preprocessor   import LabsPreprocessor
from src.stage2_preprocessing.patient_matcher      import PatientMatcher
from src.stage2_preprocessing.time_aligner         import TimeAligner

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def _save(df, filename: str) -> Path:
    path = OUTPUTS_DIR / filename
    df.to_csv(path, index=False)
    return path


def _null_summary(df) -> str:
    nulls = df.isnull().sum().sum()
    return f"{nulls:,} total nulls"


def main() -> None:
    print("=" * 65)
    print("  ClinNote - Stage 2: Preprocessing")
    print("=" * 65)

    results = {}
    success = {}

    # ------------------------------------------------------------------ #
    # Stage 1: Load raw data                                               #
    # ------------------------------------------------------------------ #
    print("\n[Loading Stage 1 data...]")
    try:
        patients_raw = PatientLoader().load()
        notes_raw    = NotesLoader().load()
        labs_raw     = LabsLoader().load()
        vitals_raw   = VitalsLoader().load()
        print("[OK] All 4 sources loaded.")
    except Exception as exc:
        print(f"[FATAL] Stage 1 loading failed: {exc}")
        print("Stage 2 Failed")
        return

    # ------------------------------------------------------------------ #
    # Step 1: TextCleaner                                                  #
    # ------------------------------------------------------------------ #
    print("\n" + "-" * 50)
    print("Step 1 - TextCleaner")
    print("-" * 50)
    try:
        cleaner = TextCleaner()
        notes_clean = cleaner.clean_dataframe(notes_raw, text_col="text")
        path = _save(notes_clean, "preprocessed_notes.csv")
        results["notes"]  = notes_clean
        success["notes"]  = True
        print(f"  Saved -> {path}")
    except Exception as exc:
        print(f"  [ERROR] TextCleaner failed: {exc}")
        results["notes"] = notes_raw
        success["notes"] = False

    # ------------------------------------------------------------------ #
    # Step 2: VitalsPreprocessor                                           #
    # ------------------------------------------------------------------ #
    print("\n" + "-" * 50)
    print("Step 2 - VitalsPreprocessor")
    print("-" * 50)
    try:
        vpp = VitalsPreprocessor()
        vitals_clean = vpp.preprocess(vitals_raw)
        path = _save(vitals_clean, "preprocessed_vitals.csv")
        results["vitals"] = vitals_clean
        success["vitals"] = True
        print(f"  Saved -> {path}")
    except Exception as exc:
        print(f"  [ERROR] VitalsPreprocessor failed: {exc}")
        results["vitals"] = vitals_raw
        success["vitals"] = False

    # ------------------------------------------------------------------ #
    # Step 3: LabsPreprocessor                                             #
    # ------------------------------------------------------------------ #
    print("\n" + "-" * 50)
    print("Step 3 - LabsPreprocessor")
    print("-" * 50)
    try:
        lpp = LabsPreprocessor(missing_strategy="drop")
        labs_clean = lpp.preprocess(labs_raw)
        path = _save(labs_clean, "preprocessed_labs.csv")
        results["labs"] = labs_clean
        success["labs"] = True
        print(f"  Saved -> {path}")
    except Exception as exc:
        print(f"  [ERROR] LabsPreprocessor failed: {exc}")
        results["labs"] = labs_raw
        success["labs"] = False

    # ------------------------------------------------------------------ #
    # Step 4: PatientMatcher                                               #
    # ------------------------------------------------------------------ #
    print("\n" + "-" * 50)
    print("Step 4 - PatientMatcher")
    print("-" * 50)
    try:
        matcher = PatientMatcher()
        patients_matched, matched_ids = matcher.match(
            patients_df=patients_raw,
            notes_df=results.get("notes", notes_raw),
            labs_df=results.get("labs", labs_raw),
            vitals_df=results.get("vitals", vitals_raw),
        )
        path = _save(patients_matched, "preprocessed_patients.csv")
        results["patients"] = patients_matched
        success["patients"] = True
        print(f"  Saved -> {path}")
    except Exception as exc:
        print(f"  [ERROR] PatientMatcher failed: {exc}")
        results["patients"] = patients_raw
        success["patients"] = False
        matched_ids = set()

    # ------------------------------------------------------------------ #
    # Step 5: TimeAligner                                                  #
    # ------------------------------------------------------------------ #
    print("\n" + "-" * 50)
    print("Step 5 - TimeAligner (notes + labs + vitals)")
    print("-" * 50)
    try:
        aligner = TimeAligner(reference="admittime", clip_negative=True)

        # Align notes
        print("  Aligning notes...")
        notes_aligned = aligner.align(
            df=results.get("notes", notes_raw),
            patients_df=patients_raw,
            time_col="charttime",
            reference="admittime",
        )

        # Align labs
        print("  Aligning labs...")
        labs_aligned = aligner.align(
            df=results.get("labs", labs_raw),
            patients_df=patients_raw,
            time_col="charttime",
            reference="admittime",
        )

        # Align vitals
        print("  Aligning vitals...")
        vitals_aligned = aligner.align(
            df=results.get("vitals", vitals_raw),
            patients_df=patients_raw,
            time_col="charttime",
            reference="admittime",
        )

        # Overwrite outputs with time-aligned versions
        _save(notes_aligned,  "preprocessed_notes.csv")
        _save(labs_aligned,   "preprocessed_labs.csv")
        _save(vitals_aligned, "preprocessed_vitals.csv")

        results["notes"]  = notes_aligned
        results["labs"]   = labs_aligned
        results["vitals"] = vitals_aligned
        success["aligner"] = True
        print("  Time alignment complete.")
    except Exception as exc:
        print(f"  [ERROR] TimeAligner failed: {exc}")
        success["aligner"] = False

    # ------------------------------------------------------------------ #
    # Final summary table                                                   #
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 65)
    print("  Stage 2 Summary")
    print("=" * 65)
    print(f"  {'Output':<28}  {'Status':<8}  {'Shape':<18}  Nulls")
    print(f"  {'-'*28}  {'-'*8}  {'-'*18}  {'-'*15}")

    output_map = [
        ("preprocessed_notes.csv",    "notes",    success.get("notes", False)),
        ("preprocessed_vitals.csv",   "vitals",   success.get("vitals", False)),
        ("preprocessed_labs.csv",     "labs",     success.get("labs", False)),
        ("preprocessed_patients.csv", "patients", success.get("patients", False)),
    ]

    all_ok = True
    for fname, key, ok in output_map:
        df   = results.get(key)
        stat = "OK" if ok else "FAILED"
        shp  = str(df.shape) if df is not None else "N/A"
        nulls = _null_summary(df) if df is not None else "N/A"
        if not ok:
            all_ok = False
        print(f"  {fname:<28}  {stat:<8}  {shp:<18}  {nulls}")

    print()
    if all_ok:
        print("  Stage 2 Complete")
    else:
        print("  Stage 2 Failed - check errors above")
    print("=" * 65)


if __name__ == "__main__":
    main()
