import argparse
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.ai.provider import MockProvider, get_provider  # noqa: E402
from app.ai.rag import KnowledgeService  # noqa: E402
from app.ai.triage import evaluate_rule, run_triage  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Patient, TriageConversation  # noqa: E402
from app.seed import seed  # noqa: E402
from app.services.embeddings import ensure_knowledge_embeddings  # noqa: E402

TIER_ORDER = ["green", "yellow", "red"]


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * ratio))
    return ordered[index]


def tier_metrics(rows: list[dict]) -> dict[str, dict]:
    result = {}
    for tier in TIER_ORDER:
        tp = sum(
            1
            for row in rows
            if row["expected_tier"] == tier and row["final_tier"] == tier
        )
        fp = sum(
            1
            for row in rows
            if row["expected_tier"] != tier and row["final_tier"] == tier
        )
        fn = sum(
            1
            for row in rows
            if row["expected_tier"] == tier and row["final_tier"] != tier
        )
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        result[tier] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="AI 智慧医院评测脚本")
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 例，默认全部")
    parser.add_argument(
        "--mode",
        choices=["auto", "rule", "model"],
        default="auto",
        help="auto 自动选择已配置模型；rule 只跑规则引擎；model 强制跑真实模型",
    )
    parser.add_argument(
        "--output-suffix",
        default="",
        help="输出文件后缀，例如 -rule，避免覆盖默认报告",
    )
    args = parser.parse_args()

    cases = json.loads((BASE_DIR / "eval_cases.json").read_text(encoding="utf-8"))
    if args.limit:
        cases = cases[: args.limit]

    provider = None
    real_model = False
    if args.mode == "rule":
        model_name = "rule-only"
    else:
        provider = get_provider()
        real_model = not isinstance(provider, MockProvider)
        model_name = provider.model if real_model else "local-rule"

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as bootstrap_db:
        seed(bootstrap_db)
        ensure_knowledge_embeddings(bootstrap_db)

    db = SessionLocal()
    rows = []
    latencies = []
    rag_hits = 0

    for case in cases:
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

        rule_result = evaluate_rule(db, patient, conversation)
        if args.mode == "rule" or not real_model:
            final_result = rule_result
            latency_ms = 0
        else:
            started = time.perf_counter()
            try:
                final_result = run_triage(db, patient, conversation)
                latency_ms = (time.perf_counter() - started) * 1000
            except Exception:
                final_result = rule_result
                latency_ms = 0

        hits = KnowledgeService(db).search(
            f"{case['chief_complaint']} {' '.join(case.get('symptoms', []))}",
            top_k=3,
        )
        rag_hit = any(
            case["expected_keyword"]
            in (
                hit["title"]
                + hit["content"]
                + hit["category"]
                + " ".join(hit.get("tags", []))
            )
            for hit in hits
        )
        if rag_hit:
            rag_hits += 1
        if latency_ms:
            latencies.append(latency_ms)

        rows.append(
            {
                "id": case["id"],
                "chief_complaint": case["chief_complaint"],
                "expected_tier": case["expected_tier"],
                "expected_department": case["expected_department"],
                "rule_tier": rule_result["tier"],
                "final_tier": final_result["tier"],
                "rule_department": rule_result["department"],
                "final_department": final_result["department"],
                "rag_hit": rag_hit,
                "latency_ms": round(latency_ms, 1),
                "label_note": case.get("label_note", ""),
            }
        )

    db.close()

    rule_accuracy = sum(
        1 for row in rows if row["rule_tier"] == row["expected_tier"]
    ) / len(rows)
    final_accuracy = sum(
        1 for row in rows if row["final_tier"] == row["expected_tier"]
    ) / len(rows)
    rule_dept_accuracy = sum(
        1
        for row in rows
        if row["rule_department"] == row["expected_department"]
    ) / len(rows)
    final_dept_accuracy = sum(
        1
        for row in rows
        if row["final_department"] == row["expected_department"]
    ) / len(rows)
    rag_recall = rag_hits / len(rows)

    confusion = defaultdict(Counter)
    for row in rows:
        confusion[row["expected_tier"]][row["final_tier"]] += 1

    errors = [
        row
        for row in rows
        if row["final_tier"] != row["expected_tier"]
        or row["final_department"] != row["expected_department"]
        or not row["rag_hit"]
    ]
    errors = sorted(
        errors,
        key=lambda row: (
            row["final_tier"] != row["expected_tier"],
            row["final_department"] != row["expected_department"],
            not row["rag_hit"],
        ),
    )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(rows),
        "real_model": real_model,
        "mode": args.mode,
        "model_name": model_name,
        "rule_tier_accuracy": round(rule_accuracy, 4),
        "final_tier_accuracy": round(final_accuracy, 4),
        "rule_department_accuracy": round(rule_dept_accuracy, 4),
        "final_department_accuracy": round(final_dept_accuracy, 4),
        "rag_recall_top3": round(rag_recall, 4),
        "latency_ms_p50": round(percentile(latencies, 0.5), 1),
        "latency_ms_p95": round(percentile(latencies, 0.95), 1),
        "confusion_matrix": {
            expected: dict(predicted) for expected, predicted in confusion.items()
        },
        "tier_metrics": tier_metrics(rows),
        "errors": errors[:15],
        "error_count": len(errors),
    }

    output_dir = REPO_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = args.output_suffix
    (output_dir / f"评测结果-50例{suffix}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# AI 智慧医院第一版评测报告",
        "",
        f"- 评测时间：{summary['generated_at']}",
        f"- 评测样本：{summary['case_count']} 例",
        f"- 模型模式：{summary['model_name']}（{summary['mode']}）",
        f"- 数据说明：样本为内部演示标注，用于开发回归，不等同于真实临床验证",
        "",
        "## 总览",
        "",
        "| 指标 | 数值 |",
        "| --- | --- |",
        f"| 规则分级准确率 | {summary['rule_tier_accuracy']:.1%} |",
        f"| 最终分级准确率 | {summary['final_tier_accuracy']:.1%} |",
        f"| 规则科室准确率 | {summary['rule_department_accuracy']:.1%} |",
        f"| 最终科室准确率 | {summary['final_department_accuracy']:.1%} |",
        f"| RAG 引用命中率 Top3 | {summary['rag_recall_top3']:.1%} |",
        f"| 单例评估延迟 P50 | {summary['latency_ms_p50']} ms |",
        f"| 单例评估延迟 P95 | {summary['latency_ms_p95']} ms |",
        "",
        "## 分档指标",
        "",
        "| 档位 | Precision | Recall | F1 |",
        "| --- | --- | --- | --- |",
    ]
    for tier in TIER_ORDER:
        metrics = summary["tier_metrics"][tier]
        lines.append(
            f"| {tier} | {metrics['precision']:.1%} | {metrics['recall']:.1%} | {metrics['f1']:.1%} |"
        )

    lines += ["", "## 混淆矩阵（预测行 x 期望列）", "", "| 期望 \\ 预测 | green | yellow | red |", "| --- | --- | --- | --- |"]
    for expected in TIER_ORDER:
        row = summary["confusion_matrix"].get(expected, {})
        lines.append(
            f"| {expected} | {row.get('green', 0)} | {row.get('yellow', 0)} | {row.get('red', 0)} |"
        )

    lines += ["", "## 待改进样例", ""]
    if summary["errors"]:
        lines += [
            "| 用例 | 主诉 | 期望 | 最终 | 期望科室 | 最终科室 | RAG |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for row in summary["errors"]:
            lines.append(
                f"| {row['id']} | {row['chief_complaint']} | "
                f"{row['expected_tier']} | {row['final_tier']} | "
                f"{row['expected_department']} | {row['final_department']} | "
                f"{'是' if row['rag_hit'] else '否'} |"
            )
    else:
        lines.append("当前评测集内未发现分级或引用错误。")

    lines += [
        "",
        "## 评测集构成",
        "",
        f"- 红色高风险：{sum(1 for c in cases if c['expected_tier'] == 'red')} 例",
        f"- 黄色中风险：{sum(1 for c in cases if c['expected_tier'] == 'yellow')} 例",
        f"- 绿色低风险：{sum(1 for c in cases if c['expected_tier'] == 'green')} 例",
        "- 覆盖科室：急诊、内科、外科、儿科、妇产科、骨科、皮肤科、耳鼻喉科、眼科、神经内科、心内科、心理科",
        "- 评测数据与脚本位于 `backend/eval/`，可重复运行",
    ]

    report = "\n".join(lines) + "\n"
    (output_dir / f"AI智慧医院-评测报告-第一版{suffix}.md").write_text(
        report, encoding="utf-8"
    )
    print(report)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
