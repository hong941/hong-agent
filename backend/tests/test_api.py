from fastapi.testclient import TestClient


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_triage_and_appointment_flow(client):
    token = _login(client, "patient_demo", "demo123")
    start = client.post(
        "/api/triage/start",
        headers=_headers(token),
        json={
            "name": "接口测试患者",
            "age": 52,
            "gender": "男",
            "chief_complaint": "突发胸痛伴呼吸困难",
        },
    )
    assert start.status_code == 200
    data = start.json()

    answer = client.post(
        "/api/triage/answer",
        headers=_headers(token),
        json={
            "conversation_id": data["conversation_id"],
            "message": "持续 40 分钟，伴大汗，无药物过敏史",
        },
    )
    assert answer.status_code == 200
    assert answer.json()["can_complete"] is True

    complete = client.post(
        "/api/triage/complete",
        headers=_headers(token),
        json={"patient_id": data["patient_id"]},
    )
    assert complete.status_code == 200
    assert complete.json()["tier"] == "red"
    assert complete.json()["department"] == "急诊科"

    appointment = client.post(
        "/api/appointments",
        headers=_headers(token),
        json={
            "patient_id": data["patient_id"],
            "department_id": complete.json()["department_id"],
        },
    )
    assert appointment.status_code == 200
    assert appointment.json()["status"] == "booked"


def test_doctor_summary_requires_staff(client):
    patient_token = _login(client, "patient_demo", "demo123")
    denied = client.get("/api/patients/1/summary", headers=_headers(patient_token))
    assert denied.status_code == 403

    doctor_token = _login(client, "doctor_zhang", "doctor123")
    summary = client.get("/api/patients/1/summary", headers=_headers(doctor_token))
    assert summary.status_code == 200
    assert "主诉" in summary.json()["summary"]
    assert summary.json()["citations"]
