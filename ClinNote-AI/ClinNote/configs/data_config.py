"""
ClinNote — Data Configuration (Stage 1 & Stage 2)

Defines all domain-specific data constants:
  - Vital sign itemids (MIMIC-IV chartevents)
  - Key laboratory itemids (MIMIC-IV labevents)
  - Laboratory reference ranges for anomaly detection
  - Column name mappings for each MIMIC-IV table

These constants are used by loaders (Stage 1) and preprocessors (Stage 2).
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Vital Sign Item IDs  (MIMIC-IV ICU chartevents → d_items)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VitalSignItemIDs:
    """MIMIC-IV itemids for the 7 core vital signs tracked by ClinNote."""

    heart_rate: int = 220045           # Heart Rate (bpm)
    systolic_bp: int = 220050          # Arterial Blood Pressure Systolic (mmHg)
    diastolic_bp: int = 220051         # Arterial Blood Pressure Diastolic (mmHg)
    mean_bp: int = 220052              # Arterial Blood Pressure Mean (mmHg)
    respiratory_rate: int = 220210     # Respiratory Rate (insp/min)
    spo2: int = 220277                 # O2 Saturation Pulseoxymetry (%)
    temperature_f: int = 223761        # Temperature Fahrenheit (°F)
    temperature_c: int = 223762        # Temperature Celsius (°C)

    def as_list(self) -> list[int]:
        """Return all itemids as a flat list for DataFrame filtering."""
        return [
            self.heart_rate, self.systolic_bp, self.diastolic_bp,
            self.mean_bp, self.respiratory_rate, self.spo2,
            self.temperature_f, self.temperature_c,
        ]

    def label_map(self) -> dict[int, str]:
        """Map itemid → human-readable label."""
        return {
            self.heart_rate: "heart_rate",
            self.systolic_bp: "systolic_bp",
            self.diastolic_bp: "diastolic_bp",
            self.mean_bp: "mean_bp",
            self.respiratory_rate: "respiratory_rate",
            self.spo2: "spo2",
            self.temperature_f: "temperature_f",
            self.temperature_c: "temperature_c",
        }

    def normal_ranges(self) -> dict[str, tuple[float, float]]:
        """
        Clinical normal ranges for each vital sign.
        Format: label -> (lower_bound, upper_bound).
        Values outside these ranges are flagged as abnormal.
        """
        return {
            "heart_rate": (60.0, 100.0),
            "systolic_bp": (90.0, 140.0),
            "diastolic_bp": (60.0, 90.0),
            "mean_bp": (70.0, 100.0),
            "respiratory_rate": (12.0, 20.0),
            "spo2": (95.0, 100.0),
            "temperature_f": (97.0, 99.5),
            "temperature_c": (36.1, 37.5),
        }


# ---------------------------------------------------------------------------
# Laboratory Item IDs  (MIMIC-IV hosp labevents → d_labitems)
# ---------------------------------------------------------------------------
# itemids are from MIMIC-IV v3.1 d_labitems. Verify against the actual file
# when implementing labs_loader.py — some itemids may map to multiple entries.

@dataclass(frozen=True)
class LabItemIDs:
    """Key laboratory test itemids tracked by the lab pipeline."""

    # Metabolic / Basic
    glucose: int = 50931               # Glucose (mg/dL)
    creatinine: int = 50912            # Creatinine (mg/dL)
    bun: int = 51006                   # Urea Nitrogen / BUN (mg/dL)
    sodium: int = 50983                # Sodium (mEq/L)
    potassium: int = 50971             # Potassium (mEq/L)
    chloride: int = 50902              # Chloride (mEq/L)
    bicarbonate: int = 50882           # Bicarbonate (mEq/L)
    calcium_total: int = 50893         # Calcium, Total (mg/dL)

    # Hematology
    hemoglobin: int = 51222            # Hemoglobin (g/dL)
    wbc: int = 51301                   # White Blood Cells (K/uL)
    platelets: int = 51265             # Platelet Count (K/uL)
    hematocrit: int = 51221            # Hematocrit (%)

    # Coagulation
    inr: int = 51237                   # INR (ratio)
    pt: int = 51274                    # Prothrombin Time (sec)
    ptt: int = 51275                   # Partial Thromboplastin Time (sec)

    # Liver / Biliary
    alt: int = 50861                   # Alanine Aminotransferase ALT (IU/L)
    ast: int = 50878                   # Aspartate Aminotransferase AST (IU/L)
    bilirubin_total: int = 50885       # Bilirubin, Total (mg/dL)
    albumin: int = 50862               # Albumin (g/dL)
    alkaline_phosphatase: int = 50863  # Alkaline Phosphatase (IU/L)

    # Cardiac
    troponin_t: int = 51003            # Troponin T (ng/mL)
    troponin_i: int = 51002            # Troponin I (ng/mL)
    ck_mb: int = 50911                 # CK-MB (ng/mL)
    bnp: int = 51214                   # B-Natriuretic Peptide BNP (pg/mL)

    # Inflammatory / Infection
    lactate: int = 50813               # Lactate (mmol/L)
    crp: int = 50889                   # C-Reactive Protein (mg/L)

    # Arterial Blood Gas
    ph: int = 50820                    # pH
    pco2: int = 50818                  # pCO2 (mmHg)
    po2: int = 50821                   # pO2 (mmHg)
    base_excess: int = 50802           # Base Excess (mEq/L)

    def as_list(self) -> list[int]:
        """Return all lab itemids as a flat list for DataFrame filtering."""
        return [
            self.glucose, self.creatinine, self.bun, self.sodium,
            self.potassium, self.chloride, self.bicarbonate, self.calcium_total,
            self.hemoglobin, self.wbc, self.platelets, self.hematocrit,
            self.inr, self.pt, self.ptt,
            self.alt, self.ast, self.bilirubin_total, self.albumin,
            self.alkaline_phosphatase,
            self.troponin_t, self.troponin_i, self.ck_mb, self.bnp,
            self.lactate, self.crp,
            self.ph, self.pco2, self.po2, self.base_excess,
        ]

    def label_map(self) -> dict[int, str]:
        """Map itemid → snake_case label used in feature vectors."""
        return {v: k for k, v in self.__dict__.items()}

    def reference_ranges(self) -> dict[str, tuple[float, float]]:
        """
        Clinical reference ranges for each lab test.
        Format: label -> (lower_bound, upper_bound).
        Source: standard adult clinical reference ranges.
        Override per-patient using d_labitems ref_range_lower / ref_range_upper.
        """
        return {
            "glucose": (70.0, 100.0),
            "creatinine": (0.6, 1.2),
            "bun": (7.0, 20.0),
            "sodium": (136.0, 145.0),
            "potassium": (3.5, 5.1),
            "chloride": (98.0, 107.0),
            "bicarbonate": (22.0, 29.0),
            "calcium_total": (8.5, 10.2),
            "hemoglobin": (12.0, 17.5),
            "wbc": (4.5, 11.0),
            "platelets": (150.0, 400.0),
            "hematocrit": (36.0, 52.0),
            "inr": (0.8, 1.1),
            "pt": (11.0, 13.5),
            "ptt": (25.0, 35.0),
            "alt": (7.0, 56.0),
            "ast": (10.0, 40.0),
            "bilirubin_total": (0.1, 1.2),
            "albumin": (3.4, 5.4),
            "alkaline_phosphatase": (44.0, 147.0),
            "troponin_t": (0.0, 0.01),
            "troponin_i": (0.0, 0.04),
            "ck_mb": (0.0, 3.0),
            "bnp": (0.0, 100.0),
            "lactate": (0.5, 2.2),
            "crp": (0.0, 3.0),
            "ph": (7.35, 7.45),
            "pco2": (35.0, 45.0),
            "po2": (75.0, 100.0),
            "base_excess": (-2.0, 2.0),
        }


# ---------------------------------------------------------------------------
# Column name mappings for MIMIC-IV tables
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ColumnNames:
    """Canonical column names for each MIMIC-IV table used in ClinNote."""

    # discharge.csv.gz  (mimic-note)
    discharge_cols: tuple[str, ...] = (
        "note_id", "subject_id", "hadm_id", "note_type",
        "note_seq", "charttime", "storetime", "text",
    )

    # labevents.csv.gz  (hosp)
    labevents_cols: tuple[str, ...] = (
        "labevent_id", "subject_id", "hadm_id", "specimen_id",
        "itemid", "charttime", "storetime", "value", "valuenum",
        "valueuom", "ref_range_lower", "ref_range_upper",
        "flag", "priority", "comments",
    )

    # d_labitems.csv.gz  (hosp)
    d_labitems_cols: tuple[str, ...] = (
        "itemid", "label", "fluid", "category", "loinc_code",
    )

    # chartevents.csv.gz  (icu)
    chartevents_cols: tuple[str, ...] = (
        "subject_id", "hadm_id", "stay_id", "caregiver_id",
        "charttime", "storetime", "itemid", "value", "valuenum",
        "valueuom", "warning",
    )

    # d_items.csv.gz  (icu)
    d_items_cols: tuple[str, ...] = (
        "itemid", "label", "abbreviation", "linksto",
        "category", "unitname", "param_type", "lownormalvalue", "highnormalvalue",
    )

    # patients.csv.gz  (hosp)
    patients_cols: tuple[str, ...] = (
        "subject_id", "gender", "anchor_age", "anchor_year",
        "anchor_year_group", "dod",
    )

    # admissions.csv.gz  (hosp)
    admissions_cols: tuple[str, ...] = (
        "subject_id", "hadm_id", "admittime", "dischtime",
        "deathtime", "admission_type", "admit_provider_id",
        "admission_location", "discharge_location",
        "insurance", "language", "marital_status", "race",
        "edregtime", "edouttime", "hospital_expire_flag",
    )

    # icustays.csv.gz  (icu)
    icustays_cols: tuple[str, ...] = (
        "subject_id", "hadm_id", "stay_id",
        "first_careunit", "last_careunit",
        "intime", "outtime", "los",
    )


# ---------------------------------------------------------------------------
# Singleton instances
# ---------------------------------------------------------------------------

VITAL_ITEMIDS = VitalSignItemIDs()
LAB_ITEMIDS = LabItemIDs()
COLUMNS = ColumnNames()


@dataclass(frozen=True)
class DataConfig:
    """Top-level data config bundling all sub-configs."""
    vital_itemids: VitalSignItemIDs = field(default_factory=VitalSignItemIDs)
    lab_itemids: LabItemIDs = field(default_factory=LabItemIDs)
    columns: ColumnNames = field(default_factory=ColumnNames)

    # Minimum requirements for a patient to be included in the cohort
    min_lab_events_per_admission: int = 5
    min_vital_hours_per_icu_stay: float = 12.0   # hours
    require_discharge_note: bool = True

    # Time window: only use data from first N hours of ICU stay
    icu_hours_window: int = 48

    # Text preprocessing
    phi_placeholder: str = "___"       # MIMIC de-identification token
    max_note_length_chars: int = 10_000


DATA_CFG = DataConfig()


# ---------------------------------------------------------------------------
# Column name mappings for the pre-extracted labs_final.csv
# (labs_final.csv has duplicate charttime/storetime columns suffixed with _x)
# ---------------------------------------------------------------------------

LABS_CHARTTIME_COL: str = "charttime_x"
LABS_STORETIME_COL: str = "storetime_x"


if __name__ == "__main__":
    print("Vital sign itemids:", VITAL_ITEMIDS.as_list())
    print("Lab itemids:", LAB_ITEMIDS.as_list()[:5], "...")
    print("Min lab events per admission:", DATA_CFG.min_lab_events_per_admission)
