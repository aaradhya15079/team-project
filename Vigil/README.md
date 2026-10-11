# Vigil - AI-Powered Personal Health Copilot

> **Hackathon Build**: Transforming complex medical records and wearable sensor streams into actionable, grounded health insights.

---

## 🚀 Architecture Overview

- **Frontend**: React + TypeScript + Vite + Tailwind CSS + Lucide Icons
  - Mobile-first, empathetic design matching the original specification
  - 2x2 live vitals metric grid (Heart Rate, Temperature, Sleep, Blood Pressure) with dynamic alert badges
  - Insight card with contextual clinical pattern analysis ("Why we flagged it")
  - Interactive Daily Care Protocol checklist (optimistic UI + SQLite database persistence)
  - Diagnostic lab records viewer with flagged out-of-range biomarkers (LDL, Fasting Glucose, hs-CRP, etc.)
  - Real-time AI Copilot chat widget with streaming text responses and verifiable clinical lab citations
  - Running live on `http://localhost:5173`

- **Backend**: FastAPI + SQLite + SQLAlchemy + Pydantic
  - SQLite database (`vigil.db`) with tables for `Patient`, `Medication`, `DiagnosticReport`, `Biomarker`, and `ChatLog`
  - CORS middleware configured for `http://localhost:5173`
  - Streaming AI responses via Server-Sent Events (`text/event-stream`)
  - Running live on `http://127.0.0.1:8000`

---

## 🛠️ API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/patient` | Returns patient profile, vitals grid, flagged patterns, and active conditions |
| `GET` | `/api/medications` | Returns the daily care protocol checklist |
| `PATCH` | `/api/medications/{id}/toggle` | Toggles the `taken_today` boolean for a medication |
| `GET` | `/api/reports` | Returns parsed diagnostic lab results and flagged out-of-range biomarkers |
| `POST` | `/api/chat` | Accepts user queries, streams real-time AI responses with evidence-based lab citations |
| `GET` | `/api/chat/history` | Fetches persistent conversation logs stored in SQLite |

---

## ⚡ Quick Start

### 1. Start Both Services (Single Command)
```powershell
.\start-dev.ps1
```
Or via npm in the project root:
```bash
npm run dev
```

### 2. Manual Server Startup

**Backend:**
```powershell
cd backend
.\venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend:**
```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

---

## 🧪 Verification & Features

- **Vitals & Pattern Detection**: Live correlation between rising resting heart rate (69 to 78 bpm over 8 days), reduced sleep duration (5.7h), and elevated hs-CRP (3.4 mg/L).
- **Interactive Checklists**: Click on any medication in the Daily Care Protocol to toggle its completion state and persist it to SQLite.
- **Biomarker Out-of-Range Highlighting**: Critical labs (LDL: 142 mg/dL, Fasting Glucose: 106 mg/dL, hs-CRP: 3.4 mg/L) are highlighted with normal reference ranges.
- **Evidence-Based Copilot**: Ask questions via the "Night help" tab or floating "Ask Vigil" button to receive streamed medical reasoning with attached source citations.
