"""
ClinNote — Pipeline Configuration (All Stages)

Defines runtime settings for each pipeline stage:
  - Dataset split ratios (train / val / test)
  - Chunking and I/O batch sizes for large file processing
  - Feature store formats (HDF5 vs pickle)
  - Logging verbosity
  - Which stages to run in the end-to-end script

These settings control *how* the pipeline runs, not the model architecture
(see model_config.py) or data schema (see data_config.py).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SplitConfig:
    """Train / validation / test split ratios. Must sum to 1.0."""
    train: float = 0.70
    val: float = 0.15
    test: float = 0.15
    stratify_by: str = "hospital_expire_flag"   # Column used for stratified split

    def __post_init__(self) -> None:
        total = self.train + self.val + self.test
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Split ratios must sum to 1.0, got {total}")


@dataclass(frozen=True)
class IOConfig:
    """I/O and chunking settings for reading large MIMIC-IV files."""
    # Number of rows per chunk when reading csv.gz files with pandas
    labevents_chunksize: int = 1_000_000
    chartevents_chunksize: int = 2_000_000
    discharge_chunksize: int = 50_000

    # Feature storage format: "hdf5" | "pickle"
    feature_store_format: str = "hdf5"

    # Number of workers for DataLoader (torch)
    dataloader_workers: int = 4

    # Pin memory for GPU data loading
    pin_memory: bool = True


@dataclass(frozen=True)
class StageFlags:
    """
    Boolean flags controlling which stages execute in run_full_pipeline.py.
    Set to False to skip a stage (e.g., if features are already cached).
    """
    run_stage1_loading: bool = True
    run_stage2_preprocessing: bool = True
    run_stage3_feature_extraction: bool = True
    run_stage4_fusion_training: bool = True
    run_stage5_analysis: bool = True
    run_stage6_output: bool = True

    # Sub-flags within Stage 3
    extract_text_features: bool = True
    extract_lab_features: bool = True
    extract_vitals_features: bool = True

    # Use cached features if available (skip re-extraction)
    use_cached_features: bool = True

    # Use cached cohort file (skip re-querying MIMIC tables)
    use_cached_cohort: bool = True


@dataclass(frozen=True)
class LoggingConfig:
    """Logging settings across all stages."""
    level: str = "INFO"          # "DEBUG" | "INFO" | "WARNING" | "ERROR"
    log_to_file: bool = True
    log_filename: str = "clinnote_pipeline.log"
    use_tensorboard: bool = True
    tensorboard_run_name: str = "clinnote_v1"


@dataclass(frozen=True)
class EvaluationConfig:
    """Settings for model evaluation (Stage 5)."""
    # Metrics to compute for mortality prediction
    classification_metrics: tuple[str, ...] = ("auroc", "auprc", "f1", "accuracy", "balanced_accuracy")

    # Decision threshold for binary classification
    decision_threshold: float = 0.5

    # Bootstrap resampling for confidence intervals
    bootstrap_iterations: int = 1000
    confidence_level: float = 0.95

    # Summary generation
    generate_summaries_for_split: str = "test"   # "train" | "val" | "test" | "all"


@dataclass
class PipelineConfig:
    """Master pipeline config — bundles all sub-configs."""
    split: SplitConfig = field(default_factory=SplitConfig)
    io: IOConfig = field(default_factory=IOConfig)
    stages: StageFlags = field(default_factory=StageFlags)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

    # Cohort size limits (useful during development)
    # Set to None to use all available patients
    max_patients_debug: int | None = None   # e.g. 500 for fast debugging


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------
PIPELINE_CFG = PipelineConfig()


if __name__ == "__main__":
    print("=== ClinNote Pipeline Configuration ===")
    print(f"Split         : train={PIPELINE_CFG.split.train}, val={PIPELINE_CFG.split.val}, test={PIPELINE_CFG.split.test}")
    print(f"Feature format: {PIPELINE_CFG.io.feature_store_format}")
    print(f"Log level     : {PIPELINE_CFG.logging.level}")
    print(f"Debug limit   : {PIPELINE_CFG.max_patients_debug} patients")
