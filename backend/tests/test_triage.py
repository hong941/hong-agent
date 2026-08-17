from app.ai.rag import KnowledgeService
from app.ai.triage import evaluate_rule
from app.database import SessionLocal
from app.models import Department, Patient, TriageConversation


def test_chest_pain_escalates_to_red(client):
    db = SessionLocal()
    patient = (
        db.query(Patient)
        .filter(Patient.chief_complaint.contains("胸痛"))
        .first()
    )
    conversation = (
        db.query(TriageConversation)
        .filter(TriageConversation.patient_id == patient.id)
        .first()
    )
    result = evaluate_rule(db, patient, conversation)
    db.close()
    assert result["tier"] == "red"


def test_routine_review_is_green(client):
    db = SessionLocal()
    department = db.query(Department).filter(Department.name == "内科").first()
    patient = Patient(
        name="测试患者",
        age=40,
        gender="女",
        chief_complaint="常规体检咨询",
        department_id=department.id,
        status="triage",
    )
    db.add(patient)
    db.flush()
    result = evaluate_rule(db, patient, None)
    db.close()
    assert result["tier"] == "green"


def test_knowledge_search_returns_citations(client):
    db = SessionLocal()
    hits = KnowledgeService(db).search("胸痛 急诊", top_k=3)
    db.close()
    assert hits
    assert any("胸痛" in hit["title"] for hit in hits)
