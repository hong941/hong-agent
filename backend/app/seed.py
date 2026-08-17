from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .models import (
    Appointment,
    AuditLog,
    Department,
    KnowledgeItem,
    Patient,
    TriageConversation,
    User,
)
from .security import hash_password
from .services.embeddings import get_embedder


def seed(db: Session) -> None:
    if db.query(Department).count() > 0:
        _ensure_extra_knowledge(db)
        return

    departments = [
        Department(
            name="急诊科",
            code="ER",
            description="处理急危重症与高风险症状",
            avg_wait_minutes=8,
            load=86,
            capacity=120,
        ),
        Department(
            name="内科",
            code="MED",
            description="内科常见病、发热感染、慢病管理",
            avg_wait_minutes=25,
            load=72,
            capacity=100,
        ),
        Department(
            name="外科",
            code="SUR",
            description="外科门诊与术后复诊",
            avg_wait_minutes=30,
            load=48,
            capacity=80,
        ),
        Department(
            name="儿科",
            code="PED",
            description="儿童常见病与保健",
            avg_wait_minutes=22,
            load=64,
            capacity=90,
        ),
        Department(
            name="妇产科",
            code="OBG",
            description="妇科与产科门诊",
            avg_wait_minutes=28,
            load=41,
            capacity=70,
        ),
        Department(
            name="骨科",
            code="ORT",
            description="骨关节与运动损伤",
            avg_wait_minutes=35,
            load=55,
            capacity=80,
        ),
        Department(
            name="皮肤科",
            code="DER",
            description="皮肤常见病诊疗",
            avg_wait_minutes=20,
            load=36,
            capacity=60,
        ),
        Department(
            name="耳鼻喉科",
            code="ENT",
            description="耳鼻咽喉疾病诊疗",
            avg_wait_minutes=18,
            load=33,
            capacity=60,
        ),
        Department(
            name="眼科",
            code="OPH",
            description="眼科疾病与视力检查",
            avg_wait_minutes=24,
            load=39,
            capacity=70,
        ),
        Department(
            name="神经内科",
            code="NEU",
            description="头痛头晕、睡眠与神经系统疾病",
            avg_wait_minutes=26,
            load=44,
            capacity=70,
        ),
        Department(
            name="心内科",
            code="CAR",
            description="心血管疾病门诊",
            avg_wait_minutes=29,
            load=58,
            capacity=80,
        ),
        Department(
            name="心理科",
            code="PSY",
            description="睡眠、情绪与心理健康咨询",
            avg_wait_minutes=32,
            load=29,
            capacity=50,
        ),
    ]
    db.add_all(departments)
    db.flush()

    users = [
        User(
            username="admin",
            hashed_password=hash_password("admin123"),
            name="系统管理员",
            role="admin",
        ),
        User(
            username="doctor_zhang",
            hashed_password=hash_password("doctor123"),
            name="张医生",
            role="doctor",
            department_id=_id(departments, "内科"),
        ),
        User(
            username="doctor_li",
            hashed_password=hash_password("doctor123"),
            name="李医生",
            role="doctor",
            department_id=_id(departments, "外科"),
        ),
        User(
            username="doctor_wang",
            hashed_password=hash_password("doctor123"),
            name="王医生",
            role="doctor",
            department_id=_id(departments, "急诊科"),
        ),
        User(
            username="nurse_liu",
            hashed_password=hash_password("nurse123"),
            name="刘护士",
            role="nurse",
            department_id=_id(departments, "急诊科"),
        ),
        User(
            username="patient_demo",
            hashed_password=hash_password("demo123"),
            name="演示患者",
            role="patient",
        ),
    ]
    db.add_all(users)
    db.flush()

    patients = [
        {
            "name": "陈秀兰",
            "age": 68,
            "gender": "女",
            "phone": "138****1201",
            "chief_complaint": "活动后胸痛伴胸闷 1 小时",
            "symptoms": ["胸痛", "胸闷", "出汗"],
            "allergies": "青霉素过敏",
            "medications": "阿司匹林",
            "medical_history": "高血压 10 年，冠心病支架术后",
            "risk_level": "red",
            "risk_score": 82,
            "triage_reason": "检测到胸痛、胸闷等高危关键词，需急诊评估",
            "department": "急诊科",
            "status": "waiting",
        },
        {
            "name": "林小宇",
            "age": 5,
            "gender": "男",
            "phone": "139****2203",
            "chief_complaint": "发热 2 天伴咳嗽",
            "symptoms": ["发热", "咳嗽", "食欲下降"],
            "allergies": "",
            "medications": "布洛芬混悬液",
            "medical_history": "既往体健",
            "risk_level": "yellow",
            "risk_score": 45,
            "triage_reason": "儿童发热伴咳嗽，建议儿科优先评估",
            "department": "儿科",
            "status": "waiting",
        },
        {
            "name": "周建国",
            "age": 55,
            "gender": "男",
            "phone": "137****3311",
            "chief_complaint": "糖尿病复诊开药",
            "symptoms": ["复诊", "血糖监测"],
            "allergies": "",
            "medications": "二甲双胍",
            "medical_history": "2 型糖尿病 6 年",
            "risk_level": "green",
            "risk_score": 18,
            "triage_reason": "常规慢病复诊，建议普通门诊",
            "department": "内科",
            "status": "scheduled",
        },
        {
            "name": "赵雅琴",
            "age": 34,
            "gender": "女",
            "phone": "136****4422",
            "chief_complaint": "皮肤皮疹伴瘙痒 3 天",
            "symptoms": ["皮疹", "瘙痒"],
            "allergies": "",
            "medications": "",
            "medical_history": "过敏性鼻炎",
            "risk_level": "green",
            "risk_score": 22,
            "triage_reason": "皮肤症状建议皮肤科就诊",
            "department": "皮肤科",
            "status": "waiting",
        },
        {
            "name": "孙国强",
            "age": 72,
            "gender": "男",
            "phone": "135****5533",
            "chief_complaint": "头晕伴行走不稳半天",
            "symptoms": ["头晕", "行走不稳"],
            "allergies": "",
            "medications": "氨氯地平",
            "medical_history": "高血压，脑梗死病史",
            "risk_level": "red",
            "risk_score": 74,
            "triage_reason": "高龄合并神经系统症状，需急诊评估",
            "department": "急诊科",
            "status": "waiting",
        },
        {
            "name": "吴梦洁",
            "age": 29,
            "gender": "女",
            "phone": "134****6644",
            "chief_complaint": "月经不调 2 个月",
            "symptoms": ["月经不调", "经量异常"],
            "allergies": "",
            "medications": "",
            "medical_history": "多囊卵巢综合征",
            "risk_level": "green",
            "risk_score": 15,
            "triage_reason": "妇科专科门诊",
            "department": "妇产科",
            "status": "scheduled",
        },
        {
            "name": "郑凯",
            "age": 42,
            "gender": "男",
            "phone": "133****7755",
            "chief_complaint": "右踝扭伤肿痛 6 小时",
            "symptoms": ["扭伤", "肿胀", "疼痛"],
            "allergies": "",
            "medications": "",
            "medical_history": "既往体健",
            "risk_level": "yellow",
            "risk_score": 38,
            "triage_reason": "外伤伴肿痛，建议骨科门诊评估",
            "department": "骨科",
            "status": "waiting",
        },
        {
            "name": "高晓梅",
            "age": 47,
            "gender": "女",
            "phone": "132****8866",
            "chief_complaint": "失眠伴焦虑 1 个月",
            "symptoms": ["失眠", "焦虑", "早醒"],
            "allergies": "",
            "medications": "",
            "medical_history": "既往体健",
            "risk_level": "green",
            "risk_score": 25,
            "triage_reason": "睡眠与情绪问题建议心理科或神经内科",
            "department": "心理科",
            "status": "waiting",
        },
        {
            "name": "罗文博",
            "age": 8,
            "gender": "男",
            "phone": "131****9977",
            "chief_complaint": "耳痛伴听力下降 2 天",
            "symptoms": ["耳痛", "听力下降"],
            "allergies": "",
            "medications": "",
            "medical_history": "既往体健",
            "risk_level": "yellow",
            "risk_score": 33,
            "triage_reason": "耳部症状建议耳鼻喉科就诊",
            "department": "耳鼻喉科",
            "status": "waiting",
        },
        {
            "name": "刘志强",
            "age": 61,
            "gender": "男",
            "phone": "130****1188",
            "chief_complaint": "血压控制不佳 1 周",
            "symptoms": ["头晕", "血压偏高"],
            "allergies": "",
            "medications": "缬沙坦",
            "medical_history": "高血压 8 年",
            "risk_level": "yellow",
            "risk_score": 42,
            "triage_reason": "血压控制不佳伴头晕，建议心内科评估",
            "department": "心内科",
            "status": "in_consultation",
        },
        {
            "name": "钱丽华",
            "age": 36,
            "gender": "女",
            "phone": "139****2299",
            "chief_complaint": "体检后咨询报告指标",
            "symptoms": ["体检咨询"],
            "allergies": "",
            "medications": "",
            "medical_history": "既往体健",
            "risk_level": "green",
            "risk_score": 8,
            "triage_reason": "健康咨询，建议普通门诊",
            "department": "内科",
            "status": "discharged",
        },
    ]

    patient_objects = []
    for item in patients:
        department = _by_name(departments, item["department"])
        patient = Patient(
            name=item["name"],
            age=item["age"],
            gender=item["gender"],
            phone=item["phone"],
            chief_complaint=item["chief_complaint"],
            symptoms=item["symptoms"],
            allergies=item["allergies"],
            medications=item["medications"],
            medical_history=item["medical_history"],
            risk_level=item["risk_level"],
            risk_score=item["risk_score"],
            triage_reason=item["triage_reason"],
            department_id=department.id,
            status=item["status"],
        )
        db.add(patient)
        patient_objects.append(patient)
    db.flush()

    for patient in patient_objects:
        db.add(
            TriageConversation(
                patient_id=patient.id,
                messages=[
                    {
                        "role": "assistant",
                        "content": "您好，请先描述您最主要的症状或就诊原因。",
                    },
                    {"role": "user", "content": patient.chief_complaint},
                    {
                        "role": "assistant",
                        "content": "已记录，请补充持续时间、严重程度、伴随症状及过敏史。",
                    },
                ],
                completed=1,
            )
        )

    now = datetime.now(timezone.utc)
    for patient in patient_objects:
        if patient.status == "scheduled":
            doctor = db.query(User).filter(User.role == "doctor").first()
            db.add(
                Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id if doctor else None,
                    department_id=patient.department_id,
                    scheduled_time=now + timedelta(hours=2),
                    status="booked",
                    notes="AI 分诊后自动预约",
                )
            )

    knowledge_items = [
        KnowledgeItem(
            title="胸痛急诊识别",
            category="急诊安全",
            content="突发胸痛、胸闷伴大汗、恶心或呼吸困难时，应立即停止活动并尽快就医。年龄较大或合并高血压、糖尿病的患者更需警惕。",
            source="公开心血管健康资料整理（演示）",
            tags=["胸痛", "急诊", "心血管"],
        ),
        KnowledgeItem(
            title="呼吸困难处理",
            category="急诊安全",
            content="出现明显呼吸困难、口唇发紫或无法平卧时，提示可能存在急性呼吸问题，应尽快前往急诊评估。",
            source="公开呼吸健康资料整理（演示）",
            tags=["呼吸困难", "急诊"],
        ),
        KnowledgeItem(
            title="意识改变与偏瘫识别",
            category="急诊安全",
            content="突发意识不清、言语不清、肢体无力或面部歪斜，可能是急性脑血管事件的信号，需立即急诊就诊，不要自行等待。",
            source="公开脑卒中科普资料整理（演示）",
            tags=["卒中", "意识", "急诊"],
        ),
        KnowledgeItem(
            title="成人发热家庭观察",
            category="发热感染",
            content="成人发热可先补充水分并监测体温，体温较高或伴明显不适时可遵医嘱使用退热药。持续发热超过 3 天或伴呼吸困难、意识改变时应及时就诊。",
            source="公开发热管理资料整理（演示）",
            tags=["发热", "体温", "观察"],
        ),
        KnowledgeItem(
            title="儿童发热就医指征",
            category="儿科",
            content="儿童发热时关注精神状态、进食和排尿情况。出现高热不退、抽搐、呼吸急促、精神萎靡或皮疹时，应及时前往儿科或急诊。",
            source="公开儿科发热资料整理（演示）",
            tags=["儿童", "发热", "儿科"],
        ),
        KnowledgeItem(
            title="婴幼儿脱水识别",
            category="儿科",
            content="婴幼儿腹泻或呕吐后，如出现哭时泪少、口唇干燥、尿量明显减少，需警惕脱水并及时就诊。",
            source="公开儿科资料整理（演示）",
            tags=["儿童", "腹泻", "脱水"],
        ),
        KnowledgeItem(
            title="腹痛就诊建议",
            category="消化内科",
            content="剧烈腹痛、持续不缓解、伴发热或血便时，不应自行服用止痛药掩盖症状，应尽快就医明确原因。",
            source="公开消化科资料整理（演示）",
            tags=["腹痛", "消化", "急诊"],
        ),
        KnowledgeItem(
            title="腹泻补液原则",
            category="消化内科",
            content="急性腹泻期间注意补水和电解质，避免脱水。持续腹泻、血便或发热时应就诊评估。",
            source="公开消化科资料整理（演示）",
            tags=["腹泻", "补液", "脱水"],
        ),
        KnowledgeItem(
            title="高血压日常管理",
            category="慢病管理",
            content="高血压患者应规律服药、监测血压并记录，避免自行停药。出现剧烈头痛、胸痛、视物模糊或肢体麻木时需紧急就医。",
            source="公开高血压管理资料整理（演示）",
            tags=["高血压", "血压", "慢病"],
        ),
        KnowledgeItem(
            title="糖尿病复诊要点",
            category="慢病管理",
            content="糖尿病患者复诊时应携带近期血糖记录、用药清单和既往检查结果，医生结合糖化血红蛋白等指标调整方案。",
            source="公开糖尿病管理资料整理（演示）",
            tags=["糖尿病", "血糖", "复诊"],
        ),
        KnowledgeItem(
            title="低血糖识别",
            category="慢病管理",
            content="出现心慌、出汗、手抖、乏力或意识模糊时，可能是低血糖表现。意识清醒时可先补充糖分，症状不缓解或意识异常需立即就医。",
            source="公开糖尿病科普资料整理（演示）",
            tags=["低血糖", "糖尿病"],
        ),
        KnowledgeItem(
            title="慢性病用药依从",
            category="慢病管理",
            content="慢性病患者应按时按量服药，如出现药物不良反应或计划调整剂量，应先咨询医生，不要自行停药。",
            source="公开慢病管理资料整理（演示）",
            tags=["用药", "依从性"],
        ),
        KnowledgeItem(
            title="头痛分型与就诊",
            category="神经内科",
            content="突发剧烈头痛、伴呕吐或神经系统症状时需急诊评估；反复发作的头痛建议神经内科专科诊治并记录发作频率。",
            source="公开神经内科资料整理（演示）",
            tags=["头痛", "神经内科"],
        ),
        KnowledgeItem(
            title="头晕伴跌倒风险",
            category="神经内科",
            content="老年人头晕伴行走不稳、言语不清或单侧无力时，应避免独自行走，尽快就医排查脑血管问题。",
            source="公开神经内科资料整理（演示）",
            tags=["头晕", "跌倒", "老年"],
        ),
        KnowledgeItem(
            title="睡眠卫生建议",
            category="心理健康",
            content="保持规律作息、减少睡前屏幕时间、避免下午后大量摄入咖啡因，有助于改善睡眠。长期失眠伴情绪问题建议专科咨询。",
            source="公开睡眠健康资料整理（演示）",
            tags=["睡眠", "失眠", "心理"],
        ),
        KnowledgeItem(
            title="焦虑情绪应对",
            category="心理健康",
            content="适度运动、正念呼吸和规律作息有助于缓解轻度焦虑。焦虑明显影响工作或睡眠时，可到心理科或精神科评估。",
            source="公开心理健康资料整理（演示）",
            tags=["焦虑", "心理"],
        ),
        KnowledgeItem(
            title="踝关节扭伤处理",
            category="骨科",
            content="急性扭伤后应减少活动、抬高患肢并局部冰敷。肿胀明显、无法负重或疼痛持续加重时，建议骨科就诊排查骨折。",
            source="公开骨科资料整理（演示）",
            tags=["扭伤", "踝关节", "骨科"],
        ),
        KnowledgeItem(
            title="颈腰痛日常管理",
            category="骨科",
            content="颈腰痛患者应避免久坐和突然扭转，可结合适度的核心力量训练。出现下肢麻木无力或大小便异常时需尽快就医。",
            source="公开骨科资料整理（演示）",
            tags=["颈腰", "骨科"],
        ),
        KnowledgeItem(
            title="皮疹护理",
            category="皮肤科",
            content="皮疹伴瘙痒时应避免抓挠，保持皮肤清洁干燥。皮疹迅速扩散、伴发热或水疱时应及时皮肤科就诊。",
            source="公开皮肤科资料整理（演示）",
            tags=["皮疹", "皮肤"],
        ),
        KnowledgeItem(
            title="湿疹日常护理",
            category="皮肤科",
            content="湿疹患者应注意保湿，避免过热和刺激性洗护用品，急性发作或继发感染时遵医嘱用药。",
            source="公开皮肤科资料整理（演示）",
            tags=["湿疹", "皮肤"],
        ),
        KnowledgeItem(
            title="耳痛与听力下降",
            category="耳鼻喉科",
            content="耳痛、耳闷或听力下降持续不缓解，或伴流脓、发热时，应到耳鼻喉科检查，避免自行掏耳或滥用滴耳液。",
            source="公开耳鼻喉科资料整理（演示）",
            tags=["耳痛", "听力"],
        ),
        KnowledgeItem(
            title="鼻出血处理",
            category="耳鼻喉科",
            content="少量鼻出血时可坐位前倾、按压鼻翼止血。出血不止、频繁复发或伴头晕乏力时应及时就诊。",
            source="公开耳鼻喉科资料整理（演示）",
            tags=["鼻出血", "耳鼻喉"],
        ),
        KnowledgeItem(
            title="视力异常就诊",
            category="眼科",
            content="突发视力下降、视野缺损或眼痛伴头痛时需尽快眼科或急诊就诊，避免延误。",
            source="公开眼科资料整理（演示）",
            tags=["视力", "眼科"],
        ),
        KnowledgeItem(
            title="结膜炎护理",
            category="眼科",
            content="眼部红肿、分泌物增多时避免揉眼，勤洗手并单独使用毛巾。症状加重或视力受影响时眼科就诊。",
            source="公开眼科资料整理（演示）",
            tags=["结膜炎", "眼"],
        ),
        KnowledgeItem(
            title="孕期常规检查",
            category="妇产科",
            content="孕期应按时产检，出现腹痛、阴道流血、胎动异常或血压升高时，应及时联系产科医生或急诊就诊。",
            source="公开妇产科资料整理（演示）",
            tags=["孕期", "产检", "妇产科"],
        ),
        KnowledgeItem(
            title="月经异常就诊",
            category="妇产科",
            content="月经周期、经量明显改变，或伴明显疼痛、异常出血时，建议妇科门诊评估，必要时结合激素与超声检查。",
            source="公开妇产科资料整理（演示）",
            tags=["月经", "妇科"],
        ),
        KnowledgeItem(
            title="预问诊信息准备",
            category="就诊流程",
            content="就诊前请准备好症状开始时间、持续时间、严重程度、伴随症状、过敏史和近期用药，有助于医生快速判断。",
            source="医院就诊流程整理（演示）",
            tags=["预问诊", "就诊"],
        ),
        KnowledgeItem(
            title="随访计划原则",
            category="就诊流程",
            content="出院或门诊后应按医嘱随访，记录症状与指标变化。如出现新发高危症状，应优先急诊就医而不是等待预约。",
            source="医院随访管理整理（演示）",
            tags=["随访", "复诊"],
        ),
        KnowledgeItem(
            title="用药安全提示",
            category="用药安全",
            content="服用处方药应遵医嘱，不自行加量或混用。出现皮疹、胸闷、喉头水肿等疑似过敏反应时立即停药并就医。",
            source="公开用药安全资料整理（演示）",
            tags=["用药", "安全"],
        ),
    ]
    embedder = get_embedder()
    for item in knowledge_items:
        item.embedding = embedder.embed(
            f"{item.title} {item.category} {item.content} {' '.join(item.tags or [])}"
        )
    db.add_all(knowledge_items)
    _ensure_extra_knowledge(db)

    db.add_all(
        [
            AuditLog(
                actor="system",
                action="seed_init",
                target_type="system",
                detail={"scope": "demo data initialized"},
            ),
            AuditLog(
                actor="nurse_liu",
                action="triage_review",
                target_type="patient",
                target_id=patient_objects[0].id,
                detail={"action": "高风险患者复核"},
            ),
            AuditLog(
                actor="doctor_wang",
                action="patient_consult",
                target_type="patient",
                target_id=patient_objects[4].id,
                detail={"status": "in_consultation"},
            ),
        ]
    )
    db.commit()


