from pathlib import Path
import json
import logging
import pandas as pd
from configs.paths import PATHS
from api.input_schema import ClinicalSubmission
from api.patient_store import PatientStore

logger = logging.getLogger(__name__)


def run_for_patient(patient_id: str) -> dict:
    """
    Run full pipeline for one patient from MIMIC-IV CSVs.
    Used by: CLI --patient_id flag, POST /api/run-patient
    """
    logger.info("Running pipeline for MIMIC patient: %s", patient_id)

    from src.stage1_data_loading.patient_loader import PatientLoader
    from src.stage1_data_loading.notes_loader import NotesLoader
    from src.stage1_data_loading.labs_loader import LabsLoader
    from src.stage1_data_loading.vitals_loader import VitalsLoader

    patients_df = PatientLoader().load()
    notes_df = NotesLoader().load()
    labs_df = LabsLoader().load()
    vitals_df = VitalsLoader().load()

    # Filter to this patient
    sid = int(patient_id)
    patients_df = patients_df[patients_df["subject_id"] == sid]
    notes_df = notes_df[notes_df["subject_id"] == sid]
    labs_df = labs_df[labs_df["subject_id"] == sid]
    vitals_df = vitals_df[vitals_df["subject_id"] == sid]

    if patients_df.empty:
        raise ValueError(f"Patient {patient_id} not found in dataset")

    hadm_id = int(patients_df["hadm_id"].iloc[0])
    return _run_pipeline(patients_df, notes_df, labs_df, vitals_df,
                         sid, hadm_id)


def run_for_submission(submission: ClinicalSubmission) -> dict:
    """
    Run full pipeline for a form submission (new or returning patient).
    Handles all 3 cases automatically via patient_store.
    Used by: POST /api/submit-patient
    """
    store = PatientStore()
    subject_id = store.get_subject_id(submission)
    hadm_id = store.get_hadm_id(subject_id, submission.patient.admittime)

    logger.info("Submission for subject_id=%s, exists=%s",
                subject_id, store.exists(subject_id))

    # CASE 2: existing patient — merge old + new data
    if store.exists(subject_id):
        logger.info("Returning patient — merging with existing data")
        data = store.merge(subject_id, submission)
        patients_df = _build_patient_df(data["patient"])
        notes_df = data["notes"]
        labs_df = data["labs"]
        vitals_df = data["vitals"]
    # CASE 3: new patient — use submission directly
    else:
        logger.info("New patient — building from submission")
        from src.stage1_data_loading.patient_loader import PatientLoader
        from src.stage1_data_loading.notes_loader import NotesLoader
        from src.stage1_data_loading.labs_loader import LabsLoader
        from src.stage1_data_loading.vitals_loader import VitalsLoader
        patients_df = PatientLoader().load_from_input(submission.patient)
        notes_df = NotesLoader().load_from_input(
            submission.note, subject_id, hadm_id)
        labs_df = LabsLoader().load_from_input(
            submission.labs, subject_id, hadm_id)
        vitals_df = VitalsLoader().load_from_input(
            submission.vitals, subject_id, hadm_id)

    # Always save/update the store
    store.save(subject_id, submission)

    return _run_pipeline(patients_df, notes_df, labs_df, vitals_df,
                         subject_id, hadm_id)


def _build_patient_df(patient_dict: dict) -> pd.DataFrame:
    """Reconstruct patients DataFrame from stored patient.json dict."""
    import pandas as pd
    row = dict(patient_dict)
    row["admittime"] = pd.to_datetime(row.get("admittime"))
    row["dischtime"] = pd.to_datetime(row.get("dischtime"))
    if "los_days" not in row:
        row["los_days"] = (
            (row["dischtime"] - row["admittime"]).total_seconds() / 86400
            if row["dischtime"] else 5.0)
    row.setdefault("hospital_expire_flag", 0)
    row.setdefault("anchor_age", row.get("age", 0))
    row.setdefault("anchor_year_group", "2010-2019")
    row.setdefault("dod", None)
    row.setdefault("deathtime", None)
    return pd.DataFrame([row])


