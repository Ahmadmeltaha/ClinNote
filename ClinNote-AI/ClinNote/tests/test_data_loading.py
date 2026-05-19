"""
Tests: Stage 1 - Data Loading

Verifies PatientLoader, NotesLoader, LabsLoader, VitalsLoader, CohortBuilder
using synthetic mock DataFrames. Does NOT require actual MIMIC data.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os


# ===========================================================================
# Shared fixtures
# ===========================================================================

@pytest.fixture
def sample_patients_df() -> pd.DataFrame:
    return pd.DataFrame({
        "subject_id"          : [101, 102, 103, 104],
        "hadm_id"             : [1001, 1002, 1003, 1004],
        "admittime"           : pd.to_datetime(["2020-01-08", "2020-02-14", "2020-03-01", "2020-04-01"]),
        "dischtime"           : pd.to_datetime(["2020-01-15", "2020-02-20", "2020-03-10", "2020-04-08"]),
        "deathtime"           : [None, None, None, None],
        "hospital_expire_flag": [0, 1, 0, 0],
        "gender"              : ["M", "F", "M", "F"],
        "anchor_age"          : [65, 72, 55, 80],
        "anchor_year"         : [2020, 2020, 2020, 2020],
        "anchor_year_group"   : ["2017-2019"] * 4,
        "dod"                 : [None, "2020-02-20", None, None],
        "admission_type"      : ["EMERGENCY"] * 4,
        "admission_location"  : ["ED"] * 4,
        "discharge_location"  : ["HOME", "DIED", "HOME", "HOME"],
        "insurance"           : ["Medicare"] * 4,
        "language"            : ["ENGLISH"] * 4,
        "marital_status"      : ["MARRIED", None, "SINGLE", "MARRIED"],
        "race"                : ["WHITE", "BLACK/AFRICAN AMERICAN", "WHITE", "ASIAN"],
        "edregtime"           : [None] * 4,
        "edouttime"           : [None] * 4,
    })


@pytest.fixture
def sample_notes_df() -> pd.DataFrame:
    return pd.DataFrame({
        "note_id"    : ["n1", "n2", "n3"],
        "subject_id" : [101, 102, 103],
        "hadm_id"    : [1001, 1002, 1003],
        "note_type"  : ["DS", "DS", "Radiology"],
        "note_source": ["discharge", "discharge", "radiology"],
        "charttime"  : pd.to_datetime(["2020-01-14", "2020-02-19", "2020-03-09"]),
        "storetime"  : pd.to_datetime(["2020-01-14", "2020-02-19", "2020-03-09"]),
        "text"       : [
            "Patient ___ admitted with chest pain.",
            "Patient ___ with pneumonia. SpO2 low.",
            "Patient ___ with altered mental status.",
        ],
    })


@pytest.fixture
def sample_labs_df() -> pd.DataFrame:
    return pd.DataFrame({
        "subject_id"      : [101, 101, 102, 102],
        "hadm_id"         : [1001, 1001, 1002, 1002],
        "itemid"          : [50912, 51222, 50912, 51301],
        "label"           : ["Creatinine", "Hemoglobin", "Creatinine", "WBC"],
        "charttime"       : pd.to_datetime(["2020-01-09", "2020-01-10", "2020-02-15", "2020-02-15"]),
        "storetime"       : pd.to_datetime(["2020-01-09", "2020-01-10", "2020-02-15", "2020-02-15"]),
        "value"           : ["3.2", "8.5", "1.0", "12.5"],
        "valuenum"        : [3.2, 8.5, 1.0, 12.5],
        "valueuom"        : ["mg/dL", "g/dL", "mg/dL", "K/uL"],
        "ref_range_lower" : [0.6, 12.0, 0.6, 4.5],
        "ref_range_upper" : [1.2, 17.5, 1.2, 11.0],
        "flag"            : ["abnormal", None, None, None],
        "fluid"           : ["Blood"] * 4,
        "category"        : ["Chemistry", "Hematology", "Chemistry", "Hematology"],
    })


@pytest.fixture
def sample_vitals_df() -> pd.DataFrame:
    return pd.DataFrame({
        "subject_id"  : [101, 101, 102, 102],
        "hadm_id"     : [1001, 1001, 1002, 1002],
        "stay_id"     : [301, 301, 302, 302],
        "itemid"      : [220045, 220277, 220045, 220210],
        "label"       : ["Heart Rate", "O2 Saturation", "Heart Rate", "Respiratory Rate"],
        "category"    : ["Vital Signs"] * 4,
        "vital_source": ["chartevents"] * 4,
        "charttime"   : pd.to_datetime(["2020-01-08 06:00", "2020-01-08 08:00",
                                         "2020-02-14 10:00", "2020-02-14 12:00"]),
        "storetime"   : pd.to_datetime(["2020-01-08 06:00", "2020-01-08 08:00",
                                         "2020-02-14 10:00", "2020-02-14 12:00"]),
        "value"       : ["88", "94", "75", "22"],
        "valuenum"    : [88.0, 94.0, 75.0, 22.0],
        "valueuom"    : ["bpm", "%", "bpm", "insp/min"],
        "warning"     : [0, 0, 0, 0],
    })


# ===========================================================================
# Helper: write fixture to temp CSV
# ===========================================================================

def write_csv(df: pd.DataFrame, directory: Path, name: str) -> Path:
    path = directory / name
    df.to_csv(path, index=False)
    return path


# ===========================================================================
# Tests: configs/paths.py
# ===========================================================================

class TestPathsConfig:
    def test_csv_paths_defined(self):
        """All 4 CSV paths should be defined and point to data/ folder."""
        from configs.paths import CLINICAL_NOTES_PATH, VITAL_SIGNS_PATH, LABS_PATH, PATIENTS_PATH
        assert "data" in str(CLINICAL_NOTES_PATH)
        assert str(VITAL_SIGNS_PATH).endswith("vital_signs.csv")
        assert str(LABS_PATH).endswith("labs_final.csv")
        assert str(PATIENTS_PATH).endswith("patients_final.csv")

    def test_output_dirs_defined(self):
        from configs.paths import OUTPUTS_DIR, FEATURES_DIR, SUMMARIES_DIR
        assert "outputs" in str(OUTPUTS_DIR)
        assert "features" in str(FEATURES_DIR)

    def test_verify_paths_runs(self):
        """verify_paths() should not raise — it just prints OK/MISSING."""
        from configs.paths import verify_paths
        verify_paths()   # must not raise

    def test_paths_singleton_exists(self):
        from configs.paths import PATHS
        assert hasattr(PATHS, "patients")
        assert hasattr(PATHS, "features_dir")
        assert hasattr(PATHS, "cohort_file")


# ===========================================================================
# Tests: configs/data_config.py
# ===========================================================================

class TestDataConfig:
    def test_vital_itemids_count(self):
        from configs.data_config import VITAL_ITEMIDS
        assert len(VITAL_ITEMIDS.as_list()) == 8

    def test_vital_itemids_includes_hr_and_spo2(self):
        from configs.data_config import VITAL_ITEMIDS
        assert 220045 in VITAL_ITEMIDS.as_list()  # Heart Rate
        assert 220277 in VITAL_ITEMIDS.as_list()  # SpO2

    def test_labs_column_mappings(self):
        from configs.data_config import LABS_CHARTTIME_COL, LABS_STORETIME_COL
        assert LABS_CHARTTIME_COL == "charttime_x"
        assert LABS_STORETIME_COL == "storetime_x"

    def test_data_cfg_fields(self):
        from configs.data_config import DATA_CFG
        assert DATA_CFG.min_lab_events_per_admission >= 1
        assert DATA_CFG.max_note_length_chars == 10_000


# ===========================================================================
# Tests: PatientLoader
# ===========================================================================

class TestPatientLoader:
    def test_load_returns_dataframe(self, sample_patients_df, tmp_path):
        path = write_csv(sample_patients_df, tmp_path, "patients_final.csv")
        from src.stage1_data_loading.patient_loader import PatientLoader
        loader = PatientLoader(patients_path=path)
        df = loader.load()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4

    def test_los_days_computed(self, sample_patients_df, tmp_path):
        path = write_csv(sample_patients_df, tmp_path, "patients_final.csv")
        from src.stage1_data_loading.patient_loader import PatientLoader
        df = PatientLoader(patients_path=path).load()
        assert "los_days" in df.columns
        assert (df["los_days"] > 0).all()

    def test_hospital_expire_flag_is_int(self, sample_patients_df, tmp_path):
        path = write_csv(sample_patients_df, tmp_path, "patients_final.csv")
        from src.stage1_data_loading.patient_loader import PatientLoader
        df = PatientLoader(patients_path=path).load()
        assert df["hospital_expire_flag"].dtype in [np.int32, np.int64, int]

    def test_drops_null_subject_id(self, sample_patients_df, tmp_path):
        df_with_null = sample_patients_df.copy()
        df_with_null.loc[0, "subject_id"] = None
        path = write_csv(df_with_null, tmp_path, "patients_final.csv")
        from src.stage1_data_loading.patient_loader import PatientLoader
        result = PatientLoader(patients_path=path).load()
        assert result["subject_id"].isna().sum() == 0
        assert len(result) == 3  # one row dropped

    def test_get_cohort_ids_returns_set_of_tuples(self, sample_patients_df, tmp_path):
        path = write_csv(sample_patients_df, tmp_path, "patients_final.csv")
        from src.stage1_data_loading.patient_loader import PatientLoader
        loader = PatientLoader(patients_path=path)
        ids = loader.get_cohort_ids()
        assert isinstance(ids, set)
        assert all(isinstance(t, tuple) and len(t) == 2 for t in ids)

    def test_caching(self, sample_patients_df, tmp_path):
        path = write_csv(sample_patients_df, tmp_path, "patients_final.csv")
        from src.stage1_data_loading.patient_loader import PatientLoader
        loader = PatientLoader(patients_path=path)
        df1 = loader.load()
        df2 = loader.load()
        assert df1 is df2   # same object returned from cache


# ===========================================================================
# Tests: NotesLoader
# ===========================================================================

class TestNotesLoader:
    def test_load_returns_dataframe(self, sample_notes_df, tmp_path):
        path = write_csv(sample_notes_df, tmp_path, "clinical_notes.csv")
        from src.stage1_data_loading.notes_loader import NotesLoader
        df = NotesLoader(discharge_path=path).load()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_required_columns_present(self, sample_notes_df, tmp_path):
        path = write_csv(sample_notes_df, tmp_path, "clinical_notes.csv")
        from src.stage1_data_loading.notes_loader import NotesLoader
        df = NotesLoader(discharge_path=path).load()
        for col in ["subject_id", "hadm_id", "text", "charttime"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_drops_empty_text(self, sample_notes_df, tmp_path):
        df_with_empty = sample_notes_df.copy()
        df_with_empty.loc[0, "text"] = ""
        df_with_empty.loc[1, "text"] = None
        path = write_csv(df_with_empty, tmp_path, "clinical_notes.csv")
        from src.stage1_data_loading.notes_loader import NotesLoader
        result = NotesLoader(discharge_path=path).load()
        assert len(result) == 1  # 2 rows dropped

    def test_charttime_is_datetime(self, sample_notes_df, tmp_path):
        path = write_csv(sample_notes_df, tmp_path, "clinical_notes.csv")
        from src.stage1_data_loading.notes_loader import NotesLoader
        df = NotesLoader(discharge_path=path).load()
        assert pd.api.types.is_datetime64_any_dtype(df["charttime"])

    def test_n_notes_property(self, sample_notes_df, tmp_path):
        path = write_csv(sample_notes_df, tmp_path, "clinical_notes.csv")
        from src.stage1_data_loading.notes_loader import NotesLoader
        loader = NotesLoader(discharge_path=path)
        loader.load()
        assert loader.n_notes == 3

    def test_unique_patients_property(self, sample_notes_df, tmp_path):
        path = write_csv(sample_notes_df, tmp_path, "clinical_notes.csv")
        from src.stage1_data_loading.notes_loader import NotesLoader
        loader = NotesLoader(discharge_path=path)
        loader.load()
        assert loader.unique_patients == 3


# ===========================================================================
# Tests: LabsLoader
# ===========================================================================

class TestLabsLoader:
    def _make_labs_csv(self, df: pd.DataFrame, tmp_path: Path) -> Path:
        """Simulate labs_final.csv with charttime_x/storetime_x column names."""
        df = df.rename(columns={"charttime": "charttime_x", "storetime": "storetime_x"})
        path = tmp_path / "labs_final.csv"
        df.to_csv(path, index=False)
        return path

    def test_load_returns_dataframe(self, sample_labs_df, tmp_path):
        path = self._make_labs_csv(sample_labs_df, tmp_path)
        from src.stage1_data_loading.labs_loader import LabsLoader
        df = LabsLoader(labevents_path=path).load()
        assert isinstance(df, pd.DataFrame)

    def test_charttime_renamed_from_x(self, sample_labs_df, tmp_path):
        path = self._make_labs_csv(sample_labs_df, tmp_path)
        from src.stage1_data_loading.labs_loader import LabsLoader
        df = LabsLoader(labevents_path=path).load()
        assert "charttime" in df.columns
        assert "charttime_x" not in df.columns

    def test_drops_null_valuenum(self, sample_labs_df, tmp_path):
        df_with_null = sample_labs_df.copy()
        df_with_null.loc[0, "valuenum"] = None
        path = self._make_labs_csv(df_with_null, tmp_path)
        from src.stage1_data_loading.labs_loader import LabsLoader
        result = LabsLoader(labevents_path=path).load()
        assert result["valuenum"].isna().sum() == 0

    def test_drops_null_subject_id(self, sample_labs_df, tmp_path):
        df_with_null = sample_labs_df.copy()
        df_with_null.loc[0, "subject_id"] = None
        path = self._make_labs_csv(df_with_null, tmp_path)
        from src.stage1_data_loading.labs_loader import LabsLoader
        result = LabsLoader(labevents_path=path).load()
        assert result["subject_id"].isna().sum() == 0

    def test_charttime_is_datetime(self, sample_labs_df, tmp_path):
        path = self._make_labs_csv(sample_labs_df, tmp_path)
        from src.stage1_data_loading.labs_loader import LabsLoader
        df = LabsLoader(labevents_path=path).load()
        assert pd.api.types.is_datetime64_any_dtype(df["charttime"])

    def test_default_itemids_match_config(self):
        from src.stage1_data_loading.labs_loader import LabsLoader
        from configs.data_config import LAB_ITEMIDS
        loader = LabsLoader()
        assert set(loader.itemids) == set(LAB_ITEMIDS.as_list())


# ===========================================================================
# Tests: VitalsLoader
# ===========================================================================

class TestVitalsLoader:
    def test_load_returns_dataframe(self, sample_vitals_df, tmp_path):
        path = write_csv(sample_vitals_df, tmp_path, "vital_signs.csv")
        from src.stage1_data_loading.vitals_loader import VitalsLoader
        df = VitalsLoader(chartevents_path=path).load()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4

    def test_drops_null_subject_id(self, sample_vitals_df, tmp_path):
        df_with_null = sample_vitals_df.copy()
        df_with_null.loc[0, "subject_id"] = None
        path = write_csv(df_with_null, tmp_path, "vital_signs.csv")
        from src.stage1_data_loading.vitals_loader import VitalsLoader
        result = VitalsLoader(chartevents_path=path).load()
        assert result["subject_id"].isna().sum() == 0

    def test_drops_rows_where_both_value_and_valuenum_null(self, sample_vitals_df, tmp_path):
        df_with_null = sample_vitals_df.copy()
        df_with_null.loc[0, "value"] = None
        df_with_null.loc[0, "valuenum"] = None
        path = write_csv(df_with_null, tmp_path, "vital_signs.csv")
        from src.stage1_data_loading.vitals_loader import VitalsLoader
        result = VitalsLoader(chartevents_path=path).load()
        assert len(result) == 3

    def test_charttime_is_datetime(self, sample_vitals_df, tmp_path):
        path = write_csv(sample_vitals_df, tmp_path, "vital_signs.csv")
        from src.stage1_data_loading.vitals_loader import VitalsLoader
        df = VitalsLoader(chartevents_path=path).load()
        assert pd.api.types.is_datetime64_any_dtype(df["charttime"])

    def test_default_itemids_include_hr_spo2(self):
        from src.stage1_data_loading.vitals_loader import VitalsLoader
        loader = VitalsLoader()
        assert 220045 in loader.itemids   # Heart Rate
        assert 220277 in loader.itemids   # SpO2

    def test_keeps_value_column_when_valuenum_null(self, sample_vitals_df, tmp_path):
        """A row with value but no valuenum should NOT be dropped."""
        df = sample_vitals_df.copy()
        df.loc[0, "valuenum"] = None  # value still present
        path = write_csv(df, tmp_path, "vital_signs.csv")
        from src.stage1_data_loading.vitals_loader import VitalsLoader
        result = VitalsLoader(chartevents_path=path).load()
        # Row should be kept since value is not null
        assert len(result) == 4


# ===========================================================================
# Tests: CohortBuilder
# ===========================================================================

class TestCohortBuilder:

    def _build(self, patients_df, notes_df, labs_df, vitals_df, tmp_path):
        """Build cohort saving to tmp_path to avoid overwriting real cohort.pkl."""
        import src.stage1_data_loading.cohort_builder as cb_mod
        from src.stage1_data_loading.cohort_builder import CohortBuilder
        orig = cb_mod.COHORT_FILE
        cb_mod.COHORT_FILE = tmp_path / "cohort_test.pkl"
        try:
            builder = CohortBuilder()
            cohort = builder.build(
                patients_df=patients_df,
                notes_df=notes_df,
                labs_df=labs_df,
                vitals_df=vitals_df,
            )
        finally:
            cb_mod.COHORT_FILE = orig
        return builder, cohort

    def test_build_returns_dataframe(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df, tmp_path
    ):
        _, cohort = self._build(sample_patients_df, sample_notes_df,
                                sample_labs_df, sample_vitals_df, tmp_path)
        assert isinstance(cohort, pd.DataFrame)

    def test_cohort_contains_required_columns(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df, tmp_path
    ):
        _, cohort = self._build(sample_patients_df, sample_notes_df,
                                sample_labs_df, sample_vitals_df, tmp_path)
        for col in ["subject_id", "hadm_id", "hospital_expire_flag"]:
            assert col in cohort.columns, f"Missing column: {col}"

    def test_cohort_only_contains_matched_subjects(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df, tmp_path
    ):
        _, cohort = self._build(sample_patients_df, sample_notes_df,
                                sample_labs_df, sample_vitals_df, tmp_path)
        expected_ids = {101, 102}
        assert set(cohort["subject_id"].unique()).issubset(expected_ids)

    def test_cohort_subject_without_labs_still_included(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df, tmp_path
    ):
        # Relaxed filter: labs are optional. A patient with notes + vitals is included
        # even without labs (feature extractor imputes zeros).
        labs_no_102 = sample_labs_df[sample_labs_df["subject_id"] != 102]
        _, cohort = self._build(sample_patients_df, sample_notes_df,
                                labs_no_102, sample_vitals_df, tmp_path)
        assert 102 in cohort["subject_id"].values

    def test_get_stats(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df, tmp_path
    ):
        builder, _ = self._build(sample_patients_df, sample_notes_df,
                                 sample_labs_df, sample_vitals_df, tmp_path)
        stats = builder.get_stats()
        assert "n_admissions" in stats
        assert "mortality_rate" in stats
        assert 0.0 <= stats["mortality_rate"] <= 1.0
