from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    user_id: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    role: str


class TriageStartRequest(BaseModel):
    name: str = "匿名患者"
    age: int = Field(30, ge=0, le=120)
    gender: str = "未知"
    chief_complaint: str = Field(min_length=1)
    phone: str = ""


class TriageStartResponse(BaseModel):
    patient_id: int
    conversation_id: int
    message: str


class TriageAnswerRequest(BaseModel):
    conversation_id: int
    message: str = Field(min_length=1)


class TriageAnswerResponse(BaseModel):
    message: str
    can_complete: bool
    user_message_count: int


class TriageCompleteRequest(BaseModel):
    patient_id: int


class TriageResult(BaseModel):
    patient_id: int
    tier: str
    score: float
    department: str
    department_id: int
    confidence: float
    reasons: list[str]
    recommendation: str
    next_steps: list[str]
    disclaimer: str


class AppointmentCreate(BaseModel):
    patient_id: int
    department_id: int
    doctor_id: int | None = None
    notes: str = ""


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: int | None
    department_id: int
    scheduled_time: datetime
    status: str
    notes: str
    doctor_name: str | None = None
    department_name: str | None = None
    patient_name: str | None = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str
    avg_wait_minutes: int
    load: int
    capacity: int


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: str
    phone: str
    chief_complaint: str
    symptoms: list[str]
    allergies: str
    medications: str
    medical_history: str
    risk_level: str
    risk_score: float
    triage_reason: str
    department_id: int | None
    status: str
    created_at: datetime
    department_name: str | None = None


class KnowledgeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    content: str
    source: str
    tags: list[str]
    created_at: datetime


class KnowledgeCreate(BaseModel):
    title: str
    category: str
    content: str
    source: str = ""
    tags: list[str] = []


class KnowledgeHit(BaseModel):
    id: int
    title: str
    category: str
    content: str
    source: str
    score: float


class SummaryOut(BaseModel):
    patient_id: int
    summary: str
    citations: list[dict[str, Any]]
    disclaimer: str


class SOAPOut(BaseModel):
    patient_id: int
    subjective: str
    objective: str
    assessment: str
    plan: str
    citations: list[dict[str, Any]]
    disclaimer: str


class FollowupOut(BaseModel):
    patient_id: int
    plan: str
    citations: list[dict[str, Any]]
    disclaimer: str


class StatusUpdate(BaseModel):
    status: str


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor: str
    action: str
    target_type: str
    target_id: int | None
    detail: dict[str, Any]
    created_at: datetime


class AlertOut(BaseModel):
    patient_id: int
    patient_name: str
    age: int
    chief_complaint: str
    risk_level: str
    status: str
    department_name: str | None = None


class DepartmentStatus(BaseModel):
    id: int
    name: str
    load: int
    avg_wait_minutes: int
    waiting_count: int


class DashboardOut(BaseModel):
    waiting_count: int
    triage_count: int
    scheduled_count: int
    red_alert_count: int
    risk_distribution: list[dict[str, Any]]
    department_status: list[DepartmentStatus]
    queue: list[PatientOut]
    alerts: list[AlertOut]
    recent_audit: list[AuditOut]


class SystemStatusOut(BaseModel):
    provider_mode: str
    model_name: str
    database_url: str
    api_base_url: str
    knowledge_count: int
    patient_count: int
