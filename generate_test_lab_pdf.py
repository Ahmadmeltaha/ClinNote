"""
Generate a test lab-report PDF that Ahmad's `pdf_lab_extractor.py` can parse.

Uses a real table structure (reportlab Table primitive). Ahmad's extractor
calls `page.extract_tables()` first, which is far more reliable than the
plain-text regex fallback (pdfplumber collapses multi-space gaps to single
spaces, breaking `\\s{2,}` patterns).

Output: D:\\Downloads\\test_lab_report.pdf
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

OUT = Path(r"D:\Downloads\test_lab_report.pdf")

# Realistic septic-shock + acute-kidney-injury panel — many values abnormal
# so the AI's lab anomaly detector fires and gives an interesting result.
LABS = [
    ("Test", "Value", "Unit", "Reference Range"),  # header row
    ("Creatinine",        "3.2",   "mg/dL",   "0.6 - 1.2"),
    ("Potassium",         "5.9",   "mEq/L",   "3.5 - 5.0"),
    ("Lactate",           "4.5",   "mmol/L",  "0.5 - 2.0"),
    ("White Blood Cells", "18.5",  "K/uL",    "4.0 - 11.0"),
    ("Hemoglobin",        "8.2",   "g/dL",    "12.0 - 16.0"),
    ("Sodium",            "132",   "mEq/L",   "135 - 145"),
    ("Glucose",           "185",   "mg/dL",   "70 - 100"),
    ("Albumin",           "2.1",   "g/dL",    "3.5 - 5.0"),
    ("Urea Nitrogen",     "48",    "mg/dL",   "7 - 20"),
    ("Platelets",         "95",    "K/uL",    "150 - 400"),
    ("Bilirubin",         "2.8",   "mg/dL",   "0.0 - 1.2"),
    ("Calcium",           "7.6",   "mg/dL",   "8.5 - 10.5"),
    ("Magnesium",         "1.2",   "mg/dL",   "1.7 - 2.4"),
    ("Chloride",          "105",   "mEq/L",   "98 - 107"),
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
        Paragraph("Test Lab Report", styles["Title"]),
        Spacer(1, 6),
        Paragraph("Patient: Test Patient &nbsp; · &nbsp; Collected: 2026-05-10", styles["Normal"]),
        Spacer(1, 18),
        table,
    ]
    doc.build(flow)
    print(f"PDF saved to {OUT}")


if __name__ == "__main__":
    main()
