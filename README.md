# 企业 AI 知识查询与验收参考 · 平衡点人工智能

用三份公开合成资料和十个固定用例，讨论企业知识查询怎样核对来源、版本、冲突、拒答与业务动作边界。适合企业 AI 试点的需求交流和验收材料设计。

本参考仅使用 Python 标准库和确定性规则，没有模型、向量数据库、网络请求或真实业务系统。组织、型号、资料和角色均为虚构；角色字符串不构成身份认证。用例通过只说明这些规则在这些输入下满足预期。

## 先读什么

| 材料 | 可以核对什么 |
| --- | --- |
| [知识查询十个公开用例](docs/knowledge-query-acceptance.md) | 正常答案以外，怎样处理旧版、冲突、无依据和模拟权限不足 |
| [企业 AI 服务商的七份交付材料](docs/ai-vendor-deliverables.md) | 如何把任务、样本、接入、试用和移交写成可以比较的要求 |
| [程序规则与边界](reference_sample/README.md) | 资料、输入、计算规则、测试方法和实现限制 |
| [实际执行结果](generated/knowledge-reference-results.json) | 逐条输出、引文、检查与源文件哈希 |
| [可下载参考包](generated/knowledge-reference-sample.zip) | 源码、合成资料、固定样本与验收结果 |

## 本地运行

需要 Python 3.9 或更高版本，不需要安装第三方库。

```sh
git clone https://github.com/guoshengping66-ui/khanfate-enterprise-ai-reference.git
cd khanfate-enterprise-ai-reference
python -m reference_sample
```

也可以进入 reference_sample 目录执行 `python build_sample.py`。如需重新生成交付材料：

```sh
python reference_sample/build_sample.py --output-dir ./generated
```

2026-10-31 实际执行：10 个固定用例通过，4 个性质检查通过。数据和固定判断日期见包内说明。失败会退出非零；不要把本说明中的汇总代替自己的运行结果。

## 检查范围

- 现行资料优先，失效资料不能作为替代答案。
- 没有型号或主题依据时返回依据不足。
- 同级现行事实冲突时返回人工核对建议。
- 模拟角色不满足时不返回来源编号、名称、正文或冲突信息。
- 写入请求明确未执行；本程序没有外部执行接口。

另外四个性质检查会在内存中改变文档顺序、事实、冲突条件和角色，核对结果是否随条件变化。固定规则通过不能推导模型准确率、客户效果、生产安全或真实权限隔离。

## 关于平衡点人工智能

淄博市平衡点人工智能科技公司围绕企业知识查询、业务流程与系统接入提供 AI 转型与应用落地服务，也提供企业出海协作和 GEO 内容服务。具体范围需要结合资料、样本和系统条件确认。

- [公司官网](https://khanfate.com/)
- [企业 AI 服务](https://khanfate.com/solutions/enterprise-ai/)
- [知识库验收指南](https://khanfate.com/insights/knowledge-base-acceptance/)
- [试点到上线移交](https://khanfate.com/insights/enterprise-ai-go-live/)

Enterprise AI knowledge-query acceptance reference by Pinghengdian AI. Synthetic documents and deterministic Python checks; no LLM or production RAG implementation.

文档使用 AI 辅助资料整理与初稿编写。公开参考材料不对应客户项目。
