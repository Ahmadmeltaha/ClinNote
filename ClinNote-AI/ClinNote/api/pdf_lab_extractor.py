"""
ClinNote — PDF Lab Report Extractor

Extracts lab test results from a PDF file uploaded by a doctor.
Uses pdfplumber to read text, then regex to find lab name/value/unit/reference range.

Returns a list of dicts ready to be used as LabInput objects or shown in an editable table.
Falls back to [] if nothing is found — caller shows a manual entry form.
"""

import re
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Common lab name aliases → normalize to our pipeline's label names
LAB_NAME_ALIASES = {
    "hgb": "Hemoglobin",
    "hemoglobin": "Hemoglobin",
    "wbc": "White Blood Cells",
    "white blood cell": "White Blood Cells",
    "white blood cells": "White Blood Cells",
    "plt": "Platelets",
    "platelet": "Platelets",
    "platelets": "Platelets",
    "creatinine": "Creatinine",
    "creat": "Creatinine",
    "glucose": "Glucose",
    "gluc": "Glucose",
    "sodium": "Sodium",
    "na": "Sodium",
    "potassium": "Potassium",
    "k": "Potassium",
    "chloride": "Chloride",
    "cl": "Chloride",
    "bicarbonate": "Bicarbonate",
    "hco3": "Bicarbonate",
    "bun": "Urea Nitrogen",
    "urea nitrogen": "Urea Nitrogen",
    "blood urea nitrogen": "Urea Nitrogen",
    "calcium": "Calcium",
    "ca": "Calcium",
    "magnesium": "Magnesium",
    "mg": "Magnesium",
    "phosphate": "Phosphate",
    "phos": "Phosphate",
    "albumin": "Albumin",
    "alb": "Albumin",
    "bilirubin": "Bilirubin",
    "total bilirubin": "Bilirubin",
    "alt": "Alanine Aminotransferase (ALT)",
    "alanine aminotransferase": "Alanine Aminotransferase (ALT)",
    "ast": "Aspartate Aminotransferase (AST)",
    "aspartate aminotransferase": "Aspartate Aminotransferase (AST)",
    "inr": "INR",
    "pt": "Prothrombin Time",
    "prothrombin time": "Prothrombin Time",
    "ptt": "Partial Thromboplastin Time",
    "partial thromboplastin time": "Partial Thromboplastin Time",
    "lactate": "Lactate",
    "lactic acid": "Lactate",
    "troponin": "Troponin T",
    "troponin t": "Troponin T",
    "troponin i": "Troponin T",
    "ph": "pH",
    "pco2": "pCO2",
    "po2": "pO2",
    "hba1c": "Hemoglobin A1c",
    "hemoglobin a1c": "Hemoglobin A1c",
    "ldl": "LDL Cholesterol",
    "hdl": "HDL Cholesterol",
    "cholesterol": "Total Cholesterol",
    "triglycerides": "Triglycerides",
    "tsh": "Thyroid Stimulating Hormone",
    "thyroid stimulating hormone": "Thyroid Stimulating Hormone",
    "ferritin": "Ferritin",
    "iron": "Iron",
    "transferrin": "Transferrin",
    "esr": "Erythrocyte Sedimentation Rate",
    "crp": "C-Reactive Protein",
    "c-reactive protein": "C-Reactive Protein",
    "procalcitonin": "Procalcitonin",
    "d-dimer": "D-Dimer",
    "fibrinogen": "Fibrinogen",
}

# Regex patterns to match common lab report line formats:
# Format 1: "Creatinine    3.2    mg/dL    [0.6 - 1.2]"
# Format 2: "Glucose: 180 mg/dL (70-100)"
# Format 3: "WBC  7.5  K/uL  Ref: 4.0-11.0"
_PATTERNS = [
    # Pattern 1: name  value  unit  [low - high]
    re.compile(
        r"(?P<name>[A-Za-z][A-Za-z0-9 \-/()]+?)\s{2,}"
        r"(?P<value>\d+\.?\d*)\s+"
        r"(?P<unit>[A-Za-z/%µ][A-Za-z0-9/%µ\.]*)\s+"
        r"[\[\(]?\s*(?P<low>\d+\.?\d*)\s*[-–]\s*(?P<high>\d+\.?\d*)\s*[\]\)]?",
        re.IGNORECASE,
    ),
    # Pattern 2: name: value unit (low-high)
    re.compile(
        r"(?P<name>[A-Za-z][A-Za-z0-9 \-/()]+?):\s*"
        r"(?P<value>\d+\.?\d*)\s+"
        r"(?P<unit>[A-Za-z/%µ][A-Za-z0-9/%µ\.]*)\s*"
        r"[\(\[]?\s*(?P<low>\d+\.?\d*)\s*[-–]\s*(?P<high>\d+\.?\d*)\s*[\)\]]?",
        re.IGNORECASE,
    ),
    # Pattern 3: name  value  unit  Ref: low-high
    re.compile(
        r"(?P<name>[A-Za-z][A-Za-z0-9 \-/()]+?)\s{2,}"
        r"(?P<value>\d+\.?\d*)\s+"
        r"(?P<unit>[A-Za-z/%µ][A-Za-z0-9/%µ\.]*)\s+"
        r"(?:Ref|Reference|Normal|Range)?:?\s*"
        r"(?P<low>\d+\.?\d*)\s*[-–]\s*(?P<high>\d+\.?\d*)",
        re.IGNORECASE,
    ),
    # Pattern 4: name  value  unit  (no reference range)
    re.compile(
        r"(?P<name>[A-Za-z][A-Za-z0-9 \-/()]+?)\s{2,}"
        r"(?P<value>\d+\.?\d*)\s+"
        r"(?P<unit>[A-Za-z/%µ][A-Za-z0-9/%µ\.]{1,10})\b",
        re.IGNORECASE,
    ),
]


