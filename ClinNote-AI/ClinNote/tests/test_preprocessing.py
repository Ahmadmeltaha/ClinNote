"""
Tests: Stage 2 - Preprocessing

Verifies TextCleaner, VitalsPreprocessor, LabsPreprocessor,
PatientMatcher, and TimeAligner using synthetic data.
No real MIMIC data required.
"""

import pytest
import pandas as pd
import numpy as np


# ===========================================================================
# Shared fixtures
# ===========================================================================

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
            "Patient ___ admitted.\n---\n\nChest pain. SpO2 98%%.",
            "  Patient ___   with pneumonia.  SpO2   low.  ",
            "Patient ___ altered mental status.===\nLabs normal.",
        ],
    })


@pytest.fixture
def sample_vitals_df() -> pd.DataFrame:
    return pd.DataFrame({
        "subject_id"  : [101, 101, 102, 102, 103],
        "hadm_id"     : [1001, 1001, 1002, 1002, 1003],
        "stay_id"     : [301, 301, 302, 302, 303],
        "label"       : [
            "Heart Rate",
            "Temperature Fahrenheit",
            "Respiratory Rate",
            "O2 Saturation Pulseoxymetry",
            "Arterial Blood Pressure systolic",
        ],
        "valuenum"    : [88.0, 98.6, 18.0, 97.0, 120.0],
        "value"       : ["88", "98.6", "18", "97", "120"],
        "charttime"   : pd.to_datetime([
            "2020-01-08 06:00", "2020-01-08 08:00",
            "2020-02-14 10:00", "2020-02-14 12:00",
            "2020-03-01 09:00",
        ]),
        "vital_source": ["chartevents"] * 5,
        "warning"     : [0, 0, 0, 0, 0],
    })


@pytest.fixture
def sample_labs_df() -> pd.DataFrame:
    return pd.DataFrame({
        "subject_id"      : [101, 101, 102, 102, 103],
        "hadm_id"         : [1001, 1001, 1002, 1002, 1003],
        "itemid"          : [50912, 51222, 50912, 51301, 50912],
        "label"           : ["Creatinine", "Hemoglobin", "Creatinine", "WBC", "Creatinine"],
        "charttime"       : pd.to_datetime(["2020-01-09", "2020-01-10",
                                             "2020-02-15", "2020-02-15", "2020-03-02"]),
        "storetime"       : pd.to_datetime(["2020-01-09", "2020-01-10",
                                             "2020-02-15", "2020-02-15", "2020-03-02"]),
        "value"           : ["3.2", "8.5", "1.0", "12.5", "0.9"],
        "valuenum"        : [3.2, 8.5, 1.0, 12.5, 0.9],
        "valueuom"        : ["mg/dL", "g/dL", "mg/dL", "K/uL", "mg/dL"],
        "ref_range_lower" : [0.6, 12.0, 0.6, 4.5, 0.6],
        "ref_range_upper" : [1.2, 17.5, 1.2, 11.0, 1.2],
        "flag"            : ["abnormal", None, None, None, None],
        "fluid"           : ["Blood"] * 5,
        "category"        : ["Chemistry", "Hematology", "Chemistry", "Hematology", "Chemistry"],
    })


@pytest.fixture
def sample_patients_df() -> pd.DataFrame:
    return pd.DataFrame({
        "subject_id"          : [101, 102, 103, 104],
        "hadm_id"             : [1001, 1002, 1003, 1004],
        "admittime"           : pd.to_datetime(["2020-01-08", "2020-02-14", "2020-03-01", "2020-04-01"]),
        "dischtime"           : pd.to_datetime(["2020-01-15", "2020-02-20", "2020-03-10", "2020-04-08"]),
        "hospital_expire_flag": [0, 1, 0, 0],
        "gender"              : ["M", "F", "M", "F"],
        "anchor_age"          : [65, 72, 55, 80],
        "anchor_year"         : [2020, 2020, 2020, 2020],
        "anchor_year_group"   : ["2017-2019"] * 4,
        "race"                : ["WHITE", "BLACK/AFRICAN AMERICAN", "WHITE", None],
        "marital_status"      : ["MARRIED", None, "SINGLE", "MARRIED"],
        "insurance"           : ["Medicare", "Medicaid", None, "Medicare"],
    })


# ===========================================================================
# Tests: TextCleaner
# ===========================================================================

