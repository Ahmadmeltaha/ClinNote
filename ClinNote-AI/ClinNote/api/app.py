"""
ClinNote — Backend API

FastAPI app exposing the full ClinNote pipeline for Meltaha's frontend integration.
Also serves the temporary test UI at /test/.

Endpoints:
  GET  /api/health                     — health check
  GET  /api/patients                   — list all patients
  GET  /api/patient/{hadm_id}          — get existing patient dashboard (Case 1)
  POST /api/patient/{hadm_id}/update   — update existing patient with new data (Case 2)
  POST /api/patient/new                — new patient full pipeline (Case 3)
  POST /api/parse-pdf                  — extract lab values from uploaded PDF
  POST /api/run-patient                — run pipeline for MIMIC patient by subject_id

Run:
  cd ClinNote
  uvicorn api.app:app --reload --port 5000

Or for the test UI only (no uvicorn needed):
  python api/app.py
"""

import json
import logging
import os
import pickle
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.input_schema import ClinicalSubmission
from api.pipeline_runner import run_for_patient, run_for_submission, run_for_hadm
from api.patient_store import PatientStore
from configs.paths import PATHS

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="ClinNote API", version="2.0",
              description="Clinical Note AI Pipeline — Backend API")

# CORS — allow all origins so Meltaha can call from any frontend port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Startup: load LLM once
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    from api.llm_summarizer import load_llm
    hf_token = os.environ.get("HF_TOKEN", "")
    ok = load_llm(hf_token)
    if ok:
        logger.info("LLM ready (Llama-3.2-3B-Instruct)")
    else:
        logger.info("LLM not loaded — summaries will use template fallback")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    from api.llm_summarizer import _pipe
    return {
        "status": "ok",
        "version": "2.0",
        "llm_loaded": _pipe is not None,
        "summaries_dir": str(PATHS.summaries_dir),
    }


def _sanitize(obj):
    """Recursively replace NaN/Inf floats with None so JSON serialization never crashes."""
    import math
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


# ---------------------------------------------------------------------------
# Patient list
# ---------------------------------------------------------------------------

@app.get("/api/patients")
def get_patients():
    """Return list of all patients with their admissions. Used for search."""
    summaries_dir = PATHS.summaries_dir
    patients: dict[int, dict] = {}

    for json_file in sorted(summaries_dir.glob("patient_*_*.json")):
        # Skip report files
        if "_report" in json_file.name:
            continue
        try:
            with open(json_file) as f:
                data = json.load(f)
            sid = int(data.get("subject_id", 0))
            hid = int(data.get("hadm_id", 0))
            if sid == 0:
                continue
            if sid not in patients:
                patients[sid] = {
                    "subject_id": sid,
                    "age": data.get("demographics", {}).get("age"),
                    "gender": data.get("demographics", {}).get("gender"),
                    "hadm_ids": [],
                    "admissions": [],
                }
            patients[sid]["hadm_ids"].append(hid)
            patients[sid]["admissions"].append({
                "hadm_id": hid,
                "risk_level": data.get("predicted_mortality", {}).get("risk_level"),
                "probability": data.get("predicted_mortality", {}).get("probability"),
                "generated_at": data.get("generated_at"),
            })
        except Exception:
            continue

    return {"patients": list(patients.values()), "total": len(patients)}


# ---------------------------------------------------------------------------
# Case 1: Get existing patient dashboard
# ---------------------------------------------------------------------------

@app.get("/api/patient/{hadm_id}")
def get_patient_dashboard(hadm_id: int):
    """
    Return stored dashboard JSON for an existing patient admission.
    Case 1: loads pre-generated JSON, then enriches with live anomaly detection
    if lab/vital summaries are empty (old files generated before anomaly pipeline).
    """
    summaries_dir = PATHS.summaries_dir
    matches = list(summaries_dir.glob(f"patient_*_{hadm_id}.json"))
    matches = [m for m in matches if "_report" not in m.name]

    if not matches:
        raise HTTPException(404, f"No dashboard found for hadm_id={hadm_id}")

    with open(matches[0]) as f:
        data = json.load(f)

    # Enrich with anomaly detection if lab/vital alerts are missing
    lab_empty = not data.get("lab_summary", {}).get("top_abnormal")
    vital_empty = not data.get("vital_summary", {}).get("alerts")
    if lab_empty or vital_empty:
        try:
            _enrich_with_anomalies(data, hadm_id)
        except Exception as e:
            logger.warning("Anomaly enrichment failed for hadm_id=%s: %s", hadm_id, e)

    # Generate LLM summary
    from api.llm_summarizer import generate_summary, build_summary_context, _pipe
    if _pipe is not None:
        ctx = build_summary_context(case=1, summary=data)
        data["clinical_summary"] = generate_summary(case=1, context=ctx)

    return _sanitize(data)


