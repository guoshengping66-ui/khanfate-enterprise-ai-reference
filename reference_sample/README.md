# 知识查询交付参考样例

本包是平衡点官网可下载的公开合成参考材料。组织、型号、资料、角色与问题均为虚构，不是客户案例、上线系统、实测业务成效或设备操作指南。

实现只使用 Python 3.9+ 标准库。没有调用模型，没有第三方库、网络请求、向量数据库或生产 RAG。它通过有限关键词识别问题，再对 Markdown 中的结构化事实实施确定性规则；不能据此声称具备任意自然语言理解或通用知识检索能力。

## 运行与独立复核

解压后进入 `reference_sample` 文件夹，执行：

```powershell
python build_sample.py
```

成功应显示固定用例 `total=10, passed=10, failed=0`，独立性质检查 `property_total=4, property_passed=4`，并退出 0。任何用例、性质检查或数据加载失败都会退出非 0。

重新生成交付文件：

```powershell
python build_sample.py --output-dir .\generated\assets
```

从本文件夹的父目录也可执行 `python -m reference_sample`。集成到网页构建脚本时，将本包父目录 `source` 放入 Python 模块路径，然后调用：

```python
from reference_sample import export_sample

report = export_sample(r"C:\path\to\assets")
print(report["summary"])
```

参数直接指向目标 `assets` 目录。函数写出 `knowledge-reference-results.json` 与 `knowledge-reference-sample.zip`；验收未通过会抛出异常，不导出新的交付文件。源文件哈希随结果公开，固定文件顺序与 ZIP 时间戳用于逐字节复核。

## 三份资料

| 编号 | 内容 | 状态 | 读取角色 |
|---|---|---|---|
| D01 | 归档周期 30 天 | 旧版，2025-12-31 已失效 | service_reader |
| D02 | 归档周期 14 天 | 2026-01-01 起现行有效 | service_reader |
| D03 | 归档周期 7 天 | 2026-01-01 起现行有效，与 D02 同级 | service_reader |

每份文档的 Markdown 顶部含 JSON 元数据。加载时会核对结构化天数与正文一致。D03 只在冲突用例中纳入可用资料；不假定“专项”标题自动拥有覆盖权。

## 规则和验收

规则的固定参考日期是 **2026-01-15**，不读取运行当天日期。

1. 识别包含写入动词的请求后返回 `action_not_executed`；本包没有业务系统接口。
2. 通过有限关键词匹配型号与“服务记录归档”主题；不匹配时返回 `insufficient_basis`。
3. 排除失效资料，随后检查所有相关现行资料的模拟角色条件。有任一所需资料不可读时返回 `access_denied`，不返回资料编号、名称、正文或冲突信息，也不退回旧版。
4. 对可读取的现行资料按明示效力等级筛选。选中资料数值一致时回答并附引文；同级数值不一致时返回 `conflict_review`，不选定天数，由人工核对。
5. 缺少可用现行依据时拒绝给出天数，不补全或猜测。

`fixtures/cases.json` 逐项列出可用资料、模拟角色、问题及期望状态。`engine.evaluate` 没有 expected 参数，也不读取该 fixtures；测试器独立比较计算结果与期望。

10 个固定用例覆盖：现行优先、旧版不能覆盖、只有失效资料、未知型号、同级冲突、无权限不泄露、写入不执行、未知主题、无权限不泄露冲突、空资料集。另有 4 个内存性质检查：打乱文档顺序、将事实反事实改为 19 天、消除冲突事实、移除读取角色。反事实只存在于测试内存，不改变三份交付文档。

`results/rules-results.json` 是实际执行输出；`results/acceptance.csv` 是固定用例的验收表。每个结果包含 answer、status、citations、checks 和人工复核步骤。引文编号、版本、生效日期、条款、原文摘要可回到三份资料逐条对照。

## 权限与能力边界

全部材料是公开合成材料。输入中的 `roles` 只是可更改的本地测试字符串；本包不认证身份，也没有服务端权限服务。无权限用例证明的是本地规则分支和响应字段，不是实际资料保密或端到端安全。真实身份认证、授权、租户隔离、检索过滤及来源内容保护必须在服务端实施，不能信任客户端传入角色。

本包没有生产 RAG、自动人工工单、审计持久化或业务执行能力。“转人工”只是一种返回状态和建议步骤，没有实际发起任何工单。写入请求不会产生外部操作。固定用例全部通过，只说明这些公开用例满足这些规则，不能推导生产准确率、客户效果或安全保证。

## ZIP 内容

- 本中文 README、三份合成 Markdown 文档。
- Python 规则、导出与验收源码，无第三方依赖。
- fixtures/cases.json：公开输入与期望。
- results/rules-results.json：实测结果与源码 SHA-256。
- results/acceptance.csv：逐用例验收记录，UTF-8 BOM 便于中文表格查看。