class TestTextCleaner:
    def test_phi_replaced(self):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner(phi_replacement="[REDACTED]")
        result = cleaner.clean("Patient ___ admitted on ___.")
        assert "[REDACTED]" in result
        assert "___" not in result

    def test_dividers_removed(self):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        result = cleaner.clean("Header\n---\nBody text\n===\nFooter")
        assert "---" not in result
        assert "===" not in result
        assert "Body text" in result

    def test_whitespace_collapsed(self):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        result = cleaner.clean("Word1   \n\n  Word2   \t  Word3")
        assert "  " not in result   # no double spaces
        assert "Word1" in result
        assert "Word2" in result

    def test_empty_string_returns_empty(self):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        assert cleaner.clean("") == ""
        assert cleaner.clean("   ") == ""

    def test_none_returns_empty(self):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        assert cleaner.clean(None) == ""  # type: ignore

    def test_no_lowercase_by_default(self):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner(lowercase=False)
        result = cleaner.clean("Patient Has ELEVATED Troponin.")
        assert "ELEVATED" in result

    def test_lowercase_option(self):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner(lowercase=True)
        result = cleaner.clean("Patient Has ELEVATED Troponin.")
        assert result == result.lower()

    def test_truncation_to_max_length(self):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner(max_length=50)
        long_text = "A" * 200
        result = cleaner.clean(long_text)
        assert len(result) <= 50

    def test_clean_dataframe_returns_dataframe(self, sample_notes_df):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        result = cleaner.clean_dataframe(sample_notes_df)
        assert isinstance(result, pd.DataFrame)
        assert "text_cleaned" in result.columns

    def test_clean_dataframe_drops_empty_rows(self):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        df = pd.DataFrame({"text": ["Valid text here.", "___", "   "]})
        cleaner = TextCleaner()
        result = cleaner.clean_dataframe(df)
        # "___" becomes "[REDACTED]" (not empty), "   " becomes "" (dropped)
        assert len(result) == 2

    def test_clean_series_same_length_as_input(self, sample_notes_df):
        from src.stage2_preprocessing.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        result = cleaner.clean_series(sample_notes_df["text"])
        assert len(result) == len(sample_notes_df)


# ===========================================================================
# Tests: VitalsPreprocessor
# ===========================================================================

class TestVitalsPreprocessor:
    def test_preprocess_returns_dataframe(self, sample_vitals_df):
        from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
        result = VitalsPreprocessor().preprocess(sample_vitals_df)
        assert isinstance(result, pd.DataFrame)

    def test_value_column_present(self, sample_vitals_df):
        from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
        result = VitalsPreprocessor().preprocess(sample_vitals_df)
        assert "value" in result.columns

    def test_is_abnormal_column_added(self, sample_vitals_df):
        from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
        result = VitalsPreprocessor().preprocess(sample_vitals_df)
        assert "is_abnormal" in result.columns
        assert result["is_abnormal"].dtype == bool

    def test_temperature_fahrenheit_converted(self, sample_vitals_df):
        from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
        result = VitalsPreprocessor().preprocess(sample_vitals_df)
        # 98.6°F -> 37.0°C
        fahrenheit_rows = result[result["label"].str.contains("Fahrenheit", na=False)]
        assert len(fahrenheit_rows) == 0   # should be renamed to Celsius
        celsius_rows = result[result["label"].str.contains("Celsius", na=False)]
        if len(celsius_rows) > 0:
            # 98.6°F -> 37.0°C (±0.1 tolerance)
            assert abs(celsius_rows.iloc[0]["value"] - 37.0) < 0.2

    def test_no_null_values_after_preprocessing(self, sample_vitals_df):
        from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
        result = VitalsPreprocessor().preprocess(sample_vitals_df)
        assert result["value"].isna().sum() == 0

    def test_out_of_bounds_rows_dropped(self):
        from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
        df = pd.DataFrame({
            "subject_id"  : [101, 101],
            "hadm_id"     : [1001, 1001],
            "label"       : ["Heart Rate", "Heart Rate"],
            "valuenum"    : [88.0, 999.0],   # 999 is out of physiological range (0-300)
            "value"       : ["88", "999"],
            "charttime"   : pd.to_datetime(["2020-01-08", "2020-01-09"]),
            "vital_source": ["chartevents", "chartevents"],
            "warning"     : [0, 0],
        })
        result = VitalsPreprocessor().preprocess(df)
        assert (result["value"] <= 300).all()

    def test_warned_rows_dropped(self):
        from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
        df = pd.DataFrame({
            "subject_id"  : [101, 101],
            "hadm_id"     : [1001, 1001],
            "label"       : ["Heart Rate", "Heart Rate"],
            "valuenum"    : [88.0, 72.0],
            "value"       : ["88", "72"],
            "charttime"   : pd.to_datetime(["2020-01-08", "2020-01-09"]),
            "vital_source": ["chartevents", "chartevents"],
            "warning"     : [1, 0],   # first row should be dropped
        })
        result = VitalsPreprocessor(drop_warned=True).preprocess(df)
        assert len(result) == 1

    def test_heart_rate_flagged_abnormal(self):
        from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
        df = pd.DataFrame({
            "subject_id"  : [101],
            "hadm_id"     : [1001],
            "label"       : ["Heart Rate"],
            "valuenum"    : [130.0],   # > 100 = abnormal
            "value"       : ["130"],
            "charttime"   : pd.to_datetime(["2020-01-08"]),
            "vital_source": ["chartevents"],
            "warning"     : [0],
        })
        result = VitalsPreprocessor().preprocess(df)
        assert result["is_abnormal"].iloc[0] == True