def _enrich_with_anomalies(data: dict, hadm_id: int) -> None:
    """
    Load MIMIC labs/vitals CSVs for this hadm_id and run anomaly detection.
    Mutates data in-place to fill lab_summary and vital_summary.
    """
    from src.stage1_data_loading.labs_loader import LabsLoader
    from src.stage1_data_loading.vitals_loader import VitalsLoader
    from src.stage2_preprocessing.labs_preprocessor import LabsPreprocessor
    from src.stage2_preprocessing.vitals_preprocessor import VitalsPreprocessor
    from src.stage5_analysis.anomaly_detector import AnomalyDetector
    from src.stage5_analysis.trend_analyzer import TrendAnalyzer
    from api.pipeline_runner import _detect_lab_anomalies_raw
    import pandas as pd

    labs_df = LabsLoader().load()
    vitals_df = VitalsLoader().load()

    labs_df = labs_df[labs_df["hadm_id"] == hadm_id]
    vitals_df = vitals_df[vitals_df["hadm_id"] == hadm_id]

    # Lab anomalies — use raw labs (has ref ranges from MIMIC)
    lab_anomalies = []
    if not labs_df.empty:
        # LabsPreprocessor flags is_abnormal using ref_range columns
        labs_proc = LabsPreprocessor().preprocess(labs_df.copy())
        if not labs_proc.empty:
            lab_anomalies = AnomalyDetector().detect_lab_anomalies(labs_proc, hadm_id)
        if not lab_anomalies:
            lab_anomalies = _detect_lab_anomalies_raw(labs_df, hadm_id)
        lab_anomalies = lab_anomalies[:10]

    # Vital name mapping: MIMIC labels → snake_case keys expected by AnomalyDetector
    _VITAL_MAP = {
        "heart rate":                              "heart_rate",
        "non invasive blood pressure systolic":    "systolic_bp",
        "arterial blood pressure systolic":        "systolic_bp",
        "manual blood pressure systolic left":     "systolic_bp",
        "manual blood pressure systolic right":    "systolic_bp",
        "non invasive blood pressure diastolic":   "diastolic_bp",
        "arterial blood pressure diastolic":       "diastolic_bp",
        "non invasive blood pressure mean":        "mean_bp",
        "arterial blood pressure mean":            "mean_bp",
        "respiratory rate":                        "respiratory_rate",
        "o2 saturation pulseoxymetry":             "spo2",
        "o2 saturation":                           "spo2",
        "spo2":                                    "spo2",
        "temperature fahrenheit":                  "temperature_f",
        "temperature celsius":                     "temperature_c",
    }

    # Vital anomalies
    vital_anomalies = []
    vital_trends = {}
    if not vitals_df.empty:
        vitals_proc = VitalsPreprocessor().preprocess(vitals_df.copy())
        if not vitals_proc.empty:
            if "valuenum" not in vitals_proc.columns and "value" in vitals_proc.columns:
                vitals_proc["valuenum"] = pd.to_numeric(vitals_proc["value"], errors="coerce")
            if "vital_name" not in vitals_proc.columns and "label" in vitals_proc.columns:
                vitals_proc = vitals_proc.rename(columns={"label": "vital_name"})
            # Map MIMIC labels to snake_case keys AnomalyDetector understands
            vitals_proc["vital_name"] = vitals_proc["vital_name"].apply(
                lambda n: _VITAL_MAP.get(str(n).lower().strip(), None)
            )
            vitals_proc = vitals_proc.dropna(subset=["vital_name"])
            if "hours_from_icu_admission" not in vitals_proc.columns:
                vitals_proc["hours_from_icu_admission"] = range(len(vitals_proc))
            stay_id = int(vitals_proc["stay_id"].iloc[0]) if "stay_id" in vitals_proc.columns and not vitals_proc.empty else 0
            if stay_id and not vitals_proc.empty:
                vital_anomalies = AnomalyDetector().detect_vital_anomalies(vitals_proc, stay_id)
                vital_trends = TrendAnalyzer().analyze_vital_trends(vitals_proc, stay_id)

    # Update data in-place
    from src.stage6_output.alert_generator import AlertGenerator
    mortality_prob = data.get("predicted_mortality", {}).get("probability", 0.0)

    data["lab_summary"] = {
        "n_abnormal": len(lab_anomalies),
        "top_abnormal": lab_anomalies,
    }
    data["vital_summary"] = {
        "alerts": vital_anomalies,
        "trend_overview": vital_trends,
    }

    # Regenerate alerts with the new anomalies
    alerts = AlertGenerator().generate_all_alerts(lab_anomalies, vital_anomalies, mortality_prob)
    data["alerts"] = AlertGenerator().to_dict_list(alerts)
    logger.info("Enriched hadm_id=%s: %d lab + %d vital anomalies", hadm_id, len(lab_anomalies), len(vital_anomalies))


