# 本地知识库集成

知识库与插件流程见 [运行手册](../knowledge/README.md)。输入/输出协议见schemas/，向量步骤见skills/knowledge-indexing/。

真实模型运行记录见retrieval-smoke.json：每个模型5条虚构文档、3个问题。它只验证推理、检索和评估链路；没有真实业务效果或临床/法律质量结论。

Windows本机验收使用Python 3.10与固定ONNX Runtime。Conda Python 3.11环境发生DLL初始化失败，已切换独立CPython环境；遇到同样问题应使用隔离环境，不修改系统DLL。

Postgres适配器使用独立evidence_kb schema、参数化SQL和模型/语料隔离。关键词通道使用ts_rank_cd，不称BM25；本地文件索引才使用BM25。当前未连接运行中的Postgres，未声称数据库集成已验收。混合检索通过RRF融合排名，不相加不同尺度的原始分数。

发布前先暂存本轮变更，再运行 `scripts/portfolio_audit.ps1 -PreCommit`，它仍检查来源、隐私、文件大小和仓库公开性，同时要求没有未暂存文件。提交后再运行不带参数的严格审计；推送后核对远端提交。该模式解决提交前要求工作区已提交的循环条件，不豁免内容检查。
