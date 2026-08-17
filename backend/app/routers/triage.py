from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai.triage import run_triage
from ..database import get_db
from ..models import Appointment, Department, Patient, TriageConversation, User
from ..schemas import (
    AppointmentCreate,
    AppointmentOut,
    TriageAnswerRequest,
    TriageAnswerResponse,
    TriageCompleteRequest,
    TriageResult,
    TriageStartRequest,
    TriageStartResponse,
)
from ..security import get_current_user
from ..services.audit import write_audit

router = APIRouter(prefix="/api", tags=["triage"])


@router.post("/triage/start", response_model=TriageStartResponse)
def start_triage(
    payload: TriageStartRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    default_department = db.query(Department).filter(Department.name == "内科").first()
    patient = Patient(
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        phone=payload.phone,
        chief_complaint=payload.chief_complaint,
        status="triage",
        department_id=default_department.id if default_department else None,
    )
    db.add(patient)
    db.flush()
    conversation = TriageConversation(
        patient_id=patient.id,
        messages=[
            {
                "role": "assistant",
                "content": "您好，请先用一句话描述您最主要的症状或就诊原因。",
            },
            {"role": "user", "content": payload.chief_complaint},
            {
                "role": "assistant",
                "content": "已记录。请补充症状持续多久、严重程度、伴随症状，以及是否有过敏史或长期用药。",
            },
        ],
    )
    db.add(conversation)
    write_audit(
        db,
        actor=user.username,
        action="triage_start",
        target_type="patient",
        target_id=patient.id,
        detail={"chief_complaint": payload.chief_complaint},
    )
    db.commit()
    return TriageStartResponse(
        patient_id=patient.id,
        conversation_id=conversation.id,
        message="已记录。请补充症状持续多久、严重程度、伴随症状，以及是否有过敏史或长期用药。",
    )


@router.post("/triage/answer", response_model=TriageAnswerResponse)
def answer_triage(
    payload: TriageAnswerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = db.get(TriageConversation, payload.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="预问诊会话不存在")
    conversation.messages = list(conversation.messages or [])
    conversation.messages.append({"role": "user", "content": payload.message})
    user_count = sum(1 for m in conversation.messages if m.get("role") == "user")
    if user_count >= 2:
        reply = "信息已补充完整，可点击“完成预问诊”获取风险分级和科室建议。"
    else:
        reply = "已记录。请再补充症状持续时间和过敏史或长期用药情况。"
    conversation.messages.append({"role": "assistant", "content": reply})
    write_audit(
        db,
        actor=user.username,
        action="triage_answer",
        target_type="patient",
        target_id=conversation.patient_id,
    )
    db.commit()
    return TriageAnswerResponse(
        message=reply,
        can_complete=user_count >= 2,
        user_message_count=user_count,
    )


@router.post("/triage/complete", response_model=TriageResult)
def complete_triage(
    payload: TriageCompleteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    patient = db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    conversation = db.query(TriageConversation).filter(
        TriageConversation.patient_id == patient.id
    ).first()
    result = run_triage(db, patient, conversation)
    patient.risk_level = result["tier"]
    patient.risk_score = result["score"]
    patient.triage_reason = "；".join(result["reasons"])
    patient.department_id = result["department_id"]
    patient.status = "waiting"
    if conversation:
        conversation.completed = 1
    write_audit(
        db,
        actor=user.username,
        action="triage_complete",
        target_type="patient",
        target_id=patient.id,
        detail={
            "tier": result["tier"],
            "score": result["score"],
            "department": result["department"],
        },
    )
    db.commit()
    return TriageResult(
        patient_id=patient.id,
        tier=result["tier"],
        score=result["score"],
        department=result["department"],
        department_id=result["department_id"],
        confidence=result["confidence"],
        reasons=result["reasons"],
        recommendation=result["recommendation"],
        next_steps=result["next_steps"],
        disclaimer=result["disclaimer"],
    )


@router.post("/appointments", response_model=AppointmentOut)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    patient = db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    department = db.get(Department, payload.department_id)
    if not department:
        raise HTTPException(status_code=404, detail="科室不存在")
    doctor = None
    if payload.doctor_id:
        doctor = db.get(User, payload.doctor_id)
    if doctor is None:
        doctor = (
            db.query(User)
            .filter(User.role == "doctor", User.department_id == department.id)
            .first()
        )
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id if doctor else None,
        department_id=department.id,
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
        status="booked",
        notes=payload.notes,
    )
    db.add(appointment)
    patient.status = "scheduled"
    write_audit(
        db,
        actor=user.username,
        action="appointment_book",
        target_type="appointment",
        target_id=appointment.id,
        detail={"patient_id": patient.id, "department": department.name},
    )
    db.commit()
    db.refresh(appointment)
    return AppointmentOut(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        department_id=appointment.department_id,
        scheduled_time=appointment.scheduled_time,
        status=appointment.status,
        notes=appointment.notes,
        doctor_name=doctor.name if doctor else None,
        department_name=department.name,
        patient_name=patient.name,
    )
