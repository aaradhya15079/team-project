from pydantic import BaseModel
from typing import List, Optional, Any

class VitalItem(BaseModel):
    name: str
    value: str
    status: str
    trend: str
    is_alert: bool

class PatientVitalsResponse(BaseModel):
    id: int
    name: str
    greeting_date: str
    flagged_pattern: dict
    vitals: List[VitalItem]
    active_conditions: List[str]

    class Config:
        from_attributes = True

class MedicationBase(BaseModel):
    name: str
    dosage: str
    timing: Optional[str] = "Morning"
    category: Optional[str] = "Prescription"
    taken_today: bool = False

class MedicationResponse(MedicationBase):
    id: int

    class Config:
        from_attributes = True

class BiomarkerResponse(BaseModel):
    id: int
    name: str
    value: str
    unit: str
    reference_range: str
    status: str
    interpretation: Optional[str] = None

    class Config:
        from_attributes = True

class DiagnosticReportResponse(BaseModel):
    id: int
    title: str
    date: str
    facility: str
    category: str
    summary: Optional[str] = None
    biomarkers: List[BiomarkerResponse]

    class Config:
        from_attributes = True

class ReportsSummaryResponse(BaseModel):
    reports: List[DiagnosticReportResponse]
    out_of_range_biomarkers: List[BiomarkerResponse]
    total_biomarkers: int

class ChatRequest(BaseModel):
    message: str

class Citation(BaseModel):
    source: str
    detail: str
    relevance: str

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: Optional[List[Citation]] = []
    created_at: str

class DocumentAnalyzeRequest(BaseModel):
    title: Optional[str] = "Clinical Document"
    document_type: Optional[str] = "lab_report" # 'lab_report', 'prescription', 'holter_ecg'
    filename: Optional[str] = "document.pdf"
    raw_text: Optional[str] = None
    preset_id: Optional[str] = None