def _normalize_name(raw: str) -> Optional[str]:
    """Map raw lab name to our canonical label. Returns None if unrecognized."""
    key = raw.strip().lower()
    return LAB_NAME_ALIASES.get(key) or LAB_NAME_ALIASES.get(key.split("(")[0].strip())


def extract_labs_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Extract lab results from PDF bytes.
    Tries table extraction first (handles structured lab report PDFs),
    then falls back to regex on plain text.

    Returns list of {name, value, unit, ref_low, ref_high}
    """
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber not installed — PDF parsing unavailable")
        return []

    try:
        results = []
        seen_names = set()

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            all_text_lines = []

            for page in pdf.pages:
                # --- Method 1: structured table extraction ---
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row:
                            continue
                        # Clean cells
                        cells = [str(c).strip() if c else "" for c in row]
                        # Need at least: name, value
                        if len(cells) < 2:
                            continue
                        # Skip header rows
                        first = cells[0].lower()
                        if any(h in first for h in ["test", "analyte", "component", "name", "parameter"]):
                            continue

                        raw_name = cells[0].strip()
                        if not raw_name or len(raw_name) < 2:
                            continue

                        # Find the numeric value (scan all cells)
                        value = None
                        value_idx = -1
                        for i, cell in enumerate(cells[1:], 1):
                            try:
                                v = float(cell.replace(",", "").replace(">", "").replace("<", ""))
                                value = v
                                value_idx = i
                                break
                            except (ValueError, AttributeError):
                                continue

                        if value is None:
                            continue

                        # Unit: next cell after value
                        unit = cells[value_idx + 1].strip() if value_idx + 1 < len(cells) else ""
                        # Clean common unit noise
                        unit = re.sub(r"[HLhl\*]+$", "", unit).strip()

                        # Reference range: look for "low - high" pattern in remaining cells
                        ref_low = ref_high = None
                        remaining = " ".join(cells[value_idx + 1:])
                        ref_match = re.search(
                            r"(?:>=?\s*)?(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)", remaining
                        )
                        if ref_match:
                            ref_low = float(ref_match.group(1))
                            ref_high = float(ref_match.group(2))
                        else:
                            # Handle ">= 60" style single-bound ranges
                            ge_match = re.search(r">=?\s*(\d+\.?\d*)", remaining)
                            if ge_match:
                                ref_low = float(ge_match.group(1))
                                ref_high = 9999.0
                            lt_match = re.search(r"<\s*(\d+\.?\d*)", remaining)
                            if lt_match:
                                ref_low = 0.0
                                ref_high = float(lt_match.group(1))

                        normalized = _normalize_name(raw_name)
                        label = normalized or raw_name.title()
                        label_key = label.lower()
                        if label_key in seen_names:
                            continue
                        seen_names.add(label_key)

                        results.append({
                            "name": label,
                            "value": value,
                            "unit": unit,
                            "ref_low": ref_low,
                            "ref_high": ref_high,
                        })

                # Collect plain text for fallback
                page_text = page.extract_text()
                if page_text:
                    all_text_lines.extend(page_text.splitlines())

        # --- Method 2: regex fallback on plain text ---
        if not results:
            full_text = "\n".join(all_text_lines)
            for pattern in _PATTERNS:
                for match in pattern.finditer(full_text):
                    raw_name = match.group("name").strip()
                    normalized = _normalize_name(raw_name)
                    label = normalized or raw_name.title()
                    label_key = label.lower()
                    if label_key in seen_names:
                        continue
                    seen_names.add(label_key)
                    try:
                        value = float(match.group("value"))
                    except (ValueError, IndexError):
                        continue
                    unit = match.group("unit").strip() if "unit" in pattern.groupindex else ""
                    ref_low = ref_high = None
                    try:
                        ref_low = float(match.group("low"))
                        ref_high = float(match.group("high"))
                    except (IndexError, ValueError, AttributeError):
                        pass
                    results.append({
                        "name": label,
                        "value": value,
                        "unit": unit,
                        "ref_low": ref_low,
                        "ref_high": ref_high,
                    })

        logger.info("PDF extraction: found %d lab values", len(results))
        return results

    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        return []


def extract_labs_from_text(text: str) -> list[dict]:
    """Same as extract_labs_from_pdf but accepts plain text (for testing)."""
    results = []
    seen_names = set()
    for pattern in _PATTERNS:
        for match in pattern.finditer(text):
            raw_name = match.group("name").strip()
            normalized = _normalize_name(raw_name)
            label = normalized or raw_name.title()
            label_key = label.lower()
            if label_key in seen_names:
                continue
            seen_names.add(label_key)
            try:
                value = float(match.group("value"))
            except (ValueError, IndexError):
                continue
            unit = match.group("unit").strip() if "unit" in pattern.groupindex else ""
            ref_low = ref_high = None
            try:
                ref_low = float(match.group("low"))
                ref_high = float(match.group("high"))
            except (IndexError, ValueError, AttributeError):
                pass
            results.append({
                "name": label,
                "value": value,
                "unit": unit,
                "ref_low": ref_low,
                "ref_high": ref_high,
            })
    return results
