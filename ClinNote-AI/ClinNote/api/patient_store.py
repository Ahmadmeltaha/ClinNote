from pathlib import Path
import json
import pandas as pd
from configs.paths import PATHS
from api.input_schema import ClinicalSubmission


class PatientStore:
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or (PATHS.output_root / "patient_data")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_subject_id(self, submission: ClinicalSubmission) -> int:
        if submission.patient.subject_id:
            return submission.patient.subject_id
        return abs(hash(submission.patient.admittime)) % 1_000_000

    def get_hadm_id(self, subject_id: int, admittime: str) -> int:
        return abs(hash(str(subject_id) + admittime)) % 10_000_000

    def exists(self, subject_id: int) -> bool:
        return (self.base_dir / str(subject_id) / "patient.json").exists()

    def save(self, subject_id: int, submission: ClinicalSubmission) -> None:
        patient_dir = self.base_dir / str(subject_id)
        patient_dir.mkdir(parents=True, exist_ok=True)
        hadm_id = self.get_hadm_id(subject_id, submission.patient.admittime)

        # Save patient demographics
        patient_data = submission.patient.model_dump()
        patient_data["hadm_id"] = hadm_id
        with open(patient_dir / "patient.json", "w") as f:
            json.dump(patient_data, f, indent=2)

        # Append note
        if submission.note:
            note_row = {"subject_id": subject_id, "hadm_id": hadm_id,
                        "note_id": f"manual_{hadm_id}",
                        "note_type": submission.note.note_type,
                        "note_seq": 1,
                        "charttime": submission.note.charttime,
                        "storetime": submission.note.charttime,
                        "text": submission.note.text}
            note_path = patient_dir / "notes.csv"
            pd.DataFrame([note_row]).to_csv(
                note_path, mode="a", header=not note_path.exists(), index=False)

        # Append labs
        if submission.labs:
            lab_rows = [{"subject_id": subject_id, "hadm_id": hadm_id,
                         "itemid": l.itemid or 0, "label": l.label,
                         "charttime": l.charttime, "storetime": l.charttime,
                         "value": str(l.valuenum), "valuenum": l.valuenum,
                         "valueuom": l.valueuom,
                         "ref_range_lower": l.ref_range_lower,
                         "ref_range_upper": l.ref_range_upper,
                         "flag": None, "priority": "STAT",
                         "fluid": "Blood", "category": "Chemistry"}
                        for l in submission.labs]
            lab_path = patient_dir / "labs.csv"
            pd.DataFrame(lab_rows).to_csv(
                lab_path, mode="a", header=not lab_path.exists(), index=False)

        # Append vitals
        if submission.vitals:
            stay_id = abs(hash(str(subject_id))) % 1_000_000
            vital_rows = [{"subject_id": subject_id, "hadm_id": hadm_id,
                           "stay_id": stay_id, "itemid": 0,
                           "label": v.label, "category": "Vitals",
                           "vital_source": "manual_entry",
                           "charttime": v.charttime, "storetime": v.charttime,
                           "value": str(v.valuenum), "valuenum": v.valuenum,
                           "valueuom": v.valueuom, "warning": 0}
                          for v in submission.vitals]
            vitals_path = patient_dir / "vitals.csv"
            pd.DataFrame(vital_rows).to_csv(
                vitals_path, mode="a",
                header=not vitals_path.exists(), index=False)

    def load(self, subject_id: int) -> dict:
        patient_dir = self.base_dir / str(subject_id)
        with open(patient_dir / "patient.json") as f:
            patient = json.load(f)
        notes_path = patient_dir / "notes.csv"
        labs_path = patient_dir / "labs.csv"
        vitals_path = patient_dir / "vitals.csv"
        return {
            "patient": patient,
            "notes": pd.read_csv(notes_path) if notes_path.exists()
                     else pd.DataFrame(),
            "labs": pd.read_csv(labs_path) if labs_path.exists()
                    else pd.DataFrame(),
            "vitals": pd.read_csv(vitals_path) if vitals_path.exists()
                      else pd.DataFrame(),
        }

    def merge(self, subject_id: int,
              new_submission: ClinicalSubmission) -> dict:
        # Load all existing data
        existing = self.load(subject_id)
        hadm_id = self.get_hadm_id(
            subject_id, new_submission.patient.admittime)

        # Build new DataFrames from submission
        note_rows, lab_rows, vital_rows = [], [], []
        stay_id = abs(hash(str(subject_id))) % 1_000_000

        if new_submission.note:
            note_rows.append({
                "subject_id": subject_id, "hadm_id": hadm_id,
                "note_id": f"manual_{hadm_id}_new",
                "note_type": new_submission.note.note_type,
                "note_seq": 1,
                "charttime": new_submission.note.charttime,
                "storetime": new_submission.note.charttime,
                "text": new_submission.note.text})

        for l in new_submission.labs:
            lab_rows.append({
                "subject_id": subject_id, "hadm_id": hadm_id,
                "itemid": l.itemid or 0, "label": l.label,
                "charttime": l.charttime, "storetime": l.charttime,
                "value": str(l.valuenum), "valuenum": l.valuenum,
                "valueuom": l.valueuom,
                "ref_range_lower": l.ref_range_lower,
                "ref_range_upper": l.ref_range_upper,
                "flag": None, "priority": "STAT",
                "fluid": "Blood", "category": "Chemistry"})

        for v in new_submission.vitals:
            vital_rows.append({
                "subject_id": subject_id, "hadm_id": hadm_id,
                "stay_id": stay_id, "itemid": 0,
                "label": v.label, "category": "Vitals",
                "vital_source": "manual_entry",
                "charttime": v.charttime, "storetime": v.charttime,
                "value": str(v.valuenum), "valuenum": v.valuenum,
                "valueuom": v.valueuom, "warning": 0})

        # Concatenate old + new, deduplicate
        new_notes_df = pd.DataFrame(note_rows)
        new_labs_df = pd.DataFrame(lab_rows)
        new_vitals_df = pd.DataFrame(vital_rows)

        merged_notes = pd.concat(
            [existing["notes"], new_notes_df], ignore_index=True
        ).drop_duplicates(subset=["charttime", "text"]) \
         if not new_notes_df.empty else existing["notes"]

        merged_labs = pd.concat(
            [existing["labs"], new_labs_df], ignore_index=True
        ).drop_duplicates(subset=["charttime", "label"]) \
         if not new_labs_df.empty else existing["labs"]

        merged_vitals = pd.concat(
            [existing["vitals"], new_vitals_df], ignore_index=True
        ).drop_duplicates(subset=["charttime", "label"]) \
         if not new_vitals_df.empty else existing["vitals"]

        return {
            "patient": existing["patient"],
            "notes": merged_notes,
            "labs": merged_labs,
            "vitals": merged_vitals,
        }
