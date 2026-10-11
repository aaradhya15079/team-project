import os
import json
import asyncio
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import engine, get_db, Base
import models
import schemas
from seed import seed_database

# Initialize database schema and initial data
Base.metadata.create_all(bind=engine)
seed_database()

app = FastAPI(
    title="Vigil Health Copilot API",
    description="Backend API powering Vigil's health dashboard and AI copilot",
    version="1.0.0"
)

# CORS Middleware setup
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Vigil Health Copilot API",
        "version": "1.0.0"
    }


# 1. GET /api/patient - Returns patient vitals and active conditions
@app.get("/api/patient")
def get_patient(db: Session = Depends(get_db)):
    patient = db.query(models.Patient).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    vitals = [
        {
            "name": "Resting heart rate",
            "value": patient.resting_heart_rate,
            "status": patient.resting_heart_rate_status,
            "trend": patient.resting_heart_rate_trend,
            "is_alert": "Outside" in patient.resting_heart_rate_status
        },
        {
            "name": "Temperature",
            "value": patient.temperature,
            "status": patient.temperature_status,
            "trend": patient.temperature_trend,
            "is_alert": "Outside" in patient.temperature_status
        },
        {
            "name": "Sleep",
            "value": patient.sleep,
            "status": patient.sleep_status,
            "trend": patient.sleep_trend,
            "is_alert": "Outside" in patient.sleep_status
        },
        {
            "name": "Blood pressure",
            "value": patient.blood_pressure,
            "status": patient.blood_pressure_status,
            "trend": patient.blood_pressure_trend,
            "is_alert": "Outside" in patient.blood_pressure_status
        }
    ]

    active_conditions = [c.strip() for c in patient.active_conditions.split(",") if c.strip()]

    return {
        "id": patient.id,
        "name": patient.name,
        "greeting_date": patient.greeting_date,
        "flagged_pattern": {
            "title": patient.flagged_title,
            "description": patient.flagged_description,
            "reason": patient.flagged_reason,
            "guidance": patient.flagged_guidance,
            "disclaimer": patient.flagged_disclaimer,
            "trends": [
                {
                    "metric": "Resting heart rate",
                    "observed": "69 to 78 bpm",
                    "baseline": "usual 60-75"
                },
                {
                    "metric": "Sleep",
                    "observed": "6.8 to 5.7 hours",
                    "baseline": "usual 7-9"
                },
                {
                    "metric": "Temperature",
                    "observed": "36.6 to 37.1°C",
                    "baseline": "still in range"
                }
            ]
        },
        "vitals": vitals,
        "active_conditions": active_conditions
    }


# 2. GET /api/medications - Returns daily care protocol checklist
@app.get("/api/medications", response_model=List[schemas.MedicationResponse])
def get_medications(db: Session = Depends(get_db)):
    medications = db.query(models.Medication).order_by(models.Medication.id.asc()).all()
    return medications


# 3. PATCH /api/medications/{id}/toggle - Updates taken_today boolean
@app.patch("/api/medications/{id}/toggle", response_model=schemas.MedicationResponse)
def toggle_medication(id: int, db: Session = Depends(get_db)):
    medication = db.query(models.Medication).filter(models.Medication.id == id).first()
    if not medication:
        raise HTTPException(status_code=404, detail=f"Medication with id {id} not found")

    medication.taken_today = not medication.taken_today
    medication.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(medication)
    return medication


# 4. GET /api/reports - Returns parsed lab results and out-of-range biomarkers
@app.get("/api/reports")
def get_reports(db: Session = Depends(get_db)):
    reports = db.query(models.DiagnosticReport).all()
    
    out_of_range_list = []
    total_biomarkers = 0

    reports_data = []
    for rep in reports:
        bio_data = []
        for bio in rep.biomarkers:
            total_biomarkers += 1
            b_dict = {
                "id": bio.id,
                "name": bio.name,
                "value": bio.value,
                "unit": bio.unit,
                "reference_range": bio.reference_range,
                "status": bio.status,
                "interpretation": bio.interpretation
            }
            bio_data.append(b_dict)
            if bio.status == "out_of_range":
                out_of_range_list.append({
                    **b_dict,
                    "report_title": rep.title,
                    "report_date": rep.date
                })

        reports_data.append({
            "id": rep.id,
            "title": rep.title,
            "date": rep.date,
            "facility": rep.facility,
            "category": rep.category,
            "summary": rep.summary,
            "biomarkers": bio_data
        })

    return {
        "reports": reports_data,
        "out_of_range_biomarkers": out_of_range_list,
        "total_biomarkers": total_biomarkers,
        "total_reports": len(reports_data)
    }


