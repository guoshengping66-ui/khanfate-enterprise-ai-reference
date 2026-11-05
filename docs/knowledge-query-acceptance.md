# 企业知识库回答“14 天”就算通过吗？用十个公开用例检查依据与例外

检查知识查询应用，除了核对答案，还需要看它依据哪份资料、资料是否现行、当前角色能否读取，以及缺少依据时返回什么。只展示一个正确答案，覆盖不了这些条件。

平衡点人工智能提供了一份可下载的合成参考程序，用固定规则把这些条件拆开检查。它只使用 Python 标准库，没有调用模型、向量数据库、网络服务或业务系统，不是生产 RAG，也没有真实身份认证。本文说明怎样复核这份程序，以及真实项目还需要验证什么。

## 三份资料，先制造可以核对的差异

参考程序固定使用 2026-01-15 作为判断日期。三份文档围绕演示型号 A-100 的服务记录归档周期：

| 文档 | 天数 | 有效状态 | 在测试中的作用 |
| --- | --- | --- | --- |
| D01 | 30 天 | 已失效 | 检查旧版能否被排除 |
| D02 | 14 天 | 现行 | 提供一份正常依据 |
| D03 | 7 天 | 现行，与 D02 同级 | 在指定用例中制造事实冲突 |

程序先识别有限关键词和型号，再按日期、模拟角色与明示效力等级处理资料。D03 只在对应测试中加入；程序不会因为某份文档标题看起来更“专项”，就认定它可以覆盖另一份资料。

## 下载后先运行，再看结果

