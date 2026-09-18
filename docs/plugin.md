# 插件与持久化知识库

插件版本 0.3.1，保留旧 JSON 小样例接口与官方出版物快照工作流。两个 Skill 分别负责知识索引和来源核对，不把模型内部 token/position embedding 拆成假的独立算法。

主流程：导入选定官方条文，构建一次索引，重复查询同一索引，导出核对单。`knowledge/research.py --request` 读取结构化请求，避免把用户问题拼进 shell。请求与输出 Schema 位于 schemas/research-input.schema.json 和 schemas/evidence-review.schema.json。

旧 `scripts/plugin_run.py` 适合短 JSON 文档和离线关键词对照，hybrid 模式会为本次输入构建索引；批量法规研究应使用持久化流程。旧输出中的 confidence 现在为 unrated 或 none，检索分数不能推出法律置信度。

本机 Windows 独立 CPython 3.10、BGE ONNX 和 PostgreSQL/pgvector 真实通过；Conda 3.11 的 DLL 故障保留为环境限制。数据库的关键词通道使用 ts_rank_cd，不称 BM25；本地文件模式使用 BM25。HTTP 接口与浏览器直接连接同一服务，详见本轮验收。

插件宿主可以基于 evidence 撰写综述，每项陈述附 source_id/chunk_id。review_candidates 是待核对线索，不得当作支持证据。引用源为原始公报，必须保留版本范围。无法验证当前适用性时列出待核对项，不用模型记忆补足。

CLI 和服务均可显式添加 `--ranking rerank`。默认 hybrid 输出 Schema 1.1；实验模式输出 1.2，增加模型版本、制品哈希和未校准评分元数据。上下文片段保留原始 matched_chunk_id、完整原文内的字符范围和内容哈希。该模式未通过默认接入门槛，不要由宿主自动启用。见[实验记录](reranker-experiment.md)。

发布前暂存变更并运行 `scripts/portfolio_audit.ps1 -PreCommit`，提交后运行 `-BeforePush` 审计，推送后运行不带参数的严格审计并核对同一提交的 GitHub 检查。未验证所有插件宿主安装环境。
