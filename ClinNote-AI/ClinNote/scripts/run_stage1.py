"""
ClinNote — Stage 1 Runner

Runs all four data loaders in order, then builds the patient cohort.
Each loader is wrapped in try/except so a failure in one does not stop the rest.

Usage:
    cd ClinNote/
    python scripts/run_stage1.py
"""

import sys
import os

# Ensure the ClinNote package root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs.paths import verify_paths, PATHS

from src.stage1_data_loading.patient_loader import PatientLoader
from src.stage1_data_loading.notes_loader   import NotesLoader
from src.stage1_data_loading.labs_loader    import LabsLoader
from src.stage1_data_loading.vitals_loader  import VitalsLoader
from src.stage1_data_loading.cohort_builder import CohortBuilder


def main() -> None:
    print("=" * 60)
    print("  ClinNote — Stage 1: Data Loading")
    print("=" * 60)

    # ------------------------------------------------------------------ #
    # Pre-flight: verify CSV files exist                                   #
    # ------------------------------------------------------------------ #
    print("\n[Pre-flight] Checking data files ...")
    verify_paths()
    PATHS.ensure_output_dirs()

    results: dict = {}   # loader_name → DataFrame or None
    success_flags: dict = {}

    # ------------------------------------------------------------------ #
    # 1. PatientLoader                                                     #
    # ------------------------------------------------------------------ #
    print("\n" + "-" * 50)
    print("Step 1 — PatientLoader")
    print("-" * 50)
    try:
        loader = PatientLoader()
        patients_df = loader.load()
        results["patients"] = patients_df
        success_flags["patients"] = True
    except Exception as exc:
        print(f"  [ERROR] PatientLoader failed: {exc}")
        results["patients"] = None
        success_flags["patients"] = False

    # ------------------------------------------------------------------ #
    # 2. NotesLoader                                                       #
    # ------------------------------------------------------------------ #
    print("\n" + "-" * 50)
    print("Step 2 — NotesLoader")
    print("-" * 50)
    try:
        loader = NotesLoader()
        notes_df = loader.load()
        results["notes"] = notes_df
        success_flags["notes"] = True
    except Exception as exc:
        print(f"  [ERROR] NotesLoader failed: {exc}")
        results["notes"] = None
        success_flags["notes"] = False

    # ------------------------------------------------------------------ #
    # 3. LabsLoader                                                        #
    # ------------------------------------------------------------------ #
    print("\n" + "-" * 50)
    print("Step 3 — LabsLoader")
    print("-" * 50)
    try:
        loader = LabsLoader()
        labs_df = loader.load()
        results["labs"] = labs_df
        success_flags["labs"] = True
    except Exception as exc:
        print(f"  [ERROR] LabsLoader failed: {exc}")
        results["labs"] = None
        success_flags["labs"] = False

    # ------------------------------------------------------------------ #
    # 4. VitalsLoader                                                      #
    # ------------------------------------------------------------------ #
    print("\n" + "-" * 50)
    print("Step 4 — VitalsLoader")
    print("-" * 50)
    try:
        loader = VitalsLoader()
        vitals_df = loader.load()
        results["vitals"] = vitals_df
        success_flags["vitals"] = True
    except Exception as exc:
        print(f"  [ERROR] VitalsLoader failed: {exc}")
        results["vitals"] = None
        success_flags["vitals"] = False

    # ------------------------------------------------------------------ #
    # 5. CohortBuilder                                                     #
    # ------------------------------------------------------------------ #
    cohort_df = None
    if all(results[k] is not None for k in ("patients", "notes", "labs", "vitals")):
        print("\n" + "-" * 50)
        print("Step 5 — CohortBuilder")
        print("-" * 50)
        try:
            builder = CohortBuilder()
            cohort_df = builder.build(
                patients_df=results["patients"],
                notes_df=results["notes"],
                labs_df=results["labs"],
                vitals_df=results["vitals"],
            )
            results["cohort"] = cohort_df
            success_flags["cohort"] = True
        except Exception as exc:
            print(f"  [ERROR] CohortBuilder failed: {exc}")
            results["cohort"] = None
            success_flags["cohort"] = False
    else:
        print("\n[WARN] Skipping CohortBuilder — one or more loaders failed.")
        success_flags["cohort"] = False

    # ------------------------------------------------------------------ #
    # Summary table                                                        #
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 60)
    print("  Stage 1 Summary")
    print("=" * 60)
    print(f"  {'Source':<12}  {'Status':<8}  {'Shape'}")
    print(f"  {'-'*12}  {'-'*8}  {'-'*20}")
    for name in ("patients", "notes", "labs", "vitals", "cohort"):
        df   = results.get(name)
        ok   = success_flags.get(name, False)
        stat = "OK" if ok else "FAILED"
        shp  = str(df.shape) if df is not None else "N/A"
        print(f"  {name:<12}  {stat:<8}  {shp}")

    print()
    all_ok = all(success_flags.get(k, False) for k in ("patients", "notes", "labs", "vitals", "cohort"))
    if all_ok:
        print("  Stage 1 Complete")
    else:
        print("  Stage 1 Failed — check errors above")
    print("=" * 60)


if __name__ == "__main__":
    main()
