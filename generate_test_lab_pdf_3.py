"""
Generate a THIRD test lab-report PDF — severe multi-organ failure scenario.

Designed to max out the AI pipeline's flags: every value is critically
abnormal so the lab anomaly detector lights up across multiple systems
(renal, hepatic, hematologic, metabolic, electrolyte).

Output: D:\\Downloads\\test_lab_report_severe.pdf

Pair this with the severe septic shock clinical note + critically abnormal
vitals (HR 138, SBP 78/42, SpO2 86, RR 32, Temp 39.7°C) for a demo where
the AI returns HIGH risk with rich findings across every system.
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(r"D:\Downloads\test_lab_report_severe.pdf")

# Severe septic shock + multi-organ failure panel.
# All 14 labs are critically abnormal. Names match Ahmad's LAB_NAME_ALIASES.
LABS = [
    ("Test", "Value", "Unit", "Reference Range"),
    ("Creatinine",        "4.5",   "mg/dL",   "0.6 - 1.2"),    # ↑↑ severe AKI
    ("Urea Nitrogen",     "78",    "mg/dL",   "7 - 20"),       # ↑↑ azotemia
    ("Lactate",           "6.8",   "mmol/L",  "0.5 - 2.0"),    # ↑↑ severe lactic acidosis
    ("White Blood Cells", "24.5",  "K/uL",    "4.0 - 11.0"),   # ↑↑ severe leukocytosis
    ("Hemoglobin",        "7.8",   "g/dL",    "12.0 - 16.0"),  # ↓↓ severe anemia
    ("Platelets",         "68",    "K/uL",    "150 - 400"),    # ↓↓ thrombocytopenia
    ("Sodium",            "128",   "mEq/L",   "135 - 145"),    # ↓ hyponatremia
    ("Potassium",         "6.2",   "mEq/L",   "3.5 - 5.0"),    # ↑↑ hyperkalemia
    ("Chloride",          "94",    "mEq/L",   "98 - 107"),     # ↓ hypochloremia
    ("Bicarbonate",       "14",    "mEq/L",   "22 - 28"),      # ↓↓ severe acidosis
    ("Glucose",           "285",   "mg/dL",   "70 - 100"),     # ↑↑ stress hyperglycemia
    ("Bilirubin",         "4.2",   "mg/dL",   "0.0 - 1.2"),    # ↑↑ hepatic injury
    ("Albumin",           "1.8",   "g/dL",    "3.5 - 5.0"),    # ↓↓ severe hypoalbuminemia
    ("Calcium",           "6.8",   "mg/dL",   "8.5 - 10.5"),   # ↓↓ severe hypocalcemia
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(OUT), pagesize=letter)
    styles = getSampleStyleSheet()

    table = Table(LABS, colWidths=[160, 60, 70, 110])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7f1d1d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#fef2f2")],
                ),
            ]
        )
    )

    flow = [
        Paragraph("Lab Report — Critical / Multi-Organ Failure", styles["Title"]),
        Spacer(1, 6),
        Paragraph(
            "Patient: Severe Sepsis &nbsp; · &nbsp; Collected: 2026-05-12 &nbsp; · &nbsp; STAT",
            styles["Normal"],
        ),
        Spacer(1, 18),
        table,
    ]
    doc.build(flow)
    print(f"PDF saved to {OUT}")


if __name__ == "__main__":
    main()
