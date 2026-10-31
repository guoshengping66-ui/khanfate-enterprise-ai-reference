"""确定性查询规则；只有 Python 标准库，没有模型、向量库、网络或业务写入接口。"""

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re


REFERENCE_DATE = "2026-01-15"
WRITE_VERBS = re.compile(r"修改|写入|保存|提交|删除|更新|设置|执行")
MODEL_PATTERN = re.compile(r"(?<![A-Z0-9])([A-Z]-\d{3})(?![A-Z0-9])", re.I)


@dataclass(frozen=True)
class Document:
    metadata: dict
    body: str

    @property
    def id(self):
        return self.metadata["id"]

    def is_current(self, reference_date):
        current = date.fromisoformat(reference_date)
        start = date.fromisoformat(self.metadata["effective_from"])
        end_text = self.metadata["effective_until"]
        end = date.fromisoformat(end_text) if end_text else None
        return self.metadata["lifecycle"] == "effective" and start <= current and (end is None or current <= end)

    def citation(self):
        excerpt = re.search(r"^第 2 条：.+$", self.body, re.M).group(0)
        return {
            "id": self.id,
            "title": self.metadata["title"],
            "version": self.metadata["version"],
            "effective_from": self.metadata["effective_from"],
            "section": self.metadata["section"],
            "excerpt": excerpt,
        }


def load_documents(package_dir=None):
    root = Path(package_dir) if package_dir else Path(__file__).resolve().parent
    documents = {}
    for path in sorted((root / "docs").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = re.match(r"<!-- metadata\s*\n(.*?)\n-->\s*\n(.*)", text, re.S)
        if not match:
            raise ValueError(f"文档元数据格式错误：{path.name}")
        metadata = json.loads(match.group(1))
        document = Document(metadata, match.group(2))
        if metadata["id"] != path.stem or metadata["id"] in documents:
            raise ValueError("文档编号与文件名不一致或重复")
        excerpt = document.citation()["excerpt"]
        if f"周期为 {metadata['retention_days']} 天" not in excerpt:
            raise ValueError(f"结构化事实与正文不一致：{path.name}")
        document.is_current(REFERENCE_DATE)  # 同时验证日期字段。
        documents[document.id] = document
    if set(documents) != {"D01", "D02", "D03"}:
        raise ValueError("参考包必须恰好包含 D01、D02、D03 三份合成文档")
    return documents


def evaluate(question, available_documents, roles, documents, reference_date=REFERENCE_DATE):
    """根据资料与角色计算结果。本函数不读取 fixtures 中的 expected。"""
    if set(available_documents) - set(documents):
        raise ValueError("输入引用了未知文档编号")
    role_set = set(roles)
    citations = []
    conflict = False
    permission_checked = False

    if WRITE_VERBS.search(question):
        status = "action_not_executed"
        answer = "未执行业务写入。本参考包只提供查询判定，没有业务系统连接或写入接口。"
        review_steps = ["如确需业务变更，由有权人员在正式系统中按既有流程处理。"]
    else:
        model_match = MODEL_PATTERN.search(question)
        model = model_match.group(1).upper() if model_match else None
        topic = "service_record_archiving" if "服务记录" in question and "归档" in question else None
        candidates = sorted(
            (documents[key] for key in set(available_documents)
             if documents[key].metadata["model"] == model and documents[key].metadata["topic"] == topic),
            key=lambda document: document.id,
        )
        current = [document for document in candidates if document.is_current(reference_date)]
        permission_checked = bool(current)
        authorized = [document for document in current if document.metadata["required_role"] in role_set]
        # 先保留现行资料，再做角色门禁；不能因现行资料不可读而退回旧版。
        # 若同一问题有部分现行资料不可读，也不基于剩余片段给出结论或泄露冲突信息。
        if current and len(authorized) != len(current):
            status = "access_denied"
            answer = "当前身份无权读取此问题所需资料，请由授权人员核对访问权限。"
            review_steps = ["由资料管理员核对身份与授权；授权完成后重新查询。"]
        elif not authorized:
            status = "insufficient_basis"
            answer = "未找到当前有效且可读取的依据，无法给出归档周期。"
            review_steps = ["补充与型号、主题一致的现行资料，再重新核对。"]
        else:
            highest_level = min(document.metadata["authority_level"] for document in authorized)
            selected = [document for document in authorized if document.metadata["authority_level"] == highest_level]
            distinct_values = {document.metadata["retention_days"] for document in selected}
            conflict = len(distinct_values) > 1
            citations = [document.citation() for document in selected]
            if conflict:
                status = "conflict_review"
                answer = "当前有效的同级资料存在冲突，需要人工核对适用范围与覆盖关系；本次不选定归档周期。"
                review_steps = ["核对每份引文的版本、适用范围和效力等级。", "由资料责任人澄清覆盖关系并更新资料后，再重新查询。"]
            else:
                status = "answered"
                days = next(iter(distinct_values))
                answer = f"根据当前有效且可读取的资料，演示型号 {model} 的服务记录归档周期为 {days} 天。"
                review_steps = ["核对引文中的版本、生效日期与条款；本结论仅适用于本合成样例。"]

    cited_documents = [documents[citation["id"]] for citation in citations]
    return {
        "answer": answer,
        "status": status,
        "citations": citations,
        "checks": {
            "read_permission_checked": permission_checked,
            "only_authorized_citations": all(document.metadata["required_role"] in role_set for document in cited_documents),
            "only_current_citations": all(document.is_current(reference_date) for document in cited_documents),
            "conflict_detected": conflict,
            "source_metadata_withheld": status == "access_denied",
            "business_write_executed": False,
        },
        "review_steps": review_steps,
    }