def _detect_lab_anomalies_raw(labs_df: "pd.DataFrame", hadm_id: int) -> list:
    """
    Detect lab anomalies directly from raw labs using ref_range columns.
    Bypasses LabsPreprocessor dedup which collapses PDF labs (all itemid=0) to 1 row.
    """
    import math
    adm = labs_df[labs_df["hadm_id"] == hadm_id].copy()
    if adm.empty:
        return []

    anomalies = []
    for _, row in adm.iterrows():
        val = row.get("valuenum")
        if val is None or (isinstance(val, float) and math.isnan(val)):
            continue
        try:
            val = float(val)
        except (ValueError, TypeError):
            continue

        ref_low = row.get("ref_range_lower")
        ref_high = row.get("ref_range_upper")

        # Skip if no reference range
        try:
            ref_low = float(ref_low)
            ref_high = float(ref_high)
            if math.isnan(ref_low) or math.isnan(ref_high):
                continue
        except (TypeError, ValueError):
            continue

        # Skip if value is within normal range
        if ref_low <= val <= ref_high:
            continue

        range_width = ref_high - ref_low
        if range_width <= 0:
            continue

        # Severity = how far outside the boundary, as a fraction of the range width
        # e.g. val=5 with range [70-100]: excess = 65, range=30, severity = 65/30 → clamped 1.0
        # e.g. val=105 with range [70-100]: excess = 5, range=30, severity = 5/30 = 0.17 → skipped
        if val < ref_low:
            excess = ref_low - val
        else:
            excess = val - ref_high
        severity = min(1.0, excess / range_width)

        if severity < 0.2:
            continue

        logger.debug("Lab anomaly: %s val=%.2f range=[%.2f-%.2f] severity=%.2f",
                     row.get("label"), val, ref_low, ref_high, severity)

        anomalies.append({
            "name":      str(row.get("label", "Unknown")),
            "value":     val,
            "unit":      str(row.get("valueuom", "")),
            "ref_low":   ref_low,
            "ref_high":  ref_high,
            "severity":  round(severity, 3),
            "direction": "HIGH" if val > ref_high else "LOW",
        })

    logger.info("Raw lab anomaly detection: %d/%d labs flagged", len(anomalies), len(adm))
    return sorted(anomalies, key=lambda x: x["severity"], reverse=True)


