# ClinNote — AI-Driven Clinical Data Integration Platform

## Overview

ClinNote is a multimodal AI pipeline that integrates three types of clinical data
from the MIMIC-IV v3.1 dataset to generate structured patient summaries with
abnormality highlighting and mortality risk prediction.

**Three modalities → One unified patient representation:**
- Clinical Notes (unstructured text): 331,794 discharge summaries
- Laboratory Results (structured numeric): ~30M lab events
- Vital Signs (structured numeric): ~330M ICU measurements

**Core innovation:** A MEDFuse-inspired Disentangled Transformer that separates
modality-specific information from cross-modal shared information using a vCLUB
Mutual Information loss, producing a 1024-dimensional unified patient embedding.

---

## Team

| Member | Role |
|--------|------|
| Ahmad Jaber | AI/ML Pipeline — Data loading, feature extraction, fusion model |
| Daliah Qadri | AI/ML Pipeline — Preprocessing, analysis, clinical output generation |
| Ahmad Meltaha | Web Development (separate repository) |

**Supervisor:** Dr. Rami Al Ouran
**Institution:** Al-Hussien bin Abdullah Technical University
**Project:** Capstone 2 — ClinNote

---

## Dataset

| Dataset | Version | Description |
|---------|---------|-------------|
| MIMIC-IV | v3.1 | Clinical database (hosp + icu modules) |
| MIMIC-IV-Note | v2.2 | Clinical notes (discharge summaries, radiology) |

Access requires credentialed PhysioNet account. Data lives at `../mimic-Data/`.

---

## Methodology: 6 Stages

### Stage 1: Data Sources
Loads raw MIMIC-IV tables. Three modalities accessed separately:
- **Text**: `mimic-note/note/discharge.csv.gz` (NotesLoader)
- **Labs**: `mimic-iv-3.1/hosp/labevents.csv.gz` + `d_labitems.csv.gz` (LabsLoader)
- **Vitals**: `mimic-iv-3.1/icu/chartevents.csv.gz` filtered by vital itemids (VitalsLoader)
- **Patient linking**: `patients.csv.gz`, `admissions.csv.gz`, `icustays.csv.gz`

### Stage 2: Preprocessing & Cleaning
- Patient ID matching across all sources (subject_id → hadm_id → stay_id)
- Text cleaning: PHI placeholder replacement, whitespace normalization
- Lab preprocessing: duplicate removal, outlier detection, anomaly flagging
- Vitals preprocessing: unit normalization (°F→°C), hard bounds filtering
- Time alignment: all events mapped to hours-from-admission

### Stage 3: Feature Extraction (Three Parallel Pipelines)
| Pipeline | Model | Input | Output |
|----------|-------|-------|--------|
| A. NLP | ClinicalBERT (`emilyalsentzer/Bio_ClinicalBERT`) | Cleaned notes | 768-dim embedding |
| B. Labs | Statistical | Latest values per lab test | 50-dim feature vector |
| C. Vitals | SciPy statistics | ICU time-series (first 48h) | 32-dim feature vector |

### Stage 4: Multimodal Fusion (MEDFuse-Inspired Disentangled Transformer)
Four-step process:
1. **Feature Projection**: Linear layers map each modality to 256-dim common space
2. **Self-Attention**: Independent multi-head self-attention per modality (S_text, S_lab, S_vitals)
3. **Cross-Attention**: Cross-modal transformer captures shared information (S_common)
4. **Disentanglement**: vCLUB MI Loss minimizes redundancy; concatenate → h_final (1024-dim)

### Stage 5: Analysis & Generation
- In-hospital mortality prediction (binary, AUROC/AUPRC evaluation)
- Clinical summary generation (template-based)
- Anomaly detection (rule-based + statistical)
- Temporal trend analysis (SciPy linear regression)

