"""
ClinNote — Temporary Test UI

Simple Flask app for testing the backend API visually.
DELETE THIS ENTIRE test_ui/ FOLDER after Meltaha integrates the real frontend.

Run:
  cd ClinNote
  python test_ui/app.py

Then open: http://localhost:5001
The API must be running separately on port 5000:
  uvicorn api.app:app --port 5000
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__, template_folder="templates", static_folder="static")

API_BASE = "http://localhost:5000"


@app.route("/")
def index():
    """Homepage — search patients, 3 case entry cards."""
    try:
        resp = requests.get(f"{API_BASE}/api/patients", timeout=30)
        patients = resp.json().get("patients", []) if resp.ok else []
    except Exception:
        patients = []
    return render_template("index.html", patients=patients, api_base=API_BASE)


@app.route("/patient/<int:hadm_id>")
def view_patient(hadm_id):
    """Case 1 & 2 — View existing patient dashboard."""
    try:
        resp = requests.get(f"{API_BASE}/api/patient/{hadm_id}", timeout=180)
        if resp.status_code == 404:
            return render_template("error.html", msg=f"Patient with hadm_id={hadm_id} not found"), 404
        data = resp.json()
    except Exception as e:
        return render_template("error.html", msg=str(e)), 500
    return render_template("dashboard.html", patient=data, hadm_id=hadm_id)


@app.route("/patient/<int:hadm_id>/update", methods=["POST"])
def update_patient(hadm_id):
    """Case 2 — Submit new data for existing patient."""
    files = {}
    data = {
        "note_text": request.form.get("note_text", ""),
        "vitals": request.form.get("vitals_json", "[]"),
    }
    if "labs_pdf" in request.files and request.files["labs_pdf"].filename:
        f = request.files["labs_pdf"]
        files["labs_pdf"] = (f.filename, f.read(), f.content_type)

    try:
        resp = requests.post(
            f"{API_BASE}/api/patient/{hadm_id}/update",
            data=data,
            files=files if files else None,
            timeout=120,
        )
        if not resp.ok:
            error_detail = resp.json().get("detail", resp.text) if resp.content else resp.text
            return render_template("error.html", msg=f"API error {resp.status_code}: {error_detail}"), 500
        result = resp.json()
    except Exception as e:
        return render_template("error.html", msg=str(e)), 500

    return render_template("dashboard.html", patient=result, hadm_id=hadm_id,
                           updated=True, diff=result.get("update_diff"))


@app.route("/patient/new", methods=["GET", "POST"])
def new_patient():
    """Case 3 — New patient form and submission."""
    if request.method == "GET":
        return render_template("new_patient.html")

    files = {}
    data = {
        "age": request.form.get("age", "0"),
        "gender": request.form.get("gender", "M"),
        "note_text": request.form.get("note_text", ""),
        "vitals": request.form.get("vitals_json", "[]"),
    }
    if "labs_pdf" in request.files and request.files["labs_pdf"].filename:
        f = request.files["labs_pdf"]
        files["labs_pdf"] = (f.filename, f.read(), f.content_type)

    try:
        resp = requests.post(
            f"{API_BASE}/api/patient/new",
            data=data,
            files=files if files else None,
            timeout=120,
        )
        if not resp.ok:
            error_detail = resp.json().get("detail", resp.text) if resp.content else resp.text
            return render_template("error.html", msg=f"API error {resp.status_code}: {error_detail}"), 500
        result = resp.json()
        hadm_id = result.get("hadm_id", 0)
    except Exception as e:
        return render_template("error.html", msg=str(e)), 500

    return render_template("dashboard.html", patient=result,
                           hadm_id=hadm_id, is_new=True)


@app.route("/api/parse-pdf-proxy", methods=["POST"])
def parse_pdf_proxy():
    """Proxy the PDF parse call to the backend API and return JSON."""
    from flask import jsonify
    if "lab_pdf" not in request.files:
        return jsonify({"error": "no file"}), 400
    f = request.files["lab_pdf"]
    try:
        resp = requests.post(
            f"{API_BASE}/api/parse-pdf",
            files={"lab_pdf": (f.filename, f.read(), f.content_type)},
            timeout=30,
        )
        if not resp.ok:
            return jsonify({"error": f"API error {resp.status_code}: {resp.text[:200]}"}), 500
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("  ClinNote Test UI")
    print("  http://localhost:5001")
    print("  (API must be on http://localhost:5000)")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5001, debug=True)
