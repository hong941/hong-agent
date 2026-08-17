import json
import re
from typing import Any

from sqlalchemy.orm import Session

from ..models import Department, Patient, TriageConversation
from .provider import MockProvider, get_provider

TIER_ORDER = {"green": 0, "yellow": 1, "red": 2}

RED_KEYWORDS = [
    "胸痛",
    "胸口痛",
    "呼吸困难",
    "喘不上气",
    "意识不清",
    "昏迷",
    "大出血",
    "抽搐",
    "剧烈腹痛",
    "剧烈头痛",
    "窒息",
    "突发偏瘫",
    "说不出话",
    "39.5",
    "40度",
    "过敏性休克",
]

YELLOW_KEYWORDS = [
    "发热",
    "发烧",
    "头晕",
    "头痛",
    "心悸",
    "呕吐",
    "腹泻",
    "腹痛",
    "外伤",
    "咳嗽",
    "乏力",
    "胸闷",
    "血糖",
    "血压",
    "疼痛",
    "肿胀",
    "皮疹",
    "失眠",
    "焦虑",
    "呼吸困难",
]

GREEN_KEYWORDS = ["复查", "复诊", "体检", "取药", "开药", "疫苗", "咨询", "慢性病", "常规", "睡眠"]
SOFT_YELLOW_KEYWORDS = ["血糖", "血压", "失眠"]

DEPARTMENT_KEYWORDS = [
    (["换药", "伤口", "术后", "外伤", "利器", "刺伤"], "外科"),
    (["胸痛", "胸闷", "心慌", "心悸", "血压", "心脏"], "心内科"),
    (["头痛", "头晕", "偏瘫", "意识", "言语不清", "神经"], "神经内科"),
    (["骨折", "扭伤", "外伤", "关节", "腰疼", "腰", "颈椎", "膝盖", "肩颈", "颈腰", "跌倒", "髋部"], "骨科"),
    (["皮疹", "瘙痒", "皮肤", "湿疹", "痤疮"], "皮肤科"),
    (["耳", "鼻塞", "流涕", "鼻", "喉", "咽", "耳鸣", "听力"], "耳鼻喉科"),
    (["眼", "视力", "结膜", "干眼", "视疲劳", "近视"], "眼科"),
    (["孕", "产", "月经", "妇科", "白带", "备孕", "胎动"], "妇产科"),
    (["儿童", "宝宝", "小儿", "幼儿", "疫苗", "生长发育"], "儿科"),
    (["糖尿病", "血糖", "内分泌"], "内科"),
    (["发热", "发烧", "咳嗽", "感冒", "腹泻", "腹痛", "乏力", "呕吐", "胃炎", "胃痛", "呕血", "痰中带血"], "内科"),
    (["失眠", "睡眠", "焦虑", "抑郁", "心理"], "心理科"),
    (["体检", "复诊", "开药", "取药", "咨询"], "内科"),
]


def _tier_to_chinese(tier: str) -> str:
    return {"red": "高风险", "yellow": "中风险", "green": "低风险"}.get(tier, "待评估")


def build_combined_text(
    patient: Patient, conversation: TriageConversation | None
) -> str:
    parts = [patient.chief_complaint or ""]
    parts.extend(patient.symptoms or [])
    if patient.medical_history:
        parts.append(patient.medical_history)
    if conversation:
        user_messages = [
            item.get("content", "")
            for item in (conversation.messages or [])
            if item.get("role") == "user"
        ]
        parts.extend(user_messages)
    return " ".join(parts)


def build_department_text(
    patient: Patient, conversation: TriageConversation | None
) -> str:
    parts = [patient.chief_complaint or ""]
    parts.extend(patient.symptoms or [])
    if conversation:
        user_messages = [
            item.get("content", "")
            for item in (conversation.messages or [])
            if item.get("role") == "user"
        ]
        parts.extend(user_messages)
    return " ".join(parts)


def _pick_department(
    db: Session, patient: Patient, conversation: TriageConversation | None
) -> Department:
    text = build_department_text(patient, conversation)
    for keywords, name in DEPARTMENT_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            department = db.query(Department).filter(Department.name == name).first()
            if department:
                return department
    internal = db.query(Department).filter(Department.name == "内科").first()
    if internal:
        return internal
    default = db.query(Department).first()
    if default:
        return default
    raise ValueError("系统尚未初始化科室数据")