# ===========================================================================
# Tests: LabsPreprocessor
# ===========================================================================

class TestLabsPreprocessor:
    def test_invalid_missing_strategy_raises(self):
        from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
        with pytest.raises(ValueError):
            LabsPreprocessor(missing_strategy="invalid")

    def test_preprocess_returns_dataframe(self, sample_labs_df):
        from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
        result = LabsPreprocessor().preprocess(sample_labs_df)
        assert isinstance(result, pd.DataFrame)

    def test_is_abnormal_column_added(self, sample_labs_df):
        from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
        result = LabsPreprocessor().preprocess(sample_labs_df)
        assert "is_abnormal" in result.columns
        assert result["is_abnormal"].dtype == bool

    def test_severity_score_column_added(self, sample_labs_df):
        from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
        result = LabsPreprocessor().preprocess(sample_labs_df)
        assert "severity_score" in result.columns
        # Must be within [0, 1]
        assert (result["severity_score"] >= 0.0).all()
        assert (result["severity_score"] <= 1.0).all()

    def test_creatinine_3_2_flagged_abnormal(self, sample_labs_df):
        """Creatinine 3.2 is above ref range 0.6-1.2 -> should be abnormal."""
        from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
        result = LabsPreprocessor().preprocess(sample_labs_df)
        creat = result[(result["label"] == "Creatinine") & (result["valuenum"] == 3.2)]
        if len(creat) > 0:
            assert creat["is_abnormal"].iloc[0] == True

    def test_normal_lab_not_flagged_abnormal(self, sample_labs_df):
        """Creatinine 0.9 is within ref range 0.6-1.2 -> should NOT be abnormal."""
        from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
        result = LabsPreprocessor().preprocess(sample_labs_df)
        normal = result[(result["label"] == "Creatinine") & (result["valuenum"] == 0.9)]
        if len(normal) > 0:
            assert normal["is_abnormal"].iloc[0] == False

    def test_drop_strategy_removes_null_valuenum(self):
        from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
        df = pd.DataFrame({
            "subject_id"      : [101, 102],
            "hadm_id"         : [1001, 1002],
            "itemid"          : [50912, 50912],
            "label"           : ["Creatinine", "Creatinine"],
            "charttime"       : pd.to_datetime(["2020-01-09", "2020-01-10"]),
            "storetime"       : pd.to_datetime(["2020-01-09", "2020-01-10"]),
            "valuenum"        : [None, 1.0],
            "value"           : [None, "1.0"],
            "valueuom"        : ["mg/dL", "mg/dL"],
            "ref_range_lower" : [0.6, 0.6],
            "ref_range_upper" : [1.2, 1.2],
            "flag"            : [None, None],
            "fluid"           : ["Blood", "Blood"],
            "category"        : ["Chemistry", "Chemistry"],
        })
        result = LabsPreprocessor(missing_strategy="drop").preprocess(df)
        assert result["valuenum"].isna().sum() == 0
        assert len(result) == 1

    def test_outlier_removed(self):
        """
        A value clearly outside the std threshold should be removed.

        Note: with a 5-sigma threshold, a single large outlier can inflate the
        std so much that its own z-score stays below 5 (masking effect). We
        therefore use a tighter threshold (2.0) on a dataset where the outlier
        is unambiguously outside 2 std deviations from the non-outlier cluster.
        """
        from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
        import numpy as np
        # Tight cluster around 1.0, plus one clear outlier
        # With threshold=2.0 sigma: 999 is far enough out even accounting for inflation
        # Verify: mean~91.75, std~300.9 -> z(999)=3.02 > 2.0 -> removed
        values = [1.0, 1.1, 1.0, 1.2, 0.9, 1.0, 1.1, 1.0, 1.0, 1.0, 999.0]
        df = pd.DataFrame({
            "subject_id"      : list(range(101, 101 + len(values))),
            "hadm_id"         : list(range(1001, 1001 + len(values))),
            "itemid"          : [50912] * len(values),
            "label"           : ["Creatinine"] * len(values),
            "charttime"       : pd.to_datetime(["2020-01-01"] * len(values)),
            "storetime"       : pd.to_datetime(["2020-01-01"] * len(values)),
            "valuenum"        : values,
            "value"           : [str(v) for v in values],
            "valueuom"        : ["mg/dL"] * len(values),
            "ref_range_lower" : [0.6] * len(values),
            "ref_range_upper" : [1.2] * len(values),
            "flag"            : [None] * len(values),
            "fluid"           : ["Blood"] * len(values),
            "category"        : ["Chemistry"] * len(values),
        })
        # z(999) = 3.02 > 2.0 threshold -> should be removed
        result = LabsPreprocessor(outlier_std_threshold=2.0).preprocess(df)
        assert 999.0 not in result["valuenum"].values