# ---------------------------------------------------------------------------
# Case 2: Update existing patient with new data
# ---------------------------------------------------------------------------

@app.post("/api/patient/{hadm_id}/update")
async def update_patient(
    hadm_id: int,
    note_text: str = Form(default=""),
    vitals: str = Form(default="[]"),
    labs_pdf: UploadFile = File(default=None),
):
    """
    Update an existing patient with new data. Any combination of:
    - note_text (string, optional)
    - labs_pdf  (PDF file, optional) — auto-extracted lab values
    - vitals    (JSON string, optional) — [{"name": "Heart Rate", "value": 88}, ...]

    Re-runs the pipeline and returns an updated dashboard JSON.
    """
    import json as _json
    from datetime import datetime

    # Find existing summary for comparison
    summaries_dir = PATHS.summaries_dir
    matches = list(summaries_dir.glob(f"patient_*_{hadm_id}.json"))
    matches = [m for m in matches if "_report" not in m.name]
    old_summary = None
    subject_id = None

    if matches:
        with open(matches[0]) as f:
            old_summary = _json.load(f)
        subject_id = old_summary.get("subject_id")

    if subject_id is None:
        raise HTTPException(404, f"No existing patient found for hadm_id={hadm_id}")

    now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    # Parse vitals JSON
    try:
        vital_list = _json.loads(vitals) if vitals else []
    except Exception:
        vital_list = []

    # Parse labs from PDF if uploaded
    lab_list = []
    if labs_pdf and labs_pdf.filename:
        from api.pdf_lab_extractor import extract_labs_from_pdf
        pdf_bytes = await labs_pdf.read()
        extracted = extract_labs_from_pdf(pdf_bytes)
        for item in extracted:
            lab_list.append({
                "label": item["name"],
                "valuenum": item["value"],
                "valueuom": item.get("unit", ""),
                "charttime": now_str,
                "ref_range_lower": item.get("ref_low"),
                "ref_range_upper": item.get("ref_high"),
            })

    # Build submission
    demo = old_summary.get("demographics", {})
    submission_data = {
        "patient": {
            "subject_id": subject_id,
            "age": int(demo.get("age", 0)),
            "gender": demo.get("gender", "U"),
            "admittime": now_str,
        },
        "note": {"text": note_text, "charttime": now_str} if note_text.strip() else None,
        "labs": lab_list,
        "vitals": [{"label": v["name"], "valuenum": float(v["value"]),
                    "charttime": now_str} for v in vital_list],
    }

    submission = ClinicalSubmission(**submission_data)
    new_summary = run_for_submission(submission)

    # Generate LLM summary focused on change
    from api.llm_summarizer import generate_summary, build_summary_context, _pipe
    if _pipe is not None:
        ctx = build_summary_context(case=2, summary=new_summary, old_summary=old_summary)
        new_summary["clinical_summary"] = generate_summary(case=2, context=ctx)

    # Add diff info for frontend
    old_prob = old_summary.get("predicted_mortality", {}).get("probability", 0.0)
    new_prob = new_summary.get("predicted_mortality", {}).get("probability", 0.0)
    new_summary["update_diff"] = {
        "old_probability": old_prob,
        "new_probability": new_prob,
        "changed": abs(new_prob - old_prob) > 0.001,
        "modalities_updated": (
            (["notes"] if note_text.strip() else []) +
            (["labs"] if lab_list else []) +
            (["vitals"] if vital_list else [])
        ),
    }

    return _sanitize(new_summary)