def evaluate_rule(
    db: Session, patient: Patient, conversation: TriageConversation | None
) -> dict[str, Any]:
    text = build_combined_text(patient, conversation)
    normalized_text = (
        text.replace("无发热", "")
        .replace("不发热", "")
        .replace("没有发热", "")
        .replace("无头痛", "")
        .replace("不头痛", "")
    )
    score = 0.0
    reasons: list[str] = []

    red_hits = [word for word in RED_KEYWORDS if word in normalized_text]
    if red_hits:
        score += 60
        reasons.append(f"检测到高危关键词：{'、'.join(red_hits[:3])}")

    yellow_hits = [
        word
        for word in YELLOW_KEYWORDS
        if word in normalized_text and word not in red_hits
    ]
    if yellow_hits:
        score += 20
        reasons.append(f"检测到需关注症状：{'、'.join(yellow_hits[:3])}")

    if any(word in text for word in GREEN_KEYWORDS) and score < 10:
        score += 5
        reasons.append("主诉为常规复诊或健康咨询")

    if any(word in text for word in GREEN_KEYWORDS):
        strong_yellow = [
            word for word in yellow_hits if word not in SOFT_YELLOW_KEYWORDS
        ]
        if not red_hits and not strong_yellow:
            score = min(score, 10)

    if patient.age is not None and patient.age < 3:
        score += 15
        reasons.append("婴幼儿人群，需优先评估")
    elif patient.age is not None and patient.age >= 70:
        score += 10
        reasons.append("高龄人群，需优先评估")

    if patient.medical_history:
        score += 5
        reasons.append("存在既往病史，需要医生结合病史判断")

    if score >= 50:
        tier = "red"
    elif score >= 20:
        tier = "yellow"
    else:
        tier = "green"

    department = _pick_department(db, patient, conversation)
    if tier == "red":
        emergency = db.query(Department).filter(Department.name == "急诊科").first()
        if emergency:
            department = emergency

    return {
        "tier": tier,
        "score": round(min(score, 100), 1),
        "department": department.name,
        "department_id": department.id,
        "reasons": reasons or ["未检测到明确高危信号，建议按普通流程就诊"],
        "confidence": 0.72 + min(0.18, len(text) / 200),
    }


def _escalate_if_needed(
    rule_result: dict[str, Any], model_result: dict[str, Any] | None
) -> dict[str, Any]:
    if not model_result or model_result.get("tier") not in TIER_ORDER:
        return rule_result
    model_tier = model_result["tier"]
    if TIER_ORDER[model_tier] > TIER_ORDER[rule_result["tier"]]:
        if model_tier != "red" and rule_result["tier"] != "yellow":
            return rule_result
        result = dict(rule_result)
        result["tier"] = model_tier
        result["reasons"] = [
            *rule_result["reasons"],
            f"模型复核升级：{model_result.get('reason', '')}",
        ]
        result["confidence"] = round(result["confidence"] * 0.9, 2)
        return result
    return rule_result


def _call_model_for_triage(
    provider, patient: Patient, conversation: TriageConversation | None
) -> dict[str, Any] | None:
    if isinstance(provider, MockProvider):
        return None
    text = build_combined_text(patient, conversation)
    prompt = (
        "你是医院预问诊分诊助手。请根据患者信息和对话判断风险等级。"
        '只输出 JSON：{"tier":"red|yellow|green","reason":"简要原因"}。\n\n'
        f"患者信息：\n{text}"
    )
    try:
        content = provider.complete(
            [{"role": "user", "content": prompt}], temperature=0
        )
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            return None
        parsed = json.loads(match.group(0))
        return {"tier": parsed.get("tier"), "reason": parsed.get("reason", "")}
    except Exception:
        return None


def run_triage(
    db: Session, patient: Patient, conversation: TriageConversation | None
) -> dict[str, Any]:
    provider = get_provider()
    rule_result = evaluate_rule(db, patient, conversation)
    model_result = _call_model_for_triage(provider, patient, conversation)
    result = _escalate_if_needed(rule_result, model_result)

    tier = result["tier"]
    if tier == "red":
        emergency = db.query(Department).filter(Department.name == "急诊科").first()
        if emergency:
            result["department"] = emergency.name
            result["department_id"] = emergency.id
    if tier == "red":
        recommendation = "建议立即前往急诊科，不要自行等待或离开医院；请家属陪同并携带身份证件。"
        next_steps = [
            "前往急诊分诊台说明高风险症状",
            "由护士安排优先接诊与生命体征评估",
            "根据医生判断决定进一步检查或留观",
        ]
    elif tier == "yellow":
        recommendation = "建议当日安排就诊，优先联系分诊台确认号源；症状加重时立即前往急诊。"
        next_steps = [
            "在候诊区关注叫号进度",
            "由医生完成进一步问诊与检查",
            "遵医嘱决定门诊治疗或转诊",
        ]
    else:
        recommendation = "可在普通门诊按预约就诊，注意观察症状变化；如有加重随时复诊。"
        next_steps = [
            "按预约时间到对应科室签到",
            "向医生补充完整病史与用药情况",
            "完成医生建议的检查或复诊安排",
        ]

    result["recommendation"] = recommendation
    result["next_steps"] = next_steps
    result["disclaimer"] = "本结果仅用于就诊引导，不构成医学诊断或治疗建议。"
    result["tier_label"] = _tier_to_chinese(tier)
    result["confidence"] = round(min(result["confidence"], 0.98), 2)
    return result