def _run_pipeline(patients_df, notes_df, labs_df, vitals_df,
                  subject_id: int, hadm_id: int) -> dict:
    """
    Run Stages 2-6 on the provided DataFrames.
    Called by both run_for_patient() and run_for_submission().
    Stages 2-6 never know whether data came from CSV or a form.
    """
    logger.info("Running pipeline stages 2-6 for %s/%s",
                subject_id, hadm_id)

    # ── Stage 2: Preprocessing ──────────────────────────────────────
    from src.stage2_preprocessing.text_cleaner import TextCleaner
    from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
    from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
    from src.stage2_preprocessing.time_aligner import TimeAligner

    # Keep raw labs before preprocessing for anomaly detection
    # (LabsPreprocessor deduplicates on itemid which collapses all PDF labs to 1 row)
    labs_df_raw = labs_df.copy() if not labs_df.empty else labs_df

    if not notes_df.empty:
        notes_df = TextCleaner().clean_dataframe(notes_df, text_col="text")
    if not vitals_df.empty:
        vitals_df = VitalsPreprocessor().preprocess(vitals_df)
    if not labs_df.empty:
        labs_df = LabsPreprocessor().preprocess(labs_df)
    if not notes_df.empty and not patients_df.empty:
        notes_df = TimeAligner().align(
            notes_df, patients_df, "charttime", "admittime")
    if not labs_df.empty and not patients_df.empty:
        labs_df = TimeAligner().align(
            labs_df, patients_df, "charttime", "admittime")
    if not vitals_df.empty and not patients_df.empty:
        vitals_df = TimeAligner().align(
            vitals_df, patients_df, "charttime", "admittime")

    # ── Stage 3: Feature extraction ─────────────────────────────────
    from src.stage3_feature_extraction.nlp_pipeline import NLPPipeline
    from src.stage3_feature_extraction.lab_pipeline import LabPipeline
    from src.stage3_feature_extraction.vitals_pipeline import VitalsPipeline
    import numpy as np

    note_text = ""
    if not notes_df.empty and "text" in notes_df.columns:
        note_text = notes_df["text"].iloc[-1]

    text_features = NLPPipeline().encode([note_text]) \
        if note_text else np.zeros((1, 768), dtype=np.float32)

    lab_features = LabPipeline().extract_for_admission(labs_df, hadm_id) \
        .reshape(1, -1) if not labs_df.empty \
        else np.zeros((1, 50), dtype=np.float32)

    stay_id = int(vitals_df["stay_id"].iloc[0]) \
        if not vitals_df.empty and "stay_id" in vitals_df.columns else 0

    vitals_features = VitalsPipeline().extract_for_stay(vitals_df, stay_id) \
        .reshape(1, -1) if (not vitals_df.empty and stay_id) \
        else np.zeros((1, 32), dtype=np.float32)

    # Build a separate vitals DataFrame for anomaly/trend analysis.
    # AnomalyDetector expects: vital_name (snake_case), valuenum, stay_id, hours_from_icu_admission
    # VitalsPreprocessor outputs: label (human-readable), value (renamed from valuenum)
    _VITAL_NAME_MAP = {
        "heart rate":                              "heart_rate",
        "systolic blood pressure":                 "systolic_bp",
        "non invasive blood pressure systolic":    "systolic_bp",
        "arterial blood pressure systolic":        "systolic_bp",
        "manual blood pressure systolic left":     "systolic_bp",
        "manual blood pressure systolic right":    "systolic_bp",
        "diastolic blood pressure":                "diastolic_bp",
        "non invasive blood pressure diastolic":   "diastolic_bp",
        "arterial blood pressure diastolic":       "diastolic_bp",
        "mean blood pressure":                     "mean_bp",
        "non invasive blood pressure mean":        "mean_bp",
        "arterial blood pressure mean":            "mean_bp",
        "respiratory rate":                        "respiratory_rate",
        "spo2":                                    "spo2",
        "o2 saturation":                           "spo2",
        "o2 saturation pulseoxymetry":             "spo2",
        "temperature fahrenheit":                  "temperature_f",
        "temperature celsius":                     "temperature_c",
        "temperature":                             "temperature_c",
    }
    vitals_for_analysis = pd.DataFrame()
    if not vitals_df.empty:
        va = vitals_df.copy()
        # Restore valuenum from value if preprocessor renamed it
        if "valuenum" not in va.columns and "value" in va.columns:
            va["valuenum"] = pd.to_numeric(va["value"], errors="coerce")
        # Rename label → vital_name then map to snake_case
        if "vital_name" not in va.columns and "label" in va.columns:
            va = va.rename(columns={"label": "vital_name"})
        va["vital_name"] = va["vital_name"].apply(
            lambda n: _VITAL_NAME_MAP.get(str(n).lower().strip())
        )
        va = va.dropna(subset=["vital_name", "valuenum"])
        if "hours_from_icu_admission" not in va.columns:
            va["hours_from_icu_admission"] = range(len(va))
        vitals_for_analysis = va

    # ── Stage 5: Analysis ───────────────────────────────────────────
    from src.stage5_analysis.mortality_predictor import MortalityPredictor
    from src.stage5_analysis.anomaly_detector import AnomalyDetector
    from src.stage5_analysis.trend_analyzer import TrendAnalyzer
    from src.stage5_analysis.summary_generator import SummaryGenerator

    predictor = MortalityPredictor()
    predictor.load_model()
    raw_prob = predictor.predict_proba(text_features, lab_features, vitals_features)
    mortality_prob = float(np.atleast_1d(raw_prob)[0])

    # Use raw labs for anomaly detection — preprocessed labs lose rows due to itemid=0 dedup
    # Cap to top 10 most severe to avoid overwhelming the dashboard
    lab_anomalies = _detect_lab_anomalies_raw(labs_df_raw, hadm_id)[:10] \
        if not labs_df_raw.empty else []
    vital_anomalies = AnomalyDetector().detect_vital_anomalies(
        vitals_for_analysis, stay_id) if (not vitals_for_analysis.empty and stay_id) else []
    vital_trends = TrendAnalyzer().analyze_vital_trends(
        vitals_for_analysis, stay_id) if (not vitals_for_analysis.empty and stay_id) else {}

    row = patients_df.iloc[0]
    demographics = {
        "age": int(row.get("anchor_age", row.get("age", 0))),
        "gender": str(row.get("gender", "U")),
    }
    admission_info = {
        "admittime": str(row.get("admittime", "")),
        "dischtime": str(row.get("dischtime", "")),
        "los_days": float(row.get("los_days", 0)),
    }

    # ── Stage 6: Output ─────────────────────────────────────────────
    from src.stage6_output.patient_summary import PatientSummaryBuilder
    from src.stage6_output.alert_generator import AlertGenerator
    from src.stage6_output.dashboard_data import DashboardDataExporter

    summary = PatientSummaryBuilder().build(
        subject_id=subject_id,
        hadm_id=hadm_id,
        demographics=demographics,
        admission_info=admission_info,
        note_text=note_text,
        lab_anomalies=lab_anomalies,
        vital_anomalies=vital_anomalies,
        vital_trends=vital_trends,
        mortality_result={
            "probability": mortality_prob,
            "risk_level": (
                "HIGH" if mortality_prob >= 0.40 else
                "MEDIUM" if mortality_prob >= 0.25 else "LOW"),
        },
    )

    alerts = AlertGenerator().generate_all_alerts(
        lab_anomalies, vital_anomalies, mortality_prob)
    summary["alerts"] = AlertGenerator().to_dict_list(alerts)

    out_path = DashboardDataExporter().export_patient_summary(summary)
    logger.info("Saved summary to %s", out_path)

    # Store note text for LLM context builder (not saved to JSON file)
    summary["_note_text"] = note_text[:500] if note_text else ""

    return summary


def run_for_hadm(hadm_id: int) -> dict:
    """
    Load and return the stored dashboard JSON for an existing hadm_id.
    No pipeline re-run — just reads the pre-generated file.
    Used by GET /api/patient/{hadm_id} (Case 1).
    """
    import json
    summaries_dir = PATHS.summaries_dir
    matches = list(summaries_dir.glob(f"patient_*_{hadm_id}.json"))
    matches = [m for m in matches if "_report" not in m.name]
    if not matches:
        raise FileNotFoundError(f"No summary found for hadm_id={hadm_id}")
    with open(matches[0]) as f:
        return json.load(f)
