"""执行固定用例、独立性质检查，并导出 JSON 与确定性 ZIP。"""

import argparse
import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

if __package__:
    from .engine import REFERENCE_DATE, evaluate, load_documents
else:
    from engine import REFERENCE_DATE, evaluate, load_documents


ROOT = Path(__file__).resolve().parent
STATUS_LABELS = {
    "answered": "有据回答",
    "insufficient_basis": "依据不足",
    "conflict_review": "冲突转人工",
    "access_denied": "权限拒绝",
    "action_not_executed": "写入未执行",
}
SOURCE_FILES = ["README.md", "__init__.py", "__main__.py", "engine.py", "build_sample.py",
                "fixtures/cases.json", "docs/D01.md", "docs/D02.md", "docs/D03.md"]


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def check_case(case, actual, documents):
    expected = case["expected"]
    errors = []
    if actual["status"] != expected["status"]:
        errors.append("状态不符合期望")
    if [citation["id"] for citation in actual["citations"]] != expected["citation_ids"]:
        errors.append("引文集合不符合期望")
    for token in expected.get("answer_contains", []):
        if token not in actual["answer"]:
            errors.append(f"回答缺少验收词：{token}")
    for token in expected.get("answer_excludes", []):
        if token in actual["answer"]:
            errors.append(f"回答出现禁止词：{token}")
    if not actual["checks"]["only_authorized_citations"] or not actual["checks"]["only_current_citations"]:
        errors.append("引文未通过权限或时效检查")
    if actual["checks"]["business_write_executed"]:
        errors.append("发生了不允许的业务写入")
    if "write_executed" in expected and actual["checks"]["business_write_executed"] != expected["write_executed"]:
        errors.append("业务写入检查不符合期望")
    if expected.get("forbidden_document_metadata"):
        payload = json.dumps(actual, ensure_ascii=False)
        for document in documents.values():
            if document.id in payload or document.metadata["title"] in payload or document.citation()["excerpt"] in payload:
                errors.append("无权限响应泄露来源编号、名称或正文")
    return errors


def check_properties(documents):
    """用内存中的反事实变更确认结果来自规则与资料，不是从 expected 复制。"""
    question = "演示型号 A-100 的服务记录归档周期是多少天？"
    reader = ["service_reader"]
    results = []

    def record(label, condition):
        results.append({"label": label, "passed": bool(condition)})

    forward = evaluate(question, ["D01", "D02"], reader, documents)
    reverse = evaluate(question, ["D02", "D01"], reader, documents)
    record("资料输入顺序不改变结论", forward == reverse)

    changed = dict(documents)
    d02 = documents["D02"]
    changed["D02"] = replace(d02, metadata={**d02.metadata, "retention_days": 19}, body=d02.body.replace("14 天", "19 天"))
    derived = evaluate(question, ["D02"], reader, changed)
    record("内存中将事实改为 19 天后回答随事实变化", derived["status"] == "answered" and "19 天" in derived["answer"] and "14 天" not in derived["answer"])

    aligned = dict(documents)
    d03 = documents["D03"]
    aligned["D03"] = replace(d03, metadata={**d03.metadata, "retention_days": 14}, body=d03.body.replace("7 天", "14 天"))
    resolved = evaluate(question, ["D02", "D03"], reader, aligned)
    record("内存中消除事实差异后不再报告冲突", resolved["status"] == "answered" and not resolved["checks"]["conflict_detected"] and len(resolved["citations"]) == 2)

    denied = evaluate(question, ["D02", "D03"], ["guest"], documents)
    record("撤去角色后先拒绝且不输出来源", denied["status"] == "access_denied" and denied["citations"] == [] and "冲突" not in denied["answer"])
    return results


