# 2026-09-18 官方条文增量

最新结果见 [官方资料验收](official-source-acceptance.md)：30 条真实官方原始公报条文，350 块，24 个有来源问题与 6 个资料缺失问题。三路检索在此开发集均 Hit@5 24/24、误给证据 0/6；实际 PostgreSQL HTTP 回归 30/30。额外三条口语改写目标条文进入支持证据为 0/3，候选原文仍可查看。不能据此宣称法律准确率或普遍自然语言能力。

以下保留早期虚构集验收，时间与数据范围不同。


# 检索回归与验收边界

用户需要能够核对原文，并分清找到了候选、获得了可引用证据、以及专业结论三个层次。本轮只对前两层建立可复现技术回归。

## 本次实际运行

使用真实 BGE small English / 384 维 模型，对仓库内 5 份原创虚构资料执行构建与 8 题评测（5 题有标注来源，3 题不应输出证据）。关键词、向量和混合检索均 Hit@3 5/5、来源 Recall@3 1.0、MRR@3 1.0；3 个无答案问题的证据输出为 0/3。完整逐题结果见 [模型回归](evaluation/fictional-model-regression.json)，构建配置见 [manifest](evaluation/model-manifest.json)。

这些是简单虚构样例上的组件结果，不是医学或法律质量评测，不是已部署客户效果。来源标注可能不完整，命中来源也不能证明选中片段充分回答问题。不能拿这 8 题对外宣称专业准确率。

18 项 Python 测试通过，其中 2 项连接本机隔离 PostgreSQL；覆盖事务回滚、幂等导入、审核门槛、评测分母以及输入长度。模型 tokenizer 在推理前计算包含查询指令和特殊 token 的长度，超过 512 token 明确拒绝；关键词模式无需查询向量推理。知识服务启动时检查模型、维度和查询指令是否与索引一致。

## 运行

Python 3.10 或 3.11，先安装 knowledge/requirements.txt：

```sh
python knowledge/pipeline.py build --language en --documents knowledge/examples/documents.jsonl --index output/regression/index.json --cache-dir .cache/models
python knowledge/evaluate.py --language en --index output/regression/index.json --cases knowledge/evaluation/cases.json --output output/regression/report.json --cache-dir .cache/models --min-hit-rate 1 --max-false-evidence-rate 0
```

报告不可覆盖。指定门槛时，指标不足、分母缺失或地区混入均退出 2，保留失败报告。GitHub Actions 的 Knowledge model regression 下载真实公开模型，重建虚构语料并运行这些门槛。它不是 mock 向量测试，但也不是真实专业语料验收。

## 指标定义

Hit@k 衡量是否找回标注来源；Recall@k 对来源去重；MRR@k 使用第一个标注来源的片段排名；source precision 为返回的不同来源中标注相关来源占比，不是平均精度 AP。false evidence rate 只以不应输出证据的题目为分母。evidence policy accuracy 只检查是否输出任何证据，不检查内容正确性。空分组返回 null，不能记作 100%。延迟包含语义查询推理，不包含模型加载、数据库和网页。

方法参考 [Haystack 对组件与端到端评测的区分](https://docs.haystack.deepset.ai/docs/evaluation) 和 [Ragas 的证据相关性指标说明](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)。评测器是本项目原创统计实现，未集成 Ragas 或使用 LLM judge。

## 尚未验证

没有独立领域专家标注集、真实用户参与者或线上客户数据库。正式领域评测还需要否定条件、来源冲突、时效、证据不足以及人工抽检。模型下载制品尚未作为固定哈希的生产供应链发布。本轮 CI 和本地数据库证据不能替代完整用户流程验收。

本轮同时将构建和服务的默认语言对齐为英文，避免英文索引启动时误用中文模型。更换模型或语言需要重新构建；不能在不同向量空间间混合检索。
