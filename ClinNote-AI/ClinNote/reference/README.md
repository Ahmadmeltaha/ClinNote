# Reference Materials

## Inspiration: MEDFuse / Multimodal Transformer

ClinNote's fusion architecture is inspired by:

> Lyu, T. et al. (2023). "A Multimodal Transformer: Fusing Clinical Notes
> With Structured EHR Data for Interpretable In-Hospital Mortality Prediction."
> IEEE Journal of Biomedical and Health Informatics.

A reference implementation for MIMIC-III is available in the `MultiModel/`
folder in the parent repository. Key files to study:

- `Models.py`      — BioClinicalBERT + time-series encoder + fusion
- `utils.py`       — Data readers, metrics calculation
- `text_utils.py`  — Clinical text preprocessing patterns

## Key Differences: ClinNote vs Reference

| Aspect | Reference (MIMIC-III) | ClinNote (MIMIC-IV v3.1) |
|--------|----------------------|---------------------------|
| Dataset | MIMIC-III | MIMIC-IV v3.1 + MIMIC-IV-Note v2.2 |
| Modalities | Text + Vitals (2) | Text + Labs + Vitals (3) |
| Fusion | Simple concatenation | Disentangled transformer + MI loss |
| Task | Mortality prediction | Mortality + Summary generation + Alerts |
| Schema | MIMIC-III (older) | MIMIC-IV (different column names) |

## MIMIC-IV Schema Changes from MIMIC-III

- `CHARTEVENTS` now includes `stay_id` (replaces ICUSTAY_ID)
- `ADMISSIONS` now has `hospital_expire_flag` (was `HOSPITAL_EXPIRE_FLAG`)
- Notes are in a **separate dataset** (MIMIC-IV-Note), not embedded in MIMIC-IV
- `LABEVENTS` now includes `ref_range_lower` / `ref_range_upper` columns
- Patient ages are de-identified differently (anchor_age system)

## vCLUB MI Loss Reference

> Chen, T. et al. (2020). "CLUB: A Contrastive Log-ratio Upper Bound of
> Mutual Information." ICML 2020. arXiv:2006.12013
