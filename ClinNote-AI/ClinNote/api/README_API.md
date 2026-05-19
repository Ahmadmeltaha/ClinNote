# ClinNote API — Integration Guide for Frontend Developer

## Overview

The ClinNote backend is a fully working AI pipeline that:
- Predicts in-hospital mortality risk from clinical notes, lab results, and vital signs
- Detects abnormal lab values and vital sign alerts
- Generates an AI clinical summary for the attending physician

**Your job as frontend developer:** call the API endpoints below and display the results.
**You do not touch any Python or AI code.**

---

## Setup (run this once)

### Requirements
- Python 3.10+ with Anaconda (already configured on the AI team's machine)
- The `ClinNote` folder (provided by AI team)
- The `.env` file (provided separately — contains the HF token)

### Steps

1. Place the `.env` file inside the `api/` folder:
   ```
   ClinNote/api/.env
   ```
   Contents of `.env`:
   ```
   HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
   ```

2. Open a terminal, go to the `ClinNote` folder:
   ```
   cd "path/to/ClinNote"
   ```

3. Start the API server:
   ```
   uvicorn api.app:app --reload --port 5000
   ```

4. The server is ready when you see:
   ```
   INFO | LLM loaded successfully
   INFO:     Application startup complete.
   ```
   First startup takes ~60 seconds because the AI model loads into GPU memory.

5. API is now live at: **`http://localhost:5000`**

---

## Base URL

```
http://localhost:5000
```

All responses are JSON. All errors return:
```json
{ "detail": "error message here" }
```

CORS is fully enabled — you can call from any frontend port (3000, 5173, 8080, etc).

---

## Endpoints

---

### 1. Health Check
**`GET /api/health`**

Check if the server and AI model are running.

**Response:**
```json
{
  "status": "ok",
  "version": "2.0",
  "llm_loaded": true,
  "summaries_dir": "C:/...outputs/summaries"
}
```

---

### 2. Get All Patients
**`GET /api/patients`**

Returns the list of all patients in the system. Use this to build the patient search/list page.

**Response:**
```json
{
  "total": 22,
  "patients": [
    {
      "subject_id": 10000032,
      "age": 52,
      "gender": "F",
      "hadm_ids": [22595853, 22841357],
      "admissions": [
        {
          "hadm_id": 22595853,
          "risk_level": "HIGH",
          "probability": 0.4231,
          "generated_at": "2026-04-30T12:00:00"
        },
        {
          "hadm_id": 22841357,
          "risk_level": "LOW",
          "probability": 0.1102,
          "generated_at": "2026-04-30T12:05:00"
        }
      ]
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | int | Unique patient ID |
| `age` | int | Patient age |
| `gender` | string | "M" or "F" |
| `hadm_ids` | int[] | All admission IDs for this patient |
| `admissions` | array | Summary info per admission |
| `risk_level` | string | "HIGH", "MEDIUM", or "LOW" |
| `probability` | float | Mortality probability 0.0–1.0 (multiply by 100 for %) |

---

### 3. Get Patient Dashboard (Case 1 — Existing Patient, No New Data)
**`GET /api/patient/{hadm_id}`**

Returns the full AI-generated dashboard for an existing patient admission.
This is the main patient view page.

**Example:** `GET /api/patient/22595853`

**Response:**
```json
{
  "patient_id": "10000032_22595853",
  "subject_id": 10000032,
  "hadm_id": 22595853,
  "demographics": {
    "age": 52,
    "gender": "F"
  },
  "admission": {
    "admittime": "2180-07-23 14:00:00",
    "dischtime": "2180-07-28 18:00:00",
    "los_days": 5.17
  },
  "diagnoses": [
    "Sepsis",
    "Acute kidney injury",
    "Hypertension"
  ],
  "medications": [
    "Vancomycin",
    "Norepinephrine",
    "Heparin"
  ],
  "predicted_mortality": {
    "probability": 0.4231,
    "risk_level": "HIGH"
  },
  "lab_summary": {
    "n_abnormal": 7,
    "top_abnormal": [
      {
        "name": "Creatinine",
        "value": 3.2,
        "unit": "mg/dL",
        "ref_low": 0.6,
        "ref_high": 1.2,
        "severity": 0.867,
        "direction": "HIGH"
      },
      {
        "name": "Potassium",
        "value": 5.9,
        "unit": "mEq/L",
        "ref_low": 3.5,
        "ref_high": 5.0,
        "severity": 0.600,
        "direction": "HIGH"
      }
    ]
  },
  "vital_summary": {
    "alerts": [
      {
        "vital_name": "heart_rate",
        "value": 118,
        "status": "HIGH",
        "trend": "INCREASING"
      },
      {
        "vital_name": "spo2",
        "value": 88,
        "status": "LOW",
        "trend": "STABLE"
      }
    ],
    "trend_overview": {
      "heart_rate": "INCREASING",
      "spo2": "STABLE"
    }
  },
  "alerts": [
    {
      "type": "LAB",
      "severity": "CRITICAL",
      "message": "Creatinine critically elevated (3.2 mg/dL)"
    },
    {
      "type": "MORTALITY",
      "severity": "HIGH",
      "message": "High mortality risk: 42.3%"
    }
  ],
  "clinical_summary": "This 52-year-old female patient presents with a high-acuity clinical picture characterized by multi-organ involvement, most critically affecting renal function. The laboratory profile reveals significant renal impairment alongside electrolyte disturbances, while vital sign monitoring indicates hemodynamic instability with a rising heart rate and compromised oxygenation. The predicted 42% in-hospital mortality risk reflects the severity of the septic presentation and warrants immediate reassessment of vasopressor support and fluid management strategy.",
  "note_excerpt": "Patient admitted with fever, hypotension, and oliguria...",
  "generated_at": "2026-04-30T12:00:00"
}
```

#### What to display and where:

| Field | Where to show it |
|-------|-----------------|
| `demographics.age` + `demographics.gender` | Patient header card |
| `admission.admittime` / `dischtime` | Admission info section |
| `admission.los_days` | Length of stay badge |
| `diagnoses` | Diagnoses list |
| `medications` | Medications list |
| `predicted_mortality.probability` | Circular gauge (× 100 = %) |
| `predicted_mortality.risk_level` | Color badge: HIGH=red, MEDIUM=orange, LOW=green |
| `lab_summary.top_abnormal` | Lab results table (sorted by severity) |
| `vital_summary.alerts` | Vital signs panel |
| `alerts` | Alert banner at top of page |
| `clinical_summary` | AI Summary text box |
| `note_excerpt` | Collapsible note preview |

#### Lab result display rules:
- `direction = "HIGH"` → red cell with ↑ arrow
- `direction = "LOW"` → blue cell with ↓ arrow
- `severity` is 0.0–1.0 → use for color intensity or a bar width visual

#### Vital trend display rules:
- `"INCREASING"` → show ↑
- `"DECREASING"` → show ↓
- `"STABLE"` → show →

#### Vital name display (convert snake_case to readable):
| API value | Display as |
|-----------|-----------|
| `heart_rate` | Heart Rate |
| `systolic_bp` | Systolic BP |
| `diastolic_bp` | Diastolic BP |
| `mean_bp` | Mean BP |
| `spo2` | SpO2 |
| `respiratory_rate` | Respiratory Rate |
| `temperature_f` | Temperature (°F) |
| `temperature_c` | Temperature (°C) |

---

### 4. Update Patient with New Data (Case 2 — Existing Patient + New Data)
**`POST /api/patient/{hadm_id}/update`**

Use when the doctor adds new information for an existing patient:
a new note, new lab PDF, or new vital readings.
All fields are optional — send only what is new.

**Content-Type:** `multipart/form-data`

**Form fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `note_text` | string | No | New clinical note text |
| `labs_pdf` | file | No | PDF lab report file |
| `vitals` | JSON string | No | Array of new vital readings (see format below) |

**Vitals JSON format:**
```json
[
  {"name": "Heart Rate", "value": 95},
  {"name": "Systolic Blood Pressure", "value": 110},
  {"name": "SpO2", "value": 96},
  {"name": "Temperature Fahrenheit", "value": 98.6},
  {"name": "Respiratory Rate", "value": 18}
]
```

**JavaScript example:**
```javascript
const formData = new FormData();
formData.append('note_text', 'Patient condition worsened overnight...');
formData.append('vitals', JSON.stringify([
  { name: 'Heart Rate', value: 110 },
  { name: 'SpO2', value: 91 }
]));
// If doctor uploaded a PDF:
// formData.append('labs_pdf', pdfFileObject);

const response = await fetch('http://localhost:5000/api/patient/22595853/update', {
  method: 'POST',
  body: formData
});
const data = await response.json();
```

**Response:** Full dashboard JSON (same as Case 1) plus an extra `update_diff` field:
```json
{
  "...full dashboard fields...",
  "update_diff": {
    "old_probability": 0.3467,
    "new_probability": 0.4231,
    "risk_changed": true,
    "old_risk": "MEDIUM",
    "new_risk": "HIGH"
  }
}
```

Use `update_diff` to show the doctor what changed:
- If `risk_changed` is true → show a banner: "Risk increased from MEDIUM (34.7%) → HIGH (42.3%)"
- If `risk_changed` is false → show: "Risk unchanged: MEDIUM (34.7% → 42.3%)"

---

### 5. New Patient — Full Pipeline (Case 3)
**`POST /api/patient/new`**

Use when admitting a brand new patient who is not yet in the system.

**Content-Type:** `multipart/form-data`

**Form fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `age` | int | **Yes** | Patient age in years |
| `gender` | string | **Yes** | "M" or "F" |
| `admittime` | string | No | Admission datetime e.g. "2026-05-01T08:00:00" (defaults to now) |
| `note_text` | string | No | Clinical note / initial assessment |
| `labs_pdf` | file | No | PDF lab report |
| `vitals` | JSON string | No | Array of vital readings (same format as Case 2) |

**JavaScript example:**
```javascript
const formData = new FormData();
formData.append('age', '67');
formData.append('gender', 'M');
formData.append('note_text', 'Patient admitted with chest pain and shortness of breath...');
formData.append('vitals', JSON.stringify([
  { name: 'Heart Rate', value: 102 },
  { name: 'Systolic Blood Pressure', value: 88 },
  { name: 'SpO2', value: 93 }
]));
// Optional: formData.append('labs_pdf', pdfFileObject);

const response = await fetch('http://localhost:5000/api/patient/new', {
  method: 'POST',
  body: formData
});
const data = await response.json();
// data.hadm_id is the new patient's admission ID — save it for navigation
```

**Response:** Full dashboard JSON (same structure as Case 1).
The new patient is automatically saved — they appear in `GET /api/patients` immediately.

---

### 6. Parse PDF Lab Report (Preview Helper)
**`POST /api/parse-pdf`**

Extract lab values from a PDF before submitting. Use this to show the doctor a preview
of what was extracted so they can verify or correct it before running the AI pipeline.

**Content-Type:** `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `lab_pdf` | file | Yes |

**Response:**
```json
{
  "parse_success": true,
  "n_extracted": 8,
  "labs": [
    {
      "name": "Creatinine",
      "value": 3.2,
      "unit": "mg/dL",
      "ref_low": 0.6,
      "ref_high": 1.2
    },
    {
      "name": "Glucose",
      "value": 185,
      "unit": "mg/dL",
      "ref_low": 70,
      "ref_high": 100
    }
  ]
}
```

If `n_extracted` is 0 or `parse_success` is false:
→ Show a manual entry table so the doctor can type the values by hand.
→ Then send those manually entered values as `labs_pdf` is skipped and you use a different approach — contact the AI team.

---

## Full Frontend Page Flow

### Patient List Page
```
GET /api/patients
→ Show searchable table: patient ID, age, gender, risk badge, last admission date
→ Click row → navigate to /dashboard/{hadm_id}
```

### Patient Dashboard Page
```
GET /api/patient/{hadm_id}
→ Show: demographics header, mortality gauge, alerts banner,
         diagnoses + medications, labs table, vitals panel, AI summary box
→ "Update Patient" button → opens Case 2 form
```

### Update Patient Page (Case 2)
```
Show form: text area for note, PDF upload, vitals input fields
→ POST /api/patient/{hadm_id}/update
→ Show updated dashboard + highlight risk change using update_diff
```

### New Patient Page (Case 3)
```
Show form: age (required), gender (required), note, PDF, vitals
→ POST /api/patient/new
→ Redirect to /dashboard/{new hadm_id from response}
```

---

## Accepted Vital Sign Names

Send these exact strings in the `name` field of the vitals JSON array:

| Send this | Meaning |
|-----------|---------|
| `"Heart Rate"` | Heart rate (bpm) |
| `"Systolic Blood Pressure"` | Systolic BP (mmHg) |
| `"Diastolic Blood Pressure"` | Diastolic BP (mmHg) |
| `"Mean Blood Pressure"` | Mean arterial pressure (mmHg) |
| `"SpO2"` | Oxygen saturation (%) |
| `"Respiratory Rate"` | Breaths per minute |
| `"Temperature Fahrenheit"` | Temperature in °F |
| `"Temperature Celsius"` | Temperature in °C |

---

## Risk Level Color Guide

| risk_level | Color | Threshold |
|------------|-------|-----------|
| `"HIGH"` | Red | Mortality ≥ 40% |
| `"MEDIUM"` | Orange/Yellow | Mortality 25–40% |
| `"LOW"` | Green | Mortality < 25% |

---

## Error Reference

| HTTP Code | Meaning | What to show |
|-----------|---------|-------------|
| 404 | Patient not found | "Patient not found" message |
| 422 | Missing required field | Form validation error |
| 500 | Server/pipeline error | "Something went wrong, try again" |

---

## Important Notes

- **First request** after server start may take a few extra seconds (AI model warming up)
- **PDF parsing** works best with text-based PDFs (not scanned/image PDFs)
- The `clinical_summary` is AI-generated text — display it exactly as returned, no editing
- The `note_excerpt` is the first 500 characters of the clinical note — good for a tooltip or expandable preview
- `generated_at` is UTC — convert to local timezone for display
- All probability values are 0.0 to 1.0 — multiply by 100 to show as a percentage
- `severity` in lab results is 0.0 to 1.0 — higher = more abnormal; use it to sort the table or set color intensity
- One patient (`subject_id`) can have multiple admissions (`hadm_id`) — each admission is an independent dashboard

---

## Deployment Plan (For Going Live)

### During Development
Use `http://localhost:5000` as the base URL while building and testing locally.
The AI team will run the API server on their machine during this phase.

### Going Live (After Frontend is Complete)
Once you finish the frontend, the AI team will deploy the API to a public server.

**What will change:**
- The base URL will change from `http://localhost:5000` to a public URL, for example:
  ```
  https://clinnote-api.railway.app
  ```
- **You only need to change one line in your frontend** — wherever you define the base URL:
  ```javascript
  // Development
  const API_BASE = "http://localhost:5000";

  // Production (swap this when AI team gives you the deployed URL)
  const API_BASE = "https://clinnote-api.railway.app";
  ```
- Everything else (endpoints, request format, response format) stays exactly the same.

**Recommended:** Store the base URL in an environment variable in your frontend:
```javascript
const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:5000";
```
Then in production just set `REACT_APP_API_URL` to the deployed URL.

### No GPU Required
The API runs on a standard server — no special hardware needed.
No API keys or `.env` files are required to run the API.

### CORS
CORS is already fully enabled on the API — your frontend can call it from any domain or port without any changes.