### Stage 6: Clinical Output
- Structured patient summaries (JSON)
- Clinical alerts (CRITICAL / WARNING / INFO)
- Dashboard data export for web frontend (Ahmad Meltaha)
- Evaluation metrics export

---

## Project Structure

```
ClinNote/
├── configs/              # All hyperparameters and data paths
│   ├── paths.py          # MIMIC-IV data paths (verified against actual files)
│   ├── model_config.py   # Fusion model hyperparameters
│   ├── data_config.py    # Vital itemids, lab itemids, reference ranges
│   └── pipeline_config.py
│
├── src/
│   ├── stage1_data_loading/      # Stage 1: MIMIC-IV data loaders
│   ├── stage2_preprocessing/     # Stage 2: Cleaning & normalization
│   ├── stage3_feature_extraction/# Stage 3: ClinicalBERT, lab/vitals features
│   ├── stage4_fusion/            # Stage 4: Disentangled transformer
│   ├── stage5_analysis/          # Stage 5: Mortality prediction & summaries
│   ├── stage6_output/            # Stage 6: JSON export for web dashboard
│   └── utils/                    # Shared: metrics, logging, visualization
│
├── scripts/              # Runnable pipeline scripts
├── notebooks/            # Jupyter notebooks for exploration
├── tests/                # pytest unit tests
├── outputs/              # Generated files (gitignored)
└── mimic-Data/           # Raw MIMIC data (gitignored, lives outside ClinNote/)
```

---

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate          # Linux/macOS
venv\Scripts\activate             # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

For GPU support (recommended for ClinicalBERT encoding):
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 3. Verify data paths

```bash
python configs/paths.py
```

---

## Running the Pipeline

### Option A: Step by step

```bash
# Stage 1+2: Preprocessing (builds cohort + cleans data)
python scripts/run_preprocessing.py

# Stage 3: Feature extraction (ClinicalBERT + labs + vitals)
python scripts/run_feature_extraction.py

# Stage 4: Train fusion model
python scripts/run_fusion_training.py

# Stage 5+6: Evaluate + generate outputs
python scripts/run_evaluation.py --generate-summaries
```

### Option B: Full pipeline

```bash
python scripts/run_full_pipeline.py
```

### Debug mode (fast, 500 patients)

```bash
python scripts/run_full_pipeline.py --debug
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use synthetic data — no real MIMIC data required.

---

## Key Configuration

Edit `configs/` files to change behaviour:

| File | What to change |
|------|---------------|
| `paths.py` | Data root if MIMIC-IV moves |
| `model_config.py` | Attention heads, dims, learning rate, epochs |
| `data_config.py` | Vital itemids, lab itemids, reference ranges |
| `pipeline_config.py` | Train/val/test splits, batch sizes, which stages to run |

---

## Output Files

All outputs go to `outputs/` (gitignored):

| File | Description |
|------|-------------|
| `outputs/features/text_embeddings.h5` | ClinicalBERT embeddings (n × 768) |
| `outputs/features/lab_features.h5` | Lab feature vectors (n × 50) |
| `outputs/features/vitals_features.h5` | Vitals feature vectors (n × 32) |
| `outputs/models/fusion_model_best.pt` | Best model checkpoint |
| `outputs/summaries/patient_*.json` | Per-patient clinical summaries |
| `outputs/summaries/cohort_overview.json` | Aggregated cohort data |
| `outputs/summaries/evaluation_metrics.json` | AUROC, AUPRC, F1, etc. |

---

## Architecture Reference

```
text (768) ──[Linear→256]──[Self-Attn]──────────────────┐
labs  (50) ──[Linear→256]──[Self-Attn]──[Cross-Attn]───[Concat 1024]──[MortalityHead]
vitals(32) ──[Linear→256]──[Self-Attn]──────────────────┘
                                             ↑
                                         MI Loss (vCLUB)
                                         disentangles specific from shared
```

Fusion output: h_final = [S_text | S_lab | S_vitals | S_common] = 1024-dim