def _ensure_extra_knowledge(db: Session) -> None:
    embedder = get_embedder()
    extras = [
        KnowledgeItem(
            title="头部外伤与出血处理",
            category="急诊安全",
            content="头部外伤后出现明显出血、意识改变、反复呕吐或肢体无力，应尽快急诊评估，不要自行驾车前往。",
            source="公开急诊资料整理（演示）",
            tags=["头部外伤", "出血", "急诊"],
        ),
        KnowledgeItem(
            title="外伤出血现场处理",
            category="急诊安全",
            content="明显外伤出血时先用干净敷料压迫止血，抬高患肢；出血不止、伤口深或伴头晕时应尽快急诊。",
            source="公开急诊资料整理（演示）",
            tags=["外伤", "出血", "急诊"],
        ),
        KnowledgeItem(
            title="疑似过敏反应识别",
            category="急诊安全",
            content="皮疹伴呼吸困难、喉头发紧、头晕或血压下降，可能是严重过敏反应，应立即前往急诊。",
            source="公开急诊资料整理（演示）",
            tags=["过敏", "皮疹", "急诊"],
        ),
        KnowledgeItem(
            title="急性哮喘发作处理",
            category="急诊安全",
            content="明显喘息、说话断续或无法平卧，提示哮喘急性发作，应尽快急诊评估并保持半坐位。",
            source="公开呼吸科资料整理（演示）",
            tags=["哮喘", "喘息", "急诊"],
        ),
        KnowledgeItem(
            title="抽搐与惊厥急救",
            category="急诊安全",
            content="抽搐发作时保持周围环境安全、侧卧防止误吸，不要强行按压肢体；持续抽搐或意识不清应及时急诊。",
            source="公开神经科资料整理（演示）",
            tags=["抽搐", "惊厥", "急诊"],
        ),
        KnowledgeItem(
            title="呕血与黑便就医",
            category="消化内科",
            content="呕血、黑便或明显乏力头晕提示可能存在消化道出血，应尽快急诊，不要自行进食。",
            source="公开消化科资料整理（演示）",
            tags=["呕血", "黑便", "消化"],
        ),
        KnowledgeItem(
            title="痰中带血就医",
            category="发热感染",
            content="痰中带血或咳血应尽快就诊，结合咳嗽、发热等情况由医生评估呼吸系统问题。",
            source="公开呼吸科资料整理（演示）",
            tags=["咳血", "咳嗽", "呼吸"],
        ),
        KnowledgeItem(
            title="儿童脱水风险",
            category="儿科",
            content="婴幼儿腹泻或呕吐后出现尿少、精神萎靡、口唇干燥，需警惕脱水并尽快前往儿科或急诊。",
            source="公开儿科资料整理（演示）",
            tags=["儿童", "脱水", "腹泻"],
        ),
        KnowledgeItem(
            title="突发视力下降就医",
            category="眼科",
            content="突发视力下降、视野缺损或眼痛伴头痛，应尽快前往眼科或急诊评估，避免延误。",
            source="公开眼科资料整理（演示）",
            tags=["视力", "眼科", "急诊"],
        ),
        KnowledgeItem(
            title="孕期胎动异常就医",
            category="妇产科",
            content="孕期胎动明显减少、腹痛或阴道流血时，应尽快联系产科或急诊评估。",
            source="公开妇产科资料整理（演示）",
            tags=["孕期", "胎动", "妇产科"],
        ),
        KnowledgeItem(
            title="心理危机紧急求助",
            category="心理健康",
            content="出现自伤、自杀风险或严重行为异常时，应尽快寻求心理科、急诊或专业求助渠道帮助。",
            source="公开心理健康资料整理（演示）",
            tags=["心理危机", "自伤", "求助"],
        ),
        KnowledgeItem(
            title="心悸胸闷就医",
            category="心内科",
            content="反复心悸、胸闷或活动后不适，建议心内科评估，并记录发作时间、诱因和伴随症状。",
            source="公开心内科资料整理（演示）",
            tags=["心悸", "胸闷", "心内科"],
        ),
        KnowledgeItem(
            title="疫苗接种与预防保健",
            category="儿科",
            content="儿童常规疫苗接种与保健评估可提前预约，接种前如实告知过敏史和近期发热情况。",
            source="公开预防保健资料整理（演示）",
            tags=["疫苗", "预防保健", "儿科"],
        ),
        KnowledgeItem(
            title="鼻塞流涕护理",
            category="耳鼻喉科",
            content="普通感冒或过敏性鼻炎引起的鼻塞流涕，可先观察并保持鼻腔湿润；持续加重或伴发热时就诊。",
            source="公开耳鼻喉科资料整理（演示）",
            tags=["鼻塞", "流涕", "耳鼻喉"],
        ),
        KnowledgeItem(
            title="恶心呕吐补水",
            category="消化内科",
            content="频繁呕吐时少量多次补水，观察尿量；出现口干、乏力或尿少提示脱水风险，应及时就诊。",
            source="公开消化科资料整理（演示）",
            tags=["呕吐", "脱水", "补水"],
        ),
        KnowledgeItem(
            title="痤疮日常护理",
            category="皮肤科",
            content="痤疮患者避免挤压，注意清洁和保湿；反复发作或出现严重结节囊肿时皮肤科就诊。",
            source="公开皮肤科资料整理（演示）",
            tags=["痤疮", "皮肤"],
        ),
        KnowledgeItem(
            title="干眼与视疲劳护理",
            category="眼科",
            content="长时间用眼后干涩、视疲劳可适当休息并使用人工泪液；持续加重或视力下降时眼科就诊。",
            source="公开眼科资料整理（演示）",
            tags=["干眼", "视疲劳", "眼科"],
        ),
        KnowledgeItem(
            title="脑卒中识别",
            category="急诊安全",
            content="突发言语不清、单侧肢体无力、面部歪斜或意识改变，可能是脑卒中，应立即前往急诊，不要自行等待。",
            source="公开神经科资料整理（演示）",
            tags=["卒中", "偏瘫", "急诊"],
        ),
        KnowledgeItem(
            title="慢性胃炎管理",
            category="消化内科",
            content="慢性胃炎复诊时应携带近期用药和症状记录，按医嘱随访，必要时复查胃镜或相关指标。",
            source="公开消化科资料整理（演示）",
            tags=["胃炎", "随访", "复诊"],
        ),
        KnowledgeItem(
            title="常规体检与健康咨询",
            category="就诊流程",
            content="常规体检和健康咨询可预约普通门诊，建议提前整理家族史、既往病史和近期不适。",
            source="医院就诊流程整理（演示）",
            tags=["体检", "咨询", "就诊"],
        ),
        KnowledgeItem(
            title="肩颈酸痛管理",
            category="骨科",
            content="肩颈酸痛多为肌肉劳损或姿势问题，可适当热敷、拉伸并改善工位姿势；持续加重伴上肢麻木时骨科就诊。",
            source="公开骨科资料整理（演示）",
            tags=["肩颈", "酸痛", "骨科"],
        ),
        KnowledgeItem(
            title="慢性腰痛复诊",
            category="骨科",
            content="慢性腰痛复诊时应记录疼痛变化和诱发因素，结合影像复查由骨科医生评估康复计划。",
            source="公开骨科资料整理（演示）",
            tags=["腰痛", "复诊", "骨科"],
        ),
        KnowledgeItem(
            title="血糖异常就医",
            category="慢病管理",
            content="血糖明显升高伴乏力、口渴或尿多时，建议及时内分泌科或内科就诊，不要自行调整降糖药。",
            source="公开糖尿病管理资料整理（演示）",
            tags=["血糖", "糖尿病", "内分泌"],
        ),
    ]
    added = False
    for item in extras:
        exists = db.query(KnowledgeItem).filter(KnowledgeItem.title == item.title).first()
        if exists is None:
            item.embedding = embedder.embed(
                f"{item.title} {item.category} {item.content} {' '.join(item.tags or [])}"
            )
            db.add(item)
            added = True
    if added:
        db.commit()


def _id(departments: list[Department], name: str) -> int:
    return _by_name(departments, name).id


def _by_name(departments: list[Department], name: str) -> Department:
    for department in departments:
        if department.name == name:
            return department
    raise ValueError(f"Unknown department: {name}")