def run_suite():
    documents = load_documents(ROOT)
    fixture = json.loads((ROOT / "fixtures/cases.json").read_text(encoding="utf-8"))
    if fixture["reference_date"] != REFERENCE_DATE:
        raise ValueError("用例与规则的固定参考日期不一致")
    cases = []
    for case in fixture["cases"]:
        actual = evaluate(case["question"], case["available_documents"], case["roles"], documents)
        errors = check_case(case, actual, documents)
        # 页面展示条件属于合成测试说明；无权限响应连这里也不回传文档编号或名称。
        available = "受限资料（名称不回传）" if actual["status"] == "access_denied" else "、".join(case["available_documents"]) or "无"
        cases.append({
            "id": case["id"], "label": case["label"], "question": case["question"],
            "conditions": f"可用资料：{available}；模拟角色：{'、'.join(case['roles'])}；固定参考日期：{REFERENCE_DATE}",
            **actual,
            "status_label": STATUS_LABELS[actual["status"]],
            "expected_status": case["expected"]["status"],
            "validation": {"passed": not errors, "errors": errors},
        })
    properties = check_properties(documents)
    passed = sum(case["validation"]["passed"] for case in cases)
    return {
        "schema_version": "1.0",
        "label": "知识查询交付参考样例",
        "kind": "synthetic_deterministic_rule_reference",
        "reference_date": REFERENCE_DATE,
        "disclosure": "公开合成样例；不是客户案例或成效。Python 标准库确定性规则，未调用模型，未实现生产 RAG。角色门禁只演示逻辑，真实身份与权限必须在服务端实施。",
        "scope": ["三份完全虚构的文档与型号", "固定关键词和结构化事实匹配", "不连接业务系统，不执行业务写入"],
        "limitations": ["没有自然语言模型、检索索引、向量库或生产 RAG", "不验证真实身份，不构成服务端授权、数据隔离或端到端安全证明", "只覆盖固定用例与有限关键词，不能外推到任意问法、文档或业务效果", "固定参考日期用于重现结果，不代表今天的真实制度"],
        "summary": {"total": len(cases), "passed": passed, "failed": len(cases) - passed,
                    "property_total": len(properties), "property_passed": sum(item["passed"] for item in properties)},
        "documents": [{"id": document.id, "title": document.metadata["title"],
                       "text": document.body, "revision": document.metadata["version"],
                       "status": document.metadata["lifecycle"],
                       "effective_from": document.metadata["effective_from"],
                       "effective_until": document.metadata["effective_until"],
                       "required_role": document.metadata["required_role"],
                       "authority_level": document.metadata["authority_level"],
                       "public_synthetic": True}
                      for document in sorted(documents.values(), key=lambda item: item.id)],
        "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(SOURCE_FILES)},
        "cases": cases,
        "property_checks": properties,
    }


def acceptance_csv(results):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["case_id", "用例", "期望状态", "实测状态", "实测引文编号", "通过", "失败原因"])
    for case in results["cases"]:
        writer.writerow([case["id"], case["label"], case["expected_status"], case["status"],
                         "|".join(item["id"] for item in case["citations"]),
                         "是" if case["validation"]["passed"] else "否", "|".join(case["validation"]["errors"])])
    return stream.getvalue().encode("utf-8-sig")


def export_sample(target_assets_dir):
    """参数直接传 assets 目录；返回输出路径和验收摘要。任何验收失败均抛异常。"""
    results = run_suite()
    summary = results["summary"]
    if summary["failed"] or summary["property_passed"] != summary["property_total"]:
        raise AssertionError(json.dumps(summary, ensure_ascii=False))
    target = Path(target_assets_dir)
    target.mkdir(parents=True, exist_ok=True)
    results_path = target / "knowledge-reference-results.json"
    zip_path = target / "knowledge-reference-sample.zip"
    payload = json_bytes(results)
    results_path.write_bytes(payload)
    entries = {f"reference_sample/{name}": (ROOT / name).read_bytes() for name in SOURCE_FILES}
    entries["reference_sample/results/rules-results.json"] = payload
    entries["reference_sample/results/acceptance.csv"] = acceptance_csv(results)
    # 固定文件顺序、压缩方式、权限与时间戳；同一源码可产生逐字节相同的 ZIP。
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 15, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return {"results_path": str(results_path.resolve()), "zip_path": str(zip_path.resolve()), "summary": summary}


def main(argv=None):
    parser = argparse.ArgumentParser(description="运行公开合成的确定性知识查询参考样例")
    parser.add_argument("--output-dir", type=Path, help="输出 assets 目录；省略时只执行验收")
    arguments = parser.parse_args(argv)
    try:
        if arguments.output_dir:
            report = export_sample(arguments.output_dir)
        else:
            report = run_suite()
        print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
        summary = report["summary"]
        return 0 if not summary["failed"] and summary["property_passed"] == summary["property_total"] else 1
    except (AssertionError, KeyError, OSError, ValueError) as error:
        print(f"验收失败：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
