"""
D20 — Generate final output files for the web dashboard.

Runs the full Stage 6 output pipeline:
  1. Loads cohort + feature store
  2. Gets mortality predictions for all patients
  3. Generates alerts using AlertGenerator
  4. Builds patient summaries using PatientSummaryBuilder
  5. Exports per-patient JSON + cohort overview JSON to outputs/summaries/
"""

import json
import logging
import os
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch

from configs.paths import PATHS
from src.stage3_feature_extraction.feature_store import FeatureStore
from src.stage5_analysis.anomaly_detector import AnomalyDetector
from src.stage5_analysis.trend_analyzer import TrendAnalyzer
from src.stage6_output.alert_generator import AlertGenerator
from src.stage6_output.dashboard_data import DashboardDataExporter
from src.stage6_output.patient_summary import PatientSummaryBuilder
from src.stage6_output.report_exporter import ReportExporter

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

SUMMARY_DIR = PATHS.summaries_dir


def load_mortality_probs(hadm_ids: list[int], store: FeatureStore) -> dict[int, float]:
    checkpoints = sorted(PATHS.models_dir.glob("*.pt"))
    if not checkpoints:
        logger.warning("No checkpoint found — using 0.0 for all patients.")
        return {hid: 0.0 for hid in hadm_ids}

    from src.stage5_analysis.mortality_predictor import MortalityPredictor
    ckpt = checkpoints[-1]
    logger.info("Loading checkpoint: %s", ckpt)
    predictor = MortalityPredictor(model_checkpoint=ckpt)
    predictor.load_model()

    # Load all features as arrays
    text_embs,   text_ids   = store.load_text_embeddings()
    lab_feats,   lab_ids    = store.load_lab_features()
    vital_feats, vital_ids  = store.load_vitals_features()

    text_map  = {int(hid): emb for hid, emb in zip(text_ids,  text_embs)}
    lab_map   = {int(hid): f   for hid, f   in zip(lab_ids,   lab_feats)}
    vital_map = {int(hid): f   for hid, f   in zip(vital_ids, vital_feats)}

    probs = {}
    for hid in hadm_ids:
        hid = int(hid)
        zeros_768 = torch.zeros(1, 768)
        zeros_50  = torch.zeros(1, 50)
        zeros_32  = torch.zeros(1, 32)
        t = torch.tensor(text_map[hid],  dtype=torch.float32).unsqueeze(0) if hid in text_map  else zeros_768
        l = torch.tensor(lab_map[hid],   dtype=torch.float32).unsqueeze(0) if hid in lab_map   else zeros_50
        v = torch.tensor(vital_map[hid], dtype=torch.float32).unsqueeze(0) if hid in vital_map else zeros_32
        probs[hid] = float(predictor.predict_proba(t, l, v))
    return probs


def classify_risk(prob: float) -> str:
    if prob >= 0.30:
        return "HIGH"
    if prob >= 0.10:
        return "MEDIUM"
    return "LOW"


def main() -> None:
    logger.info("=== D20: Generate Final Output Files ===")

    # Load cohort
    with open(PATHS.cohort_file, "rb") as f:
        cohort_df = pickle.load(f)
    logger.info("Cohort loaded: %d patients", len(cohort_df))

    # Load hadm_ids from feature store HDF5
    import h5py
    from configs.paths import PATHS as _PATHS
    store = FeatureStore()
    with h5py.File(_PATHS.features_dir / "text_embeddings.h5", "r") as f:
        hadm_ids = f["hadm_ids"][:].tolist()
    logger.info("FeatureStore: %d admissions", len(hadm_ids))

    # Get mortality predictions
    mortality_probs = load_mortality_probs(hadm_ids, store)

    # Stage 6 components
    builder   = PatientSummaryBuilder()
    alert_gen = AlertGenerator()
    detector  = AnomalyDetector()
    exporter  = DashboardDataExporter(output_dir=SUMMARY_DIR)
    reporter  = ReportExporter(output_dir=SUMMARY_DIR)

    all_summaries = []

    for hid in hadm_ids:
        row = cohort_df[cohort_df["hadm_id"] == hid]
        if row.empty:
            continue
        row  = row.iloc[0]
        prob = mortality_probs.get(hid, 0.0)
        risk = classify_risk(prob)

        # Build summary
        summary = builder.build(
            subject_id=int(row["subject_id"]),
            hadm_id=hid,
            demographics={
                "age":    row.get("anchor_age"),
                "gender": row.get("gender"),
            },
            admission_info={
                "los_days": row.get("los_days"),
            },
            note_text="",
            lab_anomalies=[],
            vital_anomalies=[],
            vital_trends={},
            mortality_result={"probability": round(prob, 4), "risk_level": risk},
        )

        # Generate alerts
        alerts = alert_gen.generate_all_alerts([], [], prob)
        summary["alerts"] = alert_gen.to_dict_list(alerts)

        all_summaries.append(summary)

        # Export individual patient JSON
        exporter.export_patient_summary(summary)
        logger.info("  Exported patient %s_%s  prob=%.3f  risk=%s  alerts=%d",
                    row["subject_id"], hid, prob, risk, len(alerts))

    # Export cohort overview
    overview_path = exporter.export_cohort_overview(all_summaries)
    logger.info("Cohort overview saved: %s", overview_path)

    # Export batch reports
    reporter.export_batch_json(all_summaries)

    # Print summary
    n_high   = sum(1 for s in all_summaries if s["predicted_mortality"]["risk_level"] == "HIGH")
    n_medium = sum(1 for s in all_summaries if s["predicted_mortality"]["risk_level"] == "MEDIUM")
    n_low    = sum(1 for s in all_summaries if s["predicted_mortality"]["risk_level"] == "LOW")
    mean_prob = sum(s["predicted_mortality"]["probability"] for s in all_summaries) / max(len(all_summaries), 1)

    print("\n" + "="*50)
    print("  D20 — Output Generation Complete")
    print("="*50)
    print(f"  Patients processed : {len(all_summaries)}")
    print(f"  HIGH risk          : {n_high}")
    print(f"  MEDIUM risk        : {n_medium}")
    print(f"  LOW risk           : {n_low}")
    print(f"  Mean mortality prob: {mean_prob:.3f}")
    print(f"  Files saved to     : {SUMMARY_DIR}")
    print("="*50)


if __name__ == "__main__":
    main()
