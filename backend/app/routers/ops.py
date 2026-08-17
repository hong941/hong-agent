from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, Department, Patient, User
from ..schemas import (
    AlertOut,
    AuditOut,
    DashboardOut,
    DepartmentStatus,
)
from ..security import require_roles
from ..services.audit import write_audit
from .patients import patient_to_out

router = APIRouter(prefix="/api/ops", tags=["ops"])

staff_dependency = require_roles("doctor", "nurse", "admin")
TIER_RANK = {"red": 0, "yellow": 1, "green": 2}


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(staff_dependency)):
    waiting_count = db.query(Patient).filter(Patient.status == "waiting").count()
    triage_count = db.query(Patient).filter(Patient.status == "triage").count()
    scheduled_count = db.query(Patient).filter(Patient.status == "scheduled").count()
    red_alert_count = db.query(Patient).filter(Patient.risk_level == "red").count()

    risk_distribution = [
        {"tier": tier, "count": db.query(Patient).filter(Patient.risk_level == tier).count()}
        for tier in ["red", "yellow", "green"]
    ]

    departments = db.query(Department).order_by(Department.id).all()
    department_status = []
    for department in departments:
        waiting = (
            db.query(Patient)
            .filter(
                Patient.department_id == department.id,
                Patient.status == "waiting",
            )
            .count()
        )
        department_status.append(
            DepartmentStatus(
                id=department.id,
                name=department.name,
                load=department.load,
                avg_wait_minutes=department.avg_wait_minutes,
                waiting_count=waiting,
            )
        )

    patients = db.query(Patient).all()
    queue = [
        patient_to_out(patient, db)
        for patient in sorted(
            patients,
            key=lambda p: (
                TIER_RANK.get(p.risk_level, 3),
                -(p.risk_score or 0),
            ),
        )
        if patient.status in ("waiting", "in_consultation", "scheduled")
    ][:12]

    alerts = []
    for patient in patients:
        if patient.risk_level == "red":
            department = (
                db.get(Department, patient.department_id)
                if patient.department_id
                else None
            )
            alerts.append(
                AlertOut(
                    patient_id=patient.id,
                    patient_name=patient.name,
                    age=patient.age,
                    chief_complaint=patient.chief_complaint,
                    risk_level=patient.risk_level,
                    status=patient.status,
                    department_name=department.name if department else None,
                )
            )

    recent_audit = (
        db.query(AuditLog).order_by(AuditLog.id.desc()).limit(10).all()
    )
    return DashboardOut(
        waiting_count=waiting_count,
        triage_count=triage_count,
        scheduled_count=scheduled_count,
        red_alert_count=red_alert_count,
        risk_distribution=risk_distribution,
        department_status=department_status,
        queue=queue,
        alerts=alerts,
        recent_audit=[AuditOut.model_validate(item) for item in recent_audit],
    )


@router.post("/patients/{patient_id}/handover")
def nurse_handover(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("nurse", "admin")),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    if patient.status == "triage":
        patient.status = "waiting"
    write_audit(
        db,
        actor=user.username,
        action="nurse_handover",
        target_type="patient",
        target_id=patient.id,
        detail={"risk_level": patient.risk_level},
    )
    db.commit()
    return {"ok": True, "message": "已由护士接管并标记为候诊"}


@router.get("/audit", response_model=list[AuditOut])
def list_audit(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(50).all()
    return [AuditOut.model_validate(item) for item in logs]
