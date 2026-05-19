"""
ClinNote — Path Configuration

Defines all filesystem paths used by the pipeline.
Data is pre-extracted into 4 clean CSV files under data/.
All other modules should import paths from here — never hardcode paths elsewhere.
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Root anchors
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Input data paths
# ---------------------------------------------------------------------------

DATA_DIR: Path = PROJECT_ROOT / "data"

CLINICAL_NOTES_PATH: Path = DATA_DIR / "clinical data.csv"
VITAL_SIGNS_PATH: Path    = DATA_DIR / "vital_signs.csv"
LABS_PATH: Path           = DATA_DIR / "labs_final.csv"
PATIENTS_PATH: Path       = DATA_DIR / "patients_final.csv"

# ---------------------------------------------------------------------------
# Output directories
# ---------------------------------------------------------------------------

OUTPUTS_DIR: Path   = PROJECT_ROOT / "outputs"
FEATURES_DIR: Path  = OUTPUTS_DIR / "features"
SUMMARIES_DIR: Path = OUTPUTS_DIR / "summaries"

# Specific output files
COHORT_FILE: Path          = FEATURES_DIR / "cohort.pkl"
TEXT_FEATURES_FILE: Path   = FEATURES_DIR / "text_embeddings.h5"
LAB_FEATURES_FILE: Path    = FEATURES_DIR / "lab_features.h5"
VITALS_FEATURES_FILE: Path = FEATURES_DIR / "vitals_features.h5"

FUSION_MODEL_CHECKPOINT: Path = OUTPUTS_DIR / "models" / "fusion_model_best.pt"


# ---------------------------------------------------------------------------
# Compatibility shim — PathConfig dataclass kept so existing imports don't break
# ---------------------------------------------------------------------------

class PathConfig:
    """Thin wrapper exposing paths as attributes (for legacy imports)."""

    project_root         = PROJECT_ROOT
    data_dir             = DATA_DIR
    clinical_notes       = CLINICAL_NOTES_PATH
    vital_signs          = VITAL_SIGNS_PATH
    labs                 = LABS_PATH
    patients             = PATIENTS_PATH
    output_root          = OUTPUTS_DIR
    features_dir         = FEATURES_DIR
    summaries_dir        = SUMMARIES_DIR
    cohort_file          = COHORT_FILE
    text_features_file   = TEXT_FEATURES_FILE
    lab_features_file    = LAB_FEATURES_FILE
    vitals_features_file = VITALS_FEATURES_FILE
    fusion_model_checkpoint = FUSION_MODEL_CHECKPOINT

    # Output sub-dirs
    models_dir         = OUTPUTS_DIR / "models"
    logs_dir           = OUTPUTS_DIR / "logs"
    visualizations_dir = OUTPUTS_DIR / "visualizations"

    def ensure_output_dirs(self) -> None:
        """Create all output directories if they do not already exist."""
        for d in (
            self.output_root, self.features_dir, self.models_dir,
            self.summaries_dir, self.logs_dir, self.visualizations_dir,
            self.output_root / "patient_data",
        ):
            d.mkdir(parents=True, exist_ok=True)

    def patient_summary_path(self, subject_id: int,
                             hadm_id: int) -> Path:
        return self.summaries_dir / f"patient_{subject_id}_{hadm_id}.json"

    def patient_data_dir(self, subject_id: int) -> Path:
        return self.output_root / "patient_data" / str(subject_id)


PATHS = PathConfig()


# ---------------------------------------------------------------------------
# verify_paths — checks all 4 CSV inputs exist
# ---------------------------------------------------------------------------

def verify_paths() -> None:
    """Check that all 4 pre-extracted CSV files exist and print OK/MISSING."""
    files = {
        "clinical data.csv":  CLINICAL_NOTES_PATH,
        "vital_signs.csv":    VITAL_SIGNS_PATH,
        "labs_final.csv":     LABS_PATH,
        "patients_final.csv": PATIENTS_PATH,
    }
    all_ok = True
    for name, path in files.items():
        status = "OK     " if path.exists() else "MISSING"
        if not path.exists():
            all_ok = False
        print(f"  [{status}] {name}  ->  {path}")
    if all_ok:
        print("  All data files found.")
    else:
        print("  WARNING: Some data files are missing!")


if __name__ == "__main__":
    print("=== ClinNote Path Configuration ===")
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Data dir     : {DATA_DIR}")
    print()
    print("Checking data files:")
    verify_paths()
    PATHS.ensure_output_dirs()
    print("Output directories ready.")
