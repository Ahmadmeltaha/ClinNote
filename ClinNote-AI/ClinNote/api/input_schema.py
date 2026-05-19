from pydantic import BaseModel


class LabInput(BaseModel):
    itemid: int | None = None
    label: str
    valuenum: float
    valueuom: str = ""
    charttime: str
    ref_range_lower: float | None = None
    ref_range_upper: float | None = None


class VitalInput(BaseModel):
    label: str
    valuenum: float
    valueuom: str = ""
    charttime: str
    stay_id: int | None = None


class NoteInput(BaseModel):
    text: str
    charttime: str
    note_type: str = "Discharge summary"


class PatientInput(BaseModel):
    subject_id: int | None = None
    age: int
    gender: str
    admittime: str
    dischtime: str | None = None


class ClinicalSubmission(BaseModel):
    patient: PatientInput
    note: NoteInput | None = None
    labs: list[LabInput] = []
    vitals: list[VitalInput] = []
