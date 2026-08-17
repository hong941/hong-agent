import json
from typing import Any

from sqlalchemy.orm import Session

from ..models import Department, Patient, TriageConversation
from .provider import MockProvider, get_provider
from .rag import KnowledgeService

DISCLAIMER = "本内容由 AI 辅助生成，仅供医疗人员参考，不替代医生专业判断。"


def _citations(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": hit["title"],
            "source": hit["source"],
            "category": hit["category"],
            "score": hit["score"],
        }
        for hit in hits
    ]


def _patient_payload(patient: Patient) -> dict[str, Any]:
    return {
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "chief_complaint": patient.chief_complaint,
        "symptoms": patient.symptoms or [],
        "allergies": patient.allergies,
        "medications": patient.medications,
        "medical_history": patient.medical_history,
        "risk_level": patient.risk_level,
        "status": patient.status,
    }


def _hits_text(hits: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- {hit['title']}（来源：{hit['source']}）\n  {hit['content']}"
        for hit in hits
    )


def build_summary(
    db: Session, patient: Patient, conversation: TriageConversation | None
) -> dict[str, Any]:
    hits = KnowledgeService(db).search_for_patient(patient, conversation)
    provider = get_provider()
    if not isinstance(provider, MockProvider):
        prompt = (
            "你是医院病历助手。请用简洁中文生成患者就诊摘要，必须包含：基本信息、主诉、"
            "风险等级、关键症状、病史、过敏史、用药情况和下一步建议。"
            "只输出摘要正文，不要输出额外解释。\n\n"
            f"患者信息：{json.dumps(_patient_payload(patient), ensure_ascii=False)}\n\n"
            f"可参考知识：{_hits_text(hits)}"
        )
        try:
            content = provider.complete(
                [{"role": "user", "content": prompt}], temperature=0.2
            )
            return {
                "patient_id": patient.id,
                "summary": content,
                "citations": _citations(hits),
                "disclaimer": DISCLAIMER,
            }
        except Exception:
            pass

    symptom_text = "、".join(patient.symptoms or []) or patient.chief_complaint
    summary = (
        f"{patient.name}，{patient.age} 岁，{patient.gender}。主诉：{patient.chief_complaint}。"
        f"风险分级：{patient.risk_level}。症状要点：{symptom_text}。"
        f"既往史：{patient.medical_history or '未记录'}。过敏史：{patient.allergies or '未记录'}。"
        f"长期用药：{patient.medications or '未记录'}。\n"
    )
    if hits:
        summary += "知识库建议：\n"
        for hit in hits[:3]:
            summary += f"- {hit['title']}：{hit['content'][:120]}\n"
    return {
        "patient_id": patient.id,
        "summary": summary.strip(),
        "citations": _citations(hits),
        "disclaimer": DISCLAIMER,
    }


def build_soap(
    db: Session, patient: Patient, conversation: TriageConversation | None
) -> dict[str, Any]:
    hits = KnowledgeService(db).search_for_patient(patient, conversation)
    department = db.get(Department, patient.department_id) if patient.department_id else None
    subjective = (
        f"主诉：{patient.chief_complaint}。患者自述症状：{'；'.join(patient.symptoms or [])}。"
        f"既往史：{patient.medical_history or '未记录'}。"
    )
    objective = (
        f"风险分级：{patient.risk_level}，分诊评分：{patient.risk_score}。"
        f"过敏史：{patient.allergies or '未记录'}；长期用药：{patient.medications or '未记录'}。"
    )
    assessment = "根据现有信息初步判断需结合病史与体征进一步评估。\n"
    if hits:
        assessment += "可参考知识：\n"
        for hit in hits[:3]:
            assessment += f"- {hit['title']}：{hit['content'][:120]}\n"
    plan = (
        f"建议就诊科室：{department.name if department else '待定'}。\n"
        "1. 由医生完成补充问诊和体格检查；\n"
        "2. 根据评估结果安排必要的检验检查；\n"
        "3. 制定随访计划并交代复诊指征。"
    )
    return {
        "patient_id": patient.id,
        "subjective": subjective,
        "objective": objective,
        "assessment": assessment,
        "plan": plan,
        "citations": _citations(hits),
        "disclaimer": DISCLAIMER,
    }


def build_followup(
    db: Session, patient: Patient, conversation: TriageConversation | None
) -> dict[str, Any]:
    hits = KnowledgeService(db).search_for_patient(patient, conversation)
    department = db.get(Department, patient.department_id) if patient.department_id else None
    plan = (
        f"患者 {patient.name} 本次就诊后随访计划（{department.name if department else '待定'}）：\n"
        "1. 按医嘱完成用药或检查，记录症状变化；\n"
        "2. 如出现胸痛、呼吸困难、意识改变等加重症状，立即前往急诊；\n"
        "3. 按约定时间复诊，复查相关指标；\n"
        "4. 保持健康生活方式，控制慢病风险因素。"
    )
    return {
        "patient_id": patient.id,
        "plan": plan,
        "citations": _citations(hits),
        "disclaimer": DISCLAIMER,
    }
