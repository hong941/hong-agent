import json
from pathlib import Path

from app.ai.triage import evaluate_rule
from app.database import SessionLocal
from app.models import Patient, TriageConversation

CASES = json.loads(
    (Path(__file__).resolve().parents[1] / "eval" / "eval_cases.json").read_text(
        encoding="utf-8"
    )
)


def test_rule_eval_accuracy_threshold(client):
    db = SessionLocal()
    correct = 0
    for case in CASES:
        patient = Patient(
            name="评测患者",
            age=case["age"],
            gender=case["gender"],
            chief_complaint=case["chief_complaint"],
            symptoms=case.get("symptoms", []),
            allergies=case.get("allergies", ""),
            medications=case.get("medications", ""),
            medical_history=case.get("medical_history", ""),
        )
        conversation = TriageConversation(
            messages=[{"role": "user", "content": case["chief_complaint"]}]
        )
        result = evaluate_rule(db, patient, conversation)
        if result["tier"] == case["expected_tier"]:
            correct += 1
    db.close()
    assert correct / len(CASES) >= 0.70
