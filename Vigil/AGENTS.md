# Vigil Development Guide (For Antigravity Agents & Collaborators)

## 🎯 Project Overview
**Vigil** is an AI-powered personal health companion that bridges continuous wearable sensor telemetry (resting heart rate, HRV, circadian skin temperature, sleep recovery) with episodic clinical laboratory diagnostic records (blood panels, ECGs, prescriptions).

---

## 🏗️ Architecture & Services

### 1. Frontend (`/frontend`)
- **Framework**: React 19 + TypeScript + Vite + Tailwind CSS + Lucide Icons + Three.js + Framer Motion.
- **Port**: `http://127.0.0.1:5173/`
- **Proxy Configuration**: `/api` requests are automatically proxied to the backend at `http://127.0.0.1:8000`.
- **Components Built**:
  - `pages/HomePage.tsx`: Public universal marketing page featuring:
    - Interactive 3D WebGL Biometric Core (`Biometric3DCanvas.tsx`).
    - Full-Screen 3D Physiological Digital Twin observatory (`Full3DHealthObservatory.tsx`).
    - Interactive Color-Negate Bio-Fluoroscopy X-Ray stage (`#color-negate-lens`).
    - Liquid Negate Cursor (`LiquidNegateCursor.tsx`).
    - 4-Pillar Platform Architecture Bento Grid with 3D tilt cards (`Card3DTilt.tsx`).
    - Membership tiers & FAQ accordion.
  - `Dashboard.tsx`: Completed patient health dashboard featuring:
    - 2x2 live vitals metric grid (RHR, Temperature, Sleep, Blood Pressure).
    - 8-day historical telemetry chart with interactive hover inspection.
    - AI clinical intake with OCR document scanning simulation (`/api/documents/analyze`).
    - Streaming Night Help Copilot with citations (`/api/chat`).
    - Interactive Daily Care Protocol checklist (`/api/medications`).
    - Diagnostic reports and flagged out-of-range biomarkers (`/api/reports`).
    - Care circle & high-contrast printable Emergency Medical ICE pass.
  - `components/AuthModal.tsx`: Teammate-ready authentication & registration modal.
    - Ready to connect to backend auth endpoints (`/api/auth/register`, `/api/auth/login`).
    - Has an "Instant Demo: Launch with Eleanor Vance" button for quick review.
  - `App.tsx`: Manages routing between `HomePage` and `Dashboard`, enforces authentication gate (no dashboard readings until signup/login), and syncs `#home` vs `#dashboard` browser hash.

### 2. Backend (`/backend`)
- **Framework**: FastAPI + Python 3.10+ + SQLAlchemy + SQLite (`vigil.db`).
- **Port**: `http://127.0.0.1:8000/`
- **Key Files**:
  - `main.py`: API entry point with endpoints:
    - `GET /api/patient`: Patient vitals, 8-day trend, active conditions.
    - `GET /api/medications`: Medication checklist.
    - `PATCH /api/medications/{id}/toggle`: Toggle medication taken status.
    - `GET /api/reports`: Diagnostic reports & biomarker flags.
    - `POST /api/documents/analyze`: Document OCR analysis.
    - `POST /api/chat`: Server-sent events streaming copilot.
    - `GET /api/chat/history`: Chat history log.
  - `models.py`: SQLAlchemy database models.
  - `schemas.py`: Pydantic validation schemas.
  - `seed.py`: Initial database seeding.

---

## 🚀 How to Run Locally

### Start Both Services (Single Command)
```powershell
.\start-dev.ps1
```

### Or Start Individually
**Backend:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend:**
```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

---

## 🤝 Backend Teammate Handoff & Next Steps
- The frontend `AuthModal.tsx` is ready for integration. To connect real authentication:
  - Add `POST /api/auth/signup` and `POST /api/auth/login` in `backend/main.py`.
  - Update `AuthModal.tsx` fetch calls to point to these endpoints.
