# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository structure

This repo has two parts, deployed and versioned independently:

- **`backend/`** — a single-file FastAPI app (`main.py`), deployed to Railway.
- **`frontend/`** — a Create React App, deployed to Vercel. **`frontend` is a git submodule** (its own `.git`, own remote) — commits inside `frontend/` do not get picked up by `git add`/`git commit` at the repo root; you must commit inside `frontend/` separately, and the root repo just tracks a pinned commit SHA for it. Run `git status` in both the root and `frontend/` when checking for uncommitted work.

There is no shared package manager, monorepo tool, or root-level build script — treat backend and frontend as two independent projects that happen to live in the same working copy.

## Commands

### Backend (`backend/`)
```bash
cd backend
pip install fastapi uvicorn groq opencv-python-headless reportlab pillow python-multipart
export GROQ_API_KEY=your_groq_api_key_here
uvicorn main:app --reload
```
- Runs at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.
- No test suite, linter, or formatter is configured for the backend.
- `requirements.txt` is a full `pip freeze` (includes streamlit, torch, pandas, etc. that `main.py` doesn't import) — don't treat it as a minimal/curated dependency list when reasoning about what the app actually uses.

### Frontend (`frontend/`)
```bash
cd frontend
npm install
npm start      # dev server on http://localhost:3000
npm run build
npm test       # react-scripts test (Jest + Testing Library), watch mode by default
```
To run a single test file: `npm test -- App.test.js` (CRA's Jest wrapper; add `-- --watchAll=false` for a single non-interactive run).

## Architecture

### Backend (`backend/main.py`)
Everything — API routes, DB access, image preprocessing, PDF generation, and the AI prompt — lives in this one file. Flow for the core endpoint:

1. `POST /analyze` receives an uploaded image, decodes it with OpenCV.
2. `preprocess_image()` runs denoising → unsharp-mask sharpening → LAB-space CLAHE contrast enhancement.
3. The enhanced image is base64-encoded and sent to Groq's vision API (`meta-llama/llama-4-scout-17b-16e-instruct`) along with `SYSTEM_PROMPT`, which forces a strict JSON response describing verdict, quality score, and a `defects[]` list (each defect carries severity, urgency, damage/financial/safety projections).
4. The result is persisted to SQLite (`visiq_history.db`, created at `init_db()` on startup) via `save_inspection()`, then returned to the client merged with computed fields (`defect_count`, `severity_counts`, `image_size`, `processing_time_ms`).

Other endpoints: `GET /history` (last 20 inspections, wrapped as `{"inspections": [...]}`), `GET /stats` (aggregate counts/pass rate, keyed as `total_inspections`/`approved`/`defective`/`review`/`avg_score`/`pass_rate`), `POST /export-pdf` (rebuilds a ReportLab PDF from a JSON inspection result posted by the client), `GET /health`.

Note: the Groq JSON schema returns `component_type`/`component_info`; the backend stores that under a DB column and response field named `material_type` (the frontend's field name) — `save_inspection()` and the `/analyze` response both map `component_type` → `material_type` internally, so don't be surprised the DB column name doesn't match the AI schema key.

### Frontend (`frontend/src/App.js`)
Single-file React app (no router, no component files) — all UI (tab switching between Inspect/History/Stats, upload/camera capture, results display, defect cards, PDF/text export) lives in `App.js` as inline-styled components. `API` at the top of the file is hardcoded to a production Railway URL (`https://visiq-production.up.railway.app`), not an env var — update this constant directly when pointing at a different backend, including local dev.

Notable behaviors:
- Camera capture uses `getUserMedia` + a hidden `<canvas>` to snapshot a frame into a `File`, then reuses the normal upload/analyze flow.
- "Download PDF" (`downloadPDF`) does not call the backend's `/export-pdf` endpoint — it builds and downloads a plain `.txt` file client-side. The backend PDF endpoint exists but is currently unused by the UI.