# ---------------------------------------------------------------------------
# Case 3: New patient — full pipeline
# ---------------------------------------------------------------------------

@app.post("/api/patient/new")
async def new_patient(
    age: int = Form(...),
    gender: str = Form(...),
    admittime: str = Form(default=""),
    note_text: str = Form(default=""),
    vitals: str = Form(default="[]"),
    labs_pdf: UploadFile = File(default=None),
):
    """
    Full pipeline for a brand new patient.
    Required: age, gender
    Optional: note_text, vitals (JSON), labs_pdf
    """
    import json as _json
    from datetime import datetime

    now_str = admittime or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    # Parse vitals
    try:
        vital_list = _json.loads(vitals) if vitals else []
    except Exception:
        vital_list = []

    # Parse labs from PDF
    lab_list = []
    if labs_pdf and labs_pdf.filename:
        from api.pdf_lab_extractor import extract_labs_from_pdf
        pdf_bytes = await labs_pdf.read()
        extracted = extract_labs_from_pdf(pdf_bytes)
        for item in extracted:
            lab_list.append({
                "label": item["name"],
                "valuenum": item["value"],
                "valueuom": item.get("unit", ""),
                "charttime": now_str,
                "ref_range_lower": item.get("ref_low"),
                "ref_range_upper": item.get("ref_high"),
            })

    submission_data = {
        "patient": {
            "age": age,
            "gender": gender,
            "admittime": now_str,
        },
        "note": {"text": note_text, "charttime": now_str} if note_text.strip() else None,
        "labs": lab_list,
        "vitals": [{"label": v["name"], "valuenum": float(v["value"]),
                    "charttime": now_str} for v in vital_list],
    }

    submission = ClinicalSubmission(**submission_data)
    summary = run_for_submission(submission)

    # LLM summary — new patient
    from api.llm_summarizer import generate_summary, build_summary_context, _pipe
    if _pipe is not None:
        ctx = build_summary_context(case=3, summary=summary)
        summary["clinical_summary"] = generate_summary(case=3, context=ctx)

    return _sanitize(summary)


# ---------------------------------------------------------------------------
# PDF parse endpoint (standalone — returns extracted labs for preview)
# ---------------------------------------------------------------------------

@app.post("/api/parse-pdf")
async def parse_pdf(lab_pdf: UploadFile = File(...)):
    """
    Upload a PDF lab report → returns extracted lab values as JSON.
    Use this to show an editable preview table before submitting.
    """
    from api.pdf_lab_extractor import extract_labs_from_pdf
    pdf_bytes = await lab_pdf.read()
    labs = extract_labs_from_pdf(pdf_bytes)
    return _sanitize({
        "labs": labs,
        "parse_success": len(labs) > 0,
        "n_extracted": len(labs),
        "filename": lab_pdf.filename,
    })


# ---------------------------------------------------------------------------
# Legacy: run pipeline for MIMIC patient by subject_id
# ---------------------------------------------------------------------------

@app.post("/api/run-patient")
def trigger_patient(body: dict, background_tasks: BackgroundTasks):
    """Run pipeline for existing MIMIC patient by subject_id."""
    patient_id = body.get("patient_id")
    if not patient_id:
        raise HTTPException(400, "patient_id required")
    background_tasks.add_task(run_for_patient, str(patient_id))
    return {"status": "processing", "patient_id": patient_id}


@app.get("/api/result/{patient_id}")
def get_result(patient_id: str):
    """Retrieve stored result JSON for a MIMIC patient."""
    summaries_dir = PATHS.summaries_dir
    matches = list(summaries_dir.glob(f"patient_{patient_id}*.json"))
    matches = [m for m in matches if "_report" not in m.name]
    if not matches:
        raise HTTPException(404, f"No result found for patient {patient_id}")
    with open(matches[0]) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Dev server entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=5000, reload=True)