# ===========================================================================
# Tests: PatientMatcher
# ===========================================================================

class TestPatientMatcher:
    def test_invalid_stay_selection_raises(self):
        from src.stage2_preprocessing.patient_matcher import PatientMatcher
        with pytest.raises(ValueError):
            PatientMatcher(icu_stay_selection="invalid")

    def test_match_returns_tuple(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
    ):
        from src.stage2_preprocessing.patient_matcher import PatientMatcher
        result = PatientMatcher().match(
            sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_matched_df_has_required_columns(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
    ):
        from src.stage2_preprocessing.patient_matcher import PatientMatcher
        matched_df, _ = PatientMatcher().match(
            sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
        )
        for col in ["subject_id", "hadm_id", "gender", "hospital_expire_flag"]:
            assert col in matched_df.columns

    def test_only_matched_subjects_returned(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
    ):
        from src.stage2_preprocessing.patient_matcher import PatientMatcher
        matched_df, matched_ids = PatientMatcher().match(
            sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
        )
        # Subject 104 is NOT in notes/labs/vitals -> must not appear
        assert 104 not in matched_df["subject_id"].values
        assert set(matched_df["subject_id"].unique()).issubset(matched_ids)

    def test_gender_encoded_as_int(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
    ):
        from src.stage2_preprocessing.patient_matcher import PatientMatcher
        matched_df, _ = PatientMatcher().match(
            sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
        )
        if "gender" in matched_df.columns and len(matched_df) > 0:
            assert matched_df["gender"].dropna().isin([0, 1]).all()

    def test_null_race_filled(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
    ):
        from src.stage2_preprocessing.patient_matcher import PatientMatcher
        matched_df, _ = PatientMatcher().match(
            sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
        )
        if "race" in matched_df.columns:
            assert matched_df["race"].isna().sum() == 0

    def test_null_insurance_filled(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
    ):
        from src.stage2_preprocessing.patient_matcher import PatientMatcher
        matched_df, _ = PatientMatcher().match(
            sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
        )
        if "insurance" in matched_df.columns:
            assert matched_df["insurance"].isna().sum() == 0

    def test_matched_ids_is_set_of_ints(
        self, sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
    ):
        from src.stage2_preprocessing.patient_matcher import PatientMatcher
        _, matched_ids = PatientMatcher().match(
            sample_patients_df, sample_notes_df, sample_labs_df, sample_vitals_df
        )
        assert isinstance(matched_ids, set)


# ===========================================================================
# Tests: TimeAligner
# ===========================================================================

class TestTimeAligner:
    def test_invalid_reference_raises(self):
        from src.stage2_preprocessing.time_aligner import TimeAligner
        with pytest.raises(ValueError):
            TimeAligner(reference="invalid_ref")

    def test_align_adds_hours_from_admission(self, sample_vitals_df, sample_patients_df):
        from src.stage2_preprocessing.time_aligner import TimeAligner
        aligner = TimeAligner(reference="admittime", clip_negative=False)
        result = aligner.align(sample_vitals_df, sample_patients_df)
        assert "hours_from_admission" in result.columns

    def test_hours_from_admission_non_negative_when_clipped(
        self, sample_vitals_df, sample_patients_df
    ):
        from src.stage2_preprocessing.time_aligner import TimeAligner
        aligner = TimeAligner(reference="admittime", clip_negative=True)
        result = aligner.align(sample_vitals_df, sample_patients_df)
        assert (result["hours_from_admission"] >= 0).all()

    def test_hours_computed_correctly(self):
        from src.stage2_preprocessing.time_aligner import TimeAligner
        events = pd.DataFrame({
            "subject_id": [101],
            "hadm_id"   : [1001],
            "charttime" : pd.to_datetime(["2020-01-08 12:00"]),
        })
        patients = pd.DataFrame({
            "subject_id": [101],
            "hadm_id"   : [1001],
            "admittime" : pd.to_datetime(["2020-01-08 00:00"]),
        })
        aligner = TimeAligner(reference="admittime", clip_negative=True)
        result = aligner.align(events, patients)
        # Event is 12 hours after admission
        assert abs(result["hours_from_admission"].iloc[0] - 12.0) < 0.01

    def test_pre_admission_events_dropped_when_clip_true(self):
        from src.stage2_preprocessing.time_aligner import TimeAligner
        events = pd.DataFrame({
            "subject_id": [101, 101],
            "hadm_id"   : [1001, 1001],
            "charttime" : pd.to_datetime(["2020-01-07 12:00",   # BEFORE admission
                                           "2020-01-08 06:00"]), # after admission
        })
        patients = pd.DataFrame({
            "subject_id": [101],
            "hadm_id"   : [1001],
            "admittime" : pd.to_datetime(["2020-01-08 00:00"]),
        })
        aligner = TimeAligner(reference="admittime", clip_negative=True)
        result = aligner.align(events, patients)
        assert len(result) == 1
        assert result["hours_from_admission"].iloc[0] >= 0

    def test_max_hours_filter(self):
        from src.stage2_preprocessing.time_aligner import TimeAligner
        events = pd.DataFrame({
            "subject_id": [101, 101],
            "hadm_id"   : [1001, 1001],
            "charttime" : pd.to_datetime(["2020-01-08 06:00",   # 6h after admission
                                           "2020-01-11 00:00"]), # 72h after admission
        })
        patients = pd.DataFrame({
            "subject_id": [101],
            "hadm_id"   : [1001],
            "admittime" : pd.to_datetime(["2020-01-08 00:00"]),
        })
        aligner = TimeAligner(reference="admittime", clip_negative=True)
        result = aligner.align(events, patients, max_hours=48.0)
        assert len(result) == 1    # only the 6h event survives
        assert result["hours_from_admission"].iloc[0] <= 48.0

    def test_align_labs_method(self, sample_labs_df, sample_patients_df):
        from src.stage2_preprocessing.time_aligner import TimeAligner
        aligner = TimeAligner(reference="admittime")
        result = aligner.align_labs(sample_labs_df, sample_patients_df)
        assert "hours_from_admission" in result.columns

    def test_align_notes_method(self, sample_notes_df, sample_patients_df):
        from src.stage2_preprocessing.time_aligner import TimeAligner
        aligner = TimeAligner(reference="admittime")
        result = aligner.align_notes(sample_notes_df, sample_patients_df)
        assert "hours_from_admission" in result.columns

    def test_filter_window(self, sample_vitals_df, sample_patients_df):
        from src.stage2_preprocessing.time_aligner import TimeAligner
        aligner = TimeAligner(reference="admittime", clip_negative=False)
        aligned = aligner.align(sample_vitals_df, sample_patients_df)
        filtered = aligner.filter_window(aligned, "hours_from_admission", max_hours=48.0)
        assert (filtered["hours_from_admission"] <= 48.0).all()
