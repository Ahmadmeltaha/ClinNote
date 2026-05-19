"""Smoke-test Ahmad's PDF lab extractor against our generated test PDF."""
import sys
sys.path.insert(0, r"D:\CliNote\ClinNote-AI\ClinNote")

from api.pdf_lab_extractor import extract_labs_from_pdf

with open(r"D:\Downloads\test_lab_report_severe.pdf", "rb") as f:
    labs = extract_labs_from_pdf(f.read())

print(f"Extracted {len(labs)} labs:\n")
for l in labs:
    name = l["name"]
    value = l["value"]
    unit = l.get("unit") or ""
    lo = l.get("ref_low")
    hi = l.get("ref_high")
    print(f"  {name:<35} {value:>6}  {unit:<10}  [{lo} - {hi}]")