# GET /api/chat/history - Get existing conversation logs
@app.get("/api/chat/history")
def get_chat_history(db: Session = Depends(get_db)):
    logs = db.query(models.ChatLog).order_by(models.ChatLog.id.asc()).all()
    result = []
    for log in logs:
        citations = []
        if log.citations:
            try:
                citations = json.loads(log.citations)
            except Exception:
                citations = []
        result.append({
            "id": log.id,
            "role": log.role,
            "content": log.content,
            "citations": citations,
            "created_at": log.created_at.strftime("%I:%M %p") if log.created_at else ""
        })
    return result


# 5. POST /api/chat - Accepts user message, returns mocked AI streaming response with citations
@app.post("/api/chat")
async def chat_with_copilot(req: schemas.ChatRequest, db: Session = Depends(get_db)):
    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Save user message to database
    user_entry = models.ChatLog(
        role="user",
        content=user_text,
        citations=None
    )
    db.add(user_entry)
    db.commit()

    # Determine dynamic contextual clinical response based on user inquiry
    lower_query = user_text.lower()
    
    citations = []
    if "heart" in lower_query or "rate" in lower_query or "pulse" in lower_query or "bpm" in lower_query:
        answer_text = (
            "Your resting heart rate has climbed consistently from 69 to 78 bpm over the past 8 days. "
            "When cross-referenced with your bloodwork, your high-sensitivity CRP is currently 3.4 mg/L, "
            "suggesting subclinical inflammatory stress or immune activation rather than an isolated cardiovascular anomaly. "
            "I recommend prioritizing 8 hours of restorative rest tonight, maintaining adequate hydration, and monitoring if temperature increases beyond 37.1°C."
        )
        citations = [
            {"source": "Vitals Trend (Oct 03-11)", "detail": "RHR: 69 -> 78 bpm (+13% elevation)", "relevance": "Wearable Sensor Stream"},
            {"source": "Labcorp Panel (Sep 28)", "detail": "hs-CRP: 3.4 mg/L (Ref < 1.0)", "relevance": "Systemic Inflammation Biomarker"}
        ]
    elif "sleep" in lower_query or "tired" in lower_query or "fatigue" in lower_query or "insomnia" in lower_query:
        answer_text = (
            "Your sleep duration has dropped to an average of 5.7 hours, which is well below your baseline range of 7.0–9.0 hours. "
            "This sleep debt exacerbates sympathetic nervous tone, directly driving the 8-day resting heart rate rise to 78 bpm. "
            "Consider taking your prescribed Magnesium Glycinate (200 mg) approximately 30 minutes before sleep, and avoid blue-light exposure 45 minutes prior to bedtime."
        )
        citations = [
            {"source": "Sleep Biometrics", "detail": "5.7 hours recorded (Deficit of 1.3-3.3 hours)", "relevance": "Recovery Metric"},
            {"source": "Care Protocol", "detail": "Magnesium Glycinate 200mg (Unchecked today)", "relevance": "Sleep architecture support"}
        ]
    elif "med" in lower_query or "drug" in lower_query or "pill" in lower_query or "stat" in lower_query:
        answer_text = (
            "Reviewing your care protocol: Metformin (500mg) and Vitamin D3 (2,000 IU) have been logged as taken. "
            "However, Atorvastatin (20mg) and Magnesium Glycinate (200mg) remain unchecked for this evening. "
            "Keeping up with Atorvastatin is essential given your latest LDL cholesterol level of 142 mg/dL."
        )
        citations = [
            {"source": "Medication Protocol", "detail": "Atorvastatin 20mg pending for evening", "relevance": "Adherence Checklist"},
            {"source": "Quest Labs (Oct 04)", "detail": "LDL-C: 142 mg/dL (Ref < 100 mg/dL)", "relevance": "Target Biomarker"}
        ]
    elif "lab" in lower_query or "report" in lower_query or "cholesterol" in lower_query or "glucose" in lower_query or "sugar" in lower_query:
        answer_text = (
            "In your latest lab report from Quest Diagnostics, we identified two key out-of-range biomarkers: "
            "LDL Cholesterol is at 142 mg/dL (recommended < 100 mg/dL) and Fasting Glucose is at 106 mg/dL (HbA1c: 5.8%). "
            "On the positive side, your kidney filtration rate (eGFR: 96 mL/min) and liver enzymes (ALT: 24 U/L) are in excellent condition."
        )
        citations = [
            {"source": "Quest Diagnostics (Oct 04)", "detail": "LDL: 142 mg/dL, Fasting Glucose: 106 mg/dL", "relevance": "Out-of-range Biomarkers"},
            {"source": "Quest Diagnostics (Oct 04)", "detail": "HbA1c: 5.8% (Pre-diabetic threshold)", "relevance": "Glycemic Indicator"}
        ]
    else:
        answer_text = (
            f"I have reviewed your clinical profile regarding '{user_text}'. "
            "Your wearable sensors show an active alert: resting heart rate has elevated to 78 bpm across 8 consecutive days alongside restricted sleep (5.7h). "
            "Recent labs also highlight elevated hs-CRP (3.4 mg/L) and LDL (142 mg/dL). "
            "These combined indicators suggest physiological stress or an incipient recovery deficit. If fatigue or palpitation symptoms persist, a brief clinical review is recommended."
        )
        citations = [
            {"source": "Multi-Stream Synthesis", "detail": "RHR 78 bpm + hs-CRP 3.4 mg/L", "relevance": "Correlated Biomarker & Sensor Stream"},
            {"source": "Care Protocol", "detail": "2 out of 5 daily items logged", "relevance": "Active Regimen"}
        ]

    # Save assistant response to DB (done synchronously or when stream concludes)
    assistant_entry = models.ChatLog(
        role="assistant",
        content=answer_text,
        citations=json.dumps(citations)
    )
    db.add(assistant_entry)
    db.commit()
    db.refresh(assistant_entry)

    # SSE streaming generator
    async def stream_generator():
        words = answer_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            payload = {
                "chunk": chunk,
                "done": False,
                "citations": None
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.025)  # Realistic streaming delay

        # Final terminal chunk with citations
        final_payload = {
            "chunk": "",
            "done": True,
            "citations": citations,
            "message_id": assistant_entry.id
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


# 6. POST /api/documents/analyze - Upload/Analyze document, update DB, synthesize findings
@app.post("/api/documents/analyze")
def analyze_document(req: schemas.DocumentAnalyzeRequest, db: Session = Depends(get_db)):
    preset = req.preset_id or ("quest_panel" if "quest" in (req.title or "").lower() or req.document_type == "lab_report" else "jenkins_rx")
    
    patient = db.query(models.Patient).first()
    
    # Process according to document type / preset
    if preset == "jenkins_rx" or req.document_type == "prescription":
        # Add or update medication in care protocol
        existing_coq10 = db.query(models.Medication).filter(models.Medication.name.like("%CoQ10%")).first()
        if not existing_coq10:
            new_med = models.Medication(
                name="CoQ10 (Ubiquinol)",
                dosage="100 mg",
                timing="Morning",
                category="Prescription Support",
                taken_today=False
            )
            db.add(new_med)
        
        # Update patient guidance
        if patient and "CoQ10" not in (patient.active_conditions or ""):
            patient.active_conditions = (patient.active_conditions or "") + ", Prescribed CoQ10 Statin Adjunct"
        
        db.commit()
        
        return {
            "status": "success",
            "document_type": "prescription",
            "title": req.title or "Dr. Sarah Jenkins Rx Prescription Slip",
            "facility": "Mercy Health Medical Center",
            "date": datetime.utcnow().strftime("%d %b %Y"),
            "extracted_items": [
                {"name": "CoQ10 (Ubiquinol)", "dosage": "100 mg", "frequency": "Once daily with morning meal", "action": "Added to Care Protocol"},
                {"name": "Atorvastatin Calcium", "dosage": "20 mg", "frequency": "Nightly at bedtime", "action": "Confirmed Existing Protocol"},
                {"name": "Magnesium Glycinate", "dosage": "200 mg", "frequency": "Nightly 30 min before bed", "action": "Confirmed Existing Protocol"}
            ],
            "clinical_correlation": "CoQ10 initiated to mitigate potential statin-related muscular fatigue and support myocardial energy synthesis.",
            "dashboard_updates": {
                "medications_added": 1,
                "protocol_updated": True,
                "biomarkers_updated": 0
            }
        }
    
    elif preset == "holter_ecg" or req.document_type == "holter_ecg":
        # Holter ECG analysis
        if patient:
            patient.resting_heart_rate = "78 bpm"
            patient.flagged_guidance = "Holter confirms nocturnal sinus tachycardia spikes corresponding to brief awakenings. No sustained malignant arrhythmias."
            db.commit()
            
        return {
            "status": "success",
            "document_type": "holter_ecg",
            "title": req.title or "Ambulatory Holter & Rhythm Strip (24h)",
            "facility": "Mercy Trauma Center & Cardiology",
            "date": datetime.utcnow().strftime("%d %b %Y"),
            "extracted_items": [
                {"name": "Average 24h Heart Rate", "value": "74 bpm", "range": "60 - 85 bpm", "status": "Normal"},
                {"name": "Peak Nocturnal Pulse", "value": "91 bpm", "range": "< 80 bpm during sleep", "status": "Elevated Arousal"},
                {"name": "Arrhythmia Burden (PVCs/PACs)", "value": "< 0.4%", "range": "< 1.0%", "status": "Benign"}
            ],
            "clinical_correlation": "Confirms the 8-day resting heart rate rise seen on wearables stems from nighttime autonomic arousal rather than structural cardiomyopathy.",
            "dashboard_updates": {
                "medications_added": 0,
                "protocol_updated": True,
                "biomarkers_updated": 3
            }
        }

    else:
        # Default: Comprehensive Lab Panel (Quest Diagnostics)
        new_report = models.DiagnosticReport(
            patient_id=patient.id if patient else 1,
            title=req.title or "Quest Comprehensive Metabolic & Lipid Panel",
            date=datetime.utcnow().strftime("%d %b %Y"),
            facility="Quest Diagnostics Clinical Lab",
            category="Blood Chemistry & Lipids",
            summary="Elevated Fasting LDL-C (142 mg/dL) and High-Sensitivity CRP (3.4 mg/L) detected alongside normal renal and liver function."
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        # Add biomarkers
        b1 = models.Biomarker(
            report_id=new_report.id,
            name="hs-CRP (High-Sensitivity)",
            value="3.4",
            unit="mg/L",
            reference_range="< 1.0 mg/L",
            status="out_of_range",
            interpretation="Elevated inflammatory marker; correlates with physiological strain and 8-day resting heart rate rise."
        )
        b2 = models.Biomarker(
            report_id=new_report.id,
            name="LDL Cholesterol (Direct)",
            value="142",
            unit="mg/dL",
            reference_range="< 100 mg/dL",
            status="out_of_range",
            interpretation="Moderate elevation. Primary focus for evening lipid management protocol."
        )
        b3 = models.Biomarker(
            report_id=new_report.id,
            name="Fasting Glucose",
            value="106",
            unit="mg/dL",
            reference_range="70 - 99 mg/dL",
            status="out_of_range",
            interpretation="Impaired fasting glucose threshold; continue metabolic monitoring."
        )
        b4 = models.Biomarker(
            report_id=new_report.id,
            name="eGFR (Creatinine-based)",
            value="96",
            unit="mL/min",
            reference_range="> 60 mL/min",
            status="normal",
            interpretation="Optimal renal filtration capacity."
        )
        b5 = models.Biomarker(
            report_id=new_report.id,
            name="ALT (Alanine Aminotransferase)",
            value="24",
            unit="U/L",
            reference_range="7 - 35 U/L",
            status="normal",
            interpretation="Normal hepatic integrity."
        )
        db.add_all([b1, b2, b3, b4, b5])
        db.commit()
        
        return {
            "status": "success",
            "document_type": "lab_report",
            "title": new_report.title,
            "facility": new_report.facility,
            "date": new_report.date,
            "extracted_items": [
                {"name": "hs-CRP (Inflammation)", "value": "3.4 mg/L", "reference": "< 1.0 mg/L", "status": "High (Out of Range)"},
                {"name": "LDL Cholesterol", "value": "142 mg/dL", "reference": "< 100 mg/dL", "status": "Elevated (Out of Range)"},
                {"name": "Fasting Glucose", "value": "106 mg/dL", "reference": "70-99 mg/dL", "status": "Borderline"},
                {"name": "eGFR (Kidney)", "value": "96 mL/min", "reference": "> 60 mL/min", "status": "Optimal Normal"},
                {"name": "ALT (Liver)", "value": "24 U/L", "reference": "7-35 U/L", "status": "Optimal Normal"}
            ],
            "clinical_correlation": "Cross-referenced with 90-day wearable baseline: hs-CRP of 3.4 mg/L validates the 8-day resting heart rate rise (+9 bpm) as an active systemic immune or recovery load.",
            "dashboard_updates": {
                "report_id": new_report.id,
                "biomarkers_added": 5,
                "out_of_range_count": 3
            }
        }
