from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..ai.copilot import build_followup, build_soap, build_summary
from ..ai.rag import KnowledgeService
from ..database import get_db
from ..models import Department, Patient, TriageConversation, User
from ..schemas import (
    FollowupOut,
    KnowledgeHit,
    PatientOut,
    SOAPOut,
    StatusUpdate,
    SummaryOut,
)
from ..security import get_current_user, require_roles
from ..services.audit import write_audit

router = APIRouter(prefix="/api", tags=["patients"])

staff_dependency = require_roles("doctor", "nurse", "admin")


def patient_to_out(patient: Patient, db: Session) -> PatientOut:
    department = db.get(Department, patient.department_id) if patient.department_id else None
    return PatientOut(
        id=patient.id,
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        phone=patient.phone,
        chief_complaint=patient.chief_complaint,
        symptoms=patient.symptoms or [],
        allergies=patient.allergies,
        medications=patient.medications,
        medical_history=patient.medical_history,
        risk_level=patient.risk_level,
        risk_score=patient.risk_score,
        triage_reason=patient.triage_reason,
        department_id=patient.department_id,
        status=patient.status,
        created_at=patient.created_at,
        department_name=department.name if department else None,
    )


@router.get("/patients", response_model=list[PatientOut])
def list_patients(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(staff_dependency),
):
    query = db.query(Patient)
    if status:
        query = query.filter(Patient.status == status)
    patients = query.order_by(Patient.created_at.desc()).all()
    return [patient_to_out(patient, db) for patient in patients]


@router.get("/patients/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(staff_dependency),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    return patient_to_out(patient, db)


@router.get("/patients/{patient_id}/conversation")
def get_conversation(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(staff_dependency),
):
    conversation = (
        db.query(TriageConversation)
        .filter(TriageConversation.patient_id == patient_id)
        .first()
    )
    return {"messages": conversation.messages if conversation else []}


@router.get("/patients/{patient_id}/summary", response_model=SummaryOut)
def get_summary(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(staff_dependency),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    conversation = db.query(TriageConversation).filter(
        TriageConversation.patient_id == patient.id
    ).first()
    result = build_summary(db, patient, conversation)
    write_audit(
        db,
        actor=user.username,
        action="ai_summary",
        target_type="patient",
        target_id=patient.id,
    )
    db.commit()
    return result


@router.post("/patients/{patient_id}/soap", response_model=SOAPOut)
def generate_soap(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(staff_dependency),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    conversation = db.query(TriageConversation).filter(
        TriageConversation.patient_id == patient.id
    ).first()
    result = build_soap(db, patient, conversation)
    write_audit(
        db,
        actor=user.username,
        action="ai_soap_draft",
        target_type="patient",
        target_id=patient.id,
    )
    db.commit()
    return result


@router.get("/patients/{patient_id}/followup", response_model=FollowupOut)
def get_followup(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(staff_dependency),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    conversation = db.query(TriageConversation).filter(
        TriageConversation.patient_id == patient.id
    ).first()
    result = build_followup(db, patient, conversation)
    write_audit(
        db,
        actor=user.username,
        action="ai_followup",
        target_type="patient",
        target_id=patient.id,
    )
    db.commit()
    return result


@router.post("/patients/{patient_id}/status")
def update_status(
    patient_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(staff_dependency),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    patient.status = payload.status
    write_audit(
        db,
        actor=user.username,
        action="patient_status_update",
        target_type="patient",
        target_id=patient.id,
        detail={"status": payload.status},
    )
    db.commit()
    return {"ok": True, "status": patient.status}


@router.get("/knowledge/search", response_model=list[KnowledgeHit])
def search_knowledge(
    q: str = Query(default="", min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return KnowledgeService(db).search(q, top_k=6)
