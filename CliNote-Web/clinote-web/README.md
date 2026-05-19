# CliNote — AI-Powered Clinical Data Integration

A clinical dashboard for doctors to manage patient records and run AI-driven mortality risk prediction on their cases. Doctors enter notes, labs, and vital signs (manual or via MIMIC-IV CSV bulk imports), then click **Analyze with AI** to get back a clinical summary, mortality risk score with confidence level, and prioritized alerts. Built as a graduation capstone at **Al-Hussein Technical University (HTU)**.

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-38bdf8?logo=tailwindcss)
![Prisma](https://img.shields.io/badge/Prisma-5-2D3748?logo=prisma)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3ECF8E?logo=supabase)
![NextAuth](https://img.shields.io/badge/Auth-NextAuth.js-7B61FF)
![Vercel](https://img.shields.io/badge/Deploy-Vercel-000?logo=vercel)

## Team

- **Ahmad Meltaha** — Fullstack Developer (web dashboard)
- **Ahmad Jaber** — AI Engineer (ClinNote pipeline — separate repository)
- **Daliah Qadri** — Data Engineer
- **Supervisor:** Dr. Rami Al Ouran

## Features

- Doctor authentication with JWT sessions (NextAuth Credentials provider, bcrypt-hashed passwords)
- Patient CRUD with ownership-based access control (every record is scoped to the logged-in doctor)
- Clinical data entry: diagnoses, medications, allergies, lab results, vital signs, clinical notes
- CSV bulk upload supporting MIMIC-IV format (`labs_final.csv`, `vital_signs.csv`, `clinical_notes.csv`)
- AI mortality risk prediction with mock fallback when the AI server is offline
- Real-time alerts panel with priority sorting, filters, and resolution tracking
- Auto-generated clinical reports with editor, side-by-side AI comparison, and approval workflow (DRAFT → PENDING → APPROVED / REJECTED)
- Model performance dashboard (AUROC, ablation study, anomaly-detection precision/recall)
- Skeleton loading screens and per-route error boundaries for resilient UX
- Dark mode (Tailwind `dark:` variants), responsive layout

## Architecture

```
   ┌─────────────────┐    HTTP    ┌──────────────────────┐
   │     Browser     │ ─────────► │  Next.js  (port 3000)│
   └─────────────────┘            │  UI + API routes     │
                                  └──────┬───────────────┘
                                         │
                          ┌──────────────┴──────────────┐
                          │                             │
                          ▼                             ▼
                ┌─────────────────┐         ┌──────────────────────┐
                │    Supabase     │         │   ClinNote AI        │
                │   PostgreSQL    │         │   FastAPI (port 5000)│
                │    via Prisma   │         │   ClinicalBERT +     │
                │                 │         │   Phi-3.5-mini       │
                └─────────────────┘         └──────────────────────┘
```

The AI pipeline is a separate Python service maintained by Ahmad Jaber. During development it lives in a sibling folder (`../ClinNote-AI/`) and the web app talks to it over HTTP. When the AI server isn't reachable, the web app falls back to a mock response so the UI remains fully usable for demos.

## Prerequisites

- Node.js 20+
- npm
- A Supabase account (free tier is enough)
- *(Optional)* The ClinNote AI pipeline server, running locally on port 5000. The web app degrades gracefully to mock data when the AI server is offline.

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd clinote-web
```

### 2. Install dependencies

```bash
npm install
```

### 3. Create a Supabase project

- Go to [supabase.com](https://supabase.com) → **New Project**
- Pick a region close to you (we used West EU)
- Copy the **Transaction Pooler** connection string → `DATABASE_URL`
- Copy the **Direct Connection** connection string → `DIRECT_URL`

### 4. Create `.env.local`

Use this template and fill in your values:

```env
# Database
DATABASE_URL="postgresql://postgres.xxx:PASSWORD@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"
DIRECT_URL="postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres"

# Auth
NEXTAUTH_SECRET="any-random-32-char-string"
NEXTAUTH_URL="http://localhost:3000"

# AI Pipeline (default port 5000)
AI_PIPELINE_URL="http://localhost:5000"

# Set to "true" to force mock AI even when the server is reachable
# AI_USE_MOCK="true"
```

Also copy `DATABASE_URL` and `DIRECT_URL` into a `.env` file at the project root — the Prisma CLI reads `.env`, not `.env.local`.

### 5. Push the database schema

```bash
npx prisma db push
npx prisma generate
```

### 6. Start the dev server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). On first load you'll be redirected to `/login` — click **Sign up** to create an account, then you land on the dashboard.

### 7. (Optional) Start the AI pipeline

In a separate terminal, from the ClinNote-AI repository:

```bash
uvicorn api.app:app --reload --port 5000 --app-dir <path-to-ClinNote-AI>
```

Verify by opening [http://localhost:5000/api/health](http://localhost:5000/api/health) — you should get a JSON response with `"version": "2.0"` and `"llm_loaded": true`.

If you skip this step, the web app uses mock AI data automatically.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Supabase Transaction Pooler connection string (used by the app at runtime) |
| `DIRECT_URL` | Yes | Supabase Direct Connection (used by Prisma migrations / `db push`) |
| `NEXTAUTH_SECRET` | Yes | 32+ character random string for signing JWT sessions |
| `NEXTAUTH_URL` | Yes | Public URL of the app (`http://localhost:3000` in dev, your Vercel URL in prod) |
| `AI_PIPELINE_URL` | No | Base URL of the AI server. Defaults to `http://localhost:5000` |
| `AI_USE_MOCK` | No | Set to `"true"` to force mock AI even when the real server is reachable. Useful for offline demos |

## Project Structure

```
src/
├── app/
│   ├── (auth)/            — login + register pages (no sidebar)
│   ├── (dashboard)/       — main app pages (with sidebar)
│   │   ├── dashboard/     — overview + stats
│   │   ├── patients/      — list, new, [id] detail, edit, update, report
│   │   ├── alerts/        — global alerts feed
│   │   └── model-performance/ — AUROC, ablation chart, training info
│   └── api/               — REST API routes
├── components/
│   ├── layout/            — Sidebar, Header, MainLayout
│   ├── patients/          — PatientTable, PatientForm, UpdatePatientForm
│   ├── patient-detail/    — DemographicsCard, MortalityGauge, AnalyzeButton, etc.
│   ├── alerts/            — AlertCard, AlertsList
│   ├── reports/           — ReportView, ReportEditor, ReportApproval
│   ├── dashboard/         — StatsGrid, RiskDistributionChart, RecentAlerts
│   ├── model-performance/ — MetricsOverview, AblationChart, AnomalyDetectionStats
│   └── ui/                — reusable primitives (Button, Badge, Modal, Skeleton, ErrorState…)
├── lib/
│   ├── server/            — prisma, auth, ai-pipeline, ai-adapter, ai-analysis
│   └── client/            — API helpers, utils, MIMIC CSV mappers
├── types/                 — all TypeScript interfaces
└── middleware.ts          — route protection
```

## API Routes

| Route group | Purpose |
|-------------|---------|
| `/api/auth/*` | NextAuth (sign-in, callbacks) and registration |
| `/api/patients` | List + create patients |
| `/api/patients/[id]` | Read / update / delete a single patient |
| `/api/patients/[id]/diagnoses`, `/medications`, `/allergies`, `/lab-results`, `/vital-signs`, `/clinical-notes` | Per-section CRUD plus `…/bulk` endpoints for CSV imports |
| `/api/patients/[id]/submit` | Trigger an AI analysis using whatever data is in the DB |
| `/api/patients/[id]/update-and-analyze` | Save new clinical data + re-run analysis in one call |
| `/api/patients/[id]/reports/*` | Report CRUD and approval workflow |
| `/api/alerts` and `/api/alerts/[id]` | Global alerts feed + resolve |

## AI Integration

- The web app calls Ahmad Jaber's FastAPI server with **multipart/form-data** requests (note text, vitals JSON, optional PDF labs).
- Each patient is linked to Ahmad's pipeline via two columns on our `Patient` model: `aiHadmId` (admission ID) and `aiSubjectId` (patient ID). Both are populated automatically the first time AI analysis runs on a patient.
- Three flows are handled inside `src/lib/server/ai-analysis.ts`:
  1. **First analysis** for a patient → `POST /api/patient/new`, store the returned `hadm_id` and `subject_id`.
  2. **Re-analysis** of an existing patient → `POST /api/patient/{hadm_id}/update` with the latest local note + vitals so Ahmad's pipeline always sees fresh data. The response includes `update_diff` for the risk-change banner.
  3. **AI server unreachable** → fall back to a hardcoded sepsis template via the same adapter pipeline so consumers don't know the difference.
- The translation layer (`src/lib/server/ai-adapter.ts`) keeps the UI insulated from changes in Ahmad's response shape — components only ever consume our internal `PatientResult` type.
- First real call after the AI server boots takes ~60 s while Phi-3.5-mini warms up. CPU-only PyTorch installs add another few seconds per call.

For the full API contract, see `../ClinNote-AI/ClinNote/api/README_API.md`.

## Scripts

```bash
npm run dev         # Start dev server (http://localhost:3000)
npm run build       # Production build
npm run start       # Run production build
npm run lint        # ESLint
npx prisma studio   # Browse the database in a GUI
npx prisma db push  # Push schema changes to Supabase
```

## Deployment

The app deploys to **Vercel**. Connect the GitHub repo, set the environment variables from the table above in Vercel's dashboard, and Vercel handles the rest.

The AI pipeline runs separately — on a developer's machine during demos, or on a server with a GPU for a production deployment.

## Acknowledgments

- Built as a graduation capstone at Al-Hussein Technical University (HTU) under Dr. Rami Al Ouran
- Uses the MIMIC-IV ICU dataset for training and demo data
- AI pipeline: ClinicalBERT (note encoder) + Phi-3.5-mini-instruct (summary generator) via HuggingFace