可以直接克隆本仓库，或从[平衡点公开参考包](https://khanfate.com/assets/knowledge-reference-sample.zip)下载并解压。进入 reference_sample 目录，使用 Python 3.9 或更高版本执行：

```powershell
python build_sample.py
```

2026-10-31 在本仓库的副本重新执行得到的汇总为：

```json
{
  "total": 10,
  "passed": 10,
  "failed": 0,
  "property_total": 4,
  "property_passed": 4
}
```

这些数字表示公开固定规则下的检查结果，不能换算成模型准确率或生产系统通过率。读者应保留自己运行时的输出；任一用例或性质检查失败，程序会以非零状态退出。

如需重新导出结果和源码包，可以执行：

```powershell
python build_sample.py --output-dir ./generated/assets
```

## 十条样本分别检查什么

| 编号 | 输入条件 | 预期状态 |
| --- | --- | --- |
| C01 | 同时提供旧版和现行资料 | 按现行资料回答 |
| C02 | 调换旧版与现行资料的输入顺序 | 仍按现行资料回答 |
| C03 | 只有失效资料 | 依据不足，不给天数 |
| C04 | 查询没有依据的型号 | 依据不足 |
| C05 | 两份同级现行资料存在冲突 | 返回冲突，建议人工核对 |
| C06 | 模拟角色无权读取所需资料 | 拒绝并隐藏来源信息 |
| C07 | 要求修改并保存到业务系统 | 明确未执行写入 |
| C08 | 查询没有依据的主题 | 依据不足 |
| C09 | 无权角色查询存在冲突的资料 | 不透露冲突及来源信息 |
| C10 | 没有可用资料 | 依据不足 |

这里有两个容易忽略的点。第一，现行资料不可读时，不能退回旧版给出答案。第二，拒绝正文没有写出天数，还不足以说明响应没有泄露信息；来源编号、标题和引文也应一起核对。

上述权限行为只验证本地规则分支。roles 是可以修改的输入字符串，真实系统必须由服务端验证身份并实施授权。

## 从输入到完整输出，复核三个样本

2026-11-05 从公开仓库重新匿名克隆后执行，十个固定用例与四个性质检查通过。以下三段输出由同版 `engine.evaluate` 实际计算，未从测试期望复制。资料判断日期固定为 2026-01-15。

本次计算的[源码](https://github.com/guoshengping66-ui/khanfate-enterprise-ai-reference/blob/9e6f0c3eaee7e7b8ba2d7d6b61a911fed662672e/reference_sample/engine.py)、[固定输入](https://github.com/guoshengping66-ui/khanfate-enterprise-ai-reference/blob/9e6f0c3eaee7e7b8ba2d7d6b61a911fed662672e/reference_sample/fixtures/cases.json)及[完整十项结果](https://github.com/guoshengping66-ui/khanfate-enterprise-ai-reference/blob/9e6f0c3eaee7e7b8ba2d7d6b61a911fed662672e/generated/knowledge-reference-results.json)均固定到同一公开提交。

### C01 · 同时传入旧版与现行资料

D01 的 30 天已失效，D02 的 14 天在固定判断日期有效。实际响应引用 D02，保留版本、生效日期与第 2 条原文。复核时同时检查答案和引文。

输入参数如下。

```json
{
  "question": "演示型号 A-100 的服务记录归档周期是多少天？",
  "available_documents": [
    "D01",
    "D02"
  ],
  "roles": [
    "service_reader"
  ]
}
```

<details>
<summary>展开实际计算的完整输出</summary>

```json
{
  "answer": "根据当前有效且可读取的资料，演示型号 A-100 的服务记录归档周期为 14 天。",
  "status": "answered",
  "citations": [
    {
      "id": "D02",
      "title": "演示型号 A-100 服务记录归档规范（现行）",
      "version": "2.0",
      "effective_from": "2026-01-01",
      "section": "第 2 条：归档周期",
      "excerpt": "第 2 条：演示型号 A-100 的服务记录归档周期为 14 天。"
    }
  ],
  "checks": {
    "read_permission_checked": true,
    "only_authorized_citations": true,
    "only_current_citations": true,
    "conflict_detected": false,
    "source_metadata_withheld": false,
    "business_write_executed": false
  },
  "review_steps": [
    "核对引文中的版本、生效日期与条款；本结论仅适用于本合成样例。"
  ]
}
```

</details>

### C05 · 同级现行资料冲突时停在人工核对

D02 与 D03 同为现行、同级，天数分别为 14 和 7。实际响应保留两条来源供授权读者核对，返回 conflict_review。此处的转人工是返回建议，程序没有创建工单。

输入参数如下。

```json
{
  "question": "演示型号 A-100 的服务记录归档周期是多少天？",
  "available_documents": [
    "D02",
    "D03"
  ],
  "roles": [
    "service_reader"
  ]
}
```

<details>
<summary>展开实际计算的完整输出</summary>

```json
{
  "answer": "当前有效的同级资料存在冲突，需要人工核对适用范围与覆盖关系；本次不选定归档周期。",
  "status": "conflict_review",
  "citations": [
    {
      "id": "D02",
      "title": "演示型号 A-100 服务记录归档规范（现行）",
      "version": "2.0",
      "effective_from": "2026-01-01",
      "section": "第 2 条：归档周期",
      "excerpt": "第 2 条：演示型号 A-100 的服务记录归档周期为 14 天。"
    },
    {
      "id": "D03",
      "title": "演示型号 A-100 服务记录归档专项说明（同级）",
      "version": "1.0",
      "effective_from": "2026-01-01",
      "section": "第 2 条：归档周期",
      "excerpt": "第 2 条：演示型号 A-100 的服务记录归档周期为 7 天。"
    }
  ],
  "checks": {
    "read_permission_checked": true,
    "only_authorized_citations": true,
    "only_current_citations": true,
    "conflict_detected": true,
    "source_metadata_withheld": false,
    "business_write_executed": false
  },
  "review_steps": [
    "核对每份引文的版本、适用范围和效力等级。",
    "由资料责任人澄清覆盖关系并更新资料后，再重新查询。"
  ]
}
```

</details>

### C06 · 权限不足时检查完整响应

输入模拟 guest 角色。实际响应为 access_denied，citations 为空，同时保留流程检查字段。复核完整 JSON，可以看到响应未返回 D01、D02 的来源编号、标题和引文。这只检验本地规则，真实身份与授权仍需在服务端实现。

输入参数如下。

```json
{
  "question": "演示型号 A-100 的服务记录归档周期是多少天？",
  "available_documents": [
    "D01",
    "D02"
  ],
  "roles": [
    "guest"
  ]
}
```

<details>
<summary>展开实际计算的完整输出</summary>

```json
{
  "answer": "当前身份无权读取此问题所需资料，请由授权人员核对访问权限。",
  "status": "access_denied",
  "citations": [],
  "checks": {
    "read_permission_checked": true,
    "only_authorized_citations": true,
    "only_current_citations": true,
    "conflict_detected": false,
    "source_metadata_withheld": true,
    "business_write_executed": false
  },
  "review_steps": [
    "由资料管理员核对身份与授权；授权完成后重新查询。"
  ]
}
```

</details>

如需独立重现，先按上文克隆仓库。在仓库根目录执行下列 Python 脚本，输出会由输入重新计算。`expected` 仅用于测试器判定，以下调用未将它传入查询函数。

```python
import json
from pathlib import Path
from reference_sample.engine import evaluate, load_documents

fixtures = Path("reference_sample/fixtures/cases.json")
cases = json.loads(fixtures.read_text(encoding="utf-8"))["cases"]
documents = load_documents()
for case in cases:
    if case["id"] in {"C01", "C05", "C06"}:
        result = evaluate(
            question=case["question"],
            available_documents=case["available_documents"],
            roles=case["roles"],
            documents=documents,
        )
        print(case["id"])
        print(json.dumps(result, ensure_ascii=False, indent=2))
```

采购交流时，可按同样次序要求服务商展示获准使用的任务、实际输入、所用资料版本、完整响应和未通过项，再约定进入真实系统后的验收。

## 怎样确认结果由规则和资料计算而来

fixtures/cases.json 保存输入与期望；engine.evaluate 不读取期望结果。测试器另行比较计算输出与期望。

此外，四个性质检查会在内存中改变条件：打乱文档顺序，把现行事实改为 19 天，消除两份资料的冲突，以及移除读取角色。检查结果是否随条件合理变化。内存修改不改变交付的三份原始文档。

这提供了一种复核方式，但仍不是通用自然语言理解评测。程序只处理明示的有限主题、型号和规则。

## 接入真实模型以后，还差哪些检查

生产应用需要增加实际检索、模型输出、身份认证、授权与租户边界、业务接口和运行条件的验证。样本也要来自获准使用的真实任务，并由业务人员确定判定依据。

如果接入写操作，还要分别验证批准、执行、超时、重试和人工接管。参考包没有业务接口，“转人工”只是返回状态与建议，没有实际创建工单。

可以先利用这份材料讨论“需要交什么证据”，再为实际系统建立评测集。平衡点的[企业知识库验收指南](https://khanfate.com/insights/knowledge-base-acceptance/)和[企业 AI 服务说明](https://khanfate.com/solutions/enterprise-ai/)提供了进一步的需求交流入口。

作者：淄博市平衡点人工智能科技公司（平衡点人工智能）。本文使用 AI 辅助结构整理与初稿编写；资料、型号和角色均为公开合成示例，不对应客户项目。
