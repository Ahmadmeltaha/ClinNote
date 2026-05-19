# ClinNote

**AI-powered clinical data integration platform.** Doctors enter patient data (notes, labs, vitals), the system runs it through a multimodal AI pipeline, and produces a structured clinical dashboard with mortality risk scores, prioritized alerts, and an AI-generated summary.

Built as the Spring 2025 capstone project at **Al-Hussein Technical University** (Computer Science / AI & Data Science).

---

## Team

| Name | Role |
|---|---|
| **Ahmad Jaber** (22110362) | AI pipeline, FastAPI server, ML model |
| **Daliah Qadri** (22210028) | Anomaly detection, data preprocessing |
| **Ahmad Meltaha** (22110360) | Web application (frontend + backend), database, deployment |

Supervisor: **Dr. Rami Al Ouran**

---

## Repository Layout

This is a mono-repo with two sibling projects:

```
ClinNote/
├── CliNote-Web/clinote-web/    →  Web application (Next.js + Prisma + Supabase)
└── ClinNote-AI/ClinNote/       →  AI pipeline (FastAPI + PyTorch + Phi-3.5-mini)
```

Each subproject has its own README with details:

- **Web app:** [`CliNote-Web/clinote-web/README.md`](./CliNote-Web/clinote-web/README.md)
- **AI pipeline:** [`ClinNote-AI/ClinNote/README.md`](./ClinNote-AI/ClinNote/README.md) and [`ClinNote-AI/ClinNote/api/README_API.md`](./ClinNote-AI/ClinNote/api/README_API.md)

---

## Tech Stack

### Web Application

| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router) + React 19 |
| Language | TypeScript (strict mode) |
| Styling | Tailwind CSS v4 + class-based dark mode |
| Database | Supabase Postgres |
| ORM | Prisma |
| Authentication | NextAuth.js (Credentials provider, JWT sessions) |
| Forms | React Hook Form + Zod |
| Charts | Recharts |

### AI Pipeline

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| ML framework | PyTorch |
| NLP model | Bio_ClinicalBERT |
| LLM | Phi-3.5-mini-instruct |
| Architecture | DisentangledTransformer (custom multimodal fusion) |
| PDF parsing | pdfplumber |

---

## How It Works

The system supports three clinical workflows:

1. **View an existing patient** — load a pre-generated dashboard from disk (~2 s)
2. **Update a patient** — submit new notes, vitals, or lab PDFs → AI pipeline re-runs → returns a refreshed dashboard with a risk-change diff (~8–15 s)
3. **Register a new patient** — full pipeline runs from scratch and assigns a new admission ID

The web app communicates with the AI pipeline through a REST API (`/api/patient/{hadm_id}`, `/api/patient/new`, `/api/patient/{hadm_id}/update`, `/api/parse-pdf`). The web app also maintains its own Supabase database with all 568 cohort patients pre-imported, so browsing and searching work even when the AI server is offline.

---

## Local Setup

### Prerequisites

- **Node.js** 20+ (for the web app)
- **Python** 3.11+ (for the AI pipeline)
- **PostgreSQL** access via Supabase (or any Postgres instance) for the web app
- ~8 GB free RAM (Phi-3.5-mini loads ~7 GB)

### Web app

```bash
cd CliNote-Web/clinote-web
npm install
cp .env.example .env.local   # fill in DATABASE_URL, NEXTAUTH_SECRET, etc.
npx prisma generate
npx prisma migrate deploy
npm run dev
```

The web app starts on http://localhost:3000.

### AI server

```bash
cd ClinNote-AI/ClinNote
python -m venv venv
venv\Scripts\activate                       # Windows
# or: source venv/bin/activate              # macOS / Linux
pip install -r requirements.txt

# Start the FastAPI server
python -m uvicorn api.app:app --host 127.0.0.1 --port 5000
```

The AI server starts on http://127.0.0.1:5000. **Use `127.0.0.1`, not `localhost`** — on Windows, Node's `fetch` resolves `localhost` to IPv6 but uvicorn binds IPv4 only.

### Wiring them together

In the web app's `.env.local`, set:

```env
AI_PIPELINE_URL=http://127.0.0.1:5000
```

The web app auto-detects whether the AI server is up. If it isn't, it falls back to a mock response so the UI never crashes.

---

## Data Handling

The system was trained and evaluated on **MIMIC-IV** (Medical Information Mart for Intensive Care IV), a de-identified clinical database accessed through PhysioNet under an approved Data Use Agreement.

**Per the PhysioNet DUA, raw MIMIC-IV CSVs are NOT included in this repository.** Anyone running the AI pipeline locally needs their own PhysioNet credentials and a local copy of the data.

The repository also excludes all AI-generated per-patient outputs (summaries, features, model checkpoints) for the same reason.

---

## License

This project is part of an academic capstone and is shared for educational and review purposes. The AI pipeline (`ClinNote-AI/`) is the work of Ahmad Jaber and Daliah Qadri. The web application (`CliNote-Web/`) is the work of Ahmad Meltaha.

External components keep their original licenses (Bio_ClinicalBERT, Phi-3.5-mini, Next.js, etc.).
