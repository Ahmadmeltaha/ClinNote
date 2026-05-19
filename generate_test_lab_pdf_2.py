"""
Generate a SECOND test lab-report PDF — contrasting LOW-acuity scenario.

Where the first PDF (test_lab_report.pdf) was septic shock + AKI (lots of
critical abnormalities, expect HIGH mortality), this one is a stable
post-op recovery with mostly normal labs and a couple of mild findings.
Expected AI result: LOW or low-MEDIUM mortality risk.

Output: D:\\Downloads\\test_lab_report_2.pdf
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

OUT = Path(r"D:\Downloads\test_lab_report_2.pdf")

# Stable post-cholecystectomy day 2 — mostly normal panel
# (mild post-op anemia + slight stress hyperglycemia, otherwise unremarkable)
LABS = [
    ("Test", "Value", "Unit", "Reference Range"),  # header row
    ("Hemoglobin",        "11.8",  "g/dL",    "12.0 - 16.0"),  # mild low (post-op)
    ("White Blood Cells", "9.2",   "K/uL",    "4.0 - 11.0"),   # normal
    ("Platelets",         "245",   "K/uL",    "150 - 400"),    # normal
    ("Sodium",            "139",   "mEq/L",   "135 - 145"),    # normal
    ("Potassium",         "4.0",   "mEq/L",   "3.5 - 5.0"),    # normal
    ("Chloride",          "102",   "mEq/L",   "98 - 107"),     # normal
    ("Creatinine",        "0.9",   "mg/dL",   "0.6 - 1.2"),    # normal
    ("Urea Nitrogen",     "14",    "mg/dL",   "7 - 20"),       # normal
    ("Glucose",           "108",   "mg/dL",   "70 - 100"),     # mild high (stress)
    ("Albumin",           "3.8",   "g/dL",    "3.5 - 5.0"),    # normal
    ("Bilirubin",         "0.7",   "mg/dL",   "0.0 - 1.2"),    # normal
    ("Calcium",           "9.4",   "mg/dL",   "8.5 - 10.5"),   # normal
    ("Magnesium",         "2.0",   "mg/dL",   "1.7 - 2.4"),    # normal
    ("Lactate",           "1.4",   "mmol/L",  "0.5 - 2.0"),    # normal
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(OUT), pagesize=letter)
    styles = getSampleStyleSheet()

    table = Table(LABS, colWidths=[160, 60, 70, 110])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
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
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
            ]
        )
    )

    flow = [
        Paragraph("Lab Report — Routine Post-Op", styles["Title"]),
        Spacer(1, 6),
        Paragraph("Patient: Stable Recovery &nbsp; · &nbsp; Collected: 2026-05-08", styles["Normal"]),
        Spacer(1, 18),
        table,
    ]
    doc.build(flow)
    print(f"PDF saved to {OUT}")


if __name__ == "__main__":
    main()
